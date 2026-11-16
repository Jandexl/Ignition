/* 1gnition configuration. This is the only file the backend team needs to touch to connect.
 *
 * DATA_MODE
 *   "files": read data/*.json (falls back to data/seed.js when opened from disk)
 *   "api":   read from API_BASE, one GET per collection, e.g. GET {API_BASE}/runs
 *            Each endpoint returns the same JSON shape as the matching file in data/.
 *
 * AI_ENDPOINT
 *   Empty: the Ask panel uses offline, rule-based answers and labels them as such.
 *   Set:   the Ask panel POSTs {question, scenario, context} and expects
 *          {answer, citations:[{source_id, location}], state}. See DATA_CONTRACT.md.
 *   Never put an API key in this file. Keys live on the server.
 *
 * BACKEND_URL
 *   The deployed Python API (backend/service/server.py on Render), which also serves this site.
 *   - Page served by that server (https://onegnition.onrender.com): same-origin calls.
 *   - Page on localhost / 127.0.0.1: same-origin calls, i.e. the local server.py
 *     (add ?api=render to use the deployed backend from a local page instead).
 *   - Any other copy (GitHub Pages, opened from disk): cross-origin calls to BACKEND_URL,
 *     so the server's IGNITION_CORS_ORIGINS must list that page's origin.
 */
(function () {
  var BACKEND = "https://onegnition.onrender.com";
  var loc = typeof window.location !== "undefined" ? window.location : { hostname: "", origin: "", search: "", protocol: "" };
  var local = /^(localhost|127\.0\.0\.1)$/.test(loc.hostname) && !/[?&]api=render\b/.test(loc.search);
  var root = loc.protocol !== "file:" && (loc.origin === BACKEND || local) ? "" : BACKEND;
  window.IGNIS_BACKEND = { URL: BACKEND, ROOT: root };
})();
window.IGNIS_CONFIG = {
  DATA_MODE: "files",
  DATA_BASE: "data/",
  API_BASE: "",
  AI_ENDPOINT: "",
  COLLECTIONS: ["meta", "sources", "investigations", "runs", "spread_rates", "findings", "flags", "predictions", "scientific_comparisons", "synthetic_verification_results", "synthetic_model_benchmark", "evidence_catalog", "build_manifest", "source_conflicts", "brand_copy", "science_project_status"],
  OPTIONAL: ["synthetic_verification_results", "synthetic_model_benchmark", "evidence_catalog", "build_manifest", "source_conflicts", "brand_copy", "science_project_status"],   // site still works if these are absent
  BACKEND_URL: window.IGNIS_BACKEND.URL,
  PREDICT_ENDPOINT: window.IGNIS_BACKEND.ROOT + "/api/predict",                 // NASA scenario check: always a null number (no reviewed model)
  SYNTHETIC_DEMO_ENDPOINT: window.IGNIS_BACKEND.ROOT + "/api/synthetic-demo",   // SYNTHETIC model on invented data; every answer labelled
  HEALTH_ENDPOINT: window.IGNIS_BACKEND.ROOT + "/api/health",
  TOLERANCE: { o2_pct: 1, pressure_kpa: 5 },        // design choice, shown on screen
  GATE: { min_spread_rows: 6, min_flights: 3 }        // legacy heuristic only. NOT scientific approval; prediction state comes from the backend (VALIDATION_NOT_SUPPORTED)
};
