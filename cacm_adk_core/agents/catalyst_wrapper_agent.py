# cacm_adk_core/agents/catalyst_wrapper_agent.py
import logging
import json # For parsing results if they are JSON strings
from typing import Dict, Any, Optional

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext
from cacm_adk_core.agents.catalyst_agent import CatalystAgent as OriginalCatalystAgent # Import the original

# Default path for the original CatalystAgent's config.
# This could be made more dynamic via agent_config if needed.
DEFAULT_CATALYST_CONFIG_PATH = "config/catalyst_config.json" # Assuming it's in config/

class CatalystWrapperAgent(Agent):
    """
    A wrapper agent to integrate the existing CatalystAgent script
    into the orchestrator framework.
    """

    def __init__(self, kernel_service: KernelService, agent_config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_name="CatalystWrapperAgent", kernel_service=kernel_service)
        self.config = agent_config if agent_config else {}
        self.catalyst_config_path = self.config.get("catalyst_config_path", DEFAULT_CATALYST_CONFIG_PATH)
        self.logger.info(f"CatalystWrapperAgent initialized. Original Catalyst config path: {self.catalyst_config_path}")

    async def run(self, task_description: str, current_step_inputs: Dict[str, Any], shared_context: SharedContext) -> Dict[str, Any]:
        """
        Wraps and executes the original CatalystAgent with the provided inputs.

        This method instantiates the `OriginalCatalystAgent` (from 
        `cacm_adk_core.agents.catalyst_agent.py`), passes the necessary
        parameters to its `run` method, and then formats the output.

        Args:
            task_description (str): A description of the task for logging/context.
            current_step_inputs (Dict[str, Any]): Inputs for this execution step:
                - "client_id" (str): The client identifier. Required.
                - "company_id" (str): The company identifier. Required.
                - "industry" (str): The industry context. Required.
                - "catalyst_config_path" (str, optional): Path to the 
                  `catalyst_config.json` file if different from the default 
                  (`config/catalyst_config.json`).
            shared_context (SharedContext): The shared context object (not directly
                                            used by this wrapper's core logic but
                                            available for potential extensions).

        Returns:
            Dict[str, Any]: A dictionary containing the execution status and result:
                - {"status": "success", "data": <catalyst_agent_output_dict>}
                - {"status": "error", "message": <error_description_str>}
        """
        self.logger.info(f"'{self.agent_name}' received task: {task_description} with inputs: {current_step_inputs}")

        client_id = current_step_inputs.get("client_id")
        company_id = current_step_inputs.get("company_id")
        industry = current_step_inputs.get("industry")

        if not all([client_id, company_id, industry]):
            missing_params = [
                name for name, val in [("client_id", client_id), ("company_id", company_id), ("industry", industry)] if not val
            ]
            error_msg = f"Missing required parameters: {', '.join(missing_params)}"
            self.logger.error(error_msg)
            return {"status": "error", "message": error_msg}

        try:
            # Instantiate the original CatalystAgent
            # It loads its own config (URLs etc.) from the path provided.
            original_catalyst = OriginalCatalystAgent(config_path=self.catalyst_config_path)
            
            # Run the original CatalystAgent's logic
            # The original run method is synchronous, so we call it directly.
            # If it were async, we'd await it.
            # Consider if the original catalyst_agent.py needs modification
            # to be more library-friendly (e.g. not printing, returning structured data).
            # For now, assume its run() method returns a dictionary or JSON-serializable data.
            catalyst_result = original_catalyst.run(
                client_id=client_id,
                company_id=company_id,
                industry=industry
            )

            self.logger.info(f"Original CatalystAgent execution completed. Result type: {type(catalyst_result)}")
            
            # Ensure the result is a dictionary (it should be based on CatalystAgent's code)
            if not isinstance(catalyst_result, dict):
                # If it's a JSON string, try to parse it.
                if isinstance(catalyst_result, str):
                    try:
                        catalyst_result = json.loads(catalyst_result)
                    except json.JSONDecodeError as je:
                        self.logger.error(f"Failed to parse CatalystAgent string result as JSON: {je}")
                        return {"status": "error", "message": f"CatalystAgent returned non-JSON string: {catalyst_result[:200]}"} # Truncate long strings
                else: # If it's neither dict nor string, wrap it or error
                    self.logger.warning(f"CatalystAgent result was not a dict. Wrapping: {type(catalyst_result)}")
                    catalyst_result = {"raw_output": catalyst_result}


            return {"status": "success", "data": catalyst_result}

        except FileNotFoundError as fnf_error:
            # Specifically catch FileNotFoundError if catalyst_config.json is missing
            self.logger.error(f"Error during CatalystWrapperAgent execution: Config file not found at {self.catalyst_config_path}. Error: {fnf_error}")
            return {"status": "error", "message": f"Configuration file for original CatalystAgent not found: {self.catalyst_config_path}. Details: {fnf_error}"}
        except Exception as e:
            self.logger.exception(f"Error during CatalystWrapperAgent execution: {e}")
            return {"status": "error", "message": f"An unexpected error occurred while running CatalystAgent: {e}"}
