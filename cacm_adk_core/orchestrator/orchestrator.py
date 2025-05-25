# cacm_adk_core/orchestrator/orchestrator.py
import json
import random
from typing import List, Dict, Any, Tuple, Callable # Added Callable
import importlib # Added

from cacm_adk_core.validator.validator import Validator
# Assuming basic_functions might be directly imported if needed, but registration handles it
# from cacm_adk_core.compute_capabilities import basic_functions

class Orchestrator:
    def __init__(self, validator: Validator, catalog_filepath="config/compute_capability_catalog.json"):
        self.validator = validator
        self.compute_catalog = None
        self.load_compute_capability_catalog(catalog_filepath)
        self.capability_function_map: Dict[str, Callable] = {} # Added
        self._register_capabilities() # Added

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
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
    SCHEMA_FILE = os.path.join(BASE_DIR, "cacm_standard/cacm_schema_v0.2.json")
    CATALOG_FILE = os.path.join(BASE_DIR, "config/compute_capability_catalog.json")

    val = Validator(schema_filepath=SCHEMA_FILE) 
    if not val.schema:
        print("CRITICAL: Could not load CACM Schema for Orchestrator example. Exiting.")
    else:
        orch = Orchestrator(validator=val, catalog_filepath=CATALOG_FILE) 
        if orch.compute_catalog is None : 
             print("CRITICAL: Compute Capability Catalog not loaded properly. Check path & file. Exiting.")
        else:
            # Test with a CACM that uses registered functions
            test_exec_cacm = {
                "cacmId": "exec-test-001", "version": "1.0.0", "name": "Function Execution Test",
                "description": "Testing real function execution.",
                "metadata": {"creationDate": "2023-03-17T10:00:00Z"},
                "inputs": {
                    "inputNumerator": {"value": 100.0, "type": "float", "description": "Numerator for ratio"},
                    "inputDenominator": {"value": 20.0, "type": "float", "description": "Denominator for ratio"},
                    "metricForScoring": {"value": 75.0, "type": "float", "description": "Metric for simple scorer"}
                },
                "outputs": { 
                    "calculatedTestRatio": {"description": "Result of cc:CalculateRatio_v1", "type": "float"},
                    "scoringAssessment": {"description": "Result of cc:SimpleScorer_v1", "type": "string"}
                },
                "workflow": [
                    {
                        "stepId": "step_ratio", "description": "Calculate a ratio.",
                        "computeCapabilityRef": "cc:CalculateRatio_v1",
                        "inputBindings": {
                            "numerator": "cacm.inputs.inputNumerator.value",
                            "denominator": "cacm.inputs.inputDenominator.value"
                        },
                        "outputBindings": {"result": "cacm.outputs.calculatedTestRatio"} 
                        # This binding key 'result' must match the output name in catalog for cc:CalculateRatio_v1
                    },
                    {
                        "stepId": "step_score_metric", "description": "Score a metric.",
                        "computeCapabilityRef": "cc:SimpleScorer_v1",
                        "inputBindings": {
                            "financial_metric": "cacm.inputs.metricForScoring.value",
                            "threshold": 50.0, # Direct value example
                            "operator": ">=" 
                        },
                        "outputBindings": {"assessment": "cacm.outputs.scoringAssessment"}
                        # This binding key 'assessment' must match the output name in catalog for cc:SimpleScorer_v1
                    }
                ]
            }
            print("\n--- Testing Orchestrator with real function execution ---")
            success, logs, outputs = orch.run_cacm(test_exec_cacm)
            print(f"Run Success: {success}")
            print("Logs:")
            for log_entry in logs: print(f"  {log_entry}")
            print("Final CACM Outputs:")
            print(json.dumps(outputs, indent=2))

            # Test with a step output feeding into another
            test_chained_exec_cacm = {
                "cacmId": "exec-test-002", "version": "1.0.0", "name": "Chained Function Execution Test",
                "description": "Testing real function execution where one step uses another's output.",
                "metadata": {"creationDate": "2023-03-18T10:00:00Z"},
                "inputs": {
                    "initialNum": {"value": 200.0, "type": "float"},
                    "divisor": {"value": 4.0, "type": "float"}
                },
                "outputs": { 
                    "finalAssessment": {"description": "Result of cc:SimpleScorer_v1 on a calculated ratio", "type": "string"}
                },
                "workflow": [
                    {
                        "stepId": "s1_calc_ratio", "description": "Calculate an intermediate ratio.",
                        "computeCapabilityRef": "cc:CalculateRatio_v1",
                        "inputBindings": {
                            "numerator": "cacm.inputs.initialNum.value",
                            "denominator": "cacm.inputs.divisor.value"
                        },
                        "outputBindings": {"result": "intermediate_ratio_output"} # Not a final CACM output, just for step_outputs
                    },
                    {
                        "stepId": "s2_score_ratio", "description": "Score the calculated ratio.",
                        "computeCapabilityRef": "cc:SimpleScorer_v1",
                        "inputBindings": {
                            "financial_metric": "steps.s1_calc_ratio.outputs.result", # Using output from previous step
                            "threshold": 40.0, 
                            "operator": ">" 
                        },
                        "outputBindings": {"assessment": "cacm.outputs.finalAssessment"}
                    }
                ]
            }
            print("\n--- Testing Orchestrator with chained real function execution ---")
            success_chained, logs_chained, outputs_chained = orch.run_cacm(test_chained_exec_cacm)
            print(f"Chained Run Success: {success_chained}")
            print("Chained Logs:")
            for log_entry in logs_chained: print(f"  {log_entry}")
            print("Chained Final CACM Outputs:")
            print(json.dumps(outputs_chained, indent=2))
