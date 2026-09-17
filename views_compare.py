"""views_compare.py -- Compare Boards page rendering logic."""
import pandas as pd
import streamlit as st
from common import *


def render_compare_page(data, selected_names, year):
    if len(selected_names) < 2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("**Select at least 2 boards** from the sidebar to compare them side by side.")
        st.markdown("</div>", unsafe_allow_html=True)
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
    st.markdown(
        f"""<div class="board-header">
        <div class="board-header-title">🆚 Comparing {len(selected_names)} Boards</div>
        <div class="board-header-sub">{year_label} · {' · '.join(selected_names)}</div>
        </div>""",
        unsafe_allow_html=True,
    )
    if missing:
        st.caption(f"⚠️ No {year_label} data published for: {', '.join(missing)}.")

    cards_html = ['<div class="kpi-grid">']
    for i, (_, row) in enumerate(agg.iterrows()):
        accent = PALETTE[i % len(PALETTE)]
        pass_val = f"{row['Pass %']:.1f}%" if pd.notna(row["Pass %"]) else "—"
        cards_html.append(kpi_card(row["Board"], pass_val, f"{fmt_k(int(row['Appeared']))} appeared", accent))
    cards_html.append("</div>")
    st.markdown("".join(cards_html), unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("📈 Pass % Trend Comparison")
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
    st.markdown("</div>", unsafe_allow_html=True)

    gc1, gc2 = st.columns(2)
    with gc1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🟦 Passed vs Failed")
        show_chart(grouped_bar_chart(agg["Board"].tolist(),
                                      {"Passed": agg["Passed"].tolist(), "Failed": agg["Failed"].tolist()},
                                      "Passed vs Failed by Board", colors=[PASS_COLOR, FAIL_COLOR]))
        st.markdown("</div>", unsafe_allow_html=True)
    with gc2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🔵 Volume vs Performance")
        show_chart(bubble_scatter_chart(agg["Appeared"].tolist(), agg["Pass %"].tolist(),
                                        agg["Appeared"].tolist(), agg["Board"].tolist(),
                                        "Appeared vs Pass % (bubble size = Appeared)", x_title="Total Appeared"))
        st.markdown("</div>", unsafe_allow_html=True)

    gender_rows = []
    for b in present:
        g = gender_df_for(data, b, year)
        for _, r in g.iterrows():
            gender_rows.append({"Board": b, "Gender": gender_label(r["Gender"]), "Pass %": r["Pass %"]})
    if gender_rows:
        gdf = pd.DataFrame(gender_rows)
        pivot = gdf.pivot_table(index="Board", columns="Gender", values="Pass %", aggfunc="mean").reindex(present)
        pivot = pivot.dropna(how="all")  # drop boards with no gender data at all (e.g. not reported) instead of showing a nan% bar
        gender_colors = [GENDER_COLORS.get(c, NAVY) for c in pivot.columns]
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("👥 Gender Pass % Comparison")
        show_chart(grouped_bar_chart(pivot.index.tolist(), {col: pivot[col].round(1).tolist() for col in pivot.columns},
                                      "Pass % by Gender — Selected Boards", y_title="Pass %", colors=gender_colors,
                                      show_values=True, value_suffix="%"))
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("📋 Comparison Table")
    st.dataframe(agg, use_container_width=True, hide_index=True)
    csv_download_button(agg, "⬇️ Download comparison CSV", "board_comparison.csv")
    st.markdown("</div>", unsafe_allow_html=True)