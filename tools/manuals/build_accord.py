"""Build data/manuals/honda/accord.yaml.

Sources, in priority order for each year:
- Honda owner's manuals (techinfo.honda.com), cached in data/cache/manuals/honda-accord/. Listed in MANUALS;
  a manual whose PDF is not cached is skipped, so its years stay gaps.
- Honda's 2017 Accord Facts Guide and Honda Info Center wheel/tire feature pages (2018-2026), cached as
  data/cache/web/hic_<year>_<body>_Exterior-Features_Wheels-and-Tires.html.
- tirepressure.com (third_party_reference), tires only, only for years with no OEM tire document.
"""
import html, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import DOCS, cite, dump
from tirepressure import rows as tp_rows

CACHE = ROOT / "data/cache/manuals/honda-accord"
WEB = ROOT / "data/cache/web"
ACCESSED = "2026-11-01"
R = []
OEM_TIRE_YEARS = set()

def tire(y, size, ls, trim, src, note=None):
    r = {"field": "tires", "years": [y, y], "trim": trim, "size": size}
    if ls: r["load_speed"] = ls
    if note: r["note"] = note
    r["src"] = src
    R.append(r)

# ---------------- tires: 2017 Facts Guide (table columns as printed)
FG = "fg2017"
DOCS[FG] = {"pdf": str(CACHE / "FG2017-Honda-Accord-Facts-Guide.pdf"), "doc": "2017 Honda Accord Facts Guide (Honda Info Center)",
            "url": (CACHE / "FG2017-Honda-Accord-Facts-Guide.url").read_text().strip(), "type": "oem_spec_sheet", "accessed": ACCESSED}
for pg, rx, cols in (
    (91, r"All.Season Tires\s+205/65 R16\s+235/40 R19\s+215/55 R17\s+215/55 R17\s+215/55 R17\s+235/40 R19",
     (("Sedan LX", "205/65R16", None), ("Sedan Sport", "235/40R19", None), ("Sedan EX", "215/55R17", None), ("Sedan EX-L", "215/55R17", None),
      ("Sedan EX-L V-6", "215/55R17", None), ("Sedan Touring", "235/40R19", None))),
    (105, r"All.Season Tires\s+225/50 R17 94V\s+225/50 R17 94V\s+225/50 R17 94V",
     (("Hybrid", "225/50R17", "94V"), ("Hybrid EX-L", "225/50R17", "94V"), ("Hybrid Touring", "225/50R17", "94V"))),
    (117, r"All.Season Tires\s+P215/55 R17\s+P235/45 R18\s+P235/45 R18\s+P235/45 R18\s+235/40 R19 96V",
     (("Coupe LX-S", "P215/55R17", None), ("Coupe EX", "P235/45R18", None), ("Coupe EX-L", "P235/45R18", None),
      ("Coupe EX-L V-6", "P235/45R18", None), ("Coupe Touring", "235/40R19", "96V")))):
    q = cite(FG, pg, rx)
    for trim, size, ls in cols:
        tire(2017, size, ls, trim, [q])
OEM_TIRE_YEARS.add(2017)

# ---------------- tires: Honda Info Center 2018-2026 (quote = the whole sentence as printed)
TRIM_RX = (r"^The (Accord .+?) (?:is|are) fitted", r"standard on (Accord .+?)(?: models)?; they", r"^(Accord .+?) trims show off",
           r"^The (Accord .+?) (?:shows? off|wears)", r"^The (.+?) trims? dazzles?", r"look on the (.+)$")
# Honda prints 225/50 R19 for these two pages; its 2020 page says 235/40 R19 for the same wheel. Resolved by HELD below.
HELD = {(2018, "225/50R19"), (2019, "225/50R19")}
def sentences(path):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", path.read_text(errors="replace"), flags=re.S)
    x = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    return [s.strip() for s in re.split(r"(?<=[a-z\d])\.\s+(?=[A-Z])", x)]

def trim_of(sent):
    for rx in TRIM_RX:
        m = re.search(rx, sent)
        if m:
            return m.group(1)
    raise SystemExit(f"no trim pattern for: {sent}")

for f in sorted(WEB.glob("hic_20*_Accord*_Exterior-Features_Wheels-and-Tires.html")):
    m = re.match(r"hic_(\d{4})_(Accord(?:-Hybrid)?)_", f.name)
    y, body = int(m.group(1)), m.group(2)
    ref = f"hic{y}{body.replace('-', '')}"
    DOCS[ref] = {"doc": f"Honda Info Center: {y} {body.replace('-', ' ')} Wheels and Tires",
                 "url": f"https://www.hondainfocenter.com/{y}/{body}/Feature-Guide/Exterior-Features/Wheels-and-Tires/",
                 "type": "oem_spec_sheet", "accessed": ACCESSED}
    for sent in sentences(f):
        for a, b, c in re.findall(r"(\d{3}/\d{2}) ?(Z?R) ?(\d{2})", sent):
            size = f"{a}{b}{c}"
            if (y, size) in HELD:
                continue
            tire(y, size, None, trim_of(sent), [{"ref": ref, "quote": (sent + ".")[:200]}])
    OEM_TIRE_YEARS.add(y)

# ---------------- tires: tirepressure.com, only for years with no OEM tire document
for y in range(2005, 2027):
    if y in OEM_TIRE_YEARS:
        continue
    ref = f"tp{y}"
    DOCS[ref] = {"doc": f"TirePressure.com: {y} Honda Accord Tire Pressure", "url": f"https://tirepressure.com/{y}-honda-accord-tire-pressure",
                 "type": "third_party_reference", "accessed": ACCESSED}
    for row in tp_rows(WEB / f"tp_accord_{y}.html"):
        tire(y, row["size"], None, row["trims"][:150], [{"ref": ref, "quote": row["text"][:200]}])

if "--write" in sys.argv:
    dump(str(ROOT / "data/manuals/honda/accord.yaml"), "honda/accord", R)
