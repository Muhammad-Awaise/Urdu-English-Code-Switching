from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

from app.core.config import settings


LABELS = ["URDU_ROMAN", "ENGLISH", "AMBIGUOUS", "UNKNOWN"]


@dataclass
class TrainConfig:
    model_type: str = "logreg"  # dictionary|logreg|linearsvm|naive_bayes
    word_ngram_range: tuple[int, int] = (1, 1)
    char_ngram_range: tuple[int, int] = (2, 5)
    C: float = 1.0
    class_weight: str | None = "balanced"
    random_seed: int = 42
    use_char: bool = True
    use_word: bool = True
    max_features: int = 50000
    task: str = "word_lid"


def build_pipeline(cfg: TrainConfig) -> Pipeline:
    transformers = []
    if cfg.use_word:
        transformers.append(
            (
                "word",
                TfidfVectorizer(
                    analyzer="word",
                    ngram_range=cfg.word_ngram_range,
                    min_df=1,
                    max_features=cfg.max_features // 2 if cfg.use_char else cfg.max_features,
                ),
            )
        )
    if cfg.use_char:
        transformers.append(
            (
                "char",
                TfidfVectorizer(
                    analyzer="char",
                    ngram_range=cfg.char_ngram_range,
                    min_df=1,
                    max_features=cfg.max_features // 2 if cfg.use_word else cfg.max_features,
                ),
            )
        )
    if not transformers:
        raise ValueError("At least one of use_word or use_char must be enabled")

    feats = FeatureUnion(transformers) if len(transformers) > 1 else transformers[0][1]

    mt = cfg.model_type.lower()
    if mt == "logreg":
        clf = LogisticRegression(
            C=cfg.C,
            class_weight=cfg.class_weight,
            max_iter=2000,
            random_state=cfg.random_seed,
            solver="lbfgs",
            n_jobs=1,
        )
    elif mt == "linearsvm":
        base = LinearSVC(
            C=cfg.C,
            class_weight=cfg.class_weight,
            random_state=cfg.random_seed,
            dual="auto",
        )
        # Real probabilities via calibration (not fake score mapping).
        # cv folds are chosen later in train_word_lid based on class counts.
        clf = CalibratedClassifierCV(base, method="sigmoid", cv=3)
    elif mt == "naive_bayes":
        clf = MultinomialNB()
    else:
        raise ValueError(f"Unsupported model_type for sklearn training: {cfg.model_type}")

    return Pipeline([("features", feats), ("clf", clf)])


def compute_metrics(y_true: list[str], y_pred: list[str], labels: list[str] | None = None) -> dict:
    labels = labels or sorted(set(y_true) | set(y_pred))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    report = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "per_class": {
            label: {
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i, label in enumerate(labels)
        },
        "classification_report": report,
        "confusion_matrix": {"labels": labels, "matrix": cm.tolist()},
    }


def train_word_lid(
    X_train: list[str],
    y_train: list[str],
    X_val: list[str] | None,
    y_val: list[str] | None,
    X_test: list[str] | None,
    y_test: list[str] | None,
    cfg: TrainConfig,
    artifact_dir: Path | None = None,
    progress_cb=None,
) -> dict[str, Any]:
    if len(X_train) < 4:
        raise ValueError("Need at least 4 labeled training tokens before local ML training.")

    if progress_cb:
        progress_cb("PREPARING", 0.1)

    pipeline = build_pipeline(cfg)
    # Adapt calibration folds for tiny class counts
    if cfg.model_type.lower() == "linearsvm":
        from collections import Counter

        min_count = min(Counter(y_train).values()) if y_train else 1
        cv = max(2, min(3, min_count))
        base = LinearSVC(
            C=cfg.C,
            class_weight=cfg.class_weight,
            random_state=cfg.random_seed,
            dual="auto",
        )
        if min_count < 2:
            pipeline = Pipeline([("features", pipeline.named_steps["features"]), ("clf", base)])
        else:
            pipeline = Pipeline(
                [
                    ("features", pipeline.named_steps["features"]),
                    ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=cv)),
                ]
            )

    t0 = time.perf_counter()
    if progress_cb:
        progress_cb("TRAINING", 0.35)
    pipeline.fit(X_train, y_train)
    train_time = time.perf_counter() - t0

    metrics: dict[str, Any] = {"train_time_sec": train_time}
    misclassified: list[dict] = []

    def eval_split(name: str, X, y):
        nonlocal misclassified
        if not X or not y:
            return
        if progress_cb:
            progress_cb("VALIDATING" if name == "val" else "EVALUATING", 0.7 if name == "val" else 0.85)
        t_inf = time.perf_counter()
        pred = pipeline.predict(X)
        inf = time.perf_counter() - t_inf
        m = compute_metrics(y, list(pred))
        m["inference_time_sec"] = inf
        m["n_samples"] = len(y)
        metrics[name] = m
        if name == "test":
            for xt, yt, yp in zip(X, y, pred):
                if yt != yp:
                    misclassified.append({"token": xt, "true": yt, "pred": str(yp)})

    eval_split("val", X_val, y_val)
    eval_split("test", X_test, y_test)
    # Always report train metrics for transparency (not for model selection)
    train_pred = pipeline.predict(X_train)
    metrics["train"] = compute_metrics(y_train, list(train_pred))

    artifact_dir = artifact_dir or (settings.artifacts_dir / "models")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    name = f"{cfg.model_type}_word_lid"
    path = artifact_dir / f"{name}_{version}.joblib"
    bundle = {
        "pipeline": pipeline,
        "labels": LABELS,
        "config": asdict(cfg),
        "trained_at": version,
        "task": "word_lid",
    }
    joblib.dump(bundle, path)
    size_bytes = path.stat().st_size

    if progress_cb:
        progress_cb("COMPLETED", 1.0)

    return {
        "artifact_path": str(path),
        "name": name,
        "version": version,
        "architecture": cfg.model_type,
        "metrics": metrics,
        "misclassified": misclassified[:200],
        "model_size_bytes": size_bytes,
        "hyperparameters": asdict(cfg),
    }


def new_job_id() -> str:
    return uuid4().hex[:12]
