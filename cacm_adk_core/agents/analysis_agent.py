import logging
from typing import Dict, Any

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext
from semantic_kernel.functions.kernel_arguments import KernelArguments # Corrected import path
# from semantic_kernel.functions.function_result import FunctionResult # For type hint if needed

# logger = logging.getLogger(__name__) # Will use instance logger

class AnalysisAgent(Agent):
    """
    Agent responsible for performing analysis tasks, potentially using financial skills.
    """
    def __init__(self, kernel_service: KernelService):
        """
        Initializes the AnalysisAgent.

        Args:
            kernel_service (KernelService): The service providing access to the Semantic Kernel.
        """
        # This agent is associated with the "FinancialAnalysis" plugin by default
        super().__init__(agent_name="AnalysisAgent", kernel_service=kernel_service, skills_plugin_name="FinancialAnalysis")

    async def run(self, task_description: str, current_step_inputs: Dict[str, Any], shared_context: SharedContext) -> Dict[str, Any]:
        """
        Executes the analysis task.

        Args:
            task_description (str): Description of the analysis task.
            current_step_inputs (Dict[str, Any]): Inputs for this step (e.g., financial data to analyze).
            shared_context (SharedContext): The shared context object.

        Returns:
            Dict[str, Any]: Results of the execution, including status.
        """
        self.logger.info(f"'{self.agent_name}' received task: {task_description} with inputs: {current_step_inputs}")
        self.logger.info(f"Operating with SharedContext ID: {shared_context.get_session_id()} (CACM ID: {shared_context.get_cacm_id()})")

        # Example: Read data potentially set by DataIngestionAgent
        last_ingested_doc_id = shared_context.get_data("last_ingested_document_id")
        if last_ingested_doc_id:
            self.logger.info(f"Found last ingested document ID in shared context: '{last_ingested_doc_id}'")
            doc_content_snippet = shared_context.get_data(f"{last_ingested_doc_id}_content_snippet")
            if doc_content_snippet:
                 self.logger.info(f"Content snippet for '{last_ingested_doc_id}': '{doc_content_snippet[:50]}...'")


        kernel = self.get_kernel()
        analysis_output_payload = {"message": "Analysis agent started."}
        skill_result_payload = None

        kernel = self.get_kernel()
        if not kernel:
            self.logger.error("Kernel not available, cannot execute skills.")
            analysis_output_payload["message"] = "Kernel not available."
            skill_result_payload = None # Ensure this is None
            # Skip to reporting logic
        elif self.skills_plugin_name:
            self.logger.info(f"Attempting to use skill plugin: '{self.skills_plugin_name}'")
            financial_analysis_plugin = self.get_plugin(self.skills_plugin_name)
            if not financial_analysis_plugin:
                self.logger.error(f"Plugin '{self.skills_plugin_name}' not found.")
                analysis_output_payload["message"] = f"Plugin '{self.skills_plugin_name}' not found."
                skill_result_payload = None # Ensure this is None
            else: # Plugin found
                self.logger.info(f"Plugin '{self.skills_plugin_name}' retrieved.")
                calculate_ratios_function = financial_analysis_plugin.get("calculate_basic_ratios")

                if not calculate_ratios_function:
                    self.logger.error("'calculate_basic_ratios' function not found in plugin.")
                    analysis_output_payload["message"] = "'calculate_basic_ratios' function not found."
                    skill_result_payload = None # Ensure this is None
                else: # Function found, proceed with skill invocation
                    self.logger.info("Function 'calculate_basic_ratios' found. Preparing arguments.")

                    # Prepare KernelArguments
                    # The skill expects 'financial_data' and 'rounding_precision'
                    # These should be mapped from current_step_inputs by the orchestrator
                    # based on the capability definition in the catalog.
                    # The keys here ("financial_data", "rounding_precision") must match the keys
                    # used in the step's inputBindings in the CACM template.
                    financial_data_input = current_step_inputs.get("financial_data")
                    rounding_precision_input = current_step_inputs.get("rounding_precision", 2)

                    if financial_data_input is None:
                        self.logger.error("Missing 'financial_data' in current_step_inputs for skill.")
                        analysis_output_payload["message"] = "Missing 'financial_data' for skill."
                    else:
                        kernel_args = KernelArguments(
                            financial_data=financial_data_input,
                            rounding_precision=rounding_precision_input
                        )
                        self.logger.info(f"Invoking 'calculate_basic_ratios' with financial_data: {financial_data_input}, precision: {rounding_precision_input}")

                        try:
                            result_from_skill = await kernel.invoke(calculate_ratios_function, kernel_args)
                            self.logger.info(f"Raw result from 'calculate_basic_ratios' skill: {type(result_from_skill)} - {str(result_from_skill)}")

                            # Assuming result_from_skill is FunctionResult, its .value is the actual output
                            skill_result_payload = result_from_skill.value
                            self.logger.info(f"Extracted skill result payload: {skill_result_payload}")
                            analysis_output_payload["message"] = "Financial ratios calculated successfully by skill."
                            analysis_output_payload["skill_outputs"] = skill_result_payload # Store the direct skill output
                        except Exception as e:
                            self.logger.error(f"Error invoking 'calculate_basic_ratios' skill: {e}", exc_info=True)
                            analysis_output_payload["message"] = f"Error invoking skill: {e}"
                            analysis_output_payload["skill_error"] = str(e)
        else:
            self.logger.warning("No skills_plugin_name configured for this agent. Skipping skill execution.")
            analysis_output_payload["message"] = "No skill plugin configured for AnalysisAgent."

        # Conceptual: How an LLM-based skill might be used
        # text_for_analysis = shared_context.get_data("main_document_processed_text")
        # if text_for_analysis and kernel:
        #     try:
        #         # sk_mdna_summarizer_skill = kernel.plugins.get("SK_MDNA_SummarizerSkill") # If registered as such
        #         # summarize_function = sk_mdna_summarizer_skill.get("summarize_section")
        #         # summary_args = KernelArguments(input=text_for_analysis, max_sentences="5")
        #         # summary = await kernel.invoke(summarize_function, summary_args)
        #         # self.logger.info(f"LLM Summary (conceptual): {summary.value}")
        #         # analysis_output_payload["llm_summary"] = summary.value
        #         pass # Placeholder for actual LLM skill call
        #     except Exception as e:
        #         self.logger.error(f"Error invoking conceptual LLM skill: {e}")


        # Attempt to get ReportGenerationAgent and send results
        self.logger.info(f"'{self.agent_name}' attempting to get ReportGenerationAgent after skill execution.")
        # Pass some context if needed for report agent creation, or an empty dict
        report_agent_creation_context = {"triggering_agent": self.agent_name, "cacm_id": shared_context.get_cacm_id()}
        report_agent = await self.get_or_create_agent("ReportGenerationAgent", context_data=report_agent_creation_context)

        if report_agent:
            self.logger.info(f"'{self.agent_name}' successfully got instance of ReportGenerationAgent.")

            # Data to send to the report agent
            data_for_report = {
                "summary": f"Analysis by {self.agent_name} for task: '{task_description}'. CACM ID: {shared_context.get_cacm_id()}",
                "original_inputs": current_step_inputs,
                "analysis_payload": analysis_output_payload, # This now includes skill_outputs or errors
                "skill_direct_payload": skill_result_payload # Pass the direct skill output if available
            }

            try:
                # Call a method on the report_agent instance
                await report_agent.receive_analysis_results(sending_agent_name=self.agent_name, results=data_for_report)
                self.logger.info(f"'{self.agent_name}' successfully sent results to ReportGenerationAgent.")
                # Determine overall status based on skill execution success
                if skill_result_payload: # Skill produced some result
                    overall_status = "success" if not skill_result_payload.get("errors") else "error"
                elif "error" in analysis_output_payload.get("message", "").lower() or \
                     "not found" in analysis_output_payload.get("message", "").lower() or \
                     "Missing" in analysis_output_payload.get("message", "").lower() or \
                     "kernel not available" in analysis_output_payload.get("message", "").lower(): # Added this check
                    overall_status = "error"
                else: # No skill result, but no explicit error message yet, implies other issue or placeholder path
                    overall_status = "warning"

                final_agent_return_payload = {
                    "status": overall_status, # Reflect skill execution status
                    "agent": self.agent_name,
                    "message": analysis_output_payload.get("message", f"{self.agent_name} completed processing; sent results to ReportGenerationAgent."),
                    "ratios_from_skill": skill_result_payload if skill_result_payload else analysis_output_payload.get("skill_outputs"),
                    "full_analysis_log": analysis_output_payload
                }
                return final_agent_return_payload
            except Exception as e:
                self.logger.error(f"Error during interaction with ReportGenerationAgent: {e}", exc_info=True)
                return {"status": "error",
                        "agent": self.agent_name,
                        "message": f"{self.agent_name} failed during/after sending results to ReportGenerationAgent: {e}",
                        "ratios_from_skill": skill_result_payload, # Still include if skill ran
                        "full_analysis_log": analysis_output_payload}
        else: # Failed to get ReportGenerationAgent
            self.logger.error(f"'{self.agent_name}' could not get ReportGenerationAgent. Results not sent.")
            # Determine overall status based on skill execution success before this failure
            if skill_result_payload:
                overall_status_before_reporting_fail = "success" if not skill_result_payload.get("errors") else "error"
            elif "error" in analysis_output_payload.get("message", "").lower() or \
                 "not found" in analysis_output_payload.get("message", "").lower() or \
                 "Missing" in analysis_output_payload.get("message", "").lower() or \
                 "kernel not available" in analysis_output_payload.get("message", "").lower(): # Added this check
                overall_status_before_reporting_fail = "error"
            else:
                overall_status_before_reporting_fail = "warning"

            return {"status": "error", # Explicitly error as it couldn't report
                    "agent": self.agent_name,
                    "message": f"{self.agent_name} completed analysis part (status: {overall_status_before_reporting_fail}) but failed to get ReportGenerationAgent.",
                    "ratios_from_skill": skill_result_payload,
                    "full_analysis_log": analysis_output_payload}

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    from semantic_kernel import Kernel
    # Mock KernelService for testing
    # For the __main__ test, we need a more complete Orchestrator mock if we are to test get_or_create_agent realistically
    # or use the actual Orchestrator if possible. The current base_agent test uses a simpler mock.
    # For now, let's assume the existing mock is enough to instantiate the agent.
    class MockKernelService(KernelService):
        def __init__(self):
            self._kernel = Kernel()
            try:
                from cacm_adk_core.native_skills import FinancialAnalysisSkill
                self._kernel.add_plugin(FinancialAnalysisSkill(), plugin_name="FinancialAnalysis")
                logging.info("MockKernelService: FinancialAnalysisSkill registered.") # Use global logging for __main__
            except Exception as e:
                 logging.error(f"MockKernelService: Failed to register FinancialAnalysisSkill for test: {e}")
        def get_kernel(self): return self._kernel
        def _initialize_kernel(self): pass

    class MockOrchestrator: # A more specific mock for what AnalysisAgent needs from agent_manager
        def __init__(self, kernel_service):
            self.kernel_service = kernel_service
            self.logger = logging.getLogger("MockOrchestrator")
            self.agent_instances = {} # Simulate instance store
            self.agents = {"ReportGenerationAgent": ReportGenerationAgent} # Simulate registered classes

        async def get_or_create_agent_instance(self, agent_name_key: str, context_data_for_creation: dict):
            self.logger.info(f"MockOrchestrator attempting to get/create '{agent_name_key}'.")
            if agent_name_key in self.agent_instances:
                return self.agent_instances[agent_name_key]
            if agent_name_key == "ReportGenerationAgent":
                from cacm_adk_core.agents.report_generation_agent import ReportGenerationAgent # Ensure import
                instance = ReportGenerationAgent(self.kernel_service)
                instance.set_agent_manager(self) # type: ignore # It expects Orchestrator, fine for mock
                self.agent_instances[agent_name_key] = instance
                return instance
            return None

    mock_kernel_service = MockKernelService()
    analysis_agent = AnalysisAgent(kernel_service=mock_kernel_service)

    # AnalysisAgent needs an agent_manager that has get_or_create_agent_instance
    mock_orchestrator = MockOrchestrator(mock_kernel_service)
    analysis_agent.set_agent_manager(mock_orchestrator) # type: ignore # It expects Orchestrator, fine for mock

    mock_shared_context = SharedContext(cacm_id="test_analysis_cacm")
    # Simulate DataIngestionAgent's output in shared_context
    mock_shared_context.set_data("last_ingested_document_id", "XYZ_10K_2023")
    mock_shared_context.set_data("XYZ_10K_2023_content_snippet", "Revenue increased by 10%...")


    import asyncio
    async def test_run():
        result = await analysis_agent.run(
            task_description="Perform analysis and calculate basic ratios.",
            current_step_inputs={ # These are inputs for AnalysisAgent itself
                "financial_data": {"current_assets": 100, "current_liabilities": 50, "total_debt": 200, "total_equity": 100},
                "some_other_data": "test"
            },
            shared_context=mock_shared_context
        )
        logging.info(f"AnalysisAgent run result: {result}")
        # Check if ReportGenerationAgent (mocked) stored something
        if "ReportGenerationAgent" in mock_orchestrator.agent_instances:
            report_agent_instance = mock_orchestrator.agent_instances["ReportGenerationAgent"]
            if hasattr(report_agent_instance, 'stored_results'):
                 logging.info(f"ReportGenerationAgent stored results: {report_agent_instance.stored_results}")


    asyncio.run(test_run())
