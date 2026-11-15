# 1gnition — COMPLETE PROJECT HANDOFF / MASTER IMPLEMENTATION PROMPT

**Audience:** Frontend Lead, Backend Lead, ML Lead, Scientific Lead, Data Lead, QA/Presentation Lead  
**Project:** NASA Space Apps 2026 — *Flame in Freefall*  
**Brand:** **1gnition** (formerly IGNIS; retain `ignis_ml` internal Python import/package names for compatibility)  
**Status:** Science/data/ML prototype built; final frontend integration, scientific sign-off, end-to-end QA, deployment and submission still need confirmation.  
**Instruction:** Treat this document as the project specification, not as evidence that a feature is already integrated. Inspect the actual supplied packages and preserve their code.

---

## INSTRUCTIONS TO BOTH LEADS

You are the Frontend and Backend Engineering Leads for **1gnition**, an evidence-driven research platform for NASA microgravity combustion investigations. Your job is to **integrate the existing website, audited NASA data, scientific-comparison package, ML backend, synthetic verification, and research-gap analysis into one trustworthy, polished, responsive working application**. Do not restart the research, overwrite verified sources, fabricate experiments, or train an unsupported NASA prediction model. Protect existing working functionality, run tests, and report actual completion status.

**Primary deliverable:** A deployed, source-linked interactive scientific dashboard with four connected views: **Compare Runs**, **Evidence Explorer**, **Scale Transfer Lab**, and **Research Gaps**, driven by a persistent scenario bar. It must visibly distinguish published NASA measurements, digitized estimates, calculations, scientific interpretations, synthetic verification, and future hypotheses. A visitor must be able to follow a complete research story in under two minutes.

**Central research/product question:** *When can findings from small-scale microgravity combustion experiments meaningfully inform larger spacecraft-fire configurations, and what evidence is missing when transfer is not justified?*

**Featured physical research question (not confirmed):** *Under fixed concurrent airflow and atmosphere in microgravity, does reducing full duct height increase SIBAL flame-base spread rate more for wide specimens than for narrow specimens?*

**Core outcome:** Make the scientific reasoning auditable—not just an information retrieval site and not a fake fire simulator. Use programmatic matching, physics-based domain interpretation, provenance checks, model-readiness logic, and ML research infrastructure. The user must always know what is measured, what is inferred, and what is unsupported.

### Non-negotiable scientific safeguards

1. **Flame length/size (cm) is not flame-spread rate (cm/s)**. Separate labels, axes, units, tables, calculations and tooltips. Pyrolysis length is another separate outcome.
2. The **20 and 25 values in the four-run demonstration are airflow speeds in cm/s, not oxygen percentages**. The oxygen percentage is approximately 21–22% according to the specific published source and flight.
3. Do not treat eight Olson rows + 23 Urban Figure 10 readings + two PSI-99 rows as independent experiments. They overlap or may overlap. Alternative representations require provenance links, not duplicate model rows.
4. BASS = **PSI-26**; BASS-II = **PSI-25**; Saffire I/II/III = **PSI-98/99/100** respectively. Do not merge BASS with BASS-II. SIBAL and PMMA must not be pooled as the same fuel. Saffire V uses cotton, not SIBAL.
5. Maintain **source-specific geometry definitions**. In Olson Table 1 the Saffire full duct heights are **51 cm** (I–III) and **30.5 cm** (IV/V); a legacy Urban Table 2 `duct_height_cm=46` is a source-specific label and must not be silently treated as identical. Full duct height, full duct width, half-height/clearance, and specimen-wall gap are distinct.
6. Unknown fields are `null`, never 0 or an invented nominal Earth value. A source conflict is an explicit conflict, not a value to be averaged away.
7. The current real-NASA prediction state is **`VALIDATION_NOT_SUPPORTED`** with **`prediction_cm_s: null`**. Never generate NASA model accuracy, NASA flame predictions, lunar-gravity predictions, safety certifications, or a fire animation that implies validated physics.
8. Synthetic cases are **invented artificial data** used to verify software; never mix them into the NASA catalog. Grouped PMMA real-data exploration is **preliminary and not canonical M1/M2 or cross-scale validation**.
9. Existing published scientific explanations (Olson et al. 2023; other combustion research) must be credited. **1gnition did not experimentally discover confinement effects or prove a new combustion law.** Its novelty is an integrated, transparent scientific evidence-transferability workflow.
10. Source links, original units, publication locators, confidence/measurement status, and limitations must be accessible from the UI.

---

## 1. THE PROBLEM, USERS, AND GOAL

NASA Physical Sciences Informatics (PSI) archives microgravity combustion research. The challenge brief referred to roughly 24 investigations and ~12 TB, but treat those as **brief-level context**, not audited counts of data indexed by 1gnition. Most relevant initial studies are BASS and Saffire. Experiments differ in fuel geometry, airflow, oxygen, pressure, flight, apparatus, measurement definitions, sensors and independence. A researcher asking about a habitat configuration needs to identify relevant experiments, compare conditions, understand whether a physical conclusion transfers, and identify gaps.

**Users:** spacecraft-fire and fire-safety researchers, aerospace engineers, students, educators, habitat-design teams. **Safety context:** This is a research/education tool, not a certified fire-risk calculator.

**Required journey:** scenario selection → ranked/relevant investigations → source-linked run comparison → observed result → matched/different/missing conditions → scientifically defensible interpretation or refusal → proposed next experiment/data gap. User settings persist across all four views.

**One-line pitch:** **1gnition converts scattered NASA combustion measurements into traceable, physics-informed comparisons and research decisions, combining data interpretation, computational validation and ML safeguards.**

---

## 2. SCIENTIFIC DATA — AUTHORITATIVE SOURCES

**PRIMARY CANONICAL SOURCE FOR FEATURED NUMERICAL RATES:** `IGNIS_Scientific_Data_Revision.zip` → `ignis_table1_rates.csv` (Olson et al., *Combustion and Flame* 248, 112559, 2023, Table 1). Eight paper rows: seven SIBAL, one cotton. They are not eight fully independent model-validation groups. The ML revision embeds the same table at `ignis-ml/data/revision/ignis_table1_rates.csv`. Use this file and its stable `record_id` values—not starter CSVs—for the featured scientific comparisons.

| record_id | Fuel | Specimen width × length (cm) | Full duct height (cm) | O₂ (%) | Pressure (kPa) | Concurrent inlet speed (cm/s) | Spread rate (cm/s) | Flame length (cm) | Pyrolysis length (cm) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| I-1 | SIBAL | 40.6 × 94 | 51 | 21.7 | 102 | 20 | 0.18 | 4 | 4 |
| II-5 | SIBAL | 5 × 29 | 51 | 22.1 | 103 | 20 | 0.21 | 4 | 4 |
| II-6 | SIBAL | 5 × 29 | 51 | 22.1 | 103 | 25 | 0.26 | 5 | 5 |
| III-1 | SIBAL | 40.6 × 94 | 51 | 21.2 | 99 | 25 | 0.23 | 5 | 5 |
| IV-SIBAL | SIBAL | 40.6 × 50 | 30.5 | 23.1 | 99 | 20 | 0.36 | 8.5 | 8.5 |
| V-COTTON | Cotton | 40.6 × 50 | 30.5 | 26.9 | 76 | 20 | 0.34 | 14 | 10 |
| BASS-NARROW | SIBAL | 1.2 × 10 | 7.6 | 21.5 | 101 | 19 | 0.27 | 2.2 | unknown |
| BASS-WIDE | SIBAL | 2.2 × 10 | 7.6 | 21.6 | 101 | 22 | 0.51 | 6.2 | unknown |

**Important:** These are published summary measurements, not reprocessed onboard telemetry. All eight rows have `approved_for_ml=False` in the revised scientific dataset. Each row includes source ID and locator. BASS pyrolysis lengths are missing. The source's estimated flame-height fields must retain their estimation flag. Saffire V represents a different fuel and a lower-pressure oxygen-enriched atmosphere.

**SECOND SOURCE — URBAN 2021:** `ignis_urban_table2_flame_sizes.csv` contains the historical Table 2 flame-size example. For I-1, II-5, II-6, III-1, nominal airflow is 20/20/25/25 cm/s and steady flame size is 4/4/5/5 cm, respectively; specimens are nominal 41×94 vs 5×30 cm. This source reports *steady size*, not rate; preserve it as a source-scoped account. Do **not** overwrite Olson dimensions/atmosphere or merge the legacy `46` field into Olson's `51 cm` height without review.

**THIRD SOURCE — FIGURE 10:** `ignis_spread_rates_reviewed.csv` includes **23 manually redigitized marker readings** across BASS and Saffire series (16 BASS; 7 Saffire). Figure conventions: concurrent flow is plotted to the LEFT (signed negative horizontal coordinates); opposed flow to RIGHT (positive). Vertical axis is spread rate in cm/s. The source marker-to-run crosswalk is not complete. The approximate ±1.1 cm/s airflow and ±0.010 cm/s spread-rate envelopes describe **manual plotting/digitization allowance**, not NASA measurement uncertainty or a statistical confidence interval. Retain unlinked points as Figure 10 markers, not verified run-level training records. Seven potential overlaps with Olson records are documented; two BASS candidate matches remain unresolved; 16 markers lack Table 1 counterparts. Do not force merges.

**FOURTH SOURCE — PSI-99:** `ignis_psi99_rate_claims.csv` records two archive numerical entries, 2.1 and 2.6 mm/s, corresponding to 0.21 and 0.26 cm/s for the Saffire II examples. They are alternative source claims, **not two new independent burns**. An archive header says length despite mm/s rate units; flight II-6 airflow conflicts with Olson's 25 cm/s figure. Keep the conflict visible.

**FIFTH SOURCE — RECOVERY / PMMA:** BASS-II summary report Table 5.1 transcription includes **43 flow-step rows, 39 published numerical PMMA spread rates from 18 test IDs** in the latest feasibility subset. Oxygen is initial/final per test; exact oxygen at each flow step is unknown. This is a separate PMMA, opposed-flow, within-BASS-II technical case; no SIBAL cross-scale claim. A prior recovery package also includes 31 SIBAL test-matrix entries, predominantly conditions rather than rate outcomes. Never pretend those matrix entries supply additional numerical training targets.

**Required source files:** `ignis_source_manifest.csv`, `ignis_comparability_matrix.csv`, `ignis_comparison_cases.csv`, `PSI_TRANSCRIPTION.md`, `Scientific_Methodology.md`, `Scientific_Lead_Decision.md` and original source links below.

**Source links:**
- Olson et al. (2023), *The effect of duct size, sample size, and fuel composition on concurrent flame spread over large cellulose samples in microgravity*: https://doi.org/10.1016/j.combustflame.2022.112559 ; open manuscript https://discovery.ucl.ac.uk/id/eprint/10164340/1/SIBAL-cotton%20revised%20Sept%20per%20review%20track%20changes%20accepted.pdf
- Urban et al., *Fire Safety Implications of Preliminary Results from Saffire IV and V Experiments on Large Scale Spacecraft Fires*, ICES-2021-266: https://ntrs.nasa.gov/citations/20210011521
- BASS-II NASA/TM-20210011385: https://ntrs.nasa.gov/citations/20210011385
- PSI-25 BASS-II: https://psi.nasa.gov/physci/repo/data/investigations/PSI-25
- PSI-26 BASS: https://psi.nasa.gov/physci/repo/data/investigations/PSI-26
- PSI-98 Saffire I: https://psi.nasa.gov/physci/repo/data/investigations/PSI-98
- PSI-99 Saffire II: https://psi.nasa.gov/physci/repo/data/investigations/PSI-99
- PSI-100 Saffire III: https://psi.nasa.gov/physci/repo/data/investigations/PSI-100

**All source-derived claims must link to the appropriate specific table, figure, report page or PSI record.** No invented NASA data, missing values, or unverified run mappings.

---

## 3. THREE KEY SCIENTIFIC COMPARISONS — DEMO CENTERPIECE

The canonical calculations are in `ignis_comparison_cases.csv` and `ignis-ml/outputs/scientific_comparisons.json` → `comparison_cases`.

**A — I-1 vs II-5 (both nominal 20 cm/s concurrent):** 0.18 → 0.21 cm/s, difference **+0.03 cm/s** and **+16.67%** relative to I-1. Both report **4 cm flame length and 4 cm pyrolysis length**. SIBAL fuel and Olson full duct height 51 cm match, but specimen width **40.6 vs 5 cm**, length **94 vs 29 cm**, O₂ **21.7 vs 22.1%**, pressure **102 vs 103 kPa**, ignition/card position, flight, relative humidity and instrumentation/fit conditions differ. **Conclusion:** same reported flame extent does not imply the same propagation speed. Does not isolate width causation.

**B — III-1 vs II-6 (both nominal 25 cm/s concurrent in Olson):** 0.23 → 0.26 cm/s, difference **+0.03 cm/s**, **+13.04%** relative to III-1. Both report **5 cm flame length and 5 cm pyrolysis length**. Width 40.6 vs 5 cm, length 94 vs 29 cm; O₂ 21.2 vs 22.1%; pressure 99 vs 103 kPa; flights and positions differ. Archive flow conflicts for II-6 and III must be flagged. **Conclusion:** descriptive recurrence of equal reported length with different rate; not a statistically replicated width effect.

**C — I-1 vs IV-SIBAL (both nominal 20 cm/s concurrent):** 0.18 → 0.36 cm/s, difference **+0.18 cm/s**, **+100%**, or 2.00× rate. Full duct height **51 → 30.5 cm**, width **40.6 cm** matches, but specimen length 94 → 50 cm, O₂ 21.7 → 23.1%, pressure 102 → 99 kPa, RH, flight and camera conditions differ. Published flame and pyrolysis lengths 4 → 8.5 cm. IV time at a stable plateau is short. **Conclusion:** the shallower-duct configuration is associated with a larger spread rate; not proof that height caused the entire increase.

**Display requirements:** Each comparison must show a two-run card, the exact rate difference, denominator for percent change, lengths separate from rates, a matched/different/unknown variable matrix, source links, and a clear `Descriptive comparison — causal effect not isolated` warning. Never claim statistical significance or independent replicate uncertainty from these single summary entries.

---

## 4. SCIENTIFIC PHYSICS — WHAT 1GNITION INTERPRETS

**Measured/physical terms:**
- Flame-base spread rate = slope of base position versus time over a defined interval, cm/s: approximately `v = Δx / Δt` for a steady segment. It describes advancing front motion.
- Visible flame length = position of visible flame tip minus flame base, cm; depends on image/illumination protocol.
- Pyrolysis length = pyrolysis front minus flame base, cm; not necessarily identical to visible flame length.
- Forced flow direction: **concurrent** = gas flow in same direction as advancing flame front; **opposed** = opposite. These are distinct regimes. Do not silently put unknown direction into opposed.
- Thermally expanded gases, developing boundary layers, core-flow acceleration, wall heat transfer, near-wall velocity, and lateral oxygen diffusion are physical mechanisms discussed by the published researchers, not mechanisms newly established by 1gnition.
- Narrow flames may receive lateral oxygen from exposed sides; wide flames in shallower ducts may alter core acceleration. Competing holder/wall heat losses and quenching can reverse simple trends. A single universal monotonic width or duct-height law is unjustified.
- SIBAL is cotton–fiberglass fabric (75% cotton/25% fiberglass in the reviewed paper). PMMA and pure cotton have different material behavior.

**Confinement metric:** A proposed dimensionless ratio `G = w / H` is sometimes useful, where `w` = specimen width in cm, `H` = **full** duct height in cm. `G` alone does **not** identify separate width, height and interaction effects. Identical `G` can arise from different absolute geometries. Preserve original geometry dimensions and definitions.

**Separate Science Lead's proposed log-linear model (NOT fitted or validated on NASA):**

`ln(v_hat/v_ref) = beta0 + beta_u*(u/u_ref) + beta_X*(X_O2-X_ref) + beta_P*ln(P/P_ref) + beta_G*ln((w/H)/G_ref)`

where `v_hat` is predicted positive spread rate, `v_ref` a positive reference rate; `u` and `u_ref` inlet and positive reference flow speeds; `X_O2` and `X_ref` oxygen mole fractions (e.g. 0.217, not 21.7); `P`/`P_ref` pressure and positive reference; `w` specimen width; `H` full duct height; `G_ref` positive reference ratio; `beta` fitted coefficients. Reference choices are scaling conventions, **not calibrated NASA parameters**. A log-linear positive-rate model cannot directly predict zero/extinction, nonmonotonic confinement or full flame shape. Do not use unestimated coefficients to render NASA predictions. This is distinct from implemented M2 Ridge.

**Simple front-travel illustration (optional):** `x(t) = x0 + v*t` with **published measured** or expressly hypothetical fixed rate `v`, elapsed time `t` and starting position `x0`. Label `constant-rate extrapolation/illustration`, not flight footage, full flame simulation, heat/temperature prediction or safety outcome. Do not extrapolate beyond valid intervals/length without a prominent limit.

---

## 5. FINAL PHYSICS HYPOTHESIS AND EXPERIMENT DESIGN

**Question:** At fixed concurrent inlet airflow and atmospheric conditions in microgravity, does reducing full duct height change SIBAL flame-base spread rate differently for 5 cm and 40.6 cm specimen widths?

**Directional hypothesis (untested):** Reducing full duct height increases mean spread rate **more for wide than narrow specimens** under the proposed fixed conditions.

**Proposed 2×2 controlled matrix (20 cm/s concurrent, SIBAL):**

| Full duct height | Narrow 5 cm | Wide 40.6 cm |
|---|---|---|
| 51 cm deep | Historical analog II-5 | Historical analog I-1 |
| 30.5 cm shallow | **NO MATCHING HISTORICAL SAFFIRE CONFIGURATION** | Historical analog IV-SIBAL |

All three historical analogs have unequal other controls and are **not** a valid completed factorial experiment. Adding just the missing fourth cell would not make the historical three fully controlled.

**Controlled protocol to propose:** same batch/composition/areal density/thickness and sample length; same duct planform 109×46 cm where feasible; common entrance-to-igniter distance and mounting; matched oxygen, total pressure, RH, temperatures, ignition, calibrated inlet speed, imaging and analysis protocol; monitor local flow and wall/side clearances; independent new specimens; randomized/block-balanced flights/sessions; same prespecified steady base trajectory window; image calibration/uncertainty; report extinction separately. Three independent burns per cell is a pilot concept, **not** a justified confirmatory sample size.

**Primary interaction on raw-rate scale:**

`Delta = (mean_v_wide_shallow - mean_v_wide_deep) - (mean_v_narrow_shallow - mean_v_narrow_deep)`

`Delta` is in cm/s. `Delta > 0` supports the directional pattern **in a properly controlled replicated experiment**; an estimated positive sign alone, without uncertainty/controls, is not confirmation. Use appropriate independent block/session-level uncertainty estimates. This experiment has **not** occurred.

**Do not claim:** A measured new interaction from historical Saffire records; a NASA-validated width-effect coefficient; a universal law that shallower confinement always increases flame spread; any operational prediction at lunar gravity.

---

## 6. MACHINE LEARNING AND COMPUTATIONAL ENGINEERING

**Existing package:** `IGNIS_ML_Scientific_Revision.zip` → `ignis-ml/`, Python `ignis_ml`, `pyproject.toml`, unit tests, CLI, schemas and docs. `1gnition_Synthetic_Factorial_Verification.zip` extends this package. Preserve it; do not rewrite without reason.

**Models:**
- **M0:** simple mean training baseline (or context baseline). Establishes basic benchmark.
- **M1 `condition_ridge`:** Ridge regression on flow velocity, oxygen %, pressure, material and flow direction. No specimen-width predictor.
- **M2 geometry-aware Ridge:** M1 plus selected geometry feature, currently `sample_width_cm` according to `configs/model_config.json`. Other geometry features are conditional on data quality and approved pre-evaluation plan. **Current M2 does not implement a verified width×duct-height interaction or the Science Lead's log-linear formula.**
- **Proposed future ratio/log-linear candidate:** A separate uncalibrated empirical model; not a replacement for the working M2.
- **Factorial-analysis engine:** `src/ignis_ml/factorial.py` (`analyze_burns`) supports future independently repeated experiment designs; not trained NASA combustion physics.

**Synthetic benchmark:** 72 synthetic observations across 12 artificial groups; condition-only M1 MAE about 0.023995 cm/s; M2 MAE about 0.002589 cm/s (about 89.2% lower) because the synthetic data generator deliberately includes a width effect. It is **software demonstration only**; never put '89% better NASA accuracy' on any page.

**Latest synthetic factorial verification:** `1gnition_Synthetic_Factorial_Verification.zip`, `outputs/synthetic_factorial_verification/synthetic_verification_results.json`. Eight new tests plus previous 69, **77 automated tests passed** in that verification package. Artificial positive, zero, negative true interactions (+0.08/0/−0.08 cm/s) were recovered approximately (+0.07633/−0.00077/−0.0834 cm/s), and an alternative height-session design was tested. The positive scenario's approximate 95% interval was [0.06854,0.08413] cm/s; null scenario interval [−0.00934,+0.00781]. These reflect artificial noise **not NASA confidence intervals**. The generator programmed the answers. Use a bold banner `SYNTHETIC VERIFICATION — NOT NASA DATA`.

**Actual NASA-published-data feasibility study:** `1gnition_Real_Data_Validation_Feasibility.zip`: 39 PMMA rate observations, 18 test IDs, five grouped folds. Preliminary mean-only MAE 0.0024153 cm/s, airflow-only Ridge 0.0027059 cm/s, flow+geometry Ridge 0.0022923 cm/s. Approximate post-hoc resampling interval for improvement includes 0; test ID independence and transcription need further verification. Not canonical M1/M2, not SIBAL, not Saffire transfer, not established improvement. **Keep in technical research notes**, not a NASA-prediction accuracy card.

**Critical model readiness:** `scientific_comparisons.json` returns `prediction_status: "VALIDATION_NOT_SUPPORTED"` and `prediction_cm_s: null`. All 8 published Olson records have `approved_for_ml: false`. Existing ML outputs `candidate_evaluation_refusal.json`, `starter_evaluation_refusal.json` explain why experimental group training is blocked. If users enter unsupported conditions, respond with a comprehensible evidence and uncertainty explanation, not invented numbers.

**General output statuses from model prediction backend:** `SUPPORTED`, `LIMITED_EVIDENCE`, `UNSUPPORTED` (and input-error envelopes); `SUPPORTED` numerical data only when a genuinely reviewed model exists, or clearly bannered synthetic-only fixture. Review all `synthetic`, `domain`, `limitations`, and `validation` fields. A `null` prediction must stay null. Do not derive a validated status from site-side minimum row count. Review source, grouping, domain and approval independently.

**Validation requirements for future real M2:** independent burn/flight/run IDs; identical spread-rate target definitions, units, consistent fuel/material, oxygen/pressure at measurement time, verified full geometry and flow, source provenance, dependency groups, frozen features/hyperparameters, grouped independent held-out campaigns/target scale, MAE/RMSE and uncertainty. Existing evidence insufficient for this strong cross-scale claim.

**Backend modules/documentation to examine:** `docs/SCIENCE_FRONTEND.md`, `docs/DASHBOARD_INTEGRATION.md`, `docs/DATA_REQUIREMENTS.md`, `docs/VALIDATION_PROTOCOL.md`, `docs/request.schema.json`, `docs/response.schema.json`, `docs/data_contract.json`, `src/ignis_ml/{science.py,factorial.py,prediction.py,evaluation.py,models.py,validation.py}`, `configs/model_config.json`. A full authenticated production API is **not** supplied in the ML ZIP; it is an importable library/CLI with static JSON exports.

**Reproduction from ML package root:**

```bash
python3 -m pip install -e .
python3 -m ignis_ml.science
python3 scripts/verify_factorial_synthetic.py  # in synthetic-extension package
python3 -m unittest discover -s tests -v
```

---

## 7. WEBSITE STRUCTURE AND EXPECTED USER INTERACTIONS

**Preserve and improve the existing `ignis-site.zip` static site** with `index.html`, `js/`, `css/`, `img/`, `data/`, `DATA_CONTRACT.md`, `tools/check-matching.cjs`. Do not discard the frontend teammate's current work. Initial site uses `js/config.js`, default static JSON mode, fallback `data/seed.js`; JSON endpoints can replace it later. Its `predictions.json` is empty in the reviewed older build. Do not infer current frontend deployment status from that ZIP; inspect actual latest repo/site first.

### Persistent scenario selector

Accessible on all views: habitat context (clearly assumed/non-measured), material, fuel/measurement question, oxygen %, pressure kPa, airflow cm/s, flow direction, gravity regime, optionally sample width/length and duct geometry. Defaults must say their source or `illustrative assumption`. When a user adjusts a scenario, update matching, evidence support, coverage and warnings, but **never fabricate a new combustion prediction**.

### View 1 — COMPARE RUNS (featured opening)

- Show four-run 2×2 demo: rows **narrow 5 cm** and **wide ~40.6 cm**; columns **20 cm/s flow** and **25 cm/s flow**. Historical run IDs: II-5, II-6, I-1, III-1 respectively.
- The original Urban four-run flame-size results are 4 cm (20 flow) and 5 cm (25 flow) at both sample widths. Clearly label these `steady flame size` from Urban 2021. Offer a **separate, source-linked Olson 2023 flame-length vs spread-rate comparison** with updated actual flight atmospheres and dimensions. Do not mix table fields or silently overwrite one source's measurements.
- Make pair selection interactive. Default I-1 vs II-5. Switch to III-1 vs II-6 and I-1 vs IV-SIBAL; for I vs IV show +100% and confounding instead of a causal claim.
- Matched/different/unknown/conflicting conditions displayed side by side; explanatory text changes when selected pair changes. Show exact source table/row, measurement status, units and limits. Allow source opening.
- If using illustrative front motion from published rates, label `constant-rate illustration based on published table value` (not recreated video or full flame simulation).

### View 2 — EVIDENCE EXPLORER

- List/filter/rank indexed NASA investigations by relevance to selected research question and separately by experimental similarity; explain ranking criteria as heuristic design choices, not physical probabilities.
- BASS PSI-26, BASS-II PSI-25, Saffire I/II/III PSI-98/99/100 are separate. Additional smoke/aerosol and liquid-fuel investigation categories may be represented **only to the extent the source-backed records actually exist**. Do not pretend to have indexed all NASA PSI files.
- Each card includes objective, material, apparatus, gravity, atmosphere, sensors/outcomes, source links and missingness. Drill down to individual available runs.
- Filters: material, outcome (flame size, spread rate, smoke, extinction), flow regime, gravity, oxygen/pressure bands; explain absent data vs absence of phenomenon.
- Scenario similarity is not experimental independence or eligibility for numerical prediction.

### View 3 — SCALE TRANSFER LAB (science highlight)

Provide three clearly separated modes:

**(A) Published NASA Evidence:** Source-linked 2023 table results, three comparisons, optionally Figure 10 reconstruction. Surface measured vs inferred fields, rate and length switch, confounding analysis, source conflicts, and `VALIDATION_NOT_SUPPORTED` status for real NASA predictions. Do not display a numerical result for arbitrary custom user scenario unless it is an observed existing case.

**(B) Synthetic Method Verification:** Selector `Positive / Zero / Negative / Alternative session design` from real synthetic-results JSON; chart four artificial means; show *true inserted interaction*, calculated interaction, approximate 95% interval and refused invalid cases. Large visible `SYNTHETIC VERIFICATION — NOT NASA DATA / NOT PHYSICAL VALIDATION` banner. Never pool with NASA data or use its uncertainties as NASA uncertainty.

**(C) Proposed Experimental Test:** 2×2 width × height grid with historical analogs and missing narrow/shallow, **all historical cells flagged as confounded**, rationale for independent replication, physical hypothesis, interaction equation and what measurements/controls would be required. The log-linear exploratory ratio formula may be shown as `proposed model, not fitted` with all coefficients undefined/uncalibrated; do not imply a working simulator.

Optional technical subsection: M0/M1/M2 descriptions and synthetic MAE clearly labeled *software benchmark, not NASA accuracy*; exploratory PMMA appendix only if scientifically reviewed.

### View 4 — RESEARCH GAPS

- Distinguish **missing experiment configuration**, **missing run identity**, **missing oxygen/pressure/geometry/flow history**, **source conflicts**, **insufficient independent replication**, and **out-of-domain scenario**.
- Show the targeted `5 cm width × 30.5 cm full duct height @ 20 cm/s concurrent, SIBAL` historical gap, and why a single new burn still would not make the entire historical set controlled.
- Report which indexed configurations actually exist and what they measure. Avoid universal statements such as 'NASA has never tested this' unless globally verified.
- Provide an actionable proposal: factor to change, factors to hold fixed, measure (flame-base trajectory and spread rate), independence/blocking, diagnostics, sources.
- Optional oxygen/pressure coverage plot should be labeled coverage of **the team's indexed dataset**, not all NASA research.

### Overall UI/UX design

A sophisticated but uncluttered research interface: near-navy/dark charcoal, warm orange flame accent, restrained cyan for data, white accessible text, generous spacing, clear typography, subtle meaningful animation, responsive/mobile friendly. **1gnition** wordmark/logo throughout; stop displaying IGNIS in user-facing brand while leaving import/module filenames intact. Use authentic, credited NASA imagery where licensed/appropriate and simple diagrammatic visualizations. Emphasize functional demonstration above decorative gimmicks. Provide explanatory tooltips for scientific terms (flame spread, quench, concurrent/opposed, uncertainty, provenance). Avoid false confidence badges and fake 'safe/unsafe' outputs. Accessible focus, keyboard navigation, reasonable contrast, load/error/empty states and direct source-link actions. Keep performance lightweight.

---

## 8. DATA/API INTEGRATION — CANONICAL CONTRACTS AND EXISTING MISMATCH

**The old frontend and new ML outputs DO NOT share a single schema.** The existing site reads eight legacy JSON collections from `data/`: `meta.json`, `sources.json`, `investigations.json`, `runs.json`, `spread_rates.json`, `findings.json`, `flags.json`, `predictions.json` (empty for unvalidated real models). `DATA_CONTRACT.md` defines their fields, provenance and units. The new scientific package separately exports `outputs/scientific_comparisons.json` with:

```json
{
  "schema_version": "1.0",
  "prediction_status": "VALIDATION_NOT_SUPPORTED",
  "prediction_cm_s": null,
  "table1_records": ["8 published table row objects"],
  "comparison_cases": ["3 comparison objects"],
  "factorial_readiness": {"status": "INCOMPLETE_HISTORICAL_DESIGN"},
  "alternative_source_claims": {"...": "source crosswalks"}
}
```

**This skeleton illustrates shape only, not an actual payload. Use the actual generated file.**

Actual `comparison_cases` include `baseline`, `comparison`, `measurements` (arrays ordered `[baseline,comparison]`), `difference_cm_s`, `ratio`, `percent_change`, `source_id`, `source_locations`, `comparability` rows, `confounding_warning`, `interpretation: descriptive_only`. `factorial_readiness` includes the four cells, `historical_ids`, `missing_configuration`, `hypothesis`, `hypothesis_status: UNTESTED`, `interaction_cm_s: null`, `interval_cm_s: null`, `reason` and protocol.

**Backend integration assignment:** Build a safe adapter/loader mapping new scientific records onto UI presentation models **without losing original source-specific fields or measurement status**. Preserve provenance and canonical IDs; add an explicit discriminator such as `evidence_class` (`published_numeric`, `digitized`, `synthetic`, `derived_comparison`, `proposed_experiment`). Never accidentally replace flame length with spread rate. Do not copy 2023 full duct height into legacy 2021 `duct_height_cm` while pretending they share a common definition.

**Frontend integration assignment:** Load `/data/scientific_comparisons.json` alongside the legacy collections, and load `/data/synthetic_verification_results.json` only for the separately labeled synthetic tab. Maintain old features while adding new panels. For fastest reliable hackathon deployment, precomputed JSON + client-side deterministic comparisons are acceptable; a hosted inference API is optional. If adding an API, follow `docs/request.schema.json` and `docs/response.schema.json`, validate input, return explicit statuses/abstention, handle CORS/security, and never expose model artifacts/API keys to the browser.

**Old frontend `GATE` warning:** `js/config.js` includes heuristic minimum row/flight thresholds (`min_spread_rows:6`, `min_flights:3`). These are **not** scientific approval. Real prediction permissions must be controlled by backend review/fingerprint, data validation, and the `VALIDATION_NOT_SUPPORTED` state. Disable any old UI that turns a threshold into 'validated model available'.

**Source and missingness contracts:** `null` for missing, 0 only for measured zero; fields explicit units `_cm`, `_cm_s`, `_mm_s`, `_kpa`, `_pct` or `oxygen_vol_pct`; convert 2.1 mm/s to 0.21 cm/s, oxygen 0.217 fraction to 21.7%, do not mix pressure units. Keep `source_id`, `source_locator` / `source_location`, original-source link and measurement method. Let user open the paper/PSI page.

**Representative file-copy plan:**

```text
DATA revision ZIP                 → /research/sources/ and a versioned canonical dataset
ML revision ZIP                   → /backend/ignis-ml/ (keep import ignis_ml)
ML scientific_comparisons.json    → /frontend/data/scientific_comparisons.json
Synthetic verification JSON      → /frontend/data/synthetic_verification_results.json
Existing ignis-site.zip          → /frontend/ (preserve teammate edits)
Real PMMA preflight ZIP          → /research/technical-exploration/ (NOT model validation)
```

Do not blindly overwrite newer teammate files. Inspect the actual current repository and merge carefully.

---

## 9. TECHNICAL AND SCIENTIFIC QA / ACCEPTANCE TESTS

**Data and science:**
1. Load exactly eight canonical Olson Table 1 records; seven SIBAL and one cotton; no duplicate counting with Figure 10 or PSI-99.
2. Verify I-1 vs II-5: +0.03 cm/s, +16.67%, both flame lengths 4 cm; III-1 vs II-6: +0.03 cm/s, +13.04%, both lengths 5 cm; I-1 vs IV-SIBAL: +0.18 cm/s, +100%, lengths 4 vs 8.5 cm.
3. Display source-specific O₂/pressure/geometry accurately; use the Olson Table 1 values for the featured rate comparisons; show Urban Table 2 separately as historical flame-size source; retain identified PSI flow conflicts.
4. Never combine cm flame length with cm/s rate or turn 20/25 cm/s airflows into oxygen concentrations.
5. Figure 10 markers are approximate digitizations; x-axis concurrent left/opposed right; point/run IDs unresolved; manual reading uncertainty not mistaken for experimental uncertainty.
6. BASS/BASS-II and materials distinct; no hard joins on provisional run aliases.
7. Missing proposed factorial cell is 5 cm width × 30.5 cm full height at nominal 20 cm/s concurrent; historical analogs are flagged incomplete/confounded. No confirmatory historical interaction statistic.
8. No NASA prediction number from invalid/missing scenario; `prediction_cm_s` stays null; unsupported requests explain reasons. No synthetic performance claimed as NASA predictive accuracy.
9. Synthetic verification mode explicitly states artificial data and correctly shows expected/estimated +/-/0 interactions; invalid designs refused.
10. Source links lead to the correct specific paper/report and source location.

**Engineering and UX:**
11. Re-run latest Python tests (77 in synthetic extension) and existing JS matching regression tests; record environment, commands and counts. Passing unit tests are not proof of integrated site QA.
12. Confirm every scenario input actually updates downstream comparison/matching or visibly indicates no supported data; no fake working controls.
13. Test homepage, four tabs, pair selector, outcome toggle, sources, filters, charts, mobile widths, keyboard behavior, unknown inputs, broken links, offline/static fallback, performance and navigation.
14. Ensure no `NaN`, `undefined`, `null` rendered as an invented zero, cached prior prediction after refusal, or page crash when JSON unavailable.
15. Confirm identical source values across chart, cards, tooltips, downloads and video/deck; label rounding and basis for percentages.
16. Rebrand user-facing name/logo to **1gnition** consistently.
17. Publish and verify public site URL; no private local paths or missing assets. If an API is deployed, test CORS, runtime response, errors, rate limiting/security as appropriate.
18. Give Scientific Lead/QA member at least 5–8 source-reviewed cases, including confounded and missing-data cases, to check classifications. Report results truthfully; don't call a handful of tuned examples an independent accuracy study.

**Acceptance demo (must work end-to-end):** Open 1gnition → choose Saffire I-1 vs II-5 → reveal both lengths 4 cm and rates 0.18 vs 0.21 cm/s → show 16.67% difference and changed width/length/O₂/flight → switch to III-1 vs II-6 and I-1 vs IV → show limitations, not false causal attribution → open Scale Transfer Lab → see real NASA prediction `VALIDATION_NOT_SUPPORTED` → open separate synthetic verification mode and inspect +/-/0 cases → open Research Gaps → see the untested width×height 2×2 design and missing historical analog → click a source.

---

## 10. TEAM OWNERSHIP / IMPLEMENTATION ORDER

**Frontend Lead:** Keep current implementation. Rebrand; integrate canonical scientific JSON and separate synthetic tab; implement real experiment comparison, 2×2 matrix, details/flags/provenance, charts, responsive states and narrative. Deliver working build/public URL and screenshots.

**Backend Lead:** Freeze canonical dataset/source manifest; generate/rebuild scientific JSON; add schema adapter/validation and deterministic evidence-comparison endpoints or static exports; preserve refusal logic; document exact JSON contracts and deployment; don't activate unsupported predictors. Deliver reproducible commands and integration notes.

**ML Lead:** Verify imported M0/M1/M2/factorial modules and tests; verify all numerical comparisons, model states, synthetic-only flags and no fabricated real predictions; help front end map model readiness; keep uncalibrated log-linear model distinct. Deliver concise review sign-off.

**Scientific Lead:** Approve outcome definitions, three descriptive comparisons, attribution of physical mechanisms, unresolved source conflicts, untested directional hypothesis, controlled-design assumptions and final claims. No need to invent experimental confirmation.

**Data Lead:** Maintain primary-source links and duplicate crosswalk; recover raw data only if specifically useful and time permits; keep canonical dataset frozen and evidence quality labels exact.

**QA/Presentation Lead:** Independently check 5–8 grounded comparison examples, verify calculations/links/logic, capture a real website demo, prepare 7-slide/story media with only shipped features, ensure current public links.

**P0 order:** 1) Pull latest actual frontend repo and source packages. 2) Reconcile schema and add science JSON. 3) Ship three featured comparisons and evidence warnings. 4) Add factorial grid and synthetic verification tab. 5) Run tests and scientific QA. 6) Deploy and capture actual product demo. 7) Freeze scientific claims and submit. **Do not let new M2 model fitting, CFD ambitions or full NASA raw telemetry recovery block the existing grounded demonstration.**

---

## 11. APPROVED FINAL PROJECT NARRATIVE

**Problem:** NASA's microgravity fire experiments are scientifically valuable but differ in geometry, flow, atmosphere, material, measurement procedures and independence. A small-scale result cannot be transferred to a larger configuration solely because a single nominal variable matches.

**What we measured/reconstructed:** Published Saffire pairs have equal reported flame lengths yet differing spread rates; among published configurations the I→IV SIBAL spread rate doubles, but other factors also change. These are descriptive results from existing NASA-associated publications, not new burns by our team.

**What we investigated physically:** How confinement, specimen width, boundary-layer development, thermal expansion, lateral oxygen diffusion and near-wall conditions complicate cross-scale interpretation. Published authors already discuss these mechanisms; 1gnition makes them traceable to particular experimental contrasts and uncertainties.

**What our technology contributes:** Source-linked NASA evidence exploration, comparison rules, confounder/missingness detection, backed-by-tests ML research tools, explicit refusal of unsupported predictions, and a testable experiment design that explains what data are needed next.

**What we did not establish:** A statistically significant isolated width effect, an experimentally validated width×height interaction, successful M2 prediction on unseen Saffire experiments, or a physics-accurate spacecraft fire simulation.

**Closing line:** **1gnition — Know what the evidence supports.**

---

## 12. EXPECTED FINAL HANDOFF BACK TO TEAM

Return: (1) exact files changed and why, (2) final frontend/backend architecture and data-flow diagram, (3) source-to-UI mapping and field-unit contract, (4) links or copies of produced JSON/build artifacts, (5) test commands and real pass/fail logs, (6) complete scientific QA results, (7) screenshots of core flows, (8) production URL/deployment instructions, (9) known limitations and unimplemented features, (10) list of final items requiring Scientific Lead approval.

**No unsupported claims of completion.** If a capability is static/demo-only, label it. If a true service isn't deployed, say so. If the current frontend differs from the archived ZIP, update this plan against the real repo rather than overwriting teammates' newer work. Produce a coherent, testable product that demonstrates existing NASA observations before extending speculative modeling.
