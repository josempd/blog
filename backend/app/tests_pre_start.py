import logging

import structlog
from sqlalchemy import Engine
from sqlmodel import Session, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.db import engine
from app.core.logging import setup_logging

setup_logging(log_level="INFO", json_output=False)
logger = structlog.stdlib.get_logger(__name__)
# stdlib logger needed for tenacity callbacks
_stdlib_logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(_stdlib_logger, 20),  # INFO = 20
    after=after_log(_stdlib_logger, 30),  # WARNING = 30
)
def init(db_engine: Engine) -> None:
    try:
        # Try to create session to check if DB is awake
        with Session(db_engine) as session:
            session.exec(select(1))
    except Exception as e:
        logger.error("db_not_ready", error=str(e))
        raise


def main() -> None:
    logger.info("initializing_service")
    init(engine)
    logger.info("service_initialized")


if __name__ == "__main__":
    main()
