# cacm_adk_core/orchestrator/orchestrator.py
import json
import random
import logging 
import uuid # Added
from typing import List, Dict, Any, Tuple, Callable, Type, Optional 
import importlib 

from cacm_adk_core.validator.validator import Validator
# Assuming basic_functions might be directly imported if needed, but registration handles it
# from cacm_adk_core.compute_capabilities import basic_functions
from cacm_adk_core.compute_capabilities import financial_ratios # For direct call
from cacm_adk_core.semantic_kernel_adapter import KernelService 
from cacm_adk_core.agents.base_agent import Agent 
from cacm_adk_core.context.shared_context import SharedContext # Added

# Placeholder agent imports - will be done in a registration method
# from cacm_adk_core.agents.data_ingestion_agent import DataIngestionAgent
# from cacm_adk_core.agents.analysis_agent import AnalysisAgent
# from cacm_adk_core.agents.report_generation_agent import ReportGenerationAgent
from cacm_adk_core.agents.fundamental_analyst_agent import FundamentalAnalystAgent
from cacm_adk_core.agents.SNC_analyst_agent import SNCAnalystAgent
from cacm_adk_core.agents.data_retrieval_agent import DataRetrievalAgent
from cacm_adk_core.agents.catalyst_wrapper_agent import CatalystWrapperAgent
from cacm_adk_core.agents.knowledge_graph_agent import KnowledgeGraphAgent


class Orchestrator:
    def __init__(self, kernel_service: KernelService, validator: Validator = None, catalog_filepath="config/compute_capability_catalog.json", load_catalog_on_init=True): # Validator optional, added load_catalog_on_init
        self.kernel_service = kernel_service # Added
        self.validator = validator
        self.compute_catalog = {} # Initialize as empty dict
        self.capability_function_map: Dict[str, Callable] = {} # Kept for mixed workflows
        self.agents: Dict[str, Type[Agent]] = {} # Added for agent classes
        self.agent_instances: Dict[str, Agent] = {} # Added for active agent instances per run
        
        if load_catalog_on_init: # Conditional loading
            self.load_compute_capability_catalog(catalog_filepath)
            # _register_capabilities will use self.compute_catalog to find skill_plugin_name etc.
            # For now, it registers Python module based functions. We might need to adjust it
            # or rely on Kernel-based skill invocation if agent_type is not present.
            self._register_capabilities() 
        
        self._register_placeholder_agents() # Register agent classes


    def _register_placeholder_agents(self):
        """Imports and registers known agent classes."""
        from cacm_adk_core.agents.data_ingestion_agent import DataIngestionAgent
        from cacm_adk_core.agents.analysis_agent import AnalysisAgent
        from cacm_adk_core.agents.report_generation_agent import ReportGenerationAgent
        # FundamentalAnalystAgent and SNCAnalystAgent are already imported at the top level
        # DataRetrievalAgent is also imported at the top level
        
        self.register_agent("DataIngestionAgent", DataIngestionAgent)
        self.register_agent("AnalysisAgent", AnalysisAgent) # Placeholder, might be replaced or removed if DRA is the one
        self.register_agent("ReportGenerationAgent", ReportGenerationAgent)
        self.register_agent("FundamentalAnalystAgent", FundamentalAnalystAgent)
        self.register_agent("SNCAnalystAgent", SNCAnalystAgent)
        self.register_agent("DataRetrievalAgent", DataRetrievalAgent)
        self.register_agent("CatalystWrapperAgent", CatalystWrapperAgent)
        self.register_agent("KnowledgeGraphAgent", KnowledgeGraphAgent) # Added KnowledgeGraphAgent registration
        print(f"INFO: Orchestrator: Registered {len(self.agents)} agent types.")

    def register_agent(self, agent_name_key: str, agent_class: Type[Agent]):
        """Registers an agent class with the orchestrator."""
        if not issubclass(agent_class, Agent):
            raise ValueError(f"Cannot register {agent_class.__name__}: not a subclass of Agent.")
        self.agents[agent_name_key] = agent_class
        print(f"INFO: Orchestrator: Agent type '{agent_name_key}' registered with class {agent_class.__name__}.")

    def load_compute_capability_catalog(self, catalog_filepath="config/compute_capability_catalog.json"):
        try:
            with open(catalog_filepath, 'r') as f:
                data = json.load(f)
                self.compute_catalog = {cap['id']: cap for cap in data.get("computeCapabilities", [])}
            print(f"INFO: Orchestrator: Loaded {len(self.compute_catalog)} compute capabilities from {catalog_filepath}")
        except FileNotFoundError:
            print(f"ERROR: Orchestrator: Compute capability catalog not found at {catalog_filepath}")
            self.compute_catalog = {} 
        except json.JSONDecodeError:
            print(f"ERROR: Orchestrator: Could not decode JSON from catalog file {catalog_filepath}")
            self.compute_catalog = {}

    def _register_capabilities(self): # New method
        log_messages_temp: List[str] = [] # For local logging during registration
        if not self.compute_catalog:
            print("ERROR: Orchestrator_Register: Compute catalog not loaded. Cannot register capabilities.")
            return

        for cap_id, cap_def in self.compute_catalog.items():
            module_name = cap_def.get("module")
            func_name = cap_def.get("functionName")

            if module_name and func_name:
                try:
                    module = importlib.import_module(module_name)
                    function_object = getattr(module, func_name)
                    self.capability_function_map[cap_id] = function_object
                    log_messages_temp.append(f"INFO: Orchestrator_Register: Successfully registered '{cap_id}' -> {module_name}.{func_name}")
                except ImportError:
                    log_messages_temp.append(f"ERROR: Orchestrator_Register: Could not import module '{module_name}' for capability '{cap_id}'.")
                except AttributeError:
                    log_messages_temp.append(f"ERROR: Orchestrator_Register: Could not find function '{func_name}' in module '{module_name}' for capability '{cap_id}'.")
                except Exception as e:
                    log_messages_temp.append(f"ERROR: Orchestrator_Register: Unexpected error registering capability '{cap_id}': {e}")
        
        # Print registration logs to server console (not returned to run_cacm logs)
        for msg in log_messages_temp:
            print(msg)

    def execute_cacm(self, template_path: str, input_data: dict) -> Dict[str, Any]:
        """
        Executes a CACM based on a template file and input data.
        Focuses on special handling for basic_ratio_analysis_template.json for this task.
        """
        log_messages: List[str] = [] 
        
        try:
            with open(template_path, 'r') as f:
                template = json.load(f)
            log_messages.append(f"INFO: Orchestrator: Successfully loaded template: {template_path}")
        except FileNotFoundError:
            print(f"ERROR: Orchestrator: Template file not found: {template_path}")
            return {"errors": [f"Template file not found: {template_path}"], "cacm_id": None, "outputs": {}}
        except json.JSONDecodeError:
            print(f"ERROR: Orchestrator: Error decoding JSON from template: {template_path}")
            return {"errors": [f"Error decoding JSON from template: {template_path}"], "cacm_id": None, "outputs": {}}

        cacm_id_from_template = template.get("cacmId", "UnknownCACM")
        
        # --- Special Handling for Basic Ratio Analysis Template ---
        # Using endswith as a simple check for this specific task; robust check would be full path or ID.
        if template_path.endswith("basic_ratio_analysis_template.json"):
            
            log_messages.append(f"INFO: Orchestrator: Detected Basic Ratio Analysis Template ('{cacm_id_from_template}'). Using direct execution path.")
            
            # 1. Extract financialStatementData from top-level input_data
            # Template defines inputs.financialStatementData
            financial_statement_data_from_input = input_data.get("financialStatementData")
            
            if financial_statement_data_from_input is None:
                err_msg = "Input 'financialStatementData' not found in input_data."
                log_messages.append(f"ERROR: Orchestrator: {err_msg}")
                return {"errors": [err_msg], "cacm_id": cacm_id_from_template, "outputs": {}}
            
            if not isinstance(financial_statement_data_from_input, dict):
                err_msg = f"'financialStatementData' in input_data is not a valid dictionary, got {type(financial_statement_data_from_input).__name__}."
                log_messages.append(f"ERROR: Orchestrator: {err_msg}")
                return {"errors": [err_msg], "cacm_id": cacm_id_from_template, "outputs": {}}

            # 2. Extract roundingPrecision from template's parameters
            rounding_precision = 2 # Default
            template_parameters = template.get("parameters", [])
            if isinstance(template_parameters, list):
                for param_def in template_parameters:
                    if isinstance(param_def, dict) and (param_def.get("paramId") == "roundingPrecision" or param_def.get("name") == "Rounding Precision"):
                        rounding_precision = param_def.get("defaultValue", 2)
                        break
            log_messages.append(f"INFO: Orchestrator: Using rounding precision: {rounding_precision}")

            # 3. Call the financial_ratios.calculate_basic_ratios function
            try:
                result_from_module = financial_ratios.calculate_basic_ratios(
                    financial_data=financial_statement_data_from_input, # Pass the nested dict
                    rounding_precision=rounding_precision
                )
                log_messages.append(f"INFO: Orchestrator: Called financial_ratios.calculate_basic_ratios. Result: {result_from_module}")
            except Exception as e:
                err_msg = f"Error calling calculate_basic_ratios: {str(e)}"
                log_messages.append(f"ERROR: Orchestrator: {err_msg}")
                return {"errors": [err_msg], "cacm_id": cacm_id_from_template, "outputs": {}}

            # 4. Structure the output according to the template's outputs section
            # Template output schema: {"outputs": {"calculatedRatios": {"type": "object", ...}}}
            # Module output: {"calculated_ratios": {...ratios...}, "errors": [...]}
            
            final_cacm_output_payload = {}
            template_output_schema = template.get("outputs", {})
            
            if "calculatedRatios" in template_output_schema: # Key in template's output schema
                final_cacm_output_payload["calculatedRatios"] = result_from_module.get("calculated_ratios", {})
            else:
                # If template output structure is different, this part would need adjustment
                # For now, we directly map the module's main result if the key matches.
                log_messages.append(f"WARN: Orchestrator: Template output schema does not directly define 'calculatedRatios'. Using module's output structure.")
                final_cacm_output_payload = result_from_module.get("calculated_ratios", {})
            
            # Consolidate errors
            orchestrator_errors = [] # For errors generated by orchestrator itself
            module_errors = result_from_module.get("errors", [])
            if module_errors:
                 orchestrator_errors.extend(module_errors)
            
            log_messages.append(f"INFO: Orchestrator: Basic Ratio Analysis execution completed.")
            # The return for execute_cacm is just the output payload, errors are illustrative for logging here.
            # A more robust implementation would have a consistent return type like Tuple[Dict, List[str]]
            if orchestrator_errors: # If there were errors from the module, include them in a standard way
                final_cacm_output_payload["execution_errors"] = orchestrator_errors
            
            return final_cacm_output_payload

        else:
            # Fallback for other templates - indicates not implemented for this specific task scope
            log_messages.append(f"INFO: Orchestrator: CACM ID '{cacm_id_from_template}' or template path '{template_path}' not specially handled by this simplified execute_cacm.")
            print("\n".join(log_messages)) # Print logs for debugging this path
            return {
                "errors": [f"Execution path for template '{template_path}' (CACM ID: '{cacm_id_from_template}') is not implemented in this version."],
                "cacm_id": cacm_id_from_template,
                "outputs": {}
            }

    async def run_cacm(self, cacm_instance_data: dict) -> Tuple[bool, List[str], Dict[str, Any]]:
        log_messages: List[str] = []
        final_cacm_outputs: Dict[str, Any] = {} 
        step_outputs: Dict[str, Any] = {}
        self.agent_instances.clear() # Clear instances at the start of a new run
        log_messages.append("INFO: Orchestrator: Cleared active agent instances for new run_cacm execution.")

        # Create SharedContext for this run
        cacm_id = cacm_instance_data.get("cacmId", f"UnknownCACM_{str(uuid.uuid4())}")
        shared_context = SharedContext(cacm_id=cacm_id)
        shared_context.set_global_parameter("initial_inputs", cacm_instance_data.get("inputs", {}))
        log_messages.append(f"INFO: Orchestrator: Initialized SharedContext for session {shared_context.get_session_id()} (CACM ID: {shared_context.get_cacm_id()})")

        if not self.validator or not self.validator.schema:
            log_messages.append("ERROR: Orchestrator: Validator or schema not properly initialized.")
            return False, log_messages, final_cacm_outputs

        is_valid, errors = self.validator.validate_cacm_against_schema(cacm_instance_data)
        if not is_valid:
            log_messages.append("ERROR: Orchestrator: CACM instance is invalid. Cannot execute.")
            for error in errors:
                log_messages.append(f"  Validation Error: Path: {'.'.join(map(str, error.get('path',[]))) if error.get('path') else 'N/A'}, Message: {error.get('message', 'N/A')}")
            return False, log_messages, final_cacm_outputs

        log_messages.append("INFO: Orchestrator: CACM instance is valid. Starting execution...")
        
        workflow_steps = cacm_instance_data.get("workflow", [])
        if not workflow_steps:
            log_messages.append("INFO: Orchestrator: Workflow has no steps.")
        
        for step in workflow_steps:
            step_id = step.get('stepId', 'Unknown Step')
            description = step.get('description', 'No description')
            capability_ref = step.get('computeCapabilityRef')
            
            log_messages.append(f"INFO: Orchestrator: --- Executing Step '{step_id}': {description} ---")
            
            if not capability_ref:
                log_messages.append(f"ERROR: Orchestrator: Step '{step_id}' is missing 'computeCapabilityRef'. Skipping.")
                continue
            
            capability_def = self.compute_catalog.get(capability_ref)
            if not capability_def:
                log_messages.append(f"ERROR: Orchestrator: Capability '{capability_ref}' not found in catalog for step '{step_id}'. Skipping.")
                continue

            log_messages.append(f"INFO: Orchestrator:   Compute Capability Ref: {capability_ref}")
            agent_type = capability_def.get("agent_type")

            current_step_result_data: Optional[Dict[str, Any]] = None

            # Prepare context_data for agents or function_args for skills
            # This logic is common for both agent and skill execution paths
            # It resolves input bindings from cacm.inputs or previous steps.
            # For simplicity, we'll pass all resolved inputs as context_data to agents,
            # and filter them into function_args for direct skill calls.
            
            resolved_inputs: Dict[str, Any] = {}
            step_input_bindings = step.get('inputBindings', {})
            for cap_input_def in capability_def.get('inputs', []):
                param_name = cap_input_def['name']
                param_type = cap_input_def['type'] # For potential type coercion
                is_optional = cap_input_def.get('optional', False)
                
                binding_value_source = step_input_bindings.get(param_name)
                resolved_value: Any = None
                value_found = False

                if binding_value_source:
                    if isinstance(binding_value_source, str) and binding_value_source.startswith("cacm.inputs."):
                        key_parts = binding_value_source.split("cacm.inputs.")[-1].split('.')
                        current_data_val = cacm_instance_data.get("inputs", {})
                        for i, part in enumerate(key_parts):
                            if isinstance(current_data_val, dict):
                                current_data_val = current_data_val.get(part)
                            else: current_data_val = None; break
                        if current_data_val is not None:
                            resolved_value = current_data_val.get("value") if isinstance(current_data_val, dict) and "value" in current_data_val else current_data_val
                            value_found = True
                    elif isinstance(binding_value_source, str) and binding_value_source.startswith("steps."):
                        parts = binding_value_source.split('.')
                        if len(parts) == 4 and parts[1] and parts[3]: # steps.stepA.outputs.result
                            prev_step_id, _, prev_output_name = parts[1], parts[2], parts[3]
                            resolved_value = step_outputs.get(prev_step_id, {}).get(prev_output_name)
                            if resolved_value is not None: value_found = True
                        else: log_messages.append(f"WARN: Orchestrator: Invalid step binding format: {binding_value_source}")
                    else: # Direct value
                        resolved_value = binding_value_source
                        value_found = True
                
                if value_found:
                    # Basic type coercion (can be expanded)
                    try:
                        if param_type == 'float' and resolved_value is not None: resolved_value = float(resolved_value)
                        elif param_type == 'integer' and resolved_value is not None: resolved_value = int(resolved_value)
                        resolved_inputs[param_name] = resolved_value
                    except ValueError as ve:
                        log_messages.append(f"ERROR: Orchestrator: Type coercion failed for param '{param_name}' (value: {resolved_value}) to type '{param_type}': {ve}")
                        if not is_optional: return False, log_messages, final_cacm_outputs
                        resolved_inputs[param_name] = None # Or default
                elif not is_optional:
                    log_messages.append(f"ERROR: Orchestrator: Missing required input '{param_name}' for {capability_ref} in step '{step_id}'.")
                    # Halt or mark step as failed
                    # For now, we'll let it proceed and the agent/function might fail
            
            if agent_type:
                log_messages.append(f"INFO: Orchestrator: Attempting to execute Agent '{agent_type}' for capability '{capability_ref}'.")
                agent_class = self.agents.get(agent_type)
                if agent_class:
                    # Get or create agent instance for this run
                    if agent_type in self.agent_instances:
                        agent_instance = self.agent_instances[agent_type]
                        log_messages.append(f"INFO: Orchestrator: Reusing existing instance of agent '{agent_type}'.")
                    else:
                        log_messages.append(f"INFO: Orchestrator: Creating new instance of agent '{agent_type}'.")
                        agent_instance = agent_class(self.kernel_service)
                        agent_instance.set_agent_manager(self) # Set the orchestrator as manager
                        self.agent_instances[agent_type] = agent_instance
                    
                    # Task description could come from step.description or capability_def.task_details_from_capability
                    task_desc_from_step = description
                    task_desc_from_cap = capability_def.get("task_details_from_capability", f"Execute {capability_ref}")
                    effective_task_desc = f"{task_desc_from_step} (Detail: {task_desc_from_cap})"
                    
                    try:
                        # Agent's run method now receives resolved_inputs as current_step_inputs and shared_context
                        current_step_result_data = await agent_instance.run(
                            effective_task_desc, 
                            resolved_inputs, 
                            shared_context
                        )
                        log_messages.append(f"INFO: Orchestrator: Agent '{agent_type}' executed. Result: {current_step_result_data}")
                    except Exception as e:
                        log_messages.append(f"ERROR: Orchestrator: Agent '{agent_type}' execution failed: {e}")
                        # Handle agent error (e.g., stop workflow or mark step as failed)
                else:
                    log_messages.append(f"ERROR: Orchestrator: Agent type '{agent_type}' not found in registered agents. Skipping step.")
            
            elif capability_def.get("skill_plugin_name") and capability_def.get("skill_function_name"):
                # SKILL EXECUTION LOGIC (using Kernel)
                plugin_name = capability_def["skill_plugin_name"]
                function_name = capability_def["skill_function_name"]
                log_messages.append(f"INFO: Orchestrator: Attempting to execute Kernel Skill '{plugin_name}.{function_name}'.")
                kernel = self.kernel_service.get_kernel()
                try:
                    # Ensure resolved_inputs are packaged into KernelArguments if needed by SK version
                    # For SK native functions, direct kwarg passing from a dict might work.
                    # from semantic_kernel.functions.kernel_arguments import KernelArguments
                    # kernel_args = KernelArguments(**resolved_inputs)
                    # skill_function = kernel.plugins[plugin_name][function_name]
                    # result_obj = await kernel.invoke(skill_function, kernel_args)
                    # current_step_result_data = result_obj.value # Or process result_obj as needed

                    # Simplified direct call assuming native function signature matches resolved_inputs keys
                    # This needs to be robust based on how SK expects args for registered native functions.
                    skill_function = kernel.plugins[plugin_name][function_name]
                    # For native functions, SK might expect parameters directly, not via KernelArguments always.
                    # The `invoke` method with function object and kwargs (from resolved_inputs) is typical.
                    result_obj = await kernel.invoke(skill_function, **resolved_inputs)
                    
                    # The result from invoke might be a FunctionResult or directly the value.
                    # Assuming it's FunctionResult, and .value holds the actual output.
                    if hasattr(result_obj, 'value'):
                        current_step_result_data = result_obj.value
                    else: # If it's the direct value (older SK or specific function types)
                        current_step_result_data = result_obj

                    log_messages.append(f"INFO: Orchestrator: Kernel Skill '{plugin_name}.{function_name}' executed. Result: {current_step_result_data}")
                except Exception as e:
                    log_messages.append(f"ERROR: Orchestrator: Kernel Skill '{plugin_name}.{function_name}' execution failed: {e}")

            elif capability_ref in self.capability_function_map: # Fallback to old Python module functions
                log_messages.append(f"INFO: Orchestrator: Executing legacy Python function for '{capability_ref}'.")
                target_function = self.capability_function_map[capability_ref]
                try:
                    current_step_result_data = target_function(**resolved_inputs) # Pass resolved inputs
                    log_messages.append(f"INFO: Orchestrator: Legacy function '{capability_ref}' executed. Result: {current_step_result_data}")
                except Exception as e:
                    log_messages.append(f"ERROR: Orchestrator: Legacy function '{capability_ref}' execution failed: {e}")
            else:
                log_messages.append(f"WARN: Orchestrator: No execution path (Agent, Kernel Skill, or legacy function) found for capability '{capability_ref}'. Mocking outputs if any.")
                # Mocking logic (if needed for unhandled capabilities that have output bindings)
                # This part can be simplified or removed if all capabilities must have an execution path.
                mocked_outputs_for_step = {}
                for binding_key, cacm_output_ref_str in step.get('outputBindings', {}).items():
                     if isinstance(cacm_output_ref_str, str) and cacm_output_ref_str.startswith("cacm.outputs."):
                        output_key = cacm_output_ref_str.split("cacm.outputs.")[-1]
                        mocked_value = f"Mocked for unhandled {capability_ref} -> {binding_key}"
                        # Ensure the mocked value is stored in a way that step_outputs can use it
                        # The binding_key is what downstream steps will look for.
                        mocked_outputs_for_step[binding_key] = mocked_value 
                        final_cacm_outputs[output_key] = {"value": mocked_value, "description": f"Mocked output for {output_key}"}
                current_step_result_data = mocked_outputs_for_step


            # Store step output
            if current_step_result_data is not None:
                # If the function/agent returns a single value but catalog defines specific named outputs,
                # we need to map it. For now, assume result is a dict if multiple outputs expected.
                step_outputs[step_id] = current_step_result_data
                
                # Map to final_cacm_outputs based on step's outputBindings
                for binding_key_in_step_output, cacm_output_ref_str in step.get('outputBindings', {}).items():
                    if isinstance(cacm_output_ref_str, str) and cacm_output_ref_str.startswith("cacm.outputs."):
                        output_key_in_cacm = cacm_output_ref_str.split("cacm.outputs.")[-1]
                        
                        # Value to set should come from the current_step_result_data
                        # The binding_key_in_step_output is the key in the dict returned by the function/agent
                        value_to_set = None
                        if isinstance(current_step_result_data, dict):
                            value_to_set = current_step_result_data.get(binding_key_in_step_output)
                        elif len(capability_def.get('outputs', [])) == 1 and capability_def['outputs'][0]['name'] == binding_key_in_step_output:
                            # Handle cases where function returns a single value, and binding key matches that single output name
                            value_to_set = current_step_result_data
                        
                        if value_to_set is not None:
                            # CRITICAL DEBUG LOG
                            log_msg_detail = f"INFO: Orchestrator: Mapping step output key '{binding_key_in_step_output}' to CACM output key '{output_key_in_cacm}' with value type '{type(value_to_set).__name__}'."
                            print(log_msg_detail) # Print directly for immediate visibility in test output
                            log_messages.append(log_msg_detail)
                            final_cacm_outputs[output_key_in_cacm] = {"value": value_to_set, "description": f"Output from {capability_ref} via step {step_id}"}
                        else:
                            log_messages.append(f"WARN: Orchestrator: Output '{binding_key_in_step_output}' from step '{step_id}' not found in result or was None. Cannot map to CACM output '{output_key_in_cacm}'.")
            else:
                 log_messages.append(f"WARN: Orchestrator: Step '{step_id}' for capability '{capability_ref}' produced no result data (or result was None).")

        # Log final context summary
        if shared_context: # Ensure shared_context exists
            shared_context.log_context_summary() 
            log_messages.append(f"INFO: Orchestrator: SharedContext summary logged for session {shared_context.get_session_id()}")

        log_messages.append("INFO: Orchestrator: Execution completed.")
        return True, log_messages, final_cacm_outputs

    async def get_or_create_agent_instance(self, agent_name_key: str, context_data_for_creation: Optional[Dict[str, any]] = None) -> Optional[Agent]:
        """
        Retrieves an existing agent instance or creates a new one if not found.
        This is called by agents wanting to communicate with other agents.
        """
        if agent_name_key in self.agent_instances:
            self.logger.info(f"Orchestrator: Returning existing instance of agent '{agent_name_key}'.")
            return self.agent_instances[agent_name_key]
        
        if agent_name_key in self.agents: # Check against registered agent classes
            self.logger.info(f"Orchestrator: Dynamically creating new instance of agent '{agent_name_key}'. Context for creation (if any): {context_data_for_creation}")
            agent_class = self.agents[agent_name_key]
            instance = agent_class(self.kernel_service)
            instance.set_agent_manager(self)
            self.agent_instances[agent_name_key] = instance
            
            # Optional: Call a specific initialization method on the agent if it needs context
            # For example: if hasattr(instance, 'custom_init_with_context'):
            #    await instance.custom_init_with_context(context_data_for_creation if context_data_for_creation else {})
            
            return instance
        else:
            self.logger.error(f"Orchestrator: Agent class for '{agent_name_key}' not found in registered agents.")
            return None

if __name__ == '__main__':
    import os
    import sys

    import os
    import sys
    import asyncio # Added for async run_cacm

    # Setup logging for the __main__ block
    # logging.basicConfig(level=logging.INFO) # Already done by the first logger_main line
    logger_main = logging.getLogger("__main__") # Ensure logger_main is defined to avoid NameError
    # The previous change assumed logging was already configured, but it's safer to ensure it here or at top of __main__
    if not logging.getLogger().hasHandlers(): # Check if root logger has handlers
        logging.basicConfig(level=logging.INFO)


    # Determine the base directory of the project
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR)) # Up two levels: orchestrator -> cacm_adk_core -> project root
    if BASE_DIR not in sys.path: # Ensure path is added only once if script is re-run in some contexts
        sys.path.insert(0, BASE_DIR)

    # Instantiate KernelService
    kernel_service_instance = KernelService()

    # Instantiate Orchestrator with KernelService
    orch = Orchestrator(kernel_service=kernel_service_instance, load_catalog_on_init=True)
    orch.logger = logger_main # Assign logger to orchestrator instance for its own logs if it uses self.logger


    # --- Test for execute_cacm (existing synchronous direct call path) ---
    # This part remains for testing the old path, though not the focus of current changes.
    logger_main.info("\n--- Testing execute_cacm (Legacy Synchronous Path for specific template) ---")
    template_file_direct = os.path.join(BASE_DIR, "cacm_library/templates/basic_ratio_analysis_template.json")
    sample_input_data_direct = {
        "financialStatementData": {
            "currentAssets": 2000.0, "currentLiabilities": 1000.0,
            "totalDebt": 1500.0, "totalEquity": 2500.0
        }
    }
    if not os.path.exists(template_file_direct):
        logger_main.error(f"Template file does not exist at {template_file_direct}")
    else:
        result_direct = orch.execute_cacm(
           template_path=template_file_direct,
           input_data=sample_input_data_direct
        )
        logger_main.info(f"Orchestrator execute_cacm result:\n{json.dumps(result_direct, indent=2)}")

    # --- Test for run_cacm (new asynchronous workflow execution path) ---
    logger_main.info("\n--- Testing run_cacm (Asynchronous Workflow Path) ---")
    # Create a sample CACM instance data that uses an agent
    # (assuming 'urn:adk:capability:financial_ratios_calculator:v1' is updated to use AnalysisAgent)
    # and we add a new capability for DataIngestionAgent.
    # Let's assume a capability "urn:adk:capability:data_ingestor:v1" exists and is mapped to DataIngestionAgent.
    # For this test, we'll need to ensure such a capability is in the catalog or handle it if not.
    # For simplicity, let's assume it is, or the test will show it failing to find it if not.
    # To make this test runnable without modifying the catalog just for a test,
    # we can define a placeholder capability in the orchestrator's catalog for testing if needed,
    # or ensure the catalog file is updated. For now, let's draft the CACM.

    # We need to add an entry for DataIngestionAgent in the catalog for this to fully work.
    # Let's assume "urn:adk:capability:basic_document_ingestor:v1" will be its ID.
    # (This would ideally be added to compute_capability_catalog.json in a prior step if not there)
    # Removing the temporary addition of "urn:adk:capability:basic_document_ingestor:v1"
    # as the new test workflow does not use DataIngestionAgent.
    # if "urn:adk:capability:basic_document_ingestor:v1" not in orch.compute_catalog:
    #     orch.compute_catalog["urn:adk:capability:basic_document_ingestor:v1"] = {
    #         "id": "urn:adk:capability:basic_document_ingestor:v1",
    #         "name": "Basic Document Ingestor (Agent)",
    #         "description": "Ingests a document and updates shared context.",
    #         "agent_type": "DataIngestionAgent",
    #         "inputs": [
    #             {"name": "document_type", "type": "string", "description": "Type of the document (e.g., 10K_FILING)."},
    #             {"name": "document_id", "type": "string", "description": "Unique ID for the document."}
    #         ],
    #         "outputs": [ # DataIngestionAgent returns this structure
    #             {"name": "ingestion_status", "type": "object", "description": "Status of ingestion."}
    #         ]
    #     }
    #     logger_main.info("Added temporary 'urn:adk:capability:basic_document_ingestor:v1' to catalog for test.")

    # Load the new test workflow
    # sample_cacm_instance_for_agent = {} # This will be loaded specifically for the MSFT workflow
    # test_workflow_path = os.path.join(BASE_DIR, "examples/test_integrated_agents_workflow.json")
    # if not os.path.exists(test_workflow_path):
    #     logger_main.error(f"Test workflow file not found: {test_workflow_path}")
    #     # Exiting or skipping test if file not found
    # else:
    #     with open(test_workflow_path, 'r') as f:
    #         sample_cacm_instance_for_agent = json.load(f)
    #     logger_main.info(f"Loaded test workflow from: {test_workflow_path}")

    # Create a dummy validator if needed, or ensure Orchestrator handles it being None for this test
    # For this test, let's assume validation is not the focus and Orchestrator init handles validator=None
    if orch.validator is None:
        logger_main.warning("Orchestrator validator is None. CACM instance validation will be skipped in run_cacm.")
        # Mock a validator that always returns true if strict validation is an issue for this test
        class MockValidator:
            schema = True # Dummy attribute
            def validate_cacm_against_schema(self, data): return True, []
        orch.validator = MockValidator()


    async def run_agent_test():
        logger_main.info("\n--- Orchestrator Test: MSFT Comprehensive Analysis Workflow ---")
        msft_workflow_path = os.path.join(BASE_DIR, "examples/msft_comprehensive_analysis_workflow.json")

        if not os.path.exists(msft_workflow_path):
            logger_main.error(f"MSFT comprehensive workflow file not found: {msft_workflow_path}")
            return

        with open(msft_workflow_path, 'r') as f:
            msft_cacm_instance = json.load(f)

        logger_main.info(f"Loaded MSFT comprehensive workflow from: {msft_workflow_path}")

        success_msft, logs_msft, outputs_msft = await orch.run_cacm(msft_cacm_instance)

        logger_main.info(f"MSFT Comprehensive Analysis test success: {success_msft}")
        logger_main.info(f"MSFT Comprehensive Analysis test logs:\n" + "\n".join(logs_msft))
        logger_main.info(f"MSFT Comprehensive Analysis test outputs:\n{json.dumps(outputs_msft, indent=2)}")

        # Commenting out other test runs to focus output
        # # Test for Integrated FundamentalAnalystAgent & SNCAnalystAgent
        # logger_main.info("\n--- Orchestrator Test: Integrated FAA & SNCAA Workflow ---")
        # test_integrated_workflow_path = os.path.join(BASE_DIR, "examples/test_integrated_agents_workflow.json")
        # if not os.path.exists(test_integrated_workflow_path):
        #     logger_main.error(f"Test workflow file not found: {test_integrated_workflow_path}")
        # else:
        #     with open(test_integrated_workflow_path, 'r') as f:
        #         integrated_cacm_instance = json.load(f)
        #     success_integrated, logs_integrated, outputs_integrated = await orch.run_cacm(integrated_cacm_instance)
        #     logger_main.info(f"Integrated FAA & SNCAA test success: {success_integrated}")
        #     logger_main.info(f"Integrated FAA & SNCAA test logs:\n" + "\n".join(logs_integrated))
        #     logger_main.info(f"Integrated FAA & SNCAA test outputs:\n{json.dumps(outputs_integrated, indent=2)}")

        # # Test for DataIngestionAgent
        # logger_main.info("\n--- Orchestrator Test: DataIngestionAgent Workflow ---")
        # test_dia_workflow_path = os.path.join(BASE_DIR, "examples/test_data_ingestion_agent_workflow.json")
        # if not os.path.exists(test_dia_workflow_path):
        #     logger_main.error(f"Test workflow file not found: {test_dia_workflow_path}")
        # else:
        #     with open(test_dia_workflow_path, 'r') as f:
        #         dia_cacm_instance = json.load(f)
        #     success_dia, logs_dia, outputs_dia = await orch.run_cacm(dia_cacm_instance)
        #     logger_main.info(f"DataIngestionAgent test success: {success_dia}")
        #     logger_main.info(f"DataIngestionAgent test logs:\n" + "\n".join(logs_dia))
        #     logger_main.info(f"DataIngestionAgent test outputs:\n{json.dumps(outputs_dia, indent=2)}")

        # # Test for CatalystWrapperAgent
        # logger_main.info("\n--- Orchestrator Test: CatalystWrapperAgent Workflow ---")
        # test_cwa_workflow_path = os.path.join(BASE_DIR, "examples/test_catalyst_wrapper_agent_workflow.json")
        # if not os.path.exists(test_cwa_workflow_path):
        #     logger_main.error(f"Test workflow file not found: {test_cwa_workflow_path}")
        # else:
        #     with open(test_cwa_workflow_path, 'r') as f:
        #         cwa_cacm_instance = json.load(f)
        #     success_cwa, logs_cwa, outputs_cwa = await orch.run_cacm(cwa_cacm_instance)
        #     logger_main.info(f"CatalystWrapperAgent test success: {success_cwa}")
        #     logger_main.info(f"CatalystWrapperAgent test logs:\n" + "\n".join(logs_cwa))
        #     logger_main.info(f"CatalystWrapperAgent test outputs:\n{json.dumps(outputs_cwa, indent=2)}")

    asyncio.run(run_agent_test())
