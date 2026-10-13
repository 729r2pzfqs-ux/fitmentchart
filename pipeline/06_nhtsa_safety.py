"""Step 06: recalls, complaints and NCAP crash ratings from the NHTSA APIs.

Endpoints (api.nhtsa.gov):
  /products/vehicle/models?modelYear=&make=&issueType=r|c   model names NHTSA uses that year
  /recalls/recallsByVehicle?make=&model=&modelYear=
  /complaints/complaintsByVehicle?make=&model=&modelYear=
  /SafetyRatings/modelyear/{y}/make/{make}                  NCAP-rated models
  /SafetyRatings/modelyear/{y}/make/{make}/model/{model}    rated variants
  /SafetyRatings/VehicleId/{id}                             ratings for one variant

NHTSA's model naming drifts by year (2008 "SILVERADO", 2019 "SILVERADO 1500" +
"SILVERADO LD 1500"; "WRANGLER" + "WRANGLER UNLIMITED"), so the names are
discovered per year, filtered with the makes.yaml `nhtsa` rule, topped up with
the rule's `always` names (the discovery list is incomplete), queried one by
one, and the results de-duplicated by campaign number / ODI number. The same
complaint can be filed under two names; it's counted once.

Writes data/sources/nhtsa/<make>/<model>.json
"""
from __future__ import annotations

import sys
from collections import Counter
from datetime import date, datetime
from urllib.parse import quote

from common import (get_json, has_flag, iter_models, load_config, log, matches,
                    read_json, source_path, write_json)

API = "https://api.nhtsa.gov"


def iso_date(s: str | None) -> str | None:
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip()[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return None


def rating(v) -> int | None:
    try:
        n = int(str(v).strip())
    except (TypeError, ValueError):
        return None
    return n if 1 <= n <= 5 else None


def nhtsa_names(make: str, year: str, rule: dict, refresh: bool) -> list[str]:
    names = set()
    for issue in ("r", "c"):
        body = get_json(f"{API}/products/vehicle/models",
                        {"modelYear": year, "make": make, "issueType": issue}, refresh=refresh)
        for r in body.get("results") or []:
            if matches(rule, r.get("model", "")):
                names.add(r["model"].strip())
    names.update(rule.get("always", []))
    return sorted(names)


def recalls(make: str, year: str, names: list[str], refresh: bool) -> dict:
    camps = {}
    for n in names:
        body = get_json(f"{API}/recalls/recallsByVehicle",
                        {"make": make, "model": n, "modelYear": year}, refresh=refresh,
                        ok_status=(200, 400))
        for r in body.get("results") or []:
            cid = r.get("NHTSACampaignNumber")
            if not cid:
                continue
            c = camps.setdefault(cid, {
                "campaign": cid,
                "date": iso_date(r.get("ReportReceivedDate")),
                "component": r.get("Component"),
                "summary": (r.get("Summary") or "").strip(),
                "consequence": (r.get("Consequence") or "").strip(),
                "remedy": (r.get("Remedy") or "").strip(),
                "park_it": bool(r.get("parkIt")),
                "park_outside": bool(r.get("parkOutSide")),
                "nhtsa_models": [],
            })
            if n not in c["nhtsa_models"]:
                c["nhtsa_models"].append(n)
    out = sorted(camps.values(), key=lambda c: (c["date"] or "", c["campaign"]), reverse=True)
    return {"count": len(out), "campaigns": out}


def complaints(make: str, year: str, names: list[str], refresh: bool) -> dict:
    seen = {}
    for n in names:
        body = get_json(f"{API}/complaints/complaintsByVehicle",
                        {"make": make, "model": n, "modelYear": year}, refresh=refresh,
                        ok_status=(200, 400))
        for r in body.get("results") or []:
            odi = r.get("odiNumber")
            if odi is not None:
                seen[odi] = r
    comps = Counter()
    for r in seen.values():
        for c in (r.get("components") or "").split(","):
            c = c.strip()
            if c:
                comps[c] += 1
    rows = seen.values()
    return {
        "count": len(seen),
        "crashes": sum(bool(r.get("crash")) for r in rows),
        "fires": sum(bool(r.get("fire")) for r in rows),
        "injuries": sum(int(r.get("numberOfInjuries") or 0) for r in rows),
        "deaths": sum(int(r.get("numberOfDeaths") or 0) for r in rows),
        "top_components": [{"component": c, "count": n} for c, n in comps.most_common(8)],
    }


def ncap(make: str, year: str, rule: dict, refresh: bool) -> dict:
    body = get_json(f"{API}/SafetyRatings/modelyear/{year}/make/{quote(make)}", refresh=refresh,
                    accept_empty=True)
    models = sorted({r["Model"] for r in body.get("Results") or [] if matches(rule, r.get("Model", ""))})
    variants = []
    for m in models:
        vb = get_json(f"{API}/SafetyRatings/modelyear/{year}/make/{quote(make)}/model/{quote(m, safe='')}",
                      refresh=refresh, accept_empty=True)
        for v in vb.get("Results") or []:
            det = get_json(f"{API}/SafetyRatings/VehicleId/{v['VehicleId']}", refresh=refresh)
            d = (det.get("Results") or [{}])[0]
            rp = d.get("RolloverPossibility")
            variants.append({
                "vehicle_id": v["VehicleId"],
                "description": v.get("VehicleDescription"),
                "nhtsa_model": m,
                "overall": rating(d.get("OverallRating")),
                "front": rating(d.get("OverallFrontCrashRating")),
                "side": rating(d.get("OverallSideCrashRating")),
                "rollover": rating(d.get("RolloverRating")),
                "rollover_risk_pct": round(rp * 100, 1) if isinstance(rp, (int, float)) and rp > 0 else None,
                "esc": d.get("NHTSAElectronicStabilityControl"),
                "fcw": d.get("NHTSAForwardCollisionWarning"),
                "ldw": d.get("NHTSALaneDepartureWarning"),
            })
    rated = [v["overall"] for v in variants if v["overall"]]
    return {
        "variants": variants,
        "overall_best": max(rated) if rated else None,
        "overall_worst": min(rated) if rated else None,
    }


def main() -> None:
    refresh = has_flag("--refresh")
    cfg = load_config()
    # optional: `--only toyota/tacoma` to fetch one model (lets models run in parallel)
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    for make, model, slug in iter_models(cfg):
        if only and slug != only:
            continue
        skel = read_json(source_path("vpic", slug))
        rule = model["nhtsa"]
        years_out = {}
        for y in sorted(skel["years"]):
            names = nhtsa_names(make["name"], y, rule, refresh)
            rec = recalls(make["name"], y, names, refresh) if names else {"count": 0, "campaigns": []}
            com = complaints(make["name"], y, names, refresh) if names else None
            nc = ncap(make["name"], y, rule, refresh)
            years_out[y] = {"nhtsa": {
                "nhtsa_models": names,
                "recalls": rec,
                "complaints": com,
                "ncap": nc,
            }}
            log(f"  {slug} {y}: names={names} recalls={rec['count']} "
                f"complaints={com['count'] if com else '-'} ncap_variants={len(nc['variants'])} "
                f"best={nc['overall_best']}")
        write_json(source_path("nhtsa", slug), {
            "slug": slug,
            "source": {"name": "NHTSA", "url": API, "fetched": date.today().isoformat()},
            "years": years_out,
        })
        log(f"{slug:28s} years={len(years_out)}")


if __name__ == "__main__":
    main()
