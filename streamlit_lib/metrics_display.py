"""Shared readable rendering for stored train/val/test metric blocks."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_lib.formatters import format_metric
from streamlit_lib.ui import metric_row


def per_class_df(per_class) -> pd.DataFrame | None:
    if not isinstance(per_class, dict) or not per_class:
        return None
    rows = []
    for label, row in sorted(per_class.items()):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "Label": label,
                "Precision": format_metric(row.get("precision")),
                "Recall": format_metric(row.get("recall")),
                "F1": format_metric(row.get("f1", row.get("f1-score"))),
                "Support": row.get("support", "—"),
            }
        )
    return pd.DataFrame(rows) if rows else None


def confusion_matrix_df(cm) -> pd.DataFrame | None:
    if not cm:
        return None
    if isinstance(cm, list):
        return pd.DataFrame(cm)
    if not isinstance(cm, dict):
        return None
    labels = cm.get("labels")
    matrix = cm.get("matrix") or cm.get("data")
    if isinstance(matrix, list):
        idx = labels if isinstance(labels, list) and len(labels) == len(matrix) else None
        cols = labels if isinstance(labels, list) and matrix and len(labels) == len(matrix[0]) else None
        df = pd.DataFrame(matrix, index=idx, columns=cols)
        if idx is not None:
            df.index.name = "True \\ Pred"
        return df
    nested = {
        k: v
        for k, v in cm.items()
        if k not in {"labels", "matrix", "data"} and isinstance(v, dict)
    }
    if nested:
        all_labels = sorted({*nested.keys(), *[p for row in nested.values() for p in row.keys()]})
        data = [
            [int(nested.get(true_lab, {}).get(pred_lab, 0)) for pred_lab in all_labels]
            for true_lab in all_labels
        ]
        df = pd.DataFrame(data, index=all_labels, columns=all_labels)
        df.index.name = "True \\ Pred"
        return df
    return None


def render_split_metrics(title: str, block: dict | None, *, show_details: bool = True) -> None:
    """Render accuracy/F1 metrics + optional per-class and confusion matrix."""
    if not isinstance(block, dict) or not block:
        st.caption(f"No {title.lower()} metrics stored.")
        return

    st.markdown(f"##### {title}")
    metric_row(
        [
            ("Accuracy", format_metric(block.get("accuracy"))),
            ("Macro F1", format_metric(block.get("macro_f1"))),
            ("Weighted F1", format_metric(block.get("weighted_f1"))),
            (
                "Samples",
                block.get("n_samples") if block.get("n_samples") is not None else "—",
            ),
        ],
        compact=False,
    )

    if not show_details:
        return

    pc = per_class_df(block.get("per_class"))
    if pc is not None:
        st.markdown("**Per-class**")
        st.dataframe(pc, use_container_width=True, hide_index=True)

    cm_df = confusion_matrix_df(block.get("confusion_matrix"))
    if cm_df is not None:
        st.markdown("**Confusion matrix** (rows = true, cols = predicted)")
        st.dataframe(cm_df, use_container_width=True)


def render_experiment_results(results: dict | None, *, compact: bool = False) -> None:
    """Full results view for one experiment (test / val / train)."""
    if not isinstance(results, dict) or not results:
        st.caption("No results stored for this experiment.")
        return

    if results.get("train_time_sec") is not None:
        st.caption(f"Train time: {format_metric(results.get('train_time_sec'), 4)} s")

    test = results.get("test") if isinstance(results.get("test"), dict) else {}
    val = results.get("val") if isinstance(results.get("val"), dict) else {}
    train = results.get("train") if isinstance(results.get("train"), dict) else {}

    if test:
        render_split_metrics("Test", test, show_details=not compact)
    if val or train:
        c1, c2 = st.columns(2)
        with c1:
            if val:
                render_split_metrics("Validation", val, show_details=not compact)
        with c2:
            if train:
                render_split_metrics("Train", train, show_details=False)
