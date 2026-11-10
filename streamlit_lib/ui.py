"""Shared Streamlit presentation helpers."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from streamlit_lib.formatters import format_compact_count

__all__ = [
    "configure_page",
    "page_header",
    "metric_row",
    "token_chips_html",
    "legend_html",
    "inject_base_css",
    "shimmer_metrics",
    "shimmer_block",
    "with_loading",
]

# Empty menu items so config.toml toolbarMode=minimal can hide the ⋮ control.
_MENU_ITEMS = {"Get Help": None, "Report a bug": None, "About": None}


def configure_page(
    page_title: str,
    *,
    page_icon: str | None = None,
    layout: str = "wide",
    initial_sidebar_state: str = "expanded",
) -> None:
    """Shared set_page_config for multipage consistency (minimal toolbar)."""
    kwargs: dict[str, Any] = {
        "page_title": page_title,
        "layout": layout,
        "initial_sidebar_state": initial_sidebar_state,
        "menu_items": _MENU_ITEMS,
    }
    if page_icon is not None:
        kwargs["page_icon"] = page_icon
    st.set_page_config(**kwargs)

LABEL_COLORS = {
    "URDU_ROMAN": ("#1f9d55", "#e8f8ee"),
    "ENGLISH": ("#2563eb", "#e8eefc"),
    "AMBIGUOUS": ("#d97706", "#fff4e5"),
    "UNKNOWN": ("#6b7280", "#f3f4f6"),
    "OTHER": ("#475569", "#eef2f7"),
}


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)


def metric_row(items: list[tuple[str, Any]], compact: bool = True) -> None:
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        display = format_compact_count(value) if compact else (value if value is not None else "—")
        col.metric(label, display)


def token_chips_html(tokens: list[dict], selected_pos: int | None = None) -> str:
    parts: list[str] = []
    for t in tokens:
        label = t.get("label") or "OTHER"
        fg, bg = LABEL_COLORS.get(label, LABEL_COLORS["OTHER"])
        border = (
            "2px solid #071526"
            if selected_pos is not None and t.get("position") == selected_pos
            else "1px solid transparent"
        )
        token = html.escape(str(t.get("token", "")))
        parts.append(
            "<span style=\""
            f"display:inline-block;margin:3px;padding:4px 10px;border-radius:999px;"
            f"background:{bg};color:{fg};border:{border};font-weight:600;font-size:0.92rem;\">"
            f"{token}</span>"
        )
    return (
        "<div style='line-height:2.1;padding:0.75rem;border-radius:12px;"
        "background:#f8fafc;border:1px solid #e2e8f0;'>"
        + "".join(parts)
        + "</div>"
    )


def legend_html() -> str:
    chips = []
    names = [
        ("URDU_ROMAN", "Roman Urdu"),
        ("ENGLISH", "English"),
        ("AMBIGUOUS", "Ambiguous"),
        ("UNKNOWN", "Unknown"),
    ]
    for key, name in names:
        fg, bg = LABEL_COLORS[key]
        chips.append(
            f"<span style='display:inline-block;margin:2px 8px 2px 0;padding:3px 10px;"
            f"border-radius:999px;background:{bg};color:{fg};font-size:0.8rem;'>{name}</span>"
        )
    return "".join(chips)


def inject_base_css() -> None:
    """Inject shared styles + hide Streamlit / Community Cloud toolbar chrome.

    Uses official-ish data-testid hooks where available, plus attribute fallbacks.
    Keeps the left sidebar collapse control usable (does not blank the whole header).
    Host chrome that lives *outside* the app iframe cannot always be removed.
    """
    st.markdown(
        """
        <style>
          .block-container { padding-top: 1.4rem; max-width: 1200px; }
          div[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
          h1, h2, h3 { letter-spacing: -0.02em; }

          /* --- Hide Cloud / app toolbar chrome (Share, star, edit, GitHub, ⋮, Deploy) --- */
          #MainMenu,
          footer,
          div[data-testid="stDecoration"],
          div[data-testid="stStatusWidget"],
          div[data-testid="stToolbar"],
          div[data-testid="stAppToolbar"],
          .stDeployButton,
          [data-testid="stAppDeployButton"],
          [data-testid="stToolbarActionButtonShare"],
          [data-testid="stToolbarActionButtonFavorite"],
          [data-testid="stToolbarActionButtonStar"],
          [data-testid="stToolbarActionButtonRename"],
          [data-testid="stToolbarActionButtonEdit"],
          [data-testid="stToolbarActionButtonGithub"],
          [data-testid="stToolbarActionButtonGitHub"],
          [data-testid^="stToolbarActionButton"] {
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
            height: 0 !important;
            width: 0 !important;
            min-width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
          }

          /* Attribute / label fallbacks when testids differ by Streamlit version.
             Avoid blanketing all header buttons — sidebar collapse lives in header too. */
          header a[href*="github.com"],
          header a[href*="share.streamlit"],
          header [aria-label="Share"],
          header [aria-label="Share this app"],
          header [aria-label="Favorite"],
          header [aria-label="Star"],
          header [aria-label="Edit"],
          header [aria-label="Rename"],
          header [aria-label="GitHub"],
          header [aria-label="Source on GitHub"],
          header [title="Share"],
          header [title="GitHub"] {
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
          }

          /* Soft mask over top-right if any residual Cloud chips remain inside the app */
          .cs-toolbar-mask {
            position: fixed;
            top: 0;
            right: 0;
            width: min(320px, 42vw);
            height: 3.25rem;
            z-index: 1000000;
            background: #ffffff;
            pointer-events: auto;
          }

          @keyframes cs-shimmer {
            0% { background-position: -400px 0; }
            100% { background-position: 400px 0; }
          }
          .cs-shimmer {
            background: linear-gradient(90deg, #eef2f7 25%, #f8fafc 37%, #eef2f7 63%);
            background-size: 800px 100%;
            animation: cs-shimmer 1.15s ease-in-out infinite;
            border-radius: 12px;
          }
          .cs-shimmer-card {
            padding: 1rem;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            background: #fff;
            margin-bottom: 0.75rem;
          }
          .cs-shimmer-line { height: 12px; margin-bottom: 10px; }
          .cs-shimmer-line.lg { height: 28px; width: 55%; }
          .cs-shimmer-line.sm { width: 35%; }
          .cs-shimmer-line.md { width: 75%; }
        </style>
        <div class="cs-toolbar-mask" aria-hidden="true"></div>
        """,
        unsafe_allow_html=True,
    )


def shimmer_metrics(n: int = 4) -> None:
    cols = st.columns(max(1, int(n)))
    for col in cols:
        col.markdown(
            """
            <div class="cs-shimmer-card">
              <div class="cs-shimmer cs-shimmer-line sm"></div>
              <div class="cs-shimmer cs-shimmer-line lg"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def shimmer_block(rows: int = 3) -> None:
    chunks = []
    for _ in range(max(1, int(rows))):
        chunks.append(
            """
            <div class="cs-shimmer-card">
              <div class="cs-shimmer cs-shimmer-line md"></div>
              <div class="cs-shimmer cs-shimmer-line sm"></div>
              <div class="cs-shimmer cs-shimmer-line" style="width:90%;"></div>
            </div>
            """
        )
    st.markdown("".join(chunks), unsafe_allow_html=True)


def with_loading(label: str = "Loading…"):
    """Context manager: show spinner while work runs."""
    return st.spinner(label)
