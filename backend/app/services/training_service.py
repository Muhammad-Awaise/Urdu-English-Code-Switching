from __future__ import annotations

import threading
import traceback
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.ml.trainers import TrainConfig, new_job_id, train_word_lid
from app.models.orm import (
    DatasetRecord,
    ModelArtifact,
    ModelEvaluation,
    TokenAnnotation,
    TrainingExperiment,
    TrainingJob,
)


_lock = threading.Lock()
_threads: dict[str, threading.Thread] = {}


def _load_split_xy(db: Session, version_id: int, split: str) -> tuple[list[str], list[str]]:
    records = (
        db.query(DatasetRecord)
        .filter(DatasetRecord.version_id == version_id, DatasetRecord.split == split)
        .all()
    )
    X: list[str] = []
    y: list[str] = []
    for rec in records:
        for ann in rec.annotations:
            if ann.label in {"URDU_ROMAN", "ENGLISH", "AMBIGUOUS", "UNKNOWN"}:
                X.append(ann.token.lower())
                y.append(ann.label)
    return X, y


def _load_all_labeled(db: Session, version_id: int) -> tuple[list[str], list[str]]:
    records = db.query(DatasetRecord).filter(DatasetRecord.version_id == version_id).all()
    X, y = [], []
    for rec in records:
        for ann in rec.annotations:
            if ann.label in {"URDU_ROMAN", "ENGLISH", "AMBIGUOUS", "UNKNOWN"}:
                X.append(ann.token.lower())
                y.append(ann.label)
    return X, y


def start_training_job(db: Session, payload: dict[str, Any]) -> TrainingJob:
    job_id = new_job_id()
    cfg = TrainConfig(
        model_type=payload.get("model_type", "logreg"),
        word_ngram_range=tuple(payload.get("word_ngram_range", [1, 1])),
        char_ngram_range=tuple(payload.get("char_ngram_range", [2, 5])),
        C=float(payload.get("C", 1.0)),
        class_weight=payload.get("class_weight", "balanced"),
        random_seed=int(payload.get("random_seed", 42)),
        use_char=bool(payload.get("use_char", True)),
        use_word=bool(payload.get("use_word", True)),
        max_features=int(payload.get("max_features", 50000)),
        task=payload.get("task", "word_lid"),
    )
    job = TrainingJob(
        job_id=job_id,
        status="QUEUED",
        stage="QUEUED",
        progress=0.0,
        model_type=cfg.model_type,
        dataset_version_id=payload.get("dataset_version_id"),
        config={**payload, "resolved": cfg.__dict__},
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    t = threading.Thread(target=_run_job, args=(job_id,), daemon=True)
    with _lock:
        _threads[job_id] = t
    t.start()
    return job


def _run_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
        if not job:
            return
        job.status = "PREPARING"
        job.stage = "PREPARING"
        job.started_at = datetime.utcnow()
        db.commit()

        if job.cancel_requested:
            job.status = "CANCELLED"
            job.completed_at = datetime.utcnow()
            db.commit()
            return

        version_id = job.dataset_version_id
        if not version_id:
            raise ValueError("dataset_version_id is required")

        X_train, y_train = _load_split_xy(db, version_id, "train")
        X_val, y_val = _load_split_xy(db, version_id, "val")
        X_test, y_test = _load_split_xy(db, version_id, "test")

        if len(X_train) < 4:
            # Fall back to all labeled tokens with a simple holdout if splits empty
            X_all, y_all = _load_all_labeled(db, version_id)
            if len(X_all) < 8:
                raise ValueError(
                    "Insufficient labeled tokens. Annotate a dataset and split it before training."
                )
            rng = np_random(job.config.get("resolved", {}).get("random_seed", 42))
            idx = list(range(len(X_all)))
            rng.shuffle(idx)
            n = len(idx)
            n_train = int(0.7 * n)
            n_val = int(0.15 * n)
            train_i = idx[:n_train]
            val_i = idx[n_train : n_train + n_val]
            test_i = idx[n_train + n_val :]
            X_train = [X_all[i] for i in train_i]
            y_train = [y_all[i] for i in train_i]
            X_val = [X_all[i] for i in val_i]
            y_val = [y_all[i] for i in val_i]
            X_test = [X_all[i] for i in test_i]
            y_test = [y_all[i] for i in test_i]

        resolved = job.config.get("resolved", {}) if job.config else {}
        cfg = TrainConfig(
            model_type=resolved.get("model_type", job.model_type),
            word_ngram_range=tuple(resolved.get("word_ngram_range", (1, 1))),
            char_ngram_range=tuple(resolved.get("char_ngram_range", (2, 5))),
            C=float(resolved.get("C", 1.0)),
            class_weight=resolved.get("class_weight", "balanced"),
            random_seed=int(resolved.get("random_seed", 42)),
            use_char=bool(resolved.get("use_char", True)),
            use_word=bool(resolved.get("use_word", True)),
            max_features=int(resolved.get("max_features", 50000)),
        )

        def progress_cb(stage: str, progress: float) -> None:
            db.refresh(job)
            if job.cancel_requested:
                raise RuntimeError("CANCELLED")
            job.status = stage if stage in {
                "QUEUED", "PREPARING", "TRAINING", "VALIDATING", "EVALUATING", "COMPLETED", "FAILED", "CANCELLED"
            } else "TRAINING"
            job.stage = stage
            job.progress = float(progress)
            db.commit()

        result = train_word_lid(
            X_train, y_train, X_val, y_val, X_test, y_test, cfg, progress_cb=progress_cb
        )

        job.status = "COMPLETED"
        job.stage = "COMPLETED"
        job.progress = 1.0
        job.metrics = result["metrics"]
        job.artifact_path = result["artifact_path"]
        job.completed_at = datetime.utcnow()
        db.commit()

        # Register model but do NOT auto-activate
        artifact = ModelArtifact(
            name=result["name"],
            version=result["version"],
            architecture=result["architecture"],
            dataset_version_id=version_id,
            artifact_path=result["artifact_path"],
            metrics=result["metrics"],
            hyperparameters=result["hyperparameters"],
            preprocessing={"lowercase": True},
            is_active=False,
        )
        db.add(artifact)
        db.flush()

        if "test" in result["metrics"]:
            ev = ModelEvaluation(
                model_id=artifact.id,
                split="test",
                metrics=result["metrics"]["test"],
                confusion_matrix=result["metrics"]["test"].get("confusion_matrix"),
                misclassified=result.get("misclassified"),
            )
            db.add(ev)

        exp_id = f"exp_{uuid4().hex[:10]}"
        db.add(
            TrainingExperiment(
                experiment_id=exp_id,
                job_id=job_id,
                hypothesis=job.config.get("hypothesis") if job.config else None,
                research_question=job.config.get("research_question") if job.config else None,
                dataset_version_id=version_id,
                model_type=job.model_type,
                preprocessing={"lowercase": True},
                hyperparameters=result["hyperparameters"],
                results=result["metrics"],
            )
        )
        db.commit()
    except Exception as exc:
        job = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
        if job:
            if str(exc) == "CANCELLED" or job.cancel_requested:
                job.status = "CANCELLED"
            else:
                job.status = "FAILED"
                job.error_log = traceback.format_exc()
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
        with _lock:
            _threads.pop(job_id, None)


def np_random(seed: int):
    import random

    r = random.Random(seed)
    return r


def cancel_job(db: Session, job_id: str) -> TrainingJob | None:
    job = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
    if not job:
        return None
    job.cancel_requested = True
    if job.status in {"QUEUED"}:
        job.status = "CANCELLED"
        job.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job
