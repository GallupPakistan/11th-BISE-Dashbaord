"""views_board.py -- Single-board deep-dive page rendering logic."""
import pandas as pd
import streamlit as st
from common import *


def render_board_page(selected_board_name, data, year, selected_year):
    totals = board_totals(data, selected_board_name, year)
    gender_df = gender_df_for(data, selected_board_name, year)
    type_df = type_df_for(data, selected_board_name, year)
    group_gender_df = group_gender_df_for(data, selected_board_name, year)
    group_totals = group_totals_df_for(data, selected_board_name, year)
    subjects = subject_df_for(data, selected_board_name, year)
    districts = district_df_for(data, selected_board_name, year)
    trend_df = yearly_trend_df_for(data, selected_board_name)

    if totals["appeared"] <= 0:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(f"**No records** in the workbook for **{selected_board_name}** · **{selected_year}**.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    total_appeared = totals["appeared"]
    total_passed = totals["passed"]
    total_failed = totals["failed"]
    pass_pct = totals["pass_pct"]
    fail_pct = round(100 - pass_pct, 1) if pass_pct else 0
    yoy = yoy_delta_from_trend(trend_df)

    insights = build_insights(gender_df, type_df, group_totals, subjects, pass_pct, yoy)
    st.markdown(
        f"""<div class="board-header">
        <div class="board-header-title">{selected_board_name}</div>
        <div class="board-header-sub">{selected_year} · Total Appeared: <strong>{total_appeared:,}</strong> students</div>
        </div>""",
        unsafe_allow_html=True,
    )

    render_notes(totals["notes"])

    _gaps = []
    if gender_df.empty:
        _gaps.append("Boys/Girls split not published for this selection")
    if type_df.empty:
        _gaps.append("Regular/Private split not published for this selection")
    if subjects.empty:
        _gaps.append("Subject-wise pass % not published for this selection")
    if districts.empty:
        _gaps.append("District-wise results not published for this board")
    if _gaps:
        st.caption("⚠️ Data completeness: " + " · ".join(_gaps))

    render_gender_type_flow(selected_board_name, str(selected_year), totals, gender_df, type_df)

    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.subheader("💡 Key Insights")
    for line in insights:
        st.markdown(f"- {line}")
    st.markdown("</div>", unsafe_allow_html=True)

    boys_total = totals["male_appeared"]
    girls_total = totals["female_appeared"]
    gender_value = f"{fmt_k(boys_total)} / {fmt_k(girls_total)}" if boys_total + girls_total > 0 else "Not available"
    reg_total = priv_total = 0
    if not type_df.empty and "Candidate Type" in type_df.columns:
        regular = type_df[type_df["Candidate Type"] == "Regular"]
        private = type_df[type_df["Candidate Type"] == "Private"]
        reg_total = int(regular["Appeared"].sum()) if not regular.empty else 0
        priv_total = int(private["Appeared"].sum()) if not private.empty else 0
    trend_note = f" · YoY Δ {yoy:+.1f}%" if yoy is not None else ""

    kpi_data = [
        ("Total Appeared", fmt_k(total_appeared), f"{selected_year if selected_year != 'All Years' else 'All years combined'}"),
        ("Total Pass", fmt_k(total_passed), f"{pass_pct:.0f}% of total{trend_note}"),
        ("Total Fail", fmt_k(total_failed), f"{fail_pct:.0f}% of total"),
        ("Boys / Girls", gender_value, "Gender split" if boys_total + girls_total > 0 else "Not in source data"),
    ]
    cols = st.columns(4)
    for col, accent, (label, value, sub) in zip(cols, [NAVY, PASS_COLOR, FAIL_COLOR, MALE_COLOR], kpi_data):
        col.markdown(kpi_card(label, value, sub, accent), unsafe_allow_html=True)

    reg_priv_value = f"{fmt_k(reg_total)} / {fmt_k(priv_total)}" if reg_total + priv_total > 0 else "Not available"
    reg_priv_sub = "Student type split" if reg_total + priv_total > 0 else "Not in source data"
    st.markdown(kpi_card("Regular / Private", reg_priv_value, reg_priv_sub, NAVY_LIGHT), unsafe_allow_html=True)

    st.write("")
    render_chart_legend()

    gc1, gc2 = st.columns([1, 1.4])
    with gc1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🎯 Overall Pass Rate (Gauge)")
        show_chart(gauge_chart(pass_pct, f"{selected_board_name} · Pass %"))
        st.markdown("</div>", unsafe_allow_html=True)
    with gc2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🧱 Result Breakdown (Passed vs Failed)")
        show_chart(stacked_bar_breakdown_chart(total_appeared, total_passed, total_failed, "Appeared → Passed / Failed"))
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🔻 Result Funnel")
    show_chart(funnel_chart(["Appeared", "Passed"], [total_appeared, total_passed], f"{selected_board_name} — Appeared → Passed"))
    st.markdown("</div>", unsafe_allow_html=True)

    if not group_totals.empty:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🟧 Group Share (Pre-Medical / Pre-Engineering / Humanities / ...)")
        show_chart(treemap_chart(group_totals["Group"].tolist(), group_totals["Appeared"].tolist(), "Appeared Share by Group"))
        st.markdown("</div>", unsafe_allow_html=True)
    elif not districts.empty:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🟧 District Share (Treemap)")
        show_chart(treemap_chart(districts["District"].tolist(), districts["Appeared"].tolist(), "Share by District"))
        st.markdown("</div>", unsafe_allow_html=True)

    has_gender = not gender_df.empty
    has_passfail = total_passed + total_failed > 0
    if has_gender and has_passfail:
        col_gender, col_board = st.columns(2)
        with col_gender:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Gender Distribution")
            show_chart(gender_split_pie(gender_df))
            st.markdown("</div>", unsafe_allow_html=True)
        with col_board:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Board Pass / Fail")
            show_chart(pass_fail_pie(total_passed, total_failed, selected_board_name))
            st.markdown("</div>", unsafe_allow_html=True)
    elif has_gender:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Gender Distribution")
        show_chart(gender_split_pie(gender_df))
        st.markdown("</div>", unsafe_allow_html=True)
    elif has_passfail:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Board Pass / Fail")
        show_chart(pass_fail_pie(total_passed, total_failed, selected_board_name))
        st.markdown("</div>", unsafe_allow_html=True)

    col_gender_bar, col_type_bar = st.columns(2)
    with col_gender_bar:
        if has_gender:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Pass / Fail by Gender")
            gender_bar = gender_df.copy()
            gender_bar["Label"] = gender_bar["Gender"].map(gender_label)
            show_chart(pass_fail_hbar(gender_bar, "Label"))
            st.markdown("</div>", unsafe_allow_html=True)
    with col_type_bar:
        if not type_df.empty and "Candidate Type" in type_df.columns:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Pass / Fail by Student Type")
            show_chart(pass_fail_hbar(type_df, "Candidate Type"))
            st.markdown("</div>", unsafe_allow_html=True)

    if not trend_df.empty and len(trend_df) >= 1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📈 Year-over-Year Comparison")
        if len(trend_df) >= 2:
            tc1, tc2 = st.columns(2)
            with tc1:
                show_chart(trend_line_chart(trend_df, "Pass % Trend"))
            with tc2:
                show_chart(year_compare_chart(trend_df))
        else:
            st.dataframe(trend_df, use_container_width=True, hide_index=True)
            st.caption("Only one year of data is published for this board in the workbook.")
        st.markdown("</div>", unsafe_allow_html=True)

    if not group_gender_df.empty:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📊 Pass % by Group and Gender")
        show_chart(group_pass_chart(group_gender_df))
        st.dataframe(group_totals, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    elif not group_totals.empty:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📊 Pass % by Group")
        gfig_df = group_totals.sort_values("Pass %")
        show_chart(pass_fail_hbar(gfig_df.rename(columns={"Group": "Group"}), "Group", "Group Pass / Fail"))
        st.dataframe(group_totals, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if not subjects.empty:
        weak = subjects[subjects["Pass %"] < 70].sort_values("Pass %")
        if not weak.empty:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("⚠️ Subjects Below 70% Pass Rate")
            st.dataframe(weak[["Subject", "Appeared", "Passed", "Pass %"]], use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

    if not districts.empty:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🏙️ District-wise Pass %")
        show_chart(district_pass_hbar(districts, top_n=1000))
        st.dataframe(districts, use_container_width=True, hide_index=True)
        csv_download_button(districts, "⬇️ Download districts CSV", f"{selected_board_name}_districts.csv")
        st.markdown("</div>", unsafe_allow_html=True)

    if not subjects.empty:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📚 Subject-wise Pass %")
        show_chart(subject_pass_hbar(subjects, top_n=1000))
        st.dataframe(subjects, use_container_width=True, hide_index=True)
        csv_download_button(subjects, "⬇️ Download subjects CSV", f"{selected_board_name}_subjects.csv")
        st.markdown("</div>", unsafe_allow_html=True)
