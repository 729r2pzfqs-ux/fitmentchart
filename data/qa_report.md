# QA report

Generated 2026-11-01.

**10 models**: 0 errors, 134 warnings, 37 coverage gaps.

## Coverage (model-years with a value)

| model | years | engines | towing | wheel | tires | battery | wipers | oil | dims | nhtsa |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| chevrolet/silverado-1500 | 22 | 22/22 | 18/22 | 22/22 | 22/22 | 22/22 | 22/22 | 21/22 | 22/22 | 22/22 |
| ford/f-150 | 22 | 22/22 | 21/22 | 22/22 | 22/22 | 22/22 | 22/22 | 16/22 | 22/22 | 22/22 |
| honda/accord | 22 | 22/22 | - | 9/22 | 22/22 | 21/22 | 21/22 | - | 22/22 | 22/22 |
| honda/civic | 22 | 22/22 | 15/22 | 17/22 | 18/22 | 19/22 | 22/22 | 15/22 | 22/22 | 22/22 |
| jeep/wrangler | 22 | 22/22 | 14/22 | 22/22 | 12/22 | 22/22 | 21/22 | 15/22 | 22/22 | 22/22 |
| ram/1500 | 22 | 22/22 | 16/22 | 22/22 | 22/22 | 20/22 | 21/22 | 21/22 | 22/22 | 22/22 |
| tesla/model-3 | 10 | 10/10 | - | 10/10 | 10/10 | - | - | - | 9/10 | 10/10 |
| toyota/camry | 22 | 22/22 | 19/22 | 20/22 | 22/22 | 21/22 | 22/22 | 19/22 | 22/22 | 22/22 |
| toyota/corolla | 22 | 22/22 | 18/22 | 14/22 | 22/22 | 22/22 | 22/22 | 18/22 | 22/22 | 22/22 |
| toyota/tacoma | 22 | 22/22 | 17/22 | 22/22 | 17/22 | 22/22 | 22/22 | 17/22 | 22/22 | 22/22 |
| **all** | | **100%** | **66%** | **86%** | **90%** | **91%** | **93%** | **68%** | **99%** | **100%** |

## Detail

| model | engines w/ HP | wheel basis | OE wheel years | NCAP-rated years | recalls | complaints |
|---|---:|---|---:|---:|---:|---:|
| chevrolet/silverado-1500 | 84/97 | exact 10, generation 12 | 9 | 22 | 167 | 15452 |
| ford/f-150 | 89/91 | exact 16, generation 6 | 16 | 22 | 239 | 22539 |
| honda/accord | 56/56 | exact 5, generation 4, missing 13 | 5 | 15 | 168 | 13835 |
| honda/civic | 77/77 | exact 10, generation 7, missing 5 | 10 | 16 | 124 | 11285 |
| jeep/wrangler | 54/54 | exact 11, generation 11 | 11 | 22 | 184 | 14845 |
| ram/1500 | 80/83 | exact 14, generation 8 | 13 | 22 | 254 | 17601 |
| tesla/model-3 | 0/10 | exact 9, generation 1 | 9 | 7 | 139 | 4385 |
| toyota/camry | 60/62 | exact 7, generation 13, missing 2 | 7 | 15 | 95 | 12659 |
| toyota/corolla | 36/36 | exact 4, generation 10, missing 8 | 4 | 15 | 109 | 9136 |
| toyota/tacoma | 44/44 | exact 10, generation 12 | 10 | 21 | 132 | 5613 |

## Errors (0)

None.

## Warnings (134)

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
- `honda/accord` 2006 **engines**: 3.0L 6-cyl hybrid: HP matched by model name only [253]
- `honda/accord` 2013 **wheel**: inferred across the generation from special-trim rows only: Honda Accord PHEV 2014-2017
- `honda/accord` 2014 **engines**: 2.0L 4-cyl plug-in hybrid: HP matched by model name only [196]
- `honda/accord` 2014 **engines**: 2.0L 4-cyl hybrid: HP matched by model name only [196]
- `honda/accord` 2015 **engines**: 2.0L 4-cyl hybrid: HP matched by model name only [196]
- `honda/accord` 2017 **engines**: 2.0L 4-cyl hybrid: HP matched by model name only [143]
- `honda/accord` 2018 **engines**: 2.0L 4-cyl hybrid: HP matched by model name only [143]
- `honda/accord` 2020 **engines**: 2.0L 4-cyl hybrid: HP matched by model name only [143]
- `honda/accord` 2021 **engines**: 2.0L 4-cyl hybrid: HP matched by model name only [143]
- `honda/accord` 2022 **engines**: 2.0L 4-cyl hybrid: HP matched by model name only [143]
- `honda/accord` 2023 **engines**: 1.5L 4-cyl turbo: HP matched by model name only [192]
- `honda/accord` 2025 **engines**: 1.5L 4-cyl turbo: HP matched by model name only [192]
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
- `ram/1500` 2005 **engines**: 3.7L 6-cyl: HP matched by model name only [215]
- `ram/1500` 2005 **engines**: 5.7L 8-cyl: HP matched by model name only [345]
- `ram/1500` 2005 **engines**: 8.3L 10-cyl: no rated HP in EPA test-car data
- `ram/1500` 2006 **engines**: 3.7L 6-cyl: HP matched by model name only [215]
- `ram/1500` 2006 **engines**: 5.7L 8-cyl: no rated HP in EPA test-car data
- `ram/1500` 2006 **engines**: 8.3L 10-cyl: no rated HP in EPA test-car data
- `ram/1500` 2007 **engines**: 3.7L 6-cyl: HP matched by model name only [215]
- `ram/1500` 2007 **engines**: 5.7L 8-cyl: HP matched by model name only [345]
- `ram/1500` 2012 **engines**: 3.7L 6-cyl: HP matched by model name only [215]
- `tesla/model-3` 2017 **engines**: Electric: no rated HP in EPA test-car data
- `tesla/model-3` 2018 **engines**: Electric: no rated HP in EPA test-car data
- `tesla/model-3` 2019 **engines**: Electric: no rated HP in EPA test-car data
- `tesla/model-3` 2020 **engines**: Electric: no rated HP in EPA test-car data
- `tesla/model-3` 2021 **engines**: Electric: no rated HP in EPA test-car data
- `tesla/model-3` 2022 **engines**: Electric: no rated HP in EPA test-car data
- `tesla/model-3` 2023 **engines**: Electric: no rated HP in EPA test-car data
- `tesla/model-3` 2024 **engines**: Electric: no rated HP in EPA test-car data
- `tesla/model-3` 2025 **engines**: Electric: no rated HP in EPA test-car data
- `tesla/model-3` 2026 **engines**: Electric: no rated HP in EPA test-car data
- `toyota/camry` 2005 **engines**: 3.3L 6-cyl: no rated HP in EPA test-car data
- `toyota/camry` 2006 **engines**: 3.3L 6-cyl: no rated HP in EPA test-car data
- `toyota/camry` 2007 **engines**: 2.4L 4-cyl hybrid: HP matched by model name only [147]
- `toyota/camry` 2008 **wheel**: inferred across the generation from special-trim rows only: Toyota Camry SE 2007
- `toyota/camry` 2008 **engines**: 3.5L 6-cyl: HP matched by model name only [268]
- `toyota/camry` 2008 **engines**: 2.4L 4-cyl hybrid: HP matched by model name only [147]
- `toyota/camry` 2009 **wheel**: inferred across the generation from special-trim rows only: Toyota Camry SE 2007
- `toyota/camry` 2009 **engines**: 2.4L 4-cyl hybrid: HP matched by model name only [147]
- `toyota/camry` 2010 **wheel**: inferred across the generation from special-trim rows only: Toyota Camry SE 2007
- `toyota/camry` 2010 **engines**: 2.4L 4-cyl hybrid: HP matched by model name only [147]
- `toyota/camry` 2011 **wheel**: inferred across the generation from special-trim rows only: Toyota Camry SE 2007
- `toyota/camry` 2011 **engines**: 2.4L 4-cyl hybrid: HP matched by model name only [147]
- `toyota/camry` 2012 **engines**: 2.5L 4-cyl: HP matched by model name only [178]
- `toyota/camry` 2012 **engines**: 3.5L 6-cyl: HP matched by model name only [268]
- `toyota/camry` 2013 **engines**: 2.5L 4-cyl: HP matched by model name only [178]
- `toyota/camry` 2017 **engines**: 2.5L 4-cyl: HP matched by model name only [178]
- `toyota/camry` 2017 **engines**: 3.5L 6-cyl: HP matched by model name only [268]

## Gaps (37)

- `chevrolet/silverado-1500`  **towing**: missing for ['2015', '2016', '2018', '2021']
- `chevrolet/silverado-1500`  **oil**: missing for ['2011']
- `ford/f-150`  **towing**: missing for ['2026']
- `ford/f-150`  **oil**: missing for ['2018', '2019', '2022', '2023', '2024', '2025']
- `honda/accord`  **towing**: no source provides this field yet
- `honda/accord`  **wheel**: missing for ['2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2018', '2019', '2020', '2021', '2022']
- `honda/accord`  **battery**: missing for ['2026']
- `honda/accord`  **wipers**: missing for ['2026']
- `honda/accord`  **oil**: no source provides this field yet
- `honda/civic`  **towing**: missing for ['2013', '2015', '2016', '2023', '2024', '2025', '2026']
- `honda/civic`  **wheel**: missing for ['2005', '2012', '2013', '2014', '2015']
- `honda/civic`  **tires**: missing for ['2013', '2015', '2016', '2017']
- `honda/civic`  **battery**: missing for ['2005', '2025', '2026']
- `honda/civic`  **oil**: missing for ['2013', '2015', '2016', '2023', '2024', '2025', '2026']
- `jeep/wrangler`  **towing**: missing for ['2005', '2006', '2007', '2008', '2009', '2010', '2015', '2020']
- `jeep/wrangler`  **tires**: missing for ['2005', '2006', '2007', '2008', '2009', '2010', '2015', '2017', '2018', '2020']
- `jeep/wrangler`  **wipers**: missing for ['2014']
- `jeep/wrangler`  **oil**: missing for ['2006', '2007', '2008', '2009', '2010', '2015', '2020']
- `ram/1500`  **towing**: missing for ['2005', '2006', '2008', '2009', '2010', '2013']
- `ram/1500`  **battery**: missing for ['2025', '2026']
- `ram/1500`  **wipers**: missing for ['2026']
- `ram/1500`  **oil**: missing for ['2005']
- `tesla/model-3`  **towing**: no source provides this field yet
- `tesla/model-3`  **battery**: no source provides this field yet
- `tesla/model-3`  **wipers**: no source provides this field yet
- `tesla/model-3`  **oil**: no source provides this field yet
- `tesla/model-3`  **dims**: missing for ['2017']
- `toyota/camry`  **towing**: missing for ['2005', '2006', '2007']
- `toyota/camry`  **wheel**: missing for ['2005', '2006']
- `toyota/camry`  **battery**: missing for ['2026']
- `toyota/camry`  **oil**: missing for ['2005', '2006', '2007']
- `toyota/corolla`  **towing**: missing for ['2005', '2006', '2007', '2008']
- `toyota/corolla`  **wheel**: missing for ['2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026']
- `toyota/corolla`  **oil**: missing for ['2005', '2006', '2007', '2008']
- `toyota/tacoma`  **towing**: missing for ['2005', '2006', '2007', '2013', '2026']
- `toyota/tacoma`  **tires**: missing for ['2005', '2006', '2007', '2013', '2026']
- `toyota/tacoma`  **oil**: missing for ['2005', '2006', '2007', '2013', '2026']
