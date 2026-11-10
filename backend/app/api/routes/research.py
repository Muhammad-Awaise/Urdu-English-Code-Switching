from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import FindingCreate, NoteCreate, NoteUpdate, PaperCreate, ReportRequest
from app.core.database import get_db
from app.models.orm import ResearchFinding, ResearchNote, ResearchPaper, TrainingExperiment
from app.services.research_service import (
    NOTE_CATEGORIES,
    export_report,
    get_or_create_methodology,
    research_dashboard,
    save_methodology,
)

router = APIRouter()


@router.get("/research/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return research_dashboard(db)


@router.get("/research/notes")
def list_notes(category: str | None = None, db: Session = Depends(get_db)):
    q = db.query(ResearchNote)
    if category:
        q = q.filter(ResearchNote.category == category)
    notes = q.order_by(ResearchNote.id.desc()).all()
    return {
        "categories": NOTE_CATEGORIES,
        "notes": [
            {
                "id": n.id,
                "title": n.title,
                "category": n.category,
                "content": n.content,
                "tags": n.tags,
                "linked_experiment_id": n.linked_experiment_id,
                "linked_model_id": n.linked_model_id,
                "linked_dataset_id": n.linked_dataset_id,
                "created_at": n.created_at.isoformat() if n.created_at else None,
                "updated_at": n.updated_at.isoformat() if n.updated_at else None,
            }
            for n in notes
        ],
    }


@router.post("/research/notes")
def create_note(payload: NoteCreate, db: Session = Depends(get_db)):
    note = ResearchNote(**payload.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"id": note.id}


@router.put("/research/notes/{note_id}")
def update_note(note_id: int, payload: NoteUpdate, db: Session = Depends(get_db)):
    note = db.query(ResearchNote).filter(ResearchNote.id == note_id).first()
    if not note:
        raise HTTPException(404, "Note not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(note, k, v)
    note.updated_at = datetime.utcnow()
    db.commit()
    return {"id": note.id}


@router.delete("/research/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(ResearchNote).filter(ResearchNote.id == note_id).first()
    if not note:
        raise HTTPException(404, "Note not found")
    db.delete(note)
    db.commit()
    return {"deleted": True}


@router.get("/research/papers")
def list_papers(db: Session = Depends(get_db)):
    papers = db.query(ResearchPaper).order_by(ResearchPaper.id.desc()).all()
    return {
        "papers": [
            {
                "id": p.id,
                "title": p.title,
                "authors": p.authors,
                "year": p.year,
                "venue": p.venue,
                "doi": p.doi,
                "free_fulltext_url": p.free_fulltext_url,
                "research_objective": p.research_objective,
                "dataset": p.dataset,
                "methodology": p.methodology,
                "model": p.model,
                "reported_results": p.reported_results,
                "findings": p.findings,
                "limitations": p.limitations,
                "relevance": p.relevance,
            }
            for p in papers
        ]
    }


@router.post("/research/papers")
def create_paper(payload: PaperCreate, db: Session = Depends(get_db)):
    paper = ResearchPaper(**payload.model_dump())
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return {"id": paper.id}


@router.delete("/research/papers/{paper_id}")
def delete_paper(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(ResearchPaper).filter(ResearchPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(404, "Paper not found")
    db.delete(paper)
    db.commit()
    return {"deleted": True}


@router.get("/research/experiments")
def list_experiments(db: Session = Depends(get_db)):
    rows = db.query(TrainingExperiment).order_by(TrainingExperiment.id.desc()).all()
    return {
        "experiments": [
            {
                "experiment_id": e.experiment_id,
                "job_id": e.job_id,
                "hypothesis": e.hypothesis,
                "research_question": e.research_question,
                "dataset_version_id": e.dataset_version_id,
                "model_type": e.model_type,
                "preprocessing": e.preprocessing,
                "hyperparameters": e.hyperparameters,
                "results": e.results,
                "error_observations": e.error_observations,
                "conclusion": e.conclusion,
                "future_improvements": e.future_improvements,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in rows
        ]
    }


@router.get("/research/methodology")
def methodology(db: Session = Depends(get_db)):
    return get_or_create_methodology(db)


@router.put("/research/methodology")
def update_methodology(payload: dict, db: Session = Depends(get_db)):
    return save_methodology(db, payload)


@router.post("/research/findings")
def create_finding(payload: FindingCreate, db: Session = Depends(get_db)):
    row = ResearchFinding(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


@router.post("/research/reports")
def reports(payload: ReportRequest, db: Session = Depends(get_db)):
    return export_report(db, payload.report_type, payload.format)
