import logging
from typing import Dict, Any, Optional  # Added Optional

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import (
    KernelService,
)  # Not directly used, but good for consistency
from cacm_adk_core.context.shared_context import SharedContext


class DataIngestionAgent(Agent):
    """
    Agent responsible for handling data ingestion tasks,
    conceptually reading from files or taking direct inputs,
    and populating SharedContext.
    """

    def __init__(self, kernel_service: KernelService):
        super().__init__(agent_name="DataIngestionAgent", kernel_service=kernel_service)

    def _read_file_content_or_default(
        self, file_path: Optional[str], default_value: Any, data_type: str = "text"
    ) -> Any:
        """
        Conceptually reads content from a file path or returns a default value.

        In its current implementation, this method simulates file reading by returning
        hardcoded sample data based on the `data_type` if `file_path` is provided.
        If `file_path` is None or empty, it returns `default_value`.
        This method is intended to be replaced with actual file I/O in a production setting.

        Args:
            file_path (Optional[str]): The actual path to the file.
            default_value (Any): The value to return if file_path is not provided or an error occurs.
            data_type (str): A string indicating the type of data (e.g., "text", "json"). Only "text" is fully supported for actual reading now.

        Returns:
            Any: The file content (string for text) or the default_value.
        """
        if not file_path:
            return default_value

        try:
            # Assuming files are UTF-8 encoded text files for now.
            # For JSON, we'd use json.load(f) after opening.
            # This agent part needs to align with how actual file paths are resolved (e.g., relative to project root).
            # For now, assume file_path is directly usable.
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.logger.info(f"Successfully read content from file: {file_path}")
            return content
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            return default_value
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return default_value

    async def run(
        self,
        task_description: str,
        current_step_inputs: Dict[str, Any],
        shared_context: SharedContext,
    ) -> Dict[str, Any]:
        """
        Ingests various types of data into SharedContext based on inputs.

        This agent processes several optional inputs from `current_step_inputs`.
        For inputs that specify file paths (e.g., `riskFactorsFilePath`), it uses
        the `_read_file_content_or_default` method to conceptually load data.
        Direct data inputs (e.g., `riskFactorsText`) can also be provided and
        are often used as fallbacks if file paths are not given.

        The ingested data is stored in `SharedContext` under specific keys for
        downstream agents to use.

        Args:
            task_description (str): Description of the ingestion task.
            current_step_inputs (Dict[str, Any]): Optional inputs, including:
                - "companyName" (str): Company name.
                - "companyTicker" (str): Company ticker.
                - "riskFactorsFilePath" (str): Conceptual path to risk factors text file.
                - "riskFactorsText" (str): Direct risk factors text.
                - "mockFinancialsFilePath" (str): Conceptual path to mock financials JSON.
                - "mockStructuredFinancialsForLLMSummary" (dict): Direct mock financials.
                  (Used for 'business_overview_text' in ReportGenerationAgent via SharedContext key 'structured_financials_for_summary')
                - "fullFinancialStatementFilePath" (str): Conceptual path to expanded financials.
                - "financialStatementData" (dict): Direct basic or expanded financials.
            shared_context (SharedContext): The context where ingested data will be stored.

        Returns:
            Dict[str, Any]: A dictionary summarizing the ingestion operation:
                - {"ingestion_summary": {
                      "status": "success",
                      "agent": self.agent_name,
                      "message": "Data ingestion processed...",
                      "attempted_to_store_keys": List[str]
                  }}
        """
        self.logger.info(
            f"'{self.agent_name}' received task: {task_description} with inputs: {current_step_inputs}"
        )
        self.logger.info(
            f"Operating with SharedContext ID: {shared_context.get_session_id()} (CACM ID: {shared_context.get_cacm_id()})"
        )

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
            data_type="risk_text",
        )
        if risk_text_from_file:
            shared_context.set_data("risk_factors_section_text", risk_text_from_file)
            self.logger.info(
                f"Stored risk_factors_section_text (length: {len(risk_text_from_file)}). Source: {'file' if current_step_inputs.get('riskFactorsFilePath') else 'direct input'}."
            )
            stored_keys_list.append("risk_factors_section_text")
        else:
            self.logger.warning("riskFactorsText not found in inputs or file path.")

        # Mock Structured Financials for LLM Summary (file path or direct)
        mock_financials_from_file = self._read_file_content_or_default(
            current_step_inputs.get("mockFinancialsFilePath"),
            current_step_inputs.get("mockStructuredFinancialsForLLMSummary"),
            data_type="mock_financials_json",
        )
        if mock_financials_from_file:
            shared_context.set_data(
                "structured_financials_for_summary", mock_financials_from_file
            )
            self.logger.info(
                f"Stored structured_financials_for_summary. Source: {'file' if current_step_inputs.get('mockFinancialsFilePath') else 'direct input'}."
            )
            stored_keys_list.append("structured_financials_for_summary")
        else:
            self.logger.warning(
                "mockStructuredFinancialsForLLMSummary not found in inputs or file path."
            )

        # Expanded Financial Data for Ratios (file path or direct)
        # This will be stored under "financial_data_for_ratios_expanded"
        # The old "financial_data_for_ratios" might still be populated if "financialStatementData" is directly provided
        # and "fullFinancialStatementFilePath" is not.

        expanded_financial_data = self._read_file_content_or_default(
            current_step_inputs.get("fullFinancialStatementFilePath"),
            current_step_inputs.get(
                "financialStatementData"
            ),  # Fallback to direct data if path not given
            data_type="expanded_financials_json",
        )

        # If fallback was used (direct financialStatementData) and it's not the conceptual file version,
        # check if it has the new expanded keys. If not, provide a default expanded structure.
        if (
            isinstance(expanded_financial_data, dict)
            and expanded_financial_data.get("source") != "file_conceptual"
            and not all(
                k in expanded_financial_data
                for k in ["revenue", "gross_profit", "net_income", "total_assets"]
            )
        ):
            self.logger.warning(
                "Fallback financialStatementData does not have the full expanded structure. Using a default expanded structure for ratios, preserving original basic ratio keys if present."
            )
            default_expanded_structure = {
                "current_assets": expanded_financial_data.get("current_assets", 0.0),
                "current_liabilities": expanded_financial_data.get(
                    "current_liabilities", 0.0
                ),
                "total_debt": expanded_financial_data.get("total_debt", 0.0),
                "total_equity": expanded_financial_data.get(
                    "total_equity", 1.0
                ),  # Avoid div by zero if possible
                "revenue": 2000000.0,
                "gross_profit": 800000.0,  # Default new fields
                "net_income": 100000.0,
                "total_assets": 1200000.0,
                "source": "default_expanded_fallback",
            }
            expanded_financial_data = default_expanded_structure

        if expanded_financial_data:
            shared_context.set_data(
                "financial_data_for_ratios_expanded", expanded_financial_data
            )
            self.logger.info(
                f"Stored financial_data_for_ratios_expanded. Source: {'file' if current_step_inputs.get('fullFinancialStatementFilePath') else ('direct_input_or_default_expanded')}."
            )
            stored_keys_list.append("financial_data_for_ratios_expanded")
        else:
            self.logger.warning(
                "financial_data_for_ratios_expanded (from file/input) not found."
            )

        # For backward compatibility or simpler tests, also store the basic ratio data if provided directly
        # under the old key, if `financial_data_for_ratios_expanded` wasn't populated from a specific file for it.
        # This helps if AnalysisAgent is not yet updated to use "financial_data_for_ratios_expanded".
        # However, the plan is to update AnalysisAgent, so this might become less relevant.
        # For now, if financialStatementData was provided directly and no specific expanded file path,
        # also store it under the old key.
        if not current_step_inputs.get(
            "fullFinancialStatementFilePath"
        ) and current_step_inputs.get("financialStatementData"):
            if (
                "financial_data_for_ratios" not in stored_keys_list
            ):  # Avoid double storing if already handled by expansion
                shared_context.set_data(
                    "financial_data_for_ratios",
                    current_step_inputs.get("financialStatementData"),
                )
                self.logger.info(
                    "Stored direct financialStatementData under 'financial_data_for_ratios' for basic ratio compatibility."
                )
                stored_keys_list.append("financial_data_for_ratios (compat)")

        # Process text_files_to_ingest
        text_files_to_ingest = current_step_inputs.get("text_files_to_ingest")
        if isinstance(text_files_to_ingest, list):
            for file_item in text_files_to_ingest:
                if isinstance(file_item, dict):
                    file_path = file_item.get("file_path")
                    context_key = file_item.get("context_key")
                    if file_path and context_key:
                        # Use the updated _read_file_content_or_default for actual file reading
                        content = self._read_file_content_or_default(
                            file_path, default_value=None, data_type="text"
                        )
                        if content is not None:
                            shared_context.set_data(context_key, content)
                            self.logger.info(
                                f"Stored content from '{file_path}' into SharedContext key '{context_key}'."
                            )
                            stored_keys_list.append(context_key)
                        else:
                            self.logger.warning(
                                f"Failed to read or content was empty for file '{file_path}' specified in text_files_to_ingest."
                            )
                    else:
                        self.logger.warning(
                            f"Invalid item in text_files_to_ingest (missing file_path or context_key): {file_item}"
                        )
                else:
                    self.logger.warning(
                        f"Invalid item type in text_files_to_ingest (expected dict): {file_item}"
                    )
        elif text_files_to_ingest is not None:  # If it exists but is not a list
            self.logger.warning(
                f"text_files_to_ingest parameter was provided but is not a list: {text_files_to_ingest}"
            )

        self.logger.info(
            f"'{self.agent_name}' completed data ingestion. Shared context updated."
        )
        return {
            "ingestion_summary": {  # To match integration test output binding
                "status": "success",
                "agent": self.agent_name,
                "message": "Data ingestion processed; see logs and SharedContext for details.",
                "attempted_to_store_keys": stored_keys_list,
            }
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from semantic_kernel import Kernel

    class MockKernelService(KernelService):
        def __init__(self):
            self._kernel = Kernel()
            logging.info("MockKernelService initialized.")

        def get_kernel(self):
            return self._kernel

        def _initialize_kernel(self):
            pass

    mock_service = MockKernelService()
    data_agent = DataIngestionAgent(kernel_service=mock_service)
    mock_shared_context = SharedContext(cacm_id="test_data_ingestion_cacm")

    import asyncio

    async def test_run():
        inputs_direct = {
            "companyName": "DirectCorp",
            "companyTicker": "DCORP",
            "financialStatementData": {
                "current_assets": 100.0,
                "current_liabilities": 50.0,
            },  # Old structure
            "mockStructuredFinancialsForLLMSummary": {"revenue_y1": 1000},
            "riskFactorsText": "Direct risk text.",
        }
        print("\n--- Testing with Direct Data Inputs ---")
        result_direct = await data_agent.run(
            "Ingest direct data.", inputs_direct, mock_shared_context
        )
        logging.info(
            f"DataIngestionAgent (direct) result: {json.dumps(result_direct, indent=2)}"
        )
        mock_shared_context.log_context_summary()

        inputs_file_paths = {
            "companyName": "FileCorp",
            "companyTicker": "FCORP",
            "riskFactorsFilePath": "conceptual_risks.txt",
            "mockFinancialsFilePath": "conceptual_mock_financials.json",
            "fullFinancialStatementFilePath": "conceptual_expanded_financials.json",
        }
        print("\n--- Testing with File Path Inputs (Conceptual) ---")
        # Create a new context for the second run or clear relevant parts of the old one
        mock_shared_context_file = SharedContext(
            cacm_id="test_data_ingestion_file_cacm"
        )
        result_file = await data_agent.run(
            "Ingest from file paths.", inputs_file_paths, mock_shared_context_file
        )
        logging.info(
            f"DataIngestionAgent (file) result: {json.dumps(result_file, indent=2)}"
        )
        mock_shared_context_file.log_context_summary()

    asyncio.run(test_run())
