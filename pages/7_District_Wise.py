"""
District Wise — one combined page across every board whose gazette actually
publishes a district breakdown. Boards without district data are simply left
out — never estimated or interpolated.
"""
import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar
from components.topbar import render_topbar
from components.page_header import render_page_header
from components.kpi_card import render_kpi_row
from common import (
    inject_css, load_workbook, show_missing_workbook_error,
    district_df_for, boards_with_district_data,
    show_chart, district_pass_hbar, treemap_chart, bubble_scatter_chart,
    csv_download_button, fmt_k, ALL_BOARD_NAMES, chart_card,
)

st.set_page_config(page_title="District Wise — 11th Class Results", page_icon="🏙️", layout="wide")
inject_css()
render_sidebar()

try:
    data = load_workbook()
except FileNotFoundError:
    show_missing_workbook_error()
    st.stop()

render_topbar(
    active_page="District Wise",
    subtitle="District-level pass % from every board whose gazette publishes one — no estimates.",
    stat_label="BISE Boards",
    stat_value="15",
    stat_icon="account_balance",
)

year_choice = render_page_header(
    title="Select Year to View Results",
    year_options=[2025, 2024, "All Years"],
    year_default=2025,
    key="district_year_selector",
)
year = None if year_choice in (None, "All Years") else int(year_choice)
year_label = "All Years" if year is None else str(year_choice)

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

kpis = [
    dict(icon="location_city", value=str(len(all_districts)), label="DISTRICTS REPORTED",
         delta=f"Across {len(district_boards)} reporting boards", delta_positive=True, accent="blue"),
    dict(icon="group", value=fmt_k(int(all_districts["Appeared"].sum())), label="TOTAL APPEARED",
         delta="All reporting districts", delta_positive=True, accent="gold"),
    dict(icon="emoji_events", value=f"{all_districts.iloc[0]['Pass %']:.1f}%", label="BEST DISTRICT",
         delta=f"{all_districts.iloc[0]['Label']}", delta_positive=True, accent="green"),
    dict(icon="trending_down", value=f"{all_districts.iloc[-1]['Pass %']:.1f}%", label="WEAKEST DISTRICT",
         delta=f"{all_districts.iloc[-1]['Label']}", delta_positive=False, accent="red"),
]
render_kpi_row(kpis)

# ── Top 10 districts ────────────────────────────────────────────────────────
with chart_card("Top 10 Districts by Pass %", f"{year_label}, all reporting boards"):
    top10 = all_districts.head(10)[["Label", "Pass %"]].rename(columns={"Label": "District"})
    show_chart(district_pass_hbar(top10, top_n=10))

# ── Every other reporting district ──────────────────────────────────────────
rest = all_districts.iloc[10:]
if not rest.empty:
    with chart_card(f"All Other Districts ({len(rest)})", "Same metric, the long tail"):
        rest_chart_df = rest[["Label", "Pass %"]].rename(columns={"Label": "District"})
        show_chart(district_pass_hbar(rest_chart_df, top_n=len(rest_chart_df), title=f"District Pass % — remaining {len(rest)} districts"))

sc1, sc2 = st.columns(2)
with sc1:
    with chart_card("District Share by Enrollment", "All districts by students appeared"):
        show_chart(treemap_chart(all_districts["Label"].tolist(), all_districts["Appeared"].tolist(), title="All Districts by Students Appeared"))
with sc2:
    with chart_card("District Size vs Pass %", "Bubble size = students appeared"):
        show_chart(bubble_scatter_chart(all_districts["Appeared"].tolist(), all_districts["Pass %"].tolist(),
                                        all_districts["Appeared"].tolist(), all_districts["Label"].tolist(),
                                        title="Students Appeared vs Pass %", x_title="Students Appeared"))

with chart_card("Every Reporting District — Full Table", f"{year_label}, all reporting boards"):
    table = all_districts[["District", "Board", "Appeared", "Passed", "Pass %"]].sort_values(["Board", "Pass %"], ascending=[True, False])
    st.dataframe(table, width='stretch', hide_index=True)
    csv_download_button(table, "⬇️ Download all-boards district CSV", "district_wise_all_boards.csv")

st.markdown("---")
st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")
