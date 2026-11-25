import pandas as pd
import os
import streamlit as st

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "Training_data.xlsx")

# Sheet names in the new Training_data.xlsx (matched ignoring leading/trailing spaces)
VAYU_SHEET = "Cloud VM Price"
HANA_SHEET = "Hana VM Price"
OLVM_SHEET = "OLVM Price"

# Column positions (0-based) in each sheet. Vayu is unchanged from the old layout.
VAYU_OS_COLUMNS = {
    "Linux": {"Hourly- ppu": 6, "1 year Reserved": 7, "3 Year Reserved": 8},
    "Windows": {"Hourly- ppu": 9, "1 year Reserved": 10, "3 Year Reserved": 11},
    "SUSE- Linux": {"Hourly- ppu": 12, "1 year Reserved": 13, "3 Year Reserved": 14},
    "SLES for SAP": {"Hourly- ppu": 15, "1 year Reserved": 16, "3 Year Reserved": 17},
    "Redhat Enterprise Linux": {"Hourly- ppu": 18, "1 year Reserved": 19, "3 Year Reserved": 20},
    "RHEL for SAP": {"Hourly- ppu": 21, "1 year Reserved": 22, "3 Year Reserved": 23},
}

HANA_OS_COLUMNS = {
    "Linux": {"Hourly- ppu": 5, "1 year Reserved": 6, "3 Year Reserved": 7},
    "SUSE- Linux": {"Hourly- ppu": 8, "1 year Reserved": 9, "3 Year Reserved": 10},
    "RHEL for SAP": {"Hourly- ppu": 11, "1 year Reserved": 12, "3 Year Reserved": 13},
}

OLVM_OS_COLUMNS = {
    "Linux": {"Hourly- ppu": 5, "1 year Reserved": 6, "3 Year Reserved": 7},
}


# ── Load each sheet ONCE and cache it ──
@st.cache_data
def _load_sheet(sheet_name):
    """Reads one sheet exactly once. Matches the name ignoring stray spaces."""
    xls = pd.ExcelFile(DATA_PATH)
    match = [s for s in xls.sheet_names if s.strip().lower() == sheet_name.strip().lower()]
    if not match:
        raise ValueError(
            f"Sheet '{sheet_name}' not found in {os.path.basename(DATA_PATH)}. "
            f"Available sheets: {xls.sheet_names}"
        )
    return pd.read_excel(xls, sheet_name=match[0], header=None)


def _parse_rows(df, service_type, os_columns):
    rows = []
    for _, row in df.iterrows():
        if str(row[0]).strip() == service_type:
            entry = {
                "Flavour": str(row[1]).strip(),
                "vCPU": row[2],
                "RAM (GB)": row[3],
                "Root Disk (GB)": row[4],
            }
            if service_type == "Vayu Cloud- Open Stack":
                entry["Root Disk Windows (GB)"] = row[4]
                entry["Root Disk Other OS (GB)"] = row[5]
            for os_name, cols in os_columns.items():
                for tier, col_idx in cols.items():
                    val = row[col_idx]
                    entry[f"{os_name}__{tier}"] = val if pd.notna(val) else None
            rows.append(entry)
    return pd.DataFrame(rows)


@st.cache_data
def load_vayu_cloud():
    return _parse_rows(_load_sheet(VAYU_SHEET), "Vayu Cloud- Open Stack", VAYU_OS_COLUMNS)


@st.cache_data
def load_hana_grid():
    return _parse_rows(_load_sheet(HANA_SHEET), "HANA Grid", HANA_OS_COLUMNS)


@st.cache_data
def load_olvm():
    return _parse_rows(_load_sheet(OLVM_SHEET), "OLVM", OLVM_OS_COLUMNS)


@st.cache_data
def get_vayu_flavours():
    return sorted(load_vayu_cloud()["Flavour"].tolist())


@st.cache_data
def get_hana_flavours():
    return sorted(load_hana_grid()["Flavour"].tolist())


@st.cache_data
def get_olvm_flavours():
    return sorted(load_olvm()["Flavour"].tolist())


@st.cache_data
def get_vayu_row(flavour):
    df = load_vayu_cloud()
    result = df[df["Flavour"] == flavour]
    return None if result.empty else result.iloc[0]


@st.cache_data
def get_hana_row(flavour):
    df = load_hana_grid()
    result = df[df["Flavour"] == flavour]
    return None if result.empty else result.iloc[0]


@st.cache_data
def get_olvm_row(flavour):
    df = load_olvm()
    result = df[df["Flavour"] == flavour]
    return None if result.empty else result.iloc[0]
