# Scientific validation protocol

## Eligibility before any fitting

1. Confirm the target is a comparable flame-spread rate, with consistent definition, cm/s units and source location. Only verified numerical values or explicitly reviewed digitization may enter experimental evaluation.
2. Resolve material specification, atmosphere, gravity regime, flow direction and selected geometry. Keep BASS distinct from BASS-II. Never promote a candidate run link to a verified link by assumption.
3. Have the Scientific Lead document comparability and the Data Lead establish dependence. Measurements from the same run, specimen reuse, phases, repeat series or other linked observations belong to a single globally unique `dependency_group_id` as required by their actual dependence.
4. Provide run IDs and campaign/investigation identities even when grouping more coarsely. IDs are not proof: `independence_review_id` must point to the external audit that establishes why the chosen partitions are defensible.
5. Freeze cohort filters, target, features, alpha, group structure, domain tolerance, split strategy and evaluation criteria before inspecting held-out scores. Record the plan ID and review references.

The software enforces declarations, missingness, source references, same-run group consistency and split overlap. It cannot detect a fabricated review, hidden shared specimens, or a user inspecting the test set outside the system. Those are scientific governance responsibilities. Treat the configuration as a record of review, not proof that review occurred.

## Split modes

| Strategy | Test partition | Important restriction |
|---|---|---|
| `logo` | One dependency group at a time | Default; repeated observations stay together |
| `groupkfold` | Several complete groups per fold | Deterministic grouping, no row shuffle |
| `campaign` | One investigation/campaign tuple at a time | Reject if dependency groups span train and test campaigns |
| `cross_scale` | All observations of a predeclared held-out investigation | Train on remaining reviewed investigations; do not infer scale from names or widths |

At least three reviewed groups overall and at least two training groups per fold are engineering minima. They do **not** establish adequate statistical power. Campaign mode additionally requires at least three campaign partitions. Cross-scale mode can report one held-out group with a clear count and limitations; such evidence is weak and must not be sold as broad transfer validity. Users decide the scientific adequacy before activation, not just whether the code runs.

Each fold checks row, observation-ID, dependency-group and composite run-ID overlap. Unknown material/direction categories in a test fold block the entire comparison. Numeric extrapolation is reported per observation. The three models use identical folds and observations. Missing geometry is not a reason to compare Model 2 on an easier subset: choose one complete reviewed cohort first.

## Metrics and residual analysis

Report pooled MAE, pooled RMSE and signed bias in cm/s, plus group-macro MAE and group-macro RMSE (the unweighted mean of individual group RMSEs). Group-macro metrics give each group equal weight; pooled scores give each observation equal weight. Both are useful when a run supplies many observations.

The report contains per-group metrics, group and observation counts, predictor lists, configuration, sources, fold membership, out-of-domain warnings, and a SHA-256 fingerprint of ordered data, manifest and configuration. Residuals are prediction minus measurement. Seven diagnostic plots check error patterns, feature coverage and group balance.

No uncertainty bands are generated. Digitization reading envelopes are not automatically measurement error, and residual scatter is not experimental uncertainty. Additional runs are needed before defensible prediction intervals or robust group-bootstrap comparisons can be designed.

## What would support a geometry advantage?

Predeclare Model 2 and compare it with Model 1 and the mean baseline on the same independent tests. Look for lower MAE and RMSE across multiple held-out groups/campaigns, not a benefit concentrated in one campaign. Review paired group differences, residual patterns, stability to justified measurement uncertainty, and whether geometry was entangled with oxygen, direction, material or apparatus. Do not choose favorable features or alpha using those test scores and then cite the same scores as untouched validation.

This version reports paired aggregate changes and per-group errors, but does not perform hypothesis tests or claim statistical significance. If model choice follows these scores, a fresh independent evaluation is needed. There is no automatic model ranking-to-activation step.

## Failure and review states

- `INVALID`: data readiness failed; warnings alone do not cause this state.
- `VALIDATION_NOT_SUPPORTED`: evaluation cannot legitimately run with the supplied data/plan.
- `SYNTHETIC_EVALUATION_ONLY`: engineering fixture tested; no experimental validation.
- `EVALUATED_PENDING_REVIEW`: grouped experimental metrics computed, awaiting scientific assessment.
- `REVIEWED_GROUPED_EVALUATION`: model activated with matching documented approval; still research use only.

Review acceptance must explain independent selection, remaining confounding, prediction-domain coverage and adequacy of errors. Activation recomputes the evaluation and checks the approval's fingerprint/model/status. This prevents accidentally approving different data or configuration, but does not authenticate the reviewer. Changing the model implementation/version requires re-evaluation and renewed review. Do not edit a saved bundle to bypass these gates.
