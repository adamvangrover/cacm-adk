# cacm_adk_core/agents/knowledge_graph_agent.py
import logging
import os # For path joining
import json # For JSON processing in results conversion
from typing import Dict, Any, Optional, List

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService # For standard init
from cacm_adk_core.context.shared_context import SharedContext
from semantic_kernel.functions.kernel_arguments import KernelArguments


try:
    from rdflib import Graph, URIRef, Literal
    from rdflib.plugins.sparql.results.jsonresults import JSONResultSerializer # For converting results
    from io import StringIO # For serializing to JSON string (use StringIO for text)
    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False
    # Define dummy classes if rdflib is not available, so type hints don't break.
    # These won't be functional but allow the agent to load.
    class URIRef: pass 
    class Literal: pass

# Determine project root to construct default KG file path
AGENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(AGENT_FILE_DIR, '..', '..'))
DEFAULT_KG_FILE_PATH = os.path.join(PROJECT_ROOT, "knowledge_graph_instantiations", "kb_core_instances.ttl")


class KnowledgeGraphAgent(Agent):
    """
    Executes SPARQL queries against local Knowledge Graph (KG) files and can
    optionally populate the KG with new triples before querying.
    """

    def __init__(self, kernel_service: KernelService):
        super().__init__(agent_name="KnowledgeGraphAgent", kernel_service=kernel_service)
        self.logger.info(f"KnowledgeGraphAgent initialized. RDFlib available: {RDFLIB_AVAILABLE}")
        if not RDFLIB_AVAILABLE:
            self.logger.error("RDFlib library is not installed. KnowledgeGraphAgent will not function.")

    def _parse_rdf_term(self, term_str: str) -> Any:
        """
        Parses a string term into an rdflib URIRef or Literal.
        Assumes term_str from KGPopulationSkill:
        - URIs are full (e.g., "http://...")
        - Literals are either numbers, booleans, or enclosed in quotes.
        """
        if not RDFLIB_AVAILABLE:
            raise ImportError("RDFlib not available for parsing RDF terms.")
        
        # URIs from KGPopulationSkill are expected to be full.
        if term_str.startswith("http://") or term_str.startswith("https://"):
            return URIRef(term_str)
        
        # Literal handling based on KGPopulationSkill's format_literal output
        if term_str.startswith('"') and term_str.endswith('"'):
            return Literal(term_str[1:-1]) 
        if term_str.lower() == "true":
            return Literal(True)
        if term_str.lower() == "false":
            return Literal(False)
        try:
            return Literal(int(term_str))
        except ValueError:
            try:
                return Literal(float(term_str))
            except ValueError:
                # Default for unquoted strings that are not bool/numbers.
                # KGPopulationSkill should quote string literals.
                return Literal(term_str)

    def _convert_sparql_results_to_json_serializable(self, results) -> List[Dict[str, Any]]:
        if not results or not RDFLIB_AVAILABLE:
            return []
        
        # Use StringIO for text-based serialization expected by JSONResultSerializer
        string_stream = StringIO()
        serializer = JSONResultSerializer(results)
        serializer.serialize(string_stream)
        string_stream.seek(0)
        json_results = json.load(string_stream)
        
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
        kg_file_path_input = current_step_inputs.get("kg_file_path") # Path to load from AND/OR persist to
        rdf_turtle_data_to_load = current_step_inputs.get("rdf_turtle_data_to_load") # Output from KGPopulationSkill
        persist_changes = current_step_inputs.get("persist_changes", False) # New input to control saving

        agent_final_status = "success"
        agent_final_message = "KG operations completed."
        population_status_summary = "Not applicable"
        query_execution_summary = "Not attempted"
        persistence_summary = "Not applicable"
        
        graph = Graph() # Initialize an empty graph for this run/instance
        initial_triples_count_from_file = 0
        kg_file_loaded_path = "None" # Path of the KG file actually loaded
        
        # Determine effective KG file path (for loading and potential persistence)
        effective_kg_file_path = kg_file_path_input or DEFAULT_KG_FILE_PATH
        if not os.path.isabs(effective_kg_file_path):
            effective_kg_file_path = os.path.join(PROJECT_ROOT, effective_kg_file_path)

        # 1. Load existing KG from file (if specified or default exists)
        if os.path.exists(effective_kg_file_path):
            try:
                self.logger.info(f"Loading Knowledge Graph from file: {effective_kg_file_path}")
                graph.parse(effective_kg_file_path, format="turtle")
                initial_triples_count_from_file = len(graph)
                kg_file_loaded_path = effective_kg_file_path
                self.logger.info(f"KG loaded from '{kg_file_loaded_path}'. Initial graph size: {initial_triples_count_from_file} triples.")
            except Exception as e:
                self.logger.error(f"Error loading KG file {effective_kg_file_path}: {e}")
                # Non-fatal if we are primarily populating a new graph or querying an empty one
                agent_final_status = "warning" 
                agent_final_message = f"Warning: Error loading KG file {effective_kg_file_path}. Error: {e}. Proceeding with current graph content."
        else:
            self.logger.info(f"KG file {effective_kg_file_path} not found. Starting with an empty graph or only populated data.")
            # This is not an error if the intent is to populate a new graph.
            # If a query is run on an empty graph, it will just return no results.
            kg_file_loaded_path = f"File not found ({effective_kg_file_path})"


        # 2. Populate graph with new RDF Turtle data, if provided
        triples_added_from_population = 0
        if rdf_turtle_data_to_load and isinstance(rdf_turtle_data_to_load, str):
            self.logger.info(f"Attempting KG population with provided RDF Turtle data.")
            population_status_summary = "Population attempted."
            try:
                count_before_load = len(graph)
                # Create a temporary graph to parse the input Turtle data
                temp_graph = Graph()
                temp_graph.parse(data=rdf_turtle_data_to_load, format="turtle")
                
                # Merge the temporary graph into the main graph
                for triple in temp_graph:
                    graph.add(triple)
                
                triples_added_from_population = len(graph) - count_before_load
                population_status_summary = f"Success: Added {triples_added_from_population} new triples from provided Turtle data."
                self.logger.info(population_status_summary)
                if agent_final_message == "KG operations completed.": agent_final_message = "KG population successful."

            except Exception as e_pop:
                self.logger.exception(f"Error during KG population from Turtle data: {e_pop}")
                population_status_summary = f"Error parsing/loading Turtle data: {e_pop}"
                if agent_final_status == "success": agent_final_status = "error"
                if agent_final_message == "KG operations completed.": agent_final_message = f"KG population from Turtle data failed: {e_pop}"
        elif rdf_turtle_data_to_load:
             population_status_summary = "Skipped: 'rdf_turtle_data_to_load' was not a string."
             if agent_final_status == "success": agent_final_status = "warning"
        else:
            population_status_summary = "Skipped: No 'rdf_turtle_data_to_load' provided."

        self.logger.info(f"Graph size after potential population: {len(graph)} triples.")

        # 3. Execute SPARQL query, if provided
        if sparql_query:
            query_execution_summary = "Query execution attempted."
            # Check if graph is essentially empty (only contains loaded file data, no new population)
            # or completely empty (no file loaded, no population)
            if len(graph) == 0 or (len(graph) == initial_triples_count_from_file and triples_added_from_population == 0):
                # Allow query if file was loaded, even if no new triples added.
                # Only warn if graph is TRULY empty (no file, no population)
                if len(graph) == 0:
                    self.logger.warning("Attempting to query an entirely empty graph (no file loaded, no data populated). Results will be empty.")
                    query_results_list = []
                    query_execution_summary = "Skipped: Query against completely empty graph."
                    if agent_final_status == "success": agent_final_status = "warning" # Downgrade status
                    if agent_final_message == "KG operations completed.": agent_final_message = "Query skipped on empty graph."
                else:
                    # Proceed with query if graph has some content (from file or population)
                    try:
                        self.logger.info(f"Executing SPARQL query (first 100 chars): \n{sparql_query[:100]}...")
                        query_results_raw = graph.query(sparql_query)
                        query_results_list = self._convert_sparql_results_to_json_serializable(query_results_raw)
                        self.logger.info(f"SPARQL query executed. Number of results: {len(query_results_list)}")
                        query_execution_summary = f"Success: Found {len(query_results_list)} results."
                        if agent_final_message == "KG operations completed.": agent_final_message = "KG query processed."
                    except Exception as e_query:
                        self.logger.exception(f"Error during SPARQL query execution: {e_query}")
                        query_execution_summary = f"Error: {e_query}"
                        if agent_final_status == "success": agent_final_status = "error"
                        if agent_final_message == "KG operations completed.": agent_final_message = f"SPARQL query failed: {e_query}"
            else: # Graph has content, proceed with query
                try:
                    self.logger.info(f"Executing SPARQL query (first 100 chars): \n{sparql_query[:100]}...")
                    query_results_raw = graph.query(sparql_query)
                    query_results_list = self._convert_sparql_results_to_json_serializable(query_results_raw)
                    self.logger.info(f"SPARQL query executed. Number of results: {len(query_results_list)}")
                    query_execution_summary = f"Success: Found {len(query_results_list)} results."
                    if agent_final_message == "KG operations completed.": agent_final_message = "KG query processed."
                except Exception as e_query:
                    self.logger.exception(f"Error during SPARQL query execution: {e_query}")
                    query_execution_summary = f"Error: {e_query}"
                    if agent_final_status == "success": agent_final_status = "error"
                    if agent_final_message == "KG operations completed.": agent_final_message = f"SPARQL query failed: {e_query}"
        else:
            query_execution_summary = "Skipped: No 'sparql_query' provided."
            if agent_final_message == "KG operations completed.": agent_final_message = "KG populated (if data provided), no query."
        
        # 4. Persist changes to KG file, if requested and applicable
        if persist_changes and triples_added_from_population > 0:
            persistence_summary = "Persistence attempted."
            try:
                # Ensure directory for effective_kg_file_path exists
                kg_dir = os.path.dirname(effective_kg_file_path)
                if not os.path.exists(kg_dir):
                    os.makedirs(kg_dir, exist_ok=True)
                    self.logger.info(f"Created directory for KG file: {kg_dir}")
                
                graph.serialize(destination=effective_kg_file_path, format="turtle")
                persistence_summary = f"Success: Graph with {len(graph)} triples persisted to '{effective_kg_file_path}'."
                self.logger.info(persistence_summary)
                if agent_final_message == "KG operations completed." or agent_final_message == "KG population successful.": 
                    agent_final_message = "KG population and persistence successful."
            except Exception as e_persist:
                self.logger.exception(f"Error persisting graph to {effective_kg_file_path}: {e_persist}")
                persistence_summary = f"Error: {e_persist}"
                if agent_final_status == "success": agent_final_status = "error"
                if agent_final_message == "KG operations completed.": agent_final_message = f"KG persistence failed: {e_persist}"
        elif persist_changes:
            persistence_summary = "Skipped: No new triples were added by population, so no changes to persist."
            self.logger.info(persistence_summary)
        else:
            persistence_summary = "Skipped: 'persist_changes' was false."

        # Consolidate final message based on operations performed
        if agent_final_message == "KG operations completed.": # Default if no specific path taken
            parts = []
            if rdf_turtle_data_to_load: parts.append("Population " + ("processed" if "Success" in population_status_summary else "failed/skipped"))
            if sparql_query: parts.append("Query " + ("processed" if "Success" in query_execution_summary else "failed/skipped"))
            if persist_changes and triples_added_from_population > 0 : parts.append("Persistence " + ("successful" if "Success" in persistence_summary else "failed"))
            
            if not parts: agent_final_message = "No specific KG operations (load, populate, query, persist) were actively performed or requested with data."
            else: agent_final_message = "; ".join(parts) + "."
        
        return {
            "status": agent_final_status,
            "agent_name": self.agent_name,
            "message": agent_final_message,
            "data": {
                "kg_file_loaded": kg_file_loaded_path,
                "initial_graph_size_from_file": initial_triples_count_from_file,
                "population_summary": population_status_summary,
                "triples_added_by_population": triples_added_from_population,
                "final_graph_size": len(graph),
                "persistence_summary": persistence_summary,
                "query_executed": sparql_query if sparql_query else "None",
                "query_execution_summary": query_execution_summary,
                "results_count": len(query_results_list),
                "results": query_results_list
            }
        }

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    # For __main__ testing, we need a KernelService instance, but KGPopulationSkill
    # is no longer called by KG Agent directly. So, we'll simulate its output.
    kernel_service_instance = KernelService() # Still needed for Agent init
    
    # Simulate output of KGPopulationSkill
    # To do this properly, we'd need to run KGPopulationSkill first.
    # For this standalone test of KG Agent, let's craft some sample Turtle data.
    sample_rdf_turtle_input = """
        @prefix kgclass: <http://example.com/ontology/cacm_credit_ontology/0.3/classes/#> .
        @prefix kgprop: <http://example.com/ontology/cacm_credit_ontology/0.3/properties/#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        <http://example.com/entity/MAINTESTCO> a kgclass:Obligor ;
            rdfs:label "Main Test Corp from Turtle Input"^^xsd:string ;
            kgprop:hasTickerSymbol "MTCI"^^xsd:string .
    """

    kg_agent = KnowledgeGraphAgent(kernel_service=kernel_service_instance)
    mock_shared_context = SharedContext(cacm_id="test_kg_agent_cacm_v2")

    query_for_main_test_co = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?label WHERE { <http://example.com/entity/MAINTESTCO> rdfs:label ?label . }
    """
    
    dummy_base_kg_content = """
        @prefix kgclass: <http://example.com/ontology/cacm_credit_ontology/0.3/classes/#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        <http://example.com/entity/DUMMY_IN_FILE> rdf:type kgclass:Obligor ;
                                                rdfs:label "Dummy Corp Loaded From File"^^xsd:string .
    """
    dummy_kg_file_for_test = os.path.join(PROJECT_ROOT, "knowledge_graph_instantiations", "kga_test_dummy.ttl")
    persisted_kg_file_for_test = os.path.join(PROJECT_ROOT, "knowledge_graph_instantiations", "kga_test_persisted.ttl")

    with open(dummy_kg_file_for_test, "w") as f:
        f.write(dummy_base_kg_content)
    
    # Clean up persisted file if it exists from a previous run
    if os.path.exists(persisted_kg_file_for_test):
        os.remove(persisted_kg_file_for_test)

    import asyncio
    async def test_run_v2():
        print("\n--- Test 1: Load from file, Populate from Turtle, Query, Persist ---")
        inputs_test1 = {
            "kg_file_path": "knowledge_graph_instantiations/kga_test_dummy.ttl", # Load this
            "rdf_turtle_data_to_load": sample_rdf_turtle_input,          # Populate this
            "persist_changes": True,                                     # Persist combined graph
            "sparql_query": query_for_main_test_co                       # Query for populated data
        }
        # Modify kg_file_path_input for persistence to go to a new file
        # The 'kg_file_path' in inputs_test1 will be used for loading *and* persistence if persist_changes is true.
        # To avoid overwriting the dummy, let's make a copy or change the path for persistence.
        # For simplicity in this test, we'll allow it to overwrite kga_test_dummy.ttl for this specific test,
        # or better, use a different path for persistence.
        # Let's assume for this test, if kg_file_path is given, it's also the target for persistence.
        # We'll use 'persisted_kg_file_for_test' for the output of this step.
        
        # To test persistence to a *different* file than loaded, we'd need another input like 'persist_to_kg_file_path'.
        # The current refactor uses 'effective_kg_file_path' for both load and save if 'persist_changes' is true.
        # So, for Test 1, we'll load dummy, add turtle, and save back to dummy.
        # For Test 1 modified: load dummy, add turtle, save to NEW file (persisted_kg_file_for_test)
        # This requires a slight adjustment in how `effective_kg_file_path` is used for saving if a different output path is desired.
        # For now, the code saves to the same `effective_kg_file_path` it loaded from (or default).
        # To test persistence to a new file, we'll set kg_file_path to the new file and NOT load from it initially.
        
        print("\n--- Test 1 (Modified): Populate from Turtle, Query, Persist to NEW file ---")
        inputs_test1_mod = {
            "kg_file_path": persisted_kg_file_for_test, # Target for persistence
            "rdf_turtle_data_to_load": sample_rdf_turtle_input,
            "persist_changes": True,
            "sparql_query": query_for_main_test_co
        }
        result_test1 = await kg_agent.run("Populate, Query, Persist New", inputs_test1_mod, mock_shared_context)
        print(f"Test 1 Result: {json.dumps(result_test1, indent=2)}")
        assert result_test1['status'] == 'success'
        assert result_test1['data']['triples_added_by_population'] > 0
        assert len(result_test1['data']['results']) > 0
        assert result_test1['data']['results'][0]['label'] == "Main Test Corp from Turtle Input"
        assert os.path.exists(persisted_kg_file_for_test), "Persisted KG file should exist."
        print("Test 1 (Modified) - Assertions PASSED")

        print("\n--- Test 2: Load from persisted file, Query ---")
        inputs_test2 = {
            "kg_file_path": persisted_kg_file_for_test, # Load the file saved in Test 1
            "sparql_query": query_for_main_test_co
        }
        result_test2 = await kg_agent.run("Load Persisted, Query", inputs_test2, mock_shared_context)
        print(f"Test 2 Result: {json.dumps(result_test2, indent=2)}")
        assert result_test2['status'] == 'success'
        assert len(result_test2['data']['results']) > 0
        assert result_test2['data']['results'][0]['label'] == "Main Test Corp from Turtle Input"
        print("Test 2 - Assertions PASSED")
        
        print("\n--- Test 3: Query only from original dummy file ---")
        query_for_dummy_in_file = """
             PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
             SELECT ?label WHERE { <http://example.com/entity/DUMMY_IN_FILE> rdfs:label ?label . }
        """
        inputs_test3 = {
            "kg_file_path": dummy_kg_file_for_test,
            "sparql_query": query_for_dummy_in_file
        }
        result_test3 = await kg_agent.run("Query Original Dummy", inputs_test3, mock_shared_context)
        print(f"Test 3 Result: {json.dumps(result_test3, indent=2)}")
        assert result_test3['status'] == 'success'
        assert len(result_test3['data']['results']) > 0
        assert result_test3['data']['results'][0]['label'] == "Dummy Corp Loaded From File"
        print("Test 3 - Assertions PASSED")

        # Clean up
        if os.path.exists(dummy_kg_file_for_test): os.remove(dummy_kg_file_for_test)
        if os.path.exists(persisted_kg_file_for_test): os.remove(persisted_kg_file_for_test)
        print(f"\nCleaned up test KG files.")

    asyncio.run(test_run_v2())

# Ensure rdflib types are defined for global scope if not imported for type hinting
if not RDFLIB_AVAILABLE:
    class URIRef: pass
    class Literal: pass
    Graph = None # To satisfy linters if Graph is used in type hints outside methods
