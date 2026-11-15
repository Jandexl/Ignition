"""Evidence-domain checks; bounds are observed coverage, never safety thresholds."""
import numpy as np
import pandas as pd
from .schema import CONDITIONS, CATEGORIES, GEOMETRY


def check_domain(train, scenario, cfg):
    reasons = []
    numeric = list(CONDITIONS) + list(cfg.geometry)
    # Available geometry constrains predictions even if the selected baseline ignores it.
    numeric += [c for c in GEOMETRY if c not in numeric and c in train and train[c].notna().all()]
    cats = list(CATEGORIES)
    if cfg.geometry: cats += ['geometry_definition_id']
    values = {}
    for c in numeric:
        v = scenario.get(c)
        if isinstance(v, bool) or not isinstance(v, (int, float, np.number)) or not np.isfinite(v):
            reasons.append(f'Missing or invalid numerical input: {c}')
            continue
        values[c] = float(v)
        lo, hi = float(train[c].min()), float(train[c].max())
        if v < lo or v > hi: reasons.append(f'{c}={v:g} outside observed [{lo:g}, {hi:g}]')
    for c in cats:
        if scenario.get(c) not in set(train[c].dropna()): reasons.append(f'Unsupported or missing {c}: {scenario.get(c)}')
    if cfg.geometry and scenario.get('geometry_status') not in ('verified', 'synthetic'):
        reasons.append('Scenario geometry is not verified')
    if reasons: return reasons
    compatible = np.ones(len(train), dtype=bool)
    for c in cats: compatible &= train[c].eq(scenario[c]).to_numpy()
    if not compatible.any(): return ['Unobserved combination of material, direction, regime or geometry definition']
    # Require local support within the SAME categorical combination, not just marginal ranges.
    span = train[numeric].max() - train[numeric].min()
    denom = span.where(span > 0, 1).to_numpy(dtype=float)
    d = np.sqrt(np.mean(((train.loc[compatible, numeric].to_numpy(dtype=float) -
                          np.array([values[c] for c in numeric])) / denom)**2, axis=1))
    if d.min() > cfg.max_domain_distance:
        reasons.append(f'No nearby evidence: normalized distance {d.min():.3f} exceeds reviewed tolerance {cfg.max_domain_distance:g}')
    return reasons
