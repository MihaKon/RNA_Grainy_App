from fastapi import APIRouter, File, Form, Request, UploadFile

from app.models.api import CoarseGrainResult, ErrorResponse
from app.models.form import FileUploadRequest, PresetRequest, RCSBRequest, UploadBase
from app.services.coarse_graining import (
    StructureSource,
    build_coarse_grain_result,
    coarse_grain_structure,
    fetch_rcsb_structure,
    read_preset_structure,
    read_uploaded_structure,
)

router = APIRouter(
    prefix="/api/coarse-grain",
    tags=["coarse-grain"],
    responses={422: {"model": ErrorResponse}},
)


async def process_and_build_result(
    request: Request, source: StructureSource, upload_request: UploadBase
) -> CoarseGrainResult:
    models: list[int] = upload_request.models  # type: ignore[assignment]
    chains: list[str] = upload_request.chains  # type: ignore[assignment]
    custom_model_data: dict | None = upload_request.custom_model_data  # type: ignore[assignment]

    outcome = await coarse_grain_structure(
        source,
        upload_request.selected_model,
        models=models,
        chains=chains,
        custom_model_data=custom_model_data,
    )
    return build_coarse_grain_result(
        request,
        source,
        outcome,
        upload_request.selected_model,
        models=models,
        chains=chains,
        custom_model_data=custom_model_data,
    )


@router.post("/file")
async def coarse_grain_file(
    request: Request,
    file: UploadFile = File(...),
    selected_model: str = Form(...),
    custom_model_data: str | None = Form(None),
    models: str | None = Form(None),
    chains: str | None = Form(None),
) -> CoarseGrainResult:
    upload_request = FileUploadRequest(
        file=file,
        selected_model=selected_model,
        custom_model_data=custom_model_data,
        models=models,  # type: ignore[arg-type]
        chains=chains,  # type: ignore[arg-type]
    )
    source = await read_uploaded_structure(upload_request.file)
    return await process_and_build_result(request, source, upload_request)


@router.post("/rcsb")
async def coarse_grain_rcsb(
    request: Request,
    rcsb_id: str = Form(...),
    selected_model: str = Form(...),
    custom_model_data: str | None = Form(None),
    models: str | None = Form(None),
    chains: str | None = Form(None),
) -> CoarseGrainResult:
    upload_request = RCSBRequest(
        rcsb_id=rcsb_id,
        selected_model=selected_model,
        custom_model_data=custom_model_data,
        models=models,  # type: ignore[arg-type]
        chains=chains,  # type: ignore[arg-type]
    )
    source = await fetch_rcsb_structure(upload_request.rcsb_id)
    return await process_and_build_result(request, source, upload_request)


@router.post("/preset")
async def coarse_grain_preset(
    request: Request,
    preset_id: str = Form(...),
    selected_model: str = Form(...),
    custom_model_data: str | None = Form(None),
    models: str | None = Form(None),
    chains: str | None = Form(None),
) -> CoarseGrainResult:
    upload_request = PresetRequest(
        preset_id=preset_id,
        selected_model=selected_model,
        custom_model_data=custom_model_data,
        models=models,  # type: ignore[arg-type]
        chains=chains,  # type: ignore[arg-type]
    )
    source = read_preset_structure(upload_request.preset_id)
    return await process_and_build_result(request, source, upload_request)
