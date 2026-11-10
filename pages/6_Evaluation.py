from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_lib.bootstrap import init_app
from streamlit_lib.cache import cached_compare_models
from streamlit_lib.data_access import model_evaluation
from streamlit_lib.formatters import format_metric, format_model_type, format_model_version
from streamlit_lib.ui import inject_base_css, metric_row, page_header, shimmer_block


def confusion_matrix_df(cm) -> pd.DataFrame | None:
    """Turn stored confusion matrix JSON into a labeled table (rows=true, cols=pred)."""
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

    # Nested dict: {true: {pred: count}}
    nested = {k: v for k, v in cm.items() if k not in {"labels", "matrix", "data"} and isinstance(v, dict)}
    if nested:
        all_labels = sorted({*nested.keys(), *[p for row in nested.values() for p in row.keys()]})
        data = []
        for true_lab in all_labels:
            data.append([int(nested.get(true_lab, {}).get(pred_lab, 0)) for pred_lab in all_labels])
        df = pd.DataFrame(data, index=all_labels, columns=all_labels)
        df.index.name = "True \\ Pred"
        return df
    return None


def misclassified_df(items: list) -> pd.DataFrame:
    rows = []
    for i, item in enumerate(items):
        if isinstance(item, dict):
            rows.append(
                {
                    "#": i + 1,
                    "Token": item.get("token") or item.get("text") or "—",
                    "True label": item.get("true") or item.get("gold") or item.get("y_true") or "—",
                    "Predicted": item.get("pred") or item.get("y_pred") or "—",
                    "Sentence / context": item.get("sentence") or item.get("context") or item.get("text_full") or "",
                }
            )
        else:
            rows.append({"#": i + 1, "Token": str(item), "True label": "—", "Predicted": "—", "Sentence / context": ""})
    return pd.DataFrame(rows)


st.set_page_config(page_title="Evaluation", layout="wide")
init_app()
inject_base_css()

page_header(
    "Model Evaluation",
    "Metrics come from real held-out predictions stored after local training — never fabricated.",
)

skel = st.empty()
with skel.container():
    shimmer_block(2)
with st.spinner("Loading model comparison…"):
    compare = cached_compare_models()
skel.empty()

models = compare.get("models") or []
if not models:
    st.info("No evaluated models yet. Train a model first.")
    st.stop()

st.dataframe(
    pd.DataFrame(
        [
            {
                "Model": m.get("name"),
                "Version": format_model_version(m.get("version")),
                "Architecture": format_model_type(m.get("architecture")),
                "Accuracy": format_metric(m.get("accuracy")),
                "Macro F1": format_metric(m.get("macro_f1")),
                "Weighted F1": format_metric(m.get("weighted_f1")),
                "Train time (s)": format_metric(m.get("train_time_sec"))
                if m.get("train_time_sec") is not None
                else "—",
            }
            for m in models
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

selected = st.selectbox(
    "Inspect model evaluation",
    options=[m["model_id"] for m in models],
    format_func=lambda mid: next(
        f"{m['name']} · {format_model_version(m['version'])} · {format_model_type(m.get('architecture'))}"
        for m in models
        if m["model_id"] == mid
    ),
)

try:
    with st.spinner("Loading evaluation detail…"):
        detail = model_evaluation(int(selected))
except Exception as exc:
    st.error(str(exc))
    st.stop()

model_info = detail.get("model") or {}
test_metrics = ((model_info.get("metrics") or {}).get("test")) or {}
evals = detail.get("evaluations") or []

st.markdown(
    f"### {model_info.get('name') or 'Model'} · {format_model_version(model_info.get('version'))}"
)
metric_row(
    [
        ("Architecture", format_model_type(model_info.get("architecture"))),
        ("Accuracy", format_metric(test_metrics.get("accuracy"))),
        ("Macro F1", format_metric(test_metrics.get("macro_f1"))),
        ("Weighted F1", format_metric(test_metrics.get("weighted_f1"))),
    ],
    compact=False,
)

cm = None
mis = []
if evals:
    cm = evals[0].get("confusion_matrix")
    mis = (evals[0].get("misclassified") or [])[:50]
if cm is None:
    cm = test_metrics.get("confusion_matrix")

left, right = st.columns(2)

with left:
    st.subheader("Confusion matrix")
    st.caption("Rows = true label · Columns = predicted label")
    df_cm = confusion_matrix_df(cm)
    if df_cm is not None and not df_cm.empty:
        st.dataframe(df_cm, use_container_width=True)
        # Quick correct / wrong summary when square numeric
        try:
            correct = int(pd.to_numeric(pd.Series(df_cm.values.diagonal()), errors="coerce").fillna(0).sum())
            total = int(pd.to_numeric(df_cm.to_numpy().ravel(), errors="coerce").fillna(0).sum())
            wrong = total - correct
            st.write(f"Correct: **{correct}** · Misclassified: **{wrong}** · Total: **{total}**")
        except Exception:
            pass
    else:
        st.info("No confusion matrix stored for this model yet.")

with right:
    st.subheader("Misclassified examples")
    st.caption("Tokens where the model prediction disagreed with the gold label")
    if mis:
        st.dataframe(misclassified_df(mis), use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(mis)} example(s).")
    else:
        st.success("No misclassified examples stored (or none available for this evaluation).")
