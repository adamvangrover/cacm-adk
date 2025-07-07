# tests/core/test_template_engine.py
import unittest
import os
import shutil
import json  # Added for creating minimal valid JSON if needed

try:
    from cacm_adk_core.template_engine.template_engine import TemplateEngine
except ImportError:
    TemplateEngine = None

# Updated to reflect pure JSON and new test strategy
TEST_TEMPLATES_DIR_MINIMAL = "temp_test_templates_minimal_json"
MAIN_TEMPLATES_LIB_DIR = "cacm_library/templates"  # Relative to project root
BASIC_TEMPLATE_FILENAME_JSON = (
    "basic_ratio_analysis_template.json"  # Using one of the actual templates
)


class TestTemplateEngineMinimal(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if TemplateEngine is None:
            raise unittest.SkipTest(
                "TemplateEngine component not found or import error."
            )

        os.makedirs(TEST_TEMPLATES_DIR_MINIMAL, exist_ok=True)

        # Path to the main basic_ratio_analysis_template.json (after it's renamed in the actual library)
        # This assumes the script running tests is in the project root, or MAIN_TEMPLATES_LIB_DIR is adjusted.
        # For robustness in test environments, let's consider MAIN_TEMPLATES_LIB_DIR relative to this test file's project.
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        src_basic_template_path = os.path.join(
            project_root, MAIN_TEMPLATES_LIB_DIR, BASIC_TEMPLATE_FILENAME_JSON
        )
        dest_basic_template_path = os.path.join(
            TEST_TEMPLATES_DIR_MINIMAL, BASIC_TEMPLATE_FILENAME_JSON
        )

        if os.path.exists(src_basic_template_path):
            shutil.copy(src_basic_template_path, dest_basic_template_path)
        else:
            # If the main template (now .json) doesn't exist (e.g. tests run before main files are fully in place),
            # create a minimal valid one for tests to proceed.
            print(
                f"Warning: Main template {src_basic_template_path} not found. Creating a minimal version for tests."
            )
            minimal_basic_template_content_dict = {
                "name": "Minimal Basic Template",
                "description": "A very basic template for testing.",
                "cacmId": "replace-me",
                "metadata": {"templateDetails": {"templateName": "Minimal Template"}},
            }  # Pure JSON as dict
            with open(dest_basic_template_path, "w") as f:
                json.dump(minimal_basic_template_content_dict, f, indent=2)

        cls.engine = TemplateEngine(templates_dir=TEST_TEMPLATES_DIR_MINIMAL)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_TEMPLATES_DIR_MINIMAL):
            shutil.rmtree(TEST_TEMPLATES_DIR_MINIMAL)

    def test_engine_initialization(self):
        self.assertIsNotNone(self.engine, "Engine should initialize.")
        self.assertTrue(os.path.isdir(self.engine.templates_dir))

    def test_load_template_json(self):  # Renamed to reflect JSON
        # This test now relies on the (copied or minimal) BASIC_TEMPLATE_FILENAME_JSON
        template_data = self.engine.load_template(BASIC_TEMPLATE_FILENAME_JSON)
        self.assertIsNotNone(
            template_data, f"Should load the template: {BASIC_TEMPLATE_FILENAME_JSON}."
        )
        # Check for a field that exists in both the full template and the minimal one
        self.assertIn("name", template_data)
        if (
            template_data.get("name") == "Minimal Basic Template"
        ):  # Check if it's the minimal version
            self.assertEqual(template_data.get("name"), "Minimal Basic Template")
        else:  # Check against the expected name of the full basic_ratio_analysis_template
            self.assertEqual(
                template_data.get("name"), "Basic Financial Ratio Analysis"
            )

    def test_list_templates_json(self):  # Renamed
        templates = self.engine.list_templates()
        self.assertEqual(
            len(templates), 1, "Should list one .json template from the test directory."
        )
        if len(templates) == 1:
            self.assertEqual(templates[0]["filename"], BASIC_TEMPLATE_FILENAME_JSON)
            # Name check depends on whether the full template was copied or minimal was created
            expected_name = "Basic Ratio Analysis"
            # If minimal was created, its templateDetails.templateName is "Minimal Template"
            # If full was copied, its templateDetails.templateName is "Basic Ratio Analysis"
            # The list_templates method prefers templateDetails.templateName
            # Minimal template has metadata.templateDetails.templateName = "Minimal Template"
            # Full basic_ratio_analysis_template.json has metadata.templateDetails.templateName = "Basic Ratio Analysis"

            # Check if the minimal template was created (by checking its specific name)
            # This requires loading the template to see if its the minimal one or the full one
            loaded_template_for_name_check = self.engine.load_template(
                BASIC_TEMPLATE_FILENAME_JSON
            )
            if loaded_template_for_name_check.get("name") == "Minimal Basic Template":
                expected_name_in_list = "Minimal Template"
            else:
                expected_name_in_list = "Basic Ratio Analysis"
            self.assertEqual(templates[0]["name"], expected_name_in_list)

    def test_instantiate_template_json(self):  # Renamed
        instance = self.engine.instantiate_template(BASIC_TEMPLATE_FILENAME_JSON)
        self.assertIsNotNone(instance)
        self.assertNotEqual(
            instance.get("cacmId"), "replace-me"
        )  # Minimal template has this
        self.assertIn("creationDate", instance.get("metadata", {}))


if __name__ == "__main__":
    unittest.main()
