# {{agent_name}}.py
# Forged by AgentForge: {{timestamp}}
# Base Template: skill_based_agent_template

import logging
import json
from typing import Dict, Any, Optional, List

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext

class {{agent_name}}(Agent):
    """
    {{agent_description}}

    This agent primarily acts as a wrapper for a set of Semantic Kernel skills
    defined in its associated plugin ('{{skills_plugin_name}}'). It orchestrates
    calls to these skills based on the task description or specific inputs.
    """

    def __init__(self, kernel_service: KernelService, agent_config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_name="{{agent_name}}",
                         kernel_service=kernel_service,
                         skills_plugin_name="{{skills_plugin_name}}") # Crucial for this agent type
        self.config = agent_config if agent_config else {}
        # {{class_attributes_block}} # Placeholder

        if not self.skills_plugin_name:
            self.logger.error(f"CRITICAL: skills_plugin_name is not set for SkillBasedAgent '{self.agent_name}'. This agent will not function correctly.")

        self.logger.info(f"{{agent_name}} initialized. SK Plugin: '{self.skills_plugin_name}', Config: {self.config}")

    async def run(self, task_description: str, current_step_inputs: Dict[str, Any], shared_context: SharedContext) -> Dict[str, Any]:
        self.logger.info(f"'{self.agent_name}' received task: {task_description} with inputs: {current_step_inputs}")
        self.current_run_inputs = current_step_inputs

        # Determine which skill to run and prepare its inputs
        # This logic can be simple (e.g., a single skill) or complex (dynamic dispatch)
        # {{skill_dispatch_logic_block}} # Placeholder - AgentForge or dev must fill this

        # Example: Run a specific skill based on an input parameter or task_description
        skill_to_run = current_step_inputs.get("target_skill_name", "{{default_target_skill_name}}")
        sk_input_vars = current_step_inputs.get("skill_input_variables", {})

        # You might want to augment sk_input_vars with context or other inputs
        # sk_input_vars["task_description"] = task_description # Example

        if not skill_to_run:
            return {"status": "error", "message": "No target_skill_name provided or defaulted for SkillBasedAgent."}

        kernel = self.get_kernel()
        if not kernel:
            return {"status": "error", "message": "Semantic Kernel not available."}

        if not self.skills_plugin_name or not kernel.plugins.get(self.skills_plugin_name):
            return {"status": "error", "message": f"SK Plugin '{self.skills_plugin_name}' not found."}

        skill_function = kernel.plugins[self.skills_plugin_name].get(skill_to_run)
        if not skill_function:
            return {"status": "error", "message": f"Skill '{skill_to_run}' not found in plugin '{self.skills_plugin_name}'."}

        try:
            self.logger.info(f"Invoking SK skill: {self.skills_plugin_name}.{skill_to_run} with inputs: {sk_input_vars}")
            result = await kernel.invoke(skill_function, **sk_input_vars)
            skill_output = str(result) # Or process result.value, result.metadata etc. as needed

            # Attempt to parse if output is expected to be JSON
            # try_parse_json = current_step_inputs.get("parse_skill_output_as_json", False)
            # if try_parse_json:
            #     try:
            #         skill_output = json.loads(skill_output)
            #     except json.JSONDecodeError:
            #         self.logger.warning(f"Skill output for {skill_to_run} was not valid JSON, returning as string.")
            # {{skill_output_processing_block}} # Placeholder

            self.logger.info(f"'{self.agent_name}' - skill '{skill_to_run}' executed successfully.")
            return {"status": "success", "data": {"skill_name_executed": skill_to_run, "output": skill_output}}

        except Exception as e:
            self.logger.exception(f"Error during {self.agent_name} skill invocation '{skill_to_run}': {e}")
            return {"status": "error", "message": f"Error invoking skill '{skill_to_run}': {e}"}

    # {{helper_methods_block}} # Placeholder

# {{main_execution_block_placeholder}}
