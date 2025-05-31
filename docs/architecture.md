# CACM-ADK System Architecture

## High-Level Overview

The CACM-ADK is an agent-driven framework designed to assist in authoring and executing standardized Credit Analysis Capability Modules (CACMs). It leverages Semantic Kernel for orchestrating both native Python functions (as skills) and potential AI/LLM-driven capabilities. The architecture emphasizes modularity, skill-based task execution, and collaborative agents to perform complex credit analysis workflows defined in CACMs. The system aims to be portable, extensible, and provide a robust environment for developing and managing credit analysis processes.

## Key Architectural Layers & Components

### 1. User Interface / Entry Point
*   **REST API Layer (FastAPI):**
    *   Exposes functionalities via a RESTful API (`api/main.py`) for programmatic interaction with the Orchestrator, Template Engine, Validator, and Ontology Navigator.
*   **Web UI (Landing Page):**
    *   A simple HTML landing page (`static/index.html`) providing an overview and links to documentation and API demos.
*   **Command Line Interface (CLI):**
    *   The ADK CLI Tool (`scripts/adk_cli.py`) provides direct access to core ADK functionalities for developers and scripting.

### 2. CACM-ADK Core Engine (`cacm_adk_core/`)
This engine houses the primary logic for CACM authoring, processing, and agent-based execution.

*   **Orchestrator (`orchestrator/orchestrator.py`) - Agent Workflow Orchestrator/Manager:**
    *   Loads CACM definitions and the `Compute Capability Catalog`.
    *   Parses CACM workflows, resolving each step to either an agent invocation or a direct Semantic Kernel skill call.
    *   Manages the lifecycle of agents and the `SharedContext` for each CACM workflow run.
    *   For agent-based steps, it instantiates/reuses the appropriate agent (e.g., `DataIngestionAgent`, `AnalysisAgent`) and passes the task description, step-specific inputs, and the shared context.
    *   For skill-based steps (if no agent is specified), it can directly invoke skills registered with the `KernelService`.
    *   It facilitates inter-agent communication by providing a mechanism for agents to request instances of other agents.
    *   Aggregates results from steps and maps them to final CACM outputs.

*   **Agent Subsystem (`agents/`):**
    *   **`base_agent.py` (`Agent` class):** An abstract base class defining the common interface for all agents, including `__init__`, `get_kernel`, `set_agent_manager`, `get_or_create_agent`, and an abstract `async def run(task_description, current_step_inputs, shared_context)` method.
    *   **`data_ingestion_agent.py` (`DataIngestionAgent`):** Responsible for data intake tasks, such as fetching documents or data from specified sources. It updates the `SharedContext` with references to ingested data (e.g., document URIs, processed data snippets).
    *   **`analysis_agent.py` (`AnalysisAgent`):** Performs analytical tasks. It can use `SharedContext` to access data prepared by other agents (e.g., `DataIngestionAgent`). It leverages Semantic Kernel skills (e.g., `FinancialAnalysis.calculate_basic_ratios` native skill) for computations. It can also communicate with other agents (e.g., `ReportGenerationAgent`) to pass on its findings.
    *   **`report_generation_agent.py` (`ReportGenerationAgent`):** Compiles findings from `SharedContext` and data passed by other agents (e.g., analysis results from `AnalysisAgent`) into structured reports.
    *   **Agent Communication:** Agents can request instances of other agents via their `agent_manager` (the Orchestrator), enabling direct method calls for passing information (e.g., `AnalysisAgent` calling `ReportGenerationAgent.receive_analysis_results()`).

*   **Semantic Kernel Integration:**
    *   **`semantic_kernel_adapter.py` (`KernelService`):** A singleton service that initializes and manages the global Semantic Kernel instance. It configures LLM services (e.g., OpenAI, using environment variables for API keys) and registers plugins (collections of skills).
    *   **`native_skills.py`:** Contains Python classes (e.g., `BasicCalculationSkill`, `FinancialAnalysisSkill`) whose methods are decorated with `@kernel_function` to become native Semantic Kernel skills. These skills are registered with the `KernelService`.
    *   **`processing_pipeline/semantic_kernel_skills.py`:** (Conceptual/Placeholder) Intended for defining LLM-based semantic functions (e.g., `SK_MDNA_SummarizerSkill`). These skills would also be registered with the `KernelService` and could be invoked by agents or the orchestrator.

*   **Shared Context (`context/shared_context.py`):**
    *   The `SharedContext` class provides a centralized object for data sharing and session state management throughout a single CACM workflow execution.
    *   It holds a unique `session_id`, the `cacm_id`, references to documents and knowledge bases, global parameters for the run, and a general `data_store` for inter-agent/skill data exchange.
    *   Agents receive and update the `SharedContext` during their execution.

*   **Template Engine (`template_engine.py`):**
    *   Lists and instantiates CACM templates (pure JSON).
*   **Semantic & Structural Validator (`validator.py`):**
    *   Validates CACM instances against the JSON schema (`cacm_schema_v0.2.json`).
*   **Report Generator (`report_generator.py`):** (Note: This is a separate, older component. Its functionality will likely be superseded or integrated with `ReportGenerationAgent`).
    *   Simulates multi-persona rationale for reports.
*   **Ontology Navigator (`ontology_navigator/ontology_navigator.py`):**
    *   Loads and provides query access to the project's RDF/OWL ontology using `rdflib`.

### 3. Data & Standards Layer
*   **CACM Standard (`cacm_standard/cacm_schema_v0.2.json`):**
    *   JSON schema for CACM definitions.
*   **Ontology (`ontology/credit_analysis_ontology_v0.3/credit_ontology_v0.3.ttl`):**
    *   Provides semantic definitions. Recently updated with an `adkarch:` namespace to define architectural components like `adkarch:Agent`, specific agent types (e.g., `adkarch:AnalysisAgent`), `adkarch:SemanticSkill`, and properties like `adkarch:usesSkill` and `adkarch:communicatesWith`.
*   **Compute Capability Catalog (`config/compute_capability_catalog.json`):**
    *   Maps logical capabilities referenced in CACM workflows to specific execution handlers.
    *   Now includes fields like `agent_type` (to dispatch to a specific agent class) or `skill_plugin_name` and `skill_function_name` (for direct Semantic Kernel skill invocation). This guides the Orchestrator.
*   **CACM Templates (`cacm_library/templates/`):**
    *   Library of predefined, reusable CACM structures.

### 4. External Dependencies & Services
*   **Semantic Kernel:** Used for skill management and orchestration.
*   **(Future):** LLMs, dedicated Ontology Store, external Compute Services.

### 5. Developer/Analyst Tools
#### Jupyter Notebook: Interactive Report Crafter
(As previously described, remains relevant for prompt engineering and understanding data-to-report flows).

## Data Flows

1.  **CACM Definition:** A user authors or selects a CACM template (JSON).
2.  **Workflow Initiation:** The CACM instance (JSON) is submitted to the Orchestrator (e.g., via API or CLI).
3.  **Orchestrator Processing:**
    *   The Orchestrator validates the CACM.
    *   It initializes a `SharedContext` for this CACM run (e.g., `cacm_id`, `session_id`, initial inputs).
    *   It iterates through the `workflow` steps defined in the CACM.
4.  **Step Execution (Agent or Skill):**
    *   For each step, the Orchestrator consults the `Compute Capability Catalog` using the step's `computeCapabilityRef`.
    *   **If `agent_type` is specified:**
        *   The Orchestrator instantiates or reuses the specified agent (e.g., `DataIngestionAgent`).
        *   The agent is provided with the `SharedContext`, a task description, and resolved inputs for the current step.
        *   The agent executes its `run` method:
            *   It may interact with external data sources.
            *   It may update the `SharedContext` (e.g., `DataIngestionAgent` adds document references; `AnalysisAgent` might store intermediate findings).
            *   It can invoke Semantic Kernel skills (native or LLM-based) using its `KernelService` access. Arguments for skills can be drawn from its inputs or `SharedContext`.
            *   It can request other agents via `self.agent_manager.get_or_create_agent_instance()` and communicate by calling their methods (e.g., `AnalysisAgent` calling `ReportGenerationAgent.receive_analysis_results()`).
        *   The agent returns a result dictionary to the Orchestrator.
    *   **If `skill_plugin_name` / `skill_function_name` are specified (and no `agent_type`):**
        *   The Orchestrator directly prepares arguments and invokes the specified Semantic Kernel skill via `KernelService`.
        *   The skill result is processed.
    *   **(Fallback):** If neither agent nor skill is specified, legacy Python functions from `capability_function_map` might be called, or a mock response generated.
5.  **Data Sharing & State:**
    *   Agents use the `SharedContext` to pass data, references, and parameters between each other implicitly (by writing to and reading from common context areas) or explicitly (by passing data in direct calls).
6.  **Output Aggregation:**
    *   The Orchestrator collects results from each step and maps them to the final CACM outputs as defined in the `outputBindings` and the CACM's root `outputs` section.
7.  **Result Return:** The Orchestrator returns the final aggregated outputs of the CACM execution.

*(A visual diagram illustrating this flow, showing the Orchestrator, Agents, SharedContext, Semantic Kernel, and Catalog, would be beneficial for clarity.)*

## Deployment Model

### Containerization (Docker)
(As previously described)

### Local Development
(As previously described)
