import logging
import json 
from typing import Dict, Any, Optional

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService # For consistency, though not directly used by this agent's current logic
from cacm_adk_core.context.shared_context import SharedContext


class ReportGenerationAgent(Agent):
    """
    Agent responsible for assembling a comprehensive report by consolidating
    outputs from various analytical agents and relevant data from SharedContext.

    It primarily uses structured data passed via `current_step_inputs` (which are typically
    bound to the outputs of upstream agents like FundamentalAnalystAgent, SNCAnalystAgent,
    and CatalystWrapperAgent) and textual data (like company overview and risk factors)
    retrieved directly from `SharedContext`.
    """
    def __init__(self, kernel_service: KernelService):
        super().__init__(agent_name="ReportGenerationAgent", kernel_service=kernel_service)

    async def run(self, task_description: str, current_step_inputs: Dict[str, Any], shared_context: SharedContext) -> Dict[str, Any]:
        """
        Assembles a comprehensive Markdown report from various data sources.

        This method constructs a report by:
        1.  Retrieving structured analysis results (from FundamentalAnalystAgent,
            SNCAnalystAgent, CatalystWrapperAgent) passed directly via `current_step_inputs`.
        2.  Fetching general textual information (e.g., company overview, risk factors)
            from `SharedContext`, assuming they were populated by an earlier agent
            (like DataIngestionAgent).
        3.  Formatting these pieces of information into different sections of a
            Markdown document.

        Args:
            task_description (str): A description of the task (e.g., "Generate comprehensive report for MSFT").
            current_step_inputs (Dict[str, Any]): Inputs for this step, typically bound from
                                                outputs of previous agents. Expected keys include:
                - "report_title_detail" (str, optional): Specific text to include in the report title.
                - "fundamental_analysis_data_ref" (dict, optional): The structured output
                  from `FundamentalAnalystAgent` (includes status, data object with ratios, summaries, etc.).
                - "snc_analysis_data_ref" (dict, optional): The structured output from
                  `SNCAnalystAgent` (includes status, data object with rating and rationale).
                - "catalyst_data_ref" (dict, optional): The structured output from
                  `CatalystWrapperAgent` (includes status, data object with Catalyst insights).
            shared_context (SharedContext): The shared context object used to retrieve
                                            common textual data like company name, business overview,
                                            and risk factors.

        Returns:
            Dict[str, Any]: A dictionary containing the execution status and results:
                - {"status": "success",
                   "agent": self.agent_name,
                   "message": "Report generated successfully...",
                   "generated_report_text": <markdown_string>,
                   "report_file_path": <conceptual_path_to_saved_report_str>
                  }
                - {"status": "error", "message": <error_description_str>} (Not explicitly returned now, but could be added)
        """
        self.logger.info(f"'{self.agent_name}' received task: {task_description} with inputs: {current_step_inputs}")
        self.logger.info(f"Operating with SharedContext ID: {shared_context.get_session_id()} (CACM ID: {shared_context.get_cacm_id()})")

        # Retrieve data from current_step_inputs (passed via orchestrator bindings)
        fundamental_analysis_data = current_step_inputs.get("fundamental_analysis_data_ref")
        snc_analysis_data = current_step_inputs.get("snc_analysis_data_ref")
        catalyst_data = current_step_inputs.get("catalyst_data_ref")

        # Retrieve text data from SharedContext
        # Keys used here must match those used by DataIngestionAgent
        company_name = shared_context.get_data("company_name", "N/A") # Still useful for title
        company_ticker = shared_context.get_data("company_ticker", "N/A") # Still useful
        business_overview_text = shared_context.get_data("structured_financials_for_summary", "[Business Overview Not Available]")
        risk_factors_text = shared_context.get_data("risk_factors_section_text", "[Risk Factors Text Not Available]")
        
        self.logger.info(f"Retrieved data for report generation. Company: {company_name}")

        report_parts = []
        
        report_title_detail = current_step_inputs.get("report_title_detail", "Comprehensive Analysis Report")
        report_parts.append(f"# {report_title_detail} for {company_name} ({company_ticker})")
        report_parts.append(f"## Task: {task_description}")
        report_parts.append(f"Generated by: {self.agent_name} for CACM ID: {shared_context.get_cacm_id()} (Session: {shared_context.get_session_id()})")
        report_parts.append("---")

        # Company Overview Section
        report_parts.append("## 1. Company Overview")
        report_parts.append(business_overview_text)
        
        # Fundamental Analysis Section
        report_parts.append("\n## 2. Fundamental Analysis")
        if fundamental_analysis_data and isinstance(fundamental_analysis_data, dict) and fundamental_analysis_data.get('status') == "success":
            faa_data = fundamental_analysis_data.get('data', {})
            report_parts.append("### Key Financial Ratios:")
            ratios = faa_data.get('financial_ratios', {})
            if ratios:
                for key, value in ratios.items():
                    report_parts.append(f"- **{key.replace('_', ' ').title()}:** {value:.2f}" if isinstance(value, float) else f"- **{key.replace('_', ' ').title()}:** {value}")
            else:
                report_parts.append("- No financial ratios provided.")

            report_parts.append(f"\n### DCF Valuation: ${faa_data.get('dcf_valuation', 'N/A'):,.2f}" if isinstance(faa_data.get('dcf_valuation'), (int,float)) else f"\n### DCF Valuation: {faa_data.get('dcf_valuation', 'N/A')}")
            report_parts.append(f"### Enterprise Value: ${faa_data.get('enterprise_value', 'N/A'):,.2f}" if isinstance(faa_data.get('enterprise_value'), (int,float)) else f"### Enterprise Value: {faa_data.get('enterprise_value', 'N/A')}")
            report_parts.append(f"### Financial Health Assessment: {faa_data.get('financial_health', 'N/A')}")
            report_parts.append("\n### Analysis Summary (from FundamentalAnalystAgent):")
            report_parts.append(faa_data.get('analysis_summary', "[Summary not available]"))
        else:
            report_parts.append("Fundamental analysis data not available or indicates an error.")
            if fundamental_analysis_data and isinstance(fundamental_analysis_data, dict):
                 report_parts.append(f"Error details: {fundamental_analysis_data.get('message', 'Unknown error')}")


        # SNC Analysis Section
        report_parts.append("\n## 3. Shared National Credit (SNC) Analysis")
        if snc_analysis_data and isinstance(snc_analysis_data, dict) and snc_analysis_data.get('status') == "success":
            sncaa_data = snc_analysis_data.get('data', {})
            report_parts.append(f"**SNC Rating:** {sncaa_data.get('rating', '[Rating not provided]')}")
            report_parts.append("\n**Rationale:**")
            report_parts.append(sncaa_data.get('rationale', '[Rationale not provided]'))
        else:
            report_parts.append("SNC analysis data not available or indicates an error.")
            if snc_analysis_data and isinstance(snc_analysis_data, dict):
                 report_parts.append(f"Error details: {snc_analysis_data.get('message', 'Unknown error')}")

        # Catalyst Strategic Insights Section
        report_parts.append("\n## 4. Catalyst Strategic Insights")
        if catalyst_data and isinstance(catalyst_data, dict) and catalyst_data.get('status') == "success":
            cat_data = catalyst_data.get('data', {})
            report_parts.append("```json")
            report_parts.append(json.dumps(cat_data, indent=2))
            report_parts.append("```")
        else:
            report_parts.append("Catalyst strategic insights not available or indicates an error.")
            if catalyst_data and isinstance(catalyst_data, dict):
                report_parts.append(f"Error details: {catalyst_data.get('message', 'Unknown error')}")


        # Key Risk Factors Section
        report_parts.append("\n## 5. Key Risk Factors (from Document)")
        report_parts.append(risk_factors_text)
        
        # Deprecated/Removed old sections that pulled directly from SharedContext
        # - Old "Key Financial Ratios" (now part of Fundamental Analysis section)
        # - Old "Financial Performance Summary" (covered by FAA summary)
        # - Old "Key Risks Summary" (covered by FAA summary or new Risk Factors section)
        # - Old "Overall Assessment" (covered by FAA summary)

        if current_step_inputs:
            report_parts.append("\n## 6. Additional Report Parameters (Step Inputs)")
            # Filter out the large data refs for cleaner display of other params
            filtered_inputs_for_display = {k: v for k, v in current_step_inputs.items() if not k.endswith("_data_ref")}
            report_parts.append(f"```json\n{json.dumps(filtered_inputs_for_display, indent=2)}\n```")

        # This section might be redundant if all data comes via current_step_inputs bindings
        if hasattr(self, 'stored_results') and self.stored_results:
            report_parts.append("\n## 7. Data Received via Direct Agent Communication (Legacy)")
            for i, res_item in enumerate(self.stored_results):
                report_parts.append(f"**Item {i+1} from Agent '{res_item.get('from', 'Unknown')}':**")
                report_parts.append(f"```json\n{json.dumps(res_item.get('data',{}), indent=2)}\n```")
        
        final_report_string = "\n\n".join(report_parts)
            
        self.logger.info(f"Report assembled. Length: {len(final_report_string)}")

        # Conceptual File Output Logic
        report_filename = f"generated_report_{shared_context.get_session_id()}_{shared_context.get_cacm_id()}.md"
        conceptual_file_path = f"./output_artifacts/final_machine_reports/{report_filename}"
        self.logger.info(f"Conceptually saving report to: {conceptual_file_path}")
        self.logger.debug(f"Report Content for {report_filename}:\n{final_report_string}")
            
        # d. Update Agent Return Value
        return {
            "status": "success",
            "agent": self.agent_name,
            "message": "Report generated successfully and conceptually saved to file.",
            "generated_report_text": final_report_string,
            "report_file_path": conceptual_file_path 
        }

    async def receive_analysis_results(self, sending_agent_name: str, results: Dict[str, Any]):
        """
        Stores results received directly from another agent.

        This method is intended for scenarios where an agent might push its results
        directly to this ReportGenerationAgent, outside the typical orchestrator-managed
        workflow step bindings. This could be considered a legacy pattern or used for
        specific inter-agent communication needs not covered by the standard flow.

        Args:
            sending_agent_name (str): The name of the agent sending the results.
            results (Dict[str, Any]): The data/results payload from the sending agent.
        """
        self.logger.info(f"'{self.agent_name}' received analysis results from '{sending_agent_name}'. Storing under 'stored_results'.")
        if not hasattr(self, 'stored_results'):
            self.stored_results = []
        self.stored_results.append({ "from": sending_agent_name, "data": results})
        self.logger.info(f"Results from '{sending_agent_name}' stored. Total stored items: {len(self.stored_results)}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # from semantic_kernel import Kernel # Not strictly needed for this __main__ as kernel isn't used by agent directly
    
    class MockKernelService(KernelService): # Minimal mock
        def __init__(self): self.logger = logging.getLogger("MockReportGenKernelService")
        def get_kernel(self): return None
        def _initialize_kernel(self): pass

    mock_service = MockKernelService()
    report_agent = ReportGenerationAgent(kernel_service=mock_service)
    test_shared_context = SharedContext(cacm_id="report_gen_test_001")

    # Populate SharedContext with sample data as if previous agents ran
    test_shared_context.set_data("company_name", "TestCorp")
    test_shared_context.set_data("company_ticker", "TCORP")
    test_shared_context.set_data("calculated_key_ratios", {
        "current_ratio": 2.15, 
        "debt_to_equity_ratio": 0.65,
        "gross_profit_margin": 55.5,
        "net_profit_margin": 12.0
    })
    test_shared_context.set_data("financial_performance_summary_text", "[Placeholder Financial Summary - Test Data]")
    test_shared_context.set_data("key_risks_summary_text", "[Placeholder Risk Summary - Test Data]")
    test_shared_context.set_data("overall_assessment_text", "[Placeholder Overall Assessment - Test Data]")

    import asyncio
    async def test_run():
        # Simulate receiving data from AnalysisAgent
        await report_agent.receive_analysis_results(
            "MockAnalysisAgent", 
            {"summary": "Mock analysis summary", "key_metric": 123.45}
        )
        
        result = await report_agent.run(
            task_description="Generate the standard financial report.",
            current_step_inputs={"report_title_detail": "Annual Test Report"},
            shared_context=test_shared_context
        )
        print("\n--- Generated Report Text ---")
        print(result.get("generated_report_text"))
        print(f"\nConceptual file path: {result.get('report_file_path')}")
        print(f"Agent status: {result.get('status')}, message: {result.get('message')}")
        
        print("\n--- SharedContext after Report Generation ---")
        test_shared_context.log_context_summary()

    asyncio.run(test_run())
