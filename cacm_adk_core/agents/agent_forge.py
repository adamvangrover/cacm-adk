# cacm_adk_core/agents/agent_forge.py
import logging
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
# import importlib # Not used in refactored version
# import yaml # Not used in refactored version
import json # For loading/saving registry and snippets

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext
# from core.utils.config_utils import load_config, save_config # Removed, registry handled differently


class AgentForge(Agent):
    """
    The AgentForge is responsible for the dynamic creation and modification
    of new agent code and configurations based on templates and user requirements.
    It can list available templates, retrieve their content, and (in future versions)
    generate or suggest modifications to agent code.
    """

    def __init__(self, kernel_service: KernelService, agent_config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_name="AgentForge", 
                         kernel_service=kernel_service, 
                         skills_plugin_name="AgentForgeSkills") # Assuming it will use SK
        self.config = agent_config if agent_config else {}
        
        # Default template directory within the cacm_adk_core structure
        # Points to the new Adam v18 specific template subdirectory
        default_template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "adam_v18")
        self.template_dir = Path(self.config.get("template_dir", default_template_dir))
        
        # Path for the registry of forged agents, updated for Adam v18.
        # Defaulting to 'config/adam_v18_forged_agents_registry.json' relative to the project root.
        self.forged_agents_registry_path = Path(self.config.get("forged_agents_registry_path", "config/adam_v18_forged_agents_registry.json"))
        
        self.logger.info(f"AgentForge initialized. Adam v18 Template dir: {self.template_dir}, Adam v18 Registry: {self.forged_agents_registry_path}")


    async def run(self, task_description: str, current_step_inputs: Dict[str, Any], shared_context: SharedContext) -> Dict[str, Any]:
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
        self.logger.debug(f"Listing templates from: {self.template_dir}")
        if not self.template_dir.exists() or not self.template_dir.is_dir():
            self.logger.warning(f"Template directory {self.template_dir} does not exist or is not a directory.")
            return []
        # Assuming templates end with .py.tpl for Python agent templates
        return [f.stem.replace('.py', '') for f in self.template_dir.glob("*.py.tpl")] 

    def _get_template_content_logic(self, template_name: str) -> Optional[str]:
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
