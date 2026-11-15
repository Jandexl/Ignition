"""Conservative readiness validation, separate from data exploration."""
import numpy as np
import pandas as pd
from .schema import FIELDS, UNITS, CONDITIONS, GEOMETRY, CATEGORIES, TARGET


def validate(df, manifest, geometry=(), synthetic=False):
    issues = []
    def add(code, message, mask=None, severity='error'):
        rows = [] if mask is None else df.index[mask].astype(str).tolist()
        issues.append(dict(code=code, severity=severity, message=message, rows=rows))
    required = [c for c, (_, _, missing) in FIELDS.items() if missing == 'never'] + list(geometry)
    if geometry:
        required += ['geometry_status', 'geometry_definition_id']
    for c in required:
        if c not in df:
            add('MISSING_COLUMN', f'Required column {c!r} is absent.')
        else:
            missing = df[c].isna() | df[c].astype(str).str.strip().eq('')
            if missing.any(): add('MISSING_VALUE', f'{c}: missing values block reviewed evaluation.', missing)
    if df.empty: add('EMPTY', 'No usable observations.')
    for flag in ('approved_for_ml', 'independent_run_verified'):
        if flag in df:
            permitted = df[flag].map(lambda v: v is True or isinstance(v, np.bool_) and bool(v))
            if (~permitted).any(): add('AUDIT_VETO', f'{flag} is not explicitly true in supplied audit.', ~permitted)
    if 'observation_id' in df and df.observation_id.duplicated().any():
        add('DUPLICATE_ID', 'Repeated observation IDs.', df.observation_id.duplicated(False))
    if df.duplicated().any(): add('DUPLICATE_ROW', 'Exact duplicate rows.', df.duplicated(keep=False))
    for c in UNITS:
        if c not in df: continue
        populated = df[c].notna()
        v = pd.to_numeric(df[c], errors='coerce')
        bad = populated & (~np.isfinite(v) | (v < 0))
        if c in GEOMETRY + ('pressure_kpa',): bad |= populated & (v <= 0)
        if c == 'oxygen_percent': bad |= populated & (v > 100)
        if bad.any(): add('INVALID_NUMERIC', f'{c}: must be finite, physical numeric values in {UNITS[c]}.', bad)
        unit_col = c + '__unit'
        if unit_col in df and (~df[unit_col].eq(UNITS[c])).any():
            add('UNIT_MISMATCH', f'{unit_col} disagrees with canonical unit {UNITS[c]}.', ~df[unit_col].eq(UNITS[c]))
    expected = {'outcome_type': ['flame_spread_rate'], 'outcome_unit': ['cm/s'],
                'flow_direction': ['concurrent', 'opposed'],
                'data_origin': ['synthetic'] if synthetic else ['experimental'],
                'verification_status': ['synthetic'] if synthetic else ['verified'],
                'grouping_status': ['synthetic'] if synthetic else ['verified'],
                'measurement_status': ['synthetic'] if synthetic else ['verified_numeric', 'reviewed_digitized']}
    if geometry: expected['geometry_status'] = ['synthetic'] if synthetic else ['verified']
    for c, allowed in expected.items():
        if c in df and (~df[c].isin(allowed)).any():
            add('UNAPPROVED_' + c.upper(), f'{c} must be one of {allowed}.', ~df[c].isin(allowed))
    if geometry and 'geometry_definition_id' in df and df.geometry_definition_id.nunique() != 1:
        add('GEOMETRY_DEFINITIONS', 'Geometry requires one consistent reviewed definition ID per cohort.')
    for c in CATEGORIES:
        if c not in df: continue
        nonnull = df[c].dropna().astype(str)
        mapping = pd.DataFrame({'original': nonnull, 'normalized': nonnull.str.strip().str.casefold()})
        if (mapping.groupby('normalized').original.nunique() > 1).any() or (nonnull != nonnull.str.strip()).any():
            add('CONFLICTING_LABELS', f'{c}: inconsistent whitespace/case; resolve with reviewed label mapping.')
    for c in ('gravity_regime', 'combustion_regime'):
        if c in df and df[c].nunique() > 1:
            add('INCOMPATIBLE_REGIMES', f'Select one scientifically comparable {c}.')
    run_cols = ['investigation_id', 'campaign_id', 'run_id']
    if all(c in df for c in run_cols + ['dependency_group_id']):
        if (df.groupby(run_cols, dropna=False).dependency_group_id.nunique() > 1).any():
            add('SPLIT_RUN', 'One run maps to multiple dependency groups; leakage risk.')
    if df.get('measurement_status', pd.Series(dtype=str)).eq('reviewed_digitized').fillna(False).any():
        add('DIGITIZATION', 'Digitization uncertainty is separate from model error; review sensitivity.', severity='warning')
    if 'material' in df and df.material.nunique() > 1:
        add('MATERIAL_COMPARABILITY', 'Multiple materials require explicit scientific comparability review.', severity='warning')
    for c in GEOMETRY:
        if c not in df or df[c].isna().any():
            add('UNKNOWN_GEOMETRY', f'{c} unavailable in some rows; excluded unless verified and complete.', severity='warning')
    if manifest is None or not {'source_id', 'title', 'url', 'verification_status'}.issubset(manifest.columns):
        add('SOURCE_MANIFEST', 'Manifest needs source_id, title, url and verification_status.')
    else:
        if manifest.source_id.isna().any() or manifest.source_id.duplicated().any():
            add('SOURCE_ID_CONFLICT', 'Manifest source IDs must be nonmissing and unique.')
        if 'source_id' in df:
            allowed = 'synthetic' if synthetic else 'verified'
            good = manifest.verification_status.eq(allowed)
            for c in ['title', 'url']:
                good &= manifest[c].notna() & manifest[c].astype(str).str.strip().ne('')
            missing = ~df.source_id.isin(manifest.loc[good, 'source_id'])
            if missing.any(): add('UNRESOLVED_SOURCE', 'Observation source is missing or unverified in manifest.', missing)
    return {'status': 'INVALID' if any(x['severity'] == 'error' for x in issues) else 'READY_FOR_EVALUATION',
            'n_observations': len(df), 'issues': issues,
            'note': 'Readiness is not scientific validation or proof of independence.'}
