# Free Resources

All runtime dependencies are free/open-source PyPI or npm packages. No paid APIs or hosted inference.

## Lexicons (shipped)

| Resource | Path | License / note |
|----------|------|----------------|
| Roman Urdu lexicon | `data/lexicons/roman_urdu.txt` | Curated for this project; MIT with code |
| English common words | `data/lexicons/english_common.txt` | Curated for this project; MIT with code |
| Ambiguous tokens | `data/lexicons/ambiguous.txt` | Curated for this project; MIT with code |

## Sample dataset

| Resource | Path | License / note |
|----------|------|----------------|
| sample_code_switching | seeded into SQLite + `data/raw/sample_code_switching.json` | Illustrative only; MIT with code |

## Python packages

See `backend/requirements.txt` (FastAPI, uvicorn, SQLAlchemy, pandas, numpy, scikit-learn, joblib, openpyxl, python-docx, reportlab, pytest, httpx, ruff, pydantic, python-multipart).

## Frontend packages

React, Vite, TypeScript, Tailwind CSS, Recharts, React Router — free npm packages.

## Not included / not auto-downloaded

- No Hugging Face paid endpoints
- No OpenAI / Gemini / Claude APIs
- No automatic large transformer weight downloads
- No paid datasets

If you later import an external public dataset, document its license and source here before redistribution.
