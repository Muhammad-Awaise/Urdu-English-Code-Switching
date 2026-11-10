"""Ensure backend package imports work and the SQLite DB is ready."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

_initialized = False


def ensure_backend_path() -> Path:
    backend = str(BACKEND)
    if backend not in sys.path:
        sys.path.insert(0, backend)
    return BACKEND


def init_app() -> bool:
    """One-time app bootstrap for the Streamlit process lifetime."""
    global _initialized
    if _initialized:
        return True

    ensure_backend_path()
    from app.core.config import ensure_directories
    from app.core.database import Base, SessionLocal, engine
    from app.services.seed import seed_if_empty

    ensure_directories()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
        from app.core.runtime_settings import refresh_runtime_overrides

        refresh_runtime_overrides(db)
    finally:
        db.close()
    _initialized = True
    return True


def get_db_session():
    ensure_backend_path()
    init_app()
    from app.core.database import SessionLocal

    return SessionLocal()
