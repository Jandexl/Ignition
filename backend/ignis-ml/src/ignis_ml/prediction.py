"""Reviewed model activation and strict JSON prediction/refusal interface."""
from dataclasses import dataclass
import json
from pathlib import Path
import joblib
import jsonschema
from .contracts import REQUEST_SCHEMA
import numpy as np
import pandas as pd
from . import __version__
from .schema import CONDITIONS, CATEGORIES, TARGET
from .models import build
from .evaluation import evaluate
from .domain import check_domain

@dataclass
class Bundle:
    estimator: object
    training: pd.DataFrame
    config: object
    model_name: str
    evaluation: dict
    approval: dict
    synthetic: bool


def activate(df, manifest, cfg, model_name, approval, synthetic=False):
    """Recompute evaluation, bind review to exact data/config. No automatic model selection."""
    report = evaluate(df, manifest, cfg, synthetic)
    desired = 'SYNTHETIC_EVALUATION_ONLY' if synthetic else 'EVALUATED_PENDING_REVIEW'
    if report['status'] != desired: raise ValueError('Independent evaluation is not supported')
    required = ('reviewer', 'review_reference', 'acceptance_rationale', 'domain_rationale')
    if any(not isinstance(approval.get(k), str) or not approval[k].strip() for k in required):
        raise ValueError('Documented scientific approval is required')
    if approval.get('fingerprint') != report['fingerprint'] or approval.get('model_name') != model_name:
        raise ValueError('Approval does not match evaluated data/config/model')
    if approval.get('evaluation_status') != desired: raise ValueError('Approval origin/status mismatch')
    if model_name not in report['metrics']: raise ValueError('Model was not evaluated')
    if approval.get('selection_independent_of_test') is not True:
        raise ValueError('Selection using evaluation scores needs fresh held-out evaluation')
    if not synthetic and any(v['n_out_of_domain'] for v in report['metrics'].values()):
        raise ValueError('Out-of-domain evaluation requires a separate validated deployment-domain study; activation blocked')
    estimator = build(model_name, cfg).fit(df, df[TARGET].to_numpy(float))
    return Bundle(estimator, df.copy(), cfg, model_name, report, dict(approval), synthetic)


def predict(scenario, bundle=None, evidence=None):
    response = dict(status='UNSUPPORTED', predicted_flame_spread_rate_cm_s=None, prediction_units='cm/s',
                    model_version=__version__, model_type=None, inputs_used={}, validation_status='VALIDATION_NOT_SUPPORTED',
                    model_performance=None, source_ids=[], evidence_limitations=[], out_of_domain_warnings=[],
                    abstention_reasons=[], synthetic=False, intended_use='research_demonstration_only')
    try:
        jsonschema.validate(scenario, REQUEST_SCHEMA)
        json.dumps(scenario, allow_nan=False)
    except (jsonschema.ValidationError, ValueError, TypeError) as exc:
        response['abstention_reasons'] = ['Invalid scenario: ' + str(exc).split('\n')[0]]
        return response
    if bundle is None:
        response['abstention_reasons'] = ['No independently evaluated and reviewed active model.']
        # Relevant evidence can be useful, but must match material, direction and known regimes.
        candidates = evidence
        if candidates is not None:
            for c in ['material', 'flow_direction', 'gravity_regime', 'combustion_regime']:
                if c in scenario and c in candidates:
                    candidates = candidates[candidates[c].eq(scenario[c])]
            if 'material' not in scenario: candidates = candidates.iloc[0:0]
        if candidates is not None and len(candidates):
            response['status'] = 'LIMITED_EVIDENCE'
            response['synthetic'] = bool('data_origin' in candidates and candidates.data_origin.eq('synthetic').any())
            response['source_ids'] = sorted(candidates.source_id.dropna().astype(str).unique().tolist()) if 'source_id' in candidates else []
            response['evidence_limitations'] = ['Relevant records are not a validated model; source IDs may still require reconciliation.']
        return response
    response.update(model_type=bundle.model_name, synthetic=bundle.synthetic,
        validation_status='SYNTHETIC_DEMO_ONLY' if bundle.synthetic else 'REVIEWED_GROUPED_EVALUATION',
        model_performance=bundle.evaluation['metrics'][bundle.model_name],
        source_ids=sorted(bundle.training.source_id.unique().tolist()),
        evidence_limitations=bundle.evaluation['limitations'] +
           (['SYNTHETIC demonstration: no NASA accuracy or spacecraft-safety claim.'] if bundle.synthetic else []))
    reasons = check_domain(bundle.training, scenario, bundle.config)
    if reasons:
        response['out_of_domain_warnings'] = reasons
        response['abstention_reasons'] = ['Scenario is outside the reviewed evidence domain.']
        return response
    expected_origin = 'synthetic' if bundle.synthetic else 'verified'
    if bundle.config.geometry and scenario.get('geometry_status') != expected_origin:
        response['abstention_reasons'] = ['Geometry verification origin does not match model.']; return response
    frame = pd.DataFrame([scenario])
    value = float(bundle.estimator.predict(frame)[0])
    if not np.isfinite(value) or value < 0:
        response['abstention_reasons'] = ['Model returned a nonphysical prediction; no clipping applied.']; return response
    used = list(CONDITIONS) + ['material', 'flow_direction']
    if bundle.model_name == 'geometry_ridge': used += list(bundle.config.geometry)
    if bundle.model_name == 'mean': used = []
    response.update(status='SUPPORTED', predicted_flame_spread_rate_cm_s=value,
                    inputs_used={k: scenario[k] for k in used})
    return response


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def save(bundle, path):
    joblib.dump(bundle, path)


def load(path):
    # joblib/pickle can execute code. Only load trusted project-generated artifacts.
    value = joblib.load(path)
    if not isinstance(value, Bundle): raise ValueError('Not an IGNIS model bundle')
    return value
