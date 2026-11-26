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
  GEMINI_API_BASE  optional, for tests only.
"""
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_MODEL = "gemini-3.5-flash-lite"
API_BASE = "https://generativelanguage.googleapis.com/v1beta"
MAX_QUESTION = 600
MAX_HISTORY = 6
STATES = ("supported", "limited", "insufficient", "out_of_scope")

DATA_FILES = ("meta", "sources", "investigations", "runs", "spread_rates", "findings", "flags", "source_conflicts")
DOC_FILES = ("Scientific_Methodology.md", "Scientific_Lead_Decision.md", "SCIENCE_FRONTEND.md")

RULES = """You are Ask 1gnition, the assistant inside 1gnition, a NASA Space Apps 2026 project (challenge: Flame in Freefall).
1gnition shows which NASA microgravity combustion runs bear on a spacecraft or Moon-base fire scenario,
which comparisons between runs are fair, and where the evidence runs out.

Rules. Follow all of them.
1. Answer ONLY from CONTEXT below. If CONTEXT does not cover the question, say so plainly and, if useful,
   say what data would be needed. Never fill gaps from general knowledge, and never guess.
2. Never predict, estimate, extrapolate or interpolate a flame spread rate, flame length or any other value
   for a scenario. 1gnition's prediction status is VALIDATION_NOT_SUPPORTED: no evaluated NASA model exists.
   You may quote measured values exactly as recorded, with their record ID and source.
3. Keep units exact. Flame length or size (cm) is not spread rate (cm/s or mm/s). Airflow (cm/s) is not oxygen (%).
4. Numbers from the synthetic model or synthetic verification are INVENTED data. If you mention them,
   say they are synthetic and not NASA data.
5. When sources disagree (see source_conflicts and flags), show both values and say the conflict is unresolved.
   Do not pick one. Records that may describe the same burn are not independent runs.
6. Comparisons between runs are descriptive unless CONTEXT says otherwise: list what changed between them,
   and do not claim a cause.
7. For general questions about the project or how to use the site, answer briefly from CONTEXT.
   For questions unrelated to 1gnition or microgravity fire, say you can only help with 1gnition's evidence.
8. Be concise: at most about 150 words, plain language, no markdown headings.
9. Cite every factual claim with source_id values that appear in CONTEXT, plus a location (table/row/page) when CONTEXT gives one.

Reply with JSON only, exactly this shape:
{"answer": "<text>", "state": "supported" | "limited" | "insufficient" | "out_of_scope",
 "citations": [{"source_id": "<id from CONTEXT>", "location": "<where in that source>"}]}
state: supported = the records answer it directly; limited = partly, with caveats; insufficient = the records
do not cover it; out_of_scope = not about 1gnition or its evidence."""

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
        self.demo = demo
        self.context, self.source_ids, self.context_numbers = self._build_context()

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
        text = "CONTEXT (1gnition indexed records, JSON):\n" + json.dumps(parts, separators=(",", ":"), ensure_ascii=False)
        text += "\n\nCONTEXT (science notes):\n" + "\n\n".join(f"--- {k} ---\n{v}" for k, v in docs.items())
        return text, ids, _numbers(text)

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
        system = RULES + "\n\n" + self.context
        contents = [dict(role="model" if h["role"] == "assistant" else "user", parts=[dict(text=h["text"])]) for h in hist]
        user = f"Current scenario panel settings (may be blank): {json.dumps(scen)}\n\nQuestion: {q}"
        contents.append(dict(role="user", parts=[dict(text=user)]))
        payload = dict(system_instruction=dict(parts=[dict(text=system)]), contents=contents,
                       generationConfig=dict(temperature=0.2, maxOutputTokens=700, responseMimeType="application/json"))
        raw = self._call(payload)
        return self._check(raw, q, scen, hist)

    # ---- internals
    def _call(self, payload):
        url = f"{self.api_base}/models/{self.model}:generateContent"
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key})
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                j = json.loads(r.read())
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = json.loads(e.read()).get("error", {}).get("message", "")
            except Exception:
                pass
            if e.code == 429:
                raise RuntimeError("The AI service is busy (free-tier limit reached). Try again in a minute.")
            if e.code == 404:
                raise RuntimeError(f"Model '{self.model}' not found. Set GEMINI_MODEL on the server. {detail}".strip())
            raise RuntimeError(f"AI service error {e.code}. {detail}".strip())
        except (urllib.error.URLError, TimeoutError) as e:
            raise RuntimeError(f"Could not reach the AI service: {getattr(e, 'reason', e)}")
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
        return dict(answer=answer, state=state, citations=good, unverified_numbers=unverified,
                    ai_generated=True, provider="Google Gemini", model=self.model)
