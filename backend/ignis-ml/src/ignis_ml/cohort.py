"""Explicit, reviewed filtering with an inclusion/exclusion ledger; never blanket dropna."""
import pandas as pd

ALLOWED = {'material', 'flow_direction', 'gravity_regime', 'combustion_regime', 'investigation_id',
           'campaign_id', 'verification_status', 'measurement_status', 'geometry_definition_id'}


def select_cohort(df, specification):
    if not specification.get('review_reference') or not specification.get('reason'):
        raise ValueError('Cohort selection requires review_reference and reason')
    filters = specification.get('equals', {})
    if not filters or not set(filters).issubset(ALLOWED):
        raise ValueError('Use explicit allowed metadata filters; target-based cohort selection is forbidden')
    include = pd.Series(True, index=df.index)
    for field, values in filters.items():
        if field not in df or not isinstance(values,list) or not values:
            raise ValueError(f'Invalid cohort filter: {field}')
        include &= df[field].isin(values)
    ledger = {'specification': specification, 'n_input': len(df), 'n_selected': int(include.sum()),
              'included_observation_ids': df.loc[include,'observation_id'].tolist(),
              'excluded_observation_ids': df.loc[~include,'observation_id'].tolist()}
    return df.loc[include].copy(), ledger
