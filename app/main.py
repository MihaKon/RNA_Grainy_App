import enum
from collections import defaultdict
from io import StringIO
from typing import Any

import uvicorn
from Bio.PDB.MMCIFParser import MMCIFParser
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB.Structure import Structure
from fastapi import FastAPI, Form, HTTPException, Request, UploadFile, File
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from typing import Optional
from .services import fetch_rscb_content

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

def render_error_response(request: Request, error: str, status_code: int) -> HTMLResponse:
    context = {"error": error}

    return TEMPLATES.TemplateResponse(
        request=request,
        name="components/error_alert.html",
        context=context,
        status_code=status_code,
    )

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
    request: Request, file: Optional[UploadFile]=File(None), rscb_file: Optional[str] = Form(None), selected_model: str = Form(...)
) -> HTMLResponse:
    file_content: Optional[str] = None
    filename: Optional[str] = None
    file_format: str = ""
    try:
        if rscb_file:
            file_content = await fetch_rscb_content(rscb_file)
            if file_content is None:
                return render_error_response(request, f"PDB ID '{rscb_file}' not found.", 404)
            filename = f"{rscb_file.strip().upper()}.cif"
            file_format = "cif"

        elif file and file.filename:
            file_format = "" if file.filename is None else file.filename.split(".")[-1].lower()
            filename = file.filename
            file_content = (await file.read()).decode("utf-8")

        else:
            return render_error_response(request, "No file or PDB ID provided.", 400)        
        
        if file_format not in SupportedFormats:
            return render_error_response(request, f"File format '{file_format}' is not supported.", 415)
        file_like = StringIO(file_content)

        parser = FORMAT_PARSERS[SupportedFormats(file_format)](QUIET=True)

        original_structure: Structure = parser.get_structure(filename, file_like)
        coarse_file = transform_to_coarse_grain(
            original_structure, getattr(CoarseGrainModels, selected_model.upper())
        )

        f = StringIO(coarse_file.getvalue())
        parser = PDBParser(QUIET=True)
        coarse_structure = parser.get_structure(filename, f)

        if file_format == SupportedFormats.CIF.value:
            file_format = "mmcif"

        initial_data = {
            "filename": filename,
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

    except Exception as e:
        return render_error_response(request, f"Internal server error: {e}", 500)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=5050)
