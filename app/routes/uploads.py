from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

from app.models.form import FileUploadRequest, PresetRequest, RCSBRequest, UploadBase
from app.services.coarse_graining import (
    StructureSource,
    coarse_grain_structure,
    fetch_rcsb_structure,
    read_preset_structure,
    read_uploaded_structure,
)
from app.services.structures import StructureProcessor
from app.settings import TEMPLATES

router = APIRouter(prefix="/upload", tags=["upload"])


async def handle_request_and_render(
    request: Request, source: StructureSource, upload_request: UploadBase
) -> HTMLResponse:
    outcome = await coarse_grain_structure(
        source,
        upload_request.selected_model,
        models=upload_request.models,  # type: ignore
        chains=upload_request.chains,  # type: ignore
        custom_model_data=upload_request.custom_model_data,  # type: ignore
    )

    context = StructureProcessor.build_comparison_context(
        request=request,
        workspace_id=outcome.workspace_id,
        filename=source.filename,
        file_format=source.file_format,
        selected_model=upload_request.selected_model,
        atom_counts={
            "original": outcome.original_atom_count,
            "coarse": outcome.coarse_atom_count,
        },
        selected_models=upload_request.models,  # type: ignore
        selected_chains=upload_request.chains,  # type: ignore
        custom_model_data=upload_request.custom_model_data,  # type: ignore
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
    upload_request = FileUploadRequest(
        file=file,
        selected_model=selected_model,
        custom_model_data=custom_model_data,
        models=models,
        chains=chains,
    )
    source = await read_uploaded_structure(upload_request.file)
    return await handle_request_and_render(request, source, upload_request)


@router.post("/rcsb/", response_class=HTMLResponse)
async def upload_rcsb(
    request: Request,
    rcsb_id: str = Form(...),
    selected_model: str = Form(...),
    custom_model_data: str = Form(None),
    models: str = Form(None),
    chains: str = Form(None),
) -> HTMLResponse:
    upload_request = RCSBRequest(
        rcsb_id=rcsb_id,
        selected_model=selected_model,
        custom_model_data=custom_model_data,
        models=models,
        chains=chains,
    )
    source = await fetch_rcsb_structure(upload_request.rcsb_id)
    return await handle_request_and_render(request, source, upload_request)


@router.post("/preset/", response_class=HTMLResponse)
async def upload_preset(
    request: Request,
    preset_id: str = Form(...),
    selected_model: str = Form(...),
    custom_model_data: str = Form(None),
    models: str = Form(None),
    chains: str = Form(None),
) -> HTMLResponse:
    upload_request = PresetRequest(
        preset_id=preset_id,
        selected_model=selected_model,
        custom_model_data=custom_model_data,
        models=models,
        chains=chains,
    )
    source = read_preset_structure(upload_request.preset_id)
    return await handle_request_and_render(request, source, upload_request)
