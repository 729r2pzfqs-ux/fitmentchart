"""Parse GM trailering-guide 'SILVERADO 1500 ... TRAILER WEIGHT RATINGS' tables -> rows."""
import re, subprocess, sys
def rows(pdf, page):
    t = subprocess.run(["pdftotext", "-layout", "-f", str(page), "-l", str(page), pdf, "-"],
                       capture_output=True, text=True).stdout
    out, pending = [], ""
    for line in t.split("\n"):
        s = line.strip()
        m = re.match(r"^(.*?[A-Za-z].*?)\s{2,}(\d\.\d\d)\s*\d?\s{2,}(\d{1,2},\d{3})\s+(.*)$", s)
        if m:
            label = (pending + " " + m.group(1)).strip()
            vals = re.findall(r"\d{1,2},\d{3}|—|-(?=\s|$)", m.group(4))
            nums = [int(v.replace(",", "")) for v in vals if v[0].isdigit()]
            out.append({"label": re.sub(r"\s+", " ", label), "axle": m.group(2),
                        "gcwr": int(m.group(3).replace(",", "")), "vals": nums, "line": s})
            pending = ""
        elif re.match(r"^[A-Za-z0-9].{3,60}$", s) and re.search(r"V8|V6|Turbo|L4|Diesel|Duramax|Vortec|EcoTec", s) and not re.search(r"AXLE|GCWR", s):
            pending = s
        else:
            if not re.search(r"and Max|Package|NHT|Trail", s):
                pending = ""
    return out
if __name__ == "__main__":
    for r in rows(sys.argv[1], int(sys.argv[2])):
        print(f"{r['label'][:45]:45s} axle={r['axle']} gcwr={r['gcwr']:>6} max={max(r['vals']) if r['vals'] else None} vals={r['vals']}")
