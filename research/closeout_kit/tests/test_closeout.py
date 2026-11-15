import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def read(p): return json.loads((ROOT/'data'/p).read_text())

class CloseoutConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.science=read('scientific_comparisons.json')
        cls.conflicts=read('source_conflicts.json')['conflicts']
        cls.status=read('science_project_status.json')
        cls.brand=read('brand_copy.json')
        cls.ui=read('final_ui_qa_cases.json')

    def test_01_all_table1_records_are_published_and_not_ml_approved(self):
        rows=self.science['table1_records']
        self.assertEqual(len(rows),8)
        self.assertEqual(len({x['record_id'] for x in rows}),8)
        self.assertTrue(all(x['approved_for_ml'] is False for x in rows))

    def test_02_three_rates_and_percent_changes(self):
        cases={(x['baseline'],x['comparison']):x for x in self.science['comparison_cases']}
        expected={('I-1','II-5'):(0.18,0.21,16.67),('III-1','II-6'):(0.23,0.26,13.04),('I-1','IV-SIBAL'):(0.18,0.36,100.)}
        self.assertEqual(set(cases),set(expected))
        for key,(a,b,pct) in expected.items():
            with self.subTest(pair=key):
                c=cases[key]
                self.assertEqual(c['measurements']['spread_cm_s'],[a,b])
                self.assertAlmostEqual(c['percent_change'],pct,places=2)

    def test_03_lengths_distinct_and_warnings_present(self):
        for c in self.science['comparison_cases']:
            self.assertIn('flame_length_cm',c['measurements'])
            self.assertIn('spread_cm_s',c['measurements'])
            self.assertTrue(c['confounding_warning'])
        cases=self.science['comparison_cases']
        self.assertEqual(cases[0]['measurements']['flame_length_cm'],[4.,4.])
        self.assertEqual(cases[1]['measurements']['flame_length_cm'],[5.,5.])

    def test_04_factorial_hypothesis_not_confirmatory(self):
        f=self.science['factorial_readiness']
        self.assertIsNone(f['interaction_cm_s'])
        self.assertIsNone(f['interval_cm_s'])
        missing=[c for c in f['cells'] if not c['historical_ids']]
        self.assertEqual(len(missing),1)
        self.assertEqual((missing[0]['width_cm'],missing[0]['full_duct_height_cm']),(5.0,30.5))

    def test_05_nasa_prediction_remains_refused(self):
        self.assertEqual(self.science['prediction_status'],'VALIDATION_NOT_SUPPORTED')
        self.assertIsNone(self.science['prediction_cm_s'])

    def test_06_psi100_airflow_discrepancy_remains_unresolved(self):
        c=next(x for x in self.conflicts if x['conflict_id']=='SAFFIRE_III1_FLOW_PSI100_VS_OLSON')
        self.assertEqual({x['source_id']:x['value'] for x in c['claims']},{'OLSON-2023-T1':25,'NASA-PSI-100':30})
        self.assertEqual(c['resolution_status'],'unresolved')
        self.assertTrue(all(x['url'].startswith('https://') for x in c['claims']))

    def test_07_iv_candidate_not_verified_or_double_counted(self):
        c=next(x for x in self.conflicts if x['conflict_id']=='SAFFIRE_IV1_IV_SIBAL_ALIAS')
        self.assertEqual(c['match_status'],'probable_not_confirmed')
        self.assertIs(c['count_as_additional_independent_run'],False)

    def test_08_status_brand_and_qa_contract(self):
        self.assertEqual(self.status['science_research_status'],'COMPLETE_FOR_HACKATHON')
        self.assertEqual(self.brand['hero_line_1'],'ZERO GUESSING.')
        self.assertEqual(self.brand['hero_line_2'],'ZERO HIDDEN UNCERTAINTY.')
        self.assertIn('rule-based',self.brand['assistant_disclosure'])
        self.assertEqual(len(self.ui['cases']),8)
        self.assertEqual(len({x['id'] for x in self.ui['cases']}),8)

if __name__=='__main__': unittest.main()
