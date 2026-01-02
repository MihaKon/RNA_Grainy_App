import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.coarse_grain.models import CoarseGrainModelRegistry
from app.messages import render_form_error_message
from app.models import SupportedFormats
from app.routes import jobs, upload
from app.settings import STATIC_DIR, TEMPLATES

async def app_exception_handler(request: Request, exc: Exception):
    error_message = str(exc)

    return render_form_error_message(
        request=request,
        error=error_message,
        status_code=400
    )

app = FastAPI(title="RNA Coarse Grain App", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.add_middleware(GZipMiddleware)
app.include_router(upload.router)
app.include_router(jobs.router)
app.add_exception_handler(Exception, app_exception_handler)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(
        request=request,
        name="upload_form.html",
        context={
            "supported_file_formats": [
                file_format.value for file_format in SupportedFormats
            ],
            "coarse_grain_models": CoarseGrainModelRegistry.get_dropdown_options(),
        },
    )


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=5050, reload=True)
