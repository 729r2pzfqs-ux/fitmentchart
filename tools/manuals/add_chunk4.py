"""Gap-research chunk 4, verified: Silverado 1500 towing (GM trailering guides/charts), oil (GM TechLink
engine-oil-capacity charts 2021-2026) and tires (tirepressure.com, third_party_reference). Battery: no
OEM/verifiable source found, nothing added. Run after build_silverado.py and add_wipers.py.
"""
import json, re, subprocess, sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import cite, DOCS, page_text
from gmtow2 import best, rows as gm_rows
from tirepressure import rows as tp_rows

Y = ROOT / "data/manuals/chevrolet/silverado-1500.yaml"
data = yaml.safe_load(Y.read_text())
ENG = {y: {e["displacement_l"] for e in v["engines"]} for y, v in
       json.load(open(ROOT / "data/models/chevrolet/silverado-1500.json"))["years"].items()}
CS = ROOT / "data/cache/manuals/chevy-silverado"
TL = ROOT / "data/cache/manuals/gm-techlink"
TOW_YEARS = {2017, 2022, 2023, 2024, 2025, 2026}
OIL_YEARS = set(range(2021, 2027))
data["records"] = [r for r in data["records"] if not (
    (r["field"] == "towing" and r["years"][0] in TOW_YEARS) or
    (r["field"] == "oil" and r["years"][0] in OIL_YEARS) or
    (r["field"] == "tires" and any(data["sources"].get(s["ref"], {}).get("type") == "third_party_reference" for s in r["src"])))]
R = []
def reg(ref, pdf, doc, url, typ):
    DOCS[ref] = {"pdf": str(pdf), "doc": doc, "url": url, "type": typ, "accessed": "2026-10-14"}
    data["sources"][ref] = {k: v for k, v in DOCS[ref].items() if k != "pdf"}

# ---------------------------------------------------------------- towing
reg("tg2017", CS / "tg2017.pdf", "2017 Chevrolet Trailering Guide (GM)", (CS / "tg2017.url").read_text().strip(), "oem_towing_guide")
data["sources"]["tg2017"]["note"] = "GM-published guide; copy hosted by a dealer site (xr793.com)"
for y, ref, title in ((2022, "tg2022", "2022 Chevrolet Trailering Guide"), (2023, "tg2023", "2023 Chevrolet Trailering Guide"),
                      (2024, "tg2024", "2024 Chevrolet Trailering Guide"), (2025, "tg2025", "2025 Chevrolet Trailering Guide"),
                      (2026, "tg2026m", "2026 Silverado 1500 Max Trailering chart")):
    reg(ref, CS / f"{ref}.pdf", title + " (Chevrolet)", (CS / f"{ref}.url").read_text().strip(), "oem_towing_guide")
def tow(y, d, eng, mx, gcwr, src, axle=None, pkg=None, note=None, trim=None):
    if d not in ENG[str(y)]:
        return
    r = {"field": "towing", "years": [y, y], "displacement_l": d, "engine": eng}
    if trim: r["trim"] = trim
    if axle: r["axle"] = axle
    r.update({"max_lb": mx, "gcwr_lb": gcwr})
    if pkg: r["package"] = pkg
    if note: r["note"] = note
    r["src"] = src; R.append(r)
# 2017 guide p.9 (engine labels sit between their axle rows; read by hand)
for d, eng, axle, gcwr, mx, rx, pkg in (
        (4.3, "EcoTec3 4.3L V6", "3.42", 12800, 7600, r"3\.42 12,800 — — 7,600", None),
        (5.3, "EcoTec3 5.3L V8", "3.42", 15000, 9800, r"3\.42 15,000 — 9,800", None),
        (5.3, "EcoTec3 5.3L V8 with Max Trailering Package", "3.73", 16700, 11100, r"3\.73 16,700 (— )+11,100", "Max Trailering Package"),
        (5.3, "EcoTec3 5.3L V8 (8-speed automatic) with Max Trailering Package", "3.42", 16700, 11000, r"3\.42 16,700 (— )*[\d,— ]{0,40}?11,000", "Max Trailering Package"),
        (6.2, "EcoTec3 6.2L V8", "3.23", 15000, 9400, r"EcoTec3 6\.2L V8 3\.23 15,000 (— )+9,400", None),
        (6.2, "EcoTec3 6.2L V8 with Max Trailering Package", "3.42", 18200, 12500, r"18,200 .{0,80}?12,500", "Max Trailering Package")):
    tow(2017, d, eng, mx, gcwr, [cite("tg2017", 9, rx, [f"{mx:,}"])], axle=axle, pkg=pkg,
        note="max conventional rating across cab/box/drive for this row")
# 2022-2025 guides: max per engine from (engine, GCWR, max) rows
GUIDE = {2022: ("tg2022", [33, 34], "new body"), 2023: ("tg2023", [33, 34], None), 2024: ("tg2024", [26, 27], None),
         2025: ("tg2025", [26, 27], None)}
DISP = {"2.7L TurboMax": 2.7, "5.3L EcoTec3 V8": 5.3, "6.2L EcoTec3 V8": 6.2, "Duramax 3.0L I-6 Turbo-Diesel": 3.0}
for y, (ref, pages, trim) in GUIDE.items():
    for k, r in best(DOCS[ref]["pdf"], pages).items():
        if k not in DISP:
            continue
        tow(y, DISP[k], k, r["max"], r["gcwr"], [cite(ref, r["page"], re.escape(r["text"]), [f"{r['max']:,}"])],
            trim=("Silverado 1500 (new for 2022)" if trim else None),
            note="max conventional rating across cab/bed/drive; footnoted packages (Max Trailering, 20-inch wheels) apply")
    for p in pages:  # ZR2 rows are labelled in the model column
        t = page_text(DOCS[ref]["pdf"], p)
        for m in re.finditer(r"ZR2 4x4 (6\.2L (?:EcoTec3®? )?V8|Duramax®? 3\.0L I-6) (\d{2},\d{3}) (\d{1,2},\d{3})", t):
            d = 6.2 if "6.2" in m.group(1) else 3.0
            tow(y, d, m.group(1) + " (ZR2)", int(m.group(3).replace(",", "")), int(m.group(2).replace(",", "")),
                [cite(ref, p, re.escape(m.group(0)), [m.group(3)])], trim="ZR2")
for k, r in best(DOCS["tg2022"]["pdf"], [38, 39]).items():  # 2022 carry-over Silverado 1500 LTD
    if k in DISP:
        tow(2022, DISP[k], k, r["max"], r["gcwr"], [cite("tg2022", r["page"], re.escape(r["text"]), [f"{r['max']:,}"])],
            trim="Silverado 1500 LTD (carry-over body)", note="max conventional rating across cab/bed/drive")
# 2026 chart (matrix; engine labels centred between their GCWR rows; read by hand)
for d, eng, gcwr, mx, rx, pkg, trim in (
        (2.7, "2.7L Turbo", 14500, 9500, r"14,500 9,300 9,100 9,000 9,000 9,300 9,000 – 9,500", None, None),
        (5.3, "5.3L V8", 16800, 11400, r"16,8003 11,300 11,200 11,000 11,000 11,400", "Max Trailering Package", None),
        (6.2, "6.2L V8", 19100, 13200, r"19\.100 4 – – 13,200 13,200", "RST with Max Trailering Package and 20-inch wheels", None),
        (6.2, "6.2L V8 (ZR2)", 15000, 8800, r"6\.2L V8 \(ZR2\) 15,000 – – 8,800", None, "ZR2"),
        (3.0, "Duramax 3.0L I-6", 19100, 13300, r"19\.1005 13,200 13,100 13,000 12,800 13,300", "Max Trailering Package and 20-inch wheels", None),
        (3.0, "Duramax 3.0L I-6 (ZR2)", 15000, 8700, r"Duramax 3\.0L I-6 \(ZR2\) 15,000 – – 8,700", None, "ZR2")):
    tow(2026, d, eng, mx, gcwr, [cite("tg2026m", 1, rx, [f"{mx:,}"])], pkg=pkg, trim=trim,
        note="max across cab/bed/drive columns" if not trim else None)

# ---------------------------------------------------------------- oil: GM TechLink charts
TLDOC = {2021: "tl21", 2022: "tl22", 2023: "tl23", 2024: "tl24", 2025: "tl25", 2026: "tl26"}
for y, ref in TLDOC.items():
    reg(ref, TL / f"{ref}.pdf", f"GM TechLink: {y} Engine Oil Capacities (with filter)", (TL / f"{ref}.url").read_text().strip(), "oem_spec_sheet")
    # Rows read from the Silverado 1500 block of each chart (the same rows also appear for sister GM trucks,
    # so quotes prove the value is printed on the chart; the model association is from the Silverado 1500 block).
    rows = []
    if y <= 2025:
        rows += [(2.7, "2.7L L4 L3B", "aluminum oil pan", "dexos1", "5W-30", 5.5, 5.2, r"L3B( with)?( 2\.7L L4)? 5\.2 5\.5 dexos1 5W-30"),
                 (2.7, "2.7L L4 L3B", "plastic oil pan", "dexos1", "5W-30", 6.0, 5.7, r"L3B( with)?( 2\.7L L4)? 5\.7 6\.0 dexos1 5W-30")]
    else:
        rows += [(2.7, "2.7L L4 L3B", "aluminum or plastic oil pan", "dexos1", "5W-30", 6.0, 5.7, r"2\.7L L4 aluminum pan 5\.7 6\.0 dexos1 5W-30")]
    dz = "LM2" if y <= 2022 else "LZ0"
    rows.append((3.0, f"3.0L L6 Diesel {dz}", None, "dexosD", "0W-20", 7.0, 6.6, rf"3\.0L L6 Diesel {dz} 6\.6 7\.0 dexosD 0W-20"))
    if y == 2021:
        rows.append((4.3, "4.3L V6 LV3", None, "dexos1", "5W-30", 6.0, 5.7, r"4\.3L V6 LV3 5\.7 6\.0 dexos1 5W-30"))
    v8 = "L82, L84" if y <= 2022 else "L84"
    rows.append((5.3, f"5.3L V8 {v8}", None, "dexos1", "0W-20", 8.0, 7.6, rf"5\.3L V8 {v8} 7\.6 8\.0 dexos1 0W-20"))
    rows.append((6.2, "6.2L V8 L87", None, "dexos1", "0W-20", 8.0, 7.6, r"6\.2L V8 L87 7\.6 8\.0 dexos1 0W-20"))
    for d, eng, cond, spec, grade, qt, lt, rx in rows:
        if d not in ENG[str(y)]:
            continue
        r = {"field": "oil", "years": [y, y], "displacement_l": d, "engine": eng}
        if cond: r["condition"] = cond
        r.update({"grade": grade, "spec": spec, "capacity_qt": qt, "capacity_l": lt,
                  "src": [cite(ref, 1, rx, [str(qt)]), cite(ref, 1, r"Silverado 1500")]})
        if y == 2022:
            r["note"] = "same values listed for Silverado 1500 and Silverado 1500 LTD"
        R.append(r)

# ---------------------------------------------------------------- tires: tirepressure.com
for y in range(2005, 2027):
    if y == 2019:
        continue  # 2019 sizes come from the 1500-only owner manual
    ref = f"tp{y}"
    data["sources"][ref] = {"doc": f"TirePressure.com: {y} Chevrolet Silverado 1500 Tire Pressure",
                            "url": f"https://tirepressure.com/{y}-chevrolet-silverado-1500-tire-pressure",
                            "type": "third_party_reference", "accessed": "2026-10-14"}
    for row in tp_rows(ROOT / f"data/cache/web/tp_silv_{y}.html"):
        R.append({"field": "tires", "years": [y, y], "trim": row["trims"][:150], "size": row["size"],
                  "src": [{"ref": ref, "quote": row["text"][:200]}]})

data["records"].extend(R)
with open(Y, "w") as fh:
    fh.write("# Generated from GM owner manuals, GM/Chevrolet trailering guides, GM TechLink oil charts (quotes verified\n"
             "# against the cited PDF page), tirepressure.com (third_party_reference) and Rain-X wiper pages.\n")
    yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, width=120)
from collections import Counter
print(Counter((r["field"], r["years"][0]) for r in R if r["field"] != "tires"))
print("tires", sum(r["field"] == "tires" for r in R))
