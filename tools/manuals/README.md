# Manual-spec builders

These scripts regenerate `data/manuals/<make>/<model>.yaml` from OEM PDFs cached in `data/cache/manuals/` (gitignored).

Run them in this order. The builders rewrite each file, then `add_wipers.py` appends the Rain-X wiper records:

```
python tools/manuals/build_tacoma.py      # toyota.ca owner's manuals (OM… PDFs), year mapping from toyota.ca's manuals API
python tools/manuals/build_silverado.py   # GM owner manuals + GM trailering guides
python tools/manuals/build_f150.py        # Ford RV & Trailer Towing Guides 2005-2025
python tools/manuals/build_wrangler.py    # Mopar owner's manuals
python tools/manuals/build_civic.py       # 2005 Civic owner's manual (Honda techinfo sections)
python tools/manuals/rxrun.py data/cache/rainx   # fetch Rain-X wiper pages (slow; cached)
python tools/manuals/add_wipers.py
python tools/manuals/add_f150_oil.py     # F-150 oil: Ford 2020/2021 tech-spec sheets + f150hub.com (third_party_reference)
python tools/manuals/add_chunk2.py       # F-150 tires/battery/2026 oil (Ford sheets, tirepressure.com), Civic oil 2006-2022 (Honda manuals)
python tools/manuals/add_chunk3.py       # Civic tires (manuals + Honda Info Center), wipers (HondaPartsNow), towing (manuals)
python tools/manuals/add_chunk4.py       # Silverado towing (GM guides/charts 2017, 2022-26), oil (GM TechLink 2021-26), tires (tirepressure.com)
python tools/manuals/add_chunk5.py       # Wrangler towing/tires/oil capacity (FCA/Stellantis spec sheets 2011-26), EcoDiesel grade (manuals)
python tools/manuals/add_battery.py      # battery groups, ALL confidence: low (research note + autopadre.com corroboration)
```

`mkyaml.cite()` is the safety net.
- Every quote is re-extracted from the cited PDF page.
- A build fails if the pattern isn't on that page, or if the value isn't inside the quote.

Download URLs for each PDF are recorded in the YAML `sources` block.
