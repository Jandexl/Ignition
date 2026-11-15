import tempfile
import unittest
from pathlib import Path
import pandas as pd
from scipy.stats import t
from ignis_ml.science import export_evidence, CELLS
from ignis_ml.factorial import analyze_burns

class RevisionTests(unittest.TestCase):
    def test_historical_export(self):
        with tempfile.TemporaryDirectory() as d:
            r=export_evidence(Path(__file__).resolve().parents[1]/'data/revision',Path(d)/'cases.json')
        self.assertEqual(len(r['table1_records']),8)
        self.assertEqual(sorted(map(len,r['alternative_source_claims'].values())),[2,23])
        cases=r['comparison_cases']
        self.assertEqual([c['difference_cm_s'] for c in cases],[.03,.03,.18])
        self.assertEqual([c['percent_change'] for c in cases],[16.67,13.04,100])
        self.assertTrue(all(c['comparability'] for c in cases))
        self.assertIsNone(r['prediction_cm_s'])
        ready=r['factorial_readiness']
        self.assertIsNone(ready['interaction_cm_s'])
        self.assertEqual(ready['missing_configuration'],[dict(width_cm=5.,full_duct_height_cm=30.5,historical_ids=[])])
        self.assertFalse(any(row['approved_for_ml'] for row in r['table1_records']))

    def setUp(self):
        rows=[]
        for block in range(3):
            for w,h in CELLS:
                ident=f'{block}-{w}-{h}'
                rows.append(dict(block_id=block,burn_id=ident,specimen_id=ident,width_cm=w,
                    full_duct_height_cm=h,spread_cm_s=1+(block+1)*(w==40.6 and h==30.5),
                    included=True,exclusion_reason=''))
        self.df=pd.DataFrame(rows)

    def analyze(self,df):
        return analyze_burns(df,design='randomized_complete_blocks',controls_verified=True)

    def test_block_interval(self):
        r=self.analyze(self.df)
        self.assertEqual(r['interaction_cm_s'],2)
        self.assertAlmostEqual(r['interval_cm_s'][0],2-t.ppf(.975,2)/3**.5)

    def test_missing_cell_or_repeat(self):
        for df in [self.df.iloc[1:],pd.concat([self.df,self.df.iloc[:1]])]:
            self.assertIsNone(self.analyze(df)['interaction_cm_s'])

    def test_split_plot_refused(self):
        r=analyze_burns(self.df,design='height_by_session',controls_verified=True)
        self.assertIsNone(r['interval_cm_s'])

    def test_session_randomization_unit(self):
        df=self.df.copy()
        df['block_id']=df.block_id.astype(str)+'-'+df.full_duct_height_cm.astype(str)
        result=analyze_burns(df,design='randomized_height_sessions',controls_verified=True)
        self.assertEqual(result['sessions_per_height'],{'shallow':3,'deep':3})
        self.assertAlmostEqual(result['interaction_cm_s'],2)
        self.assertAlmostEqual(result['interval_cm_s'][1],2+t.ppf(.975,2)/3**.5)
