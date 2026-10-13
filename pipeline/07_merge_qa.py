"""Step 07: merge every source extract into data/models/, then run QA.

Inputs (all keyed by model slug and model year):
  data/sources/vpic/        skeleton: which years exist, body style   (step 01)
  data/sources/fueleconomy/ engines                                    (step 02)
  data/sources/cvs/         dims                                       (step 03)
  data/sources/ankusi/      wheel                                      (step 04)
  data/sources/manuals/     towing/tires/battery/wipers/oil, once 05 exists
  data/sources/nhtsa/       nhtsa                                      (step 06)

Only years present in the vPIC skeleton are kept. Each source owns its fields.
A source that offers a field it doesn't own is an error, so two sources can
never silently overwrite each other.

Outputs:
  data/models/<make>/<model>.json
  data/qa_report.json, data/qa_report.md
Exit status 1 if QA finds errors.
"""
from __future__ import annotations

import sys
from datetime import date

from common import (DATA, ROOT, generation_for, iter_models, load_config, load_generations,
                    log, model_path, read_json, source_path, write_json)

sys.path.insert(0, str(ROOT))
import qa  # noqa: E402

# source -> fields it is allowed to set
OWNERSHIP = {
    "fueleconomy": {"engines"},
    "cvs": {"dims"},
    "ankusi": {"wheel"},
    "manuals": {"towing", "tires", "battery", "wipers", "oil"},
    "nhtsa": {"nhtsa"},
}


def main() -> int:
    cfg = load_config()
    gens = load_generations()
    today = date.today().isoformat()
    problems = []

    for make, model, slug in iter_models(cfg):
        skel = read_json(source_path("vpic", slug))
        out = {
            "make": skel["make"],
            "model": skel["model"],
            "slug": slug,
            "body": skel["body"],
            "updated": today,
            "generations": gens.get(slug, []),
            "sources": {},
            "years": {},
        }
        for y, blk in skel["years"].items():
            out["years"][y] = {"generation": [g["name"] for g in generation_for(slug, int(y), gens)],
                               **{k: (v.copy() if isinstance(v, (dict, list)) else v) for k, v in blk.items()}}

        for src, fields in OWNERSHIP.items():
            p = source_path(src, slug)
            if not p.exists():
                continue
            data = read_json(p)
            out["sources"][src] = data.get("source", {})
            stray = sorted(set(data["years"]) - set(out["years"]))
            if stray:
                log(f"  note: {slug} {src} has years outside the vPIC skeleton, ignored: {stray}")
            for y, blk in data["years"].items():
                if y not in out["years"]:
                    continue
                for field, value in blk.items():
                    if field not in fields:
                        problems.append(f"{slug} {y}: source {src!r} tried to set {field!r}")
                        continue
                    out["years"][y][field] = value

        write_json(model_path(slug), out)
        log(f"merged {slug:28s} years={len(out['years'])} sources={sorted(out['sources'])}")

    if problems:
        for p in problems:
            log(f"ERROR {p}")
        return 1

    rep = qa.run()
    write_json(DATA / "qa_report.json", rep)
    md = ["# QA report", "", f"Generated {today}.", "",
          f"**{rep['summary']['models']} models**: {rep['summary']['errors']} errors, "
          f"{rep['summary']['warnings']} warnings, {rep['summary']['gaps']} coverage gaps.", "",
          "## Coverage (model-years with a value)", "", qa.coverage_table(rep), "",
          "## Detail", "",
          "| model | engines w/ HP | wheel basis | OE wheel years | NCAP-rated years | recalls | complaints |",
          "|---|---:|---|---:|---:|---:|---:|"]
    for slug, cov in rep["coverage"].items():
        d = cov["_detail"]
        wb = ", ".join(f"{k} {v}" for k, v in sorted(d["wheel_basis"].items()))
        md.append(f"| {slug} | {d['engines_with_hp']}/{d['engines_total']} | {wb} | {d['oe_wheel_years']} | "
                  f"{d['ncap_rated_years']} | {d['recalls_total']} | {d['complaints_total']} |")
    for sev in ("error", "warning", "gap"):
        items = [i for i in rep["issues"] if i["severity"] == sev]
        md += ["", f"## {sev.capitalize()}s ({len(items)})", ""]
        md += [f"- `{i['slug']}` {i['year'] or ''} **{i['field']}**: {i['msg']}" for i in items] or ["None."]
    (DATA / "qa_report.md").write_text("\n".join(md) + "\n")

    print()
    print(qa.coverage_table(rep))
    s = rep["summary"]
    print(f"\nQA: {s['errors']} errors, {s['warnings']} warnings, {s['gaps']} coverage gaps "
          f"-> data/qa_report.md")
    return 1 if s["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
