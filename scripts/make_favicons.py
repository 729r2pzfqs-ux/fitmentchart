#!/usr/bin/env python3
"""Generate the favicon pack for fitmentchart.com.

The mark is a wheel hub seen face-on: an orange rim ring on the navy header
colour, a white hub with five lug holes around the center bore (a bolt
pattern). At 16 and 32 px the lug holes and bore turn to mush, so those sizes
are rendered from a bolder variant with bigger lugs and no bore ring.

Output lands in favicon/ and is committed; build.py copies it to the site
root. Only re-run when the icon changes. Needs rsvg-convert and ImageMagick
(brew install librsvg imagemagick):

    python3 scripts/make_favicons.py
"""
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "favicon"
NAVY, ORANGE, WHITE = "#14213d", "#e85d04", "#ffffff"


def svg(small: bool = False, full_bleed: bool = False) -> str:
    bg = (f'<rect width="512" height="512" fill="{NAVY}"/>' if full_bleed
          else f'<rect width="512" height="512" rx="104" fill="{NAVY}"/>')
    ring_r, ring_w = (176, 56) if small else (180, 40)
    hub_r = 118 if small else 128
    lug_pcd, lug_r = (66, 26) if small else (78, 20)
    lugs = "".join(
        f'<circle cx="{256 + lug_pcd * math.sin(2 * math.pi * i / 5):.1f}" '
        f'cy="{256 - lug_pcd * math.cos(2 * math.pi * i / 5):.1f}" r="{lug_r}" fill="{NAVY}"/>'
        for i in range(5))
    bore = "" if small else f'<circle cx="256" cy="256" r="26" fill="none" stroke="{NAVY}" stroke-width="12"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">{bg}'
            f'<circle cx="256" cy="256" r="{ring_r}" fill="none" stroke="{ORANGE}" stroke-width="{ring_w}"/>'
            f'<circle cx="256" cy="256" r="{hub_r}" fill="{WHITE}"/>{lugs}{bore}</svg>\n')


def png(src: Path, size: int, dest: Path) -> None:
    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), "-o", str(dest), str(src)], check=True)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / "favicon.svg").write_text(svg())
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "small.svg").write_text(svg(small=True))
        (t / "bleed.svg").write_text(svg(full_bleed=True))
        for size in (16, 32, 48):
            png(t / "small.svg" if size < 48 else OUT / "favicon.svg", size, t / f"{size}.png")
        shutil.copy(t / "16.png", OUT / "favicon-16x16.png")
        shutil.copy(t / "32.png", OUT / "favicon-32x32.png")
        subprocess.run(["magick", str(t / "16.png"), str(t / "32.png"), str(t / "48.png"), str(OUT / "favicon.ico")], check=True)
        # iOS applies its own rounded mask, so the touch icon is full-bleed
        png(t / "bleed.svg", 180, OUT / "apple-touch-icon.png")
    png(OUT / "favicon.svg", 192, OUT / "favicon-192.png")
    png(OUT / "favicon.svg", 512, OUT / "favicon-512.png")
    (OUT / "site.webmanifest").write_text(json.dumps({
        "name": "FitmentChart", "short_name": "FitmentChart",
        "icons": [{"src": "/favicon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "/favicon-512.png", "sizes": "512x512", "type": "image/png"}],
        "theme_color": NAVY, "background_color": "#f7f8fa", "display": "browser"}, indent=2) + "\n")
    for p in sorted(OUT.iterdir()):
        print(f"{p.name:24s} {p.stat().st_size:7d} bytes")


if __name__ == "__main__":
    main()
