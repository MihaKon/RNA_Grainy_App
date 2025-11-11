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

from .services import fetch_rcsb_file, RCSBNotFoundError, RCSBServiceError

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

async def process_structure(request: Request, file_content: str, filename: str, file_format: str, selected_model: str) -> HTMLResponse:
    try:
        file_like = StringIO(file_content)

        parser = FORMAT_PARSERS[SupportedFormats(file_format)](QUIET=True)

        original_structure: Structure = parser.get_structure(filename, file_like)
        coarse_file = transform_to_coarse_grain(
            original_structure, getattr(CoarseGrainModels, selected_model.upper())
        )

        f = StringIO(coarse_file.getvalue())
        parser = PDBParser(QUIET=True)
        coarse_structure = parser.get_structure(filename, f)

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



@app.post("/upload-file/")
async def upload_file(
    request: Request, file: UploadFile | None = File(None), selected_model: str = Form(...)) -> HTMLResponse:
    #TODO: Extend error handling
    if not file or not file.filename:
        return render_error_response(request, f"No file provided", 400)
    
    file_format = file.filename.split(".")[-1].lower()
    if file_format not in SupportedFormats:
        return render_error_response(request, f"File format '{file_format}' is not supported.", 415)
    
    try:
        file_content = (await file.read()).decode("utf-8")
    except Exception as e:
        return render_error_response(request, f"Error reading file: {e}", 400)

    return await process_structure(
        request = request,
        file_content = file_content,
        filename = file.filename,
        file_format = file_format,
        selected_model = selected_model
    )     
        

@app.post("/fetch-rcsb")
async def fetch_rcsb(
    request: Request, rcsb_id: str | None = Form(None), selected_model: str = Form(...)) -> HTMLResponse:
    if not rcsb_id:
        return render_error_response(request, f"No structure ID provided", 400)
    
    try:
        file_content = await fetch_rcsb_file(rcsb_id)
        
        file_format = SupportedFormats.CIF.value
        filename = f"{rcsb_id.strip().upper()}.{file_format}"

        return await process_structure(
            request = request,
            file_content = file_content,
            filename = filename,
            file_format = file_format,
            selected_model = selected_model
        )
    except RCSBServiceError as e:
        return render_error_response(request, f"Internal server error: {e}", 500)
    except RCSBNotFoundError as e:
        return render_error_response(request, f"{e}", 404)

    
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=5050)
