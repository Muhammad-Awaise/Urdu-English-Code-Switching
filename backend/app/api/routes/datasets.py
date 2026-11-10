from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.schemas import CleanRequest, DatasetCreate, SentenceCreate, SplitRequest
from app.core.database import get_db
from app.models.orm import Dataset, DatasetRecord, DatasetVersion
from app.services.dataset_service import (
    add_annotated_sentence,
    clean_dataset,
    compute_stats,
    create_dataset,
    get_latest_version,
    import_file_bytes,
    split_dataset,
    validate_dataset,
)

router = APIRouter()


@router.get("/datasets")
def list_datasets(db: Session = Depends(get_db)):
    out = []
    for ds in db.query(Dataset).order_by(Dataset.id.desc()).all():
        ver = get_latest_version(db, ds.id)
        out.append(
            {
                "id": ds.id,
                "name": ds.name,
                "description": ds.description,
                "source": ds.source,
                "license_note": ds.license_note,
                "latest_version": (
                    {"id": ver.id, "version": ver.version, "stats": ver.stats} if ver else None
                ),
            }
        )
    return {"datasets": out}


@router.post("/datasets")
def create(payload: DatasetCreate, db: Session = Depends(get_db)):
    if db.query(Dataset).filter(Dataset.name == payload.name).first():
        raise HTTPException(400, "Dataset name already exists")
    ds = create_dataset(
        db,
        name=payload.name,
        description=payload.description,
        source=payload.source,
        license_note=payload.license_note,
    )
    ver = get_latest_version(db, ds.id)
    return {"id": ds.id, "name": ds.name, "version_id": ver.id if ver else None}


@router.get("/datasets/import-jobs/{job_id}")
def import_job_status(job_id: str):
    """Must be registered before /datasets/{dataset_id} so 'import-jobs' is not parsed as an id."""
    from app.services.bulk_import import get_import_job

    job = get_import_job(job_id)
    if not job:
        raise HTTPException(404, "Import job not found")
    return job


@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found")
    versions = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).all()
    return {
        "id": ds.id,
        "name": ds.name,
        "description": ds.description,
        "source": ds.source,
        "license_note": ds.license_note,
        "versions": [
            {"id": v.id, "version": v.version, "stats": v.stats, "split_seed": v.split_seed}
            for v in versions
        ],
    }


@router.post("/datasets/{dataset_id}/upload")
async def upload(dataset_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    from app.services.bulk_import import should_use_async_import, start_large_csv_import

    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(404, "Dataset not found")
    ver = get_latest_version(db, dataset_id)
    if not ver:
        raise HTTPException(400, "No dataset version")
    content = await file.read()
    filename = file.filename or "upload.csv"
    try:
        # Large CSVs (thousands–100k rows): background chunked fast import
        if filename.lower().endswith(".csv") and should_use_async_import(filename, content):
            return start_large_csv_import(ver.id, filename, content)
        result = import_file_bytes(db, ver.id, filename, content)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
    return result


@router.post("/datasets/{dataset_id}/sentences")
def add_sentence(dataset_id: int, payload: SentenceCreate, db: Session = Depends(get_db)):
    ver = get_latest_version(db, dataset_id)
    if not ver:
        raise HTTPException(404, "Dataset not found")
    rec = add_annotated_sentence(
        db,
        ver.id,
        text=payload.text,
        annotations=[a.model_dump() for a in payload.annotations],
        sentence_id=payload.sentence_id,
        notes=payload.notes,
        annotator=payload.annotator,
    )
    compute_stats(db, ver.id)
    return {"record_id": rec.id, "sentence_id": rec.sentence_id}


@router.get("/datasets/{dataset_id}/records")
def list_records(
    dataset_id: int,
    unlabeled_only: bool = False,
    split: str | None = None,
    db: Session = Depends(get_db),
):
    ver = get_latest_version(db, dataset_id)
    if not ver:
        raise HTTPException(404, "Dataset not found")
    q = db.query(DatasetRecord).filter(DatasetRecord.version_id == ver.id)
    if split:
        q = q.filter(DatasetRecord.split == split)
    records = q.order_by(DatasetRecord.id.asc()).all()
    out = []
    for rec in records:
        anns = sorted(rec.annotations, key=lambda a: a.position)
        if unlabeled_only and anns and not any(a.label == "UNKNOWN" for a in anns):
            continue
        if unlabeled_only and not anns:
            pass
        out.append(
            {
                "id": rec.id,
                "sentence_id": rec.sentence_id,
                "text": rec.text,
                "split": rec.split,
                "notes": rec.notes,
                "annotations": [
                    {
                        "id": a.id,
                        "position": a.position,
                        "token": a.token,
                        "label": a.label,
                        "uncertain": a.uncertain,
                        "note": a.note,
                        "annotator": a.annotator,
                    }
                    for a in anns
                ],
            }
        )
    return {"version_id": ver.id, "records": out}


@router.post("/datasets/{dataset_id}/validate")
def validate(dataset_id: int, db: Session = Depends(get_db)):
    ver = get_latest_version(db, dataset_id)
    if not ver:
        raise HTTPException(404, "Dataset not found")
    return validate_dataset(db, ver.id)


@router.post("/datasets/{dataset_id}/clean")
def clean(dataset_id: int, payload: CleanRequest, db: Session = Depends(get_db)):
    ver = get_latest_version(db, dataset_id)
    if not ver:
        raise HTTPException(404, "Dataset not found")
    return clean_dataset(
        db,
        ver.id,
        remove_empty=payload.remove_empty,
        remove_duplicates=payload.remove_duplicates,
    )


@router.post("/datasets/{dataset_id}/split")
def split(dataset_id: int, payload: SplitRequest, db: Session = Depends(get_db)):
    ver = get_latest_version(db, dataset_id)
    if not ver:
        raise HTTPException(404, "Dataset not found")
    try:
        return split_dataset(
            db,
            ver.id,
            train_ratio=payload.train_ratio,
            val_ratio=payload.val_ratio,
            test_ratio=payload.test_ratio,
            seed=payload.seed,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
