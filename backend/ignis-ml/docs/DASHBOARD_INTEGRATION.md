# Dashboard integration

Use `predict(scenario, bundle=None, evidence=None)` from the Python backend. The frontend should consume JSON, not Python/joblib objects. `request.schema.json` and `response.schema.json` are Draft 2020-12 schemas. The implementation validates incoming request structure and refuses malformed input; tests validate every example response.

## Request

All requests require material, flow direction, airflow in cm/s, oxygen percentage, total pressure in kPa, gravity regime and combustion regime. Geometry fields are conditionally required by the active model's domain, including geometry fully known in its training cohort. Selected geometry additionally requires a matching definition ID and verification status. The exact synthetic request is `outputs/scenario_supported_SYNTHETIC.json`.

```python
import json
from ignis_ml.prediction import load, predict

# Trusted bundle only. Regenerate this demo file locally if dependency versions differ.
bundle = load('outputs/SYNTHETIC_DEMO_MODEL.joblib')
scenario = json.load(open('outputs/scenario_supported_SYNTHETIC.json'))
response = predict(scenario, bundle=bundle)
print(json.dumps(response, allow_nan=False))
```

For the current actual evidence, leave `bundle=None`. Pass a table of evidence metadata to show relevant source IDs without producing a number. The evidence matcher is deliberately simple: exact material and supplied direction/regime matches. It is not the full Evidence Explorer ranking engine, and it does not reconcile material aliases or certify source IDs. Use the project's reviewed evidence layer for richer rankings.

## Render the state faithfully

| Status | Frontend behavior |
|---|---|
| `SUPPORTED` | Show the number and units only when the model is reviewed; for `synthetic=true`, show a prominent “Synthetic demonstration — not NASA validation” banner |
| `LIMITED_EVIDENCE` | Show relevant records/source IDs, limitations and abstention reason; prediction remains null |
| `UNSUPPORTED` | Show the reasons and domain warnings; prediction remains null |

Never convert `null` into zero, display a cached old prediction after a refusal, or translate `SUPPORTED` into “safe.” The output's intended use remains `research_demonstration_only` even after experimental review. Always display validation status and independent group counts with any error metrics. Synthetic performance must never appear on a NASA accuracy card.

`model_performance` is aggregate held-out error, not a prediction-specific confidence interval. `inputs_used` contains the regression's raw inputs (empty for the mean baseline). Domain checks can depend on additional scenario inputs. All relevant training source IDs are returned; nearest-evidence retrieval is separate.

Examples provided:

- `outputs/supported_SYNTHETIC.json`: numerical fixture prediction with synthetic flag.
- `outputs/limited_evidence.json`: relevant fixture evidence without an active model; null prediction.
- `outputs/unsupported.json`: airflow far outside fixture coverage; null prediction with a domain warning.

All three are engineering examples. Current NASA-specific refusals are in `starter_evaluation_refusal.json` and `candidate_evaluation_refusal.json`; their evaluation schema differs from the prediction response schema.

## Activating a future reviewed experimental model

The CLI evaluates but does not auto-approve. A responsible reviewer supplies an approval dictionary after reviewing the report. Approval requires reviewer identity, a review document reference, an acceptance rationale, a domain rationale, matching fingerprint/model/evaluation status, and a truthful declaration that selection was independent of the reported test scores.

```python
from ignis_ml.prediction import activate, save
# df, manifest and cfg are the SAME reviewed cohort and frozen configuration evaluated earlier.
# approval is read from the real scientific review record, not generated from a score threshold.
bundle = activate(df, manifest, cfg, 'condition_ridge', approval, synthetic=False)
save(bundle, 'outputs/reviewed_research_model.joblib')
```

Activation recomputes the evaluation and checks its fingerprint. No NASA approval record is supplied in this package. The synthetic helper `approval_for` is exclusively for fixtures and visibly labels itself as such. Never use it to manufacture a scientific approval.

A backend should control who can load bundles or supply approvals. This package has no authentication layer, public API server, rate limiting or hosted deployment; those are outside its lightweight scope. It is ready to be called from your existing backend.

## CLI exit behavior

`0` means the command completed its supported action. `2` means an input error, readiness/evaluation refusal, or prediction abstention. Inspect the JSON status rather than treating every nonzero result as a crash. The `INPUT_ERROR` envelope is a CLI error report, not a prediction response.
