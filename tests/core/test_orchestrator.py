# tests/core/test_orchestrator.py
import unittest
# No need to mock print anymore as logs are returned
# from unittest.mock import patch 
import os
import json # For inspecting outputs if needed, and for dummy catalog

try:
    from cacm_adk_core.orchestrator.orchestrator import Orchestrator
    from cacm_adk_core.validator.validator import Validator
except ImportError:
    Orchestrator = None
    Validator = None

# Assuming schema and catalog are relative to project root for tests
SCHEMA_FILE_PATH_FOR_TEST = "cacm_standard/cacm_schema_v0.2.json"
# Use a dedicated test catalog to avoid issues with main catalog changes or absence
TEST_CATALOG_FILENAME = "test_compute_capability_catalog.json" 


class TestOrchestrator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if Orchestrator is None or Validator is None:
            raise unittest.SkipTest("Orchestrator or Validator component not found or import error.")
        
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        schema_path = os.path.join(base_dir, SCHEMA_FILE_PATH_FOR_TEST)
        
        # Create a dedicated test catalog file for these tests
        cls.test_catalog_path = os.path.join(os.path.dirname(__file__), TEST_CATALOG_FILENAME)
        test_catalog_content = {
            "computeCapabilities": [
                {"id": "dummy:TestCapability", "name": "Dummy Test Capability", "description": "For testing.", "inputs": {}, "outputs": {}},
                {"id": "score:Capability", "name": "Scoring Cap", "description": "For testing score outputs.", "inputs": {}, "outputs": {}},
                {"id": "segment:Capability", "name": "Segmenting Cap", "description": "For testing segment outputs.", "inputs": {}, "outputs": {}}
            ]
        }
        with open(cls.test_catalog_path, "w") as f:
            json.dump(test_catalog_content, f)

        if not os.path.exists(schema_path):
            # This should ideally not happen if project structure is correct
            raise unittest.SkipTest(f"Schema file not found for tests: {schema_path}")
        
        cls.validator = Validator(schema_filepath=schema_path)
        if not cls.validator.schema:
             raise unittest.SkipTest(f"Could not load schema at {schema_path} for Orchestrator tests.")
        
        # Orchestrator now uses the dedicated test catalog
        cls.orchestrator = Orchestrator(validator=cls.validator, catalog_filepath=cls.test_catalog_path)

    @classmethod
    def tearDownClass(cls):
        # Clean up the dedicated test catalog file
        if hasattr(cls, 'test_catalog_path') and os.path.exists(cls.test_catalog_path):
            try:
                os.remove(cls.test_catalog_path)
                # print(f"Cleaned up test catalog: {cls.test_catalog_path}")
            except OSError as e:
                print(f"Error cleaning up test catalog {cls.test_catalog_path}: {e}")

    def test_orchestrator_initialization_and_catalog_loading(self):
        self.assertIsNotNone(self.orchestrator, "Orchestrator should be initializable")
        self.assertIsNotNone(self.orchestrator.validator, "Orchestrator should have a validator")
        self.assertIsNotNone(self.orchestrator.compute_catalog, "Compute catalog should be loaded")
        self.assertTrue(len(self.orchestrator.compute_catalog) > 0, "Test compute catalog should not be empty")
        self.assertIn("dummy:TestCapability", self.orchestrator.compute_catalog.keys())


    def test_run_cacm_valid_instance_with_mocked_outputs(self):
        valid_cacm = {
            "cacmId": "test-orch-valid-001", "version": "1.0.0", "name": "Test Valid Run with Outputs",
            "description": "Valid CACM for orchestrator run test with mocked outputs.",
            "metadata": {"creationDate": "2023-01-01T12:00:00Z"},
            "inputs": {"in1": {"description": "d", "type": "string"}},
            "outputs": { 
                "overallScore": {"description":"final score", "type": "number"},
                "customerSegment": {"description":"customer segment", "type": "string"},
                "isValidIndicator": {"description":"validity flag", "type": "boolean"},
                "genericOutput": {"description":"some other output", "type": "string"}
            },
            "workflow": [{
                "stepId": "s1", "description": "Generate multiple outputs", 
                "computeCapabilityRef": "dummy:TestCapability", 
                "inputBindings": {}, 
                "outputBindings": {
                    "step_score_out": "cacm.outputs.overallScore",
                    "step_segment_out": "cacm.outputs.customerSegment",
                    "step_indicator_out": "cacm.outputs.isValidIndicator",
                    "step_generic_out": "cacm.outputs.genericOutput"
                }
            }]
        }
        
        success, logs, outputs = self.orchestrator.run_cacm(valid_cacm)
        
        self.assertTrue(success, "run_cacm should return True for a valid instance.")
        self.assertTrue(any("INFO: Orchestrator: CACM instance is valid." in log for log in logs), "Missing 'valid instance' log.")
        self.assertTrue(any("INFO: Orchestrator: --- Executing Step 's1'" in log for log in logs), "Missing 'executing step' log.")
        self.assertTrue(any("INFO: Orchestrator: Simulated execution completed." in log for log in logs), "Missing 'execution completed' log.")
        
        # Check overallScore (mocked as int)
        self.assertIn("overallScore", outputs, "overallScore key missing in outputs.")
        self.assertIn("value", outputs["overallScore"], "'value' missing in overallScore output.")
        self.assertIsInstance(outputs["overallScore"]["value"], int, "overallScore value should be an int.")
        self.assertTrue(any("Mocked CACM Output 'overallScore'" in log for log in logs), "Missing log for overallScore mocking.")

        # Check customerSegment (mocked as str from list)
        self.assertIn("customerSegment", outputs, "customerSegment key missing in outputs.")
        self.assertIn("value", outputs["customerSegment"], "'value' missing in customerSegment output.")
        self.assertIsInstance(outputs["customerSegment"]["value"], str, "customerSegment value should be a str.")
        self.assertTrue(any(val in outputs["customerSegment"]["value"] for val in ["Low Risk", "Medium Risk", "High Risk", "Category A", "Category B"]), "customerSegment value not from expected choices.")
        self.assertTrue(any("Mocked CACM Output 'customerSegment'" in log for log in logs), "Missing log for customerSegment mocking.")

        # Check isValidIndicator (mocked as bool)
        self.assertIn("isValidIndicator", outputs, "isValidIndicator key missing in outputs.")
        self.assertIn("value", outputs["isValidIndicator"], "'value' missing in isValidIndicator output.")
        self.assertIsInstance(outputs["isValidIndicator"]["value"], bool, "isValidIndicator value should be a bool.")
        self.assertTrue(any("Mocked CACM Output 'isValidIndicator'" in log for log in logs), "Missing log for isValidIndicator mocking.")
        
        # Check genericOutput (mocked as str)
        self.assertIn("genericOutput", outputs, "genericOutput key missing in outputs.")
        self.assertIn("value", outputs["genericOutput"], "'value' missing in genericOutput output.")
        self.assertIsInstance(outputs["genericOutput"]["value"], str, "genericOutput value should be a str.")
        self.assertTrue("Mocked String Value for genericOutput" in outputs["genericOutput"]["value"], "genericOutput value mismatch.")
        self.assertTrue(any("Mocked CACM Output 'genericOutput'" in log for log in logs), "Missing log for genericOutput mocking.")


    def test_run_cacm_invalid_instance(self):
        invalid_cacm = { 
            "cacmId": "test-orch-invalid-002", "version": "1.0.0",
            # "name": "Missing Name CACM", # Name is required, making it invalid
            "description": "Invalid CACM for orchestrator run test.",
            "metadata": {"creationDate": "2023-01-01T12:00:00Z"},
            "inputs": {"in1": {"description": "d", "type": "string"}},
            "outputs": {"out1": {"description": "d", "type": "string"}},
            "workflow": [{
                "stepId": "s1", "description": "First step", 
                "computeCapabilityRef": "dummy:TestCapability",
                "inputBindings": {}, "outputBindings": {}
            }]
        }
        # This CACM is invalid because 'name' is missing.
        
        success, logs, outputs = self.orchestrator.run_cacm(invalid_cacm)
        
        self.assertFalse(success, "run_cacm should return False for an invalid instance.")
        self.assertTrue(any("ERROR: Orchestrator: CACM instance is invalid." in log for log in logs))
        self.assertTrue(any("'name' is a required property" in log for log in logs)) # Specific schema error
        self.assertEqual(outputs, {}, "Outputs should be empty for an invalid CACM run.")

if __name__ == '__main__':
    unittest.main()
