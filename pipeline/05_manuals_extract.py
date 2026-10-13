"""Step 05: owner's-manual specs (towing, tires, oil, battery, wipers).

Input: data/manuals/<make>/<model>.yaml. These are hand-curated extracts from
OEM owner's manuals, OEM towing guides and spec sheets, and (for battery /
wipers, which manuals rarely print) battery and wiper makers' fitment
catalogues. Every record cites a document, a page and a verbatim quote. The
file format is defined in data/manuals/README.md.

This step does no fetching. Values are curated by hand because each OEM lays
out its manuals differently. What it does is enforce the rules: every record
needs a resolvable source with a quote, values must pass sanity limits, and
two records may not give different single-valued specs (wipers) for the
same year. It then expands each record to the model years it covers.

Writes data/sources/manuals/<make>/<model>.json, which step 07 merges.
Exits 1 on any validation error. Nothing is written for a model that
fails validation.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict

import yaml

from common import DATA, iter_models, load_config, log, read_json, source_path, write_json

MANUALS = DATA / "manuals"
SOURCE_TYPES = {"oem_manual", "oem_towing_guide", "oem_spec_sheet", "oem_parts_catalog",
                "aftermarket_fitment"}
FIELDS = {"towing", "tires", "oil", "battery", "wipers"}

TIRE_RE = re.compile(r"^(P|LT)?\d{3}/\d{2}Z?R\d{2}(\.\d)?$|^\d{2}x\d{1,2}\.\d{2}R\d{2}(LT)?$", re.I)
OIL_RE = re.compile(r"^\d{1,2}W-\d{2}$")
BATTERY_RE = re.compile(r"^[A-Z]{0,2}\d{1,3}[A-Z]{0,2}(-\d)?$|^H\d$|^T\d$", re.I)

COMMON_KEYS = {"field", "years", "src", "note"}
KEYS = {
    "towing": {"displacement_l", "engine", "drive", "cab", "bed", "trim", "axle", "wheelbase",
               "max_lb", "tongue_lb", "gcwr_lb", "package"},
    "tires": {"trim", "size", "load_speed", "position", "displacement_l"},
    "oil": {"displacement_l", "engine", "condition", "grade", "alt_grades", "spec", "capacity_qt", "capacity_l"},
    "battery": {"displacement_l", "engine", "trim", "group", "cca", "ah"},
    "wipers": {"driver_in", "passenger_in", "rear_in", "trim", "body"},
}


class Invalid(Exception):
    pass


def num(v, lo, hi, what):
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        raise Invalid(f"{what} must be a number, got {v!r}")
    if not lo <= v <= hi:
        raise Invalid(f"{what} {v} outside {lo}-{hi}")
    return v


def check_record(rec: dict, sources: dict) -> list[dict]:
    """Validate one record; return its resolved source list."""
    f = rec.get("field")
    if f not in FIELDS:
        raise Invalid(f"unknown field {f!r}")
    extra = set(rec) - COMMON_KEYS - KEYS[f]
    if extra:
        raise Invalid(f"{f}: unexpected keys {sorted(extra)}")
    ys = rec.get("years")
    if not (isinstance(ys, list) and len(ys) == 2 and all(isinstance(y, int) for y in ys) and ys[0] <= ys[1]):
        raise Invalid(f"years must be [start, end], got {ys!r}")

    srcs = rec.get("src")
    if not srcs:
        raise Invalid("record has no src")
    resolved = []
    for s in srcs:
        ref = s.get("ref")
        if ref not in sources:
            raise Invalid(f"src ref {ref!r} not in sources")
        doc = sources[ref]
        quote = (s.get("quote") or "").strip()
        if not quote:
            raise Invalid(f"src {ref}: missing verbatim quote")
        if len(quote) > 300:
            raise Invalid(f"src {ref}: quote longer than 300 chars")
        if str(doc.get("url", "")).lower().split("?")[0].endswith(".pdf") and s.get("page") is None:
            raise Invalid(f"src {ref}: PDF source needs a page number")
        resolved.append({"doc": doc["doc"], "url": doc.get("url"), "type": doc["type"],
                         "page": s.get("page"), "quote": quote, "accessed": str(doc.get("accessed", ""))})

    if f == "towing":
        num(rec.get("max_lb"), 0, 20000, "max_lb")
        if rec.get("tongue_lb") is not None:
            num(rec["tongue_lb"], 0, 3000, "tongue_lb")
            if rec["max_lb"] and rec["tongue_lb"] > 0.25 * rec["max_lb"]:
                raise Invalid(f"tongue_lb {rec['tongue_lb']} > 25% of max_lb {rec['max_lb']}")
        if rec.get("gcwr_lb") is not None:
            num(rec["gcwr_lb"], 3000, 25000, "gcwr_lb")
            if rec["gcwr_lb"] <= rec["max_lb"]:
                raise Invalid(f"gcwr_lb {rec['gcwr_lb']} <= max_lb {rec['max_lb']}")
    elif f == "tires":
        if not TIRE_RE.match(str(rec.get("size", "")).replace(" ", "")):
            raise Invalid(f"tire size {rec.get('size')!r} not a recognised format")
    elif f == "oil":
        if rec.get("grade") is None and rec.get("capacity_qt") is None:
            raise Invalid("oil record needs grade and/or capacity_qt")
        if rec.get("grade") is not None and not OIL_RE.match(str(rec["grade"])):
            raise Invalid(f"oil grade {rec['grade']!r} not like 0W-20")
        for g in rec.get("alt_grades") or []:
            if not OIL_RE.match(str(g)):
                raise Invalid(f"alt oil grade {g!r} not like 0W-20")
        if rec.get("capacity_qt") is not None:
            num(rec["capacity_qt"], 2.5, 14, "capacity_qt")
        if rec.get("capacity_l") is not None:
            num(rec["capacity_l"], 2.5, 14, "capacity_l")
    elif f == "battery":
        if not BATTERY_RE.match(str(rec.get("group", ""))):
            raise Invalid(f"battery group {rec.get('group')!r} not a BCI group")
        if rec.get("cca") is not None:
            num(rec["cca"], 250, 1300, "cca")
    elif f == "wipers":
        if rec.get("driver_in") is None and rec.get("passenger_in") is None and rec.get("rear_in") is None:
            raise Invalid("wipers record has no lengths")
        for k in ("driver_in", "passenger_in", "rear_in"):
            if rec.get(k) is not None:
                num(rec[k], 8, 32, k)
    if rec.get("displacement_l") is not None:
        num(rec["displacement_l"], 0.6, 8.5, "displacement_l")
    return resolved


def payload(rec: dict) -> dict:
    return {k: v for k, v in rec.items() if k not in ("field", "years", "src")}


def build_model(slug: str, data: dict, years: set[str]) -> tuple[dict, list[str]]:
    errors: list[str] = []
    sources = data.get("sources") or {}
    for ref, doc in sources.items():
        if doc.get("type") not in SOURCE_TYPES:
            errors.append(f"source {ref}: type {doc.get('type')!r} not one of {sorted(SOURCE_TYPES)}")
        if not doc.get("doc"):
            errors.append(f"source {ref}: missing doc name")
        if not doc.get("url"):
            errors.append(f"source {ref}: missing url")

    out: dict[str, dict] = defaultdict(lambda: {"towing": [], "tires": [], "oil": {"engines": []},
                                                "battery": {"options": []}, "wipers": {}})
    outside = set()
    for i, rec in enumerate(data.get("records") or []):
        try:
            src = check_record(rec, sources)
        except Invalid as e:
            errors.append(f"record #{i} ({rec.get('field')} {rec.get('years')}): {e}")
            continue
        f = rec["field"]
        body = payload(rec)
        for y in range(rec["years"][0], rec["years"][1] + 1):
            ys = str(y)
            if ys not in years:
                outside.add(y)
                continue
            blk = out[ys]
            if f == "wipers":
                w = blk["wipers"]
                for k in ("driver_in", "passenger_in", "rear_in", "body", "trim"):
                    if body.get(k) is None:
                        continue
                    if k in w and w[k] != body[k] and k.endswith("_in"):
                        errors.append(f"{ys} wipers {k}: {w[k]} vs {body[k]} from different records")
                    w[k] = body[k]
                w.setdefault("src", []).extend(s for s in src if s not in w.get("src", []))
                continue
            target = {"towing": blk["towing"], "tires": blk["tires"],
                      "oil": blk["oil"]["engines"], "battery": blk["battery"]["options"]}[f]
            same = next((t for t in target if {k: v for k, v in t.items() if k != "src"} == body), None)
            if same:  # an identical value from a second source: corroboration, keep both
                same["src"].extend(s for s in src if s not in same["src"])
            else:
                target.append({**body, "src": list(src)})

    # drop empty containers so QA sees an honest gap
    final = {}
    for y, blk in out.items():
        clean = {}
        if blk["towing"]:
            clean["towing"] = blk["towing"]
        if blk["tires"]:
            clean["tires"] = blk["tires"]
        if blk["oil"]["engines"]:
            clean["oil"] = blk["oil"]
        if blk["battery"]["options"]:
            clean["battery"] = blk["battery"]
        if blk["wipers"]:
            clean["wipers"] = blk["wipers"]
        if clean:
            final[y] = clean
    notes = [f"records cover years outside the vPIC skeleton, ignored: {sorted(outside)}"] if outside else []
    return {"years": dict(sorted(final.items())), "notes": notes}, errors


def main() -> int:
    cfg = load_config()
    failed = False
    for make, model, slug in iter_models(cfg):
        src_file = MANUALS / f"{slug}.yaml"
        out_path = source_path("manuals", slug)
        if not src_file.exists():
            if out_path.exists():
                out_path.unlink()
            log(f"{slug:28s} no data/manuals file yet (fields stay empty)")
            continue
        data = yaml.safe_load(src_file.read_text())
        if data.get("slug") != slug:
            log(f"ERROR {slug}: file slug {data.get('slug')!r} != {slug!r}")
            failed = True
            continue
        skel = read_json(source_path("vpic", slug))
        built, errors = build_model(slug, data, set(skel["years"]))
        if errors:
            failed = True
            for e in errors:
                log(f"ERROR {slug}: {e}")
            continue
        types = sorted({d["type"] for d in (data.get("sources") or {}).values()})
        write_json(out_path, {
            "slug": slug,
            "source": {"name": "Owner's manuals, OEM towing guides/spec sheets and fitment catalogues",
                       "file": f"data/manuals/{slug}.yaml", "documents": len(data.get("sources") or {}),
                       "document_types": types},
            "notes": built["notes"],
            "years": built["years"],
        })
        per_field = {f: sum(f in b for b in built["years"].values()) for f in sorted(FIELDS)}
        log(f"{slug:28s} records={len(data.get('records') or [])} years_with_data={len(built['years'])} "
            + " ".join(f"{k}={v}" for k, v in per_field.items()))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
