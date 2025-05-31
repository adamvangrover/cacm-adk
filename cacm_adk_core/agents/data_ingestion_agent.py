import logging
from typing import Dict, Any, Optional # Added Optional

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService # Not directly used, but good for consistency
from cacm_adk_core.context.shared_context import SharedContext


class DataIngestionAgent(Agent):
    """
    Agent responsible for handling data ingestion tasks,
    conceptually reading from files or taking direct inputs,
    and populating SharedContext.
    """
    def __init__(self, kernel_service: KernelService):
        super().__init__(agent_name="DataIngestionAgent", kernel_service=kernel_service)

    def _read_file_content_or_default(self, file_path: Optional[str], default_value: Any, data_type: str = "text") -> Any:
        if file_path:
            self.logger.info(f"Conceptually reading {data_type} data from file: {file_path}")
            # In a real scenario, actual file reading and parsing would happen here.
            if data_type == "risk_text":
                return "Sample risk factors text from conceptual file. Competition remains a key challenge. Market volatility could impact performance."
            elif data_type == "mock_financials_json":
                return {"source": "file_conceptual", "revenue_y1": 2100000, "revenue_y2": 2600000, "net_income_y1": 110000, "net_income_y2": 160000, "currency": "USD", "period_y1_label": "FY2022-File", "period_y2_label": "FY2023-File"}
            elif data_type == "expanded_financials_json":
                # This structure includes all keys expected by the enhanced FinancialAnalysisSkill
                return {
                    "source": "file_conceptual",
                    "current_assets": 760000.0, "current_liabilities": 310000.0,
                    "total_debt": 510000.0, "total_equity": 910000.0,
                    "revenue": 2600000.0, "gross_profit": 1000000.0,
                    "net_income": 160000.0, "total_assets": 1500000.0
                }
            self.logger.warning(f"Unknown data_type '{data_type}' for conceptual file read. Returning default.")
            return default_value
        return default_value

    async def run(self, task_description: str, current_step_inputs: Dict[str, Any], shared_context: SharedContext) -> Dict[str, Any]:
        self.logger.info(f"'{self.agent_name}' received task: {task_description} with inputs: {current_step_inputs}")
        self.logger.info(f"Operating with SharedContext ID: {shared_context.get_session_id()} (CACM ID: {shared_context.get_cacm_id()})")

        stored_keys_list = []

        # Company Info (direct from inputs)
        company_name = current_step_inputs.get("companyName")
        company_ticker = current_step_inputs.get("companyTicker")

        if company_name is not None:
            shared_context.set_data("company_name", company_name)
            self.logger.info(f"Stored company_name: {company_name}")
            stored_keys_list.append("company_name")
        else:
            self.logger.warning("companyName not found in current_step_inputs.")

        if company_ticker is not None:
            shared_context.set_data("company_ticker", company_ticker)
            self.logger.info(f"Stored company_ticker: {company_ticker}")
            stored_keys_list.append("company_ticker")
        else:
            self.logger.warning("companyTicker not found in current_step_inputs.")

        # Risk Factors Text (file path or direct)
        risk_text_from_file = self._read_file_content_or_default(
            current_step_inputs.get("riskFactorsFilePath"),
            current_step_inputs.get("riskFactorsText"),
            data_type="risk_text"
        )
        if risk_text_from_file:
            shared_context.set_data("risk_factors_section_text", risk_text_from_file)
            self.logger.info(f"Stored risk_factors_section_text (length: {len(risk_text_from_file)}). Source: {'file' if current_step_inputs.get('riskFactorsFilePath') else 'direct input'}.")
            stored_keys_list.append("risk_factors_section_text")
        else:
            self.logger.warning("riskFactorsText not found in inputs or file path.")

        # Mock Structured Financials for LLM Summary (file path or direct)
        mock_financials_from_file = self._read_file_content_or_default(
            current_step_inputs.get("mockFinancialsFilePath"),
            current_step_inputs.get("mockStructuredFinancialsForLLMSummary"),
            data_type="mock_financials_json"
        )
        if mock_financials_from_file:
            shared_context.set_data("structured_financials_for_summary", mock_financials_from_file)
            self.logger.info(f"Stored structured_financials_for_summary. Source: {'file' if current_step_inputs.get('mockFinancialsFilePath') else 'direct input'}.")
            stored_keys_list.append("structured_financials_for_summary")
        else:
            self.logger.warning("mockStructuredFinancialsForLLMSummary not found in inputs or file path.")

        # Expanded Financial Data for Ratios (file path or direct)
        # This will be stored under "financial_data_for_ratios_expanded"
        # The old "financial_data_for_ratios" might still be populated if "financialStatementData" is directly provided
        # and "fullFinancialStatementFilePath" is not.

        expanded_financial_data = self._read_file_content_or_default(
            current_step_inputs.get("fullFinancialStatementFilePath"),
            current_step_inputs.get("financialStatementData"), # Fallback to direct data if path not given
            data_type="expanded_financials_json"
        )

        # If fallback was used (direct financialStatementData) and it's not the conceptual file version,
        # check if it has the new expanded keys. If not, provide a default expanded structure.
        if isinstance(expanded_financial_data, dict) and \
           expanded_financial_data.get("source") != "file_conceptual" and \
           not all(k in expanded_financial_data for k in ["revenue", "gross_profit", "net_income", "total_assets"]):
            self.logger.warning("Fallback financialStatementData does not have the full expanded structure. Using a default expanded structure for ratios, preserving original basic ratio keys if present.")
            default_expanded_structure = {
                "current_assets": expanded_financial_data.get("current_assets", 0.0),
                "current_liabilities": expanded_financial_data.get("current_liabilities", 0.0),
                "total_debt": expanded_financial_data.get("total_debt", 0.0),
                "total_equity": expanded_financial_data.get("total_equity", 1.0), # Avoid div by zero if possible
                "revenue": 2000000.0, "gross_profit": 800000.0, # Default new fields
                "net_income": 100000.0, "total_assets": 1200000.0,
                "source": "default_expanded_fallback"
            }
            expanded_financial_data = default_expanded_structure

        if expanded_financial_data:
            shared_context.set_data("financial_data_for_ratios_expanded", expanded_financial_data)
            self.logger.info(f"Stored financial_data_for_ratios_expanded. Source: {'file' if current_step_inputs.get('fullFinancialStatementFilePath') else ('direct_input_or_default_expanded')}.")
            stored_keys_list.append("financial_data_for_ratios_expanded")
        else:
            self.logger.warning("financial_data_for_ratios_expanded (from file/input) not found.")

        # For backward compatibility or simpler tests, also store the basic ratio data if provided directly
        # under the old key, if `financial_data_for_ratios_expanded` wasn't populated from a specific file for it.
        # This helps if AnalysisAgent is not yet updated to use "financial_data_for_ratios_expanded".
        # However, the plan is to update AnalysisAgent, so this might become less relevant.
        # For now, if financialStatementData was provided directly and no specific expanded file path,
        # also store it under the old key.
        if not current_step_inputs.get("fullFinancialStatementFilePath") and current_step_inputs.get("financialStatementData"):
            if "financial_data_for_ratios" not in stored_keys_list: # Avoid double storing if already handled by expansion
                 shared_context.set_data("financial_data_for_ratios", current_step_inputs.get("financialStatementData"))
                 self.logger.info("Stored direct financialStatementData under 'financial_data_for_ratios' for basic ratio compatibility.")
                 stored_keys_list.append("financial_data_for_ratios (compat)")


        self.logger.info(f"'{self.agent_name}' completed data ingestion. Shared context updated.")
        return {
            "ingestion_summary": { # To match integration test output binding
                "status": "success",
                "agent": self.agent_name,
                "message": "Data ingestion processed; see logs and SharedContext for details.",
                "attempted_to_store_keys": stored_keys_list
            }
        }

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    from semantic_kernel import Kernel

    class MockKernelService(KernelService):
        def __init__(self): self._kernel = Kernel(); logging.info("MockKernelService initialized.")
        def get_kernel(self): return self._kernel
        def _initialize_kernel(self): pass

    mock_service = MockKernelService()
    data_agent = DataIngestionAgent(kernel_service=mock_service)
    mock_shared_context = SharedContext(cacm_id="test_data_ingestion_cacm")

    import asyncio
    async def test_run():
        inputs_direct = {
            "companyName": "DirectCorp",
            "companyTicker": "DCORP",
            "financialStatementData": {"current_assets": 100.0, "current_liabilities": 50.0}, # Old structure
            "mockStructuredFinancialsForLLMSummary": {"revenue_y1": 1000},
            "riskFactorsText": "Direct risk text."
        }
        print("\n--- Testing with Direct Data Inputs ---")
        result_direct = await data_agent.run("Ingest direct data.", inputs_direct, mock_shared_context)
        logging.info(f"DataIngestionAgent (direct) result: {json.dumps(result_direct, indent=2)}")
        mock_shared_context.log_context_summary()

        inputs_file_paths = {
            "companyName": "FileCorp",
            "companyTicker": "FCORP",
            "riskFactorsFilePath": "conceptual_risks.txt",
            "mockFinancialsFilePath": "conceptual_mock_financials.json",
            "fullFinancialStatementFilePath": "conceptual_expanded_financials.json"
        }
        print("\n--- Testing with File Path Inputs (Conceptual) ---")
        # Create a new context for the second run or clear relevant parts of the old one
        mock_shared_context_file = SharedContext(cacm_id="test_data_ingestion_file_cacm")
        result_file = await data_agent.run("Ingest from file paths.", inputs_file_paths, mock_shared_context_file)
        logging.info(f"DataIngestionAgent (file) result: {json.dumps(result_file, indent=2)}")
        mock_shared_context_file.log_context_summary()

    asyncio.run(test_run())
