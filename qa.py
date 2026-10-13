"""Quality gates for data/models/*.json.

    python qa.py            check, print summary, exit 1 on any error
    python qa.py --json     also print the full report as JSON

Step 07 runs the same checks after merging and writes data/qa_report.{json,md};
build.py refuses to build while errors exist.

Severity
  error    a value is impossible or malformed; must be fixed before building
  warning  plausible but suspicious, or inferred from weak evidence; review
  gap      a field has no value for a model-year (coverage, not correctness)
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "data" / "models"

FIELDS = ["engines", "towing", "wheel", "tires", "battery", "wipers", "oil", "dims", "nhtsa"]
BOLT_RE = re.compile(r"^(\d{1,2})x(\d{2,3}(?:\.\d+)?)$")
VALID_CYL = {2, 3, 4, 5, 6, 8, 10, 12, 16}


def filled(field: str, v) -> bool:
    if field == "wheel":
        return bool(v and v.get("bolt_pattern"))
    if field == "dims":
        return bool(v and v.get("summary"))
    if field == "nhtsa":
        return bool(v and (v.get("recalls") is not None))
    return bool(v)


class Report:
    def __init__(self):
        self.issues: list[dict] = []

    def add(self, sev, slug, year, field, msg):
        self.issues.append({"severity": sev, "slug": slug, "year": year, "field": field, "msg": msg})

    def count(self, sev):
        return sum(i["severity"] == sev for i in self.issues)


def in_range(x, lo, hi):
    return x is not None and lo <= x <= hi


def check_wheel(r: Report, slug, y, w):
    if not w:
        return
    if w.get("basis") == "conflict":
        r.add("warning", slug, y, "wheel", f"sources disagree: {w.get('candidates')}")
        return
    bp = w.get("bolt_pattern", "")
    m = BOLT_RE.match(bp or "")
    if not m:
        r.add("error", slug, y, "wheel", f"malformed bolt pattern {bp!r}")
        return
    lugs, pcd = int(m.group(1)), float(m.group(2))
    if w.get("lug_count") != lugs:
        r.add("error", slug, y, "wheel", f"lug_count {w.get('lug_count')} != pattern {bp}")
    if not 3 <= lugs <= 10:
        r.add("error", slug, y, "wheel", f"lug count {lugs} out of range")
    if not 98 <= pcd <= 210:
        r.add("error", slug, y, "wheel", f"PCD {pcd} mm out of range")
    cb = w.get("center_bore_mm")
    if cb is None:
        r.add("warning", slug, y, "wheel", "centre bore missing")
    elif not (50 <= cb <= 130) or cb >= pcd:
        r.add("error", slug, y, "wheel", f"centre bore {cb} mm implausible for {bp}")
    if w.get("basis") == "generation" and w.get("trim_only_evidence"):
        r.add("warning", slug, y, "wheel",
              "inferred across the generation from special-trim rows only: "
              + ", ".join(f"{e['model']} {e['year']}" for e in w.get("evidence", [])))
    for o in w.get("oe_wheels", []):
        if not (13 <= o["diameter_in"] <= 26 and 4 <= o["width_in"] <= 13):
            r.add("error", slug, y, "wheel", f"OE wheel size implausible: {o}")
        if o.get("offset_mm") is not None and not -60 <= o["offset_mm"] <= 80:
            r.add("error", slug, y, "wheel", f"OE wheel offset implausible: {o}")


def check_engines(r: Report, slug, y, engines):
    labels = set()
    for e in engines:
        lab = e.get("label", "?")
        if lab in labels and lab != "Electric":
            r.add("warning", slug, y, "engines", f"duplicate engine label {lab}")
        labels.add(lab)
        if e.get("electrification") != "ev":
            if not in_range(e.get("displacement_l"), 0.6, 8.5):
                r.add("error", slug, y, "engines", f"{lab}: displacement {e.get('displacement_l')}")
            if e.get("cylinders") not in VALID_CYL:
                r.add("error", slug, y, "engines", f"{lab}: cylinders {e.get('cylinders')}")
        hp = e.get("hp") or []
        if e.get("hp_rejected"):
            r.add("warning", slug, y, "engines",
                  f"{lab}: EPA HP {e['hp_rejected']['values']} rejected, {e['hp_rejected']['reason']}")
        elif not hp:
            r.add("warning", slug, y, "engines", f"{lab}: no rated HP in EPA test-car data")
        for h in hp:
            if not 50 <= h <= 1000:
                r.add("error", slug, y, "engines", f"{lab}: hp {h} out of range")
        if len(hp) > 1 and max(hp) > 1.4 * min(hp):
            r.add("warning", slug, y, "engines", f"{lab}: wide HP spread {hp} (several trims share this engine)")
        if e.get("hp_match") == "name":
            r.add("warning", slug, y, "engines", f"{lab}: HP matched by model name only {hp}")
        mpg = e.get("mpg") or {}
        for k in ("city", "hwy", "combined"):
            v = mpg.get(k)
            if not v:
                r.add("error", slug, y, "engines", f"{lab}: missing {k} MPG")
                continue
            if v[0] > v[1] or not (5 <= v[0] and v[1] <= 160):
                r.add("error", slug, y, "engines", f"{lab}: {k} MPG {v} implausible")
        c, h, cb = mpg.get("city"), mpg.get("hwy"), mpg.get("combined")
        if c and h and cb:
            lo, hi = min(c[0], h[0]) - 1, max(c[1], h[1]) + 1
            if not (lo <= cb[0] and cb[1] <= hi):
                r.add("warning", slug, y, "engines", f"{lab}: combined MPG {cb} outside city {c}/hwy {h}")


def check_dims(r: Report, slug, y, d, body):
    s = (d or {}).get("summary") or {}
    if not s:
        return
    limits = {"length_mm": (3000, 7500), "width_mm": (1500, 2600), "height_mm": (1100, 2500),
              "wheelbase_mm": (2000, 4500), "curb_weight_kg": (900, 4000),
              "track_front_mm": (1200, 2000), "track_rear_mm": (1200, 2000)}
    for k, (lo, hi) in limits.items():
        v = s.get(k)
        if v and not (lo <= v[0] <= v[1] <= hi):
            r.add("error", slug, y, "dims", f"{k} {v} outside {lo}-{hi}")
    for v in d.get("variants", []):
        if v.get("wheelbase_mm") and v.get("length_mm") and v["wheelbase_mm"] >= v["length_mm"]:
            r.add("error", slug, y, "dims", f"{v['name']}: wheelbase >= length")


def check_nhtsa(r: Report, slug, y, n):
    if not n:
        return
    if not n.get("nhtsa_models"):
        r.add("warning", slug, y, "nhtsa", "no NHTSA model name matched; recalls/complaints not queried")
    rec = n.get("recalls") or {}
    if rec.get("count", 0) != len(rec.get("campaigns", [])):
        r.add("error", slug, y, "nhtsa", "recall count != campaign list length")
    # campaign types: V vehicle, E equipment, C child seat, T tire
    for c in rec.get("campaigns", []):
        if not re.fullmatch(r"\d{2}[VECT]\d{6}", c.get("campaign", "")):
            r.add("error", slug, y, "nhtsa", f"malformed campaign number {c.get('campaign')}")
    for v in (n.get("ncap") or {}).get("variants", []):
        for k in ("overall", "front", "side", "rollover"):
            if v.get(k) is not None and not 1 <= v[k] <= 5:
                r.add("error", slug, y, "nhtsa", f"NCAP {k} rating {v[k]} out of range")


def check_model(r: Report, m: dict) -> dict:
    slug = m["slug"]
    years = sorted(m["years"], key=int)
    ys = [int(y) for y in years]
    for a, b in zip(ys, ys[1:]):
        if b != a + 1:
            r.add("warning", slug, f"{a}-{b}", "years", f"gap in model years {a}..{b}")

    prev_bp, prev_gen = None, None
    prev_cw = None
    for y in years:
        blk = m["years"][y]
        missing_keys = [f for f in FIELDS if f not in blk]
        if missing_keys:
            r.add("error", slug, y, "schema", f"missing keys {missing_keys}")
        check_wheel(r, slug, y, blk.get("wheel"))
        check_engines(r, slug, y, blk.get("engines") or [])
        check_dims(r, slug, y, blk.get("dims"), m.get("body"))
        check_nhtsa(r, slug, y, blk.get("nhtsa"))

        # bolt pattern should only change at a generation boundary
        w = blk.get("wheel") or {}
        gens = tuple(blk.get("generation") or [])
        bp = (w.get("bolt_pattern"), w.get("center_bore_mm")) if w.get("bolt_pattern") else None
        if bp and prev_bp and bp != prev_bp and not (set(gens) - set(prev_gen or ())):
            r.add("warning", slug, y, "wheel", f"wheel spec changed {prev_bp} -> {bp} within {gens}")
        if bp:
            prev_bp, prev_gen = bp, gens

        cw = ((blk.get("dims") or {}).get("summary") or {}).get("curb_weight_kg")
        if cw and prev_cw and abs(cw[1] - prev_cw[1]) > 0.25 * prev_cw[1]:
            r.add("warning", slug, y, "dims", f"max curb weight jumped {prev_cw[1]} -> {cw[1]} kg")
        if cw:
            prev_cw = cw

    cov = {}
    for f in FIELDS:
        have = [y for y in years if filled(f, m["years"][y].get(f))]
        cov[f] = {"filled": len(have), "total": len(years),
                  "missing_years": [y for y in years if y not in have]}
        if not have:
            r.add("gap", slug, None, f, "no source provides this field yet")
        elif len(have) < len(years):
            r.add("gap", slug, None, f, f"missing for {cov[f]['missing_years']}")

    eng = [e for y in years for e in m["years"][y].get("engines") or []]
    wheel_basis = defaultdict(int)
    for y in years:
        wheel_basis[(m["years"][y].get("wheel") or {}).get("basis", "missing")] += 1
    cov["_detail"] = {
        "engines_total": len(eng),
        "engines_with_hp": sum(bool(e.get("hp")) for e in eng),
        "wheel_basis": dict(wheel_basis),
        "oe_wheel_years": sum(bool((m["years"][y].get("wheel") or {}).get("oe_wheels")) for y in years),
        # pre-2011 NCAP had no overall score, so count any star rating
        "ncap_rated_years": sum(any(v.get(k) for v in (((m["years"][y].get("nhtsa") or {}).get("ncap") or {})
                                                       .get("variants") or [])
                                    for k in ("overall", "front", "side", "rollover"))
                                for y in years),
        "recalls_total": sum(((m["years"][y].get("nhtsa") or {}).get("recalls") or {}).get("count", 0) for y in years),
        "complaints_total": sum((((m["years"][y].get("nhtsa") or {}).get("complaints")) or {}).get("count", 0)
                                for y in years),
    }
    return cov


def run(models_dir: Path = MODELS) -> dict:
    r = Report()
    coverage = {}
    files = sorted(models_dir.rglob("*.json"))
    if not files:
        r.add("error", None, None, "models", f"no model JSON files under {models_dir}")
    for p in files:
        m = json.loads(p.read_text())
        expected = p.relative_to(models_dir).with_suffix("").as_posix()
        if m.get("slug") != expected:
            r.add("error", m.get("slug"), None, "schema", f"slug {m.get('slug')!r} != path {expected!r}")
        coverage[m["slug"]] = check_model(r, m)
    return {
        "summary": {"models": len(files), "errors": r.count("error"),
                    "warnings": r.count("warning"), "gaps": r.count("gap")},
        "coverage": coverage,
        "issues": r.issues,
    }


def coverage_table(rep: dict) -> str:
    cols = FIELDS
    head = "| model | years | " + " | ".join(cols) + " |"
    sep = "|---|---:|" + "|".join("---:" for _ in cols) + "|"
    lines = [head, sep]
    tot = defaultdict(lambda: [0, 0])
    for slug, cov in rep["coverage"].items():
        n = cov[cols[0]]["total"]
        cells = []
        for c in cols:
            f = cov[c]["filled"]
            tot[c][0] += f
            tot[c][1] += n
            cells.append(f"{f}/{n}" if f else "-")
        lines.append(f"| {slug} | {n} | " + " | ".join(cells) + " |")
    lines.append("| **all** | | " + " | ".join(
        f"**{100 * tot[c][0] // max(tot[c][1], 1)}%**" for c in cols) + " |")
    return "\n".join(lines)


def main() -> int:
    rep = run()
    s = rep["summary"]
    print(coverage_table(rep))
    print()
    for sev in ("error", "warning"):
        for i in rep["issues"]:
            if i["severity"] == sev:
                print(f"{sev.upper():8s} {i['slug']} {i['year'] or ''} [{i['field']}] {i['msg']}")
    print(f"\n{s['models']} models: {s['errors']} errors, {s['warnings']} warnings, {s['gaps']} coverage gaps")
    if "--json" in sys.argv:
        print(json.dumps(rep, indent=2))
    return 1 if s["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
