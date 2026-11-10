from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import SettingsUpdate
from app.core.config import settings
from app.core.database import get_db
from app.models.orm import ApplicationSetting

router = APIRouter()


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    rows = db.query(ApplicationSetting).all()
    stored = {r.key: r.value for r in rows}
    return {
        "app_name": settings.app_name,
        "database_url": settings.database_url,
        "cs_min_tokens_per_language": settings.cs_min_tokens_per_language,
        "cs_min_confidence": settings.cs_min_confidence,
        "default_split": {
            "train": settings.default_train_ratio,
            "val": settings.default_val_ratio,
            "test": settings.default_test_ratio,
        },
        "random_seed": settings.random_seed,
        "zero_paid_resources": True,
        "stored": stored,
    }


@router.put("/settings")
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db)):
    for key, value in payload.values.items():
        row = db.query(ApplicationSetting).filter(ApplicationSetting.key == key).first()
        if not row:
            row = ApplicationSetting(key=key, value=value if isinstance(value, dict) else {"value": value})
            db.add(row)
        else:
            row.value = value if isinstance(value, dict) else {"value": value}
            row.updated_at = datetime.utcnow()
    db.commit()
    return get_settings(db)
