from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.exceptions import InvalidRequestError
from app.models import SupportedFormats
from app.services.jobs import JobManager

FILE_TYPES = ["reference", "coarse"]

router = APIRouter(prefix="/api/job", tags=["job"])


@router.get("/{job_id}/{file_type}")
async def get_job_file(
    job_id: str, file_type: str, file_format: str = Query(...)
) -> FileResponse:
    if file_type not in FILE_TYPES:
        raise InvalidRequestError("Invalid file type requested.")

    if file_format not in (SupportedFormats.PDB.value, SupportedFormats.MMCIF.value):
        raise InvalidRequestError("Invalid file format requested.")

    if file_type == "reference":
        filename = f"reference.{file_format}"
    else:
        filename = f"coarse.{file_format}"

    file_path = JobManager.get_file_path(job_id, filename)

    return FileResponse(path=file_path, media_type="application/octet-stream")
