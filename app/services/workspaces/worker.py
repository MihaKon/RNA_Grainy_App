import logging
import signal
import threading
from types import FrameType

from app.services.workspaces.cleaner import WorkspaceCleaner
from app.settings import WORKSPACE_CLEANUP_INTERVAL

logger = logging.getLogger(__name__)
stop_event = threading.Event()


def request_shutdown(_signum: int, _frame: FrameType | None) -> None:
    stop_event.set()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)

    logger.info("Workspace cleaner started.")

    while not stop_event.is_set():
        try:
            WorkspaceCleaner.cleanup_workspaces()
        except Exception:
            logger.exception("Unexpected error during workspace cleanup.")

        stop_event.wait(WORKSPACE_CLEANUP_INTERVAL)

    logger.info("Workspace cleaner stopped.")


if __name__ == "__main__":
    main()
