# Data compatibility report — 14 November 2026

The four requested CSVs were read in full before writing adapters. Copies under `data/current/` are text snapshots reconstructed from that complete read; raw measurement columns and notes are retained. They are historical starter inputs, not the latest approved dataset.

## The four requested files

| File | Actual contents | Usable now | Blocks predictive evaluation |
|---|---|---|---|
| `ignis_experiments_starter.csv` | 4 rows; 16 columns; `outcome_type=steady_flame_size`; values 4, 4, 5, 5 cm | Compare Runs, unit checks, metadata display | Wrong target for spread-rate regression; flow direction blank; scientific verification and independence audit absent |
| `ignis_source_manifest_starter.csv` | 1 source; 8 columns; NASA-ICES-2021-266 | Provenance for the transcribed Table 2 rows | Its PSI-98 association is explicitly marked for verification and must not represent all Saffire campaigns |
| `ignis_bass_saffire_candidate_observations.csv` | 23 rows; 18 columns; approximate flow/rate values and working reading envelopes | Provisional exploration, adapter and quality testing | All 23 run IDs blank; 16 BASS rows missing oxygen/pressure/length; all target values digitized; geometry and dependence unresolved |
| `ignis_bass_saffire_source_manifest.csv` | 5 sources; 6 columns | Research starting points | None matches observation source ID `URBAN_2021_ICES_2021_266_FIG10`; review status absent |

The starter's 2×2 comparison changes specimen size and **airflow (20 versus 25 cm/s)**. Oxygen is **21% in all four rows**; pressure is 100 kPa. Do not present this as a 20%/25% oxygen comparison. This statement describes the file, not a fresh re-verification of the underlying paper.

The candidate table has 16 BASS-series rows, four pooled Saffire I/III rows, two Saffire II rows and one Saffire IV row. The adapters rename `campaign`, `flow_magnitude_cm_s_est`, `oxygen_mol_percent`, and `flame_spread_rate_cm_s_est` to canonical fields while retaining every original column under `raw__...`. They never invent IDs, map BASS to BASS-II, or mark records verified. `outcome_type` is normalized from the explicitly supplied spread-rate column definition, not inferred from magnitudes. No working uncertainty value is used as a calibrated error bar or training weight.

## Later Data Research audit checked during this build

Read in full: `ignis_spread_rates_reviewed.csv`, `ignis_evidence_summary.json`, and `ignis_published_spread_rates.csv` from the separate audit. These newer outputs supersede the starter's interpretation; they were not silently merged into modeling data.

- All 23 reviewed figure points still have `approved_for_ml=False` and no verified run IDs. The audit distinguishes 11 probable links from zero confirmed links.
- The source ID is reconciled to NASA-ICES-2021-266 in the newer reviewed file. Thus the source-ID mismatch above is a **starter-specific issue**, not an unresolved claim about the latest audit.
- The audit identifies BASS as PSI-26 and BASS-II as PSI-25; these are distinct investigations. Its reviewed table preserves pooled/unresolved campaign identities.
- Canonical `duct_height_cm` has been cleared. Reference full-duct heights and sample-wall gaps are separated. For BASS the audit records a 7.6 cm full duct reference and 3.8 cm sample-wall gap reference; neither is automatically approved per figure point. Do not train on the starter's unreviewed 3.8 cm height.
- Two numerical Saffire II entries were recovered: 2.1 and 2.6 mm/s, equivalent to 0.21 and 0.26 cm/s. Both remain `approved_for_ml=False`, with header/metadata conflicts and one shared campaign. They may be alternate representations of two plotted points, not two extra independent experiments.
- Nominal versus measured airflow, oxygen and thickness conflicts remain. Candidate atmosphere values must stay separate from confirmed point-level conditions.
- The audit summary explicitly reports `approved_ml_rows: 0`. This package therefore fits **no NASA model**, including the naive baseline, and reports **no NASA predictive accuracy**.

Read-source records for traceability: reviewed rates `libfile_375a651305808191a9aabc4b7e995b37`; summary `libfile_293b007152508191932d4327ca3aaf12`; published rates `libfile_bcd82e96ec248191a0aafda203b2d7de`. These identify the user's audit artifacts, not independent external verification by this build.

## What the data team must supply next

A point/run/phase/specimen crosswalk; defensible dependency clusters; reviewed material identities and spread-regime definitions; actual or clearly designated nominal point-level atmosphere/flow; unambiguous geometry definitions; consistent source IDs and a reviewed source manifest. Preserve unresolved values as missing. Review and resolve conflicting measurements rather than replacing them with convenient constants.

Import into the canonical contract only after this work. Do not map `candidate_run_id` to `run_id`, `conservative_group` to a verified independence claim, or a status containing the word “reviewed” to `verified`. The existing reviewed CSV is an audit artifact, not a fit-ready table.

The fallback is still useful: show evidence, provenance, comparison limitations, missing features, and refusal reasons. Use the seven synthetic figures to demonstrate the engineering workflow, with their visible synthetic labels. No experimental measured-versus-predicted figure is warranted yet.
