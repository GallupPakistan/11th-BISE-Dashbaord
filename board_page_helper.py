"""
board_page_helper.py — shared renderer used by each single-board page
(pages/10_BISE_Abbottabad.py, pages/11_BISE_Bahawalpur.py, ...).
"""
import streamlit as st

from common import (
    inject_css,
    render_hero_banner,
    render_sidebar_brand,
    render_currently_viewing,
    load_workbook,
    show_missing_workbook_error,
    get_available_years,
)
from views_board import render_board_page


def render_single_board_page(display_name: str):
    st.set_page_config(page_title=f"{display_name} — BISE Dashboard", page_icon="🏫", layout="wide")
    inject_css()

    try:
        data = load_workbook()
    except FileNotFoundError:
        show_missing_workbook_error()
        return

    available_years = sorted(get_available_years(data), reverse=True)
    year_options = [str(y) for y in available_years] + ["All Years"]

    with st.sidebar:
        render_sidebar_brand()
        st.markdown("---")
        st.markdown("**Filters**")
        year_choice = st.selectbox("Year", year_options, key=f"year_{display_name}")
        st.markdown("---")
        render_currently_viewing(f"{display_name}<br>{year_choice}")

    year = None if year_choice == "All Years" else int(year_choice)
    year_label = "All Years" if year is None else str(year)

    st.markdown(render_hero_banner(15), unsafe_allow_html=True)
    st.subheader(f"🏫 {display_name} — {year_label}")

    if st.button("← Back to Board Explorer", key=f"back_{display_name}"):
        st.switch_page("pages/1_Board_Explorer.py")

    render_board_page(display_name, data, year, year_label)

    st.markdown("---")
    st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")
