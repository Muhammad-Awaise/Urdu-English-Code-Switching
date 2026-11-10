# Architecture

## Overview

```
React UI (Vite)
    ↓ HTTP /api
FastAPI
    ├── NLP (tokenize, preprocess, dictionary baseline, active-model inference)
    ├── ML (TF-IDF features, LogReg / LinearSVM / NB, joblib artifacts)
    ├── Services (datasets, training jobs, research, reports, dashboard)
    └── SQLite (SQLAlchemy ORM)
```

## Design rules

- All ML runs locally on CPU.
- Active model is never auto-overwritten after training.
- If no active trained model exists, analyzer uses dictionary baseline and says so.
- Code-switching requires reliable evidence of **both** languages.

## Key packages

- `backend/app/nlp/` — tokenization, preprocessing, dictionary LID, CS policy
- `backend/app/ml/` — sklearn trainers + metrics
- `backend/app/services/` — datasets, training threads, research/export, seed
- `backend/app/api/routes/` — REST endpoints
- `frontend/src/pages/` — research UI modules

## Storage

- SQLite DB: `backend/data/app.db`
- Model artifacts: `artifacts/models/`
- Exports: `artifacts/exports/`
- Lexicons: `data/lexicons/`
