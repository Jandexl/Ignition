"""Reusable figures; every output includes origin and validation context."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from .schema import CONDITIONS, GEOMETRY, TARGET

COLORS = {'mean': '#7a8695', 'condition_ridge': '#267b9f', 'geometry_ridge': '#db6d37'}


def make_plots(df, report, directory):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    context = ('SYNTHETIC • software test only' if report.get('synthetic') else 'EXPERIMENTAL • evaluation pending scientific review')
    context += '\n' + report['status'] + ' | sources: ' + ', '.join(df.source_id.dropna().astype(str).unique())
    paths = []
    def finish(fig, ax, name, title):
        ax.set_title(title, loc='left', fontsize=13, fontweight='bold', pad=16)
        fig.text(.02, .02, context, fontsize=8, color='#53616b')
        fig.tight_layout(rect=(0, .10, 1, 1))
        path = directory / (name+'.png'); fig.savefig(path, dpi=150); plt.close(fig); paths.append(str(path))
    plt.rcParams.update({'axes.spines.top': False, 'axes.spines.right': False, 'font.size': 10})
    cols = list(CONDITIONS + GEOMETRY + (TARGET,))
    fig, ax = plt.subplots(figsize=(9, 5))
    coverage = [100*df[c].notna().mean() if c in df else 0 for c in cols]
    ax.barh([c.replace('_', ' ') for c in cols], coverage, color='#267b9f')
    ax.set_xlim(0, 105); ax.set_xlabel('Nonmissing values (%) — presence does not mean verified')
    finish(fig, ax, 'feature_coverage', f'Feature coverage | n={len(df)} records')
    if not report.get('predictions'): return paths
    p = pd.DataFrame(report['predictions'])
    fig, ax = plt.subplots(figsize=(8, 6))
    for name, part in p.groupby('model'):
        ax.scatter(part.measured_cm_s, part.predicted_cm_s, label=name, color=COLORS[name], s=24, alpha=.7)
    lo, hi = min(p.measured_cm_s.min(), p.predicted_cm_s.min()), max(p.measured_cm_s.max(), p.predicted_cm_s.max())
    ax.plot([lo, hi], [lo, hi], '--', color='#333333', label='Identity line')
    ax.set_xlabel('Measured flame-spread rate (cm/s)'); ax.set_ylabel('Held-out prediction (cm/s)'); ax.legend(fontsize=8)
    finish(fig, ax, 'measured_predicted', f'Independent-group predictions | {p.observation_id.nunique()} records')
    fig, ax = plt.subplots(figsize=(8, 5))
    for name, part in p.groupby('model'):
        ax.scatter(part.airflow_cm_s, part.residual_cm_s, label=name, color=COLORS[name], s=23, alpha=.7)
    ax.axhline(0, color='black', linewidth=.8); ax.legend(fontsize=8)
    ax.set_xlabel('Airflow speed (cm/s)'); ax.set_ylabel('Prediction − measurement (cm/s)')
    finish(fig, ax, 'residual_airflow', 'Residuals versus airflow')
    fig, ax = plt.subplots(figsize=(9, 5))
    camps = sorted(p.campaign.unique()); names = list(report['metrics'])
    for j, name in enumerate(names):
        part = p[p.model.eq(name)]
        ax.scatter([camps.index(c) + .18*(j-1) for c in part.campaign], part.residual_cm_s,
                   s=22, alpha=.65, color=COLORS[name], label=name)
    ax.axhline(0, color='black', linewidth=.8); ax.set_xticks(range(len(camps)), camps); ax.legend(fontsize=8)
    ax.set_xlabel('Held-out observation campaign'); ax.set_ylabel('Prediction − measurement (cm/s)')
    finish(fig, ax, 'residual_campaign', 'Campaign residuals | individual held-out observations')
    fig, ax = plt.subplots(figsize=(8, 5)); x = np.arange(len(names))
    for delta, metric, label in [(-.18, 'mae_cm_s', 'MAE'), (.18, 'rmse_cm_s', 'RMSE')]:
        ax.bar(x+delta, [report['metrics'][n][metric] for n in names], .34, label=label)
    ax.set_xticks(x, names); ax.set_ylabel('Held-out error (cm/s)'); ax.legend()
    finish(fig, ax, 'model_comparison', 'Model errors | identical evaluation observations')
    fig, ax = plt.subplots(figsize=(9, 5))
    counts = p[p.model.eq(names[0])].group.value_counts().sort_index()
    ax.bar(counts.index, counts, color='#267b9f'); ax.tick_params(axis='x', rotation=45)
    ax.set_ylabel('Evaluated observations'); ax.set_xlabel('Independent dependency group')
    finish(fig, ax, 'test_groups', f'Evaluated group distribution | {len(counts)} groups')
    fig, ax = plt.subplots(figsize=(7, 5))
    base = p[p.model.eq(names[0])]
    ax.bar(['Inside evidence domain', 'Outside evidence domain'],
           [int(base.domain_supported.sum()), int((~base.domain_supported).sum())], color=['#267b9f', '#db6d37'])
    ax.set_ylabel('Held-out observations')
    finish(fig, ax, 'domain_warnings', 'Domain coverage | not a spacecraft safety assessment')
    return paths
