import logging
from typing import Dict, Any # Added Any

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext # Added

# logger = logging.getLogger(__name__) # Will use instance logger

class DataIngestionAgent(Agent):
    """
    Agent responsible for handling data ingestion tasks.
    """
    def __init__(self, kernel_service: KernelService):
        """
        Initializes the DataIngestionAgent.

        Args:
            kernel_service (KernelService): The service providing access to the Semantic Kernel.
        """
        super().__init__(agent_name="DataIngestionAgent", kernel_service=kernel_service)

    async def run(self, task_description: str, current_step_inputs: Dict[str, Any], shared_context: SharedContext) -> Dict[str, Any]:
        """
        Executes the data ingestion task.

        Args:
            task_description (str): Description of the data ingestion task.
            current_step_inputs (Dict[str, Any]): Inputs for this step (e.g., source configuration).
            shared_context (SharedContext): The shared context object.

        Returns:
            Dict[str, Any]: Results of the execution, including status.
        """
        self.logger.info(f"'{self.agent_name}' received task: {task_description} with inputs: {current_step_inputs}")
        self.logger.info(f"Operating with SharedContext ID: {shared_context.get_session_id()} (CACM ID: {shared_context.get_cacm_id()})")

        company_name = current_step_inputs.get("companyName")
        company_ticker = current_step_inputs.get("companyTicker")
        mock_financials_for_summary = current_step_inputs.get("mockStructuredFinancialsForLLMSummary")
        risk_factors_text_input = current_step_inputs.get("riskFactorsText")
        # Note: The input key for ratios is "financialStatementData" in the CACM template for AnalysisAgent,
        # but "financial_data_for_ratios" is the key used in SharedContext.
        # The DataIngestionAgent will receive it as "financialStatementData" if that's what the CACM input is named.
        financial_data_for_ratios_input = current_step_inputs.get("financialStatementData")

        stored_keys_list = []

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

        if mock_financials_for_summary is not None:
            shared_context.set_data("structured_financials_for_summary", mock_financials_for_summary)
            self.logger.info(f"Stored structured_financials_for_summary: {mock_financials_for_summary}")
            stored_keys_list.append("structured_financials_for_summary")
        else:
            self.logger.warning("mockStructuredFinancialsForLLMSummary not found in current_step_inputs.")

        if risk_factors_text_input is not None:
            shared_context.set_data("risk_factors_section_text", risk_factors_text_input)
            self.logger.info("Stored risk_factors_section_text (content length: {}).".format(len(risk_factors_text_input)))
            stored_keys_list.append("risk_factors_section_text")
        else:
            self.logger.warning("riskFactorsText not found in current_step_inputs.")

        if financial_data_for_ratios_input is not None:
            # This will be stored under "financial_data_for_ratios" for AnalysisAgent to pick up
            shared_context.set_data("financial_data_for_ratios", financial_data_for_ratios_input)
            self.logger.info(f"Stored financial_data_for_ratios: {financial_data_for_ratios_input}")
            stored_keys_list.append("financial_data_for_ratios")
        else:
            self.logger.warning("financialStatementData (for ratios) not found in current_step_inputs.")

        # Example of adding a document reference if a URI was provided
        # This part adapts the previous placeholder logic for document references
        doc_uri_input = current_step_inputs.get("documentURI") # Assuming a CACM input like "documentURI"
        doc_type_input = current_step_inputs.get("documentType", "GeneralDocument") # Default if not specified
        if doc_uri_input:
            shared_context.add_document_reference(doc_type=doc_type_input, doc_uri=doc_uri_input)
            self.logger.info(f"Added document reference to shared context: Type='{doc_type_input}', URI='{doc_uri_input}'")
            stored_keys_list.append(f"doc_ref_{doc_type_input}")


        self.logger.info(f"'{self.agent_name}' completed data ingestion. Shared context updated with specified keys.")
        return {
            "status": "success",
            "agent": self.agent_name,
            "message": "Data ingested from inputs and stored in SharedContext.",
            "stored_keys_in_shared_context": stored_keys_list
        }

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    from semantic_kernel import Kernel # For MockKernelService

    class MockKernelService(KernelService): # Simplified from base_agent's test
        def __init__(self): self._kernel = Kernel(); logging.info("MockKernelService initialized.")
        def get_kernel(self): return self._kernel
        def _initialize_kernel(self): pass


    mock_service = MockKernelService()
    data_agent = DataIngestionAgent(kernel_service=mock_service)
    mock_shared_context = SharedContext(cacm_id="test_data_ingestion_cacm")

    import asyncio
    async def test_run():
        result = await data_agent.run(
            task_description="Ingest a 10K filing.",
            current_step_inputs={"document_type": "10K_FILING", "document_id": "XYZ_10K_2023"},
            shared_context=mock_shared_context
        )
        logging.info(f"DataIngestionAgent run result: {result}")
        mock_shared_context.log_context_summary() # Check context state

    asyncio.run(test_run())
