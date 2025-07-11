# cacm_adk_core/agents/fundamental_analyst_agent.py

import csv
import os

# from core.utils.data_utils import send_message # send_message is not used in this file

import logging
import pandas as pd
import numpy as np
from scipy import stats  # For statistical calculations (e.g., for DCF)
from typing import Dict, Any, Optional, Union, List  # Added List
from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext

# from semantic_kernel import Kernel # No longer needed directly for type hint in init
from semantic_kernel.functions.kernel_arguments import KernelArguments  # Added for SK
import asyncio

# import yaml # Not used in agent logic
# from unittest.mock import patch # Not used in agent logic


# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # Handled by orchestrator/base
# For XAI debug logs, ensure the logger level is set to DEBUG if you want to see them.
# Example: logging.getLogger().setLevel(logging.DEBUG) in the main application or test setup.


class FundamentalAnalystAgent(Agent):
    """
    Agent for performing fundamental analysis of companies.

    This agent analyzes financial statements, calculates key financial ratios,
    performs valuation modeling (DCF and comparables), and assesses financial health.
    It relies on DataRetrievalAgent for fetching company data via A2A communication.
    """

    def __init__(
        self,
        kernel_service: KernelService,
        agent_config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            agent_name="FundamentalAnalystAgent",
            kernel_service=kernel_service,
            skills_plugin_name="FundamentalAnalysisSkill",
        )
        self.config = agent_config if agent_config else {}  # Store agent_config
        self.persona = self.config.get("persona", "Financial Analyst")
        self.description = self.config.get(
            "description", "Performs fundamental company analysis."
        )
        # Peer agent management is now handled by the base Agent class via self.get_or_create_agent()

    async def run(
        self,
        task_description: str,
        current_step_inputs: Dict[str, Any],
        shared_context: SharedContext,
    ) -> Dict[str, Any]:
        """
        Performs fundamental analysis on a given company.

        This involves:
        1. Retrieving company data via DataRetrievalAgent.
        2. Calculating key financial ratios.
        3. Performing DCF valuation (with potential overrides from inputs).
        4. Calculating Enterprise Value.
        5. Assessing overall financial health.
        6. Generating a textual analysis summary using an SK skill (with potential custom guidance from inputs).

        Args:
            task_description (str): Description of the analysis task.
            current_step_inputs (Dict[str, Any]): Inputs for this step, including:
                - "company_id" (str): The unique identifier for the company. Required.
                - "summary_guidance_prompt_addon" (str, optional): Custom guidance for the
                  SK skill generating the analysis summary.
                - "dcf_override_discount_rate" (float, optional): Value to override the
                  default/data-derived DCF discount rate.
                - "dcf_override_terminal_growth_rate" (float, optional): Value to override
                  the default/data-derived DCF terminal growth rate.
            shared_context (SharedContext): The shared context for the current CACM run.

        Returns:
            Dict[str, Any]: A dictionary containing the status and the analysis results:
                - {"status": "success", "data": <analysis_package_dict>}
                - {"status": "error", "message": <error_message_str>}
                The <analysis_package_dict> includes financial_ratios, dcf_valuation,
                enterprise_value, financial_health, and analysis_summary.
        """
        self.current_run_inputs = (
            current_step_inputs  # Store for access in helper methods
        )
        company_id = self.current_run_inputs.get("company_id")
        if not company_id:
            logging.error(
                "FAA_RUN_ERROR: 'company_id' not found in current_step_inputs."
            )
            return {
                "status": "error",
                "message": "'company_id' is required but was not provided.",
            }

        logging.info(
            f"Executing fundamental analysis for company_id: {company_id} (Task: {task_description})"
        )
        logging.debug(
            f"FAA_XAI:RUN_INPUT: company_id='{company_id}', task_description='{task_description}', inputs='{current_step_inputs}'"
        )

        try:
            company_data = await self.retrieve_company_data(company_id, shared_context)
            if company_data is None:
                logging.error(
                    f"Failed to retrieve company data for {company_id} via A2A."
                )
                return {
                    "status": "error",
                    "message": f"Could not retrieve data for company {company_id}",
                }

            logging.debug(f"FAA_XAI:RUN_COMPANY_DATA_KEYS: {list(company_data.keys())}")

            financial_ratios = self.calculate_financial_ratios(company_data)
            dcf_valuation_result = self.calculate_dcf_valuation(company_data)
            comps_valuation = self.calculate_comps_valuation(
                company_data
            )  # Placeholder
            enterprise_value_result = self.calculate_enterprise_value(company_data)
            financial_health = self.assess_financial_health(financial_ratios)

            # Summarize Press Releases
            press_release_summaries = await self._summarize_press_releases(
                shared_context
            )

            analysis_summary = await self.generate_analysis_summary(
                company_id,
                financial_ratios,
                dcf_valuation_result,
                comps_valuation,
                financial_health,
                enterprise_value_result,
                press_release_summaries,  # Pass summaries
            )

            result_package = {
                "company_id": company_id,
                "financial_ratios": financial_ratios,
                "dcf_valuation": dcf_valuation_result,
                "comps_valuation": comps_valuation,
                "enterprise_value": enterprise_value_result,
                "financial_health": financial_health,
                "press_release_summaries": press_release_summaries,  # Add to result
                "analysis_summary": analysis_summary,
                "data_source_notes": "Analysis incorporates data from financial statements and SK-generated summaries of available press releases.",
            }
            logging.debug(f"FAA_XAI:RUN_OUTPUT_SUCCESS: {result_package}")
            return {"status": "success", "data": result_package}

        except Exception as e:
            logging.exception(f"Error during fundamental analysis of {company_id}: {e}")
            logging.debug(f"FAA_XAI:RUN_OUTPUT_ERROR: Exception {e}")
            return {
                "status": "error",
                "message": f"An error occurred during analysis: {e}",
            }

    async def retrieve_company_data(
        self, company_id: str, shared_context: SharedContext
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves comprehensive company data by invoking the DataRetrievalAgent.

        This method uses the agent-to-agent (A2A) communication pattern facilitated
        by `self.get_or_create_agent()` to request data for the specified `company_id`.
        It expects the DataRetrievalAgent to return a structured data package.

        Args:
            company_id (str): The identifier of the company for which to retrieve data.
            shared_context (SharedContext): The shared context of the current run.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the company data package
            if successful, otherwise None.
        """
        dra_agent_name = "DataRetrievalAgent"  # This should match the name/key used for DRA registration
        logging.info(
            f"Attempting to get or create '{dra_agent_name}' to retrieve data for {company_id}."
        )

        try:
            # Note: get_or_create_agent now expects agent_name and shared_context
            dra_agent = await self.get_or_create_agent(dra_agent_name, shared_context)
            if not dra_agent:
                logging.error(
                    f"Could not get or create {dra_agent_name}. Cannot retrieve company data for {company_id}."
                )
                return None

            task_description_for_dra = "Retrieve financial data for a company"
            inputs_for_dra = {
                "company_id": company_id,
                "data_type": "get_company_financials",
            }  # Example inputs

            logging.info(
                f"Requesting company financials for {company_id} from {dra_agent_name}."
            )
            response_from_dra = await dra_agent.run(
                task_description_for_dra, inputs_for_dra, shared_context
            )

            if response_from_dra and response_from_dra.get("status") == "success":
                company_data = response_from_dra.get("data")
                logging.debug(
                    f"Data received from {dra_agent_name} for {company_id}: {company_data is not None}"
                )
                return company_data
            else:
                error_msg = (
                    response_from_dra.get("message", "Unknown error from DRA")
                    if response_from_dra
                    else "No response from DRA"
                )
                logging.warning(
                    f"{dra_agent_name} failed to provide data for {company_id}. Status: {response_from_dra.get('status') if response_from_dra else 'N/A'}, Message: {error_msg}"
                )
                return None

        except Exception as e:
            logging.exception(
                f"Error communicating with {dra_agent_name} for {company_id}: {e}"
            )
            return None

    def calculate_financial_ratios(
        self, company_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculates key financial ratios.
        """
        logging.debug(
            f"FAA_XAI:CALC_RATIOS_INPUT: company_data keys: {list(company_data.keys())}"
        )
        ratios = {}
        try:
            # Ensure financial_data_detailed and its sub-keys exist
            financial_details = company_data.get("financial_data_detailed", {})
            income_statement = financial_details.get("income_statement", {})
            balance_sheet = financial_details.get("balance_sheet", {})

            if not income_statement or not balance_sheet:
                logging.warning(
                    "FAA_XAI:CALC_RATIOS_WARN: Missing financial statements for ratio calculation."
                )
                return {}

            # Safely get values, assuming they are lists and we need the last element
            revenue_list = income_statement.get("revenue", [])
            net_income_list = income_statement.get("net_income", [])
            ebitda_list = income_statement.get("ebitda", [])

            total_assets_list = balance_sheet.get("total_assets", [])
            total_liabilities_list = balance_sheet.get("total_liabilities", [])
            shareholders_equity_list = balance_sheet.get("shareholders_equity", [])

            if not all(
                [
                    revenue_list,
                    net_income_list,
                    total_assets_list,
                    total_liabilities_list,
                    shareholders_equity_list,
                ]
            ):
                logging.warning(
                    "FAA_XAI:CALC_RATIOS_WARN: Missing essential lists in financial statements for ratio calculation."
                )
                return {}

            revenue = revenue_list[-1] if revenue_list else 0
            net_income = net_income_list[-1] if net_income_list else 0
            ebitda = ebitda_list[-1] if ebitda_list else 0

            total_assets = total_assets_list[-1] if total_assets_list else 0
            total_liabilities = (
                total_liabilities_list[-1] if total_liabilities_list else 0
            )
            shareholders_equity = (
                shareholders_equity_list[-1] if shareholders_equity_list else 0
            )

            logging.debug(
                f"FAA_XAI:CALC_RATIOS_VALUES: Revenue={revenue}, NetIncome={net_income}, EBITDA={ebitda}, Assets={total_assets}, Liab={total_liabilities}, Equity={shareholders_equity}"
            )

            ratios["revenue_growth"] = (
                (revenue / revenue_list[-2] - 1)
                if len(revenue_list) > 1 and revenue_list[-2] != 0
                else None
            )
            ratios["net_profit_margin"] = net_income / revenue if revenue else None
            ratios["return_on_equity"] = (
                net_income / shareholders_equity if shareholders_equity else None
            )
            ratios["debt_to_equity"] = (
                total_liabilities / shareholders_equity if shareholders_equity else None
            )
            ratios["current_ratio"] = (
                total_assets / total_liabilities if total_liabilities else None
            )  # Simplified current ratio
            ratios["ebitda_margin"] = ebitda / revenue if revenue and ebitda else None

        except (KeyError, IndexError, TypeError) as e:
            logging.exception(f"Error calculating financial ratios: {e}")
            logging.debug(f"FAA_XAI:CALC_RATIOS_ERROR: Exception {e}")
            return {}

        logging.debug(f"FAA_XAI:CALC_RATIOS_OUTPUT: {ratios}")
        return ratios

    def calculate_comps_valuation(
        self, company_data: Dict[str, Any]
    ) -> Optional[float]:
        logging.warning("Comps valuation not yet implemented.")
        return None

    def assess_financial_health(self, financial_ratios: Dict[str, float]) -> str:
        logging.debug(
            f"FAA_XAI:ASSESS_HEALTH_INPUT: financial_ratios={financial_ratios}"
        )
        if not financial_ratios:
            logging.debug(
                "FAA_XAI:ASSESS_HEALTH_RESULT: Ratios empty, returning Unknown."
            )
            return "Unknown"

        score = 0
        if financial_ratios.get("return_on_equity", 0) > 0.15:
            score += 2
        if financial_ratios.get("debt_to_equity", 1) < 1:
            score += 1
        if financial_ratios.get("current_ratio", 0) > 1.5:
            score += 1
        if financial_ratios.get("net_profit_margin", 0) > 0.1:
            score += 1
        if (
            financial_ratios.get("revenue_growth") is not None
            and financial_ratios.get("revenue_growth", 0) > 0.05
        ):
            score += 1  # Added check for > 0.05

        logging.debug(f"FAA_XAI:ASSESS_HEALTH_SCORE: Score={score}")

        health_assessment = "Weak"
        if score >= 4:
            health_assessment = "Strong"
        elif score >= 2:
            health_assessment = "Moderate"

        logging.debug(f"FAA_XAI:ASSESS_HEALTH_OUTPUT: Health='{health_assessment}'")
        return health_assessment

    async def _summarize_press_releases(
        self, shared_context: SharedContext
    ) -> Dict[str, str]:
        """
        Summarizes available press release texts from SharedContext using SK.
        """
        summaries = {}
        kernel = self.get_kernel()
        if not kernel:
            logging.warning(
                "FAA_SUMMARIZE_PR: Kernel not available, cannot summarize press releases."
            )
            return summaries

        # Define which press releases to look for in shared_context
        # These keys should match the 'context_key' provided in the workflow for DataIngestionAgent
        press_release_context_keys = {
            "q4_2024": "press_release_q4_2024",
            "q1_2025": "press_release_q1_2025",
        }

        for period, context_key in press_release_context_keys.items():
            press_release_text = shared_context.get_data(
                context_key
            )  # Ensure get_data is used
            if press_release_text and isinstance(press_release_text, str):
                logging.info(
                    f"FAA_SUMMARIZE_PR: Summarizing press release for {period} from context key '{context_key}'."
                )
                try:
                    args = KernelArguments(
                        input=press_release_text, max_sentences="5"
                    )  # Summarize to 5 sentences
                    summary_result = await kernel.invoke(
                        plugin_name="SummarizationSkills",  # As defined in semantic_kernel_adapter
                        function_name="summarize_section",  # From SK_MDNA_SummarizerSkill
                        arguments=args,
                    )
                    summary_value = str(summary_result)
                    if (
                        summary_value
                        and "[Placeholder LLM Summary:" not in summary_value
                    ):  # Check if not placeholder
                        summaries[f"summary_press_release_{period}"] = summary_value
                        logging.info(
                            f"FAA_SUMMARIZE_PR: Successfully summarized press release for {period}."
                        )
                        logging.debug(
                            f"FAA_XAI:SUMMARIZE_PR_SK_OUTPUT_{period}: '{summary_value}'"
                        )
                    else:
                        logging.warning(
                            f"FAA_SUMMARIZE_PR: Received placeholder or empty summary for {period} from SK. Text was: {summary_value}"
                        )
                        summaries[f"summary_press_release_{period}"] = (
                            "Summary could not be generated by SK (placeholder returned)."
                        )

                except Exception as e:
                    logging.error(
                        f"FAA_SUMMARIZE_PR: Error summarizing press release for {period} using SK: {e}"
                    )
                    summaries[f"summary_press_release_{period}"] = (
                        f"Error during SK summarization: {e}"
                    )
            else:
                logging.info(
                    f"FAA_SUMMARIZE_PR: No press release text found in SharedContext for key '{context_key}' ({period})."
                )
                summaries[f"summary_press_release_{period}"] = (
                    "Not available in SharedContext."
                )

        return summaries

    async def generate_analysis_summary(
        self,
        company_id: str,
        financial_ratios: Dict[str, float],
        dcf_valuation: Optional[float],
        comps_valuation: Optional[float],
        financial_health: str,
        enterprise_value: Optional[float],
        press_release_summaries: Dict[str, str],
    ) -> str:  # Added press_release_summaries
        """
        Generates a textual summary of the fundamental analysis using a Semantic Kernel skill.

        It compiles various analytical components (ratios, valuation, health assessment, press release summaries)
        into a structured input for the "SummarizeAnalysis" SK skill.
        If `summary_guidance_prompt_addon` is present in `self.current_run_inputs`
        (passed from the `run` method's inputs), it will be used to customize or
        replace the default prompt for the SK skill.

        Args:
            company_id (str): Company identifier.
            financial_ratios (Dict[str, float]): Calculated financial ratios.
            dcf_valuation (Optional[float]): DCF valuation result.
            comps_valuation (Optional[float]): Comparables valuation result (currently placeholder).
            financial_health (str): Assessed financial health string.
            enterprise_value (Optional[float]): Calculated enterprise value.

        Returns:
            str: The generated analysis summary text. Falls back to a basic formatted
                 string if SK skill execution fails or kernel is not available.
        """
        kernel = self.get_kernel()
        if kernel:
            try:
                ratios_str_parts = []
                if financial_ratios:
                    for ratio, value in financial_ratios.items():
                        ratios_str_parts.append(
                            f"  - {ratio}: {value:.2f}"
                            if value is not None
                            else f"  - {ratio}: N/A"
                        )
                ratios_summary_str = (
                    "\n".join(ratios_str_parts) if ratios_str_parts else "Not available"
                )

                dcf_summary = (
                    f"Value: {dcf_valuation:.2f}"
                    if dcf_valuation is not None
                    else "Not available"
                )
                comps_summary = (
                    f"Value: {comps_valuation:.2f}"
                    if comps_valuation is not None
                    else "Not available"
                )
                enterprise_value_summary_str = (
                    f"Value: {enterprise_value:.2f}"
                    if enterprise_value is not None
                    else "Not available"
                )

                DEFAULT_FAA_SUMMARY_PROMPT = (
                    "Provide a comprehensive analysis conclusion based on the provided data. "
                    "Your summary should cover the following aspects clearly:\n"
                    "- Start with an overall assessment of the company's financial health (as provided) and briefly justify it.\n"
                    "- Discuss key insights derived from the financial ratios. Highlight any ratios that are particularly strong, weak, or show significant trends.\n"
                    "- Explain the implications of the DCF valuation and Enterprise Value, if available. What do these values suggest about the company's intrinsic worth or market perception?\n"
                    "- If available, comment on the estimated default likelihood and recovery rate.\n"
                    "- Conclude with a balanced view, mentioning both positive aspects and potential concerns or areas requiring further investigation.\n"
                    "Ensure the analysis is objective and data-driven."
                )

                base_prompt = self.config.get(
                    "summarize_analysis_user_prompt", DEFAULT_FAA_SUMMARY_PROMPT
                )
                summary_guidance_prompt_addon = self.current_run_inputs.get(
                    "summary_guidance_prompt_addon"
                )

                if (
                    summary_guidance_prompt_addon
                    and isinstance(summary_guidance_prompt_addon, str)
                    and summary_guidance_prompt_addon.strip()
                ):
                    # If addon is provided, use it as the main prompt. This matches notebook's intent.
                    final_user_prompt = summary_guidance_prompt_addon
                    logging.info(
                        "Using summary guidance from 'summary_guidance_prompt_addon' input for SK."
                    )
                else:
                    final_user_prompt = base_prompt
                    logging.info("Using default/config summary prompt for SK.")

                input_vars = {  # SK arguments are typically flat key-value pairs
                    "company_id": company_id,
                    "financial_health": financial_health,
                    "ratios_summary": ratios_summary_str,
                    "dcf_valuation_summary": dcf_summary,
                    "comps_valuation_summary": comps_summary,
                    "enterprise_value_summary": enterprise_value_summary_str,
                    "press_release_summary_q4_2024": press_release_summaries.get(
                        "summary_press_release_q4_2024",
                        "Not available or error in summarization.",
                    ),
                    "press_release_summary_q1_2025": press_release_summaries.get(
                        "summary_press_release_q1_2025",
                        "Not available or error in summarization.",
                    ),
                    "user_provided_key_insights_or_conclusion_prompt": final_user_prompt,
                }

                skill_name = "SummarizeAnalysis"  # This should be a skill specific to FAA for its overall summary
                logging.info(
                    f"Attempting to generate summary for {company_id} using Semantic Kernel skill '{self.skills_plugin_name}.{skill_name}'."
                )
                logging.debug(f"FAA_XAI:GEN_SUMMARY_SK_INPUT: {input_vars}")

                # Use the invoke_skill method from the base Agent class or directly use kernel.invoke
                # Assuming invoke_skill handles finding the function and invoking
                # result = await self.invoke_skill(skill_name, input_vars)
                # If invoke_skill is not available, or for more direct control:
                if (
                    not kernel.plugins
                    or self.skills_plugin_name not in kernel.plugins
                    or skill_name not in kernel.plugins[self.skills_plugin_name]
                ):
                    logging.error(
                        f"Skill '{self.skills_plugin_name}.{skill_name}' not found in kernel plugins."
                    )
                    raise ValueError(
                        f"Skill '{self.skills_plugin_name}.{skill_name}' not found."
                    )

                sk_function = kernel.plugins[self.skills_plugin_name][skill_name]
                result = await kernel.invoke(
                    sk_function, **input_vars
                )  # Pass input_vars as keyword arguments
                summary = str(result)

                logging.debug(f"FAA_XAI:GEN_SUMMARY_SK_OUTPUT: '{summary}'")
                logging.info(
                    f"Successfully generated summary for {company_id} using SK."
                )
                return summary
            except AttributeError as e:
                logging.warning(
                    f"Semantic Kernel or skill method not available, or attribute error: {e}. Falling back to string formatting for summary."
                )
            except ValueError as e:
                logging.warning(
                    f"Semantic Kernel skill '{self.skills_plugin_name}.{skill_name}' execution failed: {e}. Falling back to string formatting."
                )
            except Exception as e:
                logging.error(
                    f"An unexpected error occurred while using Semantic Kernel for summary: {e}. Falling back to string formatting."
                )

        logging.warning(
            f"Generating summary for {company_id} using fallback string formatting."
        )
        summary = f"Fundamental Analysis for {company_id}:\n\n"
        if financial_ratios:
            summary += "Key Financial Ratios:\n"
            for ratio, value in financial_ratios.items():
                summary += (
                    f"  - {ratio}: {value:.2f}\n"
                    if value is not None
                    else f"  - {ratio}: N/A\n"
                )
        else:
            summary += "  Financial ratios could not be calculated.\n"
        summary += f"Financial Health: {financial_health}\n"
        if dcf_valuation is not None:
            summary += f"DCF Valuation: {dcf_valuation:.2f}\n"
        else:
            summary += "DCF Valuation: Not available\n"
        if comps_valuation is not None:  # Though it's always None currently
            summary += f"Comps Valuation: {comps_valuation:.2f}\n"
        else:
            summary += "Comps Valuation: Not available\n"
        if enterprise_value is not None:
            summary += f"Enterprise Value: {enterprise_value:.2f}\n"
        else:
            summary += "Enterprise Value: Not available\n"

        # Add press release summaries to fallback
        summary += "Press Release Summaries (if available):\n"
        summary += f"  - Q4 2024: {press_release_summaries.get('summary_press_release_q4_2024', 'Not available')}\n"
        summary += f"  - Q1 2025: {press_release_summaries.get('summary_press_release_q1_2025', 'Not available')}\n"

        default_likelihood = self.estimate_default_likelihood(financial_ratios)
        if default_likelihood is not None:
            summary += f"Estimated Default Likelihood: {default_likelihood:.2%}\n"
        else:
            summary += f"Estimated Default Likelihood: N/A\n"

        # Assuming financial_ratios is the correct input, not financial_statements
        distressed_metrics = self.calculate_distressed_metrics(
            financial_ratios if financial_ratios else {}
        )
        if distressed_metrics:
            summary += "Distressed Metrics:\n"
            for metric, value in distressed_metrics.items():
                summary += f"  - {metric}: {value:.2f}\n"

        recovery_rate = self.estimate_recovery_rate(
            financial_ratios if financial_ratios else {}, default_likelihood
        )
        if recovery_rate is not None:
            summary += f"Estimated Recovery Rate (in default): {recovery_rate:.2%}\n"

        summary += "\n(Summary generated using fallback string formatting. Incorporates SK-generated press release summaries if available.)"
        logging.debug(f"FAA_XAI:GEN_SUMMARY_FALLBACK_OUTPUT: '{summary}'")
        return summary

    def export_to_csv(self, data: Dict[str, List[Union[str, float]]], filename: str):
        # ... (existing code) ...
        pass

    def calculate_growth_rate(
        self, financial_statements: Dict[str, Any], metric: str
    ) -> Optional[float]:
        # ... (existing code) ...
        pass

    def calculate_ebitda_margin(
        self, financial_statements: Dict[str, Any]
    ) -> Optional[float]:
        # ... (existing code) ...
        pass

    def calculate_dcf_valuation(self, company_data: Dict[str, Any]) -> Optional[float]:
        """
        Calculates the Discounted Cash Flow (DCF) valuation for a company.

        This method uses a two-stage Free Cash Flow (FCF) projection model.
        Override values for 'discount_rate' and 'terminal_growth_rate_perpetuity'
        can be provided via 'self.current_run_inputs'. If not provided or invalid,
        values from the 'dcf_assumptions' in 'company_data' are used.

        Args:
            company_data: A dictionary containing company data, including
                          'financial_data_detailed' which should have
                          'cash_flow_statement' and 'dcf_assumptions'.

        Returns:
            The calculated DCF valuation as a float, or None if critical data
            is missing or assumptions are invalid (e.g., discount rate is not
            greater than the terminal growth rate).
        """
        company_name_for_log = company_data.get("company_info", {}).get(
            "name", "Unknown"
        )
        logging.debug(
            f"FAA_XAI:DCF_INPUT: company_id='{company_name_for_log}', company_data keys: {list(company_data.keys())}"
        )
        try:
            financial_details = company_data.get("financial_data_detailed", {})
            cash_flow_statement = financial_details.get("cash_flow_statement", {})
            historical_fcf = cash_flow_statement.get("free_cash_flow", [])

            if not historical_fcf:
                logging.warning(
                    f"FAA_XAI:DCF_ABORT: No historical free cash flow data for {company_name_for_log}."
                )
                return None

            last_historical_fcf = historical_fcf[-1]
            if not isinstance(
                last_historical_fcf, (int, float)
            ):  # Ensure last FCF is usable
                logging.warning(
                    f"FAA_XAI:DCF_ABORT: Last historical FCF for {company_name_for_log} ('{last_historical_fcf}') is not numeric."
                )
                return None

            dcf_assumptions = financial_details.get("dcf_assumptions", {})

            # Get override values from current_run_inputs
            override_discount_rate = self.current_run_inputs.get(
                "dcf_override_discount_rate"
            )
            override_terminal_growth_rate = self.current_run_inputs.get(
                "dcf_override_terminal_growth_rate"
            )

            # Core rates from existing assumptions or overrides
            discount_rate = dcf_assumptions.get("discount_rate")
            if (
                override_discount_rate is not None
                and isinstance(override_discount_rate, float)
                and override_discount_rate > 0
            ):
                discount_rate = override_discount_rate
                logging.info(
                    f"FAA_XAI:DCF_OVERRIDE: Using override discount rate: {discount_rate}"
                )

            terminal_growth_rate_perpetuity = dcf_assumptions.get(
                "terminal_growth_rate"
            )
            if (
                override_terminal_growth_rate is not None
                and isinstance(override_terminal_growth_rate, float)
                and override_terminal_growth_rate >= 0
            ):  # Allow 0 for terminal growth
                terminal_growth_rate_perpetuity = override_terminal_growth_rate
                logging.info(
                    f"FAA_XAI:DCF_OVERRIDE: Using override terminal growth rate: {terminal_growth_rate_perpetuity}"
                )

            # New parameters for two-stage growth model
            fcf_projection_years_total = int(
                dcf_assumptions.get("fcf_projection_years_total", 10)
            )  # Default 10 years
            initial_high_growth_period_years = int(
                dcf_assumptions.get("initial_high_growth_period_years", 5)
            )  # Default 5 years
            initial_high_growth_rate = dcf_assumptions.get(
                "initial_high_growth_rate", 0.10
            )  # Default 10%
            stable_growth_rate = dcf_assumptions.get(
                "stable_growth_rate", 0.05
            )  # Default 5% for second stage

            # Ensure initial_high_growth_period_years is not more than fcf_projection_years_total
            initial_high_growth_period_years = min(
                initial_high_growth_period_years, fcf_projection_years_total
            )

            logging.debug(
                f"FAA_XAI:DCF_PARAMS_TWO_STAGE: LastHistFCF={last_historical_fcf}, DiscountRate={discount_rate}, "
                f"TerminalGrowthRatePerpetuity={terminal_growth_rate_perpetuity}, TotalProjectionYears={fcf_projection_years_total}, "
                f"HighGrowthYears={initial_high_growth_period_years}, HighGrowthRate={initial_high_growth_rate}, StableGrowthRate={stable_growth_rate}"
            )

            # Validate core rates and growth rates
            essential_rates = [
                discount_rate,
                terminal_growth_rate_perpetuity,
                initial_high_growth_rate,
                stable_growth_rate,
            ]
            if not all(
                isinstance(rate, (int, float))
                for rate in essential_rates
                if rate is not None
            ):  # Allow None for rates not used if logic handles it
                logging.warning(
                    f"FAA_XAI:DCF_ABORT: One or more DCF rates are non-numeric for {company_name_for_log}. Rates: DR={discount_rate}, TGR_P={terminal_growth_rate_perpetuity}, IHGR={initial_high_growth_rate}, SGR={stable_growth_rate}"
                )
                return None
            if (
                discount_rate is None or terminal_growth_rate_perpetuity is None
            ):  # These are always needed
                logging.warning(
                    f"FAA_XAI:DCF_ABORT: Discount rate or terminal perpetuity growth rate is missing for {company_name_for_log}."
                )
                return None
            if (
                discount_rate <= terminal_growth_rate_perpetuity
            ):  # Check against perpetuity growth rate
                logging.warning(
                    f"FAA_XAI:DCF_ABORT: Discount rate ({discount_rate}) not > terminal perpetuity growth rate ({terminal_growth_rate_perpetuity}) for {company_name_for_log}."
                )
                return None

            projected_cash_flows = []
            current_fcf = last_historical_fcf

            for year_num in range(1, fcf_projection_years_total + 1):
                growth_rate_for_year = 0.0
                if year_num <= initial_high_growth_period_years:
                    if (
                        initial_high_growth_rate is None
                    ):  # Should be caught by all() check above if strictly required for all years
                        logging.warning(
                            f"FAA_XAI:DCF_WARN: Missing initial_high_growth_rate for year {year_num}, using 0 growth for this year."
                        )
                    else:
                        growth_rate_for_year = initial_high_growth_rate
                else:  # Stable growth period (years > initial_high_growth_period_years up to fcf_projection_years_total)
                    if (
                        stable_growth_rate is None
                    ):  # Should be caught by all() check if strictly required
                        logging.warning(
                            f"FAA_XAI:DCF_WARN: Missing stable_growth_rate for year {year_num}, using 0 growth for this year."
                        )
                    else:
                        growth_rate_for_year = stable_growth_rate

                current_fcf *= 1 + growth_rate_for_year
                projected_cash_flows.append(current_fcf)

            logging.debug(
                f"FAA_XAI:DCF_PROJECTED_FCF_TWO_STAGE ({fcf_projection_years_total} years): {projected_cash_flows}"
            )

            if not projected_cash_flows:
                logging.warning(
                    f"FAA_XAI:DCF_ABORT: No projected cash flows generated for {company_name_for_log}."
                )
                return None

            terminal_value_fcf_base = projected_cash_flows[-1]
            terminal_value = (
                terminal_value_fcf_base * (1 + terminal_growth_rate_perpetuity)
            ) / (discount_rate - terminal_growth_rate_perpetuity)
            logging.debug(
                f"FAA_XAI:DCF_TERMINAL_VALUE: TV_FCF_Base={terminal_value_fcf_base}, TV={terminal_value}"
            )

            present_values = []
            for i, fcf in enumerate(projected_cash_flows):
                pv = fcf / ((1 + discount_rate) ** (i + 1))
                present_values.append(pv)

            terminal_pv = terminal_value / (
                (1 + discount_rate) ** fcf_projection_years_total
            )
            logging.debug(f"FAA_XAI:DCF_PV_TERMINAL_VALUE: PV_TV={terminal_pv}")

            dcf_valuation = sum(present_values) + terminal_pv
            logging.debug(f"FAA_XAI:DCF_OUTPUT: DCF_Valuation={dcf_valuation}")
            return dcf_valuation

        except Exception as e:
            logging.exception(
                f"Error calculating DCF valuation for {company_name_for_log}: {e}"
            )
            logging.debug(f"FAA_XAI:DCF_ERROR: Exception {e}")
            return None

    def calculate_enterprise_value(
        self, company_data: Dict[str, Any]
    ) -> Optional[float]:
        company_name_for_log = company_data.get("company_info", {}).get(
            "name", "Unknown"
        )
        logging.debug(
            f"FAA_XAI:EV_INPUT: company_id='{company_name_for_log}', company_data keys: {list(company_data.keys())}"
        )
        try:
            financial_details = company_data.get("financial_data_detailed", {})
            if not financial_details:
                logging.warning(
                    f"FAA_XAI:EV_ABORT: 'financial_data_detailed' missing for {company_name_for_log}."
                )
                return None

            market_data_info = financial_details.get("market_data", {})
            balance_sheet_info = financial_details.get("balance_sheet", {})

            share_price = market_data_info.get("share_price")
            shares_outstanding = market_data_info.get("shares_outstanding")
            logging.debug(
                f"FAA_XAI:EV_MARKET_DATA: SharePrice={share_price}, SharesOutstanding={shares_outstanding}"
            )

            market_cap = None
            if isinstance(share_price, (int, float)) and isinstance(
                shares_outstanding, (int, float)
            ):
                market_cap = share_price * shares_outstanding
            else:
                logging.warning(
                    f"FAA_XAI:EV_WARN: Market Cap could not be calculated for {company_name_for_log} due to missing/invalid share_price or shares_outstanding."
                )

            short_term_debt_values = balance_sheet_info.get("short_term_debt", [0])
            short_term_debt = (
                short_term_debt_values[-1] if short_term_debt_values else 0
            )
            long_term_debt_values = balance_sheet_info.get("long_term_debt", [0])
            long_term_debt = long_term_debt_values[-1] if long_term_debt_values else 0
            total_debt = short_term_debt + long_term_debt

            cash_and_equivalents_values = balance_sheet_info.get(
                "cash_and_equivalents", [0]
            )
            cash_and_equivalents = (
                cash_and_equivalents_values[-1] if cash_and_equivalents_values else 0
            )
            logging.debug(
                f"FAA_XAI:EV_COMPONENTS: MarketCap={market_cap}, TotalDebt={total_debt}, Cash={cash_and_equivalents}"
            )

            if market_cap is not None:
                enterprise_value = market_cap + total_debt - cash_and_equivalents
                logging.debug(
                    f"FAA_XAI:EV_OUTPUT: EV={enterprise_value} for {company_name_for_log}"
                )
                return enterprise_value
            else:
                logging.warning(
                    f"FAA_XAI:EV_ABORT: Enterprise Value cannot be calculated as Market Cap is unavailable for {company_name_for_log}."
                )
                return None

        except Exception as e:
            logging.exception(
                f"Error calculating enterprise value for {company_name_for_log}: {e}"
            )
            logging.debug(f"FAA_XAI:EV_ERROR: Exception {e}")
            return None

    def estimate_default_likelihood(
        self, financial_ratios: Dict[str, float]
    ) -> Optional[float]:
        # ... (existing code) ...
        pass

    def calculate_distressed_metrics(
        self, financial_statements: Dict[str, Any]
    ) -> Dict[str, float]:  # Should be financial_ratios based on usage
        # ... (existing code, note the type hint vs usage in generate_analysis_summary) ...
        pass

    def estimate_recovery_rate(
        self, financial_statements, default_likelihood
    ):  # Should be financial_ratios
        # ... (existing code, note the type hint vs usage in generate_analysis_summary) ...
        pass

    # Obsolete send_message - peer communication is via agent.run()
    # def send_message(self, message: Dict[str, Any]):
    #     # ... (existing code) ...
    #     pass


# Example Usage (for testing):
# The if __name__ == '__main__': block should be removed as agents are run by the orchestrator.
# Test code would typically reside in a separate test file/suite.
