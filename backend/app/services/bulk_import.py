"""High-throughput dataset import for large CSVs (up to ~100k+ rows)."""

from __future__ import annotations

import threading
import traceback
from collections import Counter
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.models.orm import DatasetRecord, DatasetVersion, TokenAnnotation
from app.nlp.dictionary_classifier import get_dictionary_classifier
from app.nlp.labels import TokenLabel
from app.nlp.tokenizer import tokenize
from app.services.dataset_service import (
    TEXT_COLUMN_ALIASES,
    _resolve_text_column,
)


ASYNC_ROW_THRESHOLD = 1500
CHUNK_SIZE = 5000
ANN_BATCH = 20_000

_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}


def get_import_job(job_id: str) -> dict | None:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def _update_job(job_id: str, **kwargs) -> None:
    with _lock:
        if job_id in _jobs:
            _jobs[job_id].update(kwargs)
            _jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()


def _estimate_csv_rows(content: bytes) -> int:
    lines = content.count(b"\n")
    if content and not content.endswith(b"\n"):
        lines += 1
    return max(0, lines - 1)


def should_use_async_import(filename: str, content: bytes) -> bool:
    name = filename.lower()
    if name.endswith((".xlsx", ".xls")):
        return len(content) > 1_500_000
    if name.endswith(".csv"):
        return _estimate_csv_rows(content) >= ASYNC_ROW_THRESHOLD or len(content) > 1_500_000
    if name.endswith((".json", ".jsonl")):
        return len(content) > 1_500_000
    return False


def _label_fast(text: str, clf) -> tuple[list[tuple[str, str, int]], Counter, str]:
    tokens = tokenize(text)
    preds = clf.predict_tokens(tokens)
    triples: list[tuple[str, str, int]] = []
    counts: Counter = Counter()
    has_urdu = False
    has_eng = False
    for p in preds:
        triples.append((p.token, p.label.value, p.position))
        if p.kind != "word":
            continue
        counts["total_words"] += 1
        if p.label == TokenLabel.URDU_ROMAN:
            counts["roman_urdu"] += 1
            has_urdu = True
        elif p.label == TokenLabel.ENGLISH:
            counts["english"] += 1
            has_eng = True
        elif p.label == TokenLabel.AMBIGUOUS:
            counts["ambiguous"] += 1
        elif p.label == TokenLabel.UNKNOWN:
            counts["unknown"] += 1
    if has_urdu and has_eng:
        cs = "YES"
    elif has_urdu or has_eng:
        cs = "NO"
    else:
        cs = "INSUFFICIENT_EVIDENCE"
    return triples, counts, cs


def _insert_chunk(
    db: Session,
    version_id: int,
    rows: list[dict[str, Any]],
    clf,
    totals: Counter,
    cs_totals: Counter,
) -> int:
    """Insert a chunk with bulk ORM mappings for speed."""
    if not rows:
        return 0

    record_maps = []
    pending_anns: list[list[tuple[str, str, int]]] = []
    now = datetime.utcnow()

    for row in rows:
        text_val = row["text"]
        triples, counts, cs = _label_fast(text_val, clf)
        totals.update(counts)
        cs_totals[cs] += 1
        record_maps.append(
            {
                "version_id": version_id,
                "sentence_id": row["sentence_id"],
                "text": text_val,
                "split": row.get("split"),
                "notes": None,
                "created_at": now,
            }
        )
        pending_anns.append(triples)

    # Capture last id before insert so we can map new rows without IN(...)
    last_id = db.query(func.max(DatasetRecord.id)).scalar() or 0

    db.bulk_insert_mappings(DatasetRecord, record_maps)
    db.flush()

    new_ids = [
        rid
        for (rid,) in (
            db.query(DatasetRecord.id)
            .filter(DatasetRecord.version_id == version_id, DatasetRecord.id > last_id)
            .order_by(DatasetRecord.id.asc())
            .all()
        )
    ]
    if len(new_ids) != len(record_maps):
        # Fallback if ids are non-contiguous
        sids = [r["sentence_id"] for r in record_maps]
        inserted = (
            db.query(DatasetRecord.id, DatasetRecord.sentence_id)
            .filter(DatasetRecord.version_id == version_id, DatasetRecord.sentence_id.in_(sids))
            .all()
        )
        sid_to_id = {sid: rid for rid, sid in inserted}
        new_ids = [sid_to_id[r["sentence_id"]] for r in record_maps if r["sentence_id"] in sid_to_id]

    ann_maps: list[dict[str, Any]] = []
    for rid, triples in zip(new_ids, pending_anns):
        for token, label, pos in triples:
            ann_maps.append(
                {
                    "record_id": rid,
                    "position": pos,
                    "token": token,
                    "label": label,
                    "uncertain": label in {"AMBIGUOUS", "UNKNOWN"},
                    "annotator": None,
                    "note": None,
                }
            )
    if ann_maps:
        for i in range(0, len(ann_maps), ANN_BATCH):
            db.bulk_insert_mappings(TokenAnnotation, ann_maps[i : i + ANN_BATCH])
    db.commit()
    return len(record_maps)


def _iter_text_rows_from_csv(content: bytes):
    """Yield (rows, processed_count) using chunked reads — no per-row metadata notes."""
    df_head = pd.read_csv(BytesIO(content), nrows=5)
    cols = {str(c).lower().strip(): c for c in df_head.columns}
    text_col = _resolve_text_column(cols)
    if text_col is None:
        raise ValueError(
            "CSV must include a text column "
            f"(one of: {', '.join(TEXT_COLUMN_ALIASES)})."
        )
    sid_col = cols.get("sentence_id") or cols.get("row_number")
    use_row_number = cols.get("row_number") == sid_col

    # Only load the columns we need — huge win on wide Daraz-style CSVs
    usecols = [text_col] + ([sid_col] if sid_col is not None else [])
    reader = pd.read_csv(
        BytesIO(content),
        chunksize=CHUNK_SIZE,
        usecols=usecols,
        dtype=str,
        keep_default_na=False,
    )
    global_i = 0
    for chunk in reader:
        texts = chunk[text_col].tolist()
        sids_raw = chunk[sid_col].tolist() if sid_col is not None else None
        rows: list[dict[str, Any]] = []
        for i, text_val in enumerate(texts):
            text_val = (text_val or "").strip()
            if not text_val or text_val.lower() == "nan":
                global_i += 1
                continue
            if sids_raw is not None:
                raw = sids_raw[i]
                if use_row_number:
                    try:
                        sid = f"row_{int(float(raw)):06d}"
                    except (TypeError, ValueError):
                        sid = f"row_{global_i:06d}"
                else:
                    sid = str(raw)
            else:
                sid = f"row_{global_i:06d}"
            rows.append({"sentence_id": sid, "text": text_val})
            global_i += 1
        if rows:
            yield rows, global_i


def _run_large_csv_import(job_id: str, version_id: int, filename: str, content: bytes) -> None:
    db = SessionLocal()
    try:
        if str(engine.url).startswith("sqlite"):
            db.execute(text("PRAGMA journal_mode=WAL"))
            db.execute(text("PRAGMA synchronous=NORMAL"))
            db.execute(text("PRAGMA temp_store=MEMORY"))
            db.execute(text("PRAGMA cache_size=-160000"))
            db.execute(text("PRAGMA mmap_size=268435456"))

        total_est = max(1, _estimate_csv_rows(content))
        _update_job(
            job_id,
            status="RUNNING",
            stage="Reading CSV in chunks",
            progress=0.02,
            total_estimate=total_est,
        )

        clf = get_dictionary_classifier()
        totals: Counter = Counter()
        cs_totals: Counter = Counter()
        added = 0
        processed_hint = 0

        for rows, processed_hint in _iter_text_rows_from_csv(content):
            for row in rows:
                row["sentence_id"] = f"{job_id}_{row['sentence_id']}"
            _update_job(
                job_id,
                stage=f"Analyzing & saving rows ({added:,}+ / ~{total_est:,})…",
                progress=min(0.95, 0.05 + 0.9 * (processed_hint / total_est)),
                processed=processed_hint,
            )
            added += _insert_chunk(db, version_id, rows, clf, totals, cs_totals)

        _update_job(job_id, stage="Saving dataset stats", progress=0.97)
        # Build stats from in-memory counters — avoid re-scanning 100k+ ORM rows
        stats = {
            "total_sentences": added,
            "total_tokens": (
                totals.get("roman_urdu", 0)
                + totals.get("english", 0)
                + totals.get("ambiguous", 0)
                + totals.get("unknown", 0)
            ),
            "english_tokens": totals.get("english", 0),
            "roman_urdu_tokens": totals.get("roman_urdu", 0),
            "ambiguous_tokens": totals.get("ambiguous", 0),
            "unknown_tokens": totals.get("unknown", 0),
            "unlabeled_sentences": 0,
            "mixed_language_sentences": cs_totals.get("YES", 0),
            "english_only_sentences": 0,
            "roman_urdu_only_sentences": 0,
            "code_switching_no": cs_totals.get("NO", 0),
            "code_switching_insufficient": cs_totals.get("INSUFFICIENT_EVIDENCE", 0),
            "duplicate_records": 0,
            "splits": {"unassigned": added},
            "bulk_import": True,
        }
        ver = db.query(DatasetVersion).filter(DatasetVersion.id == version_id).first()
        if ver:
            ver.stats = stats
            db.commit()

        analysis = {
            "sentences_analyzed": added,
            "code_switching_yes": cs_totals.get("YES", 0),
            "code_switching_no": cs_totals.get("NO", 0),
            "code_switching_insufficient": cs_totals.get("INSUFFICIENT_EVIDENCE", 0),
            "roman_urdu_tokens": totals.get("roman_urdu", 0),
            "english_tokens": totals.get("english", 0),
            "ambiguous_tokens": totals.get("ambiguous", 0),
            "unknown_tokens": totals.get("unknown", 0),
            "total_words": totals.get("total_words", 0),
            "model": {
                "name": "dictionary-baseline",
                "version": "dictionary-baseline-v1",
                "source": "dictionary-bulk-fast",
            },
            "bulk_mode": True,
            "note": (
                "Large-file fast import: chunked CSV read + dictionary labeling + bulk SQLite inserts."
            ),
        }
        result = {
            "added": added,
            "errors": [],
            "stats": stats,
            "auto_labeled_sentences": added,
            "preserved_gold_sentences": 0,
            "analysis": analysis,
            "bulk_dictionary_mode": True,
            "source_file": filename,
            "async": True,
        }
        _update_job(
            job_id,
            status="COMPLETED",
            stage="Completed",
            progress=1.0,
            result=result,
            completed_at=datetime.utcnow().isoformat(),
        )
    except Exception:
        _update_job(
            job_id,
            status="FAILED",
            stage="Failed",
            progress=1.0,
            error=traceback.format_exc(),
            completed_at=datetime.utcnow().isoformat(),
        )
    finally:
        db.close()


def start_large_csv_import(version_id: int, filename: str, content: bytes) -> dict:
    job_id = uuid4().hex[:12]
    upload_dir = settings.artifacts_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / f"{job_id}_{Path(filename).name}"
    path.write_bytes(content)

    with _lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "QUEUED",
            "stage": "Queued",
            "progress": 0.0,
            "version_id": version_id,
            "source_file": filename,
            "result": None,
            "error": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    t = threading.Thread(
        target=_run_large_csv_import,
        args=(job_id, version_id, filename, content),
        daemon=True,
    )
    t.start()
    return {
        "async": True,
        "job_id": job_id,
        "status": "QUEUED",
        "source_file": filename,
        "message": "Large file import started in background for speed.",
        "upload_path": str(path),
    }
