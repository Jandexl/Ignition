# 1gnition — Independent evidence readiness and real-data feasibility study

**Study date:** 15 November 2026. **Status:** Exploratory analysis **only**; not physical validation, not verified NASA M1/M2 predictive accuracy, not a new experiment.

## What was actually done

1. Opened the project's revised Olson et al. (2023) Table 1 transcription and filtered seven SIBAL published records.
2. Checked for the four SIBAL width × full-duct-height cells: narrow/deep, wide/deep, narrow/shallow, wide/shallow.
3. Opened the team's separate BASS-II NASA/TM-20210011385 Table 5.1 PMMA transcription (43 flow-step rows, 39 rates), keeping each test ID's flow stages together.
4. On these **39 real published but not independently reverified numerical values** from **18 test IDs**, carried out an **exploratory** fixed 5-fold grouped holdout comparison:
   - Mean-only baseline.
   - Ridge with flow speed.
   - Ridge with flow speed, sample width, thickness, and number of burning sides.
5. Calculated out-of-fold MAE/RMSE, plus a post-hoc group bootstrap comparing the mean baseline and geometry-augmented model.

## What this does and does not establish

- It is a useful computational feasibility diagnostic using values transcribed from a NASA-published report.
- The 18 test identifiers are **provisional burn-independence groups** until raw logs confirm them.
- This does **not** test the canonical M1 and M2: the PMMA table lacks stage-specific oxygen and total pressure, two essential M1 conditions, and the geometry features differ from canonical M2.
- PMMA is not SIBAL; **all** rows are opposed flow and BASS-II. There are **no Saffire target-scale holdouts**. Accordingly the results do not validate BASS-to-Saffire transfer.
- These aren't verified NASA telemetry-based remeasurements; original files were not reprocessed, and the transcription still needs manual source-image verification.
- The small performance difference is not statistically decisive; the post-hoc interval includes zero. Do not present it as a validated ML improvement.
- No physical combustion simulation or microgravity experiment was conducted.

## Observed results

| Fixed grouped benchmark | MAE (cm/s) | RMSE (cm/s) |
|---|---:|---:|
| Train-group mean baseline | 0.0024153 | 0.0032303 |
| Flow-only Ridge | 0.0027059 | 0.0033602 |
| Flow + geometry Ridge | 0.0022923 | 0.0029036 |

The MAE reduction of the augmented model relative to the mean baseline is **0.00012295 cm/s** (about **5.1%**) in this *preliminary, unapproved data test*. Post-hoc test-ID resampling gives an approximately **95% interval of -0.0006595 to +0.0009005 cm/s** for the improvement. Zero falls within this interval. This interval is descriptive of grouped resampling of fixed out-of-fold predictions, not a formal confidence interval for a new campaign.

## Physical hypothesis is still unidentified

Of the five Saffire SIBAL Table 1 configurations, the narrow/deep condition has II-5 and II-6, wide/deep has I-1 and III-1, wide/shallow has IV-SIBAL, and **narrow/shallow is absent**. These analogues do not match oxygen, specimen length, flight and other conditions. It is not possible to compute a controlled confirmatory width × confinement interaction from these records. The additional two BASS SIBAL rows come from a different, much smaller apparatus and are not substitutes for the missing Saffire cell.

## Evidence required to close the gaps

**Physical interaction:** An appropriate qualified microgravity facility would need to measure multiple new independent burns in all four geometry cells, with common materials/length, actual pressure/oxygen/flow, matched positioning and a prespecified flame-base measurement protocol. Block or randomize geometry assignments across independent sessions. Estimate interaction and confidence interval, checking robustness to quenching/measurement uncertainties. Access to that facility and new measurements cannot be replaced by computer analysis.

**Cross-scale prediction:** Recover/verify raw burn, campaign, sensor and timing metadata; reconcile dimensions and per-stage conditions; curate sufficient *independent* SIBAL train and Saffire holdout groups; freeze M0/M1/M2 and data eligibility; evaluate held-out MAE/RMSE and uncertainty without selecting features on the test data. No eligible independently verified cross-scale evaluation cohort has yet been established.

**Do not show these exploratory numbers as 1gnition's NASA-model accuracy on the website.** If the study is shown at all, use an explicit research-feasibility label separate from published source observations and from the synthetic test.

## Reproduce the bounded study

In the extracted folder with Python, NumPy, pandas, and scikit-learn installed:

```bash
python run_preflight.py
```

Source files are included in `input_data/` as transcriptions. Source provenance: Olson et al., *Combustion and Flame* (2023), Table 1, DOI: https://doi.org/10.1016/j.combustflame.2022.112559 ; NASA/TM-20210011385 Table 5.1: https://ntrs.nasa.gov/citations/20210011385 .

## Outputs

- `real_data_preflight.json`: data checks, factor-grid occupancy, grouped holdout results, limitations.
- `pmma_exploratory_group_holdout_predictions.csv`: measured/predicted values in all held-out folds, for technical audit only.
- `run_preflight.py`: reproducibility code.
- `input_data/`: original team transcriptions used for this diagnostic.
