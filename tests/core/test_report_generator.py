# tests/core/test_report_generator.py
import unittest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, List # Ensure List is imported
try:
    from cacm_adk_core.report_generator.report_generator import ReportGenerator
except ImportError:
    ReportGenerator = None

class TestEnhancedPersonaReportGenerator(unittest.TestCase): # Renamed class

    @classmethod
    def setUpClass(cls):
        if ReportGenerator is None:
            raise unittest.SkipTest("ReportGenerator component not found or import error.")
        cls.reporter = ReportGenerator()

    # --- Tests for Helper Methods (including new persona methods) ---

    def test_map_score_to_sp(self):
        self.assertEqual(self.reporter._map_score_to_sp(800), "AAA")
        self.assertEqual(self.reporter._map_score_to_sp(None), "Not Rated")

    def test_map_score_to_snc_updated(self): # Renamed for clarity
        self.assertEqual(self.reporter._map_score_to_snc(700), "Pass")
        self.assertEqual(self.reporter._map_score_to_snc(600), "Special Mention") # Updated expected value
        self.assertEqual(self.reporter._map_score_to_snc(500), "Substandard")
        self.assertEqual(self.reporter._map_score_to_snc(400), "Doubtful") # Updated expected value
        self.assertEqual(self.reporter._map_score_to_snc(300), "Loss")     # Updated expected value
        self.assertEqual(self.reporter._map_score_to_snc(None), "Ungraded")

    def test_generate_mocked_outlook(self):
        self.assertIn(self.reporter._generate_mocked_outlook(760), ["Positive", "Stable"])
        self.assertEqual(self.reporter._generate_mocked_outlook(None), "Uncertain")

    def test_generate_fundamental_perspective(self):
        perspective_strong = self.reporter._generate_fundamental_perspective(
            750, {"profitabilityMetric": {"value": 0.20}, "leverageRatio": {"value": 1.0}, "freeCashFlowYield": {"value": 0.07}}, None
        )
        self.assertIn("Profitability (e.g., margin 20.00%) appears strong", perspective_strong)
        self.assertIn("Leverage (e.g., D/E 1.00x) is considered low", perspective_strong)
        self.assertIn("Free Cash Flow Yield (7.00%) indicates strong", perspective_strong)

        perspective_weak = self.reporter._generate_fundamental_perspective(
            550, {"profitabilityMetric": 0.02, "leverageRatio": 4.5}, None # Using direct value
        )
        self.assertIn("Profitability (e.g., margin 2.00%) appears weak", perspective_weak)
        self.assertIn("Leverage (e.g., D/E 4.50x) is considered high", perspective_weak)
        self.assertNotIn("Free Cash Flow Yield", perspective_weak) # Metric not provided

        perspective_mixed = self.reporter._generate_fundamental_perspective(
            650, {"profitabilityMetric": {"value":0.10}, "leverageRatio": {"value":2.0}}, {} # Empty cacm_inputs
        )
        self.assertIn("moderate", perspective_mixed) # For both profitability and leverage

        perspective_na = self.reporter._generate_fundamental_perspective(600, {}, None)
        self.assertIn("not strongly conclusive", perspective_na)


    def test_generate_regulatory_snc_perspective(self):
        self.assertIn("no undue criticism", self.reporter._generate_regulatory_snc_perspective("Pass", 700, {}))
        self.assertIn("potential weaknesses", self.reporter._generate_regulatory_snc_perspective("Special Mention", 600, {}))
        self.assertIn("inadequately protected", self.reporter._generate_regulatory_snc_perspective("Substandard", 500, {}))
        self.assertIn("highly questionable and improbable", self.reporter._generate_regulatory_snc_perspective("Doubtful", 400, {}))
        self.assertIn("uncollectible", self.reporter._generate_regulatory_snc_perspective("Loss", 300, {}))

    def test_generate_market_outlook_perspective(self):
        self.assertIn("favorable market conditions", self.reporter._generate_market_outlook_perspective("Positive", None))
        self.assertIn("challenging market conditions", self.reporter._generate_market_outlook_perspective("Negative", {}))
        self.assertIn("evolving market landscape", self.reporter._generate_market_outlook_perspective("Developing", None))

    def test_generate_strategic_commentary(self):
        comment_ma = self.reporter._generate_strategic_commentary(
            {"strategic_initiative_type": "M&A"}, 
            {"mergerAndAcquisitionActivityIndicator": {"value": True}}
        )
        self.assertIn("M&A activities", comment_ma)

        comment_organic = self.reporter._generate_strategic_commentary(
            {"strategic_initiative_type": "Organic Growth"}, {}
        )
        self.assertIn("organic growth", comment_organic) # Default if no M&A hint

    def test_generate_mocked_xai_and_rationale_orchestration(self):
        xai, rationale = self.reporter._generate_mocked_xai_and_rationale(
            720, "Pass", "Positive", 
            {"profitabilityMetric": {"value": 0.25}, "leverageRatio": {"value": 0.5}}, 
            None
        )
        self.assertTrue(len(xai) > 0)
        self.assertIn("Fundamental View:", rationale)
        self.assertIn("SNC Perspective:", rationale)
        self.assertIn("Market Outlook:", rationale)
        self.assertIn("Strategic Note:", rationale)
        self.assertNotIn("High financial leverage.", xai) # Leverage is low
        self.assertNotIn("Weak profitability margins.", xai) # Profitability is high

        xai_low, _ = self.reporter._generate_mocked_xai_and_rationale(
            530, "Substandard", "Negative",
            {"profitabilityMetric": 0.02, "leverageRatio": 5.0},
            None
        )
        self.assertIn("High financial leverage.", xai_low)
        self.assertIn("Weak profitability margins.", xai_low)
        self.assertIn("Regulatory concerns indicated by SNC rating: Substandard.", xai_low) # Added period
        self.assertIn("Negative market/business outlook.", xai_low)


    # --- Tests for the main report generation method ---
    def test_generate_full_sme_report_high_score_enhanced_rationale(self): # Renamed
        mock_outputs = {
            "creditScore": {"value": 780}, "profitabilityMetric": {"value": 0.25},
            "leverageRatio": {"value": 1.2}, "freeCashFlowYield": {"value": 0.08},
            "qualitativeScore": {"value": 70}
        }
        report = self.reporter.generate_sme_score_report(mock_outputs, sme_identifier="SME_HighCo_Enhanced")

        self.assertEqual(report["creditRating"]["spScaleEquivalent"], "AA")
        self.assertEqual(report["creditRating"]["sncRegulatoryEquivalent"], "Pass")
        self.assertIn(report["executiveSummary"]["outlook"], ["Positive", "Stable"])
        self.assertEqual(report["executiveSummary"]["overallAssessment"], "Low Risk")
        
        self.assertTrue(len(report["detailedRationale"]) > 100, "Detailed rationale should be substantial.")
        self.assertIn("Fundamental View:", report["detailedRationale"])
        self.assertIn("SNC Perspective: The 'Pass' rating suggests", report["detailedRationale"])
        self.assertIn("Market Outlook: The current", report["detailedRationale"])
        self.assertIn("Strategic Note:", report["detailedRationale"])
        
        # Check XAI factors based on the new logic
        self.assertTrue(any("No overriding individual risk factors" in factor for factor in report["keyRiskFactors_XAI"]) 
                        or len(report["keyRiskFactors_XAI"]) == 0, # It's possible no specific factors are triggered for high score
                        "XAI factors for high score seem incorrect.")


    def test_generate_full_sme_report_low_score_enhanced_rationale(self): # Renamed
        mock_outputs = {
            "creditScore": {"value": 520}, "profitabilityMetric": {"value": 0.03},
            "leverageRatio": {"value": 4.0}, "freeCashFlowYield": {"value": 0.01},
            "qualitativeScore": {"value": 40}
        }
        report = self.reporter.generate_sme_score_report(mock_outputs, sme_identifier="SME_LowCo_Enhanced")

        self.assertEqual(report["creditRating"]["spScaleEquivalent"], "CCC")
        self.assertEqual(report["creditRating"]["sncRegulatoryEquivalent"], "Substandard")
        self.assertIn(report["executiveSummary"]["outlook"], ["Stable", "Negative", "Developing"])
        self.assertEqual(report["executiveSummary"]["overallAssessment"], "Medium-High Risk")

        self.assertTrue(len(report["detailedRationale"]) > 100)
        self.assertIn("Fundamental View: Profitability (e.g., margin 3.00%) appears weak.", report["detailedRationale"])
        self.assertIn("Leverage (e.g., D/E 4.00x) is considered high.", report["detailedRationale"])
        self.assertIn("SNC Perspective: The 'Substandard' rating means", report["detailedRationale"])
        
        self.assertIn("High financial leverage.", report["keyRiskFactors_XAI"])
        self.assertIn("Weak profitability margins.", report["keyRiskFactors_XAI"])
        self.assertIn("Regulatory concerns indicated by SNC rating: Substandard.", report["keyRiskFactors_XAI"]) # Added period
        

    def test_get_output_value_helper(self): # Kept from previous version
        self.assertEqual(self.reporter._get_output_value({"value": 10}), 10)
        self.assertEqual(self.reporter._get_output_value({"val": 10, "desc": "d"}), {"val": 10, "desc": "d"})
        self.assertEqual(self.reporter._get_output_value(100), 100)
        self.assertEqual(self.reporter._get_output_value(None, default="Test"), "Test")
        self.assertEqual(self.reporter._get_output_value({"value": None}, default="Test"), None)
        self.assertEqual(self.reporter._get_output_value({}, default="EmptyReplaced"), "EmptyReplaced")

if __name__ == '__main__':
    unittest.main()
