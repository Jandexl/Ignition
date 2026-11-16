#!/usr/bin/env python3
"""Check a deployed 1gnition backend end to end (standard library only).

    python3 backend/service/check_deploy.py                       # https://onegnition.onrender.com
    python3 backend/service/check_deploy.py http://localhost:8787

Checks: site served, health, NASA /api/predict never numeric, /api/scenario returns the
published I-1 rate with its source, synthetic demo domain,
one in-domain synthetic answer that reproduces the saved reference, one refusal,
one rejected real material, and CORS for the Netlify site. The free Render
plan sleeps when idle, so the first request waits up to 90 s.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://onegnition.onrender.com").rstrip("/")
SITE_ORIGIN = "https://1gnition.netlify.app"
REF = 0.12151900837578189   # backend/ignis-ml/outputs/supported_SYNTHETIC.json
results = []


def call(path, body=None, method=None, headers=None, timeout=90):
    data = json.dumps(body).encode() if body is not None else None
    h = {"Content-Type": "application/json"} if data else {}
    h.update(headers or {})
    req = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, r.headers, raw
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))


def js(raw):
    try:
        return json.loads(raw)
    except ValueError:
        return {}


code, _, raw = call("/index.html")
check("Site served at /index.html", code == 200 and b"1gnition" in raw, code)
code, _, raw = call("/api/health")
h = js(raw)
check("GET /api/health ok", code == 200 and h.get("status") == "ok", code)
check("Health: NASA prediction VALIDATION_NOT_SUPPORTED", h.get("prediction_status") == "VALIDATION_NOT_SUPPORTED")
sd = h.get("synthetic_demo") or {}
check("Health: synthetic demo model loaded", sd.get("ready") is True, sd.get("reason") or "field missing: old deploy?")

nasa = dict(flow_velocity_cm_s=20, oxygen_percent=21.7, pressure_kpa=102, material="SIBAL", flow_direction="concurrent",
            gravity_regime="microgravity", combustion_regime="steady_solid_spread")
code, _, raw = call("/api/predict", nasa)
p = js(raw)
check("POST /api/predict: NASA answer has no number", code == 200 and p.get("predicted_flame_spread_rate_cm_s", 0) is None, code)

code, _, raw = call("/api/scenario", nasa)
m = js(raw).get("measurements") or {}
ex = m.get("exact_matches") or []
check("POST /api/scenario: published I-1 rate 0.18 cm/s with its source",
      code == 200 and len(ex) == 1 and ex[0].get("measured_flame_spread_rate_cm_s") == 0.18
      and ex[0]["record"].get("source_id") == "OLSON-2023-T1", f"{code} {len(ex)} matches")

code, _, raw = call("/api/synthetic-demo/domain")
d = js(raw)
check("GET /api/synthetic-demo/domain labelled synthetic", code == 200 and d.get("not_nasa_data") is True
      and d.get("validation_status") == "SYNTHETIC_DEMO_ONLY", code)
check("Domain: start-up self-test passed", (d.get("self_test") or {}).get("passed") is True)

demo = dict(flow_velocity_cm_s=5, oxygen_percent=20, pressure_kpa=90, sample_width_cm=2, flow_direction="opposed")
code, _, raw = call("/api/synthetic-demo", demo)
r = js(raw).get("result") or {}
v = r.get("predicted_flame_spread_rate_cm_s")
check("Synthetic demo reproduces saved reference 0.121519 cm/s",
      code == 200 and r.get("synthetic") is True and isinstance(v, float) and abs(v - REF) < 1e-9, f"{code} {v}")
code, _, raw = call("/api/synthetic-demo", dict(demo, oxygen_percent=30, pressure_kpa=70.3))
r = js(raw).get("result") or {}
check("Synthetic demo refuses Moon-base air (no number)", code == 200 and r.get("status") == "UNSUPPORTED"
      and r.get("predicted_flame_spread_rate_cm_s", 0) is None, code)
code, _, raw = call("/api/synthetic-demo", dict(demo, material="SIBAL"))
check("Synthetic demo rejects a real material (400)", code == 400, code)

code, hd, _ = call("/api/synthetic-demo", method="OPTIONS",
                   headers={"Origin": SITE_ORIGIN, "Access-Control-Request-Method": "POST"})
allow = hd.get("Access-Control-Allow-Origin")
check(f"CORS allows the Netlify site {SITE_ORIGIN}", allow in (SITE_ORIGIN, "*"), f"Access-Control-Allow-Origin={allow}; set IGNITION_CORS_ORIGINS on Render")

print(f"\n{sum(results)} of {len(results)} deployment checks passed against {BASE}")
sys.exit(0 if all(results) else 1)
