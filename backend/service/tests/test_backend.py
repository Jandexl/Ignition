"""Backend tests: evidence adapter, acceptance checks and API server.

    IGNITION_FRONTEND=../frontend python3 -m unittest discover -s backend/tests -v
"""
import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
os.environ.setdefault("IGNITION_QUIET", "1")
import evidence  # noqa: E402
import server  # noqa: E402

FRONTEND = Path(os.environ.get("IGNITION_FRONTEND", HERE.parents[2] / "frontend")).resolve()
DATA = FRONTEND / "data"


class Adapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sci = evidence.load_json(DATA / "scientific_comparisons.json")
        cls.syn = evidence.load_json(DATA / "synthetic_verification_results.json")

    def test_acceptance_checks_all_pass(self):
        res = evidence.acceptance_checks(self.sci, self.syn)
        self.assertTrue(res)
        self.assertEqual([r["check"] for r in res if not r["passed"]], [])

    def test_closeout_conflicts_and_brand(self):
        res = evidence.conflict_checks(self.sci, evidence.load_json(DATA / "source_conflicts.json"), evidence.load_json(DATA / "brand_copy.json"))
        self.assertEqual(len(res), 9)
        self.assertEqual([r["check"] for r in res if not r["passed"]], [])

    def test_no_hardcoded_conflicts_in_frontend(self):
        js = (FRONTEND / "js" / "app.js").read_text()
        for needle in ["KNOWN_CONFLICTS", "URBAN_OF", "30 cm/s for Saffire-III"]:
            self.assertNotIn(needle, js)

    def test_reviewed_case_returned_unchanged(self):
        c = evidence.compare_records(self.sci, "I-1", "II-5")
        self.assertTrue(c["reviewed_case"])
        self.assertEqual(c["difference_cm_s"], 0.03)
        self.assertEqual(c["percent_change"], 16.67)
        self.assertEqual(c["measurements"]["flame_length_cm"], [4.0, 4.0])

    def test_adhoc_pair_matches_package_arithmetic(self):
        c = evidence.compare_records(self.sci, "II-5", "II-6")
        self.assertFalse(c["reviewed_case"])
        self.assertAlmostEqual(c["difference_cm_s"], 0.05)
        self.assertAlmostEqual(c["ratio"], round(0.26 / 0.21, 6))
        self.assertEqual(c["interpretation"], "descriptive_only")
        changed = {r["variable"] for r in c["comparability"] if r["status"] == "different_in_Table1"}
        self.assertEqual(changed, {"flow_cm_s"})

    def test_unknown_and_same_ids_refused(self):
        with self.assertRaises(KeyError):
            evidence.compare_records(self.sci, "I-1", "X-9")
        with self.assertRaises(ValueError):
            evidence.compare_records(self.sci, "I-1", "I-1")

    def test_null_stays_null(self):
        c = evidence.compare_records(self.sci, "BASS-NARROW", "BASS-WIDE")
        self.assertEqual(c["measurements"]["pyrolysis_length_cm"], [None, None])

    def test_cotton_pair_warns_about_fuel(self):
        c = evidence.compare_records(self.sci, "IV-SIBAL", "V-COTTON")
        self.assertTrue(c["confounding_warning"].startswith("Different fuels"))

    def test_catalog_classes_and_no_double_counting(self):
        cat = evidence.build_catalog(self.sci, self.syn, evidence.load_json(DATA / "runs.json"), evidence.load_json(DATA / "spread_rates.json"))
        classes = {i["evidence_class"] for i in cat}
        self.assertEqual(classes, {"published_numeric", "digitized", "archive_claim", "derived_comparison", "proposed_experiment", "synthetic"})
        self.assertTrue(all(i.get("counts_as_independent_run") is False for i in cat if i["evidence_class"] in ("digitized", "archive_claim")))
        self.assertTrue(all(i.get("is_nasa_data") is False for i in cat if i["evidence_class"] == "synthetic"))

    def test_frontend_data_matches_build_manifest(self):
        man = evidence.load_json(DATA / "build_manifest.json")
        import hashlib
        for name, digest in man["outputs"].items():
            self.assertEqual(hashlib.sha256((DATA / name).read_bytes()).hexdigest(), digest, name)
        self.assertIsNone(man["prediction_cm_s"])


class Api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.serve(FRONTEND, "127.0.0.1", 0)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        cls.t = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.t.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def req(self, path, body=None, ctype="application/json"):
        data = json.dumps(body).encode() if body is not None else None
        r = urllib.request.Request(self.base + path, data=data, headers={"Content-Type": ctype} if data else {})
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, json.loads(resp.read()), resp.headers
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read()), e.headers

    SCENARIO = dict(flow_velocity_cm_s=20, oxygen_percent=21.7, pressure_kpa=102, material="SIBAL",
                    flow_direction="concurrent", gravity_regime="microgravity", combustion_regime="steady_solid_spread")

    def test_health(self):
        code, j, h = self.req("/api/health")
        self.assertEqual(code, 200)
        self.assertEqual(j["prediction_status"], "VALIDATION_NOT_SUPPORTED")
        self.assertEqual(h["Access-Control-Allow-Origin"], "*")

    def test_collections_match_files(self):
        for n in ["runs", "sources", "scientific_comparisons", "evidence_catalog"]:
            code, j, _ = self.req(f"/api/{n}")
            self.assertEqual(code, 200)
            self.assertEqual(j, evidence.load_json(DATA / f"{n}.json"))

    def test_path_traversal_refused(self):
        code, _, _ = self.req("/api/..%2Fjs%2Fconfig")
        self.assertEqual(code, 404)

    def test_static_site_served(self):
        with urllib.request.urlopen(self.base + "/index.html") as r:
            self.assertIn(b"1gnition", r.read())

    def test_predict_matching_evidence_is_limited_and_null(self):
        code, j, _ = self.req("/api/predict", self.SCENARIO)
        self.assertEqual(code, 200)
        self.assertEqual(j["status"], "LIMITED_EVIDENCE")
        self.assertIsNone(j["predicted_flame_spread_rate_cm_s"])
        self.assertEqual(j["validation_status"], "VALIDATION_NOT_SUPPORTED")
        self.assertIn("OLSON-2023-T1", j["source_ids"])
        self.assertTrue(j["abstention_reasons"])

    def test_predict_unmatched_material_unsupported(self):
        code, j, _ = self.req("/api/predict", dict(self.SCENARIO, material="PMMA"))
        self.assertEqual(j["status"], "UNSUPPORTED")
        self.assertIsNone(j["predicted_flame_spread_rate_cm_s"])

    def test_predict_invalid_scenario_abstains(self):
        code, j, _ = self.req("/api/predict", dict(self.SCENARIO, oxygen_percent=150))
        self.assertEqual(j["status"], "UNSUPPORTED")
        self.assertIsNone(j["predicted_flame_spread_rate_cm_s"])
        self.assertTrue(j["abstention_reasons"][0].startswith("Invalid scenario"))

    def test_predict_wrong_content_type(self):
        code, j, _ = self.req("/api/predict", self.SCENARIO, ctype="text/plain")
        self.assertEqual(code, 400)

    def test_compare_endpoint(self):
        code, j, _ = self.req("/api/compare", {"baseline": "I-1", "comparison": "IV-SIBAL"})
        self.assertEqual(code, 200)
        self.assertEqual(j["percent_change"], 100.0)
        code, j, _ = self.req("/api/compare", {"baseline": "I-1", "comparison": "nope"})
        self.assertEqual(code, 400)

    def test_body_too_large(self):
        code, _, _ = self.req("/api/compare", {"baseline": "x" * 20000, "comparison": "y"})
        self.assertEqual(code, 413)


if __name__ == "__main__":
    unittest.main()
