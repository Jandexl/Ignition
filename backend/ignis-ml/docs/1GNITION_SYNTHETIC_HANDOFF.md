# 1gnition — Synthetic factorial verification handoff

**Result:** The existing `ignis_ml.factorial.analyze_burns` function recovered known positive (+0.08), null (0), and negative (−0.08) width × confinement interactions in deliberately fabricated noisy measurements. A height-by-session design also recovered the known positive interaction. The original and added tests all pass (77 total), and four invalid-input guardrails refuse to return an interaction.

**What this is:** Software verification with artificial datasets generated from chosen cell means plus random noise. The positive, null, and negative results were programmed into the data generator. They do not constitute new NASA evidence, physics simulation, independent experimental replication, or proof of the directional scientific hypothesis.

## Input definitions

- Width: `5 cm` (narrow) or `40.6 cm` (wide).
- Full duct height: `30.5 cm` (shallow) or `51 cm` (deep).
- All generated rates: cm/s.
- Deliberately chosen deep-duct rates: narrow 0.20; wide 0.22.
- Deliberately chosen shallow-duct narrow rate: 0.24.
- Deliberately chosen shallow-duct wide rates: 0.34 (positive), 0.26 (zero), 0.18 (negative).
- The primary randomized-complete-block synthetic design uses 20 independent fictional blocks, each containing four independently identified fictional specimens: 80 generated burns per case. 0.006 cm/s shared block offset and 0.012 cm/s independent per-burn Gaussian noise, with fixed recorded seeds.
- The alternative randomized-height-session simulation uses 12 sessions per duct height and two width conditions per session: 48 generated burns.

## Interaction definition

`(wide_shallow − wide_deep) − (narrow_shallow − narrow_deep)` where each term is the mean spread rate, in cm/s. The primary statistic is on the raw spread-rate scale, not the logarithmic scale.

## What to copy into the frontend

- `outputs/synthetic_factorial_verification/synthetic_verification_results.json`: machine-readable outcomes, true interactions, estimates, approximate 95% intervals, and four scientific guardrail refusals.
- `outputs/synthetic_factorial_verification/positive_synthetic_2x2.png`: four-cell synthetic result; error bars are one standard deviation of generated burn rates, not NASA measurement uncertainty.
- `outputs/synthetic_factorial_verification/synthetic_interactions_95ci.png`: known values (×), estimated interactions, and approximate t/Welch intervals.

A safe frontend mode has visible heading **SYNTHETIC VERIFICATION — NOT NASA DATA**. It should display a scenario switcher `Positive / Zero / Negative`, the four generated cell means, an estimated interaction with uncertainty, and a sentence explaining that the interaction was built into the generator to test software.

Suggested user-facing caption:
> In this mathematical verification, the 1gnition analysis recovered deliberately inserted positive, zero, and negative interactions from invented, noisy observations. This validates the behavior of the estimator on these scenarios; it does not validate the physical hypothesis or a NASA-trained flame-spread predictor.

Do not merge synthetic rows into the source-linked NASA experiment catalog, rebrand these as historical NASA data, or use synthetic confidence intervals as NASA experimental uncertainty. Keep real NASA prediction state `VALIDATION_NOT_SUPPORTED`.

## How to reproduce

From the preserved `ignis-ml` package root:

```bash
python -m pip install -e .
python scripts/verify_factorial_synthetic.py
python -m unittest discover -s tests -v
```

The old import/package name `ignis_ml` is retained deliberately for backwards compatibility. Only the user-facing project brand changes to **1gnition**.

## Remaining scientific milestones

1. Controlled microgravity burns in all four factorial configurations, with independent replicated specimens, matched conditions, calibrated flame-front tracking, and a prespecified analysis plan.
2. Independent real-NASA experimental train/holdout groups for M1/M2 or the Science Lead's exploratory log-linear model.
3. A targeted predictive-use domain, acceptable error criteria, and quantified generalization uncertainty.
