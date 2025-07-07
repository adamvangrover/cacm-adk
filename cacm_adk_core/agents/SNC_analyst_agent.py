# cacm_adk_core/agents/SNC_analyst_agent.py
import logging
import json
import os  # Added for knowledge base loading
import asyncio
from enum import Enum
from typing import Dict, Any, Optional, Tuple

# from unittest.mock import patch

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext
from semantic_kernel.functions.kernel_arguments import KernelArguments  # Added for SK

# from semantic_kernel import Kernel

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

    def __init__(
        self,
        kernel_service: KernelService,
        agent_config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            agent_name="SNCAnalystAgent",
            kernel_service=kernel_service,
            skills_plugin_name="SNCRatingAssistSkill",
        )
        self.config = agent_config if agent_config else {}
        self.persona = self.config.get("persona", "SNC Analyst Examiner")
        self.description = self.config.get(
            "description",
            "Analyzes Shared National Credits based on regulatory guidelines by retrieving data via A2A and using Semantic Kernel skills.",
        )
        self.expertise = self.config.get(
            "expertise",
            ["SNC analysis", "regulatory compliance", "credit risk assessment"],
        )

        self.comptrollers_handbook_snc = self.config.get(
            "comptrollers_handbook_SNC", {}
        )
        if not self.comptrollers_handbook_snc:
            logging.warning(
                "Comptroller's Handbook SNC guidelines not found in agent configuration."
            )

        self.occ_guidelines_snc = self.config.get("occ_guidelines_SNC", {})
        if not self.occ_guidelines_snc:
            logging.warning("OCC Guidelines SNC not found in agent configuration.")

        # Load SNC Knowledge Base
        try:
            kb_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "knowledge_base",
                "snc_knowledge_base.json",
            )
            with open(kb_path, "r") as f:
                self.snc_kb = json.load(f)
            logging.info("Successfully loaded snc_knowledge_base.json.")
        except Exception as e:
            logging.error(f"Failed to load snc_knowledge_base.json: {e}")
            self.snc_kb = {}  # Initialize to empty if loading fails

    # Illustrative helper method (implementation detail can be refined later)
    def _get_relevant_kb_entries(
        self, kb_section_name: str, keywords_or_ids: list
    ) -> str:
        """
        Retrieves relevant entries from the loaded knowledge base.
        For this subtask, it's a simplified placeholder. A real implementation
        would involve more sophisticated searching/filtering.
        """
        if not self.snc_kb:
            return "Knowledge base not loaded."

        section = self.snc_kb.get(kb_section_name, [])
        if not section:
            return f"Knowledge base section '{kb_section_name}' not found or empty."

        # Simple keyword matching for demonstration
        relevant_texts = []
        if isinstance(section, list):  # for lists of items like guidelines, definitions
            for item in section:
                item_text = json.dumps(item)  # Convert item to string to search
                if any(
                    keyword.lower() in item_text.lower() for keyword in keywords_or_ids
                ):
                    relevant_texts.append(item_text)
        elif isinstance(section, dict):  # for structured objects like handbooks
            # For handbooks, we might just return a summary or specific sub-sections based on keywords
            section_text = json.dumps(section)
            if any(
                keyword.lower() in section_text.lower() for keyword in keywords_or_ids
            ):
                # Return a summary or a specific part, simplified for now
                relevant_texts.append(
                    f"Content from {kb_section_name} matching {keywords_or_ids}"
                )

        if not relevant_texts:
            return f"No entries found in '{kb_section_name}' for keywords/IDs: {keywords_or_ids}."

        return "; ".join(relevant_texts)

    async def run(
        self,
        task_description: str,
        current_step_inputs: Dict[str, Any],
        shared_context: SharedContext,
    ) -> Dict[str, Any]:
        """
        Performs a Shared National Credit (SNC) analysis for a given company.

        The process involves:
        1. Retrieving detailed company data using DataRetrievalAgent.
        2. Preparing financial and qualitative inputs for Semantic Kernel (SK) skills.
        3. Performing financial analysis (using key ratios from retrieved data).
        4. Performing qualitative analysis (based on retrieved data and SK inputs).
        5. Evaluating credit risk mitigation factors.
        6. Determining an SNC rating (Pass, Special Mention, Substandard, Doubtful, Loss)
           and generating a rationale, leveraging SK skills with regulatory guidelines
           (Comptroller's Handbook SNC, OCC Guidelines) from agent configuration.

        Args:
            task_description (str): Description of the analysis task.
            current_step_inputs (Dict[str, Any]): Inputs for this step, must include:
                - "company_id" (str): The unique identifier for the company to be analyzed.
            shared_context (SharedContext): Used for A2A communication (e.g., to get DataRetrievalAgent).

        Returns:
            Dict[str, Any]: A dictionary with the execution status and results:
                - {"status": "success", "data": {"rating": str|None, "rationale": str}}
                  (rating is the string value of the SNCRating enum or None)
                - {"status": "error", "message": str}
        """
        company_id = current_step_inputs.get("company_id")
        logging.info(
            f"Executing SNC analysis for company_id: {company_id} (Task: {task_description})"
        )
        logging.debug(
            f"SNC_ANALYSIS_RUN_INPUT: company_id='{company_id}', inputs='{current_step_inputs}'"
        )

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

            inputs_for_dra = {
                "company_id": company_id,
                "data_type": "get_company_financials",
            }
            task_description_for_dra = (
                f"Retrieve financial data for SNC analysis of {company_id}"
            )
            logging.debug(
                f"SNC_ANALYSIS_A2A_REQUEST: Requesting data from {dra_agent_name}: {inputs_for_dra}"
            )

            response_from_dra = await dra_agent.run(
                task_description_for_dra, inputs_for_dra, shared_context
            )
            logging.debug(
                f"SNC_ANALYSIS_A2A_RESPONSE: Received response: {response_from_dra is not None}"
            )

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
            logging.exception(error_msg)  # Log full exception
            return {"status": "error", "message": error_msg}

        company_info = company_data_package.get("company_info", {})
        financial_data_detailed = company_data_package.get(
            "financial_data_detailed", {}
        )
        qualitative_company_info = company_data_package.get(
            "qualitative_company_info", {}
        )
        industry_data_context = company_data_package.get("industry_data_context", {})
        economic_data_context = company_data_package.get("economic_data_context", {})
        collateral_and_debt_details = company_data_package.get(
            "collateral_and_debt_details", {}
        )

        logging.debug(
            f"SNC_ANALYSIS_DATA_EXTRACTED: CompanyInfo: {list(company_info.keys())}, FinancialDetailed: {list(financial_data_detailed.keys())}, Qualitative: {list(qualitative_company_info.keys())}, Industry: {list(industry_data_context.keys())}, Economic: {list(economic_data_context.keys())}, Collateral: {list(collateral_and_debt_details.keys())}"
        )

        financial_analysis_inputs_for_sk = self._prepare_financial_inputs_for_sk(
            financial_data_detailed
        )
        qualitative_analysis_inputs_for_sk = self._prepare_qualitative_inputs_for_sk(
            qualitative_company_info
        )

        financial_analysis_result = self._perform_financial_analysis(
            financial_data_detailed, financial_analysis_inputs_for_sk
        )
        qualitative_analysis_result = self._perform_qualitative_analysis(
            company_info.get("name", company_id),
            qualitative_company_info,
            industry_data_context,
            economic_data_context,
            qualitative_analysis_inputs_for_sk,
        )
        credit_risk_mitigation_info = self._evaluate_credit_risk_mitigation(
            collateral_and_debt_details
        )

        try:
            # Analyze Press Releases with SK
            sk_press_release_insights = await self._analyze_press_releases_with_sk(
                shared_context
            )

            # _determine_rating now returns (rating, rationale, formal_write_up_content)
            rating, rationale, formal_write_up_content = await self._determine_rating(
                company_info.get("name", company_id),
                financial_analysis_result,
                qualitative_analysis_result,
                credit_risk_mitigation_info,
                economic_data_context,
                sk_press_release_insights,  # Pass insights
            )
            logging.debug(
                f"SNC_ANALYSIS_RUN_OUTPUT: Rating='{rating.value if rating else 'N/A'}', Rationale (excerpt)='{rationale[:200]}...'"
            )

            # The rationale might be the main narrative from formal_write_up_content or a precursor
            # For now, let's assume 'rationale' is a good summary, and formal_write_up has the full JSON

            output_data = {
                "rating": rating.value if rating else None,
                "rationale": rationale,
                "formal_write_up": formal_write_up_content,  # The parsed JSON object
                "sk_generated_press_release_insights": sk_press_release_insights,
                "key_credit_metrics_assessed": {
                    "financial_analysis": financial_analysis_result,
                    "qualitative_analysis": qualitative_analysis_result,
                    "credit_risk_mitigation": credit_risk_mitigation_info,
                },
                "information_sources_referenced": [
                    "snc_knowledge_base.json (including OCC Guidelines, SNC Program Criteria, Regulatory Definitions, Comptroller's Handbooks excerpts)",
                    "Company-specific financial and qualitative data retrieved via DataRetrievalAgent",
                ],
                "data_source_notes": "SNC analysis incorporates data from financial statements, SK-generated insights, and regulatory knowledge base.",
            }
            return {"status": "success", "data": output_data}

        except Exception as e:
            error_msg = f"Error during SNC rating determination, formal write-up, or press release analysis for {company_id}: {e}"
            logging.exception(error_msg)
            return {"status": "error", "message": error_msg}

    def _prepare_financial_inputs_for_sk(
        self, financial_data_detailed: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Prepares stringified financial data elements required by Semantic Kernel skills
        for SNC analysis, extracted from the detailed financial data package.
        """
        cash_flow_statement = financial_data_detailed.get("cash_flow_statement", {})
        key_ratios = financial_data_detailed.get("key_ratios", {})
        market_data = financial_data_detailed.get("market_data", {})
        dcf_assumptions = financial_data_detailed.get("dcf_assumptions", {})

        return {
            "historical_fcf_str": str(
                cash_flow_statement.get("free_cash_flow", ["N/A"])
            ),
            "historical_cfo_str": str(
                cash_flow_statement.get("cash_flow_from_operations", ["N/A"])
            ),
            "annual_debt_service_str": str(
                market_data.get("annual_debt_service_placeholder", "Not Available")
            ),
            "ratios_summary_str": (
                json.dumps(key_ratios) if key_ratios else "Not available"
            ),
            "projected_fcf_str": str(
                dcf_assumptions.get("projected_fcf_placeholder", "Not Available")
            ),
            "payment_history_status_str": str(
                market_data.get("payment_history_placeholder", "Current")
            ),
            "interest_capitalization_status_str": str(
                market_data.get("interest_capitalization_placeholder", "No")
            ),
        }

    def _prepare_qualitative_inputs_for_sk(
        self, qualitative_company_info: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Prepares stringified qualitative data elements required by Semantic Kernel skills
        for SNC analysis, extracted from the qualitative company information.
        """
        return {
            "qualitative_notes_stability_str": qualitative_company_info.get(
                "revenue_cashflow_stability_notes_placeholder",
                "Management reports stable customer contracts.",
            ),
            "notes_financial_deterioration_str": qualitative_company_info.get(
                "financial_deterioration_notes_placeholder",
                "No significant deterioration noted recently.",
            ),
        }

    def _perform_financial_analysis(
        self,
        financial_data_detailed: Dict[str, Any],
        sk_financial_inputs: Dict[str, str],
    ) -> Dict[str, Any]:
        logging.debug(
            f"SNC_FIN_ANALYSIS_INPUT: financial_data_detailed keys: {list(financial_data_detailed.keys())}, sk_inputs keys: {list(sk_financial_inputs.keys())}"
        )
        key_ratios = financial_data_detailed.get("key_ratios", {})

        analysis_result = {
            "debt_to_equity": key_ratios.get("debt_to_equity_ratio"),
            "profitability": key_ratios.get("net_profit_margin"),
            "liquidity_ratio": key_ratios.get("current_ratio"),
            "interest_coverage": key_ratios.get("interest_coverage_ratio"),
            **sk_financial_inputs,
        }
        logging.debug(f"SNC_FIN_ANALYSIS_OUTPUT: {analysis_result}")
        return analysis_result

    def _perform_qualitative_analysis(
        self,
        company_name: str,
        qualitative_company_info: Dict[str, Any],
        industry_data_context: Dict[str, Any],
        economic_data_context: Dict[str, Any],
        sk_qualitative_inputs: Dict[str, str],
    ) -> Dict[str, Any]:
        logging.debug(
            f"SNC_QUAL_ANALYSIS_INPUT: company_name='{company_name}', qualitative_info_keys={list(qualitative_company_info.keys())}, industry_keys={list(industry_data_context.keys())}, economic_keys={list(economic_data_context.keys())}, sk_qual_inputs keys: {list(sk_qualitative_inputs.keys())}"
        )
        qualitative_result = {
            "management_quality": qualitative_company_info.get(
                "management_assessment", "Not Assessed"
            ),
            "industry_outlook": industry_data_context.get("outlook", "Neutral"),
            "economic_conditions": economic_data_context.get(
                "overall_outlook", "Stable"
            ),
            "business_model_strength": qualitative_company_info.get(
                "business_model_strength", "N/A"
            ),
            "competitive_advantages": qualitative_company_info.get(
                "competitive_advantages", "N/A"
            ),
            **sk_qualitative_inputs,
        }
        logging.debug(f"SNC_QUAL_ANALYSIS_OUTPUT: {qualitative_result}")
        return qualitative_result

    def _evaluate_credit_risk_mitigation(
        self, collateral_and_debt_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        logging.debug(
            f"SNC_CREDIT_MITIGATION_INPUT: collateral_and_debt_details_keys={list(collateral_and_debt_details.keys())}"
        )
        ltv = collateral_and_debt_details.get("loan_to_value_ratio")
        collateral_quality_assessment = "Low"
        if ltv is not None:
            try:
                ltv_float = float(ltv)
                if ltv_float < 0.5:
                    collateral_quality_assessment = "High"
                elif ltv_float < 0.75:
                    collateral_quality_assessment = "Medium"
            except ValueError:
                logging.warning(f"Could not parse LTV ratio '{ltv}' as float.")

        mitigation_result = {
            "collateral_quality_fallback": collateral_quality_assessment,
            "collateral_summary_for_sk": collateral_and_debt_details.get(
                "collateral_type", "Not specified."
            ),
            "loan_to_value_ratio": str(ltv) if ltv is not None else "Not specified.",
            "collateral_notes_for_sk": collateral_and_debt_details.get(
                "other_credit_enhancements", "None."
            ),
            "collateral_valuation": collateral_and_debt_details.get(
                "collateral_valuation"
            ),
            "guarantees_present": collateral_and_debt_details.get(
                "guarantees_exist", False
            ),
        }
        logging.debug(f"SNC_CREDIT_MITIGATION_OUTPUT: {mitigation_result}")
        return mitigation_result

    async def _determine_rating(
        self,
        company_name: str,
        financial_analysis: Dict[str, Any],
        qualitative_analysis: Dict[str, Any],
        credit_risk_mitigation: Dict[str, Any],
        economic_data_context: Dict[str, Any],
        sk_press_release_insights: Dict[str, str],
    ) -> Tuple[
        Optional[SNCRating], str, Dict[str, Any]
    ]:  # Added Dict for formal_write_up
        """
        Determines the SNC rating, generates a rationale, and produces a formal write-up.

        Integrates analyses, uses SK skills with expanded knowledge base context,
        and invokes FormalWriteUpSkill for a structured output.
        """
        logging.debug(
            f"SNC_DETERMINE_RATING_INPUT: company='{company_name}', financial_analysis_keys={list(financial_analysis.keys())}, qualitative_analysis_keys={list(qualitative_analysis.keys())}, credit_mitigation_keys={list(credit_risk_mitigation.keys())}, economic_context_keys={list(economic_data_context.keys())}, press_release_insights_keys={list(sk_press_release_insights.keys())}"
        )

        rationale_parts = []

        if sk_press_release_insights:
            rationale_parts.append("SK-Generated Press Release Insights:")
            for period, insight in sk_press_release_insights.items():
                rationale_parts.append(
                    f"  - {period.replace('_', ' ').title()}: {insight}"
                )
            rationale_parts.append("\n")

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
                    "guideline_substandard_collateral": self.comptrollers_handbook_snc.get(
                        "substandard_definition",
                        "Collateral is inadequately protective.",
                    ),
                    "guideline_repayment_source": self.comptrollers_handbook_snc.get(
                        "primary_repayment_source",
                        "Primary repayment should come from a sustainable source of cash under borrower control.",
                    ),
                    "collateral_description": credit_risk_mitigation.get(
                        "collateral_summary_for_sk", "Not specified."
                    ),
                    "ltv_ratio": credit_risk_mitigation.get(
                        "loan_to_value_ratio", "Not specified."
                    ),
                    "other_collateral_notes": credit_risk_mitigation.get(
                        "collateral_notes_for_sk", "None."
                    ),
                    # New placeholders for CollateralRiskAssessment
                    "occ_rcr_collateral_valuation_perfection_monitoring": self._get_relevant_kb_entries(
                        "occ_guidelines",
                        ["collateral", "valuation", "perfection", "monitoring"],
                    ),
                    "occ_ll_collateral_specifics": self._get_relevant_kb_entries(
                        "occ_guidelines", ["Leveraged Lending", "Collateral"]
                    ),
                    "ratings_guide_substandard_collateral_dependency": self._get_relevant_kb_entries(
                        "ratings_guide", ["Substandard", "collateral"]
                    ),
                    "ratings_guide_doubtful_collateral_shortfall": self._get_relevant_kb_entries(
                        "ratings_guide", ["Doubtful", "collateral"]
                    ),
                    "definition_nlv_olv_concepts": self._get_relevant_kb_entries(
                        "definitions",
                        [
                            "NLV",
                            "OLV",
                            "Net Liquidation Value",
                            "Orderly Liquidation Value",
                        ],
                    ),
                    "ch_rcr_collateral_evaluation_factors": self._get_relevant_kb_entries(
                        "comptrollers_handbook_rating_credit_risk",
                        ["collateral evaluation"],
                    ),
                }
                logging.debug(
                    f"SNC_XAI:SK_INPUT:{skill_name_collateral}: {sk_input_vars_collateral}"
                )

                sk_function_collateral = kernel.plugins[self.skills_plugin_name][
                    skill_name_collateral
                ]  # SNCRatingAssistSkill
                result_collateral = await kernel.invoke(
                    sk_function_collateral, **sk_input_vars_collateral
                )
                sk_response_collateral_str = str(result_collateral)

                lines = sk_response_collateral_str.strip().splitlines()
                if lines:
                    if "Assessment:" in lines[0]:
                        collateral_sk_assessment_str = (
                            lines[0]
                            .split("Assessment:", 1)[1]
                            .strip()
                            .replace("[", "")
                            .replace("]", "")
                        )
                    if len(lines) > 1 and "Justification:" in lines[1]:
                        collateral_sk_justification = (
                            lines[1].split("Justification:", 1)[1].strip()
                        )
                logging.debug(
                    f"SNC_XAI:SK_OUTPUT:{skill_name_collateral}: Assessment='{collateral_sk_assessment_str}', Justification='{collateral_sk_justification}'"
                )
                if collateral_sk_justification:
                    rationale_parts.append(
                        f"SK Collateral Assessment ({collateral_sk_assessment_str}): {collateral_sk_justification}"
                    )
            except Exception as e:
                logging.error(
                    f"Error in {skill_name_collateral} SK skill for {company_name}: {e}"
                )

            # 2. AssessRepaymentCapacity
            try:
                skill_name_repayment = "AssessRepaymentCapacity"
                sk_input_vars_repayment = {
                    "guideline_repayment_source": self.comptrollers_handbook_snc.get(
                        "primary_repayment_source", "Default guideline..."
                    ),
                    "guideline_substandard_paying_capacity": self.comptrollers_handbook_snc.get(
                        "substandard_definition", "Default substandard..."
                    ),
                    "repayment_capacity_period_years": str(
                        self.comptrollers_handbook_snc.get(
                            "repayment_capacity_period", 7
                        )
                    ),
                    "historical_fcf": financial_analysis.get(
                        "historical_fcf_str", "Not available"
                    ),
                    "historical_cfo": financial_analysis.get(
                        "historical_cfo_str", "Not available"
                    ),
                    "annual_debt_service": financial_analysis.get(
                        "annual_debt_service_str", "Not available"
                    ),
                    "relevant_ratios": financial_analysis.get(
                        "ratios_summary_str", "Not available"
                    ),
                    "projected_fcf": financial_analysis.get(
                        "projected_fcf_str", "Not available"
                    ),
                    "qualitative_notes_stability": qualitative_analysis.get(
                        "qualitative_notes_stability_str", "None provided."
                    ),
                    # New placeholders for AssessRepaymentCapacity
                    "occ_guideline_cash_flow_analysis_expectations": self._get_relevant_kb_entries(
                        "occ_guidelines", ["cash flow", "repayment capacity"]
                    ),
                    "occ_ll_underwriting_repayment": self._get_relevant_kb_entries(
                        "occ_guidelines",
                        ["Leveraged Lending", "underwriting", "repayment"],
                    ),
                    "ratings_guide_pass_repayment_focus": self._get_relevant_kb_entries(
                        "ratings_guide", ["Pass", "repayment"]
                    ),
                    "definition_ebitda_for_repayment": self._get_relevant_kb_entries(
                        "definitions", ["EBITDA"]
                    ),
                    "ch_rcr_repayment_evaluation_guidance": self._get_relevant_kb_entries(
                        "comptrollers_handbook_rating_credit_risk",
                        ["repayment evaluation"],
                    ),
                    "llg_ebitda_adjustments_for_repayment": self._get_relevant_kb_entries(
                        "leveraged_lending_guidance", ["EBITDA adjustments"]
                    ),
                }
                logging.debug(
                    f"SNC_XAI:SK_INPUT:{skill_name_repayment}: {sk_input_vars_repayment}"
                )

                sk_function_repayment = kernel.plugins[self.skills_plugin_name][
                    skill_name_repayment
                ]  # SNCRatingAssistSkill
                result_repayment = await kernel.invoke(
                    sk_function_repayment, **sk_input_vars_repayment
                )
                sk_response_repayment_str = str(result_repayment)

                lines = sk_response_repayment_str.strip().splitlines()
                if lines:
                    if "Assessment:" in lines[0]:
                        repayment_sk_assessment_str = (
                            lines[0]
                            .split("Assessment:", 1)[1]
                            .strip()
                            .replace("[", "")
                            .replace("]", "")
                        )
                    if len(lines) > 1 and "Justification:" in lines[1]:
                        repayment_sk_justification = (
                            lines[1].split("Justification:", 1)[1].strip()
                        )
                    if len(lines) > 2 and "Concerns:" in lines[2]:
                        repayment_sk_concerns = (
                            lines[2].split("Concerns:", 1)[1].strip()
                        )
                logging.debug(
                    f"SNC_XAI:SK_OUTPUT:{skill_name_repayment}: Assessment='{repayment_sk_assessment_str}', Justification='{repayment_sk_justification}', Concerns='{repayment_sk_concerns}'"
                )
                if repayment_sk_justification:
                    rationale_parts.append(
                        f"SK Repayment Capacity ({repayment_sk_assessment_str}): {repayment_sk_justification}. Concerns: {repayment_sk_concerns}"
                    )
            except Exception as e:
                logging.error(
                    f"Error in {skill_name_repayment} SK skill for {company_name}: {e}"
                )

            # 3. AssessNonAccrualStatusIndication
            try:
                skill_name_nonaccrual = "AssessNonAccrualStatusIndication"
                sk_input_vars_nonaccrual = {
                    "guideline_nonaccrual_status": self.occ_guidelines_snc.get(
                        "nonaccrual_status", "Default non-accrual..."
                    ),
                    "guideline_interest_capitalization": self.occ_guidelines_snc.get(
                        "capitalization_of_interest", "Default interest cap..."
                    ),
                    "payment_history_status": financial_analysis.get(
                        "payment_history_status_str", "Current"
                    ),
                    "relevant_ratios": financial_analysis.get(
                        "ratios_summary_str", "Not available"
                    ),
                    "repayment_capacity_assessment": (
                        repayment_sk_assessment_str
                        if repayment_sk_assessment_str
                        else "Adequate"
                    ),
                    "notes_financial_deterioration": qualitative_analysis.get(
                        "notes_financial_deterioration_str", "None noted."
                    ),
                    "interest_capitalization_status": financial_analysis.get(
                        "interest_capitalization_status_str", "No"
                    ),
                    # New placeholders for AssessNonAccrualStatusIndication
                    "occ_guideline_nonaccrual_specifics": self._get_relevant_kb_entries(
                        "occ_guidelines", ["nonaccrual", "90 day"]
                    ),
                    "ratings_guide_substandard_definition": self._get_relevant_kb_entries(
                        "ratings_guide", ["Substandard"]
                    ),
                    "definition_nonaccrual_accounting": self._get_relevant_kb_entries(
                        "definitions", ["Nonaccrual accounting", "ASC 310-10-35"]
                    ),
                    "occ_interest_capitalization_detail": self._get_relevant_kb_entries(
                        "occ_guidelines", ["interest capitalization"]
                    ),
                }
                logging.debug(
                    f"SNC_XAI:SK_INPUT:{skill_name_nonaccrual}: {sk_input_vars_nonaccrual}"
                )

                sk_function_nonaccrual = kernel.plugins[self.skills_plugin_name][
                    skill_name_nonaccrual
                ]  # SNCRatingAssistSkill
                result_nonaccrual = await kernel.invoke(
                    sk_function_nonaccrual, **sk_input_vars_nonaccrual
                )
                sk_response_nonaccrual_str = str(result_nonaccrual)

                lines = sk_response_nonaccrual_str.strip().splitlines()
                if lines:
                    if "Assessment:" in lines[0]:
                        nonaccrual_sk_assessment_str = (
                            lines[0]
                            .split("Assessment:", 1)[1]
                            .strip()
                            .replace("[", "")
                            .replace("]", "")
                        )
                    if len(lines) > 1 and "Justification:" in lines[1]:
                        nonaccrual_sk_justification = (
                            lines[1].split("Justification:", 1)[1].strip()
                        )
                logging.debug(
                    f"SNC_XAI:SK_OUTPUT:{skill_name_nonaccrual}: Assessment='{nonaccrual_sk_assessment_str}', Justification='{nonaccrual_sk_justification}'"
                )
                if nonaccrual_sk_justification:
                    rationale_parts.append(
                        f"SK Non-Accrual Assessment ({nonaccrual_sk_assessment_str}): {nonaccrual_sk_justification}"
                    )
            except Exception as e:
                logging.error(
                    f"Error in {skill_name_nonaccrual} SK skill for {company_name}: {e}"
                )
        else:
            logging.warning(
                f"SNC_XAI:SK_WARNING: Kernel not available for SNC rating determination for {company_name}. Proceeding with fallback logic."
            )

        debt_to_equity = financial_analysis.get("debt_to_equity")
        profitability = financial_analysis.get("profitability")
        rating = SNCRating.PASS

        logging.debug(
            f"SNC_XAI:RATING_PARAMS_FOR_LOGIC: DtE={debt_to_equity}, Profitability={profitability}, SKCollateral='{collateral_sk_assessment_str}', SKRepayment='{repayment_sk_assessment_str}', SKNonAccrual='{nonaccrual_sk_assessment_str}', FallbackCollateral='{credit_risk_mitigation.get('collateral_quality_fallback')}', ManagementQuality='{qualitative_analysis.get('management_quality')}'"
        )

        # Incorporate SK outputs into rating logic
        if repayment_sk_assessment_str == "Unsustainable" or (
            nonaccrual_sk_assessment_str == "Non-Accrual Warranted"
            and repayment_sk_assessment_str == "Weak"
        ):
            logging.debug(
                f"SNC_XAI:RATING_RULE: LOSS - Based on SK Repayment ('{repayment_sk_assessment_str}') and/or SK Non-Accrual ('{nonaccrual_sk_assessment_str}')."
            )
            rating = SNCRating.LOSS
            rationale_parts.append(
                "Loss rating driven by SK assessment of unsustainable repayment or non-accrual with weak repayment."
            )
        elif repayment_sk_assessment_str == "Weak" or (
            collateral_sk_assessment_str == "Substandard"
            and repayment_sk_assessment_str == "Adequate"
        ):
            logging.debug(
                f"SNC_XAI:RATING_RULE: DOUBTFUL - Based on SK Repayment ('{repayment_sk_assessment_str}') or SK Collateral ('{collateral_sk_assessment_str}') with Repayment ('{repayment_sk_assessment_str}')."
            )
            rating = SNCRating.DOUBTFUL
            rationale_parts.append(
                "Doubtful rating influenced by SK assessment of weak repayment or substandard collateral with adequate repayment."
            )
        elif (
            nonaccrual_sk_assessment_str == "Non-Accrual Warranted"
            or collateral_sk_assessment_str == "Substandard"
            or (
                repayment_sk_assessment_str == "Adequate"
                and collateral_sk_assessment_str != "Pass"
            )
        ):  # If repayment is just adequate and collateral isn't perfect
            logging.debug(
                f"SNC_XAI:RATING_RULE: SUBSTANDARD - Based on SK Non-Accrual ('{nonaccrual_sk_assessment_str}'), SK Collateral ('{collateral_sk_assessment_str}'), or SK Repayment ('{repayment_sk_assessment_str}')."
            )
            rating = SNCRating.SUBSTANDARD
            rationale_parts.append(
                "Substandard rating influenced by SK assessments (Non-Accrual, Collateral, or Repayment indicating weaknesses)."
            )

        if rating == SNCRating.PASS:
            if debt_to_equity is not None and profitability is not None:
                if debt_to_equity > 3.0 and profitability < 0:
                    if rating == SNCRating.PASS:
                        logging.debug(
                            f"SNC_XAI:RATING_RULE_FALLBACK: LOSS - DtE ({debt_to_equity}) > 3.0 and Profitability ({profitability}) < 0"
                        )
                        rating = SNCRating.LOSS
                        rationale_parts.append(
                            "Fallback: High D/E ratio and negative profitability."
                        )
                elif debt_to_equity > 2.0 and profitability < 0.1:
                    if rating == SNCRating.PASS:
                        logging.debug(
                            f"SNC_XAI:RATING_RULE_FALLBACK: DOUBTFUL - DtE ({debt_to_equity}) > 2.0 and Profitability ({profitability}) < 0.1"
                        )
                        rating = SNCRating.DOUBTFUL
                        rationale_parts.append(
                            "Fallback: Elevated D/E ratio and low profitability."
                        )
                elif (
                    financial_analysis.get("liquidity_ratio", 0) < 1.0
                    and financial_analysis.get("interest_coverage", 0) < 1.0
                ):
                    if rating == SNCRating.PASS:
                        logging.debug(
                            f"SNC_XAI:RATING_RULE_FALLBACK: SUBSTANDARD - Liquidity ({financial_analysis.get('liquidity_ratio')}) < 1.0 and Interest Coverage ({financial_analysis.get('interest_coverage')}) < 1.0"
                        )
                        rating = SNCRating.SUBSTANDARD
                        rationale_parts.append(
                            "Fallback: Insufficient liquidity and interest coverage."
                        )
                elif (
                    collateral_sk_assessment_str is None
                    and credit_risk_mitigation.get("collateral_quality_fallback")
                    == "Low"
                ) and qualitative_analysis.get("management_quality") == "Weak":
                    if rating == SNCRating.PASS:
                        logging.debug(
                            f"SNC_XAI:RATING_RULE_FALLBACK: SPECIAL_MENTION - Fallback Collateral: {credit_risk_mitigation.get('collateral_quality_fallback')}, Management: {qualitative_analysis.get('management_quality')}"
                        )
                        rating = SNCRating.SPECIAL_MENTION
                        rationale_parts.append(
                            f"Fallback: Collateral concerns (Fallback: {credit_risk_mitigation.get('collateral_quality_fallback')}) and weak management warrant Special Mention."
                        )
                elif (
                    debt_to_equity <= 1.0
                    and profitability >= 0.3
                    and qualitative_analysis.get("economic_conditions") == "Stable"
                ):
                    # This is a definite PASS if not overridden by SK.
                    logging.debug(
                        f"SNC_XAI:RATING_RULE_FALLBACK: PASS - DtE ({debt_to_equity}) <= 1.0, Profitability ({profitability}) >= 0.3, Econ Conditions: {qualitative_analysis.get('economic_conditions')}"
                    )
                    rating = SNCRating.PASS  # Explicitly ensure it's Pass
                    rationale_parts.append(
                        "Fallback: Strong financials and stable economic conditions."
                    )
                else:
                    if rating == SNCRating.PASS:
                        logging.debug(
                            f"SNC_XAI:RATING_RULE_FALLBACK: SPECIAL_MENTION - Fallback/Mixed Indicators. Initial DtE: {debt_to_equity}, Profitability: {profitability}"
                        )
                        rating = SNCRating.SPECIAL_MENTION
                        rationale_parts.append(
                            "Fallback: Mixed financial indicators or other unaddressed concerns warrant monitoring."
                        )
            elif rating == SNCRating.PASS:
                logging.debug(
                    "SNC_XAI:RATING_RULE_FALLBACK: UNDETERMINED - Missing key financial metrics (DtE or Profitability)"
                )
                rating = None
                rationale_parts.append(
                    "Fallback: Cannot determine rating due to missing key financial metrics (debt-to-equity or profitability)."
                )

        rationale_parts.append(
            f"Regulatory guidance: Comptroller's Handbook SNC v{self.comptrollers_handbook_snc.get('version', 'N/A')}, OCC Guidelines v{self.occ_guidelines_snc.get('version', 'N/A')}."
        )
        # Consolidate rationale parts before formal write-up, this can serve as a base or summary
        preliminary_rationale = " ".join(filter(None, rationale_parts))

        # Invoke FormalWriteUpSkill
        formal_write_up_json_str = "{}"  # Default empty JSON
        parsed_formal_write_up = {"error": "FormalWriteUpSkill not invoked or failed."}

        if kernel:
            try:
                overall_assessment_summary = (
                    f"Collateral Assessment: {collateral_sk_assessment_str if collateral_sk_assessment_str else 'N/A'}. "
                    f"Repayment Capacity: {repayment_sk_assessment_str if repayment_sk_assessment_str else 'N/A'} (Concerns: {repayment_sk_concerns if repayment_sk_concerns else 'None'}). "
                    f"Non-Accrual Status: {nonaccrual_sk_assessment_str if nonaccrual_sk_assessment_str else 'N/A'}. "
                    f"Preliminary Rationale: {preliminary_rationale}"
                )

                formal_write_up_inputs = {
                    "assigned_rating": rating.value if rating else "Undetermined",
                    "rating_outlook": "Stable",  # Placeholder, can be enhanced later
                    "overall_snc_assessment_summary": overall_assessment_summary,
                    "detailed_justification_non_accrual": (
                        nonaccrual_sk_justification
                        if nonaccrual_sk_justification
                        else "Not assessed by SK."
                    ),
                    "detailed_justification_repayment_capacity": (
                        repayment_sk_justification
                        if repayment_sk_justification
                        else "Not assessed by SK."
                    ),
                    "detailed_justification_collateral_risk": (
                        collateral_sk_justification
                        if collateral_sk_justification
                        else "Not assessed by SK."
                    ),
                    "key_financial_metrics_summary": json.dumps(
                        financial_analysis
                    ),  # Pass the whole dict
                    "key_qualitative_factors_summary": json.dumps(
                        qualitative_analysis
                    ),  # Pass the whole dict
                    "relevant_occ_guidelines_summary": self._get_relevant_kb_entries(
                        "occ_guidelines",
                        [
                            "risk rating",
                            "leveraged lending",
                            "nonaccrual",
                            "collateral",
                            "repayment",
                        ],
                    ),  # Example broad fetch
                    "relevant_snc_criteria_summary": self._get_relevant_kb_entries(
                        "shared_national_credit_criteria",
                        ["SNC Program", "risk assessment"],
                    ),  # Example broad fetch
                    "company_id": company_name,
                }
                logging.debug(
                    f"SNC_XAI:SK_INPUT:FormalWriteUpSkill: {formal_write_up_inputs}"
                )

                # Assuming FormalWriteUpSkill is registered under its own plugin name
                # If it was added to SNCRatingAssistSkill, the plugin_name would be self.skills_plugin_name
                sk_function_formal_write_up = kernel.plugins["FormalWriteUpSkill"][
                    "FormalWriteUpSkill"
                ]
                formal_write_up_result = await kernel.invoke(
                    sk_function_formal_write_up, **formal_write_up_inputs
                )
                formal_write_up_json_str = str(formal_write_up_result)
                logging.debug(
                    f"SNC_XAI:SK_OUTPUT:FormalWriteUpSkill: {formal_write_up_json_str}"
                )

                try:
                    parsed_formal_write_up = json.loads(formal_write_up_json_str)
                    # Use the narrative from the formal write-up as the primary rationale if available
                    final_rationale = parsed_formal_write_up.get(
                        "ratingJustificationNarrative", preliminary_rationale
                    )
                except json.JSONDecodeError as e:
                    logging.error(
                        f"Failed to parse formal_write_up_json_str: {e}. String was: {formal_write_up_json_str}"
                    )
                    parsed_formal_write_up = {
                        "error": "Failed to parse formal write-up JSON.",
                        "raw_output": formal_write_up_json_str,
                    }
                    final_rationale = (
                        preliminary_rationale  # Fallback to preliminary rationale
                    )

            except Exception as e:
                logging.error(
                    f"Error invoking FormalWriteUpSkill for {company_name}: {e}"
                )
                # parsed_formal_write_up will retain its default error state
                final_rationale = preliminary_rationale  # Fallback
        else:
            final_rationale = preliminary_rationale  # Fallback if no kernel

        logging.debug(
            f"SNC_DETERMINE_RATING_OUTPUT: Final Rating='{rating.value if rating else 'Undetermined'}', Final Rationale='{final_rationale[:200]}...'"
        )
        logging.info(
            f"SNC rating for {company_name}: {rating.value if rating else 'Undetermined'}."
        )
        return rating, final_rationale, parsed_formal_write_up

    async def _analyze_press_releases_with_sk(
        self, shared_context: SharedContext
    ) -> Dict[str, str]:
        """
        Analyzes (summarizes) available press release texts from SharedContext using SK.
        """
        insights = {}
        kernel = self.get_kernel()
        if not kernel:
            logging.warning(
                "SNC_ANALYZE_PR: Kernel not available, cannot analyze press releases."
            )
            return insights

        # These keys should match the 'context_key' provided in the workflow for DataIngestionAgent
        press_release_context_keys = {
            "q4_2024": "press_release_q4_2024",
            "q1_2025": "press_release_q1_2025",
        }

        for period, context_key in press_release_context_keys.items():
            press_release_text = shared_context.get_data(
                context_key
            )  # Changed .get to .get_data
            if press_release_text and isinstance(press_release_text, str):
                logging.info(
                    f"SNC_ANALYZE_PR: Analyzing press release for {period} from context key '{context_key}'."
                )
                try:
                    # Using summarize_section for broad insights. Could be refined with more targeted prompts/skills later.
                    args = KernelArguments(input=press_release_text, max_sentences="5")
                    summary_result = await kernel.invoke(
                        plugin_name="SummarizationSkills",
                        function_name="summarize_section",
                        arguments=args,
                    )
                    summary_value = str(summary_result)

                    if (
                        summary_value
                        and "[Placeholder LLM Summary:" not in summary_value
                    ):
                        insights[f"insights_press_release_{period}"] = summary_value
                        logging.info(
                            f"SNC_ANALYZE_PR: Successfully analyzed press release for {period}."
                        )
                        logging.debug(
                            f"SNC_XAI:ANALYZE_PR_SK_OUTPUT_{period}: '{summary_value}'"
                        )
                    else:
                        logging.warning(
                            f"SNC_ANALYZE_PR: Received placeholder or empty summary for {period} from SK. Text was: {summary_value}"
                        )
                        insights[f"insights_press_release_{period}"] = (
                            "Insights could not be generated by SK (placeholder returned)."
                        )
                except Exception as e:
                    logging.error(
                        f"SNC_ANALYZE_PR: Error analyzing press release for {period} using SK: {e}"
                    )
                    insights[f"insights_press_release_{period}"] = (
                        f"Error during SK analysis: {e}"
                    )
            else:
                logging.info(
                    f"SNC_ANALYZE_PR: No press release text found in SharedContext for key '{context_key}' ({period})."
                )
                insights[f"insights_press_release_{period}"] = (
                    "Not available in SharedContext."
                )

        return insights


# The if __name__ == '__main__': block should be removed as agents are run by the orchestrator.
# Test code would typically reside in a separate test file/suite.
