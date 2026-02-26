"""CLI entrypoint for content sync.

Run as:  python -m app.content.sync

All orchestration logic lives in ``services.content_sync``. This module
exists solely to provide the ``python -m`` entrypoint for ``prestart.sh``.
"""

from __future__ import annotations

from pathlib import Path

import structlog
from sqlmodel import Session

from app.core.config import settings
from app.core.db import engine
from app.core.logging import setup_logging
from app.services.content_sync import sync_content

logger = structlog.stdlib.get_logger(__name__)


def main() -> None:
    setup_logging(log_level="INFO", json_output=False)

    content_path = Path(settings.CONTENT_DIR)
    if not content_path.is_absolute():
        content_path = Path(__file__).resolve().parents[3] / content_path

    logger.info("content_sync_starting", content_dir=str(content_path))

    with Session(engine) as session:
        sync_content(session=session, content_dir=content_path)

    logger.info("content_sync_finished")


if __name__ == "__main__":
    main()
