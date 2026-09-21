"""
Board Explorer — full results for any BISE board(s) / year, filterable.
Quick Jump: a compare shortcut, browse-by-board grid and browse-by-year tiles.
"""
import re

import streamlit as st

from components.sidebar import render_sidebar
from components.topbar import render_topbar
from components.page_header import render_page_header
from components.filter_bar import render_filter_row
from common import (
    inject_css, load_workbook, show_missing_workbook_error,
    get_available_years, ALL_BOARD_NAMES, BOARD_PROVINCE, chart_card,
)
from views_board import render_board_page

BOARDS_KEY = "explorer_boards_filter"
YEAR_KEY = "explorer_year_selector"

st.set_page_config(page_title="Board Explorer — 11th Class Results", page_icon="🏫", layout="wide")
inject_css()
render_sidebar()

try:
    data = load_workbook()
except FileNotFoundError:
    show_missing_workbook_error()
    st.stop()

render_topbar(
    active_page="Board Explorer",
    subtitle="Full results for any BISE board or year — Quick Jump cards, a compare shortcut and per-board deep dives.",
    stat_label="BISE Boards",
    stat_value="15",
    stat_icon="account_balance",
)


def _board_page_path(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    page_num = 10 + sorted(ALL_BOARD_NAMES).index(name)
    return f"pages/{page_num}_{slug}.py"


year_choice = render_page_header(
    title="Select Year to View Results",
    year_options=[2025, 2024, "All Years"],
    year_default=2025,
    key=YEAR_KEY,
)
year = None if year_choice in (None, "All Years") else int(year_choice)
year_label = "All Years" if year is None else str(year_choice)

picked = render_filter_row([
    {"label": "Boards", "options": ALL_BOARD_NAMES, "default": [], "key": BOARDS_KEY,
     "multi": True, "dropdown": True},
])
explicit_boards = picked.get(BOARDS_KEY) or []

# Treat "every board picked" the same as "nothing picked" — the multiselect
# has no built-in "select all" toggle, so this is the only way a user ends up
# with all 15 checked, and showing 15 expanded accordions in that case is
# strictly worse than just showing the Quick Jump browse view.
show_quick_jump = not explicit_boards or set(explicit_boards) == set(ALL_BOARD_NAMES)
selected_boards = explicit_boards if explicit_boards else list(ALL_BOARD_NAMES)

if show_quick_jump:
    with chart_card("🧭 Quick Jump — Browse by Board / Year", "Open any board's full results, or jump into a side-by-side comparison"):
        all_names_sorted = sorted(ALL_BOARD_NAMES)

        with st.container(border=True):
            cc1, cc2 = st.columns([3, 1])
            with cc1:
                st.markdown('<div class="chart-card-title" style="font-size:15px;">🆚 Compare Boards Side-by-Side</div>', unsafe_allow_html=True)
                st.markdown('<div class="chart-card-subtitle">Pick any two (or more) boards and compare pass %, appeared, gender & trends.</div>', unsafe_allow_html=True)
            with cc2:
                if st.button("Compare now →", key="explorer_compare_btn", width='stretch'):
                    st.session_state["compare_boards_filter"] = all_names_sorted[:2]
                    st.switch_page("pages/2_Compare_Boards.py")

        st.write("")
        st.markdown("**🏫 Browse by Board**")
        per_row = 4
        for i in range(0, len(all_names_sorted), per_row):
            row = all_names_sorted[i:i + per_row]
            cols = st.columns(per_row)
            for col, name in zip(cols, row):
                with col:
                    with st.container(border=True):
                        st.markdown(f'**🏫 {name}**', unsafe_allow_html=True)
                        st.markdown(f'<div class="chart-card-subtitle">{BOARD_PROVINCE.get(name, "")}</div>', unsafe_allow_html=True)
                        if st.button("View results →", key=f"qj_board_{name}", width='stretch'):
                            st.switch_page(_board_page_path(name))

        st.write("")
        years_qj = sorted(get_available_years(data))
        if years_qj:
            st.markdown("**📅 Browse by Year**")
            ycols = st.columns(min(len(years_qj), 6))
            for col, yr in zip(ycols, years_qj):
                with col:
                    with st.container(border=True):
                        st.markdown(f'**📅 {int(yr)}**', unsafe_allow_html=True)
                        st.markdown('<div class="chart-card-subtitle">All boards</div>', unsafe_allow_html=True)
                        if st.button("View results →", key=f"qj_year_{int(yr)}", width='stretch'):
                            st.session_state[YEAR_KEY] = str(int(yr))
                            st.rerun()
    st.info("Pick a board above, or narrow the Boards filter, to see its full results.")
else:
    auto_expand = len(selected_boards) == 1
    for selected_board_name in selected_boards:
        with st.expander(f"📍 {selected_board_name}", expanded=auto_expand):
            render_board_page(selected_board_name, data, year, year_label)

st.markdown("---")
st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")
