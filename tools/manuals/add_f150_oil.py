"""Append verified F-150 oil records to data/manuals/ford/f-150.yaml.

Run after build_f150.py. Sources:
- Ford's own technical-spec sheets (2020, 2021). These were fetched through WebFetch because Ford's CDN answers 403 to curl.
  Cached copies are in data/cache/manuals/ford-techspecs/.
- f150hub.com spec pages (third_party_reference), only for values the page states verbatim.
  Cached copies are in data/cache/web/.
Claims that couldn't be verified, or that the Ford sheets contradict, are not added (see git log).
"""
import html, re, sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import cite, DOCS

Y = ROOT / "data/manuals/ford/f-150.yaml"
data = yaml.safe_load(Y.read_text())
data["records"] = [r for r in data["records"] if r["field"] != "oil"]  # idempotent: this script owns F-150 oil
TS = ROOT / "data/cache/manuals/ford-techspecs"
for y in (2020, 2021):
    DOCS[f"ts{y}"] = {"pdf": str(TS / f"ts{y}.pdf"), "doc": f"{y} F-150 Technical Specs (Ford Motor Company)",
                      "url": (TS / f"ts{y}.url").read_text().strip(), "type": "oem_spec_sheet", "accessed": "2026-10-13"}
    data["sources"][f"ts{y}"] = {k: v for k, v in DOCS[f"ts{y}"].items() if k != "pdf"}

def web_quote(fname, pattern, must):
    t = (ROOT / "data/cache/web" / fname).read_text(errors="replace")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    x = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    m = re.search(pattern, x)
    if not m or must not in m.group(0):
        raise SystemExit(f"{fname}: pattern/value not found: {pattern}")
    return m.group(0)[:200]

WEB = {"f150hub_42": ("f150hub_specs_ford-4.2.html", "https://www.f150hub.com/specs/ford-4.2.html", "F150hub: Ford 4.2L V6 specs"),
       "f150hub_4654": ("f150hub_maintenance_4.6-5.4-f-150-maintenance.html",
                        "https://www.f150hub.com/maintenance/4.6-5.4-f-150-maintenance.html", "F150hub: 4.6L/5.4L F-150 maintenance"),
       "f150hub_62": ("f150hub_specs_ford-6.2.html", "https://www.f150hub.com/specs/ford-6.2.html", "F150hub: Ford 6.2L V8 specs"),
       "f150hub_37": ("f150hub_specs_ford-3.7.html", "https://www.f150hub.com/specs/ford-3.7.html", "F150hub: Ford 3.7L V6 specs"),
       "f150hub_50": ("f150hub_specs_ford-5.0.html", "https://www.f150hub.com/specs/ford-5.0.html", "F150hub: Ford 5.0L V8 specs"),
       "f150hub_35": ("f150hub_specs_ford-3.5.html", "https://www.f150hub.com/specs/ford-3.5.html", "F150hub: Ford 3.5L Ti-VCT V6 specs")}
for ref, (_, url, doc) in WEB.items():
    data["sources"][ref] = {"doc": doc, "url": url, "type": "third_party_reference", "accessed": "2026-10-13"}

R = []
def add(years, d, eng, qt, src, grade=None, cond=None):
    for y in years:
        r = {"field": "oil", "years": [y, y], "displacement_l": d, "engine": eng}
        if cond: r["condition"] = cond
        if grade: r["grade"] = grade
        r["capacity_qt"] = qt
        r["src"] = src
        R.append(r)

def w(ref, pattern, must):
    return {"ref": ref, "quote": web_quote(WEB[ref][0], pattern, must)}

# third-party reference values (only what each page states)
add(range(2005, 2009), 4.2, "4.2L V6", 6.0, [w("f150hub_42", r"Engine Oil Capacity: 6 qts w/ filter", "6 qts")])
q4654 = w("f150hub_4654", r"Engine oil \(4\.6L\) SAE 5W-20 full synthetic engine oil 6 U\.S\. quarts w/ filter change", "6 U.S. quarts")
add(range(2005, 2011), 4.6, "4.6L V8", 6.0, [q4654], grade="5W-20")
q54 = w("f150hub_4654", r"7 U\.S\. quarts w/ filter change \(2004\+ model years\)", "7 U.S. quarts")
q54g = w("f150hub_4654", r"Engine oil \(5\.4L\) SAE 5W-20", "5W-20")
add(range(2005, 2011), 5.4, "5.4L V8", 7.0, [q54, q54g], grade="5W-20")
add(range(2011, 2015), 3.7, "3.7L V6", 6.0, [w("f150hub_37", r"Engine Oil Capacity: 6 quarts w/ filter", "6 quarts")])
add(range(2011, 2015), 6.2, "6.2L V8", 7.0, [w("f150hub_62", r"Engine Oil Capacity: 7 qts w/ filter", "7 qts")])
add(range(2011, 2018), 5.0, "5.0L V8", 7.7, [w("f150hub_50", r"2011 - 2017 7\.7 qts w/ filter", "7.7")])
add(range(2015, 2018), 3.5, "3.5L Ti-VCT V6 (naturally aspirated)", 6.3,
    [w("f150hub_35", r"Engine Oil Capacity: 6\.3 qts w/ filter", "6.3")])

# Ford 2020 tech specs, PDF p.1: capacity only (the "Oil capacity/grade" row prints no grade)
row1 = cite("ts2020", 1, r"Oil capacity/grade 6 quarts 6 quarts 8\.85 quarts", ["8.85"])
row2 = cite("ts2020", 1, r"Oil capacity/grade 6 quarts 6\.5 quarts 6 quarts", ["6.5"])
add([2020], 3.3, "3.3L Ti-VCT V6 FFV", 6.0, [row1])
add([2020], 2.7, "2.7L EcoBoost V6", 6.0, [row1])
add([2020], 5.0, "5.0L V8", 8.85, [row1])
add([2020], 3.5, "3.5L EcoBoost V6 (incl. High Output)", 6.0, [row2])
add([2020], 3.0, "3.0L Power Stroke V6 diesel", 6.5, [row2])
# Ford 2021 tech specs: p.1 gasoline V6/V8, p.2 diesel / EcoBoost / PowerBoost
p1 = cite("ts2021", 1, r"6 quarts with Filter 6 quarts with Filter 7\.75 quarts", ["7.75"])
p1g = cite("ts2021", 1, r"\(5W-20 SAE GF6\) \(5W-30 SAE GF6\) \(5W-30 SAE GF6\)", ["5W-20"])
p2 = cite("ts2021", 2, r"6\.5 quarts \(5W-30 SAE FA4\) 6 quarts with Filter \(5W-30 SAE GF6\) 6 quarts with Filter \(5W-30 SAE GF6\)", ["6.5"])
add([2021], 3.3, "3.3-liter Ti-VCT V6 FFV", 6.0, [p1, p1g], grade="5W-20")
add([2021], 2.7, "2.7-liter EcoBoost V6", 6.0, [p1, p1g], grade="5W-30")
add([2021], 5.0, "5.0-liter Ti-VCT V8", 7.75, [p1, p1g], grade="5W-30")
add([2021], 3.0, "3.0-liter Power Stroke V6 diesel", 6.5, [p2], grade="5W-30")
add([2021], 3.5, "3.5-liter EcoBoost V6", 6.0, [p2], grade="5W-30")
add([2021], 3.5, "3.5-liter PowerBoost full hybrid V6", 6.0, [p2], grade="5W-30", cond="PowerBoost hybrid")

data["records"].extend(R)
with open(Y, "w") as fh:
    fh.write("# Generated from OEM documents (quotes verified against the cited PDF page), Ford tech-spec sheets,\n"
             "# f150hub.com reference pages and Rain-X wiper fitment pages.\n")
    yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, width=120)
print(f"added {len(R)} oil records")
