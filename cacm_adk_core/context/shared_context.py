import uuid
import logging
import json # Moved to top
from typing import Optional, Dict, List, Any

class SharedContext:
    """
    Manages and shares context between agents, skills, and the Semantic Kernel
    throughout a CACM execution session.
    """
    def __init__(self, cacm_id: str, session_id: Optional[str] = None):
        """
        Initializes the SharedContext.

        Args:
            cacm_id (str): The ID of the CACM instance this context is associated with.
            session_id (Optional[str]): A unique session ID. If None, one is generated.
        """
        self.session_id: str = session_id or str(uuid.uuid4())
        self.cacm_id: str = cacm_id
        self.document_references: Dict[str, str] = {}
        self.knowledge_base_references: List[str] = []
        self.global_parameters: Dict[str, Any] = {}
        self.data_store: Dict[str, Any] = {}  # For general inter-agent/skill data

        self.logger = logging.getLogger(f"context.SharedContext.{self.session_id}")
        self.logger.info(f"SharedContext initialized for CACM ID '{self.cacm_id}' (Session ID: {self.session_id})")

    def get_session_id(self) -> str:
        return self.session_id

    def get_cacm_id(self) -> str:
        return self.cacm_id

    def add_document_reference(self, doc_type: str, doc_uri: str):
        self.document_references[doc_type] = doc_uri
        self.logger.info(f"Added document reference: Type='{doc_type}', URI='{doc_uri}'")

    def get_document_reference(self, doc_type: str) -> Optional[str]:
        return self.document_references.get(doc_type)

    def get_all_document_references(self) -> Dict[str, str]:
        return self.document_references.copy()

    def add_knowledge_base_reference(self, kb_uri: str):
        if kb_uri not in self.knowledge_base_references:
            self.knowledge_base_references.append(kb_uri)
            self.logger.info(f"Added knowledge base reference: URI='{kb_uri}'")
        else:
            self.logger.debug(f"Knowledge base reference URI='{kb_uri}' already exists.")

    def get_all_knowledge_base_references(self) -> List[str]:
        return self.knowledge_base_references.copy()

    def set_global_parameter(self, key: str, value: Any):
        self.global_parameters[key] = value
        self.logger.info(f"Set global parameter: Key='{key}', Value='{value}'")

    def get_global_parameter(self, key: str) -> Optional[Any]:
        return self.global_parameters.get(key)

    def get_all_global_parameters(self) -> Dict[str, Any]:
        return self.global_parameters.copy()

    def set_data(self, key: str, value: Any):
        """Stores general data in the data_store."""
        self.data_store[key] = value
        self.logger.info(f"Set data in data_store: Key='{key}' (Value type: {type(value).__name__})")

    def get_data(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """Retrieves data from the data_store."""
        return self.data_store.get(key, default)

    def log_context_summary(self):
        """Logs a summary of the current context content."""
        summary_lines = [
            f"--- SharedContext Summary (Session: {self.session_id}, CACM: {self.cacm_id}) ---",
            f"Document References: {json.dumps(self.document_references, indent=2) if self.document_references else 'None'}",
            f"Knowledge Base Refs: {self.knowledge_base_references if self.knowledge_base_references else 'None'}",
            f"Global Parameters: {json.dumps(self.global_parameters, indent=2) if self.global_parameters else 'None'}",
            f"Data Store Keys: {list(self.data_store.keys()) if self.data_store else 'None'}",
            f"--- End of Summary ---"
        ]
        self.logger.info("\n".join(summary_lines))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_context = SharedContext(cacm_id="test_cacm_001")

    test_context.add_document_reference("10K_FILING", "s3://bucket/10k.pdf")
    test_context.add_document_reference("NEWS_ARTICLE", "http://example.com/news.html")

    test_context.add_knowledge_base_reference("kb:company_policies_v1")

    test_context.set_global_parameter("target_fiscal_year", 2024)
    test_context.set_global_parameter("user_preferences", {"language": "en", "detail_level": "high"})

    test_context.set_data("processed_text_segment_1", "This is a sample processed text.")
    test_context.set_data("analysis_score_component_A", 0.75)

    retrieved_doc = test_context.get_document_reference("10K_FILING")
    logging.info(f"Retrieved 10K: {retrieved_doc}")

    retrieved_param = test_context.get_global_parameter("target_fiscal_year")
    logging.info(f"Retrieved fiscal year: {retrieved_param}")

    retrieved_data = test_context.get_data("analysis_score_component_A")
    logging.info(f"Retrieved component A score: {retrieved_data}")

    test_context.log_context_summary()
