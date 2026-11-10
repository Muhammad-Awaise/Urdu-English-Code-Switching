"""Thin wrappers around backend services for Streamlit pages."""

from __future__ import annotations


from streamlit_lib.bootstrap import get_db_session


def dashboard_overview() -> dict:
    from app.services.dashboard_service import overview

    db = get_db_session()
    try:
        return overview(db)
    finally:
        db.close()


def analyze_text(text: str, use_preprocessing: bool = True, model_override: str | None = None) -> dict:
    from app.nlp.analyzer import analyze_text as _analyze

    db = get_db_session()
    try:
        return _analyze(
            text,
            use_preprocessing=use_preprocessing,
            model_override=model_override,
            db_session=db,
        )
    finally:
        db.close()


def list_datasets() -> list[dict]:
    from app.models.orm import Dataset
    from app.services.dataset_service import get_latest_version

    db = get_db_session()
    try:
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
        return out
    finally:
        db.close()


def create_dataset(name: str, description: str = "User dataset", license_note: str = "user-provided") -> dict:
    from app.models.orm import Dataset
    from app.services.dataset_service import create_dataset as _create
    from app.services.dataset_service import get_latest_version

    db = get_db_session()
    try:
        if db.query(Dataset).filter(Dataset.name == name).first():
            raise ValueError("Dataset name already exists")
        ds = _create(db, name=name, description=description, source=None, license_note=license_note)
        ver = get_latest_version(db, ds.id)
        bust_caches()
        return {"id": ds.id, "name": ds.name, "version_id": ver.id if ver else None}
    finally:
        db.close()


def upload_dataset_file(dataset_id: int, filename: str, content: bytes) -> dict:
    from app.services.bulk_import import should_use_async_import, start_large_csv_import
    from app.services.dataset_service import get_latest_version, import_file_bytes

    db = get_db_session()
    try:
        ver = get_latest_version(db, dataset_id)
        if not ver:
            raise ValueError("No dataset version")
        if filename.lower().endswith(".csv") and should_use_async_import(filename, content):
            return start_large_csv_import(ver.id, filename, content)
        return import_file_bytes(db, ver.id, filename, content)
    finally:
        db.close()


def import_job_status(job_id: str) -> dict | None:
    from app.services.bulk_import import get_import_job

    return get_import_job(job_id)


def validate_dataset(dataset_id: int) -> dict:
    from app.services.dataset_service import get_latest_version, validate_dataset as _validate

    db = get_db_session()
    try:
        ver = get_latest_version(db, dataset_id)
        if not ver:
            raise ValueError("Dataset not found")
        return _validate(db, ver.id)
    finally:
        db.close()


def clean_dataset(dataset_id: int, remove_empty: bool = True, remove_duplicates: bool = False) -> dict:
    from app.services.dataset_service import clean_dataset as _clean
    from app.services.dataset_service import get_latest_version

    db = get_db_session()
    try:
        ver = get_latest_version(db, dataset_id)
        if not ver:
            raise ValueError("Dataset not found")
        return _clean(db, ver.id, remove_empty=remove_empty, remove_duplicates=remove_duplicates)
    finally:
        db.close()


def split_dataset(
    dataset_id: int,
    train_ratio: float | None = None,
    val_ratio: float | None = None,
    test_ratio: float | None = None,
    seed: int | None = None,
) -> dict:
    from app.core.runtime_settings import default_split, random_seed
    from app.services.dataset_service import get_latest_version, split_dataset as _split

    ratios = default_split()
    train_ratio = ratios["train"] if train_ratio is None else train_ratio
    val_ratio = ratios["val"] if val_ratio is None else val_ratio
    test_ratio = ratios["test"] if test_ratio is None else test_ratio
    seed = random_seed() if seed is None else seed

    db = get_db_session()
    try:
        ver = get_latest_version(db, dataset_id)
        if not ver:
            raise ValueError("Dataset not found")
        return _split(
            db,
            ver.id,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            seed=seed,
        )
    finally:
        db.close()


def _serialize_record(rec) -> dict:
    anns = sorted(rec.annotations, key=lambda a: a.position)
    return {
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


def _unlabeled_record_ids_query(db, version_id: int):
    from sqlalchemy import case, func

    from app.models.orm import DatasetRecord, TokenAnnotation

    return (
        db.query(DatasetRecord.id)
        .outerjoin(TokenAnnotation, TokenAnnotation.record_id == DatasetRecord.id)
        .filter(DatasetRecord.version_id == version_id)
        .group_by(DatasetRecord.id)
        .having(
            (func.count(TokenAnnotation.id) == 0)
            | (func.sum(case((TokenAnnotation.label == "UNKNOWN", 1), else_=0)) > 0)
        )
        .order_by(DatasetRecord.id.asc())
    )


def count_records(dataset_id: int, unlabeled_only: bool = False) -> int:
    from sqlalchemy import func

    from app.models.orm import DatasetRecord
    from app.services.dataset_service import get_latest_version

    db = get_db_session()
    try:
        ver = get_latest_version(db, dataset_id)
        if not ver:
            return 0
        if not unlabeled_only:
            return (
                db.query(func.count(DatasetRecord.id))
                .filter(DatasetRecord.version_id == ver.id)
                .scalar()
                or 0
            )
        subq = _unlabeled_record_ids_query(db, ver.id).subquery()
        return db.query(func.count()).select_from(subq).scalar() or 0
    finally:
        db.close()


def get_record_at(dataset_id: int, index: int, unlabeled_only: bool = False) -> dict | None:
    """Fetch a single sentence by index — avoids loading entire datasets."""
    from app.models.orm import DatasetRecord
    from app.services.dataset_service import get_latest_version

    if index < 0:
        return None
    db = get_db_session()
    try:
        ver = get_latest_version(db, dataset_id)
        if not ver:
            return None
        if unlabeled_only:
            row = _unlabeled_record_ids_query(db, ver.id).offset(int(index)).limit(1).first()
            if not row:
                return None
            rec = db.query(DatasetRecord).filter(DatasetRecord.id == row[0]).first()
        else:
            rec = (
                db.query(DatasetRecord)
                .filter(DatasetRecord.version_id == ver.id)
                .order_by(DatasetRecord.id.asc())
                .offset(int(index))
                .limit(1)
                .first()
            )
        return _serialize_record(rec) if rec else None
    finally:
        db.close()


def list_records(
    dataset_id: int,
    unlabeled_only: bool = False,
    offset: int = 0,
    limit: int | None = None,
) -> list[dict]:
    """List records. Prefer limit/offset for large datasets; limit=None loads all (legacy)."""
    from app.models.orm import DatasetRecord
    from app.services.dataset_service import get_latest_version

    db = get_db_session()
    try:
        ver = get_latest_version(db, dataset_id)
        if not ver:
            return []
        if unlabeled_only:
            id_q = _unlabeled_record_ids_query(db, ver.id)
            if offset:
                id_q = id_q.offset(int(offset))
            if limit is not None:
                id_q = id_q.limit(int(limit))
            ids = [row[0] for row in id_q.all()]
            if not ids:
                return []
            records = (
                db.query(DatasetRecord)
                .filter(DatasetRecord.id.in_(ids))
                .order_by(DatasetRecord.id.asc())
                .all()
            )
            return [_serialize_record(rec) for rec in records]

        q = (
            db.query(DatasetRecord)
            .filter(DatasetRecord.version_id == ver.id)
            .order_by(DatasetRecord.id.asc())
        )
        if offset:
            q = q.offset(int(offset))
        if limit is not None:
            q = q.limit(int(limit))
        return [_serialize_record(rec) for rec in q.all()]
    finally:
        db.close()


def bust_caches() -> None:
    try:
        from streamlit_lib.cache import clear_data_caches

        clear_data_caches()
    except Exception:
        pass


def update_annotation(annotation_id: int, label: str | None = None, uncertain: bool | None = None) -> None:
    from app.models.orm import TokenAnnotation

    db = get_db_session()
    try:
        ann = db.query(TokenAnnotation).filter(TokenAnnotation.id == annotation_id).first()
        if not ann:
            raise ValueError("Annotation not found")
        if label is not None:
            ann.label = label
            ann.uncertain = label in {"AMBIGUOUS", "UNKNOWN"}
        if uncertain is not None:
            ann.uncertain = uncertain
        db.commit()
        bust_caches()
    finally:
        db.close()


def preprocess_text(text: str, **opts) -> dict:
    from app.nlp.preprocess import PreprocessConfig, preprocess

    cfg = PreprocessConfig(
        unicode_normalize=opts.get("unicode_normalize", True),
        clean_text=opts.get("clean_text", True),
        whitespace_normalize=opts.get("whitespace_normalize", True),
        lowercase=opts.get("lowercase", True),
        collapse_repeated_chars=opts.get("collapse_repeated_chars", True),
        roman_urdu_normalize=opts.get("roman_urdu_normalize", True),
    )
    result = preprocess(text, cfg)
    disabled = preprocess(
        text,
        PreprocessConfig(
            unicode_normalize=True,
            clean_text=True,
            whitespace_normalize=True,
            lowercase=False,
            collapse_repeated_chars=False,
            roman_urdu_normalize=False,
        ),
    )
    return {
        "with_preprocessing": {
            "original": result.original,
            "cleaned": result.cleaned,
            "normalized": result.normalized,
            "tokenized": result.token_texts,
        },
        "without_roman_normalization": {
            "original": disabled.original,
            "cleaned": disabled.cleaned,
            "normalized": disabled.normalized,
            "tokenized": disabled.token_texts,
        },
    }


def start_training(config: dict) -> dict:
    from app.models.orm import DatasetRecord, TokenAnnotation
    from app.services.training_service import start_training_job

    db = get_db_session()
    try:
        if config.get("model_type") == "dictionary":
            raise ValueError("Dictionary baseline does not require training.")
        n_tokens = (
            db.query(TokenAnnotation)
            .join(DatasetRecord, DatasetRecord.id == TokenAnnotation.record_id)
            .filter(DatasetRecord.version_id == config["dataset_version_id"])
            .count()
        )
        if n_tokens > 5000 and not config.get("confirm_large_run"):
            raise ValueError(
                f"Large experiment confirmation required. Labeled tokens: {n_tokens}. "
                "Enable 'Confirm large run'."
            )
        job = start_training_job(db, config)
        return {
            "job_id": job.job_id,
            "status": job.status,
            "model_type": job.model_type,
            "dataset_version_id": job.dataset_version_id,
        }
    finally:
        db.close()


def list_training_jobs() -> list[dict]:
    from app.models.orm import TrainingJob

    db = get_db_session()
    try:
        jobs = db.query(TrainingJob).order_by(TrainingJob.id.desc()).limit(100).all()
        return [
            {
                "job_id": j.job_id,
                "status": j.status,
                "stage": j.stage,
                "progress": j.progress,
                "model_type": j.model_type,
                "dataset_version_id": j.dataset_version_id,
                "metrics": j.metrics,
                "error_log": j.error_log,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            }
            for j in jobs
        ]
    finally:
        db.close()


def cancel_training_job(job_id: str) -> dict:
    from app.services.training_service import cancel_job

    db = get_db_session()
    try:
        job = cancel_job(db, job_id)
        if not job:
            raise ValueError("Job not found")
        return {"job_id": job.job_id, "status": job.status, "cancel_requested": job.cancel_requested}
    finally:
        db.close()


def list_models() -> dict:
    from app.models.orm import ModelArtifact

    db = get_db_session()
    try:
        models = db.query(ModelArtifact).order_by(ModelArtifact.id.desc()).all()
        return {
            "models": [
                {
                    "id": m.id,
                    "name": m.name,
                    "version": m.version,
                    "architecture": m.architecture,
                    "dataset_version_id": m.dataset_version_id,
                    "artifact_path": m.artifact_path,
                    "metrics": m.metrics,
                    "is_active": m.is_active,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in models
            ],
            "fallback": {
                "name": "dictionary-baseline",
                "version": "dictionary-baseline-v1",
            },
        }
    finally:
        db.close()


def set_model_active(model_id: int, active: bool) -> None:
    from app.models.orm import ModelArtifact

    db = get_db_session()
    try:
        model = db.query(ModelArtifact).filter(ModelArtifact.id == model_id).first()
        if not model:
            raise ValueError("Model not found")
        if active:
            for m in db.query(ModelArtifact).filter(ModelArtifact.is_active.is_(True)).all():
                m.is_active = False
            model.is_active = True
        else:
            model.is_active = False
        db.commit()
        bust_caches()
    finally:
        db.close()


def compare_models() -> dict:
    from app.models.orm import ModelArtifact, TrainingExperiment

    db = get_db_session()
    try:
        models = db.query(ModelArtifact).order_by(ModelArtifact.id.asc()).all()
        rows = []
        for m in models:
            test = (m.metrics or {}).get("test") or {}
            rows.append(
                {
                    "model_id": m.id,
                    "name": m.name,
                    "version": m.version,
                    "architecture": m.architecture,
                    "accuracy": test.get("accuracy"),
                    "macro_f1": test.get("macro_f1"),
                    "weighted_f1": test.get("weighted_f1"),
                    "train_time_sec": (m.metrics or {}).get("train_time_sec"),
                    "is_active": m.is_active,
                }
            )
        experiments = db.query(TrainingExperiment).order_by(TrainingExperiment.id.desc()).limit(50).all()
        return {
            "models": rows,
            "experiments": [
                {
                    "experiment_id": e.experiment_id,
                    "model_type": e.model_type,
                    "results": e.results,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in experiments
            ],
        }
    finally:
        db.close()


def model_evaluation(model_id: int) -> dict:
    from app.models.orm import ModelArtifact, ModelEvaluation

    db = get_db_session()
    try:
        model = db.query(ModelArtifact).filter(ModelArtifact.id == model_id).first()
        if not model:
            raise ValueError("Model not found")
        evals = db.query(ModelEvaluation).filter(ModelEvaluation.model_id == model_id).all()
        return {
            "model": {
                "id": model.id,
                "name": model.name,
                "version": model.version,
                "architecture": model.architecture,
                "metrics": model.metrics,
            },
            "evaluations": [
                {
                    "id": e.id,
                    "split": e.split,
                    "metrics": e.metrics,
                    "confusion_matrix": e.confusion_matrix,
                    "misclassified": e.misclassified,
                }
                for e in evals
            ],
        }
    finally:
        db.close()


def research_dashboard() -> dict:
    from app.services.research_service import research_dashboard as _dash

    db = get_db_session()
    try:
        return _dash(db)
    finally:
        db.close()


def list_notes() -> dict:
    from app.models.orm import ResearchNote
    from app.services.research_service import NOTE_CATEGORIES

    db = get_db_session()
    try:
        notes = db.query(ResearchNote).order_by(ResearchNote.id.desc()).all()
        return {
            "categories": NOTE_CATEGORIES,
            "notes": [
                {
                    "id": n.id,
                    "title": n.title,
                    "category": n.category,
                    "content": n.content,
                    "tags": n.tags,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in notes
            ],
        }
    finally:
        db.close()


def create_note(title: str, category: str, content: str) -> int:
    from app.models.orm import ResearchNote

    db = get_db_session()
    try:
        note = ResearchNote(title=title, category=category, content=content)
        db.add(note)
        db.commit()
        db.refresh(note)
        return note.id
    finally:
        db.close()


def delete_note(note_id: int) -> None:
    from app.models.orm import ResearchNote

    db = get_db_session()
    try:
        note = db.query(ResearchNote).filter(ResearchNote.id == note_id).first()
        if note:
            db.delete(note)
            db.commit()
    finally:
        db.close()


def list_papers() -> list[dict]:
    from app.models.orm import ResearchPaper

    db = get_db_session()
    try:
        papers = db.query(ResearchPaper).order_by(ResearchPaper.id.desc()).all()
        return [
            {
                "id": p.id,
                "title": p.title,
                "authors": p.authors,
                "year": p.year,
                "venue": p.venue,
                "findings": p.findings,
                "relevance": p.relevance,
            }
            for p in papers
        ]
    finally:
        db.close()


def create_paper(payload: dict) -> int:
    from app.models.orm import ResearchPaper

    db = get_db_session()
    try:
        paper = ResearchPaper(**payload)
        db.add(paper)
        db.commit()
        db.refresh(paper)
        return paper.id
    finally:
        db.close()


def list_experiments() -> list[dict]:
    from app.models.orm import TrainingExperiment

    db = get_db_session()
    try:
        exps = db.query(TrainingExperiment).order_by(TrainingExperiment.id.desc()).limit(100).all()
        return [
            {
                "experiment_id": e.experiment_id,
                "job_id": e.job_id,
                "model_type": e.model_type,
                "hypothesis": e.hypothesis,
                "research_question": e.research_question,
                "dataset_version_id": e.dataset_version_id,
                "preprocessing": e.preprocessing,
                "hyperparameters": e.hyperparameters,
                "results": e.results,
                "error_observations": e.error_observations,
                "conclusion": e.conclusion,
                "future_improvements": e.future_improvements,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in exps
        ]
    finally:
        db.close()


def methodology() -> dict:
    from app.services.research_service import get_or_create_methodology

    db = get_db_session()
    try:
        return get_or_create_methodology(db)
    finally:
        db.close()


def export_report(report_type: str = "complete", fmt: str = "markdown") -> dict:
    from app.services.research_service import export_report as _export

    db = get_db_session()
    try:
        return _export(db, report_type=report_type, fmt=fmt)
    finally:
        db.close()


def app_settings() -> dict:
    from app.core.config import settings
    from app.core.runtime_settings import refresh_runtime_overrides
    from app.models.orm import ApplicationSetting

    db = get_db_session()
    try:
        runtime = refresh_runtime_overrides(db)
        rows = db.query(ApplicationSetting).all()
        stored = {r.key: r.value for r in rows}
        return {
            "app_name": settings.app_name,
            "database_url": settings.database_url,
            "cs_min_tokens_per_language": runtime["cs_min_tokens_per_language"],
            "cs_min_confidence": runtime["cs_min_confidence"],
            "default_split": {
                "train": runtime["default_train_ratio"],
                "val": runtime["default_val_ratio"],
                "test": runtime["default_test_ratio"],
            },
            "random_seed": runtime["random_seed"],
            "zero_paid_resources": True,
            "file_defaults": {
                "cs_min_tokens_per_language": settings.cs_min_tokens_per_language,
                "cs_min_confidence": settings.cs_min_confidence,
                "default_train_ratio": settings.default_train_ratio,
                "default_val_ratio": settings.default_val_ratio,
                "default_test_ratio": settings.default_test_ratio,
                "random_seed": settings.random_seed,
            },
            "stored": stored,
        }
    finally:
        db.close()


def save_runtime_settings(values: dict) -> dict:
    from app.core.runtime_settings import save_runtime_overrides

    db = get_db_session()
    try:
        saved = save_runtime_overrides(db, values)
        bust_caches()
        return saved
    finally:
        db.close()


def update_experiment_notes(
    experiment_id: str,
    *,
    conclusion: str | None = None,
    error_observations: str | None = None,
    future_improvements: str | None = None,
    hypothesis: str | None = None,
    research_question: str | None = None,
) -> dict:
    from app.models.orm import TrainingExperiment

    db = get_db_session()
    try:
        exp = (
            db.query(TrainingExperiment)
            .filter(TrainingExperiment.experiment_id == experiment_id)
            .first()
        )
        if not exp:
            raise ValueError("Experiment not found")
        if conclusion is not None:
            exp.conclusion = conclusion.strip() or None
        if error_observations is not None:
            exp.error_observations = error_observations.strip() or None
        if future_improvements is not None:
            exp.future_improvements = future_improvements.strip() or None
        if hypothesis is not None:
            exp.hypothesis = hypothesis.strip() or None
        if research_question is not None:
            exp.research_question = research_question.strip() or None
        db.commit()
        return {
            "experiment_id": exp.experiment_id,
            "conclusion": exp.conclusion,
            "error_observations": exp.error_observations,
            "future_improvements": exp.future_improvements,
            "hypothesis": exp.hypothesis,
            "research_question": exp.research_question,
        }
    finally:
        db.close()


def batch_analyze_texts(
    texts: list[str],
    *,
    use_preprocessing: bool = True,
    model_override: str | None = None,
    line_offset: int = 0,
) -> list[dict]:
    """Analyze many lines; returns one row dict per non-empty line."""
    from app.nlp.analyzer import analyze_text as _analyze

    rows: list[dict] = []
    db = get_db_session()
    try:
        for i, raw in enumerate(texts):
            text = (raw or "").strip()
            if not text:
                continue
            try:
                result = _analyze(
                    text,
                    use_preprocessing=use_preprocessing,
                    model_override=model_override,
                    db_session=db,
                )
                summary = result.get("summary") or {}
                cs = result.get("code_switching") or {}
                tokens = result.get("tokens") or []
                rows.append(
                    {
                        "line": line_offset + i + 1,
                        "text": text,
                        "cs_status": cs.get("status"),
                        "detected_languages": ",".join(cs.get("detected_languages") or []),
                        "total_words": summary.get("total_words"),
                        "roman_urdu": summary.get("roman_urdu"),
                        "english": summary.get("english"),
                        "ambiguous": summary.get("ambiguous"),
                        "unknown": summary.get("unknown"),
                        "token_labels": " ".join(
                            f"{t.get('token')}/{t.get('label')}" for t in tokens
                        ),
                    }
                )
            except Exception as exc:
                rows.append(
                    {
                        "line": line_offset + i + 1,
                        "text": text,
                        "cs_status": "ERROR",
                        "detected_languages": "",
                        "total_words": None,
                        "roman_urdu": None,
                        "english": None,
                        "ambiguous": None,
                        "unknown": None,
                        "token_labels": str(exc),
                    }
                )
        return rows
    finally:
        db.close()


def export_annotations(
    dataset_id: int,
    *,
    fmt: str = "csv",
    unlabeled_only: bool = False,
    max_records: int | None = None,
) -> tuple[str, str, str]:
    """
    Export annotations for a dataset.
    Returns (filename, mime, content_str).
    """
    import csv
    import io
    import json

    records = list_records(
        dataset_id,
        unlabeled_only=unlabeled_only,
        offset=0,
        limit=max_records,
    )
    if fmt == "jsonl":
        buf = io.StringIO()
        for rec in records:
            buf.write(
                json.dumps(
                    {
                        "sentence_id": rec["sentence_id"],
                        "text": rec["text"],
                        "split": rec.get("split"),
                        "tokens": [
                            {
                                "position": a["position"],
                                "token": a["token"],
                                "label": a["label"],
                                "uncertain": a.get("uncertain"),
                            }
                            for a in rec.get("annotations") or []
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        return f"annotations_ds{dataset_id}.jsonl", "application/x-ndjson", buf.getvalue()

    # CSV: one row per token (flat)
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=[
            "sentence_id",
            "text",
            "split",
            "position",
            "token",
            "label",
            "uncertain",
        ],
    )
    writer.writeheader()
    for rec in records:
        anns = rec.get("annotations") or []
        if not anns:
            writer.writerow(
                {
                    "sentence_id": rec["sentence_id"],
                    "text": rec["text"],
                    "split": rec.get("split") or "",
                    "position": "",
                    "token": "",
                    "label": "",
                    "uncertain": "",
                }
            )
            continue
        for a in anns:
            writer.writerow(
                {
                    "sentence_id": rec["sentence_id"],
                    "text": rec["text"],
                    "split": rec.get("split") or "",
                    "position": a["position"],
                    "token": a["token"],
                    "label": a["label"],
                    "uncertain": a.get("uncertain"),
                }
            )
    return f"annotations_ds{dataset_id}.csv", "text/csv", buf.getvalue()
