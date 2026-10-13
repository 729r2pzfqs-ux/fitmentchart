"""Step 03: exterior dimensions + curb weight from NHTSA's Canadian Vehicle Specs.

vPIC endpoint: GetCanadianVehicleSpecifications?Year=&Make=&Model=&units=Metric
(Transport Canada CVS data hosted by NHTSA). The Model parameter is a substring
search. Each result is one body/drive variant ("F-150 P/U SUPERCREW 5.5-FT BOX
4X4"), and makes.yaml `cvs` rules filter out siblings such as F-250 SD.

CVS codes used (metric: cm / kg):
  OL overall length   OW overall width   OH overall height   WB wheelbase
  CW curb weight      TWF/TWR front/rear track width          WD weight distribution F/R %
  MYR  the model year the measurement was taken on (2-digit). The specs are reused
       across unchanged years, so MYR is often older than the query year.

Writes data/sources/cvs/<make>/<model>.json
"""
from __future__ import annotations

from common import (get_json, has_flag, iter_models, load_config, log, matches,
                    read_json, source_path, write_json)

URL = "https://vpic.nhtsa.dot.gov/api/vehicles/GetCanadianVehicleSpecifications/"
CM_FIELDS = {"OL": "length", "OW": "width", "OH": "height", "WB": "wheelbase",
             "TWF": "track_front", "TWR": "track_rear"}


def num(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def parse_variant(specs: list[dict]) -> dict:
    s = {d["Name"]: d["Value"] for d in specs}
    v = {"name": (s.get("Model") or "").strip()}
    for code, key in CM_FIELDS.items():
        cm = num(s.get(code))
        if cm and cm > 0:
            v[f"{key}_mm"] = int(round(cm * 10))
            v[f"{key}_in"] = round(cm / 2.54, 1)
    cw = num(s.get("CW"))
    if cw and cw > 0:
        v["curb_weight_kg"] = int(round(cw))
        v["curb_weight_lb"] = int(round(cw * 2.20462))
    wd = (s.get("WD") or "").strip()
    if wd and "/" in wd:
        f, r = (num(x) for x in wd.split("/", 1))
        if f is not None and r is not None:
            v["weight_dist_front_pct"], v["weight_dist_rear_pct"] = int(f), int(r)
    myr = (s.get("MYR") or "").strip()
    if myr.isdigit():
        yy = int(myr)
        v["measured_model_year"] = 2000 + yy if yy < 90 else 1900 + yy
    return v


def summarize(variants: list[dict]) -> dict:
    out = {}
    for key in ("length_mm", "width_mm", "height_mm", "wheelbase_mm", "track_front_mm",
                "track_rear_mm", "curb_weight_kg", "length_in", "width_in", "height_in",
                "wheelbase_in", "curb_weight_lb"):
        vals = [v[key] for v in variants if key in v]
        if vals:
            out[key] = [min(vals), max(vals)]
    return out


def main() -> None:
    refresh = has_flag("--refresh")
    cfg = load_config()
    for make, model, slug in iter_models(cfg):
        skel = read_json(source_path("vpic", slug))
        rule = model["cvs"]
        years_out = {}
        for y in sorted(skel["years"]):
            variants, seen = [], set()
            for q in rule["query"]:
                body = get_json(URL, {"Year": y, "Make": make["name"], "Model": q,
                                      "units": "Metric", "format": "json"}, refresh=refresh)
                for res in body.get("Results") or []:
                    v = parse_variant(res.get("Specs") or [])
                    if not matches(rule, v["name"]) or v["name"] in seen:
                        continue
                    seen.add(v["name"])
                    variants.append(v)
            if variants:
                variants.sort(key=lambda v: v["name"])
                years_out[y] = {"dims": {"summary": summarize(variants), "variants": variants}}
        write_json(source_path("cvs", slug), {
            "slug": slug,
            "source": {"name": "Transport Canada Canadian Vehicle Specifications via NHTSA vPIC",
                       "url": URL},
            "years": years_out,
        })
        nvar = sum(len(v["dims"]["variants"]) for v in years_out.values())
        missing = sorted(set(skel["years"]) - set(years_out))
        log(f"{slug:28s} years={len(years_out):2d}/{len(skel['years'])} variants={nvar}"
            + (f" missing={missing}" if missing else ""))


if __name__ == "__main__":
    main()
