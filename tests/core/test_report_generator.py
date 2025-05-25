# tests/core/test_report_generator.py
import unittest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple # Added Tuple for type hinting if needed
# Important: Adjust import if ReportGenerator path or class name changes
try:
    from cacm_adk_core.report_generator.report_generator import ReportGenerator
except ImportError:
    ReportGenerator = None

class TestEnhancedReportGenerator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if ReportGenerator is None:
            raise unittest.SkipTest("ReportGenerator component not found or import error.")
        cls.reporter = ReportGenerator()

    def test_map_score_to_sp(self):
        self.assertEqual(self.reporter._map_score_to_sp(800), "AAA")
        self.assertEqual(self.reporter._map_score_to_sp(750), "AA")
        self.assertEqual(self.reporter._map_score_to_sp(700), "A")
        self.assertEqual(self.reporter._map_score_to_sp(650), "BBB")
        self.assertEqual(self.reporter._map_score_to_sp(600), "BB")
        self.assertEqual(self.reporter._map_score_to_sp(550), "B")
        self.assertEqual(self.reporter._map_score_to_sp(500), "CCC")
        self.assertEqual(self.reporter._map_score_to_sp(400), "CC/C/D or Not Rated")
        self.assertEqual(self.reporter._map_score_to_sp(None), "Not Rated")

    def test_map_score_to_snc(self):
        self.assertEqual(self.reporter._map_score_to_snc(700), "Pass")
        self.assertEqual(self.reporter._map_score_to_snc(600), "Special Mention (SM)")
        self.assertEqual(self.reporter._map_score_to_snc(500), "Substandard")
        self.assertEqual(self.reporter._map_score_to_snc(400), "Doubtful/Loss")
        self.assertEqual(self.reporter._map_score_to_snc(None), "Ungraded")

    def test_generate_mocked_outlook(self):
        # Check it returns one of the expected values for different score ranges
        self.assertIn(self.reporter._generate_mocked_outlook(760), ["Positive", "Stable"])
        self.assertIn(self.reporter._generate_mocked_outlook(560), ["Stable", "Negative"])
        self.assertEqual(self.reporter._generate_mocked_outlook(None), "Uncertain") # Corrected: Should be "Uncertain" for None


    def test_generate_xai_and_rationale(self):
        # Basic test, more complex scenarios could be added
        xai, rationale = self.reporter._generate_mocked_xai_and_rationale(
            720, {"profitabilityMetric": {"value": 0.25}, "leverageRatio": {"value": 0.5}}
        )
        self.assertTrue(len(xai) > 0)
        self.assertTrue(len(rationale) > 50) # Expect some decent length
        self.assertIn("Strong profitability demonstrated.", rationale)
        self.assertIn("Conservative leverage position noted.", rationale)

        xai_low, rationale_low = self.reporter._generate_mocked_xai_and_rationale(
            530, {"profitabilityMetric": {"value": 0.02}, "leverageRatio": {"value": 5.0}, "qualitativeScore": {"value": 30}}
        )
        self.assertIn("Low profitability ratios observed.", xai_low)
        self.assertIn("High leverage position.", xai_low)
        self.assertIn("Weak qualitative factors (e.g., management, industry).", xai_low)
        # Corrected: Check for a specific part of the generated rationale that should exist
        self.assertIn("Qualitative assessments indicate some underlying weaknesses.", rationale_low) 


    def test_generate_full_sme_report_high_score(self):
        mock_outputs = {
            "creditScore": {"value": 780, "description": "Final score"},
            "profitabilityMetric": {"value": 0.25},
            "leverageRatio": {"value": 1.2},
            "qualitativeScore": {"value": 70}
        }
        report = self.reporter.generate_sme_score_report(mock_outputs, sme_identifier="SME_HighCo")

        self.assertEqual(report["reportHeader"]["smeIdentifier"], "SME_HighCo")
        self.assertEqual(report["creditRating"]["spScaleEquivalent"], "AA")
        self.assertEqual(report["creditRating"]["sncRegulatoryEquivalent"], "Pass")
        self.assertIn(report["executiveSummary"]["outlook"], ["Positive", "Stable"])
        self.assertEqual(report["executiveSummary"]["overallAssessment"], "Low Risk") # Overridden by high score
        self.assertTrue(len(report["keyRiskFactors_XAI"]) > 0)
        self.assertTrue(len(report["detailedRationale"]) > 0)
        self.assertEqual(report["supportingMetrics"]["creditScoreRaw"]["value"], 780)

    def test_generate_full_sme_report_low_score(self):
        mock_outputs = {
            "creditScore": {"value": 520},
            "profitabilityMetric": {"value": 0.03},
            "leverageRatio": {"value": 4.0},
            "qualitativeScore": {"value": 40}
        }
        report = self.reporter.generate_sme_score_report(mock_outputs, sme_identifier="SME_LowCo")

        self.assertEqual(report["creditRating"]["spScaleEquivalent"], "CCC")
        self.assertEqual(report["creditRating"]["sncRegulatoryEquivalent"], "Substandard")
        # For score 520, outlook can be "Stable", "Negative", or "Developing"
        self.assertIn(report["executiveSummary"]["outlook"], ["Stable", "Negative", "Developing"])
        self.assertEqual(report["executiveSummary"]["overallAssessment"], "Medium-High Risk")
        self.assertIn("Low profitability ratios observed.", report["keyRiskFactors_XAI"])
        self.assertIn("High leverage position.", report["keyRiskFactors_XAI"])

    def test_get_output_value_helper(self):
        # Test cases from previous ReportGenerator version
        self.assertEqual(self.reporter._get_output_value({"value": 10}), 10)
        self.assertEqual(self.reporter._get_output_value({"val": 10, "desc": "d"}), {"val": 10, "desc": "d"})
        self.assertEqual(self.reporter._get_output_value(100), 100) # Direct value
        self.assertEqual(self.reporter._get_output_value(None, default="Test"), "Test")
        self.assertEqual(self.reporter._get_output_value({"value": None}, default="Test"), None)
        self.assertEqual(self.reporter._get_output_value({}, default="EmptyReplaced"), "EmptyReplaced") # Empty dict replaced by default


if __name__ == '__main__':
    unittest.main()
