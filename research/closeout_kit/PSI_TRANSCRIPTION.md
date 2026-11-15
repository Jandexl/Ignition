# Selected PSI observations — manual audit transcription

Observed live 2026-11-14. These are source claims, not repaired values. They are not original file downloads or calibrated measurement reanalysis.

## PSI-98 — Saffire I, Version 4

https://psi.nasa.gov/physci/repo/data/investigations/PSI-98

DOI: 10.60555/0t15-1z43. Experimental Table:

| Sample | Material | Thickness (column cm) | Length (column cm) | Width (column cm) | Airflow cm/s | O2 % | Burn s | Direction | Cameras |
|---|---|---|---|---|---|---|---|---|---|
| S1 | SIBAL Fabric | 0.37 | 40.6 | 94 | 20 | 21.5 - 21.7 | 420 | Concurrent | S1C1 / S1C2 |
| S2 | SIBAL Fabric | 0.37 | 40.6 | 94 | 20 | ~21.5 | 70 | Opposed | S2C1 / S2C2 |

Length/width appear swapped against the paper and narrative; thickness unit is unresolved. Keep both raw claims.

## PSI-99 — Saffire II, Version 5

https://psi.nasa.gov/physci/repo/data/investigations/PSI-99

DOI: 10.60555/2chp-m469. Experimental Table:

| Sample | Material cell | Thickness text | Length | Width | Flow | O2 | Burn time | Direction | Cell under `?-g Spread Length` |
|---|---|---|---|---|---|---|---|---|---|
| 2-5 | Cotton-Fiberglass (SIBAL) | 037 mm | 29 cm | 5 cm | 20 cm/s | ~22.1 | 145 s | Concurrent | 2.1 mm/s |
| 2-6 | blank | 037 mm | 29 cm | 5 cm | 20 cm/s | ~22.1 | 115 s | Concurrent | 2.6 mm/s |

Both have 80 W ignition, 9.2 s ignition time and 29 cm microgravity burn length. The 2-6 camera cells display S6C1 and S56C2. Do not repair that second label without the image directory documentation. Paper Table2 supplies the SIBAL material identification for II-6. Rate dimension is inferred from mm/s despite malformed header. The rate's exact averaging interval remains unresolved.

## PSI-100 — Saffire III, Version 4

https://psi.nasa.gov/physci/repo/data/investigations/PSI-100

DOI: 10.60555/040q-4h36. Experimental Table:

| Sample | Material | Thickness | Length | Width | Airflow | Direction | Cameras |
|---|---|---|---|---|---|---|---|
| S1 | SIBAL Fabric | .33 cm | 94 cm | 40.6 cm | 30 cm/s | Concurrent | S1C1 / S1C2 |
| S2 | SIBAL Fabric | .33 cm | 94 cm | 40.6 cm | 30 cm/s | Opposed | S2C1 / S2C2 |

Table2 paper lists 25 cm/s for III-1. Actual-vs-nominal explanation is plausible but not verified. No oxygen column was shown in this table.

## PSI-26 — BASS, Version 4

https://psi.nasa.gov/physci/repo/data/investigations/PSI-26

DOI: 10.60555/58h4-dy80. SIBAL-filtered inventory, all 12 rows:

| Date | GMT | As-run test | Test | Sample | Material |
|---|---|---|---|---|---|
| 3/30/2012 | 90 | 1 | 1 | 4 | SIBAL 2 cm |
| 4/5/2012 | 96 | 4 | 7 | 10 | SIBAL 2 cm |
| 4/5/2012 | 96 | 5 | 8 | 11 | SIBAL 2 cm |
| 5/10/2012 | 131 | 12 | 4 | 12 | SIBAL 2 cm |
| 5/10/2012 | 131 | 13 | 10 | 2 | SIBAL 1 cm |
| 6/28/2012 | 180 | 37 | 5 | 9 | SIBAL 2 cm |
| 6/29/2012 | 181 | 44 | 5b | 9 | SIBAL 2 cm opposed flow |
| 7/3/2012 | 185 | 45 | 6 | 8 | SIBAL 2 cm |
| 7/19/2012 | 201 | 54 | 2 | 5 | SIBAL 2 cm |
| 7/19/2012 | 201 | 55 | 3 | 6 | SIBAL 2 cm |
| 8/9/2012 | 222 | 65 | 11 | 3 | SIBAL 1 cm |
| 8/9/2012 | 222 | 66 | 9 | 7 | SIBAL 2 cm |

This table identifies inventory tests, not numerical spread-rate intervals. Sample9 repeats across two dates/directions. GMT96-T7, GMT96-T8, GMT131-T10 and GMT222-T11 agree with named BASS rows in report Table7.1; this does not prove their Figure10 point assignments.

## PSI-25 — BASS-II, Version 4

https://psi.nasa.gov/physci/repo/data/investigations/PSI-25

DOI: 10.60555/4qc4-de67. Experiment table includes PI, test/date/GMT/sample identifiers, material, flow-restrictor/fan/air readings, imaging counts and gas readings. Initial rows inspected were PMMA films, not the Figure10 SIBAL series. Source columns can be malformed; values were not copied into the 23-point dataset.
