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
from semantic_kernel.functions.kernel_arguments import KernelArguments # Added for SK
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
        else:
            if not self.comptrollers_handbook_snc.get('regulatory_classifications'):
                logging.warning("Comptroller's Handbook: 'regulatory_classifications' key missing.")
            if not self.comptrollers_handbook_snc.get('general_principles'):
                logging.warning("Comptroller's Handbook: 'general_principles' key missing.")
            if not self.comptrollers_handbook_snc.get('accounting_issues'):
                logging.warning("Comptroller's Handbook: 'accounting_issues' key missing.")
        
        self.occ_guidelines_snc = self.config.get('occ_guidelines_SNC', {})
        if not self.occ_guidelines_snc:
            logging.warning("OCC Guidelines SNC not found in agent configuration.")
        else:
            # Example for OCC, assuming a similar structure might evolve or for consistency
            if not self.occ_guidelines_snc.get('key_risk_areas_2024'): # As per instruction
                 logging.warning("OCC Guidelines: 'key_risk_areas_2024' key missing.")

    async def run(self, task_description: str, current_step_inputs: Dict[str, Any], shared_context: SharedContext) -> Dict[str, Any]:
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
            # Analyze Press Releases with SK
            # Pass company_info to _analyze_press_releases_with_sk
            sk_press_release_insights = await self._analyze_press_releases_with_sk(shared_context, company_info)


            # _determine_rating now returns a tuple (rating, rationale)
            # Pass company_data_package directly
            rating, rationale = await self._determine_rating(
                company_name=company_info.get('name', company_id),
                company_data_package=company_data_package, # Pass the whole package
                sk_press_release_insights=sk_press_release_insights
            )
            logging.debug(f"SNC_ANALYSIS_RUN_OUTPUT: Rating='{rating.value if rating else 'N/A'}', Rationale='{rationale}'")
            
            output_data = {
                "rating": rating.value if rating else None,
                "rationale": rationale,
                "sk_generated_press_release_insights": sk_press_release_insights, # Add to output
                "data_source_notes": "SNC analysis incorporates data from financial statements and SK-generated insights from available press releases."
            }
            return {"status": "success", "data": output_data}

        except Exception as e:
            error_msg = f"Error during SNC rating determination or press release analysis for {company_id}: {e}"
            logging.exception(error_msg)
            return {"status": "error", "message": error_msg}

    def _prepare_financial_inputs_for_sk(self, financial_data_detailed: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepares stringified financial data elements required by Semantic Kernel skills
        for SNC analysis, extracted from the detailed financial data package.
        """
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
        """
        Prepares stringified qualitative data elements required by Semantic Kernel skills
        for SNC analysis, extracted from the qualitative company information.
        """
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

    # --- New SK Argument Preparation Helper Methods ---

    def _prepare_args_for_financial_statement_analysis_sk(self, company_data_package: Dict[str, Any]) -> KernelArguments:
        args = KernelArguments()
        financial_data_detailed = company_data_package.get('financial_data_detailed', {})
        # Guidelines
        handbook_fs = self.comptrollers_handbook_snc.get('financial_statement_analysis', {})
        args["guideline_financial_statement_analysis_focus"] = handbook_fs.get('focus', "Default focus...")
        args["guideline_cash_flow_definition"] = handbook_fs.get('cash_flow_definition', "Default cash flow def...")
        args["guideline_cash_flow_scrutiny"] = handbook_fs.get('cash_flow_scrutiny', "Default scrutiny points...")
        args["guideline_ratio_analysis"] = handbook_fs.get('ratio_analysis', "Default ratio guideline...")
        args["guideline_projection_analysis"] = handbook_fs.get('projection_analysis', "Default projection guideline...")
        # Data
        args["balance_sheet_summary_str"] = str(financial_data_detailed.get('balance_sheet_summary_placeholder', "Not available"))
        args["income_statement_summary_str"] = str(financial_data_detailed.get('income_statement_summary_placeholder', "Not available"))
        args["cash_flow_statement_summary_str"] = str(financial_data_detailed.get('cash_flow_statement_summary_placeholder', "Not available"))
        args["financial_projections_summary_str"] = str(financial_data_detailed.get('financial_projections_summary_placeholder', "Not available"))
        args["key_financial_ratios_str"] = str(financial_data_detailed.get('key_ratios_summary_placeholder', "Not available"))
        logging.debug(f"SNC_XAI:PREP_ARGS:FinancialStatementAnalysisSkill: {args}")
        return args

    def _prepare_args_for_qualitative_factors_sk(self, company_data_package: Dict[str, Any]) -> KernelArguments:
        args = KernelArguments()
        qualitative_company_info = company_data_package.get('qualitative_company_info', {})
        industry_data_context = company_data_package.get('industry_data_context', {})
        economic_data_context = company_data_package.get('economic_data_context', {})
        # Guidelines
        handbook_qual = self.comptrollers_handbook_snc.get('qualitative_factors', {})
        args["guideline_underwriting_standards"] = handbook_qual.get('underwriting_standards', "Default underwriting...")
        args["guideline_management_competency"] = handbook_qual.get('management_competency', "Default management...")
        args["guideline_industry_analysis"] = handbook_qual.get('industry_analysis', "Default industry...")
        # Data
        args["borrower_management_assessment_str"] = str(qualitative_company_info.get('management_assessment', "Not available"))
        args["borrower_industry_str"] = str(company_data_package.get('company_info', {}).get('industry_placeholder', "Not specified"))
        args["industry_outlook_str"] = str(industry_data_context.get('outlook', "Neutral"))
        # TODO: Get snc_review_focus_industries_str from OCC guidelines or agent config
        args["snc_review_focus_industries_str"] = self.occ_guidelines_snc.get('snc_review_focus_industries_placeholder', "{}")
        args["economic_conditions_str"] = str(economic_data_context.get('overall_outlook', "Stable"))
        args["underwriting_elements_summary_str"] = str(company_data_package.get('loan_details',{}).get('underwriting_summary_placeholder', "Standard terms"))
        args["company_business_model_strength_str"] = str(qualitative_company_info.get('business_model_strength', "Not assessed"))
        args["company_competitive_advantages_str"] = str(qualitative_company_info.get('competitive_advantages', "Not specified"))
        logging.debug(f"SNC_XAI:PREP_ARGS:QualitativeFactorsSkill: {args}")
        return args

    def _prepare_args_for_advanced_credit_risk_mitigation_sk(self, company_data_package: Dict[str, Any]) -> KernelArguments:
        args = KernelArguments()
        collateral_and_debt_details = company_data_package.get('collateral_and_debt_details', {})
        # Guidelines
        handbook_crm = self.comptrollers_handbook_snc.get('credit_risk_mitigation', {})
        args["guideline_guarantee_assessment"] = handbook_crm.get('guarantee_assessment', "Default guarantee...")
        args["guideline_letter_of_credit_assessment"] = handbook_crm.get('letter_of_credit_assessment', "Default L/C...")
        args["guideline_credit_derivative_assessment"] = handbook_crm.get('credit_derivative_assessment', "Default derivative...")
        args["guideline_credit_insurance_assessment"] = handbook_crm.get('credit_insurance_assessment', "Default insurance...")
        # Data
        args["collateral_summary_str"] = str(collateral_and_debt_details.get('collateral_summary_placeholder', "Not available"))
        args["guarantee_details_str"] = str(collateral_and_debt_details.get('guarantee_details_placeholder', "None"))
        args["letter_of_credit_details_str"] = str(collateral_and_debt_details.get('letter_of_credit_details_placeholder', "None"))
        args["credit_derivative_details_str"] = str(collateral_and_debt_details.get('credit_derivative_details_placeholder', "None"))
        args["credit_insurance_details_str"] = str(collateral_and_debt_details.get('credit_insurance_details_placeholder', "None"))
        args["borrower_default_status_str"] = str(company_data_package.get('loan_details', {}).get('default_status_placeholder', "Not in default"))
        logging.debug(f"SNC_XAI:PREP_ARGS:AdvancedCreditRiskMitigationSkill: {args}")
        return args

    def _prepare_args_for_structural_weakness_sk(self, company_data_package: Dict[str, Any]) -> KernelArguments:
        args = KernelArguments()
        loan_details = company_data_package.get('loan_details', {})
        financial_data_detailed = company_data_package.get('financial_data_detailed', {})
        # Guidelines
        handbook_struct = self.comptrollers_handbook_snc.get('structural_weaknesses', {}) # Assuming Appendix F is here
        args["guideline_appendix_f_summary"] = handbook_struct.get('appendix_f_summary', "Default Appendix F summary...")
        # Data
        args["loan_purpose_str"] = str(loan_details.get('loan_purpose_placeholder', "Not specified"))
        args["repayment_terms_str"] = str(loan_details.get('repayment_terms_placeholder', "Not specified"))
        args["covenants_summary_str"] = str(loan_details.get('covenants_summary_placeholder', "None"))
        args["debt_service_coverage_ratio_str"] = str(financial_data_detailed.get('key_ratios',{}).get('dscr_placeholder', "Not available"))
        args["leverage_ratio_str"] = str(financial_data_detailed.get('key_ratios',{}).get('leverage_placeholder', "Not available"))
        args["tangible_net_worth_str"] = str(financial_data_detailed.get('balance_sheet',{}).get('tangible_net_worth_placeholder', "Not available"))
        args["collateral_ltv_advance_rates_str"] = str(company_data_package.get('collateral_and_debt_details',{}).get('ltv_advance_rates_placeholder', "Not available"))
        args["guarantor_support_details_str"] = str(company_data_package.get('collateral_and_debt_details',{}).get('guarantor_support_placeholder', "N/A"))
        args["reliance_on_projections_str"] = str(loan_details.get('reliance_on_projections_placeholder', "No unusual reliance"))
        logging.debug(f"SNC_XAI:PREP_ARGS:StructuralWeaknessIdentificationSkill: {args}")
        return args

    def _prepare_args_for_accounting_compliance_sk(self, company_data_package: Dict[str, Any], current_classification: str) -> KernelArguments:
        args = KernelArguments()
        loan_details = company_data_package.get('loan_details', {})
        # Guidelines
        handbook_acct = self.comptrollers_handbook_snc.get('accounting_issues', {})
        args["guideline_nonaccrual_summary"] = handbook_acct.get('nonaccrual_status', {}).get('summary_for_skill', "Default nonaccrual summary...")
        args["guideline_interest_capitalization"] = handbook_acct.get('capitalization_of_interest', "Default interest cap guideline...")
        args["guideline_restructured_loans"] = handbook_acct.get('formally_restructured_loans', "Default restructured guideline...")
        args["guideline_loans_purchased_at_discount"] = handbook_acct.get('loans_purchased_at_discount', "Default discount guideline...")
        # Data
        args["loan_current_status_str"] = str(loan_details.get('current_status_placeholder', "Performing"))
        args["interest_capitalized_flag_bool"] = loan_details.get('interest_capitalized_flag_placeholder', False)
        args["loan_classification_str"] = current_classification # Passed in
        args["is_formally_restructured_bool"] = loan_details.get('is_formally_restructured_placeholder', False)
        args["restructured_terms_summary_str"] = str(loan_details.get('restructured_terms_summary_placeholder', "N/A"))
        args["is_purchased_at_discount_bool"] = loan_details.get('is_purchased_at_discount_placeholder', False)
        args["purchase_discount_details_str"] = str(loan_details.get('purchase_discount_details_placeholder', "N/A"))
        logging.debug(f"SNC_XAI:PREP_ARGS:AccountingComplianceSkill: {args}")
        return args

    def _prepare_args_for_collateral_assessment_sk(self, company_data_package: Dict[str, Any]) -> KernelArguments:
        args = KernelArguments()
        collateral_details = company_data_package.get('collateral_and_debt_details', {})
        loan_details = company_data_package.get('loan_details', {})
        # Guidelines
        handbook_coll = self.comptrollers_handbook_snc.get('collateral_assessment', {}) # New structured path
        args["guideline_collateral_definition_general"] = handbook_coll.get('definition_general', "Default def...")
        args["guideline_collateral_valuation_methods"] = handbook_coll.get('valuation_methods', "Default val methods...")
        args["guideline_collateral_perfection_control"] = handbook_coll.get('perfection_control', "Default perfection...")
        args["guideline_collateral_dependent_classification"] = handbook_coll.get('collateral_dependent_classification', "Default dep class...")
        # Data
        args["collateral_description_str"] = str(collateral_details.get('collateral_description_placeholder', "Not specified"))
        args["collateral_valuation_amount_str"] = str(collateral_details.get('valuation_amount_placeholder', "Not available"))
        args["collateral_valuation_type_basis_str"] = str(collateral_details.get('valuation_type_basis_placeholder', "Not specified"))
        args["collateral_valuation_date_str"] = str(collateral_details.get('valuation_date_placeholder', "Not specified"))
        args["lien_status_control_str"] = str(collateral_details.get('lien_status_control_placeholder', "Not specified"))
        args["loan_balance_str"] = str(loan_details.get('current_balance_placeholder', "Not available"))
        args["is_borrower_collateral_dependent_bool"] = loan_details.get('is_collateral_dependent_placeholder', False)
        logging.debug(f"SNC_XAI:PREP_ARGS:CollateralRiskAssessment: {args}")
        return args

    def _prepare_args_for_non_accrual_sk(self, company_data_package: Dict[str, Any], repayment_assessment_str: str) -> KernelArguments:
        args = KernelArguments()
        loan_details = company_data_package.get('loan_details', {})
        financial_data = company_data_package.get('financial_data_detailed', {}) # For payment history, deterioration notes
        qual_info = company_data_package.get('qualitative_company_info', {})
        # Guidelines
        handbook_acct = self.comptrollers_handbook_snc.get('accounting_issues', {})
        non_accrual_guidelines = handbook_acct.get('nonaccrual_status', {})
        args["guideline_nonaccrual_general_rule"] = non_accrual_guidelines.get('general_rule', "Default general rule...")
        args["guideline_nonaccrual_well_secured_definition"] = non_accrual_guidelines.get('well_secured_definition', "Default well secured...")
        args["guideline_nonaccrual_in_process_of_collection_definition"] = non_accrual_guidelines.get('in_process_of_collection_definition', "Default in process...")
        args["guideline_nonaccrual_return_to_accrual_conditions"] = non_accrual_guidelines.get('return_to_accrual_conditions', "Default return conditions...")
        args["guideline_interest_capitalization"] = handbook_acct.get('capitalization_of_interest', "Default interest cap...") # Context
        # Data
        args["payment_history_status_str"] = str(financial_data.get('market_data', {}).get('payment_history_placeholder', "Current"))
        args["days_past_due_int"] = loan_details.get('days_past_due_placeholder', 0)
        args["is_well_secured_bool"] = company_data_package.get('collateral_and_debt_details',{}).get('is_well_secured_placeholder', False)
        args["is_in_process_of_collection_bool"] = loan_details.get('is_in_process_of_collection_placeholder', False)
        args["expects_full_payment_bool"] = loan_details.get('expects_full_payment_placeholder', True)
        args["is_maintained_on_cash_basis_due_to_deterioration_bool"] = loan_details.get('is_cash_basis_due_to_deterioration_placeholder', False)
        args["repayment_capacity_assessment_str"] = repayment_assessment_str # From other skill
        args["notes_financial_deterioration_str"] = str(qual_info.get('financial_deterioration_notes_placeholder', "None noted."))
        args["interest_capitalization_status_str"] = str(financial_data.get('market_data', {}).get('interest_capitalization_placeholder', "No"))
        args["current_accrual_status_str"] = str(loan_details.get('current_accrual_status_placeholder',"Accrual"))
        logging.debug(f"SNC_XAI:PREP_ARGS:AssessNonAccrualStatusIndication: {args}")
        return args

    def _prepare_args_for_repayment_capacity_sk(self, company_data_package: Dict[str, Any]) -> KernelArguments:
        args = KernelArguments()
        financial_data = company_data_package.get('financial_data_detailed', {})
        qual_info = company_data_package.get('qualitative_company_info', {})
        loan_details = company_data_package.get('loan_details', {})
        # Guidelines
        handbook_rep = self.comptrollers_handbook_snc.get('repayment_capacity', {}) # New structured path
        args["guideline_repayment_source"] = handbook_rep.get('primary_source_definition', "Default primary source...")
        args["guideline_substandard_paying_capacity"] = self.comptrollers_handbook_snc.get('regulatory_classifications', {}).get('substandard', {}).get('definition', "Paying capacity is inadequate.") # from previous structure
        args["guideline_expected_performance_period"] = handbook_rep.get('expected_performance_period', "Default perf period...")
        args["guideline_cash_flow_analysis_details"] = handbook_rep.get('cash_flow_analysis_details', "Default CF analysis...")
        args["guideline_ratio_analysis_details"] = handbook_rep.get('ratio_analysis_details', "Default ratio analysis...")
        args["guideline_projection_analysis_details"] = handbook_rep.get('projection_analysis_details', "Default proj analysis...")
        args["guideline_other_repayment_sources_caution"] = handbook_rep.get('other_sources_caution', "Default other sources caution...")
        # Data
        args["historical_fcf_str"] = str(financial_data.get("cash_flow_statement", {}).get('free_cash_flow', ["N/A"]))
        args["historical_cfo_str"] = str(financial_data.get("cash_flow_statement", {}).get('cash_flow_from_operations', ["N/A"]))
        args["annual_debt_service_str"] = str(financial_data.get("market_data", {}).get("annual_debt_service_placeholder", "Not Available"))
        args["relevant_ratios_summary_str"] = json.dumps(financial_data.get("key_ratios", {})) if financial_data.get("key_ratios") else "Not available"
        args["projected_fcf_str"] = str(financial_data.get("dcf_assumptions", {}).get("projected_fcf_placeholder", "Not Available"))
        args["qualitative_notes_stability_str"] = str(qual_info.get("revenue_cashflow_stability_notes_placeholder", "None provided."))
        args["other_repayment_sources_details_str"] = str(loan_details.get('other_repayment_sources_placeholder', "None specified."))
        logging.debug(f"SNC_XAI:PREP_ARGS:AssessRepaymentCapacity: {args}")
        return args

    # --- End of New SK Argument Preparation Helper Methods ---

    async def _determine_rating(self, company_name: str, 
                               company_data_package: Dict[str, Any], # Changed signature
                               # financial_analysis: Dict[str, Any], # Replaced by company_data_package
                               # qualitative_analysis: Dict[str, Any], # Replaced by company_data_package
                               # credit_risk_mitigation: Dict[str, Any], # Replaced by company_data_package
                               # economic_data_context: Dict[str, Any], # Replaced by company_data_package
                               sk_press_release_insights: Optional[Dict[str, str]] = None # Made optional
                               ) -> Tuple[Optional[SNCRating], str]:
        """
        Determines the SNC rating and generates a rationale by invoking multiple Semantic Kernel skills.

        This method integrates financial analysis results, qualitative assessments,
        credit risk mitigation information, and economic context. It uses Semantic
        Kernel skills with guidelines from agent configuration
        to assess various risk aspects. Fallback logic based on key financial ratios
        is applied if SK skill outputs are inconclusive or unavailable.
        The final rating and a consolidated rationale are returned.
        """
        # logging.debug(f"SNC_DETERMINE_RATING_INPUT: company='{company_name}', financial_analysis_keys={list(financial_analysis.keys())}, qualitative_analysis_keys={list(qualitative_analysis.keys())}, credit_mitigation_keys={list(credit_risk_mitigation.keys())}, economic_context_keys={list(economic_data_context.keys())}, press_release_insights_keys={list(sk_press_release_insights.keys()) if sk_press_release_insights else []}")
        logging.debug(f"SNC_DETERMINE_RATING_INPUT: company='{company_name}', company_data_package keys: {list(company_data_package.keys())}, press_release_insights keys: {list(sk_press_release_insights.keys()) if sk_press_release_insights else []}")

        rationale_parts = []
        final_rating_reasoning = [] # Stores reasons for rating changes
        current_rating = SNCRating.PASS # Start with PASS and downgrade

        # Add SK-generated press release insights to rationale
        if sk_press_release_insights:
            # This check is now more important as the method is called directly
            if isinstance(sk_press_release_insights, dict) and sk_press_release_insights.get("relevant_info"):
                rationale_parts.append("Press Release Insights (SK: ExtractSNCRelevantInfoFromPressReleaseSkill):")
                rationale_parts.append(sk_press_release_insights["relevant_info"])
                if sk_press_release_insights.get("overall_tone"):
                    rationale_parts.append(f"Overall Tone from Press Release: {sk_press_release_insights['overall_tone']}")
                rationale_parts.append("\n")
            elif isinstance(sk_press_release_insights, str): # backward compatibility if old summarization was used
                rationale_parts.append(f"Press Release Summary (Legacy): {sk_press_release_insights}\n")


        # Placeholder for skill results
        skill_outputs = {}

        kernel = self.get_kernel()
        if not kernel:
            logging.warning(f"SNC_XAI:SK_WARNING: Kernel not available for SNC rating determination for {company_name}. Proceeding with fallback logic.")
            # Simplified fallback if kernel is entirely missing - this part needs more thought
            # For now, it will just use the old DtE/Profitability logic
            # financial_analysis_result_fallback = self._perform_financial_analysis(company_data_package.get('financial_data_detailed',{}), {}) # Minimal call
            # debt_to_equity = financial_analysis_result_fallback.get("debt_to_equity")
            # profitability = financial_analysis_result_fallback.get("profitability")
            # Fallback logic here - this will be part of the larger refactor below.
            # For now, just return undetermined if no kernel.
            return None, "Rating undetermined: Semantic Kernel not available for full analysis."

        # --- Invoke All Skills ---
        try:
            # 1. FinancialStatementAnalysisSkill
            skill_name_fs = "FinancialStatementAnalysisSkill"
            args_fs = self._prepare_args_for_financial_statement_analysis_sk(company_data_package)
            logging.debug(f"SNC_XAI:SK_INPUT:{skill_name_fs}: {args_fs}")
            result_fs = await kernel.invoke(kernel.plugins[self.skills_plugin_name][skill_name_fs], **args_fs)
            skill_outputs[skill_name_fs] = str(result_fs)
            logging.debug(f"SNC_XAI:SK_OUTPUT:{skill_name_fs}: {skill_outputs[skill_name_fs][:300]}...") # Log snippet
            rationale_parts.append(f"Financial Statement Analysis (SK: {skill_name_fs}):\n{skill_outputs[skill_name_fs]}\n")

            # 2. AssessRepaymentCapacity (Refined)
            skill_name_repayment = "AssessRepaymentCapacity"
            args_repayment = self._prepare_args_for_repayment_capacity_sk(company_data_package)
            logging.debug(f"SNC_XAI:SK_INPUT:{skill_name_repayment}: {args_repayment}")
            result_repayment = await kernel.invoke(kernel.plugins[self.skills_plugin_name][skill_name_repayment], **args_repayment)
            skill_outputs[skill_name_repayment] = str(result_repayment)
            logging.debug(f"SNC_XAI:SK_OUTPUT:{skill_name_repayment}: {skill_outputs[skill_name_repayment][:300]}...")
            rationale_parts.append(f"Repayment Capacity Assessment (SK: {skill_name_repayment}):\n{skill_outputs[skill_name_repayment]}\n")
            # Extract assessment for other skills and rating logic
            repayment_assessment_str = "Adequate" # Default
            if "Assessment: Strong" in skill_outputs[skill_name_repayment]: repayment_assessment_str = "Strong"
            elif "Assessment: Weak" in skill_outputs[skill_name_repayment]: repayment_assessment_str = "Weak"
            elif "Assessment: Unsustainable" in skill_outputs[skill_name_repayment]: repayment_assessment_str = "Unsustainable"


            # 3. QualitativeFactorsSkill
            skill_name_qual = "QualitativeFactorsSkill"
            args_qual = self._prepare_args_for_qualitative_factors_sk(company_data_package)
            logging.debug(f"SNC_XAI:SK_INPUT:{skill_name_qual}: {args_qual}")
            result_qual = await kernel.invoke(kernel.plugins[self.skills_plugin_name][skill_name_qual], **args_qual)
            skill_outputs[skill_name_qual] = str(result_qual)
            logging.debug(f"SNC_XAI:SK_OUTPUT:{skill_name_qual}: {skill_outputs[skill_name_qual][:300]}...")
            rationale_parts.append(f"Qualitative Factors Assessment (SK: {skill_name_qual}):\n{skill_outputs[skill_name_qual]}\n")

            # 4. CollateralRiskAssessment (Refined)
            skill_name_collateral = "CollateralRiskAssessment"
            args_collateral = self._prepare_args_for_collateral_assessment_sk(company_data_package)
            logging.debug(f"SNC_XAI:SK_INPUT:{skill_name_collateral}: {args_collateral}")
            result_collateral = await kernel.invoke(kernel.plugins[self.skills_plugin_name][skill_name_collateral], **args_collateral)
            skill_outputs[skill_name_collateral] = str(result_collateral)
            logging.debug(f"SNC_XAI:SK_OUTPUT:{skill_name_collateral}: {skill_outputs[skill_name_collateral][:300]}...")
            rationale_parts.append(f"Collateral Risk Assessment (SK: {skill_name_collateral}):\n{skill_outputs[skill_name_collateral]}\n")
            collateral_assessment_str = "Adequate" # Default
            if "Assessment: Strong" in skill_outputs[skill_name_collateral]: collateral_assessment_str = "Strong"
            elif "Assessment: Marginally Adequate" in skill_outputs[skill_name_collateral]: collateral_assessment_str = "Marginally Adequate"
            elif "Assessment: Inadequate" in skill_outputs[skill_name_collateral]: collateral_assessment_str = "Inadequate"


            # 5. AdvancedCreditRiskMitigationSkill
            skill_name_adv_crm = "AdvancedCreditRiskMitigationSkill"
            args_adv_crm = self._prepare_args_for_advanced_credit_risk_mitigation_sk(company_data_package)
            logging.debug(f"SNC_XAI:SK_INPUT:{skill_name_adv_crm}: {args_adv_crm}")
            result_adv_crm = await kernel.invoke(kernel.plugins[self.skills_plugin_name][skill_name_adv_crm], **args_adv_crm)
            skill_outputs[skill_name_adv_crm] = str(result_adv_crm)
            logging.debug(f"SNC_XAI:SK_OUTPUT:{skill_name_adv_crm}: {skill_outputs[skill_name_adv_crm][:300]}...")
            rationale_parts.append(f"Advanced Credit Risk Mitigation Assessment (SK: {skill_name_adv_crm}):\n{skill_outputs[skill_name_adv_crm]}\n")

            # 6. StructuralWeaknessIdentificationSkill
            skill_name_struct = "StructuralWeaknessIdentificationSkill"
            args_struct = self._prepare_args_for_structural_weakness_sk(company_data_package)
            logging.debug(f"SNC_XAI:SK_INPUT:{skill_name_struct}: {args_struct}")
            result_struct = await kernel.invoke(kernel.plugins[self.skills_plugin_name][skill_name_struct], **args_struct)
            skill_outputs[skill_name_struct] = str(result_struct)
            logging.debug(f"SNC_XAI:SK_OUTPUT:{skill_name_struct}: {skill_outputs[skill_name_struct][:300]}...")
            rationale_parts.append(f"Structural Weakness Identification (SK: {skill_name_struct}):\n{skill_outputs[skill_name_struct]}\n")
            # Example parsing for rating logic:
            structural_integrity_assessment = "Sound"
            if "critical structural flaws" in skill_outputs[skill_name_struct].lower():
                structural_integrity_assessment = "Critical Flaws"
            elif "structural weaknesses requiring attention" in skill_outputs[skill_name_struct].lower():
                structural_integrity_assessment = "Weaknesses Found"


            # 7. AssessNonAccrualStatusIndication (Refined)
            # Note: This skill might be called after an initial classification if it depends on it.
            # For now, assume it's called with a preliminary 'Pass' or the current rating.
            skill_name_nonaccrual = "AssessNonAccrualStatusIndication"
            args_nonaccrual = self._prepare_args_for_non_accrual_sk(company_data_package, repayment_assessment_str) # Pass repayment assessment
            logging.debug(f"SNC_XAI:SK_INPUT:{skill_name_nonaccrual}: {args_nonaccrual}")
            result_nonaccrual = await kernel.invoke(kernel.plugins[self.skills_plugin_name][skill_name_nonaccrual], **args_nonaccrual)
            skill_outputs[skill_name_nonaccrual] = str(result_nonaccrual)
            logging.debug(f"SNC_XAI:SK_OUTPUT:{skill_name_nonaccrual}: {skill_outputs[skill_name_nonaccrual][:300]}...")
            rationale_parts.append(f"Non-Accrual Status Assessment (SK: {skill_name_nonaccrual}):\n{skill_outputs[skill_name_nonaccrual]}\n")
            nonaccrual_assessment_str = "Accrual" # Default
            if "Assessment: Appropriate Status: Nonaccrual" in skill_outputs[skill_name_nonaccrual] or "Recommended Action: Place on Nonaccrual" in skill_outputs[skill_name_nonaccrual]:
                nonaccrual_assessment_str = "Nonaccrual Warranted"

            # 8. AccountingComplianceSkill
            # This skill might also depend on a preliminary classification.
            skill_name_acct = "AccountingComplianceSkill"
            # For current_classification, we might need a pre-assessment or use 'Pass' initially.
            # Let's assume 'Pass' for now or derive from previous non-accrual/repayment.
            prelim_classification_for_acct = current_rating.value # Use current_rating before it's finalized
            args_acct = self._prepare_args_for_accounting_compliance_sk(company_data_package, prelim_classification_for_acct)
            logging.debug(f"SNC_XAI:SK_INPUT:{skill_name_acct}: {args_acct}")
            result_acct = await kernel.invoke(kernel.plugins[self.skills_plugin_name][skill_name_acct], **args_acct)
            skill_outputs[skill_name_acct] = str(result_acct)
            logging.debug(f"SNC_XAI:SK_OUTPUT:{skill_name_acct}: {skill_outputs[skill_name_acct][:300]}...")
            rationale_parts.append(f"Accounting Compliance Assessment (SK: {skill_name_acct}):\n{skill_outputs[skill_name_acct]}\n")
            # Example parsing for rating logic:
            accounting_compliance_summary = "Compliant"
            if "Overall Accounting Compliance Summary:\nIdentified issues" in skill_outputs[skill_name_acct] or "Overall Accounting Compliance Summary:\nPotential issues" in skill_outputs[skill_name_acct] : # crude check
                accounting_compliance_summary = "Issues Found"

        except Exception as e:
            logging.error(f"SNC_XAI:SK_ERROR: Exception during SK skill invocation for {company_name}: {e}")
            rationale_parts.append(f"Error during comprehensive SK analysis: {e}. Rating may be based on limited data or fallback logic.\n")
            # Fallback or partial rating logic might be needed here.

        # --- Revised Rating Logic ---
        logging.debug(f"SNC_XAI:RATING_INPUTS_PRIMARY: Repayment='{repayment_assessment_str}', NonAccrual='{nonaccrual_assessment_str}', Collateral='{collateral_assessment_str}', Structural='{structural_integrity_assessment}', Accounting='{accounting_compliance_summary}'")

        if repayment_assessment_str == "Unsustainable":
            current_rating = SNCRating.LOSS
            final_rating_reasoning.append("Repayment capacity assessed as Unsustainable (SK: AssessRepaymentCapacity).")
        elif nonaccrual_assessment_str == "Nonaccrual Warranted" and repayment_assessment_str == "Weak":
            current_rating = SNCRating.LOSS # Or Doubtful, handbook dependent
            final_rating_reasoning.append("Nonaccrual Warranted and Weak repayment capacity (SK: AssessNonAccrualStatusIndication, AssessRepaymentCapacity).")

        if current_rating.value > SNCRating.DOUBTFUL.value : # If not already Loss
            if repayment_assessment_str == "Weak":
                current_rating = SNCRating.DOUBTFUL
                final_rating_reasoning.append("Repayment capacity assessed as Weak (SK: AssessRepaymentCapacity).")
            elif structural_integrity_assessment == "Critical Flaws" and repayment_assessment_str != "Strong":
                current_rating = SNCRating.DOUBTFUL
                final_rating_reasoning.append("Critical structural flaws identified and repayment not Strong (SK: StructuralWeaknessIdentificationSkill, AssessRepaymentCapacity).")

        if current_rating.value > SNCRating.SUBSTANDARD.value: # If not already Loss or Doubtful
            if nonaccrual_assessment_str == "Nonaccrual Warranted":
                current_rating = SNCRating.SUBSTANDARD
                final_rating_reasoning.append("Nonaccrual status Warranted (SK: AssessNonAccrualStatusIndication).")
            elif collateral_assessment_str == "Inadequate":
                current_rating = SNCRating.SUBSTANDARD
                final_rating_reasoning.append("Collateral risk assessed as Inadequate (SK: CollateralRiskAssessment).")
            elif structural_integrity_assessment == "Critical Flaws": # If repayment was strong but flaws exist
                current_rating = SNCRating.SUBSTANDARD
                final_rating_reasoning.append("Critical structural flaws identified (SK: StructuralWeaknessIdentificationSkill).")
            elif structural_integrity_assessment == "Weaknesses Found" and repayment_assessment_str != "Strong":
                current_rating = SNCRating.SUBSTANDARD
                final_rating_reasoning.append("Structural weaknesses found and repayment not Strong (SK: StructuralWeaknessIdentificationSkill, AssessRepaymentCapacity).")
            elif accounting_compliance_summary == "Issues Found" and repayment_assessment_str != "Strong":
                 current_rating = SNCRating.SUBSTANDARD
                 final_rating_reasoning.append("Accounting compliance issues found and repayment not Strong (SK: AccountingComplianceSkill, AssessRepaymentCapacity).")


        if current_rating.value > SNCRating.SPECIAL_MENTION.value: # If not already Substandard or worse
            if repayment_assessment_str == "Adequate" and (collateral_assessment_str == "Marginally Adequate" or structural_integrity_assessment == "Weaknesses Found"):
                current_rating = SNCRating.SPECIAL_MENTION
                final_rating_reasoning.append("Adequate repayment but with marginal collateral or structural weaknesses (SK: AssessRepaymentCapacity, CollateralRiskAssessment, StructuralWeaknessIdentificationSkill).")
            elif "Overall Qualitative Risk Summary:" in skill_outputs.get(skill_name_qual, "") and "significant weaknesses" in skill_outputs[skill_name_qual].lower() : # Example
                 current_rating = SNCRating.SPECIAL_MENTION
                 final_rating_reasoning.append("Significant qualitative weaknesses identified (SK: QualitativeFactorsSkill).")
            # Add more Special Mention conditions based on other skill outputs if needed

        # --- Old Fallback Logic (as a last resort or final check if still PASS) ---
        if not final_rating_reasoning and current_rating == SNCRating.PASS : # Only if no SK rule triggered a change
            financial_data_detailed = company_data_package.get('financial_data_detailed', {})
            key_ratios = financial_data_detailed.get("key_ratios", {}) # For DtE, Profitability
            debt_to_equity = key_ratios.get("debt_to_equity_ratio")
            profitability = key_ratios.get("net_profit_margin")
            # economic_conditions = company_data_package.get('economic_data_context', {}).get("overall_outlook", "Stable") # Already in qual skill
            # collateral_quality_fallback = company_data_package.get('collateral_and_debt_details', {}).get("collateral_quality_fallback_placeholder", "Low") # Covered by Collateral SK
            # management_quality = company_data_package.get('qualitative_company_info', {}).get("management_assessment", "Not Assessed") # Covered by Qual SK

            logging.debug(f"SNC_XAI:RATING_RULE_FALLBACK_INPUTS: DtE={debt_to_equity}, Profitability={profitability}")
            if debt_to_equity is not None and profitability is not None:
                if debt_to_equity > 3.0 and profitability < 0:
                    current_rating = SNCRating.LOSS
                    final_rating_reasoning.append("Fallback: High D/E ratio and negative profitability.")
                elif debt_to_equity > 2.0 and profitability < 0.1:
                    current_rating = SNCRating.DOUBTFUL
                    final_rating_reasoning.append("Fallback: Elevated D/E ratio and low profitability.")
                # Removed other fallback conditions as they are better covered by specific skills now.
                # The SM for mixed indicators might be too broad if all skills ran and found nothing.
            elif not skill_outputs: # If SK skills totally failed to produce output
                current_rating = None # Undetermined
                final_rating_reasoning.append("Fallback: Rating undetermined due to missing key financial metrics and SK analysis failure.")

        if not final_rating_reasoning and current_rating == SNCRating.PASS:
            final_rating_reasoning.append("Overall assessment indicates a Pass rating based on available information and SK analysis.")
        elif not final_rating_reasoning and current_rating is None: # Should not happen if logic is complete
             final_rating_reasoning.append("Rating could not be determined.")


        rationale_parts.append(f"\nFinal Rating Determination Process:")
        for reason in final_rating_reasoning:
            rationale_parts.append(f"- {reason}")

        rationale_parts.append(f"\nFinal Assigned Rating: {current_rating.value if current_rating else 'Undetermined'}")
        rationale_parts.append(f"Regulatory guidance: Comptroller's Handbook SNC v{self.comptrollers_handbook_snc.get('version', 'N/A')}, OCC Guidelines v{self.occ_guidelines_snc.get('version', 'N/A')}.")
        final_rationale = "\n".join(filter(None, rationale_parts))

        logging.debug(f"SNC_DETERMINE_RATING_OUTPUT: Final Rating='{current_rating.value if current_rating else 'Undetermined'}', Rationale Snippet='{final_rationale[:300]}...'")
        logging.info(f"SNC rating for {company_name}: {current_rating.value if current_rating else 'Undetermined'}.")
        return current_rating, final_rationale

    async def _analyze_press_releases_with_sk(self, shared_context: SharedContext, company_info: Dict[str, Any]) -> Optional[Dict[str, str]]: # Added company_info
        """
        Analyzes available press release texts from SharedContext using ExtractSNCRelevantInfoFromPressReleaseSkill.
        Returns a dictionary with 'relevant_info' and 'overall_tone'.
        """
        # insights = {} # Old structure
        output_dict = {"relevant_info": "No relevant press releases analyzed or no information extracted.", "overall_tone": "Neutral"}
        kernel = self.get_kernel()
        if not kernel:
            logging.warning("SNC_ANALYZE_PR: Kernel not available, cannot analyze press releases.")
            return output_dict

        # These keys should match the 'context_key' provided in the workflow for DataIngestionAgent
        # For simplicity, let's assume one main press release for now, or the agent could loop if multiple are structured.
        # This example takes the first one found from a predefined list.
        press_release_context_keys_to_check = ["press_release_q1_2025", "press_release_q4_2024", "latest_press_release"]
        
        press_release_text = None
        found_context_key = None
        for key in press_release_context_keys_to_check:
            text = shared_context.get_data(key)
            if text and isinstance(text, str):
                press_release_text = text
                found_context_key = key
                logging.info(f"SNC_ANALYZE_PR: Found press release text in SharedContext with key '{found_context_key}'.")
                break

        if not press_release_text:
            logging.info("SNC_ANALYZE_PR: No press release text found in SharedContext for predefined keys.")
            return output_dict

        try:
            skill_name_pr = "ExtractSNCRelevantInfoFromPressReleaseSkill"
            # key_areas_csv = self.config.get('press_release_key_areas_csv', "financial results,debt,management changes,layoffs,regulatory issues,product failures,M&A,strategic partnerships,market outlook")
            # For now, use the default from skill config if not in agent config.
            # The skill itself has a default, so we might not even need to pass it if the default is good.
            # For explicit control:
            key_areas_csv = "financial results,debt,management changes,layoffs,regulatory issues,product failures,M&A,strategic partnerships,market outlook,earnings forecast,legal proceedings"


            args_pr = KernelArguments(
                press_release_text=press_release_text,
                company_name=company_info.get('name', "the company"),
                key_areas_of_concern_csv=key_areas_csv
            )
            logging.debug(f"SNC_XAI:SK_INPUT:{skill_name_pr}: company_name='{args_pr['company_name']}', key_areas='{args_pr['key_areas_of_concern_csv']}', text length={len(press_release_text)}")

            result_pr = await kernel.invoke(
                kernel.plugins[self.skills_plugin_name][skill_name_pr],
                **args_pr
            )
            raw_output_str = str(result_pr)
            logging.debug(f"SNC_XAI:SK_OUTPUT:{skill_name_pr}: {raw_output_str[:300]}...")

            # Simple parsing based on example output structure
            # "Relevant Information from Press Release:\n[...]\nOverall Tone: [Tone]"
            relevant_info_part = raw_output_str
            overall_tone_part = "Neutral (tone not explicitly extracted)"

            if "Overall Tone:" in raw_output_str:
                parts = raw_output_str.split("Overall Tone:", 1)
                relevant_info_part = parts[0].replace("Relevant Information from Press Release:", "").strip()
                overall_tone_part = parts[1].strip()

            output_dict["relevant_info"] = relevant_info_part
            output_dict["overall_tone"] = overall_tone_part

            logging.info(f"SNC_ANALYZE_PR: Successfully analyzed press release. Tone: {overall_tone_part}")
            return output_dict

        except Exception as e:
            logging.error(f"SNC_ANALYZE_PR: Error analyzing press release using SK skill {skill_name_pr}: {e}")
            output_dict["relevant_info"] = f"Error during SK analysis of press release: {e}"
            output_dict["overall_tone"] = "Error"
            return output_dict

        # return insights # Old return
        This method integrates financial analysis results, qualitative assessments, 
        credit risk mitigation information, and economic context. It uses Semantic 
        Kernel skills (CollateralRiskAssessment, AssessRepaymentCapacity, 
        AssessNonAccrualStatusIndication) with guidelines from agent configuration
        to assess various risk aspects. Fallback logic based on key financial ratios
        is applied if SK skill outputs are inconclusive or unavailable.
        The final rating and a consolidated rationale are returned.
        """
        logging.debug(f"SNC_DETERMINE_RATING_INPUT: company='{company_name}', financial_analysis_keys={list(financial_analysis.keys())}, qualitative_analysis_keys={list(qualitative_analysis.keys())}, credit_mitigation_keys={list(credit_risk_mitigation.keys())}, economic_context_keys={list(economic_data_context.keys())}, press_release_insights_keys={list(sk_press_release_insights.keys())}")
        
        rationale_parts = []
        
        # Add SK-generated press release insights to rationale
        if sk_press_release_insights:
            rationale_parts.append("SK-Generated Press Release Insights:")
            for period, insight in sk_press_release_insights.items():
                rationale_parts.append(f"  - {period.replace('_', ' ').title()}: {insight}")
            rationale_parts.append("\n") # Add a newline for separation

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
                    "guideline_substandard_collateral": self.comptrollers_handbook_snc.get('regulatory_classifications', {}).get('substandard', {}).get('definition', "Collateral is inadequately protective."),
                    "guideline_repayment_source": self.comptrollers_handbook_snc.get('general_principles', {}).get('primary_repayment_source_definition', "Primary repayment should come from a sustainable source of cash under borrower control."),
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
                    "guideline_repayment_source": self.comptrollers_handbook_snc.get('general_principles', {}).get('primary_repayment_source_definition', "Primary repayment should come from a sustainable source of cash under borrower control."), # Matched to collateral skill for now
                    "guideline_substandard_paying_capacity": self.comptrollers_handbook_snc.get('regulatory_classifications', {}).get('substandard', {}).get('definition', "Paying capacity is inadequate."),
                    "repayment_capacity_period_years": str(self.comptrollers_handbook_snc.get('general_principles', {}).get('expected_performance_evaluation_period_years', 7)),
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
                    "guideline_nonaccrual_status": self.comptrollers_handbook_snc.get('accounting_issues', {}).get('nonaccrual_status', {}).get('general_rule_summary', "A loan should be placed on nonaccrual status when principal or interest is 90 days or more past due, unless it is well secured and in the process of collection; or payment in full is expected."),
                    "guideline_interest_capitalization": self.comptrollers_handbook_snc.get('accounting_issues', {}).get('capitalization_of_interest', "Capitalization of interest should be supported by an improvement in the borrower's financial condition that demonstrates an ability to repay the additional debt."),
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

# Removed old SK calls from here, will be done inside the new _determine_rating structure.
# The old rating logic is also removed and will be replaced by the new comprehensive logic.
