#!/usr/bin/env python3
import unittest
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any # Added Dict here

# Assuming KernelArguments and FunctionResult are correctly located for the SK version
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel import Kernel # For Kernel type hint

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.agents.analysis_agent import AnalysisAgent
# from cacm_adk_core.agents.data_ingestion_agent import DataIngestionAgent # If testing it too
from cacm_adk_core.agents.report_generation_agent import ReportGenerationAgent
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext

# Disable verbose logging from agents during tests unless specifically needed
# logging.disable(logging.CRITICAL) # Keep logs for debugging for now
logging.basicConfig(level=logging.DEBUG)


# Simpler MockKernelService that doesn't inherit but provides the interface
class SimpleMockKernelService:
    def __init__(self):
        self._kernel = MagicMock(spec=Kernel)
        self._kernel.plugins = MagicMock() # This is critical for AnalysisAgent tests
        self.logger = logging.getLogger("SimpleMockKernelService")
        self.logger.info("SimpleMockKernelService initialized for testing.")

    def get_kernel(self) -> Kernel:
        return self._kernel

# A concrete Agent for testing base class functionality
class ConcreteTestAgent(Agent):
    async def run(self, task_description: str, current_step_inputs: Dict, shared_context: SharedContext) -> Dict:
        # Minimal implementation for testing base class features
        self.logger.info(f"ConcreteTestAgent running task: {task_description}")
        return {"status": "success", "message": "ConcreteTestAgent executed"}


class TestBaseAgent(unittest.IsolatedAsyncioTestCase):

    async def test_agent_initialization(self):
        mock_kernel_service = SimpleMockKernelService()
        agent = ConcreteTestAgent(agent_name="TestAgent", kernel_service=mock_kernel_service, skills_plugin_name="TestPlugin")
        self.assertEqual(agent.agent_name, "TestAgent")
        self.assertEqual(agent.kernel_service, mock_kernel_service)
        self.assertEqual(agent.skills_plugin_name, "TestPlugin")
        self.assertIsNone(agent.agent_manager)

    async def test_set_agent_manager(self):
        mock_kernel_service = SimpleMockKernelService()
        agent = ConcreteTestAgent(agent_name="TestAgent", kernel_service=mock_kernel_service)
        mock_manager = MagicMock() # Mock Orchestrator
        agent.set_agent_manager(mock_manager)
        self.assertEqual(agent.agent_manager, mock_manager)

    async def test_get_or_create_agent(self):
        mock_kernel_service = SimpleMockKernelService()
        requesting_agent = ConcreteTestAgent(agent_name="RequestingAgent", kernel_service=mock_kernel_service)

        # Case 1: Agent manager not set
        result_no_manager = await requesting_agent.get_or_create_agent("TargetAgent")
        self.assertIsNone(result_no_manager)

        # Case 2: Agent manager is set
        mock_agent_manager = MagicMock()
        mock_agent_manager.get_or_create_agent_instance = AsyncMock(return_value="mock_target_agent_instance")
        requesting_agent.set_agent_manager(mock_agent_manager)

        target_agent = await requesting_agent.get_or_create_agent("TargetAgent", context_data={"key": "value"})
        self.assertEqual(target_agent, "mock_target_agent_instance")
        mock_agent_manager.get_or_create_agent_instance.assert_called_once_with(
            "TargetAgent", context_data_for_creation={"key": "value"}
        )


class TestAnalysisAgent(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_kernel_service = SimpleMockKernelService() # Use the simpler mock
        self.mock_kernel = self.mock_kernel_service.get_kernel()

        # Ensure plugins attribute on the kernel mock is correctly set up for __getitem__
        self.mock_financial_analysis_plugin = MagicMock()
        self.mock_calculate_ratios_function = MagicMock() # This will be the KernelFunctionMetadata mock

        # Configure plugin access: kernel.plugins['PluginName']['FunctionName']
        # In SK v1+, plugins is a KernelPluginCollection, which acts like a dict.
        # We mock its __getitem__ to return our plugin mock.
        self.mock_kernel.plugins.__getitem__.side_effect = lambda key: {
            "FinancialAnalysis": self.mock_financial_analysis_plugin
        }.get(key)

        # Configure function access on the plugin mock
        self.mock_financial_analysis_plugin.__getitem__.side_effect = lambda key: {
            "calculate_basic_ratios": self.mock_calculate_ratios_function
        }.get(key)
        # Also handle .get() if the agent uses it
        self.mock_financial_analysis_plugin.get.side_effect = lambda key: {
             "calculate_basic_ratios": self.mock_calculate_ratios_function
        }.get(key)


        self.analysis_agent = AnalysisAgent(kernel_service=self.mock_kernel_service)
        self.shared_context = SharedContext(cacm_id="test_analysis_cacm")

        # Mock agent manager for inter-agent communication
        self.mock_agent_manager = MagicMock()
        self.mock_report_agent_instance = AsyncMock(spec=ReportGenerationAgent) # Mock the agent instance
        self.mock_agent_manager.get_or_create_agent_instance = AsyncMock(return_value=self.mock_report_agent_instance)
        self.analysis_agent.set_agent_manager(self.mock_agent_manager)


    async def test_run_successful_skill_invocation(self):
        expected_skill_output_dict = {"calculated_ratios": {"current_ratio": 2.0}, "errors": []}
        # The skill's invoke returns a FunctionResult, which has a 'value' attribute
        mock_function_result = MagicMock(spec=FunctionResult)
        mock_function_result.value = expected_skill_output_dict

        self.mock_kernel.invoke = AsyncMock(return_value=mock_function_result)

        current_step_inputs = {
            "financial_data": {"current_assets": 1000, "current_liabilities": 500}, # Corrected key
            "rounding_precision": 2 # Corrected key
        }

        result = await self.analysis_agent.run("calculate basic ratios", current_step_inputs, self.shared_context)

        self.mock_kernel.invoke.assert_called_once()
        # Check args passed to invoke. The first arg is the function, second is KernelArguments
        call_args = self.mock_kernel.invoke.call_args
        self.assertEqual(call_args[0][0], self.mock_calculate_ratios_function)
        kernel_args_passed = call_args[0][1]
        self.assertIsInstance(kernel_args_passed, KernelArguments)
        self.assertEqual(kernel_args_passed["financial_data"], current_step_inputs["financial_data"]) # Corrected key
        self.assertEqual(kernel_args_passed["rounding_precision"], current_step_inputs["rounding_precision"]) # Corrected key

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["ratios_from_skill"], expected_skill_output_dict)

        # Verify call to ReportGenerationAgent
        self.mock_agent_manager.get_or_create_agent_instance.assert_called_with(
            "ReportGenerationAgent",
            context_data_for_creation=unittest.mock.ANY # Corrected: parameter name is context_data_for_creation
        )
        self.mock_report_agent_instance.receive_analysis_results.assert_called_once()


    async def test_run_kernel_not_available(self):
        self.analysis_agent.kernel_service.get_kernel = MagicMock(return_value=None) # KernelService returns no kernel
        result = await self.analysis_agent.run("task", {}, self.shared_context)
        self.assertEqual(result["status"], "error") # Or based on how it handles this
        self.assertIn("Kernel not available", result["message"])
        # Ensure skill invocation was not attempted, but call to ReportGenerationAgent might still occur
        self.mock_kernel.invoke.assert_not_called()

    async def test_run_skill_plugin_not_found(self):
        self.mock_kernel.plugins.__getitem__.side_effect = KeyError("FinancialAnalysis") # Simulate plugin not found by raising KeyError for that specific plugin

        current_step_inputs = {"financial_data": {"current_assets": 1000, "current_liabilities": 500}} # Corrected key

        result = await self.analysis_agent.run("task requesting FinancialAnalysis", current_step_inputs, self.shared_context)

        self.assertEqual(result["status"], "error")
        self.assertIn("Plugin 'FinancialAnalysis' not found", result["message"]) # Message from agent
        self.mock_kernel.invoke.assert_not_called()


    async def test_run_skill_function_not_found(self):
        # Temporarily override the side_effect for 'get' on the specific plugin mock
        # to ensure it returns None for 'calculate_basic_ratios'
        original_side_effect = self.mock_financial_analysis_plugin.get.side_effect
        self.mock_financial_analysis_plugin.get.side_effect = lambda key: None if key == "calculate_basic_ratios" else original_side_effect(key)

        current_step_inputs = {"financial_data": {"current_assets": 1000, "current_liabilities": 500}}
        result = await self.analysis_agent.run("task asking for basic ratios", current_step_inputs, self.shared_context)

        self.mock_financial_analysis_plugin.get.assert_called_with("calculate_basic_ratios")
        self.assertEqual(result["status"], "error")
        self.assertIn("'calculate_basic_ratios' function not found", result["message"])
        self.mock_kernel.invoke.assert_not_called()

        # Restore original side_effect if other tests in the same class instance might rely on it
        self.mock_financial_analysis_plugin.get.side_effect = original_side_effect

    async def test_run_skill_invocation_exception(self):
        self.mock_kernel.invoke = AsyncMock(side_effect=Exception("Skill execution failed!"))

        current_step_inputs = {"financial_data": {"current_assets": 1000, "current_liabilities": 500}} # Corrected key
        result = await self.analysis_agent.run("task", current_step_inputs, self.shared_context)

        self.assertEqual(result["status"], "error")
        self.assertIn("Error invoking skill: Skill execution failed!", result["message"])
        # It should still attempt to call report agent if an error occurs during skill invocation
        self.mock_report_agent_instance.receive_analysis_results.assert_called_once()

if __name__ == '__main__':
    unittest.main()
