import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import asyncio
from contextlib import asynccontextmanager
from app.services.jobs import JobManager
import logging
from collections.abc import AsyncGenerator

from app.coarse_grain.models import CoarseGrainModelRegistry
from app.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
)
from app.models.form import SupportedFormats
from app.routes import docs, jobs, uploads
from app.settings import STATIC_DIR, TEMPLATES, JOB_CLEANUP_INTERVAL

logger = logging.getLogger(__name__)


async def cleanup_jobs_periodically() -> None:
    while True:
        await asyncio.sleep(JOB_CLEANUP_INTERVAL)
        try:
            await asyncio.to_thread(JobManager.cleanup_expired_jobs)
        except Exception:
            logger.exception("Unexpected error during expired job cleanup.")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await asyncio.to_thread(JobManager.cleanup_expired_jobs)
    cleanup_task = asyncio.create_task(cleanup_jobs_periodically())

    try:
        yield
    finally:
        cleanup_task.cancel()

        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="RNA Coarse Grain App", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.add_middleware(GZipMiddleware)
app.include_router(docs.router)
app.include_router(uploads.router)
app.include_router(jobs.router)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)


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
