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
 */
window.IGNIS_CONFIG = {
  DATA_MODE: "files",
  DATA_BASE: "data/",
  API_BASE: "",
  AI_ENDPOINT: "",
  COLLECTIONS: ["meta", "sources", "investigations", "runs", "spread_rates", "findings", "flags", "predictions", "scientific_comparisons", "synthetic_verification_results", "synthetic_model_benchmark", "evidence_catalog", "build_manifest", "source_conflicts", "brand_copy", "science_project_status"],
  OPTIONAL: ["synthetic_verification_results", "synthetic_model_benchmark", "evidence_catalog", "build_manifest", "source_conflicts", "brand_copy", "science_project_status"],   // site still works if these are absent
  PREDICT_ENDPOINT: "https://onegnition.onrender.com/api/predict",   // e.g. "http://localhost:8787/api/predict" when backend/server.py runs. Empty: use the static status in scientific_comparisons.json
  TOLERANCE: { o2_pct: 1, pressure_kpa: 5 },        // design choice, shown on screen
  GATE: { min_spread_rows: 6, min_flights: 3 }        // legacy heuristic only. NOT scientific approval; prediction state comes from the backend (VALIDATION_NOT_SUPPORTED)
};
