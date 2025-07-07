# AGENT.MD - KnowledgeGraphAgent

**Parent AGENT.MD:** `../AGENT.MD` (Refers to `cacm_adk_core/agents/AGENT.MD`)

This document provides specific guidance for working with the `KnowledgeGraphAgent` within the CACM-ADK project.

## 1. Purpose & Key Responsibilities

*   **Purpose:** The `KnowledgeGraphAgent` is responsible for all interactions with the project's Knowledge Graph (KG). This includes querying the KG for information and potentially populating/updating the KG with new data or relationships.
*   **Key Responsibilities:**
    *   Load an RDF graph from a specified TTL file (or use a default one like `knowledge_graph_instantiations/kb_core_instances.ttl`).
    *   Execute SPARQL queries against the loaded KG.
    *   Return query results in a structured format (typically a list of dictionaries).
    *   *(Planned/Future based on Plan 1.2.3)* Accept RDF triples (e.g., from `KGPopulationSkill`) and load them into its in-memory graph.
    *   *(Planned/Future based on Plan 1.2.3)* Persist changes from its in-memory graph back to a TTL file if required.
    *   Handle errors related to KG file loading, SPARQL query parsing/execution, and data serialization.

## 2. Dependencies

*   **Internal Dependencies:**
    *   Inherits from `cacm_adk_core.agents.base_agent.Agent`.
    *   `cacm_adk_core.semantic_kernel_adapter.KernelService`: Though not heavily used for skills by default, it's part of the base agent signature. Could be used if KG interactions were to be augmented by LLM skills (e.g., natural language to SPARQL, which is not current scope but a future possibility).
    *   `cacm_adk_core.context.shared_context.SharedContext`: For logging and potentially getting configuration like KG file paths if not passed directly.
    *   *(Planned/Future)* `KGPopulationSkill` (indirectly, as it would produce triples that this agent consumes).
*   **External Libraries:**
    *   `rdflib`: Core library for RDF graph manipulation, parsing TTL files, and executing SPARQL queries.
    *   `logging`: Standard Python logging.
*   **Configuration Files:**
    *   Relies on `config/compute_capability_catalog.json` for its registration (e.g., `urn:adk:capability:knowledge_graph_query_agent:v1`).
    *   The path to the default KG TTL file (e.g., `knowledge_graph_instantiations/kb_core_instances.ttl`) acts as a configuration.
*   **Data Sources (Expected in `current_step_inputs` or as defaults):**
    *   `sparql_query` (string): The SPARQL query to execute.
    *   `kg_file_path` (string, optional): Path to the KG file to load. Defaults to a system-wide default if not provided.
    *   *(Planned/Future)* `rdf_triples_data` (list or rdflib.Graph): Data to be loaded into the KG.

## 3. How to Test This Component

*   **Unit Tests:**
    *   Location of unit tests: `tests/core/agents/test_knowledge_graph_agent.py` (or `test_agents.py` if not yet separated).
    *   Key test scenarios:
        *   Successful loading of a sample TTL file.
        *   Handling of non-existent or invalid TTL files.
        *   Correct execution of valid SPARQL SELECT queries and verification of results.
        *   Handling of invalid SPARQL query syntax.
        *   *(Planned/Future)* Successful loading of provided RDF triples into the graph.
        *   *(Planned/Future)* Correct persistence of graph changes to a file.
        *   Returning appropriate error messages and statuses.
    *   How to run unit tests:
        ```bash
        pytest tests/core/agents/test_agents.py # Or specific path if refactored
        ```
*   **Integration Tests:**
    *   Tested as part of workflows that use KG querying, such as the ESG analysis part of `msft_comprehensive_analysis_workflow.json` (see `tests/core/test_orchestrator_integration.py`). These tests would involve the `AnalysisAgent` calling a mocked or real `KnowledgeGraphAgent`.
    *   *(Planned/Future)* An integration test for the `kg_population_workflow.json` would directly test the population capabilities.
*   **Mocking:**
    *   For most unit tests, `rdflib.Graph` methods (`parse`, `query`, `serialize`) can be mocked to avoid actual file I/O and complex graph operations.
    *   A small, self-contained sample TTL file should be used for tests that do require actual parsing and querying.
    *   `SharedContext` can be mocked if the agent's interaction with it becomes more complex.
*   **Manual Testing/Verification Steps:**
    *   Use `scripts/query_kg.py` (if it exists and is up-to-date) or write a small ad-hoc script to:
        1.  Instantiate `KnowledgeGraphAgent`.
        2.  Call its `run` method with a sample SPARQL query and (optionally) a KG file path.
        3.  Print the results to verify.
    *   Manually inspect the content of TTL files after population operations (once implemented).

## 4. Configuration Notes (If Applicable)

*   **Capability ID (Querying):** `urn:adk:capability:knowledge_graph_query_agent:v1` in `compute_capability_catalog.json`.
    *   Inputs for this capability: `sparql_query`, `kg_file_path` (optional).
*   **Default KG File Path:** The agent has a hardcoded default KG file path (`knowledge_graph_instantiations/kb_core_instances.ttl`). This could be made more configurable in the future (e.g., via global settings or an environment variable).
*   *(Planned/Future)* A new capability ID will be needed for KG population tasks, with different input definitions (e.g., for RDF data).

## 5. Known Issues & TODOs

*   **Known Issues:**
    *   Currently, the agent reloads the KG file from disk on each `run` call if a `kg_file_path` is provided or if it's the first call for the default KG. For multiple queries within the same workflow to the same graph, this is inefficient. It maintains an in-memory graph per instance, but instantiation logic might need review for multi-step workflows.
        *   *Correction:* The `KnowledgeGraphAgent` in the latest `orchestrator.py` seems to be instantiated once per `agent_type` for a workflow run by the orchestrator. The `load_graph_from_file` method is called within its `run` method, so it would reload if `kg_file_path` changes or if it's the first load. If `kg_file_path` is consistent and the graph is already loaded, it might not reload. This needs verification.
*   **TODOs / Future Enhancements:**
    *   **Implement KG Population:** Add the capability to ingest RDF triples and persist changes (Plan 1.2.3, 1.2.4).
    *   **Graph Persistence Strategy:** Define a clear strategy for when and how to persist changes to the KG file (e.g., immediate save, save at end of workflow, explicit save command).
    *   **Error Handling:** Improve error messages for SPARQL syntax errors or query execution failures.
    *   **Scalability:** For very large KGs, consider integration with a dedicated graph database instead of relying solely on `rdflib` in-memory processing. (Long-term)
    *   **Named Graphs:** Explore use of `rdflib`'s support for named graphs if different datasets or versions need to be managed within the same KG file or store.
    *   **Configuration of Default KG Path:** Make the default KG file path more easily configurable.

## 6. Versioning Information

*   **Current Version:** Part of the overall CACM-ADK package version. Capability ID `urn:adk:capability:knowledge_graph_query_agent:v1` implies a version for its querying interface.
*   **Change Log (Summary or Link):** Refer to the project's main changelog. Key changes would involve updates to SPARQL execution, KG loading logic, or the addition of population capabilities.

## 7. Design Notes & Rationale (Optional)

*   The agent is designed to encapsulate all direct `rdflib` interactions, providing a simpler interface for other agents that need KG access.
*   The decision to load the KG file on demand (within the `run` method, potentially) aims for simplicity in basic cases but might need optimization for performance-critical scenarios with frequent querying of large, static KGs. The orchestrator's agent instance management partially mitigates this by reusing agent instances.

---
*Self-reflect and double check: This AGENT.MD for KnowledgeGraphAgent accurately reflects its current and planned functionalities, including querying and the upcoming population feature. Dependencies, testing considerations, and configuration notes are specific. Known issues and TODOs highlight important development areas. It correctly links to the parent AGENT.MD.*
