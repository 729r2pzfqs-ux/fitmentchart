import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import DOCS, cite, dump
D = str(ROOT / "data/cache/manuals/honda-civic/") + "/"
for sec, title in (("00142", "Driving: Towing a Trailer"), ("00153", "Maintenance: Engine Oil"), ("00206", "Technical Information: Specifications")):
    DOCS[f"cv0505_{sec}"] = {"pdf": D + f"cv0505_{sec}.pdf",
                             "doc": f"2005 Honda Civic Owner's Manual (31S5A640), section {sec}: {title}",
                             "url": f"https://techinfo.honda.com/rjanisis/pubs/om/CV0505/CV0505O{sec}A.pdf",
                             "type": "oem_manual", "accessed": "2026-10-13"}
R = []
g = cite("cv0505_00153", 2, r"5W-20 oil is formulated for year.?round protection of your Honda", ["5W-20"])
R.append({"field": "oil", "years": [2005, 2005], "displacement_l": 1.7, "engine": "1.7 L SOHC (DX, LX, Canadian SE, LX-G)",
          "grade": "5W-20", "capacity_qt": 3.4, "capacity_l": 3.2,
          "src": [cite("cv0505_00206", 3, r"Including filter 3\.4 US qt \(3\.2", ["3.4"]),
                  cite("cv0505_00206", 3, r"＊3 : DX, LX, Canadian SE, LX-G"), g]})
R.append({"field": "oil", "years": [2005, 2005], "displacement_l": 1.7, "engine": "1.7 L SOHC VTEC (EX, Canadian Si)",
          "grade": "5W-20", "capacity_qt": 3.7, "capacity_l": 3.5,
          "src": [cite("cv0505_00206", 3, r"3\.7 US qt \(3\.5", ["3.7"]), cite("cv0505_00206", 3, r"＊4 : EX, Canadian Si"), g]})
for size, ls, trim, rx in (("P185/70R14", "87S", "DX, Canadian SE", r"P185/70R14 87S"),
                          ("P185/65R15", "86H", "Canadian LX-G", r"P185/65R15 86H"),
                          ("P195/60R15", "87H", "U.S. LX, EX; Canadian Si", r"P195/60R15 87H")):
    R.append({"field": "tires", "years": [2005, 2005], "trim": trim, "size": size, "load_speed": ls,
              "src": [cite("cv0505_00206", 4, rx, [size])]})
R.append({"field": "towing", "years": [2005, 2005], "max_lb": 0, "note": "not designed to tow a trailer",
          "src": [cite("cv0505_00142", 3, r"Your vehicle is not designed to tow a trailer")]})
dump(str(ROOT / "data/manuals/honda/civic.yaml"), "honda/civic", R)
