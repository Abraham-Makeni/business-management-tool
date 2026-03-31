import importlib

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def test_engine(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    # Reload config/session so they pick up DATABASE_URL
    import app.core.config as config
    importlib.reload(config)

    import app.database.session as session_mod
    importlib.reload(session_mod)

    # Rebind to an isolated engine
    engine = create_engine(
        config.DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )
    session_mod.engine = engine
    session_mod.SessionLocal.configure(bind=engine)

    # Create schema from metadata for unit tests
    from app.database.base import Base
    from app.database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    return engine


@pytest.fixture()
def db_session(test_engine):
    SessionTesting = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)
    with SessionTesting() as session:
        yield session
