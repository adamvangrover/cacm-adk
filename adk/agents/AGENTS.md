# AGENTS.md - adk/agents/

This document provides guidance for AI agents (like Jules) working with the code in the `adk/agents/` directory and its subdirectories. This directory contains base agent classes and specific agent implementations.

## 1. Overview & Purpose

*   **What is this directory/module about?** This directory houses the core agent implementations of the ADK. Agents are the primary actors in the system, responsible for performing tasks, interacting with skills, managing data, and communicating with other agents or external services.
*   **Key functionalities:**
    1.  Defining base agent behaviors and lifecycles.
    2.  Implementing specialized agents for tasks like data ingestion, knowledge graph interaction, analysis, and reporting.
    3.  Integrating with the Orchestrator and Semantic Kernel.

## 2. Coding Conventions

*   **General Style:** Adhere to PEP 8.
*   **Naming Conventions:**
    *   Agent classes: `PascalCase` ending with `Agent` (e.g., `MyNewPurposeAgent`).
    *   Agent methods: `async def method_name(...)` for potentially long-running or I/O-bound operations.
*   **Docstrings:**
    *   Google-style docstrings are mandatory for all agent classes and their public methods.
    *   Clearly document the agent's purpose, key methods, and any important configuration parameters it expects.
    *   For methods, document parameters, return values, and any significant side effects or exceptions raised.
*   **Logging:**
    *   Each agent should obtain its own logger: `self.logger = logging.getLogger(self.__class__.__name__)` or `logging.getLogger(__name__)` at the module level.
    *   Log key lifecycle events (e.g., initialization, task start/completion) and important decisions or errors.
*   **Error Handling:**
    *   Agents should handle exceptions from skills or external calls gracefully.
    *   Use custom exceptions from `adk.exceptions` where appropriate.
*   **Configuration:**
    *   Agents are typically configured via parameters passed to their `__init__` method, often originating from YAML files loaded by the Orchestrator or a central configuration manager.
    *   Document expected configuration keys in the agent's class docstring.
*   **Asynchronous Operations:**
    *   Many agent methods should be `async` to allow for non-blocking I/O operations, especially when interacting with external services, Semantic Kernel, or other agents. Use `await` for such calls.

## 3. Testing Procedures

*   **Test Location:** Unit tests for agents in `adk/agents/my_agent.py` should be in `tests/agents/test_my_agent.py`.
*   **Test Framework:** pytest.
*   **Running Tests:**
    *   Command to run all tests for agents: `pytest tests/agents/`
    *   Command to run a specific agent's test file: `pytest tests/agents/test_my_agent.py`
*   **Agent Testing Specifics:**
    *   **Initialization:** Test that agents initialize correctly with various configurations (valid and invalid).
    *   **Method Logic:** Test the core logic of each public agent method.
    *   **Skill Interaction:** Mock Semantic Kernel and skill invocations. Verify that the agent calls skills with correct parameters and handles their responses (or exceptions) appropriately.
        *   Use `mocker.patch.object(target_agent_instance.kernel, 'invoke')` or `mocker.patch.object(target_agent_instance.kernel.skills, 'get_function')`.
    *   **KG Interaction:** If the agent interacts with the Knowledge Graph, mock the `KnowledgeGraphAgent` or its methods. Verify that SPARQL queries (if constructed by the agent) are correct and that KG responses are processed as expected.
    *   **State Changes:** If an agent manages internal state, test that state transitions are correct based on inputs and method calls.
    *   **A2A Communication:** If the agent communicates with other agents (e.g., via Orchestrator), mock the Orchestrator or the target agent.

## 4. Interaction with Knowledge Graph (KG) & Ontology

*   **Primary Ontology:** `ontology/credit_analysis_ontology_v0.3/credit_ontology_v0.3.ttl`
*   **Key Classes/Properties Used:**
    *   Agents like `KnowledgeGraphAgent` will interact with most of the ontology.
    *   `DataIngestionAgent` might create instances of `cacm_ont:DataInput` and its subclasses (e.g., `cacm_ont:FinancialStatement`, `altdata:AlternativeDataRecord`, `esg:ESGMetric`).
    *   `AnalysisAgent` types might query for `kgclass:Obligor`, `kgclass:FinancialInstrument`, `cacm_ont:Metric`, `kgclass:RiskFactor`, etc., and produce new `kgclass:Analysis` or `cacm_ont:Metric` instances.
    *   `adkarch:Agent` instances representing the agents themselves can be created in the KG by an orchestrator or a specialized "SystemMetadaAgent".
*   **Querying/Populating the KG:**
    *   Agents should generally use the `KnowledgeGraphAgent` (or a similar abstraction layer) for all KG operations. Avoid embedding raw SPARQL queries directly in business logic agents if possible; centralize them in the `KnowledgeGraphAgent` or dedicated query modules/skills.
    *   When populating, ensure all created triples strictly adhere to the ontology (correct classes, properties, datatypes, relationships).
    *   `KnowledgeGraphAgent` should provide methods like `add_triples(triples)`, `query(sparql_query)`.

## 5. Versioning (Agents, Skills, Data)

*   **Agent Versioning:** Significant changes to an agent's public interface (methods, parameters it accepts, or core behavior) should be highlighted in PRs. Consider if this constitutes a conceptual "vNext" of the agent if changes are breaking.
*   Refer to the root `AGENTS.md` for general versioning guidelines on code, ontology, and CACMs.

## 6. Key Dependencies & Setup

*   **Core Dependencies:**
    *   `semantic-kernel`: For agents that utilize Semantic Kernel skills.
    *   `aiohttp` (or similar): For async HTTP calls if agents interact directly with external APIs.
    *   RDFLib or similar: Likely used by `KnowledgeGraphAgent`.
*   **Services:**
    *   Agents may depend on a running Triple Store (if `KnowledgeGraphAgent` connects to one remotely).
    *   Access to LLM services (e.g., Azure OpenAI) if using LLM-based skills.
*   **Setup:**
    *   Ensure environment variables for LLM services and any other external APIs are correctly set.

## 7. Important Notes & Gotchas

*   **Agent State:** Be mindful of agent state. If agents are intended to be stateless, ensure methods do not rely on accumulating instance variables in a way that affects subsequent independent calls (unless explicitly designed as a stateful agent for a specific workflow).
*   **Idempotency:** For agents that modify external state (like KG or databases), strive for idempotent operations where possible.
*   **Configuration Propagation:** The Orchestrator is typically responsible for loading agent configurations and passing them during agent instantiation.
*   **Agent Naming in KG:** If agents are represented in the KG, ensure their instance URIs are unique and consistently generated.

## 8. Verification Checks for Agents

*Before submitting changes to this module, an AI agent (like Jules) MUST perform the following checks:*

1.  **Run all unit tests for the `adk/agents/` directory and ensure they pass.**
    *   Command: `pytest tests/agents/`
2.  **Run linters (e.g., Flake8, Black) on `adk/agents/` and address all reported issues.**
    *   Command: `flake8 adk/agents/ ; black adk/agents/`
3.  **Verify that all new or modified agent classes and their public methods have clear, Google-style docstrings, including documentation of their expected configuration.**
4.  **If an agent's KG interaction logic was changed, manually review sample SPARQL queries generated or executed, and the structure of any triples it would add to the KG.**
5.  **Ensure agents correctly handle potential failures from skill invocations or external API calls (e.g., using try-except blocks, logging errors).**
6.  **Update this `AGENTS.md` file if any of the above instructions have changed due to your work.**

---
*This `AGENTS.md` is a living document. If you find it to be inaccurate or incomplete, please update it.*
```
