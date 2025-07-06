# cacm_adk_core/agents/knowledge_graph_agent.py
import logging
import os  # For path joining
import json  # For JSON processing in results conversion
from typing import Dict, Any, Optional, List

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService  # For standard init
from cacm_adk_core.context.shared_context import SharedContext
from semantic_kernel.functions.kernel_arguments import KernelArguments


try:
    from rdflib import Graph, URIRef, Literal
    from rdflib.plugins.sparql.results.jsonresults import (
        JSONResultSerializer,
    )  # For converting results
    from io import BytesIO  # For serializing to JSON string

    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False

    # Define dummy classes if rdflib is not available, so type hints don't break.
    # These won't be functional but allow the agent to load.
    class URIRef:
        pass

    class Literal:
        pass


# Determine project root to construct default KG file path
AGENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(AGENT_FILE_DIR, "..", ".."))
DEFAULT_KG_FILE_PATH = os.path.join(
    PROJECT_ROOT, "knowledge_graph_instantiations", "kb_core_instances.ttl"
)


class KnowledgeGraphAgent(Agent):
    """
    Executes SPARQL queries against local Knowledge Graph (KG) files and can
    optionally populate the KG with new triples before querying.
    """

    def __init__(self, kernel_service: KernelService):
        super().__init__(
            agent_name="KnowledgeGraphAgent", kernel_service=kernel_service
        )
        self.logger.info(
            f"KnowledgeGraphAgent initialized. RDFlib available: {RDFLIB_AVAILABLE}"
        )
        if not RDFLIB_AVAILABLE:
            self.logger.error(
                "RDFlib library is not installed. KnowledgeGraphAgent will not function."
            )

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

    def _convert_sparql_results_to_json_serializable(
        self, results
    ) -> List[Dict[str, Any]]:
        if not results or not RDFLIB_AVAILABLE:
            return []

        byte_stream = BytesIO()
        serializer = JSONResultSerializer(results)
        serializer.serialize(byte_stream)
        byte_stream.seek(0)
        json_results = json.load(byte_stream)

        output_list = []
        if "results" in json_results and "bindings" in json_results["results"]:
            for binding in json_results["results"]["bindings"]:
                row = {}
                for var_name, var_data in binding.items():
                    row[var_name] = var_data.get("value")
                output_list.append(row)
        return output_list

    async def run(
        self,
        task_description: str,
        current_step_inputs: Dict[str, Any],
        shared_context: SharedContext,
    ) -> Dict[str, Any]:
        self.logger.info(
            f"'{self.agent_name}' received task: {task_description} with inputs: {current_step_inputs}"
        )

        if not RDFLIB_AVAILABLE:
            return {
                "status": "error",
                "message": "RDFlib library not installed. Cannot perform KG operations.",
            }

        sparql_query = current_step_inputs.get("sparql_query")
        kg_file_path_input = current_step_inputs.get("kg_file_path")
        data_for_kg_population = current_step_inputs.get("data_for_kg_population")
        company_uri_base = current_step_inputs.get(
            "company_uri_base", "http://example.com/entity/"
        )

        agent_final_status = "success"
        agent_final_message = "KG operations completed."
        population_status_summary = "Not applicable"
        query_execution_summary = "Not attempted"

        graph = Graph()
        initial_triples_count = 0
        kg_file_loaded_path = "None"

        if kg_file_path_input:
            kg_file_to_load = kg_file_path_input
            if not os.path.isabs(kg_file_to_load):
                kg_file_to_load = os.path.join(PROJECT_ROOT, kg_file_to_load)

            if os.path.exists(kg_file_to_load):
                try:
                    self.logger.info(
                        f"Loading Knowledge Graph from file: {kg_file_to_load}"
                    )
                    graph.parse(kg_file_to_load, format="turtle")
                    initial_triples_count = len(graph)
                    kg_file_loaded_path = kg_file_to_load
                    self.logger.info(
                        f"KG loaded from file. Initial graph size: {initial_triples_count} triples."
                    )
                except Exception as e:
                    self.logger.error(f"Error loading KG file {kg_file_to_load}: {e}")
                    agent_final_status = "warning"
                    agent_final_message = (
                        f"Error loading KG file {kg_file_to_load}. Error: {e}"
                    )
            else:
                self.logger.warning(f"Specified KG file {kg_file_to_load} not found.")
                if agent_final_status == "success":
                    agent_final_status = "warning"  # Only downgrade if no prior error
                agent_final_message = (
                    f"KG file {kg_file_to_load} not found, but proceeding."
                )

        triples_added_count = 0
        if data_for_kg_population and isinstance(data_for_kg_population, dict):
            self.logger.info(
                f"Attempting KG population with provided data for company URI base: {company_uri_base}"
            )
            population_status_summary = "Population attempted."
            try:
                kernel = self.kernel_service.get_kernel()
                if not kernel:
                    population_status_summary = (
                        "Failed: Kernel not available for KGPopulationSkill."
                    )
                    if agent_final_status == "success":
                        agent_final_status = "error"
                else:
                    kg_pop_plugin = kernel.plugins.get("KGPopulation")
                    if not kg_pop_plugin:
                        population_status_summary = (
                            "Failed: KGPopulation plugin not found."
                        )
                        if agent_final_status == "success":
                            agent_final_status = "error"
                    else:
                        kg_skill_func = kg_pop_plugin.get("generate_rdf_triples")
                        if not kg_skill_func:
                            population_status_summary = (
                                "Failed: 'generate_rdf_triples' function not found."
                            )
                            if agent_final_status == "success":
                                agent_final_status = "error"
                        else:
                            kernel_args = KernelArguments(
                                company_data=data_for_kg_population,
                                company_uri_base=company_uri_base,
                            )
                            result = await kernel.invoke(kg_skill_func, kernel_args)
                            generated_triples = result.value

                            if isinstance(generated_triples, list):
                                self.logger.info(
                                    f"KGPopulationSkill generated {len(generated_triples)} triples."
                                )
                                for s_str, p_str, o_str in generated_triples:
                                    try:
                                        s = self._parse_rdf_term(s_str)
                                        p = self._parse_rdf_term(p_str)
                                        o = self._parse_rdf_term(o_str)
                                        graph.add((s, p, o))
                                        triples_added_count += 1
                                    except Exception as e_parse:
                                        self.logger.error(
                                            f"Error parsing or adding triple ('{s_str}', '{p_str}', '{o_str}'): {e_parse}"
                                        )
                                population_status_summary = f"Success: Added {triples_added_count} new triples from {len(generated_triples)} generated."
                                if triples_added_count != len(generated_triples):
                                    if agent_final_status == "success":
                                        agent_final_status = "partial_success"
                                    if (
                                        agent_final_message
                                        == "KG operations completed."
                                    ):
                                        agent_final_message = (
                                            "KG population partially completed."
                                        )
                            else:
                                population_status_summary = f"Failed: Skill did not return list. Result: {str(result)[:200]}"
                                if agent_final_status == "success":
                                    agent_final_status = "error"
                                if agent_final_message == "KG operations completed.":
                                    agent_final_message = (
                                        "KG population failed (skill error)."
                                    )
            except Exception as e_pop:
                self.logger.exception(f"Error during KG population: {e_pop}")
                population_status_summary = f"Error: {e_pop}"
                if agent_final_status == "success":
                    agent_final_status = "error"
                if agent_final_message == "KG operations completed.":
                    agent_final_message = f"KG population exception: {e_pop}"
        elif data_for_kg_population:
            population_status_summary = (
                "Skipped: 'data_for_kg_population' not a dictionary."
            )
            if agent_final_status == "success":
                agent_final_status = "warning"
        else:
            population_status_summary = "Skipped: No 'data_for_kg_population' provided."

        self.logger.info(
            f"Graph size after potential population: {len(graph)} triples."
        )

        query_results_list = []
        if sparql_query:
            query_execution_summary = "Query execution attempted."
            if (
                len(graph) == 0
                and kg_file_loaded_path == "None"
                and triples_added_count == 0
            ):
                self.logger.warning(
                    "Attempting to query an entirely empty graph. Results will be empty."
                )
                query_results_list = []
                query_execution_summary = "Skipped: Query against empty graph."
                if agent_final_status == "success":
                    agent_final_status = "warning"
                if agent_final_message == "KG operations completed.":
                    agent_final_message = "Query skipped on empty graph."
            else:
                try:
                    self.logger.info(
                        f"Executing SPARQL query (first 100 chars): \n{sparql_query[:100]}..."
                    )
                    query_results_raw = graph.query(sparql_query)
                    query_results_list = (
                        self._convert_sparql_results_to_json_serializable(
                            query_results_raw
                        )
                    )
                    self.logger.info(
                        f"SPARQL query executed. Number of results: {len(query_results_list)}"
                    )
                    query_execution_summary = (
                        f"Success: Found {len(query_results_list)} results."
                    )
                    if agent_final_message == "KG operations completed.":
                        agent_final_message = "KG query processed."
                except Exception as e_query:
                    self.logger.exception(
                        f"Error during SPARQL query execution: {e_query}"
                    )
                    query_execution_summary = f"Error: {e_query}"
                    if agent_final_status == "success":
                        agent_final_status = "error"
                    if agent_final_message == "KG operations completed.":
                        agent_final_message = f"SPARQL query failed: {e_query}"
        else:
            query_execution_summary = "Skipped: No 'sparql_query' provided."
            if agent_final_message == "KG operations completed.":
                agent_final_message = "KG populated (if data provided), no query."

        # Consolidate final message if still default
        if agent_final_message == "KG operations completed.":
            if data_for_kg_population and sparql_query:
                agent_final_message = "KG population and query processed."
            elif data_for_kg_population:
                agent_final_message = "KG population processed, no query."
            elif sparql_query:
                agent_final_message = "KG query processed, no population data."
            else:
                agent_final_message = "No KG population data or SPARQL query provided."

        return {
            "status": agent_final_status,
            "agent_name": self.agent_name,
            "message": agent_final_message,
            "data": {
                "kg_file_loaded": kg_file_loaded_path,
                "initial_graph_size": initial_triples_count,
                "population_summary": population_status_summary,
                "triples_added_by_population": triples_added_count,
                "final_graph_size": len(graph),
                "query_executed": sparql_query if sparql_query else "None",
                "query_execution_summary": query_execution_summary,
                "results_count": len(query_results_list),
                "results": query_results_list,
            },
        }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG
    )  # Use DEBUG for more verbose output from agent

    # Ensure KernelService is initialized and KGPopulationSkill is registered
    # This would typically happen at application startup.
    # For this test, we rely on KernelService being a singleton and already configured
    # if previous subtasks ran `semantic_kernel_adapter.py`'s __main__ or similar.
    # If running this test standalone repeatedly, ensure `KernelService._instance = None`
    # is called to force re-initialization if skills change, or restart Python.
    # KernelService._instance = None # Force re-init for testing if needed.

    kernel_service_instance = KernelService()  # Gets or creates the singleton

    kg_agent = KnowledgeGraphAgent(kernel_service=kernel_service_instance)
    mock_shared_context = SharedContext(cacm_id="test_kg_agent_cacm")

    sample_company_data_for_kg = {
        "companyName": "TestKGPop Corp",
        "companyTicker": "TKGP",
        "financial_data_for_ratios_expanded": {
            "current_assets": 800000.0,
            "total_debt": 450000.0,
            "source": "test_suite",
        },
        "altdata_utility_payments": [
            {
                "utilityType": "Telecom",
                "paymentStatus": "on-time",
                "paymentDate": "2023-07-01",
            }
        ],
        "esg_overall_rating": {
            "ratingValue": "A+",
            "ratingProvider": "ESG Test Raters",
        },
    }

    query_for_populated_data = """
        PREFIX kgclass: <http://example.com/ontology/cacm_credit_ontology/0.3/classes/#>
        PREFIX kgprop: <http://example.com/ontology/cacm_credit_ontology/0.3/properties/#>
        PREFIX altdata: <http://example.com/ontology/cacm_credit_ontology/0.3/alternative_data#>
        PREFIX esg: <http://example.com/ontology/cacm_credit_ontology/0.3/esg#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?companyName ?ticker ?utility_type ?payment_status ?esg_rating_value
        WHERE {
            ?company_uri rdf:type kgclass:Obligor ;
                         rdfs:label ?companyName ;
                         kgprop:hasTickerSymbol ?ticker .
            OPTIONAL {
                ?company_uri altdata:hasUtilityPaymentHistory ?payment_uri .
                ?payment_uri altdata:utilityType ?utility_type ;
                             altdata:paymentStatus ?payment_status .
            }
            OPTIONAL {
                ?company_uri esg:hasESGRating ?esg_rating_uri .
                ?esg_rating_uri esg:ratingValue ?esg_rating_value .
            }
        }
    """

    # Create a dummy KG file for the "load from file" part of the test
    dummy_kg_content = """
        @prefix kgclass: <http://example.com/ontology/cacm_credit_ontology/0.3/classes/#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        <http://example.com/entity/DUMMYCO> rdf:type kgclass:Obligor ;
                                        rdfs:label "Dummy Corp from File" .
    """
    dummy_file_path = os.path.join(
        PROJECT_ROOT, "knowledge_graph_instantiations", "dummy_test_kg.ttl"
    )
    with open(dummy_file_path, "w") as f:
        f.write(dummy_kg_content)

    import asyncio

    async def test_run():
        print("\n--- Test 1: KG Population AND Query ---")
        inputs_populate_and_query = {
            "kg_file_path": "knowledge_graph_instantiations/dummy_test_kg.ttl",  # Load dummy file
            "data_for_kg_population": sample_company_data_for_kg,
            "company_uri_base": "http://example.com/entity/",
            "sparql_query": query_for_populated_data,
        }
        result_populate = await kg_agent.run(
            "Populate KG and Query", inputs_populate_and_query, mock_shared_context
        )
        print(
            f"KG Agent (populate & query) result: {json.dumps(result_populate, indent=2)}"
        )
        if result_populate["status"] == "success":
            assert (
                len(result_populate["data"]["results"]) > 0
            ), "Query should return populated data"
            print("Assertion: Query returned populated data - PASSED (basic check)")

        print(
            "\n--- Test 2: Query Only (using default KG file if available, or previously loaded dummy) ---"
        )
        # This will use DEFAULT_KG_FILE_PATH if dummy_test_kg.ttl was not found, or if kg_file_path is omitted
        # For consistency, let's point to the dummy again explicitly.
        query_for_dummy_file_data = """
            PREFIX kgclass: <http://example.com/ontology/cacm_credit_ontology/0.3/classes/#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?label WHERE { <http://example.com/entity/DUMMYCO> rdfs:label ?label . }
        """
        inputs_query_only = {
            "kg_file_path": "knowledge_graph_instantiations/dummy_test_kg.ttl",
            "sparql_query": query_for_dummy_file_data,
        }
        result_query_only = await kg_agent.run(
            "Query Only", inputs_query_only, mock_shared_context
        )
        print(
            f"KG Agent (query only) result: {json.dumps(result_query_only, indent=2)}"
        )
        if (
            result_query_only["status"] == "success"
            and result_query_only["data"]["results_count"] > 0
        ):
            assert (
                result_query_only["data"]["results"][0]["label"]
                == "Dummy Corp from File"
            )
            print("Assertion: Query returned data from file - PASSED")
        elif result_query_only["status"] == "success":
            print(
                "Warning: Query on dummy file returned no results, file might not have loaded as expected or query is wrong."
            )

        print("\n--- Test 3: Population Only (No SPARQL Query) ---")
        inputs_populate_only = {
            "data_for_kg_population": {
                **sample_company_data_for_kg,
                "companyTicker": "TKGP_POPONLY",
            },  # Change ticker for new entity
            "company_uri_base": "http://example.com/entity/",
            # No sparql_query key
        }
        result_populate_only = await kg_agent.run(
            "Populate KG Only", inputs_populate_only, mock_shared_context
        )
        print(
            f"KG Agent (populate only) result: {json.dumps(result_populate_only, indent=2)}"
        )
        assert result_populate_only["data"]["triples_added_by_population"] > 0
        print("Assertion: Population added triples - PASSED")

        # Clean up dummy file
        if os.path.exists(dummy_file_path):
            os.remove(dummy_file_path)
            print(f"\nCleaned up dummy KG file: {dummy_file_path}")

    asyncio.run(test_run())

# Ensure rdflib types are defined for global scope if not imported for type hinting
if not RDFLIB_AVAILABLE:

    class URIRef:
        pass

    class Literal:
        pass

    Graph = None  # To satisfy linters if Graph is used in type hints outside methods
