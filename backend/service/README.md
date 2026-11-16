# 1gnition backend service

A thin layer around the science/ML package in `../ignis-ml` (Python import name `ignis_ml`, kept for compatibility). It adds three things the package does not ship: a reproducible export to the website, an evidence adapter with an `evidence_class` on every item, and a small JSON API. It fits no model and cannot return a NASA prediction.

## Files

| File | What it does |
|---|---|
| `build_frontend_data.py` | Re-exports `scientific_comparisons.json`, copies the synthetic verification results and benchmark, writes `evidence_catalog.json` and `build_manifest.json`, runs 62 acceptance checks, rebuilds `seed.js`. Stops on any failed check. |
| `evidence.py` | Adapter: `compare_records`, `build_catalog`, `acceptance_checks`, `table1_evidence_frame`. Never changes a source value. |
| `server.py` | Standard-library HTTP server: static site plus `/api/*`. |
| `tests/test_backend.py` | 18 tests: adapter, acceptance checks, manifest hashes, every endpoint. |

## Commands (from the repository root)

```bash
python3 -m pip install -e backend/ignis-ml          # numpy, pandas, scikit-learn, jsonschema, scipy, joblib, matplotlib
python3 backend/service/build_frontend_data.py --frontend frontend           # add --rerun-synthetic to regenerate the seeded synthetic run
python3 backend/service/server.py --frontend frontend --port 8787
python3 -m unittest discover -s backend/service/tests -v
(cd backend/ignis-ml && python3 -m unittest discover -s tests -v)           # the package's own 77 tests
```

## Scenario measurement lookup

POST `/api/scenario` accepts the prediction request fields and returns the original prediction status alongside `measurements`. Exact matches require all supplied numerical conditions to equal a single published Table 1 record (absolute tolerance 1e-9), plus material, direction, gravity and combustion regime. Optional geometry fields restrict matches when provided. Unreported thickness or geometry definitions cannot be treated as verified matches.

Results include the original record, rate in cm/s and mm/s, source locator, omitted geometry and all differing conditions for up to three related records. Related records share the categorical conditions and are sorted by the sum of numerical differences normalized by each candidate-set range. This ordering supplies references for comparison and carries no calibrated confidence. Records are never averaged or counted as additional burns.

The website's published-experiment selector fills the shared scenario and requests these measurements. The prediction result remains independently labeled.

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/api/health` | | `{status, ignis_ml_version, data_build, prediction_status}` |
| GET | `/api/<collection>` | | the matching `frontend/data/<collection>.json` (for `DATA_MODE: "api"`) |
| POST | `/api/compare` | `{"baseline": "I-1", "comparison": "II-5"}` | descriptive comparison of two Olson Table 1 records. Reviewed cases are returned exactly as the science package wrote them (`reviewed_case: true`); other pairs use the same arithmetic and list every changed variable. |
| POST | `/api/predict` | scenario per `ignis-ml/docs/request.schema.json` | `ignis_ml.prediction.predict(scenario, bundle=None, evidence=Table 1 metadata)`, validated against `response.schema.json`. Always `LIMITED_EVIDENCE` or `UNSUPPORTED` with `predicted_flame_spread_rate_cm_s: null`. |

Errors: `400` invalid input (`status: "INPUT_ERROR"`), `404` unknown endpoint, `413` body over 16 KB, `429` more than 60 POSTs per minute per IP, `500` if a response would fail the schema or carry a number.

## Security and limits

- No model bundle is loaded, so no numeric prediction path exists.
- No authentication. Fine for a demo or local integration; put it behind a gateway with auth before exposing it publicly.
- CORS origins come from `IGNITION_CORS_ORIGINS` (comma-separated, default `*`).
- Collection names are restricted to `a–z` and `_`, so paths cannot escape `frontend/data/`.
- No API keys are needed or stored.

## Activating a real model later

Follow `ignis-ml/docs/DASHBOARD_INTEGRATION.md`: a reviewed approval record, a matching fingerprint and a grouped held-out evaluation on independent flights. Only then load a bundle in `server.py`, and keep the frontend's synthetic banner logic for any `synthetic: true` response.
