"""
app.py — Overview page & entry point.
BISE 11th Grade (HSSC Part-I) 2024-25 Results — Results Dashboard

Visual identity is an exact replica of the 9th-class dashboard: navy
hec-topbar, navy capsule sidebar, Cinzel/Inter typography, year & province
pills, white KPI/chart cards, and the shared BOARD_COLOR_SEQUENCE charts.
Streamlit multipage routing is native (pages/ folder); the sidebar is fully
custom (components/sidebar.py) and Streamlit's auto-nav is hidden via CSS.

Run: streamlit run app.py
"""

import streamlit as st

from config.settings import PAGE_ICON
from components.sidebar import render_sidebar
from components.topbar import render_topbar
from components.page_header import render_page_header
from components.filter_bar import render_filter_bar
from common import inject_css, load_workbook, show_missing_workbook_error
from views_overview import render_overview

ALL_PROVINCES_LABEL = "All Provinces"

st.set_page_config(
    page_title="Overview - 11th Class Results",
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
render_sidebar()

try:
    data = load_workbook()
except FileNotFoundError:
    show_missing_workbook_error()
    st.stop()

render_topbar(
    active_page="Overview",
    subtitle="Province-wide 11th Class results, 2024 vs 2025, across all 15 BISE boards.",
    stat_label="BISE Boards",
    stat_value="15",
    stat_icon="account_balance",
)

# ---------------------------------------------------------------------------
# Heading + Year selector — same minimal section as the 9th-class Overview:
# a bold heading telling the user which year to pick, with the 2025/2024
# pills on the right. The chosen year drives the KPI row below.
# ---------------------------------------------------------------------------
year_choice = render_page_header(
    title="Select Year to View Results",
    year_options=[2025, 2024],
    year_default=2025,
    key="overview_year_selector",
)
year = int(year_choice) if year_choice is not None else 2025

# ---------------------------------------------------------------------------
# Province filter — capsule pills, matching the 9th-class Overview. Only
# provinces that actually have a board in the 15-board dataset are offered,
# and the default is "All Provinces" so the page opens on the full picture.
# ---------------------------------------------------------------------------
selected_province = render_filter_bar(
    "Province",
    options=["All Provinces", "KPK", "Punjab", "Federal (Islamabad)"],
    default=ALL_PROVINCES_LABEL,
    key="overview_province_filter",
)
selected_province = selected_province or ALL_PROVINCES_LABEL

render_overview(data, year, selected_province)

st.markdown("---")
st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")
