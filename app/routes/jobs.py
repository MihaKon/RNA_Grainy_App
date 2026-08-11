from fastapi import APIRouter, Query, status
from fastapi.responses import FileResponse, Response

from app.exceptions import InvalidRequestError
from app.models.form import SupportedFormats
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


@router.post(
    "/{job_id}/consumed",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def mark_job_as_consumed(job_id: str) -> Response:
    JobManager.cleanup_job(job_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
