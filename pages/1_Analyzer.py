from __future__ import annotations

import csv
import io

import pandas as pd
import streamlit as st

from streamlit_lib.bootstrap import init_app
from streamlit_lib.data_access import analyze_text, batch_analyze_texts
from streamlit_lib.formatters import format_model_version
from streamlit_lib.ui import (
    configure_page,
    inject_base_css,
    legend_html,
    metric_row,
    page_header,
    token_chips_html,
)

configure_page("Analyzer")
init_app()
inject_base_css()

EXAMPLES = [
    "Main university mein admission apply kar raha hoon.",
    "Yeh project deadline kal hai.",
    "Please send me the report.",
    "Aaj mausam bohot acha hai.",
]


def _set_example(i: int) -> None:
    st.session_state.analyzer_text = EXAMPLES[i]


def _clear_text() -> None:
    st.session_state.analyzer_text = ""
    st.session_state.pop("analyzer_result", None)


page_header(
    "Code-Switching Analyzer",
    "Identify Roman Urdu and English words in mixed-language sentences with local inference.",
)

tab_single, tab_batch = st.tabs(["Single text", "Batch analyze"])

with tab_single:
    if "analyzer_text" not in st.session_state:
        st.session_state.analyzer_text = EXAMPLES[0]

    text = st.text_area(
        "Input text",
        key="analyzer_text",
        height=140,
        placeholder="Enter mixed Roman Urdu / English text…",
    )

    cols = st.columns([2, 1, 1, 1])
    use_prep = cols[0].checkbox("Preprocessing", value=True, key="single_prep")
    words = len([w for w in text.strip().split() if w])
    cols[1].caption(f"{len(text)} chars · {words} words")
    cols[2].button("Clear", on_click=_clear_text)
    run = cols[3].button("Analyze Text", type="primary", disabled=not text.strip())

    ex_cols = st.columns(len(EXAMPLES))
    for i, ex in enumerate(EXAMPLES):
        ex_cols[i].button(ex[:36] + "…", key=f"ex_{i}", on_click=_set_example, args=(i,))

    if run:
        with st.spinner("Analyzing…"):
            try:
                st.session_state.analyzer_result = analyze_text(text, use_preprocessing=use_prep)
            except Exception as exc:
                st.error(str(exc))

    result = st.session_state.get("analyzer_result")
    if result:
        summary = result.get("summary") or {}
        cs = result.get("code_switching") or {}
        metric_row(
            [
                ("Total Words", summary.get("total_words")),
                ("Roman Urdu", summary.get("roman_urdu")),
                ("English", summary.get("english")),
                ("Code-Switching", cs.get("status")),
            ]
        )

        left, right = st.columns([1.4, 0.8])
        with left:
            st.subheader("Highlighted tokens")
            model = result.get("model") or {}
            st.caption(
                f"Model: {model.get('name')} ({format_model_version(model.get('version'))})"
            )
            st.markdown(token_chips_html(result.get("tokens") or []), unsafe_allow_html=True)
            st.markdown(legend_html(), unsafe_allow_html=True)

            tokens = result.get("tokens") or []
            labels = [f"{t.get('position')}: {t.get('token')} [{t.get('label')}]" for t in tokens]
            pick = st.selectbox("Inspect token", options=["—"] + labels)
            if pick != "—":
                pos = int(pick.split(":", 1)[0])
                selected = next((t for t in tokens if t.get("position") == pos), None)
                if selected:
                    with st.container(border=True):
                        st.markdown(f"**Token** `{selected.get('token')}`")
                        t1, t2, t3 = st.columns(3)
                        t1.write(f"**Label:** {selected.get('label') or '—'}")
                        conf = selected.get("confidence")
                        t2.write(
                            f"**Confidence:** {conf:.3f}" if isinstance(conf, (int, float)) else "**Confidence:** —"
                        )
                        t3.write(f"**Position:** {selected.get('position')}")
                        st.caption(f"Model version: {selected.get('model_version') or '—'}")
                        alt = selected.get("alternative")
                        if alt:
                            st.write(f"**Alternative:** {alt}")

        with right:
            st.subheader("Analysis results")
            st.write(
                f"- Ambiguous: **{summary.get('ambiguous')}**\n"
                f"- Unknown: **{summary.get('unknown')}**\n"
                f"- Urdu %: **{summary.get('urdu_percentage')}**\n"
                f"- English %: **{summary.get('english_percentage')}**\n"
                f"- Detected: **{', '.join(cs.get('detected_languages') or []) or '—'}**"
            )
            pie_data = {
                "Roman Urdu": summary.get("roman_urdu") or 0,
                "English": summary.get("english") or 0,
                "Ambiguous": summary.get("ambiguous") or 0,
                "Unknown": summary.get("unknown") or 0,
            }
            pie_df = pd.DataFrame({"label": k, "value": v} for k, v in pie_data.items() if v)
            if not pie_df.empty:
                st.bar_chart(pie_df.set_index("label"))

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Frequent English")
            for w, c in summary.get("most_frequent_english") or []:
                st.write(f"`{w}` ({c})")
        with c2:
            st.subheader("Frequent Roman Urdu")
            for w, c in summary.get("most_frequent_urdu") or []:
                st.write(f"`{w}` ({c})")

with tab_batch:
    st.caption(
        "Paste one sentence per line, or upload a plain-text / CSV file "
        "(first column used if CSV). Download a labeled results table when done."
    )
    batch_prep = st.checkbox("Preprocessing", value=True, key="batch_prep")
    batch_text = st.text_area(
        "Sentences (one per line)",
        height=180,
        placeholder="Main university mein admission apply kar raha hoon.\nPlease send me the report.",
        key="batch_text",
    )
    uploaded = st.file_uploader("Or upload .txt / .csv", type=["txt", "csv"], key="batch_upload")

    lines: list[str] = []
    if uploaded is not None:
        raw = uploaded.getvalue().decode("utf-8", errors="replace")
        if uploaded.name.lower().endswith(".csv"):
            reader = csv.reader(io.StringIO(raw))
            for row in reader:
                if not row:
                    continue
                cell = (row[0] or "").strip()
                if cell and cell.lower() not in {"text", "sentence", "utterance"}:
                    lines.append(cell)
        else:
            lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    elif batch_text.strip():
        lines = [ln.strip() for ln in batch_text.splitlines() if ln.strip()]

    st.caption(f"{len(lines)} non-empty line(s) ready")
    run_batch = st.button(
        "Run batch analyze",
        type="primary",
        disabled=not lines,
        key="run_batch",
    )

    if run_batch and lines:
        if len(lines) > 2000:
            st.warning("Large batch — processing first 2000 lines to keep the UI responsive.")
            lines = lines[:2000]
        progress = st.progress(0.0, text="Starting…")
        # Process in one call but update progress by chunking
        chunk_size = 50
        all_rows: list[dict] = []
        for start in range(0, len(lines), chunk_size):
            chunk = lines[start : start + chunk_size]
            all_rows.extend(
                batch_analyze_texts(
                    chunk,
                    use_preprocessing=batch_prep,
                    line_offset=start,
                )
            )
            progress.progress(
                min((start + len(chunk)) / len(lines), 1.0),
                text=f"Analyzed {min(start + len(chunk), len(lines))} / {len(lines)}",
            )
        st.session_state.batch_rows = all_rows
        progress.empty()
        st.success(f"Analyzed {len(all_rows)} sentences.")

    batch_rows = st.session_state.get("batch_rows") or []
    if batch_rows:
        df = pd.DataFrame(batch_rows)
        yes_n = int((df["cs_status"] == "YES").sum()) if "cs_status" in df.columns else 0
        no_n = int((df["cs_status"] == "NO").sum()) if "cs_status" in df.columns else 0
        insuff = int((df["cs_status"] == "INSUFFICIENT_EVIDENCE").sum()) if "cs_status" in df.columns else 0
        metric_row(
            [
                ("Sentences", len(df)),
                ("CS YES", yes_n),
                ("CS NO", no_n),
                ("Insufficient", insuff),
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button(
            "Download results CSV",
            data=csv_buf.getvalue(),
            file_name="batch_analyze_results.csv",
            mime="text/csv",
            type="primary",
        )
