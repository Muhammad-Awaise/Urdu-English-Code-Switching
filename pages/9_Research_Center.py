from __future__ import annotations

from pathlib import Path

import streamlit as st

from streamlit_lib.bootstrap import init_app
from streamlit_lib.data_access import (
    create_note,
    create_paper,
    delete_note,
    export_report,
    list_experiments,
    list_notes,
    list_papers,
    methodology,
    research_dashboard,
)
from streamlit_lib.formatters import format_datetime, format_model_type, format_model_version
from streamlit_lib.metrics_display import render_experiment_results
from streamlit_lib.ui import inject_base_css, metric_row, page_header, shimmer_metrics

st.set_page_config(page_title="Research Center", layout="wide")
init_app()
inject_base_css()

page_header(
    "Research Center",
    "Your local research workspace: notes, literature, methodology draft, and exportable reports.",
)

st.markdown(
    """
**Purpose of this page**

Keep the scientific side of the project organized in one place — without paid tools:

| Tab | What it’s for |
|---|---|
| **Notes** | Working research notes by category (questions, annotation, errors, findings…) |
| **Papers** | Manual literature entries you verified (never invent citations) |
| **Methodology** | Draft methodology template for your thesis/FYP write-up |
| **Export report** | Generate local Markdown / DOCX / PDF from stored experiments & models |

This is **documentation + evidence**, not the Analyzer itself. Use **About Project** for the full
problem/solution story; use Research Center to record *your* notes, papers, and exports.
"""
)

skel = st.empty()
with skel.container():
    shimmer_metrics(4)
with st.spinner("Loading research dashboard…"):
    dash = research_dashboard()
skel.empty()

metric_row(
    [
        ("Notes", dash.get("notes")),
        ("Papers", dash.get("papers")),
        ("Experiments", dash.get("completed_experiments")),
        ("Models", dash.get("trained_models")),
    ]
)

active = dash.get("active_model") or {}
best = dash.get("best_evaluated_model")
c1, c2 = st.columns(2)
c1.info(
    f"**Active model**\n\n{active.get('name', 'dictionary-baseline')} · "
    f"{format_model_version(active.get('version', '—'))}"
)
if best:
    c2.success(
        f"**Best evaluated Macro F1**\n\n{best.get('name')} · {best.get('macro_f1'):.3f}"
        if isinstance(best.get("macro_f1"), (int, float))
        else f"**Best evaluated**\n\n{best}"
    )
else:
    c2.warning("**Best evaluated Macro F1**\n\nNo evaluated model metrics yet")

tab_notes, tab_papers, tab_method, tab_export = st.tabs(
    ["Notes", "Papers", "Methodology", "Export report"]
)

# ----- Notes -----
with tab_notes:
    st.subheader("Research notes")
    st.caption("Capture ideas, guidelines, and observations as you work. Categories keep notes sortable.")

    notes_data = list_notes()
    cats = notes_data.get("categories") or ["general"]
    notes = notes_data.get("notes") or []

    left, right = st.columns([1.1, 1.2])
    with left:
        st.markdown("##### Add a note")
        with st.form("new_note", clear_on_submit=True):
            title = st.text_input("Title", placeholder="e.g. Ambiguous token guideline")
            category = st.selectbox("Category", cats)
            content = st.text_area("Content", height=140, placeholder="Write your observation…")
            if st.form_submit_button("Save note", type="primary"):
                if title.strip() and content.strip():
                    create_note(title.strip(), category, content.strip())
                    st.success("Note saved")
                    st.rerun()
                else:
                    st.warning("Title and content are required.")

    with right:
        st.markdown(f"##### Saved notes ({len(notes)})")
        if not notes:
            st.info("No notes yet. Add your first research note on the left.")
        else:
            filter_cat = st.selectbox(
                "Filter by category",
                options=["All"] + list(cats),
                key="note_filter",
            )
            shown = [n for n in notes if filter_cat == "All" or n.get("category") == filter_cat]
            for n in shown:
                with st.container(border=True):
                    st.markdown(f"**{n.get('title')}**")
                    st.caption(f"{n.get('category')} · {format_datetime(n.get('created_at'))}")
                    st.write(n.get("content"))
                    if st.button("Delete note", key=f"del_note_{n['id']}"):
                        delete_note(n["id"])
                        st.rerun()

# ----- Papers -----
with tab_papers:
    st.subheader("Literature / papers")
    st.caption(
        "Store only papers you have actually checked from free sources. Do not invent citations or results."
    )

    papers = list_papers()
    left, right = st.columns([1.1, 1.2])
    with left:
        st.markdown("##### Add a paper")
        with st.form("new_paper", clear_on_submit=True):
            title = st.text_input("Paper title")
            authors = st.text_input("Authors")
            year = st.number_input("Year", min_value=1900, max_value=2100, value=2024)
            venue = st.text_input("Venue / conference / journal")
            findings = st.text_area("Reported findings (your summary)", height=90)
            relevance = st.text_area("Relevance to this project", height=90)
            if st.form_submit_button("Save paper", type="primary"):
                if title.strip():
                    create_paper(
                        {
                            "title": title.strip(),
                            "authors": authors,
                            "year": int(year),
                            "venue": venue,
                            "findings": findings,
                            "relevance": relevance,
                        }
                    )
                    st.success("Paper saved")
                    st.rerun()
                else:
                    st.warning("Title is required.")

    with right:
        st.markdown(f"##### Saved papers ({len(papers)})")
        if not papers:
            st.info("No papers yet. Add verified literature entries on the left.")
        else:
            for p in papers:
                with st.container(border=True):
                    st.markdown(f"**{p.get('title')}**")
                    meta = " · ".join(
                        x
                        for x in [
                            p.get("authors") or None,
                            str(p.get("year")) if p.get("year") else None,
                            p.get("venue") or None,
                        ]
                        if x
                    )
                    if meta:
                        st.caption(meta)
                    if p.get("findings"):
                        st.markdown("**Findings**")
                        st.write(p["findings"])
                    if p.get("relevance"):
                        st.markdown("**Relevance**")
                        st.write(p["relevance"])

# ----- Methodology -----
with tab_method:
    method = methodology() or {}
    sections = method.get("sections") or {}

    SECTION_META = [
        ("1_introduction", "1. Introduction"),
        ("2_problem_statement", "2. Problem statement"),
        ("3_objectives", "3. Objectives"),
        ("4_research_questions", "4. Research questions"),
        ("5_related_work", "5. Related work"),
        ("6_dataset_description", "6. Dataset description"),
        ("7_data_collection", "7. Data collection"),
        ("8_annotation_guidelines", "8. Annotation guidelines"),
        ("9_preprocessing", "9. Preprocessing"),
        ("10_feature_engineering", "10. Feature engineering"),
        ("11_model_architecture", "11. Model architecture"),
        ("12_experimental_setup", "12. Experimental setup"),
        ("13_evaluation_metrics", "13. Evaluation metrics"),
        ("14_results", "14. Results"),
        ("15_error_analysis", "15. Error analysis"),
        ("16_discussion", "16. Discussion"),
        ("17_limitations", "17. Limitations"),
        ("18_conclusion", "18. Conclusion"),
        ("19_future_work", "19. Future work"),
    ]

    st.subheader(method.get("title") or "Methodology (DRAFT)")
    st.warning(method.get("disclaimer") or "Draft template — not experimental results.")
    st.caption(
        "Use this as your thesis/FYP methodology skeleton. Fill Results / Discussion only after real experiments. "
        "For the product-level problem/solution narrative, see **About Project**."
    )

    # Quick jump overview
    st.markdown("##### Section overview")
    overview_cols = st.columns(3)
    for i, (key, label) in enumerate(SECTION_META):
        val = sections.get(key)
        filled = bool(val) and str(val).strip() not in {
            "To be written from actual findings.",
            "No fabricated results. Fill after real experiments.",
            "To be written after experiments.",
        }
        overview_cols[i % 3].markdown(
            f"{'✅' if filled else '📝'} {label}"
        )

    st.divider()

    for key, label in SECTION_META:
        value = sections.get(key)
        with st.container(border=True):
            st.markdown(f"##### {label}")
            if isinstance(value, list):
                for item in value:
                    st.markdown(f"- {item}")
            elif value:
                st.write(value)
            else:
                st.caption("Empty section — fill during your research write-up.")

# ----- Export -----
with tab_export:
    st.subheader("Export research report")
    st.caption(
        "Builds a local report from **stored** experiments and models. "
        "Draft methodology text is labeled as draft — not as results."
    )

    e1, e2 = st.columns(2)
    with e1:
        report_type = st.selectbox(
            "Report type",
            ["complete", "training", "model_comparison"],
            format_func=lambda x: {
                "complete": "Complete (snapshot + experiments + models + methodology draft)",
                "training": "Training experiments",
                "model_comparison": "Model comparison",
            }[x],
        )
    with e2:
        fmt = st.selectbox(
            "Format",
            ["markdown", "docx", "pdf"],
            format_func=lambda x: {"markdown": "Markdown (.md)", "docx": "Word (.docx)", "pdf": "PDF"}.get(x, x),
        )

    if st.button("Generate export", type="primary"):
        try:
            with st.spinner("Writing report…"):
                res = export_report(report_type=report_type, fmt=fmt)
            st.session_state.research_export = res
        except Exception as exc:
            st.error(str(exc))
            st.session_state.pop("research_export", None)

    export_res = st.session_state.get("research_export")
    if export_res:
        paths = export_res.get("paths") or {}
        st.success("Export created")
        for kind, path in paths.items():
            st.markdown(f"**{kind}:** `{path}`")
        md_path = paths.get("markdown")
        if md_path and Path(md_path).exists():
            text = Path(md_path).read_text(encoding="utf-8")
            st.download_button(
                "Download Markdown",
                data=text,
                file_name=Path(md_path).name,
                mime="text/markdown",
            )

        st.markdown("#### Readable experiment preview")
        st.caption(
            "Same stored records as the export — shown as metrics and tables "
            "(not raw Python dicts). Open **Experiments** for full editing."
        )
        exps = list_experiments()
        if not exps:
            st.info("No experiments stored yet.")
        else:
            for e in exps[:10]:
                with st.container(border=True):
                    st.markdown(
                        f"**`{e.get('experiment_id')}`** — {format_model_type(e.get('model_type'))}"
                    )
                    st.caption(format_datetime(e.get("created_at")))
                    if e.get("hypothesis"):
                        st.write(f"**Hypothesis:** {e['hypothesis']}")
                    if e.get("conclusion"):
                        st.write(f"**Conclusion:** {e['conclusion']}")
                    render_experiment_results(
                        e.get("results") if isinstance(e.get("results"), dict) else {},
                        compact=True,
                    )

        if md_path and Path(md_path).exists():
            with st.expander("Raw Markdown file (optional)"):
                st.caption("Formatted tables for thesis export — not the old dict dump.")
                st.code(text[:12000], language="markdown")

st.divider()
st.caption(
    "Research Center = your notes, literature, methodology draft, and exports. "
    "About Project = comprehensive problem / idea / resolution brief."
)
