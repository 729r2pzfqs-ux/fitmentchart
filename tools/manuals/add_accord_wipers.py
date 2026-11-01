"""Accord wiper blades for the years Rain-X does not list (2008-2012, 2023-2025), from the HondaPartsNow
genuine-Honda parts catalog (oem_parts_catalog), the same source add_chunk3.py uses for the Civic.

Pages are cached as data/cache/web/hpn_accord_<year>.html. Every quote below is checked against the saved page
before it is written. Positions are as the catalog prints them ("Position : Driver Side" / "Passenger Side").
2008-2012: the 650 mm driver blade listed with a length is the coupe part (76620-TE0-A01); the sedan driver part
(76620-TA0-A02) is listed without a length, so the record carries a note. The passenger blade is 475 mm for both.
2026: the catalog page lists no blades, so 2026 stays a gap. Run after add_wipers.py (which leaves OEM records alone).
"""
import html, re, sys, yaml
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "data/cache/web"
PATH = ROOT / "data/manuals/honda/accord.yaml"
ACCESSED = "2026-11-01"
URL = "https://www.hondapartsnow.com/oem-{y}-honda-accord-wiper_blade.html"
# year -> ((driver label, part, mm), (passenger label, part, mm), note)
PARTS = {}
for y in range(2008, 2013):
    PARTS[y] = (("Blade, Windshield Wiper (650MM)", "76620-TE0-A01", 650), ("Blade, Windshield Wiper (475MM)", "76630-TA0-A01", 475),
                "Driver length from the coupe part (76620-TE0-A01); the sedan driver part (76620-TA0-A02) is listed without a length. "
                "Passenger 475 mm on sedan (76630-TA0) and coupe (76630-TE0).")
for y in range(2023, 2026):
    PARTS[y] = (("BLADE (600)", "76620-30A-A01", 600), ("BLADE (425)", "76630-30A-A01", 425), None)
inch = lambda mm: round(mm / 25.4, 1)

def page_text(y):
    s = (WEB / f"hpn_accord_{y}.html").read_text(errors="replace")
    s = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))

data = yaml.safe_load(PATH.read_text())
data["records"] = [r for r in data["records"] if not (r["field"] == "wipers" and r["src"][0]["ref"].startswith("hpn"))]
for k in [k for k in data["sources"] if k.startswith("hpn")]:
    del data["sources"][k]
oem_years = {y for r in data["records"] if r["field"] == "wipers" for y in range(r["years"][0], r["years"][1] + 1)}
added = 0
for y, (d, p, note) in sorted(PARTS.items()):
    if y in oem_years:
        continue
    txt = page_text(y)
    src = []
    for label, part, mm in (d, p):
        quote = f"{y} Honda Accord {label} Part Number: {part}"
        if quote not in txt:
            raise SystemExit(f"{y}: {quote!r} not on saved page")
        pos = "Driver Side" if part.startswith("76620") else "Passenger Side"
        if f"Position : {pos}" not in txt:
            raise SystemExit(f"{y}: position {pos!r} not on saved page")
        src.append({"ref": f"hpn{y}", "quote": quote})
    data["sources"][f"hpn{y}"] = {"doc": f"HondaPartsNow (genuine Honda parts catalog): {y} Honda Accord Wiper Blade",
                                   "url": URL.format(y=y), "type": "oem_parts_catalog", "accessed": ACCESSED}
    rec = {"field": "wipers", "years": [y, y], "driver_in": inch(d[2]), "passenger_in": inch(p[2])}
    if note:
        rec["note"] = note
    rec["src"] = src
    data["records"].append(rec)
    added += 1
with open(PATH, "w") as fh:
    fh.write("# Generated from OEM documents (quotes verified against the cited PDF page), Rain-X wiper fitment pages\n"
             "# and the HondaPartsNow genuine-parts catalog (tools/manuals/add_accord_wipers.py).\n")
    yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, width=120)
print(f"honda/accord wipers added={added}")
