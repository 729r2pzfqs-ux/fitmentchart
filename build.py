"""Render the static site into docs/ (GitHub Pages).

    python build.py

Pages
  /                              make + model index
  /<make>/<model>/               model overview, one row per year
  /<make>/<model>/<year>/        full spec page for one model-year
Also writes sitemap.xml, search-index.json, robots.txt, CNAME and .nojekyll, and
copies static/ to docs/static/.

Refuses to build while qa.py reports errors. docs/ is wiped and fully
regenerated each run, so never hand-edit it.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

import qa

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
MODELS = ROOT / "data" / "models"
SITE_URL = "https://fitmentchart.com"
DOMAIN = "fitmentchart.com"


def env() -> Environment:
    return Environment(loader=FileSystemLoader(ROOT / "templates"), extensions=["jinja2.ext.do"],
                       autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def year_summary(y: str, blk: dict) -> dict:
    n = blk.get("nhtsa") or {}
    return {
        "year": y,
        "generation": blk.get("generation") or [],
        "wheel": blk.get("wheel") or {},
        "engines": blk.get("engines") or [],
        "ncap_best": (n.get("ncap") or {}).get("overall_best"),
        "recalls": (n.get("recalls") or {}).get("count"),
    }


def main() -> int:
    rep = qa.run()
    if rep["summary"]["errors"]:
        print(f"QA has {rep['summary']['errors']} errors; run `python qa.py` and fix them first.")
        return 1

    models = [json.loads(p.read_text()) for p in sorted(MODELS.rglob("*.json"))]
    if not models:
        print("no models in data/models; run the pipeline first")
        return 1

    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    shutil.copytree(ROOT / "static", DOCS / "static")
    j = env()
    urls: list[str] = []
    search: list[dict] = []

    def render(tpl: str, path: str, **ctx) -> None:
        ctx.setdefault("crumbs", [])
        html = j.get_template(tpl).render(site_url=SITE_URL, path=path, **ctx)
        write(DOCS / path.lstrip("/") / "index.html", html)
        urls.append(path)

    makes: dict[str, dict] = {}
    for m in models:
        ys = sorted(m["years"], key=int)
        mk = makes.setdefault(m["make"], {"name": m["make"], "models": []})
        mk["models"].append({"slug": m["slug"], "model": m["model"],
                             "first_year": ys[0], "last_year": ys[-1]})

        years = [year_summary(y, m["years"][y]) for y in ys]
        render("model.html", f"/{m['slug']}/", m=m, years=years,
               title=f"{m['make']} {m['model']} specs by year: bolt pattern, engines, MPG | FitmentChart",
               description=f"{m['make']} {m['model']} {ys[0]}–{ys[-1]}: bolt pattern, center bore, "
                           f"engines, horsepower, fuel economy, dimensions and safety ratings by year.",
               crumbs=[("/", "Home"), (f"/{m['slug']}/", f"{m['make']} {m['model']}")])
        search.append({"t": f"{m['make']} {m['model']}", "u": f"/{m['slug']}/"})

        for i, y in enumerate(ys):
            blk = m["years"][y]
            w = blk.get("wheel") or {}
            bits = []
            if w.get("bolt_pattern"):
                bits.append(f"bolt pattern {w['bolt_pattern']}")
            if blk.get("engines"):
                bits.append(f"{len(blk['engines'])} engine option{'s' if len(blk['engines']) != 1 else ''}")
            desc = (f"{y} {m['make']} {m['model']} specs: " + ", ".join(bits) +
                    ", fuel economy, dimensions, recalls and crash ratings.") if bits else \
                   f"{y} {m['make']} {m['model']} specs, fuel economy, dimensions, recalls and crash ratings."
            render("year.html", f"/{m['slug']}/{y}/", m=m, year=y, y=blk,
                   prev_year=ys[i - 1] if i > 0 else None,
                   next_year=ys[i + 1] if i + 1 < len(ys) else None,
                   title=f"{y} {m['make']} {m['model']} bolt pattern, specs & fitment | FitmentChart",
                   description=desc,
                   crumbs=[("/", "Home"), (f"/{m['slug']}/", f"{m['make']} {m['model']}"),
                           (f"/{m['slug']}/{y}/", y)])
            search.append({"t": f"{y} {m['make']} {m['model']}", "u": f"/{m['slug']}/{y}/",
                           "bp": w.get("bolt_pattern")})

    render("index.html", "/", makes=sorted(makes.values(), key=lambda x: x["name"]),
           title="FitmentChart: bolt patterns, wheel fitment & vehicle specs by year",
           description="Bolt patterns, center bore, engines, fuel economy, dimensions and safety data "
                       "by year, make and model.")

    today = date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{SITE_URL}{u}</loc><lastmod>{today}</lastmod></url>" for u in sorted(urls)]
    sm.append("</urlset>")
    write(DOCS / "sitemap.xml", "\n".join(sm) + "\n")
    write(DOCS / "search-index.json", json.dumps(search, separators=(",", ":")))
    write(DOCS / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    write(DOCS / "CNAME", DOMAIN + "\n")
    write(DOCS / ".nojekyll", "")
    print(f"built {len(urls)} pages into docs/ ({len(models)} models)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
