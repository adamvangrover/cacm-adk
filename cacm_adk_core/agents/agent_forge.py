# cacm_adk_core/agents/agent_forge.py
import logging
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
# import importlib # Not used in refactored version
# import yaml # Not used in refactored version
import json # For loading/saving registry and snippets

# Define project root structure for robust path defaults
AGENT_FORGE_DIR = os.path.dirname(os.path.abspath(__file__))
CACM_ADK_CORE_DIR = os.path.dirname(AGENT_FORGE_DIR)
PROJECT_ROOT = os.path.dirname(CACM_ADK_CORE_DIR)

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext
# from core.utils.config_utils import load_config, save_config # Removed, registry handled differently


class AgentForge(Agent):
    """
    A meta-agent for the Adam v18.0 ecosystem, responsible for the dynamic
    creation, modification suggestion, and requirements analysis for other agents.

    It uses a set of Adam v18.0-specific templates and (conceptually) Semantic Kernel
    skills (`AgentForgeSkills`) to perform its tasks. Key functionalities include:
    - Listing available Adam v18.0 agent templates.
    - Retrieving the content of specific templates.
    - Creating new agents: Generates agent code from a template and specification,
      creates a dedicated directory with supporting files (capability snippet, README),
      and registers metadata in `config/adam_v18_forged_agents_registry.json`.
    - Suggesting code modifications for existing agents based on natural language.
    - Analyzing natural language requirements to propose specifications for new agents.
    """

    def __init__(self, kernel_service: KernelService, agent_config: Optional[Dict[str, Any]] = None):
        """
        Initializes the AgentForge.

        Args:
            kernel_service (KernelService): The service providing access to Semantic Kernel.
            agent_config (Optional[Dict[str, Any]]): Configuration dictionary. Expected keys:
                - "template_dir" (str, optional): Path to the directory containing Adam v18.0
                  agent templates. Defaults to `cacm_adk_core/agents/templates/adam_v18/`.
                - "forged_agents_registry_path" (str, optional): Path to the JSON file
                  for storing metadata of forged agents. Defaults to
                  `config/adam_v18_forged_agents_registry.json` in the project root.
                - "forged_agents_base_dir" (str, optional): Base directory where new forged agents
                  and their supporting files will be created. Defaults to
                  `cacm_adk_core/agents/forged/` in the project root.
        """
        super().__init__(agent_name="AgentForge",
                         kernel_service=kernel_service,
                         skills_plugin_name="AgentForgeSkills")
        self.config = agent_config if agent_config else {}

        # Using module-level PROJECT_ROOT for robust default path construction
        default_template_dir = os.path.join(AGENT_FORGE_DIR, "templates", "adam_v18")
        self.template_dir = Path(self.config.get("template_dir", default_template_dir))

        default_registry_path = os.path.join(PROJECT_ROOT, "config", "adam_v18_forged_agents_registry.json")
        self.forged_agents_registry_path = Path(self.config.get("forged_agents_registry_path", default_registry_path))

        default_forged_agents_base_dir = os.path.join(CACM_ADK_CORE_DIR, "agents", "forged") # For storing new agents
        self.forged_agents_base_dir = Path(self.config.get("forged_agents_base_dir", default_forged_agents_base_dir))

        self.logger.info(f"AgentForge initialized. Adam v18 Template dir: {self.template_dir}, Adam v18 Registry: {self.forged_agents_registry_path}, Forged Agents Base Dir: {self.forged_agents_base_dir}")


    async def run(self, task_description: str, current_step_inputs: Dict[str, Any], shared_context: SharedContext) -> Dict[str, Any]:
        """
        Executes a specific action for AgentForge based on inputs.

        The `action` key in `current_step_inputs` determines the operation.

        Supported Actions & their `current_step_inputs`:
        - "list_templates":
            - No specific inputs needed beyond `action`.
            - Returns: `{"status": "success", "data": {"templates": List[str]}}`
        - "get_template_content":
            - "template_name" (str): Name of the template (without .py.tpl extension).
            - Returns: `{"status": "success", "data": {"template_name": str, "content": str}}`
                       or error if not found.
        - "create_agent" (Adam v18.0 Aware - Full implementation in later step):
            - "new_agent_name" (str): Class name for the new agent.
            - "base_template_name" (str): Name of the Adam v18 template to use.
            - "agent_description" (str): Detailed natural language description of the agent.
            - "required_functionality_description" (str): Detailed natural language of methods,
              data sources, config needs for the new agent.
            - "target_adam_category" (str): e.g., "MarketAnalysis", "KnowledgeManagement".
            - "target_base_dir" (str, optional): Base directory for new agent's folder.
                                                 Defaults to `self.forged_agents_base_dir`.
            - Returns: `{"status": "success", "data": {"agent_file_path": "...",
                       "capability_snippet_path": "...", "readme_path": "...",
                       "registry_entry": { ... }}}` (Conceptual output)
        - "suggest_agent_modification" (Adam v18.0 Aware - Full implementation in later step):
            - "agent_file_path_to_modify" (str): Path to the Python file of the agent.
            - "change_description" (str): Natural language description of the desired change.
            - "agent_adam_category" (str, optional): Adam v18.0 category of the agent.
            - Returns: `{"status": "success", "data": {"suggested_modified_code": "...",
                       "suggested_config_changes": { ... }, "modification_summary": "..."}}` (Conceptual output)
        - "analyze_agent_requirement" (Adam v18.0 Aware - Full implementation in later step):
            - "user_request_for_agent" (str): Natural language request for a new agent.
            - Returns: `{"status": "success", "data": <proposed_agent_spec_json>}` (Conceptual output,
                       includes suggested name, template, Adam config values, etc.)

        Args:
            task_description (str): General description of the task for logging.
            current_step_inputs (Dict[str, Any]): Inputs for the action. Must include "action".
            shared_context (SharedContext): Shared context (not heavily used by AgentForge directly).

        Returns:
            Dict[str, Any]: A dictionary with "status" and "data" or "message".
        """
        self.logger.info(f"AgentForge received task: {task_description} with inputs: {current_step_inputs}")
        action = current_step_inputs.get("action")

        if not action:
            self.logger.error("Action not specified for AgentForge.")
            return {"status": "error", "message": "Action not specified for AgentForge."}

        try:
            if action == "list_templates":
                templates = self._list_templates_logic()
                return {"status": "success", "data": {"templates": templates}}
            elif action == "get_template_content":
                template_name = current_step_inputs.get("template_name")
                if not template_name:
                    return {"status": "error", "message": "template_name is required for get_template_content."}
                content = self._get_template_content_logic(template_name)
                if content is None:
                    return {"status": "error", "message": f"Template '{template_name}' not found."}
                return {"status": "success", "data": {"template_name": template_name, "content": content}}

            elif action == "create_agent":
                # Placeholder - To be fully implemented in Step 4 of the plan
                self.logger.info("Action 'create_agent' called. Full implementation pending.")
                return {"status": "pending_implementation", "message": "'create_agent' action logic not yet fully implemented in AgentForge."}
            elif action == "suggest_agent_modification":
                # Placeholder - To be fully implemented in Step 5 of the plan
                self.logger.info("Action 'suggest_agent_modification' called. Full implementation pending.")
                return {"status": "pending_implementation", "message": "'suggest_agent_modification' action logic not yet fully implemented."}
            elif action == "analyze_agent_requirement":
                # Placeholder - To be fully implemented in Step 6 of the plan
                self.logger.info("Action 'analyze_agent_requirement' called. Full implementation pending.")
                return {"status": "pending_implementation", "message": "'analyze_agent_requirement' action logic not yet fully implemented."}

            else:
                self.logger.warning(f"Unknown action: {action}")
                return {"status": "error", "message": f"Unknown action specified: {action}"}

        except Exception as e:
            self.logger.exception(f"Error during AgentForge action '{action}': {e}")
            return {"status": "error", "message": f"An unexpected error occurred: {e}"}

    def _list_templates_logic(self) -> List[str]:
        """Lists available Adam v18.0 agent templates from the template directory."""
        self.logger.debug(f"Listing templates from: {self.template_dir}")
        if not self.template_dir.exists() or not self.template_dir.is_dir():
            self.logger.warning(f"Template directory {self.template_dir} does not exist or is not a directory.")
            return []
        # Assuming templates end with .py.tpl for Python agent templates
        return [f.stem.replace('.py', '') for f in self.template_dir.glob("*.py.tpl")]

    def _get_template_content_logic(self, template_name: str) -> Optional[str]:
        """
        Retrieves the content of a specific Adam v18.0 agent template.

        Args:
            template_name (str): The name of the template (without .py.tpl extension).

        Returns:
            Optional[str]: The content of the template file, or None if not found.
        """
        # Assuming template_name does not include .py.tpl
        template_file_name = f"{template_name}.py.tpl"
        template_path = self.template_dir / template_file_name
        self.logger.debug(f"Attempting to read template: {template_path}")
        if template_path.exists() and template_path.is_file():
            try:
                return template_path.read_text(encoding='utf-8')
            except Exception as e:
                self.logger.exception(f"Error reading template {template_path}: {e}")
                return None
        else:
            self.logger.warning(f"Template not found: {template_path}")
            return None
