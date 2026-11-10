from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_lib.bootstrap import init_app
from streamlit_lib.cache import cached_list_models, clear_data_caches
from streamlit_lib.data_access import set_model_active
from streamlit_lib.formatters import format_datetime, format_metric, format_model_type, format_model_version
from streamlit_lib.ui import inject_base_css, metric_row, page_header, shimmer_block

st.set_page_config(page_title="Models", layout="wide")
init_app()
inject_base_css()

page_header(
    "Model Registry",
    "Activate or deactivate trained artifacts. Dictionary baseline is always available as fallback.",
)

skel = st.empty()
with skel.container():
    shimmer_block(2)
with st.spinner("Loading model registry…"):
    data = cached_list_models()
skel.empty()

models = data.get("models") or []
fallback = data.get("fallback") or {}
st.caption(
    f"Fallback when nothing is active: **{fallback.get('name')}** "
    f"({format_model_version(fallback.get('version'))})"
)

if not models:
    st.info("No trained models registered yet. Train a model in the Training page first.")
    st.stop()

rows = []
for m in models:
    test = ((m.get("metrics") or {}).get("test")) or {}
    rows.append(
        {
            "ID": m["id"],
            "Name": m["name"],
            "Version": format_model_version(m["version"]),
            "Architecture": format_model_type(m["architecture"]),
            "Macro F1": format_metric(test.get("macro_f1")),
            "Active": "yes" if m.get("is_active") else "",
            "Created": format_datetime(m.get("created_at")),
        }
    )
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

model_id = st.selectbox(
    "Select model",
    options=[m["id"] for m in models],
    format_func=lambda mid: next(
        f"{m['name']} · {format_model_version(m['version'])}"
        + (" ★ active" if m.get("is_active") else "")
        for m in models
        if m["id"] == mid
    ),
)
selected = next(m for m in models if m["id"] == model_id)

c1, c2 = st.columns(2)
if c1.button("Activate", type="primary", disabled=bool(selected.get("is_active"))):
    try:
        set_model_active(model_id, True)
        clear_data_caches()
        st.success("Activated — Analyzer will use this model")
        st.rerun()
    except Exception as exc:
        st.error(str(exc))
if c2.button("Deactivate", disabled=not selected.get("is_active")):
    try:
        set_model_active(model_id, False)
        clear_data_caches()
        st.success("Deactivated — dictionary baseline will be used")
        st.rerun()
    except Exception as exc:
        st.error(str(exc))

st.markdown("### Selected model")
h1, h2, h3, h4 = st.columns(4)
h1.metric("Architecture", format_model_type(selected.get("architecture")))
h2.metric("Version", format_model_version(selected.get("version")))
h3.metric("Status", "Active" if selected.get("is_active") else "Inactive")
h4.metric("Created", format_datetime(selected.get("created_at")))

metrics = selected.get("metrics") or {}
if not metrics:
    st.info(
        "No metrics stored for this model yet. Metrics appear after a completed training/evaluation run."
    )
else:
    test = metrics.get("test") if isinstance(metrics.get("test"), dict) else {}
    val = metrics.get("val") if isinstance(metrics.get("val"), dict) else {}
    train = metrics.get("train") if isinstance(metrics.get("train"), dict) else {}

    st.markdown("#### Test metrics")
    if test:
        metric_row(
            [
                ("Accuracy", format_metric(test.get("accuracy"))),
                ("Macro F1", format_metric(test.get("macro_f1"))),
                ("Weighted F1", format_metric(test.get("weighted_f1"))),
                (
                    "Train time (s)",
                    format_metric(metrics.get("train_time_sec"))
                    if metrics.get("train_time_sec") is not None
                    else "—",
                ),
            ],
            compact=False,
        )
    else:
        st.caption("No test metrics on this artifact.")

    vcol, tcol = st.columns(2)
    with vcol:
        st.markdown("#### Validation")
        if val:
            st.write(
                f"- Accuracy: **{format_metric(val.get('accuracy'))}**\n"
                f"- Macro F1: **{format_metric(val.get('macro_f1'))}**\n"
                f"- Weighted F1: **{format_metric(val.get('weighted_f1'))}**"
            )
        else:
            st.caption("No validation metrics.")
    with tcol:
        st.markdown("#### Train")
        if train:
            st.write(
                f"- Accuracy: **{format_metric(train.get('accuracy'))}**\n"
                f"- Macro F1: **{format_metric(train.get('macro_f1'))}**\n"
                f"- Weighted F1: **{format_metric(train.get('weighted_f1'))}**"
            )
        else:
            st.caption("No train metrics.")

    cm = test.get("confusion_matrix") if test else None
    if cm:
        st.markdown("#### Confusion matrix (test)")
        if isinstance(cm, dict):
            labels = cm.get("labels")
            matrix = cm.get("matrix") or cm.get("data") or cm
            if isinstance(matrix, list):
                st.dataframe(
                    pd.DataFrame(matrix, index=labels or None, columns=labels or None),
                    use_container_width=True,
                )
            else:
                # label -> counts map
                rows_cm = []
                if all(isinstance(v, dict) for v in cm.values()):
                    for true_lab, preds in cm.items():
                        if true_lab in {"labels", "matrix", "data"}:
                            continue
                        for pred_lab, count in preds.items():
                            rows_cm.append(
                                {"True": true_lab, "Predicted": pred_lab, "Count": count}
                            )
                    if rows_cm:
                        st.dataframe(pd.DataFrame(rows_cm), use_container_width=True, hide_index=True)
                    else:
                        st.write(cm)
                else:
                    st.write(cm)
        else:
            st.write(cm)

    # Extra non-split keys as a simple table (not JSON)
    extra = {
        k: v
        for k, v in metrics.items()
        if k not in {"train", "val", "test", "confusion_matrix"} and not isinstance(v, (dict, list))
    }
    if extra:
        st.markdown("#### Other stored values")
        st.dataframe(
            pd.DataFrame([{"Field": k, "Value": str(v)} for k, v in extra.items()]),
            use_container_width=True,
            hide_index=True,
        )
