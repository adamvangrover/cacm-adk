import logging
from typing import Dict, Any, List, Optional
import semantic_kernel as sk  # For the decorator


class ESGAnalysisSkill:
    """
    A native Python skill for processing and summarizing ESG (Environmental, Social, Governance)
    factors obtained from Knowledge Graph query results.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @sk.kernel_function(
        description="Summarizes ESG factors from Knowledge Graph query results.",
        name="summarize_esg_factors_from_kg",
    )
    async def summarize_esg_factors_from_kg(
        self, kg_query_results: List[Dict[str, Any]], company_name: str
    ) -> Dict[str, Any]:
        """
        Processes a list of dictionaries (representing SPARQL query results for ESG data)
        and summarizes them into a structured format.

        Args:
            kg_query_results (List[Dict[str, Any]]): Data from KnowledgeGraphAgent.
                Expected keys per dict (based on a conceptual SPARQL query):
                - "metric_uri" (str): URI of the ESG metric/factor.
                - "metric_label" (str): Human-readable label of the metric (e.g., "Carbon Emission").
                - "metric_value" (str): Value of the metric.
                - "metric_unit" (str, optional): Unit of the metric (e.g., "tCO2e").
                - "metric_type" (str): Full URI indicating the type (e.g., "http://.../esg#EnvironmentalFactor").
                - "rating_value" (str, optional): For overall ratings.
                - "rating_provider" (str, optional): For overall ratings.
            company_name (str): Name of the company for context.

        Returns:
            Dict[str, Any]: A dictionary summarizing the ESG factors.
        """
        self.logger.info(
            f"Starting ESG factor summarization for {company_name} with {len(kg_query_results)} KG results."
        )

        esg_summary: Dict[str, Any] = {
            "company_name": company_name,
            "environmental": [],
            "social": [],
            "governance": [],
            "overall_ratings": [],
            "other_metrics": [],  # For metrics that don't fit predefined categories or types
            "processing_notes": [],
        }

        if not kg_query_results:
            esg_summary["processing_notes"].append("Received empty KG query results.")
            return esg_summary

        for i, row in enumerate(kg_query_results):
            metric_label = row.get("metric_label")
            metric_value = row.get("metric_value")
            metric_unit = row.get("metric_unit", "")  # Optional
            metric_type_full_uri = row.get(
                "metric_type"
            )  # Full URI, e.g., http://.../esg#EnvironmentalFactor

            # For Overall Ratings (assuming a different query structure or specific type)
            # This part might need adjustment based on how OverallESGRating is queried.
            # Let's assume if 'metric_type' is 'OverallESGRating', then 'rating_value' and 'rating_provider' are primary.
            if metric_type_full_uri and "OverallESGRating" in metric_type_full_uri:
                rating_val = row.get(
                    "rating_value", metric_value
                )  # Fallback to metric_value if specific key missing
                rating_prov = row.get("rating_provider", "N/A")
                rating_label = metric_label or "Overall ESG Rating"
                esg_summary["overall_ratings"].append(
                    f"{rating_label}: {rating_val} (Provider: {rating_prov})"
                )
                continue  # Move to next item once processed as overall rating

            if not metric_label or metric_value is None:  # metric_value can be 0 or "0"
                self.logger.warning(
                    f"Skipping result item {i+1} due to missing label or value: {row}"
                )
                esg_summary["processing_notes"].append(
                    f"Skipped item {i+1}: missing label or value."
                )
                continue

            formatted_entry = f"{metric_label}: {metric_value}{' ' + metric_unit if metric_unit else ''}"

            if metric_type_full_uri:
                # Extract the type name from the URI (e.g., "EnvironmentalFactor")
                metric_type_short = (
                    metric_type_full_uri.split("#")[-1]
                    if "#" in metric_type_full_uri
                    else metric_type_full_uri.split("/")[-1]
                )

                if (
                    metric_type_short == "EnvironmentalFactor"
                    or metric_type_short == "CarbonEmission"
                    or metric_type_short == "WaterUsage"
                ):  # etc.
                    esg_summary["environmental"].append(formatted_entry)
                elif (
                    metric_type_short == "SocialFactor"
                    or metric_type_short == "EmployeeSafetyRecord"
                ):  # etc.
                    esg_summary["social"].append(formatted_entry)
                elif (
                    metric_type_short == "GovernanceFactor"
                    or metric_type_short == "BoardIndependenceRatio"
                ):  # etc.
                    esg_summary["governance"].append(formatted_entry)
                else:
                    self.logger.info(
                        f"Metric '{metric_label}' has unclassified type '{metric_type_short}'. Adding to 'other_metrics'."
                    )
                    esg_summary["other_metrics"].append(
                        f"{formatted_entry} (Type: {metric_type_short})"
                    )
            else:  # No metric_type provided
                self.logger.info(
                    f"Metric '{metric_label}' has no type specified. Adding to 'other_metrics'."
                )
                esg_summary["other_metrics"].append(
                    formatted_entry + " (Type: Not Specified)"
                )

        if (
            not esg_summary["environmental"]
            and not esg_summary["social"]
            and not esg_summary["governance"]
            and not esg_summary["overall_ratings"]
            and not esg_summary["other_metrics"]
        ):
            esg_summary["processing_notes"].append(
                "No specific ESG factors could be categorized from the provided KG results."
            )

        self.logger.info(f"Finished ESG factor summarization for {company_name}.")
        return esg_summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    skill = ESGAnalysisSkill()

    # Sample KG query results (mimicking output from KnowledgeGraphAgent)
    sample_kg_results_esg = [
        {
            "metric_uri": "http://example.com/entity/TEC/esg_metric/carbon_emissions/2022",
            "metric_label": "Scope 1 Carbon Emissions",
            "metric_value": "1500",
            "metric_unit": "tCO2e",
            "metric_type": "http://example.com/ontology/cacm_credit_ontology/0.3/esg#CarbonEmission",
        },
        {
            "metric_uri": "http://example.com/entity/TEC/esg_metric/water_usage/2022",
            "metric_label": "Water Usage",
            "metric_value": "50000",
            "metric_unit": "cubic meters",
            "metric_type": "http://example.com/ontology/cacm_credit_ontology/0.3/esg#EnvironmentalFactor",
        },
        {
            "metric_uri": "http://example.com/entity/TEC/esg_metric/employee_turnover/2022",
            "metric_label": "Employee Turnover Rate",
            "metric_value": "15",
            "metric_unit": "%",
            "metric_type": "http://example.com/ontology/cacm_credit_ontology/0.3/esg#SocialFactor",
        },
        {
            "metric_uri": "http://example.com/entity/TEC/esg_metric/board_independence/2022",
            "metric_label": "Board Independence",
            "metric_value": "80",
            "metric_unit": "%",
            "metric_type": "http://example.com/ontology/cacm_credit_ontology/0.3/esg#GovernanceFactor",
        },
        {
            "metric_uri": "http://example.com/entity/TEC/esg_rating/overall",
            "metric_label": "Overall ESG Score",
            "rating_value": "A-",
            "rating_provider": "ESG Corp",
            "metric_type": "http://example.com/ontology/cacm_credit_ontology/0.3/esg#OverallESGRating",
        },
        {
            "metric_uri": "http://example.com/entity/TEC/esg_metric/data_privacy_incidents/2022",
            "metric_label": "Data Privacy Incidents",
            "metric_value": "0",
            "metric_type": "http://example.com/ontology/cacm_credit_ontology/0.3/esg#SocialFactor",
        },  # Unit is optional
        {
            "metric_uri": "http://example.com/entity/TEC/esg_metric/unknown_metric/2023",
            "metric_label": "Future Sustainability Index",
            "metric_value": "7.5",
            "metric_unit": "score",
            "metric_type": "http://example.com/ontology/cacm_credit_ontology/0.3/custom#FutureMetric",
        },  # Unclassified type
    ]

    empty_kg_results = []
    results_missing_data = [
        {"metric_uri": "http://example.com/entity/TEC/esg_metric/partial_metric"}
        # Missing label, value, type
    ]

    import asyncio

    async def main():
        print("--- Summarizing Sample ESG KG Results ---")
        summary_result = await skill.summarize_esg_factors_from_kg(
            sample_kg_results_esg, "Test Example Corp"
        )
        import json

        print(json.dumps(summary_result, indent=2))

        print("\n--- Summarizing Empty KG Results ---")
        summary_empty = await skill.summarize_esg_factors_from_kg(
            empty_kg_results, "Test Example Corp"
        )
        print(json.dumps(summary_empty, indent=2))

        print("\n--- Summarizing KG Results with Missing Data ---")
        summary_missing = await skill.summarize_esg_factors_from_kg(
            results_missing_data, "Test Example Corp"
        )
        print(json.dumps(summary_missing, indent=2))

    asyncio.run(main())
from typing import Optional  # Added to top for logger type hint
