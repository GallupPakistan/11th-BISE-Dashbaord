"""
Subject Wise — pass % by subject, combined across all boards and per-board.
"""
import pandas as pd
import streamlit as st

from components.sidebar import render_sidebar
from components.topbar import render_topbar
from components.page_header import render_page_header
from components.filter_bar import render_filter_row
from components.kpi_card import render_kpi_row
from common import (
    inject_css, load_workbook, show_missing_workbook_error,
    subject_df_for, boards_with_subject_data,
    show_chart, subject_pass_hbar, bubble_scatter_chart, treemap_chart,
    csv_download_button, fmt_k, ALL_BOARD_NAMES, chart_card,
)

st.set_page_config(page_title="Subject Wise — 11th Class Results", page_icon="📚", layout="wide")
inject_css()
render_sidebar()

try:
    data = load_workbook()
except FileNotFoundError:
    show_missing_workbook_error()
    st.stop()

render_topbar(
    active_page="Subject Wise",
    subtitle="Subject-level pass % combined across every reporting BISE board.",
    stat_label="BISE Boards",
    stat_value="15",
    stat_icon="account_balance",
)

year_choice = render_page_header(
    title="Select Year to View Results",
    year_options=[2025, 2024, "All Years"],
    year_default=2025,
    key="subject_year_selector",
)
year = None if year_choice in (None, "All Years") else int(year_choice)
year_label = "All Years" if year is None else str(year_choice)

picked = render_filter_row([
    {"label": "Boards", "options": ALL_BOARD_NAMES, "default": [], "key": "subject_boards_filter",
     "multi": True, "dropdown": True},
])
boards_sel = picked.get("subject_boards_filter") or list(ALL_BOARD_NAMES)
if not boards_sel:
    st.info("Select at least one board in the Boards filter to see results.")
    st.stop()

frames = []
for name in boards_sel:
    df_s = subject_df_for(data, name, year)
    if df_s.empty:
        continue
    df_s = df_s.copy()
    df_s["Board"] = name
    frames.append(df_s)

if not frames:
    st.info("No subject data available for the selected boards/year.")
    st.stop()

all_subj = pd.concat(frames, ignore_index=True)

combined = all_subj.groupby("Subject", as_index=False)[["Appeared", "Passed"]].sum()
combined["Pass %"] = (100 * combined["Passed"] / combined["Appeared"].replace(0, float("nan"))).round(2)
combined = combined.sort_values("Pass %", ascending=False)

reporting = sorted(all_subj["Board"].unique().tolist())
not_reporting = [b for b in boards_sel if b not in reporting]

with chart_card("Subject-wise Pass %", f"{year_label}, selected boards combined"):
    min_appeared = st.slider(
        "Minimum students appeared (filters out tiny-sample subjects that show misleading 100%/0%)",
        min_value=0, max_value=2000, value=300, step=50, key="subject_min_appeared",
    )
    excluded_count = int((combined["Appeared"] < min_appeared).sum())
    reliable = combined[combined["Appeared"] >= min_appeared].copy()
    if excluded_count:
        st.caption(f"⚠️ {excluded_count} subject(s) below {min_appeared:,} appeared are hidden from rankings/KPIs below (still in the full download).")

    best = reliable.iloc[0] if not reliable.empty else None
    worst = reliable.sort_values("Pass %").iloc[0] if not reliable.empty else None
    kpis = [
        dict(icon="menu_book", value=str(len(reliable)), label=f"SUBJECTS (RELIABLE) · {year_label}",
             delta=f"{len(combined)} total · {len(reporting)} boards report", delta_positive=True, accent="blue"),
        dict(icon="emoji_events", value=(f"{best['Pass %']:.1f}%" if best is not None else "—"), label="BEST SUBJECT",
             delta=(f"{best['Subject']} · {fmt_k(int(best['Appeared']))} appeared" if best is not None else "No subject meets the minimum"),
             delta_positive=True, accent="green"),
        dict(icon="warning", value=(f"{worst['Pass %']:.1f}%" if worst is not None else "—"), label="WEAKEST SUBJECT",
             delta=(f"{worst['Subject']} · {fmt_k(int(worst['Appeared']))} appeared" if worst is not None else "No subject meets the minimum"),
             delta_positive=False, accent="red"),
    ]
    render_kpi_row(kpis)

    if not_reporting:
        st.caption(f"⚠️ Subject-wise results not published for: {', '.join(not_reporting)}.")

    view_mode = st.radio(
        "View",
        ["📊 Top 10 (Chart)", "📋 All Subjects (Table)"],
        horizontal=True,
        label_visibility="collapsed",
        key="subject_view_mode",
    )

    if view_mode == "📊 Top 10 (Chart)":
        top10 = reliable.head(10)
        if top10.empty:
            st.info("No subjects meet the minimum-appeared threshold above. Lower the slider to see results.")
        else:
            show_chart(subject_pass_hbar(top10, top_n=10))
            st.caption(
                f"Showing the top 10 of **{len(reliable)}** subjects with at least {min_appeared:,} students appeared, by Pass %. "
                "Switch to **All Subjects (Table)** above to see the rest — it's searchable and downloadable."
            )
    else:
        search = st.text_input("🔍 Search subjects", placeholder="Type to filter by subject name...", key="subject_search")
        table_df = reliable.copy()
        if search:
            table_df = table_df[table_df["Subject"].str.contains(search, case=False, na=False)]
        st.dataframe(table_df, width='stretch', hide_index=True)

    csv_download_button(combined, "⬇️ Download combined CSV (all subjects, no threshold)", "subject_wise_combined.csv")

sc1, sc2 = st.columns([1, 1])
with sc1:
    with chart_card("Weakest 10 Subjects", f"Lowest pass % among the {len(reliable)} meeting the {min_appeared:,}-appeared floor"):
        weakest10 = reliable.tail(10)
        if weakest10.empty:
            st.info("No subjects meet the minimum-appeared threshold above.")
        else:
            show_chart(subject_pass_hbar(weakest10, top_n=10))
with sc2:
    with chart_card("Subject Size vs Pass %", "Bubble size = students appeared"):
        if reliable.empty:
            st.info("No subjects meet the minimum-appeared threshold above.")
        else:
            bubble_df = reliable.sort_values("Appeared", ascending=False).head(25)
            show_chart(bubble_scatter_chart(
                bubble_df["Appeared"].tolist(), bubble_df["Pass %"].tolist(), bubble_df["Appeared"].tolist(),
                bubble_df["Subject"].tolist(), title="Students Appeared vs Pass %", x_title="Students Appeared",
            ))
            st.caption("Bubble size = students appeared. Shows whether larger-enrollment subjects pass at higher or lower rates.")

with chart_card("Subject Share by Enrollment", "Subjects by students appeared"):
    if reliable.empty:
        st.info("No subjects meet the minimum-appeared threshold above.")
    else:
        show_chart(treemap_chart(reliable["Subject"].tolist(), reliable["Appeared"].tolist(), title="Subjects by Students Appeared"))

with chart_card("Per-board Detail", "Every board, every subject"):
    per_board_display = all_subj.sort_values(["Board", "Pass %"], ascending=[True, False])
    st.dataframe(per_board_display, width='stretch', hide_index=True)
    csv_download_button(per_board_display, "⬇️ Download per-board CSV", "subject_wise_per_board.csv")

st.markdown("---")
st.caption("Data source: 11th Class Boards Results — Combined workbook only · no estimated values")
