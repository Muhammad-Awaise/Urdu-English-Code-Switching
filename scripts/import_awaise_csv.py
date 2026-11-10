"""Import the Awaise sentiment predictions CSV texts into this CS analyzer DB."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import pandas as pd
from app.core.config import ensure_directories
from app.core.database import Base, SessionLocal, engine
from app.models.orm import Dataset, DatasetRecord
from app.nlp.dictionary_classifier import get_dictionary_classifier
from app.nlp.tokenizer import tokenize
from app.services.dataset_service import (
    compute_stats,
    create_dataset,
    get_latest_version,
    import_json_records,
)


CSV_PATH = Path(r"C:\Users\GrowMore Devs\Downloads\Awaise\2026-11-02_urdu_fixed_predictions.csv")
DATASET_NAME = "awaise_2026_11_02_predictions"


def main() -> None:
    ensure_directories()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        df = pd.read_csv(CSV_PATH)
        existing = db.query(Dataset).filter(Dataset.name == DATASET_NAME).first()
        if existing:
            ds = existing
            ver = get_latest_version(db, ds.id)
            print(f"Using existing dataset id={ds.id}")
        else:
            ds = create_dataset(
                db,
                name=DATASET_NAME,
                description=(
                    "Imported review texts from sentiment predictions CSV. "
                    "Sentiment columns are external metadata; token labels here are "
                    "dictionary-baseline suggestions for code-switching work."
                ),
                source=str(CSV_PATH),
                license_note="User-provided local file.",
            )
            ver = get_latest_version(db, ds.id)
            print(f"Created dataset id={ds.id} version_id={ver.id}")

        assert ver is not None
        count = db.query(DatasetRecord).filter(DatasetRecord.version_id == ver.id).count()
        if count > 0:
            print(f"Already has {count} records")
            print(compute_stats(db, ver.id))
            return

        clf = get_dictionary_classifier()
        records = []
        for _, row in df.iterrows():
            text = str(row["text"])
            preds = clf.predict_tokens(tokenize(text))
            lang = row.get("language")
            sent = row.get("predicted_sentiment")
            anns = [
                {
                    "token": p.token,
                    "label": p.label.value,
                    "position": p.position,
                    "note": f"src_lang={lang}; sentiment={sent}",
                }
                for p in preds
            ]
            records.append(
                {
                    "sentence_id": f"row_{int(row['row_number']):04d}",
                    "text": text,
                    "annotations": anns,
                    "notes": (
                        f"language={lang}; gold_label={row.get('label')}; "
                        f"predicted_sentiment={sent}; model={row.get('model_name')}"
                    ),
                }
            )

        res = import_json_records(db, ver.id, records)
        print(f"Imported {res['added']} sentences; errors={len(res['errors'])}")
        print(res["stats"])
        print("See UI: Datasets -> awaise_2026_11_02_predictions")
        print("See UI: Annotation -> select that dataset")
    finally:
        db.close()


if __name__ == "__main__":
    main()
