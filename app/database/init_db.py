import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.database.session import engine

logger = logging.getLogger(__name__)


def init_db() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    alembic_ini = repo_root / "alembic.ini"

    cfg = Config(str(alembic_ini))

    # If the database has no alembic version table, treat it as fresh/unmanaged.
    # This makes startup resilient even if the file DB exists without migration metadata.
    with engine.begin() as conn:
        inspector = inspect(conn)
        tables = set(inspector.get_table_names())

    if "alembic_version" not in tables:
        try:
            command.upgrade(cfg, "head")
        except Exception:
            # Prefer stamping over crashing on first run.
            logger.exception("Alembic upgrade failed on unmanaged DB; stamping head.")
            command.stamp(cfg, "head")
        return

    command.upgrade(cfg, "head")