"""
Group-wise Analysis — Pre-Medical / Pre-Engineering / Humanities / Commerce /
General Science / Home Economics performance across BISE boards.

Unique to the 11th class (HSSC) dashboard: SSC (10th) has no subject groups,
so this page has no 10th-grade equivalent — it exists because the 11th
workbook actually publishes group-wise results.
"""
import pandas as pd
import streamlit as st

from common import (
    inject_css, render_hero_banner, render_sidebar_brand, render_currently_viewing,
    render_global_filters,
    load_workbook, show_missing_workbook_error,
    group_totals_df_for, group_gender_df_for, boards_with_group_data,
    kpi_card, show_chart, csv_download_button, fmt_k,
    grouped_bar_chart, treemap_chart, bubble_scatter_chart,
    NAVY, TEAL, ACCENT, GENDER_COLORS, ALL_BOARD_NAMES,
)
import plotly.graph_objects as go
from common import chart_title, chart_margins, style_fig

st.set_page_config(page_title="Group-wise Analysis — BISE Dashboard", page_icon="🧬", layout="wide")
inject_css()

try:
    data = load_workbook()
except FileNotFoundError:
    show_missing_workbook_error()

with st.sidebar:
    render_sidebar_brand()
    st.markdown("---")
    year, boards_sel, year_choice = render_global_filters(data, ALL_BOARD_NAMES)
    st.markdown("---")
    year_label_sb = "All Years" if year_choice == "All Years" else year_choice
    render_currently_viewing(f"Group-wise — {len(boards_sel)} board(s)<br>{year_label_sb}")

if not boards_sel:
    st.info("Select at least one board from the sidebar Filters to see results.")
    st.stop()

year_label = "All Years" if year is None else str(year)
st.markdown(render_hero_banner(15), unsafe_allow_html=True)
st.subheader(f"🧬 Group-wise Analysis — {len(boards_sel)} board(s), {year_label}")

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

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(kpi_card("GROUPS", str(len(combined)), f"{len(reporting)} of {len(boards_sel)} boards report groups", NAVY), unsafe_allow_html=True)
with c2:
    best = combined.iloc[0]
    st.markdown(kpi_card("STRONGEST GROUP", f"{best['Pass %']:.1f}%", f"{best['Group']} · {fmt_k(int(best['Appeared']))} appeared", TEAL), unsafe_allow_html=True)
with c3:
    worst = combined.sort_values("Pass %").iloc[0]
    st.markdown(kpi_card("WEAKEST GROUP", f"{worst['Pass %']:.1f}%", f"{worst['Group']} · {fmt_k(int(worst['Appeared']))} appeared", "#E11D48"), unsafe_allow_html=True)

if not_reporting:
    st.caption(f"⚠️ Group-wise results not published for: {', '.join(not_reporting)}.")

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("📊 Pass % by Group — All Selected Boards Combined")
fig = go.Figure(go.Bar(x=combined["Pass %"], y=combined["Group"], orientation="h", marker_color=ACCENT,
                        text=combined["Pass %"], texttemplate="%{text:.1f}%", textposition="outside"))
fig.update_layout(title=chart_title(f"Group Pass % ({year_label})"), height=max(360, 44 * len(combined)),
                   xaxis_range=[0, 105], showlegend=False, margin=chart_margins(extra_right=40))
show_chart(style_fig(fig))
csv_download_button(combined, "⬇️ Download combined group-wise CSV", "group_wise_combined.csv")
st.markdown("</div>", unsafe_allow_html=True)

if gender_rows:
    all_gender = pd.concat(gender_rows, ignore_index=True)
    gcombined = all_gender.groupby(["Group", "Gender"], as_index=False)[["Appeared", "Passed"]].sum()
    gcombined["Pass %"] = (100 * gcombined["Passed"] / gcombined["Appeared"].replace(0, float("nan"))).round(2)
    pivot = gcombined.pivot_table(index="Group", columns="Gender", values="Pass %", aggfunc="mean")
    pivot = pivot.reindex(combined["Group"].tolist())
    # A group reported only as a "Total" (no Male/Female split — e.g. Islamic Studies (Private))
    # has no gender row at all here, not a real 0% — drop it instead of faking a 0.0/0.0 bar.
    dropped_groups = pivot[pivot.isna().all(axis=1)].index.tolist()
    pivot = pivot.dropna(how="all")
    series = {}
    for g in ["Male", "Female"]:
        if g in pivot.columns:
            series["Boys" if g == "Male" else "Girls"] = pivot[g].fillna(0).round(1).tolist()
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("👥 Pass % by Group and Gender")
    show_chart(grouped_bar_chart(pivot.index.tolist(), series, "Group Pass % — Boys vs Girls", y_title="Pass %",
                                  colors=[GENDER_COLORS["Male"], GENDER_COLORS["Female"]],
                                  show_values=True, value_suffix="%"))
    if dropped_groups:
        st.caption(f"⚠️ No Male/Female split reported for: {', '.join(dropped_groups)} (only a combined total is published), so they're left out of this chart.")
    st.markdown("</div>", unsafe_allow_html=True)


sc1, sc2 = st.columns(2)
with sc1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🌳 Group Share by Enrollment")
    show_chart(treemap_chart(combined["Group"].tolist(), combined["Appeared"].tolist(), "Groups by Students Appeared"))
    st.markdown("</div>", unsafe_allow_html=True)
with sc2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🎯 Group Size vs Pass %")
    show_chart(bubble_scatter_chart(combined["Appeared"].tolist(), combined["Pass %"].tolist(),
                                    combined["Appeared"].tolist(), combined["Group"].tolist(),
                                    title="Students Appeared vs Pass %", x_title="Students Appeared"))
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("**Per-board detail — every board, every group**")
per_board = all_groups.sort_values(["Board", "Pass %"], ascending=[True, False])
st.dataframe(per_board, use_container_width=True, hide_index=True)
csv_download_button(per_board, "⬇️ Download per-board CSV", "group_wise_per_board.csv")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")