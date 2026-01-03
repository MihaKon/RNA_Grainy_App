from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.settings import TEMPLATES
from app.services.model_service import ModelService

router = APIRouter(prefix="/documentation", tags=["documentation"])

@router.get("/", response_class=HTMLResponse)
async def documentation_page(request: Request):
    models_data = ModelService.get_all_models() 

    return TEMPLATES.TemplateResponse(
        request=request,
        name="documentation.html",
        context={"models": models_data}
    )