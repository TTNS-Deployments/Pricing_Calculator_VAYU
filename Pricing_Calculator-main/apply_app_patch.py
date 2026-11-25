"""
Run this ONCE inside the project folder (where app.py is):

    python apply_app_patch.py

It updates the hard-coded prices and options in app.py to match the new
Training_data.xlsx. It makes a backup (app.py.bak) first and stops without
changing anything if an expected line is not found. Safe to run twice.
"""
import re
import shutil
import sys

PATH = "app.py"

NEW_LICENSE_BLOCK = '''LICENSE_PRICES = {
    "None": 0,
    "MS SQL - Standard (per 2 pCore)": 26816.74,
    "MS SQL - Enterprise (per 2 pCore)": 100966.83,
    "MS SQL - Web Edition (per 2 pCore)": 1677.09,
    "MySQL - Standard (per vCore)": 26449.28,
    "MySQL - Enterprise (per vCore)": 63478.26,
    "PostgreSQL (per month)": 20832.61,
    "Commvault Backup (per GB)": 5.22,
}'''

NEW_MGMT_BLOCK = '''MANAGEMENT_PRICES = {
    "None": 0,
    "OS Management - Windows (per VM)": 500,
    "OS Management - Linux (per VM)": 500,
    "DB Management - MSSQL (per DB)": 9750,
    "DB Management - MySQL (per DB)": 12000,
    "DB Management - PostgreSQL (per DB)": 12000,
}'''

OLD_MG_OPTS = '["None", "OS-Management", "DB Management", "Firewall Management"]'
NEW_MG_OPTS = ('["None", "OS-Management", "DB Management - MSSQL", '
               '"DB Management - MySQL", "DB Management - PostgreSQL", "Firewall Management"]')
NEW_MG_MAP = ('mg_price_map = {"OS-Management": 500, "DB Management - MSSQL": 9750, '
              '"DB Management - MySQL": 12000, "DB Management - PostgreSQL": 12000, '
              '"Firewall Management": 2000}')

# (description, regex, replacement, expected matches, marker proving it was already applied)
EDITS = [
    ("LICENSE_PRICES values (Excel: License Price + Storage price sheets)",
     r"LICENSE_PRICES = \{.*?\n\}", NEW_LICENSE_BLOCK, 1, "26816.74"),
    ("MANAGEMENT_PRICES: DB Management per database type (Excel: License Price sheet)",
     r"MANAGEMENT_PRICES = \{.*?\n\}", NEW_MGMT_BLOCK, 1, "DB Management - MSSQL (per DB)\": 9750"),
    ("Public IP price 900 -> 1350 (Excel: DC to DC Connectivity)",
     r"PUBLIC_IP_PRICE_CONNECTIVITY = 900", "PUBLIC_IP_PRICE_CONNECTIVITY = 1350", 1,
     "PUBLIC_IP_PRICE_CONNECTIVITY = 1350"),
    ("Backup Storage prices now come from pricing_engine.BACKUP_PRICES (2 places)",
     r"bk_price_map = \{[^}]*\}", "bk_price_map = BACKUP_PRICES", 2, "bk_price_map = BACKUP_PRICES"),
    ("Pricing Tier help text mentions hourly -> monthly conversion",
     r'help="Hourly PPU = Pay Per Use"',
     'help="Hourly PPU = Pay Per Use (shown as a monthly price at 730 hours per month)"', 1,
     "shown as a monthly price at 730"),
    ("Management dropdown: DB Management split into MSSQL / MySQL / PostgreSQL (2 places)",
     re.escape(OLD_MG_OPTS), NEW_MG_OPTS, 2, NEW_MG_OPTS),
    ("Management prices: DB Management 6500 -> 9750 / 12000 / 12000 (2 places)",
     r"mg_price_map = \{[^}]*\}", NEW_MG_MAP, 2, NEW_MG_MAP),
]


def main():
    try:
        with open(PATH, "r", encoding="utf-8", newline="") as f:
            raw = f.read()
    except FileNotFoundError:
        sys.exit("app.py not found. Run this from the project folder (where app.py is).")

    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")

    plan = []
    for desc, pattern, repl, expected, marker in EDITS:
        found = len(re.findall(pattern, text, flags=re.DOTALL))
        if found == expected:
            plan.append((desc, pattern, repl, True))
        elif found == 0 and marker in text:
            plan.append((desc, pattern, repl, False))
        else:
            sys.exit(f"STOPPED, nothing changed.\n'{desc}': expected {expected} match(es), found {found}.\n"
                     "Your app.py differs from the version I reviewed. Send it to me again.")

    if not any(apply for *_, apply in plan):
        sys.exit("app.py is already fully patched. Nothing to do.")

    shutil.copyfile(PATH, PATH + ".bak")
    for desc, pattern, repl, apply in plan:
        if apply:
            text = re.sub(pattern, lambda m: repl, text, flags=re.DOTALL)
            print("OK     ", desc)
        else:
            print("already", desc)

    if crlf:
        text = text.replace("\n", "\r\n")
    with open(PATH, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print("\nDone. Backup saved as app.py.bak")


if __name__ == "__main__":
    main()
