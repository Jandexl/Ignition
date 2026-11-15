"""1gnition backend: evidence adapter.

Maps the science package's outputs onto presentation records for the
frontend without changing any source value. Every record keeps its
original fields, units and source locator, and gains one discriminator,
`evidence_class`:

    published_numeric    a number printed in a published table (Olson Table 1, Urban Table 2)
    archive_claim        a value recorded in a NASA PSI archive table (PSI-99)
    digitized            a marker read off a published plot (Urban Figure 10)
    derived_comparison   arithmetic on two published numbers (the three comparison cases)
    proposed_experiment  a design that has not been run (the 2 x 2 factorial)
    synthetic            invented data used only to test software

Nothing here fits a model or produces a NASA prediction.
"""
import json
import math
from pathlib import Path

# Variables compared between two Olson Table 1 records, in the order the
# science package's comparability matrix uses.
COMPARE_VARS = ["material", "flow_direction", "flow_cm_s", "duct_full_height_cm", "duct_width_cm",
                "sample_length_cm", "sample_width_cm", "oxygen_vol_pct", "pressure_kpa"]
MEASURE_FIELDS = ["sample_width_cm", "sample_length_cm", "duct_full_height_cm", "flow_cm_s",
                  "oxygen_vol_pct", "pressure_kpa", "flame_length_cm", "pyrolysis_length_cm", "spread_cm_s"]


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _fmt(v):
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return f"{v:g}" if isinstance(v, (int, float)) else str(v)


def compare_records(sci, baseline_id, comparison_id):
    """Deterministic descriptive comparison of two Olson Table 1 records.

    Uses the same arithmetic as ignis_ml.science.export_evidence. When the pair
    is one of the three reviewed cases, the reviewed case is returned unchanged.
    """
    recs = {r["record_id"]: r for r in sci["table1_records"]}
    if baseline_id not in recs or comparison_id not in recs:
        raise KeyError("Unknown Table 1 record_id")
    if baseline_id == comparison_id:
        raise ValueError("Choose two different records")
    for case in sci["comparison_cases"]:
        if case["baseline"] == baseline_id and case["comparison"] == comparison_id:
            return dict(case, reviewed_case=True, evidence_class="derived_comparison")
    a, b = recs[baseline_id], recs[comparison_id]
    meas = {f: [a.get(f), b.get(f)] for f in MEASURE_FIELDS}
    ra, rb = a.get("spread_cm_s"), b.get("spread_cm_s")
    ratio = (rb / ra) if (isinstance(ra, (int, float)) and isinstance(rb, (int, float)) and ra > 0) else None
    rows = []
    for v in COMPARE_VARS:
        x, y = a.get(v), b.get(v)
        if x is None or y is None:
            status = "unknown_in_Table1"
        else:
            status = "same_in_Table1" if x == y else "different_in_Table1"
        rows.append(dict(comparison_a=baseline_id, comparison_b=comparison_id, variable=v, status=status,
                         reason=f"{_fmt(x) if x is not None else 'null'} vs {_fmt(y) if y is not None else 'null'}; Olson Table 1",
                         strength="descriptive"))
    if a.get("flight") != b.get("flight"):
        rows.append(dict(comparison_a=baseline_id, comparison_b=comparison_id, variable="flight",
                         status="different_in_Table1", reason=f"{a.get('flight')} vs {b.get('flight')}; Olson Table 1",
                         strength="descriptive"))
    warn = ("Not a reviewed comparison. Every changed variable below, plus relative humidity, specimen position "
            "and imaging/fit method (not Table 1 fields), could contribute to any difference.")
    if a.get("material") != b.get("material"):
        warn = "Different fuels. " + warn
    return dict(baseline=baseline_id, comparison=comparison_id, measurements=meas,
                difference_cm_s=round(rb - ra, 6) if ratio is not None else None,
                ratio=round(ratio, 6) if ratio is not None else None,
                percent_change=round(100 * (ratio - 1), 2) if ratio is not None else None,
                source_id=a["source_id"], source_locations=[a["source_locator"], b["source_locator"]],
                comparability=rows, confounding_warning=warn, interpretation="descriptive_only",
                reviewed_case=False, evidence_class="derived_comparison")


def build_catalog(sci, synthetic, runs, spread_rates, conflicts=None):
    # conflicts are provenance metadata about existing items, not new evidence, so they are not catalogued as items
    """Flat list of every evidence item the site can show, each tagged with evidence_class."""
    items = []
    for r in sci["table1_records"]:
        items.append(dict(id=f"OLSON-T1:{r['record_id']}", evidence_class="published_numeric",
                          source_scope="Olson et al. 2023, Table 1", record=r,
                          source_id=r["source_id"], source_location=r["source_locator"],
                          outcomes={"spread_cm_s": r["spread_cm_s"], "flame_length_cm": r["flame_length_cm"],
                                    "pyrolysis_length_cm": r["pyrolysis_length_cm"]}))
    for r in runs:
        items.append(dict(id=f"URBAN-T2:{r['id']}", evidence_class="published_numeric",
                          source_scope="Urban et al. 2021, ICES-2021-266 Table 2", record=r,
                          source_id=r["provenance"]["source_id"], source_location=r["provenance"]["location"],
                          outcomes={"steady_size_cm": r.get("steady_size_cm"), "max_size_cm": r.get("max_size_cm")}))
    for r in spread_rates:
        items.append(dict(id=f"SR:{r['id']}", evidence_class="published_numeric",
                          source_scope="Published average spread rate", record=r,
                          source_id=r["provenance"]["source_id"], source_location=r["provenance"]["location"],
                          outcomes={"rate_mm_s": r.get("rate_mm_s")}))
    alt = sci.get("alternative_source_claims", {})
    for r in alt.get("ignis_spread_rates_reviewed.csv", []):
        items.append(dict(id=f"FIG10:{r['observation_id']}", evidence_class="digitized",
                          source_scope="Urban et al. 2021, Figure 10 (digitized by the team)", record=r,
                          source_id=r["source_id"], source_location=r["source_location"],
                          outcomes={"spread_cm_s_redigitized": r.get("spread_cm_s_redigitized")},
                          counts_as_independent_run=False))
    for r in alt.get("ignis_psi99_rate_claims.csv", []):
        items.append(dict(id=f"PSI99:{r['observation_id']}", evidence_class="archive_claim",
                          source_scope="NASA PSI-99 experimental table", record=r,
                          source_id=r["source_id"], source_location=r["source_location"],
                          outcomes={"outcome_value_mm_s": r.get("outcome_value")},
                          counts_as_independent_run=False))
    for c in sci["comparison_cases"]:
        items.append(dict(id=f"CASE:{c['baseline']}~{c['comparison']}", evidence_class="derived_comparison",
                          source_scope="Arithmetic on two Olson Table 1 rows", record=c,
                          source_id=c["source_id"], source_location="; ".join(c["source_locations"])))
    f = sci["factorial_readiness"]
    items.append(dict(id="DESIGN:width-x-duct-height", evidence_class="proposed_experiment",
                      source_scope="Proposed by the 1gnition science team; not run", record=f,
                      source_id=None, source_location=None))
    if synthetic:
        for s in synthetic["scenarios"]:
            items.append(dict(id=f"SYN:{s['scenario']}", evidence_class="synthetic",
                              source_scope="Invented data for software verification. Not NASA data.",
                              record={k: v for k, v in s.items() if k != "analysis"},
                              source_id=None, source_location=None, is_nasa_data=False))
    return items


def acceptance_checks(sci, synthetic):
    """Spec section 9, data and science items that can be checked from the files alone."""
    res = []

    def check(name, ok, detail=""):
        res.append(dict(check=name, passed=bool(ok), detail=detail))

    recs = sci["table1_records"]
    mats = [r["material"] for r in recs]
    check("Exactly 8 Olson Table 1 records", len(recs) == 8, f"{len(recs)} records")
    check("7 SIBAL and 1 cotton", mats.count("SIBAL") == 7 and mats.count("Cotton") == 1, str(mats))
    check("No Table 1 record approved for ML", not any(r["approved_for_ml"] for r in recs))
    want = {("I-1", "II-5"): (0.03, 16.67, [4, 4]), ("III-1", "II-6"): (0.03, 13.04, [5, 5]),
            ("I-1", "IV-SIBAL"): (0.18, 100.0, [4, 8.5])}
    for (a, b), (d, p, lengths) in want.items():
        c = next((x for x in sci["comparison_cases"] if x["baseline"] == a and x["comparison"] == b), None)
        ok = c is not None and math.isclose(c["difference_cm_s"], d, abs_tol=1e-9) and \
            math.isclose(c["percent_change"], p, abs_tol=1e-9) and c["measurements"]["flame_length_cm"] == lengths
        check(f"Comparison {a} vs {b}: +{d} cm/s, +{p}%, lengths {lengths} cm", ok)
        if c:
            check(f"Comparison {a} vs {b} is descriptive only", c["interpretation"] == "descriptive_only")
    f = sci["factorial_readiness"]
    miss = f["missing_configuration"]
    check("Missing factorial cell is 5 cm wide x 30.5 cm full duct height",
          len(miss) == 1 and miss[0]["width_cm"] == 5.0 and miss[0]["full_duct_height_cm"] == 30.5)
    check("Hypothesis untested, no interaction statistic",
          f["hypothesis_status"] == "UNTESTED" and f["interaction_cm_s"] is None and f["interval_cm_s"] is None)
    check("NASA prediction disabled",
          sci["prediction_status"] == "VALIDATION_NOT_SUPPORTED" and sci["prediction_cm_s"] is None)
    alt = sci.get("alternative_source_claims", {})
    f10 = alt.get("ignis_spread_rates_reviewed.csv", [])
    psi = alt.get("ignis_psi99_rate_claims.csv", [])
    check("23 Figure 10 markers, none counted as runs", len(f10) == 23 and not any(r["count_as_additional_run"] for r in f10))
    check("2 PSI-99 archive claims, none counted as runs", len(psi) == 2 and not any(r["count_as_additional_run"] for r in psi))
    check("PSI-99 mm/s converts to Table 1 cm/s",
          all(math.isclose(p["outcome_value"] / 10, next(r["spread_cm_s"] for r in recs if r["record_id"] == p["table1_record_id"]), abs_tol=1e-9) for p in psi))
    if synthetic:
        flags = [synthetic.get(k) for k in ("is_nasa_data", "is_physics_simulation", "is_experimental_validation", "is_nasa_prediction_validation")]
        check("Synthetic file flags itself as not NASA data", flags == [False, False, False, False])
        check("Synthetic checks all pass", synthetic.get("all_checks_pass") is True)
        check("Synthetic file keeps NASA prediction disabled", synthetic.get("nasa_prediction_status") == "VALIDATION_NOT_SUPPORTED")
        check("Synthetic refusals all return null",
              all(v.get("interaction_cm_s") is None and v.get("interval_cm_s") is None for v in synthetic.get("refusal_tests", {}).values()))
    return res


def conflict_checks(sci, conflicts, brand):
    """Closeout-kit sidecars: conflicts stay unresolved/probable and agree with Table 1; brand copy is as approved."""
    res = []

    def check(name, ok, detail=""):
        res.append(dict(check=name, passed=bool(ok), detail=detail))

    recs = {r["record_id"]: r for r in sci["table1_records"]}
    cs = {c["conflict_id"]: c for c in conflicts.get("conflicts", [])}
    f = cs.get("SAFFIRE_III1_FLOW_PSI100_VS_OLSON")
    check("PSI-100 vs Olson airflow conflict present", f is not None)
    if f:
        vals = {c["source_id"]: c["value"] for c in f["claims"]}
        check("III-1 airflow conflict keeps both claims (Olson 25, PSI-100 30) and is unresolved",
              vals == {"OLSON-2023-T1": 25, "NASA-PSI-100": 30} and f["resolution_status"] == "unresolved")
        check("Olson claim in the conflict equals Table 1 III-1 flow_cm_s", vals.get("OLSON-2023-T1") == recs["III-1"]["flow_cm_s"])
    g = cs.get("SAFFIRE_IV1_IV_SIBAL_ALIAS")
    check("IV-SIBAL / IV-1 alias present", g is not None)
    if g:
        check("IV alias probable, not confirmed, not counted twice",
              g["match_status"] == "probable_not_confirmed" and g["count_as_additional_independent_run"] is False)
        olson = next(c for c in g["claims"] if c["source_id"] == "OLSON-2023-T1")
        check("IV alias Olson rate equals Table 1 IV-SIBAL spread_cm_s", olson["spread_rate_cm_s"] == recs["IV-SIBAL"]["spread_cm_s"])
    check("No conflict approved for ML", all(c.get("approved_for_ml") is False for c in cs.values()))
    check("Brand copy: hero lines as approved",
          brand.get("hero_line_1") == "ZERO GUESSING." and brand.get("hero_line_2") == "ZERO HIDDEN UNCERTAINTY." and brand.get("product_name_line") == "1gnition")
    check("Brand copy discloses a rule-based helper", "rule-based" in brand.get("assistant_disclosure", ""))
    return res


def table1_evidence_frame(sci):
    """Evidence metadata for ignis_ml.prediction.predict: source IDs only, never a number."""
    import pandas as pd
    rows = [dict(material=r["material"], flow_direction=r["flow_direction"], gravity_regime="microgravity",
                 combustion_regime="steady_solid_spread", source_id=r["source_id"], record_id=r["record_id"])
            for r in sci["table1_records"]]
    return pd.DataFrame(rows)
