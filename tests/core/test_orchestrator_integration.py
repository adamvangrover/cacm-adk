#!/usr/bin/env python3
import unittest
import asyncio
import json
import os
import logging
from unittest.mock import patch, AsyncMock, MagicMock

from cacm_adk_core.orchestrator.orchestrator import Orchestrator
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.validator.validator import Validator

logging.basicConfig(level=logging.INFO) 
logger_main = logging.getLogger("TestOrchestratorIntegration")


class TestOrchestratorIntegration(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(os.path.dirname(self.current_dir)) 
        self.catalog_path = os.path.join(self.project_root, "config/compute_capability_catalog.json")
        
        if not os.path.exists(self.catalog_path):
            logger_main.warning(f"Main catalog not found at {self.catalog_path}, creating a minimal one for test setup.")
            os.makedirs(os.path.dirname(self.catalog_path), exist_ok=True)
            minimal_catalog_for_setup = {"computeCapabilities": []} 
            with open(self.catalog_path, 'w') as f:
                json.dump(minimal_catalog_for_setup, f, indent=2)
        
        self.kernel_service = KernelService() 
        
        self.mock_validator = MagicMock(spec=Validator)
        self.mock_validator.schema = True 
        self.mock_validator.validate_cacm_against_schema.return_value = (True, [])
        
        self.orchestrator = Orchestrator(
            kernel_service=self.kernel_service,
            validator=self.mock_validator, 
            catalog_filepath=self.catalog_path,
            load_catalog_on_init=True
        )
        self.orchestrator.logger = logger_main


    @patch('cacm_adk_core.agents.report_generation_agent.ReportGenerationAgent.receive_analysis_results', new_callable=AsyncMock)
    async def test_full_agent_workflow_with_skill(self, mock_receive_analysis_results_on_report_agent):
        sample_cacm = {
            "cacmId": "test-full-report-flow-001",
            "name": "Test Full Report Generation Workflow",
            "description": "Tests a 3-agent workflow: DataIngestion -> Analysis -> ReportGeneration.",
            "inputs": {
                "companyNameInput": {"type": "string", "value": "AlphaTech Innovations"},
                "companyTickerInput": {"type": "string", "value": "ATI"},
                "statementDataInput": { 
                    "type": "object", 
                    "value": { 
                        "current_assets": 800000.0, 
                        "current_liabilities": 250000.0, 
                        "total_debt": 450000.0, 
                        "total_equity": 950000.0,
                        "revenue": 3000000.0, "gross_profit": 1200000.0,
                        "net_income": 250000.0, "total_assets": 1800000.0
                    }
                },
                "mockFinancialsInput": {
                    "type": "object",
                    "value": {"revenue_y1": 2800000, "revenue_y2": 3000000, "net_income_y1": 200000, "net_income_y2": 250000, "currency": "USD", "period_y1_label":"FY2022", "period_y2_label":"FY2023"}
                },
                "riskFactorsFilePathInput": {"type": "string", "value": "./dummy_risk_factors.txt"},
                "reportRoundingPrecisionInput": {"type": "integer", "value": 3},
                "reportTitleDetailInput": {"type": "string", "value": "Q3 Comprehensive Credit Assessment"}
            },
            "outputs": { 
                "final_credit_report_text": {"type": "string", "description": "The fully assembled credit report text."},
                "final_report_filepath": {"type": "string", "description": "Conceptual path to the generated report file."},
                "ingestion_process_output": {"type": "object", "optional": True, "description": "Output from the ingestion step."},
                "analysis_process_output": {"type": "object", "optional": True, "description": "Output from the analysis step."},
                "final_analysis_output": {"type": "object", "optional": True, "description": "Direct ratio output from analysis agent."}
            },
            "workflow": [
                {
                    "stepId": "step_ingest_data",
                    "description": "Ingest all initial data.",
                    "computeCapabilityRef": "urn:adk:capability:standard_data_ingestor:v1",
                    "inputBindings": {
                        "companyName": "cacm.inputs.companyNameInput",
                        "companyTicker": "cacm.inputs.companyTickerInput",
                        "financialStatementData": "cacm.inputs.statementDataInput",
                        "mockStructuredFinancialsForLLMSummary": "cacm.inputs.mockFinancialsInput",
                        "riskFactorsFilePath": "cacm.inputs.riskFactorsFilePathInput"
                        # "fullFinancialStatementFilePath" could be bound here if we wanted to test that specific path for expanded data
                    },
                    "outputBindings": { 
                        "ingestion_summary": "cacm.outputs.ingestion_process_output"
                    }
                },
                {
                    "stepId": "step_analyze_data",
                    "description": "Perform financial analysis.",
                    "computeCapabilityRef": "urn:adk:capability:financial_analysis_agent:v1",
                    "inputBindings": { 
                        "roundingPrecision": "cacm.inputs.reportRoundingPrecisionInput"
                    },
                    "outputBindings": {
                        "ratios_from_skill": "cacm.outputs.final_analysis_output",
                        "message": "cacm.outputs.analysis_process_output"
                    }
                },
                {
                    "stepId": "step_generate_report",
                    "description": "Generate the final credit report.",
                    "computeCapabilityRef": "urn:adk:capability:standard_report_generator:v1",
                    "inputBindings": { 
                         "report_title_detail": "cacm.inputs.reportTitleDetailInput"
                    },
                    "outputBindings": {
                        "generated_report_text": "cacm.outputs.final_credit_report_text",
                        "report_file_path": "cacm.outputs.final_report_filepath"
                    }
                }
            ]
        }

        success, logs, outputs = await self.orchestrator.run_cacm(sample_cacm)
        
        logger_main.info(f"\nDEBUG INTEGRATION TEST: Orchestrator Logs:\n{'---'.join(logs)}\n")
        logger_main.info(f"\nDEBUG INTEGRATION TEST: Final CACM Outputs:\n{json.dumps(outputs, indent=2)}\n")

        self.assertTrue(success, f"Orchestrator run_cacm failed for the full workflow. Logs: \n{'---'.join(logs)}")
        
        self.assertIn("ingestion_process_output", outputs) 
        ingestion_value = outputs["ingestion_process_output"].get("value", {})
        self.assertIsNotNone(ingestion_value, "ingestion_process_output value is None.")
        self.assertIn("financial_data_for_ratios_expanded", ingestion_value.get("attempted_to_store_keys", [])) # Changed from stored_keys_in_shared_context

        self.assertIn("analysis_process_output", outputs) 
        self.assertIsNotNone(outputs["analysis_process_output"].get("value"))
        self.assertIsInstance(outputs["analysis_process_output"]["value"], str)

        self.assertIn("final_analysis_output", outputs, "final_analysis_output (bound from ratios_from_skill) key missing.")
        self.assertIsNotNone(outputs["final_analysis_output"].get("value"))
        ratios_data_from_output = outputs["final_analysis_output"]["value"]
        self.assertIn("calculated_ratios", ratios_data_from_output)
        self.assertEqual(ratios_data_from_output["calculated_ratios"]["current_ratio"], 3.2) 
        self.assertEqual(ratios_data_from_output["calculated_ratios"]["debt_to_equity_ratio"], 0.474) 
        self.assertEqual(ratios_data_from_output["calculated_ratios"]["gross_profit_margin"], 40.0)
        self.assertEqual(ratios_data_from_output["calculated_ratios"]["net_profit_margin"], 8.333)
        self.assertEqual(ratios_data_from_output["calculated_ratios"]["return_on_assets_ROA"], 13.889)
        self.assertEqual(ratios_data_from_output["calculated_ratios"]["return_on_equity_ROE"], 26.316)
        self.assertEqual(ratios_data_from_output["calculated_ratios"]["debt_ratio"], 0.25)

        self.assertIn("final_credit_report_text", outputs, "Final credit report text key missing in outputs.")
        report_output_dict = outputs["final_credit_report_text"]
        self.assertIsNotNone(report_output_dict.get("value"))
        report_text_value = report_output_dict["value"]
        
        self.assertIn("**Company Name:** AlphaTech Innovations", report_text_value)
        self.assertIn("**Ticker:** ATI", report_text_value)
        self.assertIn("- **Current Ratio:** 3.2", report_text_value) 
        self.assertIn("- **Debt To Equity Ratio:** 0.474", report_text_value) 
        self.assertIn("- **Gross Profit Margin:** 40.0", report_text_value)
        self.assertIn("- **Net Profit Margin:** 8.333", report_text_value)
        self.assertIn("- **Return On Assets Roa:** 13.889", report_text_value)
        self.assertIn("- **Return On Equity Roe:** 26.316", report_text_value)
        self.assertIn("- **Debt Ratio:** 0.25", report_text_value)
        
        self.assertIn("[LLM Placeholder: Financial Performance Summary. Inputs: Y1 Revenue 2800000 USD", report_text_value)
        self.assertIn("[LLM Placeholder: Key Risks Summary. Input text started with: 'Sample risk factors text from conceptual file. Compe'. Actual LLM output would be here.]", report_text_value)
        self.assertIn("[LLM Placeholder: Overall Assessment. Based on Ratios", report_text_value)
        
        self.assertIn("final_report_filepath", outputs)
        filepath_output = outputs["final_report_filepath"].get("value")
        self.assertIsInstance(filepath_output, str)
        self.assertTrue(filepath_output.startswith("./output_artifacts/final_machine_reports/generated_report_"))
        self.assertTrue(filepath_output.endswith(".md"))
        
        mock_receive_analysis_results_on_report_agent.assert_called_once()
        called_kwargs = mock_receive_analysis_results_on_report_agent.call_args.kwargs
        self.assertEqual(called_kwargs.get('sending_agent_name'), "AnalysisAgent")
        received_results_to_report_agent = called_kwargs.get('results')
        self.assertIsNotNone(received_results_to_report_agent)
        self.assertIn("ratios_payload", received_results_to_report_agent) 
        self.assertIsNotNone(received_results_to_report_agent["ratios_payload"])
        self.assertEqual(received_results_to_report_agent["ratios_payload"]["calculated_ratios"]["current_ratio"], 3.2)

if __name__ == '__main__':
    unittest.main()
