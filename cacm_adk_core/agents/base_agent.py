import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, TYPE_CHECKING, Any  # Added Any

from semantic_kernel import Kernel

# Assuming KernelService provides get_kernel() that returns a Kernel instance
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext  # Added

if TYPE_CHECKING:
    from cacm_adk_core.orchestrator.orchestrator import Orchestrator  # For type hinting

logger = logging.getLogger(__name__)  # This is module-level logger


class Agent(ABC):
    """
    Abstract base class for all agents in the system.
    """

    def __init__(
        self,
        agent_name: str,
        kernel_service: KernelService,
        skills_plugin_name: Optional[str] = None,
    ):
        """
        Initializes the base agent.

        Args:
            agent_name (str): The name of the agent.
            kernel_service (KernelService): The service providing access to the Semantic Kernel.
            skills_plugin_name (Optional[str]): The default plugin name this agent might use for its skills.
        """
        self.agent_name = agent_name
        self.kernel_service = kernel_service
        self.skills_plugin_name = skills_plugin_name
        self.agent_manager: Optional["Orchestrator"] = None  # Added
        self.logger = logging.getLogger(
            f"agent.{self.agent_name}"
        )  # Per-instance logger
        self.logger.info(
            f"Agent '{self.agent_name}' created. Associated skill plugin: {self.skills_plugin_name if self.skills_plugin_name else 'N/A'}"
        )

    def set_agent_manager(self, manager: "Orchestrator"):
        """
        Sets the agent manager (Orchestrator) for this agent.
        """
        self.agent_manager = manager
        self.logger.info(f"Agent manager set for '{self.agent_name}'.")

    async def get_or_create_agent(
        self, agent_name_key: str, context_data: Optional[Dict[str, any]] = None
    ) -> Optional["Agent"]:
        """
        Requests an instance of another agent from the agent manager.
        """
        self.logger.info(
            f"'{self.agent_name}' is requesting agent '{agent_name_key}' with context: {context_data if context_data else 'None'}"
        )
        if not self.agent_manager:
            self.logger.error(
                "Agent manager not set. Cannot get or create other agents."
            )
            return None

        # Ensure context_data is a dictionary if None was passed
        context_data_for_creation = context_data if context_data is not None else {}

        try:
            # The method in Orchestrator is get_or_create_agent_instance
            agent_instance = await self.agent_manager.get_or_create_agent_instance(
                agent_name_key, context_data_for_creation=context_data_for_creation
            )
            if agent_instance:
                self.logger.info(
                    f"Successfully obtained instance of '{agent_name_key}'."
                )
            else:
                self.logger.warning(f"Failed to obtain instance of '{agent_name_key}'.")
            return agent_instance
        except Exception as e:
            self.logger.error(
                f"Error while trying to get/create agent '{agent_name_key}': {e}",
                exc_info=True,
            )
            return None

    def get_kernel(self) -> Kernel:
        """
        Retrieves the Semantic Kernel instance.

        Returns:
            Kernel: The Semantic Kernel instance.
        """
        return self.kernel_service.get_kernel()

    def get_plugin(
        self, plugin_name: str
    ):  # -> Optional[KernelPlugin]: Type hint KernelPlugin if available
        """
        Helper to get a plugin from the kernel.
        Note: The exact return type KernelPlugin might depend on SK version specifics.
        For now, using 'any' or relying on duck typing if KernelPlugin is not easily importable.
        """
        kernel = self.get_kernel()
        if kernel and kernel.plugins:
            try:
                return kernel.plugins[plugin_name]
            except KeyError:
                logger.warning(
                    f"Plugin '{plugin_name}' not found in kernel for agent '{self.agent_name}'."
                )
                return None
        logger.warning(
            f"Kernel or plugins collection not available for agent '{self.agent_name}'."
        )
        return None

    @abstractmethod
    async def run(
        self,
        task_description: str,
        current_step_inputs: Dict[str, Any],
        shared_context: SharedContext,
    ) -> Dict[str, Any]:
        """
        The main execution logic for the agent.

        Args:
            task_description (str): A description of the task the agent needs to perform.
            current_step_inputs (Dict[str, Any]): Inputs specific to this execution step, resolved by the orchestrator.
            shared_context (SharedContext): The shared context object for this CACM run.

        Returns:
            Dict[str, Any]: A dictionary containing the results of the agent's execution.
                           Should include at least a 'status' field.
        """
        pass


if __name__ == "__main__":
    # This is a conceptual test.
    # In a real scenario, you'd need a mock KernelService or a running instance.
    logging.basicConfig(level=logging.INFO)

    class MockKernelService(KernelService):
        def __init__(self):
            self._kernel = Kernel()  # Minimal Kernel for testing
            logger.info("MockKernelService initialized.")

        def get_kernel(self):
            return self._kernel

        # Add a dummy _initialize_kernel if the parent expects it
        def _initialize_kernel(self):
            logger.info("MockKernelService _initialize_kernel called (dummy).")
            # Normally this would setup OpenAI, plugins etc.
            # For this test, we just need a Kernel object.
            # Let's simulate adding a dummy plugin for get_plugin test
            # from semantic_kernel.kernel_plugin import KernelPlugin
            # self._kernel.plugins.add(KernelPlugin(name="TestPlugin")) # Example

    mock_service = MockKernelService()

    class TestAgent(Agent):
        def __init__(self, kernel_service: KernelService):
            super().__init__(
                "TestAgent", kernel_service, skills_plugin_name="TestPlugin"
            )

        async def run(
            self,
            task_description: str,
            current_step_inputs: Dict[str, Any],
            shared_context: SharedContext,
        ) -> Dict[str, Any]:
            self.logger.info(
                f"{self.agent_name} received task: {task_description} with inputs: {current_step_inputs}"
            )  # Use self.logger
            self.logger.info(
                f"Operating with SharedContext ID: {shared_context.get_session_id()}"
            )
            kernel = self.get_kernel()
            self.logger.info(
                f"Kernel instance obtained in TestAgent: {type(kernel)}"
            )  # Use self.logger

            # Test getting its own plugin
            plugin = self.get_plugin(self.skills_plugin_name)
            if plugin:
                logger.info(
                    f"Successfully retrieved plugin '{self.skills_plugin_name}' for {self.agent_name}."
                )
            else:
                logger.warning(
                    f"Could not retrieve plugin '{self.skills_plugin_name}' for {self.agent_name}."
                )

            return {
                "status": "success",
                "message": "TestAgent executed",
                "agent": self.agent_name,
            }

    test_agent = TestAgent(mock_service)

    import asyncio

    async def main():
        # For this test, create a dummy SharedContext
        mock_shared_context = SharedContext(cacm_id="test_agent_run_cacm_base")
        result = await test_agent.run(
            "Perform a test operation.", {"input_data": "sample"}, mock_shared_context
        )
        logger.info(
            f"TestAgent run result: {result}"
        )  # Use global logger or TestAgent's logger for this line if preferred.

    asyncio.run(main())
