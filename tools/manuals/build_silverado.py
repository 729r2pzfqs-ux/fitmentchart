import sys, re, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import DOCS, cite, dump, page_text
from gmold import rows as old_rows
from gmtow import rows as tg_rows

D = str(ROOT / "data/cache/manuals/chevy-silverado/") + "/"
ENG = {y: {e["displacement_l"] for e in v["engines"]} for y, v in
       json.load(open(str(ROOT / "data/models/chevrolet/silverado-1500.json")))["years"].items()}
CT = "https://chevytrucks.org/wp-content/uploads/2020/07/{y}-Chevy-Silverado-1500-Owners-Manual.pdf"
OM = {y: f"om{y}" for y in (2005, 2006, 2007, 2008, 2009, 2010, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020)}
for y, c in OM.items():
    DOCS[c] = {"pdf": D + c + ".pdf",
               "doc": f"{y} Chevrolet Silverado{' Classic' if y == 2007 else ''} Owner Manual (GM)",
               "url": CT.format(y=y), "type": "oem_manual", "accessed": "2026-10-13",
               "note": "GM-published owner manual; copy hosted by chevytrucks.org"}
TG = {2011: "https://FifthWheelSt.com/documents/silverado/Chevy_2011_Trailering_Guide.pdf",
      2012: "https://FifthWheelSt.com/documents/silverado/2012_Chevrolet_Trailering_Guide.pdf",
      2013: "https://FifthWheelSt.com/documents/silverado/2013-chevrolet_silverado_towing_guide.pdf",
      2014: "https://FifthWheelSt.com/documents/silverado/2014_chevrolet_silverado_towing_guide.pdf",
      2019: "https://www.chevrolet.ca/content/dam/chevrolet/na/canada/english/index/shared-assets/my19-cdn-trailering-guide-brochure-english.pdf",
      2020: "https://FifthWheelSt.com/documents/silverado/2020-chevrolet-trailering-guide.pdf"}
for y, u in TG.items():
    DOCS[f"tg{y}"] = {"pdf": D + f"tg{y}.pdf", "doc": f"{y} Chevrolet Trailering Guide (GM)", "url": u,
                      "type": "oem_towing_guide", "accessed": "2026-10-13",
                      **({"note": "GM-published guide; copy hosted by FifthWheelSt.com"} if "FifthWheel" in u else
                         {"note": "GM Canada trailering guide"})}

def disp(label):
    m = re.search(r"\b(\d)(\d)00\b|(\d\.\d)L?", label)
    return float(f"{m.group(1)}.{m.group(2)}") if m.group(1) else float(m.group(3))

R = []
# ------------------------------------------------------------------ oil
VISC = {  # year: (page, [(regex, grade, applies_to displacements or None=all)])
    2005: (414, [(r"SAE 5W-30 is best for your vehicle", "5W-30", None)]),
    2006: (424, [(r"SAE 5W-30 is best for your vehicle", "5W-30", None)]),
    2007: (484, [(r"SAE 5W-30 is best for your vehicle", "5W-30", None)]),
    2008: (423, [(r"SAE 5W-30 is best for your vehicle", "5W-30", None)]),
    2009: (427, [(r"SAE 5W-30 is best for the vehicle", "5W-30", None)]),
    2010: (463, [(r"SAE 5W-30 is best for the vehicle", "5W-30", None)]),
    2012: (433, [(r"SAE 5W.30 is the best viscosity grade for the vehicle", "5W-30", None)]),
    2013: (384, [(r"SAE 5W-30 is the best viscosity grade for the vehicle", "5W-30", None)]),
    2014: (382, [(r"SAE 0W-20 is the best viscosity grade for the 5\.3L and 6\.2L V8 engines", "0W-20", {5.3, 6.2}),
                 (r"SAE 5W-30 is the best viscosity grade for the 4\.3L V6, and 6\.0L V8 engines", "5W-30", {4.3, 6.0})]),
    **{y: (p, [(r"Use SAE 0W-20 viscosity grade for (engine damage not covered by the )?the 5\.3L and 6\.2L V8 engines", "0W-20", {5.3, 6.2}),
               (r"Use SAE 5W-30 viscosity grade for the 4\.3L V6, and 6\.0L V8 engines", "5W-30", {4.3, 6.0})])
       for y, p in ((2015, 390), (2016, 372), (2017, 362))},
    2018: (346, [(r"For the 5\.3L and 6\.2L V8 engines, use SAE 0W-20 viscosity grade engine oil", "0W-20", {5.3, 6.2}),
                 (r"4\.3L V6 and 6\.0L V8 engines, use SAE 5W-30 viscosity grade engine oil", "5W-30", {4.3, 6.0})]),
    2019: (325, [(r"Use SAE 0W-20 viscosity grade engine oil for the 5\.3L and 6\.2L V8 engines", "0W-20", {5.3, 6.2}),
                 (r"Use SAE 5W-30 viscosity grade engine oil for the 2\.7L L4 and 4\.3L V6 engines", "5W-30", {2.7, 4.3})]),
    2020: (338, [(r"Use SAE 0W-20 viscosity grade engine oil for the 5\.3L and 6\.2L V8 engines", "0W-20", {5.3, 6.2}),
                 (r"Use SAE 5W-30 viscosity grade engine oil for the 2\.7L L4, 4\.3L V6 and 6\.6L V8 engines", "5W-30", {2.7, 4.3})]),
}
CAP = {2005: [530], 2006: [535], 2007: [609], 2008: [539], 2009: [539], 2010: [570], 2012: [559], 2013: [497],
       2014: [498], 2015: [507], 2016: [479], 2017: [469], 2018: [458], 2019: [433], 2020: [455, 456]}
CAPRE = re.compile(r"((?:(?:\d{4}|\d\.\dL?) (?:V6|V8|L4)(?: Engine)?[;,]? ?)+)(?:(?:– )?1500 Series ?(?:\(L\d\d\) )?)?(?:[^0-9;]{0,40}?)(\d+\.\d) (qt|L) (\d+\.\d) (qt|L)")
for y, pages in CAP.items():
    c = OM[y]
    vp, vrules = VISC[y]
    for pg in pages:
        text = page_text(DOCS[c]["pdf"], pg)
        i = text.find("Engine Oil with Filter")
        seg = text[i:i + 420] if i >= 0 else text[:420]
        if i < 0 and pg == pages[0]:
            raise SystemExit(f"no oil block {c} p.{pg}")
        for m in CAPRE.finditer(seg):
            labels = re.findall(r"(?:\d{4}|\d\.\dL?) (?:V6|V8|L4)", m.group(1))
            vals = {m.group(3): float(m.group(2)), m.group(5): float(m.group(4))}
            for lab in labels:
                d = disp(lab)
                if d not in ENG[str(y)]:
                    continue
                if d == 6.0 and 2009 <= y <= 2013:
                    continue  # EPA's 1500 6.0 L these years is the Hybrid; the table row may be the HD 6.0 L
                grade = next((g for rx, g, ap in vrules if ap is None or d in ap), None)
                if grade is None:
                    continue
                vrx = next(rx for rx, g, ap in vrules if g == grade and (ap is None or d in ap))
                src = [cite(c, pg, re.escape(m.group(0)), [str(vals["qt"])]), cite(c, vp, vrx, [grade.replace("-", "")[:2]])]
                R.append({"field": "oil", "years": [y, y], "displacement_l": d, "engine": lab.strip(),
                          **({"condition": "Silverado Classic (GMT800)"} if y == 2007 else {}),
                          "grade": grade, "capacity_qt": vals["qt"], "capacity_l": vals["L"], "src": src})

# ------------------------------------------------------------------ towing: 2005-2010 manuals (configuration rows)
OLDP = {2005: (362, 367), 2006: (374, 381), 2007: (426, 431), 2008: (370, 376), 2009: (380, 389), 2010: (415, 426)}
for y, (a, b) in OLDP.items():
    c = OM[y]
    for r in old_rows(DOCS[c]["pdf"], range(a, b + 1)):
        lab = re.sub(r"\s*\((?:[a-z])\)|\*+", "", r["engine"]).strip()
        d = disp(lab)
        if d not in ENG[str(y)]:
            continue
        sec = r["section"]
        drive = "2WD" if re.match(r"^C|.*2WD", sec) else "4WD"
        cab = re.sub(r"^([CK]-1500|1500 Series (2WD|4WD))\s*", "", sec)
        cab = re.sub(r"\s*\((2WD|4WD)\)", "", cab).strip()
        pkg = None
        if re.search(r"NHT|Max Trailering", lab): pkg = "NHT Max Trailering Package"
        elif re.search(r"K5L|HD Cooling", lab): pkg = "K5L Heavy-Duty Cooling Package"
        R.append({"field": "towing", "years": [y, y], "displacement_l": d, "engine": lab, "drive": drive, "cab": cab,
                  "axle": r["axle"], "max_lb": r["max"], "gcwr_lb": r["gcwr"],
                  **({"package": pkg} if pkg else {}),
                  **({"note": "Silverado Classic (GMT800)"} if y == 2007 else {}),
                  "src": [cite(c, r["page"], re.escape(r["line"]), [f"{r['max']:,}"])]})

# ------------------------------------------------------------------ towing: trailering guides (max per engine row)
def tg_rec(y, page, label, axle, gcwr, mx, quote_rx, cab=None, drive=None, pkg=None, note=None):
    d = disp(label)
    if d not in ENG[str(y)]:
        return
    r = {"field": "towing", "years": [y, y], "displacement_l": d, "engine": label}
    if drive: r["drive"] = drive
    if cab: r["cab"] = cab
    if axle: r["axle"] = axle
    r["max_lb"] = mx
    if gcwr: r["gcwr_lb"] = gcwr
    if pkg: r["package"] = pkg
    if note: r["note"] = note
    r["src"] = [cite(f"tg{y}", page, quote_rx, [f"{mx:,}"])]
    R.append(r)

for y in (2011, 2012):  # per-engine columns; max per engine, read from the table
    tg_rec(y, 8, "Vortec 4.3L V6", "3.73", None, 5400, r"Standard Box 2WD 3\.73 5,400", "Regular Cab Standard Box", "2WD")
    tg_rec(y, 8, "Vortec 4.8L V8", "3.73", None, 7200, r"Standard Box 2WD 3\.73 5,400 3\.73 7,200", "Regular Cab Standard Box", "2WD")
    tg_rec(y, 8, "Vortec 5.3L V8", "3.42", None, 10000, r"Long Box 2WD 3\.73 5,200 3\.73 7,100 3\.42 10,000", "Regular Cab Long Box", "2WD")
    tg_rec(y, 8, "Vortec 6.0L V8 Hybrid", "3.08", None, 6100, r"Crew Cab 3\.23 4,700 3\.08 6,900\d? 3\.08 6,100", "Crew Cab Short Box", "2WD")
    tg_rec(y, 8, "Vortec 6.2L V8", "3.73", None, 10700, r"3\.73 10,700 Standard Box 2WD with MAX", "Extended Cab Standard Box", "2WD",
           "MAX Trailering Package")
tg_rec(2013, 9, "Vortec 4.3L V6", "3.73", 10000, 5400, r"3\.73 10,000 5,400 .{0,140}?4\.3L V6")
tg_rec(2013, 9, "Vortec 4.8L V8", "3.73", 12000, 7200, r"3\.73 12,000 7,200")
tg_rec(2013, 9, "Vortec 5.3L V8 with Heavy-Duty Cooling Package", "3.42", 15000, 10000, r"3\.42 15,000 - 10,000", pkg="Heavy-Duty Cooling Package")
tg_rec(2013, 9, "Vortec 5.3L V8", "3.08", 11500, 6600, r"Vortec 5\.3L V8 3\.08 11,500 6,600")
tg_rec(2013, 9, "Vortec 6.0L V8 Hybrid", "3.08", 12000, 6100, r"Vortec 6\.0L V8 Hybrid 3\.08 12,000 .{0,90}?6,100")
tg_rec(2013, 9, "Vortec 6.2L V8 with MAX Trailering Package", "3.73", 16000, 10700, r"Vortec 6\.2L V8 with MAX 3\.73 16,000 .{0,90}?10,700",
       pkg="MAX Trailering Package")
tg_rec(2013, 9, "Vortec 6.2L V8", "3.42", 15000, 9700, r"Vortec 6\.2L V8 3\.42 15,000 .{0,90}?9,700")
tg_rec(2014, 9, "EcoTec3 4.3L V6", "3.42", 12400, 7600, r"3\.42 12,400 - - 7,600")
tg_rec(2014, 9, "EcoTec3 5.3L V8", "3.42", 15000, 10200, r"3\.42 15,000 - 10,200")
tg_rec(2014, 9, "EcoTec3 5.3L V8 with Max Trailering Package", "3.73", 16700, 11500, r"EcoTec3 5\.3L V8 with Max 3\.73 16,700 - - - - 11,500", pkg="Max Trailering Package")
tg_rec(2014, 9, "EcoTec3 6.2L V8", "3.42", 15000, 9800, r"EcoTec3 6\.2L V8 3\.42 15,000 - - - - 9,800")
tg_rec(2014, 9, "EcoTec3 6.2L V8 with Max Trailering Package", "3.73", 17500, 12000, r"EcoTec3 6\.2L V8 with Max 3\.73 17,500 - - - - 12,000", pkg="Max Trailering Package")
for y, page in ((2019, 11), (2020, 15)):
    for r in tg_rows(DOCS[f"tg{y}"]["pdf"], page):
        if not r["vals"]:
            continue
        lab = r["label"]
        pkg = "Max Trailering Package" if re.search(r"Max Trailering", lab, re.I) else None
        mx = max(r["vals"])
        tg_rec(y, page, lab, r["axle"], r["gcwr"], mx,
               re.escape(r["line"].split("  ")[0].strip()) + r".{0,40}?" + re.escape(f"{r['gcwr']:,}") + r".{0,200}?" + re.escape(f"{mx:,}"),
               pkg=pkg, note="max across cab/box/drive configurations")

# two-line labels the row parser skips (label above the value line, "and Max Trailering Package" below)
tg_rec(2019, 11, "5.3L V8 (with 8-speed) and Max Trailering Package", "3.42", 16800, 11600,
       r"3\.42 16,800 — — 11,600", pkg="Max Trailering Package", note="max across cab/box/drive configurations")
tg_rec(2020, 15, "5.3L V8 (with 8-speed) and Max Trailering Package", "3.42", 16800, 11600,
       r"3\.42 16,800 — — 11,600", pkg="Max Trailering Package", note="max across cab/box/drive configurations")
tg_rec(2020, 15, "5.3L V8 (with 10-speed) and Max Trailering Package", "3.42", 16800, 11200,
       r"3\.42 16,800 — — — — — 11,200", pkg="Max Trailering Package", note="max across cab/box/drive configurations")
tg_rec(2020, 15, "6.2L V8 RST (20-inch wheels) and Max Trailering Package", "3.42", 19100, 13400,
       r"3\.42 19,100 — — — 13,400", pkg="Max Trailering Package")
tg_rec(2020, 15, "Duramax 3.0L Turbo-Diesel", "3.23", None, 9300,
       r"Duramax 3\.0L Turbo-Diesel 3\.23 — — 7,600 9,300",
       note="max across configurations; GCWR 13,000 lb (2WD) / 15,000 lb (4x4)")

# ------------------------------------------------------------------ wipers (Maintenance Replacement Parts)
WIP = {2005: 548, 2006: 553, 2007: 629, 2008: 558, 2009: 559, 2010: 587, 2012: 552, 2013: 491, 2014: 491, 2015: 502,
       2016: 476, 2017: 466, 2018: 455, 2019: 430, 2020: 452}
for y, pg in WIP.items():
    c = OM[y]
    for raw in (False, True):
        t = page_text(DOCS[c]["pdf"], pg, raw)
        m = re.search(r"Driver Side – (\d\d) cm \((\d\d\.\d) in\)", t)
        n = re.search(r"Passenger Side – (\d\d) cm \((\d\d\.\d) in\)", t)
        o = re.search(r"Wiper Blades.{0,20}?(\d\d(?:\.\d)?) in(?:ches|\.)? \((\d\d\.\d) cm\)|Wiper Blades – (\d\d\.\d) cm \((\d\d\.\d) in\)", t)
        if m and n:
            R.append({"field": "wipers", "years": [y, y], "driver_in": float(m.group(2)), "passenger_in": float(n.group(2)),
                      "src": [cite(c, pg, re.escape(m.group(0)), [m.group(2)]), cite(c, pg, re.escape(n.group(0)), [n.group(2)])]})
            break
        if o:
            inch = float(o.group(1) or o.group(4))
            R.append({"field": "wipers", "years": [y, y], "driver_in": inch, "passenger_in": inch,
                      "note": "one blade size listed for both sides",
                      "src": [cite(c, pg, re.escape(o.group(0)), [str(o.group(1) or o.group(4))])]})
            break
    else:
        raise SystemExit(f"no wipers {c} p.{pg}")

# ------------------------------------------------------------------ tires (1500-only manuals 2019-2020)
for y in (2019,):  # 2020 manual also covers 2500/3500 HD, so its tire sizes aren't 1500-specific
    c = OM[y]
    txt = open(D + c + ".txt", errors="replace").read().split("\f")
    found = {}
    for i, p in enumerate(txt, 1):
        flat = re.sub(r"\s+", " ", p)
        for m in re.finditer(r"\b(LT)?2\d\d/\s?\d\dR\d\d\b", flat):
            found.setdefault(m.group(0).replace(" ", ""), i)
    for size, pg in sorted(found.items()):
        R.append({"field": "tires", "years": [y, y], "size": size,
                  "note": "size named in the owner manual's tire sections",
                  "src": [cite(c, pg, re.escape(size).replace("/", r"/\s?"), [size[:3] if size[0] != 'L' else size[2:5]])]})

dump(str(ROOT / "data/manuals/chevrolet/silverado-1500.yaml"), "chevrolet/silverado-1500", R)
from collections import Counter
print(Counter((r["field"], r["years"][0]) for r in R if r["field"] in ("oil", "wipers", "tires")))
