"""
Province Wise — aggregates BISE boards by province (KPK, Punjab, Federal).
Province is static metadata (which province each BISE board sits in) — not
derived from the results workbook.
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
    board_totals, yearly_trend_df_for,
    show_chart, style_fig, fmt_k, csv_download_button,
    donut_pie, grouped_bar_chart, treemap_chart,
    PROVINCE_COLORS, PASS_COLOR, FAIL_COLOR, NAVY, ALL_BOARD_NAMES,
    BOARD_PROVINCE, chart_card,
)

st.set_page_config(page_title="Province Wise — 11th Class Results", page_icon="🗺️", layout="wide")
inject_css()
render_sidebar()

try:
    data = load_workbook()
except FileNotFoundError:
    show_missing_workbook_error()
    st.stop()

render_topbar(
    active_page="Province Wise",
    subtitle="Results aggregated by province — KPK, Punjab and Federal (Islamabad) boards.",
    stat_label="BISE Boards",
    stat_value="15",
    stat_icon="account_balance",
)

year_choice = render_page_header(
    title="Select Year to View Results",
    year_options=[2025, 2024, "All Years"],
    year_default=2025,
    key="province_year_selector",
)
year = None if year_choice in (None, "All Years") else int(year_choice)
year_label = "All Years" if year is None else str(year_choice)

picked = render_filter_row([
    {"label": "Boards", "options": ALL_BOARD_NAMES, "default": [], "key": "province_boards_filter",
     "multi": True, "dropdown": True},
])
boards_sel = picked.get("province_boards_filter") or list(ALL_BOARD_NAMES)
if not boards_sel:
    st.info("Select at least one board in the Boards filter to see results.")
    st.stop()

rows = []
for name in boards_sel:
    totals = board_totals(data, name, year)
    if totals["appeared"] <= 0:
        continue
    province_name = BOARD_PROVINCE.get(name, "Other")
    rows.append({
        "Board": name, "Province": province_name,
        "Appeared": totals["appeared"], "Passed": totals["passed"],
        "Failed": totals["failed"],
    })

df = pd.DataFrame(rows)
if df.empty:
    st.info("No board totals available for the selected year.")
    st.stop()

prov = df.groupby("Province", as_index=False)[["Appeared", "Passed", "Failed"]].sum()
prov["Pass %"] = (100 * prov["Passed"] / prov["Appeared"].replace(0, float('nan'))).round(2)
prov = prov.sort_values("Pass %", ascending=False)

accent_map = {"Punjab": "blue", "KPK": "gold", "Federal (Islamabad)": "red"}
kpis = []
for _, r in prov.iterrows():
    kpis.append(dict(
        icon="public", value=f"{r['Pass %']:.1f}%", label=f"{r['Province'].upper()} PASS %",
        delta=f"{fmt_k(int(r['Appeared']))} appeared", delta_positive=True,
        accent=accent_map.get(r["Province"], "blue"),
    ))
for i in range(0, len(kpis), 4):
    render_kpi_row(kpis[i:i + 4])

col1, col2 = st.columns([1, 1])
with col1:
    with chart_card("Appeared Share by Province", f"{year_label}, by students appeared"):
        show_chart(donut_pie(
            prov["Province"].tolist(), prov["Appeared"].tolist(),
            [PROVINCE_COLORS.get(p, NAVY) for p in prov["Province"]],
            title="Appeared Share by Province", height=400,
        ))
with col2:
    with chart_card("Pass % by Province", f"{year_label}"):
        fig2 = go.Figure(go.Bar(
            x=prov["Province"], y=prov["Pass %"],
            marker_color=[PROVINCE_COLORS.get(p, NAVY) for p in prov["Province"]],
            text=[f"{v:.1f}%" for v in prov["Pass %"]], textposition="outside",
        ))
        fig2.update_layout(title="Pass % by Province", yaxis_range=[0, 100])
        show_chart(style_fig(fig2))

pc1, pc2 = st.columns([1, 1])
with pc1:
    with chart_card("Passed vs Failed by Province", f"{year_label}, raw counts"):
        show_chart(grouped_bar_chart(
            prov["Province"].tolist(),
            {"Passed": prov["Passed"].astype(int).tolist(), "Failed": prov["Failed"].astype(int).tolist()},
            title="Passed vs Failed by Province", y_title="Students",
            colors=[PASS_COLOR, FAIL_COLOR],
        ))
with pc2:
    with chart_card("Province Share of Appeared", "Treemap, by students appeared"):
        show_chart(treemap_chart(
            prov["Province"].tolist(), prov["Appeared"].tolist(),
            title="Province Share by Students Appeared",
        ))

with chart_card("Boards within Each Province", "Board-level appeared/passed under the current filters"):
    df_display = df.assign(**{"Pass %": (100 * df["Passed"] / df["Appeared"].replace(0, float('nan'))).round(2)})
    st.dataframe(
        df_display.sort_values(["Province", "Pass %"], ascending=[True, False]),
        width='stretch', hide_index=True,
    )
    csv_download_button(df_display, "⬇️ Download board-level CSV", "province_wise_boards.csv")

with chart_card("Province Pass % Trend", "Province of each board is static metadata — every workbook year"):
    trend_rows = []
    for name in boards_sel:
        province_name = BOARD_PROVINCE.get(name, "Other")
        t = yearly_trend_df_for(data, name)
        if t.empty:
            continue
        t = t.copy()
        t["Province"] = province_name
        trend_rows.append(t[["Year", "Appeared", "Passed", "Province"]])

    if trend_rows:
        trend_all = pd.concat(trend_rows, ignore_index=True)
        trend_prov = trend_all.groupby(["Year", "Province"], as_index=False)[["Appeared", "Passed"]].sum()
        trend_prov["Pass %"] = (100 * trend_prov["Passed"] / trend_prov["Appeared"].replace(0, float("nan"))).round(2)

        fig3 = go.Figure()
        for p in trend_prov["Province"].unique():
            sub = trend_prov[trend_prov["Province"] == p].sort_values("Year")
            fig3.add_trace(go.Scatter(
                x=sub["Year"].astype(int).astype(str), y=sub["Pass %"], mode="lines+markers", name=p,
                line=dict(color=PROVINCE_COLORS.get(p, NAVY), width=3),
            ))
        fig3.update_layout(title="Pass % Trend by Province", yaxis=dict(title="Pass %"),
                           xaxis=dict(type="category", title="Year"))
        show_chart(style_fig(fig3))
    else:
        st.caption("ℹ️ No multi-year trend data available.")

st.markdown("---")
st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")
