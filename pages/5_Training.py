from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_lib.bootstrap import init_app
from streamlit_lib.cache import cached_list_datasets, clear_data_caches
from streamlit_lib.data_access import cancel_training_job, list_training_jobs, start_training
from streamlit_lib.formatters import format_datetime, format_metric, format_model_type
from streamlit_lib.ui import inject_base_css, metric_row, page_header, shimmer_block

st.set_page_config(page_title="Training", layout="wide")
init_app()
inject_base_css()

page_header(
    "Model Training Laboratory",
    "Local CPU training only. Analyzer stays available while jobs run in a background thread.",
)

skel = st.empty()
with skel.container():
    shimmer_block(2)
with st.spinner("Loading datasets & jobs…"):
    datasets = cached_list_datasets()
    jobs = list_training_jobs()
skel.empty()

version_options = [
    (d["latest_version"]["id"], f"{d['name']} ({d['latest_version']['version']})")
    for d in datasets
    if d.get("latest_version")
]
if not version_options:
    st.warning("Need a dataset version before training.")
    st.stop()

version_id = st.selectbox(
    "Dataset version",
    options=[v[0] for v in version_options],
    format_func=lambda vid: next(label for v, label in version_options if v == vid),
)
model_type = st.selectbox(
    "Model type",
    options=["logreg", "linearsvm", "naive_bayes"],
    format_func=lambda m: {
        "logreg": "TF-IDF + Logistic Regression",
        "linearsvm": "TF-IDF + Linear SVM",
        "naive_bayes": "Naive Bayes",
    }[m],
)
confirm_large = st.checkbox("Confirm large run if dataset is big (>5000 tokens)", value=False)

st.markdown("##### Research context (optional but recommended)")
st.caption(
    "These fields are stored on the experiment record and shown under Experiments → Research context. "
    "Past runs are empty because training was started without them."
)
hypothesis = st.text_area(
    "Hypothesis",
    placeholder="e.g. Character n-grams will improve Roman Urdu variant recall vs word TF-IDF alone.",
    height=70,
)
research_question = st.text_area(
    "Research question",
    placeholder="e.g. RQ1: How does LogReg compare to Linear SVM on held-out mixed reviews?",
    height=70,
)

if st.button("Start local training", type="primary"):
    try:
        res = start_training(
            {
                "dataset_version_id": int(version_id),
                "model_type": model_type,
                "confirm_large_run": confirm_large,
                "word_ngram_range": [1, 1],
                "char_ngram_range": [2, 5],
                "use_char": True,
                "use_word": True,
                "random_seed": 42,
                "hypothesis": hypothesis.strip() or None,
                "research_question": research_question.strip() or None,
            }
        )
        clear_data_caches()
        st.success(f"Started job {res['job_id']}")
    except Exception as exc:
        st.error(str(exc))

st.subheader("Jobs")
if st.button("Refresh jobs"):
    st.rerun()

if not jobs:
    st.info("No training jobs yet.")
else:
    rows = []
    for j in jobs:
        rows.append(
            {
                "job_id": j["job_id"],
                "status": j["status"],
                "stage": j.get("stage"),
                "progress": j.get("progress"),
                "model_type": format_model_type(j.get("model_type")),
                "started_at": format_datetime(j.get("started_at")),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    running = [j for j in jobs if j["status"] in {"QUEUED", "RUNNING"}]
    if running:
        job_id = st.selectbox("Cancel job", options=[j["job_id"] for j in running])
        if st.button("Request cancel"):
            try:
                cancel_training_job(job_id)
                st.success("Cancel requested")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    st.markdown("#### Job details")
    st.caption("Open a completed job to see metrics in a readable layout (not raw JSON).")
    for j in jobs[:8]:
        title = (
            f"{j['job_id']} · {j['status']} · {format_model_type(j.get('model_type'))} · "
            f"{format_datetime(j.get('completed_at') or j.get('started_at'))}"
        )
        with st.expander(title):
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Status", j.get("status") or "—")
            m2.metric("Model", format_model_type(j.get("model_type")))
            m3.metric("Dataset version", j.get("dataset_version_id") or "—")
            progress = j.get("progress")
            m4.metric(
                "Progress",
                f"{float(progress) * 100:.0f}%" if isinstance(progress, (int, float)) else "—",
            )

            st.write(
                f"- Stage: **{j.get('stage') or '—'}**\n"
                f"- Started: **{format_datetime(j.get('started_at'), with_seconds=True)}**\n"
                f"- Completed: **{format_datetime(j.get('completed_at'), with_seconds=True)}**"
            )

            metrics = j.get("metrics") or {}
            if metrics:
                test = metrics.get("test") if isinstance(metrics.get("test"), dict) else {}
                val = metrics.get("val") if isinstance(metrics.get("val"), dict) else {}
                train = metrics.get("train") if isinstance(metrics.get("train"), dict) else {}

                st.markdown("**Test metrics**")
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
                    st.caption("No test metrics on this job.")

                c_val, c_train = st.columns(2)
                with c_val:
                    st.markdown("**Validation**")
                    if val:
                        st.write(
                            f"- Accuracy: **{format_metric(val.get('accuracy'))}**\n"
                            f"- Macro F1: **{format_metric(val.get('macro_f1'))}**\n"
                            f"- Weighted F1: **{format_metric(val.get('weighted_f1'))}**"
                        )
                    else:
                        st.caption("No validation metrics.")
                with c_train:
                    st.markdown("**Train**")
                    if train:
                        st.write(
                            f"- Accuracy: **{format_metric(train.get('accuracy'))}**\n"
                            f"- Macro F1: **{format_metric(train.get('macro_f1'))}**\n"
                            f"- Weighted F1: **{format_metric(train.get('weighted_f1'))}**"
                        )
                    else:
                        st.caption("No train metrics.")

                extra = {
                    k: v
                    for k, v in metrics.items()
                    if k not in {"train", "val", "test"} and not isinstance(v, (dict, list))
                }
                if extra:
                    st.markdown("**Other values**")
                    st.dataframe(
                        pd.DataFrame([{"Field": k, "Value": str(v)} for k, v in extra.items()]),
                        use_container_width=True,
                        hide_index=True,
                    )
            else:
                if j.get("status") == "COMPLETED":
                    st.info("Job completed but no metrics payload was stored on this job record.")
                else:
                    st.caption("Metrics appear here after the job completes successfully.")

            if j.get("error_log"):
                st.markdown("**Error log**")
                st.code(j["error_log"])
