import logging
import signal
import threading
from types import FrameType

from app.services.jobs.cleaner import JobCleaner
from app.settings import JOB_CLEANUP_INTERVAL

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

    logger.info("Job cleaner started.")

    while not stop_event.is_set():
        try:
            JobCleaner.cleanup_jobs()
        except Exception:
            logger.exception("Unexpected error during job cleanup.")

        stop_event.wait(JOB_CLEANUP_INTERVAL)

    logger.info("Job cleaner stopped.")


if __name__ == "__main__":
    main()
