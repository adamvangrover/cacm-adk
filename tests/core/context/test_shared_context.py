#!/usr/bin/env python3
import unittest
import uuid
import logging
from unittest.mock import patch, MagicMock

from cacm_adk_core.context.shared_context import SharedContext

class TestSharedContext(unittest.TestCase):

    def test_initialization(self):
        cacm_id = "test_cacm_001"
        context = SharedContext(cacm_id)
        self.assertEqual(context.get_cacm_id(), cacm_id)
        self.assertIsNotNone(context.get_session_id())

        session_id = "custom_session_123"
        context_with_session = SharedContext(cacm_id, session_id=session_id)
        self.assertEqual(context_with_session.get_session_id(), session_id)

    def test_document_references(self):
        context = SharedContext("test_cacm_docs")
        self.assertEqual(context.get_all_document_references(), {})
        context.add_document_reference("10K", "s3://bucket/10k.pdf")
        self.assertEqual(context.get_document_reference("10K"), "s3://bucket/10k.pdf")
        self.assertIsNone(context.get_document_reference("AnnualReport"))
        expected_docs = {"10K": "s3://bucket/10k.pdf"}
        self.assertEqual(context.get_all_document_references(), expected_docs)
        context.add_document_reference("10K_UPDATE", "s3://bucket/10k_v2.pdf")
        expected_docs["10K_UPDATE"] = "s3://bucket/10k_v2.pdf"
        self.assertEqual(context.get_all_document_references(), expected_docs)

    def test_global_parameters(self):
        context = SharedContext("test_cacm_params")
        self.assertEqual(context.get_all_global_parameters(), {})
        context.set_global_parameter("year", 2024)
        self.assertEqual(context.get_global_parameter("year"), 2024)
        self.assertIsNone(context.get_global_parameter("month"))
        expected_params = {"year": 2024}
        self.assertEqual(context.get_all_global_parameters(), expected_params)
        context.set_global_parameter("user_prefs", {"theme": "dark"})
        expected_params["user_prefs"] = {"theme": "dark"}
        self.assertEqual(context.get_all_global_parameters(), expected_params)

    def test_data_store(self):
        context = SharedContext("test_cacm_datastore")
        self.assertIsNone(context.get_data("my_key"))
        self.assertEqual(context.get_data("my_key", "default_val"), "default_val")

        context.set_data("my_key", "actual_value")
        self.assertEqual(context.get_data("my_key"), "actual_value")

        complex_data = {"a": 1, "b": [1,2,3]}
        context.set_data("complex", complex_data)
        self.assertEqual(context.get_data("complex"), complex_data)

    def test_knowledge_base_references(self):
        context = SharedContext("test_cacm_kb")
        self.assertEqual(context.get_all_knowledge_base_references(), [])
        context.add_knowledge_base_reference("kb:company_v1")
        self.assertEqual(context.get_all_knowledge_base_references(), ["kb:company_v1"])
        # Test adding same reference again (should not duplicate)
        context.add_knowledge_base_reference("kb:company_v1")
        self.assertEqual(context.get_all_knowledge_base_references(), ["kb:company_v1"])
        context.add_knowledge_base_reference("kb:market_data_v2")
        self.assertEqual(sorted(context.get_all_knowledge_base_references()), sorted(["kb:company_v1", "kb:market_data_v2"]))

    @patch('logging.Logger.info') # Patching the logger directly on the class
    def test_log_context_summary(self, mock_logger_info):
        context = SharedContext("test_cacm_log_summary")
        context.add_document_reference("TEST_DOC", "uri://test_doc")
        context.set_global_parameter("test_param", "test_value")
        context.set_data("test_data_key", "test_data_value")

        context.log_context_summary()

        # Check if logger.info was called. We expect multiple calls for the summary.
        self.assertTrue(mock_logger_info.called)

        # Check if some key parts of the summary were logged
        # This is a bit brittle as it depends on the exact log string format.
        # A more robust test might capture the log output and parse it.
        # For now, we'll check if specific substrings are present in any of the calls.

        found_session_id = False
        found_doc_ref = False
        found_global_param = False
        found_data_store_key = False

        for call_args in mock_logger_info.call_args_list:
            log_message = call_args[0][0] # First argument of the call
            if context.get_session_id() in log_message:
                found_session_id = True
            if "TEST_DOC" in log_message and "uri://test_doc" in log_message:
                found_doc_ref = True
            if "test_param" in log_message and "test_value" in log_message:
                found_global_param = True
            if "test_data_key" in log_message: # The value itself isn't in the keys list log line
                found_data_store_key = True

        self.assertTrue(found_session_id, "Session ID not found in log summary.")
        self.assertTrue(found_doc_ref, "Document reference not found in log summary.")
        self.assertTrue(found_global_param, "Global parameter not found in log summary.")
        self.assertTrue(found_data_store_key, "Data store key not found in log summary.")

if __name__ == '__main__':
    unittest.main()
