from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from soccer_analytics.config import get_settings
from soccer_analytics.storage.models import Base


settings = get_settings()
engine_kwargs = {"future": True}
if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    sqlite_target = settings.database_url.removeprefix("sqlite:///")
    if sqlite_target and sqlite_target != ":memory:":
        sqlite_path = Path(sqlite_target)
        if not sqlite_path.is_absolute():
            sqlite_path = Path.cwd() / sqlite_path
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        settings.database_url = f"sqlite:///{sqlite_path.as_posix()}"

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
