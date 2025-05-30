# cacm_adk_core/compute_capabilities/financial_ratios.py

def calculate_basic_ratios(financial_data: dict, rounding_precision: int = 2) -> dict:
    errors = []
    calculated_ratios_intermediate = {
        "current_ratio": None,
        "debt_to_equity_ratio": None
    }

    required_keys = {
        "current_assets": "Current Ratio",
        "current_liabilities": "Current Ratio",
        "total_debt": "Debt-to-Equity Ratio",
        "total_equity": "Debt-to-Equity Ratio"
    }

    # Validate presence of all keys first
    missing_keys = False
    for key in required_keys:
        if key not in financial_data:
            errors.append(f"Missing required financial data key: {key} (for {required_keys[key]})")
            missing_keys = True

    # Validate types of all present keys needed for calculations
    non_numeric_keys = False
    for key in required_keys:
        if key in financial_data and not isinstance(financial_data[key], (int, float)):
            errors.append(f"Invalid type for {key}: expected numeric, got {type(financial_data[key]).__name__}.")
            non_numeric_keys = True
    
    if missing_keys or non_numeric_keys:
        # Return early if fundamental input issues exist
        return {"calculated_ratios": {}, "errors": errors}

    # Current Ratio Calculation
    current_assets = financial_data["current_assets"]
    current_liabilities = financial_data["current_liabilities"]

    if current_liabilities == 0:
        errors.append("Cannot calculate Current Ratio: Current Liabilities is zero.")
    else:
        try:
            calculated_ratios_intermediate["current_ratio"] = round(current_assets / current_liabilities, rounding_precision)
        except TypeError: # Should be caught by earlier checks, but as a safeguard
            errors.append("Type error during Current Ratio calculation. Ensure inputs are numeric.")
        except Exception as e: # Catch any other unexpected calculation error
            errors.append(f"Unexpected error calculating Current Ratio: {str(e)}")

    # Debt-to-Equity Ratio Calculation
    total_debt = financial_data["total_debt"]
    total_equity = financial_data["total_equity"]

    if total_equity == 0:
        errors.append("Cannot calculate Debt-to-Equity Ratio: Total Equity is zero.")
    else:
        try:
            calculated_ratios_intermediate["debt_to_equity_ratio"] = round(total_debt / total_equity, rounding_precision)
        except TypeError: # Safeguard
            errors.append("Type error during Debt-to-Equity Ratio calculation. Ensure inputs are numeric.")
        except Exception as e: # Catch any other unexpected calculation error
            errors.append(f"Unexpected error calculating Debt-to-Equity Ratio: {str(e)}")
            
    # Filter out ratios that could not be calculated (are None)
    final_calculated_ratios = {k: v for k, v in calculated_ratios_intermediate.items() if v is not None}

    return {"calculated_ratios": final_calculated_ratios, "errors": errors}
