/* Data loading and validation. Exposes window.IGNIS_DATA after load(). */
(function () {
  "use strict";
  const C = window.IGNIS_CONFIG;

  const REQUIRED = {
    sources: ["id", "title", "url"],
    investigations: ["id", "name", "pillars", "fuel_type", "outcomes", "source_ids"],
    runs: ["id", "investigation_id", "material", "gravity", "o2_pct", "pressure_kpa", "provenance"],
    spread_rates: ["id", "investigation_id", "material", "rate_mm_s", "provenance"],
    findings: ["id", "text", "source_id"],
    flags: ["id", "title", "detail"],
    predictions: ["id", "held_out", "measured_mm_s", "baseline_mm_s", "model_mm_s"]
  };

  async function fetchJSON(url) {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) throw new Error(url + " returned " + r.status);
    return r.json();
  }

  async function loadRaw() {
    if (C.DATA_MODE === "api" && C.API_BASE) {
      const out = {};
      const opt = new Set(C.OPTIONAL || []);
      for (const n of C.COLLECTIONS) out[n] = opt.has(n) ? await fetchJSON(C.API_BASE.replace(/\/$/, "") + "/" + n).catch(() => undefined) : await fetchJSON(C.API_BASE.replace(/\/$/, "") + "/" + n);
      return { raw: out, origin: "Team API at " + C.API_BASE };
    }
    try {
      const opt = new Set(C.OPTIONAL || []);
      const parts = await Promise.all(C.COLLECTIONS.map(n => opt.has(n) ? fetchJSON(C.DATA_BASE + n + ".json").catch(() => undefined) : fetchJSON(C.DATA_BASE + n + ".json")));
      const out = {}; C.COLLECTIONS.forEach((n, i) => out[n] = parts[i]);
      return { raw: out, origin: "the project data files" };
    } catch (e) {
      if (window.IGNIS_SEED) return { raw: window.IGNIS_SEED, origin: "the bundled copy of the project data files" };
      throw e;
    }
  }

  function validate(raw) {
    const warnings = [];
    Object.entries(REQUIRED).forEach(([col, fields]) => {
      (raw[col] || []).forEach(row => {
        const miss = fields.filter(f => row[f] === undefined || row[f] === null || row[f] === "");
        if (miss.length) warnings.push(`${col} ${row.id || "(no id)"}: missing ${miss.join(", ")}`);
      });
    });
    const src = new Set((raw.sources || []).map(s => s.id));
    ["runs", "spread_rates"].forEach(col => (raw[col] || []).forEach(r => {
      if (r.provenance && !src.has(r.provenance.source_id)) warnings.push(`${col} ${r.id}: source "${r.provenance.source_id}" is not in sources`);
    }));
    const inv = new Set((raw.investigations || []).map(i => i.id));
    (raw.runs || []).forEach(r => { if (!inv.has(r.investigation_id)) warnings.push(`runs ${r.id}: investigation "${r.investigation_id}" is not in investigations`); });
    return warnings;
  }

  async function load() {
    const { raw, origin } = await loadRaw();
    C.COLLECTIONS.forEach(n => { if (raw[n] === undefined) raw[n] = n === "meta" ? {} : ["scientific_comparisons", "synthetic_verification_results", "synthetic_model_benchmark", "build_manifest", "source_conflicts", "brand_copy", "science_project_status"].includes(n) ? null : []; });
    const D = Object.assign({}, raw);
    D.origin = origin;
    D.warnings = validate(raw);
    D.source = id => D.sources.find(s => s.id === id);
    D.run = id => D.runs.find(r => r.id === id);
    D.inv = id => D.investigations.find(i => i.id === id);
    window.IGNIS_DATA = D;
    return D;
  }

  window.IGNIS_LOAD = load;
})();
