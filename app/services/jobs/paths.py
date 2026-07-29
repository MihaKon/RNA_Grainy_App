import uuid
from pathlib import Path

from app.exceptions import FileProcessingError, InvalidRequestError
from app.settings import TEMP_DIR


def is_valid_uuid(job_id: str) -> bool:
    try:
        return str(uuid.UUID(job_id)) == job_id
    except ValueError:
        return False


def validate_uuid(job_id: str) -> None:
    if not is_valid_uuid(job_id):
        raise InvalidRequestError("Invalid job ID format.")


def check_path(path: Path, parent_path: Path) -> None:
    if not path.resolve().is_relative_to(parent_path.resolve()):
        raise InvalidRequestError("Invalid path.")


def get_job_dir(job_id: str) -> Path:
    validate_uuid(job_id)

    job_dir = TEMP_DIR / job_id

    check_path(job_dir, TEMP_DIR)
    return job_dir


def get_job_file_path(job_id: str, filename: str) -> Path:
    job_dir = get_job_dir(job_id)
    file_path = job_dir / filename
    check_path(file_path, job_dir)
    return file_path
