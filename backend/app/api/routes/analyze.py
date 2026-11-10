from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import AnalyzeRequest, BatchAnalyzeRequest
from app.core.database import get_db
from app.nlp.analyzer import analyze_batch, analyze_text

router = APIRouter()
_history: list[dict] = []


@router.post("/analyze")
def analyze(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    result = analyze_text(
        payload.text,
        use_preprocessing=payload.use_preprocessing,
        model_override=payload.model_override,
        db_session=db,
    )
    _history.append(
        {
            "text": payload.text[:200],
            "code_switching": result.get("code_switching", {}).get("status"),
            "model": result.get("model"),
            "word_count": result.get("word_count"),
        }
    )
    if len(_history) > 100:
        del _history[:-100]
    return result


@router.post("/analyze/batch")
def analyze_many(payload: BatchAnalyzeRequest, db: Session = Depends(get_db)):
    return {
        "results": analyze_batch(
            payload.texts,
            use_preprocessing=payload.use_preprocessing,
            db_session=db,
        )
    }


@router.get("/analyze/history")
def analyze_history():
    return {"history": list(reversed(_history))}
