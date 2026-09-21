"""
components/filter_bar.py

A horizontal row of capsule/pill buttons shown directly under the
topbar, for whatever filters a page needs (board, year, comparison
type, etc). Built on Streamlit's native st.pills widget, which is
already capsule-shaped - this just places it in a matching glass-card
row with a label, so every page's filter row looks the same.

Usage (inside a page, right after render_topbar(...)):

    from components.filter_bar import render_filter_bar

    selected_year = render_filter_bar(
        "Year", options=[2025, 2026], default=2026, key="year_filter"
    )

For a row with more than one filter, call it once per filter - they
stack as separate capsule rows. If you want several filters on the
SAME row, use render_filter_row() instead (see below).
"""

import streamlit as st


def render_filter_bar(label: str, options: list, default=None, key: str = "", multi: bool = False):
    """Single labeled row of capsule filter options."""
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    st.markdown(f'<span class="filter-bar-label">{label}</span>', unsafe_allow_html=True)
    value = st.pills(
        label,
        options=options,
        default=default,
        selection_mode="multi" if multi else "single",
        key=key,
        label_visibility="collapsed",
    )
    st.markdown('</div>', unsafe_allow_html=True)
    return value


def render_filter_row(filters: list[dict]):
    """
    Multiple capsule filters side by side on one row, e.g.:

        results = render_filter_row([
            {"label": "Board Type", "options": ["Gender", "District", "Grade"], "default": "Gender", "key": "f1"},
            {"label": "Year", "options": [2025, 2026], "default": 2026, "key": "f2"},
        ])
        # results is a dict keyed by each filter's `key`

    Each dict accepts: label, options, default, key, multi (bool).
    Optional per-filter keys:
      * "dropdown": True -> render st.multiselect instead of pills. Use for
        long option lists (e.g. 12 boards) whose pills would overflow the
        row's column and cannot be scrolled.
    """
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    cols = st.columns(len(filters))
    results = {}
    for col, f in zip(cols, filters):
        with col:
            st.markdown(f'<span class="filter-bar-label">{f["label"]}</span>', unsafe_allow_html=True)
            if f.get("dropdown"):
                # Multiselect dropdown instead of pills: a long option list
                # (e.g. 12 boards) overflows the pills row's column and can't
                # be scrolled; a dropdown with chips never overflows.
                results[f["key"]] = st.multiselect(
                    f["label"],
                    options=f["options"],
                    default=f.get("default"),
                    key=f["key"],
                    label_visibility="collapsed",
                )
            else:
                results[f["key"]] = st.pills(
                    f["label"],
                    options=f["options"],
                    default=f.get("default"),
                    selection_mode="multi" if f.get("multi") else "single",
                    key=f["key"],
                    label_visibility="collapsed",
                )
    st.markdown('</div>', unsafe_allow_html=True)
    return results
