# cacm_adk_core/agents/agent_forge.py
import logging
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

# import importlib # Not used in refactored version
# import yaml # Not used in refactored version
import json  # For loading/saving registry and snippets

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

    def __init__(
        self,
        kernel_service: KernelService,
        agent_config: Optional[Dict[str, Any]] = None,
    ):
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
        super().__init__(
            agent_name="AgentForge",
            kernel_service=kernel_service,
            skills_plugin_name="AgentForgeSkills",
        )
        self.config = agent_config if agent_config else {}

        # Using module-level PROJECT_ROOT for robust default path construction
        default_template_dir = os.path.join(AGENT_FORGE_DIR, "templates", "adam_v18")
        self.template_dir = Path(self.config.get("template_dir", default_template_dir))

        default_registry_path = os.path.join(
            PROJECT_ROOT, "config", "adam_v18_forged_agents_registry.json"
        )
        self.forged_agents_registry_path = Path(
            self.config.get("forged_agents_registry_path", default_registry_path)
        )

        default_forged_agents_base_dir = os.path.join(
            CACM_ADK_CORE_DIR, "agents", "forged"
        )  # For storing new agents
        self.forged_agents_base_dir = Path(
            self.config.get("forged_agents_base_dir", default_forged_agents_base_dir)
        )

        self.logger.info(
            f"AgentForge initialized. Adam v18 Template dir: {self.template_dir}, Adam v18 Registry: {self.forged_agents_registry_path}, Forged Agents Base Dir: {self.forged_agents_base_dir}"
        )

    async def run(
        self,
        task_description: str,
        current_step_inputs: Dict[str, Any],
        shared_context: SharedContext,
    ) -> Dict[str, Any]:
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
        self.logger.info(
            f"AgentForge received task: {task_description} with inputs: {current_step_inputs}"
        )
        action = current_step_inputs.get("action")

        if not action:
            self.logger.error("Action not specified for AgentForge.")
            return {
                "status": "error",
                "message": "Action not specified for AgentForge.",
            }

        try:
            if action == "list_templates":
                templates = self._list_templates_logic()
                return {"status": "success", "data": {"templates": templates}}
            elif action == "get_template_content":
                template_name = current_step_inputs.get("template_name")
                if not template_name:
                    return {
                        "status": "error",
                        "message": "template_name is required for get_template_content.",
                    }
                content = self._get_template_content_logic(template_name)
                if content is None:
                    return {
                        "status": "error",
                        "message": f"Template '{template_name}' not found.",
                    }
                return {
                    "status": "success",
                    "data": {"template_name": template_name, "content": content},
                }

            elif action == "create_agent":
                # Placeholder - To be fully implemented in Step 4 of the plan
                self.logger.info(
                    "Action 'create_agent' called. Full implementation pending."
                )
                return {
                    "status": "pending_implementation",
                    "message": "'create_agent' action logic not yet fully implemented in AgentForge.",
                }
            elif action == "suggest_agent_modification":
                # Placeholder - To be fully implemented in Step 5 of the plan
                self.logger.info(
                    "Action 'suggest_agent_modification' called. Full implementation pending."
                )
                return {
                    "status": "pending_implementation",
                    "message": "'suggest_agent_modification' action logic not yet fully implemented.",
                }
            elif action == "analyze_agent_requirement":
                # Placeholder - To be fully implemented in Step 6 of the plan
                self.logger.info(
                    "Action 'analyze_agent_requirement' called. Full implementation pending."
                )
                return {
                    "status": "pending_implementation",
                    "message": "'analyze_agent_requirement' action logic not yet fully implemented.",
                }

            else:
                self.logger.warning(f"Unknown action: {action}")
                return {
                    "status": "error",
                    "message": f"Unknown action specified: {action}",
                }

        except Exception as e:
            self.logger.exception(f"Error during AgentForge action '{action}': {e}")
            return {"status": "error", "message": f"An unexpected error occurred: {e}"}

    def _list_templates_logic(self) -> List[str]:
        """Lists available Adam v18.0 agent templates from the template directory."""
        self.logger.debug(f"Listing templates from: {self.template_dir}")
        if not self.template_dir.exists() or not self.template_dir.is_dir():
            self.logger.warning(
                f"Template directory {self.template_dir} does not exist or is not a directory."
            )
            return []
        # Assuming templates end with .py.tpl for Python agent templates
        return [f.stem.replace(".py", "") for f in self.template_dir.glob("*.py.tpl")]

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
                return template_path.read_text(encoding="utf-8")
            except Exception as e:
                self.logger.exception(f"Error reading template {template_path}: {e}")
                return None
        else:
            self.logger.warning(f"Template not found: {template_path}")
            return None


# DEPRECATED

# cacm_adk_core/agents/agent_forge.py
import logging
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
import importlib
import yaml

from core.agents.agent_base import AgentBase
from core.utils.config_utils import load_config, save_config


class AgentForge(AgentBase):
    """
    The AgentForge is responsible for the dynamic creation of new agents.
    It uses templates and configuration to generate agent code and add them
    to the system at runtime. This version incorporates advanced features
    like skill schema generation and A2A wiring.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.template_dir = Path(
            self.config.get("template_dir", "core/agents/templates")
        )
        self.agent_config_path = Path("config/agents.yaml")
        self.workflows_config_path = Path("config/workflows.yaml")
        self.agent_classes = self.load_agent_classes()

        logging.info(f"AgentForge initialized with template dir: {self.template_dir}")

    def load_agent_classes(self) -> Dict[str, str]:
        """
        Loads the available agent classes for extension.
        This could be read from a config file or dynamically discovered.
        For simplicity, it's hardcoded here.
        """
        return {
            "MarketSentimentAgent": "core.agents.market_sentiment_agent",
            "MacroeconomicAnalysisAgent": "core.agents.macroeconomic_analysis_agent",
            "GeopoliticalRiskAgent": "core.agents.geopolitical_risk_agent",
            "IndustrySpecialistAgent": "core.agents.industry_specialist_agent",
            "FundamentalAnalystAgent": "core.agents.fundamental_analyst_agent",
            "TechnicalAnalystAgent": "core.agents.technical_analyst_agent",
            "RiskAssessmentAgent": "core.agents.risk_assessment_agent",
            "NewsletterLayoutSpecialistAgent": "core.agents.newsletter_layout_specialist_agent",
            "DataVerificationAgent": "core.agents.data_verification_agent",
            "LexicaAgent": "core.agents.lexica_agent",
            "ArchiveManagerAgent": "core.agents.archive_manager_agent",
            "AgentForge": "core.agents.agent_forge",
            "PromptTuner": "core.agents.prompt_tuner",
            "CodeAlchemist": "core.agents.code_alchemist",
            "LinguaMaestro": "core.agents.lingua_maestro",
            "SenseWeaver": "core.agents.sense_weaver",
            "QueryUnderstandingAgent": "core.agents.query_understanding_agent",
            "DataRetrievalAgent": "core.agents.data_retrieval_agent",
            "ResultAggregationAgent": "core.agents.result_aggregation_agent",
        }

    async def execute(self, action: str, **kwargs: Dict[str, Any]) -> Optional[str]:
        """
        Executes an agent creation action.
        """

        if action == "create_agent":
            return await self.create_agent(
                kwargs.get("agent_name"),
                kwargs.get("agent_type"),
                kwargs.get("agent_description"),
                kwargs.get("agent_skills"),
                kwargs.get("agent_dependencies"),
                kwargs.get("agent_a2a_peers"),
            )
        elif action == "list_templates":
            return self.list_templates()
        elif action == "get_template":
            return self.get_template(kwargs.get("template_name"))
        else:
            logging.warning(f"AgentForge: Unknown action: {action}")
            return None

    def list_templates(self) -> List[str]:
        """
        Lists available agent templates.
        """
        return [f.stem for f in self.template_dir.glob("*.py")]

    def get_template(self, template_name: str) -> Optional[str]:
        """
        Retrieves the content of a specific agent template.
        """
        template_path = self.template_dir / f"{template_name}.py"
        if template_path.exists():
            return template_path.read_text()
        else:
            logging.warning(f"AgentForge: Template not found: {template_name}")
            return None

    async def create_agent(
        self,
        agent_name: str,
        agent_type: str,
        agent_description: str,
        agent_skills: List[Dict[str, Any]],
        agent_dependencies: List[str],
        agent_a2a_peers: List[str],
    ) -> Optional[str]:
        """
        Creates a new agent.
        """

        try:
            # 1. Select Template
            template_name = self.config.get(
                "default_template", "basic_agent"
            )  # Default template
            template = self.get_template(template_name)
            if not template:
                raise ValueError(f"Agent template '{template_name}' not found.")

            # 2. Customize Template
            customized_code = self.customize_template(
                template, agent_name, agent_description, agent_skills, agent_a2a_peers
            )

            # 3. Validate & Optimize (Placeholder - CodeAlchemist agent?)
            validated_code = await self.validate_and_optimize_code(customized_code)
            if not validated_code:
                raise ValueError("Generated code is invalid.")

            # 4. Save Agent Code
            agent_filename = f"{agent_name.lower()}.py"
            agent_path = Path("core/agents") / agent_filename
            self.save_agent_code(validated_code, agent_path)

            # 5. Update Configurations
            self.update_agent_config(
                agent_name,
                agent_type,
                agent_description,
                agent_dependencies,
                agent_a2a_peers,
            )
            self.update_workflows_config(agent_name, agent_dependencies)

            # 6. Agent Initialization (Orchestrator handles this)
            # Orchestrator will reload agents or dynamically import the new agent

            return f"Agent '{agent_name}' created successfully in '{agent_path}'."

        except Exception as e:
            logging.error(f"AgentForge: Error creating agent '{agent_name}': {e}")
            return None

    def customize_template(
        self,
        template: str,
        agent_name: str,
        agent_description: str,
        agent_skills: List[Dict[str, Any]],
        agent_a2a_peers: List[str],
    ) -> str:
        """
        Customizes the agent template with agent-specific details.
        This includes generating the skill schema and A2A wiring.
        """

        # Replace placeholders in the template
        code = template.replace("CLASS_NAME", agent_name).replace(
            "AGENT_DESCRIPTION", agent_description
        )

        # Generate skill schema code
        skill_schema_code = self.generate_skill_schema_code(agent_skills)
        code = code.replace("SKILL_SCHEMA", skill_schema_code)

        # Generate A2A wiring code
        a2a_wiring_code = self.generate_a2a_wiring_code(agent_a2a_peers)
        code = code.replace("A2A_WIRING", a2a_wiring_code)

        return code

    def generate_skill_schema_code(self, agent_skills: List[Dict[str, Any]]) -> str:
        """
        Generates the code for the get_skill_schema() method based on the
        provided agent skills.
        """

        skills_code = ",\n            ".join(
            [
                f"""
                {{
                    "name": "{skill['name']}",
                    "description": "{skill['description']}",
                    "inputs": {json.dumps(skill.get('inputs', []))},
                    "outputs": {json.dumps(skill.get('outputs', []))}
                }}"""
                for skill in agent_skills
            ]
        )

        return f"""
        def get_skill_schema(self) -> Dict[str, Any]:
            return {{
                "name": type(self).__name__,
                "description": self.config.get("description", "No description provided"),
                "skills": [
                    {skills_code}
                ]
            }}
        """

    def generate_a2a_wiring_code(self, agent_a2a_peers: List[str]) -> str:
        """
        Generates the code to add peer agents for A2A communication.
        This assumes the AgentOrchestrator will call the add_peer_agent method.
        """

        wiring_code = "\n        ".join(
            [f"self.add_peer_agent('{peer_agent}');" for peer_agent in agent_a2a_peers]
        )
        return f"""
        def wire_a2a_peers(self):
            {wiring_code}
        """

    async def validate_and_optimize_code(self, code: str) -> Optional[str]:
        """
        Placeholder for code validation and optimization using a CodeAlchemist agent.
        In a real system, this would involve:
            - Syntax checking
            - Security scanning
            - Performance analysis
            - Code formatting
        """

        # For now, just return the code as is (for demonstration purposes)
        return code
        # Example of calling a CodeAlchemist agent (if available):
        # code_alchemist = self.orchestrator.get_agent("CodeAlchemist")
        # if code_alchemist:
        #    return await code_alchemist.execute(action="validate_and_optimize", code=code)
        # else:
        #    logging.warning("CodeAlchemist agent not available. Skipping code validation and optimization.")
        #    return code

    def save_agent_code(self, code: str, agent_path: Path) -> None:
        """
        Saves the generated agent code to a file.
        """

        try:
            with open(agent_path, "w") as f:
                f.write(code)
            logging.info(f"Agent code saved to: {agent_path}")
        except Exception as e:
            logging.error(f"AgentForge: Error saving agent code to '{agent_path}': {e}")
            raise

    def update_agent_config(
        self,
        agent_name: str,
        agent_type: str,
        agent_description: str,
        agent_dependencies: List[str],
        agent_a2a_peers: List[str],
    ) -> None:
        """
        Updates the agent configuration file (config/agents.yaml) to include the new agent.
        """

        agent_config = load_config(self.agent_config_path)
        if agent_config is None:
            logging.error(
                f"AgentForge: Could not load agent config from {self.agent_config_path}"
            )
            return

        agent_config[agent_name] = {
            "type": agent_type,
            "description": agent_description,
            "dependencies": agent_dependencies,
            "a2a_peers": agent_a2a_peers,
        }
        save_config(self.agent_config_path, agent_config)
        logging.info(f"Agent config updated with: {agent_name}")

    def update_workflows_config(
        self, agent_name: str, agent_dependencies: List[str]
    ) -> None:
        """
        Updates the workflows configuration file (config/workflows.yaml) to
        incorporate the new agent into relevant workflows (if any).
        This is a simplified example; a more robust implementation would
        involve more intelligent workflow modification.
        """

        workflows_config = load_config(self.workflows_config_path)
        if workflows_config is None:
            logging.error(
                f"AgentForge: Could not load workflows config from {self.workflows_config_path}"
            )
            return

        for workflow in workflows_config.values():
            if agent_dependencies:
                # Naive: Add the new agent to any workflow that uses its dependencies
                if any(dep in workflow["agents"] for dep in agent_dependencies):
                    workflow["agents"].append(agent_name)
                    workflow["dependencies"][agent_name] = agent_dependencies
                    logging.info(f"Workflows config updated to include {agent_name}")
                    break  # Only update the first matching workflow (for simplicity)

        save_config(self.workflows_config_path, workflows_config)

    async def run_semantic_kernel_skill(
        self, skill_name: str, input_vars: Dict[str, str]
    ) -> str:
        """
        Placeholder for running a Semantic Kernel skill.
        This assumes the AgentForge might use SK for code generation or validation.
        """

        # For now, just return a dummy result
        return f"Semantic Kernel skill '{skill_name}' executed (dummy result)."

        # Example of calling a Semantic Kernel skill (if available):
        # if hasattr(self, 'kernel') and self.kernel:
        #    return await self.kernel.run(skill_name, input_vars=input_vars)
        # else:
        #    logging.warning("Semantic Kernel not available in AgentForge.")
        #    return f"Semantic Kernel not available. Cannot execute skill '{skill_name}'."
