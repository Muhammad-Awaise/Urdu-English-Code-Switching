from __future__ import annotations

import streamlit as st

from streamlit_lib.bootstrap import init_app
from streamlit_lib.cache import cached_count_records, cached_list_datasets, clear_data_caches
from streamlit_lib.data_access import export_annotations, get_record_at, update_annotation
from streamlit_lib.ui import (
    inject_base_css,
    legend_html,
    page_header,
    shimmer_block,
    token_chips_html,
)

st.set_page_config(page_title="Annotation", layout="wide")
init_app()
inject_base_css()

LABELS = ["URDU_ROMAN", "ENGLISH", "AMBIGUOUS", "UNKNOWN", "OTHER"]

page_header("Annotation Workbench", "Review and correct word-level language labels.")

skel = st.empty()
with skel.container():
    shimmer_block(2)

with st.spinner("Loading datasets…"):
    datasets = cached_list_datasets()
skel.empty()

if not datasets:
    st.info("Create and upload a dataset first.")
    st.stop()

ds_id = st.selectbox(
    "Dataset",
    options=[d["id"] for d in datasets],
    format_func=lambda i: next(d["name"] for d in datasets if d["id"] == i),
)
unlabeled_only = st.checkbox("Unlabeled / UNKNOWN only", value=False)

with st.expander("Export annotations"):
    ann_fmt = st.radio("Format", ["csv", "jsonl"], horizontal=True, key="ann_exp_fmt")
    only_filter = st.checkbox(
        "Respect unlabeled filter above",
        value=False,
        key="ann_exp_filter",
        help="If checked, export only the unlabeled/UNKNOWN subset when that filter is on.",
    )
    if st.button("Prepare download", key="ann_exp_btn"):
        try:
            fname, mime, content = export_annotations(
                int(ds_id),
                fmt=ann_fmt,
                unlabeled_only=bool(unlabeled_only and only_filter),
            )
            st.session_state.ann_export = {"fname": fname, "mime": mime, "content": content}
        except Exception as exc:
            st.error(str(exc))
    ann_exp = st.session_state.get("ann_export")
    if ann_exp:
        st.download_button(
            f"Download {ann_exp['fname']}",
            data=ann_exp["content"],
            file_name=ann_exp["fname"],
            mime=ann_exp["mime"],
            type="primary",
            key="ann_exp_dl",
        )

with st.spinner("Counting sentences…"):
    total = cached_count_records(int(ds_id), unlabeled_only=unlabeled_only)

st.caption(f"{total:,} sentences (loaded one at a time for speed)")

if total <= 0:
    st.warning("No records to show.")
    st.stop()

idx = st.number_input(
    "Sentence index",
    min_value=0,
    max_value=max(0, total - 1),
    value=0,
    step=1,
)

rec_skel = st.empty()
with rec_skel.container():
    shimmer_block(1)
with st.spinner("Loading sentence…"):
    rec = get_record_at(int(ds_id), int(idx), unlabeled_only=unlabeled_only)
rec_skel.empty()

if not rec:
    st.warning("Could not load this sentence.")
    st.stop()

st.markdown(f"**{rec['sentence_id']}**")
st.write(rec["text"])
st.markdown(token_chips_html(rec.get("annotations") or []), unsafe_allow_html=True)
st.markdown(legend_html(), unsafe_allow_html=True)

anns = rec.get("annotations") or []
if not anns:
    st.info("No token annotations on this sentence.")
else:
    st.subheader("Edit labels")
    for ann in anns:
        c1, c2, c3 = st.columns([2, 2, 1])
        c1.write(f"`{ann['token']}` (pos {ann['position']})")
        new_label = c2.selectbox(
            "Label",
            LABELS,
            index=LABELS.index(ann["label"]) if ann["label"] in LABELS else 3,
            key=f"lab_{ann['id']}",
            label_visibility="collapsed",
        )
        if c3.button("Save", key=f"save_{ann['id']}"):
            try:
                update_annotation(ann["id"], label=new_label)
                clear_data_caches()
                st.success(f"Updated {ann['token']} → {new_label}")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
