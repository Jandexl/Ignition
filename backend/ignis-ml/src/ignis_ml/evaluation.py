"""Independent-group comparisons with shared held-out records and auditable folds."""
import hashlib
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
from .models import build, features
from .schema import TARGET
from .validation import validate
from .domain import check_domain


def fingerprint(df, manifest, cfg):
    payload = df.to_csv(index=False) + manifest.to_csv(index=False) + json.dumps(cfg.to_dict(), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def metrics(y, pred):
    y, pred = np.asarray(y, float), np.asarray(pred, float)
    if y.ndim != 1 or y.shape != pred.shape or not len(y) or not np.isfinite([y, pred]).all():
        raise ValueError('Metrics require equal, nonempty, finite one-dimensional arrays')
    e = pred - y
    return {'mae_cm_s': float(np.mean(abs(e))), 'rmse_cm_s': float(np.sqrt(np.mean(e**2))),
            'bias_cm_s': float(np.mean(e))}


def _keys(df, cols):
    return df[cols].astype(str).apply(lambda r: tuple(r), axis=1)


def split_indices(df, cfg):
    groups = df.dependency_group_id
    if groups.nunique() < cfg.min_groups:
        raise ValueError(f'Need >= {cfg.min_groups} reviewed independent groups; got {groups.nunique()}')
    if cfg.strategy == 'cross_scale':
        if not cfg.holdout_investigation: raise ValueError('Specify the predeclared held-out investigation')
        test = df.investigation_id.eq(cfg.holdout_investigation).to_numpy()
        if not test.any() or test.all(): raise ValueError('Cross-scale split needs both train and held-out investigations')
        pairs = [(np.flatnonzero(~test), np.flatnonzero(test))]
    else:
        splitgroups = groups if cfg.strategy != 'campaign' else _keys(df, ['investigation_id', 'campaign_id']).map(repr)
        if splitgroups.nunique() < cfg.min_groups: raise ValueError('Too few independent campaign/group partitions')
        if cfg.strategy == 'groupkfold':
            if cfg.n_splits > splitgroups.nunique(): raise ValueError('n_splits exceeds groups')
            splitter = GroupKFold(n_splits=cfg.n_splits)
        else: splitter = LeaveOneGroupOut()
        pairs = list(splitter.split(df, groups=splitgroups))
    for tr, te in pairs:
        if len(tr) == 0 or len(te) == 0 or set(tr) & set(te): raise ValueError('Invalid row split')
        for cols in [['dependency_group_id'], ['investigation_id', 'campaign_id', 'run_id'], ['observation_id']]:
            if set(_keys(df.iloc[tr], cols)) & set(_keys(df.iloc[te], cols)):
                raise ValueError(f'Dependent train/test overlap: {cols}')
        if df.iloc[tr].dependency_group_id.nunique() < 2: raise ValueError('Training fold needs >=2 independent groups')
    return pairs


def evaluate(df, manifest, cfg, synthetic=False):
    report = {'status': 'VALIDATION_NOT_SUPPORTED', 'synthetic': synthetic, 'reasons': [],
              'metrics': {}, 'folds': [], 'predictions': [], 'limitations': [
                  'Group independence and comparability require human evidence; software checks declarations and overlap.',
                  'No confidence/prediction intervals; residual error is not measurement uncertainty.',
                  'Grouped errors alone do not authorize predictions or prove geometry effects.',
                  'Small group counts yield unstable estimates; minimum counts are engineering gates, not statistical proof.']}
    try: cfg.check()
    except (ValueError, TypeError) as e:
        report['reasons'] = [str(e)]; return report
    quality = validate(df, manifest, cfg.geometry, synthetic)
    report['data_validation'] = quality
    if quality['status'] != 'READY_FOR_EVALUATION':
        report['reasons'] = [x['message'] for x in quality['issues'] if x['severity'] == 'error']; return report
    df = df.reset_index(drop=True)
    try: pairs = split_indices(df, cfg)
    except ValueError as e:
        report['reasons'] = [str(e)]; return report
    names = ['mean', 'condition_ridge'] + (['geometry_ridge'] if cfg.geometry else [])
    records = []
    for k, (tr, te) in enumerate(pairs):
        train, test = df.iloc[tr], df.iloc[te]
        # Unknown model categories block all comparison models, never drop just one model's errors.
        for c in ['material', 'flow_direction']:
            if not set(test[c]).issubset(set(train[c])):
                report['reasons'] = [f'Fold {k}: unseen {c} category; select a comparable cohort.']; return report
        audit = dict(fold=k, train_observation_ids=train.observation_id.tolist(), test_observation_ids=test.observation_id.tolist(),
                     train_groups=sorted(train.dependency_group_id.unique().tolist()),
                     test_groups=sorted(test.dependency_group_id.unique().tolist()),
                     train_sources=sorted(train.source_id.unique().tolist()), test_sources=sorted(test.source_id.unique().tolist()))
        audit['domain_warnings'] = {str(row.observation_id): check_domain(train, row.to_dict(), cfg) for _, row in test.iterrows()}
        report['folds'].append(audit)
        for name in names:
            model = build(name, cfg)
            model.fit(train, train[TARGET].to_numpy(float))
            pred = model.predict(test)
            for (_, row), p in zip(test.iterrows(), pred):
                records.append(dict(model=name, fold=k, observation_id=row.observation_id, group=row.dependency_group_id,
                                    campaign=row.campaign_id, source_id=row.source_id, airflow_cm_s=float(row.flow_velocity_cm_s),
                                    measured_cm_s=float(row[TARGET]), predicted_cm_s=float(p), residual_cm_s=float(p-row[TARGET]),
                                    domain_supported=not bool(audit['domain_warnings'][str(row.observation_id)])))
    pred_df = pd.DataFrame(records)
    for name in names:
        part = pred_df[pred_df.model.eq(name)]
        group_scores = [metrics(g.measured_cm_s, g.predicted_cm_s) for _, g in part.groupby('group')]
        report['metrics'][name] = dict(**metrics(part.measured_cm_s, part.predicted_cm_s),
            group_macro_mae_cm_s=float(np.mean([m['mae_cm_s'] for m in group_scores])),
            group_macro_rmse_cm_s=float(np.mean([m['rmse_cm_s'] for m in group_scores])),
            n_test_observations=len(part), n_independent_test_groups=part.group.nunique(),
            n_out_of_domain=int((~part.domain_supported).sum()),
            features=[] if name == 'mean' else sum((list(x) for x in features(name, cfg)), []),
            group_metrics={str(g): metrics(p.measured_cm_s, p.predicted_cm_s) for g, p in part.groupby('group')})
    if 'geometry_ridge' in names:
        a, b = report['metrics']['condition_ridge'], report['metrics']['geometry_ridge']
        report['geometry_comparison'] = {
            'mae_change_geometry_minus_condition_cm_s': b['mae_cm_s']-a['mae_cm_s'],
            'rmse_change_geometry_minus_condition_cm_s': b['rmse_cm_s']-a['rmse_cm_s'],
            'interpretation': 'Negative changes favor geometry on these held-out records only; no causality or general benefit established.'}
        fixed = [c for c in cfg.geometry if df.groupby('campaign_id')[c].nunique().max() <= 1]
        if fixed: report['limitations'].append(f'Geometry constant within campaigns for {fixed}; geometry effects may be confounded with campaign/apparatus.')
    report.update(status='SYNTHETIC_EVALUATION_ONLY' if synthetic else 'EVALUATED_PENDING_REVIEW',
                  predictions=records, fingerprint=fingerprint(df, manifest, cfg), config=cfg.to_dict())
    return report
