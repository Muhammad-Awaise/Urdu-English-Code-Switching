# Urdu-English Code-Switching Analyzer

**Detecting Urdu and English in Mixed-Language Text**

A local, free/open-source NLP research platform for word-level Roman Urdu / English identification, dataset annotation, CPU model training, evaluation, and research documentation.

**No paid APIs. No cloud GPU requirement. No API keys.**

## Stack

- Core NLP/ML: SQLAlchemy, SQLite, Pandas, Scikit-learn, Joblib (under `backend/app`)
- **Primary UI (hostable): Streamlit (Python-only)** — `streamlit_app.py` + `pages/`
- Optional API: FastAPI + React/Vite TypeScript UI (still available under `backend/` and `frontend/`)
- Training: local CPU (Logistic Regression, Linear SVM, Naive Bayes + dictionary baseline)

## Quick start — Streamlit (recommended for hosting)

```powershell
cd "C:\Users\GrowMore Devs\Desktop\Projects\Urdu-English-Code-Switching Analyzer"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app.py
```

UI: http://127.0.0.1:8501

This Streamlit app imports the same Python services used by the API — **no separate uvicorn or React build is required**.

### Streamlit Community Cloud

1. Push this repo to GitHub.
2. Create an app on [share.streamlit.io](https://share.streamlit.io).
3. Set **Main file path** to `streamlit_app.py`.
4. Dependencies install from the root `requirements.txt`.

Full steps, paths, and checklist: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

### Keep-alive (optional)

Free Streamlit apps can sleep after ~12h without traffic. This repo includes
`.github/workflows/streamlit-keepalive.yml` + `scripts/streamlit_keepalive.py`
(Playwright browser visit every 6 hours UTC — same pattern as the sibling
Bilingual Sentiment project). URL is set to the live app below.

Details: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md#keep-alive-optional).

**Live demo:** https://urdu-english-code-switching.streamlit.app/

## Optional: FastAPI + React UI

### Backend

```powershell
cd "C:\Users\GrowMore Devs\Desktop\Projects\Urdu-English-Code-Switching Analyzer\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### Frontend

```powershell
cd "C:\Users\GrowMore Devs\Desktop\Projects\Urdu-English-Code-Switching Analyzer\frontend"
npm install
npm run dev
```

UI: http://127.0.0.1:5173

## Modules

1. Overview dashboard  
2. Text Analyzer (highlighting + code-switching)  
3. Datasets  
4. Annotation  
5. Preprocessing Lab  
6. Training Lab  
7. Evaluation  
8. Model Registry  
9. Experiments  
10. Research Center  
11. Settings  

## Example

Input:

`Main university mein admission apply kar raha hoon.`

Dictionary baseline expects mixed Roman Urdu + English with code-switching = YES.

## Training note

A small sample annotated dataset is seeded for pipeline checks. It is **not** a research benchmark. Annotate more data (or import a verified open-license dataset) before trusting model metrics.

Do not start large training runs without confirmation in the Training Lab.

## Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

## Documentation

See `docs/` for architecture, datasets, annotation, preprocessing, training, evaluation, methodology, limitations, and free resources.
