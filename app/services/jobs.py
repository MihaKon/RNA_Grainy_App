import asyncio
import shutil
import uuid
import logging
import time
from pathlib import Path

from app.exceptions import FileProcessingError, InvalidRequestError
from app.settings import (
    TEMP_DIR,
    JOB_MAX_LIFE_TIME,
    MIN_FREE_DISK_SIZE,
    JOB_STORAGE_MAX_SIZE,
)

logger = logging.getLogger(__name__)


class JobManager:
    @staticmethod
    def get_directory_size(directory: Path) -> int:
        total_size = 0

        for file_path in directory.iterdir():
            if file_path.is_symlink():
                continue

            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size

    @staticmethod
    def check_path(job_dir: Path) -> None:
        if not job_dir.resolve().is_relative_to(TEMP_DIR.resolve()):
            raise InvalidRequestError("Invalid job directory path.")

    @staticmethod
    def create_job_id() -> str:
        return str(uuid.uuid4())

    @classmethod
    def get_job_dir(cls, job_id: str) -> Path:
        try:
            uuid.UUID(job_id)
        except ValueError:
            raise InvalidRequestError("Invalid job ID format.")

        job_dir = TEMP_DIR / job_id

        cls.check_path(job_dir)
        return job_dir

    @classmethod
    def setup_job_dir(cls, job_id: str) -> Path:
        job_dir = cls.get_job_dir(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    @classmethod
    def reconstruct_file_path(cls, job_id: str, filename: str) -> Path:
        job_dir = cls.get_job_dir(job_id)
        file_path = job_dir / filename
        return file_path

    @classmethod
    async def create_file(cls, job_id: str, content: str, filename: str) -> Path:
        required_size = len(content.encode("utf-8"))
        disk = shutil.disk_usage(TEMP_DIR)

        if disk.free < MIN_FREE_DISK_SIZE + required_size:
            await asyncio.to_thread(cls.cleanup_expired_jobs)
            disk = shutil.disk_usage(TEMP_DIR)

        if disk.free < MIN_FREE_DISK_SIZE + required_size:
            raise FileProcessingError(
                "The server temporarily does not have enough disk space."
            )

        file_path = cls.reconstruct_file_path(job_id, filename)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except OSError as e:
            raise FileProcessingError(f"Error creating file: {e}")

        return file_path

    @classmethod
    def get_file_path(cls, job_id: str, filename: str) -> Path:
        file_path = cls.reconstruct_file_path(job_id, filename)

        if not file_path.is_file():
            raise FileProcessingError("Requested file does not exist.")

        cls.check_path(file_path)
        return file_path

    @classmethod
    def cleanup_job(cls, job_id: str) -> None:
        job_dir = cls.get_job_dir(job_id)
        try:
            shutil.rmtree(job_dir)
        except FileNotFoundError:
            pass

    @classmethod
    def cleanup_jobs_due_to_storage_limit(
        cls, active_jobs: list[tuple[float, int, Path]]
    ) -> int:
        removed_jobs = 0
        total_size = sum(job_size for _, job_size, _ in active_jobs)
        active_jobs.sort(key=lambda job: job[0])

        for _, job_size, job_dir in active_jobs:
            if total_size <= JOB_STORAGE_MAX_SIZE:
                break
            try:
                shutil.rmtree(job_dir)
                total_size -= job_size
                removed_jobs += 1

                logger.info(
                    "Removed job %s because storage limit was exceeded.",
                    job_dir.name,
                )
            except FileNotFoundError:
                total_size -= job_size
            except OSError:
                logger.warning(
                    "Could not remove temporary job %s.",
                    job_dir.name,
                    exc_info=True,
                )

        if total_size > JOB_STORAGE_MAX_SIZE:
            logger.warning(
                "Temporary job storage still exceeds the limit: "
                "%d bytes used, %d bytes allowed.",
                total_size,
                JOB_STORAGE_MAX_SIZE,
            )

        return removed_jobs

    @classmethod
    def cleanup_expired_jobs(cls) -> int:
        now = time.time()
        removed_jobs = 0
        active_jobs: list[tuple[float, int, Path]] = []

        try:
            job_dirs = list(TEMP_DIR.iterdir())
        except OSError:
            logger.exception("Could not scan temporary jobs directory.")
            return removed_jobs

        for job_dir in job_dirs:
            try:
                is_job = str(uuid.UUID(job_dir.name)) == job_dir.name
            except ValueError:
                is_job = False

            if not is_job:
                continue

            try:
                if job_dir.is_symlink() or not job_dir.is_dir():
                    continue
                job_modification_time = job_dir.stat().st_mtime
                age = now - job_modification_time
                job_size = cls.get_directory_size(job_dir)

                if age >= JOB_MAX_LIFE_TIME:
                    shutil.rmtree(job_dir)
                    removed_jobs += 1
                    continue

                active_jobs.append((job_modification_time, job_size, job_dir))
            except FileNotFoundError:
                continue
            except OSError:
                logger.warning(
                    "Could not inspect or remove temporary job %s.",
                    job_dir.name,
                    exc_info=True,
                )

        removed_jobs += cls.cleanup_jobs_due_to_storage_limit(active_jobs)

        if removed_jobs:
            logger.info("Removed %d temporary jobs.", removed_jobs)

        return removed_jobs
