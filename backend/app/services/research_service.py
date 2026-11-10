from __future__ import annotations

from datetime import datetime

from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.orm import (
    ApplicationSetting,
    Dataset,
    ModelArtifact,
    ResearchFinding,
    ResearchNote,
    ResearchPaper,
    TrainingExperiment,
)


METHODOLOGY_DRAFT = {
    "title": "Urdu-English Code-Switching Analyzer — Methodology (DRAFT)",
    "disclaimer": "This document is a draft template. Do not treat it as experimental results.",
    "sections": {
        "1_introduction": "This research investigates word-level identification of Roman Urdu and English in code-switched text.",
        "2_problem_statement": "Mixed Roman Urdu–English sentences make language ID non-trivial due to shared Latin script and spelling variation.",
        "3_objectives": [
            "Detect Roman Urdu and English tokens in mixed sentences",
            "Measure code-switching with a transparent evidence policy",
            "Train and compare free local classifiers on annotated data",
        ],
        "4_research_questions": [
            "RQ1: How accurately can dictionary and classical ML models identify Roman Urdu vs English tokens?",
            "RQ2: How do Roman Urdu spelling variants affect classification errors?",
            "RQ3: When should a sentence be labeled code-switched vs insufficient evidence?",
        ],
        "5_related_work": "Populate manually from freely accessible papers in the Literature Review module. Do not invent citations.",
        "6_dataset_description": "Use only locally created or openly licensed datasets documented in FREE_RESOURCES.md.",
        "7_data_collection": "Manual annotation and optional import of public datasets after license verification.",
        "8_annotation_guidelines": "See docs/ANNOTATION_GUIDE.md.",
        "9_preprocessing": "Unicode normalization, tokenization, optional Roman Urdu spelling map (configurable).",
        "10_feature_engineering": "Word TF-IDF, character n-grams, combined features.",
        "11_model_architecture": "Dictionary baseline; TF-IDF+LogReg; TF-IDF+LinearSVM; MultinomialNB.",
        "12_experimental_setup": "CPU-only local training; reproducible seeds; train/val/test split without test leakage into tuning.",
        "13_evaluation_metrics": "Accuracy, precision, recall, F1, macro/weighted F1, confusion matrix.",
        "14_results": "No fabricated results. Fill after real experiments.",
        "15_error_analysis": "Inspect misclassified tokens after evaluation runs.",
        "16_discussion": "To be written from actual findings.",
        "17_limitations": "Small annotated sets, lexicon coverage gaps, context-blind token classifiers.",
        "18_conclusion": "To be written after experiments.",
        "19_future_work": "Context models / CRF / optional local transformers only if justified.",
    },
}


NOTE_CATEGORIES = [
    "Literature Review",
    "Research Questions",
    "Dataset Collection",
    "Data Annotation",
    "Preprocessing",
    "Feature Engineering",
    "Model Selection",
    "Training Experiments",
    "Evaluation",
    "Error Analysis",
    "Limitations",
    "Future Work",
    "Research Findings",
]


def get_or_create_methodology(db: Session) -> dict:
    row = db.query(ApplicationSetting).filter(ApplicationSetting.key == "methodology").first()
    if not row:
        row = ApplicationSetting(key="methodology", value=METHODOLOGY_DRAFT)
        db.add(row)
        db.commit()
    return row.value


def save_methodology(db: Session, value: dict) -> dict:
    row = db.query(ApplicationSetting).filter(ApplicationSetting.key == "methodology").first()
    if not row:
        row = ApplicationSetting(key="methodology", value=value)
        db.add(row)
    else:
        row.value = value
        row.updated_at = datetime.utcnow()
    db.commit()
    return value


def research_dashboard(db: Session) -> dict:
    notes = db.query(ResearchNote).count()
    papers = db.query(ResearchPaper).count()
    experiments = db.query(TrainingExperiment).count()
    models = db.query(ModelArtifact).count()
    active = db.query(ModelArtifact).filter(ModelArtifact.is_active.is_(True)).first()
    best = None
    for m in db.query(ModelArtifact).all():
        macro = None
        if m.metrics and isinstance(m.metrics, dict):
            test = m.metrics.get("test") or {}
            macro = test.get("macro_f1")
        if macro is None:
            continue
        if best is None or macro > best["macro_f1"]:
            best = {"model_id": m.id, "name": m.name, "version": m.version, "macro_f1": macro}

    findings = (
        db.query(ResearchFinding)
        .order_by(ResearchFinding.id.desc())
        .limit(10)
        .all()
    )
    return {
        "research_title": "Urdu-English Code-Switching Analyzer",
        "objectives": METHODOLOGY_DRAFT["sections"]["3_objectives"],
        "research_questions": METHODOLOGY_DRAFT["sections"]["4_research_questions"],
        "dataset_count": db.query(Dataset).count(),
        "notes": notes,
        "papers": papers,
        "completed_experiments": experiments,
        "trained_models": models,
        "best_evaluated_model": best,
        "active_model": (
            {"id": active.id, "name": active.name, "version": active.version}
            if active
            else {"name": "dictionary-baseline", "version": "dictionary-baseline-v1"}
        ),
        "latest_findings": [
            {
                "id": f.id,
                "title": f.title,
                "is_hypothesis": f.is_hypothesis,
                "content": f.content,
            }
            for f in findings
        ],
        "note_categories": NOTE_CATEGORIES,
    }


def _fmt_num(value, digits: int = 3) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _split_block_lines(title: str, block: dict) -> list[str]:
    """Readable markdown for one train/val/test metrics block."""
    if not isinstance(block, dict) or not block:
        return []
    lines = [
        f"#### {title}",
        f"- Accuracy: {_fmt_num(block.get('accuracy'))}",
        f"- Macro F1: {_fmt_num(block.get('macro_f1'))}",
        f"- Weighted F1: {_fmt_num(block.get('weighted_f1'))}",
    ]
    if block.get("n_samples") is not None:
        lines.append(f"- Samples: {block.get('n_samples')}")
    if block.get("inference_time_sec") is not None:
        lines.append(f"- Inference time (s): {_fmt_num(block.get('inference_time_sec'), 4)}")

    per_class = block.get("per_class")
    if isinstance(per_class, dict) and per_class:
        lines.append("")
        lines.append("| Label | Precision | Recall | F1 | Support |")
        lines.append("|---|---:|---:|---:|---:|")
        for label, row in sorted(per_class.items()):
            if not isinstance(row, dict):
                continue
            f1 = row.get("f1", row.get("f1-score"))
            lines.append(
                f"| {label} | {_fmt_num(row.get('precision'))} | {_fmt_num(row.get('recall'))} "
                f"| {_fmt_num(f1)} | {row.get('support', '—')} |"
            )

    cm = block.get("confusion_matrix")
    if isinstance(cm, dict):
        labels = cm.get("labels") or []
        matrix = cm.get("matrix")
        if isinstance(matrix, list) and labels:
            lines.append("")
            lines.append("Confusion matrix (rows = true, cols = predicted):")
            header = "| True \\ Pred | " + " | ".join(str(lab) for lab in labels) + " |"
            sep = "|---|" + "|".join(["---:"] * len(labels)) + "|"
            lines.append(header)
            lines.append(sep)
            for i, lab in enumerate(labels):
                row = matrix[i] if i < len(matrix) else []
                cells = " | ".join(str(row[j]) if j < len(row) else "0" for j in range(len(labels)))
                lines.append(f"| {lab} | {cells} |")
    return lines


def format_experiment_results_md(results) -> list[str]:
    """Turn stored experiment results JSON into readable markdown lines."""
    if not results:
        return ["_No results stored._"]
    if not isinstance(results, dict):
        return [f"- Results: `{results}`"]

    lines: list[str] = []
    if results.get("train_time_sec") is not None:
        lines.append(f"- Train time (s): {_fmt_num(results.get('train_time_sec'), 4)}")

    for key, title in (("test", "Test"), ("val", "Validation"), ("train", "Train")):
        block = results.get(key)
        if isinstance(block, dict) and block:
            lines.append("")
            lines.extend(_split_block_lines(title, block))

    # Any leftover top-level keys (skip known structured ones)
    known = {"train_time_sec", "test", "val", "train"}
    extras = {k: v for k, v in results.items() if k not in known}
    if extras:
        lines.append("")
        lines.append("Other fields:")
        for k, v in extras.items():
            if isinstance(v, (dict, list)):
                lines.append(f"- {k}: _(structured; see Experiments page)_")
            else:
                lines.append(f"- {k}: {v}")
    return lines or ["_No numeric metrics stored._"]


def format_model_metrics_md(metrics) -> str:
    if not metrics:
        return "no metrics"
    if not isinstance(metrics, dict):
        return str(metrics)
    test = metrics.get("test") if isinstance(metrics.get("test"), dict) else metrics
    if not isinstance(test, dict):
        return "metrics stored"
    parts = []
    for key, label in (("accuracy", "acc"), ("macro_f1", "macro-F1"), ("weighted_f1", "w-F1")):
        if test.get(key) is not None:
            parts.append(f"{label}={_fmt_num(test.get(key))}")
    return ", ".join(parts) if parts else "metrics stored"


def export_report(db: Session, report_type: str, fmt: str = "markdown") -> dict:
    settings.artifacts_dir.joinpath("exports").mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dash = research_dashboard(db)
    experiments = db.query(TrainingExperiment).order_by(TrainingExperiment.id.desc()).limit(50).all()
    models = db.query(ModelArtifact).all()

    active = dash.get("active_model") or {}
    best = dash.get("best_evaluated_model")
    if isinstance(best, dict):
        best_txt = f"{best.get('name')} (macro F1 {_fmt_num(best.get('macro_f1'))})"
    else:
        best_txt = str(best) if best else "—"

    lines = [
        f"# {report_type.replace('_', ' ').title()} Report",
        "",
        f"Generated: {stamp} UTC",
        "",
        "> Distinction: sections labeled HYPOTHESIS/DRAFT are not experimental results.",
        "",
        "## Research Snapshot",
        f"- Datasets: {dash['dataset_count']}",
        f"- Experiments: {dash['completed_experiments']}",
        f"- Models: {dash['trained_models']}",
        f"- Active model: {active.get('name', '—')} · {active.get('version', '—')}",
        f"- Best macro F1 (from stored evals): {best_txt}",
        "",
    ]

    if report_type in {"complete", "training", "model_comparison"}:
        lines.append("## Experiments (actual stored records)")
        if not experiments:
            lines.append("_No completed experiments stored yet._")
        for e in experiments:
            lines.append(f"### {e.experiment_id} — {e.model_type}")
            if e.hypothesis:
                lines.append(f"- Hypothesis: {e.hypothesis}")
            if e.research_question:
                lines.append(f"- Research question: {e.research_question}")
            if e.conclusion:
                lines.append(f"- Conclusion: {e.conclusion}")
            lines.append(f"- Dataset version: {e.dataset_version_id or '—'}")
            lines.extend(format_experiment_results_md(e.results))
            lines.append("")

    if report_type in {"complete", "model_comparison"}:
        lines.append("## Model Registry")
        if not models:
            lines.append("_No models registered yet._")
        for m in models:
            status = "active" if m.is_active else "inactive"
            lines.append(
                f"- **{m.name}** {m.version} ({m.architecture}) — {status}; "
                f"{format_model_metrics_md(m.metrics)}"
            )

    if report_type == "complete":
        lines.append("")
        lines.append("## Methodology (DRAFT)")
        method = get_or_create_methodology(db)
        lines.append(f"**{method.get('title') or 'Methodology'}**")
        lines.append("")
        lines.append(method.get("disclaimer") or "")
        sections = method.get("sections") or {}
        for key, value in sections.items():
            title = key.replace("_", " ").title()
            lines.append(f"### {title}")
            if isinstance(value, list):
                for item in value:
                    lines.append(f"- {item}")
            else:
                lines.append(str(value) if value else "_Empty_")
            lines.append("")

    text = "\n".join(lines)
    base = settings.artifacts_dir / "exports" / f"{report_type}_{stamp}"
    md_path = base.with_suffix(".md")
    md_path.write_text(text, encoding="utf-8")
    paths = {"markdown": str(md_path)}

    if fmt in {"docx", "all"}:
        doc = Document()
        for line in lines:
            doc.add_paragraph(line)
        docx_path = base.with_suffix(".docx")
        doc.save(docx_path)
        paths["docx"] = str(docx_path)

    if fmt in {"pdf", "all"}:
        pdf_path = base.with_suffix(".pdf")
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        width, height = letter
        y = height - 40
        for line in lines:
            if y < 40:
                c.showPage()
                y = height - 40
            c.drawString(40, y, line[:110])
            y -= 12
        c.save()
        paths["pdf"] = str(pdf_path)

    return {"report_type": report_type, "paths": paths}
