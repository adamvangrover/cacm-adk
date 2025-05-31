import logging
import json
from typing import Dict, Any

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext
from semantic_kernel.functions.kernel_arguments import KernelArguments

class AnalysisAgent(Agent):
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
            "reporting_to_other_agent": "Not attempted"
        }
        final_status = "success"
        final_message = "Analysis phase completed successfully." # Default success message

        financial_summary_text = "[Financial Performance Summary Not Available - Generation Skipped or Failed]"
        key_risks_summary_text = "[Key Risks Summary Not Available - Generation Skipped or Failed]"
        overall_assessment_text = "[Overall Assessment Not Available - Generation Skipped or Failed]"
        ratios_skill_payload = None

        expanded_financial_data = shared_context.get_data("financial_data_for_ratios_expanded")
        structured_financials_for_summary = shared_context.get_data("structured_financials_for_summary")
        risk_factors_section_text = shared_context.get_data("risk_factors_section_text")

        kernel = self.get_kernel()
        if not kernel:
            agent_ops_summary["kernel_access"] = "Failed: Kernel not available."
            final_status = "error"
            final_message = agent_ops_summary["kernel_access"]
        else:
            agent_ops_summary["kernel_access"] = "Success."
            # Ratio Calculation
            if not expanded_financial_data:
                agent_ops_summary["ratio_calculation"] = "Skipped: Missing 'financial_data_for_ratios_expanded'."
                if final_status == "success": final_status = "warning"
            elif not self.skills_plugin_name:
                agent_ops_summary["ratio_calculation"] = "Skipped: No FinancialAnalysis plugin configured."
                if final_status == "success": final_status = "warning"
            else:
                fin_plugin = self.get_plugin(self.skills_plugin_name)
                if not fin_plugin:
                    agent_ops_summary["ratio_calculation"] = f"Error: Plugin '{self.skills_plugin_name}' not found."
                    final_status = "error"; final_message = agent_ops_summary["ratio_calculation"]
                else:
                    ratio_func = fin_plugin.get("calculate_basic_ratios")
                    if not ratio_func:
                        agent_ops_summary["ratio_calculation"] = "Error: 'calculate_basic_ratios' function not found."
                        final_status = "error"; final_message = agent_ops_summary["ratio_calculation"]
                    else:
                        try:
                            args = KernelArguments(financial_data=expanded_financial_data, rounding_precision=current_step_inputs.get("rounding_precision", 2))
                            result = await kernel.invoke(ratio_func, args)
                            ratios_skill_payload = result.value
                            shared_context.set_data("calculated_key_ratios", ratios_skill_payload.get("calculated_ratios", {}))
                            agent_ops_summary["ratio_calculation"] = f"Success: {ratios_skill_payload.get('calculated_ratios', {})}"
                            if ratios_skill_payload.get("errors"): final_status = "partial_success"
                        except Exception as e:
                            agent_ops_summary["ratio_calculation"] = f"Error invoking 'calculate_basic_ratios' skill: {e}"
                            final_status = "error"; final_message = agent_ops_summary["ratio_calculation"]

            # Summarization Skills (only if no critical error yet)
            if final_status not in ["error"]:
                report_plugin = kernel.plugins.get("ReportingAnalysisSkills")
                if report_plugin:
                    summ_fn = report_plugin.get("generate_financial_summary")
                    if summ_fn and structured_financials_for_summary:
                        try: financial_summary_text = (await kernel.invoke(summ_fn, KernelArguments(financial_data=structured_financials_for_summary))).value; shared_context.set_data("financial_performance_summary_text", financial_summary_text); agent_ops_summary["financial_summary_generation"] = "Success (placeholder)."
                        except Exception as e: agent_ops_summary["financial_summary_generation"] = f"Error: {e}"; final_status="error"; final_message=f"Error in financial summary: {e}"
                    elif not structured_financials_for_summary: agent_ops_summary["financial_summary_generation"] = "Skipped: No structured financials."
                    else: agent_ops_summary["financial_summary_generation"] = "Skipped: Function not found."

                    risk_fn = report_plugin.get("generate_key_risks_summary")
                    if risk_fn and risk_factors_section_text:
                        try: key_risks_summary_text = (await kernel.invoke(risk_fn, KernelArguments(risk_factors_text=risk_factors_section_text))).value; shared_context.set_data("key_risks_summary_text", key_risks_summary_text); agent_ops_summary["risk_summary_generation"] = "Success (placeholder)."
                        except Exception as e: agent_ops_summary["risk_summary_generation"] = f"Error: {e}"; final_status="error"; final_message=f"Error in risk summary: {e}"
                    elif not risk_factors_section_text: agent_ops_summary["risk_summary_generation"] = "Skipped: No risk text."
                    else: agent_ops_summary["risk_summary_generation"] = "Skipped: Function not found."

                    assess_fn = report_plugin.get("generate_overall_assessment")
                    if assess_fn:
                        r_map = shared_context.get_data("calculated_key_ratios", {}); fs_text = shared_context.get_data("financial_performance_summary_text", ""); kr_text = shared_context.get_data("key_risks_summary_text", "")
                        try: overall_assessment_text = (await kernel.invoke(assess_fn, KernelArguments(ratios_json_str=json.dumps(r_map), financial_summary_text=fs_text, key_risks_summary_text=kr_text))).value; shared_context.set_data("overall_assessment_text", overall_assessment_text); agent_ops_summary["overall_assessment_generation"] = "Success (placeholder)."
                        except Exception as e: agent_ops_summary["overall_assessment_generation"] = f"Error: {e}"; final_status="error"; final_message=f"Error in overall assessment: {e}"
                    else: agent_ops_summary["overall_assessment_generation"] = "Skipped: Function not found."

                    if any(s.startswith("Skipped:") for s in [agent_ops_summary["financial_summary_generation"], agent_ops_summary["risk_summary_generation"], agent_ops_summary["overall_assessment_generation"]]):
                        if final_status == "success": final_status = "warning"
                        if final_message == "Analysis phase completed successfully. All results stored in SharedContext.": # only override if no prior error message
                           final_message = "Analysis completed with some summarization steps skipped."
                else: # Reporting plugin not found
                    agent_ops_summary["financial_summary_generation"]=agent_ops_summary["risk_summary_generation"]=agent_ops_summary["overall_assessment_generation"]="Skipped: ReportingAnalysisSkills plugin not found."
                    if final_status == "success": final_status = "warning"; final_message = "Analysis completed with summarization plugin not found."

        agent_ops_summary["final_message_before_reporting"] = final_message

        # Communication with ReportGenerationAgent
        report_agent = await self.get_or_create_agent("ReportGenerationAgent", {"triggering_agent": self.agent_name})
        if report_agent:
            # ... (data_for_report preparation as before) ...
            data_for_report = { "analysis_status": final_status, "analysis_summary_message": final_message, "ratios_payload": ratios_skill_payload, "financial_summary": shared_context.get_data("financial_performance_summary_text"), "risk_summary": shared_context.get_data("key_risks_summary_text"), "overall_assessment": shared_context.get_data("overall_assessment_text"), "full_analysis_ops_log": agent_ops_summary }
            try: await report_agent.receive_analysis_results(self.agent_name, data_for_report); agent_ops_summary["reporting_to_other_agent"] = "Success."
            except Exception as e: agent_ops_summary["reporting_to_other_agent"] = f"Error: {e}"; final_status = "error"; final_message=f"Failed sending to ReportGen: {e}"
        else: agent_ops_summary["reporting_to_other_agent"] = "Failed: Could not get ReportGenerationAgent."; final_status = "error"; final_message="Failed to get ReportGenerationAgent."

        return {"status": final_status, "agent": self.agent_name, "message": final_message,
                "ratios_from_skill": ratios_skill_payload,
                "text_summaries_generated": {"financial_performance": shared_context.get_data("financial_performance_summary_text"),
                                             "key_risks": shared_context.get_data("key_risks_summary_text"),
                                             "overall_assessment": shared_context.get_data("overall_assessment_text")},
                "detailed_operations_summary": agent_ops_summary}

# Main block for standalone testing (if needed) - content omitted for brevity in this overwrite.
if __name__ == '__main__':
    pass
