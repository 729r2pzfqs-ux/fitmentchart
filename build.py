"""Render the static site into docs/ (GitHub Pages).

    python build.py

Pages
  /                                   home: search, models, spec shortcuts, guides
  /<make>/                            make index
  /<make>/<model>/                    model overview, one row per year (sortable)
  /<make>/<model>/<year>/             full spec page for one model-year
  /<make>/<model>/<spec>/             one spec across all years (towing-capacity, bolt-pattern, oil-capacity,
                                      tire-size, battery-size, wiper-size); only built when the spec has data
  /guides/, /guides/<slug>/           explainers, linked from the spec pages
  /about/ /privacy/ /terms/ /sources/ and 404.html
Also writes sitemap.xml, robots.txt, ads.txt, search-index.json, CNAME, .nojekyll and copies favicon/ to the root.

All templates are inline strings below (rendered through a DictLoader). Refuses to build while qa.py reports
errors. docs/ is wiped and regenerated each run, so never hand-edit it.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

from jinja2 import DictLoader, Environment, select_autoescape
from markupsafe import Markup

import qa

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
MODELS = ROOT / "data" / "models"
SITE_URL = "https://fitmentchart.com"
DOMAIN = "fitmentchart.com"
SITE_NAME = "FitmentChart"
CONTACT_EMAIL = "info@fitmentchart.com"
ADSENSE_PUB = "ca-pub-5861928596436289"
GA_ID = "G-9V072G350X"
AD_SLOTS: dict[str, str] = {}   # TODO: AdSense slot ids, e.g. {"top": "1234567890", "bottom": "..."}; empty = auto ads only
TODAY = date.today()

SPECS = {  # slug -> (label, short noun, guide slug)
    "towing-capacity": ("Towing capacity", "towing capacity", "towing-capacity-explained"),
    "bolt-pattern": ("Bolt pattern & wheel specs", "bolt pattern", "bolt-pattern-explained"),
    "oil-capacity": ("Oil type & capacity", "oil type and capacity", "engine-oil-viscosity-explained"),
    "tire-size": ("Tire sizes", "tire size", "how-to-read-a-tire-size"),
    "battery-size": ("Battery group size", "battery size", "battery-group-sizes-explained"),
    "wiper-size": ("Wiper blade sizes", "wiper blade size", "wiper-blade-sizes-explained"),
}


# ------------------------------------------------------------------ helpers
def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def commas(v) -> str:
    return f"{v:,}" if isinstance(v, (int, float)) else str(v)


def rng(vals, unit="") -> str:
    vals = sorted({v for v in vals or [] if v is not None})
    if not vals:
        return ""
    s = commas(vals[0]) if len(vals) == 1 else f"{commas(vals[0])}–{commas(vals[-1])}"
    return s + (f" {unit}" if unit else "")


def make_slug(m: dict) -> str:
    return m["slug"].split("/")[0]


def towing_max(blk: dict):
    vals = [t["max_lb"] for t in blk.get("towing") or [] if t.get("max_lb")]
    return max(vals) if vals else None


def oil_summary(blk: dict) -> list[dict]:
    return (blk.get("oil") or {}).get("engines") or []


def tire_sizes(blk: dict) -> list[str]:
    out = []
    for t in blk.get("tires") or []:
        if t["size"] not in out:
            out.append(t["size"])
    return out


def battery_groups(blk: dict) -> list[dict]:
    return (blk.get("battery") or {}).get("options") or []


def has_spec(spec: str, blk: dict) -> bool:
    return bool({
        "towing-capacity": blk.get("towing"),
        "bolt-pattern": (blk.get("wheel") or {}).get("bolt_pattern"),
        "oil-capacity": oil_summary(blk),
        "tire-size": blk.get("tires"),
        "battery-size": battery_groups(blk),
        "wiper-size": blk.get("wipers"),
    }[spec])


def tow_config(t: dict) -> str:
    bits = [t.get("engine") or (f"{t['displacement_l']}L" if t.get("displacement_l") else ""),
            t.get("drive"), t.get("cab"), t.get("bed"), t.get("trim"), f"{t['axle']} axle" if t.get("axle") else ""]
    return ", ".join(b for b in bits if b) or "All"


def fit_title(t: str) -> str:
    suffix = f" | {SITE_NAME}"
    return t + suffix if len(t + suffix) <= 65 and SITE_NAME not in t else t


def fit_desc(d: str, n: int = 160) -> str:
    if len(d) <= n:
        return d
    cut = d[:n]
    dot = cut.rfind(". ")
    if dot >= 100:
        return cut[:dot + 1]
    return cut[:n - 1].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def plain(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


# ------------------------------------------------------------------ templates
CSS_VERSION = "1"
T: dict[str, str] = {}

T["base.html"] = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }}</title>
<meta name="description" content="{{ description }}">
<link rel="canonical" href="{{ site_url }}{{ path }}">
<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ description }}">
<meta property="og:url" content="{{ site_url }}{{ path }}">
<meta property="og:type" content="{{ og_type or 'website' }}">
<meta property="og:site_name" content="{{ site_name }}">
<meta property="og:image" content="{{ site_url }}/favicon-512.png">
<meta name="twitter:card" content="summary">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#14213d">
<link rel="stylesheet" href="/static/style.css?v={{ css_version }}">
<link rel="preconnect" href="https://pagead2.googlesyndication.com" crossorigin>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('consent', 'default', {
  'analytics_storage': 'denied', 'ad_storage': 'denied', 'ad_user_data': 'denied', 'ad_personalization': 'denied',
  'wait_for_update': 500,
  'region': ['AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','GR','HU','IS','IE','IT','LV','LI','LT','LU','MT','NL','NO','PL','PT','RO','SK','SI','ES','SE','CH','GB']
});
gtag('consent', 'default', {
  'analytics_storage': 'granted', 'ad_storage': 'granted', 'ad_user_data': 'granted', 'ad_personalization': 'granted'
});
</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={{ adsense_pub }}" crossorigin="anonymous"></script>
{% if ga_id %}<script async src="https://www.googletagmanager.com/gtag/js?id={{ ga_id }}"></script>
<script>gtag('js', new Date()); gtag('config', '{{ ga_id }}');</script>
{% endif %}
{% for ld in jsonld %}<script type="application/ld+json">{{ ld|tojson }}</script>
{% endfor %}
</head>
<body>
<header class="site-header">
<div class="container header-inner">
<a href="/" class="logo">Fitment<span>Chart</span></a>
<nav class="site-nav" aria-label="Main">
{% for mk in nav_makes %}<a href="/{{ mk.slug }}/">{{ mk.name }}</a>
{% endfor %}<a href="/guides/">Guides</a>
</nav>
<form class="header-search" action="/" role="search" onsubmit="return false">
<input type="search" class="search-input" placeholder="Search year, make, model…" aria-label="Search vehicles" autocomplete="off">
<div class="search-results" hidden></div>
</form>
</div>
</header>
<main id="main" class="container">
{% if crumbs %}<nav class="crumbs" aria-label="Breadcrumb">{% for href, label in crumbs %}{% if not loop.last %}<a href="{{ href }}">{{ label }}</a><span aria-hidden="true"> › </span>{% else %}<span aria-current="page">{{ label }}</span>{% endif %}{% endfor %}</nav>{% endif %}
{{ ad("top") }}
{% block body %}{% endblock %}
{{ ad("bottom") }}
</main>
<footer class="site-footer">
<div class="container">
<div class="footer-grid">
<div class="footer-col"><h4>Vehicles</h4>
{% for m in all_models %}<a href="/{{ m.slug }}/">{{ m.make }} {{ m.model }}</a>
{% endfor %}</div>
<div class="footer-col"><h4>Specs</h4>
{% for s, v in specs.items() %}<a href="/guides/{{ v[2] }}/">{{ v[0] }}</a>
{% endfor %}</div>
<div class="footer-col"><h4>Site</h4>
<a href="/about/">About</a><a href="/sources/">Data sources</a><a href="/guides/">Guides</a><a href="/privacy/">Privacy policy</a><a href="/terms/">Terms of use</a>
</div>
</div>
<p class="footer-note">Specs are compiled from NHTSA, EPA, Transport Canada, OEM owner's manuals and spec sheets, the
<a href="https://ankusiwheels.com/wheel-fitment-dataset/">ANKUSI Wheel Fitment Dataset</a>
(<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>) and other cited sources. Always confirm fitment against
your vehicle's door placard, owner's manual or the part maker before buying. Not affiliated with any vehicle manufacturer.</p>
<p class="footer-note">&copy; {{ year_now }} {{ site_name }} · <a href="mailto:{{ email }}">{{ email }}</a></p>
</div>
</footer>
<script src="/static/site.js?v={{ css_version }}" defer></script>
</body>
</html>"""

# citation list: link per (doc, page); research notes have no url
T["macros.html"] = r"""{% macro cite(src) %}<span class="cite">{% set seen = [] %}{% for c in src %}{% set k = c.doc ~ "|" ~ c.page %}{% if k not in seen %}{% if seen %}; {% endif %}{% do seen.append(k) %}{% if c.url %}<a href="{{ c.url }}" title="{{ c.quote }}" rel="nofollow noopener" target="_blank">{{ c.doc }}{% if c.page %}, p. {{ c.page }}{% endif %}</a>{% else %}<span title="{{ c.quote }}">{{ c.doc }}</span>{% endif %}{% endif %}{% endfor %}</span>{% endmacro %}
{% macro badge(src, confidence=None) %}{% if confidence == "low" %}<span class="badge badge-low" title="Third-party data, not confirmed against an OEM document">low confidence</span>{% elif src and src|selectattr("type", "in", ["third_party_reference", "aftermarket_fitment"])|list|length == src|length %}<span class="badge badge-3p" title="From a third-party or aftermarket fitment source">third-party</span>{% endif %}{% endmacro %}
{% macro battery_disclaimer() %}<p class="disclaimer">Verify group size on your battery label or owner's manual before purchasing.</p>{% endmacro %}
{% macro spec_links(m, available, current=None) %}<nav class="spec-links" aria-label="{{ m.make }} {{ m.model }} specs">{% for s in available %}{% if s != current %}<a href="/{{ m.slug }}/{{ s }}/">{{ m.model }} {{ specs[s][0]|lower }}</a>{% endif %}{% endfor %}</nav>{% endmacro %}
"""

T["home.html"] = r"""{% extends "base.html" %}
{% block body %}
<section class="hero">
<h1>Vehicle fitment &amp; specs by year</h1>
<p class="lede">Bolt patterns, towing capacity, oil type and capacity, tire sizes, battery group and wiper sizes, with a cited source for every value.</p>
<form class="hero-search" role="search" onsubmit="return false">
<input type="search" class="search-input" placeholder="e.g. 2019 Tacoma, F-150 towing, 6x139.7" aria-label="Search vehicles" autocomplete="off">
<div class="search-results" hidden></div>
</form>
</section>

<h2>Vehicles</h2>
<div class="cards">
{% for c in model_cards %}
<a class="card" href="/{{ c.slug }}/">
<span class="card-title">{{ c.make }} {{ c.model }}</span>
<span class="card-meta">{{ c.first }}–{{ c.last }} · {{ c.n }} model years</span>
<span class="card-facts">{% if c.bolt %}Bolt pattern {{ c.bolt }}{% endif %}{% if c.tow %} · tows up to {{ c.tow|commas }} lb{% endif %}</span>
</a>
{% endfor %}
</div>

<h2>Jump to a spec</h2>
<div class="table-wrap">
<table class="matrix">
<thead><tr><th>Vehicle</th>{% for s, v in specs.items() %}<th>{{ v[0] }}</th>{% endfor %}</tr></thead>
<tbody>{% for c in model_cards %}
<tr><td><a href="/{{ c.slug }}/">{{ c.make }} {{ c.model }}</a></td>{% for s in specs %}<td>{% if s in c.available %}<a href="/{{ c.slug }}/{{ s }}/">{{ specs[s][1]|capitalize }}</a>{% else %}<span class="muted">—</span>{% endif %}</td>{% endfor %}</tr>
{% endfor %}</tbody>
</table>
</div>

<h2>Guides</h2>
<ul class="guide-list">{% for g in guides %}<li><a href="/guides/{{ g.slug }}/">{{ g.title }}</a> <span class="muted">{{ g.summary }}</span></li>{% endfor %}</ul>

<section class="about-box">
<h2>How the data is built</h2>
<p>Every towing, oil, tire, battery and wiper value links to the document it came from: an owner's manual page, an OEM towing guide or spec sheet, or (flagged as such) a third-party reference. Engines and fuel economy come from the EPA, dimensions from Transport Canada, and recalls and crash ratings from NHTSA. Where no source gives a value, we leave it blank instead of guessing. <a href="/sources/">More about the sources</a>.</p>
</section>
{% endblock %}"""

T["make.html"] = r"""{% extends "base.html" %}
{% block body %}
<h1>{{ make.name }} fitment &amp; specs</h1>
<p class="lede">{{ make.models|length }} {{ make.name }} model{{ "s" if make.models|length != 1 }} covered, with bolt patterns, towing, oil, tires, battery and wiper sizes by model year.</p>
<div class="cards">
{% for c in make.models %}
<a class="card" href="/{{ c.slug }}/">
<span class="card-title">{{ c.make }} {{ c.model }}</span>
<span class="card-meta">{{ c.first }}–{{ c.last }} · {{ c.n }} model years</span>
<span class="card-facts">{% if c.bolt %}Bolt pattern {{ c.bolt }}{% endif %}{% if c.tow %} · tows up to {{ c.tow|commas }} lb{% endif %}</span>
</a>
{% endfor %}
</div>
{% for c in make.models %}
<h2>{{ c.make }} {{ c.model }} specs</h2>
<ul class="link-list">{% for s in c.available %}<li><a href="/{{ c.slug }}/{{ s }}/">{{ c.model }} {{ specs[s][0]|lower }} by year</a></li>{% endfor %}</ul>
{% endfor %}
{% endblock %}"""

T["model.html"] = r"""{% extends "base.html" %}
{% from "macros.html" import spec_links with context %}
{% block body %}
<h1>{{ m.make }} {{ m.model }} specs by year</h1>
<p class="lede">{{ rows|length }} model years, {{ rows[0].year }}–{{ rows[-1].year }}. {{ intro }}</p>
{{ spec_links(m, available) }}
<div class="table-wrap">
<table class="sortable">
<thead><tr><th data-sort="num">Year</th><th>Generation</th><th>Bolt pattern</th><th data-sort="num">Max towing</th><th>Engines</th><th>Oil</th><th>Tires</th><th>Battery</th><th data-sort="num">Recalls</th></tr></thead>
<tbody>
{% for r in rows %}
<tr>
<td><a href="/{{ m.slug }}/{{ r.year }}/">{{ r.year }}</a></td>
<td>{{ r.generation or "—" }}</td>
<td>{{ r.bolt or "—" }}</td>
<td data-v="{{ r.tow or 0 }}">{% if r.tow %}{{ r.tow|commas }} lb{% else %}—{% endif %}</td>
<td>{{ r.engines or "—" }}</td>
<td>{{ r.oil or "—" }}</td>
<td>{{ r.tires or "—" }}</td>
<td>{{ r.battery or "—" }}</td>
<td data-v="{{ r.recalls if r.recalls is not none else -1 }}">{{ r.recalls if r.recalls is not none else "—" }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
<p class="muted small">Click a column header to sort. Max towing is the highest rating any configuration gets that year; see the year page for the configuration it requires.</p>

{% if gens %}
<h2>Generations</h2>
<ul class="link-list">{% for g in gens %}<li><strong>{{ g.name }}</strong>{% if g.code %} ({{ g.code }}){% endif %}: {{ g.start }}–{{ g.end or "present" }}{% if g.first_year %} · <a href="/{{ m.slug }}/{{ g.first_year }}/">{{ g.first_year }} specs</a>{% endif %}</li>{% endfor %}</ul>
{% endif %}

{% if siblings %}
<h2>Other vehicles</h2>
<ul class="link-list">{% for s in siblings %}<li><a href="/{{ s.slug }}/">{{ s.make }} {{ s.model }}</a></li>{% endfor %}</ul>
{% endif %}
{% endblock %}"""

T["year.html"] = r"""{% extends "base.html" %}
{% from "macros.html" import cite, badge, battery_disclaimer, spec_links with context %}
{% block body %}
<h1>{{ year }} {{ m.make }} {{ m.model }} specs &amp; fitment</h1>
<p class="lede">{% if y.generation %}{{ y.generation|join(" / ") }}. {% endif %}{{ summary }}</p>

<nav class="toc" aria-label="On this page">
{% if y.wheel.bolt_pattern %}<a href="#wheels">Wheels</a>{% endif %}{% if y.engines %}<a href="#engines">Engines</a>{% endif %}{% if y.towing %}<a href="#towing">Towing</a>{% endif %}{% if y.tires %}<a href="#tires">Tires</a>{% endif %}{% if y.oil and y.oil.engines %}<a href="#oil">Oil</a>{% endif %}{% if (y.battery and y.battery.options) or y.wipers %}<a href="#battery">Battery &amp; wipers</a>{% endif %}{% if y.dims.summary %}<a href="#dimensions">Dimensions</a>{% endif %}{% if y.nhtsa %}<a href="#safety">Safety</a>{% endif %}
</nav>

{% if y.wheel.bolt_pattern %}
<section id="wheels">
<h2>Wheels &amp; bolt pattern</h2>
<dl class="specs">
<dt>Bolt pattern</dt><dd><strong>{{ y.wheel.bolt_pattern }}</strong>{% if y.wheel.pcd_in %} ({{ y.wheel.lug_count }}x{{ y.wheel.pcd_in }}"){% endif %}</dd>
<dt>Lug count</dt><dd>{{ y.wheel.lug_count }}</dd>
<dt>Center bore</dt><dd>{% if y.wheel.center_bore_mm %}{{ y.wheel.center_bore_mm }} mm{% else %}—{% endif %}</dd>
</dl>
{% if y.wheel.oe_wheels %}
<h3>Factory wheel sizes</h3>
<ul>{% for o in y.wheel.oe_wheels %}<li>{{ o.diameter_in }}x{{ o.width_in }}{% if o.offset_mm is not none %} ET{{ o.offset_mm }}{% endif %} <span class="muted">({{ o.trim }})</span></li>{% endfor %}</ul>
{% endif %}
{% for e in y.wheel.trim_exceptions or [] %}<p class="note">Exception: the {{ e.trim }} uses {{ e.bolt_pattern }}{% if e.center_bore_mm %} / {{ e.center_bore_mm }} mm bore{% endif %}.</p>{% endfor %}
{% if y.wheel.basis == "generation" %}<p class="note">Applies across the {{ y.wheel.generations|join(" / ") }}; based on {{ y.wheel.evidence|length }} source record{{ "s" if y.wheel.evidence|length != 1 }} from other years of this generation.</p>{% endif %}
<p class="small">Source: <a href="https://ankusiwheels.com/wheel-fitment-dataset/">ANKUSI Wheel Fitment Dataset</a> (CC BY 4.0). <a href="/guides/bolt-pattern-explained/">How to read a bolt pattern</a>.</p>
</section>
{% endif %}

{% if y.engines %}
<section id="engines">
<h2>Engines &amp; fuel economy</h2>
<div class="table-wrap"><table class="sortable">
<thead><tr><th>Engine</th><th data-sort="num">Horsepower</th><th>Fuel</th><th data-sort="num">MPG city</th><th data-sort="num">MPG hwy</th><th data-sort="num">MPG combined</th><th>Drive</th></tr></thead>
<tbody>{% for e in y.engines %}
<tr><td>{{ e.label }}</td><td>{{ e.hp|join(" / ") or "—" }}</td><td>{{ e.fuel|join(", ") }}{% if e.flex_fuel %} (E85 capable){% endif %}</td>
<td>{{ e.mpg.city|unique|join("–") }}</td><td>{{ e.mpg.hwy|unique|join("–") }}</td><td>{{ e.mpg.combined|unique|join("–") }}</td><td>{{ e.drives|join(", ") }}</td></tr>
{% endfor %}</tbody></table></div>
<p class="small">Source: EPA fueleconomy.gov; horsepower from EPA fuel-economy test-car data.</p>
</section>
{% endif %}

{% if y.towing %}
<section id="towing">
<h2>Towing capacity</h2>
<p>Maximum trailer weight ranges up to <strong>{{ tow_max|commas }} lb</strong>, depending on configuration. <a href="/{{ m.slug }}/towing-capacity/">{{ m.model }} towing capacity by year</a> · <a href="/guides/towing-capacity-explained/">what GCWR and tongue weight mean</a></p>
<div class="table-wrap"><table class="sortable">
<thead><tr><th>Configuration</th><th data-sort="num">Max trailer</th><th data-sort="num">Tongue</th><th data-sort="num">GCWR</th><th>Required</th><th>Source</th></tr></thead>
<tbody>{% for t in y.towing %}
<tr><td>{{ t|towcfg }}{% if t.note %} <span class="muted">({{ t.note }})</span>{% endif %}</td>
<td data-v="{{ t.max_lb or 0 }}">{% if t.max_lb %}{{ t.max_lb|commas }} lb{% else %}Not rated{% endif %}</td>
<td data-v="{{ t.tongue_lb or 0 }}">{% if t.tongue_lb %}{{ t.tongue_lb|commas }} lb{% else %}—{% endif %}</td>
<td data-v="{{ t.gcwr_lb or 0 }}">{% if t.gcwr_lb %}{{ t.gcwr_lb|commas }} lb{% else %}—{% endif %}</td>
<td>{{ t.package or "—" }}</td><td>{{ cite(t.src) }} {{ badge(t.src) }}</td></tr>
{% endfor %}</tbody></table></div>
</section>
{% endif %}

{% if y.tires %}
<section id="tires">
<h2>Tire sizes</h2>
<div class="table-wrap"><table>
<thead><tr><th>Size</th><th>Trim</th><th>Source</th></tr></thead>
<tbody>{% for t in y.tires %}
<tr><td><strong>{{ t.size }}</strong>{% if t.load_speed %} {{ t.load_speed }}{% endif %}{% if t.position %} <span class="muted">({{ t.position }})</span>{% endif %}</td><td>{{ t.trim or "—" }}</td><td>{{ cite(t.src) }} {{ badge(t.src) }}</td></tr>
{% endfor %}</tbody></table></div>
<p class="small"><a href="/guides/how-to-read-a-tire-size/">How to read a tire size</a> · <a href="/{{ m.slug }}/tire-size/">{{ m.model }} tire sizes by year</a></p>
</section>
{% endif %}

{% if y.oil and y.oil.engines %}
<section id="oil">
<h2>Engine oil type &amp; capacity</h2>
<div class="table-wrap"><table>
<thead><tr><th>Engine</th><th>Oil grade</th><th>Capacity with filter</th><th>Source</th></tr></thead>
<tbody>{% for o in y.oil.engines %}
<tr><td>{{ o.engine or (o.displacement_l ~ "L" if o.displacement_l else "All") }}{% if o.condition %} <span class="muted">({{ o.condition }})</span>{% endif %}</td>
<td>{{ o.grade or "—" }}{% if o.alt_grades %} <span class="muted">(alt. {{ o.alt_grades|join(", ") }})</span>{% endif %}</td>
<td>{% if o.capacity_qt %}{{ o.capacity_qt }} qt{% if o.capacity_l %} ({{ o.capacity_l }} L){% endif %}{% else %}—{% endif %}</td>
<td>{{ cite(o.src) }} {{ badge(o.src) }}</td></tr>
{% endfor %}</tbody></table></div>
<p class="small"><a href="/guides/engine-oil-viscosity-explained/">What 0W-20 and 5W-30 mean</a> · <a href="/{{ m.slug }}/oil-capacity/">{{ m.model }} oil capacity by year</a></p>
</section>
{% endif %}

{% if (y.battery and y.battery.options) or y.wipers %}
<section id="battery">
<h2>Battery &amp; wiper blades</h2>
<dl class="specs">
{% for b in (y.battery.options if y.battery else []) %}
<dt>Battery{% if b.engine or b.displacement_l %} ({{ b.engine or b.displacement_l ~ "L" }}){% endif %}</dt>
<dd>Group <strong>{{ b.group }}</strong>{% if b.din %} ({{ b.din }}){% endif %}{% if b.condition %}, {{ b.condition }}{% endif %}{% if b.cca %}, {{ b.cca }} CCA{% endif %} {{ badge(b.src, b.confidence) }} {{ cite(b.src) }}</dd>
{% endfor %}
{% if y.wipers %}
<dt>Wiper blades</dt>
<dd>{% if y.wipers.driver_in %}Driver {{ y.wipers.driver_in }}"{% endif %}{% if y.wipers.passenger_in %}, passenger {{ y.wipers.passenger_in }}"{% endif %}{% if y.wipers.rear_in %}, rear {{ y.wipers.rear_in }}"{% endif %} {{ badge(y.wipers.src) }} {{ cite(y.wipers.src) }}</dd>
{% endif %}
</dl>
{% if y.battery and y.battery.options %}{{ battery_disclaimer() }}{% endif %}
</section>
{% endif %}

{% if y.dims.summary %}
<section id="dimensions">
<h2>Dimensions &amp; weight</h2>
{% set s = y.dims.summary %}
<dl class="specs">
{% if s.length_in %}<dt>Length</dt><dd>{{ s.length_in|unique|join("–") }} in ({{ s.length_mm|unique|join("–") }} mm)</dd>{% endif %}
{% if s.width_in %}<dt>Width</dt><dd>{{ s.width_in|unique|join("–") }} in</dd>{% endif %}
{% if s.height_in %}<dt>Height</dt><dd>{{ s.height_in|unique|join("–") }} in</dd>{% endif %}
{% if s.wheelbase_in %}<dt>Wheelbase</dt><dd>{{ s.wheelbase_in|unique|join("–") }} in</dd>{% endif %}
{% if s.curb_weight_lb %}<dt>Curb weight</dt><dd>{{ s.curb_weight_lb|unique|join("–") }} lb</dd>{% endif %}
</dl>
<p class="small">{{ y.dims.variants|length }} body/drive variants measured by Transport Canada (Canadian Vehicle Specifications).</p>
</section>
{% endif %}

{% if y.nhtsa %}
<section id="safety">
<h2>Safety: recalls, complaints, crash ratings</h2>
<dl class="specs">
<dt>Recalls</dt><dd>{{ y.nhtsa.recalls.count }}</dd>
{% if y.nhtsa.complaints %}<dt>Owner complaints</dt><dd>{{ y.nhtsa.complaints.count }}</dd>{% endif %}
{% if y.nhtsa.ncap.overall_best %}<dt>NCAP overall</dt><dd>{{ y.nhtsa.ncap.overall_worst }}{% if y.nhtsa.ncap.overall_worst != y.nhtsa.ncap.overall_best %}–{{ y.nhtsa.ncap.overall_best }}{% endif %} stars</dd>{% endif %}
</dl>
{% if y.nhtsa.ncap.variants %}
<div class="table-wrap"><table>
<thead><tr><th>Tested variant</th><th>Overall</th><th>Frontal</th><th>Side</th><th>Rollover</th></tr></thead>
<tbody>{% for v in y.nhtsa.ncap.variants %}<tr><td>{{ v.description }}</td><td>{{ v.overall or "—" }}</td><td>{{ v.front or "—" }}</td><td>{{ v.side or "—" }}</td><td>{{ v.rollover or "—" }}</td></tr>{% endfor %}</tbody>
</table></div>
{% endif %}
{% if y.nhtsa.recalls.campaigns %}
<details><summary>Recall campaigns ({{ y.nhtsa.recalls.campaigns|length }})</summary>
<ul class="recalls">{% for c in y.nhtsa.recalls.campaigns %}<li><a href="https://www.nhtsa.gov/?nhtsaId={{ c.campaign }}" rel="nofollow noopener" target="_blank"><strong>{{ c.campaign }}</strong></a> {% if c.date %}<span class="muted">{{ c.date }}</span>{% endif %}: {{ c.component }}</li>{% endfor %}</ul>
</details>
{% endif %}
<p class="small">Source: NHTSA recalls, complaints and NCAP APIs.</p>
</section>
{% endif %}

<nav class="year-nav">
{% if prev_year %}<a href="/{{ m.slug }}/{{ prev_year }}/">← {{ prev_year }} {{ m.model }}</a>{% else %}<span></span>{% endif %}
<a href="/{{ m.slug }}/">All {{ m.model }} years</a>
{% if next_year %}<a href="/{{ m.slug }}/{{ next_year }}/">{{ next_year }} {{ m.model }} →</a>{% else %}<span></span>{% endif %}
</nav>
<h2>More {{ m.make }} {{ m.model }} specs</h2>
{{ spec_links(m, available) }}
{% if same_year %}<h2>Other {{ year }} vehicles</h2>
<ul class="link-list">{% for s in same_year %}<li><a href="/{{ s.slug }}/{{ year }}/">{{ year }} {{ s.make }} {{ s.model }}</a></li>{% endfor %}</ul>{% endif %}
{% endblock %}"""

T["spec.html"] = r"""{% extends "base.html" %}
{% from "macros.html" import cite, badge, battery_disclaimer, spec_links with context %}
{% block body %}
<h1>{{ m.make }} {{ m.model }} {{ label|lower }} by year</h1>
<p class="lede">{{ intro }}</p>
{% if spec == "battery-size" %}{{ battery_disclaimer() }}{% endif %}
<div class="table-wrap">
<table class="sortable">
<thead><tr>{% for h in head %}<th{% if h[1] %} data-sort="num"{% endif %}>{{ h[0] }}</th>{% endfor %}</tr></thead>
<tbody>
{% for r in rows %}<tr>{% for c in r %}<td{% if c.v is not none %} data-v="{{ c.v }}"{% endif %}>{{ c.html }}</td>{% endfor %}</tr>
{% endfor %}
</tbody>
</table>
</div>
{% if missing %}<p class="muted small">No sourced value yet for {{ missing|join(", ") }}. We leave gaps blank rather than guess.</p>{% endif %}
<p class="small">Each year links to its full spec page, which lists every configuration with the source document and page. <a href="/guides/{{ guide.slug }}/">{{ guide.title }}</a>.</p>
{% if faq %}
<h2>Frequently asked questions</h2>
{% for q in faq %}<h3>{{ q.q }}</h3><p>{{ q.a }}</p>{% endfor %}
{% endif %}
<h2>More {{ m.make }} {{ m.model }} specs</h2>
{{ spec_links(m, available, spec) }}
{% if others %}<h2>{{ label }} for other vehicles</h2>
<ul class="link-list">{% for s in others %}<li><a href="/{{ s.slug }}/{{ spec }}/">{{ s.make }} {{ s.model }} {{ label|lower }}</a></li>{% endfor %}</ul>{% endif %}
{% endblock %}"""

T["guides.html"] = r"""{% extends "base.html" %}
{% block body %}
<h1>Fitment &amp; spec guides</h1>
<p class="lede">Short explainers for the numbers on our spec pages.</p>
<ul class="guide-list">{% for g in guides %}<li><a href="/guides/{{ g.slug }}/">{{ g.title }}</a><br><span class="muted">{{ g.summary }}</span></li>{% endfor %}</ul>
{% endblock %}"""

T["guide.html"] = r"""{% extends "base.html" %}
{% block body %}
<article class="prose">
<h1>{{ g.title }}</h1>
<p class="lede">{{ g.summary }}</p>
{{ g.html|safe }}
{% if g.spec %}
<h2>Look it up by vehicle</h2>
<ul class="link-list">{% for s in all_models %}{% if g.spec in s.available %}<li><a href="/{{ s.slug }}/{{ g.spec }}/">{{ s.make }} {{ s.model }} {{ specs[g.spec][0]|lower }}</a></li>{% endif %}{% endfor %}</ul>
{% endif %}
<p class="muted small">Last reviewed {{ updated }}.</p>
</article>
<h2>More guides</h2>
<ul class="link-list">{% for o in guides if o.slug != g.slug %}<li><a href="/guides/{{ o.slug }}/">{{ o.title }}</a></li>{% endfor %}</ul>
{% endblock %}"""

T["page.html"] = r"""{% extends "base.html" %}
{% block body %}
<article class="prose">
<h1>{{ heading }}</h1>
{{ content|safe }}
</article>
{% endblock %}"""

T["404.html"] = r"""{% extends "base.html" %}
{% block body %}
<h1>Page not found</h1>
<p>That page doesn't exist. Try the search box above, or start from one of these:</p>
<ul class="link-list">{% for m in all_models %}<li><a href="/{{ m.slug }}/">{{ m.make }} {{ m.model }} specs</a></li>{% endfor %}<li><a href="/guides/">Guides</a></li></ul>
{% endblock %}"""


# ------------------------------------------------------------------ guides (general explainers)
GUIDES = [
    {"slug": "bolt-pattern-explained", "spec": "bolt-pattern",
     "title": "Bolt pattern explained: what 6x139.7 means",
     "summary": "How lug count, pitch circle diameter and center bore decide whether a wheel fits.",
     "html": """
<h2>The two numbers</h2>
<p>A bolt pattern such as <strong>6x139.7</strong> gives the number of wheel studs (6) and the diameter of the imaginary circle that runs through their centers, the pitch circle diameter (PCD), in millimeters (139.7 mm). The same pattern is often written in inches: 6x139.7 mm is 6x5.5".</p>
<h2>Measuring it</h2>
<ul>
<li><strong>Even stud count</strong> (4, 6, 8): measure center to center across two directly opposite studs.</li>
<li><strong>Five studs</strong>: there is no opposite stud, so measure from the center of one stud to the far edge of a stud that isn't next to it, or use a bolt-pattern gauge.</li>
</ul>
<p>Patterns that look close are not interchangeable. 6x135 (Ford F-150 since 2004) and 6x139.7 (Silverado, Tacoma) differ by under 5 mm, enough to stress the studs.</p>
<h2>Center bore</h2>
<p>The center bore is the hole in the middle of the wheel that sits over the hub. On a <em>hub-centric</em> wheel it matches the hub diameter, so the hub carries the load and centers the wheel. Aftermarket wheels often have a larger bore; a hub-centric ring fills the gap. A wheel whose bore is <em>smaller</em> than the hub will not fit.</p>
<h2>Also check</h2>
<ul><li><strong>Offset</strong> (ET, in mm) moves the wheel in or out and affects clearance to brakes, suspension and fenders.</li>
<li><strong>Lug nut seat</strong> (conical, ball or flat) must match the wheel.</li>
<li><strong>Thread size</strong> of the studs (for example M14x1.5) must match the lug nuts.</li></ul>
"""},
    {"slug": "towing-capacity-explained", "spec": "towing-capacity",
     "title": "Towing capacity explained: max trailer, tongue weight and GCWR",
     "summary": "Why one truck has a dozen towing ratings, and which limit applies to you.",
     "html": """
<h2>Max trailer weight</h2>
<p>The maximum trailer weight rating is the heaviest loaded trailer the manufacturer approves for a specific configuration. The rating changes with the engine, axle ratio, cab and bed, drive type and towing package, which is why our tables list each configuration with the document it came from.</p>
<h2>Tongue weight</h2>
<p>Tongue weight is the downward force the trailer puts on the hitch ball. Most manufacturers ask for roughly 10–15% of the trailer's weight for a conventional trailer; too little makes a trailer sway, too much overloads the rear axle. It counts toward the vehicle's payload.</p>
<h2>GCWR</h2>
<p>The gross combined weight rating (GCWR) is the maximum weight of the loaded vehicle <em>plus</em> the loaded trailer. Passengers and cargo in the vehicle use up part of it, so a fully loaded truck may not be able to tow its maximum trailer rating.</p>
<h2>Which limit applies</h2>
<p>All of them at once: trailer weight, tongue weight, payload, GVWR, rear axle rating (GAWR) and GCWR. Whichever you hit first is your real limit. Your vehicle's door-jamb placards show GVWR, GAWR and payload for that exact truck.</p>
<h2>Equipment</h2>
<p>Higher ratings often require a factory towing package, a specific axle ratio, a weight-distributing hitch or trailer brakes. The "Required" column on our year pages lists what the source document says the rating needs.</p>
"""},
    {"slug": "engine-oil-viscosity-explained", "spec": "oil-capacity",
     "title": "Engine oil viscosity explained: what 0W-20 and 5W-30 mean",
     "summary": "Reading an SAE oil grade, and why the capacity figure includes the filter.",
     "html": """
<h2>Reading the grade</h2>
<p>An SAE multigrade such as <strong>5W-30</strong> has two parts. The number before the W ("winter") rates how the oil flows when cold: lower numbers flow more easily at start-up. The number after the dash is the viscosity at normal operating temperature (100 °C): higher numbers are thicker.</p>
<p>A 0W-20 and a 5W-20 are equally thick when hot; the 0W-20 flows better on a cold start.</p>
<h2>Use the grade your manual lists</h2>
<p>Modern engines are designed around a specific viscosity, and many manuals also call for an approval or specification (API SP, ILSAC GF-6, or a maker's own standard such as GM dexos or a Chrysler MS number). Diesel engines usually need a diesel-rated oil.</p>
<h2>Capacity</h2>
<p>The capacities we list are the refill amount <em>with a filter change</em>, as printed in the source. Add oil gradually and check the dipstick, since some oil always stays in the engine.</p>
"""},
    {"slug": "how-to-read-a-tire-size", "spec": "tire-size",
     "title": "How to read a tire size: P245/75R17 and LT285/70R17C",
     "summary": "Width, aspect ratio, construction, rim size and the P/LT prefix.",
     "html": """
<h2>The parts of P245/75R17</h2>
<ul>
<li><strong>P</strong>: P-metric passenger tire. <strong>LT</strong> means light truck, built for heavier loads and higher pressures. No prefix usually means a European metric size.</li>
<li><strong>245</strong>: section width in millimeters.</li>
<li><strong>75</strong>: aspect ratio; sidewall height is 75% of the width.</li>
<li><strong>R</strong>: radial construction.</li>
<li><strong>17</strong>: rim diameter in inches.</li>
</ul>
<p>A trailing letter such as the <strong>C</strong> in LT285/70R17C is the load range (C, D, E…), which sets the maximum load and inflation pressure.</p>
<h2>Flotation sizes</h2>
<p>Off-road sizes such as <strong>31x10.50R15LT</strong> give overall diameter (31") and width (10.5") in inches, then the rim size.</p>
<h2>Load and speed</h2>
<p>The service description after the size, such as 109S, is the load index (109 = 2,271 lb per tire) and speed rating (S = 112 mph). Replacement tires should meet or exceed the original load index.</p>
<p>The tire size your vehicle was built with is on the door-jamb placard. Different trims of the same model year often use different sizes.</p>
"""},
    {"slug": "battery-group-sizes-explained", "spec": "battery-size",
     "title": "Battery group sizes explained: 24F, 48 (H6), 94R (H7)",
     "summary": "What BCI group numbers mean, the H/L names, and how to check yours.",
     "html": """
<h2>What a group size is</h2>
<p>The Battery Council International (BCI) group number defines a battery's outside dimensions, terminal type and terminal position. It doesn't set capacity: two group 48 batteries can have very different cold-cranking amps (CCA) and reserve capacity.</p>
<h2>Common names</h2>
<p>European-style sizes have two names. Group <strong>48</strong> is also sold as <strong>H6</strong> or L3, <strong>94R</strong> as <strong>H7</strong> or L4, <strong>49</strong> as H8 or L5, and <strong>47</strong> as H5 or L2.</p>
<h2>The letters</h2>
<p>An <strong>R</strong> suffix means reversed terminal positions compared with the base group. An <strong>F</strong> (as in 24F) also means reversed terminals. Fitting the wrong one can leave the cables too short to reach.</p>
<h2>Check before you buy</h2>
<p>Group sizes can change with engine, trim, cold-weather or towing packages, and start-stop systems (which usually need an AGM battery). Read the label on the battery that's in the vehicle, or the owner's manual, and match CCA at least to the original. Most battery group sizes on this site come from third-party references and are marked <em>low confidence</em>.</p>
"""},
    {"slug": "wiper-blade-sizes-explained", "spec": "wiper-size",
     "title": "Wiper blade sizes explained: driver, passenger and rear",
     "summary": "Why the two front blades differ, and what to check besides length.",
     "html": """
<h2>Two lengths</h2>
<p>Most vehicles use a longer blade on the driver's side and a shorter one on the passenger side, sized to sweep the windshield without the blades hitting each other or the pillars. SUVs and hatchbacks often add a rear blade.</p>
<h2>Length isn't everything</h2>
<p>Blades attach with different connectors (J-hook, pin, side lock, bayonet and others). Replacement blades from the major brands come with adapters, but check that your arm type is covered.</p>
<h2>Our sources</h2>
<p>Where the manufacturer's manual or parts catalog lists blade lengths we use those. Otherwise the lengths come from a wiper maker's fitment lookup and are marked third-party. When a lookup lists more than one length for a position, we leave it blank.</p>
"""},
]


def page_content() -> dict[str, tuple[str, str, str]]:
    ga = ("<li><strong>Google Analytics 4</strong> measures page views and general usage (pages visited, approximate location, device type). "
          "It uses cookies set by Google.</li>") if GA_ID else ""
    return {
        "about": ("About FitmentChart", "About FitmentChart: a cited database of vehicle fitment and specs.", f"""
<p>FitmentChart is a reference for the specs you need when buying parts or towing: bolt pattern and center bore, towing capacity,
engine oil type and capacity, tire sizes, battery group and wiper blade sizes, plus engines, fuel economy, dimensions, recalls
and crash ratings, organised by year, make and model.</p>
<h2>Every value has a source</h2>
<p>Towing, oil, tire, battery and wiper values link to the document they came from, usually an owner's manual page, an OEM towing
guide or a manufacturer spec sheet. Values from third-party references are labelled <em>third-party</em>, and battery group sizes
that come only from third-party lookups are labelled <em>low confidence</em>. When no source gives a value we leave it blank.</p>
<p>See <a href="/sources/">data sources</a> for the full list.</p>
<h2>Check before you buy</h2>
<p>Manufacturers change parts mid-year and by trim or package. Always confirm against your vehicle's door placard, owner's manual,
the label on the part you're replacing, or the part maker's fitment guide.</p>
<h2>Contact</h2>
<p>Found an error, or have a document that fills a gap? Email <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.
Corrections with a source are especially welcome.</p>
"""),
        "sources": ("Data sources", "Where FitmentChart's vehicle specs come from: NHTSA, EPA, Transport Canada, OEM manuals and more.", """
<ul>
<li><strong>NHTSA vPIC</strong>: makes, models and model years.</li>
<li><strong>EPA fueleconomy.gov</strong>: engines, transmissions, drive types and fuel economy. Horsepower comes from the EPA's
"Data on Cars Used for Testing Fuel Economy" files.</li>
<li><strong>Transport Canada, Canadian Vehicle Specifications</strong> (via NHTSA): exterior dimensions and curb weight.</li>
<li><strong>NHTSA</strong> recalls, complaints and NCAP crash-test APIs.</li>
<li><strong><a href="https://ankusiwheels.com/wheel-fitment-dataset/">ANKUSI Wheel Fitment Dataset</a></strong>: bolt pattern,
center bore and factory wheel sizes, licensed under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>.
Where a year has no record of its own, the value is carried across a generation only if every record in that generation agrees,
and the page says so.</li>
<li><strong>OEM documents</strong>: owner's manuals (Toyota, GM, Honda, Mopar), Ford and GM towing guides, GM TechLink oil-capacity
charts, Ford, Honda and FCA/Stellantis spec sheets, and parts catalogs. Each value cites the document and page, with a verbatim
quote shown when you hover over the link.</li>
<li><strong>Third-party references</strong> (labelled): wiper-maker fitment lookups, tire-pressure and enthusiast reference sites,
and battery-size lookups. Battery group sizes from these sources are labelled <em>low confidence</em>.</li>
</ul>
<p>The data is rebuilt from these sources by an automated pipeline with quality checks. Pages show the date they were built.</p>
"""),
        "privacy": ("Privacy policy", "FitmentChart privacy policy: cookies, advertising and analytics.", f"""
<p>Last updated {TODAY.isoformat()}.</p>
<h2>What we collect</h2>
<p>FitmentChart has no accounts, forms or comments, and does not ask for personal information. The vehicle search runs in your
browser; your searches are not sent to us.</p>
<h2>Third-party services</h2>
<ul>
<li><strong>Google AdSense</strong> shows advertisements. Google and its partners may use cookies and similar technologies to
show ads based on your visits to this and other websites, and to measure ad performance. You can opt out of personalised
advertising at <a href="https://adssettings.google.com/">Google Ad Settings</a>. See
<a href="https://policies.google.com/technologies/ads">how Google uses information from sites that use its services</a>.</li>
{ga}
<li><strong>GitHub Pages</strong> hosts the site and may log IP addresses for security and operations; see GitHub's privacy statement.</li>
</ul>
<p>FitmentChart does not set its own cookies. For visitors in the European Economic Area, the UK and Switzerland, Google's
consent mode is set to deny advertising and analytics storage by default.</p>
<h2>Your choices</h2>
<p>You can block or delete cookies in your browser settings and use the Google opt-out above. Blocking cookies does not stop the site from working.</p>
<h2>Children</h2>
<p>The site is not directed at children under 13 and does not knowingly collect their information.</p>
<h2>Contact</h2>
<p>Questions about this policy: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>
"""),
        "terms": ("Terms of use", "FitmentChart terms of use and disclaimer.", f"""
<p>Last updated {TODAY.isoformat()}.</p>
<h2>Information only</h2>
<p>FitmentChart compiles vehicle specifications from public and manufacturer sources for general reference. Specifications vary
by trim, package, market and production date, and sources can contain errors. Nothing on this site replaces your vehicle's
owner's manual, its door placards or the part maker's fitment data.</p>
<h2>No warranty</h2>
<p>The site and its data are provided "as is", without warranties of any kind. We are not liable for any loss or damage arising
from use of the information, including incorrect parts, towing beyond a vehicle's actual ratings, or damage to a vehicle.
Never exceed the ratings on your vehicle's placards or in its owner's manual.</p>
<h2>Trademarks</h2>
<p>Vehicle makes and model names are trademarks of their owners and are used only to identify vehicles. FitmentChart is not
affiliated with or endorsed by any vehicle manufacturer.</p>
<h2>Third-party content</h2>
<p>Wheel data from the ANKUSI Wheel Fitment Dataset is used under CC BY 4.0. Links to external documents and sites are provided
for reference; we don't control their content.</p>
<h2>Contact</h2>
<p><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
"""),
    }


SITE_JS = r"""(function(){
// ---- search over /search-index.json
var idx=null, loading=null;
function load(){ if(idx) return Promise.resolve(idx); if(!loading) loading=fetch('/search-index.json').then(function(r){return r.json()}).then(function(d){idx=d;return d}); return loading; }
function norm(s){ return (s||'').toLowerCase().replace(/[^a-z0-9.x]+/g,' ').trim(); }
function score(item, terms){ var h=norm(item.t+' '+(item.k||'')); var s=0; for(var i=0;i<terms.length;i++){ if(h.indexOf(terms[i])<0) return 0; s+= (' '+h+' ').indexOf(' '+terms[i]+' ')>=0?2:1; } return s - item.t.length/1000; }
function esc(s){ return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]}); }
document.querySelectorAll('.search-input').forEach(function(inp){
  var box=inp.parentNode.querySelector('.search-results'); var sel=-1;
  function render(list){ sel=-1; if(!list.length){ box.innerHTML='<div class="sr-empty">No matches</div>'; box.hidden=false; return; }
    box.innerHTML=list.map(function(r){ return '<a href="'+r.u+'">'+esc(r.t)+(r.d?'<span>'+esc(r.d)+'</span>':'')+'</a>'; }).join(''); box.hidden=false; }
  inp.addEventListener('input', function(){ var q=norm(inp.value); if(q.length<2){ box.hidden=true; return; }
    load().then(function(d){ var terms=q.split(' '); var out=[]; for(var i=0;i<d.length;i++){ var s=score(d[i],terms); if(s>0) out.push([s,d[i]]); }
      out.sort(function(a,b){return b[0]-a[0]}); render(out.slice(0,10).map(function(x){return x[1]})); }); });
  inp.addEventListener('keydown', function(e){ var links=box.querySelectorAll('a'); if(!links.length) return;
    if(e.key==='ArrowDown'){ sel=Math.min(sel+1,links.length-1); e.preventDefault(); }
    else if(e.key==='ArrowUp'){ sel=Math.max(sel-1,0); e.preventDefault(); }
    else if(e.key==='Enter'){ location.href=(links[sel>=0?sel:0]).getAttribute('href'); e.preventDefault(); return; }
    else if(e.key==='Escape'){ box.hidden=true; return; } else return;
    links.forEach(function(a,i){ a.classList.toggle('active', i===sel); }); });
  document.addEventListener('click', function(e){ if(!inp.parentNode.contains(e.target)) box.hidden=true; });
  var q=new URLSearchParams(location.search).get('q'); if(q && inp.closest('.hero-search')){ inp.value=q; inp.dispatchEvent(new Event('input')); }
});
// ---- sortable tables
document.querySelectorAll('table.sortable').forEach(function(t){
  var ths=t.querySelectorAll('thead th');
  ths.forEach(function(th,col){ th.tabIndex=0; th.setAttribute('role','button'); th.setAttribute('aria-sort','none');
    function go(){ var asc=th.getAttribute('aria-sort')!=='ascending'; ths.forEach(function(o){o.setAttribute('aria-sort','none')}); th.setAttribute('aria-sort', asc?'ascending':'descending');
      var num=th.dataset.sort==='num'; var body=t.tBodies[0]; var rows=Array.prototype.slice.call(body.rows);
      rows.sort(function(a,b){ var x=a.cells[col], y=b.cells[col]; var vx=x.dataset.v!==undefined?x.dataset.v:x.textContent.trim(), vy=y.dataset.v!==undefined?y.dataset.v:y.textContent.trim();
        if(num){ vx=parseFloat(String(vx).replace(/[^0-9.\-]/g,''))||0; vy=parseFloat(String(vy).replace(/[^0-9.\-]/g,''))||0; return asc?vx-vy:vy-vx; }
        return asc?String(vx).localeCompare(vy,undefined,{numeric:true}):String(vy).localeCompare(vx,undefined,{numeric:true}); });
      rows.forEach(function(r){ body.appendChild(r); }); }
    th.addEventListener('click',go); th.addEventListener('keydown',function(e){ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); go(); } }); });
});
})();
"""

SITE_CSS = r""":root{--bg:#f7f8fa;--fg:#1d2433;--muted:#5d6678;--line:#dfe3ea;--card:#fff;--accent:#e85d04;--link:#1f5fbf;--head:#14213d;--headfg:#fff;--warn-bg:#fff4e5;--warn:#8a4b00;--th:#eef1f6}
@media (prefers-color-scheme:dark){:root{--bg:#0f141c;--fg:#e4e8ef;--muted:#9aa4b5;--line:#2a3343;--card:#161d28;--link:#7fb1ff;--head:#0a0f17;--warn-bg:#3a2a12;--warn:#ffc27a;--th:#1c2533}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--link)}
.container{max-width:1120px;margin:0 auto;padding:0 16px}
.site-header{background:var(--head);color:var(--headfg);position:sticky;top:0;z-index:20}
.header-inner{display:flex;align-items:center;gap:20px;min-height:58px;flex-wrap:wrap;padding-top:6px;padding-bottom:6px}
.logo{color:#fff;text-decoration:none;font-weight:800;font-size:1.25rem;letter-spacing:-.02em}
.logo span{color:var(--accent)}
.site-nav{display:flex;gap:14px;flex-wrap:wrap}
.site-nav a{color:#d6dcea;text-decoration:none;font-size:.95rem}
.site-nav a:hover{color:#fff}
.header-search{margin-left:auto;position:relative;flex:0 1 280px}
.search-input{width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--line);font:inherit;background:var(--card);color:var(--fg)}
.site-header .search-input{border-color:#34405c;background:#1e2a47;color:#fff}
.site-header .search-input::placeholder{color:#9fb0cf}
.search-results{position:absolute;left:0;right:0;top:calc(100% + 4px);background:var(--card);border:1px solid var(--line);border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.18);max-height:60vh;overflow:auto;z-index:30}
.search-results a{display:block;padding:8px 12px;color:var(--fg);text-decoration:none;border-bottom:1px solid var(--line)}
.search-results a span{display:block;font-size:.8rem;color:var(--muted)}
.search-results a:hover,.search-results a.active{background:var(--th)}
.sr-empty{padding:8px 12px;color:var(--muted)}
main{padding-top:18px;padding-bottom:40px;min-height:60vh}
h1{font-size:1.9rem;line-height:1.2;margin:.4em 0 .3em;letter-spacing:-.02em}
h2{font-size:1.35rem;margin:1.8em 0 .6em}
h3{font-size:1.05rem;margin:1.2em 0 .4em}
.lede{font-size:1.08rem;color:var(--muted);max-width:780px}
.muted{color:var(--muted)}
.small{font-size:.88rem}
.crumbs{font-size:.88rem;color:var(--muted);margin-bottom:6px}
.crumbs a{color:var(--muted)}
.hero{padding:22px 0 8px}
.hero h1{font-size:2.3rem}
.hero-search{position:relative;max-width:620px}
.hero-search .search-input{padding:13px 16px;font-size:1.05rem}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px}
.card{display:flex;flex-direction:column;gap:4px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;text-decoration:none;color:var(--fg);transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--accent);transform:translateY(-1px)}
.card-title{font-weight:700;font-size:1.08rem}
.card-meta,.card-facts{font-size:.88rem;color:var(--muted)}
.table-wrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px;margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:.93rem}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--th);font-weight:600;white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
table.sortable th{cursor:pointer;user-select:none}
table.sortable th::after{content:" ⇅";color:var(--muted);font-size:.8em}
table.sortable th[aria-sort=ascending]::after{content:" ▲"}
table.sortable th[aria-sort=descending]::after{content:" ▼"}
.matrix td,.matrix th{white-space:nowrap}
dl.specs{display:grid;grid-template-columns:max-content 1fr;gap:6px 18px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:10px 0}
dl.specs dt{font-weight:600;color:var(--muted)}
dl.specs dd{margin:0}
.cite{font-size:.82rem}
.cite a{color:var(--muted)}
.badge{display:inline-block;font-size:.72rem;font-weight:600;padding:1px 7px;border-radius:999px;vertical-align:1px;white-space:nowrap}
.badge-3p{background:var(--th);color:var(--muted)}
.badge-low{background:var(--warn-bg);color:var(--warn)}
.disclaimer{background:var(--warn-bg);color:var(--warn);border-radius:8px;padding:8px 12px;font-size:.92rem}
.note{font-size:.92rem;color:var(--muted)}
.toc,.spec-links{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.toc a,.spec-links a{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:.88rem;text-decoration:none}
.year-nav{display:flex;justify-content:space-between;gap:10px;margin:28px 0 8px;flex-wrap:wrap}
.link-list{columns:2 260px;padding-left:18px}
.link-list li{margin:3px 0;break-inside:avoid}
.guide-list{padding-left:18px}
.guide-list li{margin:8px 0}
.about-box{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:4px 18px 10px;margin-top:28px}
.prose{max-width:760px}
.recalls{font-size:.92rem}
details summary{cursor:pointer;font-weight:600;margin:10px 0}
.ad-slot{margin:16px 0;min-height:90px}
.site-footer{background:var(--head);color:#c4cbe0;padding:28px 0 18px;font-size:.92rem}
.site-footer a{color:#dfe5f3}
.footer-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:18px}
.footer-col{display:flex;flex-direction:column;gap:4px}
.footer-col h4{color:#fff;margin:0 0 6px}
.footer-note{margin-top:18px;color:#9ea8c2}
@media (max-width:640px){.site-header{position:static}h1{font-size:1.5rem}.hero h1{font-size:1.75rem}.header-search{flex-basis:100%;margin-left:0}.site-nav{gap:10px}dl.specs{grid-template-columns:1fr}dl.specs dt{margin-top:6px}}
"""

# ------------------------------------------------------------------ page builders
class Site:
    def __init__(self, models: list[dict]):
        self.models = models
        self.urls: list[tuple[str, float]] = []
        self.search: list[dict] = []
        self.env = Environment(loader=DictLoader(T), extensions=["jinja2.ext.do"],
                               autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
        self.env.filters["commas"] = commas
        self.env.filters["towcfg"] = tow_config
        self.env.globals["ad"] = self.ad
        self.cards = [self.card(m) for m in models]
        makes: dict[str, dict] = {}
        for c in self.cards:
            makes.setdefault(c["make_slug"], {"slug": c["make_slug"], "name": c["make"], "models": []})["models"].append(c)
        self.makes = sorted(makes.values(), key=lambda x: x["name"])
        self.common = dict(site_url=SITE_URL, site_name=SITE_NAME, adsense_pub=ADSENSE_PUB, ga_id=GA_ID,
                           css_version=CSS_VERSION, nav_makes=self.makes, all_models=self.cards, specs=SPECS,
                           year_now=TODAY.year, email=CONTACT_EMAIL, guides=GUIDES, updated=TODAY.isoformat())

    @staticmethod
    def ad(name: str):
        slot = AD_SLOTS.get(name)
        if not slot:
            return ""
        return Markup(f'<div class="ad-slot"><ins class="adsbygoogle" style="display:block" data-ad-client="{ADSENSE_PUB}" '
                      f'data-ad-slot="{slot}" data-ad-format="auto" data-full-width-responsive="true"></ins>'
                      f'<script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script></div>')

    def card(self, m: dict) -> dict:
        ys = sorted(m["years"], key=int)
        bolts = [(m["years"][y].get("wheel") or {}).get("bolt_pattern") for y in ys]
        bolts = [b for b in bolts if b]
        latest_bolt = bolts[-1] if bolts else None
        tows = [towing_max(m["years"][y]) for y in ys]
        avail = [s for s in SPECS if any(has_spec(s, m["years"][y]) for y in ys)]
        return {"slug": m["slug"], "make": m["make"], "model": m["model"], "make_slug": make_slug(m),
                "first": ys[0], "last": ys[-1], "n": len(ys), "bolt": latest_bolt,
                "tow": max([t for t in tows if t] or [0]) or None, "available": avail}

    def render(self, tpl: str, path: str, title: str, description: str, crumbs=(), jsonld=(), priority=0.5, **ctx):
        ld = list(jsonld)
        if crumbs:
            ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": label, "item": SITE_URL + href}
                for i, (href, label) in enumerate(crumbs)]})
        title = fit_title(title)
        description = fit_desc(description)
        html = self.env.get_template(tpl).render(path=path, title=title, description=description, crumbs=list(crumbs),
                                                 jsonld=ld, **self.common, **ctx)
        out = DOCS / ("404.html" if tpl == "404.html" else path.lstrip("/") + "index.html")
        write(out, html)
        if tpl != "404.html":
            self.urls.append((path, priority))

    # -- home / make
    def home(self):
        ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + "/",
               "potentialAction": {"@type": "SearchAction", "target": SITE_URL + "/?q={search_term_string}",
                                   "query-input": "required name=search_term_string"}},
              {"@context": "https://schema.org", "@type": "Organization", "name": SITE_NAME, "url": SITE_URL + "/",
               "email": CONTACT_EMAIL}]
        names = ", ".join(f"{c['make']} {c['model']}" for c in self.cards)
        self.render("home.html", "/", f"{SITE_NAME}: Bolt Patterns, Towing, Oil, Tire & Battery Specs",
                    f"Cited vehicle specs by year: bolt pattern, towing capacity, oil type and capacity, tire, battery "
                    f"and wiper sizes for the {names}.", jsonld=ld, priority=1.0, model_cards=self.cards)

    def make_pages(self):
        for mk in self.makes:
            models = ", ".join(c["model"] for c in mk["models"])
            self.render("make.html", f"/{mk['slug']}/", f"{mk['name']} fitment & specs by model and year",
                        f"{mk['name']} {models}: bolt pattern, towing capacity, oil capacity, tire, battery and wiper "
                        f"sizes by model year, each with a cited source.",
                        crumbs=[("/", "Home"), (f"/{mk['slug']}/", mk["name"])], priority=0.7, make=mk)
            self.search.append({"t": mk["name"], "u": f"/{mk['slug']}/", "d": f"{len(mk['models'])} models"})

    # -- model
    def model_page(self, m: dict, card: dict):
        ys = sorted(m["years"], key=int)
        rows = []
        for y in ys:
            b = m["years"][y]
            oils = oil_summary(b)
            oil = "; ".join(sorted({f"{o['grade']}" + (f", {o['capacity_qt']} qt" if o.get("capacity_qt") else "")
                                    if o.get("grade") else f"{o['capacity_qt']} qt" for o in oils if o.get("grade") or o.get("capacity_qt")}))
            bats = sorted({o["group"] for o in battery_groups(b)})
            rows.append({"year": y, "generation": " / ".join(b.get("generation") or []),
                         "bolt": (b.get("wheel") or {}).get("bolt_pattern"), "tow": towing_max(b),
                         "engines": ", ".join(e["label"] for e in b.get("engines") or []),
                         "oil": oil if len(oil) < 60 else f"{len(oils)} engine specs",
                         "tires": ", ".join(tire_sizes(b)[:3]) + (" …" if len(tire_sizes(b)) > 3 else ""),
                         "battery": ", ".join(bats), "recalls": ((b.get("nhtsa") or {}).get("recalls") or {}).get("count")})
        gens = []
        for g in m.get("generations") or []:
            first = next((y for y in ys if g["start"] <= int(y) <= (g["end"] or 9999)), None)
            if first:
                gens.append({**g, "first_year": first})
        bolts = sorted({r["bolt"] for r in rows if r["bolt"]})
        intro = (f"Bolt pattern {' / '.join(bolts)}" if bolts else "") + \
                (f"; towing up to {commas(card['tow'])} lb" if card["tow"] else "") + "."
        name = f"{m['make']} {m['model']}"
        self.render("model.html", f"/{m['slug']}/", f"{name} specs by year: towing, bolt pattern, oil",
                    f"{name} {ys[0]}–{ys[-1]} specs by year: bolt pattern {', '.join(bolts) or 'n/a'}, towing capacity, "
                    f"oil type and capacity, tire, battery and wiper sizes, engines and recalls.",
                    crumbs=[("/", "Home"), (f"/{card['make_slug']}/", m["make"]), (f"/{m['slug']}/", m["model"])],
                    priority=0.9, m=m, rows=rows, gens=gens, intro=intro, available=card["available"],
                    siblings=[c for c in self.cards if c["slug"] != m["slug"]])
        self.search.append({"t": name, "u": f"/{m['slug']}/", "d": f"{ys[0]}–{ys[-1]}", "k": " ".join(bolts)})

    # -- year
    def year_pages(self, m: dict, card: dict):
        ys = sorted(m["years"], key=int)
        name = f"{m['make']} {m['model']}"
        for i, y in enumerate(ys):
            b = m["years"][y]
            w = b.get("wheel") or {}
            tmax = towing_max(b)
            oils = oil_summary(b)
            bits = []
            if w.get("bolt_pattern"):
                bits.append(f"bolt pattern {w['bolt_pattern']}" + (f" ({w['center_bore_mm']} mm bore)" if w.get("center_bore_mm") else ""))
            if tmax:
                bits.append(f"towing up to {commas(tmax)} lb")
            grades = sorted({o["grade"] for o in oils if o.get("grade")})
            if grades:
                bits.append(f"oil {', '.join(grades)}")
            sizes = tire_sizes(b)
            if sizes:
                bits.append(f"tires {', '.join(sizes[:2])}" + (" and more" if len(sizes) > 2 else ""))
            summary = (f"The {y} {name} has " + ", ".join(bits) + "." if bits else
                       f"Specs for the {y} {name}.")
            desc = f"{y} {name} specs: " + (", ".join(bits) if bits else "engines, fuel economy, dimensions") + \
                   ". Plus battery, wipers, dimensions, recalls and crash ratings, with sources."
            if len(desc) > 300:
                desc = desc[:297].rsplit(" ", 1)[0] + "…"
            same_year = [c for c in self.cards if c["slug"] != m["slug"] and int(c["first"]) <= int(y) <= int(c["last"])]
            ld = {"@context": "https://schema.org", "@type": "Car", "name": f"{y} {name}",
                  "brand": {"@type": "Brand", "name": m["make"]}, "model": m["model"], "vehicleModelDate": y,
                  "url": f"{SITE_URL}/{m['slug']}/{y}/"}
            if b.get("engines"):
                ld["vehicleEngine"] = [{"@type": "EngineSpecification", "name": e["label"],
                                        **({"enginePower": {"@type": "QuantitativeValue", "value": max(e["hp"]), "unitCode": "BHP"}} if e.get("hp") else {})}
                                       for e in b["engines"]]
            if tmax:
                ld["trailerWeight"] = {"@type": "QuantitativeValue", "maxValue": tmax, "unitCode": "LBR"}
            self.render("year.html", f"/{m['slug']}/{y}/",
                        f"{y} {name} specs: bolt pattern, towing, oil", desc,
                        crumbs=[("/", "Home"), (f"/{card['make_slug']}/", m["make"]), (f"/{m['slug']}/", m["model"]),
                                (f"/{m['slug']}/{y}/", y)],
                        jsonld=[ld], priority=0.6, m=m, year=y, y=b, summary=summary, tow_max=tmax,
                        prev_year=ys[i - 1] if i else None, next_year=ys[i + 1] if i + 1 < len(ys) else None,
                        available=[s for s in card["available"]], same_year=same_year)
            self.search.append({"t": f"{y} {name}", "u": f"/{m['slug']}/{y}/", "d": ", ".join(bits[:2]),
                                "k": w.get("bolt_pattern") or ""})

    # -- spec across years
    def spec_pages(self, m: dict, card: dict):
        ys = sorted(m["years"], key=int)
        name = f"{m['make']} {m['model']}"
        guide = {g["slug"]: g for g in GUIDES}
        for spec in card["available"]:
            label, noun, gslug = SPECS[spec]
            rows, missing, faq = [], [], []
            ylink = lambda y: Markup(f'<a href="/{m["slug"]}/{y}/">{y}</a>')
            cell = lambda html, v=None: {"html": Markup(html) if isinstance(html, Markup) else html, "v": v}
            for y in ys:
                b = m["years"][y]
                if not has_spec(spec, b):
                    missing.append(y)
                    continue
                if spec == "towing-capacity":
                    best = max((t for t in b["towing"] if t.get("max_lb")), key=lambda t: t["max_lb"], default=None)
                    lo = min((t["max_lb"] for t in b["towing"] if t.get("max_lb")), default=None)
                    rows.append([cell(ylink(y), y), cell(f"{commas(best['max_lb'])} lb" if best else "Not rated", best["max_lb"] if best else 0),
                                 cell(f"{commas(lo)} lb" if lo else "—", lo or 0),
                                 cell(tow_config(best) + (f" ({best['package']})" if best.get("package") else "") if best else (b["towing"][0].get("note") or "—")),
                                 cell(str(len(b["towing"])), len(b["towing"]))])
                elif spec == "bolt-pattern":
                    w = b["wheel"]
                    oe = ", ".join(sorted({f"{o['diameter_in']}x{o['width_in']}" for o in w.get("oe_wheels") or []}))
                    rows.append([cell(ylink(y), y), cell(Markup(f"<strong>{w['bolt_pattern']}</strong>")),
                                 cell(f"{w['center_bore_mm']} mm" if w.get("center_bore_mm") else "—", w.get("center_bore_mm") or 0),
                                 cell(oe or "—"), cell("exact year" if w.get("basis") == "exact" else "generation")])
                elif spec == "oil-capacity":
                    for o in oil_summary(b):
                        rows.append([cell(ylink(y), y),
                                     cell((o.get("engine") or f"{o.get('displacement_l')}L") + (f" ({o['condition']})" if o.get("condition") else "")),
                                     cell(o.get("grade") or "—"),
                                     cell(f"{o['capacity_qt']} qt" if o.get("capacity_qt") else "—", o.get("capacity_qt") or 0)])
                elif spec == "tire-size":
                    for t in b["tires"]:
                        rows.append([cell(ylink(y), y), cell(Markup(f"<strong>{t['size']}</strong>")), cell(t.get("trim") or "—")])
                elif spec == "battery-size":
                    for o in battery_groups(b):
                        badge = '<span class="badge badge-low">low confidence</span>' if o.get("confidence") == "low" else ""
                        rows.append([cell(ylink(y), y),
                                     cell(Markup(f"<strong>{o['group']}</strong>" + (f" ({o['din']})" if o.get("din") else "") + " " + badge)),
                                     cell(o.get("engine") or (f"{o['displacement_l']}L" if o.get("displacement_l") else "All")),
                                     cell(o.get("condition") or "—")])
                elif spec == "wiper-size":
                    wp = b["wipers"]
                    rows.append([cell(ylink(y), y), cell(f'{wp["driver_in"]}"' if wp.get("driver_in") else "—", wp.get("driver_in") or 0),
                                 cell(f'{wp["passenger_in"]}"' if wp.get("passenger_in") else "—", wp.get("passenger_in") or 0),
                                 cell(f'{wp["rear_in"]}"' if wp.get("rear_in") else "—", wp.get("rear_in") or 0)])
            head = {"towing-capacity": [("Year", 1), ("Max towing", 1), ("Lowest rating", 1), ("Configuration for max", 0), ("Configurations", 1)],
                    "bolt-pattern": [("Year", 1), ("Bolt pattern", 0), ("Center bore", 1), ("Factory wheels", 0), ("Basis", 0)],
                    "oil-capacity": [("Year", 1), ("Engine", 0), ("Oil grade", 0), ("Capacity", 1)],
                    "tire-size": [("Year", 1), ("Size", 0), ("Trim", 0)],
                    "battery-size": [("Year", 1), ("Group", 0), ("Engine", 0), ("Condition", 0)],
                    "wiper-size": [("Year", 1), ("Driver", 1), ("Passenger", 1), ("Rear", 1)]}[spec]
            covered = [y for y in ys if y not in missing]
            # intro + FAQ from the data
            if spec == "towing-capacity":
                maxes = {y: towing_max(m["years"][y]) for y in covered if towing_max(m["years"][y])}
                top = max(maxes.values()) if maxes else None
                ty = [y for y, v in maxes.items() if v == top]
                intro = ((f"The {name} can tow up to {commas(top)} lb when properly equipped ({', '.join(ty[:3])}{'…' if len(ty) > 3 else ''}). "
                          if top else f"The {name} has no published trailer rating in the years listed. ") +
                         "Ratings depend on engine, axle ratio, body, and towing equipment; the table shows each year's highest and lowest rating.")
                rated = [y for y in covered if y in maxes]
                if rated:
                    last = rated[-1]
                    faq = [{"q": f"How much can a {last} {name} tow?",
                            "a": f"Up to {commas(maxes[last])} lb in its best-equipped configuration, according to the cited sources. "
                                 f"The lowest listed rating that year is {commas(min(t['max_lb'] for t in m['years'][last]['towing'] if t.get('max_lb')))} lb."}]
            elif spec == "bolt-pattern":
                bolts = sorted({m["years"][y]["wheel"]["bolt_pattern"] for y in covered})
                intro = (f"The {name} uses a {' / '.join(bolts)} bolt pattern across {covered[0]}–{covered[-1]}. "
                         f"Center bore and factory wheel sizes are listed by year.")
                faq = [{"q": f"What is the {name} bolt pattern?",
                        "a": f"{' or '.join(bolts)} for the years listed here ({covered[0]}–{covered[-1]}). Check the year row for your model year."}]
            elif spec == "oil-capacity":
                intro = (f"Engine oil grade and capacity (with filter) for each {name} engine by year, each taken from an owner's manual, "
                         f"OEM chart or labelled reference.")
                last = covered[-1]
                o = oil_summary(m["years"][last])
                desc_o = "; ".join(f"{x.get('engine') or str(x.get('displacement_l')) + 'L'}: {x.get('grade') or 'grade not listed'}"
                                   + (f", {x['capacity_qt']} qt" if x.get("capacity_qt") else "") for x in o[:4])
                faq = [{"q": f"What oil does a {last} {name} take?", "a": desc_o + "."}]
            elif spec == "tire-size":
                intro = f"Factory tire sizes for the {name} by model year and trim. Check your door-jamb placard for the size your vehicle was built with."
            elif spec == "battery-size":
                intro = (f"Battery group sizes reported for the {name} by year. Most values come from third-party lookups and are marked "
                         f"low confidence; group sizes can change with engine, trim and options.")
            else:
                intro = f"Driver, passenger and rear wiper blade lengths for the {name} by year."
            title = f"{name} {noun} by year"
            desc = plain(intro)
            if len(desc) > 300:
                desc = desc[:297].rsplit(" ", 1)[0] + "…"
            ld = []
            if faq:
                ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                    {"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}} for q in faq]})
            self.render("spec.html", f"/{m['slug']}/{spec}/", title, desc,
                        crumbs=[("/", "Home"), (f"/{card['make_slug']}/", m["make"]), (f"/{m['slug']}/", m["model"]),
                                (f"/{m['slug']}/{spec}/", label)],
                        jsonld=ld, priority=0.8, m=m, spec=spec, label=label, head=head, rows=rows, missing=missing,
                        intro=intro, faq=faq, guide=guide[gslug], available=card["available"],
                        others=[c for c in self.cards if c["slug"] != m["slug"] and spec in c["available"]])
            self.search.append({"t": f"{name} {noun}", "u": f"/{m['slug']}/{spec}/", "d": "by year",
                                "k": {"towing-capacity": "tow towing", "bolt-pattern": "lug wheel", "oil-capacity": "oil",
                                      "tire-size": "tire tyre", "battery-size": "battery", "wiper-size": "wiper"}[spec]})

    # -- guides and static pages
    def guide_pages(self):
        self.render("guides.html", "/guides/", f"Vehicle fitment guides",
                    "Explainers for bolt patterns, towing capacity, oil viscosity, tire sizes, battery group sizes and wiper blades.",
                    crumbs=[("/", "Home"), ("/guides/", "Guides")], priority=0.6)
        for g in GUIDES:
            ld = {"@context": "https://schema.org", "@type": "Article", "headline": g["title"], "description": g["summary"],
                  "dateModified": TODAY.isoformat(), "author": {"@type": "Organization", "name": SITE_NAME},
                  "publisher": {"@type": "Organization", "name": SITE_NAME}, "mainEntityOfPage": f"{SITE_URL}/guides/{g['slug']}/"}
            self.render("guide.html", f"/guides/{g['slug']}/", f"{g['title']}", g["summary"],
                        crumbs=[("/", "Home"), ("/guides/", "Guides"), (f"/guides/{g['slug']}/", g["title"])],
                        jsonld=[ld], priority=0.6, g=g, og_type="article")
            self.search.append({"t": g["title"], "u": f"/guides/{g['slug']}/", "d": "Guide"})

    def static_pages(self):
        for slug, (heading, desc, html) in page_content().items():
            self.render("page.html", f"/{slug}/", f"{heading}", desc,
                        crumbs=[("/", "Home"), (f"/{slug}/", heading)], priority=0.3, heading=heading, content=html)
        self.render("404.html", "/404.html", "Page not found", "Page not found.", crumbs=[("/", "Home"), ("/404.html", "Page not found")])

    def finish(self):
        sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        sm += [f"  <url><loc>{SITE_URL}{u}</loc><lastmod>{TODAY.isoformat()}</lastmod><priority>{p:.1f}</priority></url>"
               for u, p in sorted(self.urls)]
        sm.append("</urlset>")
        write(DOCS / "sitemap.xml", "\n".join(sm) + "\n")
        write(DOCS / "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
        write(DOCS / "search-index.json", json.dumps(self.search, separators=(",", ":"), ensure_ascii=False))
        write(DOCS / "static" / "style.css", SITE_CSS)
        write(DOCS / "static" / "site.js", SITE_JS)
        for f in sorted((ROOT / "favicon").iterdir()):  # generated by scripts/make_favicons.py
            shutil.copy2(f, DOCS / f.name)
        write(DOCS / "CNAME", DOMAIN + "\n")
        write(DOCS / ".nojekyll", "")
        write(DOCS / "ads.txt", f"google.com, {ADSENSE_PUB.replace('ca-', '')}, DIRECT, f08c47fec0942fa0\n")


def main() -> int:
    rep = qa.run()
    if rep["summary"]["errors"]:
        print(f"QA has {rep['summary']['errors']} errors; run `python qa.py` and fix them first.")
        return 1
    models = [json.loads(p.read_text()) for p in sorted(MODELS.rglob("*.json"))]
    if not models:
        print("no models in data/models; run the pipeline first")
        return 1
    models.sort(key=lambda m: (m["make"], m["model"]))
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    site = Site(models)
    site.home()
    site.make_pages()
    for m, card in zip(models, site.cards):
        site.model_page(m, card)
        site.year_pages(m, card)
        site.spec_pages(m, card)
    site.guide_pages()
    site.static_pages()
    site.finish()
    print(f"built {len(site.urls)} pages into docs/ ({len(models)} models)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
