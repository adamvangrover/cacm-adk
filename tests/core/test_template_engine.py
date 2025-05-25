# tests/core/test_template_engine.py
import unittest
import os
import shutil
try:
    from cacm_adk_core.template_engine.template_engine import TemplateEngine
except ImportError:
    TemplateEngine = None

TEST_TEMPLATES_DIR_MINIMAL = "temp_test_templates_minimal"
BASIC_TEMPLATE_FILENAME_MINIMAL = "basic_template_minimal.jsonc"

class TestTemplateEngineMinimal(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if TemplateEngine is None:
            raise unittest.SkipTest("TemplateEngine component not found or import error.")
        
        os.makedirs(TEST_TEMPLATES_DIR_MINIMAL, exist_ok=True)
        # Create a very simple template file for basic loading tests
        minimal_template_content = '''{
            "name": "Minimal Basic Template",
            "description": "A very basic template for testing.",
            "cacmId": "replace-me",
            "metadata": {"templateDetails": {"templateName": "Minimal Template"}}
        }'''
        with open(os.path.join(TEST_TEMPLATES_DIR_MINIMAL, BASIC_TEMPLATE_FILENAME_MINIMAL), "w") as f:
            f.write(minimal_template_content)
        
        cls.engine = TemplateEngine(templates_dir=TEST_TEMPLATES_DIR_MINIMAL)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_TEMPLATES_DIR_MINIMAL):
            shutil.rmtree(TEST_TEMPLATES_DIR_MINIMAL)

    def test_engine_initialization(self):
        self.assertIsNotNone(self.engine, "Engine should initialize.")
        self.assertTrue(os.path.isdir(self.engine.templates_dir))

    def test_load_minimal_template(self):
        template_data = self.engine.load_template(BASIC_TEMPLATE_FILENAME_MINIMAL)
        self.assertIsNotNone(template_data, "Should load the minimal template.")
        self.assertEqual(template_data.get("name"), "Minimal Basic Template")
        
    def test_list_templates_minimal(self):
        templates = self.engine.list_templates()
        self.assertEqual(len(templates), 1)
        if len(templates) == 1:
            self.assertEqual(templates[0]["filename"], BASIC_TEMPLATE_FILENAME_MINIMAL)
            self.assertEqual(templates[0]["name"], "Minimal Template")

    def test_instantiate_minimal_template(self):
        instance = self.engine.instantiate_template(BASIC_TEMPLATE_FILENAME_MINIMAL)
        self.assertIsNotNone(instance)
        self.assertNotEqual(instance.get("cacmId"), "replace-me")
        self.assertIn("creationDate", instance.get("metadata", {}))


if __name__ == '__main__':
    unittest.main()
