from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

from app import messages
from app.exceptions import FileProcessingError, ValidationError
from app.models import (
    COARSE_FILE_FORMAT,
    FileUploadRequest,
    RCSBRequest,
    SupportedFormats,
)
from app.rcsb import fetch_rcsb_file
from app.services.job_service import JobManager
from app.services.structure_service import StructureProcessor
from app.settings import TEMPLATES

router = APIRouter(prefix="/upload", tags=["upload"])


def process_structure(
    file_content: str,
    file_format: SupportedFormats,
    selected_model: str,
) -> str:
    original_structure = StructureProcessor.parse_structure(file_content, file_format)
    coarse_content = StructureProcessor.apply_coarse_graining(
        original_structure, selected_model
    )

    return coarse_content


async def run_job_processing(
    job_id: str,
    file_content: str,
    file_format: SupportedFormats,
    selected_model: str,
) -> None:
    JobManager.setup_job_dir(job_id)

    original_format = file_format.normalize_format()
    original_filename: str = f"reference.{original_format.value}"
    coarse_filename: str = f"coarse.{COARSE_FILE_FORMAT.value}"
    coarse_content = process_structure(file_content, file_format, selected_model)

    await JobManager.create_file(job_id, file_content, original_filename)
    await JobManager.create_file(job_id, coarse_content, coarse_filename)


async def handle_request_and_render(
    request: Request,
    file_content: str,
    filename: str,
    file_format: SupportedFormats,
    selected_model: str,
) -> HTMLResponse:
    job_id = JobManager.create_job_id()
    await run_job_processing(job_id, file_content, file_format, selected_model)

    context = StructureProcessor.build_comparison_context(
        job_id, filename, file_format, selected_model
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
) -> HTMLResponse:
    try:
        upload_req = FileUploadRequest(file=file, selected_model=selected_model)  # type: ignore
    except Exception as e:
        return messages.render_form_error_message(request, str(e), 400)

    try:
        file_content = (await upload_req.file.read()).decode("utf-8")
    except Exception as e:
        raise FileProcessingError(f"Error reading file: {e}")

    if file_content == "":
        return messages.render_form_error_message(request, "The file is empty.", 400)

    file_format = SupportedFormats(upload_req.file.filename.split(".")[-1].lower())  # type: ignore
    filename: str = upload_req.file.filename.split(".")[0] # type: ignore

    return await handle_request_and_render(
        request, file_content, filename, file_format, upload_req.selected_model
    )


@router.post("/rcsb/", response_class=HTMLResponse)
async def upload_rcsb(
    request: Request,
    rcsb_id: str = Form(...),
    selected_model: str = Form(...),
) -> HTMLResponse:
    try:
        rcsb_req = RCSBRequest(rcsb_id=rcsb_id, selected_model=selected_model)  # type: ignore
    except ValidationError as e:
        return messages.render_form_error_message(request, e.detail, e.status_code)

    file_content = await fetch_rcsb_file(rcsb_req.rcsb_id)
    if file_content is None:
        raise ValidationError(
            "Something went wrong during fetching from RCSB database."
        )

    file_format = SupportedFormats.CIF
    filename: str = rcsb_req.rcsb_id

    return await handle_request_and_render(
        request, file_content, filename, file_format, rcsb_req.selected_model
    )
