# cacm_adk_core/native_skills.py
import logging
from typing import Union, Optional, Dict, Annotated, Any # Added Any
from semantic_kernel.functions.kernel_function_decorator import kernel_function

logger = logging.getLogger(__name__)

class BasicCalculationSkill:
    """
    A skill that performs basic calculations.
    """

    @kernel_function( # Re-enabling decorator with the correct import
        description="Calculates a simple ratio given a numerator and a denominator.",
        name="calculate_ratio" # SK uses this name; if not provided, it defaults to method name
    )
    def calculate_ratio(
        self,
        numerator: Annotated[float, "The numerator of the ratio"],
        denominator: Annotated[float, "The denominator of the ratio"]
    ) -> float:
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
        if not isinstance(financial_metric, (int, float)):
            logger.error(f"Invalid input type for financial_metric: {type(financial_metric)}. Must be numeric.")
            raise TypeError(f"Financial metric must be a number, got {type(financial_metric).__name__}")
        if not isinstance(threshold, (int, float)):
            logger.error(f"Invalid input type for threshold: {type(threshold)}. Must be numeric.")
            raise TypeError(f"Threshold must be a number, got {type(threshold).__name__}")

        op = operator.strip()
        if op == '>': return "Above Threshold" if financial_metric > threshold else "Below or Equal to Threshold"
        elif op == '<': return "Below Threshold" if financial_metric < threshold else "Above or Equal to Threshold"
        elif op == '>=': return "Meets or Exceeds Threshold" if financial_metric >= threshold else "Below Threshold"
        elif op == '<=': return "Below or Meets Threshold" if financial_metric <= threshold else "Exceeds Threshold"
        elif op == '==': return "Equals Threshold" if financial_metric == threshold else "Does Not Equal Threshold"
        elif op == '!=': return "Does Not Equal Threshold" if financial_metric != threshold else "Equals Threshold"
        else:
            logger.error(f"Unsupported operator '{op}' in simple_scorer.")
            raise ValueError(f"Unsupported operator '{op}'. Supported operators are '>', '<', '>=', '<=', '==', '!='.")


class FinancialAnalysisSkill:
    """
    A skill that performs financial analysis calculations, including various ratios.
    """

    @kernel_function(
        description="Calculates various financial ratios from a dictionary of financial data. Expected keys include current_assets, current_liabilities, total_debt, total_equity, revenue, gross_profit, net_income, total_assets.",
        name="calculate_basic_ratios"
    )
    def calculate_basic_ratios(
        self,
        financial_data: Annotated[Dict[str, float], "A dictionary containing financial data. Expected keys: current_assets, current_liabilities, total_debt, total_equity, revenue, gross_profit, net_income, total_assets."],
        rounding_precision: Annotated[int, "The number of decimal places to round the results to. Default is 2."] = 2
    ) -> Dict[str, Any]:
        """
        Calculates financial ratios like Current Ratio, Debt-to-Equity, Gross Profit Margin, etc.
        Input financial_data is a dictionary, e.g.:
        {
            "current_assets": 1000.0, "current_liabilities": 500.0,
            "total_debt": 800.0, "total_equity": 1200.0,
            "revenue": 10000.0, "gross_profit": 4000.0, "net_income": 1000.0,
            "total_assets": 5000.0
        }
        Returns a dictionary containing 'calculated_ratios' and 'errors'.
        """
        errors = []
        calculated_ratios_intermediate = {
            "current_ratio": None,
            "debt_to_equity_ratio": None,
            "gross_profit_margin": None,
            "net_profit_margin": None,
            "return_on_assets_ROA": None,
            "return_on_equity_ROE": None,
            "debt_ratio": None # Total Debt / Total Assets
        }

        # Define all keys that might be required by one or more ratios
        # and the ratios they are primarily associated with (for error messages)
        required_keys_map = {
            "current_assets": "Current Ratio",
            "current_liabilities": "Current Ratio",
            "total_debt": "Debt-to-Equity Ratio, Debt Ratio",
            "total_equity": "Debt-to-Equity Ratio, ROE",
            "revenue": "Gross Profit Margin, Net Profit Margin",
            "gross_profit": "Gross Profit Margin",
            "net_income": "Net Profit Margin, ROA, ROE",
            "total_assets": "ROA, Debt Ratio"
        }
        
        # Validate presence and type of all potentially required keys
        # This is a general validation pass. Specific calculations will re-check for their particular needs.
        for key, usage_example in required_keys_map.items():
            if key not in financial_data:
                # This is not necessarily an error for all ratios, so make it a warning for now,
                # or let individual ratio calculations handle missing specific keys.
                # For simplicity, we'll log a warning here if a generally expected key is missing.
                logger.debug(f"Optional key '{key}' (used for {usage_example}) not found in financial_data.")
            elif not isinstance(financial_data[key], (int, float)):
                errors.append(f"Invalid type for '{key}': expected numeric, got {type(financial_data[key]).__name__}.")

        if errors: # If type errors found, return early as calculations will likely fail
            logger.warning(f"Input type validation errors for calculate_basic_ratios: {errors}")
            # Still return structure for consistency, but ratios will be empty
            return {"calculated_ratios": {}, "errors": errors}

        # Helper to safely get numeric data or log error and return None
        def get_numeric(key: str, ratio_name_for_error: str) -> Optional[float]:
            value = financial_data.get(key)
            if value is None:
                errors.append(f"Missing required data '{key}' for {ratio_name_for_error}.")
                return None
            if not isinstance(value, (int, float)):
                # This should have been caught by the initial type check, but as a safeguard:
                errors.append(f"Invalid type for '{key}' (for {ratio_name_for_error}): expected numeric, got {type(value).__name__}.")
                return None
            return float(value)

        # Current Ratio
        ca = get_numeric("current_assets", "Current Ratio")
        cl = get_numeric("current_liabilities", "Current Ratio")
        if ca is not None and cl is not None:
            if cl == 0: errors.append("Cannot calculate Current Ratio: Current Liabilities is zero.")
            else: calculated_ratios_intermediate["current_ratio"] = round(ca / cl, rounding_precision)

        # Debt-to-Equity Ratio
        td = get_numeric("total_debt", "Debt-to-Equity Ratio")
        te = get_numeric("total_equity", "Debt-to-Equity Ratio")
        if td is not None and te is not None:
            if te == 0: errors.append("Cannot calculate Debt-to-Equity Ratio: Total Equity is zero.")
            else: calculated_ratios_intermediate["debt_to_equity_ratio"] = round(td / te, rounding_precision)

        # Gross Profit Margin
        rev_gpm = get_numeric("revenue", "Gross Profit Margin")
        gp = get_numeric("gross_profit", "Gross Profit Margin")
        if rev_gpm is not None and gp is not None:
            if rev_gpm == 0: errors.append("Cannot calculate Gross Profit Margin: Revenue is zero.")
            else: calculated_ratios_intermediate["gross_profit_margin"] = round((gp / rev_gpm) * 100, rounding_precision)
        
        # Net Profit Margin
        rev_npm = get_numeric("revenue", "Net Profit Margin")
        ni_npm = get_numeric("net_income", "Net Profit Margin")
        if rev_npm is not None and ni_npm is not None:
            if rev_npm == 0: errors.append("Cannot calculate Net Profit Margin: Revenue is zero.")
            else: calculated_ratios_intermediate["net_profit_margin"] = round((ni_npm / rev_npm) * 100, rounding_precision)

        # Return on Assets (ROA)
        ni_roa = get_numeric("net_income", "ROA")
        ta_roa = get_numeric("total_assets", "ROA")
        if ni_roa is not None and ta_roa is not None:
            if ta_roa == 0: errors.append("Cannot calculate ROA: Total Assets is zero.")
            else: calculated_ratios_intermediate["return_on_assets_ROA"] = round((ni_roa / ta_roa) * 100, rounding_precision)

        # Return on Equity (ROE)
        ni_roe = get_numeric("net_income", "ROE")
        te_roe = get_numeric("total_equity", "ROE")
        if ni_roe is not None and te_roe is not None:
            if te_roe == 0: errors.append("Cannot calculate ROE: Total Equity is zero.")
            else: calculated_ratios_intermediate["return_on_equity_ROE"] = round((ni_roe / te_roe) * 100, rounding_precision)

        # Debt Ratio
        td_dr = get_numeric("total_debt", "Debt Ratio")
        ta_dr = get_numeric("total_assets", "Debt Ratio")
        if td_dr is not None and ta_dr is not None:
            if ta_dr == 0: errors.append("Cannot calculate Debt Ratio: Total Assets is zero.")
            else: calculated_ratios_intermediate["debt_ratio"] = round(td_dr / ta_dr, rounding_precision)
            
        final_calculated_ratios = {k: v for k, v in calculated_ratios_intermediate.items() if v is not None}
        
        if errors:
             logger.warning(f"Errors during ratio calculation: {errors}")

        return {"calculated_ratios": final_calculated_ratios, "errors": errors}

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG) # Set to DEBUG to see optional key messages
    
    # Basic Test for BasicCalculationSkill (unchanged)
    basic_skill = BasicCalculationSkill()
    print("\n--- BasicCalculationSkill Tests ---")
    try: print(f"Ratio 10/2 = {basic_skill.calculate_ratio(numerator=10.0, denominator=2.0)}")
    except Exception as e: print(f"Error: {e}")
    try: basic_skill.calculate_ratio(numerator=10.0, denominator=0.0)
    except ValueError as e: print(f"Ratio 10/0 Error: {e}")
    try: basic_skill.calculate_ratio(numerator=10.0, denominator='a') # type: ignore
    except TypeError as e: print(f"Ratio 10/'a' Error: {e}")
    print(f"Scorer 100 > 50 = {basic_skill.simple_scorer(financial_metric=100.0, threshold=50.0, operator='>')}")
    try: basic_skill.simple_scorer(financial_metric=50.0, threshold=50.0, operator='bad_op')
    except ValueError as e: print(f"Scorer 50 bad_op 50 Error: {e}")

    # Updated Test for FinancialAnalysisSkill
    financial_skill = FinancialAnalysisSkill()
    print("\n--- FinancialAnalysisSkill Tests (Expanded) ---")
    
    good_data_expanded = {
        "current_assets": 1000.0, "current_liabilities": 500.0, # CR = 2.0
        "total_debt": 800.0, "total_equity": 1200.0,           # D/E = 0.67
        "revenue": 10000.0, "gross_profit": 4000.0,             # GPM = 40.0
        "net_income": 1000.0,                                  # NPM = 10.0
        "total_assets": 5000.0                                 # ROA = 20.0, Debt Ratio = 0.16
                                                               # ROE = 83.33
    }
    print(f"Ratios (good expanded data): {financial_skill.calculate_basic_ratios(financial_data=good_data_expanded, rounding_precision=2)}")
    
    # Test with some missing data for new ratios
    data_missing_some_new = {
        "current_assets": 1000.0, "current_liabilities": 500.0,
        "total_debt": 800.0, "total_equity": 1200.0
        # Missing revenue, gross_profit, net_income, total_assets
    }
    print(f"Ratios (missing some new keys): {financial_skill.calculate_basic_ratios(financial_data=data_missing_some_new)}")

    data_zero_revenue_assets = {
        "current_assets": 1000.0, "current_liabilities": 500.0, 
        "total_debt": 800.0, "total_equity": 1200.0,          
        "revenue": 0.0, "gross_profit": 0.0,            
        "net_income": 0.0,                                  
        "total_assets": 0.0                                
    }
    print(f"Ratios (zero revenue/assets): {financial_skill.calculate_basic_ratios(financial_data=data_zero_revenue_assets)}")
    
    logger.info("Native skills module self-test completed.")
