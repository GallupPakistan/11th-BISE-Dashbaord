"""
views_overview.py -- Overview page rendering logic (used by app.py).

Data logic is unchanged: everything aggregates the combined workbook's
"Combined Overview" sheet plus per-board gender/group/subject tables —
nothing is estimated, and gaps in the workbook stay gaps. The presentation
layer is the 9th-class visual identity: white KPI cards with YoY delta
pills + spark bars, top gainer/decliner cards, and chart_card-wrapped
sections on the light-grey page.
"""
import re

import pandas as pd
import streamlit as st

from common import *  # noqa: F401,F403 -- tokens, chart factories, helpers, chart_card
from components.kpi_card import render_kpi, render_kpi_row, format_compact
import plotly.graph_objects as go

ALL_PROVINCES_LABEL = "All Provinces"


def render_overview(data, year, province):
    board_scope = [
        b for b in ALL_BOARD_NAMES
        if province == ALL_PROVINCES_LABEL or BOARD_PROVINCE.get(b, "Other") == province
    ]

    overview = filter_df(data["overview"], board=board_scope)
    rankings = board_rankings_df(data, year)
    rankings = rankings[rankings["Board"].isin(board_scope)].copy()

    df = overview if year is None else overview[overview["Year"] == year]
    if df.empty:
        st.info("No data available for the selected year.")
        return
    total_app = int(df["Total Appeared"].sum(skipna=True) or 0)
    total_pass = int(df["Total Passed"].sum(skipna=True) or 0)
    total_fail = max(total_app - total_pass, 0)
    pass_pct = round(100 * total_pass / max(total_app, 1), 2)

    year_label = "All Years (2024–2025 combined)" if year is None else str(year)

    # ── KPI row (9th-class style: icon + value + uppercase label + YoY
    #    delta pill + two-bar spark comparing this year vs the other one) ────
    other = 2024 if year == 2025 else None
    if other is not None:
        df_o = overview[overview["Year"] == other]
        o_app = int(df_o["Total Appeared"].sum(skipna=True) or 0)
        o_pass = int(df_o["Total Passed"].sum(skipna=True) or 0)
        o_fail = max(o_app - o_pass, 0)
        o_pct = round(100 * o_pass / max(o_app, 1), 2)
        app_d = total_app - o_app
        pass_d = total_pass - o_pass
        fail_d = total_fail - o_fail
        pct_d = round(pass_pct - o_pct, 2)
    else:
        o_app = o_pass = o_fail = o_pct = 0
        app_d = pass_d = fail_d = pct_d = None

    kpis = [
        dict(
            icon="group", value=format_compact(total_app), label=f"TOTAL APPEARED ({year})",
            delta="" if app_d is None else f"{format_compact(app_d)} vs {other}",
            delta_positive=(app_d or 0) >= 0, accent="blue",
            spark=None if other is None else [total_app, o_app],
        ),
        dict(
            icon="verified", value=format_compact(total_pass), label=f"TOTAL PASSED ({year})",
            delta="" if pass_d is None else f"{format_compact(pass_d)} vs {other}",
            delta_positive=(pass_d or 0) >= 0, accent="green",
            spark=None if other is None else [total_pass, o_pass],
        ),
        dict(
            icon="cancel", value=format_compact(total_fail), label=f"TOTAL FAILED ({year})",
            delta="" if fail_d is None else f"{format_compact(fail_d)} vs {other}",
            delta_positive=(fail_d or 0) < 0, accent="red",  # more failures = red pill
            spark=None if other is None else [total_fail, o_fail],
        ),
        dict(
            icon="percent", value=f"{pass_pct:.1f}%", label=f"PASS RATE ({year})",
            delta="" if pct_d is None else f"{pct_d:+.1f} pts vs {other}",
            delta_positive=(pct_d or 0) >= 0, accent="gold",
            spark=None if other is None else [pass_pct, o_pct],
        ),
    ]
    render_kpi_row(kpis)

    # ── Top gainer / top decliner — biggest pass % swings vs the other year ─
    if other is not None:
        movers = []
        for name in board_scope:
            t = yearly_trend_df_for(data, name).set_index("Year")
            if year in t.index and other in t.index:
                cur, prev = t.loc[year, "Pass %"], t.loc[other, "Pass %"]
                if pd.notna(cur) and pd.notna(prev):
                    movers.append((name, float(cur) - float(prev)))
        if movers:
            movers.sort(key=lambda r: r[1])
            g_name, g_chg = movers[-1]
            d_name, d_chg = movers[0]
            mc1, mc2 = st.columns(2)
            with mc1:
                render_kpi(
                    icon="trending_up", value=g_name, label="TOP GAINER · PASS % CHANGE",
                    delta=f"{g_chg:+.1f} pts vs {other}", delta_positive=True, accent="green",
                )
            with mc2:
                render_kpi(
                    icon="trending_down", value=d_name, label="TOP DECLINER · PASS % CHANGE",
                    delta=f"{d_chg:+.1f} pts vs {other}", delta_positive=False, accent="red",
                )

    st.caption(
        "ℹ️ Pass % here is Total Passed ÷ Total Appeared, computed the same way for every board — it can "
        "differ by a fraction of a point from a board's own officially printed figure in a few years."
    )

    # ── Result Flow — aggregated across every board in scope ────────────────
    gender_rows, type_rows = [], []
    for name in board_scope:
        g = gender_df_for(data, name, year)
        if not g.empty:
            gender_rows.append(g)
        t = type_df_for(data, name, year)
        if not t.empty:
            type_rows.append(t)

    def _combine(rows, key_col):
        if not rows:
            return pd.DataFrame(columns=[key_col, "Appeared", "Passed", "Failed", "Pass %"])
        cat = pd.concat(rows, ignore_index=True)
        out = cat.groupby(key_col, as_index=False)[["Appeared", "Passed"]].sum()
        out["Failed"] = (out["Appeared"] - out["Passed"]).clip(lower=0)
        out["Pass %"] = (100 * out["Passed"] / out["Appeared"].replace(0, float("nan"))).round(2)
        return out

    overall_gender_df = _combine(gender_rows, "Gender")
    overall_type_df = _combine(type_rows, "Candidate Type")
    overall_totals = {"appeared": total_app, "passed": total_pass, "failed": total_fail, "pass_pct": pass_pct}
    render_gender_type_flow(
        f"Overall — {province if province != ALL_PROVINCES_LABEL else 'All Boards'}",
        year_label, overall_totals, overall_gender_df, overall_type_df,
    )

    # ── Key Insights ─────────────────────────────────────────────────────────
    grp_rows = []
    for name in board_scope:
        gt = group_totals_df_for(data, name, year)
        if not gt.empty:
            grp_rows.append(gt)
    combined_groups = pd.DataFrame()
    if grp_rows:
        cat_g = pd.concat(grp_rows, ignore_index=True)
        combined_groups = cat_g.groupby("Group", as_index=False)[["Appeared", "Passed"]].sum()
        combined_groups["Pass %"] = (100 * combined_groups["Passed"] / combined_groups["Appeared"].replace(0, float("nan"))).round(2)
        combined_groups = combined_groups.sort_values("Pass %", ascending=False)

    with chart_card("Key Insights", f"{province if province != ALL_PROVINCES_LABEL else 'All Boards'} · {year_label}"):
        for line in build_insights(overall_gender_df, overall_type_df, combined_groups, pd.DataFrame(), pass_pct, None):
            st.markdown(f"- {line}")

    # ── Board Ranking by Pass % & Share of Total Appeared ────────────────────
    rank_sorted = rankings.sort_values("Appeared", ascending=False)
    rc1, rc2 = st.columns(2)
    with rc1:
        with chart_card("Board Ranking by Pass %", f"{year_label}, boards in view"):
            show_chart(board_rank_hbar(rankings["Board"].tolist(), rankings["Pass %"].tolist(),
                                       title="Board Ranking by Pass %", height=max(320, 34 * len(rankings))))
    with rc2:
        with chart_card("Share of Total Appeared", f"{year_label}, by board"):
            show_chart(donut_pie(rank_sorted["Board"].tolist(), rank_sorted["Appeared"].tolist(),
                                 [PALETTE[i % len(PALETTE)] for i in range(len(rank_sorted))],
                                 title="Students by Board", height=380))

    # ── Pass % Trend — every board, one line each, plus flagged declines ─────
    with chart_card("Pass % Trend — All Boards", "One line per board across every workbook year"):
        show_trend_table = st.toggle("Show table", key="overview_board_trend_table")

        board_trend_rows = []
        board_notes = {}  # board -> {year: note text}, used for methodology callouts
        for name in sorted(board_scope):
            t = yearly_trend_df_for(data, name)
            if t.empty:
                continue
            t = t.copy()
            t["Board"] = name
            board_trend_rows.append(t[["Year", "Board", "Pass %", "Appeared", "Failed"]])
            notes_df = filter_df(data["overview"], board=name)[["Year", "Notes"]].dropna(subset=["Notes"])
            board_notes[name] = {int(r["Year"]): str(r["Notes"]).strip() for _, r in notes_df.iterrows() if str(r["Notes"]).strip()}

        if board_trend_rows:
            board_trend = pd.concat(board_trend_rows, ignore_index=True)
            years_sorted = sorted(board_trend["Year"].unique())

            single_year_boards = []
            fig = go.Figure()
            for i, name in enumerate(sorted(board_trend["Board"].unique())):
                sub = board_trend[board_trend["Board"] == name].sort_values("Year")
                color = PALETTE[i % len(PALETTE)]
                if len(sub) == 1:
                    # Only one year of data — a line has nothing to connect to, and a
                    # plain small marker gets buried under other boards' lines, so
                    # render it as a larger, distinct diamond instead.
                    only_year = int(sub["Year"].iloc[0])
                    single_year_boards.append((name, only_year))
                    fig.add_trace(go.Scatter(
                        x=sub["Year"].astype(int).astype(str), y=sub["Pass %"], mode="markers", name=f"{name} ({only_year} only)",
                        marker=dict(color=color, size=14, symbol="diamond", line=dict(width=1.5, color="white")),
                    ))
                else:
                    fig.add_trace(go.Scatter(
                        x=sub["Year"].astype(int).astype(str), y=sub["Pass %"], mode="lines+markers", name=name,
                        line=dict(color=color, width=2.5), marker=dict(size=6),
                    ))
            fig.update_layout(
                xaxis=dict(type="category", title="Year", showgrid=True, gridcolor="rgba(0,0,0,0.06)", griddash="dot"),
                yaxis=dict(title="Pass %", showgrid=True, gridcolor="rgba(0,0,0,0.06)", griddash="dot"),
                legend=legend_top_right(), margin=chart_margins(legend_pos="top"), height=460, hovermode="closest",
            )
            show_chart(style_fig(fig))

            if single_year_boards:
                single_desc = ", ".join(f"**{n}** ({y} only)" for n, y in single_year_boards)
                st.caption(f"◆ Diamond markers = boards with only one year of data on file, shown as a point rather than a line: {single_desc}.")

            # ── Methodology callout: any board/year whose source gazette notes
            #     mention a promotion/promoted basis (rather than a true final
            #     pass/fail result) ────────────────────────────────────────────
            promo_notes = [(name, yr, note) for name, years in board_notes.items() for yr, note in years.items()
                           if re.search(r"promot", note, re.IGNORECASE)]
            if promo_notes:
                st.warning(
                    "⚠️ **" + ", ".join(f"{name} {yr}" for name, yr, _ in promo_notes) +
                    "** show unusually high pass % because their source gazettes report a **'Promoted' / promotion-basis "
                    "result** (a newer marking policy) rather than a traditional final pass/fail outcome — so those points "
                    "aren't directly comparable to the rest of the boards on this chart."
                )
                with st.expander("📋 Full data-caveat notes for the flagged board-years"):
                    for name, yr, note in promo_notes:
                        st.markdown(f"- **{name} {yr}:** {note}")
            if show_trend_table:
                trend_wide = board_trend.pivot_table(index="Board", columns="Year", values="Pass %")
                trend_wide.columns = [f"{int(c)} Pass %" for c in trend_wide.columns]
                trend_wide = trend_wide.reset_index()
                st.dataframe(trend_wide, width='stretch', hide_index=True)
                csv_download_button(trend_wide, "⬇️ Download board trend CSV", "board_pass_pct_trend.csv")

            # ── Flagged declines: boards whose pass % dropped 10+ pp between the
            #     first and last year they have data for ─────────────────────────
            if len(years_sorted) >= 2:
                DECLINE_THRESHOLD = 10.0
                first_year, last_year = years_sorted[0], years_sorted[-1]
                flagged_rows = []
                for name in sorted(board_trend["Board"].unique()):
                    sub = board_trend[board_trend["Board"] == name].set_index("Year")
                    if first_year not in sub.index or last_year not in sub.index or first_year == last_year:
                        continue
                    first_pct = sub.loc[first_year, "Pass %"]
                    last_pct = sub.loc[last_year, "Pass %"]
                    if pd.isna(first_pct) or pd.isna(last_pct):
                        continue
                    change = round(last_pct - first_pct, 2)
                    if change <= -DECLINE_THRESHOLD:
                        flagged_rows.append({
                            "Board": name,
                            f"{int(first_year)} Pass %": first_pct,
                            f"{int(last_year)} Pass %": last_pct,
                            "Change (pp)": change,
                            f"{int(last_year)} Appeared": int(sub.loc[last_year, "Appeared"]),
                            f"{int(last_year)} Failed": int(sub.loc[last_year, "Failed"]),
                        })

                excluded_single_year = [n for n, y in single_year_boards]
                if flagged_rows:
                    flagged_df = pd.DataFrame(flagged_rows).sort_values("Change (pp)")
                    st.markdown("&nbsp;", unsafe_allow_html=True)
                    st.warning("⚠️ **Significant Pass % Declines — Flagged for Review**")
                    st.error(
                        f"{len(flagged_df)} board(s) dropped {DECLINE_THRESHOLD:.0f}+ percentage points between "
                        f"{int(first_year)} and {int(last_year)} — worth investigating before drawing conclusions."
                    )
                    st.dataframe(flagged_df, width='stretch', hide_index=True)
                    for _, row in flagged_df.iterrows():
                        with st.expander(f"🔍 {row['Board']} — {row['Change (pp)']:.1f} pp — year-by-year detail"):
                            detail = board_trend[board_trend["Board"] == row["Board"]].sort_values("Year")
                            st.dataframe(detail[["Year", "Pass %", "Appeared", "Failed"]], width='stretch', hide_index=True)
                    csv_download_button(flagged_df, "⬇️ Download flagged declines CSV", "flagged_pass_pct_declines.csv")
                else:
                    st.caption(f"✅ No board dropped {DECLINE_THRESHOLD:.0f}+ percentage points between {int(first_year)} and {int(last_year)}.")

                # ── Lowest-performing board this year, even if it can't be
                #     scored as a "decline" (e.g. only one year of data) ────────
                latest_rows = board_trend[board_trend["Year"] == last_year].sort_values("Pass %")
                if not latest_rows.empty:
                    lowest = latest_rows.iloc[0]
                    lowest_name, lowest_pct = lowest["Board"], lowest["Pass %"]
                    is_single_year = lowest_name in excluded_single_year
                    msg = (
                        f"🔻 **{lowest_name}** is the **lowest-performing board** in {int(last_year)} at **{lowest_pct:.1f}%** pass rate"
                        + (" — but with only one year of data on file, it can't be scored as a decline/rise above." if is_single_year else ".")
                    )
                    st.error(msg) if not is_single_year else st.info(msg)
                    if lowest_name in BOARD_REPORTED_CONTEXT:
                        st.markdown(f"**Reported reasons for {lowest_name}'s low result:**")
                        for line in BOARD_REPORTED_CONTEXT[lowest_name]:
                            st.markdown(f"- {line}")

                if excluded_single_year:
                    st.caption(
                        f"ℹ️ Not evaluated here — no {int(first_year)} figure to compare against, so no decline/rise can be "
                        f"computed (not the same as \"no change\"): {', '.join(excluded_single_year)}."
                    )
        else:
            st.info("No multi-year trend data available for the current filter.")

    # ── Province pass % trend (across every year, regardless of the year
    #     pills — a trend needs more than one year to mean anything) ──────────
    with chart_card("Pass % Trend by Province", "Boards rolled up by their province, every workbook year"):
        trend_rows = []
        for name in board_scope:
            prov_name = BOARD_PROVINCE.get(name, "Other")
            t = yearly_trend_df_for(data, name)
            if t.empty:
                continue
            t = t.copy()
            t["Province"] = prov_name
            trend_rows.append(t[["Year", "Appeared", "Passed", "Province"]])

        if trend_rows:
            trend_all = pd.concat(trend_rows, ignore_index=True)
            trend_prov = trend_all.groupby(["Year", "Province"], as_index=False)[["Appeared", "Passed"]].sum()
            trend_prov["Pass %"] = (100 * trend_prov["Passed"] / trend_prov["Appeared"].replace(0, float("nan"))).round(2)

            fig = go.Figure()
            for p in trend_prov["Province"].unique():
                sub = trend_prov[trend_prov["Province"] == p].sort_values("Year")
                fig.add_trace(go.Scatter(
                    x=sub["Year"].astype(int).astype(str), y=sub["Pass %"], mode="lines+markers", name=p,
                    line=dict(color=PROVINCE_COLORS.get(p, NAVY), width=3), marker=dict(size=8),
                ))
            fig.update_layout(
                xaxis=dict(type="category", title="Year", showgrid=True, gridcolor="rgba(0,0,0,0.06)", griddash="dot"),
                yaxis=dict(title="Pass %", showgrid=True, gridcolor="rgba(0,0,0,0.06)", griddash="dot"),
                legend=legend_top_right(), margin=chart_margins(legend_pos="top"), height=420, hovermode="x unified",
            )
            show_chart(style_fig(fig))

            prov_wide = trend_prov.pivot_table(index="Province", columns="Year", values="Pass %")
            prov_wide.columns = [f"{int(c)} Pass %" for c in prov_wide.columns]
            prov_wide = prov_wide.reset_index()
            st.dataframe(prov_wide, width='stretch', hide_index=True)
        else:
            st.info("No multi-year trend data available for the current filter.")
        st.caption(
            "KPK boards: Peshawar, Swat, Bannu, Abbottabad, Mardan, Kohat. Punjab boards: Sargodha, D.G. Khan, "
            "Rawalpindi, Faisalabad, Lahore, Bahawalpur, Gujranwala, Sahiwal. Federal: FBISE (Islamabad)."
        )

    with chart_card("Passed vs Failed by Board", f"{year_label}, grouped bar"):
        show_chart(grouped_bar_chart(rank_sorted["Board"].tolist(),
                                     {"Passed": rank_sorted["Passed"].tolist(), "Failed": rank_sorted["Failed"].tolist()},
                                     "Passed vs Failed — All Boards"))

    bc1, bc2 = st.columns(2)
    with bc1:
        with chart_card("Board Size vs Performance", "Bubble size = students appeared"):
            show_chart(bubble_scatter_chart(rankings["Appeared"].tolist(), rankings["Pass %"].tolist(),
                                            rankings["Appeared"].tolist(), rankings["Board"].tolist(),
                                            "Appeared vs Pass %", x_title="Total Appeared"))
    with bc2:
        with chart_card("Board Share of Appeared", "Treemap, by students appeared"):
            show_chart(treemap_chart(rankings["Board"].tolist(), rankings["Appeared"].tolist(), "Appeared Share by Board"))

    with chart_card("Overall Result Funnel", f"Appeared → Passed · {year_label}"):
        show_chart(funnel_chart(["Appeared", "Passed"], [total_app, total_pass], "Appeared → Passed (All Boards)"))

    with chart_card("Board × Year Pass % (Heatmap)", "Overall pass % per board per year"):
        heat_pivot = overview.pivot_table(index="Board", columns="Year", values="Overall Pass %", aggfunc="mean")
        heat_pivot = heat_pivot.reindex(rankings.sort_values("Appeared", ascending=False)["Board"].tolist())
        if not heat_pivot.empty:
            show_chart(heatmap_chart(heat_pivot.values, [str(c) for c in heat_pivot.columns],
                                     heat_pivot.index.tolist(), "Pass % Heatmap — Board × Year"))

    with chart_card("Total Students Appeared", "Each board · each year"):
        appeared_tbl = overview.pivot_table(index="Board", columns="Year", values="Total Appeared", aggfunc="sum")
        appeared_tbl = appeared_tbl.reset_index()
        if not appeared_tbl.empty:
            st.dataframe(appeared_tbl, width='stretch', hide_index=True)
            csv_download_button(appeared_tbl, "⬇️ Download appeared CSV", "board_appeared_by_year.csv")

    with chart_card("All Boards Summary", f"{year_label}, downloadable"):
        st.dataframe(rankings, width='stretch', hide_index=True)
        csv_download_button(rankings, "⬇️ Download rankings CSV", "all_boards_rankings.csv")

    # ── Gender disaggregation ────────────────────────────────────────────────
    with chart_card("Gender Distribution — All Boards", f"Boys vs Girls · {year_label}"):
        if not overall_gender_df.empty:
            gc1, gc2 = st.columns([1, 1.4])
            with gc1:
                show_chart(donut_pie(overall_gender_df["Gender"].map(gender_label).tolist(), overall_gender_df["Appeared"].tolist(),
                                     [GENDER_COLORS.get(g, NAVY) for g in overall_gender_df["Gender"]],
                                     f"Appeared by Gender — {year_label}", height=360))
            with gc2:
                fig = go.Figure(go.Bar(x=overall_gender_df["Gender"].map(gender_label), y=overall_gender_df["Pass %"],
                                       marker_color=[GENDER_COLORS.get(g, NAVY) for g in overall_gender_df["Gender"]],
                                       text=overall_gender_df["Pass %"], texttemplate="%{text:.1f}%", textposition="outside"))
                fig.update_layout(height=360, showlegend=False, yaxis_range=[0, 105], yaxis_title="Pass %",
                                  margin=chart_margins(), plot_bgcolor="rgba(0,0,0,0)")
                show_chart(style_fig(fig))
            with st.expander("📋 Gender breakdown by board"):
                bdf_rows = []
                for name in board_scope:
                    g = gender_df_for(data, name, year)
                    for _, r in g.iterrows():
                        bdf_rows.append({"Board": name, "Gender": gender_label(r["Gender"]), "Appeared": r["Appeared"],
                                         "Passed": r["Passed"], "Pass %": r["Pass %"]})
                bdf = pd.DataFrame(bdf_rows).sort_values(["Board", "Gender"])
                st.dataframe(bdf, width='stretch', hide_index=True)
                csv_download_button(bdf, "⬇️ Download gender-by-board CSV", "gender_by_board.csv")
        else:
            st.info("No gender-wise data available for the current filter.")

    # ── Group-wise (Pre-Medical / Pre-Engineering / Humanities / ...) ────────
    with chart_card("Group-wise Pass % — All Boards", f"{year_label}, boards combined"):
        if not combined_groups.empty:
            fig = go.Figure(go.Bar(x=combined_groups["Pass %"], y=combined_groups["Group"], orientation="h",
                                   marker_color=ACCENT, text=combined_groups["Pass %"],
                                   texttemplate="%{text:.1f}%", textposition="outside"))
            fig.update_layout(title=chart_title(f"Pass % by Group ({year_label}, boards combined)"),
                              height=max(360, 42 * len(combined_groups)), xaxis_range=[0, 105],
                              showlegend=False, margin=chart_margins(extra_right=40))
            show_chart(style_fig(fig))
            with st.expander("📋 Full group-wise table"):
                st.dataframe(combined_groups, width='stretch', hide_index=True)
                csv_download_button(combined_groups, "⬇️ Download group-wise CSV", "group_wise_all_boards.csv")
        else:
            st.info(f"No board publishes group-wise data for {year_label} under the current filter.")

    # ── Subject-wise ─────────────────────────────────────────────────────────
    with chart_card("Subject-wise Pass % — All Boards", f"{year_label}, all reporting boards combined"):
        subj_rows, boards_with_subjects, boards_without_subjects = [], [], []
        for name in board_scope:
            sdf = subject_df_for(data, name, year)
            if sdf.empty:
                boards_without_subjects.append(name)
                continue
            boards_with_subjects.append(name)
            sdf = sdf.copy()
            sdf["Board"] = name
            subj_rows.append(sdf)
        if subj_rows:
            all_subj = pd.concat(subj_rows, ignore_index=True)
            agg = all_subj.groupby("Subject", as_index=False)[["Appeared", "Passed"]].sum()
            agg["Pass %"] = (100 * agg["Passed"] / agg["Appeared"].replace(0, float("nan"))).round(2)
            top = agg.sort_values("Appeared", ascending=False).head(15).sort_values("Pass %")
            fig = go.Figure(go.Bar(x=top["Pass %"], y=top["Subject"], orientation="h", marker_color=ACCENT,
                                   text=top["Pass %"], texttemplate="%{text:.1f}%", textposition="outside"))
            fig.update_layout(title=chart_title(f"Top-appeared Subjects — Pass % ({year_label}, all reporting boards combined)"),
                              height=max(400, 32 * len(top)), xaxis_range=[0, 105], showlegend=False, margin=chart_margins())
            show_chart(style_fig(fig))
            st.caption(
                f"✅ Subject-wise data available for **{len(boards_with_subjects)} of {len(boards_with_subjects) + len(boards_without_subjects)}** boards"
                f" for {year_label}: {', '.join(boards_with_subjects)}."
                + (f"  ⚠️ Not published for: {', '.join(boards_without_subjects)}." if boards_without_subjects else "")
            )
            with st.expander("📋 Full subject-wise table (all reporting boards)"):
                st.dataframe(agg.sort_values("Pass %"), width='stretch', hide_index=True)
                csv_download_button(agg, "⬇️ Download subject-wise CSV", "subject_wise_all_boards.csv")
        else:
            st.info(f"No board publishes subject-wise data for {year_label} under the current filter.")
