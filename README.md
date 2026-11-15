# 1gnition — NASA Space Apps 2026, Flame in Freefall

**ZERO GUESSING. ZERO HIDDEN UNCERTAINTY.** *Know What the Evidence Supports.* (Brand lines, not a claim of zero uncertainty: the methodology states its assumptions, unknowns and limits.)

1gnition turns scattered NASA microgravity-combustion measurements into traceable comparisons and research decisions: which runs apply, which comparisons are fair, where the evidence runs out, and what experiment to fly next. It refuses to predict where the data cannot support a number.

Live site: https://claude.ai/artifact/519TnVzzHEeWpvkrSwT34u. It is fully static: every feature runs from the generated JSON in `frontend/data/`, so no runtime API is needed. The optional Python API in `backend/service/` is not hosted.

## Layout

```
frontend/                static site (HTML/CSS/JS, no build step)
  data/                  JSON the site reads; 5 science files are generated, see DATA_CONTRACT.md
  docs/                  methodology and decision notes linked from the site
  tools/                 make_seed.py, check-matching.cjs (JS regression), acceptance_ui.py (browser QA)
backend/
  ignis-ml/              science/ML package (import name ignis_ml), unchanged from the team's revision; 77 tests
  service/               export pipeline, evidence adapter, API server; 18 tests
research/                reviewed Olson 2023 data revision, closeout kit (source conflicts, brand, QA cases), exploratory PMMA study
qa/                      8 final UI QA cases: screenshots + final_ui_qa_results.json
test_logs/               latest logs of every test suite
HANDOFF_REPORT.md        what changed, architecture, mappings, test logs, limitations, approvals needed
```

## Run it

```bash
python3 -m pip install -e backend/ignis-ml
python3 backend/service/build_frontend_data.py --frontend frontend    # regenerate science data + 62 checks
python3 backend/service/server.py --frontend frontend                 # http://127.0.0.1:8787
```

Or serve `frontend/` with any static host (`python3 -m http.server` inside it, GitHub Pages, Netlify). It also opens straight from disk using `data/seed.js`.

## Test it

```bash
(cd backend/ignis-ml && python3 -m unittest discover -s tests)       # 77
python3 -m unittest discover -s backend/service/tests                  # 18
node frontend/tools/check-matching.cjs                                 # JS matching regression
(cd research/closeout_kit && python3 -m unittest discover -s tests)    # 8 closeout consistency checks
(cd frontend && python3 -m http.server 8765 &) ; python3 frontend/tools/acceptance_ui.py   # 41 browser checks
python3 frontend/tools/final_ui_qa.py --out qa                         # the 8 final UI QA cases
```

## Deploy (GitHub Pages)

The workflow `.github/workflows/pages.yml` publishes the `frontend/` folder on every push to `main`. One-time setup: repository **Settings → Pages → Build and deployment → Source: GitHub Actions**. The site appears at `https://<user>.github.io/<repo>/`. On Pages, CSV downloads and the linked `.md` documents work, which the Claude artifact viewer blocks.

`.github/workflows/tests.yml` runs the Python, data and JS tests on every push. Browser tests (`acceptance_ui.py`, `final_ui_qa.py`) need Chrome and Playwright and are run locally.

The optional API server needs a Python host (Render, Fly.io, a VM) and is not required by the site.

## Brand

User-facing name: **1gnition**. Hero copy comes from `frontend/data/brand_copy.json`. Internal Python package and CSV names keep `ignis` for compatibility. "Ask 1gnition" is an offline rule-based evidence helper, not a generative AI assistant.
