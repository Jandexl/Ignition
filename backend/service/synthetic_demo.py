"""Synthetic demonstration model for the 1gnition API.

Wraps the saved, project-generated bundle
    backend/ignis-ml/outputs/SYNTHETIC_DEMO_MODEL.joblib
using only the package's own functions: ignis_ml.prediction.load and
ignis_ml.prediction.predict. Nothing here fits, refits, edits or clips a model.

What the model is: a geometry ridge regression fitted to INVENTED data
(ignis_ml/fixtures.py, seed 20261114: 12 invented runs x 6 observations of a
"synthetic_fabric"). Its job is to show the software path end to end. It is not
trained on NASA data, says nothing about real flames, and every response it
produces is labelled SYNTHETIC_DEMO_ONLY.

Safety rules enforced here:
  1. joblib/pickle can run code, so the file must match the SHA-256 recorded in
     backend/ignis-ml/MANIFEST.sha256 before it is loaded.
  2. The loaded object must be an ignis_ml Bundle with synthetic=True.
  3. Self-test at start-up: the bundle must reproduce the saved reference
     prediction (outputs/supported_SYNTHETIC.json) to 1e-9 cm/s. This catches a
     library-version change that would silently alter results. If any check
     fails, the demo is disabled and the API answers 503 with the reason.
  4. Every response is validated against response.schema.json and must carry
     synthetic=true and validation_status=SYNTHETIC_DEMO_ONLY, or it is refused.
"""
import hashlib
import json
import warnings
from pathlib import Path

import jsonschema

HERE = Path(__file__).resolve().parent
PKG = HERE.parent / "ignis-ml"
MODEL_REL = "outputs/SYNTHETIC_DEMO_MODEL.joblib"
LABEL = "SYNTHETIC MODEL - INVENTED DATA, NOT NASA DATA, NOT A FIRE-SAFETY PREDICTION"
NUMERIC = (("flow_velocity_cm_s", "Airflow", "cm/s"), ("oxygen_percent", "Oxygen", "%"),
           ("pressure_kpa", "Pressure", "kPa"), ("sample_width_cm", "Sample width", "cm"))
FIXED_NUMERIC = (("sample_length_cm", "cm"), ("sample_thickness_mm", "mm"), ("duct_height_cm", "cm"))
FIXED_TEXT = ("material", "gravity_regime", "combustion_regime", "geometry_definition_id")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_hash(pkg=PKG, rel=MODEL_REL):
    for line in (pkg / "MANIFEST.sha256").read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == rel:
            return parts[0]
    raise ValueError(f"{rel} is not listed in MANIFEST.sha256")


class SyntheticDemo:
    def __init__(self, pkg=PKG):
        self.pkg = Path(pkg)
        self.path = self.pkg / MODEL_REL
        self.ready, self.reason, self.bundle, self.self_test = False, None, None, None
        self.response_schema = json.loads((self.pkg / "docs" / "response.schema.json").read_text())
        try:
            self._load()
        except Exception as e:  # any failure disables the demo; it never falls back to a guess
            self.ready, self.reason, self.bundle = False, f"{type(e).__name__}: {e}", None

    # ---- loading
    def _load(self):
        from ignis_ml.prediction import Bundle, load, predict
        want, got = manifest_hash(self.pkg), sha256(self.path)
        if got != want:
            raise ValueError(f"model file hash {got[:12]} does not match MANIFEST.sha256 {want[:12]}; refusing to unpickle")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            bundle = load(self.path)
        if not isinstance(bundle, Bundle) or bundle.synthetic is not True:
            raise ValueError("bundle is not flagged synthetic; refusing to serve it as a demo")
        ref_in = json.loads((self.pkg / "outputs" / "scenario_supported_SYNTHETIC.json").read_text())
        ref_out = json.loads((self.pkg / "outputs" / "supported_SYNTHETIC.json").read_text())
        r = predict(ref_in, bundle)
        diff = abs((r["predicted_flame_spread_rate_cm_s"] or -1) - ref_out["predicted_flame_spread_rate_cm_s"])
        if r["status"] != "SUPPORTED" or diff > 1e-9:
            raise ValueError(f"self-test failed: reference prediction differs by {diff:g} cm/s")
        self.bundle, self.ready = bundle, True
        self.self_test = dict(passed=True, reference_cm_s=ref_out["predicted_flame_spread_rate_cm_s"],
                              reproduced_cm_s=r["predicted_flame_spread_rate_cm_s"], abs_diff_cm_s=diff,
                              load_warnings=sorted({type(w.message).__name__ for w in caught}))

    # ---- public
    def status(self):
        return dict(ready=self.ready, reason=self.reason, label=LABEL)

    def domain(self):
        """Inputs the model needs and the region of invented data it has seen."""
        if not self.ready:
            return None
        t, b = self.bundle.training, self.bundle
        perf = b.evaluation["metrics"][b.model_name]
        runtime = {}
        try:
            import sklearn
            runtime["running_with_scikit_learn"] = sklearn.__version__
            rv = json.loads((self.pkg / "outputs" / "runtime_versions.json").read_text())
            runtime["saved_with_scikit_learn"] = rv["packages"]["scikit-learn"]
        except Exception:
            pass
        return dict(
            label=LABEL, data_origin="synthetic", not_nasa_data=True,
            validation_status="SYNTHETIC_DEMO_ONLY", model_type=b.model_name,
            model_file=MODEL_REL, model_sha256=sha256(self.path),
            generator="ignis_ml/fixtures.py, seed 20261114 (invented numbers, not a combustion model)",
            training=dict(rows=int(len(t)), independent_groups=int(t.dependency_group_id.nunique()),
                          source_id=sorted(t.source_id.unique().tolist())),
            inputs={k: dict(label=lab, unit=u, min=float(t[k].min()), max=float(t[k].max()),
                            observed=sorted(float(v) for v in t[k].unique()))
                    for k, lab, u in NUMERIC},
            flow_direction=sorted(t.flow_direction.unique().tolist()),
            fixed={**{k: dict(value=float(t[k].iloc[0]), unit=u) for k, u in FIXED_NUMERIC},
                   **{k: dict(value=str(t[k].iloc[0])) for k in FIXED_TEXT},
                   "geometry_status": dict(value="synthetic")},
            max_domain_distance=b.config.max_domain_distance,
            performance_on_invented_holdouts=dict(
                mae_cm_s=perf["mae_cm_s"], rmse_cm_s=perf["rmse_cm_s"],
                n_test_observations=perf["n_test_observations"],
                n_independent_test_groups=perf["n_independent_test_groups"],
                note="Leave-one-invented-group-out error on invented data. Not an accuracy claim for NASA flights."),
            limitations=b.evaluation["limitations"] + [
                "SYNTHETIC demonstration: no NASA accuracy or spacecraft-safety claim.",
                "The generator programmed a linear rule; the model recovering it shows the code works, not physics."],
            self_test=self.self_test, runtime=runtime)

    def scenario(self, body):
        """Complete scenario from the five user inputs plus the model's fixed synthetic fields."""
        if not isinstance(body, dict):
            raise ValueError("Send a JSON object")
        allowed = {k for k, _, _ in NUMERIC} | {"flow_direction"}
        extra = set(body) - allowed
        if extra:
            raise ValueError(f"Only {sorted(allowed)} can be set; the rest are fixed by the synthetic model. Unexpected: {sorted(extra)}")
        missing = sorted(allowed - set(body))
        if missing:
            raise ValueError(f"Missing input(s): {missing}")
        for k, _, _ in NUMERIC:
            v = body[k]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v or v in (float("inf"), float("-inf")):
                raise ValueError(f"{k} must be a finite number")
        if body["flow_direction"] not in ("concurrent", "opposed"):
            raise ValueError("flow_direction must be 'concurrent' or 'opposed'")
        t = self.bundle.training
        s = {k: float(t[k].iloc[0]) for k, _ in FIXED_NUMERIC}
        s.update({k: str(t[k].iloc[0]) for k in FIXED_TEXT}, geometry_status="synthetic")
        s.update(body)
        return s

    def run(self, body):
        from ignis_ml.prediction import predict
        scenario = self.scenario(body)
        resp = predict(scenario, self.bundle)
        jsonschema.validate(resp, self.response_schema)
        if resp["synthetic"] is not True or resp["validation_status"] != "SYNTHETIC_DEMO_ONLY":
            raise RuntimeError("Synthetic demo produced a response not labelled synthetic; refused")
        return dict(label=LABEL, data_origin="synthetic", not_nasa_data=True, scenario=scenario, result=resp)
