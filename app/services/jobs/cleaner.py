import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from app.services.jobs.paths import is_valid_uuid
from app.settings import (
    JOB_MAX_LIFETIME,
    JOB_STORAGE_MAX_SIZE,
    JOB_STORAGE_DIR,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JobSnapshot:
    path: Path
    modified_at: float
    size: int


class JobCleaner:
    @staticmethod
    def get_directory_size(directory: Path) -> int:
        total_size = 0

        for file_path in directory.iterdir():
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size

    @classmethod
    def _scan_jobs(cls) -> list[JobSnapshot]:
        jobs: list[JobSnapshot] = []
        try:
            for job_dir in JOB_STORAGE_DIR.iterdir():
                if not is_valid_uuid(job_dir.name):
                    continue

                try:
                    if not job_dir.is_dir():
                        continue
                    job_modification_time = job_dir.stat().st_mtime
                    job_size = cls.get_directory_size(job_dir)

                    jobs.append(
                        JobSnapshot(
                            path=job_dir,
                            modified_at=job_modification_time,
                            size=job_size,
                        )
                    )
                except FileNotFoundError:
                    logger.debug(
                        "Job %s already removed.",
                        job_dir.name,
                    )
                    continue

                except OSError:
                    logger.warning(
                        "Could not inspect job %s.",
                        job_dir.name,
                        exc_info=True,
                    )

        except OSError:
            logger.exception("Could not scan job storage directory.")

        return jobs

    @classmethod
    def _remove_expired_jobs(
        cls, jobs: list[JobSnapshot]
    ) -> tuple[list[JobSnapshot], int]:
        now = time.time()
        removed_jobs_count = 0
        remaining_jobs: list[JobSnapshot] = []
        for job in jobs:
            try:
                age = now - job.modified_at
                if age >= JOB_MAX_LIFETIME:
                    shutil.rmtree(job.path)
                    removed_jobs_count += 1
                    continue
                remaining_jobs.append(job)
            except FileNotFoundError:
                continue
            except OSError:
                logger.warning(
                    "Could not remove expired job %s.",
                    job.path.name,
                    exc_info=True,
                )
                remaining_jobs.append(job)

        return remaining_jobs, removed_jobs_count

    @classmethod
    def _remove_jobs_over_storage_limit(cls, jobs: list[JobSnapshot]) -> int:
        removed_jobs_count = 0

        total_size = sum(job.size for job in jobs)
        oldest_jobs = sorted(jobs, key=lambda job: job.modified_at)

        for job in oldest_jobs:
            if total_size <= JOB_STORAGE_MAX_SIZE:
                break
            try:
                shutil.rmtree(job.path)
                total_size -= job.size
                removed_jobs_count += 1

                logger.info(
                    "Removed job %s because storage limit was exceeded.",
                    job.path.name,
                )
            except FileNotFoundError:
                total_size -= job.size
            except OSError:
                logger.warning(
                    "Could not remove job %s.",
                    job.path.name,
                    exc_info=True,
                )

        if total_size > JOB_STORAGE_MAX_SIZE:
            logger.warning(
                "Job storage still exceeds the limit: %d bytes used, %d bytes allowed.",
                total_size,
                JOB_STORAGE_MAX_SIZE,
            )

        return removed_jobs_count

    @classmethod
    def cleanup_jobs(cls) -> int:
        """Remove expired jobs and enforce the storage size limit."""
        jobs = cls._scan_jobs()
        remaining_jobs, expired_count = cls._remove_expired_jobs(jobs)
        storage_count = cls._remove_jobs_over_storage_limit(remaining_jobs)

        removed_count = expired_count + storage_count

        if removed_count:
            logger.info("Removed %d jobs.", removed_count)

        return removed_count
