import unittest
from cacm_adk_core.compute_capabilities.financial_ratios import calculate_basic_ratios

class TestFinancialRatios(unittest.TestCase):

    def test_valid_inputs(self):
        data = {
            "current_assets": 1000.0,
            "current_liabilities": 500.0,
            "total_debt": 800.0,
            "total_equity": 1000.0
        }
        result = calculate_basic_ratios(data)
        self.assertEqual(len(result["errors"]), 0)
        self.assertAlmostEqual(result["calculated_ratios"]["current_ratio"], 2.0)
        self.assertAlmostEqual(result["calculated_ratios"]["debt_to_equity_ratio"], 0.8)

    def test_missing_current_assets(self):
        data = {
            # "current_assets": 1000.0, # Missing
            "current_liabilities": 500.0,
            "total_debt": 800.0,
            "total_equity": 1000.0
        }
        result = calculate_basic_ratios(data)
        self.assertIn("Missing required financial data key: current_assets (for Current Ratio)", result["errors"])
        self.assertNotIn("current_ratio", result["calculated_ratios"]) # Should not be calculated
        # Debt-to-Equity might also not be calculated if we exit early on any missing key for any ratio it's associated with
        # Based on current logic, it should also be missing as "current_assets" is a required key for the function as a whole.
        self.assertNotIn("debt_to_equity_ratio", result["calculated_ratios"])


    def test_missing_current_liabilities(self):
        data = {
            "current_assets": 1000.0,
            # "current_liabilities": 500.0, # Missing
            "total_debt": 800.0,
            "total_equity": 1000.0
        }
        result = calculate_basic_ratios(data)
        self.assertIn("Missing required financial data key: current_liabilities (for Current Ratio)", result["errors"])
        self.assertNotIn("current_ratio", result["calculated_ratios"])
        self.assertNotIn("debt_to_equity_ratio", result["calculated_ratios"])


    def test_invalid_input_type_string(self):
        data = {
            "current_assets": "abc",
            "current_liabilities": 500.0,
            "total_debt": 800.0,
            "total_equity": 1000.0
        }
        result = calculate_basic_ratios(data)
        self.assertIn("Invalid type for current_assets: expected numeric, got str.", result["errors"])
        self.assertEqual(result["calculated_ratios"], {})

    def test_division_by_zero_current_ratio(self):
        data = {
            "current_assets": 1000.0,
            "current_liabilities": 0,
            "total_debt": 800.0,
            "total_equity": 1000.0
        }
        result = calculate_basic_ratios(data)
        self.assertIn("Cannot calculate Current Ratio: Current Liabilities is zero.", result["errors"])
        self.assertNotIn("current_ratio", result["calculated_ratios"]) # or it could be None
        self.assertIn("debt_to_equity_ratio", result["calculated_ratios"]) # D2E should still calculate
        if "debt_to_equity_ratio" in result["calculated_ratios"]:
             self.assertAlmostEqual(result["calculated_ratios"]["debt_to_equity_ratio"], 0.8)


    def test_division_by_zero_debt_to_equity(self):
        data = {
            "current_assets": 1000.0,
            "current_liabilities": 500.0,
            "total_debt": 800.0,
            "total_equity": 0
        }
        result = calculate_basic_ratios(data)
        self.assertIn("Cannot calculate Debt-to-Equity Ratio: Total Equity is zero.", result["errors"])
        self.assertNotIn("debt_to_equity_ratio", result["calculated_ratios"]) # or it could be None
        self.assertIn("current_ratio", result["calculated_ratios"]) # Current ratio should still calculate
        if "current_ratio" in result["calculated_ratios"]:
            self.assertAlmostEqual(result["calculated_ratios"]["current_ratio"], 2.0)

    def test_different_rounding_precision(self):
        data = {
            "current_assets": 1000.0,
            "current_liabilities": 300.0, # 3.333...
            "total_debt": 1.0,
            "total_equity": 3.0 # 0.333...
        }
        result = calculate_basic_ratios(data, rounding_precision=4)
        self.assertEqual(len(result["errors"]), 0)
        self.assertAlmostEqual(result["calculated_ratios"]["current_ratio"], 3.3333)
        self.assertAlmostEqual(result["calculated_ratios"]["debt_to_equity_ratio"], 0.3333)

        result_default_precision = calculate_basic_ratios(data) # Default is 2
        self.assertEqual(len(result_default_precision["errors"]), 0)
        self.assertAlmostEqual(result_default_precision["calculated_ratios"]["current_ratio"], 3.33)
        self.assertAlmostEqual(result_default_precision["calculated_ratios"]["debt_to_equity_ratio"], 0.33)

    def test_empty_input_dict(self):
        data = {}
        result = calculate_basic_ratios(data)
        self.assertTrue(len(result["errors"]) > 0)
        self.assertIn("Missing required financial data key: current_assets (for Current Ratio)", result["errors"])
        self.assertIn("Missing required financial data key: current_liabilities (for Current Ratio)", result["errors"])
        self.assertIn("Missing required financial data key: total_debt (for Debt-to-Equity Ratio)", result["errors"])
        self.assertIn("Missing required financial data key: total_equity (for Debt-to-Equity Ratio)", result["errors"])
        self.assertEqual(result["calculated_ratios"], {})

    def test_all_inputs_zero(self):
        data = {
            "current_assets": 0.0,
            "current_liabilities": 0.0,
            "total_debt": 0.0,
            "total_equity": 0.0
        }
        result = calculate_basic_ratios(data)
        self.assertIn("Cannot calculate Current Ratio: Current Liabilities is zero.", result["errors"])
        self.assertIn("Cannot calculate Debt-to-Equity Ratio: Total Equity is zero.", result["errors"])
        self.assertEqual(result["calculated_ratios"], {})

    def test_partial_valid_data_one_ratio_calculable(self):
        # Only D2E can be calculated
        data = {
            "current_assets": "not a number", # Invalid
            "current_liabilities": 500.0,
            "total_debt": 800.0,
            "total_equity": 1000.0
        }
        result = calculate_basic_ratios(data)
        self.assertIn("Invalid type for current_assets: expected numeric, got str.", result["errors"])
        self.assertEqual(result["calculated_ratios"], {}) # Because of early exit

        # Test where D2E is calculable but CR is not (due to zero denominator)
        data_cr_zero = {
            "current_assets": 1000.0,
            "current_liabilities": 0.0, # Zero
            "total_debt": 800.0,
            "total_equity": 1000.0
        }
        result_cr_zero = calculate_basic_ratios(data_cr_zero)
        self.assertIn("Cannot calculate Current Ratio: Current Liabilities is zero.", result_cr_zero["errors"])
        self.assertNotIn("current_ratio", result_cr_zero["calculated_ratios"])
        self.assertIn("debt_to_equity_ratio", result_cr_zero["calculated_ratios"])
        self.assertAlmostEqual(result_cr_zero["calculated_ratios"]["debt_to_equity_ratio"], 0.8)


if __name__ == '__main__':
    unittest.main()
