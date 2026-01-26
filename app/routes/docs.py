from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.services.doc import DocsContextBuilder
from app.settings import TEMPLATES

router = APIRouter(prefix="/documentation", tags=["documentation"])


@router.get("/", response_class=HTMLResponse)
async def documentation_page(request: Request) -> HTMLResponse:
    models_data = DocsContextBuilder.get_all_models()

    return TEMPLATES.TemplateResponse(
        request=request, name="documentation.html", context={"models": models_data}
    )
