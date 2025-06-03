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
            "ratio_explanations_generation": "Not attempted", 
            "esg_data_processing": "Not attempted", 
            "conceptual_data_drift_check": "Not attempted",
            "conceptual_model_drift_check": "Not attempted",
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

            # Conceptual Data Drift Check
            if final_status not in ["error"] and expanded_financial_data:
                self.logger.info("Performing conceptual data drift check.")
                historical_stats = {"current_assets_mean": 600000.0, "revenue_mean": 2200000.0, "total_debt_mean": 400000.0 }
                data_drift_detected_messages = []

                for key, hist_mean in historical_stats.items():
                    current_value = expanded_financial_data.get(key)
                    if current_value is not None:
                        try:
                            current_value_float = float(current_value)
                            deviation = abs(current_value_float - hist_mean) / hist_mean if hist_mean != 0 else float('inf')
                            if deviation > 0.5: # More than 50% deviation
                                msg = f"CONCEPTUAL DATA DRIFT: '{key}' ({current_value_float:,.0f}) significantly deviates by {deviation:.2%} from historical mean ({hist_mean:,.0f})."
                                self.logger.warning(msg)
                                data_drift_detected_messages.append(msg)
                        except ValueError:
                            self.logger.warning(f"Could not convert current value of '{key}' ({current_value}) to float for data drift check.")
                    else:
                        self.logger.info(f"Key '{key}' not present in current expanded_financial_data for data drift check.")
                
                if data_drift_detected_messages:
                    agent_ops_summary["conceptual_data_drift_check"] = "Potential data drift detected: " + "; ".join(data_drift_detected_messages)
                    if final_status == "success": final_status = "warning"
                    if "Potential data drift detected" not in final_message and "Analysis phase completed successfully." in final_message : final_message = "Analysis completed with potential data drift detected (conceptual check)."
                    elif "Potential data drift detected" not in final_message: final_message += " Potential data drift detected (conceptual check)."

                else:
                    agent_ops_summary["conceptual_data_drift_check"] = "No significant data drift detected (placeholder logic)."
            elif not expanded_financial_data:
                 agent_ops_summary["conceptual_data_drift_check"] = "Skipped: expanded_financial_data not available."


            # Conceptual Model Drift Check (on a calculated ratio)
            if final_status not in ["error"] and ratios_skill_payload:
                self.logger.info("Performing conceptual model drift check on current_ratio.")
                calculated_ratios_map = ratios_skill_payload.get("calculated_ratios", {})
                current_ratio_value = calculated_ratios_map.get("current_ratio")

                if current_ratio_value is not None:
                    try:
                        current_ratio_float = float(current_ratio_value)
                        historical_avg_current_ratio = 1.8 
                        model_drift_threshold = 0.5 # Absolute difference

                        if abs(current_ratio_float - historical_avg_current_ratio) > model_drift_threshold:
                            msg = f"CONCEPTUAL MODEL DRIFT: 'current_ratio' ({current_ratio_float:.2f}) significantly deviates from historical average ({historical_avg_current_ratio:.2f}). Output may be drifting."
                            self.logger.warning(msg)
                            agent_ops_summary["conceptual_model_drift_check"] = msg
                            if final_status == "success": final_status = "warning"
                            if "Potential model drift detected" not in final_message and "Analysis phase completed successfully." in final_message : final_message = "Analysis completed with potential model drift detected (conceptual check)."
                            elif "Potential model drift detected" not in final_message : final_message += " Potential model drift detected (conceptual check)."
                        else:
                            agent_ops_summary["conceptual_model_drift_check"] = f"No significant model output drift detected for current_ratio ({current_ratio_float:.2f}) vs historical ({historical_avg_current_ratio:.2f}) (placeholder logic)."
                    except ValueError:
                        self.logger.warning(f"Could not convert current_ratio value ('{current_ratio_value}') to float for model drift check.")
                        agent_ops_summary["conceptual_model_drift_check"] = "Skipped: current_ratio value not numeric."
                else:
                    agent_ops_summary["conceptual_model_drift_check"] = "Skipped: 'current_ratio' not found in calculated ratios."
            elif not ratios_skill_payload:
                agent_ops_summary["conceptual_model_drift_check"] = "Skipped: Ratio calculation payload not available."

            # Summarization Skills (only if no critical error yet)
            if final_status not in ["error"]: # This check might be redundant if already error, but safe
                report_plugin = kernel.plugins.get("ReportingAnalysisSkills")
                if report_plugin:
                    # 1. Generate Financial Summary
                    fin_summary_fn = report_plugin.get("generate_financial_summary")
                    if fin_summary_fn:
                        if structured_financials_for_summary:
                            try:
                                self.logger.info("Invoking 'generate_financial_summary' LLM skill.")
                                result = await kernel.invoke(fin_summary_fn, KernelArguments(financial_data=structured_financials_for_summary))
                                financial_summary_text = str(result.value if result and hasattr(result, 'value') else result).strip()
                                shared_context.set_data("financial_performance_summary_llm", financial_summary_text)
                                if "[Placeholder" in financial_summary_text or "[LLM" in financial_summary_text:
                                    agent_ops_summary["financial_summary_generation"] = f"Success (LLM returned placeholder/error: {financial_summary_text[:100]})"
                                    if final_status == "success": final_status = "partial_success"
                                else:
                                    agent_ops_summary["financial_summary_generation"] = "Success (LLM generated)."
                            except Exception as e:
                                financial_summary_text = "[LLM Financial Summary generation failed in agent.]"
                                shared_context.set_data("financial_performance_summary_llm", financial_summary_text)
                                agent_ops_summary["financial_summary_generation"] = f"Error invoking skill: {e}"
                                final_status="error"; final_message=f"Error in financial summary generation: {e}"
                        else:
                            agent_ops_summary["financial_summary_generation"] = "Skipped: No 'structured_financials_for_summary' in shared_context."
                            financial_summary_text = "[Financial Performance Summary Not Available - Input Missing]"
                            shared_context.set_data("financial_performance_summary_llm", financial_summary_text)
                            if final_status == "success": final_status = "warning"
                    else:
                        agent_ops_summary["financial_summary_generation"] = "Skipped: 'generate_financial_summary' function not found in plugin."
                        financial_summary_text = "[Financial Performance Summary Not Available - Skill Missing]"
                        shared_context.set_data("financial_performance_summary_llm", financial_summary_text)
                        if final_status == "success": final_status = "warning"

                    # 2. Generate Key Risks Summary
                    key_risks_fn = report_plugin.get("generate_key_risks_summary")
                    if key_risks_fn:
                        if risk_factors_section_text:
                            try:
                                self.logger.info("Invoking 'generate_key_risks_summary' LLM skill.")
                                result = await kernel.invoke(key_risks_fn, KernelArguments(risk_factors_text=risk_factors_section_text))
                                key_risks_summary_text = str(result.value if result and hasattr(result, 'value') else result).strip()
                                shared_context.set_data("key_risks_summary_llm", key_risks_summary_text)
                                if "[Placeholder" in key_risks_summary_text or "[LLM" in key_risks_summary_text:
                                    agent_ops_summary["risk_summary_generation"] = f"Success (LLM returned placeholder/error: {key_risks_summary_text[:100]})"
                                    if final_status == "success": final_status = "partial_success"
                                else:
                                    agent_ops_summary["risk_summary_generation"] = "Success (LLM generated)."
                            except Exception as e:
                                key_risks_summary_text = "[LLM Key Risks Summary generation failed in agent.]"
                                shared_context.set_data("key_risks_summary_llm", key_risks_summary_text)
                                agent_ops_summary["risk_summary_generation"] = f"Error invoking skill: {e}"
                                final_status="error"; final_message=f"Error in risk summary generation: {e}"
                        else:
                            agent_ops_summary["risk_summary_generation"] = "Skipped: No 'risk_factors_section_text' in shared_context."
                            key_risks_summary_text = "[Key Risks Summary Not Available - Input Missing]"
                            shared_context.set_data("key_risks_summary_llm", key_risks_summary_text)
                            if final_status == "success": final_status = "warning"
                    else:
                        agent_ops_summary["risk_summary_generation"] = "Skipped: 'generate_key_risks_summary' function not found in plugin."
                        key_risks_summary_text = "[Key Risks Summary Not Available - Skill Missing]"
                        shared_context.set_data("key_risks_summary_llm", key_risks_summary_text)
                        if final_status == "success": final_status = "warning"

                    # 3. Generate Overall Assessment
                    overall_assessment_fn = report_plugin.get("generate_overall_assessment")
                    if overall_assessment_fn:
                        calculated_ratios_map = shared_context.get_data("calculated_key_ratios", {})
                        ratios_json_str = json.dumps(calculated_ratios_map)
                        # Use the freshly generated summaries (which might be placeholders if earlier steps failed)
                        current_financial_summary = shared_context.get_data("financial_performance_summary_llm", financial_summary_text)
                        current_key_risks_summary = shared_context.get_data("key_risks_summary_llm", key_risks_summary_text)
                        try:
                            self.logger.info("Invoking 'generate_overall_assessment' LLM skill.")
                            args = KernelArguments(
                                ratios_json_str=ratios_json_str,
                                financial_summary_text=current_financial_summary,
                                key_risks_summary_text=current_key_risks_summary
                            )
                            result = await kernel.invoke(overall_assessment_fn, args)
                            overall_assessment_text = str(result.value if result and hasattr(result, 'value') else result).strip()
                            shared_context.set_data("overall_assessment_llm", overall_assessment_text)
                            if "[Placeholder" in overall_assessment_text or "[LLM" in overall_assessment_text:
                                agent_ops_summary["overall_assessment_generation"] = f"Success (LLM returned placeholder/error: {overall_assessment_text[:100]})"
                                if final_status == "success": final_status = "partial_success"
                            else:
                                agent_ops_summary["overall_assessment_generation"] = "Success (LLM generated)."
                        except Exception as e:
                            overall_assessment_text = "[LLM Overall Assessment generation failed in agent.]"
                            shared_context.set_data("overall_assessment_llm", overall_assessment_text)
                            agent_ops_summary["overall_assessment_generation"] = f"Error invoking skill: {e}"
                            final_status="error"; final_message=f"Error in overall assessment generation: {e}"
                    else:
                        agent_ops_summary["overall_assessment_generation"] = "Skipped: 'generate_overall_assessment' function not found in plugin."
                        overall_assessment_text = "[Overall Assessment Not Available - Skill Missing]"
                        shared_context.set_data("overall_assessment_llm", overall_assessment_text)
                        if final_status == "success": final_status = "warning"
                    
                    if any("Skipped:" in s for s in [agent_ops_summary["financial_summary_generation"], agent_ops_summary["risk_summary_generation"], agent_ops_summary["overall_assessment_generation"]]):
                        if final_status == "success": final_status = "warning"
                        if final_message == "Analysis phase completed successfully.": 
                           final_message = "Analysis completed with some LLM summarization steps skipped or function not found."
                    elif any("LLM returned placeholder" in s for s in [agent_ops_summary["financial_summary_generation"], agent_ops_summary["risk_summary_generation"], agent_ops_summary["overall_assessment_generation"]]):
                         if final_status == "success": final_status = "partial_success" # Already partial_success if placeholder
                         if final_message == "Analysis phase completed successfully.":
                            final_message = "Analysis completed, but some LLM summaries are placeholders."

                else: # Reporting plugin not found
                    agent_ops_summary["financial_summary_generation"]=agent_ops_summary["risk_summary_generation"]=agent_ops_summary["overall_assessment_generation"]="Skipped: ReportingAnalysisSkills plugin not found."
                    shared_context.set_data("financial_performance_summary_llm", financial_summary_text) # Store default placeholder
                    shared_context.set_data("key_risks_summary_llm", key_risks_summary_text) # Store default placeholder
                    shared_context.set_data("overall_assessment_llm", overall_assessment_text) # Store default placeholder
                    if final_status == "success": final_status = "warning"; final_message = "Analysis completed, but ReportingAnalysisSkills plugin for LLM summaries was not found."

            # Ratio Explanation Generation (after ratio calculation and summarization, if plugin available)
            if final_status not in ["error"] and report_plugin: # report_plugin check implies kernel is available
                calculated_ratios = shared_context.get_data("calculated_key_ratios", {})
                key_ratios_explanations_llm = {}
                explanations_succeeded = 0
                explanations_failed_or_placeholder = 0

                if calculated_ratios:
                    explanation_skill_func = report_plugin.get("generate_explanation")
                    if explanation_skill_func:
                        self.logger.info(f"Found 'generate_explanation' skill. Attempting to explain {len(calculated_ratios)} ratios.")
                        ratio_contexts = {
                            "current_ratio": "Measures short-term liquidity (Current Assets / Current Liabilities).",
                            "debt_to_equity_ratio": "Indicates financial leverage (Total Debt / Total Equity).",
                            "gross_profit_margin": "Shows the percentage of revenue that exceeds the cost of goods sold (COGS).",
                            "net_profit_margin": "Represents the percentage of revenue remaining after all operating expenses, interest, taxes, and preferred stock dividends have been deducted.",
                            "return_on_equity": "Measures the profitability of a corporation in relation to stockholders’ equity.",
                            # Add more contexts as per FinancialAnalysisSkill's output
                        }
                        for ratio_key, ratio_value in calculated_ratios.items():
                            if ratio_value is None or str(ratio_value).strip().lower() in ["n/a", "nan", "inf", "-inf", ""]:
                                explanation_text = f"Value for {ratio_key.replace('_', ' ').title()} is not suitable for explanation."
                                key_ratios_explanations_llm[ratio_key] = explanation_text
                                explanations_failed_or_placeholder += 1
                                continue

                            data_point_name = ratio_key.replace('_', ' ').title()
                            data_point_value_str = f"{ratio_value:.2f}" if isinstance(ratio_value, (float, int)) else str(ratio_value)
                            context_desc = ratio_contexts.get(ratio_key, "A financial ratio indicating company performance or financial health.")
                            
                            try:
                                self.logger.debug(f"Invoking 'generate_explanation' for {data_point_name} ({data_point_value_str}).")
                                exp_args = KernelArguments(
                                    data_point_name=data_point_name,
                                    data_point_value=data_point_value_str,
                                    context_description=context_desc
                                )
                                result = await kernel.invoke(explanation_skill_func, exp_args)
                                explanation_text = str(result.value if result and hasattr(result, 'value') else result).strip()

                                if "[Placeholder" in explanation_text or "[LLM" in explanation_text or not explanation_text:
                                    self.logger.warning(f"LLM returned placeholder or empty explanation for {data_point_name}.")
                                    explanation_text = f"LLM explanation for {data_point_name} (value: {data_point_value_str}) was a placeholder or empty."
                                    explanations_failed_or_placeholder += 1
                                else:
                                    self.logger.info(f"LLM explanation generated for {data_point_name}.")
                                    explanations_succeeded += 1
                                key_ratios_explanations_llm[ratio_key] = explanation_text
                            except Exception as e:
                                self.logger.error(f"Error invoking 'generate_explanation' for {data_point_name}: {e}")
                                key_ratios_explanations_llm[ratio_key] = f"Error generating explanation for {data_point_name}: {e}"
                                explanations_failed_or_placeholder += 1
                        
                        agent_ops_summary["ratio_explanations_generation"] = f"Success for {explanations_succeeded} ratio(s), Failed/Placeholder for {explanations_failed_or_placeholder} ratio(s)."
                        if explanations_failed_or_placeholder > 0 and final_status == "success":
                            final_status = "partial_success"
                            final_message = "Analysis completed, but some ratio explanations are placeholders or failed."

                    else: # explanation_skill_func not found
                        agent_ops_summary["ratio_explanations_generation"] = "Skipped: 'generate_explanation' function not found in ReportingAnalysisSkills plugin."
                        for ratio_key in calculated_ratios.keys():
                            key_ratios_explanations_llm[ratio_key] = "Explanation generation skill not available."
                        if final_status == "success" and calculated_ratios: final_status = "warning"
                else: # No calculated ratios
                    agent_ops_summary["ratio_explanations_generation"] = "Skipped: No ratios were calculated or available."
                
                shared_context.set_data("key_ratios_explanations_llm", key_ratios_explanations_llm)
            elif final_status not in ["error"]: # report_plugin was not found
                 agent_ops_summary["ratio_explanations_generation"] = "Skipped: ReportingAnalysisSkills plugin not found."
                 if final_status == "success": final_status = "warning"

            # ESG Data Retrieval and Summarization
            if final_status not in ["error"]: # Proceed only if no critical errors so far
                self.logger.info("Starting ESG data retrieval and summarization process.")
                company_ticker_for_uri = shared_context.get_data("companyTicker", "unknown_company_ticker")
                # Assuming a base URI structure, this should align with KG population
                company_uri_base_for_query = current_step_inputs.get("company_uri_base", "http://example.com/entity/")
                company_uri_for_query = f"{company_uri_base_for_query.rstrip('/')}/{company_ticker_for_uri}"

                esg_sparql_query = f"""
                    PREFIX esg: <http://example.com/ontology/cacm_credit_ontology/0.3/esg#>
                    PREFIX kgclass: <http://example.com/ontology/cacm_credit_ontology/0.3/classes/#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX altdata: <http://example.com/ontology/cacm_credit_ontology/0.3/alternative_data#> # Not used here but good practice

                    SELECT ?metric_uri ?metric_label ?metric_value ?metric_unit ?metric_type ?rating_provider
                    WHERE {{
                      BIND(<{company_uri_for_query}> AS ?company_entity)

                      {{
                        # Get directly reported ESG metrics (Environmental, Social, Governance)
                        ?company_entity esg:reportsESGMetric ?metric_uri .
                        ?metric_uri rdfs:label ?metric_label ;
                                    esg:metricValue ?metric_value ;
                                    rdf:type ?metric_type_full_uri .
                        OPTIONAL {{ ?metric_uri esg:metricUnit ?metric_unit . }}
                        FILTER(?metric_type_full_uri IN (esg:EnvironmentalFactor, esg:SocialFactor, esg:GovernanceFactor, esg:CarbonEmission, esg:WaterUsage, esg:WasteManagementPolicyAdherence, esg:EmployeeSafetyRecord, esg:CommunityInvestmentLevel, esg:DiversityAndInclusionRating, esg:BoardIndependenceRatio, esg:ExecutiveCompensationPolicyTransparency, esg:ShareholderRightsStrength ))
                        BIND(REPLACE(STR(?metric_type_full_uri), STR(esg:), "esg:") AS ?metric_type) # Pass short form
                      }}
                      UNION
                      {{
                        # Get overall ESG ratings
                        ?company_entity esg:hasESGRating ?metric_uri .
                        ?metric_uri rdf:type esg:OverallESGRating ;
                                    rdfs:label ?metric_label ; 
                                    esg:ratingValue ?metric_value .
                        OPTIONAL {{ ?metric_uri esg:dataSource ?rating_provider . }}
                        BIND("esg:OverallESGRating" AS ?metric_type) 
                      }}
                    }}
                """
                self.logger.debug(f"Formulated SPARQL query for ESG data:\n{esg_sparql_query}")

                try:
                    kg_agent = await self.get_or_create_agent("KnowledgeGraphAgent", {})
                    if not kg_agent:
                        agent_ops_summary["esg_data_processing"] = "Failed: Could not get KnowledgeGraphAgent."
                        if final_status == "success": final_status = "error"
                    else:
                        # Default kg_file_path can be handled by KG agent itself or specified here
                        kg_agent_inputs = {"sparql_query": esg_sparql_query}
                        # One might pass a specific KG file if ESG data is in a separate graph:
                        # kg_agent_inputs["kg_file_path"] = current_step_inputs.get("esg_kg_file_path", None) 
                        
                        self.logger.info("Invoking KnowledgeGraphAgent to fetch ESG data.")
                        kg_results_payload = await kg_agent.run("Fetch ESG data from KG", kg_agent_inputs, shared_context)

                        if kg_results_payload.get("status") == "success":
                            actual_kg_results = kg_results_payload.get("data", {}).get("results", [])
                            agent_ops_summary["esg_data_processing"] = f"KG query successful, {len(actual_kg_results)} results."
                            
                            if actual_kg_results:
                                esg_analysis_plugin = kernel.plugins.get("ESGAnalysis")
                                if not esg_analysis_plugin:
                                    agent_ops_summary["esg_data_processing"] += " Error: ESGAnalysis plugin not found."
                                    if final_status == "success": final_status = "error"
                                else:
                                    esg_skill_func = esg_analysis_plugin.get("summarize_esg_factors_from_kg")
                                    if not esg_skill_func:
                                        agent_ops_summary["esg_data_processing"] += " Error: summarize_esg_factors_from_kg function not found."
                                        if final_status == "success": final_status = "error"
                                    else:
                                        company_name_for_summary = shared_context.get_data("companyName", "N/A")
                                        esg_args = KernelArguments(kg_query_results=actual_kg_results, company_name=company_name_for_summary)
                                        
                                        self.logger.info(f"Invoking ESGAnalysisSkill to summarize {len(actual_kg_results)} ESG factors.")
                                        summary_result = await kernel.invoke(esg_skill_func, esg_args)
                                        summarized_esg_data = summary_result.value
                                        
                                        shared_context.set_data("summarized_esg_data", summarized_esg_data) # Changed key from _llm
                                        agent_ops_summary["esg_data_processing"] += " Summarization successful."
                                        self.logger.info(f"ESG data summarized and stored in SharedContext: {summarized_esg_data}")
                            else: # No results from KG
                                agent_ops_summary["esg_data_processing"] += " No specific ESG data points found in KG for company."
                                shared_context.set_data("summarized_esg_data", {"company_name": shared_context.get_data("companyName", "N/A"), "notes": "No ESG data points found in KG."})
                                if final_status == "success": final_status = "partial_success" # It's not an error, but data is missing
                        else: # KG Agent failed
                            agent_ops_summary["esg_data_processing"] = f"Failed: KnowledgeGraphAgent error - {kg_results_payload.get('message', 'Unknown error')}"
                            if final_status == "success": final_status = "error"
                
                except Exception as e_esg:
                    self.logger.exception(f"Error during ESG data processing: {e_esg}")
                    agent_ops_summary["esg_data_processing"] = f"Failed: Exception - {e_esg}"
                    if final_status == "success": final_status = "error"
            
            # Consolidate final message if it's still the default success one
            if final_status == "success" and final_message == "Analysis phase completed successfully.":
                final_message = "All analysis steps, including ESG processing, completed."
            elif final_status == "partial_success" and final_message == "Analysis phase completed successfully.": # Overwrite default if partial due to ESG
                 final_message = agent_ops_summary.get("esg_data_processing", "Analysis partially completed; check ESG processing status.")
            elif final_status == "error" and final_message == "Analysis phase completed successfully.": # Overwrite default if error due to ESG
                 final_message = agent_ops_summary.get("esg_data_processing", "Analysis error; check ESG processing status.")


        agent_ops_summary["final_message_before_reporting"] = final_message

        # Communication with ReportGenerationAgent
        report_agent = await self.get_or_create_agent("ReportGenerationAgent", {"triggering_agent": self.agent_name})
        if report_agent:
            data_for_report = {
                "analysis_status": final_status,
                "analysis_summary_message": final_message,
                "ratios_payload": ratios_skill_payload,
                "financial_summary": shared_context.get_data("financial_performance_summary_llm"),
                "risk_summary": shared_context.get_data("key_risks_summary_llm"),
                "overall_assessment": shared_context.get_data("overall_assessment_llm"),
                "full_analysis_ops_log": agent_ops_summary
            }
            try:
                await report_agent.receive_analysis_results(self.agent_name, data_for_report)
                agent_ops_summary["reporting_to_other_agent"] = "Success."
            except Exception as e:
                agent_ops_summary["reporting_to_other_agent"] = f"Error: {e}"
                final_status = "error"; final_message=f"Failed sending results to ReportGenerationAgent: {e}"
        else:
            agent_ops_summary["reporting_to_other_agent"] = "Failed: Could not get or create ReportGenerationAgent."
            final_status = "error"; final_message="Critical error: Failed to obtain ReportGenerationAgent."

        return {"status": final_status, "agent": self.agent_name, "message": final_message,
                "ratios_from_skill": ratios_skill_payload,
                "text_summaries_generated": {
                    "financial_performance": shared_context.get_data("financial_performance_summary_llm"),
                    "key_risks": shared_context.get_data("key_risks_summary_llm"),
                    "overall_assessment": shared_context.get_data("overall_assessment_llm")
                },
                "detailed_operations_summary": agent_ops_summary}

# Main block for standalone testing (if needed) - content omitted for brevity in this overwrite.
if __name__ == '__main__':
    pass
