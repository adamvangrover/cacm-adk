# cacm_adk_core/compute_capabilities/basic_functions.py
from typing import Union, Optional


def calculate_ratio(
    numerator: Union[int, float], denominator: Union[int, float]
) -> Optional[float]:
    """Calculates a simple ratio. Returns None if denominator is zero."""
    if not isinstance(numerator, (int, float)) or not isinstance(
        denominator, (int, float)
    ):
        # Or raise TypeError - for now, return None for type issues to simplify Orchestrator
        print(
            f"ERROR: calculate_ratio: Invalid input types: num={type(numerator)}, den={type(denominator)}"
        )
        return None
    if denominator == 0:
        print("ERROR: calculate_ratio: Denominator cannot be zero.")
        return None
    return float(numerator) / float(denominator)


def simple_scorer(
    financial_metric: Union[int, float],
    threshold: Union[int, float],
    operator: str = ">",
) -> str:
    """
    Compares a financial metric against a threshold using a specified operator.
    Returns a string indicating the result (e.g., 'Above Threshold', 'Criteria Met').
    Supported operators: '>', '<', '>=', '<=', '==', '!='.
    """
    if not isinstance(financial_metric, (int, float)) or not isinstance(
        threshold, (int, float)
    ):
        print(
            f"ERROR: simple_scorer: Invalid input types: metric={type(financial_metric)}, threshold={type(threshold)}"
        )
        return "Error: Invalid Input Types"

    if operator == ">":
        return (
            "Above Threshold"
            if financial_metric > threshold
            else "Below or Equal to Threshold"
        )
    elif operator == "<":
        return (
            "Below Threshold"
            if financial_metric < threshold
            else "Above or Equal to Threshold"
        )
    elif operator == ">=":
        return (
            "Meets or Exceeds Threshold"
            if financial_metric >= threshold
            else "Below Threshold"
        )
    elif operator == "<=":
        return (
            "Below or Meets Threshold"
            if financial_metric <= threshold
            else "Exceeds Threshold"
        )
    elif operator == "==":
        return (
            "Equals Threshold"
            if financial_metric == threshold
            else "Does Not Equal Threshold"
        )
    elif operator == "!=":
        return (
            "Does Not Equal Threshold"
            if financial_metric != threshold
            else "Equals Threshold"
        )
    else:
        print(f"ERROR: simple_scorer: Unsupported operator '{operator}'.")
        return "Error: Unsupported Operator"


if __name__ == "__main__":
    print(f"Ratio 10/2 = {calculate_ratio(10, 2)}")
    print(f"Ratio 10/0 = {calculate_ratio(10, 0)}")
    print(f"Ratio 10/'a' = {calculate_ratio(10, 'a')}")  # type: ignore

    print(f"Scorer 100 > 50 = {simple_scorer(100, 50, '>')}")
    print(f"Scorer 50 > 100 = {simple_scorer(50, 100, '>')}")
    print(f"Scorer 50 == 50 = {simple_scorer(50, 50, '==')}")
    print(f"Scorer 50 bad_op 50 = {simple_scorer(50, 50, 'bad_op')}")
