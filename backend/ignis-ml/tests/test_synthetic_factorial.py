"""Synthetic-only verification of the established factorial estimator."""
import unittest
import pandas as pd

from scripts.verify_factorial_synthetic import SCENARIOS, simulated_burns, simulated_height_sessions, true_interaction
from ignis_ml.factorial import analyze_burns


class SyntheticFactorialVerificationTests(unittest.TestCase):
    def analyze(self, scenario):
        data, means = simulated_burns(scenario, SCENARIOS[scenario], blocks=20)
        result = analyze_burns(data, design='randomized_complete_blocks', controls_verified=True)
        return data, means, result

    def test_positive_interaction_detected(self):
        _, means, result = self.analyze('positive')
        self.assertAlmostEqual(true_interaction(means), .08)
        self.assertEqual(result['status'], 'ESTIMATED')
        self.assertGreater(result['interval_cm_s'][0], 0.)
        self.assertLess(abs(result['interaction_cm_s']-.08), .025)

    def test_null_interaction_interval_contains_zero(self):
        _, means, result = self.analyze('zero')
        self.assertAlmostEqual(true_interaction(means), 0.)
        self.assertLessEqual(result['interval_cm_s'][0], 0.)
        self.assertGreaterEqual(result['interval_cm_s'][1], 0.)
        self.assertLess(abs(result['interaction_cm_s']), .025)

    def test_negative_interaction_detected(self):
        _, means, result = self.analyze('negative')
        self.assertAlmostEqual(true_interaction(means), -.08)
        self.assertLess(result['interval_cm_s'][1], 0.)
        self.assertLess(abs(result['interaction_cm_s']+.08), .025)

    def test_alternative_height_session_design(self):
        data, means = simulated_height_sessions('test_height_sessions', SCENARIOS['positive'], sessions_per_height=12)
        result = analyze_burns(data, design='randomized_height_sessions', controls_verified=True)
        self.assertAlmostEqual(true_interaction(means), .08)
        self.assertEqual(result['status'], 'ESTIMATED')
        self.assertGreater(result['interval_cm_s'][0], 0.)
        self.assertEqual(result['sessions_per_height'], {'shallow':12, 'deep':12})

    def test_refuses_unverified_controls(self):
        data, _, _ = self.analyze('positive')
        result = analyze_burns(data, design='randomized_complete_blocks', controls_verified=False)
        self.assertEqual(result['status'], 'ANALYSIS_NOT_SUPPORTED')
        self.assertIsNone(result['interaction_cm_s'])

    def test_refuses_missing_factorial_cell(self):
        data, _, _ = self.analyze('positive')
        reduced = data.loc[~((data.width_cm==5) & (data.full_duct_height_cm==30.5))]
        result = analyze_burns(reduced, design='randomized_complete_blocks', controls_verified=True)
        self.assertEqual(result['status'], 'ANALYSIS_NOT_SUPPORTED')
        self.assertIsNone(result['interaction_cm_s'])

    def test_refuses_reused_specimen(self):
        data, _, _ = self.analyze('positive')
        repeated = pd.concat([data, data.iloc[[0]]], ignore_index=True)
        result = analyze_burns(repeated, design='randomized_complete_blocks', controls_verified=True)
        self.assertEqual(result['status'], 'ANALYSIS_NOT_SUPPORTED')
        self.assertIsNone(result['interaction_cm_s'])

    def test_refuses_unsupported_design(self):
        data, _, _ = self.analyze('positive')
        result = analyze_burns(data, design='unreviewed_design', controls_verified=True)
        self.assertEqual(result['status'], 'ANALYSIS_NOT_SUPPORTED')
        self.assertIsNone(result['interaction_cm_s'])


if __name__ == '__main__':
    unittest.main()
