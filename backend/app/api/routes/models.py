from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.orm import ModelArtifact

router = APIRouter()


class RegisterModel(BaseModel):
    name: str
    version: str
    architecture: str
    artifact_path: str
    dataset_version_id: int | None = None
    metrics: dict | None = None
    hyperparameters: dict | None = None
    preprocessing: dict | None = None
    activate: bool = False


@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    models = db.query(ModelArtifact).order_by(ModelArtifact.id.desc()).all()
    return {
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "version": m.version,
                "architecture": m.architecture,
                "dataset_version_id": m.dataset_version_id,
                "artifact_path": m.artifact_path,
                "metrics": m.metrics,
                "hyperparameters": m.hyperparameters,
                "preprocessing": m.preprocessing,
                "is_active": m.is_active,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in models
        ],
        "fallback": {
            "name": "dictionary-baseline",
            "version": "dictionary-baseline-v1",
            "note": "Used when no active trained model is set.",
        },
    }


@router.post("/models/register")
def register(payload: RegisterModel, db: Session = Depends(get_db)):
    if not Path(payload.artifact_path).exists():
        raise HTTPException(400, "artifact_path does not exist locally")
    if payload.activate:
        for m in db.query(ModelArtifact).filter(ModelArtifact.is_active.is_(True)).all():
            m.is_active = False
    model = ModelArtifact(
        name=payload.name,
        version=payload.version,
        architecture=payload.architecture,
        dataset_version_id=payload.dataset_version_id,
        artifact_path=payload.artifact_path,
        metrics=payload.metrics,
        hyperparameters=payload.hyperparameters,
        preprocessing=payload.preprocessing,
        is_active=payload.activate,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return {"id": model.id, "is_active": model.is_active}


@router.post("/models/{model_id}/activate")
def activate(model_id: int, db: Session = Depends(get_db)):
    model = db.query(ModelArtifact).filter(ModelArtifact.id == model_id).first()
    if not model:
        raise HTTPException(404, "Model not found")
    for m in db.query(ModelArtifact).filter(ModelArtifact.is_active.is_(True)).all():
        m.is_active = False
    model.is_active = True
    db.commit()
    return {"id": model.id, "is_active": True}


@router.post("/models/{model_id}/deactivate")
def deactivate(model_id: int, db: Session = Depends(get_db)):
    model = db.query(ModelArtifact).filter(ModelArtifact.id == model_id).first()
    if not model:
        raise HTTPException(404, "Model not found")
    model.is_active = False
    db.commit()
    return {"id": model.id, "is_active": False, "fallback": "dictionary-baseline"}


@router.post("/models/{model_id}/rollback")
def rollback(model_id: int, db: Session = Depends(get_db)):
    """Activate the selected prior model without deleting the current artifact."""
    return activate(model_id, db)


@router.delete("/models/{model_id}")
def delete_model(model_id: int, confirm: bool = False, delete_file: bool = False, db: Session = Depends(get_db)):
    if not confirm:
        raise HTTPException(400, "Pass confirm=true to delete a model registry entry")
    model = db.query(ModelArtifact).filter(ModelArtifact.id == model_id).first()
    if not model:
        raise HTTPException(404, "Model not found")
    path = Path(model.artifact_path)
    db.delete(model)
    db.commit()
    deleted_file = False
    if delete_file and path.exists():
        path.unlink()
        deleted_file = True
    return {"deleted": True, "deleted_file": deleted_file}
