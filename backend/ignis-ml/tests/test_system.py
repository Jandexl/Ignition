import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
import jsonschema
from ignis_ml.schema import convert, adapt_current, TARGET, contract
from ignis_ml.validation import validate
from ignis_ml.models import build, PhysicsFeatures
from ignis_ml.evaluation import evaluate, metrics, split_indices
from ignis_ml.fixtures import fixture, demo_config, approval_for, scenario_from_row
from ignis_ml.prediction import activate, predict, save, load, write_json
from ignis_ml.contracts import RESPONSE_SCHEMA
from ignis_ml.domain import check_domain
from ignis_ml.plotting import make_plots

ROOT = Path(__file__).resolve().parents[1]

class SystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.manifest = fixture(); cls.cfg = demo_config()
        cls.report = evaluate(cls.data, cls.manifest, cls.cfg, synthetic=True)
        cls.bundle = activate(cls.data, cls.manifest, cls.cfg, 'geometry_ridge', approval_for(cls.report), synthetic=True)

    def setUp(self):
        self.df = self.data.copy(deep=True)
        self.scenario = scenario_from_row(self.df.iloc[0])

    def quality(self, df=None): return validate(self.df if df is None else df, self.manifest, self.cfg.geometry, True)
    def ev(self, df=None, cfg=None): return evaluate(self.df if df is None else df, self.manifest, cfg or self.cfg, True)
    def assertBlocked(self, df=None, cfg=None): self.assertEqual(self.ev(df,cfg)['status'], 'VALIDATION_NOT_SUPPORTED')

    def test_fixture_contract(self):
        self.assertEqual(self.quality()['status'], 'READY_FOR_EVALUATION')
        self.assertTrue(set(contract()).issubset(self.df.columns))
    def test_unit_conversion(self):
        np.testing.assert_allclose(convert([2.1, 2.6], 'mm/s','cm/s'), [.21,.26])
        np.testing.assert_allclose(convert([.21], 'fraction','%'), [21])
        np.testing.assert_allclose(convert([100000], 'Pa','kPa'), [100])
        np.testing.assert_allclose(convert([410], 'mm','cm'), [41])
    def test_units_reject_dimension_mismatch(self):
        with self.assertRaises(ValueError): convert([4], 'cm', 'cm/s')
    def test_unknown_units(self):
        with self.assertRaises(ValueError): convert([1], 'mph', 'cm/s')
    def test_missing_columns(self): self.assertBlocked(self.df.drop(columns=['pressure_kpa']))
    def test_missing_run(self):
        self.df.loc[0,'run_id'] = None; self.assertBlocked()
    def test_empty_dataset(self): self.assertBlocked(self.df.iloc[:0])
    def test_duplicate_id(self):
        self.df.loc[1,'observation_id'] = self.df.loc[0,'observation_id']; self.assertBlocked()
    def test_duplicate_row(self): self.assertBlocked(pd.concat([self.df, self.df.iloc[:1]], ignore_index=True))
    def test_size_is_not_rate(self):
        self.df['outcome_type'] = 'steady_flame_size'; self.df['outcome_unit'] = 'cm'; self.assertBlocked()
    def test_no_target(self):
        self.df[TARGET] = np.nan; self.assertBlocked()
    def test_numeric_invalid(self):
        for value in ['not a number', np.inf, -1]:
            df = self.df.copy(); df['pressure_kpa'] = df.pressure_kpa.astype(object); df.loc[0,'pressure_kpa'] = value
            self.assertBlocked(df)
    def test_oxygen_physical_range(self):
        self.df.loc[0,'oxygen_percent'] = 110; self.assertBlocked()
    def test_unit_column_mismatch(self):
        self.df['flow_velocity_cm_s__unit'] = 'm/s'; self.assertBlocked()
    def test_missing_atmosphere(self):
        for col in ['oxygen_percent', 'pressure_kpa']:
            d = self.df.copy(); d[col] = np.nan; self.assertBlocked(d)
    def test_conflicting_labels(self):
        self.df.loc[0,'material'] = 'Synthetic_Fabric'; self.assertBlocked()
    def test_invalid_flow_direction(self):
        self.df.loc[0,'flow_direction'] = 'backwards'; self.assertBlocked()
    def test_missing_source(self):
        self.df.loc[0,'source_id'] = 'unknown'; self.assertBlocked()
    def test_source_manifest_duplicate(self):
        m = pd.concat([self.manifest,self.manifest], ignore_index=True)
        self.assertEqual(validate(self.df,m,self.cfg.geometry,True)['status'],'INVALID')
    def test_unverified_geometry(self):
        self.df['geometry_status'] = 'uncertain'; self.assertBlocked()
    def test_one_group(self):
        self.df['dependency_group_id'] = 'ONE'; self.assertBlocked()
    def test_two_groups_insufficient(self): self.assertBlocked(self.df.iloc[:12])
    def test_same_run_multiple_groups(self):
        self.df['run_id'] = 'ONE'; self.assertBlocked()
    def test_same_campaign_blocks_campaign_cv(self):
        self.df['campaign_id'] = 'ONE'; self.assertBlocked(cfg=replace(self.cfg,strategy='campaign'))
    def test_group_separation_all_strategies(self):
        for strategy in ['logo','groupkfold','campaign']:
            pairs = split_indices(self.df, replace(self.cfg,strategy=strategy))
            for tr,te in pairs:
                self.assertFalse(set(self.df.iloc[tr].dependency_group_id)&set(self.df.iloc[te].dependency_group_id))
                self.assertFalse(set(tr)&set(te))
    def test_dependence_crossing_campaigns(self):
        self.df.loc[self.df.campaign_id.eq('SYN-C1'),'dependency_group_id'] = 'SYN-G0'
        self.assertBlocked(cfg=replace(self.cfg,strategy='campaign'))
    def test_cross_scale_holdout(self):
        self.df.loc[self.df.campaign_id.eq('SYN-C2'),'investigation_id'] = 'SYN-LARGE'
        result = self.ev(cfg=replace(self.cfg,strategy='cross_scale',holdout_investigation='SYN-LARGE'))
        self.assertEqual(result['status'],'SYNTHETIC_EVALUATION_ONLY')
        self.assertEqual(result['metrics']['mean']['n_test_observations'],24)
    def test_cross_scale_overlap(self):
        self.df.loc[0,'investigation_id'] = 'SYN-LARGE'
        self.assertBlocked(cfg=replace(self.cfg,strategy='cross_scale',holdout_investigation='SYN-LARGE'))
    def test_unseen_category_test_fold(self):
        self.df.loc[:5,'material'] = 'unseen'; self.assertBlocked()
    def test_mean_training_only(self):
        tr, te = split_indices(self.df,self.cfg)[0]
        m = build('mean',self.cfg).fit(self.df.iloc[tr],self.df.iloc[tr][TARGET])
        np.testing.assert_allclose(m.predict(self.df.iloc[te]),self.df.iloc[tr][TARGET].mean())
        other = self.df.copy(); other.loc[te,TARGET] = 999
        m2 = build('mean',self.cfg).fit(other.iloc[tr],other.iloc[tr][TARGET])
        np.testing.assert_allclose(m.predict(self.df.iloc[te]),m2.predict(self.df.iloc[te]))
    def test_scaler_training_only(self):
        tr,te = split_indices(self.df,self.cfg)[0]
        m = build('condition_ridge',self.cfg).fit(self.df.iloc[tr],self.df.iloc[tr][TARGET])
        scaler = m.named_steps['preprocess'].named_transformers_['numeric']
        np.testing.assert_allclose(scaler.mean_, self.df.iloc[tr][['flow_velocity_cm_s','oxygen_percent','pressure_kpa']].mean())
        other = self.df.copy(); other.loc[te,'flow_velocity_cm_s'] = 10000
        m2 = build('condition_ridge',self.cfg).fit(other.iloc[tr],other.iloc[tr][TARGET])
        np.testing.assert_array_equal(scaler.mean_, m2.named_steps['preprocess'].named_transformers_['numeric'].mean_)
    def test_target_change_does_not_change_its_fold_prediction(self):
        oid=self.df.iloc[0].observation_id; self.df.loc[0,TARGET] += 100
        other=self.ev()
        a=[r['predicted_cm_s'] for r in self.report['predictions'] if r['observation_id']==oid]
        b=[r['predicted_cm_s'] for r in other['predictions'] if r['observation_id']==oid]
        np.testing.assert_array_equal(a,b)
    def test_ratio_feature(self):
        out=PhysicsFeatures(True).fit_transform(self.df)
        np.testing.assert_allclose(out.width_height_ratio,self.df.sample_width_cm/self.df.duct_height_cm)
        self.assertNotIn('width_height_ratio',self.df)
    def test_ratio_preconditions(self):
        self.assertBlocked(cfg=replace(self.cfg,width_height_ratio=True))
    def test_feature_leakage_rejected(self): self.assertBlocked(cfg=replace(self.cfg,geometry=(TARGET,)))
    def test_plan_not_frozen(self): self.assertBlocked(cfg=replace(self.cfg,frozen_before_evaluation=False))
    def test_metrics_known(self):
        m=metrics([1,3],[2,1]); self.assertAlmostEqual(m['mae_cm_s'],1.5)
        self.assertAlmostEqual(m['rmse_cm_s'],np.sqrt(2.5)); self.assertAlmostEqual(m['bias_cm_s'],-.5)
    def test_metrics_bad_shape(self):
        for a,b in [([],[]),([1],[1,2]),([np.nan],[1])]:
            with self.assertRaises(ValueError): metrics(a,b)
    def test_equal_model_observations(self):
        p=pd.DataFrame(self.report['predictions']); sets=[set(g.observation_id) for _,g in p.groupby('model')]
        self.assertTrue(all(s==sets[0] for s in sets)); self.assertEqual(len(sets[0]),72)
    def test_constant_target(self):
        self.df[TARGET]=.2; r=self.ev()
        for m in r['metrics'].values(): self.assertAlmostEqual(m['mae_cm_s'],0)
    def test_synthetic_never_real(self):
        self.assertEqual(evaluate(self.df,self.manifest,self.cfg)['status'],'VALIDATION_NOT_SUPPORTED')
    def test_approval_bound_to_data(self):
        self.df.loc[0,TARGET] += .001
        with self.assertRaises(ValueError): activate(self.df,self.manifest,self.cfg,'geometry_ridge',approval_for(self.report),True)
    def test_selection_leakage_refused(self):
        a=approval_for(self.report);a['selection_independent_of_test']=False
        with self.assertRaises(ValueError): activate(self.df,self.manifest,self.cfg,'geometry_ridge',a,True)
    def test_supported_demo(self):
        result=predict(self.scenario,self.bundle)
        self.assertEqual(result['status'],'SUPPORTED');self.assertTrue(result['synthetic'])
        jsonschema.validate(result,RESPONSE_SCHEMA)
    def test_unsupported_material(self):
        result=predict(dict(self.scenario,material='unknown'),self.bundle)
        self.assertEqual(result['status'],'UNSUPPORTED'); self.assertIsNone(result['predicted_flame_spread_rate_cm_s'])
    def test_unseen_direction(self):
        result=predict(dict(self.scenario,flow_direction='stagnant'),self.bundle)
        self.assertEqual(result['status'],'UNSUPPORTED')
    def test_far_outside_domain(self):
        result=predict(dict(self.scenario,flow_velocity_cm_s=900),self.bundle)
        self.assertEqual(result['status'],'UNSUPPORTED');self.assertTrue(result['out_of_domain_warnings'])
    def test_unverified_scenario_geometry(self):
        self.assertEqual(predict(dict(self.scenario,geometry_status='unreviewed'),self.bundle)['status'],'UNSUPPORTED')
    def test_lunar_gravity_refused(self):
        self.assertEqual(predict(dict(self.scenario,gravity_regime='lunar'),self.bundle)['status'],'UNSUPPORTED')
    def test_no_model_limited(self):
        r=predict(self.scenario,evidence=self.df);self.assertEqual(r['status'],'LIMITED_EVIDENCE')
        self.assertIsNone(r['predicted_flame_spread_rate_cm_s']);jsonschema.validate(r,RESPONSE_SCHEMA)
    def test_no_model_unknown_evidence(self):
        self.assertEqual(predict(dict(self.scenario,material='unknown'),evidence=self.df)['status'],'UNSUPPORTED')
    def test_invalid_scenarios(self):
        for s in [None, {}, [], dict(self.scenario,oxygen_percent=float('nan')),dict(self.scenario,material=[]),dict(self.scenario,pressure_kpa=True)]:
            r=predict(s,self.bundle);self.assertEqual(r['status'],'UNSUPPORTED');jsonschema.validate(r,RESPONSE_SCHEMA)
    def test_missing_input(self):
        del self.scenario['pressure_kpa'];self.assertEqual(predict(self.scenario,self.bundle)['status'],'UNSUPPORTED')
    def test_joint_domain(self):
        train=self.df.copy();train['oxygen_percent']=train.flow_velocity_cm_s
        scenario=scenario_from_row(train.iloc[0]);scenario['oxygen_percent']=float(train.oxygen_percent.max())
        self.assertTrue(check_domain(train,scenario,replace(self.cfg,max_domain_distance=.01)))
    def test_serialization(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'model.joblib';save(self.bundle,path)
            self.assertEqual(predict(self.scenario,self.bundle),predict(self.scenario,load(path)))
    def test_strict_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'response.json';write_json(p,predict(self.scenario,self.bundle))
            jsonschema.validate(json.loads(p.read_text()),RESPONSE_SCHEMA)
            with self.assertRaises(ValueError): write_json(p,{'bad':float('nan')})
    def test_response_schema_refuses_numeric_abstention(self):
        r=predict(self.scenario,evidence=self.df);r['predicted_flame_spread_rate_cm_s']=1
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(r,RESPONSE_SCHEMA)
    def test_starter_adapter_missing_status_regression(self):
        raw=pd.read_csv(ROOT/'data/current/ignis_experiments_starter.csv'); original=raw.copy()
        adapted=adapt_current(raw,'starter')
        self.assertTrue(adapted[TARGET].isna().all());self.assertEqual(adapted.iloc[0].sample_width_cm,41)
        pd.testing.assert_frame_equal(raw,original)
        self.assertEqual(validate(adapted,self.manifest)['status'],'INVALID')
    def test_candidate_adapter_refuses_evaluation(self):
        raw=pd.read_csv(ROOT/'data/current/ignis_bass_saffire_candidate_observations.csv')
        d=adapt_current(raw,'candidate');self.assertEqual(len(d),23);self.assertTrue(d.run_id.isna().all())
        self.assertBlocked(d)
    def test_reviewed_cohort_selection(self):
        from ignis_ml.cohort import select_cohort
        sub, ledger=select_cohort(self.df, {'review_reference':'SYN', 'reason':'Demonstration', 'equals':{'flow_direction':['opposed']}})
        self.assertEqual(len(sub),36);self.assertEqual(len(ledger['excluded_observation_ids']),36)
        with self.assertRaises(ValueError): select_cohort(self.df, {'review_reference':'SYN', 'reason':'bad', 'equals':{TARGET:[.2]}})

    def test_audit_veto(self):
        for flag in ['approved_for_ml','independent_run_verified']:
            d=self.df.copy();d[flag]=False;self.assertBlocked(d)

    def test_ratio_model_fits(self):
        cfg=replace(self.cfg,geometry=('sample_width_cm','duct_height_cm'),width_height_ratio=True)
        r=self.ev(cfg=cfg);self.assertEqual(r['status'],'SYNTHETIC_EVALUATION_ONLY')
        self.assertIn('width_height_ratio',r['metrics']['geometry_ridge']['features'])

    def test_negative_model_prediction_abstains(self):
        from sklearn.dummy import DummyRegressor
        from copy import deepcopy
        b=deepcopy(self.bundle);b.estimator=DummyRegressor(strategy='constant',constant=-1).fit(self.df,self.df[TARGET])
        r=predict(self.scenario,b);self.assertEqual(r['status'],'UNSUPPORTED');self.assertIsNone(r['predicted_flame_spread_rate_cm_s'])

    def test_plot_pipeline(self):
        with tempfile.TemporaryDirectory() as d:
            paths=make_plots(self.df,self.report,d);self.assertEqual(len(paths),7)
            for path in paths:self.assertGreater(Path(path).stat().st_size,1000)

if __name__=='__main__': unittest.main(verbosity=2)
