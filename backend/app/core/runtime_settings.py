"""Runtime overrides for CS policy / split / seed (stored in ApplicationSetting)."""

from __future__ import annotations

from typing import Any

from app.core.config import settings

RUNTIME_KEY = "runtime_config"
_overrides: dict[str, Any] | None = None


def _defaults() -> dict[str, Any]:
    return {
        "cs_min_tokens_per_language": settings.cs_min_tokens_per_language,
        "cs_min_confidence": settings.cs_min_confidence,
        "default_train_ratio": settings.default_train_ratio,
        "default_val_ratio": settings.default_val_ratio,
        "default_test_ratio": settings.default_test_ratio,
        "random_seed": settings.random_seed,
    }


def refresh_runtime_overrides(db=None) -> dict[str, Any]:
    """Load overrides from DB into process memory. Safe to call often."""
    global _overrides
    merged = _defaults()
    try:
        if db is None:
            from app.core.database import SessionLocal

            db_local = SessionLocal()
            close = True
        else:
            db_local = db
            close = False
        try:
            from app.models.orm import ApplicationSetting

            row = (
                db_local.query(ApplicationSetting)
                .filter(ApplicationSetting.key == RUNTIME_KEY)
                .first()
            )
            if row and isinstance(row.value, dict):
                for k, v in row.value.items():
                    if k in merged and v is not None:
                        merged[k] = v
        finally:
            if close:
                db_local.close()
    except Exception:
        # During early import / tests without DB, fall back to defaults
        pass
    _overrides = merged
    return dict(merged)


def get_runtime() -> dict[str, Any]:
    global _overrides
    if _overrides is None:
        return refresh_runtime_overrides()
    return dict(_overrides)


def cs_min_confidence() -> float:
    return float(get_runtime().get("cs_min_confidence", settings.cs_min_confidence))


def cs_min_tokens_per_language() -> int:
    return int(get_runtime().get("cs_min_tokens_per_language", settings.cs_min_tokens_per_language))


def default_split() -> dict[str, float]:
    r = get_runtime()
    return {
        "train": float(r.get("default_train_ratio", settings.default_train_ratio)),
        "val": float(r.get("default_val_ratio", settings.default_val_ratio)),
        "test": float(r.get("default_test_ratio", settings.default_test_ratio)),
    }


def random_seed() -> int:
    return int(get_runtime().get("random_seed", settings.random_seed))


def save_runtime_overrides(db, values: dict[str, Any]) -> dict[str, Any]:
    """Persist overrides and refresh process cache."""
    from datetime import datetime

    from app.models.orm import ApplicationSetting

    global _overrides
    current = _defaults()
    # merge existing stored
    row = db.query(ApplicationSetting).filter(ApplicationSetting.key == RUNTIME_KEY).first()
    if row and isinstance(row.value, dict):
        current.update({k: v for k, v in row.value.items() if k in current})

    allowed = set(_defaults().keys())
    for k, v in values.items():
        if k in allowed and v is not None:
            current[k] = v

    # normalize types
    current["cs_min_tokens_per_language"] = int(current["cs_min_tokens_per_language"])
    current["cs_min_confidence"] = float(current["cs_min_confidence"])
    current["default_train_ratio"] = float(current["default_train_ratio"])
    current["default_val_ratio"] = float(current["default_val_ratio"])
    current["default_test_ratio"] = float(current["default_test_ratio"])
    current["random_seed"] = int(current["random_seed"])

    if not row:
        row = ApplicationSetting(key=RUNTIME_KEY, value=current)
        db.add(row)
    else:
        row.value = current
        row.updated_at = datetime.utcnow()
    db.commit()
    _overrides = dict(current)
    return dict(current)
