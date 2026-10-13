"""Step 02: engines per model-year from fueleconomy.gov (EPA).

Sources
  * https://fueleconomy.gov/feg/epadata/vehicles.csv.zip
      one row per EPA-certified configuration: displacement, cylinders, turbo /
      supercharger, fuel, hybrid/EV type, transmission, drive, MPG.
  * EPA "Data on Cars Used for Testing Fuel Economy" (one file per model year),
      https://www.epa.gov/compliance-and-fuel-economy-data/data-cars-used-testing-fuel-economy
      vehicles.csv has no horsepower; the test-car lists carry "Rated
      Horsepower" for every tested configuration, so HP is joined from there.

Engine grouping: rows that share displacement, cylinder count, forced
induction, fuel family and electrification are one engine. MPG becomes a
[min, max] range across that engine's drive/transmission configurations.

HP join: for each vehicles.csv row, candidate test cars are the same model year,
make, model (makes.yaml `testcar` rule), displacement (+-0.06 L), cylinders and
fuel family. The test car whose city/highway test results equal the row's
unadjusted MPG is the configuration that was tested (see match_hp). When no
test matches (analytically derived configs), the closest model name is used and
`hp_match` says "name". An engine keeps every distinct HP rating its trims carry
(e.g. Civic 1.5T: 174 / 180 / 205 hp). For hybrids EPA rates the engine alone,
not combined system output.

Writes data/sources/fueleconomy/<make>/<model>.json
"""
from __future__ import annotations

import csv
import io
import re
import zipfile
from collections import defaultdict

from common import (CACHE_DIR, download, has_flag, iter_models, load_config, log,
                    matches, read_json, session, source_path, write_json, year_range)

VEHICLES_URL = "https://fueleconomy.gov/feg/epadata/vehicles.csv.zip"
TESTCAR_PAGE = "https://www.epa.gov/compliance-and-fuel-economy-data/data-cars-used-testing-fuel-economy"

# FFV is deliberately *not* generic: Ford names its flex-fuel test cars "F-150 FFV",
# which separates the 3.5 Ti-VCT (FFV) from the 3.5 EcoBoost (not FFV).
GENERIC_TOKENS = {
    "2WD", "4WD", "AWD", "FWD", "RWD", "4X4", "4X2", "PICKUP", "TRUCK", "CAB",
    "CHASSIS", "THE", "WITH", "AND", "LBS", "GVWR", "MODE", "SPORT", "TIRES",
    "TOYOTA", "FORD", "HONDA", "CHEVROLET", "CHEVY", "JEEP", "GMC",
}
ELECTRIFIED_RE = re.compile(r"HYBRID|\bHEV\b|\bPHEV\b|4XE|PLUG|\bBEV\b|\bEV\b", re.I)


# --------------------------------------------------------------------------- EPA vehicles.csv

def load_vehicles(refresh: bool) -> list[dict]:
    z = download(VEHICLES_URL, "vehicles.csv.zip", refresh=refresh, min_bytes=500_000)
    with zipfile.ZipFile(z) as zf:
        name = next(n for n in zf.namelist() if n.lower().endswith("vehicles.csv"))
        text = zf.read(name).decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))


def fnum(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f


def electrification(row: dict) -> str | None:
    atv = (row.get("atvType") or "").strip().lower()
    if atv == "hybrid":
        return "hybrid"
    if atv == "plug-in hybrid":
        return "phev"
    if atv == "ev":
        return "ev"
    return None


def fuel_family(row: dict) -> str:
    ft = (row.get("fuelType1") or row.get("fuelType") or "").lower()
    if "diesel" in ft:
        return "diesel"
    if "natural gas" in ft or "cng" in ft:
        return "cng"
    if "electric" in ft:
        return "electric"
    return "gasoline"


def aspiration(row: dict) -> str:
    if (row.get("tCharger") or "").strip() in ("T", "TRUE", "1"):
        return "turbo"
    if (row.get("sCharger") or "").strip() in ("S", "SC", "TRUE", "1"):
        return "supercharged"
    return "na"


# --------------------------------------------------------------------------- EPA test-car lists (HP)

def testcar_links(refresh: bool) -> dict[int, list[str]]:
    cache = CACHE_DIR / "testcar_links.json"
    if cache.exists() and not refresh:
        return {int(k): v for k, v in read_json(cache).items()}
    html = session().get(TESTCAR_PAGE, timeout=60,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; fitmentchart-pipeline)"}).text
    links: dict[int, list[str]] = defaultdict(list)
    for href in re.findall(r'href="([^"]+\.(?:csv|xlsx))"', html, re.I):
        fname = href.rsplit("/", 1)[-1].lower()
        m = re.match(r"(\d{2})-?t(?:e)?stcar", fname)
        if not m:
            continue
        yy = int(m.group(1))
        year = 2000 + yy if yy < 90 else 1900 + yy
        url = href if href.startswith("http") else "https://www.epa.gov" + href
        if url not in links[year]:
            links[year].append(url)
    if not links:
        raise SystemExit("could not find any test-car files on the EPA page; layout changed?")
    write_json(cache, links)
    return dict(links)


def _norm(h) -> str:
    return re.sub(r"\s+", " ", str(h or "")).strip().lower()


TC_FIELDS = {
    "year": "model year",
    "make": "represented test veh make",
    "model": "represented test veh model",
    "displ": "test veh displacement (l)",
    "hp": "rated horsepower",
    "cyl": "# of cylinders and rotors",
    "fuel": "test fuel type description",
    "proc": "test procedure cd",
    "fe": "rnd_adj_fe",
}

# 2005-2009 files use EPA's older database column names: no make column (only the
# manufacturer), carline instead of model, displacement in cubic inches, and a
# fuel *code*. Manufacturer -> make is only needed for our makes; the carline
# regex in makes.yaml then separates e.g. Silverado from Sierra under GM.
OLD_FIELDS = {"year": "mdlyr_dt", "mfr": "vi_mfr_nm", "model": "cl_nm",
              "cid": "gbe_cid_msr", "hp": "vc_rtd_hp_msr", "cyl": "vc_cyl_cnt",
              "fuel_cd": "veh_fl_typ_cd", "proc": "tst_prc_cd", "fe": "gt_rnd_adj_qty"}
OLD_MFR_MAKE = {"TOYOTA": "TOYOTA", "FORD MOTOR COMPANY": "FORD", "HONDA": "HONDA",
                "GENERAL MOTORS": "CHEVROLET", "CHRYSLER LLC": "JEEP",
                "DAIMLERCHRYSLER": "JEEP", "DAIMLERCHRYSLER CORPORATION": "JEEP"}
# Fuel codes, from the newer files' code/description pairs:
# 19 "Federal Cert Diesel 7-15 PPM Sulfur", 41 "CNG", 62 "Electricity"
OLD_FUEL_CODES = {"19": "diesel", "41": "cng", "62": "electric"}
CID_TO_L = 0.016387064
# Test procedure codes (same in both formats). Cold-CO (11) and US06/SC03 are
# not the city/highway label tests, so they are ignored for MPG matching.
FTP_CODES = {"2", "21", "25", "31", "35"}
HWY_CODES = {"3"}
FE_TOLERANCE = 0.006  # test results are rounded to 0.1 mpg; tested configs match within that


def _normalise_testcar(r: dict) -> dict | None:
    """Map a raw row from either file format to {make, model, displ, cyl, hp, fuel_family, cat, fe}."""
    if "mdlyr_dt" in r:
        g = {k: r.get(v) for k, v in OLD_FIELDS.items()}
        make = OLD_MFR_MAKE.get(str(g["mfr"] or "").strip().upper())
        cid = fnum(g["cid"])
        displ = cid * CID_TO_L if cid else None
        family = OLD_FUEL_CODES.get(str(g["fuel_cd"] or "").strip(), "gasoline")
    else:
        g = {k: r.get(v) for k, v in TC_FIELDS.items()}
        make = str(g["make"] or "").strip().upper()
        displ = fnum(g["displ"])
        desc = str(g["fuel"] or "").lower()
        family = ("diesel" if "diesel" in desc else "cng" if "cng" in desc or "natural gas" in desc
                  else "electric" if "electric" in desc else "gasoline")
    hp, cyl = fnum(g["hp"]), fnum(g["cyl"])
    if not make or not hp or not displ:
        return None
    proc = str(g["proc"] or "").strip()
    if proc.endswith(".0"):
        proc = proc[:-2]
    cat = "city" if proc in FTP_CODES else "hwy" if proc in HWY_CODES else None
    fe = fnum(g["fe"])
    return {"make": make, "model": str(g["model"] or "").strip().upper(),
            "displ": round(displ, 3), "cyl": int(cyl) if cyl else None,
            "hp": int(round(hp)), "fuel_family": family,
            "cat": cat, "fe": round(fe, 2) if (cat and fe) else None}


def _rows_from_file(path) -> list[dict]:
    if path.suffix.lower() == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.worksheets[0]
        it = ws.iter_rows(values_only=True)
        header = None
        for row in it:
            if row and any(_norm(c) == "model year" for c in row):
                header = [_norm(c) for c in row]
                break
        if header is None:
            raise RuntimeError(f"no header row in {path}")
        rows = [dict(zip(header, r)) for r in it]
        wb.close()
        return rows
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    rdr = csv.reader(io.StringIO(text))
    header = [_norm(c) for c in next(rdr)]
    return [dict(zip(header, r)) for r in rdr]


def load_testcars(years: list[int], makes: set[str], refresh: bool) -> dict[int, list[dict]]:
    """Return {year: [ {make, model, displ, cyl, hp, fuel_family, cat, fe} ]} for our makes."""
    links = testcar_links(refresh)
    out: dict[int, list[dict]] = {}
    for y in years:
        cache = CACHE_DIR / "testcar" / f"{y}.json"
        if cache.exists() and not refresh:
            out[y] = read_json(cache)
            continue
        recs = []
        for url in links.get(y, []):
            fname = url.rsplit("/", 1)[-1]
            path = download(url, f"testcar/{fname}", refresh=refresh, min_bytes=10_000)
            for r in _rows_from_file(path):
                rec = _normalise_testcar(r)
                if rec and rec["make"] in makes:
                    rec["file"] = fname
                    recs.append(rec)
        # de-duplicate (each config appears once per test procedure)
        seen, uniq = set(), []
        for r in recs:
            k = (r["make"], r["model"], r["displ"], r["cyl"], r["hp"], r["fuel_family"], r["cat"], r["fe"])
            if k not in seen:
                seen.add(k)
                uniq.append(r)
        out[y] = uniq
        write_json(cache, uniq)
        log(f"  test cars {y}: {len(uniq)} rows for our makes from {len(links.get(y, []))} file(s)")
    return out


def tokens(name: str) -> set[str]:
    # "F-150" and "F150" must tokenise the same
    name = re.sub(r"(?<=[A-Z])-(?=\d)", "", name.upper())
    return {t for t in re.findall(r"[A-Z0-9]+", name)
            if t not in GENERIC_TOKENS and not re.fullmatch(r"\d", t)}


def match_hp(row: dict, candidates: list[dict]) -> tuple[list[int], list[str], str | None]:
    """Return (hp values, matched test-car model names, method) for one vehicles.csv row.

    1. "fe": the test car whose city (FTP) and highway test results equal this
       row's unadjusted city/highway MPG (UCity/UHighway). A tested
       configuration's label values are computed from exactly those tests, so this
       pins the configuration even when two engines share a displacement (Civic
       2.0 vs 2.0 turbo, F-150 3.5 vs 3.5 EcoBoost, hybrid vs non-hybrid).
       Test rows are grouped per test car (model + HP); a car matching on both
       city and highway beats one matching on a single test, then the smallest
       deviation wins.
    2. "name": otherwise, test cars with the closest model name, requiring the
       hybrid/EV keyword to agree with the EPA row's electrification.
    """
    displ = fnum(row["displ"])
    cyl = int(fnum(row["cylinders"]) or 0) or None
    family = fuel_family(row)
    pool = [c for c in candidates
            if abs(c["displ"] - displ) <= 0.06
            and not (cyl and c["cyl"] and c["cyl"] != cyl)
            and c["fuel_family"] == family]
    if not pool:
        return [], [], None

    target = {"city": fnum(row.get("UCity")), "hwy": fnum(row.get("UHighway"))}
    cars: dict[tuple, dict] = defaultdict(lambda: {"city": [], "hwy": []})
    for c in pool:
        if c["cat"] and c["fe"]:
            cars[(c["model"], c["hp"])][c["cat"]].append(c["fe"])
    ranked = []
    for (model_name, hp), fes in cars.items():
        diffs = []
        for cat in ("city", "hwy"):
            t = target[cat]
            if t and fes[cat]:
                diffs.append(min(abs(f - t) / t for f in fes[cat]))
        if diffs and max(diffs) <= FE_TOLERANCE:
            ranked.append((-len(diffs), max(diffs), model_name, hp))
    if ranked:
        ranked.sort()
        best_n, best_d = ranked[0][0], ranked[0][1]
        win = [r for r in ranked if r[0] == best_n and r[1] <= best_d + 0.002]
        return sorted({r[3] for r in win}), sorted({r[2] for r in win}), "fe"

    elec = electrification(row) is not None
    pool = [c for c in pool if bool(ELECTRIFIED_RE.search(c["model"])) == elec]
    if not pool:
        return [], [], None
    et = tokens(row["model"])

    def score(c):
        ct = tokens(c["model"])
        return len(et & ct) - 0.5 * len(ct - et)

    best = max(score(c) for c in pool)
    winners = [c for c in pool if score(c) == best]
    return sorted({c["hp"] for c in winners}), sorted({c["model"] for c in winners}), "name"


# --------------------------------------------------------------------------- main

def engine_label(e: dict) -> str:
    parts = []
    if e["displacement_l"]:
        parts.append(f"{e['displacement_l']:.1f}L")
    if e["cylinders"]:
        parts.append(f"{e['cylinders']}-cyl")
    if e["aspiration"] == "turbo":
        parts.append("turbo")
    elif e["aspiration"] == "supercharged":
        parts.append("supercharged")
    if e["fuel_family"] == "diesel":
        parts.append("diesel")
    elif e["fuel_family"] == "cng":
        parts.append("CNG")
    if e["electrification"] == "hybrid":
        parts.append("hybrid")
    elif e["electrification"] == "phev":
        parts.append("plug-in hybrid")
    elif e["electrification"] == "ev":
        parts = ["Electric"]
    return " ".join(parts)


def reject_hp_outliers(out_years: dict) -> list[str]:
    """Drop HP that contradicts both neighbouring years of the same engine.

    The EPA test-car files are manufacturer-submitted and occasionally wrong:
    2018 F-150 2.7L EcoBoost is listed at "400" rated HP, which is its torque
    (lb-ft). HP is 325 in 2017 and 2019. When year N's HP values all differ by
    more than 10% from identical HP lists in N-1 and N+1, they move to
    `hp_rejected`. Nothing is substituted, so the year shows no HP and QA
    reports it.
    """
    notes = []
    by_label: dict[str, dict[int, dict]] = defaultdict(dict)
    for y, blk in out_years.items():
        for e in blk["engines"]:
            by_label[e["label"]][int(y)] = e
    for label, ys in by_label.items():
        for y, e in ys.items():
            prev, nxt = ys.get(y - 1), ys.get(y + 1)
            if not (e["hp"] and prev and nxt and prev["hp"] and prev["hp"] == nxt["hp"]):
                continue
            ref = prev["hp"]
            if all(min(abs(h - r) / r for r in ref) > 0.10 for h in e["hp"]):
                e["hp_rejected"] = {"values": e["hp"],
                                    "reason": f"contradicts {y - 1} and {y + 1} ({ref})"}
                e["hp"], e["hp_match"] = [], None
                notes.append(f"{y} {label}: rejected HP {e['hp_rejected']['values']} (neighbours {ref})")
    return notes


def rng(vals):
    vals = [v for v in vals if v is not None]
    return [min(vals), max(vals)] if vals else None


def main() -> None:
    refresh = has_flag("--refresh")
    cfg = load_config()
    years = year_range(cfg)
    log("loading EPA vehicles.csv ...")
    vehicles = load_vehicles(refresh)
    log(f"  {len(vehicles)} rows")
    makes_upper = {m["epa_make"].upper() for m in cfg["makes"]}
    log("loading EPA test-car lists (rated HP) ...")
    testcars = load_testcars(years, makes_upper, refresh)

    for make, model, slug in iter_models(cfg):
        skel = read_json(source_path("vpic", slug))
        rows_by_year: dict[str, list[dict]] = defaultdict(list)
        for r in vehicles:
            if r["make"] != make["epa_make"]:
                continue
            if not matches(model["epa"], r["model"]):
                continue
            y = r["year"]
            if int(y) in years:
                rows_by_year[y].append(r)

        out_years = {}
        hp_hits = hp_total = 0
        for y in sorted(rows_by_year):
            tc = [c for c in testcars.get(int(y), [])
                  if c["make"] == make["epa_make"].upper() and matches(model["testcar"], c["model"])]
            groups: dict[tuple, dict] = {}
            for r in rows_by_year[y]:
                displ = fnum(r["displ"])
                cyl = int(fnum(r["cylinders"]) or 0)
                key = (displ, cyl, aspiration(r), fuel_family(r), electrification(r))
                g = groups.setdefault(key, {"rows": [], "hp_fe": set(), "hp_name": set(),
                                            "tc_models": set()})
                g["rows"].append(r)
                if displ:
                    hp, tcm, method = match_hp(r, tc)
                    if method:
                        g[f"hp_{method}"].update(hp)
                        g["tc_models"].update(tcm)
                        g.setdefault("methods", set()).add(method)

            engines = []
            for (displ, cyl, asp, ff, elec), g in groups.items():
                rows = g["rows"]
                fuels = sorted({r["fuelType1"] for r in rows if r.get("fuelType1")})
                e = {
                    "displacement_l": displ,
                    "cylinders": cyl or None,
                    "aspiration": asp,
                    "fuel_family": ff,
                    "fuel": fuels,
                    "flex_fuel": any("E85" in (r.get("fuelType") or "") for r in rows),
                    "electrification": elec,
                    # union over this engine's configurations; each config's HP came
                    # from its own FE match or, failing that, its model name
                    "hp": sorted(g["hp_fe"] | g["hp_name"]),
                    "hp_match": ("mixed" if len(g.get("methods", ())) > 1
                                 else next(iter(g["methods"])) if g.get("methods") else None),
                    "mpg": {
                        "city": rng([fnum(r["city08"]) for r in rows]),
                        "hwy": rng([fnum(r["highway08"]) for r in rows]),
                        "combined": rng([fnum(r["comb08"]) for r in rows]),
                    },
                    "drives": sorted({r["drive"] for r in rows if r.get("drive")}),
                    "transmissions": sorted({r["trany"] for r in rows if r.get("trany")}),
                    "epa_models": sorted({r["model"] for r in rows}),
                    "epa_ids": sorted(int(r["id"]) for r in rows),
                    "hp_source_models": sorted(g["tc_models"]),
                }
                for k in ("city", "hwy", "combined"):
                    if e["mpg"][k]:
                        e["mpg"][k] = [int(v) for v in e["mpg"][k]]
                e["label"] = engine_label(e)
                engines.append(e)
                hp_total += 1
                hp_hits += bool(e["hp"])
            engines.sort(key=lambda e: (e["electrification"] is not None, e["displacement_l"] or 99,
                                        e["aspiration"], e["fuel_family"]))
            out_years[y] = {"engines": engines}

        for note in reject_hp_outliers(out_years):
            log(f"  {slug}: {note}")
            hp_hits -= 1

        skel_years = set(skel["years"])
        epa_only = sorted(set(out_years) - skel_years)
        write_json(source_path("fueleconomy", slug), {
            "slug": slug,
            "source": {"vehicles_csv": VEHICLES_URL, "hp": TESTCAR_PAGE},
            "years": out_years,
        })
        log(f"{slug:28s} years={len(out_years):2d}/{len(skel_years)} engines={hp_total:3d} "
            f"with_hp={hp_hits}" + (f" (EPA-only years: {epa_only})" if epa_only else ""))


if __name__ == "__main__":
    main()
