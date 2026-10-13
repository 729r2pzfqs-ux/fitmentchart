import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import DOCS, cite, dump

D = str(ROOT / "data/cache/manuals/toyota-tacoma/") + "/"
MAN = {2008: "OM35892U", 2009: "OM35883U", 2010: "OM35A20U", 2011: "OM35A34U", 2012: "OM35A48U",
       2014: "OM35A38U", 2015: "OM04009U", 2016: "OM04005U", 2017: "OM04013U", 2018: "OM04017U",
       2019: "OM04021U", 2020: "OM04025U", 2021: "OM04029U", 2022: "OM04037U", 2023: "OM04047U",
       2024: "OM04041U", 2025: "OM04011U"}
HYB = {2024: "OM04042U", 2025: "OM04012U"}
for y, c in list(MAN.items()) + [(y, c) for y, c in HYB.items()]:
    hyb = c in HYB.values()
    DOCS[c] = {"pdf": D + c + ".pdf",
               "doc": f"{y} Toyota Tacoma{' Hybrid' if hyb else ''} Owner's Manual ({c})",
               "url": f"https://www.toyota.ca/content/dam/toyota/documents/manuals/en/{c}/{c}.pdf",
               "type": "oem_manual", "accessed": "2026-10-13"}

R = []
def oil(y, d, eng, grade, alt, qt, l, src, cond=None):
    r = {"field": "oil", "years": [y, y], "displacement_l": d, "engine": eng}
    if cond: r["condition"] = cond
    r.update({"grade": grade})
    if alt: r["alt_grades"] = alt
    r.update({"capacity_qt": qt, "capacity_l": l, "src": src})
    R.append(r)

M = "[−-]"  # these manuals print a unicode minus in grades
# ---- oil 2008-2015: 2TR-FE 2.7 L and 1GR-FE 4.0 L V6 (capacity differs 2WD vs 4WD/PreRunner)
c = MAN[2008]
v27 = cite(c, 385, rf"2\.7 L 4{M}cylinder \(2TR{M}FE\) engine.{{0,3}}SAE 5W{M}20 or 0W{M}20")
v40 = cite(c, 385, rf"4\.0 L V6 \(1GR{M}FE\) engine.{{0,3}}SAE 5W{M}30")
oil(2008, 2.7, "2.7 L 4-cylinder (2TR-FE)", "5W-20", ["0W-20"], 6.1, 5.8,
    [cite(c, 420, r"With filter 5\.8 \(6\.1, 5\.1\)", ["6.1"]), v27])
oil(2008, 4.0, "4.0 L V6 (1GR-FE)", "5W-30", None, 4.8, 4.5,
    [cite(c, 420, r"Two.wheel drive models except Pre.?Runner With filter (Without filter )?4\.5 \(4\.8, 4\.0\)", ["4.8"]), v40],
    "2WD except PreRunner")
oil(2008, 4.0, "4.0 L V6 (1GR-FE)", "5W-30", None, 5.5, 5.2,
    [cite(c, 420, r"PreRunner.{0,80}?5\.2 \(5\.5, 4\.6\)", ["5.5"]), v40], "4WD and PreRunner")

def old_oil(y, cap27_pg, cap40_pg, v27, v40, g27="0W-20", alt27=None):
    c = MAN[y]
    oil(y, 2.7, "2.7 L 4-cylinder (2TR-FE)", g27, alt27, 6.1, 5.8,
        [cite(c, cap27_pg, r"6\.1 qt\. \(5\.8 L, 5\.1 Imp\.qt\.\)", ["6.1"]), v27])
    oil(y, 4.0, "4.0 L V6 (1GR-FE)", "5W-30", None, 4.8, 4.5,
        [cite(c, cap40_pg, r"2WD models except.{0,40}?4\.8 qt\. \(4\.5 L, 4\.0 Imp\.qt\.\)", ["4.8"]), v40],
        "2WD except PreRunner")
    oil(y, 4.0, "4.0 L V6 (1GR-FE)", "5W-30", None, 5.5, 5.2,
        [cite(c, cap40_pg, r"4WD models and.{0,40}?5\.5 qt\. \(5\.2 L, 4\.6 Imp\.qt\.\)", ["5.5"]), v40],
        "4WD and PreRunner")

c = MAN[2009]
old_oil(2009, 472, 473, cite(c, 364, r"2TR-FE\) engine SAE 5W-20 or 0W-20"), cite(c, 364, r"1GR-FE\) engine SAE 5W-30"),
        "5W-20", ["0W-20"])
c = MAN[2010]
old_oil(2010, 478, 479, cite(c, 478, r"Recommended viscosity: SAE 5W-20 or 0W-20"), cite(c, 480, r"Recommended viscosity: SAE 5W-30"),
        "5W-20", ["0W-20"])
c = MAN[2011]
old_oil(2011, 494, 495, cite(c, 494, r"Recommended viscosity: SAE 0W-20"), cite(c, 496, r"Recommended viscosity: SAE 5W-30"))
for y, cp, p27, p40 in ((2012, 558, 559, 560), (2014, 536, 537, 538), (2015, 526, 527, 528)):
    c = MAN[y]
    old_oil(y, cp, cp, cite(c, p27, r"2TR-FE\) engine.{0,40}?SAE 0W-20"), cite(c, p40, r"1GR-FE\) engine.{0,40}?SAE 5W-30"))

# ---- oil 2016-2023: 2TR-FE 2.7 L and 2GR-FKS 3.5 L V6
for y, pg in ((2016, 573), (2017, 575), (2018, 629), (2019, 633), (2020, 539)):
    c = MAN[y]
    visc = cite(c, pg, r"Recommended viscosity: SAE 0W-20")
    oil(y, 2.7, "2TR-FE engine", "0W-20", None, 6.2, 5.9,
        [cite(c, pg, r"6\.2 qt\. 5\.8 qt\. 2TR-FE engine", ["6.2"]), visc])
    oil(y, 3.5, "2GR-FKS engine", "0W-20", None, 6.1, 5.8,
        [cite(c, pg, r"without towing 6\.1 qt\.", ["6.1"]), visc], "without towing package")
    oil(y, 3.5, "2GR-FKS engine", "0W-20", None, 6.2, 5.9,
        [cite(c, pg, r"with towing 6\.2 qt\.", ["6.2"]), visc], "with towing package")
for y, pg in ((2021, 541), (2022, 547), (2023, 547)):
    c = MAN[y]
    visc = cite(c, pg, r"Recommended viscosity: SAE 0W-20")
    cap = cite(c, pg, r"2TR-FE engine 2GR-FKS engine With filter Without filter 6\.2 qt\.", ["6.2"])
    oil(y, 2.7, "2TR-FE engine", "0W-20", None, 6.2, 5.9, [cap, visc])
    oil(y, 3.5, "2GR-FKS engine", "0W-20", None, 6.2, 5.9, [cap, visc])

# ---- oil 2024-2025: 2.4 L turbo (gas and i-FORCE MAX hybrid manuals)
for c, y, pg, vpg in ((MAN[2024], 2024, 617, 617), (MAN[2025], 2025, 616, 617),
                      (HYB[2024], 2024, 587, 587), (HYB[2025], 2025, 600, 601)):
    hyb = c in HYB.values()
    oil(y, 2.4, "2.4 L turbo hybrid (i-FORCE MAX)" if hyb else "2.4 L turbo", "0W-20", None, 5.9, 5.6,
        [cite(c, pg, r"5\.9 qt\. \(5\.6 L, 4\.9 Imp\.", ["5.9"]), cite(c, vpg, r"SAE 0W-20 is the best choice")])

# ---- towing
def tow(y, src, max_lb, d=None, eng=None, package=None, gcwr=None, note=None, drive=None, cab=None):
    r = {"field": "towing", "years": [y, y]}
    for k, v in (("displacement_l", d), ("engine", eng), ("drive", drive), ("cab", cab)):
        if v is not None: r[k] = v
    r["max_lb"] = max_lb
    if gcwr: r["gcwr_lb"] = gcwr
    if package: r["package"] = package
    if note: r["note"] = note
    r["src"] = src
    R.append(r)

for y, pg in ((2008, 419), (2009, 469), (2010, 475)):
    c = MAN[y]
    tow(y, [cite(c, pg, r"With towing package (2948 kg )?\(?6500 lb\.\)?", ["6500"])], 6500, package="Towing package",
        note="model-wide rating in the specifications; trailer weight + cargo")
    tow(y, [cite(c, pg, r"Without towing package (Towing capacity )?(1587 kg )?\(?3500 lb\.\)?", ["3500"])], 3500,
        note="without towing package; model-wide rating in the specifications")

olds = {2011: (489, 490), 2012: (553, 554), 2014: (531, 532), 2015: (521, 522)}
ranges = {2011: ("6300", "3300"), 2012: ("6400", "3300"), 2014: ("6200", "3300"), 2015: ("6200", "3300")}
for y, (p1, p2) in olds.items():
    c = MAN[y]
    lo_pkg, lo_nopkg = ranges[y]
    tow(y, [cite(c, p2, r"TRN225L-PRPDKA 2\.7 L 4-cylinder 3400 lb\.", ["3400"]),
            cite(c, p2, r"TRN265L-PRPDKA \(2TR-FE\) engine 3500 lb\.", ["3500"])], 3500, 2.7, "2.7 L 4-cylinder (2TR-FE)",
        note="3,400 lb on Double Cab 2WD TRN225L-PRPDKA")
    tow(y, [cite(c, p2, r"6500 lb\. \((2945|2948) kg\)\*3", ["6500"]),
            cite(c, p2 if y != 2011 else p2, rf"{lo_pkg} lb\. \(\d+ kg\)\*3", [lo_pkg])], 6500, 4.0, "4.0 L V6 (1GR-FE)",
        package="Towing package", note=f"{int(lo_pkg):,}-6,500 lb by cab/drive/bed (model code)")
    tow(y, [cite(c, p1, rf"{lo_nopkg} lb\. \(\d+ kg\)", [lo_nopkg]), cite(c, p2, r"3500 lb\. \(\d+ kg\)\*2", ["3500"])],
        3500, 4.0, "4.0 L V6 (1GR-FE)", note=f"without towing package; {int(lo_nopkg):,}-3,500 lb by model code")

# 2016-2017: package footnotes; 2018-2023: no package distinction
for y, (pa, pd1, pd2) in {2016: (174, 175, 176), 2017: (176, 177, 178)}.items():
    c = MAN[y]
    tow(y, [cite(c, pd1, r"2TR-FE 7920 lb\. 3500 lb\.", ["3500"])], 3500, 2.7, "2TR-FE")
    tow(y, [cite(c, pa, r"11310 lb\.\*3 6800 lb\.\*3", ["6800"]), cite(c, pd2, r"11090 lb\.\*3 6000 lb\.\*3", ["6000"])],
        6800, 3.5, "2GR-FKS", package="Towing package", gcwr=11310, drive="2WD", cab="Access Cab",
        note="max on Access Cab 2WD GRN325L-CRTSHA; 6,000-6,800 lb by cab/drive/bed")
    tow(y, [cite(c, pa, r"7890 lb\.\*2 3500 lb\.\*2", ["3500"])], 3500, 3.5, "2GR-FKS", note="without towing package")
for y, pa, pd, g68, g60, g27 in ((2018, 181, 182, 11240, 11020, 7860), (2019, 181, 182, 11240, 11020, 7860),
                                 (2020, 189, 190, 11270, 11040, 7870), (2021, 189, 190, 11270, 11040, 7870),
                                 (2022, 189, 190, 11270, 11040, 7870), (2023, 189, 190, 11270, 11040, 7870)):
    c = MAN[y]
    tow(y, [cite(c, pd, rf"2TR-FE {g27} lb\. 3500 lb\.", ["3500"])], 3500, 2.7, "2TR-FE", gcwr=g27, cab="Double Cab", drive="2WD")
    tow(y, [cite(c, pa, rf"{g68} lb\. 6800 lb\.", ["6800"]), cite(c, pd, rf"{g60} lb\. 6000 lb\.", ["6000"])],
        6800, 3.5, "2GR-FKS", gcwr=g68, drive="2WD", cab="Access Cab",
        note="max on Access Cab 2WD GRN325L-CRTSHA; 6,000-6,800 lb by cab/drive/bed")
for c, y, p_dbl, p_xtra in ((MAN[2024], 2024, 205, 206), (MAN[2025], 2025, 204, 205)):
    tow(y, [cite(c, p_xtra, r"TZNA45L- 11335 lb\. 6500 lb\.", ["6500"])], 6500, 2.4, "2.4 L turbo", gcwr=11335,
        cab="XtraCab", note="max rating (XtraCab SR5 / TRD PreRunner); Double Cab grades 6,300-6,400 lb")
    tow(y, [cite(c, p_dbl, r"TZNA41L-PRZ- 8210 lb\. 3500 lb\.", ["3500"])], 3500, 2.4, "2.4 L turbo", gcwr=8210,
        cab="Double Cab", note="SR grade")
for c, y, pg in ((HYB[2024], 2024, 192), (HYB[2025], 2025, pg := 197)):
    tow(y, [cite(c, pg, r"Short Limited 11675 lb\. \(5295 kg\) 6000 lb\.", ["6000"])], 6000, 2.4,
        "2.4 L turbo hybrid (i-FORCE MAX)", note="short bed grades")
    tow(y, [cite(c, pg, r"Long TRAILHUNTER 11825 lb\. \(5365 kg\) 5950 lb\.", ["5950"])], 5950, 2.4,
        "2.4 L turbo hybrid (i-FORCE MAX)", gcwr=11825, note="long bed TRAILHUNTER")

# ---- tires (sizes as listed in each manual's tire specifications)
TIRES = {
    2008: (["P215/70R15 97S", "P245/75R16 109S", "P265/70R16 111T", "P265/65R17 110S", "P255/45R18 99V"], {}),
    2009: (["P215/70R15 97S", "P245/75R16 109S", "P265/70R16 111T", "P265/65R17 110S", "P255/45R18 99V"], {}),
    2010: (["P215/70R15 97S", "P245/75R16 109S", "P265/70R16 111T", "P265/65R17 110S", "P255/45R18 99V"], {}),
    2011: (["P215/70R15 97S", "P245/75R16 109S", "P265/70R16 111T", "P265/65R17 110S", "P255/45R18 99V"], {}),
    2012: (["P215/70R15 97S", "P245/75R16 109S", "P265/70R16 111T", "P265/65R17 110S", "P255/45R18 99V", "P265/60R18 109H"], {}),
    2014: (["P215/70R15 97S", "P245/75R16 109S", "P265/70R16 111T", "P265/65R17 110S", "P255/45R18 99V", "P265/60R18 109H"], {}),
    2015: (["P215/70R15 97S", "P245/75R16 109S", "P265/70R16 111T", "P265/65R17 110S", "P255/45R18 99V", "P265/60R18 109H"], {}),
}
for y in range(2016, 2024):
    TIRES[y] = (["P245/75R16 109S", "265/70R16 112T", "P265/65R17 110S", "P265/60R18 109H"], {})
TIRES[2024] = (["245/70R17 110T", "245/75R17 112S", "265/70R17 115T", "265/65R18 114T"], {})
TIRES[2025] = TIRES[2024]
import re as _re
from mkyaml import page_text
def find_page(c, size):
    pdf = DOCS[c]["pdf"]
    import subprocess
    n = int(_re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    txt = open(pdf[:-4] + ".txt", errors="replace").read().split("\f")
    for i, p in enumerate(txt, 1):
        if size in p and _re.search(r"psi|kPa", p) and _re.search(r"Tire size|TIRES", p):
            return i
    raise SystemExit(f"{size} not found in {c}")
for y, (sizes, _) in TIRES.items():
    for c in [MAN[y]] + ([HYB[y]] if y in HYB else []):
        hyb = c in HYB.values()
        for s in (["265/65R18 114T", "245/75R17 112S", "265/70R18 116T"] if hyb else sizes):
            pg = find_page(c, s)
            R.append({"field": "tires", "years": [y, y], "size": s.split()[0], "load_speed": s.split()[1],
                      **({"trim": "Hybrid (i-FORCE MAX)"} if hyb else {}),
                      "src": [cite(c, pg, _re.escape(s), [s.split()[0]])]})

dump(str(ROOT / "data/manuals/toyota/tacoma.yaml"), "toyota/tacoma", R)
