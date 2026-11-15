/* Deterministic program logic. No AI here: matching, ranking and gates are rules the user can read. */
(function () {
  "use strict";
  const C = window.IGNIS_CONFIG;

  const L = {};
  L.MATERIAL = { SIBAL: "SIBAL cotton-fiberglass fabric", Cotton: "cotton jersey", PMMA: "PMMA (acrylic)", Nomex: "Nomex", Silicone: "silicone" };
  L.matName = m => L.MATERIAL[m] || m;
  L.GRAV = { micro: "microgravity", lunar: "lunar gravity (0.165 g)", mars: "Mars gravity (0.38 g)", earth: "Earth gravity (1 g)" };
  L.OUT = {
    steady_size: { label: "steady flame size", unit: "cm", pillar: "prevention" },
    spread_rate: { label: "flame spread rate", unit: "mm/s", pillar: "prevention" },
    smoke: { label: "smoke particle size", unit: "", pillar: "detection" },
    extinction: { label: "extinction or suppression limit", unit: "", pillar: "suppression" }
  };
  L.PILLAR = { prevention: "Prevention", detection: "Detection", suppression: "Suppression" };
  L.STATE = {
    pub: { label: "Published observation", cls: "s-pub" },
    expl: { label: "Exploratory comparison", cls: "s-expl" },
    eval: { label: "Independently evaluated prediction", cls: "s-eval" },
    insuf: { label: "Insufficient evidence", cls: "s-insuf" }
  };
  L.PRESET = {
    lunar: { label: "Moon base", o2: "30", p: "70.3", g: "lunar", air: "",
      note: "From the challenge brief: 30% oxygen or more at 10.2 psi (70.3 kPa) or less. Shown at the boundary values." },
    iss: { label: "ISS-like cabin", o2: "21", p: "101.3", g: "micro", air: "",
      note: "Illustrative assumption: Earth-like air at sea-level pressure (14.7 psi = 101.3 kPa) in microgravity. Not a measured ISS cabin record." },
    mars: { label: "Mars habitat", o2: "", p: "", g: "mars", air: "",
      note: "Mars gravity. The brief gives no cabin atmosphere, so oxygen and pressure stay unspecified." },
    custom: { label: "Custom", note: "Custom scenario. Empty fields stay unspecified and are never filled with Earth values." }
  };
  L.INCIDENT = {
    apollo1: { label: "Apollo 1, 1967", set: { hab: "custom", o2: "100", p: "", g: "earth", out: "spread_rate", mat: "Cotton" }, source: "apollo1",
      note: "Apollo 1: NASA's safety office reports that the pure-oxygen atmosphere let the fire spread quickly through combustible cabin materials. Question: how does high oxygen change flame spread over fabrics?" },
    mir: { label: "Mir, 1997", set: { hab: "iss", out: "smoke" }, source: "mir",
      note: "Mir: a solid-fuel oxygen generator ignited and filled the module with dense smoke. Question: how is smoke detected early in microgravity?" },
    apollo13: { label: "Apollo 13", set: { hab: "custom", o2: "", p: "", g: "micro", out: "extinction" }, source: "apollo13",
      note: "Apollo 13: an oxygen tank failed after overheating damaged its wiring insulation. This is a hardware failure, so the combustion data connects only weakly." }
  };

  L.num = v => v == null || String(v).trim() === "" || !Number.isFinite(Number(v)) ? null : Number(v);
  L.fmtRange = (r, u) => r ? (r[0] === r[1] ? `${r[0]}${u}` : `${r[0]}–${r[1]}${u}`) : null;

  /* Conditions compared between two runs */
  L.COND = [
    { k: "airflow_cm_s", label: "Airflow", f: r => r.airflow_cm_s + " cm/s" },
    { k: "material", label: "Material", f: r => L.matName(r.material) },
    { k: "o2_pct", label: "Oxygen", f: r => r.o2_pct + " %" },
    { k: "pressure_kpa", label: "Pressure", f: r => r.pressure_kpa + " kPa" },
    { k: "duct_height_cm", label: "Duct height", f: r => r.duct_height_cm + " cm" },
    { k: "size", label: "Sample size", f: r => r.sample_width_cm + " × " + r.sample_length_cm + " cm" },
    { k: "gravity", label: "Gravity", f: r => L.GRAV[r.gravity] },
    { k: "flow_direction", label: "Flow direction", f: r => r.flow_direction },
    { k: "flight", label: "Flight", f: r => r.flight }
  ];
  const cv = (r, k) => {
    if (k !== "size") return r[k];
    if (r.sample_width_cm == null || r.sample_length_cm == null) return null;
    return [r.sample_width_cm, r.sample_length_cm].join("x");
  };
  L.known = (r, k) => cv(r, k) != null && cv(r, k) !== "";
  L.diff = (a,b) => L.COND.filter(c => L.known(a,c.k) && L.known(b,c.k) && cv(a,c.k) !== cv(b,c.k));
  L.diffCausal = (a,b) => L.diff(a,b).filter(c => c.k !== "flight");

  // All checks refer to one row. Missing atmosphere values cannot count as matches.
  L.conditions = (S,r) => {
    const checks = [
      ["Gravity", r.gravity === S.g],
      ["Oxygen", Number.isFinite(r.o2_pct) && L.num(S.o2) !== null && Math.abs(r.o2_pct - Number(S.o2)) <= C.TOLERANCE.o2_pct],
      ["Pressure", Number.isFinite(r.pressure_kpa) && L.num(S.p) !== null && Math.abs(r.pressure_kpa - Number(S.p)) <= C.TOLERANCE.pressure_kpa]
    ];
    if (L.num(S.air) !== null) checks.push(["Airflow", r.airflow_cm_s === Number(S.air)]);
    if (S.dir) checks.push(["Flow direction", r.flow_direction === S.dir]);
    return checks;
  };
  L.applicability = (S,rs,outcome="steady_size") => {
    const pool = rs.filter(r => r.material === S.mat);
    if (S.out !== outcome || !pool.length) return {level:2,reasons:["No indexed measurement in this selection covers the requested material and outcome."]};
    const match = pool.find(r => L.conditions(S,r).every(([,ok]) => ok));
    if (match) return {level:0,reasons:[`Run ${match.id} matches the specified conditions within the displayed tolerances. This is an observation at the recorded settings.`]};
    const rows = pool.map(r => ({r,missing:L.conditions(S,r).filter(([,ok])=>!ok).map(([name])=>name)})).sort((a,b)=>a.missing.length-b.missing.length);
    const best=rows[0];
    return {level:pool.some(r => r.gravity === S.g) ? 1 : 2,reasons:[`No single run matches all requested conditions. For ${best.r.id}, check ${best.missing.join(", ").toLowerCase()}. Unspecified oxygen or pressure cannot establish an atmosphere match.`]};
  };

  /* Evidence ranking: relevance and similarity are scored separately */
  L.scoreInv = (S, v, runs = []) => {
    const rel = [], sim = []; let r = 0, s = 0;
    const o = L.OUT[S.out];
    if (v.outcomes.includes(S.out)) { r += 2; rel.push(["y", `Measures ${o.label} directly`]); }
    else if (v.pillars.includes(o.pillar)) { r += 1; rel.push(["", `Related ${o.pillar} question, different measurement`]); }
    else rel.push(["n", `Does not measure ${o.label}`]);
    if (v.fuel_type === "solid" && v.materials.includes(S.mat)) { r += 2; rel.push(["y", `Tested ${L.matName(S.mat)}`]); }
    else if (v.fuel_type === "solid") { r += 1; rel.push(["", `Solid fuel, but not ${L.matName(S.mat)}`]); }
    else if (v.fuel_type === "gas burner") { r += 1; rel.push(["", "Gas burner that emulates a burning solid"]); }
    else rel.push(["n", `Different fuel type: ${v.fuel_type}`]);
    const pool = runs.filter(run => run.investigation_id === v.id);
    const sameMaterial = pool.filter(run => run.material === S.mat);
    const ranked = (sameMaterial.length ? sameMaterial : pool).map(run => {
      const checks = L.conditions(S,run);
      return {run, checks, score:checks.filter(([,ok]) => ok).length};
    }).sort((a,b) => b.score-a.score);
    const best = ranked[0];
    if (best) {
      s = best.score;
      best.checks.forEach(([label,ok]) => sim.push([ok ? "y" : "n", label+" "+(ok ? "matches" : "unmatched or unspecified")+" · "+best.run.id]));
    } else {
      if ((v.gravity || []).includes(S.g)) s++;
      sim.push(["q", "Summary only. Gravity is the only scored condition."]);
    }
    return {r,s,rel,sim,rMax:4,sMax:3 + (L.num(S.air) === null ? 0 : 1) + (S.dir ? 1 : 0)};
  };

  /* Distance in tolerance units: 1.0 means one tolerance step away */
  L.dist = (r, o2, p) => Math.hypot((r.o2_pct - o2) / C.TOLERANCE.o2_pct, (r.pressure_kpa - p) / C.TOLERANCE.pressure_kpa);
  L.nearest = (rs, o2, p) => rs.map(r => ({ r, d: L.dist(r, o2, p) })).sort((a, b) => a.d - b.d)[0];
  L.within = (r, o2, p) => Math.abs(r.o2_pct - o2) <= C.TOLERANCE.o2_pct && Math.abs(r.pressure_kpa - p) <= C.TOLERANCE.pressure_kpa;

  /* Transfer Lab data gate, computed from the loaded spread-rate rows */
  L.gate = (D) => {
    const sr = D.spread_rates, G = C.GATE;
    const flights = new Set(sr.map(r => (D.run(r.run_id) || {}).flight).filter(Boolean)).size;
    const configs = new Set(sr.map(r => [r.material, r.sample_width_cm, r.o2_pct, r.pressure_kpa, r.airflow_cm_s, r.flow_direction].join("|"))).size;
    const full = sr.filter(r => r.provenance && D.source(r.provenance.source_id) && r.provenance.location && r.flow_direction && r.kind === "steady" && [r.rate_mm_s,r.o2_pct,r.pressure_kpa,r.airflow_cm_s,r.sample_width_cm].every(Number.isFinite)).length;
    const scales = new Set(sr.map(r => r.sample_width_cm >= 10 ? "large" : "small")).size;
    const items = [
      { label: "Spread-rate rows indexed", have: sr.length, need: `${G.min_spread_rows} or more`, ok: sr.length >= G.min_spread_rows },
      { label: "Independent flights or campaigns", have: flights, need: `${G.min_flights} or more, so one can be held out`, ok: flights >= G.min_flights },
      { label: "Distinct test configurations", have: configs, need: "more than one", ok: configs > 1 },
      { label: "Both small and large samples present", have: scales === 2 ? "yes" : "no", need: "yes, to test scale transfer", ok: scales === 2 },
      { label: "Steady rates with documented test conditions", have: `${full} of ${sr.length}`, need: "all rows", ok: sr.length > 0 && full === sr.length }
    ];
    return { items, pass: items.every(i => i.ok), predictions: D.predictions.length };
  };

  window.IGNIS_LOGIC = L;
})();
