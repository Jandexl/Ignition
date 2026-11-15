"""Estimate the interaction from future randomized complete blocks of independent burns."""
import numpy as np
import pandas as pd
from scipy.stats import t
from .science import CELLS


def analyze_burns(burns, *, design, controls_verified):
    """One row per independently ignited specimen. Equal weight per independent block."""
    def refuse(reason):
        return dict(status='ANALYSIS_NOT_SUPPORTED', reason=reason, interaction_cm_s=None, interval_cm_s=None)
    if design not in ('randomized_complete_blocks','randomized_height_sessions') or controls_verified is not True:
        return refuse('Requires a supported randomized design and verified common controls.')
    required = ['block_id','burn_id','specimen_id','width_cm','full_duct_height_cm','spread_cm_s','included','exclusion_reason']
    if not set(required).issubset(burns):
        return refuse('Missing future-experiment fields: ' + ', '.join(sorted(set(required)-set(burns))))
    for col in ['block_id','burn_id','specimen_id']:
        if burns[col].isna().any() or burns[col].astype(str).str.strip().eq('').any():
            return refuse('Missing identity: '+col)
    if burns.burn_id.duplicated().any() or burns.specimen_id.duplicated().any():
        return refuse('Repeated burn or specimen identity.')
    if not burns.included.map(lambda x:isinstance(x,(bool,np.bool_))).all():
        return refuse('Inclusion flags must be booleans.')
    excluded = burns.loc[~burns.included]
    if excluded.exclusion_reason.fillna('').astype(str).str.strip().eq('').any():
        return refuse('Every excluded burn needs a recorded reason.')
    data = burns.loc[burns.included].copy()
    for col in ['width_cm','full_duct_height_cm','spread_cm_s']:
        data[col]=pd.to_numeric(data[col], errors='coerce')
        if not np.isfinite(data[col]).all(): return refuse('Missing or invalid '+col)
    if (data.spread_cm_s < 0).any(): return refuse('Negative spread rate.')
    groups = ['block_id','width_cm','full_duct_height_cm']
    grouped = data.groupby(groups).spread_cm_s
    if set(zip(data.width_cm,data.full_duct_height_cm)) != set(CELLS):
        return refuse('Expected both widths crossed with both full duct heights.')
    means = grouped.mean().unstack(['width_cm','full_duct_height_cm'])
    if design == 'randomized_height_sessions':
        # Height is assigned to sessions. Each session supplies one paired width contrast.
        session_groups = data.groupby('block_id')
        if (session_groups.full_duct_height_cm.nunique() != 1).any() or (session_groups.width_cm.nunique() != 2).any() or len(session_groups) != burns.block_id.nunique():
            return refuse('Each independent session needs one assigned height and both widths.')
        by_width = data.groupby(['block_id','width_cm']).spread_cm_s.mean().unstack()
        contrast = by_width[40.6] - by_width[5.]
        heights = session_groups.full_duct_height_cm.first()
        shallow, deep = contrast[heights == 30.5], contrast[heights == 51.]
        if min(len(shallow),len(deep)) < 3:
            return refuse('This pilot interval requires at least three independent sessions per height.')
        variances = [part.var()/len(part) for part in (shallow,deep)]
        variance = sum(variances)
        if variance == 0:
            return refuse('No between-session variation to estimate a Welch interval.')
        degrees = variance**2 / sum(v**2/(len(part)-1) for v,part in zip(variances,(shallow,deep)))
        estimate = float(shallow.mean()-deep.mean())
        margin = float(t.ppf(.975,degrees)*np.sqrt(variance))
        return dict(status='ESTIMATED', interaction_cm_s=estimate, interval_cm_s=[estimate-margin,estimate+margin],
                    method='Approximate 95% Welch interval comparing independent session width contrasts',
                    sessions_per_height={'shallow':len(shallow),'deep':len(deep)},
                    session_width_contrasts_cm_s=contrast.to_dict(),
                    height_contrasts_cm_s={label: float(by_width.loc[heights==30.5,w].mean()-by_width.loc[heights==51.,w].mean())
                                          for label,w in [('narrow',5.),('wide',40.6)]},
                    cell_summaries=data.groupby(groups[1:]).spread_cm_s.agg(['mean','std','count']).reset_index().to_dict('records'),
                    exclusions=excluded[['burn_id','exclusion_reason']].to_dict('records'))
    if means.isna().any().any() or len(means)!=burns.block_id.nunique() or len(means)<3:
        return refuse('Need at least three independent complete blocks for this pilot interval.')
    narrow = means[(5.,30.5)] - means[(5.,51.)]
    wide = means[(40.6,30.5)] - means[(40.6,51.)]
    differences = wide - narrow
    estimate = float(differences.mean())
    margin = float(t.ppf(.975,len(means)-1)*differences.sem())
    cells = data.groupby(groups[1:]).spread_cm_s.agg(['mean','std','count']).reset_index()
    return dict(status='ESTIMATED',interaction_cm_s=estimate, interval_cm_s=[estimate-margin,estimate+margin],
                method='Approximate 95% Student t interval across independent block interaction contrasts',
                independent_blocks=len(means),height_contrasts_cm_s=dict(narrow=narrow.mean(),wide=wide.mean()),
                cell_summaries=cells.to_dict('records'),block_interactions_cm_s=differences.to_dict(),
                exclusions=excluded[['burn_id','exclusion_reason']].to_dict('records'))
