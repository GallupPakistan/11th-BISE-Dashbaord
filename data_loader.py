"""
data_loader.py
Loads the 11th Class (HSSC Part-I) Results — Combined workbook and exposes
it as tidy pandas DataFrames.

Unlike the 10th-grade workbook (raw, per-board sheets scraped from PDFs in
wildly different layouts), this workbook already ships 4 pre-built
"Combined" long-format tables — one row per Board x Year x dimension — plus
one raw detail sheet per board/year (kept in the workbook for reference,
not re-parsed here since the 4 Combined sheets already roll them up).

Every function here only reads, filters, and aggregates numbers that are
already in the workbook. Nothing is estimated or assumed. Where the
workbook itself doesn't have a figure for a board (e.g. no district-wise
breakdown, no subject list, no Male/Female split for a given year), the
corresponding DataFrame simply comes back empty for that board/year — it
is never filled in or guessed.
"""
from pathlib import Path
import re

import pandas as pd
import streamlit as st

BASE = Path(__file__).parent
WORKBOOK = BASE / "11th_Class_Boards_Results_Combined.xlsx"

SHEET_OVERVIEW = "Combined Overview"
SHEET_GROUPWISE = "Combined GroupWise"
SHEET_SUBJECTWISE = "Combined SubjectWise"
SHEET_DISTRICTWISE = "Combined DistrictWise"

# Short board name as printed in the workbook -> full display name used
# throughout the UI (same 15 BISE boards as the 10th-grade dashboard).
BOARD_DISPLAY = {
    "Abbottabad": "BISE Abbottabad",
    "Bahawalpur": "BISE Bahawalpur",
    "Bannu": "BISE Bannu",
    "DG Khan": "BISE Dera Ghazi Khan",
    "Faisalabad": "BISE Faisalabad",
    "Gujranwala": "BISE Gujranwala",
    "Kohat": "BISE Kohat",
    "Lahore": "BISE Lahore",
    "Mardan": "BISE Mardan",
    "Peshawar": "BISE Peshawar",
    "Rawalpindi": "BISE Rawalpindi",
    "Sahiwal": "BISE Sahiwal",
    "Sargodha": "BISE Sargodha",
    "Swat": "BISE Swat",
    "FBISE (Islamabad)": "FBISE",
}
BOARD_SHORT = {v: k for k, v in BOARD_DISPLAY.items()}
ALL_BOARD_NAMES = sorted(BOARD_DISPLAY.values())

# Province each BISE board sits in — static metadata (BISE boards are
# organized by province/territory; this doesn't come from the results
# workbook and doesn't change year to year).
BOARD_PROVINCE = {
    "BISE Peshawar": "KPK", "BISE Swat": "KPK", "BISE Bannu": "KPK",
    "BISE Abbottabad": "KPK", "BISE Mardan": "KPK", "BISE Kohat": "KPK",
    "BISE Sargodha": "Punjab", "BISE Dera Ghazi Khan": "Punjab", "BISE Rawalpindi": "Punjab",
    "BISE Faisalabad": "Punjab", "BISE Lahore": "Punjab", "BISE Bahawalpur": "Punjab",
    "BISE Gujranwala": "Punjab", "BISE Sahiwal": "Punjab",
    "FBISE": "Federal (Islamabad)",
}
PROVINCE_COLORS = {"KPK": "#2E7D32", "Punjab": "#1565C0", "Federal (Islamabad)": "#8B5CF6", "Other": "#94A3B8"}

# ── Subject-name normalization ──────────────────────────────────────────────
# Different boards/years label the same paper differently — a trailing
# "(Regular)" / "(Pre-Med)" / "(Compulsory)" / "(Elective)" / "(... overall)"
# group qualifier in parens, a bare trailing "Compulsory"/"Elective" word
# (e.g. "Urdu Compulsory" vs "Urdu", "Islamiyat Compulsory" vs "Islamiyat
# Elective"), a "-I" part-number suffix, a plain spelling/typo variant (e.g.
# "Mutaliae-Quran-e-Hakeem" vs "Mutalia-e-Quran Hakeem"), or an outright
# different name for the same paper (e.g. "Islamic Education" / "Islamic
# Studies" / "Islamiyat" are all the compulsory religious-studies paper).
# None of that changes what paper it is, so it's all folded into one
# canonical name before anything is grouped or charted.
SUBJECT_ALIASES = {
    "business math": "Mathematics",
    "business mathematics": "Mathematics",
    "health & phy. education": "Health & Physical Education",
    "hpe": "Health & Physical Education",
    "islamyat": "Islamiyat",
    "islamic education": "Islamiyat",
    "islamic studies": "Islamiyat",
    "islamic history": "Islamiyat",
    "mutalia-e-quran hakeem": "Mutalia-e-Quran Hakeem",
    "mutaliae quran-e-hakeem": "Mutalia-e-Quran Hakeem",
    "mutaliae-quran-e-hakeem": "Mutalia-e-Quran Hakeem",
    "mutalia quran": "Mutalia-e-Quran Hakeem",
    "pakistan study": "Pakistan Studies",
    "pashtu": "Pashto",
    "principles of economics": "Economics",
}


def normalize_subject(name) -> str:
    s = str(name).strip()
    s = re.sub(r"\s*\([^)]*\)", "", s)                          # drop any "(...)" group qualifier
    s = re.sub(r"-I$", "", s)                                    # drop a trailing "-I" part number
    s = re.sub(r"\s+(Compulsory|Elective)$", "", s, flags=re.I)  # drop a bare trailing Compulsory/Elective qualifier
    s = re.sub(r"\s+", " ", s).strip()
    return SUBJECT_ALIASES.get(s.lower(), s)


# ── District-name normalization ─────────────────────────────────────────────
# Same idea as subjects: different year's gazette for the same board can spell
# a district differently ("Muzaffargarh" vs "Muzaffar Garh", "Kot Addu" vs
# "Kot Adu") — fold those into one canonical name so a district isn't double
# counted as two separate rows.
DISTRICT_ALIASES = {
    "muzaffar garh": "Muzaffargarh",
    "kot adu": "Kot Addu",
}


def normalize_district(name) -> str:
    s = re.sub(r"\s+", " ", str(name).strip())
    return DISTRICT_ALIASES.get(s.lower(), s)

_NUMERIC_OVERVIEW_COLS = [
    "Total Applied", "Total Appeared", "Total Passed", "Overall Pass %",
    "Male Appeared", "Male Passed", "Male Pass %",
    "Female Appeared", "Female Passed", "Female Pass %",
]


def workbook_exists() -> bool:
    return WORKBOOK.exists()


@st.cache_data(show_spinner="Loading 11th class results workbook...")
def load_workbook():
    """Read the 4 Combined sheets once (cached), translate the Board column
    to full display names, coerce numeric columns, and return a dict of
    DataFrames keyed overview / groupwise / subjectwise / districtwise."""
    if not WORKBOOK.exists():
        raise FileNotFoundError(str(WORKBOOK))

    xl = pd.ExcelFile(WORKBOOK)

    def _read(name):
        df = pd.read_excel(xl, sheet_name=name, header=2)
        df = df.dropna(how="all").reset_index(drop=True)
        df["Board"] = df["Board"].map(BOARD_DISPLAY).fillna(df["Board"])
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
        return df

    overview = _read(SHEET_OVERVIEW)
    groupwise = _read(SHEET_GROUPWISE)
    subjectwise = _read(SHEET_SUBJECTWISE)
    districtwise = _read(SHEET_DISTRICTWISE)

    subjectwise["Subject"] = subjectwise["Subject"].map(normalize_subject)
    districtwise["District"] = districtwise["District"].map(normalize_district)

    for col in _NUMERIC_OVERVIEW_COLS:
        overview[col] = pd.to_numeric(overview[col], errors="coerce")
    for df in (groupwise, subjectwise, districtwise):
        for col in ("Appeared", "Passed", "Pass %"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return {"overview": overview, "groupwise": groupwise, "subjectwise": subjectwise, "districtwise": districtwise}


def get_available_years(data) -> list:
    return sorted({int(y) for y in data["overview"]["Year"].dropna().unique()})


def filter_df(df: pd.DataFrame, board=None, year=None) -> pd.DataFrame:
    out = df
    if board is not None:
        wanted = [board] if isinstance(board, str) else list(board)
        out = out[out["Board"].isin(wanted)]
    if year is not None:
        out = out[out["Year"] == year]
    return out.copy()


def board_totals(data, board=None, year=None) -> dict:
    """Total Applied/Appeared/Passed/Pass% (+ Male/Female splits + source
    Notes), summed straight off the Overview sheet."""
    df = filter_df(data["overview"], board=board, year=year)
    if df.empty:
        return {"applied": 0, "appeared": 0, "passed": 0, "failed": 0, "pass_pct": 0.0,
                "male_appeared": 0, "male_passed": 0, "female_appeared": 0, "female_passed": 0,
                "notes": []}
    appeared = int(df["Total Appeared"].sum(skipna=True) or 0)
    passed = int(df["Total Passed"].sum(skipna=True) or 0)
    applied = int(df["Total Applied"].sum(skipna=True) or 0)
    male_app = int(df["Male Appeared"].sum(skipna=True) or 0)
    male_pass = int(df["Male Passed"].sum(skipna=True) or 0)
    female_app = int(df["Female Appeared"].sum(skipna=True) or 0)
    female_pass = int(df["Female Passed"].sum(skipna=True) or 0)
    failed = max(appeared - passed, 0)
    pass_pct = round(100 * passed / appeared, 2) if appeared else 0.0
    notes = [str(n).strip() for n in df["Notes"].dropna().tolist() if str(n).strip()]
    return {"applied": applied, "appeared": appeared, "passed": passed, "failed": failed,
            "pass_pct": pass_pct, "male_appeared": male_app, "male_passed": male_pass,
            "female_appeared": female_app, "female_passed": female_pass, "notes": notes}


def gender_df_for(data, board=None, year=None) -> pd.DataFrame:
    """Male/Female Appeared/Passed/Failed/Pass % from the Overview sheet's
    own gender columns — the most reliable gender source in the workbook.
    A gender is only included if the workbook actually reports it."""
    df = filter_df(data["overview"], board=board, year=year)
    if df.empty:
        return pd.DataFrame(columns=["Gender", "Appeared", "Passed", "Failed", "Pass %"])
    m_app = df["Male Appeared"].sum(skipna=True)
    m_pass = df["Male Passed"].sum(skipna=True)
    f_app = df["Female Appeared"].sum(skipna=True)
    f_pass = df["Female Passed"].sum(skipna=True)
    rows = []
    if pd.notna(m_app) and m_app > 0:
        rows.append({"Gender": "Male", "Appeared": int(m_app), "Passed": int(m_pass or 0)})
    if pd.notna(f_app) and f_app > 0:
        rows.append({"Gender": "Female", "Appeared": int(f_app), "Passed": int(f_pass or 0)})
    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(columns=["Gender", "Appeared", "Passed", "Failed", "Pass %"])
    out["Failed"] = (out["Appeared"] - out["Passed"]).clip(lower=0)
    out["Pass %"] = (100 * out["Passed"] / out["Appeared"].replace(0, pd.NA)).astype(float).round(2)
    return out


_GENDER_WORDS = {"boys": "Male", "male": "Male", "girls": "Female", "female": "Female"}


def _parse_category(value):
    """'Regular Boys' -> ('Male', 'Regular'); 'Private Female' -> ('Female',
    'Private'); 'Total' -> (None, None); 'Boys' -> ('Male', None)."""
    if not isinstance(value, str):
        return None, None
    v = value.strip().lower()
    if v == "total":
        return None, None
    kind = "Regular" if "regular" in v else ("Private" if "private" in v else None)
    gender = None
    for word, mapped in _GENDER_WORDS.items():
        if word in v:
            gender = mapped
            break
    return gender, kind


_GROUP_FOLD = {
    "General/Computer Science": "General Science", "Computer/General Science": "General Science",
    "General Science/Pre-Computer": "General Science", "Science General": "General Science",
    "Humanities & Other Groups": "Humanities & Others", "Pre-Home Eco.": "Home Economics",
}


def _clean_group(name):
    """Fold '(Regular)'/'(Private)' qualifiers and near-duplicate spellings
    of the same group into one canonical name (e.g. 'Pre-Medical (Regular)'
    and 'Pre-Medical (Private)' both become 'Pre-Medical'), so totals and
    charts aren't fragmented by wording alone."""
    if not isinstance(name, str):
        return name
    base = name.split("(")[0].strip()
    return _GROUP_FOLD.get(base, base)


def groupwise_raw_for(data, board=None, year=None) -> pd.DataFrame:
    return filter_df(data["groupwise"], board=board, year=year)


def type_df_for(data, board=None, year=None) -> pd.DataFrame:
    """Regular vs Private — only present where the workbook's Group-wise
    Category field spells it out (a subset of boards; most report gender
    only). Empty means the workbook doesn't publish this split."""
    gw = filter_df(data["groupwise"], board=board, year=year)
    if gw.empty:
        return pd.DataFrame(columns=["Candidate Type", "Appeared", "Passed", "Failed", "Pass %"])
    rows = []
    for _, r in gw.iterrows():
        _, kind = _parse_category(r["Category (Gender/Type)"])
        if kind is None:
            continue
        rows.append({"Candidate Type": kind, "Appeared": r["Appeared"], "Passed": r["Passed"]})
    if not rows:
        return pd.DataFrame(columns=["Candidate Type", "Appeared", "Passed", "Failed", "Pass %"])
    out = pd.DataFrame(rows).groupby("Candidate Type", as_index=False)[["Appeared", "Passed"]].sum()
    out["Failed"] = (out["Appeared"] - out["Passed"]).clip(lower=0)
    out["Pass %"] = (100 * out["Passed"] / out["Appeared"].replace(0, pd.NA)).astype(float).round(2)
    return out


def group_gender_df_for(data, board=None, year=None) -> pd.DataFrame:
    """Group (Pre-Medical / Humanities / ...) x Gender, folding away the
    Regular/Private split when present. Rows where the workbook only gives
    a combined 'Total' (no gender) are excluded here by design."""
    gw = filter_df(data["groupwise"], board=board, year=year)
    if gw.empty:
        return pd.DataFrame(columns=["Group", "Gender", "Appeared", "Passed", "Pass %"])
    rows = []
    for _, r in gw.iterrows():
        gender, _ = _parse_category(r["Category (Gender/Type)"])
        if gender is None:
            continue
        rows.append({"Group": _clean_group(r["Group"]), "Gender": gender,
                     "Appeared": r["Appeared"], "Passed": r["Passed"]})
    if not rows:
        return pd.DataFrame(columns=["Group", "Gender", "Appeared", "Passed", "Pass %"])
    out = pd.DataFrame(rows).groupby(["Group", "Gender"], as_index=False)[["Appeared", "Passed"]].sum()
    out["Pass %"] = (100 * out["Passed"] / out["Appeared"].replace(0, pd.NA)).astype(float).round(2)
    return out


def group_totals_df_for(data, board=None, year=None) -> pd.DataFrame:
    """Group-level Appeared/Passed/Pass %, folding Regular+Private and
    Male+Female together."""
    gw = filter_df(data["groupwise"], board=board, year=year).copy()
    if gw.empty:
        return pd.DataFrame(columns=["Group", "Appeared", "Passed", "Pass %"])
    gw["Group"] = gw["Group"].map(_clean_group)
    out = gw.groupby("Group", as_index=False)[["Appeared", "Passed"]].sum()
    out["Pass %"] = (100 * out["Passed"] / out["Appeared"].replace(0, pd.NA)).astype(float).round(2)
    return out.sort_values("Pass %", ascending=False)


def subject_df_for(data, board=None, year=None) -> pd.DataFrame:
    df = filter_df(data["subjectwise"], board=board, year=year)
    if df.empty:
        return pd.DataFrame(columns=["Subject", "Appeared", "Passed", "Pass %"])
    out = df.groupby("Subject", as_index=False)[["Appeared", "Passed"]].sum()
    out["Pass %"] = (100 * out["Passed"] / out["Appeared"].replace(0, pd.NA)).astype(float).round(2)
    return out.sort_values("Pass %", ascending=False)


def district_df_for(data, board=None, year=None) -> pd.DataFrame:
    df = filter_df(data["districtwise"], board=board, year=year)
    if df.empty:
        return pd.DataFrame(columns=["District", "Appeared", "Passed", "Pass %"])
    out = df.groupby("District", as_index=False)[["Appeared", "Passed"]].sum()
    out["Pass %"] = (100 * out["Passed"] / out["Appeared"].replace(0, pd.NA)).astype(float).round(2)
    return out.sort_values("Pass %", ascending=False)


def yearly_trend_df_for(data, board) -> pd.DataFrame:
    df = filter_df(data["overview"], board=board).sort_values("Year")
    if df.empty:
        return pd.DataFrame(columns=["Year", "Appeared", "Passed", "Failed", "Pass %"])
    out = df.groupby("Year", as_index=False)[["Total Appeared", "Total Passed"]].sum()
    out = out.rename(columns={"Total Appeared": "Appeared", "Total Passed": "Passed"})
    out["Failed"] = (out["Appeared"] - out["Passed"]).clip(lower=0)
    out["Pass %"] = (100 * out["Passed"] / out["Appeared"].replace(0, pd.NA)).astype(float).round(2)
    return out


def board_rankings_df(data, year=None) -> pd.DataFrame:
    df = data["overview"] if year is None else filter_df(data["overview"], year=year)
    out = df.groupby("Board", as_index=False)[["Total Appeared", "Total Passed"]].sum()
    out = out.rename(columns={"Total Appeared": "Appeared", "Total Passed": "Passed"})
    out["Failed"] = (out["Appeared"] - out["Passed"]).clip(lower=0)
    out["Pass %"] = (100 * out["Passed"] / out["Appeared"].replace(0, pd.NA)).astype(float).round(2)
    return out.sort_values("Pass %", ascending=False)


def boards_with_district_data(data) -> list:
    return sorted(data["districtwise"]["Board"].dropna().unique().tolist())


def boards_with_subject_data(data) -> list:
    return sorted(data["subjectwise"]["Board"].dropna().unique().tolist())


def boards_with_group_data(data) -> list:
    return sorted(data["groupwise"]["Board"].dropna().unique().tolist())
