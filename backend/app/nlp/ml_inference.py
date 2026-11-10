from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from app.nlp.dictionary_classifier import Prediction
from app.nlp.labels import TokenLabel
from app.nlp.tokenizer import Token


def try_predict_with_active_model(
    tokens: list[Token],
    normalized_texts: list[str],
    db_session: Any | None,
) -> tuple[list[Prediction] | None, dict]:
    """Load active sklearn model from registry if present. Never fabricates probabilities."""
    meta = {"name": "dictionary-baseline", "version": "dictionary-baseline-v1", "source": "dictionary"}
    if db_session is None:
        return None, meta

    try:
        from app.models.orm import ModelArtifact

        active = (
            db_session.query(ModelArtifact)
            .filter(ModelArtifact.is_active.is_(True))
            .order_by(ModelArtifact.id.desc())
            .first()
        )
    except Exception:
        return None, meta

    if not active:
        return None, meta

    path = Path(active.artifact_path)
    if not path.exists():
        return None, meta

    try:
        bundle = joblib.load(path)
        pipeline = bundle["pipeline"]
        labels = bundle.get("labels", [])
        model_version = f"{active.name}-{active.version}"
    except Exception:
        return None, meta

    word_indices = [i for i, t in enumerate(tokens) if t.kind == "word"]
    features = [normalized_texts[i] if i < len(normalized_texts) else tokens[i].text for i in word_indices]
    if not features:
        preds = [
            Prediction(
                token=t.text,
                label=TokenLabel.OTHER,
                confidence=1.0,
                position=t.position,
                model_version=model_version,
                kind=t.kind,
            )
            for t in tokens
        ]
        return preds, {
            "name": active.name,
            "version": active.version,
            "architecture": active.architecture,
            "source": "ml-active",
            "model_id": active.id,
        }

    y_pred = pipeline.predict(features)
    confidences: list[float | None]
    if hasattr(pipeline, "predict_proba"):
        try:
            proba = pipeline.predict_proba(features)
            confidences = [float(max(row)) for row in proba]
        except Exception:
            confidences = [None] * len(features)
    else:
        confidences = [None] * len(features)

    pred_by_index: dict[int, Prediction] = {}
    for idx, feat_i in enumerate(word_indices):
        label_raw = y_pred[idx]
        try:
            label = TokenLabel(str(label_raw))
        except ValueError:
            label = TokenLabel.UNKNOWN
        alt = None
        if confidences[idx] is not None and hasattr(pipeline, "predict_proba"):
            try:
                row = pipeline.predict_proba([features[idx]])[0]
                classes = list(pipeline.classes_)
                ranked = sorted(zip(classes, row), key=lambda x: x[1], reverse=True)
                if len(ranked) > 1:
                    alt = str(ranked[1][0])
            except Exception:
                alt = None
        pred_by_index[feat_i] = Prediction(
            token=tokens[feat_i].text,
            label=label,
            confidence=confidences[idx],
            position=tokens[feat_i].position,
            model_version=model_version,
            alternative=alt,
            kind=tokens[feat_i].kind,
        )

    preds = []
    for i, t in enumerate(tokens):
        if i in pred_by_index:
            preds.append(pred_by_index[i])
        else:
            preds.append(
                Prediction(
                    token=t.text,
                    label=TokenLabel.OTHER,
                    confidence=1.0,
                    position=t.position,
                    model_version=model_version,
                    kind=t.kind,
                )
            )

    return preds, {
        "name": active.name,
        "version": active.version,
        "architecture": active.architecture,
        "source": "ml-active",
        "model_id": active.id,
        "label_space": labels,
    }
