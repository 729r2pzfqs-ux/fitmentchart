"""Step 01: build the make/model/year skeleton from the NHTSA vPIC API.

For each configured model and each model year, ask vPIC which models the make
sold that year (GetModelsForMakeYear) and keep the years where our model shows
up. Body style comes from the same endpoint filtered by vPIC vehicle type
(truck / passenger car / MPV).

Writes:
  data/sources/vpic/<make>/<model>.json   canonical skeleton (input to step 07)
  data/models/<make>/<model>.json         initial model JSON with empty spec blocks
"""
from __future__ import annotations

from collections import Counter

from common import (get_json, has_flag, iter_models, load_config, log, matches,
                    model_path, source_path, write_json, year_range)

VPIC = "https://vpic.nhtsa.dot.gov/api/vehicles"

# vPIC vehicle type -> site body category
VEHICLE_TYPES = {
    "truck": "pickup",
    "passenger car": "car",
    "multipurpose passenger vehicle (mpv)": "suv",
}

EMPTY_YEAR = {
    "engines": [], "towing": [], "wheel": {}, "tires": [], "battery": {},
    "wipers": {}, "oil": {}, "dims": {}, "nhtsa": {},
}


def models_for(make: str, year: int, vtype: str | None, refresh: bool) -> list[dict]:
    url = f"{VPIC}/GetModelsForMakeYear/make/{make}/modelyear/{year}"
    if vtype:
        url += f"/vehicletype/{vtype}"
    return get_json(url, {"format": "json"}, refresh=refresh).get("Results") or []


def main() -> None:
    refresh = has_flag("--refresh")
    cfg = load_config()
    years = year_range(cfg)

    for make, model, slug in iter_models(cfg):
        rule = model["vpic"]
        found: dict[str, dict] = {}
        bodies: Counter = Counter()
        body_by_year: dict[str, list[str]] = {}

        for y in years:
            hits = [r for r in models_for(make["vpic_make"], y, None, refresh)
                    if matches(rule, r["Model_Name"])]
            if not hits:
                continue
            found[str(y)] = {
                "vpic_models": sorted({(r["Model_Name"], r["Model_ID"]) for r in hits}),
                "make_id": hits[0]["Make_ID"],
            }
            ids = {r["Model_ID"] for r in hits}
            yb = []
            for vtype, body in VEHICLE_TYPES.items():
                if any(r["Model_ID"] in ids for r in models_for(make["vpic_make"], y, vtype, refresh)):
                    yb.append(body)
                    bodies[body] += 1
            body_by_year[str(y)] = yb

        if not found:
            raise SystemExit(f"{slug}: vPIC returned no matching models for {years[0]}-{years[-1]}")
        if not bodies:
            raise SystemExit(f"{slug}: vPIC returned no vehicle type for any year")
        body = bodies.most_common(1)[0][0]

        skeleton = {
            "make": make["name"],
            "model": model["name"],
            "slug": slug,
            "body": body,
            "vpic": {
                "make_id": next(iter(found.values()))["make_id"],
                "model_names": sorted({n for v in found.values() for n, _ in v["vpic_models"]}),
                "model_ids": sorted({i for v in found.values() for _, i in v["vpic_models"]}),
                "by_year": {y: {"models": [{"name": n, "id": i} for n, i in v["vpic_models"]],
                                "body": body_by_year.get(y, [])} for y, v in found.items()},
            },
            "years": {y: {k: (v.copy() if isinstance(v, (dict, list)) else v) for k, v in EMPTY_YEAR.items()}
                      for y in found},
        }
        write_json(source_path("vpic", slug), skeleton)

        # data/models gets a fresh skeleton only when no merged file exists yet:
        # step 07 owns that file afterwards.
        mp = model_path(slug)
        if not mp.exists() or has_flag("--reset-models"):
            out = {k: skeleton[k] for k in ("make", "model", "slug", "body")}
            out["years"] = skeleton["years"]
            write_json(mp, out)

        missing = [y for y in years if str(y) not in found]
        log(f"{slug:28s} body={body:6s} years={len(found):2d} "
            f"({min(found)}-{max(found)}) vpic={skeleton['vpic']['model_names']}"
            + (f" missing={missing}" if missing else ""))


if __name__ == "__main__":
    main()
