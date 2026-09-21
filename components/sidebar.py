"""
components/sidebar.py

Custom branded sidebar for the 11th-class dashboard: logo + app name at
top, then the analysis pages as rounded "capsule" nav links, then the 15
individual board pages under an "ALL BOARDS" section label, then the
tagline footer (styles/css.py -> _sidebar_css handles the pill shape +
active-page highlight; the .sidebar-section-label style was added there
to group the board pages).

Streamlit's own auto-generated page nav (built from the pages/ folder) is
hidden via CSS so page names don't appear twice - this list is the ONLY
nav rendered. The Overview page lives in app.py itself (linked via
"app.py"); add/remove/reorder pages ONLY in the lists below.
"""

import streamlit as st
from config.settings import APP_NAME, APP_SUBTITLE, APP_ICON, BOARD_PAGES

# Analysis pages, in the order they should appear in the sidebar.
PAGES = [
    ("app.py", "Overview", "🏠"),
    ("pages/1_Board_Explorer.py", "Board Explorer", "🏫"),
    ("pages/2_Compare_Boards.py", "Board Comparison", "📊"),
    ("pages/3_Gender_Analysis.py", "Gender Analysis", "🚻"),
    ("pages/4_Group_Analysis.py", "Group Wise", "🧪"),
    ("pages/5_Subject_Analysis.py", "Subject Wise", "📚"),
    ("pages/6_Province_Wise.py", "Province Wise", "🗺️"),
    ("pages/7_District_Wise.py", "District Wise", "🏙️"),
]


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            f"""<div class="sidebar-brand">
<div class="sidebar-brand-icon"><span class="material-symbols-outlined">{APP_ICON}</span></div>
<div class="sidebar-brand-text">{APP_NAME}<br><span style="font-weight:400;opacity:0.7;font-size:0.78rem;">{APP_SUBTITLE}</span></div>
</div>""",
            unsafe_allow_html=True,
        )

        for page_path, link_label, icon in PAGES:
            st.page_link(page_path, label=link_label, icon=icon)

        st.markdown(
            '<div class="sidebar-section-label">All Boards</div>',
            unsafe_allow_html=True,
        )
        for page_path, link_label in BOARD_PAGES:
            st.page_link(page_path, label=link_label, icon="🏫")

        st.markdown(
            '<div class="sidebar-tagline">11th Class Results<br>'
            "2024 vs 2025 · 15 BISE Boards</div>",
            unsafe_allow_html=True,
        )