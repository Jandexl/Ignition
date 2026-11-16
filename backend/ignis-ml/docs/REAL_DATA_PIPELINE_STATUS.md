# Real-data training and evaluation: what blocks it

Checked 2026-11-16 by running the package's own `ignis_ml.validation.validate` and `ignis_ml.evaluation.evaluate`, unchanged, on every real dataset in the repository. Full output: `test_logs/real_data_pipeline_check.txt`. Nothing was trained, no review fields were filled in, and no file was changed.

**Result: the real-data pipeline correctly refuses all three datasets.** The code works. The data and the human reviews it needs don't exist yet. The only model that can run is the synthetic demo (`outputs/SYNTHETIC_DEMO_MODEL.joblib`, invented data).

## Gate 1: the evaluation plan (`configs/model_config.json`)

`plan_id`, `independence_review_id`, `comparability_review_id` and `geometry_rationale` are empty, and `frozen_before_evaluation` is `false`. The CLI stops here for every dataset: "A frozen evaluation plan, independence review and comparability review are required." These are human scientific decisions. The software deliberately can't fill them in.

To reach the data checks below, the diagnostic used a **hypothetical** filled-in plan held only in memory.

## Gate 2: the data

| Dataset | Rows | Why it can't be used |
|---|---|---|
| `data/current/ignis_experiments_starter.csv` | 4 | It measures **steady flame size (cm), not spread rate (cm/s)**, so there is no target value. Flow direction, investigation ID, dependency group, regime and review ID are missing in every row. |
| `data/current/ignis_bass_saffire_candidate_observations.csv` | 23 | Rates were **digitized from Urban 2021 Figure 10**. Every row lacks a run ID, investigation ID and dependency group, and 16 of 23 rows lack oxygen and pressure. The status is `digitized_from_Figure_10`, not a reviewed status. |
| `data/revision/ignis_table1_rates.csv` (Olson et al. 2023 Table 1, the best real data) | 8 | **The reviewed table marks `approved_for_ml` false on all 8 rows**, so the audit veto blocks them. The rows have no verified investigation or dependency-group IDs and no reviewed geometry definition. Duct heights are estimated for the four Saffire I–III rows. Two materials (SIBAL, cotton) would need a comparability review. |

Every source manifest also lacks the `verification_status` column the pipeline requires.

## Gate 3: even with every review done

Olson Table 1 has **8 burns in 8 different configurations, from 5 Saffire flights plus BASS**. Each configuration was burned **once**. A leave-one-burn-out evaluation would technically run, since it needs at least 3 groups, but:

- no burn has a repeat, so run-to-run variability is unknown and a model error can't be separated from scatter between burns;
- every held-out burn changes several conditions at once (flow, width, length, duct height, oxygen, pressure, flight), so the result would test extrapolation, not interpolation;
- 8 points can't support the inputs the model uses (flow, oxygen, pressure, width, material, direction) without overfitting.

## What would unblock it

1. Recover the per-run identities: the BASS / BASS-II test logs (PSI-25, PSI-26) and the Saffire flight logs (PSI-98 to PSI-100), with oxygen and pressure per run.
2. Have the Scientific Lead sign the independence review, the comparability review and the geometry-definition document. Then set `verification_status` / `grouping_status` / `geometry_status` to `verified` and `approved_for_ml` to true only where earned.
3. Freeze the evaluation plan (`frozen_before_evaluation: true`) before looking at any test result.
4. Get replicated burns. The proposed 2 × 2 width × duct-height experiment, with independent specimens in randomized blocks, is the cleanest source.

Only after all of that may `prediction.activate` bind an approval to a real model. `/api/predict` will keep returning a null number until it does.
