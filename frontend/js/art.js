/* 1gnition illustrations. Drawn shapes only: none of these encode measured data. */
(function () {
  const A = {};
  let n = 0; const uid = p => p + (++n);

  A.flameEarth = () => { const g = uid("fe");
    return `<svg viewBox="0 0 260 300" role="img" aria-label="Illustration of a candle flame on Earth: tall teardrop shape">
    <defs>
      <radialGradient id="${g}o" cx="50%" cy="70%" r="60%"><stop offset="0" stop-color="#fff4d6"/><stop offset=".35" stop-color="#ffcf7a"/><stop offset=".7" stop-color="#f5a524"/><stop offset="1" stop-color="#e2561b" stop-opacity="0"/></radialGradient>
      <radialGradient id="${g}b" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#7fb2ff" stop-opacity=".9"/><stop offset="1" stop-color="#3b5bff" stop-opacity="0"/></radialGradient>
      <radialGradient id="${g}h" cx="50%" cy="55%" r="50%"><stop offset="0" stop-color="#f5a524" stop-opacity=".35"/><stop offset="1" stop-color="#f5a524" stop-opacity="0"/></radialGradient>
      <filter id="${g}f"><feGaussianBlur stdDeviation="3"/></filter>
    </defs>
    <ellipse cx="130" cy="150" rx="120" ry="140" fill="url(#${g}h)"/>
    <g class="plume" stroke="#f5a524" stroke-opacity=".25" fill="none" stroke-width="1.2" stroke-dasharray="3 7">
      <path d="M118 70 C110 40 124 20 116 0"/><path d="M142 70 C150 40 136 20 144 0"/><path d="M130 64 C130 40 130 20 130 0"/>
    </g>
    <g class="inflow" stroke="#7fb2ff" stroke-opacity=".5" fill="none" stroke-width="1.2" marker-end="url(#${g}a)">
      <path d="M40 250 Q90 240 108 214"/><path d="M220 250 Q170 240 152 214"/>
    </g>
    <defs><marker id="${g}a" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L6 3L0 6z" fill="#7fb2ff" fill-opacity=".6"/></marker></defs>
    <g class="flicker">
      <path d="M130 66 C150 110 166 150 160 186 C156 214 144 228 130 228 C116 228 104 214 100 186 C94 150 110 110 130 66Z" fill="url(#${g}o)" filter="url(#${g}f)"/>
      <path d="M130 120 C140 150 146 178 142 200 C140 214 136 220 130 220 C124 220 120 214 118 200 C114 178 120 150 130 120Z" fill="#fff8e6" opacity=".85"/>
      <ellipse cx="130" cy="222" rx="16" ry="10" fill="url(#${g}b)"/>
    </g>
    <rect x="127" y="214" width="6" height="16" rx="2" fill="#1b1204"/>
    <rect x="104" y="230" width="52" height="60" rx="6" fill="#1d232d" stroke="#2f3846"/>
  </svg>`; };

  A.flameMicro = () => { const g = uid("fm");
    return `<svg viewBox="0 0 260 300" role="img" aria-label="Illustration of a candle flame in microgravity: dim rounded sphere">
    <defs>
      <radialGradient id="${g}o" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#0a0c10" stop-opacity="0"/><stop offset=".55" stop-color="#3b5bff" stop-opacity=".12"/><stop offset=".78" stop-color="#7fb2ff" stop-opacity=".75"/><stop offset=".9" stop-color="#4fd1c5" stop-opacity=".35"/><stop offset="1" stop-color="#4fd1c5" stop-opacity="0"/></radialGradient>
      <radialGradient id="${g}c" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#f5a524" stop-opacity=".55"/><stop offset="1" stop-color="#f5a524" stop-opacity="0"/></radialGradient>
      <filter id="${g}f"><feGaussianBlur stdDeviation="2.4"/></filter>
    </defs>
    <g class="breathe">
      <circle cx="130" cy="176" r="84" fill="url(#${g}o)" filter="url(#${g}f)"/>
      <circle cx="130" cy="176" r="30" fill="url(#${g}c)"/>
    </g>
    <g class="diffuse" fill="#7fb2ff">
      ${Array.from({ length: 14 }, (_, i) => { const a = i / 14 * Math.PI * 2; return `<circle cx="${(130 + Math.cos(a) * 118).toFixed(1)}" cy="${(176 + Math.sin(a) * 118).toFixed(1)}" r="1.6" style="--a:${a.toFixed(2)}rad;animation-delay:${(i * .21).toFixed(2)}s"/>`; }).join("")}
    </g>
    <rect x="127" y="168" width="6" height="16" rx="2" fill="#1b1204"/>
    <rect x="104" y="184" width="52" height="60" rx="6" fill="#1d232d" stroke="#2f3846"/>
  </svg>`; };

  /* scenario art */
  A.moon = () => { const g = uid("mo");
    return `<svg viewBox="0 0 320 200" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <defs>
      <radialGradient id="${g}s" cx="35%" cy="30%" r="75%"><stop offset="0" stop-color="#d9dde4"/><stop offset=".55" stop-color="#8d95a3"/><stop offset="1" stop-color="#2a2f38"/></radialGradient>
      <linearGradient id="${g}g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a3f48"/><stop offset="1" stop-color="#14171c"/></linearGradient>
      <radialGradient id="${g}d" cx="50%" cy="20%" r="80%"><stop offset="0" stop-color="#ffcf7a" stop-opacity=".9"/><stop offset="1" stop-color="#f5a524" stop-opacity=".15"/></radialGradient>
    </defs>
    <g class="art-far"><circle cx="232" cy="62" r="40" fill="url(#${g}s)"/>
      <circle cx="220" cy="52" r="7" fill="#000" opacity=".14"/><circle cx="246" cy="74" r="10" fill="#000" opacity=".12"/><circle cx="238" cy="46" r="4" fill="#000" opacity=".15"/></g>
    <g class="art-near"><path d="M0 150 Q80 130 160 146 T320 140 V200 H0Z" fill="url(#${g}g)"/>
      <ellipse cx="60" cy="168" rx="18" ry="4" fill="#000" opacity=".3"/><ellipse cx="250" cy="176" rx="26" ry="5" fill="#000" opacity=".3"/>
      <path d="M118 150 a34 30 0 0 1 68 0z" fill="url(#${g}d)" opacity=".85"/><path d="M118 150 a34 30 0 0 1 68 0" fill="none" stroke="#ffcf7a" stroke-opacity=".7"/>
      <rect x="186" y="140" width="34" height="10" rx="3" fill="#2a2f38" stroke="#4a5160"/></g>
  </svg>`; };

  A.iss = () => { const g = uid("is");
    return `<svg viewBox="0 0 320 200" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <defs>
      <radialGradient id="${g}e" cx="50%" cy="0%" r="90%"><stop offset="0" stop-color="#2f6fd6"/><stop offset=".5" stop-color="#123a7a"/><stop offset="1" stop-color="#06122a"/></radialGradient>
      <linearGradient id="${g}p" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#c6873a"/><stop offset="1" stop-color="#6b3a12"/></linearGradient>
    </defs>
    <g class="art-far"><ellipse cx="160" cy="300" rx="260" ry="150" fill="url(#${g}e)"/>
      <ellipse cx="160" cy="300" rx="260" ry="150" fill="none" stroke="#7fb2ff" stroke-opacity=".7" stroke-width="2"/></g>
    <g class="art-near">
      <rect x="70" y="78" width="180" height="4" rx="2" fill="#8d95a3"/>
      ${[78, 104, 196, 222].map(x => `<g><rect x="${x}" y="40" width="20" height="36" fill="url(#${g}p)" stroke="#1b1204"/><rect x="${x}" y="84" width="20" height="36" fill="url(#${g}p)" stroke="#1b1204"/><line x1="${x + 10}" y1="76" x2="${x + 10}" y2="84" stroke="#8d95a3"/></g>`).join("")}
      <rect x="140" y="70" width="40" height="20" rx="6" fill="#d9dde4"/><rect x="152" y="90" width="16" height="22" rx="4" fill="#b6bfcc"/>
      <circle cx="160" cy="80" r="3" fill="#f5a524"/></g>
  </svg>`; };

  A.mars = () => { const g = uid("ma");
    return `<svg viewBox="0 0 320 200" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <defs>
      <radialGradient id="${g}s" cx="35%" cy="30%" r="75%"><stop offset="0" stop-color="#f2a36b"/><stop offset=".6" stop-color="#b4502a"/><stop offset="1" stop-color="#3a1408"/></radialGradient>
      <linearGradient id="${g}g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7a3518"/><stop offset="1" stop-color="#1c0a04"/></linearGradient>
      <linearGradient id="${g}k" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a1208" stop-opacity="0"/><stop offset="1" stop-color="#c46a3a" stop-opacity=".22"/></linearGradient>
    </defs>
    <rect width="320" height="150" fill="url(#${g}k)"/>
    <g class="art-far"><circle cx="78" cy="58" r="34" fill="url(#${g}s)"/>
      <path d="M50 52 Q78 46 106 54" stroke="#000" stroke-opacity=".15" stroke-width="4" fill="none"/><path d="M48 66 Q78 62 108 70" stroke="#000" stroke-opacity=".12" stroke-width="3" fill="none"/></g>
    <g class="art-near"><path d="M0 146 L60 128 L110 140 L170 120 L230 138 L320 126 V200 H0Z" fill="url(#${g}g)"/>
      <rect x="196" y="122" width="56" height="18" rx="9" fill="#d9dde4" opacity=".9"/><rect x="204" y="114" width="20" height="10" rx="5" fill="#b6bfcc"/>
      <circle cx="232" cy="131" r="3" fill="#f5a524"/></g>
  </svg>`; };

  A.custom = () => `<svg viewBox="0 0 320 200" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><g class="art-near" fill="none" stroke="#2f3846" stroke-width="1">
    ${Array.from({ length: 9 }, (_, i) => `<line x1="${20 + i * 35}" y1="20" x2="${20 + i * 35}" y2="180"/>`).join("")}${Array.from({ length: 5 }, (_, i) => `<line x1="20" y1="${20 + i * 40}" x2="300" y2="${20 + i * 40}"/>`).join("")}</g>
    <circle cx="160" cy="100" r="8" fill="#f5a524"/><circle cx="160" cy="100" r="22" fill="none" stroke="#f5a524" stroke-dasharray="4 4"/></svg>`;


  /* ---------- real photographs (files in img/) ---------- */
  A.PHOTOS = {
    hero:    { file: "hero-sunrise.jpg",      id: "iss063e058598",    what: "Orbital sunrise seen from the International Space Station, 24 July 2020", credit: "NASA" },
    flames:  { file: "flame-earth.jpg",       id: "GRC-1998-C-00486", what: "Candle flame in normal gravity and in microgravity", credit: "NASA Glenn Research Center" },
    acrylic: { file: "saffire-iv-acrylic.jpg",id: "jsc2023e046631",   what: "Acrylic sheet burning in orbit, Saffire-IV", credit: "NASA" },
    fabric:  { file: "saffire-iv-fabric.jpg", id: "jsc2023e046375",   what: "Cotton-fiberglass fabric burning in orbit, Saffire-IV", credit: "NASA" },
    lunar:   { file: "moon-apollo17.jpg",     id: "as17-134-20435",   what: "Apollo 17 landing site, Taurus-Littrow valley, 1972", credit: "NASA" },
    iss:     { file: "iss-flyaround.jpg",     id: "jsc2021e064215_alt", what: "International Space Station from Crew Dragon Endeavour, 2021", credit: "NASA" },
    mars:    { file: "mars-mount-sharp.jpg",  id: "PIA19803",         what: "Mount Sharp from the Curiosity rover, 2015", credit: "NASA/JPL-Caltech/MSSS" },
    night:   { file: "earth-night.jpg",       id: "iss072e340644",    what: "Orbital sunrise over Brazil from the International Space Station, 2024", credit: "NASA" }
  };
  A.photoUrl = k => "https://images.nasa.gov/details/" + A.PHOTOS[k].id;
  A.credit = k => { const p = A.PHOTOS[k]; return p ? `${p.what}. Photo: <a href="${A.photoUrl(k)}" target="_blank" rel="noopener">${p.credit}, ${p.id}</a>` : ""; };
  A.scenePhoto = h => { const p = A.PHOTOS[h]; return p ? `<img src="img/${p.file}" alt="${p.what}" loading="lazy">` : A.custom(); };
  A.scene = h => (A[{ lunar: "moon", iss: "iss", mars: "mars" }[h] || "custom"])();
  window.IGNIS_ART = A;
})();
