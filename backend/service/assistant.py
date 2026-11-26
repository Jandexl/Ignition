"""Ask 1gnition: an AI assistant grounded in 1gnition's indexed records (Google Gemini).

POST /api/ask  {"question": str, "scenario": {...}, "history": [{"role": "user"|"assistant", "text": str}]}
            -> {"answer", "state", "citations": [{"source_id", "location"}], "unverified_numbers": [...],
                "model", "provider": "Google Gemini", "ai_generated": true}

How it stays honest
  * Gemini sees only CONTEXT built here from frontend/data/*.json and the science notes in
    frontend/docs/. The system instruction tells it to answer from that context alone, to say
    when the records don't cover a question, never to predict a spread rate, and to keep
    synthetic numbers labelled as invented.
  * The server, not the model, has the last word on citations: any source_id that is not in
    the context is dropped.
  * Every number in the answer is compared with the numbers in the context, the question and the
    scenario. Numbers found nowhere are returned in unverified_numbers, and the site shows them
    with a warning instead of passing them off as data.

Configuration (environment variables on Render; never in the website):
  GEMINI_API_KEY   required. Without it /api/ask answers 503 and the site uses its offline helper.
  GEMINI_MODEL     optional, default below. Change it on Render if Google renames models.
  GEMINI_FALLBACK_MODELS  optional, comma-separated; tried when the main model is busy (503) or missing (404).
  GEMINI_API_BASE  optional, for tests only.
"""
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path


class _Busy(Exception):
    """Gemini is overloaded, rate-limited or unreachable: try again or try another model."""


class _Missing(Exception):
    """This model ID does not exist (404)."""

DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_FALLBACKS = "gemini-3.1-flash-lite,gemini-3.6-flash"   # tried in order when the main model is busy or missing
RETRY_STATUS = (429, 500, 502, 503, 504)
API_BASE = "https://generativelanguage.googleapis.com/v1beta"
MAX_QUESTION = 600
MAX_HISTORY = 6
STATES = ("supported", "limited", "insufficient", "general", "out_of_scope")

DATA_FILES = ("meta", "sources", "investigations", "runs", "spread_rates", "findings", "flags", "source_conflicts")
DOC_FILES = ("Scientific_Methodology.md", "Scientific_Lead_Decision.md", "SCIENCE_FRONTEND.md")

RULES = """You are Ask 1gnition, the assistant inside 1gnition, a NASA Space Apps 2026 project (challenge: Flame in Freefall).
1gnition shows which NASA microgravity combustion runs bear on a spacecraft or Moon-base fire scenario,
which comparisons between runs are fair, and where the evidence runs out.

Rules. Follow all of them.
1. Answer ONLY from QUICK FACTS and CONTEXT below. If they do not cover the question, say so plainly and, if useful,
   say what data would be needed. Never fill gaps from general knowledge, and never guess.
2. Answer exactly what was asked. Do not add facts the question did not ask about.
3. Never predict, estimate, extrapolate or interpolate a flame spread rate, flame length or any other value
   for a scenario. 1gnition's prediction status is VALIDATION_NOT_SUPPORTED: no evaluated NASA model exists.
   You may quote measured values exactly as recorded, with their record ID.
4. Units: copy each value with the unit it has in the records. Never offer another unit, a conversion, or
   "depending on units". Flame length or size (cm) is not spread rate (cm/s). Airflow (cm/s) is not oxygen (%).
5. Numbers from the synthetic model or synthetic verification are INVENTED data. If you mention them,
   say they are synthetic and not NASA data.
6. When sources disagree (source_conflicts, flags), give both values and say the conflict is unresolved. Do not
   pick one. If two sources report the same quantity for a run, mention both. Records that may describe the same
   burn are not independent runs.
7. Comparisons between runs are descriptive: list what changed between them and do not claim a cause.
8. SCENARIO PANEL is background only. Use it ONLY when the question refers to it ("my scenario", "these settings",
   "these conditions", "this habitat", "here"). Otherwise ignore it completely and do not mention it.
9. Vague questions (e.g. "what about the data"): give a 2-3 sentence overview of what data 1gnition has, from
   QUICK FACTS, then suggest two specific questions the user could ask. Use state "general".
10. Greetings and questions about 1gnition itself or how to use the site: answer briefly; state "general".
    Questions unrelated to 1gnition or microgravity fire: say you can only help with 1gnition's evidence;
    state "out_of_scope".
11. Be concise: at most about 120 words, plain language, no markdown.
12. Cite the sources of the records you actually used: a run's own source_id (Olson Table 1 rows are
    OLSON-2023-T1; runs give provenance.source_id), with the location given in the record. Cite "brief" only for
    facts taken from the challenge brief. No citations for greetings.

Reply with JSON only, exactly this shape:
{"answer": "<text>", "state": "supported" | "limited" | "insufficient" | "general" | "out_of_scope",
 "citations": [{"source_id": "<id from CONTEXT>", "location": "<where in that source>"}]}
state: supported = the records answer it directly; limited = partly, with caveats; insufficient = the records
do not cover it; general = greeting, overview or how-to; out_of_scope = not about 1gnition or its evidence."""

NUM = re.compile(r"(?<![\w.])-?\d+(?:[.,]\d+)?")


def _numbers(text):
    out = set()
    for m in NUM.findall(text or ""):
        try:
            v = float(m.replace(",", ""))
        except ValueError:
            continue
        out.add(round(v, 6))
    return out


class Assistant:
    def __init__(self, frontend_dir, model=None, api_key=None, api_base=None, demo=None):
        self.frontend = Path(frontend_dir)
        self.api_key = api_key if api_key is not None else os.environ.get("GEMINI_API_KEY", "").strip()
        self.model = model or os.environ.get("GEMINI_MODEL", "").strip() or DEFAULT_MODEL
        self.api_base = (api_base or os.environ.get("GEMINI_API_BASE", "").strip() or API_BASE).rstrip("/")
        fb = os.environ.get("GEMINI_FALLBACK_MODELS", DEFAULT_FALLBACKS)
        self.fallbacks = [m.strip() for m in fb.split(",") if m.strip() and m.strip() != self.model]
        self.demo = demo
        self.context, self.source_ids, self.context_numbers = self._build_context()
        self.quick = self._quick_facts()
        self.context_numbers |= _numbers(self.quick)

    # ---- context
    def _build_context(self):
        data = self.frontend / "data"
        parts, ids = {}, set()
        for name in DATA_FILES:
            p = data / f"{name}.json"
            if p.exists():
                parts[name] = json.loads(p.read_text())
        sci = json.loads((data / "scientific_comparisons.json").read_text())
        parts["olson_2023_table1_records"] = sci.get("table1_records", [])
        parts["published_comparisons"] = sci.get("comparison_cases", [])
        parts["proposed_2x2_experiment"] = sci.get("factorial_readiness", {})
        parts["nasa_prediction"] = dict(status=sci.get("prediction_status"), predicted_cm_s=sci.get("prediction_cm_s"),
                                        note="No independently evaluated NASA spread-rate model exists, so 1gnition gives no predicted rate.")
        if self.demo is not None and getattr(self.demo, "ready", False):
            d = self.demo.domain()
            parts["synthetic_demo_model"] = dict(
                label=d["label"], what="Ridge regression fitted to invented data; shows the software path works, not physics.",
                inputs={k: dict(unit=v["unit"], min=v["min"], max=v["max"]) for k, v in d["inputs"].items()},
                fixed={k: v.get("value") for k, v in d["fixed"].items()},
                behaviour="Answers only inside the invented data range; refuses outside it, e.g. 30% oxygen at 70.3 kPa.")
        docs = {}
        for name in DOC_FILES:
            p = self.frontend / "docs" / name
            if p.exists():
                docs[name] = p.read_text()
        pipeline = self.frontend.parent / "backend" / "ignis-ml" / "docs" / "REAL_DATA_PIPELINE_STATUS.md"
        if pipeline.exists():
            docs["REAL_DATA_PIPELINE_STATUS.md"] = pipeline.read_text()

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("source_id", "id") and isinstance(v, str) and k == "source_id":
                        ids.add(v)
                    if k == "source_ids" and isinstance(v, list):
                        ids.update(x for x in v if isinstance(x, str))
                    walk(v)
            elif isinstance(o, list):
                for x in o:
                    walk(x)
        walk(parts)
        ids.update(s["id"] for s in parts.get("sources", []) if isinstance(s, dict) and "id" in s)
        self._parts = parts
        text = "CONTEXT (1gnition indexed records, JSON):\n" + json.dumps(parts, separators=(",", ":"), ensure_ascii=False)
        text += "\n\nCONTEXT (science notes):\n" + "\n\n".join(f"--- {k} ---\n{v}" for k, v in docs.items())
        return text, ids, _numbers(text)

    def _runs(self):
        r = self._parts.get("runs", [])
        return r if isinstance(r, list) else next((v for v in r.values() if isinstance(v, list)), [])

    def _quick_facts(self):
        t1 = sorted(self._parts.get("olson_2023_table1_records", []), key=lambda r: -(r.get("spread_cm_s") or 0))
        runs = self._runs()
        inv = self._parts.get("investigations", [])
        inv = inv if isinstance(inv, list) else next((v for v in inv.values() if isinstance(v, list)), [])
        lines = ["QUICK FACTS (computed from the records; use these first):",
                 f"- Published flame SPREAD RATES (cm/s): {len(t1)} burns in Olson et al. (2023) Table 1, source OLSON-2023-T1. "
                 "Fastest to slowest:"]
        for r in t1:
            lines.append(f"  {r['record_id']} ({r.get('flight')}, {r.get('material')}): {r.get('spread_cm_s')} cm/s; "
                         f"width {r.get('sample_width_cm')} cm, length {r.get('sample_length_cm')} cm, airflow {r.get('flow_cm_s')} cm/s, "
                         f"oxygen {r.get('oxygen_vol_pct')}%, pressure {r.get('pressure_kpa')} kPa; flame length {r.get('flame_length_cm')} cm "
                         f"[{r.get('source_locator')}]")
        lines.append("  Saffire runs are those with a Saffire flight; BASS-WIDE and BASS-NARROW are BASS (ISS glovebox), not Saffire.")
        sized = [r for r in runs if r.get("steady_size_cm") is not None]
        lines.append(f"- Flame SIZE records (cm, not spread rates): {len(sized)} runs from the Saffire I-V paper Table 2 and other sources "
                     "(field steady_size_cm / max_size_cm in runs).")
        lines.append(f"- Investigations indexed: {len(inv)}. Gravity of every indexed run: "
                     + ", ".join(sorted({str(r.get('gravity')) for r in runs})) + ". No lunar- or Mars-gravity combustion run is indexed.")
        lines.append("- NASA spread-rate prediction: VALIDATION_NOT_SUPPORTED (no number). Only the synthetic demo model gives numbers, from invented data.")
        return "\n".join(lines)

    def _scenario_block(self, scen):
        if not any(v not in (None, "") for v in scen.values()):
            return "SCENARIO PANEL (background; use only if the question refers to it): empty."
        o2, kpa = scen.get("o2_pct"), scen.get("pressure_kpa")
        out = ["SCENARIO PANEL (background; use only if the question refers to it): " + json.dumps(scen)]
        if isinstance(o2, (int, float)) and isinstance(kpa, (int, float)):
            pts = []
            for r in self._runs():
                if isinstance(r.get("o2_pct"), (int, float)) and isinstance(r.get("pressure_kpa"), (int, float)):
                    pts.append((r["id"], r.get("flight") or r.get("investigation_id"), r["o2_pct"], r["pressure_kpa"], r.get("gravity"),
                                f"steady flame size {r.get('steady_size_cm')} cm" if r.get("steady_size_cm") is not None else "no size reported",
                                (r.get("provenance") or {}).get("source_id")))
            for r in self._parts.get("olson_2023_table1_records", []):
                pts.append((r["record_id"], r.get("flight"), r["oxygen_vol_pct"], r["pressure_kpa"], "micro",
                            f"spread rate {r['spread_cm_s']} cm/s", "OLSON-2023-T1"))
            pts.sort(key=lambda x: ((x[2] - o2) ** 2 + ((x[3] - kpa) / 5) ** 2) ** .5)
            out.append("Closest indexed runs to these settings (by oxygen and pressure; computed by the server):")
            for x in pts[:4]:
                out.append(f"  {x[0]} ({x[1]}): {x[2]}% oxygen, {x[3]} kPa, gravity {x[4]}, {x[5]}; "
                           f"{abs(x[2]-o2):.1f} oxygen points and {abs(x[3]-kpa):.1f} kPa away [source {x[6]}]")
            exact = [x for x in pts if abs(x[2] - o2) < .05 and abs(x[3] - kpa) < .5]
            out.append("  An indexed run matches these settings exactly." if exact else "  No indexed run matches these settings exactly.")
        if str(scen.get("gravity", "")).lower() in ("lunar", "moon", "mars", "partial"):
            out.append("  No indexed run was done at this gravity level.")
        return "\n".join(out)

    # ---- public
    @property
    def ready(self):
        return bool(self.api_key)

    def status(self):
        return dict(ready=self.ready, provider="Google Gemini", model=self.model,
                    reason=None if self.ready else "GEMINI_API_KEY is not set on the server")

    def validate(self, body):
        if not isinstance(body, dict):
            raise ValueError("Send a JSON object")
        q = body.get("question")
        if not isinstance(q, str) or not q.strip():
            raise ValueError("question must be a non-empty string")
        if len(q) > MAX_QUESTION:
            raise ValueError(f"question is longer than {MAX_QUESTION} characters")
        scen = body.get("scenario") or {}
        if not isinstance(scen, dict):
            raise ValueError("scenario must be an object")
        hist = body.get("history") or []
        if not isinstance(hist, list):
            raise ValueError("history must be a list")
        clean = []
        for h in hist[-MAX_HISTORY:]:
            if isinstance(h, dict) and h.get("role") in ("user", "assistant") and isinstance(h.get("text"), str):
                clean.append(dict(role=h["role"], text=h["text"][:1500]))
        return q.strip(), {k: v for k, v in scen.items() if isinstance(v, (str, int, float)) or v is None}, clean

    def ask(self, body):
        q, scen, hist = self.validate(body)
        system = RULES + "\n\n" + self.quick + "\n\n" + self.context
        contents = [dict(role="model" if h["role"] == "assistant" else "user", parts=[dict(text=h["text"])]) for h in hist]
        user = f"{self._scenario_block(scen)}\n\nQuestion: {q}"
        contents.append(dict(role="user", parts=[dict(text=user)]))
        payload = dict(system_instruction=dict(parts=[dict(text=system)]), contents=contents,
                       generationConfig=dict(temperature=0.1, maxOutputTokens=700, responseMimeType="application/json"))
        raw, used = self._call(payload)
        out = self._check(raw, q, scen, hist)
        out["model"] = used
        return out

    # ---- internals
    def _call(self, payload):
        """Main model, the main model again after a short pause, then each fallback model.
        Busy (429/5xx/timeouts) moves on to the next attempt; a missing model (404) is skipped.
        Stops after about 70 s in total so the website's 90 s limit is never hit. Returns (text, model used)."""
        import time
        t0, busy, main_missing = time.time(), False, None
        for model, pause in [(self.model, 0), (self.model, 1.5)] + [(m, 0) for m in self.fallbacks]:
            if model == self.model and main_missing is not None:
                continue
            if time.time() - t0 + pause > 45:
                break
            time.sleep(pause)
            try:
                return self._call_one(model, payload, timeout=min(25, max(5, 70 - (time.time() - t0)))), model
            except _Busy:
                busy = True
            except _Missing as e:
                if model == self.model:
                    main_missing = str(e)
        if main_missing is not None and not busy:
            raise RuntimeError(f"Model '{self.model}' not found. Set GEMINI_MODEL on the server. {main_missing}".strip())
        raise RuntimeError("The AI service is busy right now. Try again in a minute.")

    def _call_one(self, model, payload, timeout=25):
        url = f"{self.api_base}/models/{model}:generateContent"
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                j = json.loads(r.read())
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = json.loads(e.read()).get("error", {}).get("message", "")
            except Exception:
                pass
            if e.code in RETRY_STATUS:
                raise _Busy(detail)
            if e.code == 404:
                raise _Missing(detail)
            raise RuntimeError(f"AI service error {e.code}. {detail}".strip())
        except (urllib.error.URLError, TimeoutError) as e:
            raise _Busy(str(getattr(e, "reason", e)))
        try:
            cand = j["candidates"][0]
            return "".join(p.get("text", "") for p in cand["content"]["parts"])
        except (KeyError, IndexError, TypeError):
            reason = (j.get("promptFeedback") or {}).get("blockReason") or "no answer returned"
            raise RuntimeError(f"The AI service returned no answer ({reason}).")

    def _check(self, raw, q, scen, hist):
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
        try:
            j = json.loads(text)
            answer = str(j.get("answer", "")).strip()
            state = j.get("state") if j.get("state") in STATES else "limited"
            cites = j.get("citations") or []
        except (ValueError, AttributeError):
            answer, state, cites = text, "limited", []
        if not answer:
            raise RuntimeError("The AI service returned an empty answer.")
        good, seen = [], set()
        for c in cites if isinstance(cites, list) else []:
            if isinstance(c, dict) and c.get("source_id") in self.source_ids:
                key = (c["source_id"], str(c.get("location", ""))[:160])
                if key not in seen:
                    seen.add(key)
                    good.append(dict(source_id=key[0], location=key[1]))
        allowed = self.context_numbers | _numbers(q) | _numbers(json.dumps(scen)) | _numbers(" ".join(h["text"] for h in hist))
        unverified = []
        for m in NUM.findall(answer):
            try:
                v = round(float(m.replace(",", "")), 6)
            except ValueError:
                continue
            if v not in allowed and abs(v) not in allowed and m not in unverified:
                unverified.append(m)
        warnings = []
        if re.search(r"(?<![cmkμu])m/s|\bmeters? per second|metres? per second|\bin/s|ft/s|mph|km/h", answer, re.I):
            warnings.append("This answer mentions a unit (such as m/s) that 1gnition's records don't use. Spread rates in the records are in cm/s.")
        if state == "out_of_scope":
            good = []
        return dict(answer=answer, state=state, citations=good, unverified_numbers=unverified, warnings=warnings,
                    ai_generated=True, provider="Google Gemini", model=self.model)
