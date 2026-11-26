# 1gnition — NASA Space Apps 2026, Flame in Freefall

**ZERO GUESSING. ZERO HIDDEN UNCERTAINTY.** *Know What the Evidence Supports.* (Brand lines, not a claim of zero uncertainty: the methodology states its assumptions, unknowns and limits.)

1gnition turns scattered NASA microgravity-combustion measurements into traceable comparisons and research decisions: which runs apply, which comparisons are fair, where the evidence runs out, and what experiment to fly next. It refuses to predict where the data cannot support a number.

Live site and API: https://onegnition.onrender.com (one Render service; see `DEPLOYMENT.md`). NASA measurements, comparisons and sources come from the generated JSON in `frontend/data/` and work without the API. The API adds the backend scenario check (always a null NASA number) and an interactive **synthetic model demo**: the saved `SYNTHETIC_DEMO_MODEL.joblib`, fitted to invented data and labelled as such on every answer. Why no real-data model exists yet: `backend/ignis-ml/docs/REAL_DATA_PIPELINE_STATUS.md`.

## Layout

```
frontend/                static site (HTML/CSS/JS, no build step)
  data/                  JSON the site reads; 5 science files are generated, see DATA_CONTRACT.md
  docs/                  methodology and decision notes linked from the site
  tools/                 make_seed.py, check-matching.cjs (JS regression), acceptance_ui.py (browser QA)
backend/
  ignis-ml/              science/ML package (import name ignis_ml), unchanged from the team's revision; 77 tests
  service/               export pipeline, evidence adapter, API server, synthetic demo loader, deploy check, AI assistant; 44 tests
research/                reviewed Olson 2023 data revision, closeout kit (source conflicts, brand, QA cases), exploratory PMMA study
qa/                      8 final UI QA cases: screenshots + final_ui_qa_results.json
test_logs/               latest logs of every test suite
HANDOFF_REPORT.md        what changed, architecture, mappings, test logs, limitations, approvals needed
DEPLOYMENT.md            Render + GitHub Pages deployment, settings and checks
render.yaml, requirements.txt, .python-version   Render build (versions pinned to the saved model)
```

## Run it

```bash
python3 -m pip install -r requirements.txt && python3 -m pip install -e backend/ignis-ml
python3 backend/service/build_frontend_data.py --frontend frontend    # regenerate science data + 71 checks
python3 backend/service/server.py --frontend frontend                 # http://127.0.0.1:8787 (site + API + synthetic demo)
```

Or serve `frontend/` with any static host (`python3 -m http.server` inside it, GitHub Pages, Netlify). It also opens straight from disk using `data/seed.js`.

## Test it

```bash
(cd backend/ignis-ml && python3 -m unittest discover -s tests)       # 77
python3 -m unittest discover -s backend/service/tests                  # 44 (11 for the AI assistant, against a fake Gemini)
node frontend/tools/check-matching.cjs                                 # JS matching regression
(cd research/closeout_kit && python3 -m unittest discover -s tests)    # 8 closeout consistency checks
python3 backend/service/server.py --frontend frontend --port 8765 &   # browser suites use the local API
python3 frontend/tools/acceptance_ui.py --base http://localhost:8765   # 41 browser checks
python3 frontend/tools/final_ui_qa.py --base http://localhost:8765 --out qa   # the 8 final UI QA cases
python3 backend/service/check_deploy.py                                # 12 checks against the live Render service
```

## Deploy

Render (site + API): see `DEPLOYMENT.md`. Every push to `main` redeploys https://onegnition.onrender.com.

### GitHub Pages (optional static copy)

The workflow `.github/workflows/pages.yml` publishes the `frontend/` folder on every push to `main`. One-time setup: repository **Settings → Pages → Build and deployment → Source: GitHub Actions**. The site appears at `https://<user>.github.io/<repo>/`. On Pages, CSV downloads and the linked `.md` documents work, which the Claude artifact viewer blocks.

`.github/workflows/tests.yml` runs the Python, data and JS tests on every push. Browser tests (`acceptance_ui.py`, `final_ui_qa.py`) need Chrome and Playwright and are run locally.

A Pages copy calls the Render API across origins, so Render's `IGNITION_CORS_ORIGINS` must include `https://knnucs.github.io`.

## Ask 1gnition (AI assistant) and use of AI

Ask 1gnition sends questions to Google Gemini through the backend (`backend/service/assistant.py`). Gemini receives only 1gnition's indexed records and science notes, is told to answer from them alone, never to predict a spread rate, and to cite its sources. The server drops any citation that isn't a real indexed source and flags any number that doesn't appear in the records. Every answer is labelled "AI-generated". Without a `GEMINI_API_KEY` on the server, the panel falls back to the offline rule-based helper.

**Use of AI (Super Intelligence) in this project:** AI assistants (Claude by Anthropic) helped write code, tests and documentation. The Ask 1gnition panel uses Google Gemini at run time and labels its answers as AI-generated. Scientific data come from the cited NASA and peer-reviewed sources, not from AI.

## Brand

User-facing name: **1gnition**. Hero copy comes from `frontend/data/brand_copy.json`. Internal Python package and CSV names keep `ignis` for compatibility. "Ask 1gnition" uses Google Gemini when the server has a key (answers labelled AI-generated), and an offline rule-based helper otherwise.
