"""Published comparisons and historical coverage; no estimator is fitted here."""
import argparse
import json
from pathlib import Path
import pandas as pd

from .prediction import write_json

CELLS = [(width, height) for width in (5., 40.6) for height in (30.5, 51.)]


def export_evidence(directory, output):
    directory, output = Path(directory), Path(output)
    table = pd.read_csv(directory / 'ignis_table1_rates.csv').set_index('record_id', verify_integrity=True)
    if len(table) != 8 or not table.approved_for_ml.eq(False).all():
        raise ValueError('Expected eight descriptive Table 1 records.')
    crosswalk = {}
    for name, key in [('ignis_spread_rates_reviewed.csv', 'table1_candidate'),
                      ('ignis_psi99_rate_claims.csv', 'table1_record_id')]:
        claims = pd.read_csv(directory / name)
        if not claims.count_as_additional_run.eq(False).all():
            raise ValueError('Review revised source identity before counting observations.')
        if not set(claims[key].dropna()).issubset(table.index):
            raise ValueError('Unknown Table 1 cross-reference')
        crosswalk[name] = json.loads(claims.to_json(orient='records'))
    matrix = pd.read_csv(directory / 'ignis_comparability_matrix.csv')
    cases = []
    for case in pd.read_csv(directory / 'ignis_comparison_cases.csv').itertuples():
        a, b = table.loc[case.baseline], table.loc[case.comparison]
        ratio = b.spread_cm_s / a.spread_cm_s
        fields = ['sample_width_cm','sample_length_cm','duct_full_height_cm','flow_cm_s',
                  'oxygen_vol_pct','pressure_kpa','flame_length_cm','pyrolysis_length_cm','spread_cm_s']
        cases.append(dict(baseline=case.baseline, comparison=case.comparison,
                          measurements={f:[float(a[f]),float(b[f])] for f in fields},
                          difference_cm_s=round(b.spread_cm_s-a.spread_cm_s, 6),
                          ratio=round(ratio, 6), percent_change=round(100*(ratio-1), 2),
                          source_id=a.source_id, source_locations=[a.source_locator,b.source_locator],
                          comparability=json.loads(matrix[(matrix.comparison_a == case.baseline) & (matrix.comparison_b == case.comparison)].to_json(orient='records')),
                          confounding_warning=case.limitations, interpretation='descriptive_only'))
    subset = table.query('material == "SIBAL" and flow_direction == "concurrent" and flow_cm_s == 20')
    cells = []
    for width,height in CELLS:
        matches = subset[(subset.sample_width_cm == width) & (subset.duct_full_height_cm == height)]
        cells.append(dict(width_cm=width, full_duct_height_cm=height, historical_ids=list(matches.index)))
    ready = dict(status='INCOMPLETE_HISTORICAL_DESIGN', cells=cells,
                 missing_configuration=[c for c in cells if not c['historical_ids']],
                 material='SIBAL', flow_direction='concurrent', flow_cm_s=20, gravity='microgravity',
                 hypothesis='Shallow minus deep mean spread rate is greater for wide than narrow specimens.',
                 hypothesis_status='UNTESTED', interaction_cm_s=None, interval_cm_s=None,
                 reason='Three historical cells have one record each and unequal controls. Filling the fourth cell alone would leave flight, atmosphere and specimen conditions confounded.',
                 protocol='Replicate all four cells using fresh independently ignited specimens, common controls and randomized blocks. See Scientific_Methodology.md.')
    payload = dict(schema_version='1.0', prediction_status='VALIDATION_NOT_SUPPORTED',
                   prediction_cm_s=None, table1_records=json.loads(table.reset_index().to_json(orient='records')),
                   comparison_cases=cases, factorial_readiness=ready, alternative_source_claims=crosswalk)
    write_json(output,payload)
    return payload


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', default='data/revision')
    parser.add_argument('--output', default='outputs/scientific_comparisons.json')
    args = parser.parse_args()
    export_evidence(args.data,args.output)
