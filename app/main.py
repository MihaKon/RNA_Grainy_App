import pathlib
from enum import Enum
from io import StringIO

import uvicorn
from Bio.PDB.MMCIFParser import MMCIFParser
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB.Structure import Structure
from fastapi import FastAPI, HTTPException, Request, UploadFile, Form
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import coarse_modeler

BASE_DIR = pathlib.Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES = Jinja2Templates(directory=TEMPLATES_DIR)


class SupportedFormats(Enum):
    PDB = "pdb"
    CIF = "cif"


FORMAT_PARSERS = {SupportedFormats.PDB: PDBParser, SupportedFormats.CIF: MMCIFParser}


app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.add_middleware(GZipMiddleware)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    models = ["option1", "option2", "option3"]
    return TEMPLATES.TemplateResponse(
        request=request,
        name="file_upload.html",
        context={
            "supported_file_formats": [
                file_format.value for file_format in SupportedFormats
            ],
            "coarse_grain_models": models,
        },
    )


@app.post("/uploadfile/")
async def upload_file(request: Request, file: UploadFile, selected_model: str = Form(...)) -> HTMLResponse:
    file_format = "" if file.filename is None else file.filename.split(".")[-1]
    if file_format not in SupportedFormats:
        raise HTTPException(status_code=415, detail="File format not supported")
    content = await file.read()
    file_like = StringIO(content.decode("utf-8"))
    parser = FORMAT_PARSERS[SupportedFormats(file_format)]
    original_structure: Structure = parser(QUIET=True).get_structure(
        file.filename, file_like
    )

    # TODO: REMOVE
    if file_format == SupportedFormats.CIF.value:
        file_format = "mmcif"

    model = selected_model

    coarse_structure = coarse_modeler.transform_to_coarse_grain(original_structure)
    context: dict[str, str | list[int] | None] = {
        "filename": file.filename,
        "file_format": file_format,
        "file_data": file_like.getvalue(),
        "atoms": [],
        "models": [],
        "chains": [],
        "residues": [],        
        "selected_model": model,
        }
    # Temporary placeholder for all the data
    # TODO: when discusiing what data to export we will refactor it
    # to separate functions
    for structure in [original_structure, coarse_structure]:
        context["atoms"].append(sum(1 for _ in structure.get_atoms()))  # type: ignore
        context["chains"].append(sum(1 for _ in structure.get_chains()))  # type: ignore
        context["models"].append(sum(1 for _ in structure.get_models()))  # type: ignore
        context["residues"].append(sum(1 for _ in structure.get_residues()))  # type: ignore
    return TEMPLATES.TemplateResponse(
        request=request,
        name="comparison.html",
        context=context,
    )


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=5050)
