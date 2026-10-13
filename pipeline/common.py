"""Shared helpers for the pipeline steps: paths, config, cached HTTP, JSON IO."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MODELS_DIR = DATA / "models"
SOURCES_DIR = DATA / "sources"
CACHE_DIR = DATA / "cache"
HTTP_CACHE = CACHE_DIR / "http"
DOWNLOADS = CACHE_DIR / "downloads"

USER_AGENT = "fitmentchart.com data pipeline (+https://fitmentchart.com)"

_session: requests.Session | None = None


def session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers["User-Agent"] = USER_AGENT
    return _session


# --------------------------------------------------------------------------- config

def load_config() -> dict:
    return yaml.safe_load((DATA / "makes.yaml").read_text())


def load_generations() -> dict:
    return yaml.safe_load((DATA / "generations.yaml").read_text())


def year_range(cfg: dict | None = None) -> list[int]:
    cfg = cfg or load_config()
    return list(range(cfg["years"]["start"], cfg["years"]["end"] + 1))


def iter_models(cfg: dict | None = None):
    """Yield (make_cfg, model_cfg, slug) for every configured model."""
    cfg = cfg or load_config()
    for make in cfg["makes"]:
        for model in make["models"]:
            yield make, model, f"{make['slug']}/{model['slug']}"


def matches(rule: dict | None, text: str) -> bool:
    """Apply an {include, exclude} regex rule from makes.yaml to a source string."""
    if not rule or text is None:
        return False
    if not re.search(rule["include"], text, re.I):
        return False
    exc = rule.get("exclude")
    return not (exc and re.search(exc, text, re.I))


def generation_for(slug: str, year: int, gens: dict | None = None) -> list[dict]:
    """All generations covering `year` (two in overlap years)."""
    gens = gens if gens is not None else load_generations()
    out = []
    for g in gens.get(slug, []):
        end = g["end"] if g["end"] is not None else 9999
        if g["start"] <= year <= end:
            out.append(g)
    return out


# --------------------------------------------------------------------------- HTTP

def get_json(url: str, params: dict | None = None, *, refresh: bool = False,
             retries: int = 5, accept_empty: bool = False,
             ok_status: tuple[int, ...] = (200,)) -> dict:
    """GET a JSON endpoint with an on-disk cache and retry/backoff.

    NHTSA endpoints intermittently answer 200 with an empty body when hit in
    quick succession, so an empty/invalid body is treated as retryable.
    `ok_status` lists extra statuses whose JSON body is a valid answer (NHTSA
    recalls answers 400 + {"Count":0,"results":[]} for a name with no recalls).
    """
    req = requests.Request("GET", url, params=params).prepare()
    key = hashlib.sha1(req.url.encode()).hexdigest()
    path = HTTP_CACHE / key[:2] / f"{key}.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text())["body"]

    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            r = session().get(req.url, timeout=60)
            if r.status_code == 404 and accept_empty:
                body = {}
                break
            if r.status_code not in ok_status:
                r.raise_for_status()
            body = r.json()
            break
        except (requests.RequestException, ValueError) as e:
            last_err = e
            time.sleep(1.5 * (2 ** attempt))
    else:
        raise RuntimeError(f"GET failed after {retries} attempts: {req.url}: {last_err}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"url": req.url, "fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "body": body}))
    time.sleep(0.15)  # be polite to government APIs
    return body


def download(url: str, name: str, *, refresh: bool = False, min_bytes: int = 1000,
             headers: dict | None = None) -> Path:
    """Download a file into data/cache/downloads/<name> (cached)."""
    dest = DOWNLOADS / name
    if dest.exists() and dest.stat().st_size >= min_bytes and not refresh:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    h = {"User-Agent": "Mozilla/5.0 (compatible; fitmentchart-pipeline)"}
    h.update(headers or {})
    with session().get(url, stream=True, timeout=300, headers=h) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with tmp.open("wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
    if tmp.stat().st_size < min_bytes:
        raise RuntimeError(f"download too small ({tmp.stat().st_size} B): {url}")
    tmp.replace(dest)
    return dest


# --------------------------------------------------------------------------- IO

def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n")


def read_json(path: Path):
    return json.loads(path.read_text())


def source_path(source: str, slug: str) -> Path:
    return SOURCES_DIR / source / f"{slug}.json"


def model_path(slug: str) -> Path:
    return MODELS_DIR / f"{slug}.json"


def has_flag(flag: str) -> bool:
    return flag in sys.argv[1:]


def log(msg: str) -> None:
    print(msg, flush=True)
