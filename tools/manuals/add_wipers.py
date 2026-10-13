"""Append Rain-X wiper fitment records to each data/manuals YAML (years without OEM wiper data only)."""
import json, glob, yaml, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import dump, DOCS
C = str(ROOT / "data/cache/rainx/") + "/"
M = str(ROOT / "data/manuals/") + "/"
SLUG = {("Toyota", "Tacoma"): "toyota/tacoma", ("Ford", "F-150"): "ford/f-150", ("Honda", "Civic"): "honda/civic",
        ("Chevrolet", "Silverado 1500"): "chevrolet/silverado-1500", ("Jeep", "Wrangler"): "jeep/wrangler"}
by = {}
for f in glob.glob(C + "*.json"):
    r = json.load(open(f)); by.setdefault(SLUG[(r["make"], r["model"])], []).append(r)
for slug, rows in sorted(by.items()):
    path = M + slug + ".yaml"
    data = yaml.safe_load(open(path))
    data["records"] = [x for x in data["records"] if not (x["field"] == "wipers" and any(
        data["sources"][s["ref"]]["type"] == "aftermarket_fitment" for s in x["src"]))]
    oem_years = {y for x in data["records"] if x["field"] == "wipers" for y in range(x["years"][0], x["years"][1] + 1)}
    added = skipped = 0
    for r in sorted(rows, key=lambda r: r["year"]):
        pos = r["positions"]
        if r["year"] in oem_years or not pos.get("Driver") or not r["vehicle"] or str(r["year"]) not in r["vehicle"]:
            skipped += 1; continue
        if any(len(v) != 1 for v in pos.values()):
            skipped += 1; continue  # several lengths for one position (sub-models): ambiguous, leave empty
        ref = f"rainx{r['year']}"
        data["sources"][ref] = {"doc": f"Rain-X Blade Size Finder: {r['vehicle']}", "url": r["url"],
                                "type": "aftermarket_fitment", "accessed": "2026-10-13"}
        rec = {"field": "wipers", "years": [r["year"], r["year"]], "driver_in": pos["Driver"][0]}
        if pos.get("Passenger"): rec["passenger_in"] = pos["Passenger"][0]
        if pos.get("Rear"): rec["rear_in"] = pos["Rear"][0]
        rec["src"] = [{"ref": ref, "quote": q} for q in r["quotes"].values()]
        data["records"].append(rec); added += 1
    with open(path, "w") as fh:
        fh.write("# Generated from OEM documents (quotes verified against the cited PDF page) plus Rain-X wiper fitment pages.\n")
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, width=120)
    print(f"{slug:26s} wipers added={added} skipped={skipped} (OEM wiper years: {len(oem_years)})")
