from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import ensure_directories
from app.core.database import Base, SessionLocal, engine
from app.models.orm import Dataset, DatasetRecord
from app.services.dataset_service import create_dataset, get_latest_version, import_file_bytes

CSV = Path(r"C:\Users\GrowMore Devs\Downloads\Awaise\2026-11-02_urdu_fixed_predictions.csv")


def main() -> None:
    ensure_directories()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        name = "upload_auto_test"
        ds = db.query(Dataset).filter(Dataset.name == name).first()
        if not ds:
            ds = create_dataset(db, name=name, description="auto analysis test", license_note="test")
        ver = get_latest_version(db, ds.id)
        assert ver is not None
        # clear previous test rows
        for rec in db.query(DatasetRecord).filter(DatasetRecord.version_id == ver.id).all():
            db.delete(rec)
        db.commit()
        res = import_file_bytes(db, ver.id, CSV.name, CSV.read_bytes())
        print("added", res["added"])
        print("auto_labeled", res["auto_labeled_sentences"])
        print("preserved", res["preserved_gold_sentences"])
        print("analysis", res["analysis"])
    finally:
        db.close()


if __name__ == "__main__":
    main()
