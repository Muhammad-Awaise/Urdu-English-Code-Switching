"""Display formatters shared across Streamlit pages."""

from __future__ import annotations

from datetime import datetime


def format_datetime(value, *, with_seconds: bool = False) -> str:
    """Turn ISO timestamps into a readable local-style datetime string."""
    if value is None or value == "":
        return "—"
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return "—"
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return text
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    if with_seconds:
        return dt.strftime("%d %b %Y, %I:%M:%S %p")
    return dt.strftime("%d %b %Y, %I:%M %p")


def format_model_type(value) -> str:
    labels = {
        "logreg": "Logistic Regression",
        "linearsvm": "Linear SVM",
        "naive_bayes": "Naive Bayes",
        "dictionary": "Dictionary baseline",
    }
    if value is None or value == "":
        return "—"
    key = str(value)
    return labels.get(key, key.replace("_", " ").title())


def format_model_version(value) -> str:
    """Show train-time versions like 20261102_122543 as a readable datetime."""
    if value is None or value == "":
        return "—"
    text = str(value).strip()
    # YYYYMMDD_HHMMSS (UTC stamp used when saving trained models)
    if len(text) == 15 and text[8] == "_" and text[:8].isdigit() and text[9:].isdigit():
        try:
            dt = datetime.strptime(text, "%Y%m%d_%H%M%S")
            return dt.strftime("%d %b %Y, %I:%M:%S %p") + " UTC"
        except ValueError:
            return text
    return text


def format_compact_count(value) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, str) and not _is_number(value):
        return value
    try:
        n = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not (n == n):  # NaN
        return str(value)
    abs_n = abs(n)
    sign = "-" if n < 0 else ""
    if abs_n >= 1_000_000:
        v = abs_n / 1_000_000
        return f"{sign}{_trim(v)}M"
    if abs_n >= 1_000:
        v = abs_n / 1_000
        return f"{sign}{_trim(v)}K"
    if abs_n == int(abs_n):
        return f"{sign}{int(abs_n)}"
    return f"{n:.2f}"


def format_metric(value, digits: int = 3) -> str:
    if value is None or value == "":
        return "—"
    try:
        n = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{n:.{digits}f}"


def _trim(v: float) -> str:
    if v >= 100:
        return str(round(v))
    text = f"{v:.1f}"
    return text[:-2] if text.endswith(".0") else text


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False
