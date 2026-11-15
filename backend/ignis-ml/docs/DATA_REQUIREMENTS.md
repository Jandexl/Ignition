# Data requirements and reviewed-data import

`data_contract.json` defines each field's scientific meaning, units, role, missing policy, scientific-review requirement and leakage restriction. `data_contract.md` is the same contract as a readable table. This contract is intentionally stricter than the starter files.

## Canonical units and meanings

Airflow and spread rate use cm/s; specimen width/length and duct height use cm; thickness uses mm; total absolute pressure uses kPa; oxygen uses mole/volume percent on a 0–100 scale. An unqualified mass fraction is not interchangeable with oxygen mole fraction. Flow speed is a nonnegative magnitude; concurrent/opposed direction is a separate category.

Suffixes are a unit declaration: `flow_velocity_cm_s` means the caller has already converted correctly. If per-column `__unit` fields are supplied, the validator checks their consistency. The code cannot discover mislabeled but plausible measurements purely from their magnitudes. Preserve original units, values and conversion records in separate columns/files and have a reviewer verify them.

`schema.convert(values, from_unit, to_unit)` explicitly supports mm/cm/m, mm/s/cm/s/m/s, Pa/kPa, and oxygen fraction/percent. Unknown or dimensionally incompatible conversions raise an error. Missing values remain missing; convert only known entries. Never guess a unit from the magnitude.

Examples: 410 mm becomes 41 cm; 2.1 mm/s becomes 0.21 cm/s; oxygen mole fraction 0.21 becomes 21%; 100000 Pa becomes 100 kPa. Converting cm to cm/s is forbidden.

## Required review metadata

Experimental rows use `data_origin=experimental`, `verification_status=verified`, and `grouping_status=verified`. Accepted measurement statuses are `verified_numeric` and `reviewed_digitized`; the latter produces a warning and requires a sensitivity discussion. Reviewed digitization may be usable in a future study, but the present 23 points do not meet the other requirements.

`dependency_group_id` must be globally unique and must unite all dependent measurements. A run key is the tuple of investigation ID, campaign ID and run ID. Several rows from one run are allowed, provided they share a dependency group. Different observations with identical numerical conditions are not automatically duplicates: repeated experiments can legitimately match conditions. The software rejects duplicate observation IDs/exact rows, and human provenance review must identify the same measurement re-exported under a different ID.

Geometry fields may be missing when unused. Selected geometry must be finite, positive and reviewed, with a shared `geometry_definition_id`. If every geometry field is absent from a conditions-only study, no geometric transfer claim is supported. Missing pressure or oxygen always blocks this version: no nominal-value imputation occurs.

A source manifest must contain unique nonmissing `source_id`, nonempty `title` and `url`, plus `verification_status=verified`. Row-level `source_location` and `review_id` identify where the measurement came from and where its audit is recorded. Keep additional manifest metadata; the pipeline does not discard it or infer review from a source's title.

## Import and evaluate

1. Keep original reviewed CSV/source files unchanged. Create a separate canonical CSV with explicit rename/conversion mappings and review references. Do not feed the older starter adapter a newer schema and assume it has been scientifically approved.
2. Fill only confirmed metadata. Obtain the independence and comparability reports. A missing required value should remain a visible blocker.
3. Copy `configs/model_config.json` to a new study file. Replace the unresolved review references, freeze the configuration before test inspection, and set `frozen_before_evaluation=true` only when that is true. Choose minimal justified geometry or set `geometry=[]` for conditions-only evaluation.
4. If selecting a comparable subset, use a reviewed cohort JSON. Example structure:

```json
{
  "review_reference": "YOUR_REAL_COHORT_REVIEW",
  "reason": "Compare one material and one reviewed spread regime",
  "equals": {
    "material": ["YOUR_VERIFIED_MATERIAL"],
    "gravity_regime": ["microgravity"],
    "combustion_regime": ["YOUR_VERIFIED_REGIME"]
  }
}
```

The selector records included and excluded observation IDs; it cannot filter on target values. There is no silent `dropna` or automatic removal of difficult test records. If no filtering is needed, omit `--cohort`.

```bash
python -m ignis_ml.cli validate data/reviewed_canonical.csv \
  --manifest data/reviewed_sources.csv --config configs/my_reviewed_plan.json \
  --output outputs/reviewed_validation.json

python -m ignis_ml.cli evaluate data/reviewed_canonical.csv \
  --manifest data/reviewed_sources.csv --config configs/my_reviewed_plan.json \
  --cohort configs/my_reviewed_cohort.json --output outputs/reviewed_evaluation.json
```

5. Review errors, warnings, group counts, per-fold domain checks, residuals and confounding. Generate figures with `plotting.make_plots(selected_dataframe, report, output_directory)` only after evaluation succeeds. No automatic model activation follows evaluation.
6. Scientific review must assess whether errors and evidence are adequate for the narrowly stated research use. Supply the matching fingerprint and model choice to `prediction.activate`; see the integration guide.
7. If readiness fails or groups remain insufficient, export the refusal JSON and relevant evidence to the dashboard. No rewrite is needed when fit-ready data arrives, but scientific review cannot be replaced by a schema mapping.

The original starter checks can be reproduced with `--adapter starter` or `--adapter candidate`. Those adapters intentionally mark their outputs unreviewed. Their `raw__...` columns preserve the original values for traceability.
