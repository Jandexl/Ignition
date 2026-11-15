# Model design

## One target, three predeclared models

The target is flame-spread rate in cm/s, for a reviewed solid-fuel spread regime. Flame length/size in cm cannot be substituted. A row is a measurement; independence belongs to a reviewed dependency group, not the row.

| Model | Predictors | Purpose |
|---|---|---|
| `mean` | None; training-fold mean target | Minimal reference for useful prediction |
| `condition_ridge` | Flow speed, oxygen %, absolute pressure; material and direction | Test whether conditions add predictive information |
| `geometry_ridge` | Same conditions plus predeclared reviewed geometry | Test whether geometry adds information on identical held-out records |

Numeric scaling and categorical encoding are inside each scikit-learn Pipeline. Every fold creates a fresh model and fits preprocessing exclusively on training data. No imputer is used: unknown atmospheres remain unknown. Ridge alpha is fixed at 1.0 in the demo; experimental alpha must be frozen in the evaluation plan. If tuning is later needed, use an inner grouped validation loop and a separate outer evaluation; the current version deliberately does not implement tuning.

`ColumnTransformer` selects only the allowlisted pre-outcome columns. Run, campaign, source, observation ID, digitization status, uncertainty envelopes and target never become predictors. Regime fields constrain domain/cohort membership. Material aliases must be reviewed externally; case/whitespace conflicts are detected but semantic equivalence cannot be inferred reliably by software.

## Geometry is conditional

Width and length describe the specimen. Duct height describes a confinement dimension only after the Scientific Lead establishes which surfaces it measures. A width/height ratio is dimensionless because both quantities use cm. It is not a universal scaling law. Dimensions cannot be mixed between full duct height and specimen-to-wall gap. `geometry_definition_id` references the common reviewed definition; differing definitions block evaluation.

The code can evaluate width, length, thickness, duct height and one optional width/height ratio. Add only features justified before seeing test scores. With very few independent runs, prefer one geometry feature. If geometry is constant within campaigns, the report warns that campaign/apparatus effects can be confounded. This warning is a diagnostic, not an exhaustive causal-identifiability test.

The synthetic generator explicitly includes a width term. Therefore a width-aware model doing better on that fixture verifies the software's sensitivity to an invented signal; it is no evidence that width helps on NASA data.

## Domain and approval

The domain uses observed bounds, known categorical combinations and a nearest-observation distance after scaling numeric differences by observed ranges. Checks include fully populated geometry even when a baseline does not use it. All comparisons use the same conservative domain definition. The default maximum distance 0.35 is a **software heuristic** requiring a documented review rationale before experimental activation, not a physical safety threshold or uncertainty estimate.

Axis ranges alone do not establish joint coverage. The local check requires matching material, flow direction, gravity regime, combustion regime and selected geometry definition. It reduces false coverage but still cannot prove physical applicability.

Evaluation can report errors on out-of-domain test records, including cross-scale transfer tests; those records are flagged and never silently discarded. Experimental activation is conservatively blocked if any evaluated observation is out of domain. A separate deployment-domain study is needed before supporting such extrapolation. Evaluation itself never automatically activates a predictor.

## Lightweight implementation choices

Ordinary pandas, NumPy, scikit-learn, matplotlib, joblib and jsonschema. Python's standard-library unittest supplies the tests. JSON configuration avoids a YAML dependency. Python module/CLI integration avoids web infrastructure. The modules combine closely related functions rather than adding empty baseline/export/preprocessing files.

## Reference documentation

Implementation references accessed 2026-11-14; package tested with scikit-learn 1.8.0. Documentation URLs are versioned for reproducibility:

- [Ridge](https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.Ridge.html)
- [GroupKFold](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.GroupKFold.html)
- [Pipeline](https://scikit-learn.org/1.8/modules/generated/sklearn.pipeline.Pipeline.html)

Scientific source interpretation remains governed by the supplied audit and Scientific Lead, rather than these software references.
