import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.coarse_grain.models import CoarseGrainModels
from app.models import SupportedFormats
from app.routes.upload import router as upload_router
from app.settings import STATIC_DIR, TEMPLATES

app = FastAPI(title="RNA Coarse Grain App", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.add_middleware(GZipMiddleware)
app.include_router(upload_router)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(
        request=request,
        name="upload_form.html",
        context={
            "supported_file_formats": [
                file_format.value for file_format in SupportedFormats
            ],
            "coarse_grain_models": [model.name.title() for model in CoarseGrainModels],
        },
    )


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=5050, reload=True)
