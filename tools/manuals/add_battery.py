"""Battery group sizes for all five models: LOW confidence, third-party only.

No OEM document found prints BCI group sizes for these vehicles, so the owner chose (2026-10-14) to publish
the gap-research values with a disclaimer. Each record carries `confidence: low` and cites:
- the research note line itself (source type `research_note`; the research cited autopadre.com,
  autofiles.com, getjerry.com, optimabatteries.com and owner forums), and
- the autopadre.com per-year row(s) that agree, quoted verbatim from the cached page
  (data/cache/web/autopadre/<make>-<model>.html), as corroboration.
Where autopadre lists a different group for a year the record covers, the record's `note` says so.
Run last (after add_chunk5.py).
"""
import re, sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from autopadre import rows as ap_rows

RESEARCH = {"doc": "Gap-research notes, battery section (2026-10-14); cites autopadre.com, autofiles.com, "
                   "getjerry.com, optimabatteries.com and owner forums",
            "type": "research_note", "accessed": "2026-10-14"}

# (years, group, din, displacement filter or None, engine text, condition, research quote)
DATA = {
    "ford/f-150": [
        ((2005, 2008), "65", None, None, "4.2L / 4.6L / 5.4L", None, "2005-2008 (4.2L/4.6L/5.4L): group=65, alt group=59"),
        ((2005, 2008), "59", None, None, "4.2L / 4.6L / 5.4L", "alternate fitment", "2005-2008 (4.2L/4.6L/5.4L): group=65, alt group=59"),
        ((2009, 2014), "65", None, None, "all engines", None, "2009-2014 (all engines): group=65"),
        ((2015, 2020), "48", "H6", None, "gas engines", "standard", "2015-2020 (gas): group=48 (H6) std; group=94R (H7) higher trims. 2015 may be H7 only."),
        ((2015, 2020), "94R", "H7", None, "gas engines", "higher trims (2015 may be H7 only)", "2015-2020 (gas): group=48 (H6) std; group=94R (H7) higher trims. 2015 may be H7 only."),
        ((2018, 2021), "49", "H8", 3.0, "3.0L Power Stroke diesel", "AGM", "2018-2021 (3.0L diesel): group=49 (H8) AGM"),
        ((2021, 2026), "48", "H6", None, "gas / hybrid", "AGM, standard", "2021-2026 (gas/hybrid): group=48 (H6) AGM std; group=94R (H7) AGM optional"),
        ((2021, 2026), "94R", "H7", None, "gas / hybrid", "AGM, optional", "2021-2026 (gas/hybrid): group=48 (H6) AGM std; group=94R (H7) AGM optional"),
    ],
    "honda/civic": [
        ((2006, 2015), "51R", None, None, "1.8L, Si, GX", None, "2006-2015 (1.8L, Si, GX): group=51R"),
        ((2016, 2021), "51R", None, 1.5, "1.5L turbo (incl. Si)", None, "2016-2021 1.5T (incl. Si): group=51R"),
        ((2016, 2021), "47", "H5", 2.0, "2.0L / Type R", None, "2016-2021 2.0L/Type R: group=47 (H5)"),
        ((2022, 2024), "51R", None, 1.5, "1.5L turbo", None, "2022-2024 1.5T: group=51R; 2.0L/Type R: group=47 (H5)"),
        ((2022, 2024), "47", "H5", 2.0, "2.0L / Type R", None, "2022-2024 1.5T: group=51R; 2.0L/Type R: group=47 (H5)"),
    ],
    "chevrolet/silverado-1500": [
        ((2005, 2006), "75", None, None, "all engines", None, "2005-2006: group=75"),
        ((2007, 2013), "48", "H6", None, "all engines", None, "2007-2013: group=48 (H6)"),
        ((2014, 2018), "48", "H6", None, "all engines", "standard", "2014-2018: group=48 (H6) std; group=94R (H7) with trailering/HD packages"),
        ((2014, 2018), "94R", "H7", None, "all engines", "with trailering / HD packages", "2014-2018: group=48 (H6) std; group=94R (H7) with trailering/HD packages"),
        ((2019, 2026), "94R", "H7", 2.7, "2.7L turbo", "AGM", "2019-2026: 2.7L/5.3L/6.2L group=94R (H7) AGM; 3.0L Duramax group=49 (H8) AGM; 4.3L (2019-21) group=48 (H6)"),
        ((2019, 2026), "94R", "H7", 5.3, "5.3L V8", "AGM", "2019-2026: 2.7L/5.3L/6.2L group=94R (H7) AGM; 3.0L Duramax group=49 (H8) AGM; 4.3L (2019-21) group=48 (H6)"),
        ((2019, 2026), "94R", "H7", 6.2, "6.2L V8", "AGM", "2019-2026: 2.7L/5.3L/6.2L group=94R (H7) AGM; 3.0L Duramax group=49 (H8) AGM; 4.3L (2019-21) group=48 (H6)"),
        ((2019, 2026), "49", "H8", 3.0, "3.0L Duramax diesel", "AGM", "2019-2026: 2.7L/5.3L/6.2L group=94R (H7) AGM; 3.0L Duramax group=49 (H8) AGM; 4.3L (2019-21) group=48 (H6)"),
        ((2019, 2021), "48", "H6", 4.3, "4.3L V6", None, "2019-2026: 2.7L/5.3L/6.2L group=94R (H7) AGM; 3.0L Duramax group=49 (H8) AGM; 4.3L (2019-21) group=48 (H6)"),
    ],
    "jeep/wrangler": [
        ((2005, 2006), "34/78", None, None, "all engines (TJ)", "dual-terminal", "2005-2006 TJ: group=34/78"),
        ((2007, 2010), "34/78", None, None, "3.8L (JK)", "dual-terminal", "2007-2011 JK: group=34/78 (2007-10), 78 (2011)"),
        ((2011, 2011), "78", None, None, "3.8L (JK)", None, "2007-2011 JK: group=34/78 (2007-10), 78 (2011)"),
        ((2012, 2018), "48", "H6", 3.6, "3.6L (JK)", None, "2012-2018 JK: group=48 (H6)"),
        ((2018, 2026), "94R", "H7", None, "JL", "build-dependent (eTorque/ESS adds an AUX14 auxiliary battery)", "2018-2026 JL: group=94R (H7) or 48 (H6), build-dependent. eTorque/ESS adds AUX14."),
        ((2018, 2026), "48", "H6", None, "JL", "build-dependent", "2018-2026 JL: group=94R (H7) or 48 (H6), build-dependent. eTorque/ESS adds AUX14."),
    ],
    "toyota/tacoma": [
        ((2005, 2014), "24F", None, None, "all engines", "standard", "2005-2014: group=24F std; 27F with tow package"),
        ((2005, 2014), "27F", None, None, "all engines", "with tow package", "2005-2014: group=24F std; 27F with tow package"),
        ((2015, 2015), "24F", None, None, "all engines", None, "2015: group=24F"),
        ((2016, 2023), "24F", None, None, "2.7L / 3.5L", None, "2016-2023: group=24F; group=35 alt on 3.5L V6"),
        ((2016, 2023), "35", None, 3.5, "3.5L V6", "alternate fitment", "2016-2023: group=24F; group=35 alt on 3.5L V6"),
        ((2024, 2026), "94R", "H7", None, "2.4L turbo", "per owner reports; unverified", "2024-2026: group=94R (H7) per owner reports (flag as unverified)"),
    ],
}

def norm(code):
    """autopadre code -> BCI group: 'H6 (48)' -> '48', 'H7 (94R)' -> '94R', '24F' -> '24F'."""
    m = re.match(r"^H\d \((\w+)\)$", code)
    return m.group(1) if m else code

def matches(group, ap):
    return ap == group or (group == "34/78" and ap in ("34", "78"))

summary = []
for slug, recs in DATA.items():
    path = ROOT / "data/manuals" / f"{slug}.yaml"
    data = yaml.safe_load(path.read_text())
    data["records"] = [r for r in data["records"] if not (r["field"] == "battery" and r.get("confidence") == "low")]
    rref, aref = "research_battery", "autopadre_battery"
    page = ROOT / "data/cache/web/autopadre" / f"{slug.replace('/', '-')}.html"
    data["sources"][rref] = dict(RESEARCH)
    data["sources"][aref] = {"doc": f"AutoPadre: {slug.split('/')[1].replace('-', ' ').title()} battery size",
                             "url": f"https://www.autopadre.com/battery-size/{slug.replace('/', '-')}",
                             "type": "third_party_reference", "accessed": "2026-10-14"}
    ap = {}
    for row in ap_rows(page):
        ap.setdefault(row["year"], []).append(row)
    for (y0, y1), group, din, displ, eng, cond, rquote in recs:
        rec = {"field": "battery", "years": [y0, y1]}
        if displ is not None:
            rec["displacement_l"] = displ
        rec["engine"] = eng
        if cond:
            rec["condition"] = cond
        rec["group"] = group
        if din:
            rec["din"] = din
        rec["confidence"] = "low"
        src = [{"ref": rref, "quote": rquote}]
        agree, differ, absent = [], [], []
        for y in range(y0, y1 + 1):
            rows_y = ap.get(y, [])
            hit = [r for r in rows_y if matches(group, norm(r["code"]))]
            if hit:
                agree.append(y); src.append({"ref": aref, "quote": hit[0]["quote"][:200]})
            elif rows_y:
                differ.append(f"{y}: {', '.join(sorted({norm(r['code']) for r in rows_y}))}")
            else:
                absent.append(y)
        notes = []
        if agree:
            notes.append(f"autopadre.com agrees for {', '.join(map(str, agree))}")
        if differ and not cond:  # alternates/options are expected to differ from autopadre's single row
            notes.append(f"autopadre.com lists other groups ({'; '.join(differ)})")
        rec["note"] = "; ".join(notes) or "no autopadre.com row for these years"
        rec["src"] = src
        data["records"].append(rec)
        summary.append((slug, y0, y1, group, cond or "", len(agree), differ if not cond else []))
    with open(path, "w") as fh:
        fh.write("# Generated by tools/manuals (see its README). Battery records with `confidence: low` are third-party only.\n")
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, width=120)
for s in summary:
    print(f"{s[0]:26s} {s[1]}-{s[2]} {s[3]:6s} {s[4][:30]:30s} autopadre agrees {s[5]} yrs" + (f"  DIFFERS {s[6]}" if s[6] else ""))
