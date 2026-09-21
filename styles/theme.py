"""
styles/theme.py

Single source of truth for colors and fonts. Every CSS block in
styles/css.py reads its values from the COLORS / FONTS dicts here.
To re-theme the whole dashboard, edit ONLY this file.
"""

COLORS = {
    # Topbar / primary surfaces
    "primary": "#0B1E4D",          # main navy background (topbar, sidebar)
    "primary_light": "#123068",    # slightly lighter navy (hover states, cards)

    # Accents
    "accent": "#3B82F6",           # bright blue accent bar / links
    "accent_light": "#79AFFF",     # subtitle / brand-sub light blue
    "gold": "#C9A84C",             # secondary accent (KPI highlights, active nav item)

    # Backgrounds
    "bg_page": "#E9EAEE",          # overall app background (light grey)
    "bg_card": "rgba(255,255,255,0.05)",   # glass card fill (used on navy surfaces only)
    "border_card": "rgba(255,255,255,0.12)",

    # Light surface cards (KPI cards, chart cards) — these sit directly
    # on the light-grey page background, so they need solid light fill
    # and dark text, unlike the glass cards on navy surfaces above.
    "card_bg_light": "#FFFFFF",
    "card_border_light": "#DCDFE6",
    "card_shadow_light": "rgba(16, 24, 64, 0.08)",
    "text_on_light": "#141B3C",           # dark navy, for values/titles on light cards
    "text_on_light_muted": "#6B7280",     # grey, for labels/subtitles on light cards

    # Text (used on navy surfaces: topbar, sidebar)
    "text_primary": "#FFFFFF",
    "text_secondary": "rgba(255,255,255,0.75)",
    "text_muted": "rgba(255,255,255,0.55)",

    # Status colors (for deltas / change indicators)
    "positive": "#22C55E",
    "negative": "#EF4444",
    "neutral": "#9CA3AF",

    # Year color-coding (kept consistent with the source Excel workbook)
    "year_2024": "#5B8DEF",
    "year_2025": "#E8B94A",

    # Year-over-year trend charts — light blue (2024) vs dark navy (2025)
    "trend_2024": "#8FB8F6",
    "trend_2025": "#123068",

    # Pakistan choropleth map
    "map_no_data": "#E5E7EB",          # light grey fill (old, very subtle)
    "map_no_data_strong": "#C7CDDA",   # clearly-visible grey for provinces with no board data
    "map_land": "#EEF1F6",             # land background behind the map patch
    "map_scale": ["#BFD7FF", "#3B82F6", "#0B1E4D"],  # low -> high appeared

    # Stat badge (topbar right-hand KPI)
    "stat_icon_bg": "#0F4C9D",
    "stat_icon_border": "#1A60BC",
}

FONTS = {
    "heading": "'Cinzel', serif",
    "body": "'Inter', 'Segoe UI', sans-serif",
}

# Chart-specific color sequences (Plotly) — keep board colors stable across
# every chart so the same board always renders in the same color.
BOARD_COLOR_SEQUENCE = [
    "#3B82F6", "#C9A84C", "#22C55E", "#EF4444", "#A855F7",
    "#F97316", "#14B8A6", "#EC4899", "#84CC16", "#6366F1",
    "#F43F5E", "#0EA5E9", "#EAB308", "#8B5CF6", "#10B981",
]