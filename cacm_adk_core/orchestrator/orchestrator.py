# cacm_adk_core/orchestrator/orchestrator.py
import json
import random # Added
from typing import List, Dict, Any, Tuple # Added

from cacm_adk_core.validator.validator import Validator

class Orchestrator:
    # __init__ and load_compute_capability_catalog remain the same as before
    def __init__(self, validator: Validator, catalog_filepath="config/compute_capability_catalog.json"):
        self.validator = validator
        self.compute_catalog = None
        self.load_compute_capability_catalog(catalog_filepath)

    def load_compute_capability_catalog(self, catalog_filepath="config/compute_capability_catalog.json"):
        # log_messages_temp = [] # Temporary for this method if it needs logging
        # This method's print statements are for server console, not captured by run_cacm's logs.
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


    def run_cacm(self, cacm_instance_data: dict) -> Tuple[bool, List[str], Dict[str, Any]]:
        log_messages: List[str] = []
        mocked_final_outputs: Dict[str, Any] = {}

        if not self.validator or not self.validator.schema:
            log_messages.append("ERROR: Orchestrator: Validator or schema not properly initialized.")
            return False, log_messages, mocked_final_outputs

        is_valid, errors = self.validator.validate_cacm_against_schema(cacm_instance_data)
        if not is_valid:
            log_messages.append("ERROR: Orchestrator: CACM instance is invalid. Cannot execute.")
            for error in errors:
                log_messages.append(f"  Validation Error: Path: {error.get('path', 'N/A')}, Message: {error.get('message', 'N/A')}")
            return False, log_messages, mocked_final_outputs

        log_messages.append("INFO: Orchestrator: CACM instance is valid. Starting simulated execution...")
        
        workflow_steps = cacm_instance_data.get("workflow", [])
        if not workflow_steps:
            log_messages.append("INFO: Orchestrator: Workflow has no steps.")
        
        for step in workflow_steps:
            step_id = step.get('stepId', 'Unknown Step')
            description = step.get('description', 'No description')
            capability_ref = step.get('computeCapabilityRef', 'No capability reference')
            
            log_messages.append(f"INFO: Orchestrator: --- Executing Step '{step_id}': {description} ---")
            log_messages.append(f"INFO: Orchestrator:   Compute Capability: {capability_ref}")

            if self.compute_catalog and capability_ref in self.compute_catalog:
                log_messages.append(f"INFO: Orchestrator:     (Capability '{capability_ref}' found in catalog: {self.compute_catalog[capability_ref].get('name')})")
            elif self.compute_catalog is not None: # Check if catalog was attempted to be loaded
                log_messages.append(f"WARN: Orchestrator:     (Capability '{capability_ref}' NOT found in catalog)")
            else: # Catalog is None
                log_messages.append(f"ERROR: Orchestrator: Compute catalog not loaded. Cannot check capability reference.")

            
            log_messages.append(f"INFO: Orchestrator:   Input Bindings: {step.get('inputBindings', {})}")
            log_messages.append(f"INFO: Orchestrator:   Output Bindings: {step.get('outputBindings', {})}")

            # Mock outputs based on outputBindings
            for _binding_name, cacm_output_ref in step.get('outputBindings', {}).items():
                if isinstance(cacm_output_ref, str) and cacm_output_ref.startswith("cacm.outputs."):
                    output_key = cacm_output_ref.split("cacm.outputs.")[-1]
                    mocked_value = None
                    description_text = f"Simulated output for {output_key}"

                    if "score" in output_key.lower():
                        mocked_value = random.randint(550, 820)
                        description_text = f"Simulated score for {output_key}"
                    elif "segment" in output_key.lower() or "category" in output_key.lower():
                        mocked_value = random.choice(["Low Risk", "Medium Risk", "High Risk", "Category A", "Category B"])
                        description_text = f"Simulated segment/category for {output_key}"
                    elif "indicator" in output_key.lower() or "flag" in output_key.lower():
                        mocked_value = random.choice([True, False])
                        description_text = f"Simulated boolean indicator for {output_key}"
                    else:
                        mocked_value = f"Mocked String Value for {output_key}"
                    
                    mocked_final_outputs[output_key] = {"value": mocked_value, "description": description_text}
                    log_messages.append(f"INFO: Orchestrator:     Mocked CACM Output '{output_key}' = {mocked_value}")


        log_messages.append("INFO: Orchestrator: Simulated execution completed.")
        return True, log_messages, mocked_final_outputs

# Update the __main__ block if it exists, to handle the new return type
if __name__ == '__main__':
    # Corrected path for direct execution from project root: python cacm_adk_core/orchestrator/orchestrator.py
    # For this to work, ensure cacm_standard and config are accessible from root.
    # The __main__ block is primarily for dev testing of this specific module.
    
    # Determine base path for resources, assuming script is in cacm_adk_core/orchestrator/
    import os
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # This should be project root
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
            test_cacm = {
                "cacmId": "orchestrator-run-test-002", "version": "1.0.0", "name": "Orchestrator Output Test",
                "description": "Testing mocked outputs from orchestrator.",
                "metadata": {"creationDate": "2023-03-16T10:00:00Z"},
                "inputs": {"param1": {"description": "d", "type": "number"}},
                "outputs": { 
                    "finalScore": {"description": "The final calculated score.", "type": "number"},
                    "riskCategory": {"description": "The category of risk.", "type": "string"}
                },
                "workflow": [{
                    "stepId": "sA", "description": "Generate score and category",
                    "computeCapabilityRef": "dummy:TestGenerateScoreAndCategory", # This dummy ref might not be in catalog
                    "inputBindings": {"input_param": "cacm.inputs.param1"},
                    "outputBindings": {
                        "model_score_output": "cacm.outputs.finalScore",
                        "model_segment_output": "cacm.outputs.riskCategory"
                    }
                }]
            }
            print("\n--- Testing Orchestrator with mocked outputs ---")
            success, logs, outputs = orch.run_cacm(test_cacm)
            print(f"Run Success: {success}")
            print("Logs:")
            for log_entry in logs: print(f"  {log_entry}")
            print("Mocked Outputs:")
            print(json.dumps(outputs, indent=2))

            # Test invalid case
            invalid_test_cacm = test_cacm.copy() # shallow copy
            del invalid_test_cacm["name"]
            success, logs, outputs = orch.run_cacm(invalid_test_cacm)
            print(f"\nRun Success (Invalid CACM): {success}")
            print("Logs (Invalid CACM):")
            for log_entry in logs: print(f"  {log_entry}")
            print("Mocked Outputs (Invalid CACM):")
            print(json.dumps(outputs, indent=2))
