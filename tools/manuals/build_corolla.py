"""Toyota Corolla sedan, Hybrid, Hatchback and iM: oil, tires, towing from toyota.ca owner's manuals.

Year-to-manual mapping comes from toyota.ca's manuals API:
  /bin/api/get-manuals-search-options.toyota.en.json          (series names and years)
  /bin/api/get-manuals.toyota.en.json?year=<y>&series=<name>  (documents)
It starts at MY2008. The 2008 manual (OM12B28U) has fonts without a text layer, so pdftotext cannot
read it and quotes cannot be verified. 2005-08 tires come from tirepressure.com (third_party_reference);
the 2005-07 manuals are on assets.sia.toyota.com, which answers 403, so oil and towing stay empty.
PDFs and saved pages are cached in data/cache/manuals/toyota-corolla/.
"""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import DOCS, cite, dump
from tirepressure import rows as tp_rows

ACCESSED = "2026-11-01"
D = ROOT / "data/cache/manuals/toyota-corolla"
SED = {2009: ["OM12A89U", "OM12C16U"], 2010: ["OM12C22U"], 2011: ["OM12D65U"], 2012: ["OM12F48U", "OM12E95U"],
       2013: ["OM12E11U", "OM12F86U"], 2014: ["OM12F00U"], 2015: ["OM12G79U"], 2016: ["OM12J84U"], 2017: ["OM02494U"],
       2018: ["OM02509U"], 2019: ["OM02535U"], 2020: ["OM12K77U"], 2021: ["OM02559U"], 2022: ["OM02617U"],
       2023: ["OM02695U"], 2024: ["OM02684U"], 2025: ["OM02688U"], 2026: ["OM02722U"]}
HYB = {2020: ["OM12K81U"], 2021: ["OM12N83U"], 2022: ["OM12R27U"], 2023: ["OM12T23U"], 2024: ["OM12S09U"],
       2025: ["OM12S84U"], 2026: ["OM12U41U"]}
HB = {2019: ["OM12K90U"], 2020: ["OM12N10U"], 2021: ["OM12P39U"], 2022: ["OM12Q05U"], 2023: ["OM12S00U"],
      2024: ["OM12S56U"], 2025: ["OM12T33U"], 2026: ["OM12U26U"]}
IM = {2017: ["OM12K64U"], 2018: ["OM12M42U"]}
BUILT = {"OM12A89U": "produced January 2008 and later", "OM12C16U": "produced February 2008 to December 2008",
         "OM12F48U": "produced March 2012 to July 2012", "OM12E95U": "produced November 2011 to February 2012",
         "OM12E11U": "produced January 2013 and later", "OM12F86U": "produced August 2012 to December 2012"}
LOWER_PATH = {"OM02722U", "OM12U26U"}   # toyota.ca keeps these under a lower-case folder

def register(table, label):
    for y, codes in table.items():
        for c in codes:
            folder = c.lower() if c in LOWER_PATH else c
            built = f", {BUILT[c]}" if c in BUILT else ""
            DOCS[c] = {"pdf": str(D / f"{c}.pdf"), "doc": f"{y} Toyota {label} Owner's Manual ({c}{built})",
                       "url": f"https://www.toyota.ca/content/dam/toyota/documents/manuals/en/{folder}/{c}.pdf",
                       "type": "oem_manual", "accessed": ACCESSED}
register(SED, "Corolla")
register(HYB, "Corolla Hybrid")
register(HB, "Corolla Hatchback")
register(IM, "Corolla iM")

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
            if re.search(r"SAE ?\d+W|With filter|Oil capacity", t) and re.search(r"[Vv]iscosity|filter", t)]

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
        rf"{q} qt\. ?\({L} L, \d\.\d Imp\. ?qt\.\)",
        rf"{q} qt\. ?\({L} L, \d\.\d Imp\.",
    ], [qt])

def visc_src(c, g, alt, section=False):
    """section: the manual has a separate 1.8 L oil section, so prefer its wording over the shared "or" line."""
    nums = spec_pages(c)
    both = [rf"SAE {alt} or (?:SAE )?{g}.{{0,60}}?However, SAE {g.replace('-', '-? ?')} is the best choice",
            rf"SAE {g} is the best choice.{{0,120}}?If SAE {g}(?: oil)? is not available,? ?SAE {alt}(?: motor| engine)? oil may be used",
            rf"If SAE {g}(?: oil)? is not available,? ?SAE {alt}(?: motor| engine)? oil may be used"]
    if section:
        both = both[1:]
    try:
        return [first(c, nums, both, [g, alt])]
    except SystemExit:
        pass
    out = []
    try:
        out.append(first(c, nums, [rf"SAE {g} is the best choice", rf"{g} is the oil that provides the optimal level of fuel efficiency"], [g]))
    except SystemExit:
        out.append(first(c, nums, [rf"Recommended viscosity:? SAE {g}"], [g]))
    a = first(c, nums, [rf"If SAE {g}(?: oil)? is not available,?.{{0,120}}?SAE {alt}(?: motor| engine)? oil may be used", rf"SAE {alt} or {g}"], [alt])
    return out + ([a] if a not in out else [])

def oil(y, codes, d, eng, qt, l, g, alt, tie=None, cond=None, section=False):
    """tie: regex for the engine label, cited when the capacity quote does not name the engine."""
    for c in codes:
        src = [cap_src(c, qt, l)] + visc_src(c, g, alt, section)
        if tie:
            src.append(first(c, spec_pages(c), [tie]))
        r = {"field": "oil", "years": [y, y], "displacement_l": d, "engine": eng}
        if cond: r["condition"] = cond
        r.update({"grade": g, "alt_grades": [alt]})
        r.update({"capacity_qt": qt, "capacity_l": l, "src": src})
        add(r)

ZR, AZ = "1.8 L 4-cylinder (2ZR-FE)", "2.4 L 4-cylinder (2AZ-FE)"
ZRS, ZRA = "1.8 L 4-cylinder (2ZR-FE and 2ZR-FAE)", "1.8 L 4-cylinder (2ZR-FAE)"
M20, ZRH = "2.0 L 4-cylinder (M20A-FKS)", "1.8 L 4-cylinder hybrid (2ZR-FXE)"
for y in (2009, 2010, 2011):
    oil(y, SED[y], 1.8, ZR, 4.4, 4.2, "0W-20", "5W-20", section=y == 2011)
    oil(y, SED[y], 2.4, AZ, 4.0, 3.8, "0W-20", "5W-20")
# 2012-13 manuals still print the 2AZ-FE, but EPA lists no 2.4 L Corolla for those years: records left out
for y in (2012, 2013):
    oil(y, SED[y], 1.8, ZR, 4.4, 4.2, "0W-20", "5W-20", section=True)
for y in range(2014, 2020):
    oil(y, SED[y], 1.8, ZRS, 4.4, 4.2, "0W-20", "5W-20")
for y in IM:
    oil(y, IM[y], 1.8, ZRA, 4.4, 4.2, "0W-20", "5W-20", cond="iM")
for y in (2020, 2021, 2022):
    oil(y, SED[y], 1.8, ZRA, 4.4, 4.2, "0W-20", "5W-20", r"\[2ZR-FAE\]")
    oil(y, SED[y], 2.0, M20, 4.9, 4.6, "0W-16", "0W-20", r"\[M20A-FKS\]")
oil(2023, SED[2023], 2.0, M20, 4.9, 4.6, "0W-8", "0W-16")
for y in (2024, 2025, 2026):
    oil(y, SED[y], 2.0, M20, 4.4, 4.2, "0W-8", "0W-16")
for y in range(2019, 2023):
    oil(y, HB[y], 2.0, M20, 4.9, 4.6, "0W-16", "0W-20", cond="Hatchback")
for y in range(2023, 2027):
    oil(y, HB[y], 2.0, M20, 4.4, 4.2, "0W-8", "0W-16", cond="Hatchback")
for y in HYB:
    oil(y, HYB[y], 1.8, ZRH, 4.4, 4.2, "0W-16", "0W-20")

# ---- towing
NOTE0 = "Toyota does not recommend towing a trailer with this vehicle"
def lb_pages(c):
    return [i for i, t in enumerate(pages(c), 1) if "1500 lb" in t or "150 lb" in t or re.search(r"does not recommend\s+tow", t)]
def no_tow(y, codes, trim=None, d=None, eng=None):
    for c in codes:
        nums = [i for i, t in enumerate(pages(c), 1) if re.search(r"does not recommend\s+tow", t)]
        pats = [r"Toyota does not recommend tow-? ?ing a trailer with your vehicle", r"Toyota does not recommend tow-? ?ing"]
        if d:
            pats = [r"1\.8 L 4-cylinder \(2ZR-FE\) engine: Toyota does not recommend towing a trailer with your vehicle"]
        r = {"field": "towing", "years": [y, y]}
        if d: r.update({"displacement_l": d, "engine": eng})
        if trim: r["trim"] = trim
        r.update({"max_lb": 0, "note": NOTE0, "src": [first(c, nums, pats, ["recommend"])]})
        add(r)
def tow1500(y, codes, rx, d=None, eng=None):
    for c in codes:
        r = {"field": "towing", "years": [y, y]}
        if d: r.update({"displacement_l": d, "engine": eng})
        r.update({"max_lb": 1500, "tongue_lb": 150, "note": "trailer weight + cargo weight",
                  "src": [first(c, lb_pages(c), [rx], ["1500"]), first(c, lb_pages(c), [r"maximum 150 lb\. \(68 kg\)"], ["150"])]})
        add(r)
for y in (2009, 2010):
    tow1500(y, SED[y], r"Towing capacity 1500 lb\. \(680 kg\) \(trailer weight \+ cargo weight\)")
tow1500(2011, SED[2011], r"2\.4 L 4-cylinder \(2AZ-FE\) engine: 1500 lb\. \(680 kg\)", 2.4, AZ)
for y in (2011, 2012, 2013):
    no_tow(y, SED[y], d=1.8, eng=ZR)
for y in range(2014, 2027):
    no_tow(y, SED[y])
for y in HB:
    no_tow(y, HB[y], "Hatchback")
for y in HYB:
    no_tow(y, HYB[y], "Hybrid")
for y in IM:
    no_tow(y, IM[y], "iM")

# ---- tires: every size in the manual's tire specification tables (T-prefixed compact spares are skipped)
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
for table, trim in ((SED, None), (HYB, "Hybrid"), (HB, "Hatchback"), (IM, "iM")):
    for y, codes in table.items():
        tires(y, codes, trim)
for y in (2005, 2006, 2007, 2008):   # no readable manual; tires only, never overriding an OEM value
    ref = f"tp{y}"
    DOCS[ref] = {"doc": f"TirePressure.com: {y} Toyota Corolla Tire Pressure",
                 "url": f"https://tirepressure.com/{y}-toyota-corolla-tire-pressure",
                 "type": "third_party_reference", "accessed": ACCESSED}
    for row in tp_rows(D / f"tp_{y}.html"):
        R.append({"field": "tires", "years": [y, y], "size": row["size"], "trim": row["trims"][:150],
                  "src": [{"ref": ref, "quote": row["text"][:200]}]})

R.sort(key=lambda r: (["oil", "towing", "tires"].index(r["field"]), r["years"][0]))
OUT = ROOT / "data/manuals/toyota/corolla.yaml"
dump(str(OUT), "toyota/corolla", R)
txt = OUT.read_text().split("\n", 1)[1]
OUT.write_text("# Generated by tools/manuals/build_corolla.py: toyota.ca owner's manuals (quotes verified against the cited\n"
               "# PDF page), tirepressure.com (third_party_reference) for 2005-08 tires.\n" + txt)
