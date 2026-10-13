"""Step 05 (placeholder): owner's-manual extraction. Not built yet; Phase 0 skips it.

Planned scope: the fields no open dataset covers, all per model-year.
  oil      viscosity, capacity with filter (qt / L), drain interval
  battery  BCI group size, CCA
  wipers   driver / passenger / rear blade length (in)
  tires    OE tire sizes + door-placard pressures
  towing   max trailer weight per engine / drivetrain / cab config

Output contract (step 07 already merges it once files exist):
  data/sources/manuals/<make>/<model>.json
  {"slug": ..., "source": {...},
   "years": {"2019": {"oil": {...}, "battery": {...}, "wipers": {...},
                      "tires": [...], "towing": [...]}}}
Step 07 lets this source set only those five fields.

This script deliberately writes nothing, so those fields stay empty and QA
reports them as coverage gaps instead of showing made-up numbers.
"""
from __future__ import annotations

if __name__ == "__main__":
    print("05_manuals_extract: not implemented yet; oil/battery/wipers/tires/towing stay empty "
          "(QA reports them as gaps)")
