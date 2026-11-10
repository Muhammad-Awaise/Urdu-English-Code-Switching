from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_lib.bootstrap import init_app
from streamlit_lib.cache import cached_compare_models
from streamlit_lib.data_access import list_experiments, update_experiment_notes
from streamlit_lib.formatters import format_datetime, format_metric, format_model_type
from streamlit_lib.metrics_display import render_experiment_results
from streamlit_lib.ui import configure_page, inject_base_css, page_header, shimmer_block

configure_page("Experiments")
init_app()
inject_base_css()

page_header(
    "Experiments",
    "Compare registered models and inspect completed training experiment records.",
)

st.caption(
    "Experiments are created automatically when a training job finishes. "
    "This page shows stored results in a readable layout (not raw JSON)."
)

skel = st.empty()
with skel.container():
    shimmer_block(2)
with st.spinner("Loading experiments…"):
    compare = cached_compare_models()
    exps = list_experiments()
skel.empty()

models = compare.get("models") or []
if models:
    st.subheader("Registered models")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "name": m.get("name"),
                    "architecture": m.get("architecture"),
                    "accuracy": format_metric(m.get("accuracy")),
                    "macro_f1": format_metric(m.get("macro_f1")),
                    "weighted_f1": format_metric(m.get("weighted_f1")),
                    "active": "yes" if m.get("is_active") else "",
                }
                for m in models
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No models yet. Train a model first.")

st.subheader("Training experiments")
if not exps:
    st.info("No experiments logged yet. Complete a Training Lab run to create one.")
    st.stop()

st.dataframe(
    pd.DataFrame(
        [
            {
                "Experiment": e.get("experiment_id"),
                "Model": format_model_type(e.get("model_type")),
                "Dataset version": e.get("dataset_version_id") or "—",
                "Hypothesis": (e.get("hypothesis") or "—")[:80],
                "Created": format_datetime(e.get("created_at")),
            }
            for e in exps
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

pick = st.selectbox(
    "Select experiment",
    options=[e["experiment_id"] for e in exps],
    format_func=lambda eid: next(
        f"{e['experiment_id']} · {format_model_type(e.get('model_type'))} · {format_datetime(e.get('created_at'))}"
        for e in exps
        if e["experiment_id"] == eid
    ),
)
detail = next(e for e in exps if e["experiment_id"] == pick)
results = detail.get("results") if isinstance(detail.get("results"), dict) else {}

st.markdown(f"### Experiment `{detail.get('experiment_id')}`")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Model type", format_model_type(detail.get("model_type")))
m2.metric("Job ID", (detail.get("job_id") or "—")[:12])
m3.metric("Dataset version", detail.get("dataset_version_id") or "—")
m4.metric("Created", format_datetime(detail.get("created_at"), with_seconds=True))

st.markdown("#### Results")
render_experiment_results(results, compact=False)

left, right = st.columns(2)
with left:
    st.markdown("#### Research context")
    with st.container(border=True):
        has_research = any(
            [
                detail.get("hypothesis"),
                detail.get("research_question"),
                detail.get("conclusion"),
                detail.get("error_observations"),
                detail.get("future_improvements"),
            ]
        )
        if not has_research:
            st.info(
                "Research fields are empty for this run. You can fill hypothesis / question "
                "on **Training** for new jobs, or edit conclusion and notes below for this experiment."
            )

        with st.form(f"exp_notes_{pick}"):
            hyp = st.text_area(
                "Hypothesis",
                value=detail.get("hypothesis") or "",
                height=80,
                key=f"hyp_{pick}",
            )
            rq = st.text_area(
                "Research question",
                value=detail.get("research_question") or "",
                height=80,
                key=f"rq_{pick}",
            )
            conclusion = st.text_area(
                "Conclusion",
                value=detail.get("conclusion") or "",
                height=100,
                placeholder="Document what you conclude from this experiment…",
                key=f"conc_{pick}",
            )
            err_obs = st.text_area(
                "Error observations",
                value=detail.get("error_observations") or "",
                height=80,
                key=f"err_{pick}",
            )
            future = st.text_area(
                "Future improvements",
                value=detail.get("future_improvements") or "",
                height=80,
                key=f"fut_{pick}",
            )
            save_notes = st.form_submit_button("Save research notes", type="primary")

        if save_notes:
            try:
                update_experiment_notes(
                    pick,
                    hypothesis=hyp,
                    research_question=rq,
                    conclusion=conclusion,
                    error_observations=err_obs,
                    future_improvements=future,
                )
                st.success("Research notes saved.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

with right:
    st.markdown("#### Hyperparameters")
    hp = detail.get("hyperparameters") or {}
    if isinstance(hp, dict) and hp:
        st.dataframe(
            pd.DataFrame([{"Parameter": k, "Value": str(v)} for k, v in hp.items()]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No hyperparameters stored.")

    st.markdown("#### Preprocessing")
    prep = detail.get("preprocessing") or {}
    if isinstance(prep, dict) and prep:
        st.dataframe(
            pd.DataFrame([{"Setting": k, "Value": str(v)} for k, v in prep.items()]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No preprocessing metadata stored.")

with st.expander("Advanced: raw result keys (optional)"):
    st.caption("Hidden by default — only for debugging. Normal users can ignore this.")
    if isinstance(results, dict):
        st.write(sorted(results.keys()))
    else:
        st.write(results)
