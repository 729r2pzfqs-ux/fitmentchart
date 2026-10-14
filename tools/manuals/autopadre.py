"""Parse autopadre.com battery-size pages: per-year sections -> [(year, trim, code, quote)]."""
import html, re

def text(path):
    t = open(path, encoding="utf-8").read()
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    t = re.sub(r"<(tr|br|p|li|h\d|td|th)[^>]*>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return [l.strip() for l in re.sub(r"[ \t]+", " ", t).split("\n") if l.strip()]

CODE = re.compile(r"^(H\d|T\d|\d{2,3}[A-Z]{0,2}(-\d)?)( \((\d{2,3}R?)\))?$")

def rows(path):
    """Rows from the per-year detail tables ('YYYY Make Model Battery Size(s)' ... metric column)."""
    L = text(path)
    out = []
    i = 0
    while i < len(L):
        m = re.match(r"^(\d{4}) .+ Battery Size\(s\)$", L[i])
        if not m:
            i += 1; continue
        y = int(m.group(1)); i += 1
        while i < len(L) and L[i] in ("Trim", "Battery Size Code", "Battery Size (L X W X H) (Imp.)",
                                      "Battery Size (L X W X H) (Metric)"):
            i += 1
        while i + 3 < len(L) and CODE.match(L[i + 1]) and '"' in L[i + 2] and "cm" in L[i + 3]:
            trim, code = L[i], L[i + 1]
            out.append({"year": y, "trim": trim, "code": code,
                        "quote": f"{y} {trim} {code} {L[i + 2]}"})
            i += 4
    return out
