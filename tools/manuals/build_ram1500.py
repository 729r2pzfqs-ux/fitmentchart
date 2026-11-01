"""Ram 1500 (Dodge Ram 1500 through MY2010): writes data/manuals/ram/1500.yaml.

Sources, all fetched with the plain pipeline identity and cached in data/cache/manuals/ram-1500/ (gitignored):
- om/   Mopar owner's manuals and user guides (vehicleinfo.mopar.com/assets/publications/...)
- specs/ FCA/Stellantis media spec sheets and tow charts (s3 chryslermedia.iconicweb.com), plus the OEM 2007,
        2017 tow charts as hosted by fifthwheelst.com (the media host has no copy of those two)
- fa/   Feature Availability sheets (tire matrix, 2014-2016)
- tp/   tirepressure.com pages (third_party_reference, only for years without an OEM tire table)

Oil: owner's manual first, then user guide, then spec sheet (spec sheets print no grade). The Mopar numeric PDF
names (806.pdf etc.) come from search results or a small HEAD probe of nearby ids with the pipeline identity.
Towing: one record per engine + drive + cab = the highest "Max Trailer" row in that year's chart, with that
row's GCWR, axle, box and trim. The 1500 Tradesman HD rows (2012+) stay separate from the standard rows.

Conflicts, manual kept:
- 3.6L DT oil: spec sheets 2019-2023 and 2026 say 6.0 qt, the DT manuals/user guide say 5 qt.
- 3.0L EcoDiesel DT oil: spec sheets 2020-2023 say 10.5 qt, the DT manuals say 8.5 qt.
No manual was found for 2024 and 2025. The 3.6L DT stays empty there: the only value is the sheet's 6.0 qt,
which every DT manual contradicts (5 qt), and a wrong capacity overfills the engine.
2013 towing is a gap: the Stellantis media PDF answered 403, so the chart is not used from any other host.
"""
import json, re, subprocess, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mkyaml import DOCS, cite, dump, page_text
from tirepressure import rows as tp_rows

C = ROOT / "data/cache/manuals/ram-1500"
ACC = "2026-11-01"
M = "https://vehicleinfo.mopar.com/assets/publications/"
S3 = "https://s3.amazonaws.com/chryslermedia.iconicweb.com/mediasite/specs/"
FW = "https://FifthWheelSt.com/documents/ram/"
DEALER = "OEM chart, copy hosted by a dealer; the Stellantis media site lists none for this year"


def reg(ref, path, doc, url, typ, note=None):
    DOCS[ref] = {"pdf": str(path), "doc": doc, "url": url, "type": typ, "accessed": ACC}
    if note:
        DOCS[ref]["note"] = note


OM = {  # ref: (year, title, url path)
    "om2006": ("2006 Dodge Ram Truck (gas) Owner's Manual", "en-us/Ram/2006/1500/866.pdf"),
    "om2007": ("2007 Dodge Ram Truck (gas) Owner's Manual", "en-us/Ram/2007/1500/838.pdf"),
    "om2008": ("2008 Dodge Ram Truck (gas) Owner's Manual", "en-us/Ram/2008/1500/806.pdf"),
    "om2009": ("2009 Dodge Ram Truck (gas) Owner's Manual", "en-us/Ram/2009/1500/772.pdf"),
    "om2010": ("2010 Ram Truck Owner's Manual", "en-us/Ram/2010/1500/743.pdf"),
    "om2011": ("2011 Ram Truck 1500/2500/3500 Owner's Manual", "en-us/Ram/2011/1500/714.pdf"),
    "ug2013": ("2013 Ram 1500/2500/3500 Truck User's Guide", "en-us/Ram/2013/1500/P130070_13_DSDJD2_UG_EN_USC_U10_V2.pdf"),
    "om2014": ("2014 Ram Truck 1500/2500/3500 Owner's Manual", "en-us/Ram/2014/1500/279.pdf"),
    "ug2014": ("2014 Ram 1500/2500/3500 Truck User's Guide", "en-us/Ram/2014/1500/100285_14_DSDJD2_UG_EN_USC_E8_V3_DIGITAL.pdf"),
    "om2015": ("2015 Ram Truck 1500/2500/3500 Owner's Manual", "en-us/Ram/2015/1500/244.pdf"),
    "om2016": ("2016 Ram Truck 1500/2500/3500 Owner's Manual", "en-us/Ram/2016/1500/64.pdf"),
    "ds2016": ("2016 Ram Truck Diesel Supplement", "en-us/Ram/2016/1500/118.pdf"),
    "ug2017": ("2017 Ram 1500/2500/3500 User's Guide", "en-us/Ram/2017/1500/100294_17_DSDJD2_UG_EN_USC_E7_V3_DIGITAL.pdf"),
    "ds2017": ("2017 Ram Truck Diesel Supplement", "en-us/Ram/2017/1500/100330_17_DS_D_SU_EN_USA_E6_V1.pdf"),
    "om2018": ("2018 Ram Truck 1500/2500/3500 Owner's Manual", "en-us/Ram/2018/1500/P127381_18_DSDJD2_OM_EN_USC_DIGITAL.pdf"),
    "ug2018": ("2018 Ram 1500/2500/3500 User Guide", "en-us/Ram/2018/1500/100297_18_DSDJD2_UG_EN_USC_E6_V2_DIGITAL.pdf"),
    "om2019x": ("2019 Ram 1500 (DS, 19DS-126-AC) Owner's Manual", "en-us/Ram/2019/1500/9854.pdf"),
    "ug2019": ("2019 All-New Ram 1500 (DT) User Guide", "en-us/Ram/2019/1500_DT/P108670_19_DT_UG_EN_USC_DIGITAL_E9.pdf"),
    "om2020": ("2020 Ram 1500 Owner's Manual", "en-us/Ram/2020/1500_DT/5633292_20_DT_OM_EN_USC_DIGITAL_E5.pdf"),
    "om2021": ("2021 Ram 1500 Owner's Manual", "en-us/Ram/2021/1500_DT/5633293_21_DT_OM_EN_USC_DIGITAL_E4.pdf"),
    "om2022": ("2022 Ram 1500 Owner's Manual", "en-us/Ram/2022/1500_DT/5690658_22_DT_OM_EN_USC_DIGITAL_E5.pdf"),
    "om2022c": ("2022 Ram 1500 Classic Owner's Manual", "en-us/Ram/2022/1500_Classic/P136747_22_DS_OM_EN_USC_DIGITAL.pdf"),
    "om2023": ("2023 Ram 1500 Owner's Manual", "en-us/Ram/2023/1500_DT/5690659_23_DT_OM_EN_USC_DIGITAL_E6.pdf"),
    "om2026": ("2026 Ram 1500 Owner's Manual (US/Canada)", "en-us-ca/2026/Ram/1500/103960_26_DT_OM_EN_USC_DIGITAL_E1_V1.pdf"),
}
for k, (t, u) in OM.items():
    reg(k, C / "om" / f"{k}.pdf", t, M + u, "oem_manual")

SHEET = {  # ref: file, title
    "sp2011": ("2011_Ram_1500_Specs.pdf", "2011 Ram 1500 Specifications"),
    "sp2012": ("2012_Ram_1500_Specs.pdf", "2012 Ram 1500 Specifications"),
    "sp2015": ("2015_RAM_1500_SPvcfijqn696qeodm5be2oh020fk.pdf", "2015 Ram 1500 Specifications"),
    "sp2016": ("2016_RAM_1500_SP9ggrpnh4j7j42ctdakh0tqfptm.pdf", "2016 Ram 1500 Specifications"),
    "sptrx21": ("2021_RAM_1500_TRX_Specificationsncds40e91jnt64taolkbbpi9eq.pdf", "2021 Ram 1500 TRX Specifications"),
    "sp2022": ("2022_RAM_1500_SPljhbq4p17a2llk0gffhcnq6vp6.pdf", "2022 Ram 1500 Specifications"),
    "sp2023": ("2023_RAM_1500_SP2hm4pmdjg37oougooiugcoqvmm.pdf", "2023 Ram 1500 Specifications"),
    "sp2024": ("2024_RAM_1500_SP.pdf", "2024 Ram 1500 Specifications"),
    "sp2025": ("2025_Ram_1500_SPals9gfdughljsslrkifm8fhfev.pdf", "2025 Ram 1500 Specifications"),
}
for k, (f, t) in SHEET.items():
    reg(k, C / "specs" / f, t + " (FCA/Stellantis media spec sheet)", S3 + f, "oem_spec_sheet")

CHART = {  # year: ref, file, title, url, note
    2007: ("tc2007", "fifth_2007_ram_1500.pdf", "2007 Ram Base Weights/GCW/Payload chart", FW + "2007_ram_1500.pdf", DEALER),
    2012: ("tc2012", "2012Ram1500towcharts.pdf", "2012 Ram 1500 Towing Charts", None, None),
    2014: ("tc2014", "2014_Ram_1500_TowCharts.pdf", "2014 Ram 1500 Towing Charts", None, None),
    2015: ("tc2015", "2015Ram1500weightcharts.pdf", "2015 Ram 1500 Trailer Towing Chart", None, None),
    2016: ("tc2016", "2016_Ram_1500_Towing_Charta6uiodh2o5dhjpjg6m536e3f2j.pdf", "2016 Ram 1500 Trailer Towing Chart", None, None),
    2017: ("tc2017", "fifth_2017_ram_1500_towing_charts.pdf", "2017 Ram 1500 Trailer Towing Chart", FW + "2017_ram_1500_towing_charts.pdf", DEALER),
    2018: ("tc2018", "2018_RAM_1500_Towing_Charts9erd3oqa5hsbon6ei8s89jubbj.pdf", "2018 Ram 1500 Towing Chart", None,
           "cover says 2018; the table heading inside still reads 2017"),
    2019: ("tc2019", "2019_RAM_1500_TowingCharttos0d7ai3on6nkufj57pjcrqkf.pdf", "2019 Ram 1500 Towing Chart", None, None),
    2020: ("tc2020", "2020_RAM_1500_TowingChartqco8qpknek3eu41cbio9sertdh.pdf", "2020 Ram 1500 Towing Chart", None, None),
    2021: ("tc2021", "2021_RAM_1500_TowingChartui58421ctg4ce8krg2ormmck8k.pdf", "2021 Ram 1500 Towing Chart", None, None),
    2022: ("tc2022", "2022_RAM_1500_Towingbua1e6piok25592o597knb5k16.pdf", "2022 Ram 1500 Towing Charts", None, None),
    2023: ("tc2023", "2023_RAM_1500_Towingkecmrqn399hj506s9t8ss71i3t.pdf", "2023 Ram 1500 Towing Charts", None, None),
    2024: ("tc2024", "2024_RAM_1500_Towing.pdf", "2024 Ram 1500 Towing Charts", None, None),
    2025: ("tc2025", "2025_Ram_1500_Towingo641sfdhdb3h854lbudqh2hi23.pdf", "2025 Ram 1500 Towing Charts", None, None),
    2026: ("tc2026", "2026_Ram_1500_Towingmp7rhmak7upm27tiq1bjgphrln.pdf", "2026 Ram 1500 Trailer Towing Charts", None, None),
}
for y, (k, f, t, u, n) in CHART.items():
    reg(k, C / "specs" / f, t, u or S3 + f, "oem_towing_guide", n)

ENG = {int(y): {e["displacement_l"] for e in v["engines"]}
       for y, v in json.load(open(ROOT / "data/sources/fueleconomy/ram/1500.json"))["years"].items()}
R, SKIPPED = [], []


def npages(ref):
    out = subprocess.run(["pdfinfo", DOCS[ref]["pdf"]], capture_output=True, text=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", out).group(1))


def find(ref, rx, must=()):
    """cite() on the first page of the document that matches."""
    for p in range(1, npages(ref) + 1):
        if any(re.search(rx, page_text(DOCS[ref]["pdf"], p, m), re.I) for m in (False, True, "raw")):
            return cite(ref, p, rx, must)
    raise SystemExit(f"pattern {rx!r} not found in {ref}")


def add(rec):
    d = rec.get("displacement_l")
    if d is not None and d not in ENG.get(rec["years"][0], ()):
        SKIPPED.append((rec["field"], rec["years"][0], d))
        return
    R.append(rec)


# ---------------------------------------------------------------- oil
def oil(y, d, eng, grade, qt, l, src, cond=None, note=None):
    r = {"field": "oil", "years": [y, y], "displacement_l": d, "engine": eng}
    if cond: r["condition"] = cond
    if grade: r["grade"] = grade
    r.update({"capacity_qt": qt, "capacity_l": l})
    if note: r["note"] = note
    r["src"] = src
    add(r)


c = "om2006"  # year comes from Mopar's folder; the PDF prints no model year (created October 2005)
oil(2006, 3.7, "3.7L V-6", "5W-30", 5.0, 4.7, [find(c, r"3\.7L Engine V-6, SAE 5W-30, API Certified 5\.0 qts\. 4\.7L", ["5.0 qts"])])
oil(2006, 4.7, "4.7L V-8", "5W-30", 6.0, 5.7, [find(c, r"4\.7L Engine V-8, SAE 5W-30, API Certified 6\.0 qts\. 5\.7L", ["6.0 qts"])])
oil(2006, 5.7, "5.7L V-8", "5W-20", 7.0, 6.6, [find(c, r"5\.7L Engine V-8, SAE 5W-20, API Certified 7\.0 qts\. 6\.6L", ["7.0 qts"])])
c = "om2007"  # year comes from Mopar's folder; the PDF prints no model year (created March 2006)
oil(2007, 3.7, "3.7L V-6", "5W-30", 5.0, 4.7, [cite(c, 512, r"3\.7L Engine V-6 \(SAE 5W-30, API Certified\) 5\.0 qts\. 4\.7L", ["5.0 qts"])])
oil(2007, 4.7, "4.7L V-8", "5W-30", 6.0, 5.7, [cite(c, 512, r"4\.7L Engine V-8 \(SAE 5W-30, API Certified\) 6\.0 qts\. 5\.7L", ["6.0 qts"])])
oil(2007, 5.7, "5.7L V-8", "5W-20", 7.0, 6.6, [cite(c, 513, r"5\.7L Engine V-8 \(SAE 5W-20, API Certified\)\. For trucks operating under a gross combined weight rating less 7\.0 qts\. 6\.6L", ["7.0 qts"])],
    cond="trucks under 14,000 lb GCWR")
c = "om2008"
oil(2008, 3.7, "3.7L V-6", "5W-20", 5.0, 4.7, [cite(c, 511, r"3\.7L Engine V-6 \(SAE 5W-20, API Certified\) 5\.0 qts 4\.7 L", ["5.0 qts"])])
oil(2008, 4.7, "4.7L V-8", "5W-20", 6.0, 5.7, [cite(c, 511, r"4\.7L Engine V-8 \(SAE 5W-20, API Certified\) 6\.0 qts 5\.7 L", ["6.0 qts"])])
oil(2008, 5.7, "5.7L V-8", "5W-20", 7.0, 6.6, [cite(c, 511, r"5\.7L Engine V-8 \(SAE 5W-20, API Certified\)\. For trucks operat- ?7\.0 qts 6\.6 L", ["7.0 qts"])],
    cond="trucks under 14,000 lb GCWR")
for y, c, p in ((2009, "om2009", 490), (2010, "om2010", 561), (2011, "om2011", 582)):
    oil(y, 3.7, "3.7L V-6", "5W-20", 5.0, 4.7, [cite(c, p, r"3\.7L Engine \(SAE 5W-20, API Certified\) 5 Quarts 4\.7 Liters", ["5 Quarts"])])
    oil(y, 4.7, "4.7L V-8", "5W-20", 6.0, 5.7, [cite(c, p, r"4\.7L Engine \(SAE 5W-20, API Certified\) 6 Quarts 5\.7 Liters", ["6 Quarts"])])
    oil(y, 5.7, "5.7L HEMI V-8", "5W-20", 7.0, 6.6, [cite(c, p, r"5\.7L Engine \(SAE 5W-20, API Certified\) 7 Quarts 6\.6 Liters", ["7 Quarts"])])
for d, eng, qt, l in ((3.7, "3.7L V-6", 5.0, 4.7), (4.7, "4.7L V-8", 6.0, 5.7), (5.7, "5.7L HEMI V-8", 7.0, 6.6)):
    oil(2012, d, eng, None, qt, l, [find("sp2012", rf"Oil Capacity {qt} qt\. \({l}L\)", [str(qt)])])
c = "ug2013"
g13 = cite(c, 172, r"We recommend you use API certified 5W-?\s?20 engine oil", ["20"])
oil(2013, 3.6, "3.6L V-6", "5W-20", 6.0, 5.7, [cite(c, 172, r"3\.6L Engine - 6 Quarts \(5\.7 Li- ?ters\)", ["6 Quarts"]), g13])
oil(2013, 4.7, "4.7L V-8", "5W-20", 6.0, 5.7, [cite(c, 172, r"4\.7L Engine - 6 Quarts \(5\.7 Li- ?ters\)", ["6 Quarts"]), g13])
oil(2013, 5.7, "5.7L HEMI V-8", "5W-20", 7.0, 6.6, [cite(c, 172, r"5\.7L Engine - 7 Quarts \(6\.6 Li- ?ters\)", ["7 Quarts"]), g13])
c = "ug2014"
oil(2014, 3.6, "3.6L V-6", "5W-20", 6.0, 5.6, [cite("om2014", 748, r"3\.6L Engine \(We recommend you use SAE 5W-20, API Certified\) 6 Quarts 5\.6 Liters", ["6 Quarts"])])
oil(2014, 5.7, "5.7L HEMI V-8", "5W-20", 7.0, 6.6, [cite("om2014", 748, r"5\.7L Engines \(We recommend you use SAE 5W-20, API Certified\) 7 Quarts 6\.6 Liters", ["7 Quarts"])])
oil(2014, 3.0, "3.0L EcoDiesel V-6", "5W-40", 10.5, 10.0, [cite(c, 227, r"10\.5 Quarts \(10 Liters\)", ["10.5"]),
                                                          cite(c, 227, r"We recommend you use 5W-40 synthetic engine oil such as MOPAR or Shell Rotella", ["5W-40"])])
for y, c in ((2015, "om2015"), (2016, "om2016")):
    oil(y, 3.6, "3.6L V-6", "5W-20", 6.0, 5.6, [find(c, r"3\.6L Engine \(We recommend you use SAE 5W-20, API Certified\) 6 Quarts 5\.6 Liters", ["6 Quarts"])])
    oil(y, 5.7, "5.7L HEMI V-8", "5W-20", 7.0, 6.6, [find(c, r"5\.7L Engines \(We recommend you use SAE 5W-20, API Certified\) 7 Quarts 6\.6 Liters", ["7 Quarts"])])
oil(2015, 3.0, "3.0L EcoDiesel V-6", None, 10.5, None, [find("sp2015", r"Oil Capacity 10\.5 qt\. \(7\.8 liter\)", ["10.5"])],
    note="sheet prints 10.5 qt (7.8 liter); the litre figure does not match the quarts, so it is left out")
oil(2016, 3.0, "3.0L EcoDiesel V-6", "5W-40", 10.5, 10.0, [find("ds2016", r"3\.0L Liter Diesel Engine 10\.5 Quarts 10 Liters", ["10.5"]),
                                                          find("sp2016", r"Oil Capacity 10\.5 quarts \(10 liters\)", ["10.5"]),
                                                          find("ds2016", r"5W-40 synthetic engine oil", ["5W-40"])])
c = "ug2017"
oil(2017, 3.6, "3.6L V-6", "5W-20", 6.0, 5.6, [cite(c, 314, r"3\.6L Engine \(We recommend you use ?6 Quarts 5\.6 Liters ?SAE 5W-20, API Certified\)", ["6 Quarts"])])
oil(2017, 5.7, "5.7L HEMI V-8", "5W-20", 7.0, 6.6, [cite(c, 314, r"5\.7L Engines \(We recommend you use ?7 Quarts 6\.6 Liters ?SAE 5W-20, API Certified\)", ["7 Quarts"])])
oil(2017, 3.0, "3.0L EcoDiesel V-6", "5W-40", 10.5, 10.0, [cite(c, 317, r"3\.0L Liter Diesel Engine \(SAE 5W-40 Synthetic, ?10\.5 Quarts 10 Liters", ["10.5"]),
                                                          cite("ds2017", 79, r"3\.0L Liter Diesel Engine 10\.5 Quarts 10 Liters \(SAE 5W-40 Synthetic", ["10.5"])])
c = "om2018"
oil(2018, 3.6, "3.6L V-6", "5W-20", 6.0, 5.6, [cite(c, 617, r"3\.6L Engine \(We recommend you use SAE 5W-20, API Certified\) 6 Quarts 5\.6 Liters", ["6 Quarts"])])
oil(2018, 5.7, "5.7L HEMI V-8", "5W-20", 7.0, 6.6, [cite(c, 617, r"5\.7L Engines \(We recommend you use SAE 5W-20, API Certified\) 7 Quarts 6\.6 Liters", ["7 Quarts"])])
oil(2018, 3.0, "3.0L EcoDiesel V-6", "5W-40", 10.5, 10.0, [cite("ug2018", 281, r"3\.0L Liter Diesel Engine 10\.5 Quarts 10 Liters \(SAE 5W-40 Synthetic", ["10.5"])])
# 2019: the DS manual covers the truck sold as the 1500 Classic; the DT is the all-new truck's user guide
CL, DT = "1500 Classic (DS)", "new-body 1500 (DT)"
c = "om2019x"
oil(2019, 3.6, "3.6L V-6", "5W-20", 6.0, 5.6, [cite(c, 508, r"3\.6L Engine \(We recommend you use SAE 5W-20, API Certified\) 6 Quarts 5\.6 Liters", ["6 Quarts"])], cond=CL)
oil(2019, 5.7, "5.7L HEMI V-8", "5W-20", 7.0, 6.6, [cite(c, 508, r"5\.7L Engine \(We recommend you use SAE 5W-20, API Certified\) 7 Quarts 6\.6 Liters", ["7 Quarts"])], cond=CL)
c = "ug2019"
oil(2019, 3.6, "3.6L V-6", "0W-20", 5.0, 4.7, [cite(c, 239, r"3\.6L Engine \(We recommend you use SAE 0W-20, API Certified\) 5 Quarts 4\.7 Liters", ["5 Quarts"])], cond=DT)
oil(2019, 5.7, "5.7L HEMI V-8", "5W-20", 7.0, 6.6, [cite(c, 240, r"5\.7L Engines \(We recommend you use SAE 5W-20, API Certified\) 7 Quarts 6\.6 Liters", ["7 Quarts"])], cond=DT)
c = "om2020"
oil(2020, 3.6, "3.6L V-6", "0W-20", 5.0, 4.7, [cite(c, 312, r"3\.6L Engine \(We recommend you use SAE 0W-20, API Certified\) 5 Quarts 4\.7 Liters", ["5 Quarts"])], cond=DT)
oil(2020, 5.7, "5.7L HEMI V-8", "5W-20", 7.0, 6.6, [cite(c, 312, r"5\.7L Engines \(We recommend you use SAE 5W-20, API Certified\) 7 Quarts 6\.6 Liters", ["7 Quarts"])], cond=DT)
oil(2020, 3.0, "3.0L EcoDiesel V-6", None, 8.5, 8.0, [cite(c, 313, r"3\.0L Diesel Engine 8\.5 Quarts 8\.0 Liters", ["8.5"])], cond=DT)
for y, c, cp, gp in ((2021, "om2021", 362, 363), (2022, "om2022", 372, 373), (2023, "om2023", 382, 383)):
    u = r"Quarts" if y < 2023 else r"qt"
    lit = r"Liters" if y < 2023 else r"L"
    g36 = r"SAE 0W-20 (E|e)ngine (O|o)il" if y == 2021 else r"Mopar®? SAE 0W-20 Full Synthetic Engine Oil"
    g57 = r"API Certified SAE 5W-20 engine oil" if y == 2021 else g36
    gsrc = [cite(c, gp, g36, ["0W-20"])]
    oil(y, 3.6, "3.6L V-6", "0W-20", 5.0, 4.7, [cite(c, cp, rf"3\.6L Engine 5 {u} 4\.7 {lit}", ["5"])] + gsrc, cond=DT)
    oil(y, 5.7, "5.7L HEMI V-8", "5W-20" if y == 2021 else "0W-20", 7.0, 6.6,
        [cite(c, cp, rf"5\.7L Engine 7 {u} 6\.6 {lit}", ["7"]), cite(c, gp, g57, ["W-20"])], cond=DT)
    oil(y, 3.0, "3.0L EcoDiesel V-6", "5W-40", 8.5, 8.0, [cite(c, cp, rf"3\.0L Turbo Diesel Engine 8\.5 {u} 8\.0 {lit}", ["8.5"]),
                                                         cite(c, gp, r"5W-40 synthetic engine oil such as Mopar", ["5W-40"])], cond=DT)
c = "om2022c"
oil(2022, 3.6, "3.6L V-6", "5W-20", 6.0, 5.6, [cite(c, 348, r"3\.6L Engine 6 Quarts 5\.6 Liters", ["6 Quarts"]),
                                               cite(c, 348, r"We recommend using Mopar®? SAE 5W-20 Full Synthetic Engine Oil", ["5W-20"])], cond=CL)
oil(2022, 5.7, "5.7L HEMI V-8", "0W-20", 7.0, 6.6, [cite(c, 348, r"5\.7L Engine 7 Quarts 6\.6 Liters", ["7 Quarts"]),
                                                    cite(c, 349, r"We recommend using Mopar®? SAE 0W-20 Full Synthetic Engine Oil", ["0W-20"])], cond=CL)
for y, c, rx in ((2021, "sptrx21", r"Oil Capacity 7\.9 quarts \(7\.4 liters\)"), (2022, "sp2022", r"Oil Capacity 7\.9 quarts \(7\.4 liters\)"),
                 (2023, "sp2023", r"Oil Capacity 7\.9 quarts \(7\.4 liters\)"), (2024, "sp2024", r"Oil Capacity 7\.9 quarts \(7\.4 liters\)")):
    oil(y, 6.2, "6.2L HEMI Supercharged V-8", None, 7.9, 7.4, [find(c, rx, ["7.9"])], cond="TRX")
oil(2024, 5.7, "5.7L HEMI V-8 eTorque", None, 7.0, 6.6, [find("sp2024", r"Oil Capacity 7\.0 quarts \(6\.6 liters\)", ["7.0"])], cond=DT)
oil(2025, 3.0, "3.0L Straight-Six Turbo", None, 7.5, 7.1, [find("sp2025", r"Oil Capacity 7\.5 quarts \(7\.1 liters\) oil change with filter", ["7.5"])], cond="Standard Output and High Output")
c = "om2026"
oil(2026, 3.6, "3.6L V-6", "0W-20", 5.0, 4.7, [cite(c, 379, r"3\.6L Engine 5 qt 4\.7 L", ["5 qt"]), cite(c, 376, r"Mopar®? SAE 0W-20 Full Synthetic Engine Oil", ["0W-20"])])
oil(2026, 5.7, "5.7L HEMI V-8", "0W-20", 7.0, 6.6, [cite(c, 379, r"5\.7L Engine 7 qt 6\.6 ?L", ["7 qt"]), cite(c, 376, r"Mopar®? SAE 0W-20 Full Synthetic Engine Oil", ["0W-20"])])
oil(2026, 3.0, "3.0L Standard Output", "0W-20", 7.5, 7.1, [cite(c, 379, r"3\.0L Engine 7\.5 qt 7\.1 L", ["7.5"]), cite(c, 376, r"Mopar®? SAE 0W-20 Full Synthetic Engine Oil", ["0W-20"])], cond="Standard Output")
oil(2026, 3.0, "3.0L High Output (RHO)", "0W-40", 7.5, 7.1, [cite(c, 379, r"3\.0L Engine 7\.5 qt 7\.1 L", ["7.5"]), cite(c, 376, r"Mopar®? API Certified SAE 0W-40 Full Synthetic Engin", ["0W-40"])], cond="High Output (RHO)")


# ---------------------------------------------------------------- towing: tow charts
HEAD = re.compile(r"\b(STD|REG\w*|QUAD|CREW|MEGA)\b.*?\b(4x2|4x4|2WD|4WD)\b|\b(4x2|4x4|2WD|4WD)\b.*?\b(STD|REG\w*|QUAD|CREW|MEGA)\b", re.I)
ROW = re.compile(r"^(?P<pre>.*?)\b(?P<axle>[34]\.\d{1,2})\s+(?P<nums>(?:\d[\d,.]*\s+){5,}\d[\d,.]*)$")
CAB = {"STD": "Regular Cab", "REG": "Regular Cab", "QUAD": "Quad Cab", "CREW": "Crew Cab", "MEGA": "Mega Cab"}
ENGRX = re.compile(r"\b(\d\.\d)(?:L\b| V-?\d)", re.I)


def layout_lines(ref, p):
    t = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-layout", DOCS[ref]["pdf"], "-"], capture_output=True, text=True).stdout
    return [re.sub(r"\s+", " ", l).strip() for l in t.split("\n") if l.strip()]


def engine_of(text):
    """(displacement, label) for one row's engine text, or None."""
    t = text.replace("­", "")
    m = ENGRX.search(t)
    if not m:
        return None
    d = float(m.group(1))
    if d == 3.0:
        if re.search(r"DIESEL", t, re.I): return d, "3.0L EcoDiesel V-6"
        return d, "3.0L I6 Twin Turbo High Output" if re.search(r"\bHO\b", t) else "3.0L I6 Twin Turbo Standard Output"
    if d == 5.7:
        return d, "5.7L HEMI V-8 eTorque" if re.search(r"eTorque|BSG", t, re.I) else "5.7L HEMI V-8"
    if d == 3.6:
        return d, "3.6L V-6 eTorque" if re.search(r"eTorque|BSG", t, re.I) else "3.6L V-6"
    return d, {3.7: "3.7L V-6", 4.7: "4.7L V-8", 6.2: "6.2L Supercharged V-8"}[d]


def heading(l):
    u = l.replace("­", "")
    m = re.search(r"\b(STD|REG\w*|QUAD|CREW|MEGA)\b", u, re.I)
    cab = CAB[m.group(1).upper()[:3] if m.group(1).upper()[:3] in ("STD", "REG") else m.group(1).upper()]
    drive = "2WD" if re.search(r"4x2|2WD", u, re.I) else "4WD"
    b = re.search(r"(\d)['’]\s*(\d{1,2})?(?:[\"”]|\b)|(\d)-ft\.?\s*(\d)-in|(SHORT|LONG) BED", u, re.I)
    bed = None
    if b:
        bed = b.group(5).title() + " Bed" if b.group(5) else (f"{b.group(3)} ft {b.group(4)} in" if b.group(3) else
              (f"{b.group(1)} ft {b.group(2)} in" if b.group(2) else f"{b.group(1)} ft"))
    tr = re.sub(r"^(1500 )?RAM( 1500)?\s*|\b(STD|REG\w*|QUAD|CREW|MEGA)( CAB)?\b|\b4x[24]\b|\b[24]WD\b|\d['’]\s*\d*[\"”]?|\d-ft\.?\s*\d-in\.?"
                r"|\b(SHORT|LONG) BED\b|\bBOX\b|\bD[RH1] \w+\b|[:,]", " ", u, flags=re.I)
    tr = re.sub(r"\s+", " ", re.sub(r"\(continued\)", " ", tr, flags=re.I)).strip(" -")
    return cab, drive, bed, tr or None


def chart_rows(y):
    ref = CHART[y][0]
    out = []
    head, hp = None, None  # a table can run onto the next page without repeating its heading
    for p in range(1, npages(ref) + 1):
        ls = layout_lines(ref, p)
        if y == 2007 and p != 23 and not any("Payload 1500" in l for l in ls[:8]):
            continue
        for i, l in enumerate(ls):
            plain = l.replace("­", "")
            if len(l) < 75 and HEAD.search(plain) and not ROW.match(plain):
                head, hp = l, p
                continue
            m = ROW.match(l)
            if m and not head:
                raise SystemExit(f"{y} p.{p}: row before any heading: {l!r}")
            if not m:
                continue
            if y == 2007 and p == 23 and not head.startswith("1500 "):
                continue
            nums = m["nums"].split()
            mx, gcwr = int(float(nums[-1].replace(",", ""))), int(float(nums[-2].replace(",", "")))
            if not (1500 < mx < 16000 and gcwr > mx):
                continue
            # engine text: this line, else the lines just above/below (labels wrap around the row)
            up = []
            if engine_of(m["pre"]):
                ctx = m["pre"]
            else:
                j = i - 1
                while j >= 0 and i - j <= 4 and not ROW.match(ls[j]) and not HEAD.search(ls[j]):
                    up.insert(0, ls[j])
                    if ENGRX.search(ls[j]):
                        break
                    j -= 1
                down = []
                for k in range(i + 1, min(i + 5, len(ls))):
                    if ROW.match(ls[k]) or HEAD.search(ls[k]) or re.search(r"\d\.\dL?\s", ls[k]):
                        break
                    down.append(ls[k])
                ctx = " ".join(up + [m["pre"]] + down)
            e = engine_of(ctx)
            if not e:
                raise SystemExit(f"{y} p.{p}: no engine for row {l!r} (context {ctx!r})")
            out.append({"page": p, "hpage": hp, "head": head, "line": " ".join(up + [l]), "d": e[0], "eng": e[1], "axle": m["axle"], "max": mx, "gcwr": gcwr})
    return out


NOTE = "highest rating in this year's chart for this engine, cab and drive"
for y in CHART:
    ref = CHART[y][0]
    best = {}
    for r in chart_rows(y):
        cab, drive, bed, trim = heading(r["head"])
        hd = bool(trim and re.search(r"TRADESMAN HD", trim))
        k = (r["eng"], drive, cab, hd)
        if k not in best or r["max"] > best[k][0]["max"]:
            best[k] = (r, bed, trim)
    for (eng, drive, cab, hd), (r, bed, trim) in sorted(best.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2], kv[0][3])):
        rec = {"field": "towing", "years": [y, y], "displacement_l": r["d"], "engine": eng, "drive": drive, "cab": cab}
        if bed: rec["bed"] = bed
        if trim: rec["trim"] = trim
        rec.update({"axle": r["axle"], "max_lb": r["max"], "gcwr_lb": r["gcwr"], "note": NOTE})
        rec["src"] = [cite(ref, r["hpage"], re.escape(r["head"]), []), cite(ref, r["page"], re.escape(r["line"]), [])]
        add(rec)

# 2011: matrix in the spec sheet, read by hand
TOW11 = (
    (3.7, "3.7L V-6", "2WD", "Regular Cab", "Short Box", "ST", "3.92", 8500, 3750, r"3\.92 ST 8,500 3,450 3,750"),
    (3.7, "3.7L V-6", "2WD", "Quad Cab", "Short Box", "ST", "3.92", 8500, 3450, r"3\.92 ST 8,500 3,450 3,750"),
    (4.7, "4.7L V-8", "2WD", "Regular Cab", "Short Box", "ST, SLT, Outdoorsman", "3.92", 12500, 7600, r"3\.92 ST, SLT, Outdoorsman 12,500 7,600"),
    (4.7, "4.7L V-8", "4WD", "Regular Cab", "Short Box", "ST, SLT, Outdoorsman", "3.92", 12500, 7450, r"3\.92 ST, SLT, Outdoorsman 12,500 7,450"),
    (4.7, "4.7L V-8", "2WD", "Crew Cab", "Short Box", "ST, SLT, Outdoorsman", "3.92", 12500, 7250, r"3\.92 ST, SLT, Outdoorsman 12,500 7,250 7,300"),
    (4.7, "4.7L V-8", "2WD", "Quad Cab", "Short Box", "ST, SLT, Outdoorsman", "3.92", 12500, 7300, r"3\.92 ST, SLT, Outdoorsman 12,500 7,250 7,300"),
    (4.7, "4.7L V-8", "4WD", "Crew Cab", "Short Box", "ST, SLT, Outdoorsman", "3.92", 12500, 7050, r"3\.92 ST, SLT, Outdoorsman 12,500 7,050 7,150"),
    (4.7, "4.7L V-8", "4WD", "Quad Cab", "Short Box", "ST, SLT, Outdoorsman", "3.92", 12500, 7150, r"3\.92 ST, SLT, Outdoorsman 12,500 7,050 7,150"),
    (5.7, "5.7L HEMI V-8", "2WD", "Regular Cab", "Long Box", "ST, SLT, Outdoorsman, Sport", "3.92", 15500, 10400, r"14,000 15,500 9,100 10,400"),
    (5.7, "5.7L HEMI V-8", "4WD", "Regular Cab", "Long Box", "SLT, Outdoorsman, Sport, Laramie", "3.92", 15500, 10450, r"14,000 15,500 8,900 10,450"),
    (5.7, "5.7L HEMI V-8", "2WD", "Crew Cab", "Short Box", "ST, SLT, Outdoorsman, Sport, Big Horn, Lone Star, Laramie", "3.92", 15500, 10200, r"15,500 15,500 10,200 10,250"),
    (5.7, "5.7L HEMI V-8", "2WD", "Quad Cab", "Short Box", "ST, SLT, Outdoorsman, Sport, Big Horn, Lone Star, Laramie", "3.92", 15500, 10250, r"15,500 15,500 10,200 10,250"),
    (5.7, "5.7L HEMI V-8", "4WD", "Crew Cab", "Short Box", "ST, SLT, Outdoorsman, Sport, Big Horn, Lone Star, Laramie", "3.92", 15500, 10000, r"15,500 15,500 10,000 10,050"),
    (5.7, "5.7L HEMI V-8", "4WD", "Quad Cab", "Short Box", "ST, SLT, Outdoorsman, Sport, Big Horn, Lone Star, Laramie", "3.92", 15500, 10050, r"15,500 15,500 10,000 10,050"),
)
for d, eng, drive, cab, bed, trim, axle, gcwr, mx, rx in TOW11:
    add({"field": "towing", "years": [2011, 2011], "displacement_l": d, "engine": eng, "drive": drive, "cab": cab, "bed": bed,
         "trim": trim, "axle": axle, "max_lb": mx, "gcwr_lb": gcwr, "note": NOTE,
         "src": [find("sp2011", rx, [f"{mx:,}"])]})

# ---------------------------------------------------------------- tires
FA = {  # year: ref, file, page, column order as printed in the sheet header
    2014: ("fa2014", "2014_RAM_1500_FA.pdf", 8, ["Tradesman", "Express", "HFE", "Big Horn/Lone Star", "Outdoorsman", "Sport", "Laramie", "Laramie Longhorn", "Laramie Limited"]),
    2015: ("fa2015", "2015_RAM_1500_FA.pdf", 9, ["Tradesman", "Express", "HFE", "SLT", "Big Horn/Lone Star", "Outdoorsman", "Sport", "Laramie", "Laramie Longhorn", "Laramie Limited"]),
    2016: ("fa2016", "2016_RAM_1500_FArab65blg1vrdudt39it3c6qmau.pdf", 10, ["Tradesman", "Express", "HFE", "SLT", "Big Horn/Lone Star", "Outdoorsman 4x4", "Sport", "Rebel", "Laramie", "Laramie Longhorn", "Laramie Limited"]),
}
SIZE = re.compile(r"\b((?:P|LT)?\d{3}/\d{2}R\d{2})([DE])?\b")
LEG = {"S": "Standard", "O": "Optional", "P": "Package"}
for y, (ref, f, p, cols) in FA.items():
    reg(ref, C / "fa" / f, f"{y} Ram 1500 Feature Availability (FCA/Stellantis media sheet)", S3 + f, "oem_spec_sheet")
    ls = layout_lines(ref, p)
    seen = defaultdict(lambda: defaultdict(list))
    srcs = {}
    for i, l in enumerate(ls):
        m = SIZE.search(l)
        if not m or "Spare" in l:
            continue
        marks = re.findall(r"(?:(?<=\s)|^)([SOP]|—)(?=\s|$)", l[m.end():])
        full = l
        if len(marks) != len(cols):  # description wrapped: the marks sit on the next line
            marks = re.findall(r"(?:(?<=\s)|^)([SOP]|—)(?=\s|$)", ls[i + 1])
            full = l + " " + ls[i + 1]
        if len(marks) != len(cols):
            raise SystemExit(f"{y}: {len(marks)} marks for {len(cols)} columns in {l!r}")
        size = m.group(1)
        for t, k in zip(cols, marks):
            if k != "—" and t not in seen[(size, m.group(2))][k]:
                seen[(size, m.group(2))][k].append(t)
        srcs.setdefault((size, m.group(2)), []).append(cite(ref, p, re.escape(full), [size]))
    for (size, lr), ks in seen.items():
        rec = {"field": "tires", "years": [y, y], "trim": "; ".join(f"{LEG[k]}: {', '.join(ks[k])}" for k in "SOP" if ks.get(k))[:190], "size": size}
        if lr: rec["load_speed"] = f"load range {lr}"
        rec["src"] = srcs[(size, lr)]
        R.append(rec)

for y in range(2005, 2027):
    if y in FA:
        continue
    make = "dodge-ram-1500" if y <= 2010 else "ram-1500"
    name = "Dodge Ram 1500" if y <= 2010 else "Ram 1500"
    DOCS[f"tp{y}"] = {"doc": f"TirePressure.com: {y} {name} Tire Pressure", "url": f"https://tirepressure.com/{y}-{make}-tire-pressure",
                      "type": "third_party_reference", "accessed": ACC}
    for row in tp_rows(C / "tp" / f"{y}.html"):
        R.append({"field": "tires", "years": [y, y], "trim": row["trims"][:150], "size": row["size"],
                  "src": [{"ref": f"tp{y}", "quote": row["text"][:200]}]})
    if 2019 <= y <= 2024:
        DOCS[f"tpc{y}"] = {"doc": f"TirePressure.com: {y} Ram 1500 Classic Tire Pressure", "url": f"https://tirepressure.com/{y}-ram-1500-classic-tire-pressure",
                           "type": "third_party_reference", "accessed": ACC}
        for row in tp_rows(C / "tp" / f"c{y}.html"):
            R.append({"field": "tires", "years": [y, y], "trim": ("1500 Classic: " + row["trims"])[:150], "size": row["size"],
                      "src": [{"ref": f"tpc{y}", "quote": row["text"][:200]}]})

(ROOT / "data/manuals/ram").mkdir(exist_ok=True)
dump(str(ROOT / "data/manuals/ram/1500.yaml"), "ram/1500", R)
print("skipped (engine not in EPA list for that year):", sorted(set(SKIPPED)))
cov = defaultdict(set)
for r in R:
    cov[r["field"]].add(r["years"][0])
for f, ys in cov.items():
    print(f, sorted(ys), "gaps:", sorted(set(range(2005, 2027)) - ys))
