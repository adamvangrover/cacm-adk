# cacm_adk_core/report_generator/report_generator.py
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import random

class ReportGenerator:
    def _get_output_value(self, output_data: Optional[Dict[str, Any]], default: Any = None) -> Any:
        if isinstance(output_data, dict) and "value" in output_data:
            return output_data["value"]
        # Allow direct values if output_data itself is the value (e.g. for simpler mocked_outputs)
        elif output_data is not None and not isinstance(output_data, dict): 
            return output_data
        elif isinstance(output_data, dict) and not output_data: # Empty dict
            return default
        elif isinstance(output_data, dict): # Dict without 'value' key, return as is or default
             # This case might need refinement based on how mocked_outputs are structured.
             # For now, if it's a dict but not the {"value":...} structure, and not empty, return it.
             # Otherwise, it implies the structure is not as expected for direct value extraction.
            return output_data if output_data else default 
        return default

    def _map_score_to_sp(self, score: Optional[int]) -> str:
        if score is None: return "Not Rated"
        if score >= 800: return "AAA"
        if score >= 750: return "AA"
        if score >= 700: return "A"
        if score >= 650: return "BBB"
        if score >= 600: return "BB"
        if score >= 550: return "B"
        if score >= 500: return "CCC" # Simplified scale
        return "CC/C/D or Not Rated"

    def _map_score_to_snc(self, score: Optional[int]) -> str:
        if score is None: return "Ungraded"
        if score >= 700: return "Pass"
        if score >= 600: return "Special Mention (SM)"
        if score >= 500: return "Substandard"
        return "Doubtful/Loss"
        
    def _generate_mocked_outlook(self, score: Optional[int]) -> str:
        if score is None: return "Uncertain"
        if score >= 750: return random.choice(["Positive", "Stable"])
        if score >= 650: return random.choice(["Stable", "Positive"])
        if score >= 550: return random.choice(["Stable", "Negative"])
        return random.choice(["Negative", "Developing"])

    def _generate_mocked_xai_and_rationale(self, score: Optional[int], mocked_outputs: Dict[str, Any], cacm_inputs: Optional[Dict[str, Any]] = None) -> Tuple[List[str], str]:
        key_risk_factors: List[str] = []
        rationale_parts: List[str] = []

        # Example: Analyze mocked 'profitability' if present in outputs
        profitability = self._get_output_value(mocked_outputs.get("profitabilityMetric"))
        if profitability is not None:
            if isinstance(profitability, (int, float)) and profitability < 0.05: # Assuming it's a margin
                key_risk_factors.append("Low profitability ratios observed.")
                rationale_parts.append("Profitability metrics indicate potential pressure on earnings.")
            elif isinstance(profitability, (int, float)) and profitability > 0.2:
                rationale_parts.append("Strong profitability demonstrated.")


        # Example: Analyze mocked 'leverage'
        leverage = self._get_output_value(mocked_outputs.get("leverageRatio"))
        if leverage is not None:
            if isinstance(leverage, (int, float)) and leverage > 3.0:
                key_risk_factors.append("High leverage position.")
                rationale_parts.append("The entity exhibits a high leverage ratio, suggesting increased financial risk.")
            elif isinstance(leverage, (int, float)) and leverage < 1.0:
                 rationale_parts.append("Conservative leverage position noted.")


        # Example: Analyze mocked 'qualitative_assessment_score'
        qual_score = self._get_output_value(mocked_outputs.get("qualitativeScore"))
        if qual_score is not None and isinstance(qual_score, (int, float)):
            if qual_score < 50: # Assuming score out of 100
                key_risk_factors.append("Weak qualitative factors (e.g., management, industry).")
                rationale_parts.append("Qualitative assessments indicate some underlying weaknesses.")
            else:
                rationale_parts.append("Qualitative factors appear satisfactory or strong.")
        
        if not key_risk_factors: key_risk_factors.append("Primary drivers based on overall score category.")
        if not rationale_parts: 
            if score is not None and score > 650:
                rationale_parts.append("The overall financial profile appears generally positive based on the simulated data.")
            else:
                rationale_parts.append("The overall financial profile suggests areas for caution based on the simulated data.")

        # Add a generic statement based on score
        if score is not None:
            rationale_parts.append(f"The simulated score of {score} reflects these observations.")
        else:
            rationale_parts.append("Score was not available for a comprehensive rationale.")
            
        return key_risk_factors, " ".join(rationale_parts)


    def generate_sme_score_report(self, 
                                  mocked_outputs: Dict[str, Any], 
                                  sme_identifier: Optional[str] = "N/A",
                                  cacm_inputs: Optional[Dict[str, Any]] = None # For XAI context if needed
                                 ) -> Dict[str, Any]:
        
        score_data = mocked_outputs.get("creditScore") # Could be {"value": 750} or just 750
        score = self._get_output_value(score_data) # Extracts the actual score value or None

        sp_rating = self._map_score_to_sp(score)
        snc_rating = self._map_score_to_snc(score)
        outlook = self._generate_mocked_outlook(score)
        
        overall_assessment_map = {
            "Pass": "Low to Moderate Risk", "Special Mention (SM)": "Moderate Risk",
            "Substandard": "Medium-High Risk", "Doubtful/Loss": "High Risk", "Ungraded": "Risk Undetermined"
        }
        overall_assessment = overall_assessment_map.get(snc_rating, "Risk Undetermined")
        if score is not None and score >= 750: overall_assessment = "Low Risk" # Override for very high scores

        key_risk_factors, detailed_rationale = self._generate_mocked_xai_and_rationale(score, mocked_outputs, cacm_inputs)

        report = {
            "reportHeader": {
                "reportTitle": "SME Credit Score Report (Simulated)",
                "generatedDate": datetime.now(timezone.utc).isoformat(timespec='seconds'),
                "smeIdentifier": sme_identifier if sme_identifier else "N/A",
                "dataSource": "Simulated CACM Execution via ADK"
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
            "supportingMetrics": { # Selectively include some relevant metrics from mocked_outputs
                "creditScoreRaw": score_data, # Keep original structure
                "riskSegmentRaw": mocked_outputs.get("riskSegment"),
                # Add other relevant outputs if present, e.g.:
                "profitabilityMetric": mocked_outputs.get("profitabilityMetric"),
                "leverageRatio": mocked_outputs.get("leverageRatio"),
                "qualitativeScore": mocked_outputs.get("qualitativeScore")
            },
            "disclaimer": "This is a simulated report based on a predefined CACM template and dynamically mocked outputs from the Orchestrator."
        }
        return report

# Keep example usage block, update it to show new report structure
if __name__ == '__main__':
    reporter = ReportGenerator()
    import json

    mock_outputs_example = {
        "creditScore": {"value": 760, "description": "Final credit score"},
        "riskSegment": {"value": "A-Segment", "description": "Internal risk segment"},
        "profitabilityMetric": {"value": 0.22, "description": "Net Profit Margin"},
        "leverageRatio": {"value": 0.8, "description": "Debt to Equity"},
        "qualitativeScore": {"value": 80, "description": "Score from qualitative factors"}
    }
    print("--- Enhanced SME Report Example ---")
    enhanced_report = reporter.generate_sme_score_report(mock_outputs_example, sme_identifier="SME_MainSt_Bakery")
    print(json.dumps(enhanced_report, indent=2))

    mock_outputs_example_2 = {
        "creditScore": {"value": 580}, # No description
        "riskSegment": "C-Segment", # Direct value
        "leverageRatio": {"value": 4.5}
        # profitabilityMetric and qualitativeScore missing
    }
    print("\n--- Enhanced SME Report Example 2 (less data) ---")
    enhanced_report_2 = reporter.generate_sme_score_report(mock_outputs_example_2, sme_identifier="SME_TechFix_Inc")
    print(json.dumps(enhanced_report_2, indent=2))
