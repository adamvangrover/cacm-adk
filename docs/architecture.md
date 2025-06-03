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
    *   **`data_ingestion_agent.py` (`DataIngestionAgent`):** Responsible for data intake tasks. It has been updated to conceptually handle new alternative data types (e.g., utility payments, social sentiment data from `altdata_social_sentiment_json`) and ESG factors (e.g., carbon emissions from `esg_carbon_emissions_json`, overall ESG ratings from `esg_overall_rating_json`), storing this data into `SharedContext` using descriptive keys (e.g., `altdata_utility_payments`, `esg_carbon_emissions`).
    *   **`analysis_agent.py` (`AnalysisAgent`):** Significantly enhanced to perform a wider range of analytical tasks.
        *   It utilizes the now LLM-powered `CustomReportingSkills` (from `processing_pipeline/semantic_kernel_skills.py`) to generate narrative financial performance summaries, key risk summaries, and overall assessments. It also uses the new `generate_explanation` skill from `CustomReportingSkills` for providing XAI-style explanations of financial ratios.
        *   It orchestrates ESG data analysis by:
            1.  Formulating a SPARQL query to fetch ESG data (metrics and overall ratings) for the company from the Knowledge Graph, using a dynamically constructed company URI.
            2.  Invoking the `KnowledgeGraphAgent` with this SPARQL query.
            3.  Passing the structured query results from `KnowledgeGraphAgent` to the `ESGAnalysisSkill.summarize_esg_factors_from_kg` skill for processing and categorization.
        *   Stores these various enriched outputs (LLM-generated summaries, ratio explanations, summarized ESG data) in `SharedContext` using keys like `financial_performance_summary_llm`, `key_ratios_explanations_llm`, and `summarized_esg_data`.
        *   Includes new conceptual placeholders for data drift (comparing current financial data points like `current_assets` against hardcoded historical means) and model drift detection (comparing a key calculated ratio like `current_ratio` against a historical average). These checks log warnings and update an operational summary but do not halt execution.
    *   **`knowledge_graph_agent.py` (`KnowledgeGraphAgent`):**
        *   Its capabilities have been expanded to include dynamic Knowledge Graph population.
        *   It can now accept structured data (e.g., from `SharedContext` via an orchestrator or another agent) as an input parameter (`data_for_kg_population`).
        *   It utilizes the new `KGPopulationSkill.generate_rdf_triples` skill to convert this input data into a list of RDF triples.
        *   These newly generated triples are parsed and added to its in-memory RDFlib graph *before* any SPARQL query execution, allowing queries to reflect this dynamically added information. It can also load an initial graph from a file.
    *   **`report_generation_agent.py` (`ReportGenerationAgent`):** Compiles findings into structured reports.
        *   Enhanced to retrieve and incorporate the LLM-generated narrative summaries (financial, risk, overall assessment) and financial ratio explanations produced by `AnalysisAgent` (via `SharedContext`).
        *   It now includes a dedicated, dynamically numbered section for "ESG Factors Summary", populated from the `summarized_esg_data` retrieved from `SharedContext`.
    *   **Agent Communication:** Agents can request instances of other agents via their `agent_manager` (the Orchestrator), enabling direct method calls for passing information. However, `SharedContext` remains the primary mechanism for passing complex data products between analysis stages.

*   **Semantic Kernel Integration:**
    *   **`semantic_kernel_adapter.py` (`KernelService`):** A singleton service that initializes and manages the global Semantic Kernel instance. It configures LLM services and registers all skills/plugins.
    *   **`native_skills.py`:** Contains core native Python skills like `BasicCalculationSkill` and `FinancialAnalysisSkill`.
    *   **`processing_pipeline/semantic_kernel_skills.py`:** Defines more complex skills, now actively leveraging LLMs:
        *   `SK_MDNA_SummarizerSkill`: Enhanced to use LLMs for generic text summarization.
        *   `CustomReportingSkills`: Significantly upgraded to use LLMs for generating narrative financial performance summaries, key risk summaries, and overall assessments. It also includes the new `generate_explanation` skill for XAI-style explanations of financial data points.
    *   **`cacm_adk_core/skills/kg_population_skills.py`:**
        *   Introduces `KGPopulationSkill` with the `generate_rdf_triples` method. This skill converts structured Python dictionaries (conceptually from `SharedContext`) into RDF triples based on the project's ontology, preparing data for dynamic KG ingestion by `KnowledgeGraphAgent`.
    *   **`cacm_adk_core/skills/esg_analysis_skill.py`:**
        *   Introduces `ESGAnalysisSkill` with the `summarize_esg_factors_from_kg` method. This native Python skill processes the structured JSON-like results from `KnowledgeGraphAgent` SPARQL queries (specifically those fetching ESG data) and transforms them into a categorized, human-readable summary dictionary.
    *   **Skill Registration and Usage:** All these skills are registered with the `KernelService` under respective plugin names (e.g., "SummarizationSkills", "ReportingAnalysisSkills", "KGPopulation", "ESGAnalysis"). Agents invoke these skills via the kernel instance, passing arguments through `KernelArguments`.

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
    *   Provides semantic definitions for credit analysis concepts. It has been significantly extended to include:
        *   `altdata:` namespace: New classes (e.g., `altdata:UtilityPaymentRecord`, `altdata:SocialMediaSentiment`, `altdata:GeospatialRiskIndicator`) and properties for representing various alternative data types.
        *   `esg:` namespace: New classes (e.g., `esg:ESGMetric`, `esg:EnvironmentalFactor`, `esg:CarbonEmission`, `esg:OverallESGRating`) and properties for modeling Environmental, Social, and Governance factors.
        *   The existing `adkarch:` namespace defines architectural components like `adkarch:Agent`, specific agent types, `adkarch:SemanticSkill`, and relevant properties.
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
    *   Agents use the `SharedContext` extensively to pass data, references, and parameters. Key data flows now include:
        *   **Conceptual Raw Data (including Alt/ESG):** `DataIngestionAgent` "ingests" various data types (financials, risk text, conceptual alternative data like utility payments or social sentiment, ESG data like carbon emissions or overall ratings) and stores them in `SharedContext`.
        *   **Data for KG Population:** Data from `SharedContext` (e.g., ingested by `DataIngestionAgent`) can be passed as `data_for_kg_population` input to `KnowledgeGraphAgent`.
        *   **KG Population Process:** `KnowledgeGraphAgent` receives this data, invokes `KGPopulationSkill.generate_rdf_triples` to convert it into RDF triples based on the ontology, and then adds these triples to its in-memory graph.
        *   **ESG Data Retrieval & Summarization Flow:**
            1. `AnalysisAgent` formulates a SPARQL query to fetch ESG data for a specific company (identified by a URI constructed from `SharedContext` data).
            2. `AnalysisAgent` invokes `KnowledgeGraphAgent`, passing the SPARQL query. `KnowledgeGraphAgent` executes this query against its (potentially dynamically populated) graph.
            3. `AnalysisAgent` receives the structured JSON-like results from `KnowledgeGraphAgent`.
            4. `AnalysisAgent` invokes `ESGAnalysisSkill.summarize_esg_factors_from_kg`, passing the KG query results and company name.
            5. The `ESGAnalysisSkill` processes these results and returns a categorized summary dictionary.
            6. `AnalysisAgent` stores this summary in `SharedContext` (e.g., under `summarized_esg_data`).
        *   **LLM-Generated Content (Summaries, Explanations):**
            1. `AnalysisAgent` uses data from `SharedContext` (e.g., `structured_financials_for_summary`, `risk_factors_section_text`, `calculated_key_ratios`) as input for skills within `CustomReportingSkills` or `SK_MDNA_SummarizerSkill`.
            2. These skills (now LLM-powered) generate narrative summaries (financial performance, risk, overall assessment) and explanations for financial ratios.
            3. `AnalysisAgent` stores these LLM-generated text outputs in `SharedContext` (e.g., `financial_performance_summary_llm`, `key_risks_summary_llm`, `overall_assessment_llm`, `key_ratios_explanations_llm`).
        *   **Report Content Assembly:** `ReportGenerationAgent` retrieves the processed financial data, LLM-generated narrative summaries and explanations, and the summarized ESG data from `SharedContext` (and potentially from direct agent communication payloads if `AnalysisAgent` sends its full operational log) to compile the final comprehensive report.
6.  **Output Aggregation:**
    *   The Orchestrator collects results from each step and maps them to the final CACM outputs as defined in the `outputBindings` and the CACM's root `outputs` section.
7.  **Result Return:** The Orchestrator returns the final aggregated outputs of the CACM execution.

*(A visual diagram illustrating this flow would now need to highlight the interactions between `AnalysisAgent`, `KnowledgeGraphAgent`, `KGPopulationSkill`, `ESGAnalysisSkill`, the LLM-powered reporting/summarization skills, and how `SharedContext` facilitates the complex data exchanges for KG population, ESG analysis, and advanced report generation.)*

## Deployment Model

### Containerization (Docker)
(As previously described)

### Local Development
(As previously described)
