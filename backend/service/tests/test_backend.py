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

    def test_scenario_returns_original_measurement_and_geometry(self):
        code, result, _ = self.req("/api/scenario", self.SCENARIO)
        self.assertEqual(code, 200)
        matches = result["measurements"]["exact_matches"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["record"]["record_id"], "I-1")
        self.assertEqual(matches[0]["measured_flame_spread_rate_cm_s"], 0.18)
        self.assertEqual(matches[0]["measured_flame_spread_rate_mm_s"], 1.8)
        self.assertEqual(matches[0]["record"]["sample_width_cm"], 40.6)
        self.assertEqual(matches[0]["record"]["source_locator"], "Table 1, PDF p9, row 1")
        self.assertIsNone(result["prediction"]["predicted_flame_spread_rate_cm_s"])
        self.assertIn("sample_width_cm", result["measurements"]["omitted_geometry"])

    def test_scenario_all_eight_records_return_their_own_rates(self):
        sci = evidence.load_json(DATA / "scientific_comparisons.json")
        for row in sci["table1_records"]:
            query = dict(self.SCENARIO, material=row["material"], oxygen_percent=row["oxygen_vol_pct"],
                         pressure_kpa=row["pressure_kpa"], flow_velocity_cm_s=row["flow_cm_s"])
            code, result, _ = self.req("/api/scenario", query)
            self.assertEqual(code, 200)
            found = {m["record"]["record_id"]: m["measured_flame_spread_rate_cm_s"]
                     for m in result["measurements"]["exact_matches"]}
            self.assertEqual(found[row["record_id"]], row["spread_cm_s"])

    def test_scenario_nearby_record_exposes_differences(self):
        code, result, _ = self.req("/api/scenario", dict(self.SCENARIO, pressure_kpa=102.5))
        self.assertEqual(code, 200)
        measurements = result["measurements"]
        self.assertEqual(measurements["status"], "RELATED_MEASUREMENTS")
        self.assertEqual(measurements["exact_matches"], [])
        first = measurements["related_measurements"][0]
        differences = {d["condition"]: d for d in first["differing_conditions"]}
        self.assertEqual(differences["pressure_kpa"]["requested"], 102.5)
        self.assertEqual(differences["pressure_kpa"]["recorded"], 102)
        self.assertIsNone(result["prediction"]["predicted_flame_spread_rate_cm_s"])

    def test_scenario_regime_and_material_cannot_cross_match(self):
        for field, value in [("material", "PMMA"), ("flow_direction", "opposed"),
                             ("gravity_regime", "lunar"), ("combustion_regime", "gas_jet")]:
            code, result, _ = self.req("/api/scenario", dict(self.SCENARIO, **{field: value}))
            self.assertEqual(code, 200)
            self.assertEqual(result["measurements"]["status"], "NO_MATCH")
            self.assertEqual(result["measurements"]["exact_matches"], [])
            self.assertEqual(result["measurements"]["related_measurements"], [])

    def test_scenario_invalid_inputs_cannot_return_measurements(self):
        for change in [{"oxygen_percent": 150}, {"pressure_kpa": None},
                       {"flow_velocity_cm_s": float("nan")}, {"material": None}]:
            code, result, _ = self.req("/api/scenario", dict(self.SCENARIO, **change))
            self.assertEqual(code, 400)
            self.assertEqual(result["status"], "INPUT_ERROR")

    def test_scenario_geometry_and_unknown_thickness_are_not_ignored(self):
        query = dict(self.SCENARIO, sample_width_cm=5)
        _, result, _ = self.req("/api/scenario", query)
        self.assertEqual(result["measurements"]["exact_matches"], [])
        query = dict(self.SCENARIO, sample_width_cm=40.6, sample_length_cm=94, duct_height_cm=51)
        _, result, _ = self.req("/api/scenario", query)
        self.assertEqual(result["measurements"]["exact_matches"][0]["record"]["record_id"], "I-1")
        _, result, _ = self.req("/api/scenario", dict(query, sample_thickness_mm=1))
        self.assertEqual(result["measurements"]["exact_matches"], [])

    def test_scenario_multiple_matches_stay_separate(self):
        sci = evidence.load_json(DATA / "scientific_comparisons.json")
        second = dict(sci["table1_records"][0], record_id="INDEPENDENT-EXAMPLE", spread_cm_s=0.3,
                      sample_width_cm=12)
        sci["table1_records"].append(second)
        result = evidence.scenario_measurements(sci, self.SCENARIO)
        self.assertEqual(len(result["exact_matches"]), 2)
        self.assertEqual([r["measured_flame_spread_rate_cm_s"] for r in result["exact_matches"]],
                         [0.18, 0.3])

    # ---- synthetic demo model (backend/ignis-ml/outputs/SYNTHETIC_DEMO_MODEL.joblib)
    DEMO = dict(flow_velocity_cm_s=5, oxygen_percent=20, pressure_kpa=90, sample_width_cm=2, flow_direction="opposed")

    def test_synthetic_demo_ready_and_labelled(self):
        code, j, _ = self.req("/api/health")
        self.assertTrue(j["synthetic_demo"]["ready"], j["synthetic_demo"]["reason"])
        code, d, _ = self.req("/api/synthetic-demo/domain")
        self.assertEqual(code, 200)
        self.assertTrue(d["not_nasa_data"])
        self.assertEqual(d["validation_status"], "SYNTHETIC_DEMO_ONLY")
        self.assertEqual(d["training"]["source_id"], ["SYNTHETIC-GENERATOR"])
        self.assertEqual(d["inputs"]["oxygen_percent"]["min"], 20.0)
        self.assertEqual(d["inputs"]["oxygen_percent"]["max"], 23.0)
        self.assertTrue(d["self_test"]["passed"])

    def test_synthetic_demo_reproduces_saved_reference(self):
        ref = json.loads((HERE.parents[1] / "ignis-ml" / "outputs" / "supported_SYNTHETIC.json").read_text())
        code, j, _ = self.req("/api/synthetic-demo", self.DEMO)
        self.assertEqual(code, 200)
        r = j["result"]
        self.assertEqual(r["status"], "SUPPORTED")
        self.assertTrue(r["synthetic"])
        self.assertEqual(r["validation_status"], "SYNTHETIC_DEMO_ONLY")
        self.assertAlmostEqual(r["predicted_flame_spread_rate_cm_s"], ref["predicted_flame_spread_rate_cm_s"], places=12)
        self.assertTrue(j["not_nasa_data"])
        self.assertIn("NOT NASA", j["label"])

    def test_synthetic_demo_refuses_outside_domain(self):
        code, j, _ = self.req("/api/synthetic-demo", dict(self.DEMO, oxygen_percent=30, pressure_kpa=70.3))
        self.assertEqual(code, 200)
        r = j["result"]
        self.assertEqual(r["status"], "UNSUPPORTED")
        self.assertIsNone(r["predicted_flame_spread_rate_cm_s"])
        self.assertTrue(any("oxygen_percent=30" in w for w in r["out_of_domain_warnings"]))

    def test_synthetic_demo_rejects_real_material_and_bad_input(self):
        for body in [dict(self.DEMO, material="SIBAL"), dict(self.DEMO, oxygen_percent="21"),
                     dict(self.DEMO, flow_direction="up"), {"oxygen_percent": 21}]:
            code, j, _ = self.req("/api/synthetic-demo", body)
            self.assertEqual(code, 400, body)
            self.assertEqual(j["status"], "INPUT_ERROR")

    def test_nasa_predict_still_never_numeric(self):
        code, j, _ = self.req("/api/predict", dict(self.SCENARIO))
        self.assertIsNone(j["predicted_flame_spread_rate_cm_s"])
        self.assertFalse(j["synthetic"])

    def test_tampered_model_file_is_refused(self):
        import shutil, tempfile, synthetic_demo
        pkg = HERE.parents[1] / "ignis-ml"
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            for sub in ["outputs", "docs"]:
                shutil.copytree(pkg / sub, t / sub)
            shutil.copy(pkg / "MANIFEST.sha256", t / "MANIFEST.sha256")
            with open(t / "outputs" / "SYNTHETIC_DEMO_MODEL.joblib", "ab") as f:
                f.write(b"tamper")
            demo = synthetic_demo.SyntheticDemo(t)
            self.assertFalse(demo.ready)
            self.assertIn("does not match MANIFEST", demo.reason)

    def test_body_too_large(self):
        code, _, _ = self.req("/api/compare", {"baseline": "x" * 20000, "comparison": "y"})
        self.assertEqual(code, 413)


if __name__ == "__main__":
    unittest.main()
