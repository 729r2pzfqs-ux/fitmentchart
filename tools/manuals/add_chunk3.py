"""Gap-research chunk 3, verified: Civic tires, wipers, towing (battery: no verifiable source).

Sources:
- Honda owner's manuals (techinfo.honda.com), cached in data/cache/manuals/honda-civic/.
- Honda Info Center wheel/tire feature pages, 2018-2026 (hondainfocenter.com, Honda's dealer reference),
  cached as data/cache/web/hic_<year>_<body>.html.
- HondaPartsNow.com genuine-Honda parts catalog (wiper blades), 2006-2015 and 2022-2026. Quotes are the
  catalog's own part titles. Read in the browser pane because the site returns 403 to curl.
Run after add_chunk2.py.
"""
import html, re, subprocess, sys
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import cite, DOCS
HC = ROOT / "data/cache/manuals/honda-civic"
civic = yaml.safe_load((ROOT / "data/manuals/honda/civic.yaml").read_text())
for ref, src in civic["sources"].items():
    if src["type"] == "oem_manual" and (HC / f"{ref}.pdf").exists():
        DOCS[ref] = {"pdf": str(HC / f"{ref}.pdf"), **src}
TI = "https://techinfo.honda.com/rjanisis/pubs/"
EXTRA = {"NA0707": (2007, "2007 Civic Coupe Owner's Manual (Honda)", TI + "OM/NA0707/NA0707OM.pdf")}
for code in ("NC0606", "NC0707", "NC0808", "NC0909", "NC1010", "NC1111", "NA0606", "NA0808", "NA0909", "NA1010", "NA1111",
             "R01212", "R0144D"):
    assert code in DOCS, code
for code, (y, doc, url) in EXTRA.items():
    if code not in DOCS:
        DOCS[code] = {"pdf": str(HC / f"{code}.pdf"), "doc": doc, "url": url, "type": "oem_manual", "accessed": "2026-10-13"}
def reg(ref):
    civic["sources"][ref] = {k: v for k, v in DOCS[ref].items() if k != "pdf"}

# drop records this script owns (idempotent)
OWN_WIPER_YEARS = set(range(2006, 2016)) | set(range(2022, 2027))
civic["records"] = [r for r in civic["records"] if not (
    (r["field"] == "tires" and r["years"][0] >= 2006) or
    (r["field"] == "towing" and r["years"][0] >= 2006) or
    (r["field"] == "wipers" and r["years"][0] in OWN_WIPER_YEARS))]
R = []
def page_of(code, *pats):
    txt = open(HC / f"{code}.raw.txt", errors="replace").read().split("\f")
    for i, p in enumerate(txt, 1):
        f = re.sub(r"\s+", " ", p)
        if all(re.search(x, f) for x in pats):
            return i
    raise SystemExit(f"{code}: no page with {pats}")
def tire(y, size, ls, trim, src, note=None):
    r = {"field": "tires", "years": [y, y], "trim": trim, "size": size}
    if ls: r["load_speed"] = ls
    if note: r["note"] = note
    r["src"] = src; R.append(r)

# ---------------- tires: manuals 2006-2014
for code in ("NA0606", "NA0707", "NA0808", "NA0909", "NA1010", "NA1111"):
    reg(code); y = int("20" + code[2:4])
    body = "Coupe" if code in ("NA0606", "NA0707") else "Sedan"
    pg = page_of(code, r"Recommended Tire Pressures", r"Tire Size")
    t = re.sub(r"\s+", " ", open(HC / f"{code}.raw.txt", errors="replace").read().split("\f")[pg - 1])
    found = re.findall(r"\(?([A-Z][A-Za-z ,.\-]{1,60}?)\)?\s*Tire Size\s*(?:Cold Tire Pressure\s*)?(?:Front/Rear\s*)?((?:P)?\d{3}/\d{2}Z?R\d{2}) (\d{2,3}[A-Z])", t)
    for trim, size, ls in found:
        trim = trim.split(". ")[-1].strip()
        if trim in ("Cold Tire Pressure",):
            continue
        tire(y, size, ls, f"{body} {trim}", [cite(code, pg, re.escape(trim) + r"\)?\s*Tire Size.{0,40}?" + re.escape(size), [size])])
    if code == "NA0707":
        p2 = page_of(code, r"Si model only P215/45R17 87V")
        tire(y, "P215/45R17", "87V", "Coupe Si", [cite(code, p2, r"Si model only P215/45R17 87V", ["P215/45R17"])])
for code in ("NC0606", "NC0707", "NC0808", "NC0909", "NC1010", "NC1111"):
    reg(code); y = int("20" + code[2:4])
    pg = page_of(code, r"Tire Size P195/65R15 89S")
    tire(y, "P195/65R15", "89S", "Hybrid", [cite(code, pg, r"Tire Size P195/65R15 89S", ["P195/65R15"])])
reg("R01212"); reg("R0144D")
p12 = page_of("R01212", r"■ ?Tire", r"P195/65R15 89H\*1")
for size, ls, mark, trim in (("P195/65R15", "89H", "*1", "DX and LX models"), ("P195/65R15", "89S", "*2", "HF model"),
                             ("P205/55R16", "89H", "*3", "EX and EX-L models")):
    tire(2012, size, ls, trim, [cite("R01212", p12, re.escape(f"{size} {ls}{mark}"), [size]),
                                cite("R01212", p12, re.escape(f"{mark}: {trim}"))])
p12s = page_of("R01212", r"2\.4 ℓ engine models", r"P215/45R17 87V")
tire(2012, "P215/45R17", "87V", "2.4 L engine models (Si)", [cite("R01212", p12s, r"Tire Size P215/45R17 87V", ["P215/45R17"])])
p14 = page_of("R0144D", r"■ ?Tire", r"P195/65R15 89H\*1")
for size, ls, mark, trim in (("P195/65R15", "89H", "*1, *2", "Canadian DX model / LX model"), ("P195/65R15", "89S", "*3", "HF model"),
                             ("P205/55R16", "89H", "*4", "EX model"), ("P215/45R17", "87V", "*5", "U.S. EX-L and Canadian Touring models")):
    tire(2014, size, ls, trim, [cite("R0144D", p14, re.escape(f"{size} {ls}{mark}"), [size])])
p14s = page_of("R0144D", r"Optional for U\.S\. Si", r"225/40R18 92V")
tire(2014, "225/40R18", "92V", "Si (18-inch)", [cite("R0144D", p14s, r"Tire Size 225/40R18 92V 225/40R18 92Y\*1", ["225/40R18"]),
                                               cite("R0144D", p14s, r"\*1: Optional for U\.S\. Si")],
     note="225/40R18 92Y optional for U.S. Si")

# ---------------- tires: Honda Info Center 2018-2026
WEB = ROOT / "data/cache/web"
for f in sorted(WEB.glob("hic_20*_Civic-*.html")):
    y, body = int(f.name[4:8]), f.name[9:-5]
    ref = f"hic{y}{body.replace('-', '')}"
    url = f"https://www.hondainfocenter.com/{y}/{body}/Feature-Guide/Exterior-Features/Wheels-and-Tires"
    civic["sources"][ref] = {"doc": f"Honda Info Center: {y} {body.replace('-', ' ')} Wheels and Tires", "url": url,
                             "type": "oem_spec_sheet", "accessed": "2026-10-14"}
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", f.read_text(errors="replace"), flags=re.S)
    x = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    seen = set()
    for m in re.finditer(r"[^.]*?(\d{3}/\d{2}) ?(Z?R) ?(\d{2})[^.]*\.", x):
        sent = m.group(0).strip()
        size = f"{m.group(1)}{m.group(2)}{m.group(3)}"
        subj = re.search(r"(?:The )?(Civic [^,;]*?|Type R[^,;]*?|Si [^,;]*?)(?= (?:is|are|wear|wears|comes|roll|make|flashes|shows|tops|dazzles|models|Coupes|trim))", sent)
        trim = (subj.group(1) if subj else body.replace("-", " ")).strip()
        bw = body.split("-")[1] if "-" in body else ""
        if bw in ("Sedan", "Coupe", "Hatchback") and bw not in trim:
            trim = f"{trim} ({bw})"
        if (trim, size) in seen:
            continue
        seen.add((trim, size))
        tire(y, size, None, trim, [{"ref": ref, "quote": sent[:200]}])

# ---------------- wipers: HondaPartsNow genuine parts catalog (part titles as printed)
HPN = "https://www.hondapartsnow.com/oem-{y}-honda-civic-wiper_blade.html"
WIP = {}
for y in (2006, 2007):
    WIP[y] = (("Blade, Windshield Wiper (650MM) (Driver Side)", "76620-SNE-A01", 650), ("Blade, Windshield Wiper (575MM) (Passenger Side)", "76630-SNE-A01", 575),
              ("Blade, Windshield Wiper (700MM) (Driver Side)", "76620-SVA-A03", 700), ("Blade, Windshield Wiper (625MM) (Passenger Side)", "76630-SVA-A04", 625), None)
for y in range(2008, 2012):
    WIP[y] = (("Blade, Windshield Wiper (650Mm)", "76620-SNA-A12", 650), ("Blade, Windshield Wiper (575MM) (Passenger Side)", "76630-SNA-A11", 575),
              ("Blade, Windshield Wiper (700MM) (Driver Side)", "76620-SVA-A03", 700), ("Blade, Windshield Wiper (625MM) (Passenger Side)", "76630-SVA-A04", 625), None)
for y in range(2012, 2016):
    WIP[y] = (("Blade, Windshield Wiper (650Mm)", "76620-TR0-A02", 650), ("Blade, Windshield Wiper (575Mm)", "76630-TR0-A02", 575),
              ("Blade, Windshield Wiper (700Mm)", "76620-TR0-G12", 700), ("Blade, Windshield Wiper (600Mm)", "76630-TS8-A02", 600), None)
for y in range(2022, 2027):
    WIP[y] = (("BLADE, WSW (600MM)", "76620-T20-A01", 600), ("BLADE, WSW (475MM)", "76630-T20-A01", 475), None, None,
              ("BLADE, WSW (300MM)", "76730-T43-003", 300))
inch = lambda mm: round(mm / 25.4, 1)
for y, (d, p, cd, cp, rear) in WIP.items():
    ref = f"hpn{y}"
    civic["sources"][ref] = {"doc": f"HondaPartsNow (genuine Honda parts catalog): {y} Honda Civic Wiper Blade",
                             "url": HPN.format(y=y), "type": "oem_parts_catalog", "accessed": "2026-10-14"}
    q = lambda part: {"ref": ref, "quote": f"{y} Honda Civic {part[0]} Part Number: {part[1]}"}
    rec = {"field": "wipers", "years": [y, y], "driver_in": inch(d[2]), "passenger_in": inch(p[2])}
    src = [q(d), q(p)]
    if rear:
        rec["rear_in"] = inch(rear[2]); src.append(q(rear))
    if y >= 2022:
        rec["note"] = ("4-door/5-door front blades 600/475 mm; rear 300 mm on 5-door. Positions follow Honda's "
                       "part families (76620 driver, 76630 passenger, 76730 rear); the catalog lists no position for these.")
    else:
        rec["body"] = "4-door"
        rec["note"] = f"4-door blades {d[2]}/{p[2]} mm; 2-door: driver {cd[2]} mm, passenger {cp[2]} mm" + \
                      ("; 4-door Hybrid listed with the 700 mm driver blade" if y >= 2013 else "")
        src += [q(cd), q(cp)]
    rec["src"] = src
    R.append(rec)

# ---------------- towing: manuals
def tow(y, mx, trim, code, pat, note=None):
    r = {"field": "towing", "years": [y, y], "trim": trim, "max_lb": mx}
    if note: r["note"] = note
    r["src"] = [cite(code, page_of(code, pat), pat, ["1,000"] if mx else [])]
    R.append(r)
NOTOW = r"not designed to tow a trailer"
tow(2006, 0, "Coupe", "NA0606", NOTOW, "not designed to tow a trailer")
tow(2007, 0, "Coupe", "NA0707", NOTOW, "not designed to tow a trailer")
for code in ("NA0808", "NA0909", "NA1010", "NA1111"):
    tow(int("20" + code[2:4]), 1000, "Sedan", code, r"must not exceed 1,000 lbs \(450 kg\)", "total trailer weight")
for code in ("NC0606", "NC0707", "NC0808", "NC0909", "NC1010", "NC1111"):
    tow(int("20" + code[2:4]), 0, "Hybrid", code, NOTOW, "not designed to tow a trailer")
for code, y in (("R01212", 2012), ("R0144D", 2014)):
    tow(y, 1000, "Sedan except HF", code, r"must not exceed 1,000 lbs \(450 kg\)", "total trailer weight")
    tow(y, 0, "HF", code, r"HF model Your vehicle is not designed to tow a trailer", "not designed to tow a trailer")
for ref, src in list(civic["sources"].items()):
    if ref.startswith("AT") and (HC / f"{ref}.pdf").exists():
        y = int(ref[-2:]) + 2000 if not ref.startswith(("AT20", "AT40")) else 2022
        body = src["doc"].split(" Owner")[0].replace(f"{y} Civic ", "")
        tow(y, 0, body, ref, NOTOW, "not designed to tow a trailer")

civic["records"].extend(R)
with open(ROOT / "data/manuals/honda/civic.yaml", "w") as fh:
    fh.write("# Generated from Honda owner's manuals (quotes verified against the cited PDF page), Honda Info Center pages,\n"
             "# the HondaPartsNow genuine-parts catalog and Rain-X wiper pages.\n")
    yaml.safe_dump(civic, fh, sort_keys=False, allow_unicode=True, width=120)
from collections import Counter
print(Counter(r["field"] for r in R))
