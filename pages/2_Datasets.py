from __future__ import annotations

import time

import streamlit as st

from streamlit_lib.bootstrap import init_app
from streamlit_lib.cache import cached_list_datasets, clear_data_caches
from streamlit_lib.data_access import (
    app_settings,
    clean_dataset,
    create_dataset,
    export_annotations,
    import_job_status,
    split_dataset,
    upload_dataset_file,
    validate_dataset,
)
from streamlit_lib.ui import inject_base_css, metric_row, page_header, shimmer_block

st.set_page_config(page_title="Datasets", layout="wide")
init_app()
inject_base_css()

page_header("Dataset Management", "Import, validate, clean, and split annotated corpora locally.")

skel = st.empty()
with skel.container():
    shimmer_block(2)
with st.spinner("Loading datasets…"):
    datasets = cached_list_datasets()
skel.empty()
names = {d["id"]: d["name"] for d in datasets}

with st.expander("Create dataset", expanded=not datasets):
    name = st.text_input("New dataset name", placeholder="e.g. my_reviews")
    if st.button("Create", type="primary", disabled=not name.strip()):
        try:
            created = create_dataset(name.strip())
            st.success(f'Created "{created["name"]}"')
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

if not datasets:
    st.info("Create a dataset first, then upload a CSV/JSON/Excel file.")
    st.stop()

selected_id = st.selectbox(
    "Selected dataset",
    options=[d["id"] for d in datasets],
    format_func=lambda i: f"{names[i]} (id={i})",
)
selected = next(d for d in datasets if d["id"] == selected_id)
stats = (selected.get("latest_version") or {}).get("stats") or {}

uploaded = st.file_uploader(
    "Upload CSV / JSON / Excel",
    type=["csv", "json", "jsonl", "xlsx", "xls"],
)
if uploaded is not None and st.button("Import & auto-analyze", type="primary"):
    content = uploaded.getvalue()
    with st.status("Importing file…", expanded=True) as status:
        try:
            res = upload_dataset_file(selected_id, uploaded.name, content)
            if res.get("async") and res.get("job_id"):
                st.write(res.get("message") or "Background import started…")
                job_id = res["job_id"]
                progress = st.progress(0.0, text="Queued")
                while True:
                    job = import_job_status(job_id) or {}
                    pct = float(job.get("progress") or 0)
                    progress.progress(min(pct, 1.0), text=job.get("stage") or job.get("status"))
                    if job.get("status") == "COMPLETED":
                        st.session_state.upload_result = job.get("result")
                        status.update(label="Import complete", state="complete")
                        break
                    if job.get("status") == "FAILED":
                        raise RuntimeError(job.get("error") or "Import failed")
                    time.sleep(0.8)
            else:
                st.session_state.upload_result = res
                status.update(label="Import complete", state="complete")
            clear_data_caches()
            st.rerun()
        except Exception as exc:
            status.update(label="Import failed", state="error")
            st.error(str(exc))

_rt = app_settings()
_split = _rt.get("default_split") or {}
_split_label = (
    f"Split {int(float(_split.get('train', 0.7) * 100))}/"
    f"{int(float(_split.get('val', 0.15) * 100))}/"
    f"{int(float(_split.get('test', 0.15) * 100))}"
)

a, b, c = st.columns(3)
if a.button("Validate"):
    try:
        st.session_state.validation = validate_dataset(selected_id)
        st.success(f"Issues: {st.session_state.validation.get('issue_count', 0)}")
    except Exception as exc:
        st.error(str(exc))
if b.button(_split_label):
    try:
        res = split_dataset(selected_id)
        st.success(
            f"Split groups train/val/test: "
            f"{res.get('train_groups')}/{res.get('val_groups')}/{res.get('test_groups')}"
        )
        st.rerun()
    except Exception as exc:
        st.error(str(exc))
if c.button("Clean empties"):
    try:
        res = clean_dataset(selected_id, remove_empty=True, remove_duplicates=False)
        st.success(f"Cleaning actions: {len(res.get('actions') or [])}")
        st.rerun()
    except Exception as exc:
        st.error(str(exc))

with st.expander("Export annotations"):
    exp_fmt = st.radio("Format", ["csv", "jsonl"], horizontal=True, key="ds_exp_fmt")
    if st.button("Prepare download", key="ds_exp_btn"):
        try:
            fname, mime, content = export_annotations(selected_id, fmt=exp_fmt)
            st.session_state.ds_export = {"fname": fname, "mime": mime, "content": content}
        except Exception as exc:
            st.error(str(exc))
    exp = st.session_state.get("ds_export")
    if exp:
        st.download_button(
            f"Download {exp['fname']}",
            data=exp["content"],
            file_name=exp["fname"],
            mime=exp["mime"],
            type="primary",
            key="ds_exp_dl",
        )

upload_result = st.session_state.get("upload_result")
if upload_result and upload_result.get("analysis"):
    analysis = upload_result["analysis"]
    st.subheader("Upload analysis results")
    st.caption(
        f"File: {upload_result.get('source_file') or 'upload'} · "
        f"model {(analysis.get('model') or {}).get('name')}"
    )
    metric_row(
        [
            ("Sentences analyzed", analysis.get("sentences_analyzed")),
            ("Code-switching YES", analysis.get("code_switching_yes")),
            ("Code-switching NO", analysis.get("code_switching_no")),
            ("Insufficient", analysis.get("code_switching_insufficient")),
        ]
    )
    metric_row(
        [
            ("Roman Urdu tokens", analysis.get("roman_urdu_tokens")),
            ("English tokens", analysis.get("english_tokens")),
            ("Ambiguous tokens", analysis.get("ambiguous_tokens")),
            ("Unknown tokens", analysis.get("unknown_tokens")),
        ]
    )

st.subheader("Dataset stats")
if stats:
    metric_row(
        [
            ("Sentences", stats.get("total_sentences")),
            ("Tokens", stats.get("total_tokens")),
            ("Roman Urdu", stats.get("roman_urdu_tokens")),
            ("English", stats.get("english_tokens")),
        ]
    )
    metric_row(
        [
            ("Ambiguous", stats.get("ambiguous_tokens")),
            ("Mixed sentences", stats.get("mixed_language_sentences")),
            ("Duplicates", stats.get("duplicate_records")),
            ("Unlabeled", stats.get("unlabeled_sentences")),
        ]
    )
else:
    st.info("No stats yet for this dataset.")

validation = st.session_state.get("validation")
if validation:
    with st.expander("Validation report", expanded=True):
        metric_row(
            [
                ("Records", validation.get("record_count")),
                ("Issues", validation.get("issue_count")),
                ("Duplicates", len(validation.get("duplicates") or [])),
            ]
        )
        issues = (validation.get("issues") or [])[:50]
        if issues:
            st.markdown("**Issues (sample)**")
            issue_rows = []
            for iss in issues:
                issue_rows.append(
                    {
                        "Type": iss.get("type") or "—",
                        "Sentence": iss.get("sentence_id") or "—",
                        "Token": iss.get("token") or "—",
                        "Label": iss.get("label") or "—",
                        "Detail": (
                            f"tok={iss.get('tokenized')} ann={iss.get('annotated')}"
                            if iss.get("tokenized") is not None
                            else ""
                        ),
                    }
                )
            st.dataframe(issue_rows, use_container_width=True, hide_index=True)
        else:
            st.success("No issues reported.")
        dups = (validation.get("duplicates") or [])[:20]
        if dups:
            st.markdown("**Duplicate groups (sample)**")
            st.dataframe(
                [
                    {
                        "Text key": (d.get("text_key") or "")[:80],
                        "Sentence IDs": ", ".join(str(x) for x in (d.get("sentence_ids") or [])[:8]),
                    }
                    for d in dups
                ],
                use_container_width=True,
                hide_index=True,
            )
