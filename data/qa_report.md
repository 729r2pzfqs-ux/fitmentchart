# QA report

Generated 2026-10-14.

**5 models**: 0 errors, 86 warnings, 16 coverage gaps.

## Coverage (model-years with a value)

| model | years | engines | towing | wheel | tires | battery | wipers | oil | dims | nhtsa |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| chevrolet/silverado-1500 | 22 | 22/22 | 18/22 | 22/22 | 22/22 | 22/22 | 22/22 | 21/22 | 22/22 | 22/22 |
| ford/f-150 | 22 | 22/22 | 21/22 | 22/22 | 22/22 | 22/22 | 22/22 | 16/22 | 22/22 | 22/22 |
| honda/civic | 22 | 22/22 | 15/22 | 17/22 | 18/22 | 19/22 | 22/22 | 15/22 | 22/22 | 22/22 |
| jeep/wrangler | 22 | 22/22 | 14/22 | 22/22 | 12/22 | 22/22 | 21/22 | 15/22 | 22/22 | 22/22 |
| toyota/tacoma | 22 | 22/22 | 17/22 | 22/22 | 17/22 | 22/22 | 22/22 | 17/22 | 22/22 | 22/22 |
| **all** | | **100%** | **77%** | **95%** | **82%** | **97%** | **99%** | **76%** | **100%** | **100%** |

## Detail

| model | engines w/ HP | wheel basis | OE wheel years | NCAP-rated years | recalls | complaints |
|---|---:|---|---:|---:|---:|---:|
| chevrolet/silverado-1500 | 84/97 | exact 10, generation 12 | 9 | 22 | 167 | 15452 |
| ford/f-150 | 89/91 | exact 16, generation 6 | 16 | 22 | 239 | 22539 |
| honda/civic | 77/77 | exact 10, generation 7, missing 5 | 10 | 16 | 124 | 11285 |
| jeep/wrangler | 54/54 | exact 11, generation 11 | 11 | 22 | 184 | 14845 |
| toyota/tacoma | 44/44 | exact 10, generation 12 | 10 | 21 | 132 | 5613 |

## Errors (0)

None.

## Warnings (86)

- `chevrolet/silverado-1500` 2005 **engines**: 6.0L 8-cyl: no rated HP in EPA test-car data
- `chevrolet/silverado-1500` 2007 **engines**: 5.3L 8-cyl hybrid: no rated HP in EPA test-car data
- `chevrolet/silverado-1500` 2009 **engines**: 4.8L 8-cyl: HP matched by model name only [270]
- `chevrolet/silverado-1500` 2009 **engines**: 6.2L 8-cyl: no rated HP in EPA test-car data
- `chevrolet/silverado-1500` 2009 **engines**: 6.0L 8-cyl hybrid: no rated HP in EPA test-car data
- `chevrolet/silverado-1500` 2010 **engines**: 4.3L 6-cyl: no rated HP in EPA test-car data
- `chevrolet/silverado-1500` 2010 **engines**: 4.8L 8-cyl: no rated HP in EPA test-car data
- `chevrolet/silverado-1500` 2010 **engines**: 5.3L 8-cyl: no rated HP in EPA test-car data
- `chevrolet/silverado-1500` 2010 **engines**: 6.2L 8-cyl: no rated HP in EPA test-car data
- `chevrolet/silverado-1500` 2010 **engines**: 6.0L 8-cyl hybrid: no rated HP in EPA test-car data
- `chevrolet/silverado-1500` 2011 **engines**: 6.0L 8-cyl hybrid: no rated HP in EPA test-car data
- `chevrolet/silverado-1500` 2012 **engines**: 4.8L 8-cyl: HP matched by model name only [295]
- `chevrolet/silverado-1500` 2012 **engines**: 6.2L 8-cyl: HP matched by model name only [403]
- `chevrolet/silverado-1500` 2012 **engines**: 6.0L 8-cyl hybrid: no rated HP in EPA test-car data
- `chevrolet/silverado-1500` 2013 **engines**: 4.8L 8-cyl: HP matched by model name only [295]
- `chevrolet/silverado-1500` 2013 **engines**: 5.3L 8-cyl: HP matched by model name only [320]
- `chevrolet/silverado-1500` 2013 **engines**: 6.0L 8-cyl hybrid: no rated HP in EPA test-car data
- `chevrolet/silverado-1500` 2014 **engines**: 5.3L 8-cyl: no rated HP in EPA test-car data
- `chevrolet/silverado-1500` 2014 **engines**: 6.2L 8-cyl: HP matched by model name only [425]
- `chevrolet/silverado-1500` 2015 **engines**: 5.3L 8-cyl: HP matched by model name only [345]
- `chevrolet/silverado-1500` 2018 **engines**: 5.3L 8-cyl: HP matched by model name only [345]
- `chevrolet/silverado-1500` 2019 **engines**: 6.2L 8-cyl: HP matched by model name only [425]
- `chevrolet/silverado-1500` 2019 **battery**: 3.0L does not match any EPA engine this year [2.7, 4.3, 5.3, 6.2]
- `chevrolet/silverado-1500` 2024 **engines**: 6.2L 8-cyl: HP matched by model name only [420]
- `chevrolet/silverado-1500` 2025 **engines**: 6.2L 8-cyl: HP matched by model name only [420]
- `ford/f-150` 2005 **engines**: 4.6L 8-cyl: HP matched by model name only [231]
- `ford/f-150` 2005 **oil**: 4.2L V6: oil spec from a third-party reference only
- `ford/f-150` 2005 **oil**: 4.6L V8: oil spec from a third-party reference only
- `ford/f-150` 2005 **oil**: 5.4L V8: oil spec from a third-party reference only
- `ford/f-150` 2006 **engines**: 4.6L 8-cyl: HP matched by model name only [231]
- `ford/f-150` 2006 **oil**: 4.2L V6: oil spec from a third-party reference only
- `ford/f-150` 2006 **oil**: 4.6L V8: oil spec from a third-party reference only
- `ford/f-150` 2006 **oil**: 5.4L V8: oil spec from a third-party reference only
- `ford/f-150` 2007 **wheel**: inferred across the generation from special-trim rows only: Ford F-150 Foose Edition 2008, Ford F150 Harley Davidson 2006, Ford King Ranch F150 SuperCrew 2005
- `ford/f-150` 2007 **oil**: 4.2L V6: oil spec from a third-party reference only
- `ford/f-150` 2007 **oil**: 4.6L V8: oil spec from a third-party reference only
- `ford/f-150` 2007 **oil**: 5.4L V8: oil spec from a third-party reference only
- `ford/f-150` 2008 **oil**: 4.2L V6: oil spec from a third-party reference only
- `ford/f-150` 2008 **oil**: 4.6L V8: oil spec from a third-party reference only
- `ford/f-150` 2008 **oil**: 5.4L V8: oil spec from a third-party reference only
- `ford/f-150` 2009 **oil**: 4.6L V8: oil spec from a third-party reference only
- `ford/f-150` 2009 **oil**: 5.4L V8: oil spec from a third-party reference only
- `ford/f-150` 2010 **oil**: 4.6L V8: oil spec from a third-party reference only
- `ford/f-150` 2010 **oil**: 5.4L V8: oil spec from a third-party reference only
- `ford/f-150` 2011 **engines**: 3.7L 6-cyl: HP matched by model name only [275]
- `ford/f-150` 2011 **oil**: 3.7L V6: oil spec from a third-party reference only
- `ford/f-150` 2011 **oil**: 6.2L V8: oil spec from a third-party reference only
- `ford/f-150` 2011 **oil**: 5.0L V8: oil spec from a third-party reference only
- `ford/f-150` 2012 **wheel**: inferred across the generation from special-trim rows only: Ford F-150 FX4 2009, Ford F-150 Harley-Davidson 2011, Ford F-150 Platinum 2009, Ford F-150 SFE 2009, Ford F-150 STX SuperCrew 2014, Ford F-150 SVT Raptor R 2010, Ford F-150 SVT Raptor Special Edition 2014, Ford F-150 SVT Raptor SuperCrew 2011
- `ford/f-150` 2012 **engines**: 3.7L 6-cyl: HP matched by model name only [275]
- `ford/f-150` 2012 **engines**: 5.0L 8-cyl: HP matched by model name only [360]
- `ford/f-150` 2012 **oil**: 3.7L V6: oil spec from a third-party reference only
- `ford/f-150` 2012 **oil**: 6.2L V8: oil spec from a third-party reference only
- `ford/f-150` 2012 **oil**: 5.0L V8: oil spec from a third-party reference only
- `ford/f-150` 2013 **wheel**: inferred across the generation from special-trim rows only: Ford F-150 FX4 2009, Ford F-150 Harley-Davidson 2011, Ford F-150 Platinum 2009, Ford F-150 SFE 2009, Ford F-150 STX SuperCrew 2014, Ford F-150 SVT Raptor R 2010, Ford F-150 SVT Raptor Special Edition 2014, Ford F-150 SVT Raptor SuperCrew 2011
- `ford/f-150` 2013 **engines**: 5.0L 8-cyl: HP matched by model name only [360]
- `ford/f-150` 2013 **oil**: 3.7L V6: oil spec from a third-party reference only
- `ford/f-150` 2013 **oil**: 6.2L V8: oil spec from a third-party reference only
- `ford/f-150` 2013 **oil**: 5.0L V8: oil spec from a third-party reference only
- `ford/f-150` 2014 **engines**: 5.0L 8-cyl: HP matched by model name only [360]
- `ford/f-150` 2014 **oil**: 3.7L V6: oil spec from a third-party reference only
- `ford/f-150` 2014 **oil**: 6.2L V8: oil spec from a third-party reference only
- `ford/f-150` 2014 **oil**: 5.0L V8: oil spec from a third-party reference only
- `ford/f-150` 2015 **engines**: 2.7L 6-cyl turbo: HP matched by model name only [325]
- `ford/f-150` 2015 **engines**: 3.5L 6-cyl: HP matched by model name only [282]
- `ford/f-150` 2015 **oil**: 5.0L V8: oil spec from a third-party reference only
- `ford/f-150` 2015 **oil**: 3.5L Ti-VCT V6 (naturally aspirated): oil spec from a third-party reference only
- `ford/f-150` 2016 **oil**: 5.0L V8: oil spec from a third-party reference only
- `ford/f-150` 2016 **oil**: 3.5L Ti-VCT V6 (naturally aspirated): oil spec from a third-party reference only
- `ford/f-150` 2017 **oil**: 5.0L V8: oil spec from a third-party reference only
- `ford/f-150` 2017 **oil**: 3.5L Ti-VCT V6 (naturally aspirated): oil spec from a third-party reference only
- `ford/f-150` 2018 **engines**: 2.7L 6-cyl turbo: EPA HP [400] rejected, contradicts 2017 and 2019 ([325])
- `ford/f-150` 2021 **engines**: 3.5L 6-cyl turbo hybrid: no rated HP in EPA test-car data
- `ford/f-150` 2026 **engines**: 3.5L 6-cyl turbo hybrid: HP matched by model name only [400]
- `honda/civic` 2006 **wheel**: inferred across the generation from special-trim rows only: Honda Civic Type R Sedan 2007
- `honda/civic` 2008 **wheel**: inferred across the generation from special-trim rows only: Honda Civic Type R Sedan 2007
- `honda/civic` 2009 **wheel**: inferred across the generation from special-trim rows only: Honda Civic Type R Sedan 2007
- `honda/civic` 2010 **wheel**: inferred across the generation from special-trim rows only: Honda Civic Type R Sedan 2007
- `honda/civic` 2011 **wheel**: inferred across the generation from special-trim rows only: Honda Civic Type R Sedan 2007
- `honda/civic` 2012 **engines**: 1.5L 4-cyl hybrid: HP matched by model name only [90, 113]
- `honda/civic` 2013 **engines**: 1.5L 4-cyl hybrid: HP matched by model name only [90, 113]
- `honda/civic` 2014 **engines**: 1.5L 4-cyl hybrid: HP matched by model name only [110]
- `honda/civic` 2015 **engines**: 1.5L 4-cyl hybrid: HP matched by model name only [110]
- `honda/civic` 2016 **wheel**: inferred across the generation from special-trim rows only: Honda Civic Si 2017-2025
- `jeep/wrangler` 2005 **engines**: 2.4L 4-cyl: HP matched by model name only [150]
- `jeep/wrangler` 2006 **engines**: 2.4L 4-cyl: HP matched by model name only [150]

## Gaps (16)

- `chevrolet/silverado-1500`  **towing**: missing for ['2015', '2016', '2018', '2021']
- `chevrolet/silverado-1500`  **oil**: missing for ['2011']
- `ford/f-150`  **towing**: missing for ['2026']
- `ford/f-150`  **oil**: missing for ['2018', '2019', '2022', '2023', '2024', '2025']
- `honda/civic`  **towing**: missing for ['2013', '2015', '2016', '2023', '2024', '2025', '2026']
- `honda/civic`  **wheel**: missing for ['2005', '2012', '2013', '2014', '2015']
- `honda/civic`  **tires**: missing for ['2013', '2015', '2016', '2017']
- `honda/civic`  **battery**: missing for ['2005', '2025', '2026']
- `honda/civic`  **oil**: missing for ['2013', '2015', '2016', '2023', '2024', '2025', '2026']
- `jeep/wrangler`  **towing**: missing for ['2005', '2006', '2007', '2008', '2009', '2010', '2015', '2020']
- `jeep/wrangler`  **tires**: missing for ['2005', '2006', '2007', '2008', '2009', '2010', '2015', '2017', '2018', '2020']
- `jeep/wrangler`  **wipers**: missing for ['2014']
- `jeep/wrangler`  **oil**: missing for ['2006', '2007', '2008', '2009', '2010', '2015', '2020']
- `toyota/tacoma`  **towing**: missing for ['2005', '2006', '2007', '2013', '2026']
- `toyota/tacoma`  **tires**: missing for ['2005', '2006', '2007', '2013', '2026']
- `toyota/tacoma`  **oil**: missing for ['2005', '2006', '2007', '2013', '2026']
