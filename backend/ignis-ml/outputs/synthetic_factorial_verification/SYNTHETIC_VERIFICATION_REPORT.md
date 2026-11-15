# 1gnition — Synthetic factorial verification

**All measurements in this folder are generated, not NASA observations.**
This verifies the existing `ignis_ml.factorial.analyze_burns` code under controlled mathematical assumptions.

| Case | Known Δ (cm/s) | Estimated Δ | Approx. 95% interval | Result |
|---|---:|---:|---|---|
| positive | +0.0800 | +0.0763 | [+0.0685, +0.0841] | Expected sign recovered |
| zero | +0.0000 | -0.0008 | [-0.0093, +0.0078] | Near zero, interval spans zero |
| negative | -0.0800 | -0.0834 | [-0.0946, -0.0722] | Expected sign recovered |
| positive_height_sessions | +0.0800 | +0.0747 | [+0.0579, +0.0916] | Expected sign recovered |

Automated synthetic-specific checks: 5/5 passed.

These confidence intervals assume independently generated blocks/sessions and an ordinary t/Welch approximation.
They do **not** demonstrate empirical 95% coverage across real experimental settings.
The four rates for each case are intentionally chosen, including the presence/absence/direction of the interaction.
No actual flame physics is simulated, and no NASA measurements were used to estimate the interaction.
The three historical Saffire comparisons remain a separate source-backed demonstration.
The model-readiness state remains `VALIDATION_NOT_SUPPORTED` for NASA cross-scale prediction.

## Reproduce
From the `ignis-ml` folder, install requirements then run:
```bash
python scripts/verify_factorial_synthetic.py
python -m unittest discover -s tests -v
```

## Dashboard
Load `outputs/synthetic_factorial_verification/synthetic_verification_results.json`
only in an explicitly marked **Synthetic Verification** mode. Do not merge these CSVs with NASA observations.
The results include an invented four-cell comparison, uncertainty estimates, and guardrail refusals.
Do not turn the resulting statistical estimates into physical or operational flame predictions.
