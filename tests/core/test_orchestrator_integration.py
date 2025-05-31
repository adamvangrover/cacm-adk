#!/usr/bin/env python3
import unittest
import asyncio
import json
import os
import logging
from unittest.mock import patch, AsyncMock, MagicMock # Added MagicMock

from cacm_adk_core.orchestrator.orchestrator import Orchestrator
from cacm_adk_core.semantic_kernel_adapter import KernelService
# SharedContext is implicitly tested via Orchestrator and Agents
# from cacm_adk_core.context.shared_context import SharedContext 
from cacm_adk_core.validator.validator import Validator # Orchestrator needs a validator

# Disable verbose logging from components during tests unless specifically needed
logging.disable(logging.CRITICAL)
# Re-enable for this module if specific logs are needed for debugging tests
# logging.getLogger('__main__').disabled = False # If running this file directly
# logging.getLogger('cacm_adk_core.orchestrator.orchestrator').disabled = False
# logging.getLogger('agent').disabled = False # For all agents if needed


class TestOrchestratorIntegration(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Ensure the catalog path is correct relative to project root
        # Assuming tests are run from project root, or PYTHONPATH handles cacm_adk_core
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        # Adjust path to go up from tests/core to the project root where config/ is
        self.project_root = os.path.dirname(os.path.dirname(self.current_dir)) 
        self.catalog_path = os.path.join(self.project_root, "config/compute_capability_catalog.json")
        
        # Ensure the catalog exists for the test
        if not os.path.exists(self.catalog_path):
            # Create a minimal catalog if it's missing, just for this test to run
            # This is a fallback, ideally the catalog is maintained properly
            logging.warning(f"Test Catalog not found at {self.catalog_path}, creating a minimal one for test.")
            os.makedirs(os.path.dirname(self.catalog_path), exist_ok=True)
            minimal_catalog = {
                "computeCapabilities": [
                    {
                        "id": "urn:adk:capability:basic_document_ingestor:v1",
                        "name": "Basic Document Ingestor (Agent)",
                        "description": "Ingests a document and updates shared context.",
                        "agent_type": "DataIngestionAgent",
                        "inputs": [
                            {"name": "document_type", "type": "string"},
                            {"name": "document_id", "type": "string"}
                        ],
                        "outputs": [{"name": "ingestion_outcome", "type": "object"}]
                    },
                    {
                        "id": "urn:adk:capability:financial_ratios_calculator:v1",
                        "name": "Financial Ratios Calculator (Agent Enabled)",
                        "description": "Calculates key financial ratios using an agent.",
                        "agent_type": "AnalysisAgent",
                        "task_details_from_capability": "Perform basic financial ratio analysis.",
                        "skill_plugin_name": "FinancialAnalysis",
                        "skill_function_name": "calculate_basic_ratios",
                        "inputs": [
                            {"name": "financialStatementData", "type": "object"},
                            {"name": "roundingPrecision", "type": "integer", "optional": True}
                        ],
                        "outputs": [{"name": "ratios_from_skill", "type": "object"}]
                    }
                ]
            }
            with open(self.catalog_path, 'w') as f:
                json.dump(minimal_catalog, f, indent=2)
        
        self.kernel_service = KernelService() # Real KernelService
        
        # Orchestrator requires a validator. For integration test, can use a real one or a mock.
        # Using a mock validator that always validates successfully for simplicity here.
        self.mock_validator = MagicMock(spec=Validator)
        self.mock_validator.schema = True # Indicate schema is "loaded"
        self.mock_validator.validate_cacm_against_schema.return_value = (True, [])
        
        self.orchestrator = Orchestrator(
            kernel_service=self.kernel_service,
            validator=self.mock_validator, # Use mock validator
            catalog_filepath=self.catalog_path,
            load_catalog_on_init=True
        )
        # Assign a logger to orchestrator if it uses self.logger and doesn't init its own
        self.orchestrator.logger = logging.getLogger("TestOrchestrator")


    @patch('cacm_adk_core.agents.report_generation_agent.ReportGenerationAgent.receive_analysis_results', new_callable=AsyncMock)
    async def test_full_agent_workflow_with_skill(self, mock_receive_analysis):
        # This sample_cacm now defines the full 3-agent workflow
        sample_cacm = {
            "cacmId": "test-full-report-flow-001",
            "name": "Test Full Report Generation Workflow",
            "description": "Tests a 3-agent workflow: DataIngestion -> Analysis -> ReportGeneration.",
            "inputs": {
                "companyNameInput": {"type": "string", "value": "MegaCorp Inc."},
                "companyTickerInput": {"type": "string", "value": "MCORP"},
                "statementDataInput": { # For DataIngestionAgent, which then puts it into SharedContext for AnalysisAgent
                    "type": "object", 
                    "value": {"currentAssets": 750000, "currentLiabilities": 300000, "totalDebt": 500000, "totalEquity": 900000}
                },
                "mockFinancialsInput": { # For DataIngestionAgent
                    "type": "object",
                    "value": {"revenue_y1": 2000000, "revenue_y2": 2500000, "net_income_y1": 100000, "net_income_y2": 150000, "currency": "USD"}
                },
                "riskTextDataInput": { # For DataIngestionAgent
                    "type": "string",
                    "value": "Market competition is fierce. Regulatory changes are anticipated. Supply chain stability is a concern."
                },
                "reportRoundingPrecisionInput": {"type": "integer", "value": 2}, # For AnalysisAgent step
                "reportTitleDetailInput": {"type": "string", "value": "Q3 Financial Health Assessment"} # For ReportGenerationAgent step
            },
            "outputs": {
                "final_credit_report": {"type": "string", "description": "The fully assembled credit report."},
                "ingestion_process_output": {"type": "object", "optional": True, "description": "Output from the ingestion step."},
                "analysis_process_output": {"type": "object", "optional": True, "description": "Output from the analysis step."}
            },
            "workflow": [
                {
                    "stepId": "step_ingest_data",
                    "description": "Ingest initial company and financial data.",
                    "computeCapabilityRef": "urn:adk:capability:standard_data_ingestor:v1",
                    "inputBindings": {
                        "companyName": "cacm.inputs.companyNameInput",
                        "companyTicker": "cacm.inputs.companyTickerInput",
                        "financialStatementData": "cacm.inputs.statementDataInput", # This will be stored by DataIngestionAgent
                        "mockStructuredFinancialsForLLMSummary": "cacm.inputs.mockFinancialsInput",
                        "riskFactorsText": "cacm.inputs.riskTextDataInput"
                    },
                    "outputBindings": { 
                        # DataIngestionAgent returns dict with "status", "message", "stored_keys_in_shared_context"
                        "ingestion_summary": "cacm.outputs.ingestion_process_output"
                    }
                },
                {
                    "stepId": "step_analyze_data",
                    "description": "Perform financial analysis including ratio calculation and textual summaries.",
                    "computeCapabilityRef": "urn:adk:capability:financial_analysis_agent:v1",
                    "inputBindings": { # AnalysisAgent now takes roundingPrecision directly
                        "rounding_precision": "cacm.inputs.reportRoundingPrecisionInput"
                        # Other data for analysis is pulled from SharedContext by the agent
                    },
                    "outputBindings": {
                        # AnalysisAgent returns dict with "status", "message", "ratios_from_skill", "text_summaries_generated", etc.
                        "analysis_summary_output": "cacm.outputs.analysis_process_output"
                    }
                },
                {
                    "stepId": "step_generate_report",
                    "description": "Generate the final credit report.",
                    "computeCapabilityRef": "urn:adk:capability:standard_report_generator:v1",
                    "inputBindings": { # ReportGenerationAgent takes report_title_detail directly
                         "report_title_detail": "cacm.inputs.reportTitleDetailInput"
                    }, # It primarily uses SharedContext for content
                    "outputBindings": {
                        "final_report_text": "cacm.outputs.final_credit_report"
                    }
                }
            ]
        }

        success, logs, outputs = await self.orchestrator.run_cacm(sample_cacm)
        
        # Print logs for debugging if test fails
        # print("\n--- Orchestrator Logs for Integration Test ---")
        # for log_entry in logs:
        #     print(log_entry)
        # print("--- End of Logs ---")
        
        # Critical Debug: Print the actual outputs received by the test method
        print(f"\nDEBUG: Outputs received in test_full_agent_workflow_with_skill:\n{json.dumps(outputs, indent=2)}\n")

        self.assertTrue(success, "Orchestrator run_cacm failed for the full workflow.")
        
        # Verify ingestion output (optional, as it mainly writes to context)
        self.assertIn("ingestion_process_output", outputs) # Matches CACM "outputs" key
        self.assertIsNotNone(outputs["ingestion_process_output"].get("value"))
        # DataIngestionAgent returns "stored_keys_in_shared_context" in its main dict,
        # and the binding is for "ingestion_summary" which is the whole dict.
        self.assertIn("company_name", outputs["ingestion_process_output"]["value"].get("stored_keys_in_shared_context", []))

        # Verify analysis output (optional for specific details, main check is the final report)
        self.assertIn("analysis_process_output", outputs) # Matches CACM "outputs" key
        self.assertIsNotNone(outputs["analysis_process_output"].get("value"))
        # AnalysisAgent returns "ratios_from_skill" in its main dict.
        # The binding is for "analysis_summary_output" which is the whole dict from agent.
        self.assertIn("ratios_from_skill", outputs["analysis_process_output"]["value"])
        self.assertIsNotNone(outputs["analysis_process_output"]["value"]["ratios_from_skill"])
        self.assertEqual(outputs["analysis_process_output"]["value"]["ratios_from_skill"]["calculated_ratios"]["current_ratio"], 2.5) # 750k/300k

        # Main verification: the final report from ReportGenerationAgent
        self.assertIn("final_credit_report", outputs, "Final credit report key missing in outputs.")
        report_text = outputs["final_credit_report"].get("value")
        self.assertIsNotNone(report_text, "Generated report text is None.")
        
        self.assertIn("Company Name: MegaCorp Inc.", report_text)
        self.assertIn("Ticker: MCORP", report_text)
        # Ratios based on new input: 750000/300000=2.5, 500000/900000=0.555 -> 0.56 (default rounding is 2 in skill)
        # The reportRoundingPrecisionInput is 2, so AnalysisAgent should use it.
        self.assertIn("Current Ratio: 2.5", report_text) 
        self.assertIn("Debt-to-Equity Ratio: 0.56", report_text) 
        
        # Check for placeholder summaries (as SK_MDNA_SummarizerSkill is a placeholder)
        self.assertIn("[Placeholder LLM Summary: Content would be generated here based on provided input.]", report_text)
        
        # Check if ReportGenerationAgent's receive_analysis_results was called by AnalysisAgent
        mock_receive_analysis.assert_called_once()
        called_kwargs = mock_receive_analysis.call_args.kwargs
        self.assertEqual(called_kwargs.get('sending_agent_name'), "AnalysisAgent")
        received_results_to_report_agent = called_kwargs.get('results')
        self.assertIsNotNone(received_results_to_report_agent)
        self.assertIn("ratios_payload", received_results_to_report_agent) 
        self.assertIsNotNone(received_results_to_report_agent["ratios_payload"])
        self.assertEqual(received_results_to_report_agent["ratios_payload"]["calculated_ratios"]["current_ratio"], 2.5)


if __name__ == '__main__':
    # Need to run with asyncio test runner if using IsolatedAsyncioTestCase directly
    # Typically run via `python -m unittest discover tests`
    unittest.main()
