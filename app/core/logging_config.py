import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import APP_ENV, DATA_DIR


def setup_logging() -> None:
    logs_dir = Path(DATA_DIR) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_level = logging.DEBUG if APP_ENV == "development" else logging.INFO
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        file_handler = RotatingFileHandler(
            logs_dir / "app.log",
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)
