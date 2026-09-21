"""
config/settings.py

Single source of truth for text/identity constants used across the whole
dashboard. Change the app name, icon, or board page list ONLY here — every
page/component reads from this file.

(Data constants — board/province maps, sheet names, workbook path — stay in
data_loader.py, exactly like before.)
"""

# ---------------------------------------------------------------------------
# App identity (used by the topbar / sidebar / browser tab)
# ---------------------------------------------------------------------------
APP_NAME = "11th Class Results"
APP_SUBTITLE = "Analytics Dashboard"
APP_ICON = "school"           # Google "Material Symbols Outlined" icon name
PAGE_ICON = "🎓"              # browser tab favicon (emoji, used in st.set_page_config)
LAST_UPDATED = "21 Sep 2026"  # update whenever the underlying data file changes

# ---------------------------------------------------------------------------
# Years covered by the 11th-class (HSSC Part-I) workbook — newest first.
# ---------------------------------------------------------------------------
YEARS = [2025, 2024]

# ---------------------------------------------------------------------------
# The 15 single-board pages (path + sidebar label), in display order.
# Rendered at the bottom of the sidebar under an "ALL BOARDS" section label.
# ---------------------------------------------------------------------------
BOARD_PAGES = [
    ("pages/10_BISE_Abbottabad.py", "BISE Abbottabad"),
    ("pages/11_BISE_Bahawalpur.py", "BISE Bahawalpur"),
    ("pages/12_BISE_Bannu.py", "BISE Bannu"),
    ("pages/13_BISE_Dera_Ghazi_Khan.py", "BISE Dera Ghazi Khan"),
    ("pages/14_BISE_Faisalabad.py", "BISE Faisalabad"),
    ("pages/15_BISE_Gujranwala.py", "BISE Gujranwala"),
    ("pages/16_BISE_Kohat.py", "BISE Kohat"),
    ("pages/17_BISE_Lahore.py", "BISE Lahore"),
    ("pages/18_BISE_Mardan.py", "BISE Mardan"),
    ("pages/19_BISE_Peshawar.py", "BISE Peshawar"),
    ("pages/20_BISE_Rawalpindi.py", "BISE Rawalpindi"),
    ("pages/21_BISE_Sahiwal.py", "BISE Sahiwal"),
    ("pages/22_BISE_Sargodha.py", "BISE Sargodha"),
    ("pages/23_BISE_Swat.py", "BISE Swat"),
    ("pages/24_FBISE.py", "FBISE"),
]