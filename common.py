"""
common.py
Shared design tokens, chart factories, and small analytics helpers
used by every page of the BISE 11th Class (HSSC Part-I) Results Dashboard.

Visual language is an exact replica of the 9th-class (SSC) dashboard —
navy top-bar & sidebar (#0B1E4D), Cinzel/Inter typography, white KPI/chart
cards on a light-grey page (#E9EAEE), and one stable BOARD_COLOR_SEQUENCE
for charts. The theme lives in styles/theme.py + styles/css.py; reusable
visual components (topbar, sidebar, filter pills, KPI cards, chart cards)
live in components/. Every chart-producing function here takes plain
DataFrames/values, so nothing is tied to how any workbook was parsed.
"""
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data_loader
from data_loader import (
    ALL_BOARD_NAMES,
    BOARD_PROVINCE,
    PROVINCE_COLORS,
    load_workbook,
    get_available_years,
    filter_df,
    board_totals,
    gender_df_for,
    type_df_for,
    group_gender_df_for,
    group_totals_df_for,
    subject_df_for,
    district_df_for,
    yearly_trend_df_for,
    board_rankings_df,
    boards_with_district_data,
    boards_with_subject_data,
    boards_with_group_data,
)

# ── Design tokens (single source of truth: styles/theme.py) ───────────────────
# The 11th-class dashboard ships the EXACT visual identity of the 9th-class
# dashboard: navy top-bar/sidebar (#0B1E4D), bright blue accent (#3B82F6),
# gold secondary accent (#C9A84C), light-grey page (#E9EAEE), white cards,
# Cinzel headings + Inter body, and one stable 15-color BOARD_COLOR_SEQUENCE
# shared by every chart. Names below are re-exported for the rest of the app
# (a few legacy aliases keep older call-sites working).
from styles.theme import COLORS, FONTS, BOARD_COLOR_SEQUENCE  # noqa: E402,F401
from charts._base import base_layout as _base_plotly_layout  # noqa: E402
from components.chart_card import chart_card  # noqa: E402,F401 (re-exported)
from styles.css import inject_css  # noqa: E402,F401 (re-exported)

BG_PAGE = COLORS["bg_page"]
CARD_BG = COLORS["card_bg_light"]
CARD_BORDER = COLORS["card_border_light"]
CARD_SHADOW = COLORS["card_shadow_light"]
TEXT_ON_LIGHT = COLORS["text_on_light"]
TEXT_MUTED = COLORS["text_on_light_muted"]
PRIMARY = COLORS["primary"]
PRIMARY_LIGHT = COLORS["primary_light"]
ACCENT = COLORS["accent"]
ACCENT_LIGHT = COLORS["accent_light"]
GOLD = COLORS["gold"]
POSITIVE = COLORS["positive"]
NEGATIVE = COLORS["negative"]
NEUTRAL = COLORS["neutral"]
YEAR_COLORS = {2024: COLORS["year_2024"], 2025: COLORS["year_2025"]}
TREND_COLORS = {2024: COLORS["trend_2024"], 2025: COLORS["trend_2025"]}

# Legacy aliases (pages/views still import these names)
BG = BG_PAGE
CARD = CARD_BG
BORDER = CARD_BORDER
TEXT = TEXT_ON_LIGHT
MUTED = TEXT_MUTED
NAVY = PRIMARY
NAVY_LIGHT = PRIMARY_LIGHT
SIDEBAR_DARK = PRIMARY
SIDEBAR_MID = PRIMARY
TEAL = ACCENT
LIGHT_RED = NEGATIVE
PALETTE = BOARD_COLOR_SEQUENCE
PASS_COLOR = POSITIVE
FAIL_COLOR = NEGATIVE
MALE_COLOR = ACCENT            # 9th-class gender coding: Boys = blue
FEMALE_COLOR = GOLD            # Girls = gold
GENDER_COLORS = {"Male": MALE_COLOR, "Female": FEMALE_COLOR,
                 "Boys": MALE_COLOR, "Girls": FEMALE_COLOR}
TYPE_COLORS = {"Regular": ACCENT, "Private": GOLD}
PROVINCE_COLORS = {
    "KPK": "#F97316",                   # orange
    "Punjab": ACCENT,                   # blue
    "Federal (Islamabad)": "#A855F7",   # purple
    "Other": "#94A3B8",
}
CHART_CONFIG = {"displayModeBar": False, "responsive": True}


def gender_label(g):
    return "Boys" if g == "Male" else "Girls"


def _tnode(label, value, sub="", color=NAVY, leaf=False):
    pad = "8px 12px" if leaf else "10px 16px"
    minw = "72px" if leaf else "94px"
    subhtml = f'<div style="font-size:11px;opacity:.85;margin-top:1px;">{sub}</div>' if sub else ""
    return (f'<div style="display:inline-block;background:{color};color:#FFFFFF;border-radius:12px;'
            f'padding:{pad};min-width:{minw};box-shadow:0 3px 10px rgba(16,24,40,0.18);text-align:center;white-space:nowrap;">'
            f'<div style="font-size:10.5px;font-weight:600;opacity:.92;letter-spacing:.02em;">{label}</div>'
            f'<div style="font-size:17px;font-weight:700;line-height:1.25;margin-top:1px;">{value}</div>{subhtml}</div>')


TREE_LINE = "#334155"


def _stem(h=16):
    return f'<div style="width:2px;height:{h}px;background:{TREE_LINE};margin:0 auto;"></div>'


def _connector_row(children_html):
    n = len(children_html)
    cells = []
    for i, c in enumerate(children_html):
        lb = f'2px solid {TREE_LINE}' if i > 0 else '2px solid transparent'
        rb = f'2px solid {TREE_LINE}' if i < n - 1 else '2px solid transparent'
        connector = (
            f'<div style="display:flex;width:100%;height:0;">'
            f'<div style="flex:1;border-top:{lb};"></div>'
            f'<div style="flex:1;border-top:{rb};"></div></div>'
        )
        cells.append(
            f'<div style="display:flex;flex-direction:column;align-items:center;padding:0 8px;">'
            f'{connector}{_stem()}{c}</div>'
        )
    return f'<div style="display:flex;align-items:flex-start;">{"".join(cells)}</div>'


def _subtree(node_html, children_html=None):
    if not children_html:
        return f'<div style="display:inline-flex;flex-direction:column;align-items:center;">{node_html}</div>'
    if len(children_html) == 1:
        row = f'<div style="display:flex;flex-direction:column;align-items:center;">{_stem()}{children_html[0]}</div>'
    else:
        row = f'{_stem()}{_connector_row(children_html)}'
    return f'<div style="display:inline-flex;flex-direction:column;align-items:center;">{node_html}{row}</div>'


def _leaf_pair(appeared, passed, failed, pass_pct, fail_pct):
    return [
        _subtree(_tnode("Pass", fmt_k(passed), f"{pass_pct:.0f}%", PASS_COLOR, leaf=True)),
        _subtree(_tnode("Fail", fmt_k(failed), f"{fail_pct:.0f}%", FAIL_COLOR, leaf=True)),
    ]


def render_gender_type_flow(board_name, year_label, totals, gender_df, type_df):
    """Horizontal org-chart flow: Total Appeared -> Gender / Type -> Pass/Fail.
    Only draws branches the workbook actually has data for."""
    total_appeared = totals.get("appeared", 0) or 0
    branches = []

    if not gender_df.empty and "Gender" in gender_df.columns:
        g = gender_df.copy()
        g_total = int(g["Appeared"].sum())
        gender_kids = []
        for _, row in g.iterrows():
            lbl = gender_label(row["Gender"])
            appeared = int(row["Appeared"]) if pd.notna(row["Appeared"]) else 0
            passed = int(row["Passed"]) if pd.notna(row.get("Passed", np.nan)) else 0
            failed = max(appeared - passed, 0)
            pct = round(100 * passed / appeared, 1) if appeared else 0
            color = GENDER_COLORS.get(lbl, NAVY)
            node = _tnode(lbl, fmt_k(appeared), f"{pct:.0f}% pass", color)
            gender_kids.append(_subtree(node, _leaf_pair(appeared, passed, failed, pct, round(100 - pct, 1))))
        branches.append(_subtree(_tnode("Total by Gender", fmt_k(g_total), "", NAVY_LIGHT), gender_kids))

    if not type_df.empty and "Candidate Type" in type_df.columns:
        t = type_df.copy()
        t_total = int(t["Appeared"].sum())
        type_kids = []
        for _, row in t.iterrows():
            lbl = row["Candidate Type"]
            appeared = int(row["Appeared"]) if pd.notna(row["Appeared"]) else 0
            passed = int(row["Passed"]) if pd.notna(row.get("Passed", np.nan)) else 0
            failed = max(appeared - passed, 0)
            pct = round(100 * passed / appeared, 1) if appeared else 0
            color = ACCENT if "regular" in str(lbl).lower() else GOLD
            node = _tnode(lbl, fmt_k(appeared), f"{pct:.0f}% pass", color)
            type_kids.append(_subtree(node, _leaf_pair(appeared, passed, failed, pct, round(100 - pct, 1))))
        branches.append(_subtree(_tnode("Total by Type", fmt_k(t_total), "", PRIMARY), type_kids))

    if not branches:
        return

    tree_html = _subtree(_tnode("Total Appeared", fmt_k(total_appeared), year_label, NAVY), branches)
    scroll_id = "flow-scroll-" + re.sub(r"[^a-z0-9]+", "-", board_name.lower())
    html = (f'<div id="{scroll_id}" style="overflow-x:auto;padding:10px 8px 16px 8px;">'
            f'<div style="display:flex;justify-content:center;min-width:680px;padding:0 20px 4px 20px;">{tree_html}</div></div>'
            f'<script>const el=document.getElementById("{scroll_id}");'
            f'if(el){{el.scrollLeft=(el.scrollWidth-el.clientWidth)/2;}}</script>')
    with chart_card(f"Result Flow — {board_name}"):
        st.markdown(html, unsafe_allow_html=True)




# ── Plotly helpers ─────────────────────────────────────────────────────────────
def style_fig(fig):
    """Apply the shared 9th-class chart base layout (transparent plot/paper
    background, Inter font, dark-navy text, hairline gridlines) on top of
    whatever the chart factory already set — margins, legends and heights
    chosen by a factory are preserved, the base only fills in what's
    missing."""
    return _base_plotly_layout(fig)


def chart_title(text):
    if not text:
        return None
    return dict(text=text, x=0, xanchor="left", font=dict(size=14), pad=dict(t=4, b=18))


def legend_top_right():
    return dict(orientation="h", yanchor="bottom", y=1.0, x=1.0, xanchor="right",
                bgcolor="rgba(255,255,255,0.9)", tracegroupgap=10)


def legend_bottom_clear(extra_rows=0):
    return dict(orientation="h", yanchor="top", y=-0.24 - (extra_rows * 0.08), x=0.5, xanchor="center",
                bgcolor="rgba(255,255,255,0.9)", tracegroupgap=10)


def chart_margins(title="", legend_pos="none", extra_right=0):
    top = 72 if title else 44
    bottom = 52
    if legend_pos == "top":
        top = max(top, 58)
    elif legend_pos == "bottom":
        bottom = 92
    elif legend_pos == "bottom_multi":
        bottom = 115
    return dict(t=top, b=bottom, l=20, r=30 + extra_right)


def show_chart(fig):
    if fig is not None:
        st.plotly_chart(fig, width='stretch', config=CHART_CONFIG)


def fmt_k(n):
    n = 0 if n is None or (isinstance(n, float) and pd.isna(n)) else n
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return f"{n:,}"


def csv_download_button(df, label, filename):
    if df is not None and not df.empty:
        st.download_button(label, df.to_csv(index=False).encode("utf-8"), filename, "text/csv")


def render_chart_legend():
    st.markdown(
        f"""<div class="legend-bar">
        <div class="legend-item"><span class="legend-dot" style="background:{MALE_COLOR}"></span> Boys</div>
        <div class="legend-item"><span class="legend-dot" style="background:{FEMALE_COLOR}"></span> Girls</div>
        <div class="legend-item"><span class="legend-dot" style="background:{PASS_COLOR}"></span> Passed</div>
        <div class="legend-item"><span class="legend-dot" style="background:{FAIL_COLOR}"></span> Failed</div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_notes(notes):
    """Surface data-quality caveats for this board/year. These are the
    workbook's own Notes column verbatim, except where data_loader.py's
    board_totals() adds one auto-flagged note for an unexplained gender-split
    gap the source gazette doesn't itself document (always suffixed
    "[Auto-flagged by the dashboard...]" so it's never mistaken for the
    source's own words)."""
    if not notes:
        return
    with st.expander(f"ℹ️ Data notes from the source workbook ({len(notes)})"):
        for n in notes:
            st.markdown(f'<div class="note-pill">⚠️ {n}</div>', unsafe_allow_html=True)


# Explanatory context reported to this dashboard by its user for a specific
# board's results — NOT extracted from the Excel workbook. Kept visually and
# textually separate from render_notes() (workbook Notes column) wherever
# it's shown, and clearly labeled as user-supplied, not source data.
BOARD_REPORTED_CONTEXT = {
    "BISE Kohat": [
        "**Strict anti-cheating policy** — the board implemented tougher monitoring and surveillance during exams to stop unfair means.",
        "**Shift to conceptual learning** — examiners moved away from rote memorization; marking now requires clear concepts and critical thinking.",
        "**Higher grading standards** — stricter paper evaluation resulted in a clearer separation of capable students from others.",
    ],
}


# ── Chart factory functions ────────────────────────────────────────────────────
def donut_pie(labels, values, colors, title="", height=400):
    n = len(labels)
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.45, marker=dict(colors=colors),
        textinfo="percent", texttemplate="%{percent:.1%}",
        textposition="inside", insidetextorientation="horizontal",
        hovertemplate="%{label}: %{value:,}<br>%{percent:.1%}<extra></extra>",
    )])
    if n > 4:
        fig.update_traces(domain=dict(x=[0.06, 0.94], y=[0.18, 1.0]))
        legend_cfg = dict(orientation="h", yanchor="top", y=-0.02, x=0.5, xanchor="center",
                          font=dict(size=10), tracegroupgap=6, bgcolor="rgba(255,255,255,0.85)")
        margins = dict(t=55, b=115, l=10, r=10)
        chart_height = max(height + 140, 600)
    else:
        legend_cfg = dict(orientation="h", yanchor="bottom", y=-0.18, x=0.5, xanchor="center")
        margins = dict(t=55, b=90, l=30, r=30)
        chart_height = height
    fig.update_layout(title=title, height=chart_height, showlegend=True, legend=legend_cfg, margin=margins)
    return style_fig(fig)


def pass_fail_pie(passed, failed, title="", height=400):
    if passed + failed <= 0:
        return None
    return donut_pie(["Passed", "Failed"], [passed, failed], [PASS_COLOR, FAIL_COLOR], title=title, height=height)


def pass_fail_hbar(df, label_col, title="", height=None):
    if df.empty:
        return None
    plot_df = df.copy()
    if "Pass %" not in plot_df.columns or plot_df["Pass %"].isna().all():
        plot_df["Pass %"] = (100 * plot_df["Passed"] / plot_df["Appeared"].replace(0, float("nan"))).round(1)
    plot_df["Fail %"] = (100 - plot_df["Pass %"]).clip(lower=0).round(1)
    chart_h = height or max(260, 90 * len(plot_df))
    fig = go.Figure()
    fig.add_trace(go.Bar(y=plot_df[label_col].astype(str), x=plot_df["Pass %"], name="Passed",
                         orientation="h", marker_color=PASS_COLOR,
                         text=[f"{v:.0f}%" for v in plot_df["Pass %"]],
                         textposition="inside", insidetextanchor="middle"))
    fig.add_trace(go.Bar(y=plot_df[label_col].astype(str), x=plot_df["Fail %"], name="Failed",
                         orientation="h", marker_color=FAIL_COLOR,
                         text=[f"{v:.0f}%" for v in plot_df["Fail %"]],
                         textposition="inside", insidetextanchor="middle"))
    layout_kwargs = dict(barmode="stack",
                      xaxis=dict(range=[0, 100], title="Percentage"),
                      yaxis=dict(automargin=True), height=chart_h, showlegend=True,
                      legend=legend_top_right(),
                      margin=chart_margins(title=title, legend_pos="top"))
    ct = chart_title(title)
    if ct is not None:
        layout_kwargs["title"] = ct
    fig.update_layout(**layout_kwargs)
    return style_fig(fig)


def subject_pass_hbar(subjects, top_n=15, title=None):
    if subjects.empty:
        return None
    data = subjects.sort_values("Pass %", ascending=True).tail(top_n)
    fig = go.Figure(go.Bar(
        x=data["Pass %"], y=data["Subject"], orientation="h",
        marker=dict(color=data["Pass %"], colorscale=[[0, FAIL_COLOR], [0.5, NAVY_LIGHT], [1, PASS_COLOR]]),
        text=[f"{v:.1f}%" for v in data["Pass %"]], textposition="outside",
    ))
    fig.update_layout(title=chart_title(title or f"Subject-wise Pass % (top {len(data)})"),
                      xaxis=dict(range=[0, 105], title="Pass %"), yaxis=dict(automargin=True),
                      height=max(420, 28 * len(data)), showlegend=False,
                      margin=chart_margins(title="x", extra_right=40))
    return style_fig(fig)


def district_pass_hbar(districts, top_n=12, title=None):
    if districts.empty:
        return None
    data = districts.sort_values("Pass %", ascending=True).tail(top_n)
    fig = go.Figure(go.Bar(
        x=data["Pass %"], y=data["District"], orientation="h",
        marker=dict(color=data["Pass %"], colorscale=[[0, FAIL_COLOR], [0.5, NAVY_LIGHT], [1, PASS_COLOR]]),
        text=[f"{v:.1f}%" for v in data["Pass %"]], textposition="outside", cliponaxis=False,
    ))
    fig.update_layout(title=chart_title(title or f"District Pass % (top {len(data)})"),
                      xaxis=dict(range=[0, 112], title="Pass %"), yaxis=dict(automargin=True),
                      height=max(380, 32 * len(data)), showlegend=False,
                      margin=chart_margins(title="x", extra_right=40))
    return style_fig(fig)


def board_rank_hbar(labels, values, title="", x_title="Pass %", height=None, decimals=2):
    if not labels or not values:
        return None
    order = sorted(range(len(values)), key=lambda i: values[i])
    labels_s = [labels[i] for i in order]
    values_s = [values[i] for i in order]
    chart_h = height or max(280, 42 * len(labels_s))
    fig = go.Figure(go.Bar(
        x=values_s, y=labels_s, orientation="h",
        marker=dict(color=values_s, colorscale=[[0, FAIL_COLOR], [0.5, NAVY_LIGHT], [1, PASS_COLOR]]),
        text=[f"{v:.{decimals}f}%" for v in values_s], textposition="outside", cliponaxis=False,
    ))
    fig.update_layout(title=chart_title(title), xaxis=dict(range=[0, 112], title=x_title),
                      yaxis=dict(automargin=True), height=chart_h, showlegend=False,
                      margin=chart_margins(title=title, extra_right=40))
    return style_fig(fig)


def gender_split_pie(gender_df, title="Gender Distribution"):
    if gender_df.empty:
        return None
    labels, values, colors = [], [], []
    for _, row in gender_df.iterrows():
        label = gender_label(row["Gender"])
        labels.append(label)
        values.append(int(row["Appeared"]))
        colors.append(GENDER_COLORS.get(row["Gender"], TEAL))
    return donut_pie(labels, values, colors, title=title, height=400)


def trend_line_chart(df, title, y_col="Pass %", color=NAVY):
    if df.empty or y_col not in df.columns:
        return None
    plot_df = df.dropna(subset=[y_col]).copy()
    if plot_df.empty:
        return None
    yvals = plot_df[y_col].astype(float)
    y_min, y_max = yvals.min(), yvals.max()
    pad = max(3, (y_max - y_min) * 0.15)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=plot_df["Year"], y=plot_df[y_col], mode="lines+markers",
        line=dict(color=color, width=3), marker=dict(size=10),
        hovertemplate="Year %{x}<br>%{y:.1f}%<extra></extra>" if y_col == "Pass %" else "Year %{x}<br>%{y:,.0f}<extra></extra>",
        name=y_col,
    ))
    fig.update_layout(title=chart_title(title), xaxis=dict(dtick=1, title="Year"),
                      yaxis=dict(title=y_col, range=[max(0, y_min - pad), y_max + pad + 5]),
                      height=400, showlegend=False, margin=dict(t=80, b=52, l=20, r=30))
    return style_fig(fig)


def year_compare_chart(trend_df):
    if trend_df.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Bar(x=trend_df["Year"], y=trend_df["Passed"], name="Passed", marker_color=PASS_COLOR))
    fig.add_trace(go.Bar(x=trend_df["Year"], y=trend_df["Failed"], name="Failed", marker_color=FAIL_COLOR))
    fig.update_layout(title=chart_title("Passed vs Failed by Year"), barmode="stack",
                      height=360, showlegend=False, margin=chart_margins(title="Passed vs Failed by Year"))
    return style_fig(fig)


def group_pass_chart(df):
    """Bar chart of Pass % by Group x Gender (Pre-Medical/Humanities/...)."""
    if df.empty:
        return None
    pivot = df.pivot_table(index="Group", columns="Gender", values="Pass %", aggfunc="mean").reset_index()
    fig = go.Figure()
    colors = {"Male": MALE_COLOR, "Female": FEMALE_COLOR}
    for gender in pivot.columns:
        if gender == "Group":
            continue
        fig.add_trace(go.Bar(
            x=pivot["Group"], y=pivot[gender],
            name=gender_label(gender) if gender in ("Male", "Female") else gender,
            marker_color=colors.get(gender, NAVY),
            text=[f"{v:.0f}%" if pd.notna(v) else "" for v in pivot[gender]],
            textposition="outside",
        ))
    fig.update_layout(title=chart_title("Pass % by Group and Gender"), barmode="group",
                      yaxis=dict(range=[0, 110]), height=max(420, 80 * len(pivot)),
                      legend=legend_top_right(), xaxis=dict(automargin=True),
                      margin=chart_margins(title="Pass % by Group and Gender", legend_pos="top"))
    return style_fig(fig)


def gauge_chart(value, title, height=280):
    if value is None or pd.isna(value):
        return None
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(float(value), 1),
        number={"suffix": "%", "font": {"size": 32}},
        title={"text": title, "font": {"size": 14}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": PASS_COLOR, "thickness": 0.28},
            "bgcolor": "white", "borderwidth": 0,
            "steps": [{"range": [0, 50], "color": "#FCE4E4"},
                       {"range": [50, 75], "color": "#FDF3D8"},
                       {"range": [75, 100], "color": "#DFF5F1"}],
            "threshold": {"line": {"color": NAVY, "width": 3}, "thickness": 0.85, "value": round(float(value), 1)},
        },
    ))
    fig.update_layout(height=height, margin=dict(t=50, b=10, l=30, r=30))
    return style_fig(fig)


def funnel_chart(stages, values, title="", height=380):
    if not stages or not values or all(v <= 0 for v in values):
        return None
    fig = go.Figure(go.Funnel(
        y=stages, x=values, marker=dict(color=PALETTE[: len(stages)]),
        textinfo="value+percent initial", textposition="inside",
    ))
    fig.update_layout(title=chart_title(title), height=height, showlegend=False,
                      margin=chart_margins(title=title))
    return style_fig(fig)


def stacked_bar_breakdown_chart(appeared, passed, failed, title="", height=380):
    if appeared is None:
        return None
    pass_pct = (passed / appeared * 100) if appeared else 0
    fail_pct = (failed / appeared * 100) if appeared else 0
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Result Breakdown"], y=[passed], name="Passed",
                         marker=dict(color=PASS_COLOR),
                         text=[f"Passed: {passed:,.0f} ({pass_pct:.1f}%)"],
                         textposition="inside", width=[0.45]))
    fig.add_trace(go.Bar(x=["Result Breakdown"], y=[failed], name="Failed",
                         marker=dict(color=FAIL_COLOR),
                         text=[f"Failed: {failed:,.0f} ({fail_pct:.1f}%)"],
                         textposition="inside", width=[0.45]))
    fig.update_layout(barmode="stack", title=chart_title(title), height=height,
                      showlegend=True, legend=legend_top_right(),
                      margin=chart_margins(title=title, legend_pos="top"),
                      yaxis=dict(title=f"Appeared: {appeared:,.0f}", showgrid=True,
                                 gridcolor="rgba(0,0,0,0.06)", griddash="dot"),
                      xaxis=dict(showgrid=False))
    return style_fig(fig)


def treemap_chart(labels, values, title="", height=420):
    if not labels or not values:
        return None
    values = [v if pd.notna(v) and v > 0 else 0 for v in values]
    if sum(values) <= 0:
        return None
    fig = go.Figure(go.Treemap(
        labels=labels, parents=[""] * len(labels), values=values,
        marker=dict(colors=(PALETTE * (len(labels) // len(PALETTE) + 1))[: len(labels)]),
        textinfo="label+value+percent parent",
    ))
    fig.update_layout(title=chart_title(title), height=height, margin=chart_margins(title=title))
    return style_fig(fig)


def bubble_scatter_chart(x, y, size, text, title="", x_title="", y_title="Pass %", height=440):
    if x is None or len(x) == 0:
        return None
    x = [v if pd.notna(v) else 0 for v in x]
    y = [v if pd.notna(v) else 0 for v in y]
    size = [v if pd.notna(v) and v > 0 else 1 for v in size]
    max_size = max(size) if len(size) else 1
    show_labels = len(x) <= 8
    fig = go.Figure(go.Scatter(
        x=x, y=y, mode="markers+text" if show_labels else "markers",
        text=text if show_labels else None, textposition="top center",
        textfont=dict(size=10), customdata=text,
        hovertemplate="<b>%{customdata}</b><br>" + (x_title or "X") + ": %{x:,.0f}<br>" + y_title + ": %{y:.1f}%<extra></extra>",
        marker=dict(size=size, sizemode="area", sizeref=2.0 * max_size / (46.0 ** 2), sizemin=6,
                    color=y, colorscale=[[0, FAIL_COLOR], [0.5, NAVY_LIGHT], [1, PASS_COLOR]],
                    showscale=False, line=dict(width=1, color="white"), opacity=0.85),
    ))
    fig.update_layout(title=chart_title(title),
                      xaxis=dict(title=x_title), yaxis=dict(title=y_title, range=[0, 105]),
                      height=height, showlegend=False, margin=chart_margins(title=title))
    return style_fig(fig)


def grouped_bar_chart(x, series, title="", y_title="Students", height=400, colors=None,
                      show_values=False, value_suffix=""):
    if x is None or len(x) == 0:
        return None
    fig = go.Figure()
    palette = colors or [PASS_COLOR, FAIL_COLOR, NAVY, ACCENT]
    for i, (name, values) in enumerate(series.items()):
        bar_kwargs = dict(x=x, y=values, name=name, marker_color=palette[i % len(palette)])
        if show_values:
            bar_kwargs["text"] = [f"{v:.1f}{value_suffix}" for v in values]
            bar_kwargs["textposition"] = "outside"
        fig.add_trace(go.Bar(**bar_kwargs))
    fig.update_layout(title=chart_title(title), barmode="group",
                      xaxis=dict(automargin=True), yaxis=dict(title=y_title),
                      height=height, legend=legend_top_right(),
                      margin=chart_margins(title=title, legend_pos="top"))
    return style_fig(fig)


def heatmap_chart(z, x_labels, y_labels, title="", height=420):
    if z is None or len(z) == 0:
        return None
    fig = go.Figure(go.Heatmap(
        z=z, x=x_labels, y=y_labels,
        colorscale=[[0, FAIL_COLOR], [0.5, NAVY_LIGHT], [1, PASS_COLOR]],
        text=[[f"{v:.1f}%" if pd.notna(v) else "" for v in row] for row in z],
        texttemplate="%{text}", hovertemplate="%{y} · %{x}<br>%{z:.1f}%<extra></extra>",
        colorbar=dict(title="Pass %"),
    ))
    fig.update_layout(title=chart_title(title), xaxis=dict(dtick=1, title="Year"),
                      yaxis=dict(automargin=True),
                      height=max(height, 28 * len(y_labels)), margin=chart_margins(title=title))
    return style_fig(fig)


# ── Analytics helpers ──────────────────────────────────────────────────────────
def build_insights(gender_df, type_df, group_df, subjects, pass_pct, yoy_delta):
    insights = []
    if not gender_df.empty and len(gender_df) >= 2:
        g = gender_df.set_index("Gender")
        if "Male" in g.index and "Female" in g.index:
            gap = g.loc["Female", "Pass %"] - g.loc["Male", "Pass %"]
            who = "Girls" if gap >= 0 else "Boys"
            insights.append(f"{who} pass **{abs(gap):.1f}%** higher than the other gender.")
    if not type_df.empty and len(type_df) >= 2 and "Candidate Type" in type_df.columns:
        t = type_df.set_index("Candidate Type")
        if "Regular" in t.index and "Private" in t.index:
            gap = t.loc["Regular", "Pass %"] - t.loc["Private", "Pass %"]
            insights.append(f"Regular students pass **{gap:.1f}%** higher than Private students.")
    if not group_df.empty:
        best = group_df.iloc[0]
        insights.append(f"Highest-performing group: **{best['Group']}** at **{best['Pass %']:.1f}%** pass rate.")
    if not subjects.empty:
        weak = subjects[subjects["Pass %"] < 70]
        if not weak.empty:
            insights.append(f"**{len(weak)}** subject(s) below 70% pass rate.")
    if yoy_delta is not None:
        arrow = "improved" if yoy_delta >= 0 else "declined"
        insights.append(f"Pass rate {arrow} **{abs(yoy_delta):.1f}%** from 2024 to 2025.")
    insights.append(f"Overall pass rate for selected view: **{pass_pct:.1f}%**.")
    return insights


def yoy_delta_from_trend(trend_df):
    if trend_df.empty or "Pass %" not in trend_df.columns or len(trend_df) < 2:
        return None
    t = trend_df.sort_values("Year")
    return float(t.iloc[-1]["Pass %"] - t.iloc[0]["Pass %"])


# ── Shared data loading / sidebar ───────────────────────────────────────────
def show_missing_workbook_error():
    st.error(
        "Place **11th_Class_Boards_Results_Combined.xlsx** in this folder, then reload the app."
    )
    st.stop()
