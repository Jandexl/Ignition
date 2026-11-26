#!/usr/bin/env python3
"""1gnition API server (standard library only, plus the ignis_ml package).

    python3 backend/server.py --frontend ../frontend --port 8787

Serves the static site and a small JSON API:

  GET  /api/health                 status, package version, data build hash
  GET  /api/<collection>           any data/<collection>.json (DATA_MODE "api" in js/config.js)
  POST /api/scenario               published measurement matches and model status
  POST /api/compare                {"baseline": "I-1", "comparison": "II-5"}
                                   deterministic descriptive comparison of two Olson Table 1 records
  POST /api/ask                    AI assistant (Google Gemini) grounded in the indexed records; see assistant.py.
                                   Needs GEMINI_API_KEY on the server; 6 questions/min per visitor, 20/min site-wide.
  POST /api/predict                scenario per ignis-ml/docs/request.schema.json
                                   returns ignis_ml.prediction.predict(..., bundle=None): never a number.
                                   Validated against response.schema.json before it is sent.
  GET  /api/synthetic-demo/domain  inputs, observed ranges and labels of the SYNTHETIC demo model
  POST /api/synthetic-demo         {"flow_velocity_cm_s", "oxygen_percent", "pressure_kpa",
                                    "sample_width_cm", "flow_direction"} -> ignis_ml.prediction.predict
                                   with the saved SYNTHETIC_DEMO_MODEL.joblib (see synthetic_demo.py).
                                   Every answer is labelled SYNTHETIC_DEMO_ONLY: invented data, not NASA.

/api/predict never loads a bundle, so this server cannot return a NASA prediction.
The only model it loads is the synthetic demo bundle, after a SHA-256 check against
MANIFEST.sha256 and a start-up self-test; its answers go out on a separate endpoint.
There is no authentication: run it for demos and local integration, behind a
proper gateway if exposed publicly. CORS origins: IGNITION_CORS_ORIGINS
(comma-separated, default "*"). POST rate limit: 60 requests per minute per IP.
"""
import argparse
import json
import mimetypes
import os
import sys
import threading
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
PKG = HERE.parent / "ignis-ml"
sys.path.insert(0, str(PKG / "src"))
sys.path.insert(0, str(HERE))

import jsonschema  # noqa: E402
import evidence  # noqa: E402
import synthetic_demo  # noqa: E402
import assistant  # noqa: E402
from ignis_ml import __version__  # noqa: E402
from ignis_ml.prediction import predict
from ignis_ml.contracts import REQUEST_SCHEMA  # noqa: E402

RESPONSE_SCHEMA = json.loads((PKG / "docs" / "response.schema.json").read_text())
MAX_BODY = 16 * 1024
RATE = 60
ASK_RATE_IP = 6        # AI questions per minute per visitor
ASK_RATE_ALL = 20      # AI questions per minute for the whole site (protects the Gemini quota)
COLLECTION_OK = set("abcdefghijklmnopqrstuvwxyz_")


class State:
    def __init__(self, frontend):
        self.frontend = Path(frontend).resolve()
        self.data = self.frontend / "data"
        self.lock = threading.Lock()
        self.hits = {}
        self.origins = [o.strip() for o in os.environ.get("IGNITION_CORS_ORIGINS", "*").split(",") if o.strip()]
        self.demo = synthetic_demo.SyntheticDemo()
        self.ai = assistant.Assistant(self.frontend, demo=self.demo)
        self.ask_hits = {}

    def sci(self):
        return evidence.load_json(self.data / "scientific_comparisons.json")

    def allow_ask(self, ip):
        now = time.time()
        with self.lock:
            mine = [t for t in self.ask_hits.get(ip, []) if now - t < 60]
            every = [t for t in self.ask_hits.get("*", []) if now - t < 60]
            if len(mine) >= ASK_RATE_IP or len(every) >= ASK_RATE_ALL:
                self.ask_hits[ip], self.ask_hits["*"] = mine, every
                return False
            self.ask_hits[ip], self.ask_hits["*"] = mine + [now], every + [now]
            return True

    def allow(self, ip):
        now = time.time()
        with self.lock:
            q = [t for t in self.hits.get(ip, []) if now - t < 60]
            if len(q) >= RATE:
                self.hits[ip] = q
                return False
            q.append(now)
            self.hits[ip] = q
            return True


def make_handler(state):
    class H(SimpleHTTPRequestHandler):
        server_version = "1gnition"
        sys_version = ""

        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(state.frontend), **kw)

        def log_message(self, fmt, *args):
            if os.environ.get("IGNITION_QUIET") != "1":
                super().log_message(fmt, *args)

        # ---- helpers
        def _cors(self):
            origin = self.headers.get("Origin")
            if "*" in state.origins:
                self.send_header("Access-Control-Allow-Origin", "*")
            elif origin and origin in state.origins:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")

        def end_headers(self):
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            super().end_headers()

        def _json(self, code, obj):
            body = json.dumps(obj, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self._cors()
            self.end_headers()
            self.wfile.write(body)

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0:
                raise ValueError("Empty request body")
            if n > MAX_BODY:
                raise OverflowError("Request body too large")
            if "application/json" not in (self.headers.get("Content-Type") or ""):
                raise ValueError("Content-Type must be application/json")
            return json.loads(self.rfile.read(n).decode("utf-8"))

        # ---- verbs
        def do_OPTIONS(self):
            self.send_response(HTTPStatus.NO_CONTENT)
            self._cors()
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Max-Age", "600")
            self.end_headers()

        def do_GET(self):
            path = urlparse(self.path).path
            if not path.startswith("/api/"):
                return super().do_GET()
            name = path[len("/api/"):].strip("/")
            if name == "health":
                man = state.data / "build_manifest.json"
                return self._json(200, dict(status="ok", service="1gnition", ignis_ml_version=__version__,
                                            data_build=evidence.load_json(man) if man.exists() else None,
                                            prediction_status=state.sci()["prediction_status"],
                                            synthetic_demo=state.demo.status(),
                                            assistant=state.ai.status()))
            if name == "synthetic-demo/domain":
                if not state.demo.ready:
                    return self._json(503, dict(error="Synthetic demo model unavailable", reason=state.demo.reason))
                return self._json(200, state.demo.domain())
            if not name or not set(name) <= COLLECTION_OK:
                return self._json(404, dict(error="Unknown endpoint"))
            f = state.data / f"{name}.json"
            if not f.exists():
                return self._json(404, dict(error=f"No collection '{name}'"))
            return self._json(200, evidence.load_json(f))

        def _ip(self):
            fwd = self.headers.get("X-Forwarded-For", "")   # Render's proxy puts the visitor first
            return fwd.split(",")[0].strip() or self.client_address[0]

        def do_POST(self):
            path = urlparse(self.path).path
            if path not in ("/api/compare", "/api/predict", "/api/scenario", "/api/synthetic-demo", "/api/ask"):
                return self._json(404, dict(error="Unknown endpoint"))
            if not state.allow(self._ip()):
                return self._json(429, dict(error="Rate limit: 60 requests per minute"))
            try:
                body = self._body()
            except OverflowError as e:
                return self._json(413, dict(error=str(e)))
            except (ValueError, UnicodeDecodeError) as e:
                return self._json(400, dict(status="INPUT_ERROR", error=str(e).split("\n")[0]))
            if path == "/api/ask":
                if not state.ai.ready:
                    return self._json(503, dict(error="AI assistant not configured", reason=state.ai.status()["reason"]))
                if not state.allow_ask(self._ip()):
                    return self._json(429, dict(error="Too many questions right now. Wait a minute and ask again."))
                try:
                    return self._json(200, state.ai.ask(body))
                except ValueError as e:
                    return self._json(400, dict(status="INPUT_ERROR", error=str(e)))
                except RuntimeError as e:
                    return self._json(502, dict(error=str(e)))
            if path == "/api/synthetic-demo":
                if not state.demo.ready:
                    return self._json(503, dict(error="Synthetic demo model unavailable", reason=state.demo.reason))
                try:
                    return self._json(200, state.demo.run(body))
                except ValueError as e:
                    return self._json(400, dict(status="INPUT_ERROR", error=str(e)))
                except (jsonschema.ValidationError, RuntimeError) as e:
                    return self._json(500, dict(error="Synthetic response refused", detail=str(e).split("\n")[0]))
            if path == "/api/compare":
                if not isinstance(body, dict) or not isinstance(body.get("baseline"), str) or not isinstance(body.get("comparison"), str):
                    return self._json(400, dict(status="INPUT_ERROR", error="Send {\"baseline\": id, \"comparison\": id}"))
                try:
                    return self._json(200, evidence.compare_records(state.sci(), body["baseline"], body["comparison"]))
                except (KeyError, ValueError) as e:
                    return self._json(400, dict(status="INPUT_ERROR", error=str(e).strip("'")))
            if path == "/api/scenario":
                try:
                    jsonschema.validate(body, REQUEST_SCHEMA)
                    json.dumps(body, allow_nan=False)
                except (jsonschema.ValidationError, ValueError, TypeError) as exc:
                    return self._json(400, dict(status="INPUT_ERROR", error=str(exc).split("\n")[0]))
                sci = state.sci()
                prediction = predict(body, bundle=None, evidence=evidence.table1_evidence_frame(sci))
                return self._json(200, dict(
                    scenario=body,
                    measurements=evidence.scenario_measurements(sci, body),
                    prediction=prediction,
                ))
            # /api/predict: never loads a bundle, so the answer is LIMITED_EVIDENCE or UNSUPPORTED with a null number
            ev = evidence.table1_evidence_frame(state.sci())
            resp = predict(body, bundle=None, evidence=ev)
            try:
                jsonschema.validate(resp, RESPONSE_SCHEMA)
            except jsonschema.ValidationError as e:
                return self._json(500, dict(error="Response failed schema validation", detail=str(e).split("\n")[0]))
            if resp["predicted_flame_spread_rate_cm_s"] is not None:  # belt and braces
                return self._json(500, dict(error="Refusing to return a numeric NASA prediction"))
            return self._json(200, resp)

    return H


def serve(frontend, host="127.0.0.1", port=8787):
    state = State(frontend)
    mimetypes.add_type("text/markdown; charset=utf-8", ".md")
    httpd = ThreadingHTTPServer((host, port), make_handler(state))
    httpd.state = state
    return httpd


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--frontend", required=True)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    a = ap.parse_args()
    httpd = serve(a.frontend, a.host, a.port)
    print(f"1gnition serving {Path(a.frontend).resolve()} on http://{a.host}:{a.port}  (API under /api/)")
    print("Synthetic demo model:", "ready" if httpd.state.demo.ready else f"DISABLED ({httpd.state.demo.reason})")
    ai = httpd.state.ai.status()
    print("AI assistant:", f"ready ({ai['provider']}, {ai['model']})" if ai["ready"] else f"OFF ({ai['reason']}); the site uses its offline helper")
    httpd.serve_forever()
