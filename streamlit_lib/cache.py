"""Streamlit-cached data loaders for faster page navigation."""

from __future__ import annotations

import streamlit as st

from streamlit_lib import data_access as da


def clear_data_caches() -> None:
    cached_dashboard_overview.clear()
    cached_list_datasets.clear()
    cached_list_models.clear()
    cached_compare_models.clear()
    cached_count_records.clear()


@st.cache_data(ttl=45, show_spinner=False)
def cached_dashboard_overview() -> dict:
    return da.dashboard_overview()


@st.cache_data(ttl=45, show_spinner=False)
def cached_list_datasets() -> list[dict]:
    return da.list_datasets()


@st.cache_data(ttl=45, show_spinner=False)
def cached_list_models() -> dict:
    return da.list_models()


@st.cache_data(ttl=45, show_spinner=False)
def cached_compare_models() -> dict:
    return da.compare_models()


@st.cache_data(ttl=30, show_spinner=False)
def cached_count_records(dataset_id: int, unlabeled_only: bool = False) -> int:
    return da.count_records(dataset_id, unlabeled_only=unlabeled_only)
