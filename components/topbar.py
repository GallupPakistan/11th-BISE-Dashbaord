"""
components/topbar.py

Renders the full-page header as a navy card: logo badge (top left),
breadcrumb with home icon, big page title, subtitle, a calendar-icon
"Last updated" line, decorative dotted pattern, and a quick stat badge
(value + label + icon) on the right.

Structure/classes are unchanged from the reference implementation —
only the brand name/icon/subtitle defaults come from config/settings.py
so re-branding the whole app means editing ONE line there, not this file.
"""

import streamlit as st
from config.settings import APP_NAME, APP_SUBTITLE, APP_ICON, LAST_UPDATED


def render_topbar(
    active_page: str,
    subtitle: str,
    last_updated: str = LAST_UPDATED,
    stat_label: str = "",
    stat_value: str = "",
    stat_icon: str = "account_balance",
    brand_name: str = APP_NAME,
    brand_sub: str = APP_SUBTITLE,
    brand_icon: str = APP_ICON,
) -> None:
    stat_html = ""
    if stat_label and stat_value:
        stat_html = (
            f'<div class="hec-topbar-stat">'
            f'<div class="hec-topbar-stat-icon-circle"><span class="material-symbols-outlined">{stat_icon}</span></div>'
            f'<div class="hec-topbar-stat-vsep"></div>'
            f'<div class="hec-topbar-stat-text">'
            f'<div class="hec-topbar-stat-value">{stat_value}</div>'
            f'<div class="hec-topbar-stat-label">{stat_label}</div>'
            f'</div>'
            f'</div>'
        )

    # Note: keep this string flushed to the left margin to prevent markdown code-block formatting!
    topbar_html = f"""<div class="hec-topbar">
<div class="hec-topbar-dots"></div>
<div class="hec-topbar-watermark"><span class="material-symbols-outlined">{brand_icon}</span></div>

<div class="hec-topbar-toprow">
<div class="hec-topbar-lastupdated-pill">
<span class="material-symbols-outlined">calendar_month</span>
<span>Last updated: <b>{last_updated}</b></span>
</div>
<div class="hec-topbar-brand">
<div class="hec-topbar-logo-circle">
<span class="material-symbols-outlined">{brand_icon}</span>
</div>
<div class="hec-topbar-brand-text">
<div class="hec-topbar-brand-name">{brand_name}</div>
<div class="hec-topbar-brand-sub">{brand_sub}</div>
</div>
</div>
<div class="hec-topbar-vsep"></div>
<div class="hec-topbar-crumbs">
<div class="hec-topbar-crumb-icon-badge">
<span class="material-symbols-outlined">home</span>
</div>
<span class="hec-topbar-sep">/</span>
<span class="hec-topbar-crumb">Dashboard</span>
<span class="hec-topbar-sep">/</span>
<span class="hec-topbar-crumb hec-topbar-current">{active_page}</span>
</div>
</div>

<div class="hec-topbar-bottomrow">
<div class="hec-topbar-left">
<div class="hec-topbar-title-wrapper">
<div class="hec-topbar-accent-bar"></div>
<div class="hec-topbar-title">{active_page}</div>
</div>
<div class="hec-topbar-subtitle">{subtitle}</div>
</div>
<div class="hec-topbar-right">{stat_html}</div>
</div>
</div>"""

    st.markdown(topbar_html, unsafe_allow_html=True)
