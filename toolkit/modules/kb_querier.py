# toolkit/modules/kb_querier.py
import json
import os

try:
    from cacm_adk_core.ontology_navigator.ontology_navigator import OntologyNavigator
except ImportError:
    import sys
    # Add project root to path to allow finding cacm_adk_core if toolkit is not installed
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from cacm_adk_core.ontology_navigator.ontology_navigator import OntologyNavigator

DEFAULT_ONTOLOGY_PATH = "ontology/credit_analysis_ontology_v0.3/credit_ontology_v0.3.ttl"

class KBQuerierModule:
    def __init__(self, ontology_path: str = None):
        self._navigator = None
        self._init_error = None
        
        path_to_load = ontology_path if ontology_path else DEFAULT_ONTOLOGY_PATH
        
        if not os.path.exists(path_to_load):
            self._init_error = f"Ontology file not found at {path_to_load}. Please ensure the path is correct."
            # Allow instantiation, but methods will report error.
            return

        try:
            self._navigator = OntologyNavigator(ontology_path=path_to_load)
            if not self._navigator.graph: # Check if graph loading failed silently
                self._init_error = f"Ontology graph could not be loaded from {path_to_load}. Check logs from OntologyNavigator."
        except Exception as e:
            self._init_error = f"Failed to initialize OntologyNavigator: {str(e)}"

    def _check_init_error(self) -> bool:
        if self._init_error:
            return True
        if not self._navigator: # Should be caught by _init_error but as a safeguard
            self._init_error = "OntologyNavigator is not available (unknown reason)."
            return True
        return False

    def get_entity_details(self, entity_uri_or_prefixed_name: str) -> dict:
        if self._check_init_error():
            return {"error": self._init_error}
        if not entity_uri_or_prefixed_name:
            return {"error": "Entity URI or prefixed name cannot be empty."}
        return self._navigator.get_entity_details(entity_uri_or_prefixed_name)

    def list_classes(self, namespace_filter: str = None) -> dict:
        if self._check_init_error():
            return {"error": self._init_error}
        classes = self._navigator.list_classes(namespace_filter=namespace_filter)
        if not classes and namespace_filter:
             return {"classes": [], "message": f"No classes found for namespace filter '{namespace_filter}' or namespace invalid."}
        return {"classes": classes}

    def find_concepts(self, keyword: str) -> dict:
        if self._check_init_error():
            return {"error": self._init_error}
        if not keyword:
            return {"error": "Search keyword cannot be empty."}
        results = self._navigator.find_concepts(keyword)
        return {"found_concepts": results}
        
# Example usage (for testing this module directly)
# if __name__ == '__main__':
#     # Assuming this is run from project root or cacm_adk_core is in PYTHONPATH
#     querier = KBQuerierModule()
#     if querier._check_init_error():
#          print(f"Error during init: {querier._init_error}")
#     else:
#         print("--- Get Details for 'adkarch:Agent' ---")
#         print(json.dumps(querier.get_entity_details("adkarch:Agent"), indent=2))
#         print("\n--- List Classes (adkarch namespace) ---")
#         # Note: OntologyNavigator's list_classes namespace_filter expects prefix like 'adkarch'
#         # not the full URI string.
#         print(json.dumps(querier.list_classes(namespace_filter="adkarch"), indent=2))
#         print("\n--- Find Concepts for 'Agent' ---")
#         print(json.dumps(querier.find_concepts("Agent"), indent=2))
#         print("\n--- Find Concepts for 'Ratio' ---")
#         print(json.dumps(querier.find_concepts("Ratio"), indent=2))
