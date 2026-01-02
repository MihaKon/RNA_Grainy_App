from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.coarse_grain.models import CoarseGrainModelRegistry
from app.settings import TEMPLATES
from app.utils import get_model_info

router = APIRouter(prefix="/documentation", tags=["documentation"])

@router.get("/", response_class=HTMLResponse)
async def documentation_page(request: Request):
    models_data = []
    for model_name in CoarseGrainModelRegistry._registry.keys():
        model_info = get_model_info(model_name)
        models_data.append(model_info)

    models_data.sort(key=lambda x: x["beads_per_residue"])
    
    return TEMPLATES.TemplateResponse(
        request=request,
        name="documentation.html",
        context={
            "models": models_data}
    )