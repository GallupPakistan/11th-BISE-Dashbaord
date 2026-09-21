"""
charts/_base.py

Shared Plotly base layout for every chart in the 11th-class dashboard —
matches the 9th-class dashboard's chart styling exactly: transparent
plot/paper background, Inter body font, dark-navy text, hairline gridlines,
and uniform-text handling so overlapping labels hide instead of colliding.

Every chart factory should finish with:  return base_layout(fig)
Only fills values the factory hasn't already set — margins, legends and
heights chosen by a factory are preserved.
"""
import plotly.graph_objects as go

from styles.theme import COLORS, BOARD_COLOR_SEQUENCE

__all__ = ["COLORS", "BOARD_COLOR_SEQUENCE", "base_layout"]


def base_layout(fig, legend_title="", height=None):
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color=COLORS["text_on_light"],
        font_family="'Inter','Segoe UI',sans-serif",
        font_size=12,
        legend_title_text=legend_title if legend_title else None,
        uniformtext_minsize=10,
        uniformtext_mode="hide",
        bargap=0.35,
    )
    fig.update_xaxes(gridcolor="rgba(20,27,60,0.08)")
    fig.update_yaxes(gridcolor="rgba(20,27,60,0.08)")
    if height:
        fig.update_layout(height=height)
    return fig