#!/usr/bin/env python3
"""Convert data/Communities_List.xlsx into JSON files in public/.

  public/communities.json       one card per community (paired buildings that share a
                                Community Code are combined). This is what the directory page uses.
  public/communities-flat.json  one record per spreadsheet row, for other tools to read.

Hard problems (missing columns, no rows) stop the script with an error.
Softer problems are printed as WARNING lines and do not stop the build.
"""
import json, re, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "Communities_List.xlsx"
OUT = ROOT / "public"

REQUIRED = ["Community Code", "Community", "Phone Number", "Site Type", "Address", "Units Total"]
AMENITIES = ["Community Room", "Laundry Room", "Off-Street Parking", "On-Site Library", "Game Room",
             "Media Room", "Outdoor Space", "Fitness Center", "Bus Access", "Beauty Salon",
             "Computer/Business Room", "Activity/Craft Room", "Controlled Access"]
MIX = [("Efficiency Units", "Efficiency"), ("Studio Units", "Studio"), ("1-Bedroom Units", "1-bedroom"),
       ("2-Bedroom Units", "2-bedroom"), ("3-Bedroom Units", "3-bedroom"), ("4-Bedroom Units", "4-bedroom")]
STATE_NAMES = {"New York": "NY", "Texas": "TX"}  # addresses that spell the state out
warnings = []


def warn(msg):
    warnings.append(msg)
    print(f"WARNING: {msg}")


def text(v):
    """Cell -> trimmed string, or None if blank. Whole numbers lose the '.0'."""
    if pd.isna(v):
        return None
    if isinstance(v, float) and v == int(v):
        v = int(v)
    v = str(v).strip()
    return v or None


def utilities(v):
    v = text(v)
    if not v:
        return None
    if v.lower().startswith("full util"):          # also fixes the "Full Utilites" typo
        return "Full utilities"
    if v.lower() == "tenant paid":
        return "Tenant paid"
    return re.sub(r"^Partial[\s\-]*(Paid)?:?\s*", "Partial: ", v)


def disability(v):
    if pd.isna(v):
        return None
    if isinstance(v, (int, float)):
        return f"{round(v * 100)}%"
    v = str(v).strip()
    return "No" if v.lower() in ("none", "no", "n/a") else v


def state_of(addr):
    m = re.search(r"\b([A-Z]{2})\b,?\s*\d{5}", addr)
    if m:
        return m.group(1)
    return next((abbr for name, abbr in STATE_NAMES.items() if name in addr), "")


def building(r):
    other = [x.strip() for x in str(r["Other Amenities"]).split(",") if x.strip()] if pd.notna(r["Other Amenities"]) else []
    answered = any(pd.notna(r[c]) for c in ["Utilities", "Service Coordinator", "Community Room", "Fair Housing Logo"])
    return {
        "phone": text(r["Phone Number"]),
        "total": int(r["Units Total"]) if pd.notna(r["Units Total"]) else None,
        "mix": [[label, int(r[col])] for col, label in MIX if pd.notna(r[col]) and r[col] > 0],
        "mr": text(r["Market Rate Units"]),
        "ada": text(r["ADA Units"]),
        "dis": disability(r["Disability %"]),
        "util": utilities(r["Utilities"]),
        "sc": text(r["Service Coordinator"]),
        "resp": answered,
        "am": [a for a in AMENITIES if r[a] == 1],
        "other": other,
    }


def main():
    if not SRC.exists():
        sys.exit(f"ERROR: {SRC} not found")
    xl = pd.ExcelFile(SRC)
    sheet = "Communities" if "Communities" in xl.sheet_names else xl.sheet_names[0]
    df = xl.parse(sheet, keep_default_na=False, na_values=[""])
    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in REQUIRED + AMENITIES if c not in df.columns]
    if missing:
        sys.exit("ERROR: missing columns: " + ", ".join(missing))
    if "Other Amenities" not in df.columns:
        df["Other Amenities"] = None
    if df.empty:
        sys.exit("ERROR: the spreadsheet has no rows")

    groups, flat = {}, []
    for i, r in df.iterrows():
        row_no = i + 2
        raw_code = r["Community Code"]
        code = text(raw_code)
        if not code or not text(r["Community"]):
            warn(f"row {row_no}: missing community code or name, skipped")
            continue
        if str(raw_code) != code:
            warn(f"row {row_no} ({r['Community']}): code '{raw_code}' has extra spaces, trimmed to '{code}'")
        groups.setdefault(code, []).append(r)

        b = building(r)
        addr = text(r["Address"]) or ""
        flat.append({
            "code": code, "name": str(r["Community"]).strip(), "site_type": text(r["Site Type"]),
            "address": addr, "state": state_of(addr), "phone": b["phone"], "units_total": b["total"],
            "unit_mix": {label: n for label, n in b["mix"]}, "market_rate_units": b["mr"],
            "ada_units": b["ada"], "disability_pct": b["dis"], "utilities": b["util"],
            "service_coordinator": b["sc"], "fair_housing_logo": text(r["Fair Housing Logo"]),
            "amenities": b["am"], "other_amenities": b["other"], "survey_completed": b["resp"],
        })
        if b["resp"] and b["mix"] and b["total"] != sum(n for _, n in b["mix"]):
            warn(f"{r['Community']}: units total {b['total']} but unit types add up to {sum(n for _, n in b['mix'])}")
        if b["resp"] and not b["mix"]:
            warn(f"{r['Community']}: has a total but no unit type breakdown")
        if addr and not state_of(addr):
            warn(f"{r['Community']}: could not read a state from the address '{addr}'")

    cards = []
    for code, rows in groups.items():
        f = rows[0]
        addr = text(f["Address"]) or ""
        buildings = []
        for r in rows:
            b = building(r)
            p = re.search(r"\((.*?)\)", str(r["Community"]))
            b["label"] = p.group(1).strip().title() if p else "Main"
            buildings.append(b)
        name = str(f["Community"]).strip()
        if len(rows) > 1:
            name = re.sub(r"\s*\(.*?\)\s*", "", name).strip()
        cards.append({"code": code, "name": name.replace("'", "\u2019"), "addr": addr, "state": state_of(addr),
                      "type": text(f["Site Type"]) or "", "logo": text(f["Fair Housing Logo"]), "b": buildings})
    cards.sort(key=lambda c: c["name"].lower())

    OUT.mkdir(exist_ok=True)
    for fname, payload in (("communities.json", cards), ("communities-flat.json", flat)):
        (OUT / fname).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {len(flat)} rows -> {len(cards)} cards ({len(warnings)} warnings)")


if __name__ == "__main__":
    main()
