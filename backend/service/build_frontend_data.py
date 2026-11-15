#!/usr/bin/env python3
"""Rebuild the frontend's science data from the science/ML package.

    python3 backend/build_frontend_data.py --frontend ../frontend
    python3 backend/build_frontend_data.py --frontend ../frontend --rerun-synthetic

Steps
 1. Re-export scientific_comparisons.json with ignis_ml.science.export_evidence
    from ignis-ml/data/revision (the reviewed Olson Table 1 package).
 2. Copy the synthetic factorial verification results (optionally re-running the
    seeded verification script first).
 3. Build evidence_catalog.json: every evidence item tagged with evidence_class.
 4. Run the data acceptance checks (handoff section 9). Any failure stops the build.
 5. Write build_manifest.json (input/output hashes, package version, check results)
    and rebuild data/seed.js so the site also works when opened from disk.

Nothing here fits a model or writes a prediction.
"""
import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent          # backend/
PKG = ROOT / "ignis-ml"
sys.path.insert(0, str(PKG / "src"))
sys.path.insert(0, str(HERE))

import evidence  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frontend", required=True, help="path to the static site (folder containing index.html)")
    ap.add_argument("--rerun-synthetic", action="store_true", help="re-run scripts/verify_factorial_synthetic.py first")
    ap.add_argument("--closeout", default=str(ROOT.parent / "research" / "closeout_kit" / "data"),
                    help="science team's closeout kit data folder (source_conflicts, brand_copy, science_project_status)")
    a = ap.parse_args(argv)
    fe = Path(a.frontend).resolve()
    data = fe / "data"
    if not (fe / "index.html").exists():
        sys.exit(f"{fe} does not look like the frontend (no index.html)")

    from ignis_ml import __version__
    from ignis_ml.science import export_evidence

    rev = PKG / "data" / "revision"
    sci_out = data / "scientific_comparisons.json"
    export_evidence(rev, sci_out)
    print(f"[1/5] scientific_comparisons.json exported from {rev.relative_to(ROOT)}")

    syn_src = PKG / "outputs" / "synthetic_factorial_verification" / "synthetic_verification_results.json"
    if a.rerun_synthetic:
        subprocess.run([sys.executable, str(PKG / "scripts" / "verify_factorial_synthetic.py")], cwd=PKG, check=True)
    syn = evidence.load_json(syn_src)
    write(data / "synthetic_verification_results.json", syn)
    print("[2/5] synthetic_verification_results.json copied (SYNTHETIC, not NASA data)")

    ev = evidence.load_json(PKG / "outputs" / "synthetic_evaluation.json")
    if ev.get("synthetic") is not True:
        sys.exit("synthetic_evaluation.json is not flagged synthetic; refusing to publish its metrics")
    bench = dict(evidence_class="synthetic", synthetic=True, is_nasa_data=False,
                 label="SOFTWARE BENCHMARK ON SYNTHETIC DATA, NOT NASA ACCURACY",
                 note="72 invented observations in 12 invented groups. The generator includes a width effect on purpose, so the geometry-aware model is expected to win.",
                 models={k: dict(mae_cm_s=v["mae_cm_s"], rmse_cm_s=v["rmse_cm_s"], features=v["features"],
                                 n_test_observations=v["n_test_observations"], n_independent_test_groups=v["n_independent_test_groups"])
                         for k, v in ev["metrics"].items()})
    write(data / "synthetic_model_benchmark.json", bench)
    kit = Path(a.closeout)
    for n in ["source_conflicts.json", "brand_copy.json", "science_project_status.json"]:
        if not (kit / n).exists():
            sys.exit(f"missing {kit / n}")
        write(data / n, evidence.load_json(kit / n))
    if evidence.load_json(kit / "scientific_comparisons.json") != evidence.load_json(sci_out):
        sys.exit("closeout kit scientific_comparisons.json differs from the package export; reconcile before publishing")
    print("[2b] source_conflicts, brand_copy, science_project_status copied from the closeout kit (kit science JSON == export)")
    sci = evidence.load_json(sci_out)
    runs = evidence.load_json(data / "runs.json")
    srs = evidence.load_json(data / "spread_rates.json")
    cat = evidence.build_catalog(sci, syn, runs, srs, evidence.load_json(data / "source_conflicts.json"))
    write(data / "evidence_catalog.json", cat)
    counts = {}
    for i in cat:
        counts[i["evidence_class"]] = counts.get(i["evidence_class"], 0) + 1
    print(f"[3/5] evidence_catalog.json: {len(cat)} items {counts}")

    checks = evidence.acceptance_checks(sci, syn) + evidence.conflict_checks(sci, evidence.load_json(data / "source_conflicts.json"), evidence.load_json(data / "brand_copy.json"))
    sources = {s["id"] for s in evidence.load_json(data / "sources.json")}
    for i in cat:
        if i["source_id"] is not None:
            checks.append(dict(check=f"Source {i['source_id']} for {i['id']} is in sources.json",
                               passed=i["source_id"] in sources, detail=""))
    bad = [c for c in checks if not c["passed"]]
    for c in checks:
        if not c["check"].startswith("Source "):
            print(("  PASS " if c["passed"] else "  FAIL ") + c["check"])
    print(f"[4/5] {len(checks) - len(bad)} of {len(checks)} acceptance checks passed")
    if bad:
        for c in bad:
            print("  FAIL", c["check"], c["detail"])
        sys.exit(1)

    manifest = dict(
        built_at=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        ignis_ml_version=__version__,
        inputs={str(p.relative_to(ROOT)): sha(p) for p in sorted(rev.glob("*.csv"))},
        outputs={n: sha(data / n) for n in ["scientific_comparisons.json", "synthetic_verification_results.json", "synthetic_model_benchmark.json", "evidence_catalog.json", "source_conflicts.json", "brand_copy.json", "science_project_status.json"]},
        evidence_counts=counts,
        checks_passed=len(checks), checks_failed=0,
        prediction_status=sci["prediction_status"], prediction_cm_s=sci["prediction_cm_s"],
        note="Static export. No model was fitted and no NASA prediction was produced.")
    write(data / "build_manifest.json", manifest)
    seed = fe / "tools" / "make_seed.py"
    if seed.exists():
        subprocess.run([sys.executable, str(seed)], check=True)
    print("[5/5] build_manifest.json written, seed.js rebuilt")


if __name__ == "__main__":
    main()
