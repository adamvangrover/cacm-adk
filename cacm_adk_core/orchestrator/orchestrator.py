# cacm_adk_core/orchestrator/orchestrator.py
import json
import random
from typing import List, Dict, Any, Tuple, Callable # Added Callable
import importlib # Added

from cacm_adk_core.validator.validator import Validator
# Assuming basic_functions might be directly imported if needed, but registration handles it
# from cacm_adk_core.compute_capabilities import basic_functions
from cacm_adk_core.compute_capabilities import financial_ratios # For direct call

class Orchestrator:
    def __init__(self, validator: Validator = None, catalog_filepath="config/compute_capability_catalog.json", load_catalog_on_init=True): # Validator optional, added load_catalog_on_init
        self.validator = validator
        self.compute_catalog = {} # Initialize as empty dict
        self.capability_function_map: Dict[str, Callable] = {}
        
        if load_catalog_on_init: # Conditional loading
            self.load_compute_capability_catalog(catalog_filepath)
            self._register_capabilities()
        else:
            # Simplified mapping for cases where full catalog isn't loaded (e.g. direct execution)
             self.capability_function_map = {
                "urn:adk:capability:financial_ratios_calculator:v1": financial_ratios.calculate_basic_ratios
                # This specific URN is not in basic_ratio_analysis_template.json's workflow steps,
                # but represents the overall capability of the financial_ratios.py module.
                # The direct call logic in execute_cacm will use financial_ratios.calculate_basic_ratios directly.
            }


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

    def run_cacm(self, cacm_instance_data: dict) -> Tuple[bool, List[str], Dict[str, Any]]:
        log_messages: List[str] = []
        final_cacm_outputs: Dict[str, Any] = {} # Renamed from mocked_final_outputs
        step_outputs: Dict[str, Any] = {} # Added: To store outputs of each step

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
            capability_ref = step.get('computeCapabilityRef') # Ensure this key exists
            
            log_messages.append(f"INFO: Orchestrator: --- Executing Step '{step_id}': {description} ---")
            
            if not capability_ref:
                log_messages.append(f"ERROR: Orchestrator: Step '{step_id}' is missing 'computeCapabilityRef'. Skipping.")
                continue

            log_messages.append(f"INFO: Orchestrator:   Compute Capability: {capability_ref}")

            if capability_ref in self.capability_function_map:
                log_messages.append(f"INFO: Orchestrator: Attempting to execute real function for {capability_ref}")
                target_function = self.capability_function_map[capability_ref]
                function_args: Dict[str, Any] = {}
                capability_def = self.compute_catalog.get(capability_ref)
                
                if not capability_def: # Should not happen if it's in capability_function_map
                    log_messages.append(f"ERROR: Orchestrator: Capability definition not found in catalog for '{capability_ref}', though function was registered. Skipping.")
                    continue

                # Input Resolution & Type Conversion
                step_input_bindings = step.get('inputBindings', {})
                for func_param_def in capability_def.get('inputs', []):
                    param_name = func_param_def['name']
                    param_type = func_param_def['type']
                    is_optional = func_param_def.get('optional', False)
                    
                    binding_value_source = step_input_bindings.get(param_name)
                    resolved_value: Any = None
                    value_found = False

                    if binding_value_source:
                        if isinstance(binding_value_source, str) and binding_value_source.startswith("cacm.inputs."):
                            key_parts = binding_value_source.split("cacm.inputs.")[-1].split('.')
                            current_data = cacm_instance_data.get("inputs", {})
                            for i, part in enumerate(key_parts):
                                if isinstance(current_data, dict):
                                    current_data = current_data.get(part)
                                else: # Path is too deep or incorrect structure
                                    current_data = None; break
                            if current_data is not None: # Value could be at top level or under "value"
                                if isinstance(current_data, dict) and "value" in current_data:
                                    resolved_value = current_data.get("value")
                                else: # Assume direct value
                                    resolved_value = current_data
                                value_found = True
                        elif isinstance(binding_value_source, str) and binding_value_source.startswith("steps."):
                            parts = binding_value_source.split('.')
                            if len(parts) == 4 and parts[1] and parts[3]: # e.g., steps.stepA.outputs.result
                                prev_step_id, _, prev_output_name = parts[1], parts[2], parts[3]
                                resolved_value = step_outputs.get(prev_step_id, {}).get(prev_output_name)
                                if resolved_value is not None: value_found = True
                            else:
                                log_messages.append(f"WARN: Orchestrator: Invalid step binding format: {binding_value_source}")
                        else: # Direct value in binding (less common for this structure, but possible)
                            resolved_value = binding_value_source
                            value_found = True
                    
                    if not value_found and not is_optional:
                        log_messages.append(f"ERROR: Orchestrator: Missing required input '{param_name}' for {capability_ref} in step '{step_id}'.")
                        # Potentially skip execution or let function handle missing args if designed for it
                        function_args[param_name] = None # Or skip adding to args
                        continue # Or set a flag to prevent execution

                    if value_found:
                        try:
                            if param_type == 'float' and resolved_value is not None:
                                coerced_value = float(resolved_value)
                            elif param_type == 'integer' and resolved_value is not None:
                                coerced_value = int(resolved_value)
                            # Add more coercions if needed (bool, string are often direct)
                            else:
                                coerced_value = resolved_value # Assume string or already correct type
                            function_args[param_name] = coerced_value
                        except ValueError as ve:
                            log_messages.append(f"ERROR: Orchestrator: Type coercion failed for param '{param_name}' (value: {resolved_value}) to type '{param_type}': {ve}")
                            if not is_optional: return False, log_messages, final_cacm_outputs # Fail fast on type error for required param
                            function_args[param_name] = None # Or default / skip
                
                # Handle optional parameters not provided - functions should have defaults
                for func_param_def in capability_def.get('inputs', []):
                    param_name = func_param_def['name']
                    if func_param_def.get('optional', False) and param_name not in function_args:
                        # If function has default, it will be used. Otherwise, it might error.
                        # Good practice for registered functions to have defaults for optional params.
                        log_messages.append(f"INFO: Orchestrator: Optional parameter '{param_name}' not provided for {capability_ref}. Function default will be used if any.")


                try:
                    result = target_function(**function_args)
                    log_messages.append(f"INFO: Orchestrator:   Executed {capability_ref}, result: {result}")
                    
                    current_step_outputs: Dict[str, Any] = {}
                    if result is not None:
                        # Assuming single output functions for now as per catalog examples
                        if len(capability_def.get('outputs', [])) == 1:
                            cap_output_def = capability_def['outputs'][0]
                            current_step_outputs[cap_output_def['name']] = result
                        elif isinstance(result, dict): # For functions returning a dict of multiple outputs
                            current_step_outputs = result
                        else: # Single result not matching a dict, and more than one output defined - ambiguous
                            log_messages.append(f"WARN: Orchestrator: Output structure from {capability_ref} ({type(result)}) not directly mappable to multiple outputs definition. Storing raw result under 'default_output'.")
                            if capability_def.get('outputs'): # If outputs are defined, use first as key
                                 current_step_outputs[capability_def['outputs'][0]['name']] = result
                            else: # No outputs defined in catalog, but function returned something
                                 current_step_outputs["function_result"] = result


                    step_outputs[step_id] = current_step_outputs
                    
                    # Map to final_cacm_outputs
                    for binding_key, cacm_output_ref_str in step.get('outputBindings', {}).items():
                        if isinstance(cacm_output_ref_str, str) and cacm_output_ref_str.startswith("cacm.outputs."):
                            output_key_in_cacm = cacm_output_ref_str.split("cacm.outputs.")[-1]
                            # The binding_key (e.g. "model_score_output") should match a key in current_step_outputs
                            value_to_set = current_step_outputs.get(binding_key)
                            if value_to_set is not None:
                                final_cacm_outputs[output_key_in_cacm] = {"value": value_to_set, "description": f"Output from {capability_ref} via step {step_id}"}
                                log_messages.append(f"INFO: Orchestrator: Mapped step output '{binding_key}' to CACM output '{output_key_in_cacm}'.")
                            else:
                                log_messages.append(f"WARN: Orchestrator: Output '{binding_key}' from step '{step_id}' not found or was None, cannot map to CACM output '{output_key_in_cacm}'.")
                
                except Exception as e:
                    log_messages.append(f"ERROR: Orchestrator: Executing {capability_ref} with args {function_args} failed: {e}")
                    # Decide if workflow should continue or stop on error
            
            else: # Fallback to mocking for this step's outputs that map to final CACM outputs
                log_messages.append(f"INFO: Orchestrator:   Capability '{capability_ref}' not found in registered functions. Using mock logic for direct CACM outputs.")
                for _binding_name, cacm_output_ref in step.get('outputBindings', {}).items():
                    if isinstance(cacm_output_ref, str) and cacm_output_ref.startswith("cacm.outputs."):
                        output_key = cacm_output_ref.split("cacm.outputs.")[-1]
                        mocked_value: Any = None
                        description_text = f"Mocked output for {output_key} (capability {capability_ref} not executed)"

                        # Simplified mocking logic from before
                        if "score" in output_key.lower(): mocked_value = random.randint(550, 820)
                        elif "segment" in output_key.lower() or "category" in output_key.lower(): mocked_value = random.choice(["Low Risk", "Medium Risk", "High Risk"])
                        elif "indicator" in output_key.lower() or "flag" in output_key.lower(): mocked_value = random.choice([True, False])
                        else: mocked_value = f"Mocked String Value for {output_key}"
                        
                        final_cacm_outputs[output_key] = {"value": mocked_value, "description": description_text}
                        log_messages.append(f"INFO: Orchestrator:     Mocked CACM Output '{output_key}' = {mocked_value}")

        log_messages.append("INFO: Orchestrator: Execution completed.")
        return True, log_messages, final_cacm_outputs

if __name__ == '__main__':
    import os
    import sys

    # Determine the base directory of the project to construct absolute paths
    # This assumes orchestrator.py is in cacm_adk_core/orchestrator/
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    # Correct BASE_DIR to point to the project root '/app'
    # cacm_adk_core/orchestrator -> cacm_adk_core -> /app
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, BASE_DIR) # Add project root to Python path

    # No validator needed for this direct execution path if we simplify
    # val = Validator(schema_filepath=SCHEMA_FILE) 
    orch = Orchestrator(load_catalog_on_init=False) # Pass validator=None, and skip catalog loading

    # Define the path to the template and the input data
    # Path should be relative to the project root, or use absolute paths
    template_file = os.path.join(BASE_DIR, "cacm_library/templates/basic_ratio_analysis_template.json")
    
    sample_input_data = {
        "financialStatementData": {
            "currentAssets": 2000.0,
            "currentLiabilities": 1000.0,
            "totalDebt": 1500.0,
            "totalEquity": 2500.0
        }
    }

    print(f"Attempting to execute CACM template: {template_file}")
    if not os.path.exists(template_file):
        print(f"ERROR: Template file does not exist at {template_file}")
    else:
        result = orch.execute_cacm(
           template_path=template_file,
           input_data=sample_input_data
        )
        print("\n--- Orchestrator execute_cacm Result (Success Case) ---")
        print(json.dumps(result, indent=2))

    # Test with division by zero for current_liabilities
    sample_input_div_zero_cl = {
        "financialStatementData": {
            "currentAssets": 2000.0,
            "currentLiabilities": 0.0, 
            "totalDebt": 1500.0,
            "totalEquity": 2500.0
        }
    }
    print(f"\nAttempting to execute CACM with Current Liabilities = 0")
    result_div_zero_cl = orch.execute_cacm(
       template_path=template_file, # Assuming template_file path is correct from above
       input_data=sample_input_div_zero_cl
    )
    print("\n--- Orchestrator execute_cacm Result (Current Liabilities Zero) ---")
    print(json.dumps(result_div_zero_cl, indent=2))

    # Test with missing key from financialStatementData
    sample_input_missing_key = {
        "financialStatementData": {
            # "currentAssets": 2000.0, # Missing
            "currentLiabilities": 1000.0,
            "totalDebt": 1500.0,
            "totalEquity": 2500.0
        }
    }
    print(f"\nAttempting to execute CACM with missing 'currentAssets'")
    result_missing_key = orch.execute_cacm(
       template_path=template_file, # Assuming template_file path is correct
       input_data=sample_input_missing_key
    )
    print("\n--- Orchestrator execute_cacm Result (Missing Key in financialStatementData) ---")
    print(json.dumps(result_missing_key, indent=2))
    
    # Test with financialStatementData missing entirely
    sample_input_missing_fsd = {}
    print(f"\nAttempting to execute CACM with missing 'financialStatementData'")
    result_missing_fsd = orch.execute_cacm(
       template_path=template_file, # Assuming template_file path is correct
       input_data=sample_input_missing_fsd
    )
    print("\n--- Orchestrator execute_cacm Result (Missing financialStatementData) ---")
    print(json.dumps(result_missing_fsd, indent=2))
