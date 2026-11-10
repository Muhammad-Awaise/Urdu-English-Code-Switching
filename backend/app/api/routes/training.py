from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import TrainRequest
from app.core.database import get_db
from app.models.orm import DatasetRecord, TokenAnnotation, TrainingJob
from app.services.training_service import cancel_job, start_training_job

router = APIRouter()


@router.post("/training/start")
def start_training(payload: TrainRequest, db: Session = Depends(get_db)):
    if payload.model_type == "dictionary":
        raise HTTPException(400, "Dictionary baseline does not require training. Use it directly in the analyzer.")

    n_tokens = (
        db.query(TokenAnnotation)
        .join(DatasetRecord, DatasetRecord.id == TokenAnnotation.record_id)
        .filter(DatasetRecord.version_id == payload.dataset_version_id)
        .count()
    )
    if n_tokens > 5000 and not payload.confirm_large_run:
        raise HTTPException(
            400,
            "Large experiment confirmation required (confirm_large_run=true). "
            f"Labeled tokens associated with version: {n_tokens}",
        )

    job = start_training_job(db, payload.model_dump())
    return {
        "job_id": job.job_id,
        "status": job.status,
        "model_type": job.model_type,
        "dataset_version_id": job.dataset_version_id,
    }


@router.get("/training/jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(TrainingJob).order_by(TrainingJob.id.desc()).limit(100).all()
    return {
        "jobs": [
            {
                "job_id": j.job_id,
                "status": j.status,
                "stage": j.stage,
                "progress": j.progress,
                "model_type": j.model_type,
                "dataset_version_id": j.dataset_version_id,
                "metrics": j.metrics,
                "error_log": j.error_log,
                "artifact_path": j.artifact_path,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in jobs
        ]
    }


@router.get("/training/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    j = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
    if not j:
        raise HTTPException(404, "Job not found")
    return {
        "job_id": j.job_id,
        "status": j.status,
        "stage": j.stage,
        "progress": j.progress,
        "model_type": j.model_type,
        "config": j.config,
        "metrics": j.metrics,
        "error_log": j.error_log,
        "artifact_path": j.artifact_path,
        "started_at": j.started_at.isoformat() if j.started_at else None,
        "completed_at": j.completed_at.isoformat() if j.completed_at else None,
    }


@router.post("/training/jobs/{job_id}/cancel")
def cancel(job_id: str, db: Session = Depends(get_db)):
    job = cancel_job(db, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"job_id": job.job_id, "status": job.status, "cancel_requested": job.cancel_requested}
