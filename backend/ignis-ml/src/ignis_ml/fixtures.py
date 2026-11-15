"""Invented data for engineering only; generator is not a combustion model."""
import numpy as np
import pandas as pd
from .models import Config


def fixture():
    rng = np.random.default_rng(20261114)
    rows = []
    # Twelve independent invented runs; six observations in each run.
    for g in range(12):
        offset = rng.normal(0, .004)
        for j in range(6):
            flow = float(5 + 3*j + (g % 3))
            width = float(2 + 2*((g+j) % 4))
            oxygen = float(20 + ((g+2*j) % 4))
            pressure = float(90 + 5*((g+j) % 3))
            direction = 'concurrent' if j % 2 else 'opposed'
            rate = .06 + .007*flow + .012*width + .006*(oxygen-20) + .0004*(pressure-90)
            rate += .025*(direction == 'concurrent') + offset + rng.normal(0, .002)
            rows.append(dict(observation_id=f'SYN-{g:02}-{j}', investigation_id='SYNTHETIC-ONLY',
                campaign_id=f'SYN-C{g//4}', run_id=f'SYN-R{g}', dependency_group_id=f'SYN-G{g}',
                material='synthetic_fabric', flow_direction=direction, gravity_regime='synthetic_microgravity',
                combustion_regime='synthetic_steady_solid_spread', flow_velocity_cm_s=flow,
                oxygen_percent=oxygen, pressure_kpa=pressure, sample_width_cm=width, sample_length_cm=30.,
                sample_thickness_mm=.3, duct_height_cm=10., flame_spread_rate_cm_s=rate,
                outcome_type='flame_spread_rate', outcome_unit='cm/s', measurement_status='synthetic',
                verification_status='synthetic', grouping_status='synthetic', geometry_status='synthetic',
                geometry_definition_id='SYN-GEOMETRY-v1', source_id='SYNTHETIC-GENERATOR',
                source_location='fixtures.py, seed=20261114', review_id='SYNTHETIC-NOT-A-SCIENCE-REVIEW', data_origin='synthetic'))
    manifest = pd.DataFrame([dict(source_id='SYNTHETIC-GENERATOR', title='Invented software fixture',
                                  url='synthetic://ignis/fixtures.py', verification_status='synthetic')])
    return pd.DataFrame(rows), manifest


def demo_config():
    return Config(plan_id='SYN-PLAN-1', independence_review_id='SYN-GROUPS',
                  comparability_review_id='SYN-COMPARABILITY', geometry_rationale='Synthetic generator deliberately includes width; not a physical law.',
                  frozen_before_evaluation=True)


def approval_for(report, name='geometry_ridge'):
    return dict(reviewer='SYNTHETIC software test', review_reference='SYN-REVIEW',
                acceptance_rationale='Test only; no NASA approval', domain_rationale='Synthetic software coverage test',
                fingerprint=report['fingerprint'], model_name=name,
                evaluation_status=report['status'], selection_independent_of_test=True)


def scenario_from_row(row):
    from .schema import CONDITIONS, GEOMETRY, CATEGORIES
    return {k: row[k] for k in list(CONDITIONS + GEOMETRY + CATEGORIES) + ['geometry_definition_id', 'geometry_status']}
