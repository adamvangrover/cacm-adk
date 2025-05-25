# cacm_adk_core/validator/validator.py
# Requires the 'jsonschema' library. Add to requirements.txt.
import json
import jsonschema # type: ignore

class Validator:
    """
    Validates CACM instances against the official CACM JSON schema.
    """
    def __init__(self, schema_filepath: str = "cacm_standard/cacm_schema_v0.2.json"):
        """
        Initializes the Validator and loads the CACM schema.

        Args:
            schema_filepath: Path to the CACM JSON schema file.
        """
        try:
            with open(schema_filepath, 'r') as f:
                self.schema = json.load(f)
        except FileNotFoundError:
            print(f"Error: Schema file not found at {schema_filepath}")
            self.schema = None # Or raise an exception
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from schema file {schema_filepath}")
            self.schema = None # Or raise an exception

    def validate_cacm_against_schema(self, cacm_instance_data: dict) -> tuple[bool, list]:
        """
        Validates a given CACM instance (as a Python dictionary) against the loaded schema.

        Args:
            cacm_instance_data: The CACM instance to validate.

        Returns:
            A tuple: (is_valid: bool, errors: list).
            'is_valid' is True if validation passes, False otherwise.
            'errors' is a list of error messages if validation fails, otherwise an empty list.
        """
        if not self.schema:
            return False, [{"message": "CACM schema not loaded."}]

        try:
            jsonschema.validate(instance=cacm_instance_data, schema=self.schema)
            return True, []
        except jsonschema.exceptions.ValidationError as e:
            # Basic error reporting, can be made more detailed
            return False, [{"path": list(e.path), "message": e.message, "validator": e.validator}]
        except Exception as e:
            return False, [{"message": f"An unexpected error occurred during validation: {str(e)}"}]

if __name__ == '__main__':
    # Example Usage
    validator = Validator()
    if not validator.schema:
        print("Exiting due to schema loading issues.")
    else:
        print(f"Loaded schema: {validator.schema.get('title', 'Unknown Schema')}, Version: {validator.schema.get('description', 'N/A')}") # Adjusted to new schema structure
        
        # Example valid CACM (adjust to match schema v0.2 for minimal validity)
        valid_cacm_example = {
            "cacmId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "version": "0.2.0",
            "name": "Test CACM",
            "description": "A test CACM instance.",
            "metadata": {"creationDate": "2023-01-01T12:00:00Z"},
            "inputs": {
                "customer_data": {
                    "description": "Customer financial data.",
                    "type": "object",
                    "schema": {
                        "$schema": "http://json-schema.org/draft-07/schema#", # Added for nested schema
                        "type": "object",
                        "properties": {"income": {"type": "number"}},
                        "required": ["income"]
                    }
                }
            },
            "outputs": {
                "score": {
                    "description": "Calculated credit score.",
                    "type": "number"
                }
            },
            "workflow": [
                {
                    "stepId": "s1",
                    "description": "Calculate score",
                    "computeCapabilityRef": "model:CreditScoringModel"
                }
            ]
        }
        is_valid, errors = validator.validate_cacm_against_schema(valid_cacm_example)
        print(f"Validation for 'valid_cacm_example': Is Valid = {is_valid}, Errors = {errors}")

        # Example invalid CACM (missing required 'name')
        invalid_cacm_example = {
            "cacmId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "version": "0.2.0",
            # "name": "Test CACM", # Missing name
            "description": "An invalid test CACM instance.",
             "metadata": {"creationDate": "2023-01-01T12:00:00Z"},
            "inputs": {}, # Must not be empty if present, or be valid
            "outputs": {}, # Must not be empty if present, or be valid
            "workflow": [] # Must not be empty if present, or be valid
        }
        # To make this example actually invalid by schema rules for inputs/outputs/workflow if they exist
        # we'll make them valid but miss 'name'
        invalid_cacm_example_missing_name = {
            "cacmId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "version": "0.2.0",
            # "name": "Test CACM", # Missing name
            "description": "An invalid test CACM instance.",
            "metadata": {"creationDate": "2023-01-01T12:00:00Z"},
            "inputs": { "dummy_input": {"description": "d", "type": "string"}},
            "outputs": { "dummy_output": {"description": "d", "type": "string"}},
            "workflow": [{ "stepId": "s1", "description": "d", "computeCapabilityRef": "d"}]
        }

        is_valid, errors = validator.validate_cacm_against_schema(invalid_cacm_example_missing_name)
        print(f"Validation for 'invalid_cacm_example_missing_name': Is Valid = {is_valid}, Errors = {errors}")
