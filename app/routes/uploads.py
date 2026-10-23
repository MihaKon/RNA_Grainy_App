from collections import defaultdict
from typing import Any

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

from app.models.form import (
    COARSE_FILE_FORMAT,
    FileUploadRequest,
    PresetRequest,
    RCSBRequest,
    SupportedFormats,
    UploadBase,
)
from app.services.coarse_graining import (
    StructureSource,
    coarse_grain_structure,
    fetch_rcsb_structure,
    read_preset_structure,
    read_uploaded_structure,
)
from app.services.doc import DocsContextBuilder
from app.settings import PDB_MAX_ATOM_COUNT, TEMPLATES

router = APIRouter(prefix="/upload", tags=["upload"])


def build_comparison_context(
    request: Request,
    workspace_id: str,
    filename: str,
    file_format: SupportedFormats,
    selected_model: str,
    atom_counts: dict[str, int],
    selected_models: list[int],
    selected_chains: list[str],
    custom_model_data: dict | None = None,
) -> defaultdict[str, Any]:
    original_format = file_format.normalize_format()

    model_data = DocsContextBuilder.get_model(selected_model, custom_model_data)
    original_atom_count = atom_counts["original"]
    coarse_atom_count = atom_counts["coarse"]
    is_pdb_available = coarse_atom_count <= PDB_MAX_ATOM_COUNT
    reduction = (
        1 - (coarse_atom_count / original_atom_count) if original_atom_count > 0 else 0
    )

    reference_url = str(
        request.url_for(
            "get_result_file", workspace_id=workspace_id, file_type="reference"
        ).include_query_params(file_format=original_format.value)
    )
    coarse_mmcif_url = str(
        request.url_for(
            "get_result_file", workspace_id=workspace_id, file_type="coarse"
        ).include_query_params(file_format=COARSE_FILE_FORMAT.value)
    )

    coarse_pdb_url = str(
        request.url_for(
            "get_result_file", workspace_id=workspace_id, file_type="coarse"
        ).include_query_params(file_format=SupportedFormats.PDB.value)
    )

    consumed_url = str(
        request.url_for(
            "mark_result_as_consumed",
            workspace_id=workspace_id,
        )
    )

    initial_data = {
        "reference_url": reference_url,
        "coarse_mmcif_url": coarse_mmcif_url,
        "coarse_pdb_url": coarse_pdb_url if is_pdb_available else None,
        "consumed_url": consumed_url,
        "file_format": [original_format.value, COARSE_FILE_FORMAT.value],
        "workspace_id": workspace_id,
        "filename": filename,
        "atom_counts": {
            "original": original_atom_count,
            "coarse": coarse_atom_count,
            "reduction": f"{reduction:.2%}",
        },
        "selected_chains": selected_chains,
        "selected_models": selected_models,
        "model": model_data,
        "is_pdb_available": is_pdb_available,
    }

    context: defaultdict[str, Any] = defaultdict(list, initial_data)
    return context


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

    context = build_comparison_context(
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
