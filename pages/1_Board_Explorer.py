"""
Board Explorer — full results for any BISE board(s) / year, filterable.
"""
import re

import streamlit as st

from common import (
    inject_css,
    render_hero_banner,
    render_sidebar_brand,
    render_currently_viewing,
    render_global_filters,
    GLOBAL_BOARDS_KEY,
    PENDING_YEAR_KEY,
    PENDING_BOARDS_KEY,
    load_workbook,
    show_missing_workbook_error,
    get_available_years,
    ALL_BOARD_NAMES,
    BOARD_PROVINCE,
)
from views_board import render_board_page

st.set_page_config(page_title="Board Explorer — BISE Dashboard", page_icon="🏫", layout="wide")
inject_css()

try:
    data = load_workbook()
except FileNotFoundError:
    show_missing_workbook_error()

board_map = {name: name for name in ALL_BOARD_NAMES}

with st.sidebar:
    render_sidebar_brand()
    st.markdown("---")
    year, selected_boards, year_choice = render_global_filters(data, ALL_BOARD_NAMES)
    st.markdown("---")
    year_label_sb = "All Years" if year_choice == "All Years" else year_choice
    render_currently_viewing(f"Board Explorer<br>{len(selected_boards)} board(s) · {year_label_sb}")

year_label = "All Years" if year is None else str(year)


def _board_page_path(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    board_order = sorted(ALL_BOARD_NAMES)
    page_num = 10 + board_order.index(name)
    return f"pages/{page_num}_{slug}.py"


explicit_boards = st.session_state.get(GLOBAL_BOARDS_KEY, [])
# Treat "every board picked" the same as "nothing picked" — the multiselect
# has no built-in "select all" toggle, so this is the only way a user ends up
# with all 15 checked, and showing 15 expanded accordions in that case is
# strictly worse than just showing the Quick Jump browse view.
show_quick_jump = not explicit_boards or set(explicit_boards) == set(ALL_BOARD_NAMES)

st.markdown(render_hero_banner(15), unsafe_allow_html=True)
st.subheader(f"🏫 Board Explorer — {len(selected_boards)} board(s), {year_label}")

if show_quick_jump:
    with st.expander("🧭 Quick Jump — Browse by Board / Year", expanded=True):
        all_names_sorted = sorted(ALL_BOARD_NAMES)

        with st.container(border=True):
            cc1, cc2 = st.columns([3, 1])
            with cc1:
                st.markdown('<div class="navcard-title" style="font-size:16px;">🆚 Compare Boards Side-by-Side</div>', unsafe_allow_html=True)
                st.markdown('<div class="navcard-sub">Pick any two (or more) boards and compare pass %, appeared, gender & trends.</div>', unsafe_allow_html=True)
            with cc2:
                if st.button("Compare now →", key="explorer_compare_btn", use_container_width=True):
                    st.session_state[PENDING_BOARDS_KEY] = all_names_sorted[:2]
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
                        st.markdown(f'<div class="navcard-title">🏫 {name}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="navcard-sub">{BOARD_PROVINCE.get(name, "")}</div>', unsafe_allow_html=True)
                        if st.button("View results →", key=f"qj_board_{name}", use_container_width=True):
                            st.switch_page(_board_page_path(name))

        st.write("")
        years_qj = sorted(get_available_years(data))
        if years_qj:
            st.markdown("**📅 Browse by Year**")
            ycols = st.columns(min(len(years_qj), 6))
            for col, yr in zip(ycols, years_qj):
                with col:
                    with st.container(border=True):
                        st.markdown(f'<div class="navcard-title">📅 {int(yr)}</div>', unsafe_allow_html=True)
                        st.markdown('<div class="navcard-sub">All boards</div>', unsafe_allow_html=True)
                        if st.button("View results →", key=f"qj_year_{int(yr)}", use_container_width=True):
                            st.session_state[PENDING_YEAR_KEY] = str(int(yr))
                            st.rerun()
else:
    if st.button("← Back to Browse", key="back_to_browse"):
        st.session_state[PENDING_BOARDS_KEY] = []
        st.rerun()

if show_quick_jump:
    st.info("Pick a board above (Quick Jump) or from the sidebar Filters to see its results.")
    st.stop()

auto_expand = len(selected_boards) == 1

for selected_board_name in selected_boards:
    with st.expander(f"📍 {selected_board_name}", expanded=auto_expand):
        render_board_page(selected_board_name, data, year, year_label)

st.markdown("---")
st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")