"""Reproducible preliminary source-data audit and PMMA group-holdout diagnostic.
NOT an independently verified NASA ML validation. No approved coefficients are exported.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
ROOT=Path(__file__).resolve().parent
sibal=pd.read_csv(ROOT/'input_data/ignis_table1_rates.csv')
pmma=pd.read_csv(ROOT/'input_data/PMMA_Table5_1_transcription.csv')
si=sibal[sibal.material=='SIBAL'].copy()
valid=pmma[pmma.spread_rate_converted_cm_s.notna()].copy()
condition_masks={
 'narrow_deep': (si.sample_width_cm.eq(5) & si.duct_full_height_cm.eq(51)),
 'wide_deep': (si.sample_width_cm.eq(40.6) & si.duct_full_height_cm.eq(51)),
 'narrow_shallow': (si.sample_width_cm.eq(5) & si.duct_full_height_cm.eq(30.5)),
 'wide_shallow': (si.sample_width_cm.eq(40.6) & si.duct_full_height_cm.eq(30.5))}
factorial={k: {'count':int(mask.sum()),'records':si.loc[mask,'record_id'].tolist()} for k,mask in condition_masks.items()}
# Holdout is BY TEST ID, NOT by flow-step row. It remains exploratory because the
# source table is a transcription and stage-level oxygen/pressure are incomplete.
y=valid.spread_rate_converted_cm_s.to_numpy(float)
groups=valid.test_id.to_numpy(str)
X1=valid[['flow_speed_cm_s']].to_numpy(float)
X2=valid[['flow_speed_cm_s','width_cm','thickness_mm','burning_sides']].to_numpy(float)
cv=GroupKFold(n_splits=5)
models={'mean_only':None, 'flow_only_ridge':X1,'flow_plus_geometry_ridge':X2}
records=[];scores={}
for model_name,X in models.items():
 pred=np.full(y.shape,np.nan)
 fold_details=[]
 for fold,(tr,te) in enumerate(cv.split(X1,y,groups),start=1):
  if X is None: model=DummyRegressor(strategy='mean').fit(X1[tr],y[tr]); p=model.predict(X1[te])
  else: model=make_pipeline(StandardScaler(),Ridge(alpha=1.0)).fit(X[tr],y[tr]);p=model.predict(X[te])
  pred[te]=p
  fold_details.append({'fold':fold, 'train_group_count':int(len(np.unique(groups[tr]))), 'held_out_groups':sorted(set(groups[te])),'held_out_rows':int(len(te))})
 assert np.isfinite(pred).all()
 scores[model_name]={'MAE_cm_s':round(float(mean_absolute_error(y,pred)),7),'RMSE_cm_s':round(float(np.sqrt(mean_squared_error(y,pred))),7),'folds':fold_details}
 for i in range(len(y)):
  records.append({'observation_id':valid.iloc[i].observation_id,'test_id':groups[i], 'published_rate_cm_s':float(y[i]), 'model':model_name, 'heldout_prediction_cm_s':float(pred[i])})
# Post-hoc uncertainty diagnostic: bootstrap the 18 provisional test groups from
# the fixed out-of-fold predictions. This is NOT a confidence interval for
# generalizing to a new spacecraft/campaign.
from collections import defaultdict
by_model = pd.DataFrame(records).pivot(index='observation_id', columns='model', values='heldout_prediction_cm_s')
meta=valid.set_index('observation_id')[['test_id','spread_rate_converted_cm_s']]
joined=by_model.join(meta)
ids=joined.test_id.to_numpy(); true=joined.spread_rate_converted_cm_s.to_numpy(float)
e0=np.abs(joined.mean_only.to_numpy()-true)
e2=np.abs(joined.flow_plus_geometry_ridge.to_numpy()-true)
rng=np.random.default_rng(732)
unique_ids=np.unique(ids); improv=[]
for _ in range(20000):
    draw=rng.choice(unique_ids, size=len(unique_ids), replace=True)
    ii=np.concatenate([np.flatnonzero(ids==g) for g in draw])
    improv.append(float(e0[ii].mean()-e2[ii].mean()))
boot_ci=[round(float(x),7) for x in np.quantile(improv,[0.025,0.975])]
results={
 'study':'1gnition real-data predictive validation feasibility and preliminary within-PMMA group-holdout benchmark',
 'status':'EXPLORATORY_NOT_VALIDATED',
 'source_audit':{
  'SIBAL_olson_published_rows':int(len(si)),
  'SIBAL_unique_groups_by_flight':int(si.flight.nunique()),
  'SIBAL_records_approved_for_ML':int(si.approved_for_ml.sum()),
  'SIBAL_factorial_historical_analogs':factorial,
  'PMMA_published_flow_step_rows_with_rate':int(len(valid)),
  'PMMA_named_test_groups_with_rate':int(valid.test_id.nunique()),
  'PMMA_missing_step_specific_oxygen_rows':int(valid.oxygen_at_measurement_vol_pct.isna().sum()),
  'PMMA_missing_stage_specific_pressure_rows':int(len(valid)),
  'PMMA_flame_direction_categories':sorted(valid.flow_direction.unique().tolist()),
  'PMMA_approx_independent_grouping':'test_id is provisional as independent-burn identifier; original NASA run logs not reverified',
  'PMMA_source':"NASA/TM-20210011385 Table 5.1, through the team's unverified transcription",
 },
 'exploratory_holdout':{
  'description':'5-fold GroupKFold by PMMA test_id, fixed alpha=1.0, no target-based feature selection or test-group tuning',
  'models':{
   'mean_only':'Dummy mean on training groups',
   'flow_only_ridge':'Ridge with only stage airflow',
   'flow_plus_geometry_ridge':'Ridge with stage airflow, specimen width, thickness and burning sides; NOT canonical M2',
  },
  'results':scores,
  'posthoc_mean_MAE_reduction_vs_mean_baseline_cm_s':round(float(e0.mean()-e2.mean()),7),
  'posthoc_group_bootstrap_95pct_interval_cm_s':boot_ci,
  'limitations':[
   'Published rates have not been checked against original NASA raw flame-tracking data',
   'Test IDs are assumed independent; raw burn logs have not been verified',
   'Step-specific oxygen is missing for all 39 rows; initial/final readings are not substitutes',
   'Pressure at each step absent from this transcription',
   'Only PMMA opposed-flow BASS-II experiments; no SIBAL or Saffire target domain',
   'Not original M1/M2, not cross-scale, not NASA qualified accuracy or prediction software',
   'Small cohort with possible per-test material, thickness and geometry confounding',
   'Test-fold results are a diagnostic only, not an approved deployment predictor',
  ]
 },
 'next_evidence':[
  'Independent qualified experiments at all four widths/heights with matched controls and replicates',
  'Flight/sample/run IDs, independent burn and exposure grouping',
  'Stage-level oxygen, pressure, geometry, airflow calibration and instrument uncertainty',
  'Complete standardized source provenance and documented exclusions',
  'Campaign-held-out cross-scale evaluation with frozen model comparison and uncertainty budget',
 ]
}
(ROOT/'real_data_preflight.json').write_text(json.dumps(results,indent=2))
pd.DataFrame(records).to_csv(ROOT/'pmma_exploratory_group_holdout_predictions.csv',index=False)
print(json.dumps({"source_audit":results['source_audit'],"metrics":{m:{k:v for k,v in d.items() if k !='folds'} for m,d in scores.items()}},indent=2))
