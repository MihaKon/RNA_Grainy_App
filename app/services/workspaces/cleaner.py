import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from app.services.workspaces.paths import is_valid_uuid
from app.settings import (
    WORKSPACE_STORAGE_DIR,
    WORKSPACE_MAX_LIFETIME,
    WORKSPACE_STORAGE_MAX_SIZE,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkspaceSnapshot:
    path: Path
    modified_at: float
    size: int


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
                    workspace_modification_time = workspace_dir.stat().st_mtime
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
    def _remove_expired_workspaces(
        cls, workspaces: list[WorkspaceSnapshot]
    ) -> tuple[list[WorkspaceSnapshot], int]:
        now = time.time()
        removed_workspaces_count = 0
        remaining_workspaces: list[WorkspaceSnapshot] = []
        for workspace in workspaces:
            try:
                age = now - workspace.modified_at
                if age >= WORKSPACE_MAX_LIFETIME:
                    shutil.rmtree(workspace.path)
                    removed_workspaces_count += 1
                    continue
                remaining_workspaces.append(workspace)
            except FileNotFoundError:
                continue
            except OSError:
                logger.warning(
                    "Could not remove expired workspace %s.",
                    workspace.path.name,
                    exc_info=True,
                )
                remaining_workspaces.append(workspace)

        return remaining_workspaces, removed_workspaces_count

    @classmethod
    def _remove_workspaces_over_storage_limit(
        cls, workspaces: list[WorkspaceSnapshot]
    ) -> int:
        removed_workspaces_count = 0

        total_size = sum(workspace.size for workspace in workspaces)
        oldest_workspaces = sorted(
            workspaces, key=lambda workspace: workspace.modified_at
        )

        for workspace in oldest_workspaces:
            if total_size <= WORKSPACE_STORAGE_MAX_SIZE:
                break
            try:
                shutil.rmtree(workspace.path)
                total_size -= workspace.size
                removed_workspaces_count += 1

                logger.info(
                    "Removed workspace %s because storage limit was exceeded.",
                    workspace.path.name,
                )
            except FileNotFoundError:
                total_size -= workspace.size
            except OSError:
                logger.warning(
                    "Could not remove workspace %s.",
                    workspace.path.name,
                    exc_info=True,
                )

        if total_size > WORKSPACE_STORAGE_MAX_SIZE:
            logger.warning(
                "Workspace storage still exceeds the limit: %d bytes used, %d bytes allowed.",
                total_size,
                WORKSPACE_STORAGE_MAX_SIZE,
            )

        return removed_workspaces_count

    @classmethod
    def cleanup_workspaces(cls) -> int:
        """Remove expired workspaces and enforce the storage size limit."""
        workspaces = cls._scan_workspaces()
        remaining_workspaces, expired_count = cls._remove_expired_workspaces(workspaces)
        storage_count = cls._remove_workspaces_over_storage_limit(remaining_workspaces)

        removed_count = expired_count + storage_count

        if removed_count:
            logger.info("Removed %d workspaces.", removed_count)

        return removed_count
