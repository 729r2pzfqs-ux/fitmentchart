import re, html, sys, subprocess, urllib.parse
def fetch(year, make, model):
    u = "https://www.rainx.com/blade-size-finder/?" + urllib.parse.urlencode({"bf-year": year, "bf-make": make, "bf-model": model})
    t = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0", u], capture_output=True, text=True).stdout
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    x = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    pos = {}
    for m in re.finditer(r"Position: (Driver|Passenger|Rear) Length \(in\.\): (\d+)\"", x):
        pos.setdefault(m.group(1), set()).add(int(m.group(2)))
    return u, pos, x
if __name__ == "__main__":
    u, pos, x = fetch(*sys.argv[1:4])
    print(u, {k: sorted(v) for k, v in pos.items()}, "| vehicle:", re.search(r"My Vehicle ([^:]{0,60}) FIND", x).group(1) if re.search(r"My Vehicle ([^:]{0,60}) FIND", x) else "?")
