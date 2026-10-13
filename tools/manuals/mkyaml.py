"""Helpers for building data/manuals YAML with verified verbatim quotes.

cite(docid, page, regex) -> {'ref', 'page', 'quote'} where quote is the text the
regex matched on that PDF page (whitespace collapsed). Raises if not found, so a
record can never cite a page that doesn't contain its value.
"""
import re, subprocess, functools, yaml

DOCS = {}   # docid -> {'pdf': path, 'doc':..., 'url':..., 'type':...}

@functools.lru_cache(maxsize=None)
def page_text(pdf, page, raw=False):
    mode = {False: ["-layout"], True: [], "raw": ["-raw"]}[raw]
    args = ["pdftotext", "-f", str(page), "-l", str(page)] + mode + [pdf, "-"]
    return re.sub(r"\s+", " ", subprocess.run(args, capture_output=True, text=True).stdout)

def cite(docid, page, pattern, must=()):
    pdf = DOCS[docid]["pdf"]
    for raw in (False, True, "raw"):
        m = re.search(pattern, page_text(pdf, page, raw), re.I)
        if m:
            q = m.group(0).strip()[:200]
            for v in must:
                if str(v) not in q:
                    raise SystemExit(f"value {v!r} not in quote {q!r} ({docid} p.{page})")
            return {"ref": docid, "page": page, "quote": q}
    raise SystemExit(f"pattern {pattern!r} not found on {docid} p.{page}")

def dump(path, slug, records):
    used = sorted({s["ref"] for r in records for s in r["src"]})
    out = {"slug": slug,
           "sources": {k: {kk: v for kk, v in DOCS[k].items() if kk != "pdf"} for k in used},
           "records": records}
    class D(yaml.SafeDumper):
        pass
    D.add_representer(list, lambda d, v: d.represent_sequence("tag:yaml.org,2002:seq", v,
                      flow_style=all(not isinstance(x, (dict, list)) for x in v)))
    with open(path, "w") as f:
        f.write(f"# Generated from OEM documents; every quote verified against the cited PDF page.\n")
        yaml.dump(out, f, Dumper=D, sort_keys=False, allow_unicode=True, width=120)
    print(f"wrote {path}: {len(records)} records, {len(used)} documents")
