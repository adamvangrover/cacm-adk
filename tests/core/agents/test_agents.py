#!/usr/bin/env python3
import unittest
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel import Kernel

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.agents.analysis_agent import AnalysisAgent
from cacm_adk_core.agents.report_generation_agent import ReportGenerationAgent
from cacm_adk_core.context.shared_context import SharedContext

logging.basicConfig(level=logging.INFO)


class SimpleMockKernelService:
    def __init__(self):
        self._kernel = MagicMock(spec=Kernel)
        self._kernel.plugins = MagicMock()
        self.logger = logging.getLogger("SimpleMockKernelService")

    def get_kernel(self) -> Kernel:
        return self._kernel


class ConcreteTestAgent(Agent):
    async def run(
        self,
        task_description: str,
        current_step_inputs: Dict,
        shared_context: SharedContext,
    ) -> Dict:
        self.logger.info(f"ConcreteTestAgent running task: {task_description}")
        return {"status": "success", "message": "ConcreteTestAgent executed"}


class TestBaseAgent(unittest.IsolatedAsyncioTestCase):
    async def test_agent_initialization(self):
        agent = ConcreteTestAgent(
            agent_name="TestAgent", kernel_service=SimpleMockKernelService()
        )
        self.assertEqual(agent.agent_name, "TestAgent")

    async def test_set_agent_manager(self):
        agent = ConcreteTestAgent(
            agent_name="TestAgent", kernel_service=SimpleMockKernelService()
        )
        agent.set_agent_manager(MagicMock())
        self.assertIsNotNone(agent.agent_manager)

    async def test_get_or_create_agent(self):
        requesting_agent = ConcreteTestAgent(
            agent_name="RequestingAgent", kernel_service=SimpleMockKernelService()
        )
        mock_manager = MagicMock()
        mock_manager.get_or_create_agent_instance = AsyncMock(
            return_value="mock_target"
        )
        requesting_agent.set_agent_manager(mock_manager)
        target = await requesting_agent.get_or_create_agent(
            "Target", context_data={"k": "v"}
        )
        self.assertEqual(target, "mock_target")
        mock_manager.get_or_create_agent_instance.assert_called_with(
            "Target", context_data_for_creation={"k": "v"}
        )


class TestAnalysisAgent(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.maxDiff = None
        self.mock_kernel_service = SimpleMockKernelService()
        self.mock_kernel = self.mock_kernel_service.get_kernel()

        self.mock_fin_plugin = MagicMock(spec_set=["get"])
        self.mock_ratio_func = MagicMock(name="MockRatioFunc")
        self.mock_report_plugin = MagicMock(spec_set=["get"])
        self.mock_summ_func = MagicMock(name="MockSummarizeFunc")

        def get_plugin(key):
            if key == "FinancialAnalysis":
                return self.mock_fin_plugin
            if key == "ReportingAnalysisSkills":
                return self.mock_report_plugin
            return None  # Or raise KeyError to be stricter

        self.mock_kernel.plugins.get.side_effect = get_plugin
        self.mock_kernel.plugins.__getitem__.side_effect = (
            get_plugin  # For base_agent.get_plugin
        )

        self.mock_fin_plugin.get.return_value = self.mock_ratio_func
        self.mock_report_plugin.get.return_value = (
            self.mock_summ_func
        )  # All report skills point to one mock

        self.analysis_agent = AnalysisAgent(self.mock_kernel_service)
        self.shared_context = SharedContext("test_cacm")
        self.analysis_agent.set_agent_manager(
            AsyncMock()
        )  # Basic mock for agent_manager

    async def test_run_successful_full_analysis(self):
        self.shared_context.set_data(
            "financial_data_for_ratios_expanded", {"current_assets": 100}
        )
        self.shared_context.set_data(
            "structured_financials_for_summary", {"revenue": 100}
        )
        self.shared_context.set_data("risk_factors_section_text", "risk text")

        ratio_payload = {"calculated_ratios": {"current_ratio": 2.0}, "errors": []}
        summary_payload = "[Generated Summary]"
        self.mock_kernel.invoke.side_effect = [
            MagicMock(spec=FunctionResult, value=ratio_payload),
            MagicMock(spec=FunctionResult, value=summary_payload),  # Fin Summary
            MagicMock(spec=FunctionResult, value=summary_payload),  # Risk Summary
            MagicMock(spec=FunctionResult, value=summary_payload),  # Overall Assess
        ]
        result = await self.analysis_agent.run("task", {}, self.shared_context)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Analysis phase completed successfully.")
        self.assertEqual(self.mock_kernel.invoke.call_count, 4)  # Ratio + 3 summaries
        self.assertEqual(result["ratios_from_skill"], ratio_payload)

    async def test_run_kernel_not_available(self):
        self.analysis_agent.kernel_service.get_kernel = MagicMock(return_value=None)
        result = await self.analysis_agent.run("task", {}, self.shared_context)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "Failed: Kernel not available.")

    async def test_run_ratio_plugin_not_found(self):
        self.shared_context.set_data(
            "financial_data_for_ratios_expanded", {"current_assets": 1}
        )
        self.mock_kernel.plugins.get.side_effect = lambda key: (
            self.mock_report_plugin if key == "ReportingAnalysisSkills" else None
        )

        result = await self.analysis_agent.run("task", {}, self.shared_context)
        self.assertEqual(result["status"], "error")
        self.assertEqual(
            result["message"], "Error: Plugin 'FinancialAnalysis' not found."
        )

    async def test_run_ratio_function_not_found(self):
        self.shared_context.set_data(
            "financial_data_for_ratios_expanded", {"current_assets": 1}
        )
        self.mock_fin_plugin.get.return_value = None  # Ratio function not found

        result = await self.analysis_agent.run("task", {}, self.shared_context)
        self.assertEqual(result["status"], "error")
        self.assertEqual(
            result["message"], "Error: 'calculate_basic_ratios' function not found."
        )

    async def test_run_ratio_skill_invocation_exception(self):
        self.shared_context.set_data(
            "financial_data_for_ratios_expanded", {"current_assets": 1}
        )

        async def invoke_side_effect(func, args):
            if func == self.mock_ratio_func:
                raise Exception("Ratio Boom!")
            return MagicMock(spec=FunctionResult, value="summary")

        self.mock_kernel.invoke.side_effect = invoke_side_effect

        result = await self.analysis_agent.run("task", {}, self.shared_context)
        self.assertEqual(result["status"], "error")
        self.assertEqual(
            result["message"],
            "Error invoking 'calculate_basic_ratios' skill: Ratio Boom!",
        )

    async def test_run_summarization_plugin_not_found(self):
        self.shared_context.set_data(
            "financial_data_for_ratios_expanded", {"current_assets": 1}
        )  # Ratio part will run
        self.mock_kernel.plugins.get.side_effect = lambda key: (
            self.mock_fin_plugin if key == "FinancialAnalysis" else None
        )  # ReportingAnalysisSkills not found

        # Ratio skill needs a mock return value for this path
        ratio_payload = {"calculated_ratios": {"current_ratio": 2.0}, "errors": []}
        self.mock_kernel.invoke.return_value = MagicMock(
            spec=FunctionResult, value=ratio_payload
        )

        result = await self.analysis_agent.run("task", {}, self.shared_context)
        self.assertEqual(
            result["status"], "warning"
        )  # Warning because summarization was skipped
        self.assertEqual(
            result["message"], "Analysis completed with summarization plugin not found."
        )
        self.mock_kernel.invoke.assert_called_once()  # Only ratio skill called


if __name__ == "__main__":
    unittest.main()
