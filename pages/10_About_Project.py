from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_lib.bootstrap import init_app
from streamlit_lib.cache import cached_dashboard_overview
from streamlit_lib.formatters import format_compact_count, format_metric
from streamlit_lib.ui import inject_base_css, metric_row, page_header, shimmer_block, shimmer_metrics

st.set_page_config(page_title="About Project", layout="wide")
init_app()
inject_base_css()

page_header(
    "About this project — comprehensive brief",
    "Full explanation of the bilingual text problem, the research idea, how the platform resolves it, "
    "how efficient that resolution is, and how every module contributes.",
)

skel = st.empty()
with skel.container():
    shimmer_metrics(4)
    shimmer_block(1)
with st.spinner("Loading live project stats…"):
    ov = cached_dashboard_overview()
skel.empty()

cards = ov.get("cards") or {}
active = cards.get("active_model") or {}
best_f1 = cards.get("best_macro_f1")
dist = ov.get("language_distribution") or {}
models = ov.get("model_comparison") or []

st.markdown(
    """
<div style="padding:1.25rem 1.5rem;border-radius:16px;color:#fff;
background:linear-gradient(135deg,#071526 0%,#0b1f3a 50%,#1e4fd6 140%);margin-bottom:1rem;">
  <div style="font-size:0.75rem;letter-spacing:0.18em;text-transform:uppercase;opacity:0.85;">
    Detailed project brief
  </div>
  <div style="font-size:1.75rem;font-weight:700;margin-top:0.35rem;">
    Urdu–English Code-Switching Analyzer
  </div>
  <p style="margin:0.65rem 0 0;max-width:48rem;opacity:0.92;line-height:1.55;">
    A free, local research platform for word-level Roman Urdu / English identification in mixed
    Latin-script text — with code-switching detection, annotation, CPU training, evaluation,
    and research documentation. No paid APIs required.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

metric_row(
    [
        ("Dataset sentences", format_compact_count(cards.get("total_dataset_sentences"))),
        ("Annotated tokens", format_compact_count(cards.get("total_annotated_tokens"))),
        ("Best Macro F1", format_metric(best_f1) if best_f1 is not None else "n/a"),
        ("Active model", active.get("name") or "dictionary-baseline"),
    ],
    compact=False,
)

k1, k2, k3, k4 = st.columns(4)
k1.info("**Domain**\n\nRoman Urdu ↔ English code-switching")
k2.info("**Core task**\n\nWord-level language identification (LID)")
k3.info("**Output**\n\nLabels · highlights · CS status · metrics")
k4.info("**Constraint**\n\nFree · local · CPU · no paid APIs")

st.markdown("### Contents")
st.caption("Expand any section below. Live workspace stats appear at the top and in Efficiency.")

# ---------------------------------------------------------------------------
with st.expander("1. Executive summary", expanded=True):
    st.markdown(
        """
People frequently write messages that mix **English** and **Roman Urdu** in the same sentence,
using the Latin alphabet for both. A system that only “detects language for the whole sentence”
is not enough for research or product features that need to know **which words** belong to which language.

This project builds a complete **local research platform** that:

1. classifies every token as Roman Urdu, English, ambiguous, unknown, or other  
2. visualizes the mix with color highlighting and analytics  
3. detects code-switching with an **explicit evidence policy** (YES / NO / INSUFFICIENT EVIDENCE)  
4. lets researchers create/annotate datasets and train classical ML models on CPU  
5. stores experiments, evaluations, and research notes **without paid cloud AI services**

**One-line purpose:** turn mixed Roman Urdu–English text into measurable, explainable, reproducible
word-level labels and code-switching decisions that a researcher can defend in a report.
"""
    )

# ---------------------------------------------------------------------------
with st.expander("2. What this project is (and is not)", expanded=True):
    st.markdown(
        f"""
**Project name:** Urdu-English Code-Switching Analyzer  

**Subtitle:** Detecting Urdu and English in Mixed-Language Text  

**What it is**
- An NLP **research application** and lab environment, not a single-page toy demo  
- A full loop: analyze → import/annotate data → preprocess → train → evaluate → document  
- Scientifically centered on **word-level language identification** for Latin-script bilingual text  
- Plus transparent measurement of whether a sentence is truly **code-switched**

**Technology shape (hostable path)**
- **UI:** Streamlit (Python-only) for free hosting  
- **Core:** SQLAlchemy + SQLite, Pandas, Scikit-learn, Joblib  
- **Optional:** FastAPI REST API + React research console still exist in the repo  

**What it is not**
- Not a paid ChatGPT/Gemini wrapper  
- Not a claim of human-perfect bilingual understanding  
- Not an auto-scraped private-message corpus  
- Not a published leaderboard by itself — metrics come from *your* labeled data and stored evals  

**Current workspace snapshot**
- Sentences in DB: **{format_compact_count(cards.get('total_dataset_sentences'))}**  
- Annotated tokens: **{format_compact_count(cards.get('total_annotated_tokens'))}**  
- Trained models registered: **{cards.get('trained_models')}**  
- Active inference model: **{(active.get('name') or 'dictionary-baseline')}**  
  ({(active.get('version') or 'dictionary-baseline-v1')})
"""
    )

# ---------------------------------------------------------------------------
with st.expander("3. Who this helps / stakeholders"):
    st.markdown(
        """
| Stakeholder | How the project helps |
|---|---|
| NLP / linguistics students | Reproducible word-level LID + CS experiments without paid APIs |
| FYP / thesis researchers | End-to-end pipeline + notes, methodology draft, report export |
| Educators | Clear examples of code-switching and ambiguous tokens |
| Product/tool builders (local) | Offline analyzer for mixed Roman Urdu–English text |
| Annotators | Dedicated workbench to create gold labels carefully |

The design prioritizes **privacy** (local text stays local), **cost** (zero paid inference), and
**auditability** (stored metrics, model versions, experiment records).
"""
    )

# ---------------------------------------------------------------------------
with st.expander("4. Research and product objectives"):
    st.markdown(
        """
1. **Identify** Roman Urdu and English words inside mixed sentences with per-token labels.  
2. **Preserve uncertainty** — keep ambiguous/unknown instead of forcing false certainty.  
3. **Detect code-switching** only when both languages are reliably present.  
4. **Enable dataset work** — create, import, annotate, clean, and split corpora reproducibly.  
5. **Train and compare** free local classifiers (dictionary, LogReg, Linear SVM, Naive Bayes) on CPU.  
6. **Evaluate honestly** — real held-out predictions, confusion matrices, error inspection.  
7. **Support documentation** — notes, methodology draft, literature stubs, experiment journal, local exports.  
8. **Stay deployable** — Streamlit hosting without requiring a separate React build for the public demo.
"""
    )

# ---------------------------------------------------------------------------
with st.expander("5. What the system does step-by-step"):
    st.markdown(
        """
When a user analyzes text (Analyzer page or bulk import auto-labeling), the system:

1. **Ingest text** — one sentence, a paragraph, or thousands of CSV review rows.  
2. **Optional preprocessing** — Unicode normalize, clean noise, whitespace normalize, lowercase,
   collapse repeated characters, and apply configurable Roman Urdu spelling maps
   (e.g. *achha→acha*, *nahin→nahi*), while keeping original text available for inspection.  
3. **Tokenization** — split words; separate punctuation, numbers, URLs, mentions, hashtags, emojis as special kinds.  
4. **Classification** — each word gets a label from the **active trained model**, or from the
   **dictionary baseline** if none is active. The UI always shows which model/version produced the labels.  
5. **Explanation UI** — color highlights; inspect token, label, confidence (when real), position, alternatives.  
6. **Analytics** — counts, percentages, frequent English/Urdu words, transitions, ambiguous/unknown reports.  
7. **Code-switching decision** — YES / NO / INSUFFICIENT EVIDENCE according to the evidence policy.

Bulk CSV import additionally:
- detects text columns such as `text`, `Reviews`, `Review`, etc.  
- for large files (≥ ~1.5k rows), runs a **background chunked** dictionary-labeled import with progress  
- stores sentences + token annotations in SQLite for Annotation / Training later  
"""
    )

# ---------------------------------------------------------------------------
with st.expander("6. Problem statement (detailed)", expanded=True):
    st.markdown(
        """
In bilingual digital communication — especially in Pakistan and diaspora communities — users often
write Urdu using English letters (**Roman Urdu**) and insert English words in the same message.
This appears in chat, social media, e-commerce reviews, emails, and student writing.

**Core computational problem**

> Given a Latin-script sentence that may contain Roman Urdu, English, or both, assign a language
> label to each token and decide whether the sentence exhibits code-switching.

**Why whole-sentence language ID fails for this problem**
- A “mixed” label does not tell you *which* tokens are English borrowings vs Roman Urdu function words.  
- Downstream tasks (linguistic analysis, educational feedback, feature engineering, translation helpers)
  need **word-level boundaries**.  
- Fair evaluation of bilingual models also needs token-level ground truth.

**Why not just call a paid LLM API?**
- Cost and billing accounts  
- Privacy risk (sending user text to third parties)  
- Non-reproducible / opaque behavior across model versions  
- Offline / classroom / air-gapped failure  

This project **deliberately rejects** paid hosted inference for the core path and builds a free local alternative.
"""
    )

# ---------------------------------------------------------------------------
with st.expander("7. Why the problem is difficult"):
    st.markdown(
        """
| Challenge | Why it hurts LID / CS detection |
|---|---|
| **Shared script** | Both languages use Latin letters; Arabic-script Urdu detectors do not help Roman Urdu. |
| **Lexical borrowing** | English nouns/verbs sit inside Urdu grammar (*university*, *admission*, *apply*, *deadline*). |
| **Ambiguous short tokens** | *to*, *so*, *me*, *in* can be English or Roman Urdu depending on context. |
| **Spelling variation** | No single Roman Urdu orthography (*nahi/nahin*, *acha/achha*, *raha/rha*). |
| **Context dependence** | Same surface form can mean different things across sentences. |
| **Data scarcity** | Freely licensed *word-level* Roman Urdu–English datasets are limited. |
| **Annotation cost** | Gold labels require careful human judgment, especially on ambiguous tokens. |

Because of these issues, the platform treats **AMBIGUOUS** and **UNKNOWN** as first-class labels
instead of silently guessing.
"""
    )

# ---------------------------------------------------------------------------
with st.expander("8. The idea / solution thesis", expanded=True):
    st.markdown(
        """
**Thesis:** Code-switching analysis for Roman Urdu–English should be framed as

1. **Word-level language identification** with honest uncertainty labels, plus  
2. A **policy-based sentence CS decision** that requires evidence of *both* languages, plus  
3. A **local research loop** so models improve from annotated data without paid APIs.

**Design principles**
- Prefer explainable baselines before heavy models.  
- Never invent confidence scores or evaluation metrics.  
- Never auto-overwrite the active inference model after training.  
- Prefer stored artifacts (SQLite, joblib, exports) over ephemeral chat outputs.  
- Make every major claim inspectable in the UI (tokens, model version, confusion matrix, notes).
"""
    )

# ---------------------------------------------------------------------------
with st.expander("9. Worked example"):
    st.markdown("**Input**")
    st.code("Main university mein admission apply kar raha hoon.", language=None)
    st.markdown("**Illustrative target word-level pattern (linguistic goal, not a fabricated score)**")
    st.dataframe(
        pd.DataFrame(
            [
                ("Main", "URDU_ROMAN", "Roman Urdu subject pronoun / function word"),
                ("university", "ENGLISH", "English content noun (borrowing)"),
                ("mein", "URDU_ROMAN", "Roman Urdu postposition"),
                ("admission", "ENGLISH", "English content noun"),
                ("apply", "ENGLISH", "English verb"),
                ("kar", "URDU_ROMAN", "Urdu light verb / do-support"),
                ("raha", "URDU_ROMAN", "Urdu progressive auxiliary"),
                ("hoon", "URDU_ROMAN", "Urdu copula / agreement"),
            ],
            columns=["Word", "Label", "Why"],
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.markdown(
        """
**Expected analytical reading**
- Reliable Roman Urdu tokens **and** English tokens are present  
- Detected languages: Urdu + English  
- Code-switching status: **YES**  
- Punctuation would be `OTHER` and would not count as language evidence  

In the live Analyzer, labels always come from the **currently active classifier**
(dictionary or trained model). Try the same sentence on the Analyzer page to compare.
"""
    )

# ---------------------------------------------------------------------------
with st.expander("10. How this project resolves the problem (layered)", expanded=True):
    st.markdown(
        """
The resolution is **layered**: immediate usable analysis first, then data-driven improvement.

### 10.1 Immediate resolution — dictionary baseline
- Local Roman Urdu lexicon for common function/content words  
- Local English common-word lexicon  
- Explicit **ambiguous** list for high-overlap tokens  
- `UNKNOWN` when a word is absent from all lists  
- `OTHER` for non-word symbols and special tokens  

→ Working analyzer on day one without waiting for training.

### 10.2 Linguistic resolution — policies
- Do not force ambiguous words into Urdu or English  
- Do not claim code-switching when only one language is reliably found  
- Allow preprocessing on/off comparison so normalization side effects are visible  

### 10.3 Data resolution — annotation platform
- Import CSV / Excel / JSON / JSONL (including review-style `Reviews` columns)  
- Annotate tokens, mark uncertainty, filter unlabeled / UNKNOWN items  
- Validate alignment issues; clean empties with explicit actions (no silent deletion)  
- Split train/validation/test with reproducible seeds and duplicate grouping to reduce leakage  

### 10.4 Statistical resolution — local ML
- Character n-grams capture Roman Urdu morphology and spelling variants  
- Word TF-IDF captures lexical identity  
- Logistic Regression, Linear SVM, Naive Bayes train on CPU and save joblib artifacts  
- Models are registered but **never auto-overwrite** the active inference model  

### 10.5 Scientific resolution — evaluation + research center
- Metrics come from real test predictions only  
- Confusion matrices and misclassified tokens support error analysis  
- Experiment records are created when training completes  
- Notes, methodology draft, literature entries, and local report exports support write-up  

### 10.6 Product / hosting resolution — Streamlit
- Python-only UI for Streamlit Community Cloud  
- Same backend services as the FastAPI path  
- Large uploads use background chunked import so the UI stays responsive  
"""
    )

# ---------------------------------------------------------------------------
with st.expander("11. Detection and labeling policies"):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
**Token labels**
- **URDU_ROMAN** — Romanized Urdu lexical item  
- **ENGLISH** — English lexical item  
- **AMBIGUOUS** — plausible in both / unclear without forcing a side  
- **UNKNOWN** — not confidently identifiable from current resources  
- **OTHER** — punctuation, numbers, URLs, mentions, emojis, symbols  
"""
        )
    with c2:
        st.markdown(
            """
**Code-switching statuses**
- **YES** — both Urdu and English have enough reliable tokens  
  (default: at least one confident token each)  
- **NO** — exactly one language is reliably present  
- **INSUFFICIENT EVIDENCE** — too few reliable language tokens  
  (e.g. only ambiguous / unknown / other content)  

Confidence thresholds are configurable in Settings.
Models without native probabilities do **not** invent fake confidence scores.
"""
        )

# ---------------------------------------------------------------------------
with st.expander("12. How efficient is this? (runtime, cost, research)", expanded=True):
    st.markdown(
        """
Efficiency here means **speed, cost, reproducibility, and usable accuracy** on ordinary hardware —
not a claim of perfect human-level language ID.
"""
    )
    e1, e2, e3 = st.columns(3)
    e1.markdown(
        f"""
**Runtime**
- Dictionary inference ≈ near-instant per sentence  
- Chunked bulk import for thousands–100k rows  
- Classical training: seconds–minutes on CPU  
- Dashboard uses SQL aggregates (not full ORM scans)  
- Annotation loads **one sentence at a time**  
- Best stored Macro F1: **{format_metric(best_f1) if best_f1 is not None else 'n/a'}**
"""
    )
    e2.markdown(
        f"""
**Resources / cost**
- No paid API keys  
- No required GPU  
- SQLite + local artifacts  
- Streamlit hosting path  
- Sentences in this workspace: **{format_compact_count(cards.get('total_dataset_sentences'))}**  
- Tokens annotated: **{format_compact_count(cards.get('total_annotated_tokens'))}**
"""
    )
    e3.markdown(
        """
**Research efficiency**
- One app covers the full loop  
- Uncertainty labels reduce false certainty  
- Metrics only from real predictions  
- Manual model activation prevents silent swaps  
- Reports exportable locally (Markdown / DOCX / PDF)
"""
    )
    if any(dist.values()):
        st.markdown("**Current label distribution (live)**")
        st.bar_chart(pd.DataFrame({"label": list(dist.keys()), "count": list(dist.values())}).set_index("label"))
    if models:
        st.markdown("**Registered models (live)**")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "name": m.get("name"),
                        "architecture": m.get("architecture"),
                        "macro_f1": format_metric(m.get("macro_f1")),
                        "active": "yes" if m.get("is_active") else "",
                    }
                    for m in models
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    st.info(
        "Trade-off: classical local methods are transparent and cheap, but will not always match "
        "large proprietary multilingual LLMs. For thesis/FYP work, reproducibility and honesty "
        "usually matter more than opaque peak accuracy."
    )

# ---------------------------------------------------------------------------
with st.expander("13. End-to-end resolution pipeline"):
    st.markdown(
        """
1. Analyze text with the dictionary baseline to explore phenomena  
2. Collect representative mixed sentences (reviews, chats samples you have rights to use)  
3. Annotate word-level labels carefully; mark uncertain tokens  
4. Validate dataset; clean empties; split **70 / 15 / 15** with a fixed seed  
5. Compare preprocessing variants in Preprocessing Lab  
6. Train LogReg / Linear SVM / Naive Bayes locally on CPU  
7. Inspect metrics, confusion matrix, and misclassifications in Evaluation  
8. **Manually** activate a chosen model in Models  
9. Re-run Analyzer; confirm model version on predictions  
10. Record findings in Research Center; export reports locally  

This loop converts a linguistic problem into measurable labels, reproducible experiments,
and documented conclusions — without paid inference APIs.
"""
    )

# ---------------------------------------------------------------------------
with st.expander("14. Application modules and how each resolves part of the problem"):
    st.dataframe(
        pd.DataFrame(
            [
                ("Overview", "Live dashboard of dataset/model progress from real stored data."),
                ("Analyzer", "Primary inference: highlights, counts, CS status, analytics."),
                ("Datasets", "Import, validate, clean, split corpora for train/eval."),
                ("Annotation", "Create gold word-level labels for supervised learning."),
                ("Preprocessing", "Inspect how normalization changes tokens before modeling."),
                ("Training", "Local CPU jobs with progress and cancel."),
                ("Evaluation", "Compare models using real metrics and error examples."),
                ("Models", "Activate/deactivate artifacts; prevent silent overwrite."),
                ("Experiments", "Track completed training runs and stored results."),
                ("Research Center", "Notes, literature, methodology, report export."),
                ("About Project", "Problem, idea, resolution, efficiency (this page)."),
                ("Settings", "Local configuration; confirms zero paid-service dependency."),
            ],
            columns=["Module", "Role in resolving the problem"],
        ),
        use_container_width=True,
        hide_index=True,
    )

# ---------------------------------------------------------------------------
with st.expander("15. Models & training strategy (detailed)"):
    st.markdown(
        """
| Model | Role | Strengths | Watch-outs |
|---|---|---|---|
| **Dictionary baseline** | Day-one explainable LID | Transparent, fast, no training | Limited coverage → many UNKNOWN |
| **TF-IDF + Logistic Regression** | Main classical baseline | Probabilities, strong on lexical cues | Still mostly context-blind |
| **TF-IDF + Linear SVM** | Margin-based alternative | Often competitive F1 | Needs calibration for probabilities |
| **Naive Bayes** | Fast probabilistic comparator | Quick training | Independence assumptions |

**Why character n-grams help Roman Urdu**  
Spelling variants often share character patterns even when full-word forms differ
(*nahi* / *nahin*, *acha* / *achha*). Character n-grams give the model a chance to generalize
across those variants.

**Training safety rules**
- Runs in a background worker so Analyzer stays usable  
- Large jobs require explicit confirmation  
- GPU is optional and never mandatory  
- Active model is never auto-overwritten after a run completes  
"""
    )

# ---------------------------------------------------------------------------
with st.expander("16. Data reality, annotation ethics, and quality"):
    st.markdown(
        """
The platform may ship a small illustrative annotated sample to verify the pipeline. It is
**not** a research benchmark.

**Build trustworthy data**
- Prefer human-corrected gold labels over bulk auto-labels for training claims  
- Bulk dictionary import is excellent for exploration and bootstrapping, but training only on
  auto-labels largely teaches the model to imitate the dictionary  
- Import external datasets only after **license** and **label-quality** checks  
- Do not scrape private conversations or use paid corpora without rights  

**Annotation tips**
- Mark uncertain tokens instead of guessing  
- Keep guidelines consistent (especially for borrowed English nouns inside Urdu frames)  
- Use Validation / Clean tools before splitting  
- Fix seed for splits and record it in Research notes  
"""
    )

# ---------------------------------------------------------------------------
with st.expander("17. Research workflow supported by the app"):
    st.markdown(
        """
1. Formulate research questions (spelling variation, ambiguity, CS policy thresholds, model comparison).  
2. Document annotation guidelines and methodology in Research Center (draft template included).  
3. Run training; experiments are logged from stored results.  
4. Add manual observations / error analysis notes.  
5. Export Markdown / DOCX / PDF reports locally.  
6. Clearly separate **DRAFT / HYPOTHESIS** text from **actual stored metrics**.  

**Rule:** never invent citations or metrics. Literature entries are manual and verified by you.
"""
    )

# ---------------------------------------------------------------------------
with st.expander("18. Architecture (how pieces connect)"):
    st.code(
        """
Streamlit UI (streamlit_app.py + pages/)
        │
        ▼
streamlit_lib (data_access / cache / ui)
        │
        ▼
backend/app
  ├── nlp/     tokenize, preprocess, dictionary LID, CS policy, active-model inference
  ├── ml/      TF-IDF features, LogReg / LinearSVM / NB, metrics, joblib artifacts
  ├── services datasets, bulk import, training threads, research/export, dashboard
  └── SQLite   backend/data/app.db

Artifacts: artifacts/models , artifacts/exports
Lexicons:  data/lexicons
""",
        language="text",
    )
    st.markdown(
        """
**Design rules encoded in software**
- All default ML runs locally on CPU  
- Active model is never auto-overwritten after training  
- If no active trained model exists, Analyzer uses dictionary baseline and says so  
- Code-switching requires reliable evidence of **both** languages  
"""
    )

# ---------------------------------------------------------------------------
with st.expander("19. Comparison with alternative approaches"):
    st.dataframe(
        pd.DataFrame(
            [
                ("Whole-sentence language ID", "Too coarse", "Misses word-level mix structure"),
                ("Paid LLM APIs", "Often fluent guesses", "Cost, privacy, reproducibility issues"),
                ("Deep multilingual transformers", "Potentially strong", "Heavy download/GPU; optional later"),
                ("This project (dictionary + classical ML)", "Local, explainable, research loop", "Context-blind; needs gold data for strong claims"),
            ],
            columns=["Approach", "Pros", "Cons / gap this project addresses"],
        ),
        use_container_width=True,
        hide_index=True,
    )

# ---------------------------------------------------------------------------
with st.expander("20. Free / local operating constraints"):
    st.markdown(
        """
- No OpenAI / Gemini / Claude / paid Hugging Face inference for the core path  
- No required API keys or credit-card services for core functionality  
- Default training and inference run locally on CPU  
- Artifacts, datasets, notes, and reports stored on local disk / SQLite  
- Large model weights are not auto-downloaded  
- Streamlit Cloud apps may sleep or use ephemeral storage — keep important DB/exports backed up locally  
"""
    )

# ---------------------------------------------------------------------------
with st.expander("21. Limitations (honest scope)"):
    st.markdown(
        """
- Dictionary coverage is incomplete; `UNKNOWN` labels are expected for rare words.  
- Token classifiers are mostly context-blind; some ambiguities need sequence models later.  
- Roman Urdu normalization maps are helpful but not exhaustive or universally interchangeable.  
- Sample / auto-labeled data is too weak for strong generalization claims without gold annotation.  
- Free cloud hosts may sleep, wipe ephemeral disks, or limit long training.  
- Macro F1 on small or dictionary-derived labels can look optimistic relative to real-world messy text.  
"""
    )

# ---------------------------------------------------------------------------
with st.expander("22. Where to go next in the application"):
    st.markdown(
        """
1. **Analyzer** — paste mixed Roman Urdu/English text and inspect highlights.  
2. **Datasets / Annotation** — grow a trustworthy labeled corpus.  
3. **Preprocessing** — compare normalized vs raw tokens before modeling.  
4. **Training → Evaluation → Models** — improve beyond the dictionary baseline with measured results.  
5. **Research Center** — keep the scientific narrative aligned with actual experiments.  
6. **Settings** — confirm local configuration and zero paid-service dependency.  
"""
    )

st.success(
    "Summary: this project resolves mixed Roman Urdu–English text by combining word-level labeling, "
    "policy-based code-switching detection, annotation + local CPU learning, and an auditable research "
    "workflow — efficient enough for Streamlit hosting, transparent enough for academic documentation."
)
