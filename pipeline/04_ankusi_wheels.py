"""Step 04: bolt pattern, centre bore, lug count and OE wheel sizes (ANKUSI).

Dataset: ANKUSI Wheel Fitment Dataset, CC BY 4.0. Attribution required:
"ANKUSI Wheel Fitment Dataset" with a link (https://ankusiwheels.com/wheel-fitment-dataset/).

Download order (first that works wins, recorded in the output):
  1. GitHub david025445/ankusi-wheel-fitment-dataset (the URL in the project brief)
  2. GitHub david025445/ankusi-wheel-fitment-data
  3. figshare record 33921994 (DOI 10.6084/m9.figshare.33921994), latest version
  4. Hugging Face mirror hjhjhihg1/ankusi-wheel-fitment-data
On 2026-10-13 both GitHub repos returned 404, so figshare is the live source.

The dataset is a sparse sample of model-years and trims (e.g. Tacoma 2011, 2012,
2016, 2020, 2024 + TRD Pro years), not one row per year. Resolution per year:
  exact       rows covering that exact year decide it (OE wheel sizes too)
  generation  no exact row, so rows from the generation(s) covering the year
              decide it; overlap years need evidence from every generation
  conflict    rows disagree and nothing breaks the tie -> no value, QA flags it
  (missing)   no rows at all for the generation
"Decide": unanimous, else base-model rows, else the generation's base-model
rows, else a strict majority. Disagreeing trims are kept as `trim_exceptions`
(Civic Type R runs 5x120 while every other Civic is 5x114.3).
`trim_only_evidence` marks values backed only by special trims (e.g. the 8th-gen
Civic inferred from a Type R sedan row); QA warns on those.
Regional rows tagged [EU]/[UK]/etc. are excluded: this is a US site and those
variants can differ.

Writes data/sources/ankusi/<make>/<model>.json
"""
from __future__ import annotations

import csv
import io
import re

from common import (download, generation_for, has_flag, iter_models, load_config,
                    load_generations, log, matches, read_json, session, source_path,
                    write_json)

CANDIDATES = [
    ("github:david025445/ankusi-wheel-fitment-dataset",
     ["https://raw.githubusercontent.com/david025445/ankusi-wheel-fitment-dataset/main/data/ankusi-wheel-fitment.csv",
      "https://raw.githubusercontent.com/david025445/ankusi-wheel-fitment-dataset/main/ankusi-wheel-fitment.csv"]),
    ("github:david025445/ankusi-wheel-fitment-data",
     ["https://raw.githubusercontent.com/david025445/ankusi-wheel-fitment-data/main/data/ankusi-wheel-fitment.csv",
      "https://raw.githubusercontent.com/david025445/ankusi-wheel-fitment-data/main/ankusi-wheel-fitment.csv"]),
]
FIGSHARE_API = "https://api.figshare.com/v2/articles/33921994"
HF_URL = "https://huggingface.co/datasets/hjhjhihg1/ankusi-wheel-fitment-data/resolve/main/data/ankusi-wheel-fitment.csv"

ATTRIBUTION = {
    "name": "ANKUSI Wheel Fitment Dataset",
    "license": "CC BY 4.0",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "landing_page": "https://ankusiwheels.com/wheel-fitment-dataset/",
    "doi": "10.6084/m9.figshare.33921994",
}

EXPECTED_COLS = {"make", "model", "year", "bolt_pattern", "center_bore_mm", "lug_count", "oe_wheel"}
REGION_TAG = re.compile(r"\[(?!US\])[A-Z]{2,4}\]")
BOLT_RE = re.compile(r"^(\d{1,2})x(\d{2,3}(?:\.\d+)?)$")
WHEEL_RE = re.compile(r"(\d{2}(?:\.\d)?)\s*[x×]\s*(\d{1,2}(?:\.\d+)?)\s*J?(?:\s*(?:at\s*)?ET\s*(-?\d+))?", re.I)


def fetch(refresh: bool) -> tuple[str, dict]:
    """Return (csv_text, provenance)."""
    for label, urls in CANDIDATES:
        for url in urls:
            try:
                r = session().get(url, timeout=60)
            except Exception:
                continue
            if r.status_code == 200 and r.text.startswith("make,"):
                p = download(url, "ankusi/ankusi-github.csv", refresh=refresh)
                return p.read_text(encoding="utf-8"), {"via": label, "url": url}
    # figshare: resolve the current version's CSV through the API
    try:
        meta = session().get(FIGSHARE_API, timeout=60).json()
        f = next(f for f in meta["files"] if f["name"].endswith(".csv"))
        p = download(f["download_url"], f"ankusi/figshare-v{meta['version']}.csv", refresh=refresh)
        return p.read_text(encoding="utf-8"), {
            "via": "figshare", "url": f["download_url"], "version": meta["version"],
            "title": meta["title"], "md5": f.get("computed_md5"),
        }
    except Exception as e:  # noqa: BLE001 — fall through to the mirror
        log(f"  figshare failed: {e}")
    p = download(HF_URL, "ankusi/huggingface.csv", refresh=refresh)
    return p.read_text(encoding="utf-8"), {"via": "huggingface", "url": HF_URL}


def parse_years(s: str) -> list[int]:
    s = (s or "").strip().replace("–", "-").replace("—", "-")
    m = re.fullmatch(r"(\d{4})\s*-\s*(\d{4})", s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return list(range(a, b + 1)) if a <= b else []
    return [int(s)] if re.fullmatch(r"\d{4}", s) else []


def parse_oe(text: str) -> list[dict]:
    out = []
    for d, w, et in WHEEL_RE.findall(text or ""):
        dia, wid = float(d), float(w)
        if not (13 <= dia <= 26 and 4 <= wid <= 13):
            continue
        out.append({"diameter_in": dia if dia % 1 else int(dia), "width_in": wid,
                    "offset_mm": int(et) if et else None})
    return out


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def pcd_inches(pcd: float) -> float | None:
    """Imperial PCD only where it is a conventional imperial size (5.5", 4.5", 5")."""
    inch = pcd / 25.4
    q = round(inch * 4) / 4
    return q if abs(inch - q) < 0.005 else None


def main() -> None:
    refresh = has_flag("--refresh")
    cfg = load_config()
    gens = load_generations()
    text, prov = fetch(refresh)
    rows = list(csv.DictReader(io.StringIO(text)))
    missing_cols = EXPECTED_COLS - set(rows[0].keys())
    if missing_cols:
        raise SystemExit(f"ANKUSI schema changed, missing columns: {missing_cols}")
    log(f"ANKUSI: {len(rows)} rows via {prov['via']} {prov.get('version', '')}")

    for make, model, slug in iter_models(cfg):
        skel = read_json(source_path("vpic", slug))
        recs, skipped = [], []
        for r in rows:
            if r["make"].strip().lower() != make["name"].lower():
                continue
            name = r["model"].strip()
            short = re.sub(rf"^{re.escape(make['name'])}\s+", "", name, flags=re.I)
            if not matches(model["ankusi"], short):
                continue
            bp = r["bolt_pattern"].strip()
            reason = None
            if REGION_TAG.search(name):
                reason = "regional variant"
            elif not BOLT_RE.match(bp):
                reason = f"non-standard bolt pattern {bp!r}"
            elif not parse_years(r["year"]):
                reason = f"unparseable year {r['year']!r}"
            if reason:
                skipped.append({"model": name, "year": r["year"], "reason": reason})
                continue
            lugs, pcd = BOLT_RE.match(bp).groups()
            base_re = model["ankusi"].get("base") or rf"^{re.escape(model['name'])}$"
            trim = re.sub(r"\s+", " ", re.sub(model["ankusi"]["include"], " ", short, flags=re.I)).strip()
            recs.append({
                "model": name,
                "trim": trim or None,
                "is_base": bool(re.search(base_re, short, re.I)),
                "years": parse_years(r["year"]),
                "year_raw": r["year"],
                "bolt_pattern": f"{int(lugs)}x{pcd}",
                "lug_count": int(lugs),
                "pcd_mm": float(pcd),
                "center_bore_mm": num(r["center_bore_mm"]),
                "center_bore_rear_mm": num(r.get("center_bore_rear_mm")),
                "oe_wheels": parse_oe(r.get("oe_wheel", "")),
                "url": r.get("source_url", "").strip(),
            })

        def key(rec):
            return (rec["bolt_pattern"], rec["center_bore_mm"])

        def evidence(rs):
            return [{"model": x["model"], "year": x["year_raw"], "url": x["url"]} for x in rs]

        def spec_from(rs, basis, gen_names):
            r0 = rs[0]
            w = {
                "bolt_pattern": r0["bolt_pattern"],
                "lug_count": r0["lug_count"],
                "pcd_mm": r0["pcd_mm"],
                "pcd_in": pcd_inches(r0["pcd_mm"]),
                "center_bore_mm": r0["center_bore_mm"],
                "basis": basis,
                "generations": gen_names,
                "evidence": evidence(rs),
                "trim_only_evidence": not any(x["is_base"] for x in rs),
            }
            rear = {x["center_bore_rear_mm"] for x in rs if x["center_bore_rear_mm"]}
            if len(rear) == 1:
                w["center_bore_rear_mm"] = rear.pop()
            return w

        def in_gen(r, g):
            return any(g["start"] <= ry <= (g["end"] or 9999) for ry in r["years"])

        def resolve(rows, gen_rows):
            """Pick the primary (bolt pattern, bore) among `rows`.

            Unanimous -> that. Otherwise base-model rows for the year, then
            base-model rows across the generation, then a strict majority. Rows
            that disagree with the primary become trim exceptions (e.g. Civic
            Type R 5x120 vs Civic 5x114.3). Returns (primary_rows, exceptions)
            or (None, None) when nothing decides it.
            """
            keys = {key(r) for r in rows}
            primary_key = None
            if len(keys) == 1:
                primary_key = next(iter(keys))
            else:
                base = {key(r) for r in rows if r["is_base"]}
                gen_base = {key(r) for r in gen_rows if r["is_base"]}
                if len(base) == 1:
                    primary_key = next(iter(base))
                elif len(gen_base) == 1 and next(iter(gen_base)) in keys:
                    primary_key = next(iter(gen_base))
                else:
                    counts = sorted(((sum(key(r) == k for r in rows), k) for k in keys), reverse=True)
                    if counts[0][0] > counts[1][0]:
                        primary_key = counts[0][1]
            if primary_key is None:
                return None, None
            primary = [r for r in rows if key(r) == primary_key]
            exceptions = [{"trim": r["trim"] or r["model"], "bolt_pattern": r["bolt_pattern"],
                           "center_bore_mm": r["center_bore_mm"], "evidence": evidence([r])}
                          for r in rows if key(r) != primary_key]
            return primary, exceptions

        years_out, stats = {}, {"exact": 0, "generation": 0, "conflict": 0, "missing": 0}
        for y in sorted(skel["years"]):
            yi = int(y)
            gs = generation_for(slug, yi, gens)
            gen_names = [g["name"] for g in gs]
            gen_rows = [r for r in recs if any(in_gen(r, g) for g in gs)]
            exact = [r for r in recs if yi in r["years"]]
            wheel = None
            if exact:
                primary, exceptions = resolve(exact, gen_rows)
                if primary:
                    wheel = spec_from(primary, "exact", gen_names)
                    oe, seen = [], set()
                    for r in primary:
                        for o in r["oe_wheels"]:
                            k = (o["diameter_in"], o["width_in"], o["offset_mm"], r["trim"])
                            if k not in seen:
                                seen.add(k)
                                oe.append({**o, "trim": r["trim"] or "base"})
                    wheel["oe_wheels"] = oe
                    wheel["trim_exceptions"] = exceptions
                else:
                    wheel = {"basis": "conflict", "generations": gen_names,
                             "candidates": sorted({f"{a} / {b}" for a, b in {key(r) for r in exact}}),
                             "evidence": evidence(exact)}
            if wheel is None and gs:
                # Overlap years (two generations on sale) need evidence from each.
                pool = gen_rows if all(any(in_gen(r, g) for r in recs) for g in gs) else []
                if pool:
                    primary, exceptions = resolve(pool, pool)
                    if primary:
                        wheel = spec_from(primary, "generation", gen_names)
                        wheel["oe_wheels"] = []
                        wheel["trim_exceptions"] = exceptions
                    else:
                        wheel = {"basis": "conflict", "generations": gen_names,
                                 "candidates": sorted({f"{a} / {b}" for a, b in {key(r) for r in pool}}),
                                 "evidence": evidence(pool)}
            if wheel:
                stats[wheel["basis"]] += 1
                years_out[y] = {"wheel": wheel}
            else:
                stats["missing"] += 1

        write_json(source_path("ankusi", slug), {
            "slug": slug,
            "source": {**ATTRIBUTION, **prov},
            "matched_rows": len(recs),
            "skipped_rows": skipped,
            "years": years_out,
        })
        log(f"{slug:28s} rows={len(recs):3d} skipped={len(skipped)} " +
            " ".join(f"{k}={v}" for k, v in stats.items()))


if __name__ == "__main__":
    main()
