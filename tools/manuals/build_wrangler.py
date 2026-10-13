import sys, re, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import DOCS, cite, dump, page_text
D = str(ROOT / "data/cache/manuals/jeep-wrangler/") + "/"
M = "https://vehicleinfo.mopar.com/assets/publications/"
OM = {2005: ("om2005", M + "en-us/Jeep/2005/Wrangler/1590.pdf", "2005 Jeep Wrangler Owner's Manual"),
      2016: ("om2016", M + "en-us/Jeep/2016/Wrangler/73.pdf", "2016 Jeep Wrangler Owner's Manual"),
      2017: ("om2017", M + "en-us/Jeep/2017/Wrangler/2049.pdf", "2017 Jeep Wrangler Owner's Manual"),
      2018: ("om2018jl", M + "en-us/Jeep/2018/Wrangler_JL/9510.pdf", "2018 Jeep Wrangler (JL) Owner's Manual"),
      2021: ("om2021", M + "en-us/Jeep/2021/Wrangler/5690670_21_JL_OM_EN_USC_DIGITAL_E5.pdf", "2021 Jeep Wrangler Owner's Manual"),
      2022: ("om2022", M + "en-us/Jeep/2022/Wrangler/5690672_22_JL_OM_EN_USC_DIGITAL_E3.pdf", "2022 Jeep Wrangler Owner's Manual"),
      2023: ("om2023", M + "en-us/Jeep/2023/Wrangler/5690673_23_JL_OM_EN_USC_DIGITAL_E3.pdf", "2023 Jeep Wrangler Owner's Manual"),
      2026: ("om2026", M + "en-us-ca/2026/Jeep/Wrangler/102316_26_JL_OM_EN_USC_DIGITAL_E1.pdf", "2026 Jeep Wrangler Owner's Manual (US/Canada)")}
for y, (c, u, name) in OM.items():
    DOCS[c] = {"pdf": D + c + ".pdf", "doc": name, "url": u, "type": "oem_manual", "accessed": "2026-10-13"}
ENG = {y: {e["displacement_l"] for e in v["engines"]} for y, v in
       json.load(open(str(ROOT / "data/models/jeep/wrangler.json")))["years"].items()}
R = []
def oil(y, d, eng, grade, qt, l, src, cond=None):
    if d not in ENG[str(y)]:
        return
    r = {"field": "oil", "years": [y, y], "displacement_l": d, "engine": eng}
    if cond: r["condition"] = cond
    if grade: r["grade"] = grade
    r.update({"capacity_qt": qt, "capacity_l": l, "src": src})
    R.append(r)

# 2005 (TJ): grade printed inside the capacities table
c = "om2005"
oil(2005, 2.4, "2.4 Liter Engine", "5W-30", 5.0, 4.7, [cite(c, 295, r"2\.4 Liter Engine \(SAE 5W-30, API Certified Engine Oil\) 5 Qts 4\.7 Liters", ["5 Qts"])])
oil(2005, 4.0, "4.0 Liter Engine", "10W-30", 6.0, 5.7, [cite(c, 295, r"4\.0 Liter Engine \(SAE 10W-30, API Certified Engine Oil\) 6 Qts 5\.7 Liters", ["6 Qts"])])
# 2016-2017 (JK): 3.6 L only
for y, cp, vp in ((2016, 672, 612), (2017, 436, 375)):
    c = OM[y][0]
    oil(y, 3.6, "3.6L Engine", "5W-20", 6.0, 5.6, [cite(c, cp, r"Engine Oil with Filter 3\.6L Engine 6 Quarts 5\.6 Liters", ["6 Quarts"]),
                                                  cite(c, vp, r"Engine Oil Viscosity \(SAE Grade\) — 3\.6L Engine (MOPAR|Mopar) SAE 5W-20", ["5W-20"])])
# 2018+ (JL)
JL = {2018: (511, 514, 514, None), 2021: (359, 360, 360, None), 2022: (356, 357, 357, None),
      2023: (362, 363, 363, None), 2026: (354, 351, 352, 352)}
for y, (cp, v20, v36, v64) in JL.items():
    c = OM[y][0]
    unit = r"(?:Quarts|qt) (?:4\.73) (?:Liters|L)"
    g20 = cite(c, v20, r"Engine Oil — 2\.0L Engine We recommend (you use|using) Mopar®? API (SN PLUS|SP/GF-6A) Certified SAE 5W-30", ["5W-30"])
    g36 = cite(c, v36, r"Engine Oil — 3\.6L Engine We recommend (you use|using) (API Certified|Mopar®) SAE 0W-20", ["0W-20"])
    oil(y, 2.0, "2.0L Engine", "5W-30", 5.0, 4.73, [cite(c, cp, r"2\.0L Engine 5 " + unit, ["5"]), g20])
    oil(y, 3.6, "3.6L Engine", "0W-20", 5.0, 4.73, [cite(c, cp, r"3\.6L Engine 5 " + unit, ["5"]), g36])
    if y in (2021, 2022, 2023):
        oil(y, 3.0, "3.0L Diesel Engine", None, 9.0, 8.5, [cite(c, cp, r"3\.0L Diesel Engine 9 (Quarts|qt) 8\.5 (Liters|L)", ["9"])])
    if v64:
        oil(y, 6.4, "6.4L Engine", "0W-40", 7.5, 7.1, [cite(c, cp, r"6\.4L Engine 7\.5 qt 7\.1 L", ["7.5"]),
                                                       cite(c, v64, r"Engine Oil — 6\.4L Engine We recommend using Mopar® API Certified SAE 0W-40", ["0W-40"])])

# towing
def tow(y, d, eng, cab, mx, tongue, gcwr, src, axle=None, trim=None):
    if d not in ENG[str(y)]:
        return
    r = {"field": "towing", "years": [y, y], "displacement_l": d, "engine": eng, "drive": "4WD", "cab": cab}
    if trim: r["trim"] = trim
    if axle: r["axle"] = axle
    r.update({"max_lb": mx, "tongue_lb": tongue, "gcwr_lb": gcwr, "src": src})
    R.append(r)
ROW = re.compile(r"(3\.6L/ ?(?:Manual|Automatic)?) (\d\.\d\d) (Two|Four)–Door ([\d,]+) lbs (\d+) sq ft ([\d,]+) lbs ([\d,]+) lbs (?:\(\d+ kg\) )?(Automatic )?(\w+) Model")
for y, pages in ((2016, (560, 561, 562)), (2017, (316, 317, 318))):
    c = OM[y][0]
    for p in pages:
        for m in ROW.finditer(page_text(DOCS[c]["pdf"], p)):
            trans = "Manual" if "Manual" in m.group(1) else "Automatic"
            tow(y, 3.6, f"3.6L/{trans}", f"{m.group(3)}-Door", int(m.group(6).replace(",", "")), int(m.group(7).replace(",", "")),
                int(m.group(4).replace(",", "")), [cite(c, p, re.escape(m.group(0)), [m.group(6)])], axle=m.group(2), trim=m.group(9))
for y, p in ((2018, 368), (2021, 167), (2022, 167), (2023, 168)):
    c = OM[y][0]
    lb = r"lbs? \(3,?\s?\d{3} kg\)?"
    for eng, d in (("2.0L", 2.0), ("3.6L", 3.6)):
        tow(y, d, eng, "Two-Door", 2000, 200, 8016, [cite(c, p, r"Two–Door 8,016 lbs?.{0,40}?2,000 lbs?.{0,20}?200 lbs?", ["2,000"])])
        tow(y, d, eng, "Four-Door", 3500, 350, 8117, [cite(c, p, r"Four–Door 8,117 lbs?.{0,40}?3,500 lbs?.{0,30}?350 lbs?", ["3,500"])])
    if y >= 2021:
        tow(y, 3.0, "3.0L Diesel", "Four-Door", 3500, None, 8427, [cite(c, p, r"3\.0L Diesel Four–Door 8,427 lb.{0,60}?3,500 lb", ["3,500"])])
for r in R:
    if r.get("tongue_lb") is None: r.pop("tongue_lb", None)
dump(str(ROOT / "data/manuals/jeep/wrangler.yaml"), "jeep/wrangler", R)
from collections import Counter
print(sorted(Counter((r["years"][0], r["field"]) for r in R).items()))
