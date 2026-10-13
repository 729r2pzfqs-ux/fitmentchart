"""GM 2005-2010 owner-manual trailer tables -> rows with engine label on the same line."""
import re, subprocess, sys
def rows(pdf, pages):
    out = []
    for page in pages:
        t = subprocess.run(["pdftotext", "-layout", "-f", str(page), "-l", str(page), pdf, "-"],
                           capture_output=True, text=True).stdout
        section = None
        for line in t.split("\n"):
            s = line.strip()
            h = re.match(r"^([CK])[- ]?1500\b(?! HD)(.*)$", s) or re.match(r"^1500 Series (2WD|4WD)\b(.*)$", s)
            if h:
                sec = re.split(r"\s{2,}", s)[0]
                section = re.sub(r"\s*\((?:[a-z]|\w)\)\s*$|\*+$", "", sec).strip(); continue
            if re.match(r"^([CK])[- ]?(2500|3500)|^[CK][- ]?1500 HD|^C/K|^(2500|3500|1500 HD)\b.*Series|^\d{4} Series", s):
                section = None; continue
            if not section or " HD" in section:
                continue
            m = re.match(r"^((?:\d{4}|\d\.\dL?)\s?V[68].*?|Vortec.*?\d\.\dL?\s?V[68].*?)\s{2,}(\d\.\d\d)\s+(\d{1,2},\d{3})\s*lbs.*?(\d{1,2}[, ]\d{3})\s*lbs", s)
            if m and not re.search(r"Fifth|Gooseneck", m.group(1), re.I):
                out.append({"page": page, "section": section, "engine": m.group(1).strip(), "axle": m.group(2),
                            "max": int(m.group(3).replace(",", "")), "gcwr": int(m.group(4).replace(",", "").replace(" ", "")),
                            "line": re.sub(r"\s+", " ", s)})
    return out
if __name__ == "__main__":
    pdf = sys.argv[1]; pages = range(int(sys.argv[2]), int(sys.argv[3]) + 1)
    for r in rows(pdf, pages):
        print(f"p.{r['page']} | {r['section'][:42]:42s} | {r['engine'][:22]:22s} | {r['axle']} | {r['max']:>6} | {r['gcwr']:>6}")
