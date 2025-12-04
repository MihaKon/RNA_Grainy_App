from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from app.services.job_service import JobManager

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.get("/{job_id}/{file_type}")
async def get_job_file(
    job_id: str,
    file_type: str,
    ext: str = Query("pdb", pattern="^[a-zA-Z0-9]+$")
):
    if file_type not in ["reference", "coarse"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    filename = f"{file_type}.{ext}" if file_type == "reference" else "coarse.pdb"
    file_path = JobManager.get_file_path(job_id, filename)

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="text/plain"
    )