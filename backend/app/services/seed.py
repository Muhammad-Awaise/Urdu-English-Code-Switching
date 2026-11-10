from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import DATA_DIR, ensure_directories
from app.models.orm import Dataset, ResearchNote
from app.services.dataset_service import (
    add_annotated_sentence,
    compute_stats,
    create_dataset,
    get_latest_version,
    split_dataset,
)
from app.services.research_service import get_or_create_methodology


SAMPLE_SENTENCES = [
    {
        "sentence_id": "001",
        "text": "Main university mein admission apply kar raha hoon.",
        "annotations": [
            {"token": "Main", "label": "URDU_ROMAN"},
            {"token": "university", "label": "ENGLISH"},
            {"token": "mein", "label": "URDU_ROMAN"},
            {"token": "admission", "label": "ENGLISH"},
            {"token": "apply", "label": "ENGLISH"},
            {"token": "kar", "label": "URDU_ROMAN"},
            {"token": "raha", "label": "URDU_ROMAN"},
            {"token": "hoon", "label": "URDU_ROMAN"},
            {"token": ".", "label": "OTHER"},
        ],
    },
    {
        "sentence_id": "002",
        "text": "Yeh project deadline kal hai.",
        "annotations": [
            {"token": "Yeh", "label": "URDU_ROMAN"},
            {"token": "project", "label": "ENGLISH"},
            {"token": "deadline", "label": "ENGLISH"},
            {"token": "kal", "label": "URDU_ROMAN"},
            {"token": "hai", "label": "URDU_ROMAN"},
            {"token": ".", "label": "OTHER"},
        ],
    },
    {
        "sentence_id": "003",
        "text": "Please send me the report.",
        "annotations": [
            {"token": "Please", "label": "ENGLISH"},
            {"token": "send", "label": "ENGLISH"},
            {"token": "me", "label": "AMBIGUOUS"},
            {"token": "the", "label": "ENGLISH"},
            {"token": "report", "label": "ENGLISH"},
            {"token": ".", "label": "OTHER"},
        ],
    },
    {
        "sentence_id": "004",
        "text": "Aaj mausam bohot acha hai.",
        "annotations": [
            {"token": "Aaj", "label": "URDU_ROMAN"},
            {"token": "mausam", "label": "URDU_ROMAN"},
            {"token": "bohot", "label": "URDU_ROMAN"},
            {"token": "acha", "label": "URDU_ROMAN"},
            {"token": "hai", "label": "URDU_ROMAN"},
            {"token": ".", "label": "OTHER"},
        ],
    },
    {
        "sentence_id": "005",
        "text": "Teacher ne assignment submit karne ko kaha.",
        "annotations": [
            {"token": "Teacher", "label": "ENGLISH"},
            {"token": "ne", "label": "URDU_ROMAN"},
            {"token": "assignment", "label": "ENGLISH"},
            {"token": "submit", "label": "ENGLISH"},
            {"token": "karne", "label": "URDU_ROMAN"},
            {"token": "ko", "label": "URDU_ROMAN"},
            {"token": "kaha", "label": "URDU_ROMAN"},
            {"token": ".", "label": "OTHER"},
        ],
    },
    {
        "sentence_id": "006",
        "text": "I am learning natural language processing.",
        "annotations": [
            {"token": "I", "label": "ENGLISH"},
            {"token": "am", "label": "ENGLISH"},
            {"token": "learning", "label": "ENGLISH"},
            {"token": "natural", "label": "ENGLISH"},
            {"token": "language", "label": "ENGLISH"},
            {"token": "processing", "label": "ENGLISH"},
            {"token": ".", "label": "OTHER"},
        ],
    },
    {
        "sentence_id": "007",
        "text": "Mujhe laptop chahiye kyunki online class hai.",
        "annotations": [
            {"token": "Mujhe", "label": "URDU_ROMAN"},
            {"token": "laptop", "label": "ENGLISH"},
            {"token": "chahiye", "label": "URDU_ROMAN"},
            {"token": "kyunki", "label": "URDU_ROMAN"},
            {"token": "online", "label": "ENGLISH"},
            {"token": "class", "label": "ENGLISH"},
            {"token": "hai", "label": "URDU_ROMAN"},
            {"token": ".", "label": "OTHER"},
        ],
    },
    {
        "sentence_id": "008",
        "text": "Kal meeting cancel ho gayi.",
        "annotations": [
            {"token": "Kal", "label": "URDU_ROMAN"},
            {"token": "meeting", "label": "ENGLISH"},
            {"token": "cancel", "label": "ENGLISH"},
            {"token": "ho", "label": "URDU_ROMAN"},
            {"token": "gayi", "label": "URDU_ROMAN"},
            {"token": ".", "label": "OTHER"},
        ],
    },
]


def seed_if_empty(db: Session) -> None:
    ensure_directories()
    get_or_create_methodology(db)

    raw_dir = DATA_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    sample_path = raw_dir / "sample_code_switching.json"
    if not sample_path.exists():
        sample_path.write_text(json.dumps(SAMPLE_SENTENCES, indent=2, ensure_ascii=False), encoding="utf-8")

    existing = db.query(Dataset).filter(Dataset.name == "sample_code_switching").first()
    if not existing:
        ds = create_dataset(
            db,
            name="sample_code_switching",
            description="Small illustrative annotated set for pipeline testing. Not a research benchmark.",
            source="project-curated",
            license_note="MIT with project code; illustrative labels only.",
        )
        ver = get_latest_version(db, ds.id)
        assert ver is not None
        for item in SAMPLE_SENTENCES:
            add_annotated_sentence(
                db,
                ver.id,
                text=item["text"],
                annotations=item["annotations"],
                sentence_id=item["sentence_id"],
            )
        split_dataset(db, ver.id, seed=42)
        compute_stats(db, ver.id)

    if db.query(ResearchNote).count() == 0:
        db.add(
            ResearchNote(
                title="Starter note: need more annotated data",
                category="Dataset Collection",
                content=(
                    "The shipped sample set is only for pipeline checks. "
                    "Before claiming model quality, annotate a larger word-level dataset "
                    "or import a verified open-license corpus."
                ),
                tags=["data", "limitations"],
            )
        )
        db.commit()
