# tests/core/test_validator.py
import unittest
import os

try:
    from cacm_adk_core.validator.validator import Validator
except ImportError:
    Validator = None

# Ensure tests can find the schema relative to the project root
# This might need adjustment based on how the test runner is invoked.
# Assuming tests are run from the project root directory.
SCHEMA_FILE_PATH = "cacm_standard/cacm_schema_v0.2.json"


class TestValidator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if Validator is None:
            raise unittest.SkipTest("Validator component not found or import error.")
        # Try to construct the absolute path to the schema file
        # This assumes the tests are run from the root of the project directory
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        schema_path = os.path.join(base_dir, SCHEMA_FILE_PATH)

        if not os.path.exists(schema_path):
            raise unittest.SkipTest(
                f"Schema file not found at resolved path: {schema_path}. Check SCHEMA_FILE_PATH and execution directory."
            )

        cls.validator = Validator(schema_filepath=schema_path)
        if not cls.validator.schema:
            # This condition might be redundant if Validator's __init__ raises an error on load failure,
            # but good for robustness if __init__ only prints and sets schema to None.
            raise unittest.SkipTest(
                f"Could not load schema at {schema_path}. Validator __init__ might have failed."
            )

    def test_validator_initialization_and_schema_loading(self):
        self.assertIsNotNone(self.validator, "Validator should be initializable")
        self.assertIsNotNone(self.validator.schema, "Schema should be loaded")
        self.assertEqual(
            self.validator.schema.get("title"), "CACM Definition"
        )  # Check a known field
        self.assertEqual(
            self.validator.schema.get("description"),
            "Schema for a Credit Analysis Capability Module (CACM). Version 0.2",
        )

    def test_valid_cacm_instance(self):
        valid_cacm = {
            "cacmId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "version": "0.2.0",
            "name": "Valid Test CACM",
            "description": "A test CACM instance that should pass validation.",
            "metadata": {"creationDate": "2023-01-01T12:00:00Z"},
            "inputs": {
                "customer_data": {
                    "description": "Customer financial data.",
                    "type": "object",
                    "schema": {
                        # "$schema": "http://json-schema.org/draft-07/schema#", # Not strictly needed here by jsonschema library for nested schemas
                        "type": "object",
                        "properties": {"income": {"type": "number"}},
                        "required": ["income"],
                    },
                }
            },
            "outputs": {
                "score": {"description": "Calculated credit score.", "type": "number"}
            },
            "workflow": [
                {
                    "stepId": "s1_calc_score",
                    "description": "Calculate initial score",
                    "computeCapabilityRef": "model:CreditScoringModel_v1",
                }
            ],
        }
        is_valid, errors = self.validator.validate_cacm_against_schema(valid_cacm)
        self.assertTrue(is_valid, f"CACM should be valid. Errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_invalid_cacm_missing_name(self):
        invalid_cacm = {
            "cacmId": "b1c2d3e4-f5g6-7890-1234-567890abcdef",
            "version": "0.2.0",
            # "name": "Missing Name CACM", # Name is required
            "description": "This CACM is invalid because it's missing the 'name' field.",
            "metadata": {"creationDate": "2023-01-01T12:00:00Z"},
            "inputs": {
                "dummy_input": {"description": "d", "type": "string"}
            },  # Made valid to isolate error
            "outputs": {
                "dummy_output": {"description": "d", "type": "string"}
            },  # Made valid
            "workflow": [
                {"stepId": "s1", "description": "d", "computeCapabilityRef": "d"}
            ],  # Made valid
        }
        is_valid, errors = self.validator.validate_cacm_against_schema(invalid_cacm)
        self.assertFalse(is_valid, "CACM should be invalid due to missing 'name'.")
        self.assertTrue(
            any(
                "'name' is a required property" in error.get("message", "")
                for error in errors
            ),
            f"Errors: {errors}",
        )

    def test_invalid_input_item_missing_type(self):
        invalid_cacm = {
            "cacmId": "c1d2e3f4-g5h6-7890-1234-567890abcdef",
            "version": "0.2.0",
            "name": "Invalid Input CACM",
            "description": "This CACM has an input item missing its 'type'.",
            "metadata": {"creationDate": "2023-01-01T12:00:00Z"},
            "inputs": {
                "bad_input": {  # 'type' is missing here
                    "description": "This input is missing its type."
                }
            },
            "outputs": {
                "dummy_output": {"description": "d", "type": "string"}
            },  # Made valid
            "workflow": [
                {"stepId": "s1", "description": "d", "computeCapabilityRef": "d"}
            ],  # Made valid
        }
        is_valid, errors = self.validator.validate_cacm_against_schema(invalid_cacm)
        self.assertFalse(
            is_valid, "CACM should be invalid due to input item missing 'type'."
        )
        self.assertTrue(
            any(
                "'type' is a required property" in error.get("message", "")
                and error.get("path", []) == ["inputs", "bad_input"]
                for error in errors
            ),
            f"Errors: {errors}",
        )

    def test_invalid_workflow_step_missing_id(self):
        invalid_cacm = {
            "cacmId": "d1e2f3g4-h5i6-7890-1234-567890abcdef",
            "version": "0.2.0",
            "name": "Invalid Workflow CACM",
            "description": "This CACM has a workflow step missing 'stepId'.",
            "metadata": {"creationDate": "2023-01-01T12:00:00Z"},
            "inputs": {
                "dummy_input": {"description": "d", "type": "string"}
            },  # Made valid
            "outputs": {
                "dummy_output": {"description": "d", "type": "string"}
            },  # Made valid
            "workflow": [
                {  # 'stepId' is missing here
                    "description": "A step without an ID.",
                    "computeCapabilityRef": "ref:SomeRef",
                }
            ],
        }
        is_valid, errors = self.validator.validate_cacm_against_schema(invalid_cacm)
        self.assertFalse(
            is_valid, "CACM should be invalid due to workflow step missing 'stepId'."
        )
        # Path should be ['workflow', 0] because it's the first item in the array
        self.assertTrue(
            any(
                "'stepId' is a required property" in error.get("message", "")
                and error.get("path", []) == ["workflow", 0]
                for error in errors
            ),
            f"Errors: {errors}",
        )


if __name__ == "__main__":
    unittest.main()
