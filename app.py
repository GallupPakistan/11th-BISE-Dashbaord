"""
app.py — Entry point / router.
BISE 11th Grade (HSSC Part-I) 2024-25 Results -- Enhanced Results Dashboard

Sidebar navigation grouped into sections:
    Dashboard   -> Overview (Home)
    Analysis    -> Board Explorer, Compare Boards, Gender Analysis,
                   Group-wise Analysis, Subject Analysis, Province Wise,
                   District Wise
    All Boards  -> the 15 individual BISE board pages

Run: streamlit run app.py
"""

import streamlit as st

from common import (
    inject_css,
    render_hero_banner,
    render_sidebar_brand,
    render_currently_viewing,
    render_global_filters,
    load_workbook,
    show_missing_workbook_error,
    ALL_BOARD_NAMES,
)
from views_overview import render_overview


def home_page():
    st.set_page_config(
        page_title="Overview - BISE 11th Class Dashboard",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()

    try:
        data = load_workbook()
    except FileNotFoundError:
        show_missing_workbook_error()
        return

    with st.sidebar:
        render_sidebar_brand()
        st.markdown("---")
        year, boards_sel, year_choice = render_global_filters(data, ALL_BOARD_NAMES)
        st.markdown("---")
        year_label_sb = "All Years" if year_choice == "All Years" else year_choice
        render_currently_viewing(f"Overview — {len(boards_sel)} board(s)<br>{year_label_sb}")

    if not boards_sel:
        st.info("Select at least one board from the sidebar Filters to see results.")
        st.stop()

    st.markdown(render_hero_banner(15), unsafe_allow_html=True)
    render_overview(data, year, boards_sel)

    st.markdown("---")
    st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")


BOARD_PAGES = [
    ("pages/10_BISE_Abbottabad.py", "BISE Abbottabad"),
    ("pages/11_BISE_Bahawalpur.py", "BISE Bahawalpur"),
    ("pages/12_BISE_Bannu.py", "BISE Bannu"),
    ("pages/13_BISE_Dera_Ghazi_Khan.py", "BISE Dera Ghazi Khan"),
    ("pages/14_BISE_Faisalabad.py", "BISE Faisalabad"),
    ("pages/15_BISE_Gujranwala.py", "BISE Gujranwala"),
    ("pages/16_BISE_Kohat.py", "BISE Kohat"),
    ("pages/17_BISE_Lahore.py", "BISE Lahore"),
    ("pages/18_BISE_Mardan.py", "BISE Mardan"),
    ("pages/19_BISE_Peshawar.py", "BISE Peshawar"),
    ("pages/20_BISE_Rawalpindi.py", "BISE Rawalpindi"),
    ("pages/21_BISE_Sahiwal.py", "BISE Sahiwal"),
    ("pages/22_BISE_Sargodha.py", "BISE Sargodha"),
    ("pages/23_BISE_Swat.py", "BISE Swat"),
    ("pages/24_FBISE.py", "FBISE"),
]

pg = st.navigation(
    {
        "Dashboard": [
            st.Page(home_page, title="Overview", icon="🎓", default=True),
        ],
        "Analysis": [
            st.Page("pages/1_Board_Explorer.py", title="Board Explorer", icon="🏫"),
            st.Page("pages/2_Compare_Boards.py", title="Compare Boards", icon="🆚"),
            st.Page("pages/3_Gender_Analysis.py", title="Gender Analysis", icon="👥"),
            st.Page("pages/4_Group_Analysis.py", title="Group-wise Analysis", icon="🧬"),
            st.Page("pages/5_Subject_Analysis.py", title="Subject Analysis", icon="📚"),
            st.Page("pages/6_Province_Wise.py", title="Province Wise", icon="🗺️"),
            st.Page("pages/7_District_Wise.py", title="District Wise", icon="🏙️"),
        ],
        "All Boards": [
            st.Page(path, title=title, icon="🏫") for path, title in BOARD_PAGES
        ],
    }
)
pg.run()
