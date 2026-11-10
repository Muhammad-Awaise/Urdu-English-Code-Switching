# Model Training

## Models

1. Dictionary baseline (no training)
2. TF-IDF (word + char n-grams) + Logistic Regression
3. TF-IDF + Linear SVM (with probability calibration when class counts allow)
4. Multinomial Naive Bayes

## Requirements

- Annotated dataset version with labels
- Prefer explicit train/val/test split (default 70/15/15, seeded)
- Training runs in a background thread (`QUEUED` → … → `COMPLETED`/`FAILED`/`CANCELLED`)
- Artifacts saved under `artifacts/models/` via joblib
- Models are registered but **not** auto-activated

## Confirmation

Runs with >5000 associated tokens require `confirm_large_run=true`.
