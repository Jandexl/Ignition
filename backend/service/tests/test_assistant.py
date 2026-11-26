"""Ask 1gnition AI assistant (backend/service/assistant.py), tested against a fake Gemini server.

The fake server records each request and replays a scripted reply, so these tests check what
1gnition sends to Gemini and how it polices the answer, without a real API key.
"""
import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import assistant  # noqa: E402
import server  # noqa: E402

FRONTEND = Path(os.environ.get("IGNITION_FRONTEND", HERE.parents[2] / "frontend")).resolve()


class FakeGemini:
    """Stands in for generativelanguage.googleapis.com."""

    def __init__(self):
        self.requests, self.reply, self.status = [], None, 200
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                fake.requests.append(dict(path=self.path, key=self.headers.get("x-goog-api-key"), body=body))
                if fake.status != 200:
                    out = json.dumps(dict(error=dict(code=fake.status, message="scripted failure"))).encode()
                else:
                    out = json.dumps(dict(candidates=[dict(content=dict(parts=[dict(text=fake.reply)]))])).encode()
                self.send_response(fake.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(out)))
                self.end_headers()
                self.wfile.write(out)

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}/v1beta"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def say(self, answer, state="supported", citations=()):
        self.status = 200
        self.reply = json.dumps(dict(answer=answer, state=state, citations=list(citations)))


def start(env):
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        httpd = server.serve(FRONTEND, "127.0.0.1", 0)
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def req(base, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    h = {"Content-Type": "application/json"} if data else {}
    h.update(headers or {})
    r = urllib.request.Request(base + path, data=data, headers=h)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


class NoKey(unittest.TestCase):
    def test_without_key_ask_is_503_and_health_says_off(self):
        httpd, base = start({"GEMINI_API_KEY": ""})
        try:
            _, h = req(base, "/api/health")
            self.assertFalse(h["assistant"]["ready"])
            code, j = req(base, "/api/ask", dict(question="Is there lunar data?"))
            self.assertEqual(code, 503)
            self.assertIn("GEMINI_API_KEY", j["reason"])
        finally:
            httpd.shutdown()


class WithFakeGemini(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = FakeGemini()
        cls.httpd, cls.base = start({"GEMINI_API_KEY": "test-key-123", "GEMINI_API_BASE": cls.g.base,
                                     "GEMINI_MODEL": "gemini-test"})

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.g.httpd.shutdown()

    def setUp(self):
        self.httpd.state.ask_hits.clear()   # each test starts with a fresh rate-limit window

    def ask(self, body, ip):
        return req(self.base, "/api/ask", body, {"X-Forwarded-For": ip})

    def test_health_reports_ready_model(self):
        _, h = req(self.base, "/api/health")
        self.assertEqual(h["assistant"], dict(ready=True, provider="Google Gemini", model="gemini-test", reason=None))

    def test_request_sent_to_gemini_is_grounded(self):
        self.g.say("I-1 spread at 0.18 cm/s.", "supported", [dict(source_id="OLSON-2023-T1", location="Table 1, row 1")])
        code, j = self.ask(dict(question="What was I-1's spread rate?", scenario=dict(o2_pct=30),
                                history=[dict(role="user", text="hi"), dict(role="assistant", text="Hello")]), "10.0.0.1")
        self.assertEqual(code, 200, j)
        sent = self.g.requests[-1]
        self.assertEqual(sent["path"], "/v1beta/models/gemini-test:generateContent")
        self.assertEqual(sent["key"], "test-key-123")
        system = sent["body"]["system_instruction"]["parts"][0]["text"]
        self.assertIn("Answer ONLY from CONTEXT", system)
        self.assertIn("VALIDATION_NOT_SUPPORTED", system)
        self.assertIn('"record_id":"I-1"', system)          # Olson Table 1 is in the context
        self.assertIn("REAL_DATA_PIPELINE_STATUS.md", system)
        self.assertEqual([c["role"] for c in sent["body"]["contents"]], ["user", "model", "user"])
        self.assertIn("What was I-1's spread rate?", sent["body"]["contents"][-1]["parts"][0]["text"])
        self.assertEqual(sent["body"]["generationConfig"]["responseMimeType"], "application/json")

    def test_answer_is_labelled_and_citations_checked(self):
        self.g.say("I-1 spread at 0.18 cm/s.", "supported",
                   [dict(source_id="OLSON-2023-T1", location="Table 1, row 1"), dict(source_id="MADE-UP-PAPER", location="p1")])
        code, j = self.ask(dict(question="I-1 rate?"), "10.0.0.2")
        self.assertEqual(code, 200)
        self.assertTrue(j["ai_generated"])
        self.assertEqual(j["provider"], "Google Gemini")
        self.assertEqual(j["state"], "supported")
        self.assertEqual(j["citations"], [dict(source_id="OLSON-2023-T1", location="Table 1, row 1")])
        self.assertEqual(j["unverified_numbers"], [])

    def test_invented_numbers_are_flagged(self):
        self.g.say("At lunar gravity the rate would be about 0.73 cm/s.", "limited", [])
        code, j = self.ask(dict(question="Rate on the Moon?"), "10.0.0.3")
        self.assertEqual(code, 200)
        self.assertIn("0.73", j["unverified_numbers"])

    def test_numbers_from_question_are_not_flagged(self):
        self.g.say("No indexed run is at 31.5% oxygen and 68 kPa.", "insufficient", [dict(source_id="brief", location="")])
        _, j = self.ask(dict(question="Anything at 31.5% oxygen and 68 kPa?"), "10.0.0.4")
        self.assertEqual(j["unverified_numbers"], [])

    def test_bad_state_and_non_json_reply_are_handled(self):
        self.g.say("Something.", "certain", [])
        _, j = self.ask(dict(question="x?"), "10.0.0.5")
        self.assertEqual(j["state"], "limited")
        self.g.status, self.g.reply = 200, "plain text, not JSON"
        code, j = self.ask(dict(question="y?"), "10.0.0.5")
        self.assertEqual(code, 200)
        self.assertEqual(j["answer"], "plain text, not JSON")
        self.assertEqual(j["citations"], [])

    def test_input_validation(self):
        for body in [dict(), dict(question=""), dict(question="x" * 601), dict(question="ok", history="bad"),
                     dict(question="ok", scenario=[1])]:
            code, j = self.ask(body, "10.0.0.6")
            self.assertEqual(code, 400, body)
            self.assertEqual(j["status"], "INPUT_ERROR")

    def test_upstream_errors_become_clear_messages(self):
        self.g.status = 404
        code, j = self.ask(dict(question="a?"), "10.0.0.7")
        self.assertEqual(code, 502)
        self.assertIn("GEMINI_MODEL", j["error"])
        self.g.status = 429
        code, j = self.ask(dict(question="b?"), "10.0.0.7")
        self.assertEqual(code, 502)
        self.assertIn("busy", j["error"])
        self.g.status = 200

    def test_per_visitor_rate_limit(self):
        self.g.say("ok", "supported", [])
        codes = [self.ask(dict(question=f"q{i}?"), "10.9.9.9")[0] for i in range(assistant_limit() + 1)]
        self.assertEqual(codes[:-1], [200] * assistant_limit())
        self.assertEqual(codes[-1], 429)
        code, _ = self.ask(dict(question="other visitor?"), "10.9.9.8")
        self.assertEqual(code, 200)


def assistant_limit():
    return server.ASK_RATE_IP


class ContextUnit(unittest.TestCase):
    def test_context_has_records_sources_and_no_key(self):
        a = assistant.Assistant(FRONTEND, api_key="secret-should-not-appear")
        self.assertIn("OLSON-2023-T1", a.source_ids)
        self.assertIn("saffire_i_v", a.source_ids)
        self.assertNotIn("secret-should-not-appear", a.context)
        self.assertIn(0.18, a.context_numbers)
