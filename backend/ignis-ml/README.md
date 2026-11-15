# IGNIS ML — scientific revision, 15 November 2026

Eight published Olson Table 1 records support three descriptive Saffire comparisons. All eight have approved_for_ml=False. Start with [the revised science and frontend guide](docs/SCIENCE_FRONTEND.md) and [the dashboard JSON](outputs/scientific_comparisons.json). The original ML prototype and its historical audit documentation follow below. The current scientific decision is in data/revision/Scientific_Lead_Decision.md.

# IGNIS ML — reproducible research prototype

**Software tested; no validated NASA predictor is included.** This package implements three regressors, independent-group evaluation, data checks, domain checks, and a JSON interface that can abstain. The only saved model is clearly marked SYNTHETIC.

The original four CSVs were inspected. The later audit was also read: it reports **zero approved ML rows**. Neither the 23 digitized points nor the two newly recovered same-campaign numerical entries support the proposed independent cross-scale validation yet. See `docs/DATA_COMPATIBILITY.md`.

## Run on your MacBook Air M2

Use Python 3.10 or newer. In Terminal, navigate into the extracted `ignis-ml` folder. If you want to reuse your existing environment, activate it and skip the first two commands.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m ignis_ml.cli demo --root .
```

The demo is deterministic, uses NumPy seed 20261114, and requires no GPU or network after installation. It runs on CPU. It creates 72 synthetic measurements from 12 invented dependent groups, seven plots, a serialized synthetic model, and three JSON response examples. It does not fit the NASA candidates. Each run overwrites only its own demo outputs.

```bash
python -m ignis_ml.cli predict outputs/scenario_supported_SYNTHETIC.json \
  --model outputs/SYNTHETIC_DEMO_MODEL.joblib --output outputs/my_response.json
```

Open `outputs/my_response.json` or load it in your dashboard. `SUPPORTED` in this example applies **only to a synthetic software demonstration**, prominently flagged by `synthetic: true` and `SYNTHETIC_DEMO_ONLY`.

## What is included

| Location | Purpose |
|---|---|
| `src/ignis_ml/` | Implemented modules and CLI; no empty placeholders |
| `tests/test_system.py` | Automated contract, leakage, evaluation, prediction and plotting tests |
| `data/current/` | Text snapshots of the four inspected starter files, retained for audit/testing |
| `data/synthetic_fixture.csv` | Invented data; never merge with experimental data |
| `outputs/plots/` | Seven synthetic diagnostic figures |
| `outputs/test_report.txt` | Executed test results |
| `outputs/*validation.json` | Current-file quality reports with row references |
| `outputs/*evaluation_refusal.json` | Explicit refusal to evaluate current NASA records |
| `docs/ML_LEAD_BRIEFING.md` | Read this first to understand and present the work |
| `docs/DATA_REQUIREMENTS.md` | Contract, units, reviewed cohort and import procedure |
| `docs/VALIDATION_PROTOCOL.md` | Split rules, review gates and interpretation |
| `docs/DASHBOARD_INTEGRATION.md` | Interface, status rendering and activation procedure |
| `docs/*.schema.json` | Request/response schemas for backend integration |

## Scientific scope

This is a reproducible way to test a hypothesis, not a spacecraft fire-safety certification. Geometry-aware Ridge is ordinary regularized regression with reviewed geometry features; it is not a physics solver or a newly discovered physical law. There is no lunar-gravity extrapolation, automatic missing-condition imputation, automatic winner selection, or fabricated uncertainty interval.

The current fixed condition features are airflow, oxygen percentage and total pressure, with material and flow direction encoded categorically. A constant measured condition is acceptable; an unreported condition is not. The geometry extension defaults to width and can optionally use verified dimensions or the reviewed width/duct-height ratio. The ratio is off by default.

Tested here on Linux/Python 3.12; M2 instructions are provided but an actual Mac was not available. `outputs/runtime_versions.json` records the precise execution environment. Dependency ranges are in `requirements.txt`; `requirements-tested.txt` records versions used for this delivery. Re-run tests if upgrading them.

Load only trusted `.joblib` files: model serialization uses Python pickle mechanisms. Prefer regenerating the supplied synthetic bundle locally with the demo command. Code and model bundles are trusted backend assets; review references are audit records, not cryptographic identities or an authentication system.
