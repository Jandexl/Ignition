# Deploying 1gnition

The public site is on Netlify (https://1gnition.netlify.app) and the Python API is on Render (https://onegnition.onrender.com). The Render server (`backend/service/server.py`) also serves its own copy of `frontend/`. Netlify (and optionally GitHub Pages) serve `frontend/` and call the Render API across origins.

## What runs where

| Piece | Where | Notes |
|---|---|---|
| Website (`frontend/`) | Netlify (public site), Render (same server), optionally GitHub Pages | Data comes from `frontend/data/*.json`. NASA measurements and sources need no API. |
| API (`backend/service/server.py`) | Render | `/api/health`, `/api/<collection>`, `/api/compare`, `/api/scenario` (published measurements that match a scenario), `/api/predict` (NASA: always a null number), `/api/synthetic-demo` and `/api/synthetic-demo/domain` (the synthetic model) |
| Synthetic model | Loaded by the API at start-up | `backend/ignis-ml/outputs/SYNTHETIC_DEMO_MODEL.joblib`, checked against `MANIFEST.sha256`, then self-tested |

How the frontend picks the API (`frontend/js/config.js`):
- Served by Render: same-origin `/api/...`.
- Served from `localhost` / `127.0.0.1`: same-origin, i.e. your local `server.py`. Add `?api=render` to use Render instead.
- Netlify, GitHub Pages, or opened from disk: `https://onegnition.onrender.com/api/...` across origins.

## 1. Render settings (one time)

The repository has a `render.yaml` Blueprint. If the service was created by hand in the dashboard, enter the same values under the service's **Settings** and **Environment**, because dashboard values override the file.

| Setting | Value |
|---|---|
| Runtime | Python |
| Build command | `pip install -r requirements.txt` |
| Start command | `python3 backend/service/server.py --frontend frontend --host 0.0.0.0 --port $PORT` |
| Health check path | `/api/health` |
| Auto-deploy | On (deploys every push to `main`) |
| Env `PYTHON_VERSION` | `3.12.8` |
| Env `IGNITION_CORS_ORIGINS` | `https://1gnition.netlify.app,https://onegnition.onrender.com,https://knnucs.github.io` |
| Env `IGNITION_QUIET` | `1` |
| Env `GEMINI_API_KEY` | Your Google Gemini API key (from https://aistudio.google.com/apikey). Secret: set it only in the Render dashboard. |
| Env `GEMINI_MODEL` | Optional. Default `gemini-3.5-flash-lite`. Change it here if Google renames or retires the model. |

`requirements.txt` pins the library versions the model was saved with (scikit-learn 1.8.0 and others; see `backend/ignis-ml/outputs/runtime_versions.json`). Don't loosen them.

**Why CORS matters:** the Netlify site calls Render from another origin, so `https://1gnition.netlify.app` must be in `IGNITION_CORS_ORIGINS` (on 26 Nov 2026 it already was). A GitHub Pages copy additionally needs `https://knnucs.github.io`.

## 2. Deploy

1. Push to `main` on GitHub (`knnucs/1gnition`). Render rebuilds automatically, or click **Manual Deploy → Deploy latest commit**.
2. In the Render logs, look for `Synthetic demo model: ready`. If it says `DISABLED (...)`, the reason follows: a hash mismatch, a self-test failure or a missing file. The rest of the site keeps working, and the demo shows "unavailable" with no number.
3. Run the deployment check from your computer:

   ```bash
   python3 backend/service/check_deploy.py            # checks https://onegnition.onrender.com
   ```

   It should print `12 of 12 deployment checks passed`. The free Render plan sleeps after about 15 minutes idle, so the first request can take up to a minute.
4. Open https://1gnition.netlify.app → **Scale transfer → B · Synthetic check** and move the sliders. The answer card must say **SYNTHETIC · invented data · not NASA**. The "Moon-base air (outside)" preset must show **REFUSED** with no number.

**Ask 1gnition (AI):** with `GEMINI_API_KEY` set, the Render log shows `AI assistant: ready (Google Gemini, <model>)`. Without it, the log shows `AI assistant: OFF` and the site's Ask panel uses the offline rule-based helper; nothing else changes. The backend allows 6 AI questions per minute per visitor and 20 per minute site-wide, to stay inside the free Gemini quota. If answers say the model was not found, set `GEMINI_MODEL` to a current model ID from https://ai.google.dev/gemini-api/docs/models.

## 3. Netlify (public site)

- **If the Netlify site is linked to GitHub:** it redeploys on every push. In **Site configuration → Build & deploy**, Publish directory must be `frontend` and Build command must be empty.
- **If it was uploaded by drag-and-drop:** open the **Deploys** tab and drag the `frontend` folder onto the drop box.

Deploy Render first (step 2), so the new site finds the new API endpoints.

## 4. GitHub Pages (optional third copy)

`.github/workflows/pages.yml` publishes `frontend/` on every push. Do the one-time setup at **Settings → Pages → Source: GitHub Actions**. The copy at `https://knnucs.github.io/1gnition/` calls the Render API, so step 1's `IGNITION_CORS_ORIGINS` must include `https://knnucs.github.io`.

## 5. Run everything locally

```bash
python3 -m pip install -r requirements.txt
python3 backend/service/server.py --frontend frontend --port 8787     # http://127.0.0.1:8787 (site + API)
python3 backend/service/check_deploy.py http://127.0.0.1:8787
```

## 6. Tests (all must pass before a push)

```bash
python3 -m pip install -r requirements.txt && python3 -m pip install -e backend/ignis-ml
(cd backend/ignis-ml && python3 -m unittest discover -s tests)          # 77
python3 backend/service/build_frontend_data.py --frontend frontend       # 71 acceptance checks
python3 -m unittest discover -s backend/service/tests                     # 33: 7 published-measurement and 6 synthetic-demo tests included
(cd research/closeout_kit && python3 -m unittest discover -s tests)       # 8
node frontend/tools/check-matching.cjs
python3 backend/service/server.py --frontend frontend --port 8765 &       # browser suites need the API
python3 frontend/tools/acceptance_ui.py --base http://localhost:8765      # 41
python3 frontend/tools/final_ui_qa.py --base http://localhost:8765 --out qa   # 8
```

The build script rewrites `frontend/data/build_manifest.json` and `seed.js` with a new timestamp. If no data changed, `git checkout` those two files before committing.
