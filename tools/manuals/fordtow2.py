"""Ford RV & Trailer Towing Guide -> F-150 conventional-towing max per engine (state machine over lines)."""
import re, subprocess, sys
NUM = re.compile(r"(\d{1,2},\d{3})((?:\(\d+\))*)")
OTHER = re.compile(r"F-250|F-350|F-450|SUPER DUTY|RANGER|EXPEDITION|EXPLORER|MAVERICK|TRANSIT|E-SERIES|ECONOLINE|"
                   r"BRONCO|NAVIGATOR|LIGHTNING|ESCAPE|EDGE|FLEX|MOTORHOME|STRIPPED|F-53|F-59|CUTAWAY|MARK LT|SPORT TRAC", re.I)
def lines(pdf):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    for p in range(1, n + 1):
        t = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), pdf, "-"], capture_output=True, text=True).stdout
        yield p, None  # page break marker
        for l in t.split("\n"):
            yield p, l
        PAGES[p] = t
PAGES = {}
FORCE = set()  # pages known (by reading) to be F-150 tables whose heading text lacks "F-150"
def parse(pdf, force=()):
    FORCE.clear(); FORCE.update(force)
    mode, recent, cur, axle = None, [], None, None
    best = {}
    page_has_f150 = False
    header_seen = False
    for p, line in lines(pdf):
        if line is None:
            t = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), pdf, "-"], capture_output=True, text=True).stdout
            page_has_f150 = bool(re.search(r"F-150", t)) or p in FORCE
            if not page_has_f150:
                mode = None
            header_seen = False
            continue
        s = line.strip()
        recent = (recent + [s])[-4:]
        ctx = " ".join(recent)
        up = s.upper()
        if re.search(r"5TH.WHEEL|FIFTH.WHEEL|GOOSENECK", up) and not re.search(r"CONVENTIONAL", up):
            if re.search(r"TOWING|TRAILER WEIGHT", up): mode = None
        if re.search(r"CONVENTIONAL", up) and (re.search(r"F-150", ctx) or p in FORCE) \
                and not OTHER.search(ctx) and not re.search(r"HYBRID", ctx, re.I) and not re.search(r"\d,\d{3}", s):
            mode, cur, header_seen = "conv", None, False
            continue
        if re.search(r"GCWR", up):
            header_seen = True
        if mode and OTHER.search(s) and re.search(r"TOWING|PICKUP|CONVENTIONAL|^\S", up) and len(s) < 80 and not re.search(r"\d,\d{3}", s):
            mode = None
        if mode != "conv" or not header_seen:
            continue
        if re.match(r"^\s*\d\.\dL\b", line):
            m = re.match(r"^\s*(\d\.\dL\b.*?)\s+(\d\.\d\d(?:/\d\.\d\d)?)\s", line)
            cur = re.sub(r"\s+", " ", (m.group(1) if m else re.split(r"\s{2,}", s)[0])).strip()
            cur = re.sub(r"(\s|\.)\d$|\(\d\)$", r"\1", cur).rstrip(". ").strip()  # trailing footnote marker
            axle = m.group(2) if m else None
        elif re.match(r"^\s*(\d\.\d\d(?:/\d\.\d\d)?)\s+\d", line):
            axle = re.match(r"^\s*(\d\.\d\d(?:/\d\.\d\d)?)", line).group(1)
        if not cur:
            continue
        nums = NUM.findall(line)
        if len(nums) < 2:
            continue
        gcwr = int(nums[0][0].replace(",", ""))
        for v, fn in nums[1:]:
            val = int(v.replace(",", ""))
            if val >= gcwr or val < 1000:
                continue
            b = best.get(cur)
            if not b or val > b["max"]:
                same_line_axle = re.match(r"^\s*(?:\d\.\dL\b.*?\s+)?(\d\.\d\d(?:/\d\.\d\d)?)\s+\d", line)
                best[cur] = {"page": p, "engine": cur, "axle": same_line_axle.group(1) if same_line_axle else None,
                             "gcwr": gcwr, "max": val, "fn": fn, "line": re.sub(r"\s+", " ", s)}
    return list(best.values())
if __name__ == "__main__":
    for r in parse(sys.argv[1], [int(x) for x in sys.argv[2:]]):
        print(f"p.{r['page']:>2} {r['engine'][:34]:34s} axle={str(r['axle']):9s} gcwr={r['gcwr']:>6} max={r['max']:>6}{r['fn']}")
