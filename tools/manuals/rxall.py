import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from rx import fetch
year, make, model = sys.argv[1:4]
out = sys.argv[4]
u, pos, x = fetch(year, make, model)
import re
quotes = {k: re.search(rf"Position: {k} Length \(in\.\): \d+\"", x).group(0) for k in pos}
json.dump({"url": u, "year": int(year), "make": make, "model": model,
           "positions": {k: sorted(v) for k, v in pos.items()}, "quotes": quotes,
           "vehicle": (re.search(r"My Vehicle ([^:]{0,60}) FIND", x) or [None, None])[1]}, open(out, "w"))
