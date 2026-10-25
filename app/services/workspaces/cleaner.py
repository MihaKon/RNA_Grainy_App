import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from app.services.workspaces.paths import is_valid_uuid
from app.settings import (
    WORKSPACE_MAX_LIFETIME,
    WORKSPACE_STORAGE_DIR,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkspaceSnapshot:
    path: Path
    modified_at: float
    size: int

    def is_expired(self, now: float) -> bool:
        return now - self.modified_at >= WORKSPACE_MAX_LIFETIME


class WorkspaceCleaner:
    @staticmethod
    def get_directory_size(directory: Path) -> int:
        total_size = 0

        for file_path in directory.iterdir():
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size

    @classmethod
    def _scan_workspaces(cls) -> list[WorkspaceSnapshot]:
        workspaces: list[WorkspaceSnapshot] = []
        try:
            for workspace_dir in WORKSPACE_STORAGE_DIR.iterdir():
                if not is_valid_uuid(workspace_dir.name):
                    continue

                try:
                    if not workspace_dir.is_dir():
                        continue
                    metadata = workspace_dir / "result.json"
                    timestamp_path = metadata if metadata.is_file() else workspace_dir
                    workspace_modification_time = timestamp_path.stat().st_mtime
                    workspace_size = cls.get_directory_size(workspace_dir)

                    workspaces.append(
                        WorkspaceSnapshot(
                            path=workspace_dir,
                            modified_at=workspace_modification_time,
                            size=workspace_size,
                        )
                    )
                except FileNotFoundError:
                    logger.debug(
                        "Workspace %s already removed.",
                        workspace_dir.name,
                    )
                    continue

                except OSError:
                    logger.warning(
                        "Could not inspect workspace %s.",
                        workspace_dir.name,
                        exc_info=True,
                    )

        except OSError:
            logger.exception("Could not scan workspace storage directory.")

        return workspaces

    @classmethod
    def _remove_expired_workspaces(cls, workspaces: list[WorkspaceSnapshot]) -> int:
        now = time.time()
        removed_workspaces_count = 0
        for workspace in workspaces:
            try:
                if workspace.is_expired(now):
                    shutil.rmtree(workspace.path)
                    removed_workspaces_count += 1
                    continue
            except FileNotFoundError:
                continue
            except OSError:
                logger.warning(
                    "Could not remove expired workspace %s.",
                    workspace.path.name,
                    exc_info=True,
                )

        return removed_workspaces_count

    @classmethod
    def get_storage_size(cls) -> int:
        return sum(workspace.size for workspace in cls._scan_workspaces())

    @classmethod
    def cleanup_workspaces(cls) -> int:
        """Remove only workspaces whose 24-hour lifetime has elapsed."""
        workspaces = cls._scan_workspaces()
        removed_count = cls._remove_expired_workspaces(workspaces)

        if removed_count:
            logger.info("Removed %d workspaces.", removed_count)

        return removed_count
