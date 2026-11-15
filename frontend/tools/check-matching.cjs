const assert = require("node:assert/strict");
global.window = global;
require("../js/config.js");
require("../js/logic.js");
require("../data/seed.js");
const L = IGNIS_LOGIC;
const runs = IGNIS_SEED.runs;
const scenario = {g:"micro",mat:"SIBAL",out:"steady_size",o2:"21",p:"100",air:"20"};
assert.equal(L.applicability(scenario,runs).level,0);
for (const override of [{o2:"26.2"}, {air:"999"}, {out:"smoke"}, {g:"lunar"}, {p:""}, {mat:"PMMA"}]) {
  assert.notEqual(L.applicability({...scenario,...override},runs).level,0);
}
const [a,b] = runs.filter(r => ["II-5","II-6"].includes(r.id));
assert.deepEqual(L.diffCausal(a,b).map(c=>c.k),["airflow_cm_s"]);
assert.deepEqual(L.diffCausal(a,{...a,gravity:"earth",flow_direction:"opposed"}).map(c=>c.k),["gravity","flow_direction"]);
assert.equal(L.known({...a,sample_width_cm:null},"size"),false);
assert.equal(L.num("20abc"),null);
assert.equal(IGNIS_SEED.meta.figure10.length,23);
assert.equal(new Set(IGNIS_SEED.meta.figure10.map(p=>p.series)).size,6);
assert.equal(L.gate({...IGNIS_SEED,run:id=>runs.find(r=>r.id===id),source:id=>IGNIS_SEED.sources.find(s=>s.id===id)}).pass,false);
console.log("Scenario, comparison, figure and transfer checks passed.");
