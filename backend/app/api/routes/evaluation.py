from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.orm import ModelArtifact, ModelEvaluation, TrainingExperiment

router = APIRouter()


@router.get("/models/{model_id}/evaluation")
def model_evaluation(model_id: int, db: Session = Depends(get_db)):
    model = db.query(ModelArtifact).filter(ModelArtifact.id == model_id).first()
    if not model:
        raise HTTPException(404, "Model not found")
    evals = db.query(ModelEvaluation).filter(ModelEvaluation.model_id == model_id).all()
    return {
        "model": {
            "id": model.id,
            "name": model.name,
            "version": model.version,
            "architecture": model.architecture,
            "metrics": model.metrics,
        },
        "evaluations": [
            {
                "id": e.id,
                "split": e.split,
                "metrics": e.metrics,
                "confusion_matrix": e.confusion_matrix,
                "misclassified": e.misclassified,
            }
            for e in evals
        ],
        "error_analysis_hints": [
            "Roman Urdu spelling variation",
            "Ambiguous short tokens",
            "Unknown / OOV words",
            "English words inside Urdu grammatical frames",
            "Normalization side effects",
            "Context-dependent errors (token models ignore context)",
        ],
    }


@router.get("/experiments/compare")
def compare_experiments(db: Session = Depends(get_db)):
    models = db.query(ModelArtifact).order_by(ModelArtifact.id.asc()).all()
    rows = []
    for m in models:
        test = (m.metrics or {}).get("test") or {}
        rows.append(
            {
                "model_id": m.id,
                "name": m.name,
                "version": m.version,
                "architecture": m.architecture,
                "accuracy": test.get("accuracy"),
                "macro_f1": test.get("macro_f1"),
                "weighted_f1": test.get("weighted_f1"),
                "train_time_sec": (m.metrics or {}).get("train_time_sec"),
                "model_size_note": m.artifact_path,
                "is_active": m.is_active,
            }
        )
    experiments = db.query(TrainingExperiment).order_by(TrainingExperiment.id.desc()).limit(50).all()
    return {
        "models": rows,
        "experiments": [
            {
                "experiment_id": e.experiment_id,
                "model_type": e.model_type,
                "results": e.results,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in experiments
        ],
    }
