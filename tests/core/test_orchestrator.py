# tests/core/test_orchestrator.py
import unittest
from unittest.mock import patch 
import os

try:
    from cacm_adk_core.orchestrator.orchestrator import Orchestrator
    from cacm_adk_core.validator.validator import Validator
except ImportError:
    Orchestrator = None
    Validator = None

# Assuming schema and catalog are relative to project root for tests
SCHEMA_FILE_PATH_FOR_TEST = "cacm_standard/cacm_schema_v0.2.json"
CATALOG_FILE_PATH_FOR_TEST = "config/compute_capability_catalog.json"


class TestOrchestrator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if Orchestrator is None or Validator is None:
            raise unittest.SkipTest("Orchestrator or Validator component not found or import error.")
        
        # Ensure schema and catalog exist for tests
        # This assumes tests are run from the project root.
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        schema_path = os.path.join(base_dir, SCHEMA_FILE_PATH_FOR_TEST)
        catalog_path = os.path.join(base_dir, CATALOG_FILE_PATH_FOR_TEST)

        if not os.path.exists(schema_path):
            raise unittest.SkipTest(f"Schema file not found for tests: {schema_path}")
        
        # If catalog is missing, create a dummy one for test initialization to pass.
        # The actual catalog content is tested by Orchestrator's own __main__ or specific catalog tests.
        if not os.path.exists(catalog_path):
            print(f"Warning: Test Orchestrator: Main catalog {catalog_path} not found. Creating dummy for init.")
            os.makedirs(os.path.dirname(catalog_path), exist_ok=True) # Ensure config dir exists
            with open(catalog_path, "w") as f:
                f.write('{"computeCapabilities": [{"id": "dummy:Test", "name": "Dummy", "description": "Dummy", "inputs": {}, "outputs": {}}]}') # Added inputs/outputs for catalog structure
            cls.created_dummy_catalog = True # Flag to potentially clean up later if needed
        else:
            cls.created_dummy_catalog = False
        
        cls.validator = Validator(schema_filepath=schema_path)
        if not cls.validator.schema:
             raise unittest.SkipTest(f"Could not load schema at {schema_path} for Orchestrator tests.")
        cls.orchestrator = Orchestrator(validator=cls.validator, catalog_filepath=catalog_path)

    @classmethod
    def tearDownClass(cls):
        # Optional: Clean up dummy catalog if it was created by tests
        if getattr(cls, 'created_dummy_catalog', False):
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            catalog_path = os.path.join(base_dir, CATALOG_FILE_PATH_FOR_TEST)
            if "dummy:Test" in (open(catalog_path).read() if os.path.exists(catalog_path) else ""): # Basic check
                 try:
                     os.remove(catalog_path)
                     print(f"Cleaned up dummy catalog: {catalog_path}")
                 except OSError as e:
                     print(f"Error cleaning up dummy catalog {catalog_path}: {e}")


    def test_orchestrator_initialization_and_catalog_loading(self):
        self.assertIsNotNone(self.orchestrator, "Orchestrator should be initializable")
        self.assertIsNotNone(self.orchestrator.validator, "Orchestrator should have a validator")
        self.assertIsNotNone(self.orchestrator.compute_catalog, "Compute catalog should be loaded")
        # Check if the catalog has at least one item (either real or dummy)
        self.assertTrue(len(self.orchestrator.compute_catalog) > 0, "Compute catalog should not be empty")
        # If not using a dummy, check for a real capability ID
        if not self.created_dummy_catalog:
             self.assertIn("model:FinancialMetricsScorer_v1", self.orchestrator.compute_catalog.keys())


    def test_run_cacm_valid_instance(self):
        # This CACM should align with schema v0.2 and use capabilities in the catalog
        # Using 'dummy:Test' if catalog was dummied, else a real one.
        capability_to_test = "dummy:Test" if self.created_dummy_catalog else "connector:LoadData_v1"

        valid_cacm = {
            "cacmId": "test-orch-valid-001", "version": "1.0.0", "name": "Test Valid Run",
            "description": "Valid CACM for orchestrator run test.",
            "metadata": {"creationDate": "2023-01-01T12:00:00Z"},
            "inputs": {"in1": {"description": "d", "type": "string"}},
            "outputs": {"out1": {"description": "d", "type": "string"}},
            "workflow": [
                {"stepId": "s1", "description": "First step", "computeCapabilityRef": capability_to_test,
                 "inputBindings": {}, "outputBindings": {}}
            ]
        }
        with patch('builtins.print') as mocked_print:
            result = self.orchestrator.run_cacm(valid_cacm)
            self.assertTrue(result, "run_cacm should return True for a valid instance.")
            # Check for some expected log messages
            logs_str = "".join([str(call) for call in mocked_print.call_args_list])
            self.assertIn("INFO: Orchestrator: CACM instance is valid.", logs_str)
            self.assertIn("INFO: Orchestrator: --- Executing Step 's1'", logs_str)
            self.assertIn(f"Compute Capability: {capability_to_test}", logs_str)
            self.assertIn("INFO: Orchestrator: Simulated execution completed.", logs_str)


    def test_run_cacm_invalid_instance(self):
        invalid_cacm = { # Missing 'name', which is required by schema
            "cacmId": "test-orch-invalid-002", "version": "1.0.0",
            "description": "Invalid CACM for orchestrator run test.",
            "metadata": {"creationDate": "2023-01-01T12:00:00Z"},
            # Making inputs, outputs, workflow valid but top-level 'name' is missing
            "inputs": {"in1": {"description": "d", "type": "string"}},
            "outputs": {"out1": {"description": "d", "type": "string"}},
            "workflow": [
                 {"stepId": "s1", "description": "First step", 
                  "computeCapabilityRef": "dummy:Test" if self.created_dummy_catalog else "connector:LoadData_v1",
                  "inputBindings": {}, "outputBindings": {}}
            ]
        }
        del invalid_cacm["inputs"] # To make it invalid per schema (inputs is required)
        
        with patch('builtins.print') as mocked_print:
            result = self.orchestrator.run_cacm(invalid_cacm)
            self.assertFalse(result, "run_cacm should return False for an invalid instance.")
            logs_str = "".join([str(call) for call in mocked_print.call_args_list])
            self.assertIn("ERROR: Orchestrator: CACM instance is invalid.", logs_str)
            self.assertIn("'name' is a required property", logs_str) # Check for specific schema error: 'name' is missing

if __name__ == '__main__':
    unittest.main()
