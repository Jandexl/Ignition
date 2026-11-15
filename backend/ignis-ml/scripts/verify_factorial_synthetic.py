"""Reproducible 1gnition synthetic factorial-verification demonstration.

Runs the EXISTING ignis_ml.factorial.analyze_burns without any NASA fitting.
All rates and interventions below are explicitly invented for software verification.
Run from repository root with python scripts/verify_factorial_synthetic.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
from ignis_ml.factorial import analyze_burns

OUT = ROOT / 'outputs' / 'synthetic_factorial_verification'
N_BLOCKS = 20
SD_PER_BURN = 0.012
SD_SHARED_BLOCK = 0.006
SEED = 20261115
WIDTHS = (5.0, 40.6)
HEIGHTS = (51.0, 30.5)
BASE = {
    (5.0, 51.0): 0.20,
    (40.6, 51.0): 0.22,
    (5.0, 30.5): 0.24,
}
SCENARIOS = {
    'positive': {'wide_shallow': 0.34, 'seed': SEED},
    'zero': {'wide_shallow': 0.26, 'seed': SEED + 1},
    'negative': {'wide_shallow': 0.18, 'seed': SEED + 2},
}


def true_interaction(means: dict[tuple[float, float], float]) -> float:
    return ((means[(40.6, 30.5)] - means[(40.6, 51.0)])
            - (means[(5.0, 30.5)] - means[(5.0, 51.0)]))


def simulated_burns(name: str, spec: dict, blocks: int = N_BLOCKS) -> tuple[pd.DataFrame, dict]:
    means = dict(BASE)
    means[(40.6, 30.5)] = spec['wide_shallow']
    rng = np.random.default_rng(spec['seed'])
    rows = []
    for b in range(blocks):
        shared = rng.normal(0.0, SD_SHARED_BLOCK)
        # Randomized measurement order within an independent block.
        order = [(w, h) for w in WIDTHS for h in HEIGHTS]
        rng.shuffle(order)
        for order_num, (w, h) in enumerate(order):
            rate = means[(w, h)] + shared + rng.normal(0.0, SD_PER_BURN)
            if rate <= 0:
                raise ValueError('Synthetic rate must remain positive. Adjust simulation assumptions.')
            key = f'SYNTHETIC-{name}-block{b:02d}-width{w:g}-height{h:g}'
            rows.append(dict(
                block_id=f'SYNTHETIC-{name}-block{b:02d}', burn_id=key, specimen_id=key,
                width_cm=w, full_duct_height_cm=h, spread_cm_s=rate,
                included=True, exclusion_reason='', randomized_order=order_num,
                synthetic=True, origin='mathematically_generated_not_NASA',
            ))
    return pd.DataFrame(rows), means


def simulated_height_sessions(name: str, spec: dict, sessions_per_height: int = 12):
    """Alternative experimental design: whole session is assigned one duct height."""
    means = dict(BASE)
    means[(40.6, 30.5)] = spec['wide_shallow']
    rng = np.random.default_rng(20261118)
    sessions = [51.0] * sessions_per_height + [30.5] * sessions_per_height
    rng.shuffle(sessions)
    rows = []
    for session_index, h in enumerate(sessions):
        session_noise = rng.normal(0, SD_SHARED_BLOCK)
        widths = list(WIDTHS)
        rng.shuffle(widths)
        for order_num, w in enumerate(widths):
            rate = means[(w, h)] + session_noise + rng.normal(0, SD_PER_BURN)
            key = f'SYNTHETIC-{name}-session{session_index:02d}-width{w:g}-height{h:g}'
            rows.append(dict(block_id=f'SYNTHETIC-{name}-session{session_index:02d}',
                             burn_id=key, specimen_id=key,
                             width_cm=w, full_duct_height_cm=h, spread_cm_s=rate,
                             included=True, exclusion_reason='', randomized_order=order_num,
                             synthetic=True, origin='mathematically_generated_not_NASA'))
    return pd.DataFrame(rows), means


def report_result(name: str, dataframe: pd.DataFrame, means: dict, design: str) -> dict:
    # Only the trusted synthetic generator qualifies to declare its fictional controls verified.
    outcome = analyze_burns(dataframe, design=design, controls_verified=True)
    if outcome['status'] != 'ESTIMATED':
        raise AssertionError(f'Existing factorial implementation refused synthetic design: {outcome}')
    delta_true = true_interaction(means)
    delta_est = outcome['interaction_cm_s']
    low, high = outcome['interval_cm_s']
    observed_sign = 'positive' if delta_est > 0 else ('negative' if delta_est < 0 else 'zero')
    return {
        'scenario': name,
        'synthetic': True,
        'source': 'invented_means_with_seeded_Gaussian_noise_not_NASA',
        'purpose': 'factorial_analysis_software_verification_only',
        'design': design,
        'generated_independent_burns': int(len(dataframe)),
        'generated_independent_blocks_or_sessions': int(dataframe.block_id.nunique()),
        'expected_cell_means_cm_s': [
            {'width_cm': w, 'full_duct_height_cm': h, 'mean_cm_s': means[(w, h)]}
            for w in WIDTHS for h in HEIGHTS
        ],
        'known_interaction_cm_s': delta_true,
        'estimated_interaction_cm_s': delta_est,
        'estimate_minus_truth_cm_s': delta_est - delta_true,
        'approx_95pct_interval_cm_s': [low, high],
        'interval_contains_zero': bool(low <= 0 <= high),
        'correct_estimate_direction': (
            abs(delta_est) < 0.025 if abs(delta_true) < 1e-12
            else np.sign(delta_est) == np.sign(delta_true)
        ),
        'analysis': outcome,
    }


def plot_positive_cell_means(data: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for w in WIDTHS:
        cur = data.loc[data.width_cm == w]
        means = cur.groupby('full_duct_height_cm').spread_cm_s.mean()
        sds = cur.groupby('full_duct_height_cm').spread_cm_s.std()
        xs = [0, 1]
        hs = [51.0, 30.5]
        ax.errorbar(xs, [means[h] for h in hs], yerr=[sds[h] for h in hs],
                    marker='o', markersize=6, capsize=4, linewidth=2, label=f'{w:g} cm specimen width')
    ax.set_xticks([0, 1], ['Deep duct (51 cm)', 'Shallow duct (30.5 cm)'])
    ax.set_ylabel('Synthetic flame-spread rate (cm/s)')
    ax.set_title('Known positive interaction: generated measurements (not NASA)')
    ax.legend()
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(OUT / 'positive_synthetic_2x2.png', dpi=180)
    plt.close(fig)


def plot_interactions(results: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    labels = [r['scenario'].replace('_', ' ').title() for r in results]
    vals = [r['estimated_interaction_cm_s'] for r in results]
    errlow = [r['estimated_interaction_cm_s'] - r['approx_95pct_interval_cm_s'][0] for r in results]
    errhi = [r['approx_95pct_interval_cm_s'][1] - r['estimated_interaction_cm_s'] for r in results]
    xs = np.arange(len(results))
    ax.errorbar(xs, vals, yerr=[errlow,errhi], fmt='o', capsize=5, markersize=7)
    for x, r in zip(xs, results):
        ax.scatter(x, r['known_interaction_cm_s'], marker='x', s=100)
    ax.axhline(0, color='black', linestyle='--', linewidth=1)
    ax.set_xticks(xs, labels)
    ax.set_ylabel('Width × confinement interaction (cm/s)')
    ax.set_title('Synthetic verification: estimates, approximate 95% intervals and known truth (×)')
    ax.grid(axis='y', alpha=.2)
    fig.tight_layout()
    fig.savefig(OUT / 'synthetic_interactions_95ci.png', dpi=180)
    plt.close(fig)


def run() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    all_results = []
    by_name = {}
    for name, spec in SCENARIOS.items():
        data, true_means = simulated_burns(name, spec)
        data.to_csv(OUT / f'synthetic_burns_{name}.csv', index=False)
        r = report_result(name, data, true_means, 'randomized_complete_blocks')
        all_results.append(r)
        by_name[name] = data
    sessions, true_means = simulated_height_sessions('positive_height_sessions', SCENARIOS['positive'])
    sessions.to_csv(OUT / 'synthetic_burns_height_sessions.csv', index=False)
    all_results.append(report_result('positive_height_sessions', sessions, true_means,
                                     'randomized_height_sessions'))

    # Software guardrails from the existing implementation; no silent fallback to predictions.
    df = by_name['positive']
    invalid = {
        'controls_not_verified': analyze_burns(df, design='randomized_complete_blocks', controls_verified=False),
        'missing_configuration': analyze_burns(df.loc[~((df.width_cm==5.) & (df.full_duct_height_cm==30.5))],
                                              design='randomized_complete_blocks', controls_verified=True),
        'duplicate_burn': analyze_burns(pd.concat([df, df.iloc[[0]]], ignore_index=True),
                                        design='randomized_complete_blocks', controls_verified=True),
        'unknown_design': analyze_burns(df, design='unapproved_design', controls_verified=True),
    }
    if not all(r['status'] == 'ANALYSIS_NOT_SUPPORTED' and r['interaction_cm_s'] is None for r in invalid.values()):
        raise AssertionError('At least one expected guardrail refusal failed.')

    # Verification criteria are not claiming real-world power or calibrated coverage.
    tests = {
        'known_positive_recovered': all_results[0]['correct_estimate_direction'] and
                                     all_results[0]['approx_95pct_interval_cm_s'][0] > 0,
        'known_zero_recovered_without_false_positivity': all_results[1]['correct_estimate_direction'] and
                                                     all_results[1]['interval_contains_zero'],
        'known_negative_recovered': all_results[2]['correct_estimate_direction'] and
                                     all_results[2]['approx_95pct_interval_cm_s'][1] < 0,
        'alternate_height_session_design_recovered': all_results[3]['correct_estimate_direction'] and
                                     all_results[3]['approx_95pct_interval_cm_s'][0] > 0,
        'all_invalid_inputs_refused': all(v['status'] == 'ANALYSIS_NOT_SUPPORTED' for v in invalid.values()),
    }
    plot_positive_cell_means(by_name['positive'])
    plot_interactions(all_results)
    payload = {
        'project_name': '1gnition',
        'verification_title': 'Synthetic width-by-duct-height factorial software verification',
        'evidence_class': 'SYNTHETIC_SOFTWARE_TEST_ONLY',
        'is_nasa_data': False,
        'is_physics_simulation': False,
        'is_experimental_validation': False,
        'is_nasa_prediction_validation': False,
        'sample_generation': {'block_designs':N_BLOCKS, 'per_burn_sd_cm_s':SD_PER_BURN,
                              'shared_block_sd_cm_s':SD_SHARED_BLOCK, 'seed':SEED,
                              'noise_model':'Gaussian independent measurement-level noise and shared block offsets'},
        'scenarios': all_results,
        'refusal_tests': invalid,
        'checks': tests,
        'all_checks_pass': bool(all(tests.values())),
        'frontend_warning': 'SYNTHETIC DEMONSTRATION — invented rates; checks calculation software only. Not NASA data and not a validated fire prediction.',
        'scientific_hypothesis_status': 'UNTESTED_ON_CONTROLLED_MICROGRAVITY_BURNS',
        'nasa_prediction_status': 'VALIDATION_NOT_SUPPORTED',
    }
    with (OUT / 'synthetic_verification_results.json').open('w') as f:
        json.dump(payload, f, indent=2, allow_nan=False,
                  default=lambda x: x.item() if isinstance(x, np.generic) else x)
    summary = ['# 1gnition — Synthetic factorial verification', '',
               '**All measurements in this folder are generated, not NASA observations.**',
               'This verifies the existing `ignis_ml.factorial.analyze_burns` code under controlled mathematical assumptions.', '',
               '| Case | Known Δ (cm/s) | Estimated Δ | Approx. 95% interval | Result |',
               '|---|---:|---:|---|---|']
    for r in all_results:
        summary.append(f"| {r['scenario']} | {r['known_interaction_cm_s']:+.4f} | "
                       f"{r['estimated_interaction_cm_s']:+.4f} | "
                       f"[{r['approx_95pct_interval_cm_s'][0]:+.4f}, {r['approx_95pct_interval_cm_s'][1]:+.4f}] | "
                       f"{('Near zero, interval spans zero' if r['scenario']=='zero' else 'Expected sign recovered') if r['correct_estimate_direction'] else 'Review'} |")
    summary += ['', f"Automated synthetic-specific checks: {sum(tests.values())}/{len(tests)} passed.",
                '', 'These confidence intervals assume independently generated blocks/sessions and an ordinary t/Welch approximation.',
                'They do **not** demonstrate empirical 95% coverage across real experimental settings.',
                'The four rates for each case are intentionally chosen, including the presence/absence/direction of the interaction.',
                'No actual flame physics is simulated, and no NASA measurements were used to estimate the interaction.',
                'The three historical Saffire comparisons remain a separate source-backed demonstration.',
                'The model-readiness state remains `VALIDATION_NOT_SUPPORTED` for NASA cross-scale prediction.',
                '', '## Reproduce',
                'From the `ignis-ml` folder, install requirements then run:',
                '```bash', 'python scripts/verify_factorial_synthetic.py',
                'python -m unittest discover -s tests -v', '```',
                '', '## Dashboard',
                'Load `outputs/synthetic_factorial_verification/synthetic_verification_results.json`',
                'only in an explicitly marked **Synthetic Verification** mode. Do not merge these CSVs with NASA observations.',
                'The results include an invented four-cell comparison, uncertainty estimates, and guardrail refusals.',
                'Do not turn the resulting statistical estimates into physical or operational flame predictions.',
                ]
    (OUT / 'SYNTHETIC_VERIFICATION_REPORT.md').write_text('\n'.join(summary)+'\n')
    return payload


if __name__ == '__main__':
    result = run()
    print((OUT / 'SYNTHETIC_VERIFICATION_REPORT.md').read_text())
    if not result['all_checks_pass']:
        raise SystemExit('Synthetic verification checks did not all pass!')
