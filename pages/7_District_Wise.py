"""
District-wise Analysis — only the boards whose gazette actually publishes a
district breakdown appear here (Bahawalpur, DG Khan, Faisalabad, Rawalpindi,
Sahiwal, Sargodha). Boards without district data are simply not shown —
never estimated or interpolated.
"""
import pandas as pd
import streamlit as st

from common import (
    inject_css, render_hero_banner, render_sidebar_brand, render_currently_viewing,
    render_global_filters,
    load_workbook, show_missing_workbook_error,
    district_df_for, boards_with_district_data,
    kpi_card, show_chart, district_pass_hbar, treemap_chart, bubble_scatter_chart,
    csv_download_button, fmt_k, NAVY, TEAL, ALL_BOARD_NAMES,
)

st.set_page_config(page_title="District-wise Analysis — BISE Dashboard", page_icon="🏙️", layout="wide")
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
    render_currently_viewing(f"District-wise — {len(boards_sel)} board(s)<br>{year_label_sb}")

if not boards_sel:
    st.info("Select at least one board from the sidebar Filters to see results.")
    st.stop()

year_label = "All Years" if year is None else str(year)
st.markdown(render_hero_banner(15), unsafe_allow_html=True)
st.subheader(f"🏙️ District-wise Analysis — {year_label}")

district_boards = boards_with_district_data(data)
reporting = [b for b in boards_sel if b in district_boards]
not_reporting = [b for b in boards_sel if b not in district_boards]

st.caption(
    f"✅ District-wise results are published in the source workbook for: {', '.join(district_boards)}."
    + (f"  ⚠️ Not published for: {', '.join(not_reporting)}." if not_reporting else "")
)

if not reporting:
    st.info("None of the currently-selected boards publish a district-wise breakdown. Pick one of the boards listed above from the sidebar Filters.")
    st.stop()

board_pick = st.selectbox("🏫 Board", reporting, key="district_board_pick")

dist_df = district_df_for(data, board_pick, year)
if dist_df.empty:
    st.info(f"No district data for {board_pick} in {year_label}.")
    st.stop()

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(kpi_card("DISTRICTS", str(len(dist_df)), board_pick, NAVY), unsafe_allow_html=True)
with c2:
    best = dist_df.sort_values("Pass %", ascending=False).iloc[0]
    st.markdown(kpi_card("BEST DISTRICT", f"{best['Pass %']:.1f}%", f"{best['District']} · {fmt_k(int(best['Appeared']))} appeared", TEAL), unsafe_allow_html=True)
with c3:
    worst = dist_df.sort_values("Pass %").iloc[0]
    st.markdown(kpi_card("WEAKEST DISTRICT", f"{worst['Pass %']:.1f}%", f"{worst['District']} · {fmt_k(int(worst['Appeared']))} appeared", "#E11D48"), unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader(f"📊 District Pass % — {board_pick}")
show_chart(district_pass_hbar(dist_df, top_n=len(dist_df)))
csv_download_button(dist_df, "⬇️ Download district CSV", f"{board_pick}_districts.csv")
st.markdown("</div>", unsafe_allow_html=True)

sc1, sc2 = st.columns(2)
with sc1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🌳 District Share by Enrollment")
    show_chart(treemap_chart(dist_df["District"].tolist(), dist_df["Appeared"].tolist(), title="Districts by Students Appeared"))
    st.markdown("</div>", unsafe_allow_html=True)
with sc2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🎯 District Size vs Pass %")
    show_chart(bubble_scatter_chart(dist_df["Appeared"].tolist(), dist_df["Pass %"].tolist(),
                                    dist_df["Appeared"].tolist(), dist_df["District"].tolist(),
                                    title="Students Appeared vs Pass %", x_title="Students Appeared"))
    st.markdown("</div>", unsafe_allow_html=True)

if len(reporting) > 1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("📋 District Results — Every Reporting Board")
    frames = []
    for b in reporting:
        d = district_df_for(data, b, year)
        if d.empty:
            continue
        d = d.copy()
        d["Board"] = b
        frames.append(d)
    all_districts = pd.concat(frames, ignore_index=True).sort_values(["Board", "Pass %"], ascending=[True, False])
    st.dataframe(all_districts, use_container_width=True, hide_index=True)
    csv_download_button(all_districts, "⬇️ Download all-boards district CSV", "district_wise_all_boards.csv")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")
