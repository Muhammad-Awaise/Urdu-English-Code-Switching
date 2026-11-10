"""
Urdu-English Code-Switching Analyzer — Streamlit entrypoint.

Run locally:
  streamlit run streamlit_app.py

Host on Streamlit Community Cloud with this file as the main module.
Uses the existing Python backend package directly (no React / separate API required).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_lib.bootstrap import init_app
from streamlit_lib.cache import cached_dashboard_overview
from streamlit_lib.formatters import format_metric
from streamlit_lib.ui import (
    configure_page,
    inject_base_css,
    metric_row,
    page_header,
    shimmer_block,
    shimmer_metrics,
)

configure_page("Urdu-English Code-Switching Analyzer", page_icon="🔬")

init_app()
inject_base_css()

page_header(
    "Urdu-English Code-Switching Analyzer",
    "Detecting Urdu and English in mixed-language text — local models only, no paid APIs.",
)

placeholder = st.empty()
with placeholder.container():
    shimmer_metrics(4)
    shimmer_block(2)

with st.spinner("Loading dashboard…"):
    data = cached_dashboard_overview()
placeholder.empty()

cards = data.get("cards") or {}

metric_row(
    [
        ("Dataset Sentences", cards.get("total_dataset_sentences")),
        ("Annotated Tokens", cards.get("total_annotated_tokens")),
        ("Roman Urdu Tokens", cards.get("roman_urdu_tokens")),
        ("English Tokens", cards.get("english_tokens")),
    ]
)
metric_row(
    [
        ("Trained Models", cards.get("trained_models")),
        ("Experiments", cards.get("completed_experiments")),
        (
            "Best Macro F1",
            format_metric(cards.get("best_macro_f1")) if cards.get("best_macro_f1") is not None else "n/a",
        ),
        ("Active Model", (cards.get("active_model") or {}).get("name", "dictionary-baseline")),
    ],
    compact=False,
)

left, right = st.columns(2)

with left:
    st.subheader("Language distribution (annotated)")
    dist = data.get("language_distribution") or {}
    if any(dist.values()):
        chart_df = pd.DataFrame(
            {"label": list(dist.keys()), "count": list(dist.values())}
        )
        st.bar_chart(chart_df.set_index("label"))
    else:
        st.info("No annotated tokens yet. Import a dataset or use the Analyzer.")

with right:
    st.subheader("Model comparison")
    models = data.get("model_comparison") or []
    if not models:
        st.info("No trained models yet. Dictionary baseline is active for inference.")
    else:
        rows = []
        for m in models:
            rows.append(
                {
                    "Name": m.get("name"),
                    "Architecture": m.get("architecture"),
                    "Macro F1": format_metric(m.get("macro_f1")),
                    "Active": "yes" if m.get("is_active") else "",
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()
st.markdown(
    """
**Python-only Streamlit UI** — open pages from the sidebar:

Analyzer · Datasets · Annotation · Preprocessing · Training · Evaluation ·
Models · Experiments · Research Center · About Project · Settings
"""
)
