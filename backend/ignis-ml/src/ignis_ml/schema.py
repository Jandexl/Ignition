"""Canonical contract and lossless, explicitly provisional current-file adapters."""
import numpy as np
import pandas as pd

TARGET = 'flame_spread_rate_cm_s'
CONDITIONS = ('flow_velocity_cm_s', 'oxygen_percent', 'pressure_kpa')
GEOMETRY = ('sample_width_cm', 'sample_length_cm', 'sample_thickness_mm', 'duct_height_cm')
CATEGORIES = ('material', 'flow_direction', 'gravity_regime', 'combustion_regime')
UNITS = dict(zip(CONDITIONS + GEOMETRY + (TARGET,),
                 ('cm/s', '%', 'kPa', 'cm', 'cm', 'mm', 'cm', 'cm/s')))
# Role, meaning, missing policy. Every scientific field must be reviewed before evaluation.
FIELDS = {
 'observation_id': ('identifier', 'Unique measurement record, not evidence of independence', 'never'),
 'investigation_id': ('metadata', 'Verified investigation identity; BASS and BASS-II stay distinct', 'never'),
 'campaign_id': ('group', 'Verified campaign identifier', 'never'),
 'run_id': ('group', 'Verified experimental run within investigation and campaign', 'never'),
 'dependency_group_id': ('group', 'Globally unique cluster covering repeats and all related runs', 'never'),
 'material': ('input', 'Reviewed canonical fuel specification, not a loose alias', 'never'),
 'flow_direction': ('input', 'Concurrent or opposed relative to spread', 'never'),
 'gravity_regime': ('domain', 'Reviewed gravity regime, such as microgravity', 'never'),
 'combustion_regime': ('domain', 'Reviewed outcome/regime definition such as steady_solid_spread', 'never'),
 'flow_velocity_cm_s': ('input', 'Nonnegative imposed flow speed magnitude', 'never'),
 'oxygen_percent': ('input', 'Oxygen mole/volume percentage, not mass percentage', 'never'),
 'pressure_kpa': ('input', 'Absolute total gas pressure', 'never'),
 'sample_width_cm': ('candidate input', 'Verified transverse specimen width', 'if not selected'),
 'sample_length_cm': ('candidate input', 'Verified specimen length along spread', 'if not selected'),
 'sample_thickness_mm': ('candidate input', 'Verified fuel thickness', 'if not selected'),
 'duct_height_cm': ('candidate input', 'Verified confinement height with consistent definition', 'if not selected'),
 TARGET: ('target', 'Measured flame-front displacement per elapsed time in the specified regime', 'never'),
 'outcome_type': ('metadata', 'Must be flame_spread_rate', 'never'),
 'outcome_unit': ('metadata', 'Must be cm/s after explicit conversion', 'never'),
 'measurement_status': ('metadata', 'verified_numeric, reviewed_digitized, or synthetic', 'never'),
 'verification_status': ('metadata', 'verified or synthetic; unreviewed blocks modeling', 'never'),
 'grouping_status': ('metadata', 'verified or synthetic; human review of dependency structure', 'never'),
 'geometry_status': ('metadata', 'verified or synthetic when geometry is selected', 'if unused'),
 'geometry_definition_id': ('metadata', 'Shared reviewed dimension-definition document', 'if unused'),
 'source_id': ('provenance', 'Foreign key to source manifest', 'never'),
 'source_location': ('provenance', 'Table, figure, file or extraction location', 'never'),
 'review_id': ('provenance', 'External scientific audit/review document reference', 'never'),
 'data_origin': ('metadata', 'experimental or synthetic; mixing is forbidden', 'never'),
}


def convert(values, from_unit, to_unit):
    """No inference from magnitude. A caller supplies both units; original data stays separate."""
    family = {'mm': ('length', .1), 'cm': ('length', 1), 'm': ('length', 100),
              'mm/s': ('speed', .1), 'cm/s': ('speed', 1), 'm/s': ('speed', 100),
              'Pa': ('pressure', .001), 'kPa': ('pressure', 1),
              'fraction': ('oxygen', 100), '%': ('oxygen', 1)}
    if from_unit not in family or to_unit not in family or family[from_unit][0] != family[to_unit][0]:
        raise ValueError(f'Incompatible or unknown units: {from_unit} -> {to_unit}')
    arr = pd.to_numeric(pd.Series(values), errors='raise').to_numpy(dtype=float)
    if not np.isfinite(arr).all():
        raise ValueError('Conversion requires finite numbers')
    return arr * family[from_unit][1] / family[to_unit][1]


def adapt_current(raw, kind):
    """Return a new dataframe; original columns retained as raw__*. Never approves evidence."""
    out = raw.copy(deep=True)
    for c in raw:
        out['raw__' + c] = raw[c]
    if kind == 'starter':
        for old, new in [('width_mm', 'sample_width_cm'), ('length_mm', 'sample_length_cm'),
                         ('duct_height_mm', 'duct_height_cm')]:
            out[new] = convert(raw[old], 'mm', 'cm')
        out['oxygen_percent'] = raw['oxygen_concentration_percent']
        # Deliberately do not put flame size into the spread-rate column.
    elif kind == 'candidate':
        out['campaign_id'] = raw['campaign']
        out['flow_velocity_cm_s'] = raw['flow_magnitude_cm_s_est']
        out['oxygen_percent'] = raw['oxygen_mol_percent']
        out[TARGET] = raw['flame_spread_rate_cm_s_est']
        out['outcome_type'] = 'flame_spread_rate'
        out['outcome_unit'] = 'cm/s'
    else:
        raise ValueError('kind must be starter or candidate')
    for c in FIELDS:
        if c not in out:
            out[c] = pd.NA
    out['data_origin'] = 'experimental'
    for c in ('verification_status', 'grouping_status', 'geometry_status'):
        out[c] = 'unreviewed'
    return out


def contract():
    return {k: {'role': role, 'meaning': meaning, 'units': UNITS.get(k),
                'missing': missing, 'requires_review': True,
                'leakage_risk': 'NEVER a predictor' if role not in ('input', 'candidate input') else
                    'Use only pre-outcome measurements; fit transformations inside each training fold'}
            for k, (role, meaning, missing) in FIELDS.items()}
