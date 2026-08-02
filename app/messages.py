from fastapi import Request
from fastapi.responses import HTMLResponse

from app.settings import TEMPLATES


def render_form_error_message(request: Request, error: str, status_code: int) -> HTMLResponse:
    context = {"error": error}
    return TEMPLATES.TemplateResponse(
        request=request,
        name="components/error_alert.html",
        context=context,
        status_code=status_code,
    )
