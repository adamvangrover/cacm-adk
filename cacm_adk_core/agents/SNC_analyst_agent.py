# cacm_adk_core/agents/SNC_analyst_agent.py
import logging
import json
# import os # No longer needed for path manipulation or os.remove in agent logic
import asyncio
from enum import Enum
from typing import Dict, Any, Optional, Tuple # Tuple might be removed if not directly returned

# from unittest.mock import patch # Should be removed, part of old test block

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext
# from semantic_kernel import Kernel # No longer needed for direct type hint in __init__

# Logging setup is handled by the orchestrator/framework

class SNCRating(Enum):
    PASS = "Pass"
    SPECIAL_MENTION = "Special Mention"
    SUBSTANDARD = "Substandard"
    DOUBTFUL = "Doubtful"
    LOSS = "Loss"

class SNCAnalystAgent(Agent):
    """
    Agent for performing Shared National Credit (SNC) analysis.
    This agent analyzes company data based on regulatory guidelines to assign an SNC rating.
    It retrieves data via A2A communication with DataRetrievalAgent and can use SK skills.
    """

    def __init__(self, kernel_service: KernelService, agent_config: Optional[Dict[str, Any]] = None):
        super().__init__(
            agent_name="SNCAnalystAgent",
            kernel_service=kernel_service,
            skills_plugin_name="SNCRatingAssistSkill"
        )
        self.config = agent_config if agent_config else {}
        self.persona = self.config.get('persona', "SNC Analyst Examiner")
        self.description = self.config.get('description', "Analyzes Shared National Credits based on regulatory guidelines by retrieving data via A2A and using Semantic Kernel skills.")
        self.expertise = self.config.get('expertise', ["SNC analysis", "regulatory compliance", "credit risk assessment"])

        self.comptrollers_handbook_snc = self.config.get('comptrollers_handbook_SNC', {})
        if not self.comptrollers_handbook_snc:
            logging.warning("Comptroller's Handbook SNC guidelines not found in agent configuration.")
        
        self.occ_guidelines_snc = self.config.get('occ_guidelines_SNC', {})
        if not self.occ_guidelines_snc:
            logging.warning("OCC Guidelines SNC not found in agent configuration.")

    async def run(self, task_description: str, current_step_inputs: Dict[str, Any], shared_context: SharedContext) -> Dict[str, Any]:
        company_id = current_step_inputs.get('company_id')
        logging.info(f"Executing SNC analysis for company_id: {company_id} (Task: {task_description})")
        logging.debug(f"SNC_ANALYSIS_RUN_INPUT: company_id='{company_id}', inputs='{current_step_inputs}'")

        if not company_id:
            error_msg = "Company ID not provided for SNC analysis."
            logging.error(error_msg)
            return {"status": "error", "message": error_msg}

        dra_agent_name = "DataRetrievalAgent"
        try:
            dra_agent = await self.get_or_create_agent(dra_agent_name, shared_context)
            if not dra_agent:
                error_msg = f"{dra_agent_name} not found. Cannot retrieve company data for SNC analysis of {company_id}."
                logging.error(error_msg)
                return {"status": "error", "message": error_msg}

            inputs_for_dra = {'company_id': company_id, 'data_type': 'get_company_financials'}
            task_description_for_dra = f"Retrieve financial data for SNC analysis of {company_id}"
            logging.debug(f"SNC_ANALYSIS_A2A_REQUEST: Requesting data from {dra_agent_name}: {inputs_for_dra}")

            response_from_dra = await dra_agent.run(task_description_for_dra, inputs_for_dra, shared_context)
            logging.debug(f"SNC_ANALYSIS_A2A_RESPONSE: Received response: {response_from_dra is not None}")

            if not response_from_dra or response_from_dra.get("status") != "success":
                error_msg = f"Failed to retrieve company data package for {company_id} from {dra_agent_name}. Response: {response_from_dra}"
                logging.error(error_msg)
                return {"status": "error", "message": error_msg}

            company_data_package = response_from_dra.get("data")
            if not company_data_package:
                error_msg = f"No data payload in successful response from {dra_agent_name} for {company_id}."
                logging.error(error_msg)
                return {"status": "error", "message": error_msg}

        except Exception as e:
            error_msg = f"Exception during data retrieval from {dra_agent_name} for {company_id}: {e}"
            logging.exception(error_msg) # Log full exception
            return {"status": "error", "message": error_msg}

        company_info = company_data_package.get('company_info', {})
        financial_data_detailed = company_data_package.get('financial_data_detailed', {})
        qualitative_company_info = company_data_package.get('qualitative_company_info', {})
        industry_data_context = company_data_package.get('industry_data_context', {})
        economic_data_context = company_data_package.get('economic_data_context', {})
        collateral_and_debt_details = company_data_package.get('collateral_and_debt_details', {})

        logging.debug(f"SNC_ANALYSIS_DATA_EXTRACTED: CompanyInfo: {list(company_info.keys())}, FinancialDetailed: {list(financial_data_detailed.keys())}, Qualitative: {list(qualitative_company_info.keys())}, Industry: {list(industry_data_context.keys())}, Economic: {list(economic_data_context.keys())}, Collateral: {list(collateral_and_debt_details.keys())}")

        financial_analysis_inputs_for_sk = self._prepare_financial_inputs_for_sk(financial_data_detailed)
        qualitative_analysis_inputs_for_sk = self._prepare_qualitative_inputs_for_sk(qualitative_company_info)

        financial_analysis_result = self._perform_financial_analysis(financial_data_detailed, financial_analysis_inputs_for_sk)
        qualitative_analysis_result = self._perform_qualitative_analysis(
            company_info.get('name', company_id),
            qualitative_company_info,
            industry_data_context,
            economic_data_context,
            qualitative_analysis_inputs_for_sk
        )
        credit_risk_mitigation_info = self._evaluate_credit_risk_mitigation(collateral_and_debt_details)

        try:
            # _determine_rating now returns a tuple (rating, rationale)
            rating, rationale = await self._determine_rating(
                company_info.get('name', company_id),
                financial_analysis_result,
                qualitative_analysis_result,
                credit_risk_mitigation_info,
                economic_data_context
            )
            logging.debug(f"SNC_ANALYSIS_RUN_OUTPUT: Rating='{rating.value if rating else 'N/A'}', Rationale='{rationale}'")
            # Package into the dictionary format
            return {
                "status": "success",
                "data": {
                    "rating": rating.value if rating else None, # Store enum value
                    "rationale": rationale
                }
            }
        except Exception as e:
            error_msg = f"Error during SNC rating determination for {company_id}: {e}"
            logging.exception(error_msg)
            return {"status": "error", "message": error_msg}

    def _prepare_financial_inputs_for_sk(self, financial_data_detailed: Dict[str, Any]) -> Dict[str, str]:
        """Prepares stringified financial inputs required by SK skills."""
        cash_flow_statement = financial_data_detailed.get("cash_flow_statement", {})
        key_ratios = financial_data_detailed.get("key_ratios", {})
        market_data = financial_data_detailed.get("market_data", {})
        dcf_assumptions = financial_data_detailed.get("dcf_assumptions", {}) 

        return {
            "historical_fcf_str": str(cash_flow_statement.get('free_cash_flow', ["N/A"])),
            "historical_cfo_str": str(cash_flow_statement.get('cash_flow_from_operations', ["N/A"])),
            "annual_debt_service_str": str(market_data.get("annual_debt_service_placeholder", "Not Available")), 
            "ratios_summary_str": json.dumps(key_ratios) if key_ratios else "Not available",
            "projected_fcf_str": str(dcf_assumptions.get("projected_fcf_placeholder", "Not Available")), 
            "payment_history_status_str": str(market_data.get("payment_history_placeholder", "Current")), 
            "interest_capitalization_status_str": str(market_data.get("interest_capitalization_placeholder", "No")) 
        }

    def _prepare_qualitative_inputs_for_sk(self, qualitative_company_info: Dict[str, Any]) -> Dict[str, str]:
        """Prepares stringified qualitative inputs required by SK skills."""
        return {
            "qualitative_notes_stability_str": qualitative_company_info.get("revenue_cashflow_stability_notes_placeholder", "Management reports stable customer contracts."),
            "notes_financial_deterioration_str": qualitative_company_info.get("financial_deterioration_notes_placeholder", "No significant deterioration noted recently.")
        }

    def _perform_financial_analysis(self, financial_data_detailed: Dict[str, Any], sk_financial_inputs: Dict[str, str]) -> Dict[str, Any]:
        logging.debug(f"SNC_FIN_ANALYSIS_INPUT: financial_data_detailed keys: {list(financial_data_detailed.keys())}, sk_inputs keys: {list(sk_financial_inputs.keys())}")
        key_ratios = financial_data_detailed.get("key_ratios", {})
        
        analysis_result = {
            "debt_to_equity": key_ratios.get("debt_to_equity_ratio"),
            "profitability": key_ratios.get("net_profit_margin"),
            "liquidity_ratio": key_ratios.get("current_ratio"),
            "interest_coverage": key_ratios.get("interest_coverage_ratio"),
            **sk_financial_inputs 
        }
        logging.debug(f"SNC_FIN_ANALYSIS_OUTPUT: {analysis_result}")
        return analysis_result

    def _perform_qualitative_analysis(self, 
                                      company_name: str, 
                                      qualitative_company_info: Dict[str, Any], 
                                      industry_data_context: Dict[str, Any], 
                                      economic_data_context: Dict[str, Any],
                                      sk_qualitative_inputs: Dict[str, str]) -> Dict[str, Any]:
        logging.debug(f"SNC_QUAL_ANALYSIS_INPUT: company_name='{company_name}', qualitative_info_keys={list(qualitative_company_info.keys())}, industry_keys={list(industry_data_context.keys())}, economic_keys={list(economic_data_context.keys())}, sk_qual_inputs keys: {list(sk_qualitative_inputs.keys())}")
        qualitative_result = {
            "management_quality": qualitative_company_info.get("management_assessment", "Not Assessed"),
            "industry_outlook": industry_data_context.get("outlook", "Neutral"),
            "economic_conditions": economic_data_context.get("overall_outlook", "Stable"),
            "business_model_strength": qualitative_company_info.get("business_model_strength", "N/A"),
            "competitive_advantages": qualitative_company_info.get("competitive_advantages", "N/A"),
            **sk_qualitative_inputs
        }
        logging.debug(f"SNC_QUAL_ANALYSIS_OUTPUT: {qualitative_result}")
        return qualitative_result

    def _evaluate_credit_risk_mitigation(self, collateral_and_debt_details: Dict[str, Any]) -> Dict[str, Any]:
        logging.debug(f"SNC_CREDIT_MITIGATION_INPUT: collateral_and_debt_details_keys={list(collateral_and_debt_details.keys())}")
        ltv = collateral_and_debt_details.get("loan_to_value_ratio")
        collateral_quality_assessment = "Low" 
        if ltv is not None:
            try:
                ltv_float = float(ltv)
                if ltv_float < 0.5: collateral_quality_assessment = "High"
                elif ltv_float < 0.75: collateral_quality_assessment = "Medium"
            except ValueError: logging.warning(f"Could not parse LTV ratio '{ltv}' as float.")
        
        mitigation_result = {
            "collateral_quality_fallback": collateral_quality_assessment, 
            "collateral_summary_for_sk": collateral_and_debt_details.get("collateral_type", "Not specified."),
            "loan_to_value_ratio": str(ltv) if ltv is not None else "Not specified.",
            "collateral_notes_for_sk": collateral_and_debt_details.get("other_credit_enhancements", "None."),
            "collateral_valuation": collateral_and_debt_details.get("collateral_valuation"),
            "guarantees_present": collateral_and_debt_details.get("guarantees_exist", False)
        }
        logging.debug(f"SNC_CREDIT_MITIGATION_OUTPUT: {mitigation_result}")
        return mitigation_result

    async def _determine_rating(self, company_name: str, 
                               financial_analysis: Dict[str, Any], 
                               qualitative_analysis: Dict[str, Any], 
                               credit_risk_mitigation: Dict[str, Any],
                               economic_data_context: Dict[str, Any]
                               ) -> Tuple[Optional[SNCRating], str]:
        logging.debug(f"SNC_DETERMINE_RATING_INPUT: company='{company_name}', financial_analysis_keys={list(financial_analysis.keys())}, qualitative_analysis_keys={list(qualitative_analysis.keys())}, credit_mitigation_keys={list(credit_risk_mitigation.keys())}, economic_context_keys={list(economic_data_context.keys())}")
        
        rationale_parts = []
        collateral_sk_assessment_str = None
        collateral_sk_justification = ""
        repayment_sk_assessment_str = None
        repayment_sk_justification = ""
        repayment_sk_concerns = ""
        nonaccrual_sk_assessment_str = None
        nonaccrual_sk_justification = ""

        kernel = self.get_kernel()
        if kernel:
            # 1. AssessCollateralRisk
            try:
                skill_name_collateral = "CollateralRiskAssessment"
                sk_input_vars_collateral = {
                    "guideline_substandard_collateral": self.comptrollers_handbook_snc.get('substandard_definition', "Collateral is inadequately protective."),
                    "guideline_repayment_source": self.comptrollers_handbook_snc.get('primary_repayment_source', "Primary repayment should come from a sustainable source of cash under borrower control."),
                    "collateral_description": credit_risk_mitigation.get('collateral_summary_for_sk', "Not specified."),
                    "ltv_ratio": credit_risk_mitigation.get('loan_to_value_ratio', "Not specified."),
                    "other_collateral_notes": credit_risk_mitigation.get('collateral_notes_for_sk', "None.")
                }
                logging.debug(f"SNC_XAI:SK_INPUT:{skill_name_collateral}: {sk_input_vars_collateral}")

                sk_function_collateral = kernel.plugins[self.skills_plugin_name][skill_name_collateral]
                result_collateral = await kernel.invoke(sk_function_collateral, **sk_input_vars_collateral)
                sk_response_collateral_str = str(result_collateral)

                lines = sk_response_collateral_str.strip().splitlines()
                if lines:
                    if "Assessment:" in lines[0]: collateral_sk_assessment_str = lines[0].split("Assessment:", 1)[1].strip().replace('[','').replace(']','')
                    if len(lines) > 1 and "Justification:" in lines[1]: collateral_sk_justification = lines[1].split("Justification:", 1)[1].strip()
                logging.debug(f"SNC_XAI:SK_OUTPUT:{skill_name_collateral}: Assessment='{collateral_sk_assessment_str}', Justification='{collateral_sk_justification}'")
                if collateral_sk_justification: rationale_parts.append(f"SK Collateral Assessment ({collateral_sk_assessment_str}): {collateral_sk_justification}")
            except Exception as e: logging.error(f"Error in {skill_name_collateral} SK skill for {company_name}: {e}")

            # 2. AssessRepaymentCapacity
            try:
                skill_name_repayment = "AssessRepaymentCapacity"
                sk_input_vars_repayment = {
                    "guideline_repayment_source": self.comptrollers_handbook_snc.get('primary_repayment_source', "Default guideline..."),
                    "guideline_substandard_paying_capacity": self.comptrollers_handbook_snc.get('substandard_definition', "Default substandard..."),
                    "repayment_capacity_period_years": str(self.comptrollers_handbook_snc.get('repayment_capacity_period', 7)),
                    "historical_fcf": financial_analysis.get('historical_fcf_str', "Not available"),
                    "historical_cfo": financial_analysis.get('historical_cfo_str', "Not available"),
                    "annual_debt_service": financial_analysis.get('annual_debt_service_str', "Not available"),
                    "relevant_ratios": financial_analysis.get('ratios_summary_str', "Not available"),
                    "projected_fcf": financial_analysis.get('projected_fcf_str', "Not available"),
                    "qualitative_notes_stability": qualitative_analysis.get('qualitative_notes_stability_str', "None provided.")
                }
                logging.debug(f"SNC_XAI:SK_INPUT:{skill_name_repayment}: {sk_input_vars_repayment}")

                sk_function_repayment = kernel.plugins[self.skills_plugin_name][skill_name_repayment]
                result_repayment = await kernel.invoke(sk_function_repayment, **sk_input_vars_repayment)
                sk_response_repayment_str = str(result_repayment)

                lines = sk_response_repayment_str.strip().splitlines()
                if lines:
                    if "Assessment:" in lines[0]: repayment_sk_assessment_str = lines[0].split("Assessment:",1)[1].strip().replace('[','').replace(']','')
                    if len(lines) > 1 and "Justification:" in lines[1]: repayment_sk_justification = lines[1].split("Justification:",1)[1].strip()
                    if len(lines) > 2 and "Concerns:" in lines[2]: repayment_sk_concerns = lines[2].split("Concerns:",1)[1].strip()
                logging.debug(f"SNC_XAI:SK_OUTPUT:{skill_name_repayment}: Assessment='{repayment_sk_assessment_str}', Justification='{repayment_sk_justification}', Concerns='{repayment_sk_concerns}'")
                if repayment_sk_justification: rationale_parts.append(f"SK Repayment Capacity ({repayment_sk_assessment_str}): {repayment_sk_justification}. Concerns: {repayment_sk_concerns}")
            except Exception as e: logging.error(f"Error in {skill_name_repayment} SK skill for {company_name}: {e}")

            # 3. AssessNonAccrualStatusIndication
            try:
                skill_name_nonaccrual = "AssessNonAccrualStatusIndication"
                sk_input_vars_nonaccrual = {
                    "guideline_nonaccrual_status": self.occ_guidelines_snc.get('nonaccrual_status', "Default non-accrual..."),
                    "guideline_interest_capitalization": self.occ_guidelines_snc.get('capitalization_of_interest', "Default interest cap..."),
                    "payment_history_status": financial_analysis.get('payment_history_status_str', "Current"),
                    "relevant_ratios": financial_analysis.get('ratios_summary_str', "Not available"),
                    "repayment_capacity_assessment": repayment_sk_assessment_str if repayment_sk_assessment_str else "Adequate", 
                    "notes_financial_deterioration": qualitative_analysis.get('notes_financial_deterioration_str', "None noted."),
                    "interest_capitalization_status": financial_analysis.get('interest_capitalization_status_str', "No")
                }
                logging.debug(f"SNC_XAI:SK_INPUT:{skill_name_nonaccrual}: {sk_input_vars_nonaccrual}")

                sk_function_nonaccrual = kernel.plugins[self.skills_plugin_name][skill_name_nonaccrual]
                result_nonaccrual = await kernel.invoke(sk_function_nonaccrual, **sk_input_vars_nonaccrual)
                sk_response_nonaccrual_str = str(result_nonaccrual)

                lines = sk_response_nonaccrual_str.strip().splitlines()
                if lines:
                    if "Assessment:" in lines[0]: nonaccrual_sk_assessment_str = lines[0].split("Assessment:",1)[1].strip().replace('[','').replace(']','')
                    if len(lines) > 1 and "Justification:" in lines[1]: nonaccrual_sk_justification = lines[1].split("Justification:",1)[1].strip()
                logging.debug(f"SNC_XAI:SK_OUTPUT:{skill_name_nonaccrual}: Assessment='{nonaccrual_sk_assessment_str}', Justification='{nonaccrual_sk_justification}'")
                if nonaccrual_sk_justification: rationale_parts.append(f"SK Non-Accrual Assessment ({nonaccrual_sk_assessment_str}): {nonaccrual_sk_justification}")
            except Exception as e: logging.error(f"Error in {skill_name_nonaccrual} SK skill for {company_name}: {e}")
        else:
            logging.warning(f"SNC_XAI:SK_WARNING: Kernel not available for SNC rating determination for {company_name}. Proceeding with fallback logic.")

        debt_to_equity = financial_analysis.get("debt_to_equity")
        profitability = financial_analysis.get("profitability")
        rating = SNCRating.PASS 

        logging.debug(f"SNC_XAI:RATING_PARAMS_FOR_LOGIC: DtE={debt_to_equity}, Profitability={profitability}, SKCollateral='{collateral_sk_assessment_str}', SKRepayment='{repayment_sk_assessment_str}', SKNonAccrual='{nonaccrual_sk_assessment_str}', FallbackCollateral='{credit_risk_mitigation.get('collateral_quality_fallback')}', ManagementQuality='{qualitative_analysis.get('management_quality')}'")

        # Incorporate SK outputs into rating logic
        if repayment_sk_assessment_str == "Unsustainable" or \
           (nonaccrual_sk_assessment_str == "Non-Accrual Warranted" and repayment_sk_assessment_str == "Weak"):
            logging.debug(f"SNC_XAI:RATING_RULE: LOSS - Based on SK Repayment ('{repayment_sk_assessment_str}') and/or SK Non-Accrual ('{nonaccrual_sk_assessment_str}').")
            rating = SNCRating.LOSS
            rationale_parts.append("Loss rating driven by SK assessment of unsustainable repayment or non-accrual with weak repayment.")
        elif repayment_sk_assessment_str == "Weak" or \
             (collateral_sk_assessment_str == "Substandard" and repayment_sk_assessment_str == "Adequate"):
            logging.debug(f"SNC_XAI:RATING_RULE: DOUBTFUL - Based on SK Repayment ('{repayment_sk_assessment_str}') or SK Collateral ('{collateral_sk_assessment_str}') with Repayment ('{repayment_sk_assessment_str}').")
            rating = SNCRating.DOUBTFUL
            rationale_parts.append("Doubtful rating influenced by SK assessment of weak repayment or substandard collateral with adequate repayment.")
        elif nonaccrual_sk_assessment_str == "Non-Accrual Warranted" or \
             collateral_sk_assessment_str == "Substandard" or \
             (repayment_sk_assessment_str == "Adequate" and collateral_sk_assessment_str != "Pass"): # If repayment is just adequate and collateral isn't perfect
            logging.debug(f"SNC_XAI:RATING_RULE: SUBSTANDARD - Based on SK Non-Accrual ('{nonaccrual_sk_assessment_str}'), SK Collateral ('{collateral_sk_assessment_str}'), or SK Repayment ('{repayment_sk_assessment_str}').")
            rating = SNCRating.SUBSTANDARD 
            rationale_parts.append("Substandard rating influenced by SK assessments (Non-Accrual, Collateral, or Repayment indicating weaknesses).")
        
        if rating == SNCRating.PASS: 
            if debt_to_equity is not None and profitability is not None:
                if debt_to_equity > 3.0 and profitability < 0:
                    if rating == SNCRating.PASS: 
                        logging.debug(f"SNC_XAI:RATING_RULE_FALLBACK: LOSS - DtE ({debt_to_equity}) > 3.0 and Profitability ({profitability}) < 0")
                        rating = SNCRating.LOSS
                        rationale_parts.append("Fallback: High D/E ratio and negative profitability.")
                elif debt_to_equity > 2.0 and profitability < 0.1:
                     if rating == SNCRating.PASS:
                        logging.debug(f"SNC_XAI:RATING_RULE_FALLBACK: DOUBTFUL - DtE ({debt_to_equity}) > 2.0 and Profitability ({profitability}) < 0.1")
                        rating = SNCRating.DOUBTFUL
                        rationale_parts.append("Fallback: Elevated D/E ratio and low profitability.")
                elif financial_analysis.get("liquidity_ratio", 0) < 1.0 and financial_analysis.get("interest_coverage", 0) < 1.0:
                     if rating == SNCRating.PASS:
                        logging.debug(f"SNC_XAI:RATING_RULE_FALLBACK: SUBSTANDARD - Liquidity ({financial_analysis.get('liquidity_ratio')}) < 1.0 and Interest Coverage ({financial_analysis.get('interest_coverage')}) < 1.0")
                        rating = SNCRating.SUBSTANDARD
                        rationale_parts.append("Fallback: Insufficient liquidity and interest coverage.")
                elif (collateral_sk_assessment_str is None and credit_risk_mitigation.get("collateral_quality_fallback") == "Low") and \
                     qualitative_analysis.get("management_quality") == "Weak":
                     if rating == SNCRating.PASS:
                        logging.debug(f"SNC_XAI:RATING_RULE_FALLBACK: SPECIAL_MENTION - Fallback Collateral: {credit_risk_mitigation.get('collateral_quality_fallback')}, Management: {qualitative_analysis.get('management_quality')}")
                        rating = SNCRating.SPECIAL_MENTION
                        rationale_parts.append(f"Fallback: Collateral concerns (Fallback: {credit_risk_mitigation.get('collateral_quality_fallback')}) and weak management warrant Special Mention.")
                elif debt_to_equity <= 1.0 and profitability >= 0.3 and qualitative_analysis.get("economic_conditions") == "Stable":
                    # This is a definite PASS if not overridden by SK.
                    logging.debug(f"SNC_XAI:RATING_RULE_FALLBACK: PASS - DtE ({debt_to_equity}) <= 1.0, Profitability ({profitability}) >= 0.3, Econ Conditions: {qualitative_analysis.get('economic_conditions')}")
                    rating = SNCRating.PASS # Explicitly ensure it's Pass
                    rationale_parts.append("Fallback: Strong financials and stable economic conditions.")
                else: 
                    if rating == SNCRating.PASS: 
                        logging.debug(f"SNC_XAI:RATING_RULE_FALLBACK: SPECIAL_MENTION - Fallback/Mixed Indicators. Initial DtE: {debt_to_equity}, Profitability: {profitability}")
                        rating = SNCRating.SPECIAL_MENTION
                        rationale_parts.append("Fallback: Mixed financial indicators or other unaddressed concerns warrant monitoring.")
            elif rating == SNCRating.PASS : 
                logging.debug("SNC_XAI:RATING_RULE_FALLBACK: UNDETERMINED - Missing key financial metrics (DtE or Profitability)")
                rating = None 
                rationale_parts.append("Fallback: Cannot determine rating due to missing key financial metrics (debt-to-equity or profitability).")

        rationale_parts.append(f"Regulatory guidance: Comptroller's Handbook SNC v{self.comptrollers_handbook_snc.get('version', 'N/A')}, OCC Guidelines v{self.occ_guidelines_snc.get('version', 'N/A')}.")
        final_rationale = " ".join(filter(None, rationale_parts))
        
        logging.debug(f"SNC_DETERMINE_RATING_OUTPUT: Final Rating='{rating.value if rating else 'Undetermined'}', Rationale='{final_rationale}'")
        logging.info(f"SNC rating for {company_name}: {rating.value if rating else 'Undetermined'}. Rationale: {final_rationale}")
        return rating, final_rationale

# The if __name__ == '__main__': block should be removed as agents are run by the orchestrator.
# Test code would typically reside in a separate test file/suite.
