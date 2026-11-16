# 1gnition — engineering handoff report

**Date:** 15 November 2026 · **Status:** released. Science is complete for submission (Scientific Lead decision, 15 Nov). This report covers engineering integration and QA only.

Public site (static, complete): https://claude.ai/artifact/519TnVzzHEeWpvkrSwT34u · artifact version `1794773977-cec5` and later (see section 0).

---

## 00. Synthetic model demo and Render connection (16 November 2026)

| Request | Status | Evidence |
|---|---|---|
| Connect the saved `SYNTHETIC_DEMO_MODEL.joblib` to an interactive demo | Done | `backend/service/synthetic_demo.py`, `POST /api/synthetic-demo`, **Scale transfer → B · Synthetic check → Try the synthetic model** |
| Inspect required inputs and supported domain first | Done | Inputs: airflow 5–22 cm/s, oxygen 20–23 %, pressure 90–100 kPa, width 2–8 cm, direction concurrent/opposed. Fixed: `synthetic_fabric`, 30 cm × 0.3 mm sample, 10 cm duct, `synthetic_microgravity`. Plus a local-distance check (≤ 0.35). Served live at `GET /api/synthetic-demo/domain` |
| Use the existing load and predict functions | Done | `ignis_ml.prediction.load` and `ignis_ml.prediction.predict`, unchanged; no refit, no clipping, no number computed in the browser |
| Keep NASA measurements and sources | Done | All NASA data and views unchanged; `/api/predict` still never returns a number; the demo card links back to Olson Table 1 |
| Label synthetic predictions clearly | Done | "SYNTHETIC · invented data · not NASA" stamp on every answer; API returns `not_nasa_data: true` and `SYNTHETIC_DEMO_ONLY`; frontend refuses any answer not labelled synthetic |
| Report what blocks the real-data pipeline | Done | `backend/ignis-ml/docs/REAL_DATA_PIPELINE_STATUS.md`, `test_logs/10_real_data_pipeline_check.txt` |
| Connect the frontend to https://onegnition.onrender.com | Done in code, **live after push** | `frontend/js/config.js`; `render.yaml`; `DEPLOYMENT.md`. The live service still runs the previous commit, which passes only some of the 12 checks (no synthetic demo yet) (`test_logs/12_...`). The same code under Render's settings passes 12 of 12 locally (`test_logs/11_...`) |

**Safety:** the model file is unpickled only after its SHA-256 matches `MANIFEST.sha256`. At start-up it must reproduce the saved reference (0.121519 cm/s, to within 1e-9), or the demo is disabled. Library versions are pinned to the ones the model was saved with.

**Needs a person:** approve the GitHub push, then set `IGNITION_CORS_ORIGINS` on Render as in `DEPLOYMENT.md` (the live service currently sends no CORS header, so a GitHub Pages copy can't reach it). After that, run `python3 backend/service/check_deploy.py` and expect 12 of 12.

---

## 0. Closeout release (science-closed deployment kit)

| Definition of done | Status | Evidence |
|---|---|---|
| (a) No unsupported scientific predictions | Done | `prediction_status: VALIDATION_NOT_SUPPORTED`, `prediction_cm_s: null`; QA07; build check |
| (b) Comparisons and conflicts traceable to sources | Done | Every value links to a Table 1 row or PSI record; both conflicts render all claims with locator and link (QA02, QA05, QA06) |
| (c) All 8 UI QA cases passed | Done (engineering) | `qa/final_ui_qa_results.json`, screenshots `qa/QA0*.png`, `test_logs/07_final_ui_qa_8_cases.txt` |
| (d) No dead API/data dependencies | Done | Every feature runs from static JSON (`DATA_MODE: "files"`, `PREDICT_ENDPOINT: ""`); QA08 found no failed requests |
| (e) Working public URL | Done, with one manual check left | Deployed files are byte-identical (SHA-256) to the tested build. Automated browsers are stopped by claude.ai's Cloudflare check, so open the link once by hand |
| (f) Actual demo footage | Done | `1gnition_demo_capture_7s.mp4`: 1920×1080, 30 fps, 7.0 s, filmed from the real site |
| (g) Final brand copy | Done | Hero ZERO GUESSING. / ZERO HIDDEN UNCERTAINTY. / 1gnition + "Know What the Evidence Supports." from `data/brand_copy.json` |

**What changed in this release**

- **Source conflicts are now data.** `data/source_conflicts.json`, copied from the kit by the build, drives the Conflicting column, a new Data → Source conflicts tab and the Research Gaps count. The hard-coded `KNOWN_CONFLICTS` and `URBAN_OF` tables were removed, and a backend test fails if they come back.
  - **III-1 airflow:** Olson 25 cm/s and PSI-100 candidate S1 30 cm/s, shown side by side and *unresolved*.
  - **IV-SIBAL ↔ IV-1:** *probable, not confirmed*; table 0.36 and digitized ≈0.368 cm/s shown separately and not counted as a second run.
- **The build pipeline checks the kit.** It copies the kit sidecars, refuses to build if the kit's `scientific_comparisons.json` differs from the package export (they are identical), and adds 9 conflict and brand checks (71 total).
- **Hero and title use the approved brand copy.** A visible qualifier sits under the hero: the methodology still states assumptions, unknowns and source conflicts.
- **Ask 1gnition is labelled** "offline · rule-based", with the kit's disclosure: an offline rule-based evidence helper, not a generative AI assistant.
- **New QA tooling:** `frontend/tools/final_ui_qa.py` runs the kit's 8 cases.

**Still needed from people, not code**

1. The Scientific Lead or QA should read only the new wording and the conflict displays (`qa/QA02.png`, `QA05.png`, `QA06.png`).
2. Someone should open the public link once in a normal browser and click through the views.
3. `science_project_status.json` is the science team's record and was not edited. Its "NOT_VERIFIED / NOT_YET_EVIDENCED" fields can be updated by its owner using the evidence above.

---

## 1. Files changed and why

**Baseline.** The `ignis-site.zip` in the handoff was an older branch (the Cygnus-hero build). The live site was newer, with the round 6–8 design, the 1gnition rename and the first science integration. I kept the live site and merged in the handoff branch's data and logic fixes. No teammate data was overwritten.

### Frontend (`frontend/`)

| File | Change |
|---|---|
| `js/logic.js` | Took the handoff branch's stricter matching: `L.num` rejects "20abc"; unknown values are never matches; applicability needs one run that matches every condition; similarity is scored per run. Added the flow-direction check. The ISS preset is labelled an illustrative assumption. |
| `js/app.js` | **Compare Runs:** new Olson 2023 section with a pair picker (I-1/II-5 by default, III-1/II-6, I-1/IV-SIBAL), a length/rate/both toggle, and a 4-column matched / changed / unknown / conflicting matrix with the "Descriptive comparison · causal effect not isolated" warning. The Urban table no longer duplicates gravity and flow direction, and its unknown values show as unknown. **Scale Transfer:** modes A Published evidence, B Synthetic check, C Proposed test, plus NASA prediction and Your scenario; the backend scenario-check panel; the unfitted log-linear model; the protocol. **Research Gaps:** six computed gap types and the 2×2 design. **Data:** tabs for Olson Table 1, Figure 10, PSI-99 and synthetic data, with evidence-class banners. **Throughout:** glossary popovers for 11 terms, Overview counts that include Table 1, guided demo rewritten to the spec's acceptance flow (20 steps), and a fix for a lost click when a scenario field loses focus. |
| `js/data.js`, `js/config.js` | 13 collections, of which 4 are optional and don't break the page if missing. `PREDICT_ENDPOINT`. `GATE` is documented as a legacy heuristic, not approval. |
| `js/story.js` | Overview tiles for the 8 Table 1 rates and the evidence-class breakdown, which also fill the earlier dead spaces. |
| `index.html`, `css/story.css` | Flow-direction field, new panes and containers, footer closing line and attribution, styles for the new panels. |
| `data/investigations.json` | Combined records split: Saffire-I/II/III → PSI-98/99/100; BASS → PSI-26 and BASS-II → PSI-25. Materials notes cite their sources. |
| `data/runs.json`, `spread_rates.json` | Investigation IDs remapped. Flow direction "concurrent" with its audit source, from the handoff branch. |
| `data/flags.json`, `meta.json` | Nominal-conditions flag and Figure 10 markers from the handoff branch. |
| `data/sources.json` | 12 sources from the science manifest added. |
| `data/scientific_comparisons.json`, `synthetic_verification_results.json`, `synthetic_model_benchmark.json`, `evidence_catalog.json`, `build_manifest.json` | **Generated** by the backend pipeline. Do not edit by hand. |
| `tools/check-matching.cjs` | The handoff branch's JS regression test, kept. |
| `tools/acceptance_ui.py` | New browser acceptance test (41 checks). |
| `docs/` | Scientific methodology, lead decision and frontend notes, linked from the site. |
| `DATA_CONTRACT.md`, `README.md` | New collections, the `evidence_class` table and backend connection instructions. |

### Backend (`backend/`)

| Path | Change |
|---|---|
| `ignis-ml/` | The team's package, **unchanged** (the synthetic-extension version). 77 tests. |
| `service/build_frontend_data.py` | New. Re-exports the science JSON, copies synthetic results and the benchmark, writes the evidence catalog and manifest, runs 62 acceptance checks, rebuilds `seed.js`. |
| `service/evidence.py` | New adapter. Adds an `evidence_class` to every item, does deterministic pair comparison and runs the acceptance checks. Changes no source value. |
| `service/server.py` | New stdlib API: `/api/health`, `/api/<collection>`, `POST /api/compare`, `POST /api/predict` (schema-validated, never numeric). |
| `service/tests/test_backend.py` | New, 18 tests. |

### Research (`research/`)

Copied as delivered: the scientific data revision (identical to `ignis-ml/data/revision`), the exploratory PMMA feasibility study, the synthetic-verification chart and the original handoff prompt.

---

## 2. Architecture and data flow

```
 research/scientific_data_revision  ==  backend/ignis-ml/data/revision/*.csv   (Olson T1, Fig 10, PSI-99, cases, matrix)
                     │
                     ▼  ignis_ml.science.export_evidence           ignis-ml/scripts/verify_factorial_synthetic.py
 backend/service/build_frontend_data.py ──────────────────────────────────────┐
   ├─ scientific_comparisons.json      (canonical, byte-identical to team's)   │
   ├─ synthetic_verification_results.json  (SYNTHETIC)  ◄─────────────────────┘
   ├─ synthetic_model_benchmark.json       (SYNTHETIC, from outputs/synthetic_evaluation.json)
   ├─ evidence_catalog.json  (48 items × evidence_class)
   ├─ build_manifest.json    (sha256 in/out, 62 checks, prediction_cm_s: null)
   └─ seed.js                (offline copy of all 13 collections)
                     │
        frontend/data/*.json  ──────────────┬───────────────────────────────┐
                     │                      │                               │
          static host (Pages, artifact)     backend/service/server.py       opened from disk
          DATA_MODE "files"                 GET /api/<collection>           (seed.js)
                     │                      POST /api/compare
                     │                      POST /api/predict → ignis_ml.prediction.predict(bundle=None)
                     ▼                      ▼
   js/data.js (load + validate) → js/logic.js (matching, rules) → js/app.js / story.js (views)
   One scenario object S feeds Evidence, Compare, Transfer, Gaps and the Ask panel.
```

---

## 3. Source-to-UI mapping and field/unit contract

| UI element | Field(s) | Source | Unit / class |
|---|---|---|---|
| Compare → Urban grid and condition table | `runs[].steady_size_cm`, `airflow_cm_s`, `duct_height_cm` | Urban 2021 ICES-2021-266 Table 2 | cm; published_numeric (source-scoped) |
| Compare/Transfer → length panel | `table1_records[].flame_length_cm`, `pyrolysis_length_cm` | Olson 2023 Table 1 | cm; published_numeric |
| Compare/Transfer → rate panel | `spread_cm_s`, `comparison_cases[].difference_cm_s`, `percent_change`, `ratio` | Olson T1; arithmetic by `ignis_ml.science` | cm/s, % of baseline; derived_comparison |
| Matched / changed / unknown | `comparison_cases[].comparability[]`, `confounding_warning` | science package matrix | |
| Conflicting | Urban run vs Olson record (same burn); PSI-99 `flow_velocity_cm_s`; PSI-100 audit note | Urban T2, Olson T1, PSI-99, PSI-100 | archive_claim |
| Cross-checks, Data → Figure 10 | `alternative_source_claims["ignis_spread_rates_reviewed.csv"]` | Urban 2021 Fig. 10, digitized | cm/s; digitized; ±0.01 = reading envelope |
| 2×2 design (Transfer C, Gaps) | `factorial_readiness` | science package | proposed_experiment |
| NASA prediction | `prediction_status`, `prediction_cm_s` | science package | null, never 0 |
| Synthetic mode | `synthetic_verification_results.json` | `verify_factorial_synthetic.py` (seed 20261115) | synthetic |
| Model code benchmark | `synthetic_model_benchmark.json` | `outputs/synthetic_evaluation.json` | synthetic; "not NASA accuracy" |
| Replay | `spread_rates[SR-saffire1-avg].rate_mm_s` = 1.8 mm/s = 0.18 cm/s | Urban 2021 / Olson T1 I-1 | constant-rate illustration |
| Gaps map | `runs[].o2_pct`, `pressure_kpa` | Urban T2 | "team's indexed dataset" |

**Units:** suffixes `_cm`, `_cm_s`, `_mm_s`, `_kpa`, `_pct` / `oxygen_vol_pct`. PSI-99 values are shown as printed (mm/s) beside the converted value (÷10 → cm/s). Missing values are `null` and render as "not reported" or "none". Olson `duct_full_height_cm` and Urban `duct_height_cm` are never merged.

---

## 4. Produced artifacts

- `frontend/data/*.json` (13 collections) and `frontend/data/seed.js`
- `backend/service/*`
- Static build: the whole `frontend/` folder (no build step)
- Repository archive: `1gnition-repo.zip`

---

## 5. Test commands and results (logs in `test_logs/`)

Environment: Linux, Python 3.13, Node 22, Chrome via Playwright.

| # | Command | Result |
|---|---|---|
| 01 | `cd backend/ignis-ml && python3 -m unittest discover -s tests -v` | **77 passed** |
| 02 | `python3 -m unittest discover -s backend/service/tests -v` | **18 passed** |
| 03 | `python3 backend/service/build_frontend_data.py --frontend frontend` | **62 of 62** data acceptance checks; science JSON byte-identical to the team's export |
| 04 | `node frontend/tools/check-matching.cjs` | passed |
| 05 | `python3 frontend/tools/acceptance_ui.py` | **41 of 41** browser checks |
| 06 | guided-demo sweep (20 steps, desktop) | no errors; demo closes cleanly; 1 cosmetic overlap (step 2) |
| 07 | live API smoke test (`curl`) | health, predict (LIMITED_EVIDENCE / UNSUPPORTED, null), compare (+100%) |
| 08 | frontend in API mode against `server.py` | collections loaded via `/api`; scenario check rendered "no number" (pre-closeout run) |
| — | **Closeout release re-run (`test_logs/`)** | ignis-ml **77** OK · backend **20** OK · build **71/71** · closeout kit **8** OK · JS matching OK · UI acceptance **41/41** · final UI QA **8/8** · guided demo 20 steps, no errors |

Passing unit tests don't prove scientific correctness. Section 6 is the science QA.

---

## 6. Scientific QA against handoff section 9

| # | Requirement | Result |
|---|---|---|
| 1 | Exactly 8 Olson records (7 SIBAL, 1 cotton), no double counting | Pass. Build check, plus `counts_as_independent_run: false` on all 25 alternative claims |
| 2 | +0.03 / 16.67% / 4 cm; +0.03 / 13.04% / 5 cm; +0.18 / 100% / 4 vs 8.5 cm | Pass (build checks 4–9, UI checks) |
| 3 | Olson values for rate comparisons; Urban shown separately; PSI flow conflicts kept | Pass. Separate sections; II-6 (PSI-99) and III (PSI-100) airflow conflicts listed first |
| 4 | cm never mixed with cm/s; 20/25 shown as airflow | Pass. Separate panels and axes; "Inlet airflow, cm/s" |
| 5 | Figure 10 approximate, concurrent left / opposed right, reading envelope not uncertainty | Pass (cross-check text, Data tab banner) |
| 6 | BASS ≠ BASS-II; SIBAL ≠ PMMA; no hard joins on aliases | Pass. PSI-26 / PSI-25 split; IV alias marked open |
| 7 | Missing cell 5 cm × 30.5 cm at 20 cm/s; analogs flagged confounded; no interaction statistic | Pass |
| 8 | No NASA number; `prediction_cm_s` null; refusals explained | Pass (UI and API; server returns 500 rather than send a number) |
| 9 | Synthetic mode labelled, +/0/− recovered, invalid designs refused | Pass (4 scenarios, 4 refusals) |
| 10 | Source links go to the specific paper or record | Pass for the Olson popover (UCL manuscript). 24 of 25 source URLs returned HTTP 200; the Space Apps challenge page blocks automated checks, so check it by hand |
| 11 | Python and JS tests re-run | Pass, see section 5 |
| 12 | Scenario inputs change downstream output | Pass (habitat → ranking; flow direction → applicability) |
| 13 | Tabs, toggles, sources, phones, keyboard, offline | Pass. 390 px with no overflow; Enter/Space opens popovers and table rows; `seed.js` fallback tested |
| 14 | No NaN, undefined, fake zeros, crash on missing JSON | Pass |
| 15 | Same values across chart, cards, downloads | Pass. All read from one JSON; CSV is built from the same rows |
| 16 | 1gnition branding | Pass (no "IGNIS" in visible text) |
| 17 | Public URL works, no missing assets | Static URL: pass. API: not publicly deployed |
| 18 | 5–8 cases reviewed by the Scientific Lead | **Not done by engineering.** Suggested cases: I-1/II-5, III-1/II-6, I-1/IV-SIBAL, II-5/II-6, IV-SIBAL/V-COTTON (via `/api/compare`), BASS-NARROW/BASS-WIDE (null pyrolysis), Moon base → UNSUPPORTED, ISS-like 21% / 101.3 kPa |

---

## 7. Screenshots (`screenshots/`)

01 Overview hero · 02 Compare I-1 vs II-5 · 03 I-1 vs IV conditions with conflicts · 04 NASA prediction disabled · 05 synthetic verification · 06 proposed test · 07 gap types and 2×2 · 08 Data, Table 1 · 09 Evidence · 10 phone, Compare.

---

## 8. Deployment

- **Static (current):** Claude artifact at the URL above. For the submission, prefer GitHub Pages with folder `/frontend`: it gives working CSV downloads and rendered `.md` links.
- **API (optional):** `python3 backend/service/server.py --frontend frontend --host 0.0.0.0 --port 8787` on any Python host. Then set `DATA_MODE: "api"`, `API_BASE` and `PREDICT_ENDPOINT` in `frontend/js/config.js`, and set `IGNITION_CORS_ORIGINS` to the site's origin.
- **After any data change:** run the build script, re-run tests 01–05, then redeploy `frontend/`.

---

## 9. Known limitations and unimplemented items

1. **The API is on Render's free plan.** It sleeps when idle, so the first request takes up to a minute. The synthetic demo and the backend scenario check need it; every NASA view works without it.
2. **Ask 1gnition is an offline rule-based evidence helper,** labelled as such in the panel header and text. It is not a generative AI assistant, and none is connected.
3. **Claude artifact viewer limits.** It blocks file downloads (Copy CSV works) and shows `.md` documents as plain text.
4. **Fixed in the closeout release:** the PSI-100 airflow conflict and the IV alias now come from `data/source_conflicts.json`. V-COTTON is no longer linked to Urban V-2, because no conflict record supports that link.
5. **BASS-II's 39 PMMA rates are not indexed as runs,** by design. The exploratory feasibility study stays in `research/` and never appears as an accuracy card.
6. **The only model numbers come from invented data:** the M0/M1/M2 benchmark and the interactive synthetic demo. No model has been evaluated on Saffire holdouts. `REAL_DATA_PIPELINE_STATUS.md` explains why.
7. **Small layout issues remain.** The Overview "almost proposed" grid leaves its right column blank until the reveal animation runs, and guided-demo step 2 partly covers the hero map.
8. **Accessibility is only partly verified.** Keyboard and focus were checked, but no automated contrast audit (such as axe) was run.
9. **The handoff branch's Cygnus hero photo was not carried over;** the round-6 hero was kept.
10. **Legacy code is kept but unused.** `L.gate` and `GATE` remain only for the JS regression test.

---

## 10. Items requiring Scientific Lead approval

1. Wording of the three comparison conclusions and the "Descriptive comparison · causal effect not isolated" warning.
2. Every row of the Conflicting column, especially the PSI-100 30 vs 25 cm/s claim and the IV-SIBAL = IV-1 identity note.
3. Investigation split text: BASS (PSI-26) SIBAL-only note, BASS-II (PSI-25) PMMA note, and `psi_confirmed: true` for PSI-25/26/98/99/100.
4. The 11 glossary definitions (spread rate, flame length, pyrolysis length, concurrent, flow direction, full duct height, uncertainty, provenance, quench/extinction, microgravity, SIBAL).
5. The physics attribution in the hypothesis card and footer: "Published authors propose the physics … 1gnition did not discover this."
6. Protocol card (hold fixed / change / measure / replicate) and the presentation of the unfitted log-linear model.
7. Gap-type counts and phrasing on Research Gaps.
8. Synthetic mode and benchmark wording.
9. Guided-demo step texts (steps 12–17 summarise the science).
10. Hero line "Zero gravity. Zero guesswork." as a claim about the product, not the science.
