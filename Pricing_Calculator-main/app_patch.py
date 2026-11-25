"""
Run this ONCE inside the project folder (where app.py is):

    python apply_app_patch.py

It updates the hard-coded prices in app.py to match the new Training_data.xlsx.
It makes a backup (app.py.bak) first and stops without changing anything if any
expected line is not found.
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

# (description, regex, replacement, expected number of matches)
EDITS = [
    ("LICENSE_PRICES values (Excel: License Price + Storage price sheets)",
     r"LICENSE_PRICES = \{.*?\n\}", NEW_LICENSE_BLOCK, 1),
    ("Public IP price 900 -> 1350 (Excel: DC to DC Connectivity)",
     r"PUBLIC_IP_PRICE_CONNECTIVITY = 900", "PUBLIC_IP_PRICE_CONNECTIVITY = 1350", 1),
    ("Backup Storage prices now come from pricing_engine.BACKUP_PRICES (2 places)",
     r"bk_price_map = \{[^}]*\}", "bk_price_map = BACKUP_PRICES", 2),
    ("Pricing Tier help text mentions hourly -> monthly conversion",
     r'help="Hourly PPU = Pay Per Use"',
     'help="Hourly PPU = Pay Per Use (shown as a monthly price at 730 hours per month)"', 1),
]


def main():
    try:
        with open(PATH, "r", encoding="utf-8", newline="") as f:
            raw = f.read()
    except FileNotFoundError:
        sys.exit("app.py not found. Run this from the project folder (where app.py is).")

    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")

    if "bk_price_map = BACKUP_PRICES" in text and "26816.74" in text:
        sys.exit("app.py already looks patched. Nothing to do.")

    for desc, pattern, repl, expected in EDITS:
        found = len(re.findall(pattern, text, flags=re.DOTALL))
        if found != expected:
            sys.exit(f"STOPPED, nothing changed.\n'{desc}': expected {expected} match(es), found {found}.\n"
                     "Your app.py differs from the version I reviewed. Send it to me again.")

    shutil.copyfile(PATH, PATH + ".bak")
    for desc, pattern, repl, expected in EDITS:
        text = re.sub(pattern, lambda m: repl, text, flags=re.DOTALL)
        print("OK  ", desc)

    if crlf:
        text = text.replace("\n", "\r\n")
    with open(PATH, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print("\nDone. Backup saved as app.py.bak")


if __name__ == "__main__":
    main()
