"""
Board Comparison — side-by-side comparison across BISE boards, filterable
by year (pills), province (pills) and an explicit boards multiselect.
"""
import streamlit as st

from components.sidebar import render_sidebar
from components.topbar import render_topbar
from components.page_header import render_page_header
from components.filter_bar import render_filter_row
from common import (
    inject_css, load_workbook, show_missing_workbook_error, ALL_BOARD_NAMES, BOARD_PROVINCE,
)
from views_compare import render_compare_page

st.set_page_config(page_title="Board Comparison — 11th Class Results", page_icon="📊", layout="wide")
inject_css()
render_sidebar()

try:
    data = load_workbook()
except FileNotFoundError:
    show_missing_workbook_error()
    st.stop()

render_topbar(
    active_page="Board Comparison",
    subtitle="Compare Appeared, Passed and Pass % across all 15 boards, 2024 vs 2025.",
    stat_label="BISE Boards",
    stat_value="15",
    stat_icon="account_balance",
)

selected_year = render_page_header(
    title="Select Year to View Results",
    year_options=[2025, 2024],
    year_default=2025,
    key="compare_year_selector",
)
year = int(selected_year) if selected_year else 2025

results = render_filter_row([
    {"label": "Province", "options": ["All Provinces", "KPK", "Punjab", "Federal (Islamabad)"],
     "default": "All Provinces", "key": "compare_province_filter"},
    {"label": "Boards", "options": ALL_BOARD_NAMES, "default": [], "key": "compare_boards_filter",
     "multi": True, "dropdown": True},
])
province = results.get("compare_province_filter") or "All Provinces"
boards_picked = results.get("compare_boards_filter") or []

if boards_picked:
    # Explicit board picks win — e.g. the Quick Jump "Compare now" button.
    boards_sel = boards_picked
elif province != "All Provinces":
    boards_sel = [b for b in ALL_BOARD_NAMES if BOARD_PROVINCE.get(b) == province]
else:
    boards_sel = list(ALL_BOARD_NAMES)

render_compare_page(data, boards_sel, year)

st.markdown("---")
st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")
