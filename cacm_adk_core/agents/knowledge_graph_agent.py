# cacm_adk_core/agents/knowledge_graph_agent.py
import logging
import os # For path joining
import json # For JSON processing in results conversion
from typing import Dict, Any, Optional, List

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService # For standard init
from cacm_adk_core.context.shared_context import SharedContext

try:
    from rdflib import Graph
    from rdflib.plugins.sparql.results.jsonresults import JSONResultSerializer # For converting results
    from io import BytesIO # For serializing to JSON string
    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False

# Determine project root to construct default KG file path
# This assumes agent is in cacm_adk_core/agents/
AGENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(AGENT_FILE_DIR, '..', '..'))
DEFAULT_KG_FILE_PATH = os.path.join(PROJECT_ROOT, "knowledge_graph_instantiations", "kb_core_instances.ttl")


class KnowledgeGraphAgent(Agent):
    """
    Agent responsible for querying local Knowledge Graph files using SPARQL.
    It loads an RDF graph from a specified file (TTL, RDF/XML, etc.) and
    executes a SPARQL query against it, returning the results.
    """

    def __init__(self, kernel_service: KernelService, agent_config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_name="KnowledgeGraphAgent", kernel_service=kernel_service)
        self.config = agent_config if agent_config else {}
        self.logger.info(f"KnowledgeGraphAgent initialized. RDFlib available: {RDFLIB_AVAILABLE}")
        if not RDFLIB_AVAILABLE:
            self.logger.error("RDFlib library is not installed. KnowledgeGraphAgent will not function.")

    def _convert_sparql_results_to_json_serializable(self, results) -> List[Dict[str, Any]]:
        """
        Converts SPARQL query results (QueryResult) to a JSON serializable list of dicts.
        Uses RDFlib's JSONResultSerializer.
        """
        if not results:
            return []

        # JSONResultSerializer writes to a file-like object
        byte_stream = BytesIO()
        serializer = JSONResultSerializer(results)
        serializer.serialize(byte_stream) # This writes JSON to the stream
        byte_stream.seek(0) # Rewind the stream to the beginning
        json_results = json.load(byte_stream) # Load the JSON data from the stream

        # The structure from JSONResultSerializer is typically:
        # { "head": {"vars": [...]}, "results": {"bindings": [ {var1: {type:..., value:...}}, ... ]}}
        # We want to simplify this to a list of {var1: value, var2: value}

        output_list = []
        if "results" in json_results and "bindings" in json_results["results"]:
            for binding in json_results["results"]["bindings"]:
                row = {}
                for var_name, var_data in binding.items():
                    row[var_name] = var_data.get("value")
                output_list.append(row)
        return output_list


    async def run(self, task_description: str, current_step_inputs: Dict[str, Any], shared_context: SharedContext) -> Dict[str, Any]:
        self.logger.info(f"'{self.agent_name}' received task: {task_description} with inputs: {current_step_inputs}")

        if not RDFLIB_AVAILABLE:
            return {"status": "error", "message": "RDFlib library not installed. Cannot perform KG operations."}

        sparql_query = current_step_inputs.get("sparql_query")
        kg_file_path_input = current_step_inputs.get("kg_file_path")

        if not sparql_query:
            return {"status": "error", "message": "Missing 'sparql_query' in inputs."}

        # Use provided path or default
        kg_file_to_load = kg_file_path_input if kg_file_path_input else DEFAULT_KG_FILE_PATH

        # Ensure the path is absolute or correctly relative to project root if not absolute
        if not os.path.isabs(kg_file_to_load):
            kg_file_to_load = os.path.join(PROJECT_ROOT, kg_file_to_load)


        if not os.path.exists(kg_file_to_load):
            self.logger.error(f"Knowledge Graph file not found at: {kg_file_to_load}")
            return {"status": "error", "message": f"Knowledge Graph file not found: {kg_file_to_load}"}

        try:
            graph = Graph()
            self.logger.info(f"Loading Knowledge Graph from: {kg_file_to_load}")
            graph.parse(kg_file_to_load, format="turtle") # Assuming ttl, can be made format-agnostic later
            self.logger.info(f"Knowledge Graph loaded successfully. Graph size: {len(graph)} triples.")

            self.logger.info(f"Executing SPARQL query: \n{sparql_query}") # Corrected logging format
            query_results_raw = graph.query(sparql_query)

            query_results_list = self._convert_sparql_results_to_json_serializable(query_results_raw)


            self.logger.info(f"SPARQL query executed. Number of results: {len(query_results_list)}")

            return {
                "status": "success",
                "data": {
                    "query_executed": sparql_query,
                    "kg_file_used": kg_file_to_load,
                    "results_count": len(query_results_list),
                    "results": query_results_list
                }
            }

        except ImportError as e: # Should be caught by RDFLIB_AVAILABLE but as fallback
            self.logger.exception(f"RDFlib import error during KG operation: {e}")
            return {"status": "error", "message": f"RDFlib import error: {e}. Please ensure rdflib is installed."}
        except FileNotFoundError: # Should be caught by os.path.exists, but as defense
            self.logger.error(f"Knowledge Graph file not found (double check): {kg_file_to_load}")
            return {"status": "error", "message": f"Knowledge Graph file not found during operation: {kg_file_to_load}"}
        except Exception as e:
            self.logger.exception(f"Error during Knowledge Graph operation for query '{sparql_query[:100]}...': {e}")
            return {"status": "error", "message": f"Error during KG operation: {e}"}
