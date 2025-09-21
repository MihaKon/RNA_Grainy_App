import pathlib
from enum import Enum
from io import StringIO
from typing import Any

import uvicorn
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB.Structure import Structure
from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = pathlib.Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES = Jinja2Templates(directory=TEMPLATES_DIR)


class SupportedFormats(Enum):
    PDB = "pdb"
    CIF = "cif"


app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.add_middleware(GZipMiddleware)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "supported_file_formats": [
                file_format.value for file_format in SupportedFormats
            ]
        },
    )


@app.post("/uploadfile/")
async def upload_file(file: UploadFile) -> dict[str, Any]:
    file_format = ""
    if file.filename is not None:
        file_format = file.filename.split(".")[-1]
    if file_format not in SupportedFormats:
        raise HTTPException(status_code=415, detail="File format not supported")
    if file_format == SupportedFormats.PDB.value:
        content = await file.read()
        file_like = StringIO(content.decode("utf-8"))
        structure: Structure = PDBParser(QUIET=True).get_structure(  # type: ignore
            file.filename, file_like
        )
        chains = set([chain.id for model in structure for chain in model])  # type: ignore
        return {"chains": chains}
    return {"filename": file.filename}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5050)
