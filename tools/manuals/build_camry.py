"""Toyota Camry and Camry Hybrid: oil, tires, towing from toyota.ca owner's manuals (OM… PDFs).

Year-to-manual mapping comes from toyota.ca's manuals API:
  /bin/api/get-manuals-search-options.toyota.en.json          (series names and years)
  /bin/api/get-manuals.toyota.en.json?year=<y>&series=<name>  (documents)
It starts at MY2008. 2005-07 tires come from tirepressure.com (third_party_reference);
the 2005-07 manuals are on assets.sia.toyota.com, which answers 403, so oil and towing stay empty.
PDFs and saved pages are cached in data/cache/manuals/toyota-camry/.
"""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import DOCS, cite, dump
from tirepressure import rows as tp_rows

ACCESSED = "2026-11-01"
D = ROOT / "data/cache/manuals/toyota-camry"
GAS = {2008: ["OM33751U"], 2009: ["OM33780U"], 2010: ["OM33842U", "OM33838U"], 2011: ["OM33843U"],
       2012: ["OM33A27U", "OM33856U"], 2013: ["OM33A33U"], 2014: ["OM33A82U", "OM33B27U"], 2015: ["OM33A86U"],
       2016: ["OM33C34U"], 2017: ["OM33C64U"], 2018: ["OM33B95U"], 2019: ["OM06142U"], 2020: ["OM06158U"],
       2021: ["OM06242U"], 2022: ["OM06244U"], 2023: ["OM06259U"], 2024: ["OM06291U"]}
HYB = {2008: ["OM33760U"], 2009: ["OM33788U"], 2010: ["OM33800U"], 2011: ["OM33844U"],
       2012: ["OM33A28U", "OM33857U"], 2013: ["OM33A34U"], 2014: ["OM33A83U", "OM33B28U"], 2015: ["OM33A87U"],
       2016: ["OM33C35U"], 2017: ["OM33C65U"], 2018: ["OM06123U"], 2019: ["OM06143U"], 2020: ["OM06162U"],
       2021: ["OM06188U"], 2022: ["OM06246U"], 2023: ["OM06261U"], 2024: ["OM06293U"], 2025: ["OM06266U"],
       2026: ["OM06147U"]}
BUILT = {"OM33842U": "produced June 2009 to January 2010", "OM33838U": "produced January 2009 to May 2009",
         "OM33A27U": "produced June 2012 and later", "OM33856U": "produced September 2011 to December 2011",
         "OM33A28U": "produced June 2012 and later", "OM33857U": "produced October 2011 to December 2011",
         "OM33A82U": "produced December 2013 and later", "OM33B27U": "produced August 2013 to November 2013",
         "OM33A83U": "produced December 2013 and later", "OM33B28U": "produced August 2013 to November 2013"}
LOWER_PATH = {"OM06147U"}   # toyota.ca keeps these under a lower-case folder

def register(table, label):
    for y, codes in table.items():
        for c in codes:
            folder = c.lower() if c in LOWER_PATH else c
            built = f", {BUILT[c]}" if c in BUILT else ""
            DOCS[c] = {"pdf": str(D / f"{c}.pdf"), "doc": f"{y} Toyota {label} Owner's Manual ({c}{built})",
                       "url": f"https://www.toyota.ca/content/dam/toyota/documents/manuals/en/{folder}/{c}.pdf",
                       "type": "oem_manual", "accessed": ACCESSED}
register(GAS, "Camry")
register(HYB, "Camry Hybrid")

PAGES = {}
def pages(c):
    if c not in PAGES:
        PAGES[c] = (D / f"{c}.txt").read_text(errors="replace").split("\f")
    return PAGES[c]

def first(c, nums, patterns, must=()):
    """cite() the first pattern that is found on one of the pages."""
    for rx in patterns:
        for p in nums:
            try:
                return cite(c, p, rx, must)
            except SystemExit:
                continue
    raise SystemExit(f"{c}: none of {patterns} on pages {nums}")

def spec_pages(c):
    return [i for i, t in enumerate(pages(c), 1)
            if re.search(r"SAE ?\d+W|With filter|Oil capacity", t)
            and re.search(r"[Vv]iscosity|filter", t)]

R = []
def add(rec):
    """One record per value; a second manual for the same year joins as corroboration."""
    key = {k: v for k, v in rec.items() if k != "src"}
    for r in R:
        if {k: v for k, v in r.items() if k != "src"} == key:
            r["src"].extend(s for s in rec["src"] if s not in r["src"])
            return
    R.append(rec)

def cap_src(c, qt, l):
    q, L = re.escape(str(qt)), re.escape(str(l))
    return first(c, spec_pages(c), [
        rf"With filter (?:\S+ ){{0,20}}?{q} qt\. ?\({L} L, \d\.\d Imp\. ?qt\.\)",
        rf"2\.5 L 4-cylinder {q} qt\. 4\.\d qt\. \(A25A-FKS\) engine \({L} L",
        rf"3\.5 L V6 \(2GR-FKS\) {q} qt\. 5\.6 qt\. engine \({L} L",
    ], [qt])

def visc_src(c, g, alt):
    nums = spec_pages(c)
    both = [rf"SAE {alt} or {g}.{{0,60}}?However, SAE {g.replace('-', '-? ?')} is the best choice",
            rf"SAE {g} is the best choice.{{0,120}}?If SAE {g}(?: oil)? is not available,? ?SAE {alt}(?: motor| engine)? oil may be used",
            rf"If SAE {g}(?: oil)? is not available,? ?SAE {alt}(?: motor| engine)? oil may be used"]
    try:
        return [first(c, nums, both, [g, alt])]
    except SystemExit:
        pass
    out = []
    try:
        out.append(first(c, nums, [rf"SAE {g} is the best choice", rf"{g} is the oil that provides the optimal level of fuel efficiency"], [g]))
    except SystemExit:
        out.append(first(c, nums, [rf"Recommended viscosity:? SAE {g}"], [g]))
    a = first(c, nums, [rf"If SAE {g}(?: oil)? is not available,?.{{0,90}}?SAE {alt}(?: motor| engine)? oil may be used", rf"SAE {alt} or {g}"], [alt])
    return out + ([a] if a not in out else [])

def oil(y, codes, d, eng, qt, l, g, alt, cond=None):
    for c in codes:
        r = {"field": "oil", "years": [y, y], "displacement_l": d, "engine": eng}
        if cond: r["condition"] = cond
        r.update({"grade": g, "alt_grades": [alt]})
        r.update({"capacity_qt": qt, "capacity_l": l, "src": [cap_src(c, qt, l)] + visc_src(c, g, alt)})
        add(r)

AZ, AZH = "2.4 L 4-cylinder (2AZ-FE)", "2.4 L 4-cylinder hybrid (2AZ-FXE)"
AR, ARH = "2.5 L 4-cylinder (2AR-FE)", "2.5 L 4-cylinder hybrid (2AR-FXE)"
V6, V6K = "3.5 L V6 (2GR-FE)", "3.5 L V6 (2GR-FKS)"
A25, A25H = "2.5 L 4-cylinder (A25A-FKS)", "2.5 L 4-cylinder hybrid (A25A-FXS)"

for y in (2008, 2009):
    oil(y, GAS[y], 2.4, AZ, 4.5, 4.3, "0W-20", "5W-20")
    oil(y, HYB[y], 2.4, AZH, 4.5, 4.3, "0W-20", "5W-20")
    oil(y, GAS[y], 3.5, V6, 6.4, 6.1, "5W-30", "10W-30")
for y in (2010, 2011):
    oil(y, GAS[y], 2.5, AR, 4.7, 4.4, "0W-20", "5W-20")
    oil(y, HYB[y], 2.4, AZH, 4.5, 4.3, "0W-20", "5W-20")
    oil(y, GAS[y], 3.5, V6, 6.4, 6.1, "5W-30", "10W-30")
# 2012: the two manuals print the same 4.4 L as 4.7 qt and 4.6 qt
for codes, h, qt in ((["OM33856U"], False, 4.7), (["OM33A27U"], False, 4.6), (["OM33857U"], True, 4.7), (["OM33A28U"], True, 4.6)):
    oil(2012, codes, 2.5, ARH if h else AR, qt, 4.4, "0W-20", "5W-20", BUILT[codes[0]])
    if not h:
        oil(2012, codes, 3.5, V6, 6.4, 6.1, "0W-20", "5W-20")
for y in range(2013, 2018):
    oil(y, GAS[y], 2.5, AR, 4.6, 4.4, "0W-20", "5W-20")
    oil(y, HYB[y], 2.5, ARH, 4.6, 4.4, "0W-20", "5W-20")
    oil(y, GAS[y], 3.5, V6, 6.4, 6.1, "0W-20", "5W-20")
for y in range(2018, 2025):
    qt, l = (4.8, 4.5) if y < 2024 else (4.5, 4.3)
    oil(y, GAS[y], 2.5, A25, qt, l, "0W-16", "0W-20")
    oil(y, HYB[y], 2.5, A25H, qt, l, "0W-16", "0W-20")
    oil(y, GAS[y], 3.5, V6K, 5.7, 5.4, "0W-20", "5W-20")
for y in (2025, 2026):
    oil(y, HYB[y], 2.5, A25H, 4.5, 4.3, "0W-8", "0W-16")

# ---- towing
NOTE0 = "Toyota does not recommend towing a trailer with this vehicle"
def no_tow(y, codes, trim=None):
    for c in codes:
        nums = [i for i, t in enumerate(pages(c), 1) if re.search(r"does not recommend\s+tow", t)]
        src = first(c, nums, [r"Toyota does not recommend tow-? ?ing a trailer with your vehicle", r"Toyota does not recommend tow-? ?ing"], ["recommend"])
        r = {"field": "towing", "years": [y, y]}
        if trim: r["trim"] = trim
        r.update({"max_lb": 0, "note": NOTE0, "src": [src]})
        add(r)
for y in range(2008, 2012):
    for c in GAS[y]:
        nums = [i for i, t in enumerate(pages(c), 1) if "1000 lb" in t or "100 lb" in t]
        add({"field": "towing", "years": [y, y], "max_lb": 1000, "tongue_lb": 100, "note": "trailer weight + cargo weight",
             "src": [first(c, nums, [r"Towing capacity 1000 lb\. \(453 kg\) \(trailer weight \+ cargo weight\)"], ["1000"]),
                     first(c, nums, [r"maximum 100 lb\. \(45 kg\)"], ["100"])]})
for y in range(2012, 2025):
    no_tow(y, GAS[y])
for y in HYB:
    no_tow(y, HYB[y], "Hybrid")

# ---- tires: every size in the manual's tire specification tables
TIRE = re.compile(r"(?<![\w/])(P?\d{3}/\d{2}R\d{2}) (\d{2,3}[A-Z])\b")
def tires(y, codes, trim=None):
    for c in codes:
        pp = pages(c)
        found = {}
        for i, t in enumerate(pp, 1):
            if i > len(pp) * 0.6 and re.search(r"psi|kPa", t):
                for m in TIRE.finditer(" ".join(t.split())):
                    found.setdefault((m.group(1), m.group(2)), i)
        if not found:
            raise SystemExit(f"{c}: no tire sizes")
        for (size, ls), pg in found.items():
            r = {"field": "tires", "years": [y, y], "size": size, "load_speed": ls}
            if trim: r["trim"] = trim
            r["src"] = [cite(c, pg, re.escape(f"{size} {ls}"), [size])]
            add(r)
for y, codes in GAS.items():
    tires(y, codes)
for y, codes in HYB.items():
    tires(y, codes, "Hybrid")
for y in (2005, 2006, 2007):      # no manual reachable; tires only, never overriding an OEM value
    ref = f"tp{y}"
    DOCS[ref] = {"doc": f"TirePressure.com: {y} Toyota Camry Tire Pressure",
                 "url": f"https://tirepressure.com/{y}-toyota-camry-tire-pressure",
                 "type": "third_party_reference", "accessed": ACCESSED}
    for row in tp_rows(D / f"tp_{y}.html"):
        R.append({"field": "tires", "years": [y, y], "size": row["size"], "trim": row["trims"][:150],
                  "src": [{"ref": ref, "quote": row["text"][:200]}]})

R.sort(key=lambda r: (["oil", "towing", "tires"].index(r["field"]), r["years"][0]))
OUT = ROOT / "data/manuals/toyota/camry.yaml"
dump(str(OUT), "toyota/camry", R)
txt = OUT.read_text().split("\n", 1)[1]
OUT.write_text("# Generated by tools/manuals/build_camry.py: toyota.ca owner's manuals (quotes verified against the cited\n"
               "# PDF page), tirepressure.com (third_party_reference) for 2005-07 tires.\n" + txt)
