# cacm_adk_core/native_skills.py
import logging
from typing import Union, Optional, Dict, Annotated
from semantic_kernel.functions.kernel_function_decorator import kernel_function

logger = logging.getLogger(__name__)

class BasicCalculationSkill:
    """
    A skill that performs basic calculations.
    """

    @kernel_function(
        description="Calculates a simple ratio given a numerator and a denominator.",
        name="calculate_ratio"
    )
    def calculate_ratio(
        self,
        numerator: Annotated[float, "The numerator of the ratio"],
        denominator: Annotated[float, "The denominator of the ratio"]
    ) -> float:
        """
        Calculates a simple ratio.
        Raises ValueError if denominator is zero or if inputs are not numeric (via type hints).
        """
        if not isinstance(numerator, (int, float)):
            logger.error(f"Invalid input type for numerator: {type(numerator)}. Must be numeric.")
            raise TypeError(f"Numerator must be a number, got {type(numerator).__name__}")
        if not isinstance(denominator, (int, float)):
            logger.error(f"Invalid input type for denominator: {type(denominator)}. Must be numeric.")
            raise TypeError(f"Denominator must be a number, got {type(denominator).__name__}")

        if denominator == 0:
            logger.error("Denominator cannot be zero for ratio calculation.")
            raise ValueError("Denominator cannot be zero.")
        return float(numerator) / float(denominator)

    @kernel_function(
        description="Compares a financial metric against a threshold using a specified operator.",
        name="simple_scorer"
    )
    def simple_scorer(
        self,
        financial_metric: Annotated[float, "The financial metric value to compare"],
        threshold: Annotated[float, "The threshold value to compare against"],
        operator: Annotated[str, "Supported operators: '>', '<', '>=', '<=', '==', '!='. Default is '>'"] = '>'
    ) -> str:
        """
        Compares a financial metric against a threshold.
        Returns a string indicating the result (e.g., 'Above Threshold').
        Raises ValueError for unsupported operators or TypeError for non-numeric metric/threshold.
        """
        if not isinstance(financial_metric, (int, float)):
            logger.error(f"Invalid input type for financial_metric: {type(financial_metric)}. Must be numeric.")
            raise TypeError(f"Financial metric must be a number, got {type(financial_metric).__name__}")
        if not isinstance(threshold, (int, float)):
            logger.error(f"Invalid input type for threshold: {type(threshold)}. Must be numeric.")
            raise TypeError(f"Threshold must be a number, got {type(threshold).__name__}")

        op = operator.strip()
        if op == '>':
            return "Above Threshold" if financial_metric > threshold else "Below or Equal to Threshold"
        elif op == '<':
            return "Below Threshold" if financial_metric < threshold else "Above or Equal to Threshold"
        elif op == '>=':
            return "Meets or Exceeds Threshold" if financial_metric >= threshold else "Below Threshold"
        elif op == '<=':
            return "Below or Meets Threshold" if financial_metric <= threshold else "Exceeds Threshold"
        elif op == '==':
            return "Equals Threshold" if financial_metric == threshold else "Does Not Equal Threshold"
        elif op == '!=':
            return "Does Not Equal Threshold" if financial_metric != threshold else "Equals Threshold"
        else:
            logger.error(f"Unsupported operator '{op}' in simple_scorer.")
            raise ValueError(f"Unsupported operator '{op}'. Supported operators are '>', '<', '>=', '<=', '==', '!='.")


class FinancialAnalysisSkill:
    """
    A skill that performs financial analysis calculations.
    """

    @kernel_function(
        description="Calculates basic financial ratios from a dictionary of financial data.",
        name="calculate_basic_ratios"
    )
    def calculate_basic_ratios(
        self,
        financial_data: Annotated[Dict[str, float], "A dictionary containing financial data. Expected keys: 'current_assets', 'current_liabilities', 'total_debt', 'total_equity'."],
        rounding_precision: Annotated[int, "The number of decimal places to round the results to. Default is 2."] = 2
    ) -> Dict[str, any]:
        """
        Calculates basic financial ratios like Current Ratio and Debt-to-Equity Ratio.
        Input financial_data is a dictionary, e.g.:
        {
            "current_assets": 1000.0,
            "current_liabilities": 500.0,
            "total_debt": 800.0,
            "total_equity": 1200.0
        }
        Returns a dictionary containing 'calculated_ratios' and 'errors'.
        """
        errors = []
        calculated_ratios_intermediate = {
            "current_ratio": None,
            "debt_to_equity_ratio": None
        }

        required_keys_map = {
            "current_assets": "Current Ratio",
            "current_liabilities": "Current Ratio",
            "total_debt": "Debt-to-Equity Ratio",
            "total_equity": "Debt-to-Equity Ratio"
        }

        # Validate presence and type of required keys
        for key, ratio_name in required_keys_map.items():
            if key not in financial_data:
                errors.append(f"Missing required financial data key: '{key}' (for {ratio_name})")
            elif not isinstance(financial_data[key], (int, float)):
                errors.append(f"Invalid type for '{key}': expected numeric, got {type(financial_data[key]).__name__}.")

        if errors: # Return early if fundamental input issues exist
            logger.warning(f"Input validation errors for calculate_basic_ratios: {errors}")
            return {"calculated_ratios": {}, "errors": errors}

        # Current Ratio Calculation
        current_assets = financial_data["current_assets"]
        current_liabilities = financial_data["current_liabilities"]

        if current_liabilities == 0:
            errors.append("Cannot calculate Current Ratio: Current Liabilities is zero.")
            logger.warning("Attempted Current Ratio calculation with Current Liabilities as zero.")
        else:
            calculated_ratios_intermediate["current_ratio"] = round(current_assets / current_liabilities, rounding_precision)

        # Debt-to-Equity Ratio Calculation
        total_debt = financial_data["total_debt"]
        total_equity = financial_data["total_equity"]

        if total_equity == 0:
            errors.append("Cannot calculate Debt-to-Equity Ratio: Total Equity is zero.")
            logger.warning("Attempted Debt-to-Equity Ratio calculation with Total Equity as zero.")
        else:
            calculated_ratios_intermediate["debt_to_equity_ratio"] = round(total_debt / total_equity, rounding_precision)

        final_calculated_ratios = {k: v for k, v in calculated_ratios_intermediate.items() if v is not None}

        if errors:
             logger.warning(f"Errors during ratio calculation: {errors}")

        return {"calculated_ratios": final_calculated_ratios, "errors": errors}

if __name__ == '__main__':
    # Basic Test for BasicCalculationSkill
    basic_skill = BasicCalculationSkill()
    print("--- BasicCalculationSkill Tests ---")
    try:
        print(f"Ratio 10/2 = {basic_skill.calculate_ratio(numerator=10.0, denominator=2.0)}")
    except Exception as e:
        print(f"Error: {e}")
    try:
        print(f"Ratio 10/0 = {basic_skill.calculate_ratio(numerator=10.0, denominator=0.0)}")
    except Exception as e:
        print(f"Error: {e}") # Expected: Denominator cannot be zero.
    try:
        print(f"Ratio 10/'a' = {basic_skill.calculate_ratio(numerator=10.0, denominator='a')}") # type: ignore
    except Exception as e:
        print(f"Error: {e}") # Expected: TypeError

    print(f"Scorer 100 > 50 = {basic_skill.simple_scorer(financial_metric=100.0, threshold=50.0, operator='>')}")
    try:
        print(f"Scorer 50 bad_op 50 = {basic_skill.simple_scorer(financial_metric=50.0, threshold=50.0, operator='bad_op')}")
    except Exception as e:
        print(f"Error: {e}") # Expected: ValueError Unsupported operator

    # Basic Test for FinancialAnalysisSkill
    financial_skill = FinancialAnalysisSkill()
    print("\n--- FinancialAnalysisSkill Tests ---")
    good_data = {"current_assets": 1000.0, "current_liabilities": 500.0, "total_debt": 800.0, "total_equity": 1200.0}
    print(f"Ratios (good data): {financial_skill.calculate_basic_ratios(financial_data=good_data)}")

    bad_data_missing_key = {"current_assets": 1000.0, "current_liabilities": 500.0, "total_debt": 800.0} # Missing total_equity
    print(f"Ratios (missing key): {financial_skill.calculate_basic_ratios(financial_data=bad_data_missing_key)}")

    bad_data_zero_denominator = {"current_assets": 1000.0, "current_liabilities": 0.0, "total_debt": 800.0, "total_equity": 0.0}
    print(f"Ratios (zero denominators): {financial_skill.calculate_basic_ratios(financial_data=bad_data_zero_denominator)}")

    bad_data_wrong_type = {"current_assets": "1000", "current_liabilities": 500.0, "total_debt": 800.0, "total_equity": 1200.0}
    print(f"Ratios (wrong type): {financial_skill.calculate_basic_ratios(financial_data=bad_data_wrong_type)}") # type: ignore

    # Setup logging for the test run
    logging.basicConfig(level=logging.INFO)
    logger.info("Native skills module self-test completed.")
