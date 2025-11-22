from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

from app.exceptions import FileProcessingError, ValidationError
from app.models import (
    CoarseGrainModels,
    FileUploadRequest,
    RCSBRequest,
    SupportedFormats,
)
from app.rcsb import fetch_rcsb_file
from app.services.structure_service import StructureProcessor
from app.settings import TEMPLATES

router = APIRouter(prefix="/upload", tags=["upload"])


def render_error_response(
    request: Request, error: str, status_code: int
) -> HTMLResponse:
    context = {"error": error}
    return TEMPLATES.TemplateResponse(
        request=request,
        name="components/error_alert.html",
        context=context,
        status_code=status_code,
    )


def process_and_render_comparison(
    request: Request,
    file_content: str,
    filename: str,
    file_format: SupportedFormats,
    selected_model: CoarseGrainModels,
) -> HTMLResponse:
    original_structure = StructureProcessor.parse_structure(
        file_content, filename, file_format
    )
    coarse_content = StructureProcessor.apply_coarse_graining(
        original_structure, selected_model
    )
    coarse_structure = StructureProcessor.parse_structure(
        coarse_content,
        filename,
        SupportedFormats.PDB,
    )

    context = StructureProcessor.build_comparison_context(
        filename=filename,
        original_content=file_content,
        coarse_content=coarse_content,
        file_format=file_format,
        selected_model=selected_model.name,
        original_structure=original_structure,
        coarse_structure=coarse_structure,
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
        upload_req = FileUploadRequest(file=file, selected_model=selected_model)
    except Exception as e:
        return render_error_response(request, str(e), 400)

    try:
        file_content = (await upload_req.file.read()).decode("utf-8")
    except Exception as e:
        raise FileProcessingError(f"Error reading file: {e}")

    file_format = SupportedFormats(upload_req.file.filename.split(".")[-1].lower())
    filename = upload_req.file.filename

    return process_and_render_comparison(
        request, file_content, filename, file_format, upload_req.selected_model
    )


@router.post("/rcsb/", response_class=HTMLResponse)
async def upload_rcsb(
    request: Request,
    rcsb_id: str = Form(...),
    selected_model: str = Form(...),
) -> HTMLResponse:
    try:
        rcsb_req = RCSBRequest(rcsb_id=rcsb_id, selected_model=selected_model)
    except ValidationError as e:
        return render_error_response(request, e.detail, e.status_code)

    file_content = await fetch_rcsb_file(rcsb_req.rcsb_id)
    if file_content is None:
        raise ValidationError(
            "Something went wrong during fetching from RCSB database."
        )

    file_format = SupportedFormats.CIF
    filename = f"{rcsb_req.rcsb_id}.{file_format}"

    return process_and_render_comparison(
        request, file_content, filename, file_format, rcsb_req.selected_model
    )
