/* 1gnition overview story: scroll-driven sections built from the loaded data.
   Motion here either replays a published number or is labeled as illustration. */
(function () {
  const REDUCE = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = id => document.getElementById(id);
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  let A; // api from app.js

  /* ---------- reveal on scroll ---------- */
  function revealAll() {
    const els = [...document.querySelectorAll("#v-overview [data-rv], #v-overview [data-count], #pipe, #rgrid, .scene")].filter(el => !(el.dataset.count && el.closest("#rgrid")));
    if (REDUCE || !("IntersectionObserver" in window)) { els.forEach(el => { el.classList.add("in"); if (el.dataset.count) countUp(el, true); }); fireReveal(true); return; }
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (!e.isIntersecting) return;
      const el = e.target; el.classList.add("in"); io.unobserve(el);
      if (el.dataset.count) countUp(el);
      if (el.id === "rgrid") fireReveal();
      if (el.id === "codeTile") typeCode();
    }), { threshold: .25, rootMargin: "0px 0px -8% 0px" });
    els.forEach(el => io.observe(el));
    const ct = $("codeTile"); if (ct) io.observe(ct);
  }
  function countUp(el, now) {
    const to = parseFloat(el.dataset.count), dec = (el.dataset.count.split(".")[1] || "").length;
    if (now || REDUCE) { el.textContent = to.toFixed(dec); return; }
    const t0 = performance.now(), dur = 1100 + Math.min(900, to * 8);
    const step = t => { const k = clamp((t - t0) / dur, 0, 1), e = 1 - Math.pow(1 - k, 3);
      el.textContent = (to * e).toFixed(dec); if (k < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  }

  /* ---------- hero: stars, tilt ---------- */
  function stars() {
    const c = $("stars"); if (!c) return;
    const ctx = c.getContext("2d"); let W, H, pts = [], on = true, mx = 0, my = 0;
    const size = () => { const r = c.getBoundingClientRect(), d = Math.min(2, devicePixelRatio || 1);
      W = r.width; H = r.height; c.width = W * d; c.height = H * d; ctx.setTransform(d, 0, 0, d, 0, 0);
      pts = Array.from({ length: Math.round(W * H / 5200) }, () => ({ x: Math.random() * W, y: Math.random() * H * .78, r: Math.random() * 1.1 + .25, z: Math.random(), p: Math.random() * 6.28, w: .4 + Math.random() * 1.6, warm: Math.random() < .12 })); };
    const draw = t => {
      ctx.clearRect(0, 0, W, H);
      for (const s of pts) {
        const a = REDUCE ? .7 : .35 + .55 * (.5 + .5 * Math.sin(t / 1000 * s.w + s.p));
        ctx.globalAlpha = a * (.35 + s.z * .65);
        ctx.fillStyle = s.warm ? "#ffcf7a" : "#dbe6ff";
        ctx.beginPath(); ctx.arc(s.x + mx * s.z * 10, s.y + my * s.z * 6, s.r, 0, 6.283); ctx.fill();
      }
      ctx.globalAlpha = 1;
      if (on && !REDUCE) requestAnimationFrame(draw);
    };
    size(); addEventListener("resize", size);
    if (!REDUCE) {
      $("hero").addEventListener("pointermove", e => { const r = c.getBoundingClientRect(); mx = (e.clientX - r.left) / r.width - .5; my = (e.clientY - r.top) / r.height - .5; });
      new IntersectionObserver(es => { const v = es[0].isIntersecting; if (v && !on) { on = true; requestAnimationFrame(draw); } on = v; }).observe(c);
    }
    requestAnimationFrame(draw);
  }

  /* ---------- flames ---------- */
  function credits() {
    document.querySelectorAll("[data-credit]").forEach(el => { el.innerHTML = IGNIS_ART.credit(el.dataset.credit); });
    $("photoCredits").innerHTML = Object.keys(IGNIS_ART.PHOTOS).map(k => `<li>${IGNIS_ART.credit(k)}</li>`).join("");
    $("scrollCue").addEventListener("click", () => $("flames").scrollIntoView({ behavior: REDUCE ? "auto" : "smooth", block: "start" }));
  }

  /* ---------- sticky burn ---------- */
  let burn = null;
  function buildBurn() {
    const D = A.D, sr = D.spread_rates.find(r => r.run_id === "I-1") || D.spread_rates[0];
    const run = sr && D.run(sr.run_id);
    if (!sr || !run) { $("burn").classList.add("hide"); return; }
    const pv = A.pv;
    $("bsLen").innerHTML = pv("runs", run.id, "sample_length_cm", run.sample_length_cm + " cm");
    $("bsWid").innerHTML = pv("runs", run.id, "sample_width_cm", run.sample_width_cm + " cm");
    $("bsAir").innerHTML = pv("runs", run.id, "airflow_cm_s", run.airflow_cm_s + " cm/s");
    $("bsSize").innerHTML = pv("runs", run.id, "steady_size_cm", run.steady_size_cm + " cm");
    $("bsRate").innerHTML = pv("spread_rates", sr.id, "rate_mm_s", sr.rate_mm_s + " mm/s");
    $("bsDur").innerHTML = pv("spread_rates", sr.id, "duration_s", sr.duration_s + " s");
    const distCm = sr.rate_mm_s * sr.duration_s / 10;
    $("bsDist").textContent = `${sr.rate_mm_s} × ${sr.duration_s} = ${(sr.rate_mm_s * sr.duration_s).toFixed(0)} mm, or ${distCm.toFixed(1)} cm`;

    const L = run.sample_length_cm, Wd = run.sample_width_cm, s = 8.4, x0 = 70, y0 = 96, w = L * s, h = Wd * s, fl = (run.steady_size_cm || 4) * s;
    const arrows = y => `<line x1="20" y1="${y}" x2="${x0 + w + 70}" y2="${y}" class="air"/>`;
    $("burnSvg").innerHTML = `<svg viewBox="0 0 ${x0 + w + 110} ${y0 + h + 110}" role="img" aria-label="To-scale drawing of the ${L} by ${Wd} cm Saffire-I sample with the flame front at the scrolled time">
      <defs>
        <pattern id="weave" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="#2a2620"/><path d="M0 4H8M4 0V8" stroke="#3e372c" stroke-width="1"/></pattern>
        <pattern id="char" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="#0b0b0c"/><circle cx="3" cy="3" r=".9" fill="#2a2f38"/><circle cx="8" cy="7" r=".6" fill="#3a3f48"/></pattern>
        <linearGradient id="flameG" x1="0" x2="1"><stop offset="0" stop-color="#fff4d6"/><stop offset=".25" stop-color="#ffcf7a"/><stop offset=".6" stop-color="#f5a524" stop-opacity=".85"/><stop offset="1" stop-color="#e2561b" stop-opacity="0"/></linearGradient>
        <linearGradient id="emberG" x1="0" x2="1"><stop offset="0" stop-color="#e2561b" stop-opacity="0"/><stop offset="1" stop-color="#ff7a2a" stop-opacity=".9"/></linearGradient>
        <filter id="wob" x="-20%" y="-10%" width="140%" height="120%"><feTurbulence type="fractalNoise" baseFrequency=".03 .09" numOctaves="2" seed="3"><animate attributeName="seed" values="1;9;3;7;1" dur="2.4s" repeatCount="indefinite"/></feTurbulence><feDisplacementMap in="SourceGraphic" scale="14"/><feGaussianBlur stdDeviation="1.4"/></filter>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="10"/></filter>
        <clipPath id="sclip"><rect x="${x0}" y="${y0}" width="${w}" height="${h}"/></clipPath>
      </defs>
      <rect x="${x0 - 40}" y="${y0 - 40}" width="${w + 80}" height="${h + 80}" rx="6" class="duct"/>
      <g class="airflow">${arrows(y0 - 20)}${arrows(y0 + h + 20)}</g>
      <text x="${x0 - 30}" y="${y0 - 52}" class="lbl">Airflow ${run.airflow_cm_s} cm/s →</text>
      <rect x="${x0}" y="${y0}" width="${w}" height="${h}" fill="url(#weave)"/>
      <g clip-path="url(#sclip)">
        <rect id="bChar" x="${x0}" y="${y0}" width="0" height="${h}" fill="url(#char)"/>
        <rect id="bEmber" x="${x0}" y="${y0}" width="${3 * s}" height="${h}" fill="url(#emberG)"/>
        <g id="bFlame"><rect x="0" y="${y0 - 6}" width="${fl * 1.6}" height="${h + 12}" fill="#f5a524" opacity=".35" filter="url(#glow)"/>
          <rect x="0" y="${y0 + 4}" width="${fl}" height="${h - 8}" fill="url(#flameG)" filter="url(#wob)"/></g>
      </g>
      <rect x="${x0}" y="${y0}" width="${w}" height="${h}" fill="none" stroke="#4a5160"/>
      <g class="dim">
        <line x1="${x0}" y1="${y0 + h + 62}" x2="${x0 + w}" y2="${y0 + h + 62}"/><line x1="${x0}" y1="${y0 + h + 54}" x2="${x0}" y2="${y0 + h + 70}"/><line x1="${x0 + w}" y1="${y0 + h + 54}" x2="${x0 + w}" y2="${y0 + h + 70}"/>
        <text x="${x0 + w / 2}" y="${y0 + h + 88}" text-anchor="middle">${L} cm sample length</text>
        <line x1="${x0 + w + 62}" y1="${y0}" x2="${x0 + w + 62}" y2="${y0 + h}"/><line x1="${x0 + w + 54}" y1="${y0}" x2="${x0 + w + 70}" y2="${y0}"/><line x1="${x0 + w + 54}" y1="${y0 + h}" x2="${x0 + w + 70}" y2="${y0 + h}"/>
        <text x="${x0 + w + 84}" y="${y0 + h / 2}" text-anchor="middle" transform="rotate(90 ${x0 + w + 84} ${y0 + h / 2})">${Wd} cm wide</text>
        <line id="bEnd" x1="${x0 + distCm * s}" y1="${y0 - 8}" x2="${x0 + distCm * s}" y2="${y0 + h + 8}" stroke-dasharray="4 4" class="endline"/>
        <text x="${x0 + distCm * s}" y="${y0 + h + 30}" text-anchor="middle" class="endtxt">burn ends, ${distCm.toFixed(1)} cm</text>
      </g>
    </svg>`;
    burn = { sr, run, s, x0, distCm, L, el: $("burn"), steps: [...document.querySelectorAll(".burn-step")], last: -1 };
    addEventListener("scroll", onBurn, { passive: true }); addEventListener("resize", onBurn); onBurn();
  }
  function onBurn() {
    if (!burn || !$("v-overview").classList.contains("on")) return;
    const r = burn.el.getBoundingClientRect(), span = r.height - innerHeight;
    const p = clamp(-r.top / Math.max(1, span), 0, 1);
    const k = clamp((p - .06) / .84, 0, 1), t = k * burn.sr.duration_s, x = burn.sr.rate_mm_s * t / 10;
    const px = burn.x0 + x * burn.s;
    $("bChar").setAttribute("width", Math.max(0, x * burn.s));
    $("bEmber").setAttribute("x", px - 3 * burn.s);
    $("bEmber").style.opacity = k > 0 && k < 1 ? 1 : k >= 1 ? .25 : 0;
    $("bFlame").setAttribute("transform", `translate(${px},0)`);
    $("bFlame").style.opacity = k > 0 && k < 1 ? 1 : 0;
    $("brT").textContent = Math.round(t) + " s";
    $("brX").textContent = x.toFixed(1) + " cm";
    $("brP").textContent = Math.round(x / burn.L * 100) + "%";
    $("brBar").style.transform = `scaleX(${k})`;
    burn.el.classList.toggle("done", k >= 1);
    const si = p < .3 ? 0 : p < .6 ? 1 : 2;
    if (si !== burn.last) { burn.steps.forEach((s, i) => s.classList.toggle("on", i === si)); burn.last = si; }
  }

  /* ---------- hero tilt ---------- */
  function heroTilt() {
    const card = $("floatCard"), hero = $("hero");
    if (REDUCE) { card.style.setProperty("--tilt", "0deg"); return; }
    const ph = $("heroPhoto");
    const f = () => { if (scrollY > hero.offsetHeight) return; const p = clamp(scrollY / (hero.offsetHeight * .55), 0, 1); card.style.setProperty("--tilt", (14 * (1 - p)).toFixed(2) + "deg"); card.style.setProperty("--lift", (p * -24).toFixed(1) + "px"); ph.style.setProperty("--py", (scrollY * .18).toFixed(1) + "px"); };
    addEventListener("scroll", f, { passive: true }); f();
  }

  /* ---------- I-1 reveal ---------- */
  let revealed = false;
  function buildReveal() {
    const D = A.D, pv = A.pv;
    const g = D.runs.filter(r => r.material === "SIBAL" && r.o2_pct === 21 && r.pressure_kpa === 100);
    const widths = [...new Set(g.map(r => r.sample_width_cm))].sort((a, b) => a - b), flows = [...new Set(g.map(r => r.airflow_cm_s))].sort((a, b) => a - b);
    const hid = g.find(r => r.id === "I-1");
    const cell = (wv, a) => { const r = g.find(x => x.sample_width_cm === wv && x.airflow_cm_s === a);
      if (!r) return `<div class="rc none"><span class="rc-id">Not flown</span></div>`;
      const isH = hid && r.id === hid.id;
      return `<div class="rc ${isH ? "hidden-cell" : ""}" data-id="${r.id}"><div class="rc-flip">
        ${isH ? `<div class="rc-face rc-q"><b>?</b><span class="rc-scan">Looks untested</span></div>` : ""}
        <div class="rc-face rc-v"><span class="rc-id">${r.id} · ${A.esc(r.flight)}</span><span class="rc-big">${pv("runs", r.id, "steady_size_cm", `<span data-count="${r.steady_size_cm}">0</span><small>cm</small>`)}</span><span class="rc-sub">steady size · peak ${pv("runs", r.id, "max_size_cm", r.max_size_cm + " cm")}</span><span class="rc-bar"><i style="--w:${r.max_size_cm / 15}"></i><i class="st" style="--w:${r.steady_size_cm / 15}"></i></span></div>
      </div></div>`; };
    $("rgrid").innerHTML = `<span></span>${flows.map(a => `<span class="rh">${a} cm/s airflow</span>`).join("")}
      ${widths.map(wv => `<span class="rh row">${wv < 10 ? "Small" : "Large"} sample<small>${wv} cm wide</small></span>${flows.map(a => cell(wv, a)).join("")}`).join("")}`;
    const at = (wv, a) => g.find(x => x.sample_width_cm === wv && x.airflow_cm_s === a) || {};
    const sm = widths[0], lg = widths[widths.length - 1];
    $("revealOut").innerHTML = `<div class="ro-card"><span class="state s-expl">Exploratory comparison</span>
      <p><b>Run ${hid ? hid.id : "I-1"} was already in NASA's table.</b> At each airflow, the steady flame size matched across sample widths (${flows.map(a => at(sm, a).steady_size_cm + " and " + at(lg, a).steady_size_cm + " cm at " + a + " cm/s").join("; ")}). The peak was larger on the wide samples (${flows.map(a => at(lg, a).max_size_cm).join(" and ")} cm against ${flows.map(a => at(sm, a).max_size_cm).join(" and ")} cm).</p>
      <p class="small muted">One run per cell, from different flights, with no stated uncertainty. That makes it exploratory, not proof.</p>
      <div class="row"><button class="btn btn-ghost btn-sm" type="button" data-pair="I-1,III-1">Open in Compare runs →</button><button class="btn btn-quiet btn-sm" type="button" id="replayReveal">Replay</button></div></div>`;
    $("replayReveal").addEventListener("click", () => { revealed = false; $("rgrid").classList.remove("found", "searching"); fireReveal(); });
  }
  function fireReveal(now) {
    if (revealed) return; revealed = true;
    const grid = $("rgrid"), cells = [...grid.querySelectorAll(".rc:not(.hidden-cell)")], hidden = grid.querySelector(".hidden-cell");
    cells.forEach((c, i) => setTimeout(() => { c.classList.add("in"); c.querySelectorAll("[data-count]").forEach(e => countUp(e, now)); }, now ? 0 : 200 + i * 260));
    if (!hidden) return;
    if (now) { grid.classList.add("found"); hidden.classList.add("in"); hidden.querySelectorAll("[data-count]").forEach(e => countUp(e, true)); $("revealOut").classList.add("in"); return; }
    const scan = hidden.querySelector(".rc-scan"), ids = A.D.runs.map(r => r.id);
    setTimeout(() => { grid.classList.add("searching"); let i = 0;
      const tick = setInterval(() => { scan.textContent = `Searching the index… ${ids[i % ids.length]}`; i++;
        if (i > ids.length + 2) { clearInterval(tick); scan.textContent = "Match found"; grid.classList.remove("searching"); grid.classList.add("found"); hidden.classList.add("in");
          hidden.querySelectorAll("[data-count]").forEach(e => countUp(e)); setTimeout(() => $("revealOut").classList.add("in"), 700); } }, 230);
    }, 200 + cells.length * 260 + 500);
  }

  /* ---------- data bento ---------- */
  let typed = false;
  function buildBento() {
    const D = A.D, pvs = A.pvs, coll = D.meta.collection || {}, total = coll.investigations_total || 24;
    const srcN = D.sources.length, invN = D.investigations.length;
    const used = new Set([...D.runs, ...D.spread_rates].map(r => r.provenance.source_id)).size;
    const methods = {}; D.runs.forEach(r => { const m = r.provenance.method; methods[m] = (methods[m] || 0) + 1; });
    $("bento").innerHTML = `
      <div class="tile t-code" id="codeTile" data-rv><div class="tile-h"><b>One real record</b><span class="tiny muted">runs.json · ${A.esc(D.run("I-1") ? "I-1" : D.runs[0].id)}</span></div><pre class="code" id="codePre" aria-label="JSON record"></pre>
        <p class="small t2">Every measured value carries its source, the page or table it came from, how it was read, and how many times the team checked it. Unknown values stay <code>null</code>, never guessed.</p></div>
      <div class="tile t-num" data-rv><span class="big"><span data-count="${D.runs.length}">0</span></span><p>measured runs indexed, each linked to a page or table</p><a class="tiny" href="#data">See every row →</a></div>
      <div class="tile t-num" data-rv><span class="big"><span data-count="${srcN}">0</span></span><p>NASA sources listed, ${used} of them supplying measured values</p><a class="tiny" href="#data">Open the sources →</a></div>
      <div class="tile t-dots" data-rv><div class="tile-h"><b><span data-count="${invN}">0</span> of ${pvs("brief", total)} investigations summarized</b><span class="tiny muted">PSI Combustion Science</span></div>
        <div class="dots">${Array.from({ length: total }, (_, i) => `<i class="${i < invN ? "on" : ""}" style="--d:${i * 40}ms"></i>`).join("")}</div>
        <p class="small muted">The rest are waiting on the data team. The site reads the count from the files, so it grows as rows are added.</p></div>
      <div class="tile t-num" data-rv><span class="big">${pvs("brief", `<span data-count="12">0</span><small>TB</small>`)}</span><p>of microgravity combustion data in NASA's collection, per the challenge brief</p></div>
      <div class="tile t-num warn" data-rv><span class="big"><span data-count="${D.flags.length}">0</span></span><p>open data flags, shown on screen instead of hidden</p><a class="tiny" href="#data">Read the flags →</a></div>
      <div class="tile t-num t-rate" data-rv><span class="big"><span data-count="${((D.scientific_comparisons || {}).table1_records || []).length}">0</span></span><p>published spread rates from Olson et al. (2023) Table 1, in cm/s</p><a class="tiny" href="#transfer">Compare them →</a></div>
      <div class="tile t-num zero" data-rv><span class="big">0</span><p>values simulated or invented. Where the data stops, 1gnition says insufficient evidence.</p></div>
      <div class="tile t-meth" data-rv><div class="tile-h"><b>How each value was read</b></div>
        ${Object.entries(methods).map(([m, c]) => `<div class="mrow"><span>${A.esc(m === "table" ? "From a printed table" : m === "text" ? "From the paper's text" : "Digitized from a figure")}</span><span class="mbar"><i style="--w:${c / D.runs.length}"></i></span><b class="num">${c}</b></div>`).join("")}</div>`;
  }
  function buildClasses() {
    const cat = A.D.evidence_catalog; const el = document.getElementById("bento"); if (!cat || !el) return;
    const n = {}; cat.forEach(i => n[i.evidence_class] = (n[i.evidence_class] || 0) + 1);
    const L = [["published_numeric", "Published numbers"], ["digitized", "Digitized from a figure"], ["archive_claim", "NASA archive claims"], ["derived_comparison", "Derived comparisons"], ["proposed_experiment", "Proposed experiment"], ["synthetic", "Synthetic, not NASA"]];
    el.insertAdjacentHTML("beforeend", `<div class="tile t-cls" data-rv><div class="tile-h"><b>Every item is labeled by what it is</b><span class="tiny muted">${cat.length} items</span></div>
      <div class="cls-list">${L.filter(([k]) => n[k]).map(([k, l]) => `<span class="ev-cls ev-${k}">${l} · ${n[k]}</span>`).join("")}</div>
      <p class="small muted">Overlapping sources are linked, never added together: the 23 Figure 10 markers and 2 archive values describe burns already in Table 1.</p></div>`);
  }
  function typeCode() {
    if (typed) return; typed = true;
    const r = A.D.run("I-1") || A.D.runs[0];
    const keep = ["id", "flight", "material", "o2_pct", "pressure_kpa", "airflow_cm_s", "sample_width_cm", "steady_size_cm", "max_size_cm", "provenance"];
    const obj = {}; keep.forEach(k => { if (k in r) obj[k] = r[k]; });
    const json = JSON.stringify(obj, null, 2);
    const hl = s => A.esc(s).replace(/(&quot;[a-z_]+&quot;)(:)/g, '<span class="k">$1</span>$2').replace(/: (&quot;[^&]*&quot;)/g, ': <span class="s">$1</span>').replace(/: (-?\d+\.?\d*)/g, ': <span class="n">$1</span>').replace(/(<span class="k">&quot;provenance&quot;<\/span>)/, '<span class="pk">$1</span>');
    const pre = $("codePre");
    if (REDUCE) { pre.innerHTML = hl(json); return; }
    let i = 0; const t = setInterval(() => { i += 6; pre.innerHTML = hl(json.slice(0, i)) + '<span class="caret"></span>'; if (i >= json.length) { clearInterval(t); pre.innerHTML = hl(json); } }, 16);
  }

  /* ---------- scenarios ---------- */
  const GNUM = { micro: 0, lunar: .165, mars: .38, earth: 1 };
  function buildScenes() {
    const D = A.D, L = A.L;
    $("scenes").innerHTML = ["lunar", "iss", "mars"].map((h, i) => {
      const pr = L.PRESET[h], o2 = L.num(pr.o2), p = L.num(pr.p), g = GNUM[pr.g];
      const inG = D.runs.filter(r => r.gravity === pr.g);
      const within = o2 === null || p === null ? null : inG.filter(r => L.within(r, o2, p));
      const nr = o2 === null || p === null ? null : L.nearest(D.runs, o2, p);
      let state, line;
      if (within && within.length) { state = `<span class="state s-pub">${within.length} runs within tolerance</span>`; line = `Runs ${within.map(r => r.id).join(", ")} match this air and gravity.`; }
      else if (within) { state = `<span class="state s-insuf">Outside every tested box</span>`; line = nr ? `Nearest run ${nr.r.id} is ${Math.abs(nr.r.o2_pct - o2).toFixed(1)} points of oxygen short, and no run used ${A.esc(L.GRAV[pr.g]).toLowerCase()}.` : ""; }
      else { state = `<span class="state s-insuf">No run at this gravity</span>`; line = `The brief gives no Mars cabin air, so oxygen and pressure stay blank instead of borrowing Earth values.`; }
      return `<button class="scene" type="button" data-scn="${h}" style="--i:${i}">
        <div class="scene-art">${IGNIS_ART.scenePhoto(h)}<span class="ph-credit">${IGNIS_ART.PHOTOS[h].what} · ${IGNIS_ART.PHOTOS[h].credit}</span></div>
        <div class="scene-body">
          <div class="row between"><h3>${A.esc(pr.label)}</h3><span class="gauge" title="Gravity as a share of Earth's"><i style="--g:${g}"></i><b class="num">${g === 0 ? "≈0" : g} g</b></span></div>
          <dl class="scene-dl"><div><dt>Oxygen</dt><dd class="num">${o2 === null ? "not given" : o2 + "%"}</dd></div><div><dt>Pressure</dt><dd class="num">${p === null ? "not given" : p + " kPa"}</dd></div></dl>
          ${state}<p class="small t2">${line}</p>
          <span class="go">Explore this scenario →</span>
        </div></button>`;
    }).join("");
    document.querySelectorAll(".scene").forEach(el => {
      if (REDUCE) return;
      el.addEventListener("pointermove", e => { const r = el.getBoundingClientRect(), x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
        el.style.setProperty("--rx", (-y * 6).toFixed(2) + "deg"); el.style.setProperty("--ry", (x * 8).toFixed(2) + "deg"); el.style.setProperty("--mx", (x * 100 + 50) + "%"); el.style.setProperty("--my", (y * 100 + 50) + "%"); });
      el.addEventListener("pointerleave", () => { el.style.setProperty("--rx", "0deg"); el.style.setProperty("--ry", "0deg"); });
    });
    $("scenes").addEventListener("click", e => { const b = e.target.closest("[data-scn]"); if (!b || e.target.closest(".pv")) return; A.applyPreset(b.dataset.scn); A.renderAll(); A.go("evidence"); });
  }

  window.IGNIS_STORY = {
    init(api) {
      A = api;
      credits(); buildBurn(); buildReveal(); buildBento(); buildClasses(); buildScenes();
      heroTilt(); revealAll();
    },
    onShow() { onBurn(); }
  };
})();
