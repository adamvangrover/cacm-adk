# cacm_adk_core/orchestrator/orchestrator.py
import json
from cacm_adk_core.validator.validator import Validator # Assuming Validator is in this path

class Orchestrator:
    def __init__(self, validator: Validator, catalog_filepath="config/compute_capability_catalog.json"):
        """
        Initializes the Orchestrator.

        Args:
            validator: An instance of the Validator component.
            catalog_filepath: Path to the compute capability catalog JSON file.
        """
        self.validator = validator
        self.compute_catalog = None
        self.load_compute_capability_catalog(catalog_filepath)

    def load_compute_capability_catalog(self, catalog_filepath="config/compute_capability_catalog.json"):
        """ Loads the compute capability catalog from a JSON file. """
        try:
            with open(catalog_filepath, 'r') as f:
                data = json.load(f)
                self.compute_catalog = {cap['id']: cap for cap in data.get("computeCapabilities", [])}
            print(f"INFO: Orchestrator: Loaded {len(self.compute_catalog)} compute capabilities from {catalog_filepath}")
        except FileNotFoundError:
            print(f"ERROR: Orchestrator: Compute capability catalog not found at {catalog_filepath}")
            self.compute_catalog = {} # Initialize to empty if not found
        except json.JSONDecodeError:
            print(f"ERROR: Orchestrator: Could not decode JSON from catalog file {catalog_filepath}")
            self.compute_catalog = {}

    def run_cacm(self, cacm_instance_data: dict) -> bool:
        """
        Validates and then simulates the execution of a CACM instance's workflow.
        Actual computation is mocked; this method logs the steps and bindings.
        """
        if not self.validator or not self.validator.schema:
            print("ERROR: Orchestrator: Validator or schema not properly initialized.")
            return False

        is_valid, errors = self.validator.validate_cacm_against_schema(cacm_instance_data)
        if not is_valid:
            print("ERROR: Orchestrator: CACM instance is invalid. Cannot execute.")
            for error in errors:
                print(f"  Validation Error: Path: {error.get('path', 'N/A')}, Message: {error.get('message', 'N/A')}")
            return False

        print("INFO: Orchestrator: CACM instance is valid. Starting simulated execution...")
        
        workflow_steps = cacm_instance_data.get("workflow", [])
        if not workflow_steps:
            print("INFO: Orchestrator: Workflow has no steps.")
        
        for step in workflow_steps:
            step_id = step.get('stepId', 'Unknown Step')
            description = step.get('description', 'No description')
            capability_ref = step.get('computeCapabilityRef', 'No capability reference')
            
            print(f"INFO: Orchestrator: --- Executing Step '{step_id}': {description} ---")
            print(f"INFO: Orchestrator:   Compute Capability: {capability_ref}")

            if self.compute_catalog and capability_ref in self.compute_catalog:
                print(f"INFO: Orchestrator:     (Capability '{capability_ref}' found in catalog: {self.compute_catalog[capability_ref].get('name')})")
            elif self.compute_catalog:
                print(f"WARN: Orchestrator:     (Capability '{capability_ref}' NOT found in catalog)")
            
            print(f"INFO: Orchestrator:   Input Bindings: {step.get('inputBindings', {})}")
            # Future: Resolve actual data based on bindings
            print(f"INFO: Orchestrator:   Output Bindings: {step.get('outputBindings', {})}")
            # Future: Store/mock actual outputs

        print("INFO: Orchestrator: Simulated execution completed.")
        return True

if __name__ == '__main__':
    # Example Usage (requires a valid CACM JSON instance and the schema)
    # Setup validator
    val = Validator(schema_filepath="cacm_standard/cacm_schema_v0.2.json") # Assumes schema is in this path relative to execution
    if not val.schema:
        print("CRITICAL: Could not load CACM Schema for Orchestrator example. Exiting.")
    else:
        orch = Orchestrator(validator=val)
        if not orch.compute_catalog:
             print("CRITICAL: Could not load Compute Capability Catalog for Orchestrator example. Check config/compute_capability_catalog.json. Exiting.")
        else:
            # Create a minimal valid CACM for testing run_cacm
            # This should align with cacm_schema_v0.2.json and use capabilities from the catalog
            test_cacm = {
                "cacmId": "orchestrator-test-001",
                "version": "1.0.0",
                "name": "Orchestrator Run Test CACM",
                "description": "A minimal CACM to test the Orchestrator's run_cacm method.",
                "metadata": {"creationDate": "2023-03-15T10:00:00Z"},
                "inputs": {
                    "param1": {"description": "A test parameter", "type": "number"}
                },
                "outputs": {
                    "result1": {"description": "A test result", "type": "number"}
                },
                "workflow": [
                    {
                        "stepId": "step_A",
                        "description": "Load some initial data.",
                        "computeCapabilityRef": "connector:LoadData_v1",
                        "inputBindings": {"source_config": {"path": "/data/sourceA.csv"}},
                        "outputBindings": {"loaded_data_A": "steps.step_A.outputs.data"}
                    },
                    {
                        "stepId": "step_B",
                        "description": "Calculate something based on input and previous step.",
                        "computeCapabilityRef": "compute:CalculateRatio", 
                        "inputBindings": {
                            "numerator": "cacm.inputs.param1",
                            "denominator": "steps.step_A.outputs.data.someValue" 
                        },
                        "outputBindings": {"final_output": "cacm.outputs.result1"}
                    }
                ]
            }
            print("\n--- Testing Orchestrator with a minimal valid CACM ---")
            orch.run_cacm(test_cacm)

            print("\n--- Testing Orchestrator with an invalid CACM (missing 'name') ---")
            invalid_test_cacm = test_cacm.copy() # Use copy module for deepcopy if needed
            del invalid_test_cacm["name"]
            orch.run_cacm(invalid_test_cacm)
