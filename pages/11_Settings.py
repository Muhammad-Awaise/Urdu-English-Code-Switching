from __future__ import annotations

from pathlib import Path

import streamlit as st

from streamlit_lib.bootstrap import init_app
from streamlit_lib.data_access import app_settings, save_runtime_settings
from streamlit_lib.ui import inject_base_css, page_header

st.set_page_config(page_title="Settings", layout="wide")
init_app()
inject_base_css()

page_header(
    "Settings",
    "Runtime configuration for the local research platform — review and adjust CS policy, splits, and seed.",
)

settings = app_settings()
split = settings.get("default_split") or {}
file_defaults = settings.get("file_defaults") or {}
db_url = str(settings.get("database_url") or "")
db_path = db_url.replace("sqlite:///", "") if db_url.startswith("sqlite:///") else db_url

# ----- Platform -----
st.subheader("Platform")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**Application**")
    st.write(settings.get("app_name") or "—")
    st.caption("Product name shown across the research UI.")
with c2:
    st.markdown("**Paid services**")
    if settings.get("zero_paid_resources"):
        st.success("Disabled — core path uses no paid APIs")
    else:
        st.warning("Paid resources may be enabled")
    st.caption("Confirms the free / local operating constraint.")

c3, c4 = st.columns(2)
with c3:
    st.markdown("**User interface**")
    st.write("Streamlit (Python-only)")
    st.caption("Hostable UI without a separate React build.")
with c4:
    st.markdown("**Backend services**")
    st.write("SQLAlchemy + NLP/ML under `backend/app`")
    st.caption("Shared package used by Streamlit and the optional FastAPI API.")

st.divider()

# ----- Editable runtime overrides -----
st.subheader("Editable runtime overrides")
st.caption(
    "Changes save to the local database and apply immediately in this process "
    "(Analyzer CS detection, Datasets Split defaults). File/env defaults remain the fallback."
)

with st.form("runtime_settings_form"):
    st.markdown("#### Code-switching detection policy")
    p1, p2 = st.columns(2)
    with p1:
        cs_min_tokens = st.number_input(
            "Min tokens per language",
            min_value=1,
            max_value=10,
            value=int(settings.get("cs_min_tokens_per_language") or 1),
            help="Both languages need at least this many confident tokens for CS = YES.",
        )
        st.caption(
            f"File default: `{file_defaults.get('cs_min_tokens_per_language', 1)}`. "
            "Raise for stricter YES."
        )
    with p2:
        cs_min_conf = st.number_input(
            "Min confidence",
            min_value=0.0,
            max_value=1.0,
            step=0.01,
            format="%.2f",
            value=float(settings.get("cs_min_confidence") or 0.55),
            help="Tokens below this confidence are ignored as language evidence.",
        )
        st.caption(
            f"File default: `{file_defaults.get('cs_min_confidence', 0.55)}`. "
            "Tokens without a real probability are not invented."
        )

    st.markdown("#### Default dataset split")
    s1, s2, s3 = st.columns(3)
    with s1:
        train_r = st.number_input(
            "Train ratio",
            min_value=0.05,
            max_value=0.95,
            step=0.01,
            format="%.2f",
            value=float(split.get("train") or 0.7),
        )
    with s2:
        val_r = st.number_input(
            "Validation ratio",
            min_value=0.0,
            max_value=0.90,
            step=0.01,
            format="%.2f",
            value=float(split.get("val") or 0.15),
        )
    with s3:
        test_r = st.number_input(
            "Test ratio",
            min_value=0.0,
            max_value=0.90,
            step=0.01,
            format="%.2f",
            value=float(split.get("test") or 0.15),
        )
    split_sum = float(train_r) + float(val_r) + float(test_r)
    if abs(split_sum - 1.0) < 1e-6:
        st.success(f"Split sums to 100% ({split_sum:.2f})")
    else:
        st.warning(f"Split sums to {split_sum:.2f} — must equal 1.0 to save")

    st.markdown("#### Reproducibility")
    seed = st.number_input(
        "Random seed",
        min_value=0,
        max_value=2_147_483_647,
        value=int(settings.get("random_seed") or 42),
        help="Used by Datasets Split when you do not override seed there.",
    )
    st.caption(f"File default: `{file_defaults.get('random_seed', 42)}`.")

    save_col, reset_col = st.columns([1, 1])
    submitted = save_col.form_submit_button("Save overrides", type="primary")
    reset = reset_col.form_submit_button("Reset to file defaults")

if submitted:
    if abs(float(train_r) + float(val_r) + float(test_r) - 1.0) >= 1e-6:
        st.error("Train + validation + test must sum to 1.0.")
    else:
        try:
            save_runtime_settings(
                {
                    "cs_min_tokens_per_language": int(cs_min_tokens),
                    "cs_min_confidence": float(cs_min_conf),
                    "default_train_ratio": float(train_r),
                    "default_val_ratio": float(val_r),
                    "default_test_ratio": float(test_r),
                    "random_seed": int(seed),
                }
            )
            st.success("Runtime overrides saved.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

if reset:
    try:
        save_runtime_settings(
            {
                "cs_min_tokens_per_language": file_defaults.get("cs_min_tokens_per_language", 1),
                "cs_min_confidence": file_defaults.get("cs_min_confidence", 0.55),
                "default_train_ratio": file_defaults.get("default_train_ratio", 0.7),
                "default_val_ratio": file_defaults.get("default_val_ratio", 0.15),
                "default_test_ratio": file_defaults.get("default_test_ratio", 0.15),
                "random_seed": file_defaults.get("random_seed", 42),
            }
        )
        st.success("Reset to file defaults.")
        st.rerun()
    except Exception as exc:
        st.error(str(exc))

st.info(
    "**How to read CS policy:** raise min tokens / confidence for stricter CS=YES. "
    "Lower them if you want more sentences marked as code-switched."
)

st.divider()

# ----- Storage -----
st.subheader("Local storage")
st.markdown("**Database**")
st.code(db_path or db_url, language=None)
exists = Path(db_path).exists() if db_path and not db_url.startswith("postgresql") else None
if exists is True:
    st.caption("SQLite file found on disk.")
elif exists is False:
    st.caption("SQLite path configured; file is created on first run.")
else:
    st.caption("Database URL from runtime config.")

a1, a2, a3 = st.columns(3)
a1.markdown("**Models**\n\n`artifacts/models/`")
a2.markdown("**Exports**\n\n`artifacts/exports/`")
a3.markdown("**Lexicons**\n\n`data/lexicons/`")

st.divider()

st.subheader("What you handle here")
st.markdown(
    """
| Area | Action on this page |
|---|---|
| Day-to-day analysis | Nothing — use **Analyzer** |
| Datasets / labels | Use **Datasets** and **Annotation** |
| Training / models | Use **Training**, **Evaluation**, **Models** |
| CS strictness | Edit thresholds above and save |
| Split ratios / seed | Edit defaults above; Datasets Split uses them |
| Verify free/local setup | Confirm paid services disabled + SQLite path |
"""
)

st.caption("See **About Project** for the full problem, idea, resolution, and efficiency write-up.")
