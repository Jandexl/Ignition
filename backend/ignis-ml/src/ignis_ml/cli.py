"""CLI: demo, validate, evaluate, and predict. Refusals use nonzero exit codes."""
import argparse
import json
from pathlib import Path
import pandas as pd
from .schema import contract, adapt_current
from .cohort import select_cohort
from .models import Config
from .fixtures import fixture, demo_config, approval_for, scenario_from_row
from .validation import validate
from .evaluation import evaluate
from .prediction import activate, predict, save, load, write_json
from .plotting import make_plots
from .contracts import REQUEST_SCHEMA, RESPONSE_SCHEMA


def run_demo(root):
    root = Path(root); out = root/'outputs'; out.mkdir(parents=True, exist_ok=True)
    (root/'data').mkdir(exist_ok=True); (root/'docs').mkdir(exist_ok=True)
    df, manifest = fixture(); cfg = demo_config()
    df.to_csv(root/'data/synthetic_fixture.csv', index=False)
    manifest.to_csv(root/'data/synthetic_manifest.csv', index=False)
    report = evaluate(df, manifest, cfg, synthetic=True)
    if report['status'] != 'SYNTHETIC_EVALUATION_ONLY': raise RuntimeError(report['reasons'])
    write_json(out/'synthetic_evaluation.json', report)
    pd.DataFrame(report['predictions']).to_csv(out/'synthetic_predictions.csv', index=False)
    make_plots(df, report, out/'plots')
    bundle = activate(df, manifest, cfg, 'geometry_ridge', approval_for(report), synthetic=True)
    save(bundle, out/'SYNTHETIC_DEMO_MODEL.joblib')
    scenario = scenario_from_row(df.iloc[0])
    write_json(out/'scenario_supported_SYNTHETIC.json', scenario)
    for name, result in [
        ('supported_SYNTHETIC', predict(scenario, bundle)),
        ('limited_evidence', predict(scenario, evidence=df)),
        ('unsupported', predict(dict(scenario, flow_velocity_cm_s=900), bundle))]:
        write_json(out/(name+'.json'), result)
    write_json(root/'docs/data_contract.json', contract())
    write_json(root/'docs/request.schema.json', REQUEST_SCHEMA)
    write_json(root/'docs/response.schema.json', RESPONSE_SCHEMA)
    # Inspection only, never NASA fitting.
    current = root/'data/current'
    for kind, filename, manifestname in [
        ('starter', 'ignis_experiments_starter.csv', 'ignis_source_manifest_starter.csv'),
        ('candidate', 'ignis_bass_saffire_candidate_observations.csv', 'ignis_bass_saffire_source_manifest.csv')]:
        if not (current/filename).exists(): continue
        raw = pd.read_csv(current/filename); source = pd.read_csv(current/manifestname)
        adapted = adapt_current(raw, kind)
        write_json(out/(kind+'_validation.json'), validate(adapted, source, cfg.geometry))
        write_json(out/(kind+'_evaluation_refusal.json'), evaluate(adapted, source, cfg))
        adapted.to_csv(out/(kind+'_provisional_adapter.csv'), index=False)
    print('Synthetic demo complete. No NASA model was trained.')
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='command', required=True)
    demo = sub.add_parser('demo'); demo.add_argument('--root', default='.')
    for name in ('validate', 'evaluate'):
        q = sub.add_parser(name); q.add_argument('csv'); q.add_argument('--manifest', required=True)
        q.add_argument('--config', required=True); q.add_argument('--output', required=True)
        q.add_argument('--adapter', choices=['starter', 'candidate'])
        q.add_argument('--cohort', help='Reviewed JSON cohort filters with exclusion ledger')
    q = sub.add_parser('predict'); q.add_argument('scenario'); q.add_argument('--model'); q.add_argument('--evidence')
    q.add_argument('--output', required=True)
    args = p.parse_args(argv)
    try:
        if args.command == 'demo': return run_demo(args.root)
        if args.command == 'predict':
            result = predict(json.loads(Path(args.scenario).read_text()), load(args.model) if args.model else None,
                             pd.read_csv(args.evidence) if args.evidence else None)
            write_json(args.output, result); print(result['status']); return 0 if result['status'] == 'SUPPORTED' else 2
        df = pd.read_csv(args.csv); manifest = pd.read_csv(args.manifest)
        if args.adapter: df = adapt_current(df, args.adapter)
        ledger = None
        if args.cohort: df, ledger = select_cohort(df, json.loads(Path(args.cohort).read_text()))
        cfg = Config(**json.loads(Path(args.config).read_text()))
        if args.command == 'validate': result = validate(df, manifest, cfg.geometry)
        else: result = evaluate(df, manifest, cfg)
        if ledger is not None: result['cohort_ledger'] = ledger
        write_json(args.output, result); print(result['status'])
        return 0 if result['status'] in ('READY_FOR_EVALUATION', 'EVALUATED_PENDING_REVIEW') else 2
    except (ValueError, KeyError, OSError, TypeError) as e:
        write_json(args.output, {'status': 'INPUT_ERROR', 'message': str(e)}) if hasattr(args, 'output') else None
        print(f'Input error: {e}'); return 2

if __name__ == '__main__': raise SystemExit(main())
