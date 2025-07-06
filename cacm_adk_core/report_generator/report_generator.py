# cacm_adk_core/report_generator/report_generator.py
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import random


class ReportGenerator:
    def _get_output_value(
        self, output_data: Optional[Dict[str, Any]], default: Any = None
    ) -> Any:
        if isinstance(output_data, dict) and "value" in output_data:
            return output_data["value"]
        elif output_data is not None and not isinstance(output_data, dict):
            return output_data
        elif isinstance(output_data, dict) and not output_data:
            return default
        elif isinstance(output_data, dict):
            return output_data if output_data else default
        return default

    def _map_score_to_sp(self, score: Optional[int]) -> str:
        if score is None:
            return "Not Rated"
        if score >= 800:
            return "AAA"
        if score >= 750:
            return "AA"
        if score >= 700:
            return "A"
        if score >= 650:
            return "BBB"
        if score >= 600:
            return "BB"
        if score >= 550:
            return "B"
        if score >= 500:
            return "CCC"
        return "CC/C/D or Not Rated"

    def _map_score_to_snc(self, score: Optional[int]) -> str:
        if score is None:
            return "Ungraded"
        if score >= 700:
            return "Pass"
        if score >= 600:
            return "Special Mention"  # Updated
        if score >= 500:
            return "Substandard"
        if score >= 400:
            return "Doubtful"  # Updated
        return "Loss"  # Updated

    def _generate_mocked_outlook(self, score: Optional[int]) -> str:
        if score is None:
            return "Uncertain"
        if score >= 750:
            return random.choice(["Positive", "Stable"])
        if score >= 650:
            return random.choice(["Stable", "Positive"])
        if score >= 550:
            return random.choice(["Stable", "Negative"])
        return random.choice(["Negative", "Developing"])

    def _generate_fundamental_perspective(
        self,
        score: Optional[int],
        mocked_outputs: Dict[str, Any],
        cacm_inputs: Optional[Dict[str, Any]],
    ) -> str:
        parts = []
        profitability = self._get_output_value(
            mocked_outputs.get("profitabilityMetric")
        )
        leverage = self._get_output_value(mocked_outputs.get("leverageRatio"))
        fcf_yield = self._get_output_value(mocked_outputs.get("freeCashFlowYield"))

        if profitability is not None and isinstance(profitability, (float, int)):
            parts.append(
                f"Profitability (e.g., margin {profitability:.2%}) appears {'strong' if profitability > 0.15 else 'moderate' if profitability > 0.05 else 'weak'}."
            )
        if leverage is not None and isinstance(leverage, (float, int)):
            parts.append(
                f"Leverage (e.g., D/E {leverage:.2f}x) is considered {'high' if leverage > 3 else 'moderate' if leverage > 1.5 else 'low'}."
            )
        if fcf_yield is not None and isinstance(fcf_yield, (float, int)):
            parts.append(
                f"Free Cash Flow Yield ({fcf_yield:.2%}) indicates {'strong' if fcf_yield > 0.05 else 'adequate'} cash generation relative to value."
            )

        if not parts:
            return "Fundamental View: Key quantitative financial indicators were not strongly conclusive in the simulated data."
        return "Fundamental View: " + " ".join(parts)

    def _generate_regulatory_snc_perspective(
        self, snc_rating: str, score: Optional[int], mocked_outputs: Dict[str, Any]
    ) -> str:
        if snc_rating == "Pass":
            return f"SNC Perspective: The '{snc_rating}' rating suggests the credit is sound with no undue criticism warranted at this time."
        if snc_rating == "Special Mention":
            return f"SNC Perspective: The '{snc_rating}' rating indicates potential weaknesses that, if left uncorrected, may result in deterioration of the repayment prospects."
        if snc_rating == "Substandard":
            return f"SNC Perspective: The '{snc_rating}' rating means the credit is inadequately protected by the current sound worth and paying capacity of the obligor or of the collateral pledged."
        if snc_rating == "Doubtful":
            return f"SNC Perspective: The '{snc_rating}' rating implies that collection or liquidation in full, on the basis of currently existing facts, conditions, and values, is highly questionable and improbable."
        if snc_rating == "Loss":
            return f"SNC Perspective: The '{snc_rating}' rating indicates that the asset is considered uncollectible and of such little value that its continuance as a bankable asset is not warranted."
        return f"SNC Perspective: Rating of '{snc_rating}' implies significant concerns or an unmapped category."

    def _generate_market_outlook_perspective(
        self, overall_outlook_rating: str, cacm_inputs: Optional[Dict[str, Any]]
    ) -> str:
        # This would ideally use actual market/industry data from cacm_inputs if available
        # For now, provide a generic statement based on the outlook rating
        market_sentiment_map = {
            "Positive": "favorable market conditions and positive industry trends",
            "Stable": "generally stable market conditions with mixed industry signals",
            "Negative": "potential headwinds from challenging market conditions or negative industry trends",
            "Developing": "an evolving market landscape with significant uncertainties",
            "Uncertain": "a high degree of uncertainty in market and industry forecasts",
        }
        sentiment = market_sentiment_map.get(
            overall_outlook_rating, "current economic conditions and industry trends"
        )
        return f"Market Outlook: The current '{overall_outlook_rating}' outlook reflects {sentiment}."

    def _generate_strategic_commentary(
        self, cacm_inputs: Optional[Dict[str, Any]], mocked_outputs: Dict[str, Any]
    ) -> str:
        # Look for hints of M&A or major projects in inputs or outputs (conceptual for now)
        # Example: if "acquisitionSynergies" in mocked_outputs or (cacm_inputs and "M&A_Scenario_ID" in cacm_inputs):
        # For this example, let's assume a generic placeholder as actual input/output structure for strategy is not defined yet
        if mocked_outputs.get("mergerAndAcquisitionActivityIndicator", {}).get(
            "value"
        ) == True or (
            cacm_inputs
            and "strategic_initiative_type" in cacm_inputs
            and cacm_inputs["strategic_initiative_type"] == "M&A"
        ):
            return "Strategic Note: Recent or ongoing M&A activities are expected to [yield benefits / introduce risks] that are factored into the assessment. Integration success and synergy realization will be key monitoring points."
        return "Strategic Note: Current strategic initiatives appear to be focused on [e.g., organic growth, operational efficiency - to be derived from more data if available]."

    def _generate_mocked_xai_and_rationale(
        self,
        score: Optional[int],
        snc_rating: str,
        overall_outlook_rating: str,
        mocked_outputs: Dict[str, Any],
        cacm_inputs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[str], str]:
        key_risk_factors: List[str] = []
        rationale_components: List[str] = []

        rationale_components.append(
            self._generate_fundamental_perspective(score, mocked_outputs, cacm_inputs)
        )
        rationale_components.append(
            self._generate_regulatory_snc_perspective(snc_rating, score, mocked_outputs)
        )
        rationale_components.append(
            self._generate_market_outlook_perspective(
                overall_outlook_rating, cacm_inputs
            )
        )
        rationale_components.append(
            self._generate_strategic_commentary(cacm_inputs, mocked_outputs)
        )

        leverage = self._get_output_value(mocked_outputs.get("leverageRatio"))
        if (
            leverage is not None
            and isinstance(leverage, (int, float))
            and leverage > 3.0
        ):
            key_risk_factors.append("High financial leverage.")

        profitability = self._get_output_value(
            mocked_outputs.get("profitabilityMetric")
        )
        if (
            profitability is not None
            and isinstance(profitability, (int, float))
            and profitability < 0.05
        ):
            key_risk_factors.append("Weak profitability margins.")

        if snc_rating not in ["Pass"]:
            key_risk_factors.append(
                f"Regulatory concerns indicated by SNC rating: {snc_rating}."
            )
        if overall_outlook_rating == "Negative":
            key_risk_factors.append("Negative market/business outlook.")

        if not key_risk_factors:
            key_risk_factors.append(
                "No overriding individual risk factors identified in this simulation; assessment based on overall profile."
            )

        detailed_rationale = "\n\n".join(filter(None, rationale_components))
        return key_risk_factors, detailed_rationale

    def generate_sme_score_report(
        self,
        mocked_outputs: Dict[str, Any],
        sme_identifier: Optional[str] = "N/A",
        cacm_inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        score = self._get_output_value(mocked_outputs.get("creditScore"))
        sp_rating = self._map_score_to_sp(score)
        snc_rating = self._map_score_to_snc(score)
        outlook = self._generate_mocked_outlook(score)

        key_risk_factors, detailed_rationale = self._generate_mocked_xai_and_rationale(
            score, snc_rating, outlook, mocked_outputs, cacm_inputs
        )

        overall_assessment_map = {
            "Pass": "Low to Moderate Risk",
            "Special Mention": "Moderate Risk",
            "Substandard": "Medium-High Risk",
            "Doubtful": "High Risk",
            "Loss": "Very High Risk / Default",
            "Ungraded": "Risk Undetermined",
        }
        snc_rating_for_map = snc_rating  # Use the direct SNC rating string
        overall_assessment = overall_assessment_map.get(
            snc_rating_for_map, "Risk Undetermined"
        )
        if score is not None and score >= 750 and snc_rating_for_map == "Pass":
            overall_assessment = "Low Risk"

        report = {
            "reportHeader": {
                "reportTitle": "SME Credit Score Report (Simulated)",
                "generatedDate": datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                ),
                "smeIdentifier": sme_identifier if sme_identifier else "N/A",
                "dataSource": "Simulated CACM Execution via ADK",
            },
            "creditRating": {
                "spScaleEquivalent": sp_rating,
                "sncRegulatoryEquivalent": snc_rating,
            },
            "executiveSummary": {
                "overallAssessment": overall_assessment,
                "outlook": outlook,
            },
            "keyRiskFactors_XAI": key_risk_factors,
            "detailedRationale": detailed_rationale,
            "supportingMetrics": mocked_outputs,
            "disclaimer": "This is a simulated report based on a predefined CACM template and dynamically mocked outputs from the Orchestrator.",
        }
        return report


if __name__ == "__main__":
    reporter = ReportGenerator()
    import json

    mock_outputs_example = {
        "creditScore": {"value": 760, "description": "Final credit score"},
        "riskSegment": {"value": "A-Segment", "description": "Internal risk segment"},
        "profitabilityMetric": {"value": 0.22, "description": "Net Profit Margin"},
        "leverageRatio": {"value": 0.8, "description": "Debt to Equity"},
        "freeCashFlowYield": {"value": 0.06, "description": "FCF Yield"},
        "qualitativeScore": {
            "value": 80,
            "description": "Score from qualitative factors",
        },
    }
    print("--- Enhanced SME Report Example (High Score) ---")
    enhanced_report = reporter.generate_sme_score_report(
        mock_outputs_example,
        sme_identifier="SME_HighFlyer_Inc",
        cacm_inputs={"strategic_initiative_type": "Organic Growth"},
    )
    print(json.dumps(enhanced_report, indent=2))

    mock_outputs_example_2 = {
        "creditScore": {"value": 580},
        "riskSegment": "C-Segment",
        "leverageRatio": {"value": 4.5},
        "profitabilityMetric": {"value": 0.03},
        "freeCashFlowYield": {"value": 0.01},
        "mergerAndAcquisitionActivityIndicator": {"value": True},
    }
    print("\n--- Enhanced SME Report Example 2 (Lower Score, M&A hint) ---")
    enhanced_report_2 = reporter.generate_sme_score_report(
        mock_outputs_example_2,
        sme_identifier="SME_RiskTaker_LLC",
        cacm_inputs={"strategic_initiative_type": "M&A"},
    )
    print(json.dumps(enhanced_report_2, indent=2))

    mock_outputs_example_3 = {
        "creditScore": {"value": 450}
        # Other metrics intentionally missing to test defaults
    }
    print("\n--- Enhanced SME Report Example 3 (Very Low Score, Minimal Data) ---")
    enhanced_report_3 = reporter.generate_sme_score_report(
        mock_outputs_example_3, sme_identifier="SME_Challenged_Co"
    )
    print(json.dumps(enhanced_report_3, indent=2))
