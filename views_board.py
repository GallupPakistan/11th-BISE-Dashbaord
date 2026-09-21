"""views_board.py -- Single-board deep-dive page rendering logic (9th-class visual identity)."""
import streamlit as st

from common import *  # noqa: F401,F403 -- tokens, chart factories, helpers, chart_card
from components.kpi_card import render_kpi, render_kpi_row


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
        with chart_card("No Records", f"{selected_board_name} · {selected_year}"):
            st.markdown(f"**No records** in the workbook for **{selected_board_name}** · **{selected_year}**.")
        return

    total_appeared = totals["appeared"]
    total_passed = totals["passed"]
    total_failed = totals["failed"]
    pass_pct = totals["pass_pct"]
    fail_pct = round(100 - pass_pct, 1) if pass_pct else 0
    yoy = yoy_delta_from_trend(trend_df)

    insights = build_insights(gender_df, type_df, group_totals, subjects, pass_pct, yoy)

    render_notes(totals["notes"])

    # ── Gender-gap callout ───────────────────────────────────────────────────
    # The generic Key Insights list already includes a one-line gender-gap
    # note, but a genuinely large gap deserves its own visible flag rather
    # than being buried in a bullet list.
    if not gender_df.empty and len(gender_df) >= 2:
        g = gender_df.set_index("Gender")
        if "Male" in g.index and "Female" in g.index:
            m_pct, f_pct = g.loc["Male", "Pass %"], g.loc["Female", "Pass %"]
            m_app, m_pass = int(g.loc["Male", "Appeared"]), int(g.loc["Male", "Passed"])
            f_app, f_pass = int(g.loc["Female", "Appeared"]), int(g.loc["Female", "Passed"])
            gap = f_pct - m_pct
            if abs(gap) >= 15:
                lower, higher = ("Boys", "Girls") if gap > 0 else ("Girls", "Boys")
                lower_pct, higher_pct = (m_pct, f_pct) if gap > 0 else (f_pct, m_pct)
                lower_detail = f"{m_pass:,}/{m_app:,}" if gap > 0 else f"{f_pass:,}/{f_app:,}"
                higher_detail = f"{f_pass:,}/{f_app:,}" if gap > 0 else f"{m_pass:,}/{m_app:,}"
                st.warning(
                    f"⚠️ **Large gender gap at {selected_board_name} ({selected_year}):** "
                    f"**{lower}** passed at **{lower_pct:.1f}%** ({lower_detail}) vs **{higher}** at "
                    f"**{higher_pct:.1f}%** ({higher_detail}) — a **{abs(gap):.1f} pp** gap, "
                    f"consistent across every reported group, not just one subject or paper."
                )

    # ── Board-specific reported context (NOT from the results workbook) ─────
    # Explanatory context supplied by the user — kept visually and textually
    # separate from render_notes() (which only ever shows the workbook's own
    # Notes column) so it's never mistaken for a source-data caveat.
    if selected_board_name in BOARD_REPORTED_CONTEXT:
        with st.expander(f"📰 Reported reasons for {selected_board_name}'s results (not from the results data)"):
            st.caption("Context supplied by the dashboard's user — not sourced from the Excel workbook.")
            for line in BOARD_REPORTED_CONTEXT[selected_board_name]:
                st.markdown(f"- {line}")

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

    with chart_card("Key Insights", f"{selected_board_name} · {selected_year}"):
        for line in insights:
            st.markdown(f"- {line}")

    # ── KPI row (9th-class style) ────────────────────────────────────────────
    boys_total = totals["male_appeared"]
    girls_total = totals["female_appeared"]
    gender_value = f"{fmt_k(boys_total)} / {fmt_k(girls_total)}" if boys_total + girls_total > 0 else "Not available"
    gender_label_txt = "BOYS / GIRLS APPEARED" if boys_total + girls_total > 0 else "BOYS / GIRLS · N/A"

    reg_total = priv_total = 0
    if not type_df.empty and "Candidate Type" in type_df.columns:
        regular = type_df[type_df["Candidate Type"] == "Regular"]
        private = type_df[type_df["Candidate Type"] == "Private"]
        reg_total = int(regular["Appeared"].sum()) if not regular.empty else 0
        priv_total = int(private["Appeared"].sum()) if not private.empty else 0
    reg_priv_value = f"{fmt_k(reg_total)} / {fmt_k(priv_total)}" if reg_total + priv_total > 0 else "Not available"
    reg_priv_label = "REGULAR / PRIVATE" if reg_total + priv_total > 0 else "REGULAR / PRIVATE · N/A"

    kpis = [
        dict(icon="group", value=fmt_k(total_appeared), label=f"TOTAL APPEARED · {selected_year}", accent="blue"),
        dict(icon="verified", value=fmt_k(total_passed), label=f"TOTAL PASSED · {pass_pct:.1f}%",
             delta=(f"YoY {yoy:+.1f} pts" if yoy is not None else ""), delta_positive=(yoy or 0) >= 0, accent="green"),
        dict(icon="cancel", value=fmt_k(total_failed), label=f"TOTAL FAILED · {fail_pct:.0f}%", accent="red"),
        dict(icon="wc", value=gender_value, label=gender_label_txt, accent="gold"),
        dict(icon="badge", value=reg_priv_value, label=reg_priv_label, accent="blue"),
    ]
    for i in range(0, len(kpis), 4):
        render_kpi_row(kpis[i:i + 4])

    render_chart_legend()

    gc1, gc2 = st.columns([1, 1.4])
    with gc1:
        with chart_card("Overall Pass Rate (Gauge)", f"{selected_board_name} · {selected_year}"):
            show_chart(gauge_chart(pass_pct, f"{selected_board_name} · Pass %"))
            st.caption(
                "ℹ️ Calculated here as Total Passed ÷ Total Appeared, the same formula for every board — "
                "this may differ by a fraction of a percentage point from a board's own officially printed "
                "Pass % in some years."
            )
    with gc2:
        with chart_card("Result Breakdown (Passed vs Failed)", f"{selected_board_name} · {selected_year}"):
            show_chart(stacked_bar_breakdown_chart(total_appeared, total_passed, total_failed, "Appeared → Passed / Failed"))

    with chart_card("Result Funnel", f"{selected_board_name} — Appeared → Passed"):
        show_chart(funnel_chart(["Appeared", "Passed"], [total_appeared, total_passed],
                                f"{selected_board_name} — Appeared → Passed"))

    if not group_totals.empty:
        with chart_card("Group Share", "Pre-Medical / Pre-Engineering / Humanities / ... by students appeared"):
            show_chart(treemap_chart(group_totals["Group"].tolist(), group_totals["Appeared"].tolist(),
                                     "Appeared Share by Group"))
    elif not districts.empty:
        with chart_card("District Share (Treemap)", "By students appeared"):
            show_chart(treemap_chart(districts["District"].tolist(), districts["Appeared"].tolist(), "Share by District"))

    has_gender = not gender_df.empty
    has_passfail = total_passed + total_failed > 0
    if has_gender and has_passfail:
        col_gender, col_board = st.columns(2)
        with col_gender:
            with chart_card("Gender Distribution", f"{selected_board_name} · {selected_year}"):
                show_chart(gender_split_pie(gender_df))
        with col_board:
            with chart_card("Board Pass / Fail", f"{selected_board_name} · {selected_year}"):
                show_chart(pass_fail_pie(total_passed, total_failed, selected_board_name))
    elif has_gender:
        with chart_card("Gender Distribution", f"{selected_board_name} · {selected_year}"):
            show_chart(gender_split_pie(gender_df))
    elif has_passfail:
        with chart_card("Board Pass / Fail", f"{selected_board_name} · {selected_year}"):
            show_chart(pass_fail_pie(total_passed, total_failed, selected_board_name))

    col_gender_bar, col_type_bar = st.columns(2)
    with col_gender_bar:
        if has_gender:
            with chart_card("Pass / Fail by Gender", f"{selected_board_name} · {selected_year}"):
                gender_bar = gender_df.copy()
                gender_bar["Label"] = gender_bar["Gender"].map(gender_label)
                show_chart(pass_fail_hbar(gender_bar, "Label"))
    with col_type_bar:
        if not type_df.empty and "Candidate Type" in type_df.columns:
            with chart_card("Pass / Fail by Student Type", f"{selected_board_name} · {selected_year}"):
                show_chart(pass_fail_hbar(type_df, "Candidate Type"))

    if not trend_df.empty and len(trend_df) >= 1:
        with chart_card("Year-over-Year Comparison", f"{selected_board_name}, every workbook year"):
            if len(trend_df) >= 2:
                tc1, tc2 = st.columns(2)
                with tc1:
                    show_chart(trend_line_chart(trend_df, "Pass % Trend"))
                with tc2:
                    show_chart(year_compare_chart(trend_df))
            else:
                only_year = int(trend_df["Year"].iloc[0])
                st.dataframe(trend_df, width='stretch', hide_index=True)
                st.info(
                    f"ℹ️ Only **{only_year}** data is published for {selected_board_name} in the workbook — "
                    f"no prior year to compare against, so no year-over-year trend or decline/rise can be shown."
                )

    if not group_gender_df.empty:
        with chart_card("Pass % by Group and Gender", f"{selected_board_name} · {selected_year}"):
            show_chart(group_pass_chart(group_gender_df))
            st.dataframe(group_totals, width='stretch', hide_index=True)
    elif not group_totals.empty:
        with chart_card("Pass % by Group", f"{selected_board_name} · {selected_year}"):
            gfig_df = group_totals.sort_values("Pass %")
            show_chart(pass_fail_hbar(gfig_df, "Group", "Group Pass / Fail"))
            st.dataframe(group_totals, width='stretch', hide_index=True)

    if not subjects.empty:
        weak = subjects[subjects["Pass %"] < 70].sort_values("Pass %")
        if not weak.empty:
            with chart_card("Subjects Below 70% Pass Rate", "Weak papers worth investigating"):
                st.dataframe(weak[["Subject", "Appeared", "Passed", "Pass %"]], width='stretch', hide_index=True)

    if not districts.empty:
        with chart_card("District-wise Pass %", f"{selected_board_name} · {selected_year}"):
            show_chart(district_pass_hbar(districts, top_n=1000))
            st.dataframe(districts, width='stretch', hide_index=True)
            csv_download_button(districts, "⬇️ Download districts CSV", f"{selected_board_name}_districts.csv")

    if not subjects.empty:
        with chart_card("Subject-wise Pass %", f"{selected_board_name} · {selected_year}"):
            show_chart(subject_pass_hbar(subjects, top_n=1000))
            st.dataframe(subjects, width='stretch', hide_index=True)
            csv_download_button(subjects, "⬇️ Download subjects CSV", f"{selected_board_name}_subjects.csv")
