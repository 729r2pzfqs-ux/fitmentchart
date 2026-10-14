"""Gap-research chunk 2, verified against sources: F-150 tires and battery (+2026 oil), Civic oil 2006-2022.

Run after build_f150.py / add_wipers.py / add_f150_oil.py and build_civic.py.
Only values found in the cited documents are written; see git log for claims that were dropped.
"""
import re, subprocess, sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import cite, DOCS
from tirepressure import rows as tp_rows

def load(slug):
    return yaml.safe_load((ROOT / f"data/manuals/{slug}.yaml").read_text())
def save(slug, data, header):
    with open(ROOT / f"data/manuals/{slug}.yaml", "w") as fh:
        fh.write(header)
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, width=120)
def register(data, ref):
    data["sources"][ref] = {k: v for k, v in DOCS[ref].items() if k != "pdf"}

# ------------------------------------------------------------------ F-150
FT = ROOT / "data/cache/manuals/ford-techspecs"
f150 = load("ford/f-150")
f150["records"] = [r for r in f150["records"] if r["field"] not in ("tires", "battery")
                   and not (r["field"] == "oil" and r["years"] == [2026, 2026])]
for ref, title in (("ts2021", "2021 F-150 Technical Specs (Ford Motor Company)"),
                   ("ts2026", "2026 Ford F-150 Tech Specs (Ford Motor Company)"),
                   ("raptor2024", "2024 Ford Raptor and Raptor R Tech Specs (Ford Motor Company)")):
    DOCS[ref] = {"pdf": str(FT / f"{ref}.pdf"), "doc": title, "url": (FT / f"{ref}.url").read_text().strip(),
                 "type": "oem_spec_sheet", "accessed": "2026-10-13"}
    register(f150, ref)
R = []
def tire(y, size, src, trim=None, note=None):
    m = re.match(r"^((?:P|LT)?\d{3}/\d{2}R\d{2})(C)?$|^(\d{2}x\d{1,2}\.\d{1,2}R\d{2})(LT)?$", size)
    r = {"field": "tires", "years": [y, y], "size": size}
    if trim: r["trim"] = trim
    if note: r["note"] = note
    r["src"] = src
    R.append(r)
# Ford 2021 sheet, PDF p.6 (no trim mapping except Tremor)
for size, rx, note in (("245/70R17", r"245/70R17 black side wall \(BSW\) all-season tires", "standard; also OWL all-terrain"),
                       ("LT265/70R17C", r"LT265/70R17C BSW all-terrain tires", "standard"),
                       ("265/60R18", r"265/60R18 BSW all-season tires", "standard"),
                       ("275/65R18", r"275/65R18 OWL all-terrain tires", "standard"),
                       ("LT265/70R18C", r"LT265/70R18C OWL all-terrain tires", "standard"),
                       ("275/60R20", r"275/60R20 BSW all-season tires", "optional; also OWL/BSW all-terrain"),
                       ("275/50R22", r"275/50R22 BSW all-season tires", "optional")):
    tire(2021, size, [cite("ts2021", 6, rx, [size])], note=note)
tire(2021, "275/70R18", [cite("ts2021", 6, r"275/70R18 BSW all-terrain tires, Tremor", ["275/70R18"])], trim="Tremor", note="optional")
# Ford 2026 sheet, PDF p.7 (by trim)
for size, trims in (("245/70R17", "XL, XLT 4x2"), ("265/70R17", "XL 4x4"), ("265/60R18", "STX, Lariat 4x2"),
                    ("275/65R18", "STX, XLT, Lariat 4x4"), ("275/70R18", "Tremor"), ("275/60R20", "King Ranch, Platinum 4x2"),
                    ("275/60R20", "King Ranch, Platinum 4x4"), ("LT315/70R17", "Raptor"), ("265/70R17C", "XL Fleet, FX4 Package"),
                    ("265/60R18", "XLT 4x2"), ("265/70R18C", "XLT 4x4"), ("275/60R20", "STX, Lariat 4x2"),
                    ("275/60R20", "STX, Lariat 4x4"), ("275/50R22", "STX Lobo Package, King Ranch, Platinum"),
                    ("37x12.5R17", "Raptor 37 Package")):
    rx = re.escape(size) + r" all-(season|terrain) \(" + re.escape(trims) + r"\)"
    tire(2026, size, [cite("ts2026", 7, rx, [size])], trim=trims)
# Ford 2024 Raptor sheet, PDF p.3
tire(2024, "LT315/70R17", [cite("raptor2024", 3, r"LT315/70R17", ["LT315/70R17"])], trim="Raptor")
tire(2024, "37x12.5R17LT", [cite("raptor2024", 3, r"37x12\.5R17LT BFGoodrich All-Terrain T/A KO2 Tires", ["37x12.5R17LT"])],
     trim="Raptor R (optional on Raptor)")
# tirepressure.com (third_party_reference) for years without a Ford sheet; never for Lightning
for y in list(range(2005, 2021)) + [2022, 2023, 2024, 2025]:
    ref = f"tp{y}"
    url = f"https://tirepressure.com/{y}-ford-f-150-tire-pressure"
    f150["sources"][ref] = {"doc": f"TirePressure.com: {y} Ford F-150 Tire Pressure", "url": url,
                            "type": "third_party_reference", "accessed": "2026-10-13"}
    for row in tp_rows(ROOT / f"data/cache/web/tp_f150_{y}.html"):
        if "Lightning" in row["trims"] or (y == 2024 and "Raptor" in row["trims"]):
            continue
        tire(y, row["size"], [{"ref": ref, "quote": row["text"][:200]}], trim=row["trims"][:150])
# battery: Ford 2024 Raptor sheet, PDF p.1
bq = cite("raptor2024", 1, r"Battery group, CCA H7 AGM 80AH 800CCA", ["H7"])
for d, eng in ((3.5, "3.5L EcoBoost High-Output (Raptor)"), (5.2, "5.2L Supercharged V8 (Raptor R)")):
    R.append({"field": "battery", "years": [2024, 2024], "displacement_l": d, "engine": eng, "trim": "Raptor / Raptor R",
              "group": "H7", "cca": 800, "note": "AGM, 80 Ah; H7 = BCI group 94R", "src": [bq]})
# 2026 oil capacities, PDF p.2 (capacity only; the sheet prints no grade)
oq = cite("ts2026", 2, r"Oil Capacity \(quarts/liters\) 6\.0/5\.7 7\.75/7\.33 6\.0/5\.7 6\.0/5\.7 6\.0/5\.7 11\.5/10\.9", ["7.75"])
for d, eng, qt, l, cond in ((2.7, "2.7L EcoBoost V6", 6.0, 5.7, None), (5.0, "5.0L PFDI V8", 7.75, 7.33, None),
                            (3.5, "3.5L EcoBoost V6", 6.0, 5.7, None), (3.5, "3.5L PowerBoost Full Hybrid V6", 6.0, 5.7, "PowerBoost hybrid"),
                            (3.5, "3.5L EcoBoost V6 High-Output", 6.0, 5.7, "High-Output (Raptor)"),
                            (5.2, "5.2L Supercharged V8", 11.5, 10.9, None)):
    r = {"field": "oil", "years": [2026, 2026], "displacement_l": d, "engine": eng}
    if cond: r["condition"] = cond
    r.update({"capacity_qt": qt, "capacity_l": l, "src": [oq]}); R.append(r)
f150["records"].extend(R)
save("ford/f-150", f150, "# Generated: OEM towing guides/tech-spec sheets (quotes verified against the cited PDF page),\n"
                         "# f150hub.com and tirepressure.com (third_party_reference), Rain-X wiper pages.\n")
print("F-150 added", len(R))

# ------------------------------------------------------------------ Civic oil
HC = ROOT / "data/cache/manuals/honda-civic"
civic = load("honda/civic")
civic["records"] = [r for r in civic["records"] if not (r["field"] == "oil" and r["years"][0] >= 2006)]
TI = "https://techinfo.honda.com/rjanisis/pubs/"
MAN = {"NA0606": (2006, "2006 Civic Coupe Owner's Manual (31SVA600)", TI + "OM/NA0606/NA0606OM.pdf"),
       "NA0707": (2007, "2007 Civic Coupe Owner's Manual", TI + "OM/NA0707/NA0707OM.pdf"),
       "NA0808": (2008, "2008 Civic Sedan Owner's Manual", TI + "OM/NA0808/NA0808OM.pdf"),
       "NA0909": (2009, "2009 Civic Sedan Owner's Manual", TI + "OM/NA0909/NA0909OM.pdf"),
       "NA1010": (2010, "2010 Civic Sedan Owner's Manual", TI + "OM/NA1010/NA1010OM.pdf"),
       "NA1111": (2011, "2011 Civic Sedan Owner's Manual", TI + "OM/NA1111/NA1111OM.pdf"),
       "NC0606": (2006, "2006 Civic Hybrid Owner's Manual", TI + "OM/NC0606/NC0606OM.pdf"),
       "NC0707": (2007, "2007 Civic Hybrid Owner's Manual", TI + "OM/NC0707/NC0707OM.pdf"),
       "NC0808": (2008, "2008 Civic Hybrid Owner's Manual", TI + "OM/NC0808/NC0808OM.pdf"),
       "NC0909": (2009, "2009 Civic Hybrid Owner's Manual", TI + "OM/NC0909/NC0909OM.pdf"),
       "NC1010": (2010, "2010 Civic Hybrid Owner's Manual", TI + "OM/NC1010/NC1010OM.pdf"),
       "NC1111": (2011, "2011 Civic Hybrid Owner's Manual (NC1111)", TI + "OM/NC1111/NC1111OM.pdf"),
       "R01212": (2012, "2012 Civic Sedan Owner's Manual", TI + "om/r01212/r01212om.pdf"),
       "R0144D": (2014, "2014 Civic Sedan Owner's Manual", TI + "OM/R0144D/R0144DOM.pdf"),
       "AT2022": (2022, "2022 Civic Sedan Owner's Manual", TI + "OM/AH/AT202222OM/enu/AT202222OM.PDF"),
       "AT4022": (2022, "2022 Civic Hatchback Owner's Manual", TI + "OM/AH/AT402222OM/enu/AT402222OM.PDF")}
for c in ("TBA", "TGG", "TBG"):
    body = {"TBA": "Sedan", "TGG": "Hatchback", "TBG": "Coupe"}[c]
    for yy in range(17, 22):
        f = HC / f"A{c}{yy}.pdf"
        if f.exists():
            MAN[f"A{c}{yy}"] = (2000 + yy, f"20{yy} Civic {body} Owner's Manual", (HC / f"A{c}{yy}.url").read_text().strip())
for code, (y, doc, url) in MAN.items():
    DOCS[code] = {"pdf": str(HC / f"{code}.pdf"), "doc": doc + " (Honda)", "url": url, "type": "oem_manual", "accessed": "2026-10-13"}
    register(civic, code)

def find_page(code, *patterns):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", DOCS[code]["pdf"]], capture_output=True, text=True).stdout).group(1))
    txt = open(HC / f"{code}.txt", errors="replace").read().split("\f")
    for i, p in enumerate(txt, 1):
        f = re.sub(r"\s+", " ", p)
        if all(re.search(x, f) for x in patterns):
            return i
    raise SystemExit(f"{code}: page with {patterns} not found")

C = []
def oil(y, d, eng, grade, qt, l, src, cond=None):
    r = {"field": "oil", "years": [y, y], "displacement_l": d, "engine": eng}
    if cond: r["condition"] = cond
    r.update({"grade": grade, "capacity_qt": qt, "capacity_l": l, "src": src}); C.append(r)
for code in ("NA0606", "NA0707", "NA0808", "NA0909", "NA1010", "NA1111"):
    y = MAN[code][0]
    cp = find_page(code, r"Including", r"3\.9 US qt \(3\.7", r"4\.6 US qt \(4\.4")
    gp = find_page(code, r"All models except Si|DX, Canadian DX-G, LX, and EX", r"preferred 5W-20 lubricant|5W-20 oil is formulated")
    c39 = cite(code, cp, r"3\.9 US qt \(3\.7\s*\)\s*＊3", ["3.9"])
    c46 = cite(code, cp, r"4\.6 US qt \(4\.4\s*\)\s*＊4", ["4.6"])
    fn3 = cite(code, cp, r"＊3\s*:\s*(Except Si|U\.S\.: DX, LX, EX)")
    fn4 = cite(code, cp, r"＊4\s*:\s*Si")
    g20 = cite(code, gp, r"(All models except Si:|DX, Canadian DX-G, LX, and EX models:).{0,60}?5W-20", ["5W-20"])
    g30 = cite(code, gp, r"An oil with a viscosity of 5W-30 is preferred", ["5W-30"])
    gsi = cite(code, gp, r"Si model:")
    oil(y, 1.8, "1.8 L SOHC i-VTEC (all models except Si)", "5W-20", 3.9, 3.7, [c39, fn3, g20])
    oil(y, 2.0, "2.0 L DOHC i-VTEC (Si)", "5W-30", 4.6, 4.4, [c46, fn4, gsi, g30])
for code in ("NC0606", "NC0707", "NC0808", "NC0909", "NC1010", "NC1111"):
    y = MAN[code][0]
    cp = find_page(code, r"Including filter 3\.4 US qt")
    gp = find_page(code, r"0W-20 is not available|0W-20 oil recommended")
    oil(y, 1.3, "1.3 L i-VTEC IMA hybrid", "0W-20", 3.4, 3.2,
        [cite(code, cp, r"Including filter 3\.4 US qt \(3\.2", ["3.4"]),
         cite(code, gp, r"(low- ?viscosity |the viscosity )?0W-20 oil recommended|if 0W-20 is not available", ["0W-20"])],
        cond="Civic Hybrid")
for code, big in (("R01212", "2.4"), ("R0144D", "2.4")):
    y = MAN[code][0]
    cp = find_page(code, r"change capacity", r"3\.9 US qt")
    gp = find_page(code, r"Premium-grade 0W-20 detergent oil")
    g = cite(code, gp, r"Premium-grade 0W-20 detergent oil", ["0W-20"])
    oil(y, 1.8, "1.8 L engine models", "0W-20", 3.9, 3.7, [cite(code, cp, r"1\.8 ℓ engine models\s*3\.9 US qt \(3\.7 L\)|3\.9 US qt \(3\.7 L\)", ["3.9"]), g])
    oil(y, 2.4, "2.4 L engine models (Si)", "0W-20", 4.4, 4.2, [cite(code, cp, r"4\.4 US qt \(4\.2 L\)", ["4.4"]), g])
for code in [k for k in MAN if k.startswith("AT")]:
    y = MAN[code][0]
    hatch = code.startswith("ATGG")
    cp = find_page(code, r"change capacity", r"3\.7 US qt")
    gp = find_page(code, r"Premium-grade 0W-20 detergent oil")
    g = cite(code, gp, r"Premium-grade 0W-20 detergent oil", ["0W-20"])
    oil(y, 1.5, "1.5 L turbo engine models", "0W-20", 3.7, 3.5, [cite(code, cp, r"3\.7 US qt \(3\.5 L\)", ["3.7"]), g])
    if hatch:
        oil(y, 2.0, "2.0 L turbo engine models (Type R)", "0W-20", 5.7, 5.4, [cite(code, cp, r"5\.7 US qt \(5\.4 L\)", ["5.7"]), g],
            cond="Hatchback 2.0 L (Type R)")
    else:
        oil(y, 2.0, "2.0 L engine models", "0W-20", 4.4, 4.2, [cite(code, cp, r"4\.4 US qt \(4\.2 L\)", ["4.4"]), g])
civic["records"].extend(C)
save("honda/civic", civic, "# Generated from Honda owner's manuals (quotes verified against the cited PDF page) and Rain-X wiper pages.\n")
print("Civic oil added", len(C))
