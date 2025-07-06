import logging
from typing import Dict, Any, List, Tuple
import semantic_kernel as sk  # For the decorator

# Assuming the ontology prefixes are known and consistent
# These would typically be managed more centrally in a real application
ONTOLOGY_PREFIXES = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "cacm_ont": "http://example.com/ontology/cacm_credit_ontology/0.3#",
    "kgclass": "http://example.com/ontology/cacm_credit_ontology/0.3/classes/#",
    "kgprop": "http://example.com/ontology/cacm_credit_ontology/0.3/properties/#",
    "altdata": "http://example.com/ontology/cacm_credit_ontology/0.3/alternative_data#",
    "esg": "http://example.com/ontology/cacm_credit_ontology/0.3/esg#",
}


def format_uri(prefix_key: str, term: str) -> str:
    return f"{ONTOLOGY_PREFIXES[prefix_key]}{term}"


def format_literal(value: Any) -> str:
    # Basic literal formatting, could be expanded for specific XSD types
    if isinstance(value, bool):
        return str(value).lower()  # "true" or "false"
    if isinstance(value, (int, float)):
        return str(value)
    # Add quotes for strings, escape if necessary (simplified)
    return f'"{str(value)}"'


class KGPopulationSkill:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @sk.kernel_function(
        description="Generates RDF triples from structured company data.",
        name="generate_rdf_triples",
    )
    async def generate_rdf_triples(
        self, company_data: dict, company_uri_base: str = "http://example.com/entity/"
    ) -> List[Tuple[str, str, str]]:
        """
        Generates a list of RDF triples from structured company data.

        Args:
            company_data (dict): A dictionary containing company data.
            company_uri_base (str): Base URI for creating entity URIs.

        Returns:
            List[Tuple[str, str, str]]: A list of RDF triples.
        """
        triples: List[Tuple[str, str, str]] = []

        company_ticker = company_data.get("companyTicker", "unknown_company")
        company_uri = (
            company_uri_base.rstrip("/") + "/" + company_ticker.replace(" ", "_")
        )

        # Company Core Info
        triples.append(
            (company_uri, format_uri("rdf", "type"), format_uri("kgclass", "Obligor"))
        )
        company_name = company_data.get("companyName", "Unknown Company")
        triples.append(
            (company_uri, format_uri("rdfs", "label"), format_literal(company_name))
        )
        if company_data.get("companyTicker"):
            triples.append(
                (
                    company_uri,
                    format_uri("kgprop", "hasTickerSymbol"),
                    format_literal(company_data["companyTicker"]),
                )
            )

        # Financial Data (Conceptual - from financial_data_for_ratios_expanded)
        financials_expanded = company_data.get("financial_data_for_ratios_expanded")
        if isinstance(financials_expanded, dict):
            financials_uri = f"{company_uri}/financials/current_snapshot"  # Example URI
            triples.append(
                (company_uri, format_uri("kgprop", "hasFinancials"), financials_uri)
            )  # Assuming kgprop:hasFinancials exists
            triples.append(
                (
                    financials_uri,
                    format_uri("rdf", "type"),
                    format_uri("cacm_ont", "FinancialStatement"),
                )
            )  # Or more specific

            # Simplified mapping of keys to properties.
            # In a real scenario, this would need a more robust mapping or specific ontology properties.
            for key, value in financials_expanded.items():
                if value is not None and key not in [
                    "source",
                    "period_y1_label",
                    "period_y2_label",
                ]:  # Skip metadata or non-numeric
                    # Conceptual property: kgprop:has<KeyName>
                    # This assumes properties like kgprop:hasCurrentAssets, kgprop:hasTotalDebt exist.
                    # For a more robust approach, a predefined map or more generic properties would be used.
                    prop_name = f"has{key.replace('_', ' ').title().replace(' ', '')}Value"  # e.g. hasCurrentAssetsValue
                    # For now, let's use a generic kgprop:hasValue and create an entity for the item
                    item_uri = f"{financials_uri}/{key}"
                    triples.append(
                        (
                            financials_uri,
                            format_uri("kgprop", "hasFinancialItem"),
                            item_uri,
                        )
                    )  # Generic: hasFinancialItem
                    triples.append(
                        (
                            item_uri,
                            format_uri("rdf", "type"),
                            format_uri("kgclass", "BalanceSheetItem"),
                        )
                    )  # Generic type
                    triples.append(
                        (
                            item_uri,
                            format_uri("rdfs", "label"),
                            format_literal(key.replace("_", " ").title()),
                        )
                    )
                    triples.append(
                        (
                            item_uri,
                            format_uri("kgprop", "hasValue"),
                            format_literal(value),
                        )
                    )

        # Alternative Data
        # Utility Payments
        utility_payments = company_data.get("altdata_utility_payments")
        if isinstance(utility_payments, list):
            for i, record in enumerate(utility_payments):
                if isinstance(record, dict):
                    payment_uri = f"{company_uri}/utility_payment/{i+1}"
                    triples.append(
                        (
                            company_uri,
                            format_uri("altdata", "hasUtilityPaymentHistory"),
                            payment_uri,
                        )
                    )
                    triples.append(
                        (
                            payment_uri,
                            format_uri("rdf", "type"),
                            format_uri("altdata", "UtilityPaymentRecord"),
                        )
                    )
                    if record.get("utilityType"):
                        triples.append(
                            (
                                payment_uri,
                                format_uri("altdata", "utilityType"),
                                format_literal(record.get("utilityType")),
                            )
                        )
                    if record.get("paymentStatus"):
                        triples.append(
                            (
                                payment_uri,
                                format_uri("altdata", "paymentStatus"),
                                format_literal(record.get("paymentStatus")),
                            )
                        )
                    if record.get("paymentDate"):
                        triples.append(
                            (
                                payment_uri,
                                format_uri("altdata", "paymentDate"),
                                format_literal(record.get("paymentDate")),
                            )
                        )  # Assuming XSD date format

        # Social Sentiment
        social_sentiment = company_data.get("altdata_social_sentiment")
        if isinstance(social_sentiment, dict):
            sentiment_uri = f"{company_uri}/social_sentiment/current"
            triples.append(
                (
                    company_uri,
                    format_uri("altdata", "hasSocialMediaSentiment"),
                    sentiment_uri,
                )
            )
            triples.append(
                (
                    sentiment_uri,
                    format_uri("rdf", "type"),
                    format_uri("altdata", "SocialMediaSentiment"),
                )
            )
            if social_sentiment.get("sentimentScore") is not None:
                triples.append(
                    (
                        sentiment_uri,
                        format_uri("altdata", "sentimentScore"),
                        format_literal(social_sentiment.get("sentimentScore")),
                    )
                )
            if social_sentiment.get("sentimentSource"):
                triples.append(
                    (
                        sentiment_uri,
                        format_uri("altdata", "sentimentSource"),
                        format_literal(social_sentiment.get("sentimentSource")),
                    )
                )
            if social_sentiment.get("sentimentDate"):
                triples.append(
                    (
                        sentiment_uri,
                        format_uri("altdata", "sentimentDate"),
                        format_literal(social_sentiment.get("sentimentDate")),
                    )
                )

        # ESG Data
        # Overall ESG Rating
        esg_overall_rating = company_data.get("esg_overall_rating")
        if isinstance(esg_overall_rating, dict):
            esg_rating_uri = f"{company_uri}/esg_rating/overall"
            triples.append(
                (company_uri, format_uri("esg", "hasESGRating"), esg_rating_uri)
            )
            triples.append(
                (
                    esg_rating_uri,
                    format_uri("rdf", "type"),
                    format_uri("esg", "OverallESGRating"),
                )
            )
            if esg_overall_rating.get("ratingValue"):
                triples.append(
                    (
                        esg_rating_uri,
                        format_uri("esg", "ratingValue"),
                        format_literal(esg_overall_rating.get("ratingValue")),
                    )
                )
            if esg_overall_rating.get(
                "ratingProvider"
            ):  # Assuming new property esg:ratingProvider
                triples.append(
                    (
                        esg_rating_uri,
                        format_uri("esg", "dataSource"),
                        format_literal(esg_overall_rating.get("ratingProvider")),
                    )
                )

        # Carbon Emissions
        carbon_emissions = company_data.get("esg_carbon_emissions")
        if isinstance(carbon_emissions, dict):
            reporting_period = carbon_emissions.get("reportingPeriod", "unknown_period")
            emissions_uri = (
                f"{company_uri}/esg_metric/carbon_emissions/{reporting_period}"
            )
            triples.append(
                (company_uri, format_uri("esg", "reportsESGMetric"), emissions_uri)
            )
            triples.append(
                (
                    emissions_uri,
                    format_uri("rdf", "type"),
                    format_uri("esg", "CarbonEmission"),
                )
            )
            # Example: Store total emissions. Could also store scope1, scope2, scope3 individually.
            if carbon_emissions.get("totalEmissions") is not None:
                triples.append(
                    (
                        emissions_uri,
                        format_uri("esg", "metricValue"),
                        format_literal(carbon_emissions.get("totalEmissions")),
                    )
                )
            if carbon_emissions.get("unit"):
                triples.append(
                    (
                        emissions_uri,
                        format_uri("esg", "metricUnit"),
                        format_literal(carbon_emissions.get("unit")),
                    )
                )
            if carbon_emissions.get("reportingPeriod"):
                triples.append(
                    (
                        emissions_uri,
                        format_uri("esg", "reportingPeriod"),
                        format_literal(carbon_emissions.get("reportingPeriod")),
                    )
                )
            # Could add individual scopes too, e.g. by creating sub-metrics or using specific properties if defined in ontology

        self.logger.info(
            f"Generated {len(triples)} RDF triples for company {company_ticker}."
        )
        return triples


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    skill = KGPopulationSkill()

    sample_company_data = {
        "companyName": "Test Example Corp",
        "companyTicker": "TEC",
        "financial_data_for_ratios_expanded": {
            "current_assets": 750000.0,
            "current_liabilities": 300000.0,
            "total_debt": 500000.0,
            "total_equity": 1000000.0,
            "revenue": 2500000.0,
            "source": "conceptual",
        },
        "altdata_utility_payments": [
            {
                "utilityType": "Electricity",
                "paymentStatus": "on-time",
                "paymentDate": "2023-05-15",
            },
            {
                "utilityType": "Water",
                "paymentStatus": "late",
                "paymentDate": "2023-05-20",
            },
        ],
        "altdata_social_sentiment": {
            "sentimentScore": 0.72,
            "sentimentSource": "WebAnalyzer",
            "sentimentDate": "2023-06-05",
        },
        "esg_overall_rating": {
            "ratingValue": "A",
            "ratingProvider": "ESG Ratings Inc.",
            "assessmentDate": "2023-02-01",  # Assuming esg:assessmentDate might be used
        },
        "esg_carbon_emissions": {
            "scope1Emissions": 1000,
            "scope2Emissions": 2500,
            "totalEmissions": 3500,
            "unit": "tCO2e",
            "reportingPeriod": "2022",
        },
    }

    import asyncio

    async def main():
        print("--- Generating RDF Triples ---")
        triples_result = await skill.generate_rdf_triples(sample_company_data)
        for triple in triples_result:
            print(triple)

        print(f"\n--- Total Triples Generated: {len(triples_result)} ---")

        # Example with different base URI
        print("\n--- Generating RDF Triples with custom base URI ---")
        triples_custom_base = await skill.generate_rdf_triples(
            sample_company_data, company_uri_base="http://mydata.org/entities/"
        )
        # Print first few for brevity
        for i, triple in enumerate(triples_custom_base):
            if i < 5:
                print(triple)
        print(
            f"Custom base URI first subject: {triples_custom_base[0][0] if triples_custom_base else 'N/A'}"
        )

    asyncio.run(main())

# Placeholder for KernelService registration (conceptual)
# In semantic_kernel_adapter.py:
# from cacm_adk_core.skills.kg_population_skills import KGPopulationSkill
# ...
# # Inside KernelService._initialize_kernel or a similar setup method:
# self._kernel.add_plugin(KGPopulationSkill(logger=self.logger), plugin_name="KGPopulation")
# self.logger.info("KGPopulationSkill registered with the kernel.")
# ...
# Note: The actual registration requires KernelService to be modified.
# This skill file itself does not perform the registration.
# The logger passed to KGPopulationSkill would ideally be the one from KernelService.
# For standalone testing, a default logger is used if None is provided.
from typing import Optional  # Added to top for logger type hint
