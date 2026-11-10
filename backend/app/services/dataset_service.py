from __future__ import annotations

import csv
import json
import random
from collections import Counter
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.models.orm import Dataset, DatasetRecord, DatasetVersion, TokenAnnotation
from app.nlp.codeswitch import detect_code_switching, summarize_predictions
from app.nlp.dictionary_classifier import get_dictionary_classifier
from app.nlp.ml_inference import try_predict_with_active_model
from app.nlp.tokenizer import tokenize


VALID_LABELS = {"URDU_ROMAN", "ENGLISH", "AMBIGUOUS", "UNKNOWN", "OTHER"}
TEXT_COLUMN_ALIASES = (
    "text",
    "sentence",
    "review",
    "reviews",  # e.g. Daraz exports use "Reviews"
    "review_text",
    "cleaned_review_text",
    "content",
    "utterance",
    "comment",
    "comments",
    "body",
    "message",
    "tweet",
)
BULK_DICTIONARY_THRESHOLD = 300
BULK_COMMIT_EVERY = 400


def create_dataset(
    db: Session,
    name: str,
    description: str | None = None,
    source: str | None = None,
    license_note: str | None = None,
    version: str = "v1",
) -> Dataset:
    ds = Dataset(name=name, description=description, source=source, license_note=license_note)
    db.add(ds)
    db.flush()
    ver = DatasetVersion(dataset_id=ds.id, version=version, stats={})
    db.add(ver)
    db.commit()
    db.refresh(ds)
    return ds


def get_latest_version(db: Session, dataset_id: int) -> DatasetVersion | None:
    return (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.id.desc())
        .first()
    )


def compute_stats(db: Session, version_id: int) -> dict:
    records = db.query(DatasetRecord).filter(DatasetRecord.version_id == version_id).all()
    token_labels = Counter()
    sentence_types = Counter()
    unlabeled = 0
    texts = []
    for rec in records:
        texts.append(rec.text.strip().lower())
        labels = [a.label for a in rec.annotations]
        if not labels:
            unlabeled += 1
            sentence_types["unlabeled"] += 1
            continue
        for lab in labels:
            token_labels[lab] += 1
        lang = {l for l in labels if l in {"URDU_ROMAN", "ENGLISH"}}
        if "URDU_ROMAN" in lang and "ENGLISH" in lang:
            sentence_types["mixed"] += 1
        elif lang == {"ENGLISH"}:
            sentence_types["english_only"] += 1
        elif lang == {"URDU_ROMAN"}:
            sentence_types["urdu_only"] += 1
        else:
            sentence_types["other"] += 1

    dupes = len(texts) - len(set(texts))
    stats = {
        "total_sentences": len(records),
        "total_tokens": sum(token_labels.values()),
        "english_tokens": token_labels.get("ENGLISH", 0),
        "roman_urdu_tokens": token_labels.get("URDU_ROMAN", 0),
        "ambiguous_tokens": token_labels.get("AMBIGUOUS", 0),
        "unknown_tokens": token_labels.get("UNKNOWN", 0),
        "unlabeled_sentences": unlabeled,
        "mixed_language_sentences": sentence_types.get("mixed", 0),
        "english_only_sentences": sentence_types.get("english_only", 0),
        "roman_urdu_only_sentences": sentence_types.get("urdu_only", 0),
        "duplicate_records": dupes,
        "splits": dict(Counter(r.split or "unassigned" for r in records)),
    }
    ver = db.query(DatasetVersion).filter(DatasetVersion.id == version_id).first()
    if ver:
        ver.stats = stats
        db.commit()
    return stats


def add_annotated_sentence(
    db: Session,
    version_id: int,
    text: str,
    annotations: list[dict],
    sentence_id: str | None = None,
    split: str | None = None,
    notes: str | None = None,
    annotator: str | None = None,
    *,
    commit: bool = True,
) -> DatasetRecord:
    sid = sentence_id or f"s{version_id}_{db.query(DatasetRecord).filter(DatasetRecord.version_id==version_id).count()+1:04d}"
    rec = DatasetRecord(version_id=version_id, sentence_id=sid, text=text, split=split, notes=notes)
    db.add(rec)
    db.flush()
    for i, ann in enumerate(annotations):
        label = str(ann.get("label", "UNKNOWN")).upper()
        if label not in VALID_LABELS:
            label = "UNKNOWN"
        db.add(
            TokenAnnotation(
                record_id=rec.id,
                position=int(ann.get("position", i)),
                token=str(ann.get("token", "")),
                label=label,
                uncertain=bool(ann.get("uncertain", False)),
                annotator=annotator or ann.get("annotator"),
                note=ann.get("note"),
            )
        )
    if commit:
        db.commit()
        db.refresh(rec)
    return rec


def _has_usable_cs_annotations(annotations: list[dict] | None) -> bool:
    """True only when annotations already contain real CS labels (not empty/all-unknown shells)."""
    if not annotations:
        return False
    labels = [str(a.get("label", "")).upper() for a in annotations]
    if not any(label in VALID_LABELS for label in labels):
        return False
    # All UNKNOWN with no other CS signal → treat as needing auto-analysis
    meaningful = {"URDU_ROMAN", "ENGLISH", "AMBIGUOUS", "OTHER"}
    return any(label in meaningful for label in labels)


def _auto_annotations_for_text(
    text: str,
    db: Session | None = None,
    *,
    force_dictionary: bool = False,
) -> tuple[list[dict], dict]:
    """
    Generate word-level CS labels for any uploaded sentence.
    Uses active trained model when available; otherwise dictionary baseline.
    Large bulk uploads force dictionary mode to keep the API responsive.
    """
    tokens = tokenize(text)
    norms = [t.text.lower() if t.kind == "word" else t.text for t in tokens]
    preds = None
    model_meta = {
        "name": "dictionary-baseline",
        "version": "dictionary-baseline-v1",
        "source": "dictionary",
    }
    if db is not None and not force_dictionary:
        preds, model_meta = try_predict_with_active_model(tokens, norms, db)
    if preds is None:
        preds = get_dictionary_classifier().predict_tokens(tokens, norms)
        model_meta = {
            "name": "dictionary-baseline",
            "version": "dictionary-baseline-v1",
            "source": "dictionary-bulk" if force_dictionary else "dictionary",
        }
    anns = [
        {
            "token": p.token,
            "label": p.label.value,
            "position": p.position,
            "uncertain": p.label.value in {"AMBIGUOUS", "UNKNOWN"},
            "note": None if force_dictionary else f"auto:{model_meta.get('source')}",
        }
        for p in preds
    ]
    analysis = {
        "summary": summarize_predictions(preds),
        "code_switching": detect_code_switching(preds),
        "model": model_meta,
    }
    return anns, analysis


def _fast_bulk_annotations(text: str, clf) -> tuple[list[dict], Counter, str]:
    """Dictionary-only labeling with lightweight counters (no heavy summary objects)."""
    from app.nlp.labels import TokenLabel

    tokens = tokenize(text)
    preds = clf.predict_tokens(tokens)
    anns: list[dict] = []
    counts: Counter = Counter()
    has_urdu = False
    has_eng = False
    for p in preds:
        anns.append({"token": p.token, "label": p.label.value, "position": p.position})
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
    return anns, counts, cs


def _aggregate_upload_analysis(per_sentence: list[dict], model_meta: dict | None) -> dict:
    cs_counts = Counter()
    token_totals = Counter()
    for item in per_sentence:
        cs = (item.get("code_switching") or {}).get("status", "INSUFFICIENT_EVIDENCE")
        cs_counts[cs] += 1
        summary = item.get("summary") or {}
        token_totals["roman_urdu"] += int(summary.get("roman_urdu", 0))
        token_totals["english"] += int(summary.get("english", 0))
        token_totals["ambiguous"] += int(summary.get("ambiguous", 0))
        token_totals["unknown"] += int(summary.get("unknown", 0))
        token_totals["total_words"] += int(summary.get("total_words", 0))
    return {
        "sentences_analyzed": len(per_sentence),
        "code_switching_yes": cs_counts.get("YES", 0),
        "code_switching_no": cs_counts.get("NO", 0),
        "code_switching_insufficient": cs_counts.get("INSUFFICIENT_EVIDENCE", 0),
        "roman_urdu_tokens": token_totals["roman_urdu"],
        "english_tokens": token_totals["english"],
        "ambiguous_tokens": token_totals["ambiguous"],
        "unknown_tokens": token_totals["unknown"],
        "total_words": token_totals["total_words"],
        "model": model_meta
        or {"name": "dictionary-baseline", "version": "dictionary-baseline-v1", "source": "dictionary"},
        "note": (
            "Auto-generated code-switching analysis for every imported sentence. "
            "Existing gold CS token labels were preserved when present."
        ),
    }


def _metadata_notes(row: pd.Series, cols: dict[str, str], skip: set[str]) -> str | None:
    parts = []
    for key, original in cols.items():
        if key in skip:
            continue
        val = row.get(original)
        if pd.isna(val):
            continue
        parts.append(f"{key}={val}")
    return "; ".join(parts) if parts else None


def _resolve_text_column(cols: dict[str, str]) -> str | None:
    for alias in TEXT_COLUMN_ALIASES:
        if alias in cols:
            return cols[alias]
    return None


def import_json_records(
    db: Session,
    version_id: int,
    records: list[dict],
    *,
    auto_analyze: bool = True,
) -> dict:
    added = 0
    errors = []
    auto_labeled = 0
    preserved_gold = 0
    per_sentence_analysis: list[dict] = []
    last_model: dict | None = None
    force_dictionary = len(records) >= BULK_DICTIONARY_THRESHOLD
    batch_commit = len(records) >= 100
    bulk_counts: Counter = Counter()
    bulk_cs: Counter = Counter()
    bulk_clf = get_dictionary_classifier() if force_dictionary and auto_analyze else None

    for i, item in enumerate(records):
        try:
            text = str(item["text"])
            anns = item.get("annotations") or []

            if auto_analyze and not _has_usable_cs_annotations(anns):
                if force_dictionary and bulk_clf is not None:
                    anns, counts, cs = _fast_bulk_annotations(text, bulk_clf)
                    bulk_counts.update(counts)
                    bulk_cs[cs] += 1
                    last_model = {
                        "name": "dictionary-baseline",
                        "version": "dictionary-baseline-v1",
                        "source": "dictionary-bulk",
                    }
                else:
                    anns, sentence_analysis = _auto_annotations_for_text(
                        text, db, force_dictionary=False
                    )
                    last_model = sentence_analysis.get("model")
                    per_sentence_analysis.append(sentence_analysis)
                auto_labeled += 1
            else:
                if not anns:
                    if auto_analyze and force_dictionary and bulk_clf is not None:
                        anns, counts, cs = _fast_bulk_annotations(text, bulk_clf)
                        bulk_counts.update(counts)
                        bulk_cs[cs] += 1
                        auto_labeled += 1
                        last_model = {
                            "name": "dictionary-baseline",
                            "version": "dictionary-baseline-v1",
                            "source": "dictionary-bulk",
                        }
                    elif auto_analyze:
                        anns, sentence_analysis = _auto_annotations_for_text(text, db)
                        auto_labeled += 1
                        last_model = sentence_analysis.get("model")
                        per_sentence_analysis.append(sentence_analysis)
                    else:
                        anns = [
                            {"token": t.text, "label": "UNKNOWN", "position": t.position}
                            for t in tokenize(text)
                        ]
                else:
                    preserved_gold += 1

            add_annotated_sentence(
                db,
                version_id,
                text=text,
                annotations=anns,
                sentence_id=str(item.get("sentence_id") or f"imp_{i+1:04d}"),
                split=item.get("split"),
                notes=item.get("notes"),
                commit=not batch_commit,
            )
            added += 1
            if batch_commit and added % BULK_COMMIT_EVERY == 0:
                db.commit()
        except Exception as exc:
            errors.append({"index": i, "error": str(exc)})

    if batch_commit:
        db.commit()

    stats = compute_stats(db, version_id)
    if force_dictionary and auto_labeled:
        analysis = {
            "sentences_analyzed": auto_labeled,
            "code_switching_yes": bulk_cs.get("YES", 0),
            "code_switching_no": bulk_cs.get("NO", 0),
            "code_switching_insufficient": bulk_cs.get("INSUFFICIENT_EVIDENCE", 0),
            "roman_urdu_tokens": bulk_counts.get("roman_urdu", 0),
            "english_tokens": bulk_counts.get("english", 0),
            "ambiguous_tokens": bulk_counts.get("ambiguous", 0),
            "unknown_tokens": bulk_counts.get("unknown", 0),
            "total_words": bulk_counts.get("total_words", 0),
            "model": last_model
            or {
                "name": "dictionary-baseline",
                "version": "dictionary-baseline-v1",
                "source": "dictionary-bulk",
            },
            "bulk_mode": True,
            "note": (
                "Large file: fast dictionary auto-labeling was used. "
                "Gold CS labels were preserved when present."
            ),
        }
    else:
        analysis = (
            _aggregate_upload_analysis(per_sentence_analysis, last_model)
            if per_sentence_analysis
            else None
        )
    return {
        "added": added,
        "errors": errors,
        "stats": stats,
        "auto_labeled_sentences": auto_labeled,
        "preserved_gold_sentences": preserved_gold,
        "analysis": analysis,
        "bulk_dictionary_mode": force_dictionary,
    }


def import_file_bytes(db: Session, version_id: int, filename: str, content: bytes) -> dict:
    name = filename.lower()
    if name.endswith(".json"):
        data = json.loads(content.decode("utf-8"))
        records = data if isinstance(data, list) else data.get("records", [])
        result = import_json_records(db, version_id, records, auto_analyze=True)
    elif name.endswith(".jsonl"):
        records = [json.loads(line) for line in content.decode("utf-8").splitlines() if line.strip()]
        result = import_json_records(db, version_id, records, auto_analyze=True)
    elif name.endswith(".csv"):
        df = pd.read_csv(BytesIO(content))
        result = _import_dataframe(db, version_id, df)
    elif name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(BytesIO(content))
        result = _import_dataframe(db, version_id, df)
    else:
        raise ValueError("Unsupported file type. Use CSV, Excel, JSON, or JSONL.")
    result["source_file"] = filename
    return result


def _import_dataframe(db: Session, version_id: int, df: pd.DataFrame) -> dict:
    if df.empty:
        raise ValueError("Uploaded file has no rows.")

    cols = {str(c).lower().strip(): c for c in df.columns}
    text_col = _resolve_text_column(cols)
    records: list[dict] = []

    has_token_cs = (
        "token" in cols
        and "label" in cols
        and (text_col is not None or "sentence_id" in cols)
    )

    if has_token_cs:
        # Inspect whether labels are actual CS labels or unrelated (e.g. sentiment)
        sample_labels = {
            str(v).upper()
            for v in df[cols["label"]].dropna().astype(str).head(50).tolist()
        }
        cs_like = bool(sample_labels & {"URDU_ROMAN", "ENGLISH", "AMBIGUOUS", "UNKNOWN", "OTHER"})
        if cs_like:
            grouped: dict[str, dict] = {}
            for _, row in df.iterrows():
                sid_col = cols.get("sentence_id") or text_col
                sid = str(row[sid_col])
                text = str(row[text_col]) if text_col else sid
                grouped.setdefault(
                    sid,
                    {
                        "sentence_id": sid,
                        "text": text,
                        "annotations": [],
                        "notes": _metadata_notes(
                            row,
                            cols,
                            skip={"token", "label", "position", "text", "sentence", "sentence_id"},
                        ),
                    },
                )
                grouped[sid]["annotations"].append(
                    {
                        "token": str(row[cols["token"]]),
                        "label": str(row[cols["label"]]),
                        "position": len(grouped[sid]["annotations"]),
                    }
                )
                if text_col:
                    grouped[sid]["text"] = str(row[text_col])
            records = list(grouped.values())
            return import_json_records(db, version_id, records, auto_analyze=True)

    if text_col is None:
        raise ValueError(
            "CSV/Excel must include a text column "
            f"(one of: {', '.join(TEXT_COLUMN_ALIASES)}) "
            "or token/label CS annotations."
        )

    skip_meta = {
        str(text_col).lower(),
        "token",
        "label",
        "position",
        "annotations",
    }
    for i, row in df.iterrows():
        text = str(row[text_col])
        if not text.strip() or text.lower() == "nan":
            continue
        sid = None
        if "sentence_id" in cols:
            sid = str(row[cols["sentence_id"]])
        elif "row_number" in cols:
            sid = f"row_{int(row[cols['row_number']]):04d}"
        else:
            sid = f"row_{i}"
        records.append(
            {
                "sentence_id": sid,
                "text": text,
                "notes": _metadata_notes(row, cols, skip=skip_meta),
                # annotations left empty → auto CS analysis for every file
                "annotations": [],
            }
        )

    if not records:
        raise ValueError("No non-empty text rows found in uploaded file.")
    return import_json_records(db, version_id, records, auto_analyze=True)


def validate_dataset(db: Session, version_id: int) -> dict:
    records = db.query(DatasetRecord).filter(DatasetRecord.version_id == version_id).all()
    issues = []
    seen = {}
    for rec in records:
        key = rec.text.strip().lower()
        seen.setdefault(key, []).append(rec.sentence_id)
        if not rec.text.strip():
            issues.append({"type": "empty_record", "sentence_id": rec.sentence_id})
        tokens = [t.text for t in tokenize(rec.text)]
        anns = sorted(rec.annotations, key=lambda a: a.position)
        if anns and len(anns) != len(tokens):
            # soft check — tokenization may differ from manual annotation
            issues.append(
                {
                    "type": "token_alignment_warning",
                    "sentence_id": rec.sentence_id,
                    "tokenized": len(tokens),
                    "annotated": len(anns),
                }
            )
        for a in anns:
            if a.label not in VALID_LABELS:
                issues.append(
                    {
                        "type": "invalid_label",
                        "sentence_id": rec.sentence_id,
                        "token": a.token,
                        "label": a.label,
                    }
                )
            if a.label == "UNKNOWN" and not a.uncertain:
                issues.append(
                    {
                        "type": "missing_or_unknown_label",
                        "sentence_id": rec.sentence_id,
                        "token": a.token,
                    }
                )
        if not anns:
            issues.append({"type": "missing_labels", "sentence_id": rec.sentence_id})
    duplicates = [{"text_key": k, "sentence_ids": v} for k, v in seen.items() if len(v) > 1]
    report = {
        "record_count": len(records),
        "issue_count": len(issues),
        "issues": issues[:500],
        "duplicates": duplicates,
        "stats": compute_stats(db, version_id),
    }
    return report


def clean_dataset(db: Session, version_id: int, *, remove_empty: bool = True, remove_duplicates: bool = False) -> dict:
    """Generate cleaning actions; only delete when explicitly requested. Never silent."""
    report = validate_dataset(db, version_id)
    actions = []
    records = db.query(DatasetRecord).filter(DatasetRecord.version_id == version_id).all()
    if remove_empty:
        for rec in list(records):
            if not rec.text.strip():
                actions.append({"action": "removed_empty", "sentence_id": rec.sentence_id})
                db.delete(rec)
    if remove_duplicates:
        seen = {}
        for rec in db.query(DatasetRecord).filter(DatasetRecord.version_id == version_id).all():
            key = rec.text.strip().lower()
            if key in seen:
                actions.append(
                    {
                        "action": "removed_duplicate",
                        "sentence_id": rec.sentence_id,
                        "kept": seen[key],
                    }
                )
                db.delete(rec)
            else:
                seen[key] = rec.sentence_id
    db.commit()
    return {"actions": actions, "validation": validate_dataset(db, version_id)}


def split_dataset(
    db: Session,
    version_id: int,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> dict:
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        raise ValueError("Split ratios must sum to 1.0")
    # Deduplicate by text before split to reduce leakage
    records = db.query(DatasetRecord).filter(DatasetRecord.version_id == version_id).all()
    by_text: dict[str, list[DatasetRecord]] = {}
    for rec in records:
        by_text.setdefault(rec.text.strip().lower(), []).append(rec)
    groups = list(by_text.values())
    rng = random.Random(seed)
    rng.shuffle(groups)
    n = len(groups)
    n_train = int(train_ratio * n)
    n_val = int(val_ratio * n)
    train_g = groups[:n_train]
    val_g = groups[n_train : n_train + n_val]
    test_g = groups[n_train + n_val :]

    def assign(gs, split):
        for g in gs:
            for rec in g:
                rec.split = split

    assign(train_g, "train")
    assign(val_g, "val")
    assign(test_g, "test")
    ver = db.query(DatasetVersion).filter(DatasetVersion.id == version_id).first()
    if ver:
        ver.split_seed = seed
    db.commit()
    stats = compute_stats(db, version_id)
    return {
        "seed": seed,
        "groups": n,
        "train_groups": len(train_g),
        "val_groups": len(val_g),
        "test_groups": len(test_g),
        "stats": stats,
    }
