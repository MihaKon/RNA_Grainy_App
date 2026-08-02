import asyncio
import logging
import shutil
import uuid
from pathlib import Path

from app.exceptions import FileProcessingError
from app.settings import (
    MIN_FREE_DISK_SIZE,
    JOB_STORAGE_DIR,
)

from .paths import get_job_dir, get_job_file_path

logger = logging.getLogger(__name__)


class JobManager:
    @staticmethod
    def create_job_id() -> str:
        return str(uuid.uuid4())

    @classmethod
    def setup_job_dir(cls, job_id: str) -> Path:
        job_dir = get_job_dir(job_id)
        try:
            job_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.warning(
                "Could not create job directory %s.",
                job_dir,
                exc_info=True,
            )
            raise FileProcessingError(
                "The server could not prepare job storage."
            ) from exc
        return job_dir

    @staticmethod
    def _get_free_disk_size() -> int:
        try:
            return shutil.disk_usage(JOB_STORAGE_DIR).free
        except OSError as exc:
            logger.warning(
                "Could not check available disk space.",
                exc_info=True,
            )
            raise FileProcessingError(
                "The server could not access job storage."
            ) from exc

    @classmethod
    async def create_file(cls, job_id: str, content: str, filename: str) -> Path:
        required_size = len(content.encode("utf-8"))
        free_disk_size = cls._get_free_disk_size()

        if free_disk_size < MIN_FREE_DISK_SIZE + required_size:
            raise FileProcessingError(
                "The server temporarily does not have enough disk space."
            )

        file_path = get_job_file_path(job_id, filename)
        try:
            await asyncio.to_thread(
                file_path.write_text,
                content,
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning(
                "Could not create job file %s.",
                file_path,
                exc_info=True,
            )
            raise FileProcessingError(
                "The server could not create the requested file."
            ) from exc

        return file_path

    @classmethod
    def get_file_path(cls, job_id: str, filename: str) -> Path:
        file_path = get_job_file_path(job_id, filename)

        if not file_path.is_file():
            raise FileProcessingError("Requested file does not exist.")

        return file_path

    @classmethod
    def cleanup_job(cls, job_id: str) -> None:
        job_dir = get_job_dir(job_id)

        try:
            shutil.rmtree(job_dir)
        except FileNotFoundError:
            pass
        except OSError:
            logger.warning(
                "Could not remove job %s.",
                job_id,
                exc_info=True,
            )
