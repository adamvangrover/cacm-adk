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
        self.logger.info(f"Operating with SharedContext ID: {shared_context.get_session_id()}")

        # Example: Simulate fetching data and updating shared context
        source_type = current_step_inputs.get("document_type", "generic_document")
        source_uri = current_step_inputs.get("document_uri", f"dummy_uri_for_{source_type}")
        document_id = current_step_inputs.get("document_id", source_type) # Use document_type if id is missing

        # Simulate processing and storing a reference
        processed_doc_path = f"processed/{document_id}.txt"
        shared_context.add_document_reference(doc_type=source_type, doc_uri=processed_doc_path)

        # Simulate storing some processed data snippet
        shared_context.set_data(f"{document_id}_content_snippet", "This is a snippet of processed content from the document.")
        shared_context.set_data("last_ingested_document_id", document_id)

        self.logger.info(f"'{self.agent_name}' completed task for source type: {source_type}. Shared context updated.")
        return {
            "status": "success",
            "agent": self.agent_name,
            "message": "Data ingestion placeholder completed, updated shared context.",
            "ingested_document_path": processed_doc_path,
            "document_id": document_id
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
