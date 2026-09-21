"""
board_page_helper.py — shared renderer used by each of the 15 single-board
pages (pages/10_*.py … pages/24_*.py).

Wraps every board page in the 9th-class visual identity: navy hec-topbar
(board name as the page title), custom capsule sidebar, year pills, and
white chart cards via views_board.
"""
import streamlit as st

from components.sidebar import render_sidebar
from components.topbar import render_topbar
from components.page_header import render_page_header
from common import inject_css, load_workbook, show_missing_workbook_error
from views_board import render_board_page


def render_single_board_page(display_name: str):
    st.set_page_config(page_title=f"{display_name} — 11th Class Results", page_icon="🏫", layout="wide")
    inject_css()
    render_sidebar()

    try:
        data = load_workbook()
    except FileNotFoundError:
        show_missing_workbook_error()
        return

    render_topbar(
        active_page=display_name,
        subtitle=(
            f"Board-level results for {display_name} — pass/fail, gender, "
            "groups, subjects & districts, from the combined 11th-class workbook."
        ),
        stat_label="BISE Boards",
        stat_value="15",
        stat_icon="account_balance",
    )

    year_choice = render_page_header(
        title="Select Year to View Results",
        year_options=[2025, 2024, "All Years"],
        year_default=2025,
        key=f"year_{display_name}",
    )
    year = None if year_choice in (None, "All Years") else int(year_choice)
    year_label = "All Years" if year is None else str(year_choice)

    if st.button("← Back to Board Explorer", key=f"back_{display_name}"):
        st.switch_page("pages/1_Board_Explorer.py")

    render_board_page(display_name, data, year, year_label)

    st.markdown("---")
    st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")
