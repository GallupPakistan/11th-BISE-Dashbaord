"""views_compare.py -- Board Comparison page rendering logic."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import *  # noqa: F401,F403 -- tokens, chart factories, helpers, chart_card
from components.kpi_card import render_kpi_row, format_compact

# Rotating KPI accents (9th-class card accent classes)
_ACCENTS = ["blue", "green", "red", "gold"]


def render_compare_page(data, selected_names, year):
    if len(selected_names) < 2:
        st.info("Select **at least 2 boards** in the Boards filter above to compare them side by side.")
        return

    board_df = filter_df(data["overview"], board=selected_names)
    if board_df.empty:
        st.warning("No data available for the selected boards.")
        return

    scope_df = board_df if year is None else board_df[board_df["Year"] == year]
    if scope_df.empty:
        scope_df = board_df
    agg = scope_df.groupby("Board", as_index=False).agg(
        Appeared=("Total Appeared", "sum"), Passed=("Total Passed", "sum")
    )
    agg["Failed"] = (agg["Appeared"] - agg["Passed"]).clip(lower=0)
    agg["Pass %"] = (100 * agg["Passed"] / agg["Appeared"].replace(0, float("nan"))).round(1)
    present = [n for n in selected_names if n in agg["Board"].tolist()]
    missing = [n for n in selected_names if n not in present]
    agg["Board"] = pd.Categorical(agg["Board"], categories=present, ordered=True)
    agg = agg.sort_values("Board").reset_index(drop=True)
    agg["Board"] = agg["Board"].astype(str)

    year_label = "All Years" if year is None else str(year)
    if missing:
        st.caption(f"⚠️ No {year_label} data published for: {', '.join(missing)}.")

    # ── KPI cards — one per board (rows of 4), 9th-class style ──────────────
    kpis = []
    for i, (_, row) in enumerate(agg.iterrows()):
        pass_val = f"{row['Pass %']:.1f}%" if pd.notna(row["Pass %"]) else "—"
        kpis.append(dict(
            icon="school", value=pass_val, label=str(row["Board"]).upper(),
            delta=f"{format_compact(int(row['Appeared']))} appeared", delta_positive=True,
            accent=_ACCENTS[i % len(_ACCENTS)],
        ))
    for i in range(0, len(kpis), 4):
        render_kpi_row(kpis[i:i + 4])

    # ── Pass % trend comparison ──────────────────────────────────────────────
    with chart_card("Pass % Trend Comparison", f"{year_label}, one line per board"):
        trend_fig = go.Figure()
        for i, b in enumerate(selected_names):
            bd = board_df[board_df["Board"] == b].sort_values("Year")
            if bd.empty:
                continue
            pass_pct = (100 * bd["Total Passed"] / bd["Total Appeared"].replace(0, float("nan"))).round(1)
            trend_fig.add_trace(go.Scatter(x=bd["Year"], y=pass_pct, mode="lines+markers", name=b,
                                           line=dict(width=3, shape="spline", smoothing=0.8, color=PALETTE[i % len(PALETTE)]),
                                           marker=dict(size=8)))
        trend_fig.update_layout(height=420,
                                xaxis=dict(dtick=1, title="Year", showgrid=True, gridcolor="rgba(0,0,0,0.06)", griddash="dot"),
                                yaxis=dict(title="Pass %", showgrid=True, gridcolor="rgba(0,0,0,0.06)", griddash="dot"),
                                legend=legend_top_right(), margin=chart_margins(legend_pos="top"), hovermode="x unified")
        show_chart(style_fig(trend_fig))

    gc1, gc2 = st.columns(2)
    with gc1:
        with chart_card("Passed vs Failed", f"{year_label}, per board"):
            show_chart(grouped_bar_chart(agg["Board"].tolist(),
                                         {"Passed": agg["Passed"].tolist(), "Failed": agg["Failed"].tolist()},
                                         "Passed vs Failed by Board", colors=[PASS_COLOR, FAIL_COLOR]))
    with gc2:
        with chart_card("Volume vs Performance", "Bubble size = students appeared"):
            show_chart(bubble_scatter_chart(agg["Appeared"].tolist(), agg["Pass %"].tolist(),
                                            agg["Appeared"].tolist(), agg["Board"].tolist(),
                                            "Appeared vs Pass %", x_title="Total Appeared"))

    # ── Gender pass % comparison ─────────────────────────────────────────────
    gender_rows = []
    for b in present:
        g = gender_df_for(data, b, year)
        for _, r in g.iterrows():
            gender_rows.append({"Board": b, "Gender": gender_label(r["Gender"]), "Pass %": r["Pass %"]})
    if gender_rows:
        gdf = pd.DataFrame(gender_rows)
        pivot = gdf.pivot_table(index="Board", columns="Gender", values="Pass %", aggfunc="mean").reindex(present)
        # Boards with no gender data at all stay out of the chart — never a fake 0%.
        pivot = pivot.dropna(how="all")
        gender_colors = [GENDER_COLORS.get(c, NAVY) for c in pivot.columns]
        with chart_card("Gender Pass % Comparison", f"Pass % by gender, {year_label}"):
            show_chart(grouped_bar_chart(pivot.index.tolist(), {col: pivot[col].round(1).tolist() for col in pivot.columns},
                                         "Pass % by Gender — Selected Boards", y_title="Pass %", colors=gender_colors,
                                         show_values=True, value_suffix="%"))

    with chart_card("Comparison Table", f"{year_label}, {len(present)} boards"):
        st.dataframe(agg, width='stretch', hide_index=True)
        csv_download_button(agg, "⬇️ Download comparison CSV", "board_comparison.csv")
