"""
Group Wise — Pre-Medical / Pre-Engineering / Humanities / Commerce /
General Science / Home Economics performance across BISE boards.

Unique to the 11th class (HSSC) dashboard — this page exists because the
11th workbook publishes group-wise results.
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
    group_totals_df_for, group_gender_df_for, boards_with_group_data,
    show_chart, csv_download_button, fmt_k,
    grouped_bar_chart, treemap_chart, bubble_scatter_chart,
    chart_title, chart_margins, style_fig,
    ACCENT, GENDER_COLORS, ALL_BOARD_NAMES, chart_card,
)

st.set_page_config(page_title="Group Wise — 11th Class Results", page_icon="🧪", layout="wide")
inject_css()
render_sidebar()

try:
    data = load_workbook()
except FileNotFoundError:
    show_missing_workbook_error()
    st.stop()

render_topbar(
    active_page="Group Wise",
    subtitle="Pre-Medical / Pre-Engineering / Humanities / Commerce / General Science performance across BISE boards.",
    stat_label="BISE Boards",
    stat_value="15",
    stat_icon="account_balance",
)

year_choice = render_page_header(
    title="Select Year to View Results",
    year_options=[2025, 2024, "All Years"],
    year_default=2025,
    key="group_year_selector",
)
year = None if year_choice in (None, "All Years") else int(year_choice)
year_label = "All Years" if year is None else str(year_choice)

picked = render_filter_row([
    {"label": "Boards", "options": ALL_BOARD_NAMES, "default": [], "key": "group_boards_filter",
     "multi": True, "dropdown": True},
])
boards_sel = picked.get("group_boards_filter") or list(ALL_BOARD_NAMES)
if not boards_sel:
    st.info("Select at least one board in the Boards filter to see results.")
    st.stop()

reporting = [b for b in boards_sel if b in boards_with_group_data(data)]
not_reporting = [b for b in boards_sel if b not in reporting]

group_rows, gender_rows = [], []
for name in boards_sel:
    gt = group_totals_df_for(data, name, year)
    if not gt.empty:
        gt = gt.copy()
        gt["Board"] = name
        group_rows.append(gt)
    gg = group_gender_df_for(data, name, year)
    if not gg.empty:
        gg = gg.copy()
        gg["Board"] = name
        gender_rows.append(gg)

if not group_rows:
    st.info("No group-wise data available for the selected boards/year.")
    st.stop()

all_groups = pd.concat(group_rows, ignore_index=True)
combined = all_groups.groupby("Group", as_index=False)[["Appeared", "Passed"]].sum()
combined["Pass %"] = (100 * combined["Passed"] / combined["Appeared"].replace(0, float("nan"))).round(2)
combined = combined.sort_values("Pass %", ascending=False)

best = combined.iloc[0]
worst = combined.sort_values("Pass %").iloc[0]
kpis = [
    dict(icon="category", value=str(len(combined)), label="GROUPS REPORTED",
         delta=f"{len(reporting)} of {len(boards_sel)} boards", delta_positive=True, accent="blue"),
    dict(icon="trending_up", value=f"{best['Pass %']:.1f}%", label="STRONGEST GROUP",
         delta=f"{best['Group']} · {fmt_k(int(best['Appeared']))} appeared", delta_positive=True, accent="green"),
    dict(icon="trending_down", value=f"{worst['Pass %']:.1f}%", label="WEAKEST GROUP",
         delta=f"{worst['Group']} · {fmt_k(int(worst['Appeared']))} appeared", delta_positive=False, accent="red"),
]
render_kpi_row(kpis)

if not_reporting:
    st.caption(f"⚠️ Group-wise results not published for: {', '.join(not_reporting)}.")

with chart_card("Pass % by Group", f"{year_label}, all selected boards combined"):
    fig = go.Figure(go.Bar(x=combined["Pass %"], y=combined["Group"], orientation="h", marker_color=ACCENT,
                           text=combined["Pass %"], texttemplate="%{text:.1f}%", textposition="outside"))
    fig.update_layout(title=chart_title(f"Group Pass % ({year_label})"), height=max(360, 44 * len(combined)),
                      xaxis_range=[0, 105], showlegend=False, margin=chart_margins(extra_right=40))
    show_chart(style_fig(fig))
    csv_download_button(combined, "⬇️ Download combined group-wise CSV", "group_wise_combined.csv")

if gender_rows:
    all_gender = pd.concat(gender_rows, ignore_index=True)
    gcombined = all_gender.groupby(["Group", "Gender"], as_index=False)[["Appeared", "Passed"]].sum()
    gcombined["Pass %"] = (100 * gcombined["Passed"] / gcombined["Appeared"].replace(0, float("nan"))).round(2)
    pivot = gcombined.pivot_table(index="Group", columns="Gender", values="Pass %", aggfunc="mean")
    pivot = pivot.reindex(combined["Group"].tolist())
    # A group reported only as a "Total" (no Male/Female split — e.g. Islamic
    # Studies (Private)) has no gender row at all here, not a real 0% — drop
    # it instead of faking a 0.0/0.0 bar.
    dropped_groups = pivot[pivot.isna().all(axis=1)].index.tolist()
    pivot = pivot.dropna(how="all")
    series = {}
    for g in ["Male", "Female"]:
        if g in pivot.columns:
            series["Boys" if g == "Male" else "Girls"] = pivot[g].fillna(0).round(1).tolist()
    with chart_card("Pass % by Group and Gender", "Boys vs Girls within each group"):
        show_chart(grouped_bar_chart(pivot.index.tolist(), series, "Group Pass % — Boys vs Girls", y_title="Pass %",
                                     colors=[GENDER_COLORS["Male"], GENDER_COLORS["Female"]],
                                     show_values=True, value_suffix="%"))
        if dropped_groups:
            st.caption(f"⚠️ No Male/Female split reported for: {', '.join(dropped_groups)} (only a combined total is published), so they're left out of this chart.")


sc1, sc2 = st.columns(2)
with sc1:
    with chart_card("Group Share by Enrollment", "Students appeared per group"):
        show_chart(treemap_chart(combined["Group"].tolist(), combined["Appeared"].tolist(), "Groups by Students Appeared"))
with sc2:
    with chart_card("Group Size vs Pass %", "Bubble size = students appeared"):
        show_chart(bubble_scatter_chart(combined["Appeared"].tolist(), combined["Pass %"].tolist(),
                                        combined["Appeared"].tolist(), combined["Group"].tolist(),
                                        title="Students Appeared vs Pass %", x_title="Students Appeared"))

with chart_card("Per-board Detail", "Every board, every group"):
    per_board = all_groups.sort_values(["Board", "Pass %"], ascending=[True, False])
    st.dataframe(per_board, width='stretch', hide_index=True)
    csv_download_button(per_board, "⬇️ Download per-board CSV", "group_wise_per_board.csv")

st.markdown("---")
st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")
