import logging
import json 
from typing import Dict, Any

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext
from semantic_kernel.functions.kernel_arguments import KernelArguments
# from semantic_kernel.functions.function_result import FunctionResult


class AnalysisAgent(Agent):
    """
    Agent responsible for performing analysis tasks, 
    including native skill calculations and orchestrating LLM summaries.
    """
    def __init__(self, kernel_service: KernelService):
        super().__init__(agent_name="AnalysisAgent", kernel_service=kernel_service, skills_plugin_name="FinancialAnalysis")

    async def run(self, task_description: str, current_step_inputs: Dict[str, Any], shared_context: SharedContext) -> Dict[str, Any]:
        self.logger.info(f"'{self.agent_name}' received task: {task_description} with inputs: {current_step_inputs}")
        self.logger.info(f"Operating with SharedContext ID: {shared_context.get_session_id()} (CACM ID: {shared_context.get_cacm_id()})")

        agent_ops_summary = {
            "kernel_access": "Not checked",
            "ratio_calculation": "Not attempted",
            "financial_summary_generation": "Not attempted",
            "risk_summary_generation": "Not attempted",
            "overall_assessment_generation": "Not attempted",
            "reporting_to_other_agent": "Not attempted",
            "final_message_before_reporting": "Analysis processing not fully completed."
        }
        # Initialize placeholders for text summaries
        financial_summary_text = "[Financial Performance Summary Not Available - Generation Skipped or Failed]"
        key_risks_summary_text = "[Key Risks Summary Not Available - Generation Skipped or Failed]"
        overall_assessment_text = "[Overall Assessment Not Available - Generation Skipped or Failed]"
        ratios_skill_payload = None # Payload from the financial ratio native skill
        
        final_status = "success" # Assume success, change on critical error

        # a. Retrieve Inputs from SharedContext
        self.logger.info("Retrieving necessary data from SharedContext...")
        financial_data_for_ratios = shared_context.get_data("financial_data_for_ratios")
        structured_financials_for_summary = shared_context.get_data("structured_financials_for_summary")
        risk_factors_section_text = shared_context.get_data("risk_factors_section_text")

        for key, var in [("financial_data_for_ratios", financial_data_for_ratios), 
                         ("structured_financials_for_summary", structured_financials_for_summary),
                         ("risk_factors_section_text", risk_factors_section_text)]:
            if var is not None:
                self.logger.info(f"Retrieved '{key}' from SharedContext.")
            else:
                self.logger.warning(f"'{key}' not found in SharedContext. Dependent steps may be affected.")
        
        kernel = self.get_kernel()
        if not kernel:
            self.logger.error("Kernel not available, cannot execute skills.")
            agent_ops_summary["kernel_access"] = "Failed: Kernel not available."
            final_status = "error"
        else:
            agent_ops_summary["kernel_access"] = "Success."
            # b. Calculate Financial Ratios (Native Skill)
            if financial_data_for_ratios and self.skills_plugin_name:
                self.logger.info(f"Attempting financial ratio calculation using plugin: '{self.skills_plugin_name}'.")
                financial_analysis_plugin = self.get_plugin(self.skills_plugin_name)
                if financial_analysis_plugin:
                    calculate_ratios_function = financial_analysis_plugin.get("calculate_basic_ratios")
                    if calculate_ratios_function:
                        rounding_precision = current_step_inputs.get("rounding_precision", 2)
                        kernel_args_ratios = KernelArguments(financial_data=financial_data_for_ratios, rounding_precision=rounding_precision)
                        self.logger.info(f"Invoking 'calculate_basic_ratios' with precision: {rounding_precision}")
                        try:
                            result = await kernel.invoke(calculate_ratios_function, kernel_args_ratios)
                            ratios_skill_payload = result.value # This is the dict {"calculated_ratios": ..., "errors": ...}
                            shared_context.set_data("calculated_key_ratios", ratios_skill_payload.get("calculated_ratios", {}))
                            self.logger.info(f"Ratios calculated and stored: {ratios_skill_payload.get('calculated_ratios', {})}")
                            agent_ops_summary["ratio_calculation"] = f"Success: {ratios_skill_payload.get('calculated_ratios', {})}"
                            if ratios_skill_payload.get("errors"):
                                agent_ops_summary["ratio_calculation"] += f" with errors: {ratios_skill_payload['errors']}"
                                final_status = "partial_success" # Or "warning" if errors are not critical
                        except Exception as e:
                            self.logger.error(f"Error invoking 'calculate_basic_ratios' skill: {e}", exc_info=True)
                            agent_ops_summary["ratio_calculation"] = f"Error: {e}"
                            final_status = "error"
                    else:
                        agent_ops_summary["ratio_calculation"] = "Error: 'calculate_basic_ratios' function not found."
                        self.logger.error(agent_ops_summary["ratio_calculation"])
                        if final_status != "error": final_status = "partial_success"
                else:
                    agent_ops_summary["ratio_calculation"] = f"Error: Plugin '{self.skills_plugin_name}' not found."
                    self.logger.error(agent_ops_summary["ratio_calculation"])
                    if final_status != "error": final_status = "partial_success"
            elif not financial_data_for_ratios:
                agent_ops_summary["ratio_calculation"] = "Skipped: Missing 'financial_data_for_ratios' in SharedContext."
                self.logger.warning(agent_ops_summary["ratio_calculation"])
            else:
                 agent_ops_summary["ratio_calculation"] = "Skipped: No financial analysis skill plugin configured for agent."
                 self.logger.warning(agent_ops_summary["ratio_calculation"])

            # Placeholder LLM Skill Calls
            summarizer_plugin = kernel.plugins.get("SummarizationSkills")
            if summarizer_plugin and summarizer_plugin.get("summarize_section"):
                summarize_func = summarizer_plugin.get("summarize_section")
                
                # c. Financial Performance Summary
                fin_text_for_summary = f"Summarize financial performance. Key data: {json.dumps(structured_financials_for_summary if structured_financials_for_summary else {'info': 'not available'})}"
                kernel_args_fin = KernelArguments(input=fin_text_for_summary, max_sentences="3")
                try:
                    fin_summary_res = await kernel.invoke(summarize_func, kernel_args_fin)
                    financial_summary_text = fin_summary_res.value # This is the placeholder string
                    shared_context.set_data("financial_performance_summary_text", financial_summary_text)
                    self.logger.info(f"Stored financial_performance_summary_text: '{financial_summary_text[:100]}...'")
                    agent_ops_summary["financial_summary_generation"] = "Success (placeholder)."
                except Exception as e:
                    self.logger.error(f"Error invoking financial summary skill: {e}", exc_info=True)
                    agent_ops_summary["financial_summary_generation"] = f"Error: {e}"
                    if final_status != "error": final_status = "partial_success"

                # d. Key Risks Summary
                risk_text_to_summarize = risk_factors_section_text if risk_factors_section_text else "No specific risk factors text provided for summary."
                kernel_args_risk = KernelArguments(input=risk_text_to_summarize, max_sentences="3")
                try:
                    risk_summary_res = await kernel.invoke(summarize_func, kernel_args_risk)
                    key_risks_summary_text = risk_summary_res.value
                    shared_context.set_data("key_risks_summary_text", key_risks_summary_text)
                    self.logger.info(f"Stored key_risks_summary_text: '{key_risks_summary_text[:100]}...'")
                    agent_ops_summary["risk_summary_generation"] = "Success (placeholder)."
                except Exception as e:
                    self.logger.error(f"Error invoking risk summary skill: {e}", exc_info=True)
                    agent_ops_summary["risk_summary_generation"] = f"Error: {e}"
                    if final_status != "error": final_status = "partial_success"
                
                # e. Overall Assessment
                assessment_input_text = (
                    f"Overall Assessment based on: "
                    f"Financial Ratios: {shared_context.get_data('calculated_key_ratios', 'N/A')}. "
                    f"Financial Summary: {shared_context.get_data('financial_performance_summary_text', 'N/A')}. "
                    f"Risk Summary: {shared_context.get_data('key_risks_summary_text', 'N/A')}."
                )
                kernel_args_assess = KernelArguments(input=assessment_input_text, max_sentences="2")
                try:
                    overall_assess_res = await kernel.invoke(summarize_func, kernel_args_assess)
                    overall_assessment_text = overall_assess_res.value
                    shared_context.set_data("overall_assessment_text", overall_assessment_text)
                    self.logger.info(f"Stored overall_assessment_text: '{overall_assessment_text[:100]}...'")
                    agent_ops_summary["overall_assessment_generation"] = "Success (placeholder)."
                except Exception as e:
                    self.logger.error(f"Error invoking overall assessment skill: {e}", exc_info=True)
                    agent_ops_summary["overall_assessment_generation"] = f"Error: {e}"
                    if final_status != "error": final_status = "partial_success"
            else:
                self.logger.warning("SummarizationSkills or summarize_section function not found. Text summaries will be skipped.")
                agent_ops_summary["financial_summary_generation"] = "Skipped: Summarization skill not found."
                agent_ops_summary["risk_summary_generation"] = "Skipped: Summarization skill not found."
                agent_ops_summary["overall_assessment_generation"] = "Skipped: Summarization skill not found."
                if final_status == "success": final_status = "warning" # Downgrade status if summaries skipped

        # Set final message based on operations
        if final_status == "error":
            agent_ops_summary["final_message_before_reporting"] = "Analysis encountered critical errors."
        elif final_status == "partial_success" or final_status == "warning":
             agent_ops_summary["final_message_before_reporting"] = "Analysis completed with some issues or skipped steps."
        else: # success
            agent_ops_summary["final_message_before_reporting"] = "Analysis phase completed successfully. All results stored in SharedContext."

        # f. Communicate with ReportGenerationAgent
        self.logger.info(f"'{self.agent_name}' attempting to get ReportGenerationAgent after analysis.")
        report_agent_creation_context = {"triggering_agent": self.agent_name, "cacm_id": shared_context.get_cacm_id()}
        report_agent = await self.get_or_create_agent("ReportGenerationAgent", context_data=report_agent_creation_context) 
        
        if report_agent:
            self.logger.info(f"'{self.agent_name}' successfully got instance of ReportGenerationAgent.")
            data_for_report = {
                "analysis_status": final_status,
                "analysis_summary_message": agent_ops_summary["final_message_before_reporting"],
                "original_inputs": current_step_inputs, 
                "ratios_payload": ratios_skill_payload, 
                "financial_summary": financial_summary_text,
                "risk_summary": key_risks_summary_text,
                "overall_assessment": overall_assessment_text,
                "full_analysis_ops_log": agent_ops_summary
            }
            try:
                await report_agent.receive_analysis_results(sending_agent_name=self.agent_name, results=data_for_report)
                self.logger.info(f"'{self.agent_name}' successfully sent results to ReportGenerationAgent.")
                agent_ops_summary["reporting_to_other_agent"] = "Success."
            except Exception as e:
                self.logger.error(f"Error calling receive_analysis_results on ReportGenerationAgent: {e}", exc_info=True)
                agent_ops_summary["reporting_to_other_agent"] = f"Error: {e}"
                final_status = "error" # If reporting fails, the overall step might be considered an error.
        else:
            self.logger.error(f"'{self.agent_name}' could not get ReportGenerationAgent. Results not sent.")
            agent_ops_summary["reporting_to_other_agent"] = "Failed: Could not get ReportGenerationAgent."
            final_status = "error" 

        return {
            "status": final_status,
            "agent": self.agent_name,
            "message": agent_ops_summary.get("final_message_before_reporting", "Analysis agent processing finished."),
            "ratios_from_skill": ratios_skill_payload, # For direct output binding
            "text_summaries_generated": { 
                "financial_performance": financial_summary_text,
                "key_risks": key_risks_summary_text,
                "overall_assessment": overall_assessment_text
            },
            "detailed_operations_summary": agent_ops_summary
        }

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    from semantic_kernel import Kernel
    
    class MockKernelService(KernelService):
        def __init__(self):
            self._kernel = Kernel()
            try:
                from cacm_adk_core.native_skills import FinancialAnalysisSkill
                self._kernel.add_plugin(FinancialAnalysisSkill(), plugin_name="FinancialAnalysis")
                logging.info("MockKernelService: FinancialAnalysisSkill registered.")
                
                from processing_pipeline.semantic_kernel_skills import SK_MDNA_SummarizerSkill
                self._kernel.add_plugin(SK_MDNA_SummarizerSkill(), plugin_name="SummarizationSkills")
                logging.info("MockKernelService: SummarizationSkills registered.")

            except Exception as e:
                 logging.error(f"MockKernelService: Failed to register skills for test: {e}")
        def get_kernel(self): return self._kernel
        def _initialize_kernel(self): pass
    
    class MockOrchestrator: 
        def __init__(self, kernel_service):
            self.kernel_service = kernel_service
            self.logger = logging.getLogger("MockOrchestrator")
            self.agent_instances = {} 
            from cacm_adk_core.agents.report_generation_agent import ReportGenerationAgent 
            self.agents = {"ReportGenerationAgent": ReportGenerationAgent}

        async def get_or_create_agent_instance(self, agent_name_key: str, context_data_for_creation: dict):
            self.logger.info(f"MockOrchestrator attempting to get/create '{agent_name_key}'.")
            if agent_name_key in self.agent_instances:
                return self.agent_instances[agent_name_key]
            if agent_name_key == "ReportGenerationAgent":
                instance = self.agents[agent_name_key](self.kernel_service)
                instance.set_agent_manager(self) # type: ignore 
                self.agent_instances[agent_name_key] = instance
                return instance
            return None

    mock_kernel_service = MockKernelService()
    analysis_agent = AnalysisAgent(kernel_service=mock_kernel_service)
    
    mock_orchestrator = MockOrchestrator(mock_kernel_service)
    analysis_agent.set_agent_manager(mock_orchestrator) # type: ignore
    
    mock_shared_context = SharedContext(cacm_id="test_analysis_agent_full_run_cacm")
    mock_shared_context.set_data("financial_data_for_ratios", {"current_assets": 2000.0, "current_liabilities": 1000.0, "total_debt": 500.0, "total_equity": 1500.0})
    mock_shared_context.set_data("structured_financials_for_summary", {"revenue": 5000, "cogs": 2000, "net_income": 1000})
    mock_shared_context.set_data("risk_factors_section_text", "The company faces competition and market volatility. Supply chain disruptions are also a key concern.")

    import asyncio
    async def test_run():
        result = await analysis_agent.run(
            task_description="Perform full analysis: ratios and textual summaries.",
            current_step_inputs={"rounding_precision": 2, "some_other_input": "value"},
            shared_context=mock_shared_context
        )
        logging.info(f"AnalysisAgent run result: {json.dumps(result, indent=2)}")
        
        logging.info("\n--- Final SharedContext Summary ---")
        mock_shared_context.log_context_summary()

        if "ReportGenerationAgent" in mock_orchestrator.agent_instances:
            report_agent_instance = mock_orchestrator.agent_instances["ReportGenerationAgent"]
            if hasattr(report_agent_instance, 'stored_results'):
                 logging.info(f"ReportGenerationAgent stored results: {json.dumps(report_agent_instance.stored_results, indent=2)}")

    asyncio.run(test_run())
