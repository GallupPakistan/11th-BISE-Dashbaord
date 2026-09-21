"""
Gender Analysis — Boys vs Girls performance across BISE boards.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.sidebar import render_sidebar
from components.topbar import render_topbar
from components.page_header import render_page_header
from components.filter_bar import render_filter_row
from components.kpi_card import render_kpi_row
from common import (
    inject_css, load_workbook, show_missing_workbook_error,
    gender_df_for, show_chart, style_fig, fmt_k, csv_download_button,
    grouped_bar_chart, gender_split_pie, GENDER_COLORS, NAVY,
    ALL_BOARD_NAMES, BOARD_PROVINCE, chart_card,
)

st.set_page_config(page_title="Gender Analysis — 11th Class Results", page_icon="🚻", layout="wide")
inject_css()
render_sidebar()

try:
    data = load_workbook()
except FileNotFoundError:
    show_missing_workbook_error()
    st.stop()

render_topbar(
    active_page="Gender Analysis",
    subtitle="Boys vs Girls performance across all BISE boards, 2024 vs 2025.",
    stat_label="BISE Boards",
    stat_value="15",
    stat_icon="account_balance",
)

year_choice = render_page_header(
    title="Select Year to View Results",
    year_options=[2025, 2024, "All Years"],
    year_default=2025,
    key="gender_year_selector",
)
year = None if year_choice in (None, "All Years") else int(year_choice)
year_label = "All Years" if year is None else str(year_choice)

picked = render_filter_row([
    {"label": "Boards", "options": ALL_BOARD_NAMES, "default": [], "key": "gender_boards_filter",
     "multi": True, "dropdown": True},
])
boards_sel = picked.get("gender_boards_filter") or list(ALL_BOARD_NAMES)
if not boards_sel:
    st.info("Select at least one board in the Boards filter to see results.")
    st.stop()

rows = []
for name in boards_sel:
    g_df = gender_df_for(data, name, year)
    for _, r in g_df.iterrows():
        rows.append({"Board": name, "Gender": r["Gender"], "Appeared": r["Appeared"],
                     "Passed": r["Passed"], "Pass %": r["Pass %"]})

gdf_all = pd.DataFrame(rows)

if gdf_all.empty:
    st.info("No gender-split data available for the selected boards/year.")
    st.stop()

gdf_all["Province"] = gdf_all["Board"].map(BOARD_PROVINCE).fillna("Other")

overall = gdf_all.groupby("Gender", as_index=False)[["Appeared", "Passed"]].sum()
overall["Pass %"] = (100 * overall["Passed"] / overall["Appeared"].replace(0, float('nan'))).round(2)

boys = overall[overall["Gender"] == "Male"]
girls = overall[overall["Gender"] == "Female"]
boys_pct = float(boys["Pass %"].iloc[0]) if not boys.empty else 0
girls_pct = float(girls["Pass %"].iloc[0]) if not girls.empty else 0
total_appeared = int(overall["Appeared"].sum())
boys_app = int(boys["Appeared"].iloc[0]) if not boys.empty else 0
girls_app = int(girls["Appeared"].iloc[0]) if not girls.empty else 0
gap = round(girls_pct - boys_pct, 1)

kpis = [
    dict(icon="group", value=fmt_k(total_appeared), label=f"TOTAL APPEARED · {year_label}",
         delta=f"{len(boards_sel)} boards", delta_positive=True, accent="blue"),
    dict(icon="male", value=f"{boys_pct:.1f}%", label="BOYS PASS %",
         delta=(f"{fmt_k(boys_app)} appeared" if boys_app else ""), delta_positive=True, accent="blue"),
    dict(icon="female", value=f"{girls_pct:.1f}%", label="GIRLS PASS %",
         delta=(f"{fmt_k(girls_app)} appeared" if girls_app else ""), delta_positive=True, accent="gold"),
    dict(icon="swap_vert", value=f"{gap:+.1f} pts", label="GENDER GAP (GIRLS − BOYS)",
         delta=("Girls ahead" if gap >= 0 else "Boys ahead"), delta_positive=gap >= 0,
         accent="green" if gap >= 0 else "red"),
]
render_kpi_row(kpis)

gc1, gc2 = st.columns(2)
with gc1:
    with chart_card("Appeared Share — Boys vs Girls", f"{year_label}, selected boards"):
        show_chart(gender_split_pie(overall, "Overall Appeared Share"))
with gc2:
    with chart_card("Pass % by Gender", f"{year_label}, selected boards"):
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=["Boys", "Girls"], y=[boys_pct, girls_pct],
                              marker_color=[GENDER_COLORS["Male"], GENDER_COLORS["Female"]],
                              text=[f"{boys_pct:.1f}%", f"{girls_pct:.1f}%"], textposition="outside"))
        fig2.update_layout(title="Overall Pass % by Gender", yaxis_range=[0, 100])
        show_chart(style_fig(fig2))

board_pivot = gdf_all.pivot_table(index="Board", columns="Gender", values="Pass %", aggfunc="mean")
board_pivot = board_pivot.sort_values(board_pivot.columns[0], ascending=False) if not board_pivot.empty else board_pivot
series = {}
for g in ["Male", "Female"]:
    if g in board_pivot.columns:
        series["Boys" if g == "Male" else "Girls"] = board_pivot[g].fillna(0).round(1).tolist()

with chart_card("Pass % by Gender — per Board", f"{year_label}, Boys vs Girls per board"):
    show_chart(grouped_bar_chart(
        board_pivot.index.tolist(), series, title="Pass % by Gender — per Board", y_title="Pass %",
        colors=[GENDER_COLORS["Male"], GENDER_COLORS["Female"]],
        show_values=True, value_suffix="%",
    ))

board_pivot_app = gdf_all.pivot_table(index="Board", columns="Gender", values="Appeared", aggfunc="sum")
board_pivot_app = board_pivot_app.reindex(board_pivot.index) if not board_pivot.empty else board_pivot_app
series_app = {}
for g in ["Male", "Female"]:
    if g in board_pivot_app.columns:
        series_app["Boys" if g == "Male" else "Girls"] = board_pivot_app[g].fillna(0).astype(int).tolist()

with chart_card("Appeared — Boys vs Girls (headcount, per board)", f"{year_label}, per board"):
    show_chart(grouped_bar_chart(
        board_pivot_app.index.tolist(), series_app, title="Students Appeared — Boys vs Girls, per Board",
        y_title="Students Appeared", colors=[GENDER_COLORS["Male"], GENDER_COLORS["Female"]],
    ))

with chart_card("Gender Split by Province", "Same Boys/Girls figures rolled up one level — by province instead of by board"):
    st.caption("See whether the gender gap varies regionally — province instead of board.")
    prov_gender = gdf_all.groupby(["Province", "Gender"], as_index=False)[["Appeared", "Passed"]].sum()
    prov_gender["Pass %"] = (100 * prov_gender["Passed"] / prov_gender["Appeared"].replace(0, float("nan"))).round(2)
    prov_order = gdf_all.groupby("Province")["Appeared"].sum().sort_values(ascending=False).index.tolist()

    pc1, pc2 = st.columns(2)
    with pc1:
        prov_pivot_app = prov_gender.pivot_table(index="Province", columns="Gender", values="Appeared", aggfunc="sum").reindex(prov_order)
        series_prov_app = {}
        for g in ["Male", "Female"]:
            if g in prov_pivot_app.columns:
                series_prov_app["Boys" if g == "Male" else "Girls"] = prov_pivot_app[g].fillna(0).astype(int).tolist()
        show_chart(grouped_bar_chart(
            prov_pivot_app.index.tolist(), series_prov_app, title="Appeared — Boys vs Girls, by Province",
            y_title="Students Appeared", colors=[GENDER_COLORS["Male"], GENDER_COLORS["Female"]],
        ))
    with pc2:
        prov_pivot_pct = prov_gender.pivot_table(index="Province", columns="Gender", values="Pass %", aggfunc="mean").reindex(prov_order)
        series_prov_pct = {}
        for g in ["Male", "Female"]:
            if g in prov_pivot_pct.columns:
                series_prov_pct["Boys" if g == "Male" else "Girls"] = prov_pivot_pct[g].fillna(0).round(1).tolist()
        show_chart(grouped_bar_chart(
            prov_pivot_pct.index.tolist(), series_prov_pct, title="Pass % by Gender, by Province",
            y_title="Pass %", colors=[GENDER_COLORS["Male"], GENDER_COLORS["Female"]],
            show_values=True, value_suffix="%",
        ))

    gap_rows = []
    for p in prov_order:
        sub = prov_gender[prov_gender["Province"] == p].set_index("Gender")
        if "Male" in sub.index and "Female" in sub.index:
            gap_rows.append({
                "Province": p,
                "Boys Appeared": int(sub.loc["Male", "Appeared"]),
                "Girls Appeared": int(sub.loc["Female", "Appeared"]),
                "Boys Pass %": round(float(sub.loc["Male", "Pass %"]), 1),
                "Girls Pass %": round(float(sub.loc["Female", "Pass %"]), 1),
                "Gender Gap (pts, Girls-Boys)": round(float(sub.loc["Female", "Pass %"] - sub.loc["Male", "Pass %"]), 1),
            })
    gap_df = pd.DataFrame(gap_rows)
    if not gap_df.empty:
        st.markdown("**Province-wise gender breakdown**")
        st.dataframe(gap_df, width='stretch', hide_index=True)
        csv_download_button(gap_df, "⬇️ Download province-gender CSV", "gender_by_province.csv")

with chart_card("Gender Breakdown Table", f"{year_label}, every board"):
    st.dataframe(gdf_all.sort_values(["Board", "Gender"]), width='stretch', hide_index=True)
    csv_download_button(gdf_all, "⬇️ Download CSV", "gender_wise_breakdown.csv")

st.markdown("---")
st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")
