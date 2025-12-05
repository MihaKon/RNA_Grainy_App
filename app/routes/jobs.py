from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.services.job_service import JobManager
from app.models import SupportedFormats, COARSE_FILE_FORMAT

FILE_TYPES = ["reference", "coarse"]

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.get("/{job_id}/{file_type}")
async def get_job_file(
    job_id: str,
    file_type: str,
    file_format: str
) -> FileResponse:
    if file_type not in FILE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type")
    if file_format not in (SupportedFormats.PDB.value, SupportedFormats.MMCIF.value):
        raise HTTPException(status_code=400, detail="Invalid file format")
    filename = f"{file_type}.{file_format}" if file_type == "reference" else f"coarse.{COARSE_FILE_FORMAT.value}"
    file_path = JobManager.get_file_path(job_id, filename)

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="text/plain"
    )