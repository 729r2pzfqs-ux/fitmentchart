import sys, re, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import DOCS, cite, dump
from fordtow2 import parse

D = str(ROOT / "data/cache/manuals/ford-bot/") + "/"
ENG = {y: {e["displacement_l"] for e in v["engines"]} for y, v in
       json.load(open(str(ROOT / "data/models/ford/f-150.json")))["years"].items()}
URL = {y: f"https://blueovaltrucks.com/tech/pdf_documents/{y}_ford_towing_guide.pdf" for y in range(2005, 2022)}
URL.update({2022: "https://blueovaltrucks.com/tech/pdf_documents/2022_RV_Trailer_Towing_Guide.pdf",
            2023: "https://blueovaltrucks.com/tech/pdf_documents/2023-Ford-RV-and-Trailer-Towing-Guide.pdf",
            2024: "https://blueovaltrucks.com/tech/pdf_documents/2024-Ford-RV-and-Trailer-Towing-Guide.pdf",
            2025: "https://blueovaltrucks.com/tech/pdf_documents/2025-Ford-RV-and-Trailer-Towing-Guide_v1.pdf"})
for y, u in URL.items():
    DOCS[f"tg{y}"] = {"pdf": D + f"tg{y}.pdf", "doc": f"{y} Ford RV & Trailer Towing Guide", "url": u,
                      "type": "oem_towing_guide", "accessed": "2026-10-13",
                      "note": "Ford-published guide; copy hosted by blueovaltrucks.com"}
FORCE = {2012: [18]}

def disp(label):
    return float(re.match(r"(\d\.\d)L", label).group(1))

R = []
for y in range(2005, 2026):
    if y == 2009:
        continue
    for r in parse(DOCS[f"tg{y}"]["pdf"], FORCE.get(y, [])):
        d = disp(r["engine"])
        if d not in ENG[str(y)]:
            continue
        rec = {"field": "towing", "years": [y, y], "displacement_l": d, "engine": r["engine"]}
        if r["axle"]: rec["axle"] = r["axle"]
        rec.update({"max_lb": r["max"], "gcwr_lb": r["gcwr"],
                    "note": "max conventional-towing rating across cab/wheelbase/drive columns for this engine; "
                            "guide footnotes on that cell (equipment packages) apply"
                            + (f"; footnote marker {r['fn']}" if r["fn"] else ""),
                    "src": [cite(f"tg{y}", r["page"], re.escape(r["line"]), [f"{r['max']:,}"])]})
        R.append(rec)
# 2009: GCWR/Max. Trailer Summary table (two side-by-side halves, read by hand)
for eng, d, mx, gcwr, axle, rx in (
        ("4.6L 2V", 4.6, 6000, 11100, "3.73", r"– – – – 3\.73 11,100 6,000 6,000"),
        ("4.6L 3V", 4.6, 9500, 14900, "3.55", r"3\.55 14,900 9,500 9,500 \(3\)"),
        ("5.4L", 5.4, 11300, 16700, "3.73", r"145 8,200 5\.4L 6R80E 3\.73 16,700 11,300 11,300")):
    R.append({"field": "towing", "years": [2009, 2009], "displacement_l": d, "engine": eng, "axle": axle,
              "max_lb": mx, "gcwr_lb": gcwr,
              "note": "max conventional tow capacity in the 2009 F-150 GCWR/Max. Trailer Summary",
              "src": [cite("tg2009", 17, rx, [f"{mx:,}"])]})
dump(str(ROOT / "data/manuals/ford/f-150.yaml"), "ford/f-150", R)
from collections import Counter
print(sorted(Counter(r["years"][0] for r in R).items()))
