# BISE 11th Class (HSSC Part-I) Dashboard (2024-2025)

## Setup
1. Open this folder in VS Code (or any terminal).
2. Create a virtual env (optional) and install dependencies:
   pip install -r requirements.txt
3. Keep `11th_Class_Boards_Results_Combined.xlsx` in the same folder as `app.py`.
4. Run:
   streamlit run app.py

## What's inside
- `app.py` — entry point / sidebar router (Overview, Analysis pages, 15 board pages)
- `data_loader.py` — reads the workbook's 4 "Combined" sheets (Overview,
  GroupWise, SubjectWise, DistrictWise) into tidy DataFrames. Nothing is
  estimated or interpolated: if a board doesn't publish a figure (e.g. no
  district-wise breakdown, no subject list for a given year), the
  corresponding chart/table for that board is simply empty, with a note
  saying so — never filled in.
- `common.py` — shared design tokens, CSS, and chart-factory functions
  (same navy/teal visual language as the companion 10th-grade dashboard)
- `views_overview.py`, `views_board.py`, `views_compare.py` — page rendering logic
- `board_page_helper.py` + `pages/10_*.py` .. `pages/24_*.py` — one page per board
- `pages/1_Board_Explorer.py` .. `pages/7_District_Wise.py` — cross-board analysis pages:
  Board Explorer, Compare Boards, Gender Analysis, Group-wise Analysis
  (Pre-Medical / Pre-Engineering / Humanities / Commerce / General Science —
  unique to 11th, since SSC has no subject groups), Subject Analysis,
  Province Wise, District Wise (only the 6 boards that publish it)

## Data notes
- Years covered: 2024 and 2025 only (the source workbook has no 2026 data).
- Not every board has both years (e.g. Bannu and Kohat: 2025 only; Peshawar: 2024 only).
- The workbook's own `Notes` column (caveats about how a figure was derived,
  partial data, etc.) is surfaced directly on each board's page under
  "Data notes from the source workbook" — read these before citing a number.
