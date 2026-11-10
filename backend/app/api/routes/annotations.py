from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import AnnotationUpdate, SentenceCreate
from app.core.database import get_db
from app.models.orm import DatasetRecord, TokenAnnotation
from app.nlp.tokenizer import tokenize
from app.services.dataset_service import VALID_LABELS, add_annotated_sentence, get_latest_version

router = APIRouter()


@router.get("/annotations")
def list_annotations(record_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(TokenAnnotation)
    if record_id is not None:
        q = q.filter(TokenAnnotation.record_id == record_id)
    rows = q.order_by(TokenAnnotation.id.asc()).limit(5000).all()
    return {
        "annotations": [
            {
                "id": a.id,
                "record_id": a.record_id,
                "position": a.position,
                "token": a.token,
                "label": a.label,
                "uncertain": a.uncertain,
                "note": a.note,
                "annotator": a.annotator,
            }
            for a in rows
        ]
    }


@router.post("/annotations")
def create_annotations(
    dataset_id: int,
    payload: SentenceCreate,
    db: Session = Depends(get_db),
):
    ver = get_latest_version(db, dataset_id)
    if not ver:
        raise HTTPException(404, "Dataset not found")
    anns = [a.model_dump() for a in payload.annotations]
    if not anns:
        anns = [{"token": t.text, "label": "UNKNOWN", "position": t.position} for t in tokenize(payload.text)]
    rec = add_annotated_sentence(
        db,
        ver.id,
        text=payload.text,
        annotations=anns,
        sentence_id=payload.sentence_id,
        notes=payload.notes,
        annotator=payload.annotator,
    )
    return {"record_id": rec.id}


@router.put("/annotations/{annotation_id}")
def update_annotation(annotation_id: int, payload: AnnotationUpdate, db: Session = Depends(get_db)):
    ann = db.query(TokenAnnotation).filter(TokenAnnotation.id == annotation_id).first()
    if not ann:
        raise HTTPException(404, "Annotation not found")
    if payload.label is not None:
        label = payload.label.upper()
        if label not in VALID_LABELS:
            raise HTTPException(400, f"Invalid label. Use one of {sorted(VALID_LABELS)}")
        ann.label = label
    if payload.uncertain is not None:
        ann.uncertain = payload.uncertain
    if payload.note is not None:
        ann.note = payload.note
    if payload.annotator is not None:
        ann.annotator = payload.annotator
    db.commit()
    return {"id": ann.id, "label": ann.label, "uncertain": ann.uncertain}


@router.put("/annotations/records/{record_id}/bulk")
def bulk_update(record_id: int, annotations: list[AnnotationUpdate] | list[dict], db: Session = Depends(get_db)):
    rec = db.query(DatasetRecord).filter(DatasetRecord.id == record_id).first()
    if not rec:
        raise HTTPException(404, "Record not found")
    existing = sorted(rec.annotations, key=lambda a: a.position)
    for i, item in enumerate(annotations):
        data = item if isinstance(item, dict) else item.model_dump(exclude_unset=True)
        if i >= len(existing):
            break
        if "label" in data and data["label"]:
            label = str(data["label"]).upper()
            if label in VALID_LABELS:
                existing[i].label = label
        if "uncertain" in data and data["uncertain"] is not None:
            existing[i].uncertain = bool(data["uncertain"])
        if "note" in data:
            existing[i].note = data["note"]
    db.commit()
    return {"record_id": record_id, "updated": min(len(annotations), len(existing))}
