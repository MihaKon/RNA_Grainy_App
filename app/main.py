import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from app.coarse_grain.models import CoarseGrainModelRegistry
from app.exceptions import (
    AppException,
    app_exception_handler,
    request_validation_exception_handler,
    validation_exception_handler,
)
from app.models.form import SupportedFormats
from app.routes import (
    about,
    coarse_grain,
    coarse_grain_models,
    config,
    docs,
    results,
    uploads,
)
from app.settings import APP_VERSION, STATIC_DIR, TEMPLATES

app = FastAPI(title="RNAgrainy", version=APP_VERSION)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.add_middleware(GZipMiddleware)
app.include_router(about.router)
app.include_router(docs.router)
app.include_router(uploads.router)
app.include_router(results.router)
app.include_router(config.router)
app.include_router(coarse_grain_models.router)
app.include_router(coarse_grain.router)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)


@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


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
