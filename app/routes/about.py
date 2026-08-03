from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.settings import TEMPLATES

router = APIRouter(prefix="/about", tags=["about"])


@router.get("/", response_class=HTMLResponse)
async def about_page(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(request=request, name="about.html")
