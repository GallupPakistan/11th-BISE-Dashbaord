"""
components/page_header.py

Clean section directly under the navy topbar. No duplicated page title
(the topbar already shows it) — just a bold heading on the left telling
the user which year to select, and the year selector pills on the
right. This keeps the area above the data sections minimal.

Styling lives in styles/css.py (_page_header_css) — edit there, not here.
"""

import streamlit as st


def render_page_header(
    title: str,
    year_options: list[int] | None = None,
    year_default: int | None = None,
    key: str = "page_header_year",
):
    """
    Renders the heading + year pills. When `year_options` is given,
    returns the selected year as an int (defaulting to year_default);
    otherwise returns None.
    """
    left, right = st.columns([2.2, 1])
    with left:
        st.markdown(
            f'<div class="page-header-title">{title}</div>',
            unsafe_allow_html=True,
        )

    selected = None
    with right:
        if year_options:
            labels = [str(y) for y in year_options]
            default_label = str(year_default) if year_default is not None else labels[0]
            picked = st.pills(
                "Year",
                options=labels,
                default=default_label,
                key=key,
                selection_mode="single",
                label_visibility="collapsed",
            )
            # Return the picked LABEL (e.g. "2025", "2024", "All Years") —
            # pages convert it to an int year or None themselves. Returning
            # the label (instead of the 9th dashboard's int) lets pages
            # offer an "All Years" scope pill on the same control.
            selected = picked if picked is not None else default_label
    return selected