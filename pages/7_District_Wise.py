"""
District-wise Analysis — a single combined page across every board whose
gazette actually publishes a district breakdown (Bahawalpur, DG Khan,
Faisalabad, Rawalpindi, Sahiwal, Sargodha). Boards without district data are
simply left out — never estimated or interpolated. This page intentionally
ignores the sidebar's board picker (district reporting is inconsistent across
boards, so gating the page on it just produced empty screens) and only
follows the global Year filter.
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
    year, boards_sel, year_choice = render_global_filters(data, ALL_BOARD_NAMES, show_boards_filter=False)
    st.markdown("---")
    year_label_sb = "All Years" if year_choice == "All Years" else year_choice
    render_currently_viewing(f"District-wise — All reporting boards<br>{year_label_sb}")

year_label = "All Years" if year is None else str(year)
st.markdown(render_hero_banner(15), unsafe_allow_html=True)
st.subheader(f"🏙️ District-wise Analysis — All Boards, {year_label}")

district_boards = boards_with_district_data(data)
not_reporting = [b for b in ALL_BOARD_NAMES if b not in district_boards]
st.caption(
    f"✅ District-wise results are published in the source workbook for: {', '.join(district_boards)}."
    + (f"  ⚠️ Not published for: {', '.join(not_reporting)}." if not_reporting else "")
)

# ── Build one combined table across every reporting board ──────────────────
frames = []
for b in district_boards:
    d = district_df_for(data, b, year)
    if d.empty:
        continue
    d = d.copy()
    d["Board"] = b
    d["Label"] = d["District"] + " (" + d["Board"].str.replace("BISE ", "", regex=False) + ")"
    frames.append(d)

if not frames:
    st.info(f"No district-wise data is available for {year_label}.")
    st.stop()

all_districts = pd.concat(frames, ignore_index=True).sort_values("Pass %", ascending=False).reset_index(drop=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(kpi_card("DISTRICTS", str(len(all_districts)), f"Across {len(district_boards)} reporting boards", NAVY), unsafe_allow_html=True)
with c2:
    st.markdown(kpi_card("TOTAL APPEARED", fmt_k(int(all_districts["Appeared"].sum())), "All reporting districts", NAVY), unsafe_allow_html=True)
with c3:
    best = all_districts.iloc[0]
    st.markdown(kpi_card("BEST DISTRICT", f"{best['Pass %']:.1f}%", f"{best['Label']} · {fmt_k(int(best['Appeared']))} appeared", TEAL), unsafe_allow_html=True)
with c4:
    worst = all_districts.iloc[-1]
    st.markdown(kpi_card("WEAKEST DISTRICT", f"{worst['Pass %']:.1f}%", f"{worst['Label']} · {fmt_k(int(worst['Appeared']))} appeared", "#E11D48"), unsafe_allow_html=True)

# ── Top 10 districts ────────────────────────────────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("🏆 Top 10 Districts by Pass %")
top10 = all_districts.head(10)[["Label", "Pass %"]].rename(columns={"Label": "District"})
show_chart(district_pass_hbar(top10, top_n=10))
st.markdown("</div>", unsafe_allow_html=True)

# ── Every other reporting district ──────────────────────────────────────────
rest = all_districts.iloc[10:]
if not rest.empty:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader(f"📊 All Other Districts ({len(rest)})")
    rest_chart_df = rest[["Label", "Pass %"]].rename(columns={"Label": "District"})
    show_chart(district_pass_hbar(rest_chart_df, top_n=len(rest_chart_df), title=f"District Pass % — remaining {len(rest)} districts"))
    st.markdown("</div>", unsafe_allow_html=True)

sc1, sc2 = st.columns(2)
with sc1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🌳 District Share by Enrollment")
    show_chart(treemap_chart(all_districts["Label"].tolist(), all_districts["Appeared"].tolist(), title="All Districts by Students Appeared"))
    st.markdown("</div>", unsafe_allow_html=True)
with sc2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🎯 District Size vs Pass %")
    show_chart(bubble_scatter_chart(all_districts["Appeared"].tolist(), all_districts["Pass %"].tolist(),
                                    all_districts["Appeared"].tolist(), all_districts["Label"].tolist(),
                                    title="Students Appeared vs Pass %", x_title="Students Appeared"))
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("📋 Every Reporting District — Full Table")
table = all_districts[["District", "Board", "Appeared", "Passed", "Pass %"]].sort_values(["Board", "Pass %"], ascending=[True, False])
st.dataframe(table, use_container_width=True, hide_index=True)
csv_download_button(table, "⬇️ Download all-boards district CSV", "district_wise_all_boards.csv")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")
