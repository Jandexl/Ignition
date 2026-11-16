/* 1gnition front end. Views render from window.IGNIS_DATA, so new data from the team appears without code changes. */
(function () {
  "use strict";
  const C = window.IGNIS_CONFIG, L = window.IGNIS_LOGIC;
  const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let D = null;

  /* ---------------- helpers ---------------- */
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const st = k => `<span class="state ${L.STATE[k].cls}">${L.STATE[k].label}</span>`;
  const plain = t => `<span class="state s-plain">${esc(t)}</span>`;
  const pv = (col, id, field, text) => `<span class="pv" tabindex="0" data-pv="${col}|${id}|${field}">${text}</span>`;
  const pvs = (sourceId, text) => `<span class="pv" tabindex="0" data-pvs="${sourceId}">${text}</span>`;
  const srcLink = id => { const s = D.source(id); return s ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a>` : esc(id); };
  const cap = s => s ? s[0].toUpperCase() + s.slice(1) : s;
  const listJoin = a => a.length <= 1 ? a.join("") : a.slice(0, -1).join(", ") + " and " + a[a.length - 1];
  const raf2 = fn => REDUCE ? fn() : requestAnimationFrame(() => requestAnimationFrame(fn));

  /* ---------------- state ---------------- */
  const S = { hab: "lunar", mat: "SIBAL", out: "steady_size", o2: "30", p: "70.3", g: "lunar", air: "", dir: "",
    note: L.PRESET.lunar.note, sel: ["II-5", "II-6"], revealed: false, justRevealed: false,
    gMat: "all", step: "compare", sciCase: 0, sciMetric: "both", synCase: 0, dataTab: "runs", dataQ: "", prevRank: null, openInv: null };

  /* ---------------- routing ---------------- */
  const VIEWS = ["overview", "evidence", "compare", "transfer", "gaps", "data"];
  let current = "overview";
  function route() {
    const h = location.hash.replace("#", "");
    const v = VIEWS.includes(h) ? h : "overview";
    current = v;
    $("v-overview").classList.toggle("on", v === "overview");
    $("app").classList.toggle("hide", v === "overview");
    VIEWS.slice(1).forEach(n => $("v-" + n).classList.toggle("on", n === v));
    document.querySelectorAll("[data-nav]").forEach(a => a.dataset.nav === v ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current"));
    hidePop();
    if (v === "evidence") raf2(fillMeters);
    if (v === "compare") raf2(fillBars);
    if (v === "overview" && window.IGNIS_STORY) raf2(IGNIS_STORY.onShow);
  }
  function go(v, keepScroll) {
    try { if (location.hash !== "#" + v) history.replaceState(null, "", "#" + v); } catch (e) { location.hash = v; }
    route();
    if (!keepScroll) window.scrollTo(0, 0);
  }

  /* ---------------- scenario ---------------- */
  function scnLabel() {
    const o2 = L.num(S.o2), p = L.num(S.p);
    return `${L.matName(S.mat)}, ${o2 === null ? "oxygen not set" : o2 + "% oxygen"}, ${p === null ? "pressure not set" : p + " kPa"}, ${L.GRAV[S.g]}`;
  }
  function applyPreset(h) {
    S.hab = h; const pr = L.PRESET[h];
    if (h !== "custom") { S.o2 = pr.o2; S.p = pr.p; S.g = pr.g; S.air = pr.air; }
    S.note = pr.note;
  }
  function syncSide() {
    $("presetSeg").innerHTML = Object.entries(L.PRESET).map(([k, v]) => `<button type="button" data-preset="${k}" aria-pressed="${S.hab === k}">${v.label}</button>`).join("");
    $("fMat").value = S.mat; $("fOut").value = S.out; $("fO2").value = S.o2; $("fP").value = S.p; $("fG").value = S.g; $("fAir").value = S.air; $("fDir").value = S.dir || "";
    $("scnNote").textContent = S.note;
    if (window.IGNIS_ART && $("scnArt").dataset.h !== S.hab + S.g) { $("scnArt").dataset.h = S.hab + S.g; $("scnArt").innerHTML = IGNIS_ART.scenePhoto(S.hab) + `<span class="scn-art-l">${esc(L.PRESET[S.hab].label)} · ${esc(L.GRAV[S.g])}</span>`; }
    $("scnSum").textContent = `${L.PRESET[S.hab].label} · ${L.num(S.o2) ?? "?"}% O₂ · ${L.num(S.p) ?? "?"} kPa · ${S.g}`;
    $("sideInc").innerHTML = Object.entries(L.INCIDENT).map(([k, v]) => `<button class="chip" type="button" data-inc="${k}">${esc(v.label)}</button>`).join("");
  }
  function renderAll() {
    syncSide();
    renderEvidence(); renderCompare(); renderCmpOlson(); renderTransfer(); renderGaps();
  }

  /* ---------------- shared map (hero + gaps) ---------------- */
  const MP = { W: 640, H: 380, L: 52, R: 18, T: 18, B: 42, x0: 18, x1: 34, y0: 50, y1: 110 };
  const MX = v => MP.L + (v - MP.x0) / (MP.x1 - MP.x0) * (MP.W - MP.L - MP.R);
  const MY = v => MP.H - MP.B - (v - MP.y0) / (MP.y1 - MP.y0) * (MP.H - MP.T - MP.B);
  function mapSVG(opts) {
    const rs = D.runs.filter(r => !opts.mat || opts.mat === "all" || r.material === opts.mat);
    const T = C.TOLERANCE, mb = D.meta.moon_base || { o2_pct_min: 30, pressure_kpa_max: 70.3 };
    let g = "";
    for (let v = 18; v <= 34; v += 2) g += `<line x1="${MX(v)}" y1="${MP.T}" x2="${MX(v)}" y2="${MP.H - MP.B}" stroke="#232a35"/>${v % 4 === 0 ? `<text x="${MX(v)}" y="${MP.H - MP.B + 19}" text-anchor="middle">${v}</text>` : ""}`;
    for (let v = 50; v <= 110; v += 10) g += `<line x1="${MP.L}" y1="${MY(v)}" x2="${MP.W - MP.R}" y2="${MY(v)}" stroke="#232a35"/>${v > 50 && v < 110 ? `<text x="${MP.L - 9}" y="${MY(v) + 4}" text-anchor="end">${v}</text>` : ""}`;
    g += `<rect x="${MX(mb.o2_pct_min)}" y="${MY(mb.pressure_kpa_max)}" width="${MX(MP.x1) - MX(mb.o2_pct_min)}" height="${MY(MP.y0) - MY(mb.pressure_kpa_max)}" fill="#f5a524" fill-opacity=".09" stroke="#f5a524" stroke-opacity=".6" stroke-dasharray="5 4"/>`;
    g += `<text x="${(MX(mb.o2_pct_min) + MX(MP.x1)) / 2}" y="${MY(MP.y0) - 12}" text-anchor="middle" fill="#f5c46b">Moon base range</text>`;
    const groups = {};
    rs.forEach(r => { const k = r.o2_pct + "|" + r.pressure_kpa; (groups[k] = groups[k] || []).push(r); });
    Object.values(groups).forEach(a => { const r = a[0];
      g += `<rect x="${MX(r.o2_pct - T.o2_pct)}" y="${MY(r.pressure_kpa + T.pressure_kpa)}" width="${MX(r.o2_pct + T.o2_pct) - MX(r.o2_pct - T.o2_pct)}" height="${MY(r.pressure_kpa - T.pressure_kpa) - MY(r.pressure_kpa + T.pressure_kpa)}" rx="4" fill="#7fb2ff" fill-opacity=".13" stroke="#7fb2ff" stroke-opacity=".7" stroke-dasharray="4 3"/>`; });
    const o2 = L.num(opts.o2), p = L.num(opts.p);
    const onMap = o2 !== null && p !== null && o2 >= MP.x0 && o2 <= MP.x1 && p >= MP.y0 && p <= MP.y1;
    const nr = o2 !== null && p !== null && rs.length ? L.nearest(rs, o2, p) : null;
    if (onMap && nr && !L.within(nr.r, o2, p)) {
      g += `<line x1="${MX(o2)}" y1="${MY(p)}" x2="${MX(nr.r.o2_pct)}" y2="${MY(nr.r.pressure_kpa)}" stroke="#f5a524" stroke-width="1.5" stroke-dasharray="5 4"/>`;
    }
    let i = 0;
    Object.values(groups).forEach(a => {
      const r = a[0], n = a.length, near = nr && a.includes(nr.r);
      const anim = opts.animate && !REDUCE ? ` class="pop-in" style="animation-delay:${200 + i++ * 140}ms;transform-origin:${MX(r.o2_pct)}px ${MY(r.pressure_kpa)}px"` : "";
      g += `<g${anim}>`;
      if (near && onMap) g += `<circle class="pulse" cx="${MX(r.o2_pct)}" cy="${MY(r.pressure_kpa)}" r="${14 + 2 * (n - 1)}" fill="none" stroke="#f5a524" stroke-width="2"/>`;
      g += `<circle cx="${MX(r.o2_pct)}" cy="${MY(r.pressure_kpa)}" r="${6 + 2.2 * (n - 1)}" fill="#5cb0ff" stroke="#0a0c10" stroke-width="2"/>`;
      const lbl = n > 1 ? `${n} runs: ${a.map(q => q.id).join(", ")}` : `${r.id} · ${r.material === "Cotton" ? "cotton" : r.material}`;
      const crowded = Object.values(groups).some(o => o !== a && o[0].o2_pct < r.o2_pct && r.o2_pct - o[0].o2_pct <= 2 && Math.abs(o[0].pressure_kpa - r.pressure_kpa) <= 10);
      g += crowded
        ? `<text class="lab" x="${MX(r.o2_pct + T.o2_pct) + 8}" y="${MY(r.pressure_kpa) + 4}" text-anchor="start">${lbl}</text></g>`
        : `<text class="lab" x="${MX(r.o2_pct)}" y="${MY(r.pressure_kpa + T.pressure_kpa) - 9}" text-anchor="middle">${lbl}</text></g>`;
    });
    if (onMap) g += `<g${opts.animate && !REDUCE ? ` class="pop-in" style="animation-delay:${300 + i * 140}ms;transform-origin:${MX(o2)}px ${MY(p)}px"` : ""}><circle cx="${MX(o2)}" cy="${MY(p)}" r="10" fill="#0a0c10" stroke="#f5a524" stroke-width="3"/><circle cx="${MX(o2)}" cy="${MY(p)}" r="3" fill="#f5a524"/><text class="lab" x="${MX(o2) + 4}" y="${rs.some(r => Math.abs(r.o2_pct - o2) <= 4 && r.pressure_kpa - p >= -6 && r.pressure_kpa - p <= 14) ? MY(p - T.pressure_kpa) + 20 : MY(p) - 18}" text-anchor="start">${esc(opts.label || "Your habitat")}${opts.drag ? " (drag)" : ""}</text></g>`;
    g += `<text x="${(MP.L + MP.W - MP.R) / 2}" y="${MP.H - 5}" text-anchor="middle">Oxygen, %</text><text transform="translate(13 ${(MP.T + MP.H - MP.B) / 2}) rotate(-90)" text-anchor="middle">Total pressure, kPa</text>`;
    return { svg: `<svg class="chart" viewBox="0 0 ${MP.W} ${MP.H}" role="img" aria-label="Oxygen and pressure of indexed runs, with the Moon base range and the habitat">${g}</svg>`, nr, onMap, rs };
  }

  /* ---------------- overview ---------------- */
  function renderOverview() {
    const m = mapSVG({ o2: 30, p: 70.3, animate: true, label: "Moon base" });
    $("heroMap").innerHTML = m.svg;
    $("heroCap").innerHTML = `<span><span style="color:var(--pub)">●</span> Indexed run with its tolerance box. A larger dot means more runs at the same conditions</span><span><span style="color:var(--accent)">◯</span> Moon base, 30% O₂ at 70.3 kPa</span><span>Nearest run to the Moon base: ${m.nr ? m.nr.r.id + ", " + Math.abs(m.nr.r.o2_pct - 30).toFixed(1) + " points of O₂ short" : "none"}</span><span>Source: Saffire I–V paper, Table 2</span>`;
    const t1n = ((D.scientific_comparisons || {}).table1_records || []).length;
    const BR = D.brand_copy;
    if (BR) { $("heroL1").textContent = BR.hero_line_1; $("heroL2").textContent = BR.hero_line_2; $("heroName").textContent = BR.product_name_line; $("heroTag").textContent = BR.tagline; $("heroQual").textContent = BR.scientific_qualifier; }
    $("heroNote").textContent = `${t1n} published spread rates (Olson 2023) and ${D.runs.length} flame-size runs (Urban 2021) indexed, each linked to its table row. Nothing on screen is simulated.`;
    const coll = D.meta.collection || {};
    const summarized = D.investigations.length;

    const g = D.runs.filter(r => r.o2_pct === 21 && r.pressure_kpa === 100 && r.material === "SIBAL");
    const cellv = (w, a) => { const r = g.find(x => x.sample_width_cm === w && x.airflow_cm_s === a); return r ? r.steady_size_cm : "?"; };
    $("qgrid").innerHTML = `
      <a class="qcard" href="#evidence"><h3>Which runs apply to my habitat?</h3><p>Seven investigations ranked for the Moon-base scenario, with relevance and environmental similarity shown as separate scores.</p>
        <div style="display:grid;gap:8px">${["Saffire-I, -II, -III", "Saffire-IV, -V", "BASS and BASS-II"].map((n, i) => `<div class="meter"><span>${n}<b>${[4, 4, 3][i]}/4</b></span><div class="mbar"><i style="width:${[100, 100, 75][i]}%"></i></div></div>`).join("")}</div>
        <span class="go">Open the evidence explorer →</span></a>
      <a class="qcard" href="#compare"><h3>Which comparisons are fair?</h3><p>Two Saffire runs that differ only in airflow can be compared. Runs that change several conditions at once cannot. And one cell hides a surprise.</p>
        <div class="grid22" style="grid-template-columns:70px 1fr 1fr;gap:6px;pointer-events:none"><span></span><span class="gh">20 cm/s</span><span class="gh">25 cm/s</span>
          <span class="gh rowh">Small</span><span class="cell" style="min-height:58px"><span class="v" style="font-size:22px">${cellv(5, 20)}<small>cm</small></span></span><span class="cell" style="min-height:58px"><span class="v" style="font-size:22px">${cellv(5, 25)}<small>cm</small></span></span>
          <span class="gh rowh">Large</span><span class="cell empty" style="min-height:58px"><b>?</b></span><span class="cell" style="min-height:58px"><span class="v" style="font-size:22px">${cellv(41, 25)}<small>cm</small></span></span></div>
        <span class="go">Compare runs →</span></a>
      <a class="qcard" href="#gaps"><h3>Where does the data run out?</h3><p>No indexed run reaches 30% oxygen or lunar gravity. 1gnition shows the gap and proposes the next test instead of a guess.</p>
        <div class="callout bad" style="padding:12px 14px"><h3 style="font-size:14px">Moon base: outside every tested box</h3><span class="small t2">Nearest run V-2 is 3.8 points of oxygen short.</span></div>
        <span class="go">See the research gaps →</span></a>`;
    $("incidents").innerHTML = Object.entries(L.INCIDENT).map(([k, v]) => `<div class="inc"><h3>${esc(v.label)}</h3><p>${esc(cap(v.note.split(": ").slice(1).join(": ")))}</p><button class="btn btn-ghost btn-sm" type="button" data-inc="${k}">Load this scenario →</button><span class="tiny muted">${srcLink(v.source)}</span></div>`).join("");
    $("footData").innerHTML = `Data loaded from: ${esc(D.origin)}. <a href="#data">View all data and sources</a>.`;
  }

  /* ---------------- evidence ---------------- */
  function renderEvidence() {
    const scored = D.investigations.map((v, i) => ({ v, i, ...L.scoreInv(S, v, D.runs) })).sort((a, b) => b.r - a.r || b.s - a.s || a.i - b.i);
    const order = scored.map(x => x.v.id), prev = S.prevRank;
    const before = {};
    document.querySelectorAll("#invList .inv").forEach(el => { const b = el.getBoundingClientRect(); if (b.height) before[el.dataset.id] = b.top; });
    const withRuns = D.investigations.filter(v => D.runs.some(r => r.investigation_id === v.id)).length;
    $("evStrip").innerHTML = `<span><b>${D.investigations.length}</b> of ${(D.meta.collection || {}).investigations_total || 24} investigations summarized</span><span><b>${withRuns}</b> with runs indexed</span><span><b>${D.runs.length}</b> runs</span><span>Asking about <b style="font-family:var(--f-sans)">${esc(L.OUT[S.out].label)}</b> for ${esc(scnLabel())}</span>`;
    $("cover").innerHTML = Object.entries(L.PILLAR).map(([k, lab]) => {
      const invs = D.investigations.filter(v => v.pillars.includes(k));
      const n = D.runs.filter(r => invs.some(v => v.id === r.investigation_id)).length;
      return `<div class="card"><span class="small muted">${lab}</span><span class="big">${invs.length} <span class="small t2" style="font-family:var(--f-sans)">investigations</span></span><span class="small ${n ? "t2" : "muted"}">${n ? n + (n === 1 ? " run indexed" : " runs indexed") : "Summaries only, no runs indexed yet"}</span></div>`;
    }).join("");
    const relevant = scored.filter(x => x.r > 0), other = scored.filter(x => x.r === 0);
    const rowHTML = (x, idx) => {
      const v = x.v; let mv = "";
      if (prev && prev.indexOf(v.id) !== -1 && prev.indexOf(v.id) !== idx) { const m = prev.indexOf(v.id) - idx; mv = `<span class="mv ${m > 0 ? "up" : "down"}">${m > 0 ? "▲" + m : "▼" + (-m)}</span>`; }
      const runs = D.runs.filter(r => r.investigation_id === v.id);
      const li = a => a.map(([c, t]) => `<li class="${c}">${esc(t)}</li>`).join("");
      const open = S.openInv === v.id;
      return `<div class="inv ${open ? "open" : ""} ${mv ? "moved" : ""}" data-id="${v.id}">
        <button class="inv-row" type="button" data-inv="${v.id}" aria-expanded="${open}">
          <span class="inv-rank">${idx + 1}${mv}</span>
          <span class="inv-name"><b>${esc(v.name)}</b><span class="inv-meta">${v.pillars.map(p => `<span class="tag">${L.PILLAR[p]}</span>`).join("")}<span>${runs.length ? runs.length + (runs.length === 1 ? " run indexed" : " runs indexed") : "summary only"}</span>${v.psi_id ? `<span title="${v.psi_confirmed ? "PSI record confirmed" : "Record number from the team source list. The link has not been opened yet."}">${esc(v.psi_id)}${v.psi_confirmed ? "" : " · to verify"}</span>` : ""}</span></span>
          <span class="meter"><span>Scientific relevance<b>${x.r}/${x.rMax}</b></span><span class="mbar"><i data-w="${x.r / x.rMax * 100}"></i></span></span>
          <span class="meter"><span>Environmental similarity<b>${x.s}/${x.sMax}</b></span><span class="mbar sim"><i data-w="${x.s / x.sMax * 100}"></i></span>${x.s === 0 ? `<em class="zero">${esc(zeroWhy(x))}</em>` : ""}</span>
          <span class="chev" aria-hidden="true">⌄</span>
        </button>
        <div class="inv-body">
          <p class="t2">${esc(v.objective)}</p>
          <div class="kv">
            <div><b>Materials</b>${esc(v.materials_note || "Not indexed yet")}</div>
            <div><b>Apparatus</b>${esc(v.apparatus || "Not indexed yet")}</div>
            <div><b>Sensors</b>${esc(v.sensors || "Not indexed yet")}</div>
            <div><b>Tested conditions</b>${v.o2_pct_range ? `${L.fmtRange(v.o2_pct_range, "%")} oxygen, ${L.fmtRange(v.pressure_kpa_range, " kPa")}, ${v.gravity.map(g => L.GRAV[g]).join(", ")}` : "Not indexed yet"}</div>
          </div>
          ${v.caution ? `<p class="note">${esc(v.caution)}</p>` : ""}
          <div class="g2" style="gap:14px">
            <div class="card" style="padding:14px;background:var(--bg2)"><h3>Why relevance is ${x.r}/${x.rMax}</h3><ul class="why">${li(x.rel)}</ul></div>
            <div class="card" style="padding:14px;background:var(--bg2)"><h3>Why similarity is ${x.s}/${x.sMax}</h3><ul class="why">${li(x.sim)}</ul></div>
          </div>
          <div class="row">${runs.length >= 2 ? `<button class="btn btn-ghost btn-sm" type="button" data-pair="${runs[0].id},${runs[1].id}">Compare its runs</button>` : ""}<span class="small muted">Sources: ${v.source_ids.map(srcLink).join(" · ")}</span></div>
        </div></div>`;
    };
    $("invList").innerHTML = relevant.map(rowHTML).join("") + (other.length ? `<details class="inv-more"${S.moreOpen ? " open" : ""}><summary>${other.length} investigation${other.length > 1 ? "s" : ""} not relevant to ${esc(L.OUT[S.out].label)}: ${other.map(x => esc(x.v.name)).join(", ")}</summary>${other.map((x, i) => rowHTML(x, relevant.length + i)).join("")}</details>` : "");
    $("evRule").textContent = `Ranking rule (design choice): sort by relevance, then similarity. Tolerances: oxygen within ${C.TOLERANCE.o2_pct} point and pressure within ${C.TOLERANCE.pressure_kpa} kPa of the tested range. Conditions not indexed yet score zero until the data team fills them.`;
    S.prevRank = order;
    if (current === "evidence") raf2(fillMeters);
    if (!REDUCE) document.querySelectorAll("#invList .inv").forEach(el => {
      const t = before[el.dataset.id]; if (t === undefined) return;
      const dy = t - el.getBoundingClientRect().top; if (Math.abs(dy) < 2) return;
      el.style.transition = "none"; el.style.transform = `translateY(${dy}px)`;
      raf2(() => { el.style.transition = "transform .7s cubic-bezier(.2,.7,.2,1)"; el.style.transform = ""; });
    });
  }
  function zeroWhy(x) {
    const n = x.sim.filter(s => s[0] === "n").map(s => s[1].replace(/ (unmatched|matches)[\s\S]*$/, "").split(":")[0].replace(/^Tested in.*/, "gravity").toLowerCase());
    const q = x.sim.filter(s => s[0] === "q").length;
    return n.length ? `No match on ${listJoin([...new Set(n)])}${q ? ", rest not indexed" : ""}` : "Conditions not indexed yet";
  }
  function fillMeters() { document.querySelectorAll("#invList .mbar i").forEach(i => i.style.width = i.dataset.w + "%"); }

  /* ---------------- compare ---------------- */
  function gridRuns() { return D.runs.filter(r => r.o2_pct === 21 && r.pressure_kpa === 100 && r.material === "SIBAL" && r.gravity === "micro"); }
  function cellHTML(r) {
    const a = S.sel[0] === r.id, b = S.sel[1] === r.id;
    const pop = r.id === "I-1" && S.justRevealed ? "pop-in" : "";
    return `<button type="button" class="cell ${a ? "a" : ""} ${b ? "b" : ""} ${pop}" data-run="${r.id}" aria-pressed="${a || b}">
      ${a ? `<span class="pick">first</span>` : b ? `<span class="pick">second</span>` : ""}
      <span class="rid">${r.id}</span><span class="v">${r.steady_size_cm}<small>cm</small></span><span class="fl">${esc(r.flight)}</span></button>`;
  }
  function renderCompare() {
    const g = gridRuns(), find = (w, a) => g.find(r => r.sample_width_cm === w && r.airflow_cm_s === a);
    const small = find(5, 20) ? "5 × 30 cm" : "", large = find(41, 25) ? "41 × 94 cm" : "";
    const c = (w, a, hideable) => { const r = find(w, a);
      if (!r) return `<div class="cell empty"><span>No run indexed</span></div>`;
      if (hideable && !S.revealed) return `<button type="button" class="cell empty" data-reveal="1"><span>Large, 20 cm/s</span><b>Search indexed runs →</b></button>`;
      return cellHTML(r); };
    $("grid22").innerHTML = `<span></span><span class="gh">Airflow 20 cm/s</span><span class="gh">Airflow 25 cm/s</span>
      <span class="gh rowh">Small sample<br>${small}</span>${c(5, 20)}${c(5, 25)}
      <span class="gh rowh">Large sample<br>${large}</span>${c(41, 20, true)}${c(41, 25)}`;
    S.justRevealed = false;
    $("gridNote").innerHTML = S.revealed
      ? `<div class="callout ok"><h3>Run I-1 was already flown</h3><p class="small t2">Both sample sizes show the same reported pattern: 4 cm at 20 cm/s and 5 cm at 25 cm/s. Searching first avoided proposing a test NASA had already flown. Four single runs do not establish repeatability, and the large samples flew on different flights from the small ones.</p></div>`
      : `<p class="small t2">Three of four cells are shown. Before anyone proposes a new experiment for the open cell, 1gnition searches the runs it has already indexed. Click the open cell to search.</p>`;

    const opts = D.runs.map(r => `<option value="${r.id}">${r.id} · ${esc(r.flight)}</option>`).join("");
    $("pA").innerHTML = opts; $("pB").innerHTML = opts;
    $("pA").value = S.sel[0]; $("pB").value = S.sel[1];

    const A = D.run(S.sel[0]), B = D.run(S.sel[1]);
    const maxScale = Math.ceil(Math.max(A.max_size_cm || A.steady_size_cm, B.max_size_cm || B.steady_size_cm) * 1.25);
    $("sizeBars").innerHTML = `<span class="small muted">Reported flame size in cm. The bar is steady size, the white tick is maximum size.</span>` + [A, B].map((r, i) => `
      <div class="sb"><span class="lab">${r.id}</span><div class="trk"><i class="fill ${i ? "b" : "a"}" data-w="${r.steady_size_cm / maxScale * 100}"></i>${r.max_size_cm != null ? `<i class="max" style="left:${r.max_size_cm / maxScale * 100}%"></i>` : ""}</div>
      <span class="val">steady ${pv("runs", r.id, "steady_size_cm", r.steady_size_cm)} <span class="muted">· max ${r.max_size_cm ?? "n/a"}</span></span></div>`).join("") +
      `<div class="axis"><span>0</span><span>${maxScale} cm</span></div>`;
    if (current === "compare") raf2(fillBars);

    const ch = L.diffCausal(A, B), sameFlight = A.flight === B.flight;
    const names = ch.map(x => x.label.toLowerCase());
    const d = +(B.steady_size_cm - A.steady_size_cm).toFixed(1);
    const outLine = d === 0 ? `Both runs reported a steady size of ${A.steady_size_cm} cm.` : `${B.id} reported ${B.steady_size_cm} cm and ${A.id} reported ${A.steady_size_cm} cm, a difference of ${Math.abs(d)} cm.`;
    let state, head, text;
    if (A.id === B.id) { state = "insuf"; head = "Pick two different runs"; text = "A run compared with itself says nothing."; }
    else if (ch.length === 0) { state = "expl"; head = "Same listed conditions"; text = `${outLine} The two runs repeat the same listed conditions${sameFlight ? "" : " on different flights"}.`; }
    else if (ch.length === 1) { state = "expl"; head = `One condition changed: ${names[0]}`; text = `${outLine} ${ch[0].label} went from ${ch[0].f(A)} to ${ch[0].f(B)}. Every other listed condition matched${sameFlight ? "" : ", but the runs flew on different flights"}.`; }
    else { state = "insuf"; head = `${ch.length} conditions changed together`; text = `${outLine} ${cap(listJoin(names))} all differ, so this pair cannot separate their effects.`; }
    const limits = ["One run per configuration, so repeatability is unknown.", "Table 2 gives no uncertainty for these sizes, so a 1 cm difference may sit inside the measurement resolution."];
    if (!sameFlight && A.id !== B.id) limits.push(`Different flights (${A.flight} and ${B.flight}). Procedures are not yet verified as equivalent.`);
    if ([A, B].some(r => r.provenance.checks < 2)) limits.push("At least one value was read from the table once and still needs a second check.");
    const cls = { expl: "ok", insuf: "bad" }[state];
    $("finding").className = "callout " + cls;
    $("finding").innerHTML = `<div class="row between"><h3>${esc(head)}</h3>${st(state)}</div><p class="small">${esc(text)}</p>
      <details><summary class="small muted" style="cursor:pointer">Limits on this reading</summary><ul class="clean small t2" style="margin-top:6px">${limits.map(l => `<li>${esc(l)}</li>`).join("")}</ul></details>
      ${state === "insuf" && A.id !== B.id ? `<div class="row"><span class="small t2">Try a one-change pair:</span>${suggestPairs(A).map(p => `<button class="chip" type="button" data-pair="${p[0]},${p[1]}">${p[0]} → ${p[1]}</button>`).join("")}</div>` : ""}`;

    $("cmpTitle").textContent = `${A.id} and ${B.id}, condition by condition`;
    $("cmpState").innerHTML = "";
    let rows = `<thead><tr><th>Condition</th><th>${A.id}</th><th>${B.id}</th><th>Status</th></tr></thead><tbody>`;
    L.COND.forEach(c => {
      const changed = L.diff(A, B).includes(c), isFlight = c.k === "flight", unknown = !L.known(A, c.k) || !L.known(B, c.k);
      const cl = unknown ? "unrep" : changed ? (isFlight ? "confound" : "changed") : "";
      const s = unknown ? `<span class="st u">unknown</span>` : changed ? (isFlight ? `<span class="st cf">confound</span>` : `<span class="st ch">changed</span>`) : `<span class="st m">matched</span>`;
      const v = r => unknown && !L.known(r, c.k) ? "not reported" : esc(c.f(r));
      rows += `<tr class="${cl}"><td>${c.k === "duct_height_cm" ? "Duct height (Urban Table 2 label)" : c.label}</td><td class="n">${v(A)}</td><td class="n">${v(B)}</td><td>${s}</td></tr>`;
    });
    [["Measurement uncertainty", "uncertainty_cm"], ["Repeat runs", "repeats"]].forEach(([l, k]) => {
      rows += `<tr class="unrep"><td>${l}</td><td class="n">${A[k] ?? "not reported"}</td><td class="n">${B[k] ?? "not reported"}</td><td><span class="st u">not in source</span></td></tr>`;
    });
    rows += `<tr class="outcome"><td>Steady flame size</td><td class="n">${pv("runs", A.id, "steady_size_cm", A.steady_size_cm + " cm")}</td><td class="n">${pv("runs", B.id, "steady_size_cm", B.steady_size_cm + " cm")}</td><td><span class="st m">outcome</span></td></tr>`;
    rows += `<tr><td>Maximum size</td><td class="n">${pv("runs", A.id, "max_size_cm", (A.max_size_cm ?? "n/a") + " cm")}</td><td class="n">${pv("runs", B.id, "max_size_cm", (B.max_size_cm ?? "n/a") + " cm")}</td><td><span class="st m">context</span></td></tr></tbody>`;
    $("cmpTable").innerHTML = rows;
    const loc = `${D.source(A.provenance.source_id).title}, ${A.provenance.location}`;
    $("cmpAI").innerHTML = `<div class="ai-h">${plain(C.AI_ENDPOINT ? "AI explanation" : "Explanation written by 1gnition rules (offline)")}<button class="btn btn-quiet btn-sm" type="button" data-ask="Explain the comparison between ${A.id} and ${B.id}">Ask a follow-up</button></div>
      <p>${ch.length === 1 ? `Between ${A.id} and ${B.id} the only listed change is ${names[0]}. The reported steady size ${d === 0 ? "stays at " + A.steady_size_cm + " cm" : "moves from " + A.steady_size_cm + " to " + B.steady_size_cm + " cm"}. 1gnition built this comparison from two published values. The paper reports that steady size was affected by oxygen and flow velocity, but it does not discuss this pair.`
        : ch.length === 0 ? `${A.id} and ${B.id} share every listed condition, so they act as a rough repeat. The difference between them hints at run-to-run spread.`
        : `${A.id} and ${B.id} differ in ${names.length} listed conditions, so the size difference cannot be credited to any one of them. Look for a pair that changes one condition at a time.`}</p>
      <span class="cite">Cites: ${esc(loc)}${D.findings.find(f => f.id === "F4") ? "; " + esc(D.source("saffire_i_v").title) + ", text" : ""}</span>`;
    $("cmpApply").innerHTML = applyBox([A, B], `How far ${A.id} and ${B.id} apply to your scenario`);
    const fl = D.flags.filter(f => (f.applies_to || []).some(id => id === A.id || id === B.id));
    $("flagsCard").innerHTML = `<div class="row between"><h2>Data checks for these runs</h2>${plain(fl.length + " open")}</div>` +
      (fl.length ? `<ul class="clean small">${fl.map(f => `<li><b style="color:var(--accent2)">${esc(f.title)}.</b> <span class="t2">${esc(f.detail)}</span></li>`).join("")}</ul>` : `<p class="small muted">No open checks for these runs.</p>`) +
      `<p class="tiny muted">An evidence tool should show conflicts in its sources instead of silently picking one.</p>`;
  }
  function suggestPairs(A) {
    return D.runs.filter(r => r.id !== A.id && L.diffCausal(A, r).length === 1).slice(0, 3).map(r => [A.id, r.id]);
  }
  function fillBars() { document.querySelectorAll("#sizeBars .fill").forEach(f => f.style.width = f.dataset.w + "%"); }
  function applyBox(rs, title) {
    const a = L.applicability(S, rs), cls = ["ok", "warn", "bad"][a.level];
    const head = ["Supported within the tested envelope", "Limited: this would be an extrapolation", "Unsupported: no numeric estimate is offered"][a.level];
    return `<div class="callout ${cls}"><span class="small muted">${esc(title)}: ${esc(scnLabel())}</span><h3>${head}</h3>${a.reasons.length ? `<ul class="clean small t2">${a.reasons.map(r => `<li>${esc(r)}</li>`).join("")}</ul>` : `<p class="small t2">Oxygen, pressure, gravity, material and outcome all sit inside what these runs tested.</p>`}</div>`;
  }

  /* ---------------- transfer ---------------- */
  /* Reads data/scientific_comparisons.json as delivered by the ML/science team.
     Every number here is a field from that file; the only arithmetic done here is
     the length difference and the oxygen/pressure deltas, which are labeled as derived. */
  const SVAR = {
    material: ["Material", ""], flow_direction: ["Flow direction", ""], flow_cm_s: ["Inlet airflow", "cm/s"],
    duct_full_height_cm: ["Full duct height", "cm"], duct_width_cm: ["Duct width", "cm"],
    sample_length_cm: ["Sample length", "cm"], sample_width_cm: ["Sample width", "cm"],
    oxygen_vol_pct: ["Oxygen", "vol %"], pressure_kpa: ["Pressure", "kPa"]
  };
  /* Factors the confounding warning names that Table 1 does not record as a field */
  const SMISSING = [
    [/\bRH\b/, "Relative humidity", "Not a Table 1 field, so it can't be checked."],
    [/entrance position/i, "Specimen position in the duct", "Not a Table 1 field. Position changes how developed the flow is at the flame."],
    [/instrumentation|fit comparability|camera/i, "Imaging and rate-fit method", "Camera setup and the time window used to fit each rate aren't recorded per row."],
    [/plateau/i, "Length of steady spread", "The IV steady-spread window is short, so its rate rests on less of the burn."],
    [/archive flow labels/i, "Airflow label across sources", "Archive records give a different airflow than the paper for this pair."]
  ];
  const sci = () => D.scientific_comparisons;
  const SCI = () => D.scientific_comparisons || {};
  /* Plain-language definitions for scientific terms, shown in the same popover as provenance */
  const GLOSS = {
    spread_rate: ["Flame-spread rate", "How fast the flame base advances along the material, in cm/s. Measured as the slope of base position against time over a steady stretch of the burn."],
    flame_length: ["Flame length", "Distance from the flame base to the visible flame tip, in cm. Depends on the camera and lighting. It is not a speed."],
    pyrolysis_length: ["Pyrolysis length", "Length of the zone where the solid is breaking down into fuel gas, in cm. Not necessarily equal to the visible flame length."],
    concurrent: ["Concurrent flow", "Air moves in the same direction the flame is spreading. Opposed flow is a different regime and is never pooled with it."],
    flow_direction: ["Flow direction", "Concurrent: air moves the same way as the flame front. Opposed: air moves against it. Unknown direction is left unset, never assumed."],
    full_duct_height: ["Full duct height", "The full inside height of the flow duct, as Olson et al. (2023) define it: 51 cm for Saffire I–III, 30.5 cm for IV–V. Not the same as Urban Table 2's 46 cm label or a wall clearance."],
    uncertainty: ["Uncertainty", "How far a value could plausibly be off. A digitizing envelope only says how precisely a plot was read; it is not NASA's measurement uncertainty or a confidence interval."],
    provenance: ["Provenance", "Where a number came from: the source, the table, figure or page, how it was read, and how many times the team checked it."],
    quench: ["Quenching and extinction", "A flame quenches when heat loss to nearby walls or the holder is too large to keep it burning. Extinction is reported separately from spread rate."],
    microgravity: ["Microgravity", "Near-weightlessness in orbit. Hot gas does not rise, so flames get oxygen only from slow diffusion or imposed airflow."],
    sibal: ["SIBAL", "A cotton-fiberglass fabric (about 75% cotton, 25% fiberglass) used as a standard Saffire and BASS test material. Not the same as pure cotton or PMMA."]
  };
  const term = (k, text) => GLOSS[k] ? `<span class="term" tabindex="0" data-term="${k}">${text}</span>` : text;
  const TERM_OF = { "Full duct height": "full_duct_height", "Flow direction": "flow_direction", "Material": "sibal" };
  const termize = lab => TERM_OF[lab] ? term(TERM_OF[lab], esc(lab)) : esc(lab);
  const t1 = id => (sci() && sci().table1_records || []).find(r => r.record_id === id);
  const fmtv = (v, u) => v === null || v === undefined ? "not reported" : `${v}${u ? (u.startsWith("vol") ? " " : " ") + u : ""}`;
  const sgn = v => (v > 0 ? "+" : v < 0 ? "−" : "±") + Math.abs(v).toFixed(2).replace(/\.?0+$/, "");
  const caseName = c => `${c.baseline} → ${c.comparison}`;
  const caseWhat = c => { const m = c.measurements; return m.sample_width_cm[0] !== m.sample_width_cm[1] ? "Narrower specimen" : m.duct_full_height_cm[0] !== m.duct_full_height_cm[1] ? "Shallower duct" : "Comparison"; };

  function pairChart(c, metric) {
    const isRate = metric === "rate", k = isRate ? "spread_cm_s" : "flame_length_cm", u = isRate ? "cm/s" : "cm";
    const vals = c.measurements[k], max = Math.max(...vals) * 1.3 || 1, W = 520, rowH = 40, l = 96, r = 70, H = 2 * rowH + 34;
    const X = v => l + v / max * (W - l - r);
    let g = "";
    const ticks = isRate ? [0, .1, .2, .3, .4, .5].filter(v => v <= max) : [0, 2, 4, 6, 8, 10, 12].filter(v => v <= max);
    ticks.forEach(v => { g += `<line x1="${X(v)}" y1="8" x2="${X(v)}" y2="${2 * rowH + 8}" stroke="#1c222c"/><text x="${X(v)}" y="${2 * rowH + 24}" text-anchor="middle">${v}</text>`; });
    [c.baseline, c.comparison].forEach((id, i) => {
      const y = 12 + i * rowH, v = vals[i];
      g += `<text x="${l - 10}" y="${y + 19}" text-anchor="end" class="lab">${esc(id)}</text>`;
      g += v === null ? `<text x="${l + 6}" y="${y + 19}" class="lab">not reported</text>`
        : `<rect x="${l}" y="${y + 4}" width="${Math.max(2, X(v) - l)}" height="22" rx="4" fill="${i ? "url(#gB)" : "url(#gA)"}"/><text x="${X(v) + 8}" y="${y + 20}" class="lab">${v} ${u}</text>`;
    });
    return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${isRate ? "Spread rate" : "Flame length"}: ${c.baseline} ${vals[0]} ${u}, ${c.comparison} ${vals[1]} ${u}"><defs><linearGradient id="gA"><stop offset="0" stop-color="#ff6a1f"/><stop offset="1" stop-color="#ffb020"/></linearGradient><linearGradient id="gB"><stop offset="0" stop-color="#0f8f9a"/><stop offset="1" stop-color="#2ad4c4"/></linearGradient></defs>${g}</svg>`;
  }
  function metricPanel(c, metric) {
    const isRate = metric === "rate", m = c.measurements;
    const head = isRate ? "Flame-spread rate, cm/s" : "Flame length, cm";
    const what = isRate ? "How fast the flame base moves along the sample." : "How far the flame reaches at steady burning. Pyrolysis length is the charred zone.";
    const loc = c.source_locations.map(x => pvs(c.source_id, esc(x))).join(" · ");
    const foot = isRate
      ? `<div class="sci-delta"><div><span>Difference</span><b class="num">${sgn(c.difference_cm_s)} cm/s</b></div><div><span>Change from ${esc(c.baseline)}</span><b class="num">${c.percent_change > 0 ? "+" : ""}${c.percent_change}%</b></div><div><span>Ratio</span><b class="num">${(+c.ratio).toFixed(2)}×</b></div></div>`
      : `<div class="sci-delta"><div><span>Flame length</span><b class="num">${m.flame_length_cm[0]} → ${m.flame_length_cm[1]} cm</b></div><div><span>Pyrolysis length</span><b class="num">${fmtv(m.pyrolysis_length_cm[0], "")} → ${fmtv(m.pyrolysis_length_cm[1], "cm")}</b></div><div><span>Difference <i class="tiny muted">derived</i></span><b class="num">${sgn(m.flame_length_cm[1] - m.flame_length_cm[0])} cm</b></div></div>`;
    return `<div class="sci-metric ${isRate ? "is-rate" : "is-len"}"><div class="row between"><h3>${head}</h3>${st("pub")}</div><p class="small t2">${what}</p>${pairChart(c, metric)}${foot}<p class="tiny muted">Read from ${loc}</p></div>`;
  }
  /* Cross-source conflicts. Three data-driven kinds, never hard-coded:
     1. data/source_conflicts.json (science team's closeout record): value disagreements and probable aliases.
     2. Urban Table 2 vs Olson Table 1 for the same burn (same id, or the probable alias from 1).
     3. PSI-99 archive airflow vs Olson Table 1 (alternative_source_claims). */
  const CONF = () => ((D.source_conflicts || {}).conflicts || []);
  const STATUS_TXT = { unresolved: "Unresolved", candidate_link_open: "Link open", probable_not_confirmed: "Probable, not confirmed", candidate_run_link: "Candidate run link" };
  const claimIds = c => c.claims.flatMap(x => [x.run_identifier, x.record_id, x.candidate_record_id]).filter(Boolean);
  const conflictRecords = id => CONF().filter(c => claimIds(c).includes(id));
  const aliasOf = id => { const c = CONF().find(c => c.type === "candidate_record_alias" && claimIds(c).includes(id)); return c ? claimIds(c).find(x => x !== id) : null; };
  function claimHTML(c) {
    const unit = c.unit ? " " + c.unit : "";
    return `<table class="claims"><tbody>${c.claims.map(x => {
      const val = x.value != null ? x.value + unit : x.spread_rate_cm_s != null ? x.spread_rate_cm_s + " cm/s (table)" : x.digitized_rate_approx_cm_s != null ? "≈" + x.digitized_rate_approx_cm_s + " cm/s (digitized)" : "";
      const rid = x.run_identifier || x.record_id || x.candidate_record_id || "";
      return `<tr><td><b class="num">${esc(val)}</b> <span class="small">for ${esc(rid)}</span><br>${D.source(x.source_id) ? pvs(x.source_id, esc(x.source_id)) : `<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.source_id)}</a>`}<span class="tiny muted"> · ${esc(x.source_locator)}</span></td></tr>`; }).join("")}</tbody></table>`;
  }
  function conflictsFor(id) {
    const out = [], r = t1(id);
    conflictRecords(id).forEach(c => out.push({ rank: 0, lab: c.type === "candidate_record_alias" ? "Identity" : (c.variable || "Value").replace(/_/g, " ").replace(/^\w/, m => m.toUpperCase()),
      html: `<span class="cfl-status">${esc(STATUS_TXT[c.match_status] || c.match_status)} · ${esc(STATUS_TXT[c.resolution_status] || c.resolution_status)}</span><span>${esc(c.display_message)}</span>${claimHTML(c)}<span class="tiny muted">${esc(c.possible_explanation || "")}${c.count_as_additional_independent_run === false ? " Not counted as a separate run." : ""}</span>` }));
    const alias = aliasOf(id), u = D.run(id) || (alias && D.run(alias));
    if (r && u) {
      const via = u.id === id ? "" : ` (${u.id}, probable alias)`;
      [["Sample width", u.sample_width_cm, r.sample_width_cm, "cm"], ["Sample length", u.sample_length_cm, r.sample_length_cm, "cm"],
       ["Duct height", u.duct_height_cm, r.duct_full_height_cm, "cm"], ["Oxygen", u.o2_pct, r.oxygen_vol_pct, "%"], ["Pressure", u.pressure_kpa, r.pressure_kpa, "kPa"]]
        .forEach(([lab, a, b, unit]) => { if (a != null && b != null && a !== b) out.push({ rank: 2, lab, html: `<span>${esc(id)}: Urban Table 2${esc(via)} gives ${a} ${unit}${lab === "Duct height" ? " (a duct label)" : ""}; Olson Table 1 gives ${b} ${unit}${lab === "Duct height" ? " (full duct height)" : ""}. ${pvs(r.source_id, "source")}</span>` }); });
    }
    ((SCI().alternative_source_claims || {})["ignis_psi99_rate_claims.csv"] || []).filter(p => p.table1_record_id === id && r && p.flow_velocity_cm_s !== r.flow_cm_s)
      .forEach(p => out.push({ rank: 1, lab: "Airflow", html: `<span>${esc(id)}: NASA PSI-99 archive gives ${p.flow_velocity_cm_s} cm/s; Olson Table 1 gives ${r.flow_cm_s} cm/s. ${pvs(p.source_id, "source")}</span>` }));
    return out;
  }
  function conditionsCard(c, idp = "sci") {
    const A = t1(c.baseline), B = t1(c.comparison), rows = c.comparability.filter(x => x.variable !== "overall" && x.variable !== "flight");
    const overall = c.comparability.find(x => x.variable === "overall");
    const line = x => {
      const [lab, u] = SVAR[x.variable] || [x.variable, ""], a = A ? A[x.variable] : null, b = B ? B[x.variable] : null;
      const d = typeof a === "number" && typeof b === "number" && a !== b ? ` <span class="tiny muted">(${sgn(+(b - a).toFixed(2))}${u ? " " + u : ""})</span>` : "";
      return `<li><b>${termize(lab)}</b><span class="num">${esc(fmtv(a, u))} · ${esc(fmtv(b, u))}${d}</span></li>`;
    };
    const same = rows.filter(x => /^same/.test(x.status)), diff = rows.filter(x => /^different/.test(x.status)), unk = rows.filter(x => !/^same|^different/.test(x.status));
    const flightSame = A && B && A.flight === B.flight;
    const flightLi = A && B ? `<li><b>Flight</b><span class="num">${esc(A.flight)} · ${esc(B.flight)}</span></li>` : "";
    const nulls = Object.entries(c.measurements).filter(([, v]) => v.some(x => x === null)).map(([k]) => `<li><b>${esc((SVAR[k] || [k.replace(/_/g, " ")])[0])}</b><span>No value in the record for at least one run.</span></li>`);
    const miss = SMISSING.filter(([re]) => re.test(c.confounding_warning)).map(([, lab, why]) => `<li><b>${esc(lab)}</b><span>${esc(why)}</span></li>`);
    const conf = [...conflictsFor(c.baseline), ...conflictsFor(c.comparison)].map((x, i) => [x, i]).sort((a, b) => (a[0].rank - b[0].rank) || a[1] - b[1]).map(([x]) => x);
    return `<div class="card" id="${idp}Cond"><div class="row between"><h2>Matched, changed, unknown and conflicting</h2><span class="small muted">${esc(c.baseline)} · ${esc(c.comparison)}, from ${srcLink(c.source_id)}</span></div>
      <div class="sci-cond four">
        <div class="cond-col ok"><h3><span class="ic ok">✓</span>Matched <i>${same.length + (flightSame ? 1 : 0)}</i></h3><ul>${same.map(line).join("")}${flightSame ? flightLi : ""}</ul></div>
        <div class="cond-col chg"><h3><span class="ic chg">≠</span>Changed <i>${diff.length + (flightSame ? 0 : 1)}</i></h3><ul>${diff.map(line).join("")}${flightSame ? "" : flightLi}</ul></div>
        <div class="cond-col miss"><h3><span class="ic miss">?</span>Unknown <i>${nulls.length + miss.length + unk.length}</i></h3><ul>${unk.map(line).join("")}${nulls.join("")}${miss.join("") || (unk.length || nulls.length ? "" : "<li><span>None named.</span></li>")}</ul></div>
        <div class="cond-col cfl"><h3><span class="ic cfl">!</span>Conflicting <i>${conf.length}</i></h3>${(() => { const li = x => `<li><b>${esc(x.lab)}</b>${x.html}</li>`;
          if (!conf.length) return "<ul><li><span>No cross-source conflict recorded for these rows.</span></li></ul>";
          const top = conf.filter(x => x.rank < 2), rest = conf.filter(x => x.rank >= 2);
          return `<ul>${top.map(li).join("")}${top.length ? "" : rest.slice(0, 2).map(li).join("")}</ul>${(top.length ? rest : rest.slice(2)).length ? `<details class="more-cfl"><summary>${(top.length ? rest : rest.slice(2)).length} rounding and definition differences</summary><ul>${(top.length ? rest : rest.slice(2)).map(li).join("")}</ul></details>` : ""}`; })()}</div>
      </div>
      <div class="callout warn"><span class="small muted">Descriptive comparison · causal effect not isolated</span>
        <p class="small">Because these also changed, the rate difference can't be credited to ${caseWhat(c) === "Shallower duct" ? "duct height" : caseWhat(c) === "Narrower specimen" ? "sample width" : "any one variable"} alone: <b>${esc(c.confounding_warning)}.</b> One summary value per run, so no statistical significance or run-to-run uncertainty can be stated.</p>
        ${overall ? `<p class="tiny muted">Overall status: ${esc(overall.status)}. ${esc(overall.reason.replace(/;/g, "; "))}</p>` : ""}</div></div>`;
  }
  function pairPicker(cases) {
    const M = S.sciMetric;
    return `<div class="row between wrap-gap">
          <div class="seg seg3" role="group" aria-label="Choose comparison">${cases.map((x, i) => `<button type="button" data-case="${i}" aria-pressed="${i === S.sciCase}">${esc(caseName(x))}</button>`).join("")}</div>
          <div class="seg seg3" role="group" aria-label="Choose measurement">${[["length", "Flame length, cm"], ["rate", "Spread rate, cm/s"], ["both", "Side by side"]].map(([k, l]) => `<button type="button" data-metric="${k}" aria-pressed="${M === k}">${l}</button>`).join("")}</div></div>`;
  }
  function metricsBlock(c) {
    const M = S.sciMetric;
    return `<div class="sci-metrics ${M === "both" ? "two" : ""}">${M === "both" ? metricPanel(c, "length") + metricPanel(c, "rate") : metricPanel(c, M)}</div>
        <p class="tiny muted">${term("flame_length", "Length")} and ${term("spread_rate", "rate")} are different quantities, so they never share an axis. Percentages use the first run as the denominator and the rounded Table 1 inputs.</p>`;
  }
  /* Compare Runs: the Olson 2023 account of the same flights, kept separate from the Urban 2021 flame-size grid above it */
  function renderCmpOlson() {
    const el = $("cmpOlson"); if (!el) return;
    const X = sci();
    if (!X) { el.innerHTML = `<div class="callout bad"><h3>Olson Table 1 data unavailable</h3><p class="small">data/scientific_comparisons.json did not load.</p></div>`; return; }
    const cases = X.comparison_cases; if (!(S.sciCase >= 0 && S.sciCase < cases.length)) S.sciCase = 0;
    const c = cases[S.sciCase];
    el.innerHTML = `<div class="sect" id="cmpOlsonHead">
        <div class="row between"><h2>Same flights, second source: flame length vs spread rate</h2><span class="ev-cls ev-derived_comparison">Derived comparison</span></div>
        <p class="small t2">The grid above is Urban et al. (2021) Table 2, which reports steady flame size only. Olson et al. (2023) Table 1 reports the same Saffire burns with ${term("spread_rate", "flame-spread rate")}, ${term("flame_length", "flame length")} and ${term("pyrolysis_length", "pyrolysis length")}, using flight-specific atmospheres and its own duct definition. The two tables are kept separate here.</p>
        ${pairPicker(cases)}
        ${metricsBlock(c)}
      </div>
      ${conditionsCard(c, "cmp")}`;
  }
  function crossCheckCard() {
    const ac = sci().alternative_source_claims || {}, f10 = ac["ignis_spread_rates_reviewed.csv"] || [], psi = ac["ignis_psi99_rate_claims.csv"] || [];
    const prob = f10.filter(x => /^probable/.test(x.crosswalk_status)), cand = f10.filter(x => /^candidate/.test(x.crosswalk_status)), none = f10.filter(x => !x.table1_candidate);
    return `<details class="sect sci-x" id="sciCross"><summary><h2>Source cross-checks and conflicts</h2><span class="small muted">${psi.length} archive rates · ${f10.length} Figure 10 markers. None count as extra runs.</span></summary>
      <div class="tw"><table class="t"><thead><tr><th>Archive entry</th><th>Archive rate</th><th>Table 1 row</th><th>Table 1 rate</th><th>Note</th></tr></thead><tbody>
      ${psi.map(p => { const r = t1(p.table1_record_id); return `<tr><td>${pvs(p.source_id, esc(p.source_id + " · " + p.source_location))}</td><td class="n">${p.outcome_value} ${esc(p.outcome_unit)} <span class="tiny muted">(= ${(p.outcome_value / 10).toFixed(2)} cm/s)</span></td><td>${esc(p.table1_record_id)}</td><td class="n">${r ? r.spread_cm_s + " cm/s" : "—"}</td><td class="small">${esc(p.relationship)}. Archive airflow ${p.flow_velocity_cm_s} cm/s${r && r.flow_cm_s !== p.flow_velocity_cm_s ? `, paper gives ${r.flow_cm_s} cm/s` : ""}.</td></tr>`; }).join("")}
      </tbody></table></div>
      <p class="small t2">Urban et al. Figure 10 was digitized into ${f10.length} markers. Concurrent flow is plotted to the left and opposed flow to the right. ${prob.length} have a probable Table 1 counterpart (${prob.map(x => esc(x.table1_candidate)).join(", ")}). ${cand.length} are BASS candidates whose rates differ from Table 1 by more than the reading envelope (${cand.map(x => `${esc(x.table1_candidate)} ${x.figure_minus_table_cm_s > 0 ? "+" : ""}${x.figure_minus_table_cm_s} cm/s`).join(", ")}), so they stay unresolved. ${none.length} have no identified counterpart. Digitized readings carry a ±0.01 cm/s reading envelope, which is ${term("uncertainty", "not measurement uncertainty")}. These sources overlap, so their counts are never added together. All of them are listed on the <a href="#data" data-gotab="figure10">Data page</a>.</p>
    </details>`;
  }
  function table1Card() {
    const rs = sci().table1_records || [];
    const cols = [["record_id", "Record", ""], ["flight", "Flight", ""], ["material", "Material", ""], ["sample_width_cm", "Width", "cm"], ["sample_length_cm", "Length", "cm"], ["duct_full_height_cm", "Full duct height", "cm"], ["oxygen_vol_pct", "O₂", "vol %"], ["pressure_kpa", "Pressure", "kPa"], ["flow_cm_s", "Airflow", "cm/s"], ["spread_cm_s", "Spread rate", "cm/s"], ["flame_length_cm", "Flame length", "cm"], ["pyrolysis_length_cm", "Pyrolysis length", "cm"]];
    return `<details class="sect sci-x" id="sciT1"><summary><h2>All ${rs.length} published records</h2><span class="small muted">Olson et al. (2023), Table 1. ${rs.filter(r => r.approved_for_ml).length} of ${rs.length} approved for ML training.</span></summary>
      <div class="tw"><table class="t nowrap"><thead><tr>${cols.map(([, h, u]) => `<th>${h}${u ? `, ${u}` : ""}</th>`).join("")}<th>Source location</th></tr></thead><tbody>
      ${rs.map(r => `<tr>${cols.map(([k]) => `<td class="${typeof r[k] === "number" ? "n" : ""}">${r[k] === null ? `<span class="muted">not reported</span>` : esc(String(r[k]))}</td>`).join("")}<td>${pvs(r.source_id, esc(r.source_locator))}</td></tr>`).join("")}
      </tbody></table></div><p class="tiny muted">BASS pyrolysis lengths are not reported in the source and stay empty. Wide specimens are 40.6 cm here; the 2021 Urban table rounds them to 41 cm.</p></details>`;
  }
  function factorialCard(idp = "fact") {
    const F = sci().factorial_readiness, ws = [...new Set(F.cells.map(c => c.width_cm))].sort((a, b) => a - b), hs = [...new Set(F.cells.map(c => c.full_duct_height_cm))].sort((a, b) => b - a);
    const cell = (w, h) => {
      const c = F.cells.find(x => x.width_cm === w && x.full_duct_height_cm === h), ids = c ? c.historical_ids : [];
      if (!ids.length) return `<div class="fx-cell fx-miss"><span class="fx-tag">Missing</span><b>No matching historical Saffire configuration</b><span class="small">${w} cm wide in a ${h} cm full-height duct, ${F.flow_cm_s} cm/s ${esc(F.flow_direction)}, ${esc(F.material)}</span><span class="tiny">In the team's indexed records. The first cell a new experiment must fill.</span></div>`;
      return ids.map(id => { const r = t1(id); return `<div class="fx-cell"><span class="fx-tag">${esc(id)} · Flight ${esc(r ? r.flight : "?")}<i class="fx-conf">confounded analog</i></span><b class="num">${r ? r.spread_cm_s + " cm/s" : "—"}</b><span class="tiny muted">${r ? `${r.oxygen_vol_pct}% O₂ · ${r.pressure_kpa} kPa · ${r.sample_length_cm} cm long · ${pvs(r.source_id, esc(r.source_locator))}` : ""}</span></div>`; }).join("");
    };
    return `<div class="card" id="${idp}Card"><div class="row between"><h2>The proposed 2 × 2 experiment: width × duct height</h2><span class="ev-cls ev-proposed_experiment">Proposed, not run</span></div>
      <p class="small t2">Held fixed: ${esc(F.material)}, ${term("concurrent", esc(F.flow_direction))} flow at ${F.flow_cm_s} cm/s, ${esc(F.gravity)}. Rows use ${term("full_duct_height", "full duct height")} as Olson et al. define it. Each filled cell is one historical burn shown as an analog.</p>
      <div class="fx"><div></div>${ws.map(w => `<div class="fx-h">${w} cm wide<span>${w === ws[0] ? "narrow" : "wide"}</span></div>`).join("")}
        ${hs.map(h => `<div class="fx-h fx-r">${h} cm duct<span>${h === hs[0] ? "deep" : "shallow"}</span></div>${ws.map(w => cell(w, h)).join("")}`).join("")}</div>
      <p class="tiny muted">Status: ${esc(F.status.replace(/_/g, " ").toLowerCase())}. The three historical analogs differ in flight, oxygen, pressure and sample length, so they are not a completed factorial experiment. Adding only the missing cell would not make them one.</p></div>`;
  }
  function hypothesisCard() {
    const F = sci().factorial_readiness;
    return `<div class="card hyp-card" id="hypCard"><div class="row between"><h2>Hypothesis</h2><span class="state s-insuf">${esc(F.hypothesis_status)}</span></div>
      <p class="hyp">${esc(F.hypothesis)}</p>
      <div class="eq" aria-label="Interaction equation">Δ = (v̄<sub>wide, shallow</sub> − v̄<sub>wide, deep</sub>) − (v̄<sub>narrow, shallow</sub> − v̄<sub>narrow, deep</sub>)<span>Δ in cm/s. v̄ is the mean flame-base spread rate of independent burns in a cell.</span></div>
      <p class="small t2">Δ &gt; 0 would support the pattern only in a properly controlled, replicated experiment, with an uncertainty interval from independent blocks or sessions. Published authors propose the physics: a wide flame's hot gas has less room to spread sideways in a shallow duct, while oxygen can still reach a narrow flame from its sides. 1gnition did not discover this.</p>
      <div class="sci-delta"><div><span>Interaction estimate</span><b class="num">${F.interaction_cm_s === null ? "none" : F.interaction_cm_s + " cm/s"}</b></div><div><span>95% interval</span><b class="num">${F.interval_cm_s === null ? "none" : esc(String(F.interval_cm_s))}</b></div></div>
      <div class="callout bad"><span class="small muted">Why the historical flights can't confirm it</span><p class="small">${esc(F.reason)}</p></div></div>`;
  }
  function protocolCard() {
    const F = sci().factorial_readiness;
    return `<div class="sect" id="protoSect"><h2>What the experiment would need</h2>
      <div class="proto">
        <div><h3>Hold fixed</h3><ul class="clean small t2"><li>Same fabric batch, areal density, thickness and sample length</li><li>Same duct planform (109 × 46 cm where feasible), mounting and entrance-to-igniter distance</li><li>Matched oxygen, total pressure, humidity, temperatures, ignition and calibrated inlet speed</li><li>One imaging and analysis protocol with a prespecified steady fit window</li></ul></div>
        <div><h3>Change</h3><ul class="clean small t2"><li>Specimen width: 5 cm and 40.6 cm</li><li>Full duct height: 51 cm and 30.5 cm</li><li>Nothing else</li></ul><h3 style="margin-top:12px">Measure</h3><ul class="clean small t2"><li>Flame-base position against time, so the ${term("spread_rate", "spread rate")} is a fitted slope</li><li>Local flow and wall/side clearances</li><li>Extinction, reported separately</li></ul></div>
        <div><h3>Replicate</h3><ul class="clean small t2"><li>Fresh, independently ignited specimens in all four cells</li><li>Randomized, block-balanced flights or sessions</li><li>Three burns per cell is a pilot idea, not a justified confirmatory sample size</li></ul><p class="tiny muted">${esc(F.protocol)} <a href="docs/Scientific_Methodology.md" target="_blank" rel="noopener">Scientific methodology</a> · <a href="docs/Scientific_Lead_Decision.md" target="_blank" rel="noopener">Scientific lead decision</a></p></div>
      </div>
      <details class="sci-x model-x"><summary><h3>A proposed scaling model, not fitted</h3><span class="ev-cls ev-proposed_experiment">Coefficients undefined</span></summary>
        <div class="eq small">ln(v̂ / v<sub>ref</sub>) = β<sub>0</sub> + β<sub>u</sub>(u / u<sub>ref</sub>) + β<sub>X</sub>(X<sub>O₂</sub> − X<sub>ref</sub>) + β<sub>P</sub> ln(P / P<sub>ref</sub>) + β<sub>G</sub> ln((w / H) / G<sub>ref</sub>)</div>
        <p class="small t2">u is inlet flow speed, X<sub>O₂</sub> the oxygen mole fraction (0.217, not 21.7), P pressure, w specimen width and H full duct height. Every β is undefined: nothing has been fitted to NASA data, so this formula produces no numbers anywhere on the site. A positive-rate log-linear form cannot represent extinction or a non-monotonic confinement effect, and G = w / H alone cannot separate width, height and their interaction. It is separate from the implemented M2 Ridge model.</p>
      </details></div>`;
  }
  /* B · Synthetic verification: invented data with known answers, used to check the factorial-analysis code */
  const SYN_LABEL = { positive: "Positive", zero: "Zero", negative: "Negative", positive_height_sessions: "Height-session design" };
  function synChart(s) {
    const exp = s.expected_cell_means_cm_s, est = (s.analysis || {}).cell_summaries || [];
    const val = (arr, w, h, k) => (arr.find(x => x.width_cm === w && x.full_duct_height_cm === h) || {})[k];
    const W = 520, H = 280, l = 56, r = 120, t = 20, b = 46, xs = [51, 30.5];
    const all = [...exp.map(x => x.mean_cm_s), ...est.map(x => x.mean)], lo = Math.min(...all) - .03, hi = Math.max(...all) + .03;
    const X = i => l + i * (W - l - r), Y = v => t + (hi - v) / (hi - lo) * (H - t - b);
    let g = "";
    for (let v = Math.ceil(lo * 20) / 20; v <= hi; v += .05) g += `<line x1="${l}" x2="${W - r}" y1="${Y(v)}" y2="${Y(v)}" stroke="#1c222c"/><text x="${l - 8}" y="${Y(v) + 4}" text-anchor="end">${v.toFixed(2)}</text>`;
    xs.forEach((h, i) => { g += `<text x="${X(i)}" y="${H - b + 20}" text-anchor="middle">${h} cm ${i ? "shallow" : "deep"}</text>`; });
    [[5, "#2ad4c4", "Narrow 5 cm"], [40.6, "#ff8a3d", "Wide 40.6 cm"]].forEach(([w, col, lab]) => {
      const e = xs.map(h => val(exp, w, h, "mean_cm_s")), m = xs.map(h => val(est, w, h, "mean"));
      g += `<line x1="${X(0)}" y1="${Y(e[0])}" x2="${X(1)}" y2="${Y(e[1])}" stroke="${col}" stroke-width="2" stroke-dasharray="5 5" opacity=".55"/>`;
      if (m.every(Number.isFinite)) { g += `<line x1="${X(0)}" y1="${Y(m[0])}" x2="${X(1)}" y2="${Y(m[1])}" stroke="${col}" stroke-width="3"/>`; m.forEach((v, i) => { g += `<circle cx="${X(i)}" cy="${Y(v)}" r="5" fill="${col}" stroke="#0a0c10" stroke-width="2"/>`; }); }
      g += `<text x="${X(1) + 12}" y="${Y(m[1] ?? e[1]) + 4}" fill="${col}" class="lab">${lab}</text>`;
    });
    g += `<text transform="translate(14 ${(t + H - b) / 2}) rotate(-90)" text-anchor="middle">Invented mean rate, cm/s</text>`;
    return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Synthetic interaction plot for the ${esc(SYN_LABEL[s.scenario] || s.scenario)} scenario">${g}</svg><p class="tiny muted">Dashed: the means programmed into the generator. Solid with dots: what the analysis recovered from the noisy invented burns. Unequal slopes are the interaction.</p>`;
  }
  function syntheticPane() {
    const V = D.synthetic_verification_results;
    if (!V) return `<div class="callout bad"><h3>Synthetic verification results not loaded</h3><p class="small">data/synthetic_verification_results.json is missing. Run backend/build_frontend_data.py.</p></div>`;
    const sc = V.scenarios; if (!(S.synCase >= 0 && S.synCase < sc.length)) S.synCase = 0;
    const s = sc[S.synCase], f4 = v => (v >= 0 ? "+" : "−") + Math.abs(v).toFixed(4), iv = s.approx_95pct_interval_cm_s;
    const B = D.synthetic_model_benchmark;
    const MOD = { mean: ["M0", "Training mean baseline"], condition_ridge: ["M1", "Ridge on flow, oxygen, pressure, material, direction"], geometry_ridge: ["M2", "M1 plus sample width"] };
    return `<div class="syn-banner" role="note"><b>SYNTHETIC VERIFICATION — NOT NASA DATA</b><span>NOT PHYSICAL VALIDATION</span><p>${esc(V.frontend_warning)}</p></div>
      <div class="card" id="synCard"><div class="row between wrap-gap"><h2>Does the analysis code recover a known answer?</h2>
        <div class="seg seg4" role="group" aria-label="Choose synthetic scenario">${sc.map((x, i) => `<button type="button" data-syn="${i}" aria-pressed="${i === S.synCase}">${esc(SYN_LABEL[x.scenario] || x.scenario)}</button>`).join("")}</div></div>
        <p class="small t2">The generator invents a 2 × 2 width × duct-height experiment with a chosen interaction, adds seeded noise, and hands the burns to the same analysis code a real experiment would use. If the code is right, it recovers the number the generator was told. Design: ${esc(s.design.replace(/_/g, " "))}, ${s.generated_independent_burns} invented burns in ${s.generated_independent_blocks_or_sessions} ${s.design.includes("session") ? "sessions" : "blocks"}.</p>
        <div class="syn-grid"><div>${synChart(s)}</div>
          <div class="sci-delta syn-stats">
            <div><span>Programmed Δ</span><b class="num">${f4(s.known_interaction_cm_s)} cm/s</b></div>
            <div><span>Recovered Δ</span><b class="num">${f4(s.estimated_interaction_cm_s)} cm/s</b></div>
            <div><span>Error</span><b class="num">${f4(s.estimate_minus_truth_cm_s)} cm/s</b></div>
            <div><span>Approx. 95% interval</span><b class="num">${iv.map(f4).join(" to ")}</b></div>
            <div><span>Interval contains 0</span><b class="num">${s.interval_contains_zero ? "yes" : "no"}</b></div>
            <div><span>Direction recovered</span><b class="num" style="color:${s.correct_estimate_direction ? "var(--eval)" : "var(--insuf)"}">${s.correct_estimate_direction ? "yes" : "no"}</b></div>
          </div></div>
        <p class="tiny muted">The interval reflects invented noise (per-burn SD ${V.sample_generation.per_burn_sd_cm_s} cm/s, shared block SD ${V.sample_generation.shared_block_sd_cm_s} cm/s, seed ${V.sample_generation.seed}). It is not a NASA confidence interval. The generator programmed the answers.</p></div>
      <div class="g2 g2-fill">
        <div class="sect"><h2>Invalid designs are refused</h2><ul class="refusals">${Object.entries(V.refusal_tests).map(([k, v]) => `<li><span class="ev-cls ev-synthetic">${esc(v.status)}</span><b>${esc(k.replace(/_/g, " "))}</b><span class="small t2">${esc(v.reason)} Interaction: ${v.interaction_cm_s === null ? "null" : v.interaction_cm_s}.</span></li>`).join("")}</ul>
          <p class="small ${V.all_checks_pass ? "" : "t2"}">${Object.entries(V.checks).map(([k, v]) => `<span class="chk ${v ? "ok" : "no"}">${v ? "✓" : "✗"} ${esc(k.replace(/_/g, " "))}</span>`).join(" ")}</p></div>
        ${B ? `<div class="sect" id="benchSect"><div class="row between"><h2>Model code benchmark</h2><span class="ev-cls ev-synthetic">Synthetic</span></div>
          <p class="small"><b>${esc(B.label)}.</b> ${esc(B.note)}</p>
          <div class="tw"><table class="t"><thead><tr><th>Model</th><th>Inputs</th><th>MAE on invented data, cm/s</th></tr></thead><tbody>
          ${Object.entries(B.models).map(([k, m]) => `<tr><td><b>${(MOD[k] || [k])[0]}</b> <span class="small t2">${esc((MOD[k] || ["", k])[1])}</span></td><td class="small t2">${m.features.length ? esc(m.features.join(", ")) : "none"}</td><td class="n">${m.mae_cm_s.toFixed(4)}</td></tr>`).join("")}
          </tbody></table></div>
          <p class="tiny muted">${Object.values(B.models)[0].n_test_observations} invented observations in ${Object.values(B.models)[0].n_independent_test_groups} invented groups. This checks that the code works. It says nothing about accuracy on NASA flights, and no model has been run on real Saffire holdouts.</p></div>` : ""}
      </div>`;
  }
  function predictionCard() {
    const X = sci(), rs = X.table1_records || [], f10 = (X.alternative_source_claims || {})["ignis_spread_rates_reviewed.csv"] || [];
    const cfg = {}; rs.forEach(r => { const k = [r.material, r.sample_width_cm, r.sample_length_cm, r.duct_full_height_cm, r.flow_cm_s].join("|"); cfg[k] = (cfg[k] || 0) + 1; });
    const checks = [
      ["Records approved for model training", `${rs.filter(r => r.approved_for_ml).length} of ${rs.length}`, false],
      ["Configurations burned more than once", `${Object.values(cfg).filter(n => n > 1).length} of ${Object.keys(cfg).length}`, Object.values(cfg).some(n => n > 1)],
      ["Figure 10 markers usable as extra runs", `${f10.filter(x => x.count_as_additional_run).length} of ${f10.length}`, false],
      ["Held-out flight evaluation", X.prediction_cm_s === null ? "not run" : "run", X.prediction_cm_s !== null]
    ];
    return `<div class="card" id="predCard"><div class="row between"><h2>Independent NASA spread-rate prediction</h2><span class="state s-insuf">Not validated</span></div>
      <div class="pred-hero"><div><span class="small muted">Backend status</span><b class="num">${esc(X.prediction_status)}</b></div><div><span class="small muted">Predicted rate</span><b class="num">${X.prediction_cm_s === null ? "none" : X.prediction_cm_s + " cm/s"}</b></div></div>
      <p class="small">1gnition does not show a predicted spread rate or an accuracy score, because no model has been validated on independent NASA flight data. Showing a number now would look like evidence it isn't.</p>
      <div class="gate">${checks.map(([l, h, ok]) => `<div><span class="ic ${ok ? "ok" : "need"}">${ok ? "✓" : "○"}</span><span>${esc(l)}</span><span class="have">${esc(h)}</span><span class="need">${ok ? "" : "Blocks validation"}</span></div>`).join("")}</div>
      <p class="tiny muted">The only model numbers on this site are in B · Synthetic verification, labelled as a software benchmark on invented data.</p></div>
    <div class="g2 g2-fill">
      <div class="card soft" id="apiCard"><h2>Published rates for your scenario</h2>${backendBox()}</div>
      <div class="sect"><h2>What would make a prediction trustworthy</h2><ul class="clean small t2">
        <li>Fresh, independently ignited specimens in all four cells of the 2 × 2 design, with common controls and randomized blocks.</li>
        <li>Independent burn, flight and run IDs; one spread-rate definition and unit; oxygen and pressure at measurement time; verified geometry and flow.</li>
        <li>A whole flight or campaign held out, with features and settings frozen before any test result is viewed.</li>
        <li>MAE and RMSE in cm/s beside a baseline and the number of independent burns. A negative result is reported as a result.</li></ul></div>
    </div>`;
  }
  function scenarioRequest() {
    const G = { micro: "microgravity", lunar: "lunar", mars: "mars", earth: "earth" };
    const q = { flow_velocity_cm_s: L.num(S.air), oxygen_percent: L.num(S.o2), pressure_kpa: L.num(S.p), material: S.mat, flow_direction: S.dir || null, gravity_regime: G[S.g] || S.g, combustion_regime: "steady_solid_spread" };
    const missing = [["flow_velocity_cm_s", "airflow"], ["oxygen_percent", "oxygen"], ["pressure_kpa", "pressure"], ["flow_direction", "flow direction"]].filter(([k]) => q[k] === null).map(([, l]) => l);
    return { q, missing };
  }
  function scenarioEndpoint() {
    if (!C.PREDICT_ENDPOINT) return "";
    const endpoint = new URL(C.PREDICT_ENDPOINT, location.href);
    endpoint.pathname = endpoint.pathname.replace(/\/predict\/?$/, "/scenario");
    return endpoint.href;
  }
  function backendBox() {
    const { q, missing } = scenarioRequest();
    const examples = (sci()?.table1_records || []).map(row =>
      `<option value="${esc(row.record_id)}">${esc(row.record_id)} · ${esc(row.material)} · ${row.spread_cm_s} cm/s</option>`).join("");
    return `<p class="small t2">Find published rates for your scenario. Matching uses each record’s material, airflow, oxygen, pressure, direction and gravity. Results include the specimen and duct dimensions.</p>
      <div class="field"><label for="apiExample">Load a published experiment</label><select id="apiExample"><option value="">Choose an experiment…</option>${examples}</select></div>
      ${C.PREDICT_ENDPOINT ? "" : '<p class="small">Connect the backend in the website configuration to search.</p>'}
      ${missing.length ? `<p class="small t2">Set ${listJoin(missing)} in your scenario, or load an experiment above.</p>` : ""}
      <details><summary class="small muted">Request details</summary><pre class="code-sm">POST /api/scenario\n${esc(JSON.stringify(q, null, 1))}</pre></details>
      <div class="row"><button class="btn btn-primary btn-sm" type="button" id="apiSend" ${missing.length || !C.PREDICT_ENDPOINT ? "disabled" : ""}>Find measured rates</button></div><div id="apiOut" aria-live="polite"></div>`;
  }
  function loadPublishedScenario(event) {
    const row = (sci()?.table1_records || []).find(item => item.record_id === event.target.value);
    if (!row) return;
    Object.assign(S, { hab: "custom", mat: row.material, out: "spread_rate",
      o2: String(row.oxygen_vol_pct), p: String(row.pressure_kpa), air: String(row.flow_cm_s),
      dir: row.flow_direction, g: "micro", note: `Loaded conditions from Olson Table 1, ${row.record_id}. Specimen geometry is shown with each result.` });
    renderAll();
    sendPredict();
  }
  function observationCard(item, exact) {
    const row = item.record;
    const dimensions = `${row.sample_width_cm} × ${row.sample_length_cm} cm specimen; ${row.duct_full_height_cm} cm duct height`;
    const differences = item.differing_conditions.map(d =>
      `<li>${esc(d.condition.replace(/_/g, " "))}: requested ${esc(String(d.requested))}; recorded ${d.recorded === null ? "unreported" : esc(String(d.recorded))}</li>`).join("");
    const source = D.source(row.source_id);
    return `<article class="callout ${exact ? "ok" : "warn"}">
      <div class="row between"><h3>${esc(row.record_id)} · ${esc(row.material)}</h3><span class="state s-pub">Published observation</span></div>
      <p><b class="num" style="font-size:28px">${item.measured_flame_spread_rate_cm_s} cm/s</b> <span class="small t2">(${item.measured_flame_spread_rate_mm_s} mm/s)</span></p>
      <p class="small">${exact ? "All supplied conditions match this record." : "Related experiment with different conditions."}</p>
      <p class="small t2">${row.oxygen_vol_pct}% oxygen · ${row.pressure_kpa} kPa · ${row.flow_cm_s} cm/s · ${esc(row.flow_direction)} · microgravity</p>
      <p class="small t2">${esc(dimensions)}${row.height_estimated ? ". Duct height is estimated in the source." : ""}</p>
      ${differences ? `<details open><summary class="small">Conditions that differ</summary><ul class="clean small t2">${differences}</ul></details>` : ""}
      <p class="tiny muted">Source: ${source ? srcLink(row.source_id) : esc(row.source_id)} · ${esc(row.source_locator)}</p>
    </article>`;
  }
  let scenarioController = null;
  async function sendPredict() {
    if (scenarioController) scenarioController.abort();
    const out = $("apiOut");
    if (!out) return;
    const { q, missing } = scenarioRequest();
    if (missing.length || !C.PREDICT_ENDPOINT) return;
    const controller = new AbortController();
    scenarioController = controller;
    const button = $("apiSend");
    button.disabled = true;
    out.innerHTML = '<p class="small muted">Searching published records… The free backend may take a minute to wake up.</p>';
    const snapshot = JSON.stringify(q);
    const timer = setTimeout(() => controller.abort(), 120000);
    try {
      const response = await fetch(scenarioEndpoint(), { method: "POST",
        headers: { "Content-Type": "application/json" }, body: snapshot, signal: controller.signal });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `Request failed (${response.status})`);
      if (!out.isConnected || snapshot !== JSON.stringify(scenarioRequest().q)) return;
      const measurements = result.measurements;
      if (!measurements || !Array.isArray(measurements.exact_matches) || !Array.isArray(measurements.related_measurements))
        throw new Error("The backend has not been updated with measurement lookup yet");
      const exact = measurements.exact_matches;
      const related = measurements.related_measurements;
      out.innerHTML = `<div class="stack" style="margin-top:16px">
        <h3>${exact.length ? `${exact.length} published measurement${exact.length === 1 ? "" : "s"} match your supplied conditions` : "No published measurement matches all supplied conditions"}</h3>
        ${measurements.omitted_geometry.length ? '<p class="small t2">Specimen and apparatus geometry were not specified. Each value applies to its recorded geometry, shown below. Multiple records remain separate.</p>' : ""}
        ${exact.map(item => observationCard(item, true)).join("")}
        ${related.length ? `<details ${exact.length ? "" : "open"}><summary class="small">Related measured rates (${related.length})</summary><p class="small t2">Ordered by proximity within the same material, flow direction and gravity. Differences are listed for each record.</p><div class="stack">${related.map(item => observationCard(item, false)).join("")}</div></details>` : ""}
        ${measurements.reason ? `<p class="small t2">${esc(measurements.reason)}</p>` : ""}
        <div class="callout"><h3>Model prediction unavailable</h3><p class="small">No evaluated model is active. The numbers above are published measurements for the listed experiments.</p></div>
      </div>`;
    } catch (error) {
      if (scenarioController !== controller || !out.isConnected || snapshot !== JSON.stringify(scenarioRequest().q)) return;
      const message = error.name === "AbortError" ? "The backend did not respond within two minutes. Try again after it wakes up." : error.message;
      out.innerHTML = `<div class="callout bad"><h3>Could not retrieve measurements</h3><p class="small">${esc(String(message))}</p></div>`;
    } finally {
      clearTimeout(timer);
      if (button.isConnected && scenarioController === controller) button.disabled = false;
    }
  }
  function replayCard() {
    const sat = D.spread_rates[0]; if (!sat || !D.run(sat.run_id)) return "";
    const len = D.run(sat.run_id).sample_length_cm, dist = sat.rate_mm_s * sat.duration_s / 10;
    return `<div class="card soft" id="replayCard"><div class="row between"><h2>Constant-rate illustration from a published average: ${esc(sat.series)}</h2>${st("pub")}</div>
        <div class="replay">
          <div class="rscale"><span>Airflow ${sat.airflow_cm_s} cm/s →</span><span>after ${sat.duration_s} s: ${dist.toFixed(1)} cm</span></div>
          <div class="rtrack" aria-hidden="true"><div class="rburnt" id="rpBurnt"></div><div class="rmark" style="left:${dist / len * 100}%"></div><div class="rfront" id="rpFront"></div></div>
          <div class="rscale"><span>0 cm</span><span>sample length ${len} cm (run ${sat.run_id})</span></div>
          <div class="row"><button class="btn btn-primary btn-sm" type="button" id="rpPlay">Play replay</button><span class="num small" id="rpClock" aria-live="polite">t = 0 s · 0.0 cm</span></div>
          <p class="small muted">x(t) = v·t with v = ${pv("spread_rates", sat.id, "rate_mm_s", sat.rate_mm_s + " mm/s")} (${(sat.rate_mm_s / 10).toFixed(2)} cm/s, the same value as Table 1 row I-1), for ${sat.duration_s} s: ${sat.rate_mm_s} mm/s × ${sat.duration_s} s = ${sat.rate_mm_s * sat.duration_s} mm = ${dist.toFixed(1)} cm. ${sat.duration_s} s plays in 10 s. A real front speeds up and slows down. Constant-rate illustration based on a published table value: not flight video, not a flame simulation.</p>
        </div></div>`;
  }

  function renderTransfer() {
    const X = sci(), a = L.applicability(S, D.runs), PANES = ["compare", "synthetic", "design", "predict", "apply"];
    if (!X) { $("stepper").innerHTML = ""; PANES.forEach(k => $("pane-" + k).classList.toggle("on", k === "compare")); $("pane-compare").innerHTML = `<div class="callout bad"><h3>Scientific comparison data unavailable</h3><p class="small">data/scientific_comparisons.json did not load, so no comparison is shown.</p></div>`; return; }
    if (!PANES.includes(S.step)) S.step = "compare";
    const cases = X.comparison_cases, F = X.factorial_readiness, filled = F.cells.filter(c => c.historical_ids.length).length;
    if (!(S.sciCase >= 0 && S.sciCase < cases.length)) S.sciCase = 0;
    $("trStrip").innerHTML = `<span><b>${X.table1_records.length}</b> published Table 1 records</span><span><b>${cases.length}</b> published comparisons</span><span><b>${filled} of ${F.cells.length}</b> experiment cells flown</span><span>NASA prediction: <b>${X.prediction_cm_s === null ? "not validated" : "available"}</b></span>`;
    const V = D.synthetic_verification_results;
    const steps = [["compare", "A · Published evidence", "ok", `${cases.length} pairs`], ["synthetic", "B · Synthetic check", "syn", V ? (V.all_checks_pass ? "checks pass" : "check failed") : "not loaded"], ["design", "C · Proposed test", "wait", `${F.cells.length - filled} cell missing`], ["predict", "NASA prediction", "bad", "not validated"], ["apply", "Your scenario", ["ok", "wait", "bad"][a.level], ["supported", "limited", "unsupported"][a.level]]];
    $("stepper").innerHTML = steps.map(([k, l, s, w]) => `<button type="button" role="tab" data-step="${k}" aria-selected="${S.step === k}"><span class="dot ${s}"></span>${l}<span class="stw ${s}">${w}</span></button>`).join("");
    PANES.forEach(k => $("pane-" + k).classList.toggle("on", S.step === k));

    const c = cases[S.sciCase];
    const sameLen = cases.filter(x => x.measurements.flame_length_cm[0] === x.measurements.flame_length_cm[1]);
    $("pane-compare").innerHTML = `
      <div class="card" id="sciCases"><div class="row between"><h2>Three published Saffire comparisons</h2><span class="small muted">Source: ${srcLink(c.source_id)}</span></div>
        <div class="tw"><table class="t sci-glance"><thead><tr><th>Comparison</th><th>What differs</th><th>Airflow, cm/s</th><th>${term("flame_length", "Flame length")}, cm</th><th>${term("spread_rate", "Spread rate")}, cm/s</th><th>Change in rate</th></tr></thead><tbody>
        ${cases.map((x, i) => { const m = x.measurements; return `<tr class="${i === S.sciCase ? "on" : ""}" data-case="${i}" tabindex="0" role="button" aria-pressed="${i === S.sciCase}"><td><b>${esc(caseName(x))}</b></td><td>${caseWhat(x)}</td><td class="n">${m.flow_cm_s[0] === m.flow_cm_s[1] ? m.flow_cm_s[0] : m.flow_cm_s.join(" → ")}</td><td class="n">${m.flame_length_cm.join(" → ")}</td><td class="n">${m.spread_cm_s.join(" → ")}</td><td class="n"><b>${sgn(x.difference_cm_s)}</b> (${x.percent_change > 0 ? "+" : ""}${x.percent_change}%)</td></tr>`; }).join("")}
        </tbody></table></div>
        <p class="small">${sameLen.length ? `In ${sameLen.length === 2 ? "two" : sameLen.length} of these pairs (${sameLen.map(caseName).map(esc).join(", ")}) the flames reached the same length while spreading at different rates, so flame length alone can't stand in for how fast a fire grows. ` : ""}Each is one burn against one burn, with no repeat to show run-to-run spread. These are descriptive results from published work, not new burns by our team.</p>
      </div>
      <div class="sect" id="sciMetric">${pairPicker(cases)}${metricsBlock(c)}</div>
      ${conditionsCard(c, "sci")}
      ${crossCheckCard()}
      ${table1Card()}
      ${replayCard()}`;
    if ($("rpPlay")) $("rpPlay").addEventListener("click", playReplay);
    $("pane-synthetic").innerHTML = syntheticPane();
    $("pane-design").innerHTML = `<div class="g2-wide g2-fill sci-design">${factorialCard("fact")}${hypothesisCard()}</div>${protocolCard()}`;
    $("pane-predict").innerHTML = predictionCard();
    if ($("apiSend")) $("apiSend").addEventListener("click", sendPredict);
    if ($("apiExample")) $("apiExample").addEventListener("change", loadPublishedScenario);
    $("pane-apply").innerHTML = `${applyBox(D.runs, "Applicability of all indexed runs")}
      <div class="row"><span class="small muted">Try another habitat:</span>${["iss", "lunar", "mars"].map(k => `<button class="chip" type="button" data-preset="${k}" aria-pressed="${S.hab === k}">${L.PRESET[k].label}</button>`).join("")}</div>
      <p class="small muted">No spread-rate estimate is shown for any scenario, because no prediction has been validated on independent flight data. Matching uses the team's indexed records only.</p>`;
  }
  let rpRAF = null;
  function playReplay() {
    const sat = D.spread_rates[0]; if (!sat || !$("rpPlay")) return;
    cancelAnimationFrame(rpRAF);
    const len = D.run(sat.run_id).sample_length_cm, Dur = REDUCE ? 0 : 10000, t0 = performance.now();
    $("rpPlay").textContent = "Playing";
    const step = now => {
      if (!$("rpBurnt")) return;
      const f = Dur ? Math.min(1, (now - t0) / Dur) : 1, ts = f * sat.duration_s, cm = sat.rate_mm_s * ts / 10, pct = cm / len * 100;
      $("rpBurnt").style.width = pct + "%"; $("rpFront").style.left = pct + "%";
      $("rpClock").textContent = `t = ${ts.toFixed(0)} s · ${cm.toFixed(1)} cm`;
      if (f < 1) rpRAF = requestAnimationFrame(step); else $("rpPlay").textContent = "Replay again";
    };
    rpRAF = requestAnimationFrame(step);
  }

  /* ---------------- gaps ---------------- */
  function renderGapTypes() {
    const el = $("gapTypes"); if (!el) return;
    const X = sci(); if (!X) { el.innerHTML = ""; return; }
    const F = X.factorial_readiness, rs = X.table1_records, alt = X.alternative_source_claims || {}, f10 = alt["ignis_spread_rates_reviewed.csv"] || [];
    const miss = F.missing_configuration[0];
    const noLink = f10.filter(x => !x.table1_candidate).length, unres = f10.filter(x => /^candidate/.test(x.crosswalk_status)).length;
    const atmUnknown = f10.filter(x => x.atmosphere_status && /unknown/.test(x.atmosphere_status)).length;
    const invNoAtm = D.investigations.filter(v => !v.o2_pct_range || !v.pressure_kpa_range);
    const pyroNull = rs.filter(r => r.pyrolysis_length_cm === null).length;
    const conflicts = rs.reduce((n, r) => n + conflictsFor(r.record_id).length, 0) + D.flags.length;
    const cfg = {}; rs.forEach(r => { const k = [r.material, r.sample_width_cm, r.sample_length_cm, r.duct_full_height_cm, r.flow_cm_s, r.oxygen_vol_pct, r.pressure_kpa].join("|"); cfg[k] = (cfg[k] || 0) + 1; });
    const once = Object.values(cfg).filter(n => n === 1).length;
    const ap = L.applicability(S, D.runs);
    const T = [
      ["cfg", "Missing experiment configuration", miss ? "1 cell" : "none", miss ? `${miss.width_cm} cm wide × ${miss.full_duct_height_cm} cm full duct height, ${F.flow_cm_s} cm/s ${F.flow_direction}, ${F.material}. No matching historical Saffire configuration in the team's indexed records.` : "All four design cells have an analog.", "Fly it as part of the full replicated 2 × 2 below, not as a single burn."],
      ["id", "Missing run identity", `${noLink + unres} markers`, `${noLink} of ${f10.length} Figure 10 markers have no Table 1 counterpart and ${unres} BASS candidates disagree with Table 1 beyond the reading envelope. ${CONF().filter(c => c.type === "candidate_record_alias").map(c => c.display_message).join(" ")}`, "Recover the BASS test logs and the Saffire card/flight log before any hard join."],
      ["hist", "Missing atmosphere, geometry or flow history", `${atmUnknown + invNoAtm.length + pyroNull} gaps`, `${atmUnknown} Figure 10 markers have no point-level oxygen or pressure. ${invNoAtm.length} investigations have no indexed atmosphere (${invNoAtm.map(v => v.name).join(", ")}). ${pyroNull} Table 1 rows have no pyrolysis length. Humidity and flow histories are not in any table.`, "Extract per-run conditions from the PSI records, not nominal values."],
      ["cfl", "Source conflicts", `${conflicts} items`, `${CONF().length} recorded source conflicts (${CONF().map(c => c.subject).join("; ")}), all kept unresolved. Urban 2021 and Olson 2023 also round dimensions and define duct height differently, PSI-99 airflow disagrees with the paper, and ${D.flags.length} data checks are open.`, "Keep each source's value and show the conflict; never average it away."],
      ["rep", "Insufficient independent replication", `${once} of ${Object.keys(cfg).length} once`, `Every Olson Table 1 configuration was burned once, so run-to-run variability is unknown and no difference can be called significant.`, "Repeat burns with independent specimens in randomized blocks."],
      ["dom", "Out-of-domain scenario", ["inside", "partial", "outside"][ap.level], ap.reasons.join(" "), ap.level ? "Treat any answer for this habitat as a research gap, not an estimate." : "Still an observation at recorded settings, not a prediction."]
    ];
    el.innerHTML = `<div class="sect" id="gapTypesSect"><div class="row between"><h2>Six kinds of gap, kept apart</h2><span class="small muted">Computed from the team's indexed dataset, not all NASA research</span></div>
      <div class="gtypes">${T.map(([k, h, n, d, next]) => `<div class="gt gt-${k}"><div class="row between"><h3>${h}</h3><b class="num">${esc(n)}</b></div><p class="small t2">${esc(d)}</p><p class="tiny"><span class="muted">Next:</span> ${esc(next)}</p></div>`).join("")}</div></div>
      <div class="g2-wide g2-fill sci-design">${factorialCard("gapFact")}
        <div class="card soft"><h2>Why one new burn isn't enough</h2>
          <p class="small t2">Filling only the missing cell would compare a new burn against three old ones from different flights, oxygen levels, pressures and sample lengths. Any interaction estimate would mix the duct-height effect with those differences.</p>
          <p class="small t2">The test needs all four cells re-flown with fresh specimens, common controls and randomized blocks. That design, the hypothesis and the interaction formula are in <a href="#transfer" data-step-go="design">Scale transfer → C · Proposed test</a>.</p>
          <p class="small"><span class="state s-insuf">Hypothesis: ${esc(F.hypothesis_status)}</span></p></div></div>`;
  }
  function renderGaps() {
    renderGapTypes();
    const m = mapSVG({ o2: S.o2, p: S.p, mat: S.gMat, drag: true });
    $("map").innerHTML = m.svg;
    const o2 = L.num(S.o2), p = L.num(S.p);
    $("gapStrip").innerHTML = `<span><b>${D.runs.length}</b> runs plotted</span><span>Highest oxygen indexed: <b>${Math.max(...D.runs.map(r => r.o2_pct))}%</b></span><span>Gravity levels indexed: <b>${[...new Set(D.runs.map(r => r.gravity))].length}</b> (${[...new Set(D.runs.map(r => L.GRAV[r.gravity]))].join(", ")})</span>`;
    let read;
    if (o2 === null || p === null) read = `<p class="small t2">Your scenario has no oxygen or pressure set. Click the map to place your habitat.</p>`;
    else if (!m.rs.length) read = `<p class="small t2">No indexed run uses this material.</p>`;
    else {
      const r = m.nr.r, inside = L.within(r, o2, p);
      read = `<div class="row">${inside ? st("expl") : st("insuf")}<span class="num small">${o2}% O₂ · ${p} kPa</span></div>
        <p class="small">${inside ? `Inside the tolerance box of run <b>${r.id}</b>.` : `Outside every tested box. Nearest run: <b>${r.id}</b> at ${r.o2_pct}% oxygen and ${r.pressure_kpa} kPa, ${Math.abs(r.o2_pct - o2).toFixed(1)} points of oxygen and ${Math.abs(r.pressure_kpa - p).toFixed(1)} kPa away.`}</p>
        ${S.g !== "micro" ? `<p class="small t2">Gravity still differs: every indexed run is microgravity and your scenario is ${L.GRAV[S.g]}.</p>` : ""}
        ${m.onMap ? "" : `<p class="small muted">Your habitat lies outside the plotted range.</p>`}`;
    }
    $("readout").innerHTML = read + `<p class="tiny muted">Tolerance boxes are ±${C.TOLERANCE.o2_pct} point of oxygen and ±${C.TOLERANCE.pressure_kpa} kPa (design choice). Click or drag the map, or use arrow keys.</p>`;
    renderProposal();
    renderHeat();
  }
  function renderProposal() {
    const o2 = L.num(S.o2), p = L.num(S.p), o = L.OUT[S.out];
    if (o2 === null || p === null) { $("proposal").innerHTML = `<div class="callout warn"><h3>Set oxygen and pressure first</h3><p class="small t2">A follow-up needs a target atmosphere. Unset values are never replaced with Earth air.</p></div>`; return; }
    const pool = D.runs.filter(r => r.material === S.mat), base = (pool.length ? pool : D.runs);
    const cand = L.nearest(base, o2, p).r;
    if (L.within(cand, o2, p) && pool.length && S.out === "steady_size" && S.g === cand.gravity) {
      $("proposal").innerHTML = `<div class="callout ok"><h3>A relevant run is already indexed</h3><p class="small t2">Run ${cand.id} burned ${L.matName(cand.material)} at ${cand.o2_pct}% oxygen and ${cand.pressure_kpa} kPa in ${L.GRAV[cand.gravity]}. No new test is proposed.</p><div class="row"><button class="btn btn-primary btn-sm" type="button" data-pair="${cand.id},${cand.id === "II-5" ? "II-6" : "II-5"}">Compare it</button></div></div>`; return;
    }
    const dO = Math.abs(cand.o2_pct - o2) > C.TOLERANCE.o2_pct, dP = Math.abs(cand.pressure_kpa - p) > C.TOLERANCE.pressure_kpa;
    const first = dO ? `oxygen, from ${cand.o2_pct}% toward ${o2}%` : dP ? `pressure, from ${cand.pressure_kpa} kPa toward ${p} kPa` : "none in atmosphere";
    const n = (dO ? 1 : 0) + (dP ? 1 : 0);
    $("proposal").innerHTML = `<div style="display:grid;gap:12px">
      <div class="row">${st("insuf")}<span class="small muted">Searched ${D.runs.length} indexed runs first.</span></div>
      <dl class="prop">
        <dt>Open question</dt><dd>${cap(o.label)} of ${L.matName(S.mat)} at ${o2}% oxygen and ${p} kPa in ${L.GRAV[S.g]}.</dd>
        <dt>Start from</dt><dd>Run ${cand.id}: ${L.matName(cand.material)}, ${cand.o2_pct}% oxygen, ${cand.pressure_kpa} kPa, ${cand.airflow_cm_s} cm/s, ${cand.sample_width_cm} × ${cand.sample_length_cm} cm, ${cand.duct_height_cm} cm duct.${pool.length ? "" : " No run with your material is indexed, so this is the nearest atmosphere."}</dd>
        <dt>Change</dt><dd>${n ? `Step 1 of ${n}: ${first}. One variable per step.` : "Atmosphere already matches within tolerance."}${S.out !== "steady_size" ? ` The baseline reports flame size, so ${o.label} must be measured too.` : ""}</dd>
        <dt>Hold fixed</dt><dd>Material, airflow, sample size, duct height${dO && dP ? " and pressure" : ""}.</dd>
        <dt>Measure</dt><dd>${cap(o.label)}${o.unit ? " in " + o.unit : ""}, with stated uncertainty and at least one repeat.</dd>
        ${S.g !== "micro" ? `<dt>Separate gap</dt><dd>${cap(L.GRAV[S.g])} has no indexed baseline. Microgravity steps cannot close it.</dd>` : ""}
      </dl>
      <p class="tiny muted">The highest-priority suggestion under these assumptions. It is not an optimal NASA experiment plan, and feasibility is not assessed.</p></div>`;
  }
  function renderHeat() {
    const o2 = L.num(S.o2), p = L.num(S.p), T = C.TOLERANCE;
    const cols = ["Outcome asked", "Material", "Oxygen", "Pressure", "Gravity", "Runs indexed", "Spread rates", "PSI record"];
    const rows = D.investigations.map(v => {
      const runs = D.runs.filter(r => r.investigation_id === v.id), sr = D.spread_rates.filter(r => r.investigation_id === v.id);
      const cell = (cls, txt) => `<td><span class="hc ${cls}">${txt}</span></td>`;
      const out = v.outcomes.includes(S.out) ? cell("t2", "measured") : v.outcomes.length ? cell("no", "other outcomes") : cell("x", "not indexed");
      const mat = v.fuel_type !== "solid" ? cell("no", esc(v.fuel_type)) : v.materials.includes(S.mat) ? cell("t2", "tested") : cell("t", "other solids");
      const rng = (r, x, tol, u) => !r ? cell("x", "not indexed") : x === null ? cell("t", L.fmtRange(r, u)) : (x >= r[0] - tol && x <= r[1] + tol) ? cell("t2", L.fmtRange(r, u)) : cell("t", L.fmtRange(r, u));
      const grav = (v.gravity || []).includes(S.g) ? cell("t2", "micro") : cell("no", "micro only");
      const psi = v.psi_id ? cell(v.psi_confirmed ? "t" : "m", v.psi_id + (v.psi_confirmed ? "" : "?")) : cell("x", "not linked");
      return `<tr><th>${esc(v.name)}</th>${out}${mat}${rng(v.o2_pct_range, o2, T.o2_pct, "%")}${rng(v.pressure_kpa_range, p, T.pressure_kpa, " kPa")}${grav}${runs.length ? cell("t", runs.length) : cell("x", "0")}${sr.length ? cell("t", sr.length) : cell("x", "0")}${psi}</tr>`;
    }).join("");
    $("heat").innerHTML = `<table><thead><tr><th></th>${cols.map(c => `<th class="c">${c}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table>`;
  }
  /* drag */
  let dragging = false;
  function mapCoords(e) {
    const svg = $("map").querySelector("svg"), r = svg.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width * MP.W, y = (e.clientY - r.top) / r.height * MP.H;
    return [MP.x0 + (x - MP.L) / (MP.W - MP.L - MP.R) * (MP.x1 - MP.x0), MP.y0 + (MP.H - MP.B - y) / (MP.H - MP.T - MP.B) * (MP.y1 - MP.y0)];
  }
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  function setHab(o2, p, full) {
    S.o2 = String(Math.round(clamp(o2, MP.x0, MP.x1) * 10) / 10); S.p = String(Math.round(clamp(p, MP.y0, MP.y1) * 2) / 2);
    if (S.hab !== "custom") { S.hab = "custom"; S.note = L.PRESET.custom.note; }
    if (full) renderAll(); else { syncSide(); renderGaps(); }
  }

  /* ---------------- data view ---------------- */
  const TABS = {
    runs: { label: "Runs · Urban T2", cls: ["published_numeric", "Published numbers, Urban et al. 2021 Table 2 (steady flame size, cm). Source-scoped: Olson 2023 reports the same flights with different rounding and duct definitions."], rows: () => D.runs, cols: [
      ["id", "Run", "Run label from the source table"], ["prov", "Provenance", "Source, location, read method and number of checks"], ["flight", "Flight", "Mission or campaign"], ["material", "Material", "Material code"],
      ["o2_pct", "O₂ %", "Oxygen by volume, percent"], ["pressure_kpa", "kPa", "Total pressure, kilopascals"], ["airflow_cm_s", "Flow cm/s", "Imposed flow speed"],
      ["duct_height_cm", "Duct cm", "Flow duct height"], [r => r.sample_width_cm + " × " + r.sample_length_cm, "Sample cm", "Width × length, centimeters"],
      ["steady_size_cm", "Steady cm", "Reported steady state flame size"], ["max_size_cm", "Max cm", "Reported maximum flame size"]] },
    table1: { label: "Olson Table 1", cls: ["published_numeric", "Published numbers, Olson et al. 2023 Table 1. The canonical source for spread rates. 0 of 8 approved for model training."], rows: () => SCI().table1_records || [], cols: [
      ["record_id", "Record", "Source-scoped record id"], ["flight", "Flight", "Saffire flight or BASS"], ["material", "Material", "SIBAL (cotton-fiberglass) or cotton"],
      [r => r.sample_width_cm + " × " + r.sample_length_cm, "Sample cm", "Specimen width × length, cm"], ["duct_full_height_cm", "Full duct height, cm", "Full duct height as Olson defines it (not Urban's 46 cm label)"],
      ["oxygen_vol_pct", "O₂, vol %", "Oxygen by volume, percent, at hatch closure"], ["pressure_kpa", "kPa", "Total pressure"], ["flow_cm_s", "Flow, cm/s", "Concurrent inlet speed"],
      ["spread_cm_s", "Spread, cm/s", "Flame-base spread rate"], ["flame_length_cm", "Flame length, cm", "Visible flame length"], ["pyrolysis_length_cm", "Pyrolysis, cm", "Pyrolysis length; null where not reported"],
      ["source_locator", "Location", "Table, page and row"]] },
    figure10: { label: "Figure 10 · digitized", cls: ["digitized", "Markers read off Urban et al. 2021 Figure 10 by the team. Approximate. The ±0.01 cm/s envelope is reading precision, not NASA uncertainty. Not counted as runs."], rows: () => ((SCI().alternative_source_claims || {})["ignis_spread_rates_reviewed.csv"] || []), cols: [
      ["observation_id", "Marker", "Team digitization id"], ["flow_direction", "Direction", "Concurrent (plotted left) or opposed (right)"], ["sample_width_cm", "Width, cm", "Width in the figure legend"],
      ["flow_cm_s_redigitized", "Flow, cm/s", "Digitized flow magnitude"], ["spread_cm_s_redigitized", "Spread, cm/s", "Digitized spread rate"], ["digitization_rate_envelope_cm_s", "± reading, cm/s", "Manual reading envelope"],
      [r => r.table1_candidate || "none", "Table 1 match", "Possible Olson Table 1 counterpart"], ["crosswalk_status", "Crosswalk", "probable, candidate or none"], ["source_location", "Location", "Figure and page"]] },
    psi99: { label: "PSI-99 archive", cls: ["archive_claim", "Values recorded in the NASA PSI-99 experimental table. Alternative claims for the same burns as Table 1, not new runs. The archive airflow conflicts with the paper."], rows: () => ((SCI().alternative_source_claims || {})["ignis_psi99_rate_claims.csv"] || []), cols: [
      ["observation_id", "Entry", "Archive entry id"], ["run_id", "Archive run", "Run id in the archive"], ["outcome_value", "Rate, mm/s", "Value as printed (mm/s)"], [r => (r.outcome_value / 10).toFixed(2), "Rate, cm/s", "Converted: mm/s ÷ 10"],
      ["flow_velocity_cm_s", "Archive flow, cm/s", "Airflow given in the archive"], ["table1_record_id", "Table 1 row", "Same burn in Olson Table 1"], ["relationship", "Relationship", "How it relates to Table 1"], ["source_location", "Location", "Archive table row"]] },
    synthetic: { label: "Synthetic · not NASA", cls: ["synthetic", "SYNTHETIC VERIFICATION, NOT NASA DATA. Invented rates with known answers, used only to check the factorial-analysis software."], rows: () => ((D.synthetic_verification_results || {}).scenarios || []), cols: [
      ["scenario", "Scenario", "Invented case"], ["design", "Design", "Randomized complete blocks or height sessions"], ["generated_independent_burns", "Burns", "Invented burns"],
      [r => (+r.known_interaction_cm_s).toFixed(3), "True Δ, cm/s", "Interaction programmed into the generator"], [r => (+r.estimated_interaction_cm_s).toFixed(4), "Estimated Δ, cm/s", "What the software recovered"],
      [r => r.approx_95pct_interval_cm_s.map(v => v.toFixed(4)).join(" to "), "Approx. 95% interval", "Synthetic noise only, not NASA uncertainty"]] },
    conflicts: { label: "Source conflicts", cls: ["archive_claim", "Disagreements between sources and probable record aliases, from data/source_conflicts.json. Both claims are kept; none is silently chosen, and none counts as an extra run."], rows: () => CONF(), cols: [
      ["conflict_id", "Conflict", "Stable id"], ["subject", "Subject", "Records involved"], [r => r.claims.map(x => `${x.source_id}: ${x.value != null ? x.value + (r.unit ? " " + r.unit : "") : x.spread_rate_cm_s != null ? x.spread_rate_cm_s + " cm/s" : x.digitized_rate_approx_cm_s != null ? "≈" + x.digitized_rate_approx_cm_s + " cm/s" : ""} (${x.source_locator})`).join(" | "), "Claims", "Each source's value and location"],
      ["match_status", "Match", "How the records are linked"], ["resolution_status", "Resolution", "unresolved or open; never auto-resolved"], ["display_message", "Message", "What the site shows"]] },
    spread_rates: { label: "Spread rates", rows: () => D.spread_rates, cols: [
      ["id", "ID", "Row id"], ["prov", "Provenance", "Source, location, read method and number of checks"], ["series", "Series", "Configuration as named in the source"], ["material", "Material", "Material code"], ["sample_width_cm", "Width, cm", "Sample width"],
      ["flow_direction", "Flow", "concurrent or opposed"], ["o2_pct", "O₂, %", "Oxygen percent"], ["pressure_kpa", "Pressure, kPa", "Total pressure"], ["rate_mm_s", "Rate, mm/s", "Flame spread rate"],
      ["kind", "Kind", "steady, average over burn, or instantaneous"]] },
    investigations: { label: "Investigations", rows: () => D.investigations, cols: [
      ["name", "Investigation", "Name"], [r => r.pillars.map(p => L.PILLAR[p]).join(", "), "Pillars", "Prevention, detection, suppression"], ["fuel_type", "Fuel", "Fuel type"],
      [r => r.outcomes.map(o => L.OUT[o].label).join(", ") || "not indexed", "Outcomes", "What it measured"], [r => L.fmtRange(r.o2_pct_range, "%") || "not indexed", "O₂", "Tested oxygen range"],
      [r => L.fmtRange(r.pressure_kpa_range, " kPa") || "not indexed", "Pressure", "Tested pressure range"], [r => r.psi_id ? r.psi_id + (r.psi_confirmed ? "" : " (unconfirmed)") : "not linked", "PSI", "PSI record id"],
      [r => r.source_ids.length, "Sources", "Number of cited sources"]] },
    findings: { label: "Findings", rows: () => D.findings, cols: [["id", "ID", "Row id"], ["text", "Published finding", "Statement as reported, paraphrased"], [r => (D.source(r.source_id) || {}).title, "Source", "Where it is stated"], ["location", "Location", "Section, table or page"]] },
    flags: { label: "Data checks", rows: () => D.flags, cols: [["title", "Check", "Short name"], ["severity", "Type", "conflict or check"], ["detail", "Detail", "What disagrees and what 1gnition shows"], [r => (r.applies_to || []).join(", "), "Applies to", "Affected rows"]] },
    sources: { label: "Sources", rows: () => D.sources, cols: [["title", "Source", "Title"], ["type", "Type", "paper, slides, psi, brief or web"], ["url", "Link", "Where to read it"], ["note", "Note", "What is used from it"]] }
  };
  function cellVal(r, c) {
    const k = c[0];
    if (k === "prov") { const p = r.provenance || {}; return { csv: `${(D.source(p.source_id) || {}).title || p.source_id}; ${p.location}; ${p.method}; checks=${p.checks}`,
      html: `<span class="row" style="gap:6px;flex-wrap:nowrap"><span class="meth ${esc(p.method)}">${esc(p.method)}</span><span class="small t2" style="white-space:nowrap">${esc(p.location.replace("printed ", ""))}</span><span class="small ${p.checks >= 2 ? "muted" : ""}" style="${p.checks < 2 ? "color:var(--accent)" : ""}" title="${p.checks < 2 ? "Needs a second person to check this value" : "Checked independently"}">${p.checks >= 2 ? "checked twice" : "checked once, needs recheck"}</span></span>` }; }
    const v = typeof k === "function" ? k(r) : r[k];
    if (k === "url") return { csv: v, html: `<a href="${esc(v)}" target="_blank" rel="noopener">open</a>` };
    if (k === "material") return { csv: v, html: esc(v === "Cotton" ? "Cotton jersey" : v) };
    return { csv: v == null ? "" : v, html: v == null ? `<span class="muted">not reported</span>` : esc(v) };
  }
  function renderData() {
    const t = TABS[S.dataTab];
    $("dataStrip").innerHTML = `<span><b>${(SCI().table1_records || []).length}</b> Olson Table 1 records</span><span><b>${D.runs.length}</b> Urban Table 2 runs</span><span><b>${D.investigations.length}</b> investigations</span><span><b>${D.findings.length}</b> findings</span><span><b>${D.sources.length}</b> sources</span><span>Loaded from: ${esc(D.origin)}</span>`;
    const CLS = { published_numeric: "Published number", digitized: "Digitized estimate", archive_claim: "Archive claim", synthetic: "Synthetic, not NASA" };
    $("dataCls").innerHTML = t.cls ? `<span class="ev-cls ev-${t.cls[0]}">${CLS[t.cls[0]]}</span><span class="small t2">${esc(t.cls[1])}</span>` : "";
    $("dataCls").hidden = !t.cls;
    $("dataTabs").innerHTML = Object.entries(TABS).map(([k, v]) => `<button type="button" role="tab" data-tab="${k}" aria-selected="${S.dataTab === k}">${v.label}<span class="c">${v.rows().length}</span></button>`).join("");
    const q = S.dataQ.toLowerCase();
    const rows = t.rows().filter(r => !q || JSON.stringify(r).toLowerCase().includes(q));
    $("dataTable").className = "t" + (["runs", "spread_rates", "investigations", "table1", "figure10", "synthetic", "conflicts"].includes(S.dataTab) && S.dataTab !== "conflicts" ? " nowrap" : "");
    $("dataTable").innerHTML = `<thead><tr>${t.cols.map(c => `<th>${c[1]}</th>`).join("")}</tr></thead><tbody>${rows.length ? rows.map(r => `<tr>${t.cols.map(c => `<td class="${typeof r[c[0]] === "number" ? "n" : ""}">${cellVal(r, c).html}</td>`).join("")}</tr>`).join("") : `<tr><td colspan="${t.cols.length}" class="muted">${t.rows().length ? "No rows match the filter." : "No rows yet. The data team adds them to data/" + S.dataTab + ".json."}</td></tr>`}</tbody>`;
    $("schema").innerHTML = `<dl class="prop">${t.cols.map(c => `<dt>${c[1]}</dt><dd class="small t2">${c[2]}</dd>`).join("")}</dl><p class="tiny muted">Full field list and units: DATA_CONTRACT.md in the project.</p>`;
    const methods = {}; [...D.runs, ...D.spread_rates].forEach(r => { const m = r.provenance.method; methods[m] = (methods[m] || 0) + 1; });
    const once = [...D.runs, ...D.spread_rates].filter(r => r.provenance.checks < 2).length;
    $("dataHealth").innerHTML = `
      <div class="hlt"><span>Read methods</span><b>${Object.entries(methods).map(([m, n]) => `<span class="meth ${m}">${m}</span> <span class="num">${n}</span>`).join(" ")}</b></div>
      <div class="hlt ${once ? "warn" : "ok"}"><span>Values checked only once</span><b class="num">${once}</b></div>
      <div class="hlt"><span>Open data checks</span><b class="num">${D.flags.length}</b></div>
      <div class="hlt ${D.warnings.length ? "warn" : "ok"}"><span>Validation</span><b>${D.warnings.length ? `${D.warnings.length} warning${D.warnings.length > 1 ? "s" : ""}` : "All rows pass"}</b>${D.warnings.length ? `<ul class="clean tiny">${D.warnings.slice(0, 6).map(w => `<li>${esc(w)}</li>`).join("")}</ul>` : `<i class="tiny">required-field and link checks</i>`}</div>`;
  }
  function buildCSV() {
    const t = TABS[S.dataTab], rows = t.rows();
    const q = v => { const s = String(v == null ? "" : v); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
    const csv = [t.cols.map(c => q(c[1])).join(",")].concat(rows.map(r => t.cols.map(c => q(cellVal(r, c).csv)).join(","))).join("\n");
    return csv;
  }
  function copyCSV() {
    const csv = buildCSV(), btn = $("csvCopy"), done = ok => { btn.textContent = ok ? "Copied" : "Copy failed"; setTimeout(() => btn.textContent = "Copy CSV", 1600); };
    const fallback = () => { const ta = document.createElement("textarea"); ta.value = csv; ta.style.cssText = "position:fixed;opacity:0"; document.body.appendChild(ta); ta.select(); let ok = false; try { ok = document.execCommand("copy"); } catch (e) {} ta.remove(); done(ok); };
    try { navigator.clipboard.writeText(csv).then(() => done(true), fallback); } catch (e) { fallback(); }
  }
  function downloadCSV() {
    const csv = buildCSV();
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob(["\ufeff" + csv], { type: "text/csv" })); a.download = `1gnition-${S.dataTab}.csv`; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  /* ---------------- provenance popover ---------------- */
  function showPop(el) {
    const pop = $("pop"); let html;
    if (el.dataset.term) { const g = GLOSS[el.dataset.term]; html = `<span class="small muted">Term</span><b>${esc(g[0])}</b><span class="small t2">${esc(g[1])}</span>`; }
    else if (el.dataset.pvs) { const s = D.source(el.dataset.pvs); html = `<span class="small muted">Source</span><b>${esc(s.title)}</b>${s.note ? `<span class="small t2">${esc(s.note)}</span>` : ""}<a class="small" href="${esc(s.url)}" target="_blank" rel="noopener">Open source</a>`; }
    else {
      const [col, id, field] = el.dataset.pv.split("|"), row = (D[col] || []).find(r => r.id === id); if (!row) return;
      const p = row.provenance || {}, s = D.source(p.source_id) || {};
      const fl = D.flags.filter(f => (f.applies_to || []).includes(id));
      html = `<span class="small muted">${esc(id)} · ${esc(field.replace(/_/g, " "))}</span><span class="pv-val">${esc(row[field])}</span>
        <dl><dt>Source</dt><dd>${esc(s.title || p.source_id)}</dd><dt>Location</dt><dd>${esc(p.location)}</dd><dt>Read as</dt><dd>${esc(p.method)}</dd><dt>Checked</dt><dd>${p.checks} time${p.checks === 1 ? "" : "s"}</dd></dl>
        ${fl.length ? `<span class="small" style="color:var(--accent2)">Open check: ${fl.map(f => esc(f.title)).join(", ")}</span>` : ""}
        ${s.url ? `<a class="small" href="${esc(s.url)}" target="_blank" rel="noopener">Open source</a>` : ""}`;
    }
    pop.innerHTML = html; pop.classList.remove("hide");
    const r = el.getBoundingClientRect(), pw = pop.offsetWidth, ph = pop.offsetHeight;
    let x = Math.min(innerWidth - pw - 12, Math.max(12, r.left + r.width / 2 - pw / 2)), y = r.bottom + 8;
    if (y + ph > innerHeight - 12) y = r.top - ph - 8;
    pop.style.left = x + "px"; pop.style.top = y + "px";
  }
  function hidePop() { $("pop").classList.add("hide"); }

  /* ---------------- ask ---------------- */
  const SUGGEST = ["What do we know at 30% oxygen and 70 kPa?", "Is there lunar gravity data?", "Which runs can be fairly compared?", "What spread rates are indexed?"];
  function openAsk(q) {
    $("drawer").classList.add("open"); $("drawer").setAttribute("aria-hidden", "false");
    $("askMode").textContent = C.AI_ENDPOINT ? "Answers come from the backend configured in js/config.js and must cite indexed records." : ((D.brand_copy || {}).assistant_disclosure || "Ask 1gnition is an offline rule-based evidence helper, not a generative AI assistant.") + " Answers are written by fixed rules from the indexed records.";
    $("askSuggest").innerHTML = SUGGEST.map(s => `<button class="chip" type="button" data-q="${esc(s)}">${esc(s)}</button>`).join("");
    if (q) ask(q); else setTimeout(() => $("askIn").focus(), 50);
  }
  function closeAsk() { $("drawer").classList.remove("open"); $("drawer").setAttribute("aria-hidden", "true"); }
  async function ask(q) {
    const log = $("askLog");
    log.insertAdjacentHTML("beforeend", `<div class="msg q">${esc(q)}</div>`);
    let ans;
    if (C.AI_ENDPOINT) {
      try {
        const r = await fetch(C.AI_ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: q, scenario: { material: S.mat, outcome: S.out, o2_pct: L.num(S.o2), pressure_kpa: L.num(S.p), gravity: S.g, airflow_cm_s: L.num(S.air) }, context: { runs: D.runs, spread_rates: D.spread_rates, findings: D.findings } }) });
        const j = await r.json(); ans = { text: j.answer, state: j.state || "insuf", cites: (j.citations || []).map(c => `${(D.source(c.source_id) || {}).title || c.source_id}, ${c.location || ""}`) };
      } catch (e) { ans = offline(q); ans.text = "The AI backend did not respond, so this is the offline answer. " + ans.text; }
    } else ans = offline(q);
    log.insertAdjacentHTML("beforeend", `<div class="msg a fade-in"><div class="row">${st(ans.state)}${C.AI_ENDPOINT ? "" : plain("offline")}</div><p>${esc(ans.text)}</p>${ans.cites.length ? `<span class="cite">Cites: ${ans.cites.map(esc).join("; ")}</span>` : ""}</div>`);
    log.scrollTop = log.scrollHeight;
  }
  function offline(q) {
    const s = q.toLowerCase(), cites = new Set(), T2 = "Saffire I–V paper, Table 2";
    const pct = s.match(/(\d+(?:\.\d+)?)\s*%/), kpa = s.match(/(\d+(?:\.\d+)?)\s*kpa/);
    const runId = D.runs.find(r => new RegExp("\\b" + r.id.toLowerCase().replace("-", "\\-") + "\\b").test(s));
    if (/lunar|moon|gravity|mars/.test(s) && !pct) {
      const g = [...new Set(D.runs.map(r => r.gravity))];
      return { state: "insuf", text: `No. Every indexed run is ${g.map(x => L.GRAV[x]).join(" and ")}. The challenge brief says PSI held no partial-gravity combustion data when it was written. Lunar behavior can fall outside the range between microgravity and Earth results, so 1gnition gives no number for lunar gravity. FM2 plans flame-spread tests on the Moon.`, cites: ["Challenge brief", T2] };
    }
    if (/spread/.test(s)) {
      const X = D.scientific_comparisons;
      if (X) return { state: "pub", text: `Olson et al. (2023) Table 1 gives ${X.table1_records.length} published spread rates, from ${Math.min(...X.table1_records.map(r => r.spread_cm_s))} to ${Math.max(...X.table1_records.map(r => r.spread_cm_s))} cm/s. 1gnition compares three pairs: ${X.comparison_cases.map(c => `${c.baseline} to ${c.comparison}, ${c.measurements.spread_cm_s.join(" to ")} cm/s`).join("; ")}. Each is descriptive only, because other conditions changed too. No model prediction is validated, so 1gnition gives no predicted rate.`, cites: [D.source("OLSON-2023-T1") ? D.source("OLSON-2023-T1").title : "Olson et al. (2023)"] };
      return { state: "insuf", text: "No spread rates are indexed yet.", cites: [] };
    }
    if (/compar|fair|pair/.test(s)) {
      const pairs = []; D.runs.forEach((a, i) => D.runs.slice(i + 1).forEach(b => { const d = L.diffCausal(a, b); if (d.length === 1) pairs.push(`${a.id} and ${b.id} (${d[0].label.toLowerCase()} only${a.flight !== b.flight ? ", different flights" : ""})`); }));
      return { state: "expl", text: `Pairs that change one listed condition: ${pairs.join("; ")}. Each is one run per configuration with no stated uncertainty, so treat them as exploratory.`, cites: [T2] };
    }
    if (runId && !pct) { const r = runId; return { state: "pub", text: `${r.id} (${r.flight}) burned ${L.matName(r.material)} at ${r.o2_pct}% oxygen, ${r.pressure_kpa} kPa and ${r.airflow_cm_s} cm/s in a ${r.duct_height_cm} cm duct, sample ${r.sample_width_cm} × ${r.sample_length_cm} cm. Reported steady size ${r.steady_size_cm} cm, maximum ${r.max_size_cm} cm.`, cites: [`${D.source(r.provenance.source_id).title}, ${r.provenance.location}`] }; }
    const o2 = pct ? parseFloat(pct[1]) : L.num(S.o2), p = kpa ? parseFloat(kpa[1]) : L.num(S.p);
    if (o2 === null || p === null) return { state: "insuf", text: "Give an oxygen percentage and a pressure in kPa, or set them in the scenario panel, and 1gnition will check them against the indexed runs.", cites: [] };
    const nr = L.nearest(D.runs, o2, p), inside = L.within(nr.r, o2, p);
    return { state: inside ? "expl" : "insuf", text: inside ? `Run ${nr.r.id} sits within tolerance of ${o2}% oxygen and ${p} kPa. It reported a steady flame size of ${nr.r.steady_size_cm} cm in microgravity. This is one run with no stated uncertainty.` : `No indexed run covers ${o2}% oxygen at ${p} kPa. The nearest is ${nr.r.id} at ${nr.r.o2_pct}% and ${nr.r.pressure_kpa} kPa, ${Math.abs(nr.r.o2_pct - o2).toFixed(1)} points of oxygen away. 1gnition gives no number here and proposes a test on the Research gaps view.`, cites: [T2] };
  }

  /* ---------------- guided demo ---------------- */
  const TOUR = [
    { view: "overview", target: ".hx-copy h1", title: "The problem", text: "NASA's PSI holds 24 microgravity combustion investigations, about 12 TB. A Moon-base fire engineer can't easily tell which runs apply, which comparisons are fair, or where the data runs out." },
    { view: "overview", target: "#floatCard", title: "Real data, not a picture", text: "Every dot is a real Saffire run from NASA's published table, with its tolerance box. The Moon-base atmosphere sits outside all of them: the nearest run is 3.8 points of oxygen short." },
    { view: "overview", target: ".flames", title: "Why space fire is different", text: "Two NASA photos of the same kind of candle. On Earth, hot gas rises and stretches the flame. In microgravity nothing rises, so Earth fire tests don't carry over directly." },
    { view: "overview", target: ".burn-viz", y() { const b = $("burn"); return b.offsetTop + (b.offsetHeight - innerHeight) * .62; }, title: "A published number, drawn to scale", text: "Scrolling moves the flame front along the 94 cm Saffire-I sample at the published average of 1.8 mm/s. Over the 420 s burn that is 756 mm, or 75.6 cm. Nothing here is simulated." },
    { view: "evidence", target: "#side", setup() { applyPreset("lunar"); S.mat = "SIBAL"; S.out = "steady_size"; renderAll(); }, title: "One scenario drives every view", text: "The Moon-base preset loads the challenge's atmosphere: 30% oxygen at 70.3 kPa, lunar gravity. Every view reads this panel." },
    { view: "evidence", target: "#invList .inv", title: "Two scores, kept apart", text: "Relevance asks whether a study measured the right thing on the right material. Similarity asks whether its environment matches yours. Saffire is highly relevant but scores 0 of 3 on similarity here." },
    { view: "evidence", target: "#invList .inv", setup() { applyPreset("iss"); renderAll(); }, title: "Change the scenario, the ranking moves", text: "Switching to an ISS-like cabin (21% oxygen, 101.3 kPa, microgravity) raises similarity for the Saffire flights. The rows re-sort and arrows show what moved." },
    { view: "compare", target: "#pairCard", setup() { S.revealed = false; S.sel = ["II-5", "II-6"]; renderCompare(); }, title: "A fair comparison", text: "II-5 and II-6 differ only in airflow, 20 to 25 cm/s. Steady flame size went from 4 to 5 cm. 1gnition labels it exploratory: one run each, no stated uncertainty." },
    { view: "compare", target: "#pairCard", setup() { S.sel = ["II-5", "III-1"]; renderCompare(); }, title: "A confounded comparison", text: "II-5 and III-1 change airflow and sample size together, on different flights. 1gnition refuses to credit either one and marks insufficient evidence." },
    { view: "compare", target: "#gridCard", setup() { S.revealed = true; S.justRevealed = true; S.sel = ["I-1", "III-1"]; renderCompare(); }, title: "Search before proposing a test", text: "The open cell, a large sample at 20 cm/s, already exists as run I-1. Searching first avoids proposing an experiment NASA already flew." },
    { view: "compare", target: "#flagsCard", title: "We check NASA's own table", text: "While indexing, we found sample width and duct height disagree between Table 2 and the paper's text. 1gnition shows the conflict instead of silently picking one." },
    { view: "compare", target: "#cmpOlsonHead", setup() { S.sciCase = 0; S.sciMetric = "both"; renderCmpOlson(); }, title: "Same length, different speed", text: "Olson et al. (2023) Table 1 reports the same flights with spread rates. I-1 and II-5 both had 4 cm flames, yet spread at 0.18 and 0.21 cm/s: +0.03 cm/s, +16.67% of I-1. Length is not speed." },
    { view: "compare", target: "#cmpCond .sci-cond", setup() { S.sciCase = 2; S.sciMetric = "rate"; renderCmpOlson(); }, title: "Doubled, but not explained", text: "I-1 to IV-SIBAL doubled the rate (+100%), yet duct height, sample length, oxygen, pressure and flight all changed, and the sources disagree on some values. 1gnition calls it descriptive: the cause is not isolated." },
    { view: "transfer", target: "#predCard", setup() { S.step = "predict"; renderTransfer(); }, title: "No NASA prediction until it's validated", text: "The ML backend reports VALIDATION_NOT_SUPPORTED, so 1gnition shows no predicted rate and no accuracy score. The checks say exactly what blocks it." },
    { view: "transfer", target: "#synCard", setup() { S.step = "synthetic"; S.synCase = 0; renderTransfer(); }, title: "Testing the method on invented data", text: "Synthetic data with a programmed answer (+0.08 cm/s) checks that the analysis code recovers it (+0.076). It is clearly marked: not NASA data, not physical validation." },
    { view: "gaps", target: "#gapTypesSect .gtypes", setup() { applyPreset("lunar"); renderAll(); }, title: "Six kinds of gap, kept apart", text: "A missing configuration, unknown run identities, missing conditions, source conflicts, no replication and an out-of-range habitat each need a different fix." },
    { view: "gaps", target: "#gapFactCard", title: "The experiment nobody has flown", text: "Width by full duct height at 20 cm/s. Three cells have one confounded historical burn each. The narrow sample in the shallow duct has no matching Saffire configuration, and the hypothesis stays untested." },
    { view: "gaps", target: "#mapCard", setup() { applyPreset("lunar"); S.gMat = "all"; $("gMat").value = "all"; renderAll(); }, title: "Where the data runs out", text: "The Moon-base habitat sits outside every tolerance box in the team's indexed dataset. Drag it around: inside a box, 1gnition finds the matching run. Outside, it says so." },
    { view: "data", target: "#dataTable", setup() { S.dataTab = "table1"; S.dataQ = ""; renderData(); }, title: "Every number is traceable", text: "Each row shows its source, page, read method and how many times it was checked. Any table downloads or copies as CSV, and any underlined number on the site opens its provenance." },
    { view: "data", target: null, after() { openAsk("Is there lunar gravity data?"); }, title: "An assistant that won't make things up", text: "Asked about lunar gravity, 1gnition answers from the records and says insufficient evidence. That refusal is the point." }
  ];
  let tIdx = -1;
  function tourShow(i) {
    tIdx = i; const s = TOUR[i]; document.body.classList.add("touring");
    closeAsk(); hidePop();
    const card = $("tour"); card.hidden = false;
    go(s.view, true);
    if (s.setup) s.setup();
    document.querySelectorAll(".hl").forEach(e => e.classList.remove("hl"));
    $("tStep").textContent = `Step ${i + 1} of ${TOUR.length}`;
    $("tTitle").textContent = s.title; $("tText").textContent = s.text;
    $("tBack").disabled = i === 0; $("tNext").textContent = i === TOUR.length - 1 ? "Finish" : "Next";
    $("tBar").style.width = ((i + 1) / TOUR.length * 100) + "%";
    tourPlace(s);
    if (current === "evidence") raf2(fillMeters);
    if (current === "compare") raf2(fillBars);
    if (s.after) s.after();
  }
  /* Scroll the target into the space the card leaves free, then dock the card in the corner that covers it least. */
  function tourPlace(s) {
    const card = $("tour"), el = s.target && document.querySelector(s.target);
    card.style.cssText = "";
    const jump = y => window.scrollTo({ top: Math.max(0, y), behavior: "instant" });
    if (!el) { jump(0); return; }
    el.classList.add("hl");
    const VW = innerWidth, VH = innerHeight, m = 16, head = 60 + m, cw = card.offsetWidth, ch = card.offsetHeight;
    const r0 = el.getBoundingClientRect(), absTop = r0.top + scrollY, free = VH - head - ch - m * 2;
    if (s.y) jump(s.y());
    else jump(r0.height <= free ? absTop - head - (free - r0.height) / 2 : absTop - head);
    if (VW <= 640) return;
    const r = el.getBoundingClientRect();
    const spots = [[VW - cw - 24, VH - ch - 24], [24, VH - ch - 24], [VW - cw - 24, head], [24, head]];
    const cover = ([x, y]) => Math.max(0, Math.min(r.right, x + cw) - Math.max(r.left, x)) * Math.max(0, Math.min(r.bottom, y + ch) - Math.max(r.top, y));
    const best = spots.map(p => [cover(p), p]).sort((a, b) => a[0] - b[0])[0][1];
    card.style.left = best[0] + "px"; card.style.top = best[1] + "px"; card.style.right = "auto"; card.style.bottom = "auto";
  }
  function tourEnd() { document.body.classList.remove("touring"); tIdx = -1; $("tour").hidden = true; $("tour").style.cssText = ""; document.querySelectorAll(".hl").forEach(e => e.classList.remove("hl")); }

  /* ---------------- events ---------------- */
  function bind() {
    [["fMat", "mat"], ["fOut", "out"], ["fG", "g"], ["fO2", "o2"], ["fP", "p"], ["fAir", "air"], ["fDir", "dir"]].forEach(([id, k]) => $(id).addEventListener("change", e => {
      S[k] = e.target.value.trim();
      if (["g", "o2", "p", "air"].includes(k)) { S.hab = "custom"; S.note = L.PRESET.custom.note; }
      renderAll();
    }));
    /* Typing in a scenario field and then clicking a tab: the field's change event (fired on blur, between
       mousedown and click) re-renders the tab row, so the click would land on a removed button. Record the
       tab choice on pointerdown, which fires before blur; the re-render then already shows it. */
    document.addEventListener("pointerdown", e => {
      if (e.button !== 0) return;
      const t = e.target.closest("#v-transfer [data-step],#v-transfer [data-case],#v-compare [data-case],[data-metric],[data-syn]");
      if (!t || !document.activeElement || !document.activeElement.matches("#side input, #side select")) return;
      if (t.dataset.step) S.step = t.dataset.step;
      if (t.dataset.case !== undefined) S.sciCase = +t.dataset.case;
      if (t.dataset.metric) S.sciMetric = t.dataset.metric;
      if (t.dataset.syn !== undefined) S.synCase = +t.dataset.syn;
    });
    $("gMat").addEventListener("change", e => { S.gMat = e.target.value; renderGaps(); });
    $("pA").addEventListener("change", e => { S.sel = [e.target.value, S.sel[1]]; if (S.sel.includes("I-1")) S.revealed = true; renderCompare(); });
    $("pB").addEventListener("change", e => { S.sel = [S.sel[0], e.target.value]; if (S.sel.includes("I-1")) S.revealed = true; renderCompare(); });
    $("swapBtn").addEventListener("click", () => { S.sel = [S.sel[1], S.sel[0]]; renderCompare(); });
    $("dataSearch").addEventListener("input", e => { S.dataQ = e.target.value; renderData(); });
    $("csvBtn").addEventListener("click", downloadCSV);
    $("csvCopy").addEventListener("click", copyCSV);
    $("askBtn").addEventListener("click", () => openAsk());
    $("askClose").addEventListener("click", closeAsk);
    $("askForm").addEventListener("submit", e => { e.preventDefault(); const q = $("askIn").value.trim(); if (q) { ask(q); $("askIn").value = ""; } });
    $("menuBtn").addEventListener("click", () => { const o = document.querySelector(".top").classList.toggle("menu-open"); $("menuBtn").setAttribute("aria-expanded", o); });
    document.querySelectorAll(".nav a").forEach(a => a.addEventListener("click", () => document.querySelector(".top").classList.remove("menu-open")));
    if (matchMedia("(max-width:980px)").matches) { $("side").classList.add("collapsed"); $("sideToggle").textContent = "Edit"; $("sideToggle").setAttribute("aria-expanded", "false"); }
    $("sideToggle").addEventListener("click", () => { const c = $("side").classList.toggle("collapsed"); $("sideToggle").textContent = c ? "Edit" : "Hide"; $("sideToggle").setAttribute("aria-expanded", !c); });
    $("tNext").addEventListener("click", () => tIdx < TOUR.length - 1 ? tourShow(tIdx + 1) : (tourEnd(), closeAsk()));
    $("tBack").addEventListener("click", () => tIdx > 0 && tourShow(tIdx - 1));
    $("tExit").addEventListener("click", () => { tourEnd(); closeAsk(); });

    document.addEventListener("click", e => {
      const t = e.target.closest("[data-preset],[data-inc],[data-inv],[data-run],[data-pair],[data-reveal],[data-step],[data-case],[data-metric],[data-syn],[data-gotab],[data-step-go],[data-tab],[data-tour-start],[data-q],[data-ask],.pv,.term");
      if (!t) { if (!e.target.closest("#pop")) hidePop(); return; }
      if (t.classList.contains("pv") || t.classList.contains("term")) { e.preventDefault(); showPop(t); return; }
      hidePop();
      if (t.dataset.tourStart !== undefined) { tourShow(0); return; }
      if (t.dataset.preset) { applyPreset(t.dataset.preset); renderAll(); return; }
      if (t.dataset.inc) { const inc = L.INCIDENT[t.dataset.inc], s = inc.set;
        if (s.hab && s.hab !== "custom") applyPreset(s.hab); else if (s.hab) S.hab = "custom";
        ["o2", "p", "g", "out", "mat"].forEach(k => { if (k in s) S[k] = s[k]; });
        S.note = inc.note; renderAll(); go("evidence"); return; }
      if (t.dataset.inv) { if (t.closest(".inv-more")) S.moreOpen = true; S.openInv = S.openInv === t.dataset.inv ? null : t.dataset.inv; const el = t.closest(".inv"); el.classList.toggle("open"); t.setAttribute("aria-expanded", el.classList.contains("open")); return; }
      if (t.dataset.reveal) { S.revealed = true; S.justRevealed = true; S.sel = ["I-1", "III-1"]; renderCompare(); return; }
      if (t.dataset.run) { const id = t.dataset.run; if (id === S.sel[0]) S.sel = [S.sel[1], S.sel[0]]; else if (id !== S.sel[1]) S.sel = [S.sel[0], id]; renderCompare(); return; }
      if (t.dataset.pair) { const ids = t.dataset.pair.split(","); if (ids.includes("I-1") && !S.revealed) { S.revealed = true; S.justRevealed = true; } S.sel = ids; renderCompare(); go("compare"); return; }
      if (t.dataset.step) { S.step = t.dataset.step; renderTransfer(); return; }
      if (t.dataset.case !== undefined && t.closest("#v-transfer, #v-compare")) { S.sciCase = +t.dataset.case; renderTransfer(); renderCmpOlson(); return; }
      if (t.dataset.metric) { S.sciMetric = t.dataset.metric; renderTransfer(); renderCmpOlson(); return; }
      if (t.dataset.stepGo) { e.preventDefault(); S.step = t.dataset.stepGo; renderTransfer(); go("transfer"); return; }
      if (t.dataset.syn !== undefined) { S.synCase = +t.dataset.syn; renderTransfer(); return; }
      if (t.dataset.gotab) { e.preventDefault(); S.dataTab = t.dataset.gotab; S.dataQ = ""; $("dataSearch").value = ""; renderData(); go("data"); return; }
      if (t.dataset.tab) { S.dataTab = t.dataset.tab; S.dataQ = ""; $("dataSearch").value = ""; renderData(); return; }
      if (t.dataset.q) { ask(t.dataset.q); return; }
      if (t.dataset.ask) { openAsk(t.dataset.ask); return; }
    });
    document.addEventListener("keydown", e => {
      if (e.key === "Escape") { hidePop(); closeAsk(); }
      if ((e.key === "Enter" || e.key === " ") && e.target.classList && (e.target.classList.contains("pv") || e.target.classList.contains("term"))) { e.preventDefault(); showPop(e.target); }
      if ((e.key === "Enter" || e.key === " ") && e.target.matches && e.target.matches("tr[data-case]")) { e.preventDefault(); e.target.click(); }
      if (tIdx >= 0 && !e.target.closest("input,select,textarea,#map")) { if (e.key === "ArrowRight") $("tNext").click(); if (e.key === "ArrowLeft") $("tBack").click(); }
    });
    window.addEventListener("scroll", hidePop, { passive: true });
    const map = $("map");
    map.addEventListener("pointerdown", e => { if (!e.target.closest("svg")) return; dragging = true; map.setPointerCapture(e.pointerId); setHab(...mapCoords(e)); e.preventDefault(); });
    map.addEventListener("pointermove", e => { if (dragging) setHab(...mapCoords(e)); });
    const end = () => { if (dragging) { dragging = false; renderAll(); } };
    map.addEventListener("pointerup", end); map.addEventListener("pointercancel", end);
    map.addEventListener("keydown", e => { const d = { ArrowLeft: [-.5, 0], ArrowRight: [.5, 0], ArrowUp: [0, 1], ArrowDown: [0, -1] }[e.key]; if (!d) return; e.preventDefault(); setHab((L.num(S.o2) ?? 30) + d[0], (L.num(S.p) ?? 70.3) + d[1], true); });
    window.addEventListener("hashchange", () => { route(); if (tIdx < 0) window.scrollTo(0, 0); });
  }

  /* ---------------- start ---------------- */
  window.IGNIS_LOAD().then(data => {
    D = data;
    bind(); renderOverview(); renderAll(); renderData();
    if (window.IGNIS_STORY) IGNIS_STORY.init({ D, S, L, pv, pvs, esc, applyPreset, renderAll, go });
    route();
  }).catch(err => {
    document.body.insertAdjacentHTML("beforeend", `<div class="toast">Data failed to load: ${esc(err.message)}. Check js/config.js and the data files.</div>`);
  });
})();
