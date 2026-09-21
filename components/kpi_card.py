"""
components/kpi_card.py

One reusable KPI card — icon + compact value + label, with an optional
delta pill (+/-) shown in green/red. Used on every page's top row.
Styling lives in styles/css.py (_kpi_card_css) — edit there, not here.
"""

import streamlit as st


def format_compact(n) -> str:
    """Compact number formatting for KPI values and deltas:
    2213000 -> '2.21M', 105601 -> '105.6K', 12345 -> '12.3K',
    979 -> '979'. Keeps the sign for negatives (-8.5K)."""
    n = float(n)
    absn = abs(n)
    if absn >= 1_000_000:
        return f"{n / 1_000_000:.2f}".rstrip("0").rstrip(".") + "M"
    if absn >= 1_000:
        return f"{n / 1_000:.1f}".rstrip("0").rstrip(".") + "K"
    return f"{n:,.0f}"


# accent="green"/"red"/"gold"/"blue" switches the card's accent strip,
# icon tint (CSS variables set per class in styles/css.py).
_ACCENT_CLASSES = {
    "blue": "kpi-card-accent-blue",
    "green": "kpi-card-accent-green",
    "red": "kpi-card-accent-red",
    "gold": "kpi-card-accent-gold",
}


def render_kpi(
    icon: str,
    value: str,
    label: str,
    delta: str = "",
    delta_positive: bool = True,
    accent: str = "blue",
    spark: list[float] | None = None,
) -> None:
    delta_html = ""
    if delta:
        cls = "kpi-card-delta-positive" if delta_positive else "kpi-card-delta-negative"
        arrow = "arrow_upward" if delta_positive else "arrow_downward"
        delta_html = (
            f'<div class="{cls}">'
            f'<span class="material-symbols-outlined">{arrow}</span>{delta}'
            f"</div>"
        )

    spark_html = ""
    if spark:
        try:
            vals = [float(v) for v in spark]
            mx = max(vals) if vals else 1.0
            if mx <= 0:
                mx = 1.0
            bars = "".join(
                f'<span style="height:{max(3.0, v / mx * 15.0):.1f}px"></span>'
                for v in vals
            )
            spark_html = f'<div class="kpi-card-spark">{bars}</div>'
        except (TypeError, ValueError):
            spark_html = ""

    accent_cls = _ACCENT_CLASSES.get(accent, _ACCENT_CLASSES["blue"])
    html = f"""<div class="kpi-card {accent_cls}">
<div class="kpi-card-icon"><span class="material-symbols-outlined">{icon}</span></div>
<div class="kpi-card-body">
<div class="kpi-card-value">{value}</div>
<div class="kpi-card-label">{label}</div>
{delta_html}
{spark_html}
</div>
</div>"""
    st.markdown(html, unsafe_allow_html=True)


def render_kpi_row(kpis: list[dict]) -> None:
    """
    kpis: list of dicts, each with keys: icon, value, label, and
    optionally delta / delta_positive / accent. Renders them evenly
    spaced across a single row using Streamlit columns.
    """
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        with col:
            render_kpi(
                icon=kpi.get("icon", "bar_chart"),
                value=kpi.get("value", "-"),
                label=kpi.get("label", ""),
                delta=kpi.get("delta", ""),
                delta_positive=kpi.get("delta_positive", True),
                accent=kpi.get("accent", "blue"),
                spark=kpi.get("spark"),
            )