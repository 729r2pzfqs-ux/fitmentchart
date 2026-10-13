# Owner's-manual spec files (input to pipeline step 05)

There is one YAML file per model: `data/manuals/<make>/<model>.yaml`.

- These files hold the specs no open dataset covers: towing, tires, oil, battery and wipers.
- Every value is copied from a document someone can open and check. Nothing comes from memory, and nothing is estimated.
- If no source gives a value, leave it out. QA reports the gap.

Step 05 validates the file and expands each record to the model years it covers. It writes the result to `data/sources/manuals/<make>/<model>.json`, and step 07 merges that into `data/models/`.

## File shape

```yaml
slug: toyota/tacoma

sources:                       # documents cited by the records below
  om2019:
    doc: "2019 Toyota Tacoma Owner's Manual (OM04011U)"
    url: https://www.toyota.com/t3Portal/document/om-s/OM04011U/pdf/OM04011U.pdf
    type: oem_manual           # oem_manual | oem_towing_guide | oem_spec_sheet | oem_parts_catalog | aftermarket_fitment
    accessed: 2026-10-13

records:
  - field: oil
    years: [2019, 2019]        # inclusive; only years this source explicitly covers
    displacement_l: 3.5        # ties the record to an engine (matches engines[].displacement_l)
    engine: "3.5L V6 2GR-FKS"  # free text as printed
    condition: "with towing package"  # optional: when capacity differs by drive/package
    grade: "0W-20"
    capacity_qt: 6.2           # with filter change
    capacity_l: 5.9
    src: [{ref: om2019, page: 560, quote: "With filter 6.2 qt. (5.9 L, 5.2 Imp. qt.)"}]

  - field: towing
    years: [2019, 2019]
    displacement_l: 3.5
    drive: 4WD                 # 2WD | 4WD | AWD
    cab: Double Cab            # as printed, optional
    bed: "5 ft"                # optional
    trim: "TRD Off-Road"       # optional
    max_lb: 6400               # max trailer weight
    tongue_lb: 640             # optional
    gcwr_lb: 11360             # optional
    package: "Tow Package"     # equipment the rating requires, if the source says so
    src: [...]

  - field: tires
    years: [2019, 2019]
    trim: "SR, SR5"            # as printed
    size: "P245/75R16"
    load_speed: "109S"         # optional
    src: [...]

  - field: battery
    years: [2019, 2019]
    displacement_l: 3.5        # optional, if it varies by engine
    group: "24F"               # BCI group size
    cca: 582                   # optional
    src: [...]

  - field: wipers
    years: [2019, 2019]
    driver_in: 26
    passenger_in: 16
    rear_in: null              # omit or null when the vehicle has no rear wiper
    src: [...]
```

## Rules

- `years` may only span a range when the cited document itself covers that range, for example a multi-year towing guide or a manual stating "2016-2019". A 2019 manual supports 2019 only.
- Each `src` entry needs `ref` (a key in `sources`), plus `page` when the source is a PDF, plus a short verbatim `quote` (at most 200 characters) that shows the value.
- Prefer OEM documents: owner's manuals, OEM towing guides and OEM spec sheets. Use an aftermarket fitment lookup (a battery or wiper maker's catalogue) only when no OEM document gives the value. Mark it `type: aftermarket_fitment`.
- Owner's manuals rarely list battery group or wiper lengths, so those two usually come from fitment lookups.
- Units: pounds, US quarts and inches. Use the numbers as printed. Don't convert unless the source only gives metric; in that case write the metric value in the quote.
