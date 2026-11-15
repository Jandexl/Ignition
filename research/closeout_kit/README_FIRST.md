# 1gnition — Scientific Closure + Deployment Fix Kit

This kit accompanies the original full engineering handoff. It is a **data and QA patch**, not a replacement for your latest frontend/backend repository. It does not claim the current public website or API has been deployed or tested.

## Correct project status

**Science research = completed for the submission.** The Scientific Lead's Nov. 15 final decision verifies all eight Olson Table 1 records, three descriptive Saffire comparisons, source caveats, and the proposed factorial hypothesis. Experimental confirmation and NASA-trained scale-transfer prediction are still future work. **Final website claims review = not evidenced on the latest build**, a narrow engineering QA issue, not a missing research sign-off.

## Priority fixes before deployment

1. **Data-driven conflicts (P0):** Place `data/source_conflicts.json` in the site's data directory or expose it from the Python API. The UI must render both source claims and their provenance; do not use hard-coded explanatory text or blindly replace source numbers.
   - PSI-100 S1 candidate vs Olson III-1: 30 vs 25 cm/s. Preserve unresolved status.
   - IV-1 vs IV-SIBAL: probable alias/crosswalk. Do not assert exact identity or count both as separate independent burns.
2. **Prediction gate (P0):** `scientific_comparisons.json` has `prediction_status=VALIDATION_NOT_SUPPORTED`, `prediction_cm_s=null`. Never fill that null from synthetic Ridge models or a proposed log-linear equation.
3. **Public branding (P0):** Use `data/brand_copy.json` (ZERO GUESSING. / ZERO HIDDEN UNCERTAINTY. / 1gnition). Include a factual methodology note: models and interpretations retain assumptions and uncertainty. The marketing slogan is not a claim of zero uncertainty or zero prediction error.
4. **Rule-based helper (P0 clarity):** Name "Ask 1gnition", label "Offline rule-based evidence helper", disclose it is not a generative AI. Do not claim it is AI-powered if it's not.
5. **API deployment (P0 only if frontend requires runtime API):** If all user journeys work from precomputed audited JSON + deterministic browser logic, a fully functioning static deployment is acceptable. If the frontend calls a runtime API, deploy and configure that API publicly before announcing deployment. Do not claim a hosted endpoint merely because `uvicorn` or equivalent can run locally.
6. **Final website review (P0):** Record pass/fail evidence for eight cases in `data/final_ui_qa_cases.json`. Get the Scientific Lead or a delegated QA member to sign off *only on new wording and display of source disputes*. Do not require redoing the earlier scientific investigation. No evidence supplied of completed latest-site QA, so mark it pending until verified.
7. **Release gate:** Test static assets/API URLs, CORS if relevant, refresh/deep links, comparison buttons, mobile, citations, no synthetic mixing, and visible unvalidated prediction status. Capture a 6–7-second genuine screen recording for the video after this passes.

## Canonical measurements

- I-1 vs II-5: flame length 4/4 cm; spread rate 0.18/0.21 cm/s; +16.67%.
- III-1 vs II-6: flame length 5/5 cm; spread rate 0.23/0.26 cm/s; +13.04%.
- I-1 vs IV-SIBAL: rate 0.18/0.36 cm/s; +100%; duct 51/30.5 cm; oxygen 21.7/23.1%; atmospheric, specimen length, imaging and flight differences.
- Duct×width directional interaction: **hypothesis**, not physically confirmed. Four-cell historical design incomplete.

## Suggested frontend integration

```js
const [science, conflicts, brand, status] = await Promise.all([
  fetch('/data/scientific_comparisons.json').then(r => { if (!r.ok) throw new Error('Science data missing'); return r.json(); }),
  fetch('/data/source_conflicts.json').then(r => { if (!r.ok) throw new Error('Conflict data missing'); return r.json(); }),
  fetch('/data/brand_copy.json').then(r => { if (!r.ok) throw new Error('Brand copy missing'); return r.json(); }),
  fetch('/data/science_project_status.json').then(r => { if (!r.ok) throw new Error('Project status missing'); return r.json(); })
]);
// Render conflicts.conflicts by source ID, and display each claims[] separately.
// science.prediction_cm_s === null means do not render a NASA numerical prediction.
```

This is a **reference snippet**, not a direct patch for a latest repo which has not been supplied here. Frontend can keep its existing fetching and caching architecture if it produces equivalent behavior.

## Verification

From this folder:

```bash
python3 -m unittest discover -s tests -v
```

These local tests validate the supplied canonical data and patch consistency. They do **not** substitute for browser QA of the actual latest website.

## Deployment checklist

- [ ] Latest frontend code (not old `ignis-site.zip`) integrates sidecar data
- [ ] Latest backend/static JSON exports and refs work in production
- [ ] Both conflicts rendered with source provenance and uncertainty
- [ ] All 8 integrated UI QA cases pass and the check log is saved
- [ ] Hero and naming use 1gnition + requested ZERO headlines
- [ ] Ask 1gnition accurately discloses offline rules
- [ ] Live API URL verified if required, or all calls use static data
- [ ] Public website URL loads successfully across all four views
- [ ] Actual site 6–7 sec capture saved for submission video

**Don't block deploy on:** new microgravity burns, an unvalidated cross-scale predictor, a generative chatbot, or redoing the scientific literature investigation.
