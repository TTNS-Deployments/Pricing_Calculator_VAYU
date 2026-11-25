import pandas as pd
from data_loader import get_vayu_row, get_hana_row, get_olvm_row

# Updated from Training_data.xlsx -> "Storage price" sheet (Nov 2026)
STORAGE_PRICES = {
    "SSD-1": 4.17,
    "SSD-2": 8.501695,
    "SSD-3": 7.71,
    "SSD-4": 15.437288,
    "SSD-5": 12.855,
    "NAS": 8.865,
    "CIFS": 8.865,
    "Single Site Value Tier": 1.125,
    "Dual Site Value Tier": 2.46,
    "Dual Site Resilience Tier": 2.715,
    "High Performance Object Storage": 3.66,
}

BACKUP_PRICES = {
    "Value Based": 2.19,
    "Resilient": 4.11,
    "Geo-Resilient": 4.665,
    "Commvault": 5.22,
    "None": 0,
}

# Source: "DC to DC Connectivity" sheet. Basic firewall = 2765.20564 per month
# for 20 Mbps. app.py charges FIREWALL_PRICES x Mbps, so the price is stored per
# Mbps (assumes linear pricing; only the 20 Mbps data point exists).
# TODO: confirm with the pricing team.
FIREWALL_PRICES = {
    "None": 0,
    "Basic": 2765.20564 / 20,
}

PUBLIC_IP_PRICE = 1350  # per IP per month (Excel: DC to DC Connectivity, IPv4)

# The Excel guideline: hourly (ppu) prices are per hour, everything else is per
# month. Quotes are monthly, so hourly VM prices are converted at 730 hours.
HOURS_PER_MONTH = 730

# The Excel's Vayu "RHEL for SAP" middle column is headed "Daily", not
# "1 year Reserved" (a data error: it holds hourly x 24.57). In the same sheet
# every 1-year price is a fixed fraction of (hourly x 730): 0.816 for Linux,
# Windows, SUSE and RHEL, and 0.81 for SLES for SAP. RHEL for SAP is also an SAP
# licence, so its 1-year price is derived the same way as SLES for SAP (0.81).
# If the Excel column is ever corrected, set RHEL_SAP_1YR_FROM_HOURLY = False.
RHEL_SAP_1YR_FROM_HOURLY = True
RHEL_SAP_1YR_FACTOR = 0.81

VAYU_OS_OPTIONS = [
    "Linux",
    "Windows",
    "SUSE- Linux",
    "SLES for SAP",
    "Redhat Enterprise Linux",
    "RHEL for SAP",
]

HANA_OS_OPTIONS = [
    "Linux",
    "SUSE- Linux",
    "RHEL for SAP",
]

OLVM_OS_OPTIONS = [
    "Linux",
]

PRICING_TIERS = [
    "Hourly- ppu",
    "1 year Reserved",
    "3 Year Reserved",
]


def _missing(value):
    """True for None or NaN (pandas turns None into NaN in numeric columns)."""
    return value is None or pd.isna(value)


def _monthly(price, pricing_tier):
    """Hourly (ppu) prices -> monthly. Reserved prices are already monthly."""
    if pricing_tier == "Hourly- ppu":
        return price * HOURS_PER_MONTH
    return price


def calculate_vayu_price(flavour, os_type, pricing_tier, quantity,
                          storage_type, storage_gb,
                          backup_type, backup_gb,
                          firewall_type, public_ips):
    row = get_vayu_row(flavour)
    if row is None:
        return None

    key = f"{os_type}__{pricing_tier}"
    unit_vm_price = row.get(key, None)

    if RHEL_SAP_1YR_FROM_HOURLY and os_type == "RHEL for SAP" and pricing_tier == "1 year Reserved":
        hourly = row.get("RHEL for SAP__Hourly- ppu", None)
        unit_vm_price = None if _missing(hourly) else hourly * HOURS_PER_MONTH * RHEL_SAP_1YR_FACTOR

    if _missing(unit_vm_price):
        return None
    unit_vm_price = _monthly(unit_vm_price, pricing_tier)

    # Storage cost
    storage_price_per_gb = STORAGE_PRICES.get(storage_type, 0)
    storage_cost = storage_price_per_gb * storage_gb

    # Backup cost
    backup_price_per_gb = BACKUP_PRICES.get(backup_type, 0)
    backup_cost = backup_price_per_gb * backup_gb

    # Firewall cost
    firewall_cost = FIREWALL_PRICES.get(firewall_type, 0)

    # Public IP cost
    public_ip_cost = public_ips * PUBLIC_IP_PRICE

    # Per unit total
    unit_total = unit_vm_price + storage_cost + backup_cost + firewall_cost + public_ip_cost

    # Final total
    total_price = unit_total * quantity

    breakdown = {
        "VM Price (per unit)": round(unit_vm_price, 2),
        "Storage Cost (per unit)": round(storage_cost, 2),
        "Backup Cost (per unit)": round(backup_cost, 2),
        "Firewall Cost (per unit)": round(firewall_cost, 2),
        "Public IP Cost (per unit)": round(public_ip_cost, 2),
        "Unit Total": round(unit_total, 2),
        "Quantity": quantity,
        "Grand Total": round(total_price, 2),
    }

    return breakdown


def calculate_hana_price(flavour, os_type, pricing_tier, quantity,
                          storage_type, storage_gb,
                          backup_type, backup_gb):
    row = get_hana_row(flavour)
    if row is None:
        return None

    key = f"{os_type}__{pricing_tier}"
    unit_vm_price = row.get(key, None)

    if _missing(unit_vm_price):
        return None
    unit_vm_price = _monthly(unit_vm_price, pricing_tier)

    storage_price_per_gb = STORAGE_PRICES.get(storage_type, 0)
    storage_cost = storage_price_per_gb * storage_gb

    backup_price_per_gb = BACKUP_PRICES.get(backup_type, 0)
    backup_cost = backup_price_per_gb * backup_gb

    unit_total = unit_vm_price + storage_cost + backup_cost
    total_price = unit_total * quantity

    breakdown = {
        "VM Price (per unit)": round(unit_vm_price, 2),
        "Storage Cost (per unit)": round(storage_cost, 2),
        "Backup Cost (per unit)": round(backup_cost, 2),
        "Unit Total": round(unit_total, 2),
        "Quantity": quantity,
        "Grand Total": round(total_price, 2),
    }

    return breakdown


def calculate_olvm_price(flavour, pricing_tier, quantity,
                          storage_type, storage_gb,
                          backup_type, backup_gb):
    row = get_olvm_row(flavour)
    if row is None:
        return None

    key = f"Linux__{pricing_tier}"
    unit_vm_price = row.get(key, None)

    if _missing(unit_vm_price):
        return None
    unit_vm_price = _monthly(unit_vm_price, pricing_tier)

    storage_price_per_gb = STORAGE_PRICES.get(storage_type, 0)
    storage_cost = storage_price_per_gb * storage_gb

    backup_price_per_gb = BACKUP_PRICES.get(backup_type, 0)
    backup_cost = backup_price_per_gb * backup_gb

    unit_total = unit_vm_price + storage_cost + backup_cost
    total_price = unit_total * quantity

    breakdown = {
        "VM Price (per unit)": round(unit_vm_price, 2),
        "Storage Cost (per unit)": round(storage_cost, 2),
        "Backup Cost (per unit)": round(backup_cost, 2),
        "Unit Total": round(unit_total, 2),
        "Quantity": quantity,
        "Grand Total": round(total_price, 2),
    }

    return breakdown


def get_flavour_specs(product, flavour):
    if product == "Vayu Cloud":
        row = get_vayu_row(flavour)
    elif product == "Hana Grid":
        row = get_hana_row(flavour)
    else:
        row = get_olvm_row(flavour)

    if row is None:
        return {}

    specs = {
        "vCPU": int(row["vCPU"]),
        "RAM (GB)": int(row["RAM (GB)"]),
    }

    if product == "Vayu Cloud":
        specs["Root Disk Windows (GB)"] = int(row["Root Disk Windows (GB)"])
        specs["Root Disk Other OS (GB)"] = int(row["Root Disk Other OS (GB)"])
    else:
        specs["Root Disk (GB)"] = int(row["Root Disk (GB)"])

    return specs

