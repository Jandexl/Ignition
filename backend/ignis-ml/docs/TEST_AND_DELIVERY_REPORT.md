# Delivery validation report

Executed 14 November 2026 on Linux / Python 3.12.

- **64 tests passed; 0 failures, 0 errors.** Full log: `outputs/test_report.txt`.
- Editable package installation succeeded with the available dependencies.
- End-to-end demo, model serialization and installed CLI prediction succeeded.
- All three prediction response examples and CLI response passed the JSON response schema.
- CLI evaluation refusal returned exit code 2 as documented.
- Seven synthetic PNGs generated; measured/predicted and feature-coverage layouts visually inspected.
- Both original NASA observation adapters return `VALIDATION_NOT_SUPPORTED`.
- No NASA model was fitted, approved or exported.
- M2 execution was not tested; CPU-only installation commands are supplied.

## Synthetic errors — software demonstration only

The generator deliberately embeds a width effect. These numbers are not NASA findings.

| Model | MAE (cm/s) | RMSE (cm/s) | Groups | Observations |
|---|---:|---:|---:|---:|
| mean | 0.040299 | 0.050405 | 12 | 72 |
| condition_ridge | 0.023995 | 0.028077 | 12 | 72 |
| geometry_ridge | 0.002589 | 0.003246 | 12 | 72 |

Two implementation failures were discovered during testing (nullable metadata comparison and a pandas duplicate-row argument) and fixed. The final full suite passed after the fixes and additional audit-veto/negative-prediction tests. No known test failures remain.

Scientific limitations: independence/comparability reviews must be genuine; sparse evidence remains a blocker; a review reference is not authentication; model intervals and experimental measurement uncertainty are not estimated; geometry benefit and cross-scale accuracy remain unvalidated.
