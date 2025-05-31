## Pilot CACM Implementation Plan: Basic Financial Ratios

**Module Location and Name:** `cacm_adk_core/compute_capabilities/financial_ratios.py`

This location seems appropriate as it aligns with the idea of "compute capabilities" within the ADK core.

**1. Main Function(s)/Class(es):**

   We will define a primary function for calculating the ratios. A class structure might be overkill for this specific set of simple ratios but could be considered if the number of ratios and complexity grows. For now, a function-based approach is suitable.

   ```python
   def calculate_basic_ratios(financial_data: dict, rounding_precision: int = 2) -> dict:
   ```
   - **Purpose:** This function will take a dictionary `financial_data` containing necessary financial statement items and an optional `rounding_precision` parameter. It will return a dictionary containing the calculated ratios and any errors encountered.
   - **Parameters:**
     - `financial_data (dict)`: The input dictionary holding financial figures.
     - `rounding_precision (int)`: The number of decimal places to round the calculated ratios to. Defaults to 2, as per the template's parameter.

**2. Input Handling:**

   - The `financial_data` input dictionary is expected to have the following keys, corresponding to the template's `inputs.financialStatementData.schema.properties`:
     - `current_assets` (float or int)
     - `current_liabilities` (float or int)
     - `total_debt` (float or int)
     - `total_equity` (float or int)
   - **Validation:**
     - The function will first check for the presence of all required keys: `current_assets`, `current_liabilities`, `total_debt`, `total_equity`.
     - If any required key is missing, the function will note this error and the corresponding ratio(s) will not be calculated.
     - It will check if the values for these keys are numeric (float or int). If not, an error will be noted.
     - Values should ideally be non-negative, though the primary concern for calculation is numeric type and zero-division.

**3. Ratio Calculations:**

   The function will calculate the following ratios as specified in the template's `outputs` and `workflow` sections:

   - **Current Ratio:**
     - **Formula:** `current_assets / current_liabilities`
     - **Handling:**
       - If `current_liabilities` is missing or not numeric, the ratio is not calculated.
       - If `current_liabilities` is zero, the ratio is not calculated (to prevent division by zero). An appropriate error message will be generated.
       - If calculated successfully, the result will be rounded to the specified `rounding_precision`.

   - **Debt-to-Equity Ratio:**
     - **Formula:** `total_debt / total_equity`
     - **Handling:**
       - If `total_debt` or `total_equity` is missing or not numeric, the ratio is not calculated.
       - If `total_equity` is zero, the ratio is not calculated. An appropriate error message will be generated.
       - If calculated successfully, the result will be rounded to the specified `rounding_precision`.

**4. Output Structuring:**

   - The function will return a dictionary with two main keys: `calculated_ratios` and `errors`.
   - The `calculated_ratios` key will hold a dictionary of the successfully computed ratios, matching the structure in the template's `outputs.calculatedRatios.schema.properties`.
   - The `errors` key will hold a list of error messages encountered during input validation or calculation.

   **Example Return Structure:**
   ```python
   {
       "calculated_ratios": {
           "current_ratio": 1.75,  # Example value
           "debt_to_equity_ratio": 0.62 # Example value
           # Other ratios would be None or absent if not calculable
       },
       "errors": [
           # "Input 'current_assets' is missing.",
           # "Cannot calculate Current Ratio: Current Liabilities is zero."
       ]
   }
   ```
   If a ratio cannot be calculated due to missing input or an error like division by zero, its key might be present in `calculated_ratios` with a value of `None`, or it might be omitted. The presence of a message in the `errors` list will provide context.

**5. Error Handling:**

   - **Missing Inputs:** If required keys in `financial_data` are missing, an error message will be added to the `errors` list, and affected ratios will not be calculated (will be `None` or absent in the output).
   - **Invalid Input Types:** If input values are not numeric, an error message will be added, and affected ratios will not be calculated.
   - **Division by Zero:** For ratios where the denominator could be zero (e.g., `current_liabilities` for Current Ratio, `total_equity` for Debt-to-Equity Ratio):
     - The function will explicitly check for a zero denominator before attempting division.
     - If a zero denominator is found, an error message will be added to the `errors` list, and the specific ratio will be set to `None` (or a specific indicator like `"Error: Division by zero"` if preferred, though `None` is cleaner for programmatic use).
   - **General Calculation Errors:** While less likely for these simple arithmetic operations, any other unexpected errors during calculation could be caught by a try-except block, logged, and an error message added.

**6. Dependencies:**

   - No external libraries are anticipated for implementing these basic financial ratio calculations. Standard Python data types and arithmetic operations will suffice.
