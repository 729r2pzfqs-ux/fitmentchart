"""GM 2022+ trailering guides/charts: (engine, GCWR, max conventional) triples per line -> max per engine."""
import re, subprocess
ENG = r"(TurboMax[®™]?|2\.7L Turbo[A-Za-z®]*|[56]\.[23]L (?:EcoTec3®? ?)?V8(?: \(ZR2\))?|Duramax®? ?3\.0L ?I-?6(?: Turbo-Diesel)?(?: \(ZR2\))?)"
TRIP = re.compile(ENG + r"\s{1,40}(\d{2},\d{3})\s{1,40}(\d{1,2},\d{3})(?!\d)")
def rows(pdf, page):
    t = subprocess.run(["pdftotext", "-layout", "-f", str(page), "-l", str(page), pdf, "-"], capture_output=True, text=True).stdout
    out = []
    for line in t.split("\n"):
        for m in TRIP.finditer(line):
            g, mx = int(m.group(2).replace(",", "")), int(m.group(3).replace(",", ""))
            if mx < g:
                out.append({"engine": re.sub(r"\s+", " ", m.group(1)).strip(), "gcwr": g, "max": mx, "text": re.sub(r"\s+", " ", m.group(0))})
    return out
def best(pdf, pages):
    b = {}
    for p in pages:
        for r in rows(pdf, p):
            zr2 = " (ZR2)" if "ZR2" in r["engine"] else ""
            k = "2.7L TurboMax" if r["engine"].startswith(("TurboMax", "2.7L")) else \
                "5.3L EcoTec3 V8" if "5.3L" in r["engine"] else "6.2L EcoTec3 V8" if "6.2L" in r["engine"] else \
                "Duramax 3.0L I-6 Turbo-Diesel" if "Duramax" in r["engine"] else r["engine"]
            k += zr2
            if k not in b or r["max"] > b[k]["max"]:
                b[k] = {**r, "page": p, "key": k}
    return b
if __name__ == "__main__":
    import sys
    for k, r in best(sys.argv[1], [int(x) for x in sys.argv[2:]]).items():
        print(f"{k:32s} gcwr={r['gcwr']:>6} max={r['max']:>6} p.{r['page']} | {r['text']}")
