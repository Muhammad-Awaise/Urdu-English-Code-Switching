from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.orm import (
    Dataset,
    DatasetRecord,
    ModelArtifact,
    TokenAnnotation,
    TrainingExperiment,
    TrainingJob,
)
from app.services.dataset_service import get_latest_version


def overview(db: Session) -> dict:
    datasets = db.query(Dataset).all()
    total_sentences = db.query(func.count(DatasetRecord.id)).scalar() or 0

    # Fast label counts — never load hundreds of thousands of ORM rows
    label_rows = (
        db.query(TokenAnnotation.label, func.count(TokenAnnotation.id))
        .group_by(TokenAnnotation.label)
        .all()
    )
    label_counts = {label: int(count) for label, count in label_rows}
    total_anns = sum(label_counts.values())
    urdu = label_counts.get("URDU_ROMAN", 0)
    eng = label_counts.get("ENGLISH", 0)
    amb = label_counts.get("AMBIGUOUS", 0)
    unknown = label_counts.get("UNKNOWN", 0)
    other = label_counts.get("OTHER", 0)

    models = db.query(ModelArtifact).order_by(ModelArtifact.id.asc()).all()
    experiments = db.query(func.count(TrainingExperiment.id)).scalar() or 0
    jobs = db.query(TrainingJob).order_by(TrainingJob.id.desc()).limit(20).all()
    active = next((m for m in models if m.is_active), None)

    best_macro = None
    model_comparison = []
    for m in models:
        test = (m.metrics or {}).get("test") or {}
        macro = test.get("macro_f1")
        model_comparison.append(
            {
                "id": m.id,
                "name": m.name,
                "version": m.version,
                "architecture": m.architecture,
                "accuracy": test.get("accuracy"),
                "macro_f1": macro,
                "weighted_f1": test.get("weighted_f1"),
                "train_time_sec": (m.metrics or {}).get("train_time_sec"),
                "is_active": m.is_active,
            }
        )
        if macro is not None and (best_macro is None or macro > best_macro):
            best_macro = macro

    dataset_cards = []
    for ds in datasets:
        ver = get_latest_version(db, ds.id)
        # Prefer stored stats JSON — avoid re-scanning large versions
        stats = (ver.stats if ver and ver.stats else {}) or {}
        dataset_cards.append({"id": ds.id, "name": ds.name, "stats": stats})

    return {
        "cards": {
            "total_dataset_sentences": total_sentences,
            "total_annotated_tokens": total_anns,
            "roman_urdu_tokens": urdu,
            "english_tokens": eng,
            "ambiguous_tokens": amb,
            "trained_models": len(models),
            "completed_experiments": experiments,
            "best_macro_f1": best_macro,
            "active_model": (
                {"id": active.id, "name": active.name, "version": active.version}
                if active
                else {"name": "dictionary-baseline", "version": "dictionary-baseline-v1"}
            ),
        },
        "language_distribution": {
            "URDU_ROMAN": urdu,
            "ENGLISH": eng,
            "AMBIGUOUS": amb,
            "UNKNOWN": unknown,
            "OTHER": other,
        },
        "datasets": dataset_cards,
        "model_comparison": model_comparison,
        "recent_jobs": [
            {
                "job_id": j.job_id,
                "status": j.status,
                "model_type": j.model_type,
                "progress": j.progress,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in jobs
        ],
    }
