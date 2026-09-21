"""
styles/css.py

Builds every CSS block the dashboard uses from styles/theme.py values,
and exposes one inject_css() call that app.py runs once per session.

Add a new component's CSS as its own _xxx_css() function below, then
include it in inject_css(). Never write raw CSS colors inside a page or
component file — pull them from theme.COLORS instead.
"""

import streamlit as st
from styles.theme import COLORS, FONTS


def _fonts_css() -> str:
    return """
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Inter:wght@400;500;600;700;800&display=swap">
    <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Symbols+Outlined" />
    <style>
    html, body, [class*="css"] { font-family: {body}; }
    </style>
    """.replace("{body}", FONTS["body"])


def _page_base_css() -> str:
    return f"""
    <style>
    .stApp {{
        background-color: {COLORS['bg_page']};
    }}
    h1, h2, h3, .hec-topbar-title {{
        font-family: {FONTS['heading']};
    }}

    /* ---------- Hide Streamlit's default chrome ----------
       Removes the "Deploy" button and the hamburger/running-man menu
       from the default header, and collapses the header's own
       background/height so it takes up no visible space — our
       custom topbar becomes the first thing the eye hits. The header
       element itself is kept (not display:none) so the sidebar's
       native collapse/expand arrow, which lives inside it, keeps
       working. */
    header[data-testid="stHeader"] {{
        background-color: transparent;
        height: 0rem;
    }}
    div[data-testid="stToolbar"] {{
        visibility: hidden;
    }}
    #MainMenu {{
        visibility: hidden;
    }}
    footer {{
        visibility: hidden;
    }}

    /* Reclaim the vertical space the hidden header used to occupy,
       so our custom topbar is truly the first thing on the page. */
    .block-container {{
        padding-top: 1.2rem;
    }}
    </style>
    """


def _topbar_css() -> str:
    return f"""
    <style>
    /* ---------- Top bar (full page header) ---------- */
    .hec-topbar {{
        position: relative;
        overflow: hidden;
        background-color: {COLORS['primary']} !important;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin: 0 0 1.4rem 0;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.2);
        color: {COLORS['text_primary']};
    }}

    .hec-topbar-watermark {{
        position: absolute;
        top: -2rem;
        right: 30%;
        opacity: 0.05;
        pointer-events: none;
    }}
    .hec-topbar-watermark .material-symbols-outlined {{
        font-size: 18rem;
        color: {COLORS['text_primary']};
    }}

    .hec-topbar-dots {{
        position: absolute;
        top: 1.3rem;
        right: 1.6rem;
        width: 120px;
        height: 80px;
        background-image: radial-gradient(rgba(255,255,255,0.2) 1.5px, transparent 1.5px);
        background-size: 12px 12px;
        pointer-events: none;
    }}

    .hec-topbar-toprow {{
        position: relative;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 1.2rem;
        margin-bottom: 1.8rem;
    }}
    .hec-topbar-brand {{
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }}
    .hec-topbar-logo-circle {{
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background-color: rgba(255,255,255,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid rgba(255,255,255,0.15);
    }}
    .hec-topbar-logo-circle .material-symbols-outlined {{
        font-size: 24px;
        color: {COLORS['text_primary']};
    }}
    .hec-topbar-brand-text {{
        display: flex;
        flex-direction: column;
        line-height: 1.2;
    }}
    .hec-topbar-brand-name {{
        font-size: 1.1rem;
        font-weight: 700;
        color: {COLORS['text_primary']};
        letter-spacing: 0.02em;
    }}
    .hec-topbar-brand-sub {{
        font-size: 0.85rem;
        font-weight: 500;
        color: {COLORS['accent_light']};
    }}

    .hec-topbar-vsep {{
        width: 1px;
        height: 32px;
        background-color: rgba(255,255,255,0.15);
        margin: 0 0.2rem;
    }}

    .hec-topbar-crumbs {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-size: 0.85rem;
        color: {COLORS['text_secondary']};
        white-space: nowrap;
    }}
    .hec-topbar-crumb-icon-badge {{
        width: 30px;
        height: 30px;
        border-radius: 8px;
        background-color: rgba(0, 0, 0, 0.25);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.3);
    }}
    .hec-topbar-crumb-icon-badge .material-symbols-outlined {{
        font-size: 16px;
        color: {COLORS['text_primary']};
    }}
    .hec-topbar-sep {{ color: rgba(255,255,255,0.35); margin: 0 0.2rem; }}
    .hec-topbar-crumb {{ color: rgba(255,255,255,0.8); }}
    .hec-topbar-current {{ color: {COLORS['text_primary']}; font-weight: 600; }}

    .hec-topbar-bottomrow {{
        position: relative;
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 1.5rem;
    }}
    .hec-topbar-left {{ display: flex; flex-direction: column; gap: 0.6rem; max-width: 650px; }}

    .hec-topbar-title-wrapper {{
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }}
    .hec-topbar-accent-bar {{
        width: 4px;
        height: 2rem;
        border-radius: 4px;
        background-color: {COLORS['accent']};
    }}
    .hec-topbar-title {{
        font-size: 2rem;
        font-weight: 700;
        color: {COLORS['text_primary']};
        line-height: 1;
        letter-spacing: -0.01em;
    }}
    .hec-topbar-subtitle {{
        font-size: 0.9rem;
        color: {COLORS['text_secondary']};
        line-height: 1.5;
        margin-bottom: 0.3rem;
    }}
    .hec-topbar-lastupdated-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background-color: rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 8px;
        padding: 0.4rem 0.8rem;
        font-size: 0.8rem;
        color: {COLORS['text_secondary']};
        width: fit-content;
    }}
    .hec-topbar-lastupdated-pill .material-symbols-outlined {{
        font-size: 16px;
        color: {COLORS['accent_light']};
    }}
    .hec-topbar-lastupdated-pill b {{ color: {COLORS['text_primary']}; font-weight: 600; }}

    .hec-topbar-right {{ display: flex; align-items: center; }}
    .hec-topbar-stat {{
        display: flex;
        align-items: center;
        background: linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.03));
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        backdrop-filter: blur(10px);
    }}
    .hec-topbar-stat-icon-circle {{
        width: 52px;
        height: 52px;
        border-radius: 50%;
        background-color: {COLORS['stat_icon_bg']};
        border: 2px solid {COLORS['stat_icon_border']};
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }}
    .hec-topbar-stat-icon-circle .material-symbols-outlined {{
        font-size: 28px;
        color: {COLORS['text_primary']};
    }}
    .hec-topbar-stat-vsep {{
        width: 1px;
        height: 44px;
        background-color: rgba(255,255,255,0.15);
        margin: 0 1.5rem;
    }}
    .hec-topbar-stat-text {{
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    .hec-topbar-stat-value {{
        font-size: 2rem;
        font-weight: 800;
        color: {COLORS['text_primary']};
        line-height: 1;
        letter-spacing: -0.02em;
    }}
    .hec-topbar-stat-label {{
        font-size: 0.65rem;
        font-weight: 600;
        color: {COLORS['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.3rem;
    }}

    @media (max-width: 900px) {{
        .hec-topbar-watermark {{ display: none; }}
        .hec-topbar-bottomrow {{ flex-direction: column; align-items: flex-start; }}
        .hec-topbar-stat {{ width: 100%; justify-content: flex-start; }}
        .hec-topbar-center {{ display: none; }}
    }}
    </style>
    """


def _kpi_card_css() -> str:
    return f"""
    <style>
    /* Compact KPI card: left accent strip + tinted icon tile + small
       value + uppercase label + delta pill. The accent color is a CSS
       variable so each card can override it via a modifier class
       (kpi-card-accent-green/red/gold — see components/kpi_card.py). */
    .kpi-card {{
        --kpi-accent: {COLORS['accent']};
        --kpi-accent-soft: rgba(59, 130, 246, 0.12);
        position: relative;
        background: linear-gradient(180deg, #FFFFFF 0%, #F7F8FC 100%);
        border: 1px solid {COLORS['card_border_light']};
        border-radius: 14px;
        padding: 0.85rem 1rem 0.85rem 1.2rem;
        box-shadow: 0 4px 14px {COLORS['card_shadow_light']};
        display: flex;
        align-items: center;
        gap: 0.8rem;
        overflow: hidden;
        height: 100%;
        min-height: 100px;
    }}
    /* Equal-height KPI row: stretch each column's vertical block so every
       card in the row matches the tallest one. Scoped to direct markdown
       children (charts sit in border-wrappers, so they're unaffected). */
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {{
        height: 100%;
        display: flex;
        flex-direction: column;
    }}
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div[data-testid="stMarkdown"] {{
        flex: 1 1 auto;
    }}
    /* Chart cards inside columns (e.g. Pakistan Map next to Top 5
       Boards) stretch to the row's tallest card so the boxes always
       match height. */
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {{
        height: 100%;
    }}
    .kpi-card::before {{
        content: "";
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 4px;
        background: var(--kpi-accent);
    }}
    .kpi-card-accent-green {{ --kpi-accent: {COLORS['positive']}; --kpi-accent-soft: rgba(34, 197, 94, 0.12); }}
    .kpi-card-accent-red {{ --kpi-accent: {COLORS['negative']}; --kpi-accent-soft: rgba(239, 68, 68, 0.12); }}
    .kpi-card-accent-gold {{ --kpi-accent: {COLORS['gold']}; --kpi-accent-soft: rgba(201, 168, 76, 0.16); }}

    .kpi-card-icon {{
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: var(--kpi-accent-soft);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }}
    .kpi-card-icon .material-symbols-outlined {{
        font-size: 20px;
        color: var(--kpi-accent);
        font-variation-settings: 'FILL' 0, 'wght' 500, 'GRAD' 0, 'opsz' 24;
    }}
    .kpi-card-body {{ min-width: 0; }}
    .kpi-card-value {{
        font-size: 1.1rem;
        font-weight: 800;
        color: {COLORS['text_on_light']};
        line-height: 1.2;
        letter-spacing: -0.01em;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .kpi-card-label {{
        font-size: 0.66rem;
        font-weight: 600;
        color: {COLORS['text_on_light_muted']};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.1rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .kpi-card-delta-positive, .kpi-card-delta-negative {{
        display: inline-flex;
        align-items: center;
        gap: 0.2rem;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 0.12rem 0.5rem;
        border-radius: 999px;
        margin-top: 0.35rem;
        width: fit-content;
    }}
    .kpi-card-delta-positive {{ color: {COLORS['positive']}; background: rgba(34, 197, 94, 0.12); }}
    .kpi-card-delta-negative {{ color: {COLORS['negative']}; background: rgba(239, 68, 68, 0.12); }}
    .kpi-card-delta-positive .material-symbols-outlined,
    .kpi-card-delta-negative .material-symbols-outlined {{ font-size: 12px; }}

    .kpi-card-spark {{
        display: flex;
        align-items: flex-end;
        gap: 3px;
        height: 15px;
        margin-top: 0.55rem;
    }}
    .kpi-card-spark span {{
        width: 6px;
        border-radius: 3px;
        background: var(--kpi-accent);
        display: inline-block;
    }}
    </style>
    """


def _chart_card_css() -> str:
    return f"""
    <style>
    /* Chart cards are real st.container(border=True) wrappers (see
       components/chart_card.py) — restyle that wrapper into a light
       card so the border genuinely wraps the chart. */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: {COLORS['card_bg_light']};
        border: 1px solid {COLORS['card_border_light']} !important;
        border-radius: 14px;
        box-shadow: 0 4px 14px {COLORS['card_shadow_light']};
        padding: 0.9rem 1.1rem 0.3rem 1.1rem;
        margin-bottom: 1.2rem;
    }}
    /* Tighten the vertical gap between title/subtitle/chart inside cards */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlock"] {{
        row-gap: 0.25rem !important;
    }}
    .chart-card-title {{
        font-size: 1rem;
        font-weight: 700;
        color: {COLORS['text_on_light']};
    }}
    .chart-card-subtitle {{
        font-size: 0.78rem;
        color: {COLORS['text_on_light_muted']};
        margin-bottom: 0.2rem;
    }}
    </style>
    """


def _sidebar_css() -> str:
    return f"""
    <style>
    /* Hide Streamlit's own auto-generated page nav at the top of the
       sidebar (built from the pages/ folder) — we render our own list
       via components/sidebar.py, so the built-in one would duplicate
       every page name. The collapse/expand arrow (>) that Streamlit
       draws on the sidebar edge is a separate element and stays working. */
    div[data-testid="stSidebarNav"] {{
        display: none;
    }}

    /* Rounded, floating sidebar "card" look */
    section[data-testid="stSidebar"] {{
        background-color: transparent;
    }}
    section[data-testid="stSidebar"] > div:first-child {{
        background-color: {COLORS['primary']};
        border-radius: 0 18px 18px 0;
        margin: 0.6rem 0 0.6rem 0.4rem;
        padding: 1rem 0.9rem;
    }}
    section[data-testid="stSidebar"] * {{
        color: {COLORS['text_primary']};
    }}

    .sidebar-brand {{
        display: flex;
        align-items: center;
        gap: 0.7rem;
        padding: 0.4rem 0.2rem 1.2rem 0.2rem;
        border-bottom: 1px solid rgba(255,255,255,0.12);
        margin-bottom: 0.8rem;
    }}
    .sidebar-brand-icon {{
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: rgba(255,255,255,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .sidebar-brand-text {{
        font-size: 0.95rem;
        font-weight: 700;
        line-height: 1.2;
    }}
    .sidebar-section-label {{
        font-size: 0.62rem;
        font-weight: 800;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.45);
        margin: 0.9rem 0.2rem 0.3rem 0.2rem;
    }}

    /* Capsule-style nav links — the plain "just page names" list,
       pill-shaped, highlighted on hover; Streamlit marks the active
       page link with aria-current="page" so we highlight that too. */
    section[data-testid="stSidebar"] [data-testid="stPageLink"] {{
        border-radius: 999px !important;
        padding: 0.15rem 0.4rem !important;
        margin: 0.15rem 0 !important;
        transition: background-color 0.15s ease;
    }}
    section[data-testid="stSidebar"] [data-testid="stPageLink"]:hover {{
        background-color: rgba(255,255,255,0.08) !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {{
        background-color: {COLORS['accent']} !important;
        color: #FFFFFF !important;
        border-radius: 999px !important;
        font-weight: 700 !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] * {{
        color: #FFFFFF !important;
    }}

    .sidebar-tagline {{
        margin-top: 1.2rem;
        padding-top: 0.9rem;
        border-top: 1px solid rgba(255,255,255,0.12);
        font-size: 0.72rem;
        color: rgba(255,255,255,0.55);
        line-height: 1.5;
        text-align: center;
    }}
    </style>
    """


def _filter_bar_css() -> str:
    return f"""
    <style>
    /* Horizontal capsule filter row shown just under the topbar. It
       sits directly on the light-grey page background, so — like the
       KPI/chart cards — it uses the light-surface color pair rather
       than the glass-on-navy colors used inside the topbar/sidebar. */
    .filter-bar {{
        background: {COLORS['card_bg_light']};
        border: 1px solid {COLORS['card_border_light']};
        border-radius: 999px;
        padding: 0.6rem 1.2rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 14px {COLORS['card_shadow_light']};
        display: flex;
        align-items: center;
        gap: 1.2rem;
        flex-wrap: wrap;
    }}
    .filter-bar-label {{
        font-size: 0.78rem;
        font-weight: 700;
        color: {COLORS['text_on_light_muted']};
        text-transform: uppercase;
        letter-spacing: 0.04em;
        white-space: nowrap;
    }}
        /* Individual pill buttons — rounded capsules */
    .filter-bar div[data-testid="stButtonGroup"] button {{
        border-radius: 999px !important;
    }}
        /* Selected pills — filled accent background, white text */
    .filter-bar div[data-testid="stButtonGroup"] button[aria-pressed="true"],
    .filter-bar div[data-testid="stButtonGroup"] [data-selected="true"] {{
        background-color: {COLORS['accent']} !important;
        color: #FFFFFF !important;
        border: 1px solid {COLORS['accent']} !important;
    }}
    /* Unselected pills — transparent, muted outline. Note: data-selected is
       only rendered when true, so :not() is used as the catch-all fallback. */
    .filter-bar div[data-testid="stButtonGroup"] button:not([aria-pressed="true"]):not([data-selected="true"]) {{
        background-color: transparent !important;
        color: {COLORS['text_on_light_muted']} !important;
        border: 1px solid {COLORS['card_border_light']} !important;
    }}
    /* Pills that don't fit their column scroll horizontally INSIDE it
       instead of spilling past the card edge (long board lists). */
    .filter-bar div[data-testid="stButtonGroup"] {{
        max-width: 100%;
        overflow-x: auto;
        flex-wrap: nowrap;
        scrollbar-width: thin;
        padding-bottom: 2px;
    }}
    </style>
    """


def _top_boards_css() -> str:
    return f"""
    <style>
    /* Ranked Top-5 boards list — rank badge, name, progress bar, value */
    .topboard-list {{
        display: flex;
        flex-direction: column;
        gap: 0.55rem;
        padding: 0.3rem 0.1rem 0.6rem 0.1rem;
    }}
    .topboard-row {{
        display: flex;
        align-items: center;
        gap: 0.7rem;
    }}
    .topboard-rank {{
        width: 26px;
        height: 26px;
        flex: 0 0 26px;
        border-radius: 8px;
        background: {COLORS['primary']};
        color: {COLORS['text_primary']};
        font-weight: 700;
        font-size: 0.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .topboard-name {{
        flex: 0 0 8.5rem;
        font-weight: 600;
        color: {COLORS['text_on_light']};
        font-size: 0.88rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .topboard-bar {{
        flex: 1 1 auto;
        height: 10px;
        border-radius: 999px;
        background: rgba(59, 130, 246, 0.12);
        overflow: hidden;
    }}
    .topboard-fill {{
        height: 100%;
        border-radius: 999px;
        background: {COLORS['accent']};
    }}
    .topboard-value {{
        flex: 0 0 3.6rem;
        text-align: right;
        font-weight: 700;
        color: {COLORS['accent']};
        font-size: 0.88rem;
    }}
    .topboard-year {{
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: {COLORS['text_on_light_muted']};
        margin: 0.9rem 0 0.3rem 0;
    }}
    .topboard-year:first-child {{
        margin-top: 0;
    }}
    .topboard-root {{
        min-height: 452px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 0.2rem 0.1rem;
    }}
    </style>
    """


def _page_header_css() -> str:
    return f"""
    <style>
    /* Heading + year selector directly under the navy topbar. The heading
       tells the user which year to pick; the 2026/2025 pills sit on the
       right. Deliberately minimal — the topbar already shows the page
       title, so nothing is duplicated here. */
    .page-header-title {{
        font-size: 1.5rem;
        font-weight: 800;
        color: {COLORS['text_on_light']};
        line-height: 1.25;
        letter-spacing: -0.01em;
        margin: 0.2rem 0 1.2rem 0;
    }}
        /* Right-align the year pills inside the header's last column. */
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child div[data-testid="stButtonGroup"] {{
        justify-content: flex-end;
    }}
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child div[data-testid="stButtonGroup"] button {{
        border-radius: 999px !important;
    }}
    </style>
    """


def _prov_tiles_css() -> str:
    return f"""
    <style>
    /* Provincial Comparison tiles — silhouette-style stat cards, one per
       province with board data in the dataset. */
    .prov-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 0.8rem;
        padding: 0.2rem 0.1rem 0.5rem 0.1rem;
    }}
    .prov-tile {{
        background: {COLORS['card_bg_light']};
        border: 1px solid {COLORS['card_border_light']};
        border-radius: 14px;
        padding: 0.9rem 1rem;
        box-shadow: 0 4px 14px {COLORS['card_shadow_light']};
    }}
    .prov-tile-name {{
        font-size: 0.85rem;
        font-weight: 700;
        color: {COLORS['text_on_light']};
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }}
    .prov-tile-name .material-symbols-outlined {{
        font-size: 18px;
        color: {COLORS['accent']};
    }}
    .prov-tile-value {{
        font-size: 1.35rem;
        font-weight: 800;
        color: {COLORS['text_on_light']};
        margin-top: 0.35rem;
        line-height: 1;
    }}
    .prov-tile-sub {{
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: {COLORS['text_on_light_muted']};
        margin-top: 0.3rem;
    }}
    .prov-tile-bar {{
        height: 5px;
        border-radius: 999px;
        background: rgba(59, 130, 246, 0.12);
        margin-top: 0.6rem;
        overflow: hidden;
    }}
    .prov-tile-fill {{
        height: 100%;
        border-radius: 999px;
        background: {COLORS['accent']};
    }}
    </style>
    """


def inject_css() -> None:
    """Call once per page, right after st.set_page_config()."""
    st.markdown(_fonts_css(), unsafe_allow_html=True)
    st.markdown(_page_base_css(), unsafe_allow_html=True)
    st.markdown(_topbar_css(), unsafe_allow_html=True)
    st.markdown(_kpi_card_css(), unsafe_allow_html=True)
    st.markdown(_chart_card_css(), unsafe_allow_html=True)
    st.markdown(_sidebar_css(), unsafe_allow_html=True)
    st.markdown(_filter_bar_css(), unsafe_allow_html=True)
    st.markdown(_top_boards_css(), unsafe_allow_html=True)
    st.markdown(_page_header_css(), unsafe_allow_html=True)
    st.markdown(_prov_tiles_css(), unsafe_allow_html=True)