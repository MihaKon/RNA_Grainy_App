from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from gemmi import Structure

from app.exceptions import FileProcessingError
from app.models import (
    COARSE_FILE_FORMAT,
    ExampleRequest,
    FileUploadRequest,
    RCSBRequest,
    SupportedFormats,
)
from app.rcsb import fetch_rcsb_file
from app.services.jobs import JobManager
from app.services.structures import StructureProcessor
from app.settings import EXAMPLES_DIR, MAX_FILE_UPLOAD_SIZE, TEMPLATES

router = APIRouter(prefix="/upload", tags=["upload"])


def process_structure_and_get_metadata(
    file_content: str,
    file_format: SupportedFormats,
    selected_model: str,
    models: list[int],
    chains: list[str],
    custom_model_data: dict | None = None,
) -> tuple[Structure, Structure, dict[str, int]]:
    original_structure = StructureProcessor.parse_structure(
        file_content, file_format, models=models, chains=chains
    )
    coarse_structure = StructureProcessor.apply_coarse_graining(
        original_structure, selected_model, custom_model_data
    )

    atom_counts = {
        "original": StructureProcessor.get_structure_atom_count(original_structure),
        "coarse": StructureProcessor.get_structure_atom_count(coarse_structure),
    }
    return original_structure, coarse_structure, atom_counts


async def save_structures(
    job_id: str,
    original_structure: Structure,
    file_format: SupportedFormats,
    coarse_structure: Structure,
) -> None:
    JobManager.setup_job_dir(job_id)

    original_format = file_format.normalize_format()

    original_content = StructureProcessor.structure_to_cif_string(original_structure)
    cif_content = StructureProcessor.structure_to_cif_string(coarse_structure)
    pdb_content = StructureProcessor.structure_to_pdb_string(coarse_structure)

    await JobManager.create_file(
        job_id, original_content, f"reference.{original_format.value}"
    )
    await JobManager.create_file(
        job_id, cif_content, f"coarse.{COARSE_FILE_FORMAT.value}"
    )
    await JobManager.create_file(
        job_id, pdb_content, f"coarse.{SupportedFormats.PDB.value}"
    )


async def handle_request_and_render(
    request: Request,
    file_content: str,
    filename: str,
    file_format: SupportedFormats,
    selected_model: str,
    models: list[int],
    chains: list[str],
    custom_model_data: dict | None = None,
) -> HTMLResponse:
    job_id = JobManager.create_job_id()
    original_structure, coarse_structure, atom_counts = (
        process_structure_and_get_metadata(
            file_content,
            file_format,
            selected_model,
            models,
            chains,
            custom_model_data,
        )
    )
    await save_structures(job_id, original_structure, file_format, coarse_structure)

    context = StructureProcessor.build_comparison_context(
        request=request,
        job_id=job_id,
        filename=filename,
        file_format=file_format,
        selected_model=selected_model,
        atom_counts=atom_counts,
        selected_models=models,
        selected_chains=chains,
        custom_model_data=custom_model_data,
    )
    return TEMPLATES.TemplateResponse(
        request=request,
        name="comparison.html",
        context=context,
    )


@router.post("/file/", response_class=HTMLResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    selected_model: str = Form(...),
    custom_model_data: str = Form(None),
    models: str = Form(None),
    chains: str = Form(None),
) -> HTMLResponse:
    upload_req = FileUploadRequest(
        file=file,
        selected_model=selected_model,
        custom_model_data=custom_model_data,
        models=models,
        chains=chains,
    )
    if upload_req.file.size is None:
        raise FileProcessingError("Uploaded file is empty.")
    elif upload_req.file.size > MAX_FILE_UPLOAD_SIZE:
        raise FileProcessingError(
            f"File size exceeds maximum file upload size of: {MAX_FILE_UPLOAD_SIZE / 1024} KB." #TODO: MB
        )

    try:
        file_content = (await upload_req.file.read()).decode("utf-8")
    except UnicodeDecodeError as e:
        raise FileProcessingError(f"Error reading file: {e}")

    if file_content == "":
        raise FileProcessingError("Uploaded file is empty.")

    file_format = SupportedFormats(upload_req.file.filename.split(".")[-1].lower())  # type: ignore
    filename: str = upload_req.file.filename.split(".")[0]  # type: ignore

    return await handle_request_and_render(
        request,
        file_content,
        filename,
        file_format,
        upload_req.selected_model,
        models=upload_req.models,  # type: ignore
        chains=upload_req.chains,  # type: ignore
        custom_model_data=upload_req.custom_model_data,  # type: ignore
    )


@router.post("/rcsb/", response_class=HTMLResponse)
async def upload_rcsb(
    request: Request,
    rcsb_id: str = Form(...),
    selected_model: str = Form(...),
    custom_model_data: str = Form(None),
    models: str = Form(None),
    chains: str = Form(None),
) -> HTMLResponse:
    rcsb_req = RCSBRequest(
        rcsb_id=rcsb_id,
        selected_model=selected_model,
        custom_model_data=custom_model_data,
        models=models,
        chains=chains,
    )  # type: ignore

    file_content = await fetch_rcsb_file(rcsb_req.rcsb_id)
    if file_content is None:
        raise FileProcessingError(
            f"Could not fetch file for RCSB ID: {rcsb_req.rcsb_id}"
        )

    file_format = SupportedFormats.CIF
    filename: str = rcsb_req.rcsb_id

    return await handle_request_and_render(
        request,
        file_content,
        filename,
        file_format,
        rcsb_req.selected_model,
        models=rcsb_req.models,  # type: ignore
        chains=rcsb_req.chains,  # type: ignore
        custom_model_data=rcsb_req.custom_model_data,  # type: ignore
    )


@router.post("/example/", response_class=HTMLResponse)
async def upload_example(
    request: Request,
    example_id: str = Form(...),
    selected_model: str = Form(...),
    custom_model_data: str = Form(None),
    models: str = Form(None),
    chains: str = Form(None),
) -> HTMLResponse:
    example_req = ExampleRequest(
        example_id=example_id,
        selected_model=selected_model,
        custom_model_data=custom_model_data,
        models=models,
        chains=chains,
    )  # type: ignore
    example_path = (
        EXAMPLES_DIR / f"{example_req.example_id}.{SupportedFormats.CIF.value}"
    )

    if not example_path.exists():
        raise FileProcessingError(
            f"Example file not found for ID: {example_req.example_id}"
        )

    try:
        file_content = example_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise FileProcessingError(f"Error reading example file: {e}")

    if file_content == "":
        raise FileProcessingError("Example file is empty.")

    file_format = SupportedFormats.CIF
    filename: str = example_req.example_id

    return await handle_request_and_render(
        request,
        file_content,
        filename,
        file_format,
        example_req.selected_model,
        models=example_req.models,  # type: ignore
        chains=example_req.chains,  # type: ignore
        custom_model_data=example_req.custom_model_data,  # type: ignore
    )
