from __future__ import annotations

import html

import streamlit as st

from streamlit_lib.bootstrap import init_app
from streamlit_lib.data_access import preprocess_text
from streamlit_lib.ui import inject_base_css, page_header


def render_preprocess_panel(title: str, payload: dict) -> None:
    st.subheader(title)
    with st.container(border=True):
        st.markdown("**Original**")
        st.code(payload.get("original") or "—", language=None)

        st.markdown("**Cleaned**")
        st.code(payload.get("cleaned") or "—", language=None)

        st.markdown("**Normalized**")
        st.code(payload.get("normalized") or "—", language=None)

        tokens = payload.get("tokenized") or []
        st.markdown(f"**Tokens ({len(tokens)})**")
        if tokens:
            chips = " ".join(
                f"<span style='display:inline-block;margin:3px;padding:4px 10px;"
                f"border-radius:999px;background:#eef2ff;color:#1e4fd6;"
                f"font-size:0.9rem;font-weight:600;'>{html.escape(str(t))}</span>"
                for t in tokens
            )
            st.markdown(
                f"<div style='line-height:2.1;padding:0.6rem;border-radius:12px;"
                f"background:#f8fafc;border:1px solid #e2e8f0;'>{chips}</div>",
                unsafe_allow_html=True,
            )
            st.caption(" · ".join(str(t) for t in tokens))
        else:
            st.caption("No tokens produced.")


st.set_page_config(page_title="Preprocessing", layout="wide")
init_app()
inject_base_css()

page_header(
    "Preprocessing Lab",
    "Compare normalization options side-by-side before training or analysis.",
)

text = st.text_area(
    "Sample text",
    value="Mainnn university mein ADMISSION applyy kar raha hoon!!!",
    height=120,
)

c1, c2, c3 = st.columns(3)
lowercase = c1.checkbox("Lowercase", True)
collapse = c2.checkbox("Collapse repeated chars", True)
roman = c3.checkbox("Roman Urdu normalize", True)
unicode_n = st.checkbox("Unicode normalize", True)
clean = st.checkbox("Clean text", True)
whitespace = st.checkbox("Whitespace normalize", True)

if st.button("Run preprocessing", type="primary", disabled=not text.strip()):
    try:
        st.session_state.preprocess_result = preprocess_text(
            text,
            unicode_normalize=unicode_n,
            clean_text=clean,
            whitespace_normalize=whitespace,
            lowercase=lowercase,
            collapse_repeated_chars=collapse,
            roman_urdu_normalize=roman,
        )
    except Exception as exc:
        st.error(str(exc))

result = st.session_state.get("preprocess_result")
if not result:
    st.info("Click **Run preprocessing** to compare outputs.")
    st.stop()

left, right = st.columns(2)
with left:
    render_preprocess_panel("With selected options", result.get("with_preprocessing") or {})
with right:
    render_preprocess_panel(
        "Without Roman / aggressive norms",
        result.get("without_roman_normalization") or {},
    )

# Diff-style summary
a = (result.get("with_preprocessing") or {}).get("normalized") or ""
b = (result.get("without_roman_normalization") or {}).get("normalized") or ""
st.divider()
st.subheader("Quick comparison")
if a == b:
    st.success("Normalized outputs are identical for this sample and settings.")
else:
    c1, c2 = st.columns(2)
    c1.markdown("**Selected options → normalized**")
    c1.code(a, language=None)
    c2.markdown("**Without aggressive norms → normalized**")
    c2.code(b, language=None)
    st.caption("Differences usually come from lowercase, repeated-character collapse, or Roman Urdu spelling maps.")
