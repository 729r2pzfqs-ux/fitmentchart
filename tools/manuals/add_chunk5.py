"""Gap-research chunk 5, verified: Jeep Wrangler towing, oil capacity and tires from the FCA/Stellantis
media spec sheets (2011-2014, 2016, 2019, 2021-2026), plus the EcoDiesel oil grade from the 2021-2023
owner's manuals. Run after build_wrangler.py and add_wipers.py.

Not added (no verifiable source):
- Quadratec / ExtremeTerrain values for TJ 2005-06 and JK 2007-10, 2015: quadratec.com sits behind a
  bot check, and the research gave no OEM document for those years.
- Battery group sizes (Wrangler and Tacoma): the research cites autopadre.com and owner forums only. The
  spec sheets print CCA but no BCI group, and a battery record needs a group.

Conflicts kept out:
- 2016 towing. The 2016 spec sheet rates the 2-door at 2,000 lb on every axle; the 2016/2017 owner's
  manuals give 3,500 lb with the 3.73 axle. The manual rows stay, and no spec-sheet towing is added for 2016.
- 2026 6.4L oil. The spec sheet says 7 qt and the 2026 owner's manual 7.5 qt. The manual value stays.
"""
import re, subprocess, sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import cite, DOCS, page_text

Y = ROOT / "data/manuals/jeep/wrangler.yaml"
data = yaml.safe_load(Y.read_text())
SP = ROOT / "data/cache/manuals/jeep-specs"
OM = ROOT / "data/cache/manuals/jeep-wrangler"
S3 = "https://s3.amazonaws.com/chryslermedia.iconicweb.com/mediasite/specs/"
SHEETS = {  # ref: (file, year, title)
    "sp2011": ("2011_JP_Wrangler_Specs.pdf", 2011, "2011 Jeep Wrangler Specifications"),
    "sp2012": ("2012_JP_Wrangler_Specs.pdf", 2012, "2012 Jeep Wrangler Specifications"),
    "sp2013": ("2013_SP_Wrangler.pdf", 2013, "2013 Jeep Wrangler Specifications"),
    "sp2013u": ("2013_SP_Wrangler_Unl.pdf", 2013, "2013 Jeep Wrangler Unlimited Specifications"),
    "sp2014": ("2014_JP_Wrangler_SP.pdf", 2014, "2014 Jeep Wrangler Specifications"),
    "sp2016": ("2016_JP_Wrangler_SPdqfdrtdro7i79bi1ga997266g4.pdf", 2016, "2016 Jeep Wrangler Specifications"),
    "sp2019": ("2019_JP_Wrangler_SPmk1alba10mregeqq9v39oek881.pdf", 2019, "2019 Jeep Wrangler Specifications"),
    "sp2021": ("2021_JP_Wrangler_SPpr9cq0ipusqbj1krgeoq0pu45s.pdf", 2021, "2021 Jeep Wrangler Specifications"),
    "sp2022": ("2022_JP_Wrangler_SP.pdf", 2022, "2022 Jeep Wrangler Specifications"),
    "sp2023": ("2023_JP_Wrangler_SP.pdf", 2023, "2023 Jeep Wrangler Specifications"),
    "sp2024": ("2024_JP_Wrangler_SP5fcgnuvfl399adn0lfjsosc427.pdf", 2024, "2024 Jeep Wrangler Specifications"),
    "sp2024x": ("2024_JP_Wrangler_4xe_SP.pdf", 2024, "2024 Jeep Wrangler 4xe Specifications"),
    "sp2025ca": ("2025CA.pdf", 2025, "2025 Jeep Wrangler Canada Specifications"),
    "sp2026": ("2026_JP_Wrangler_SPl4u58u77eeicb0t51n2lc8s5fg.pdf", 2026, "2026 Jeep Wrangler Specifications"),
}
URL = {k: S3 + f for k, (f, _, _) in SHEETS.items()}
URL["sp2025ca"] = S3 + "CANADA_2025_JP_Wrangler_SP_qv55u7tfafof1vfvc7hpkbq4lu.pdf"

data["records"] = [r for r in data["records"] if not any(s["ref"] in SHEETS for s in r["src"])]
for k, (f, y, title) in SHEETS.items():
    DOCS[k] = {"pdf": str(SP / f), "doc": title + " (FCA/Stellantis media spec sheet)", "url": URL[k],
               "type": "oem_spec_sheet", "accessed": "2026-10-14"}
    data["sources"][k] = {kk: v for kk, v in DOCS[k].items() if kk != "pdf"}
data["sources"]["sp2025ca"]["note"] = "Canadian-market sheet; no US 2025 sheet was reachable (403)"
for k, src in list(data["sources"].items()):
    if k.startswith("om") and (OM / f"{k}.pdf").exists():
        DOCS[k] = {**src, "pdf": str(OM / f"{k}.pdf")}

NPAGES = {}
def npages(ref):
    if ref not in NPAGES:
        out = subprocess.run(["pdfinfo", DOCS[ref]["pdf"]], capture_output=True, text=True).stdout
        NPAGES[ref] = int(re.search(r"Pages:\s+(\d+)", out).group(1))
    return NPAGES[ref]

def find(ref, pattern, must=()):
    """cite() on the first page of the document whose text matches."""
    for p in range(1, npages(ref) + 1):
        if any(re.search(pattern, page_text(DOCS[ref]["pdf"], p, raw), re.I) for raw in (False, True, "raw")):
            return cite(ref, p, pattern, must)
    raise SystemExit(f"pattern {pattern!r} not found in {ref}")

ENG = {}
for y, v in __import__("json").load(open(ROOT / "data/models/jeep/wrangler.json"))["years"].items():
    ENG[int(y)] = {e["displacement_l"] for e in v["engines"]}
R = []
skipped = []
def add(rec):
    d = rec.get("displacement_l")
    if d is not None and d not in ENG[rec["years"][0]]:
        skipped.append((rec["field"], rec["years"][0], d)); return
    R.append(rec)

# ---------------------------------------------------------------- towing
N = r"\s+\d{3,4}\s+\d{4}\s+\d{4}\s+\d{4}\s+\d{4}\s+\d{4}\s+"   # payload, base wt, base F/R, GAWR F (to GAWR R)
def tow(y, d, eng, cab, mx, src, trim=None, axle=None, gcwr=None, pkg=None, note=None):
    r = {"field": "towing", "years": [y, y], "displacement_l": d, "engine": eng, "drive": "4WD", "cab": cab}
    if trim: r["trim"] = trim
    if axle: r["axle"] = axle
    r["max_lb"] = mx
    if gcwr: r["gcwr_lb"] = gcwr
    if pkg: r["package"] = pkg
    if note: r["note"] = note
    r["src"] = src; add(r)

# 2011 (3.8L, 2-door sheet): 1,000 lb with the 3.21 axle, 2,000 lb with 3.73/4.10
tow(2011, 3.8, "3.8L V-6", "Two-Door", 1000, [find("sp2011", r"3\.8L V-6 gas \(EGT\) M6 NSG370 6-SPD MANUAL \(DEH\) 3\.21\*\*" + N + r"5155 1000", ["1000"])],
    trim="Sport, Sahara", axle="3.21", note="AHT trailer-tow package not available with the 3.21 axle")
tow(2011, 3.8, "3.8L V-6", "Two-Door", 2000, [find("sp2011", r"3\.8L V-6 gas \(EGT\) M6 NSG370 6-SPD MANUAL \(DEH\) 3\.73" + N + r"6155 2000", ["2000"])],
    trim="Sport, Sahara", axle="3.73")
tow(2011, 3.8, "3.8L V-6", "Two-Door", 2000, [find("sp2011", r"3\.8L V-6 gas \(EGT\) A4 42RLE VLP 4-SPD AUTO \(DGV\) 4\.10" + N + r"6257 2000", ["2000"])],
    trim="Rubicon", axle="4.10")
# 2012-2014 2-door sheets: every Sport/Sahara/Rubicon row (3.21, 3.73, 4.10) is 2,000 lb
for y, ref in ((2012, "sp2012"), (2013, "sp2013"), (2014, "sp2014")):
    tow(y, 3.6, "3.6L V-6", "Two-Door", 2000,
        [find(ref, r"3\.6L V-6 gas \(EGT\) M6 NSG370 6-SPD MANUAL \(DEH\) 3\.73" + N + r"6029 2000", ["2000"]),
         find(ref, r"3\.6L V-6 gas \(EGT\) A5 WA580 5-SPD AUTO \(DGV\) 4\.10" + N + r"6296 2000", ["2000"])],
        trim="Sport, Sahara, Rubicon", note="every 2-door row on the sheet (3.21, 3.73 and 4.10 axles) is 2,000 lb")
# 2013 Unlimited: 2,000 lb with 3.21, 3,500 lb with 3.73/4.10
tow(2013, 3.6, "3.6L V-6", "Four-Door", 2000, [find("sp2013u", r"3\.6L V-6 gas \(EGT\) M6 NSG370 6-SPD MANUAL \(DEH\) 3\.21" + N + r"6547 2000", ["2000"])],
    trim="Unlimited Sport, Unlimited Sahara", axle="3.21")
tow(2013, 3.6, "3.6L V-6", "Four-Door", 3500, [find("sp2013u", r"3\.6L V-6 gas \(EGT\) M6 NSG370 6-SPD MANUAL \(DEH\) 3\.73" + N + r"8047 3500", ["3500"])],
    trim="Unlimited Sport, Unlimited Sahara", axle="3.73")
tow(2013, 3.6, "3.6L V-6", "Four-Door", 3500, [find("sp2013u", r"3\.6L V-6 gas \(EGT\) A5 WA580 5-SPD AUTO \(DGV\) 4\.10" + N + r"8185 3500", ["3500"])],
    trim="Unlimited Rubicon", axle="4.10")

# JL sheets: per-engine "Max. Gross Trailer Weight" lines (2-door / 4-door split)
HDR = r"Max\. Gross Trailer Weight 2,000 lbs\. \(2-door\), 3,500 lbs\. \(4-door[^)]*\)"
def hdr(ref, eng_rx, nth=0):
    """cite the nth trailer-weight line in the document (sheets list 3.6L first, then 2.0L)."""
    hits = []
    for p in range(1, npages(ref) + 1):
        t = page_text(DOCS[ref]["pdf"], p)
        hits += [(p, m.group(0)) for m in re.finditer(HDR, t)]
    p, q = hits[nth]
    # the engine heading must precede this line in reading order
    before = " ".join(page_text(DOCS[ref]["pdf"], i) for i in range(max(1, p - 1), p + 1))
    if not re.search(eng_rx, before, re.I):
        raise SystemExit(f"{ref}: trailer line #{nth} on p.{p} not under {eng_rx}")
    return cite(ref, p, re.escape(q), ["2,000", "3,500"])
for y, ref in ((2019, "sp2019"), (2024, "sp2024"), (2026, "sp2026")):
    for d, eng, nth, rx in ((3.6, "3.6L Pentastar V-6", 0, r"3\.6-LITER PENTASTAR"), (2.0, "2.0L Turbo I-4", 1, r"2\.0-LITER TURBO")):
        c = hdr(ref, rx, nth)
        tow(y, d, eng, "Two-Door", 2000, [c])
        tow(y, d, eng, "Four-Door", 3500, [c], note="Rubicon 4.10 automatic: see the 5,000 lb row" if y >= 2024 else None)
# 2025: Canadian sheet, 3.6L line is in lb; 2.0L line is kg first
c36 = find("sp2025ca", HDR, ["2,000", "3,500"])
tow(2025, 3.6, "3.6L Pentastar V-6", "Two-Door", 2000, [c36])
tow(2025, 3.6, "3.6L Pentastar V-6", "Four-Door", 3500, [c36], note="Rubicon 4.10 automatic: see the 5,000 lb row")
c20 = find("sp2025ca", r"907 kg \(2,000 lbs\.\) \(2-door\), 1,587 kg \(3,500 lbs\.\) \(4-door\), 2,276 kg \(5,000 lbs\.\) \(4-door Rubicon, automatic 4\.10 axle ratio with LT285/70R17C tire\)", ["2,000", "3,500", "5,000"])
tow(2025, 2.0, "2.0L Turbo I-4", "Two-Door", 2000, [c20])
tow(2025, 2.0, "2.0L Turbo I-4", "Four-Door", 3500, [c20], note="Rubicon 4.10 automatic: see the 5,000 lb row")
tow(2025, 2.0, "2.0L Turbo I-4", "Four-Door", 5000, [c20], trim="Rubicon", axle="4.10", gcwr=9950,
    pkg="8-speed automatic, LT285/70R17C tires",
    note="GCWR from the sheet's Rubicon table")
cite_gcwr25 = find("sp2025ca", r"\(1,298\) \(4,602\) \(2,421\) \(2,181\) \(3,100\) \(3,550\) \(9,950\) \(5,000\)", ["9,950", "5,000"])
R[-1]["src"].append(cite_gcwr25)
c25r = find("sp2025ca", r"5,000 lbs\. \(4-door Rubicon,", ["5,000"])
tow(2025, 3.6, "3.6L Pentastar V-6", "Four-Door", 5000, [c25r], trim="Rubicon", pkg="automatic",
    note="sheet line reads '5,000 lbs. (4-door Rubicon, automatic)'")
# 2024 / 2026 Rubicon 5,000 lb and 6.4L rows from the towing tables
tow(2024, 3.6, "3.6L Pentastar V-6", "Four-Door", 5000,
    [find("sp2024", r"3\.6-liter V-6 gas A8 850RE 8-speed automatic 4\.10 1298 4604 2424 2180 3100 3550 10300 5000", ["5000"])],
    trim="Rubicon", axle="4.10", gcwr=10300, pkg="8-speed automatic")
tow(2024, 2.0, "2.0L Turbo I-4", "Four-Door", 5000,
    [find("sp2024", r"2\.0-liter I-4 gas A8 850RE 8-speed automatic 4\.10 1298 4602 2421 2181 3100 3550 9950 5000", ["5000"])],
    trim="Rubicon", axle="4.10", gcwr=9950, pkg="8-speed automatic")
tow(2024, 6.4, "6.4L V-8", "Four-Door", 3500,
    [find("sp2024", r"6\.4-liter V-8 gas A8 8HP75 8-speed automatic 4\.56 1088 5268 2797 2471 3400 3550 10800 3500", ["3500"])],
    trim="Rubicon 392", axle="4.56", gcwr=10800)
tow(2026, 3.6, "3.6L Pentastar V-6", "Four-Door", 5000,
    [find("sp2026", r"3\.6-liter A8 850RE 8-speed 4\.10 1,328 4,623 2,451 2,172 3,100 3,550 10,300 5,000", ["5,000"])],
    trim="Rubicon", axle="4.10", gcwr=10300, pkg="8-speed automatic")
tow(2026, 2.0, "2.0L Turbo I-4", "Four-Door", 5000,
    [find("sp2026", r"2\.0-liter A8 850RE 8-speed 4\.10 1,310 4,640 2,460 2,180 3,100 3,550 10,300 5,000", ["5,000"])],
    trim="Rubicon", axle="4.10", gcwr=10300, pkg="8-speed automatic")
tow(2026, 6.4, "6.4L V-8", "Four-Door", 3500,
    [find("sp2026", r"6\.4-liter A8 8HP75 8-speed 4\.56 1,088 5,268 2,797 2,471 3,400 3,550 9,400 3,500", ["3,500"])],
    trim="Moab 392", axle="4.56", gcwr=9400)
# 2022/2023 Rubicon 392 (not in the owner's-manual tables). The printed GCWR (6,250) is below base
# weight + trailer, so it is left out.
for y, ref in ((2022, "sp2022"), (2023, "sp2023")):
    tow(y, 6.4, "6.4L V-8", "Four-Door", 3500,
        [find(ref, r"6\.4-liter V-8 gas A8 8HP75 8-speed automatic 4\.56 1028 5222 2773 2449 3450 3550 6250 3500", ["3500"])],
        trim="Rubicon 392", axle="4.56", note="sheet's GCWR figure (6,250) is inconsistent with its base weight, omitted")
# 4xe (plug-in hybrid)
tow(2022, 2.0, "2.0L Turbo I-4 PHEV (4xe)", "Four-Door", 3500,
    [find("sp2022", r"2\.0-liter I-4 gas PHEV A8 8P75PH 8-speed automatic 3\.73 1191 5009 2540 2469 3100 3550 9000 3500", ["3500"])],
    trim="Sahara 4xe", axle="3.73", gcwr=9000)
tow(2024, 2.0, "2.0L Turbo I-4 PHEV (4xe)", "Four-Door", 3500,
    [find("sp2024x", r"Max\. Gross Trailer Weight 3,500 lbs\.", ["3,500"])], trim="all 4xe")

# ---------------------------------------------------------------- tires (standard fitments only)
TIRE = re.compile(r"Availability (Standard[^.]*?) Size and type ((?:P|LT)?\d{3}/\d{2}R\d{2}C?)", re.I)
def trims(av):
    t = re.sub(r"^Standard\s*(on|—|-)?\s*", "", av).strip(" ()")
    t = re.sub(r"\)?,? Optional.*", "", t)
    return re.sub(r"\bWrangler (Unlimited )?", "", t).strip(" ()")
TIRE_REFS = {2011: ["sp2011"], 2012: ["sp2012"], 2013: ["sp2013"], 2014: ["sp2014"], 2016: ["sp2016"], 2019: ["sp2019"],
             2021: ["sp2021"], 2022: ["sp2022"], 2023: ["sp2023"], 2024: ["sp2024", "sp2024x"], 2025: ["sp2025ca"],
             2026: ["sp2026"]}
for y, refs in TIRE_REFS.items():
    for ref in refs:
        seen = set()
        for p in range(1, npages(ref) + 1):
            for m in TIRE.finditer(page_text(DOCS[ref]["pdf"], p)):
                trim, size = trims(m.group(1)), m.group(2).upper()
                if ref == "sp2024x" and "4xe" not in trim:
                    trim += " 4xe"
                if (trim, size) in seen:
                    continue
                seen.add((trim, size))
                add({"field": "tires", "years": [y, y], "trim": trim, "size": size,
                     "src": [cite(ref, p, re.escape(m.group(0)), [m.group(2)])]})

# ---------------------------------------------------------------- oil capacity (sheets print no grade)
have_oil = {(r["years"][0], r["displacement_l"]) for r in data["records"] if r["field"] == "oil"}
def oil(y, d, eng, qt, l, ref, rx, cond=None, note=None):
    if (y, d) in have_oil and not cond:
        return  # owner's manual already gives this engine (with grade)
    r = {"field": "oil", "years": [y, y], "displacement_l": d, "engine": eng}
    if cond: r["condition"] = cond
    r.update({"capacity_qt": qt, "capacity_l": l})
    if note: r["note"] = note
    r["src"] = [find(ref, rx, [str(qt).rstrip("0").rstrip(".")])]; add(r)
oil(2011, 3.8, "3.8L V-6", 6.0, 5.7, "sp2011", r"Oil Capacity 6\.0 qt\. \(5\.7L\) plus filter")
oil(2012, 3.6, "3.6L V-6", 6.0, 5.7, "sp2012", r"Oil Capacity 6\.0 qt\. \(5\.7L\)")
oil(2013, 3.6, "3.6L V-6", 6.0, 5.7, "sp2013", r"Oil Capacity 6\.0 qt\. \(5\.7-liter\)")
oil(2014, 3.6, "3.6L V-6", 6.0, 5.7, "sp2014", r"Oil Capacity 6\.0 qt\. \(5\.7 liter\)")
oil(2019, 3.6, "3.6L Pentastar V-6", 5.0, 4.7, "sp2019", r"Oil Capacity 5\.0 quarts \(4\.7 liters\)")
oil(2019, 2.0, "2.0L Turbo I-4", 5.0, 4.7, "sp2019", r"Oil Capacity 5 quarts \(4\.7 liters\)")
for y, ref in ((2022, "sp2022"), (2023, "sp2023"), (2024, "sp2024")):
    oil(y, 6.4, "6.4L V-8", 7.0, 6.6, ref, r"Oil Capacity 7 quarts \(6\.6 liters\)")
oil(2024, 3.6, "3.6L Pentastar V-6", 5.0, 4.7, "sp2024", r"Oil Capacity 5\.0 quarts \(4\.7 liters\)")
oil(2024, 2.0, "2.0L Turbo I-4", 5.0, 4.7, "sp2024", r"Oil Capacity 5 quarts \(4\.7 liters\)")
oil(2024, 2.0, "2.0L Turbo I-4 PHEV", 5.0, 4.7, "sp2024x", r"Oil Capacity 5 quarts \(4\.7 liters\)", cond="4xe plug-in hybrid")
oil(2025, 3.6, "3.6L Pentastar V-6", 5.0, 4.7, "sp2025ca", r"Oil Capacity, litres \(quarts\) 4\.7 \(5\.0\)")
oil(2025, 2.0, "2.0L Turbo I-4", 5.0, 4.7, "sp2025ca", r"Oil Capacity, litres \(quarts\) 4\.7 \(5\.0\)")

# EcoDiesel grade (owner's manuals); the capacity records already exist from build_wrangler.py
DIESEL_RX = {"om2021": r"We recommend you use 5W-40 synthetic engine oil such as Mopar",
             "om2022": r"We recommend using Mopar® API Certified SAE 5W-40 Full Synthetic Engine Oil",
             "om2023": r"We recommend using Mopar® API Certified SAE 5W-40 Full Synthetic Engine Oil"}
for r in data["records"]:
    ref = r["src"][0]["ref"]
    if r["field"] == "oil" and r.get("displacement_l") == 3.0 and ref in DIESEL_RX:
        r["grade"] = "5W-40"
        c = find(ref, DIESEL_RX[ref], ["5W-40"])
        r["src"] = [s for s in r["src"] if s["page"] != c["page"] or s["quote"] != c["quote"]] + [c]

data["records"] += R
with open(Y, "w") as fh:
    fh.write("# Generated from Mopar owner's manuals and FCA/Stellantis media spec sheets (quotes verified against the\n"
             "# cited PDF page) plus Rain-X wiper fitment pages (aftermarket_fitment).\n")
    yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, width=120)
counts = {}
for r in R:
    counts[r["field"]] = counts.get(r["field"], 0) + 1
print("added", counts, "skipped (engine not in EPA list for that year):", skipped)
