import enum
from collections import defaultdict
from io import StringIO
from typing import Any

import uvicorn
from Bio.PDB.MMCIFParser import MMCIFParser
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB.Structure import Structure
from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.coarse_modeler import CoarseGrainModels, transform_to_coarse_grain
from app.settings import STATIC_DIR, TEMPLATES


class SupportedFormats(enum.Enum):
    PDB = "pdb"
    CIF = "cif"


FORMAT_PARSERS = {
    SupportedFormats.PDB: PDBParser,
    SupportedFormats.CIF: MMCIFParser,
}


app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.add_middleware(GZipMiddleware)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(
        request=request,
        name="file_upload.html",
        context={
            "supported_file_formats": [
                file_format.value for file_format in SupportedFormats
            ],
            "coarse_grain_models": [model.name.title() for model in CoarseGrainModels],
        },
    )


@app.post("/uploadfile/")
async def upload_file(
    request: Request, file: UploadFile, selected_model: str = Form(...)
) -> HTMLResponse:
    file_format = "" if file.filename is None else file.filename.split(".")[-1]
    if file_format not in SupportedFormats:
        raise HTTPException(status_code=415, detail="File format not supported")
    content = await file.read()
    file_like = StringIO(content.decode("utf-8"))
    parser = FORMAT_PARSERS[SupportedFormats(file_format)](QUIET=True)
    original_structure: Structure = parser.get_structure(file.filename, file_like)
    coarse_file = transform_to_coarse_grain(
        original_structure, getattr(CoarseGrainModels, selected_model.upper())
    )
    f = StringIO(coarse_file.getvalue())
    parser = PDBParser(QUIET=True)
    coarse_structure = parser.get_structure(file.filename, f)
    if file_format == SupportedFormats.CIF.value:
        file_format = "mmcif"
    initial_data = {
        "filename": file.filename,
        "file_format": [file_format, "pdb"],
        "file_data": [
            file_like.getvalue(),
            coarse_file.getvalue(),
        ],
        "selected_model": selected_model,
    }
    context: defaultdict[str, str | list[Any] | None] = defaultdict(list, initial_data)

    # Temporary placeholder for all the data
    # TODO: when discusiing what data to export we will refactor it
    # to separate functions
    entity_keys = ["atoms", "chains", "models", "residues"]
    for structure in [original_structure, coarse_structure]:
        for key in entity_keys:
            method_to_call = getattr(structure, f"get_{key}")
            count = sum(1 for _ in method_to_call())
            context[key].append(count)  # type: ignore
    return TEMPLATES.TemplateResponse(
        request=request,
        name="comparison.html",
        context=context,
    )


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=5050)
