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
        sample_cacm = {
            "cacmId": "integration_test_workflow_001",
            "name": "Integration Test: Data Ingestion -> Analysis (with Skill) -> Report (mocked)",
            "description": "Tests a multi-step workflow involving agents and a native skill.",
            "inputs": {
                "doc_type_input": {"value": "PRESS_RELEASE", "description": "Type of document to ingest."},
                "doc_id_input": {"value": "PR_XYZ_Q1_2024", "description": "ID of document to ingest."},
                "financial_data_input": { # This key is used by cacm.inputs.financial_data_input
                    "value": {
                        "current_assets": 2500.0, "current_liabilities": 1250.0, # Expected CR = 2.0
                        "total_debt": 1000.0, "total_equity": 2000.0      # Expected D/E = 0.5
                    },
                    "description": "Financial data for analysis."
                },
                "precision_input": {"value": 2, "description": "Rounding precision for ratios."} # Used by cacm.inputs.precision_input
            },
            "outputs": { # These are the formal output keys of the CACM itself
                "ingestion_report_output": {"type": "object", "description": "Output from data ingestion."},
                "final_analysis_output": {"type": "object", "description": "Ratios calculated by the AnalysisAgent."}
            },
            "workflow": [
                {
                    "stepId": "step_ingest_data",
                    "description": "Ingest a press release.",
                    "computeCapabilityRef": "urn:adk:capability:basic_document_ingestor:v1",
                    "inputBindings": {
                        "document_type": "cacm.inputs.doc_type_input",
                        "document_id": "cacm.inputs.doc_id_input"
                    },
                    "outputBindings": {
                        "ingested_document_path": "cacm.outputs.ingestion_report_output"
                    }
                },
                {
                    "stepId": "step_analyze_data",
                    "description": "Analyze financial data using the skill-enabled AnalysisAgent.",
                    "computeCapabilityRef": "urn:adk:capability:financial_ratios_calculator:v1",
                    "inputBindings": {
                        "financial_data": "cacm.inputs.financial_data_input",
                        "rounding_precision": "cacm.inputs.precision_input"
                    },
                    "outputBindings": {
                        "ratios_from_skill": "cacm.outputs.final_analysis_output" # Binding to the CACM's declared output key
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

        self.assertTrue(success, "Orchestrator run_cacm failed.")

        self.assertIn("ingestion_report_output", outputs, "Ingestion report key missing in outputs.")
        self.assertIsNotNone(outputs["ingestion_report_output"]["value"], "Ingestion report value is None.")
        self.assertIn("processed/PR_XYZ_Q1_2024.txt", outputs["ingestion_report_output"]["value"])


        self.assertIn("final_analysis_output", outputs, "Final analysis output key missing in outputs.")
        final_ratios_value = outputs["final_analysis_output"]["value"] # This is the content of "ratios_from_skill"
        self.assertIsNotNone(final_ratios_value, "Final analysis output value is None.")

        self.assertIn("calculated_ratios", final_ratios_value)
        self.assertEqual(final_ratios_value["calculated_ratios"]["current_ratio"], 2.0)
        self.assertEqual(final_ratios_value["calculated_ratios"]["debt_to_equity_ratio"], 0.5)
        self.assertEqual(len(final_ratios_value.get("errors", [])), 0, "Skill reported errors in calculation.")

        # Check if ReportGenerationAgent's receive_analysis_results was called by AnalysisAgent
        mock_receive_analysis.assert_called_once()
        # Access keyword arguments from the mock's call_args
        called_kwargs = mock_receive_analysis.call_args.kwargs
        self.assertEqual(called_kwargs.get('sending_agent_name'), "AnalysisAgent")
        received_results_to_report_agent = called_kwargs.get('results')
        self.assertIsNotNone(received_results_to_report_agent, "Results kwarg not found in call to receive_analysis_results")
        self.assertIn("skill_direct_payload", received_results_to_report_agent)
        self.assertEqual(received_results_to_report_agent["skill_direct_payload"], final_ratios_value)


if __name__ == '__main__':
    # Need to run with asyncio test runner if using IsolatedAsyncioTestCase directly
    # Typically run via `python -m unittest discover tests`
    unittest.main()
