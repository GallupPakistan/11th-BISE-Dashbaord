"""
components/chart_card.py

Wraps a Plotly figure in a titled card so every chart on every page
looks consistent. Uses st.container(border=True) — a REAL Streamlit
container — so the card border genuinely wraps the chart. (The earlier
raw <div class="chart-card"> open/close approach broke across Streamlit
blocks: the browser auto-closed the div at the end of each markdown
block, so the border never wrapped the figure.)

The card look (background, radius, shadow, padding, tight internal
spacing) is applied by styles/css.py (_chart_card_css), which restyles
the bordered-container wrapper.

Usage:

    from components.chart_card import chart_card

    with chart_card("Board-wise Pass %", "2026, all boards"):
        st.plotly_chart(fig, width="stretch")
"""

from contextlib import contextmanager
import streamlit as st


@contextmanager
def chart_card(title: str, subtitle: str = ""):
    with st.container(border=True):
        st.markdown(f'<div class="chart-card-title">{title}</div>', unsafe_allow_html=True)
        if subtitle:
            st.markdown(f'<div class="chart-card-subtitle">{subtitle}</div>', unsafe_allow_html=True)
        yield