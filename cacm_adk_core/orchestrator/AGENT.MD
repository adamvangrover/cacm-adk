# AGENT.MD - Orchestrator

**Parent AGENT.MD:** `../../AGENT.MD`

This document provides specific guidance for working with the `Orchestrator` module within the CACM-ADK project.

## 1. Purpose & Key Responsibilities

*   **Purpose:** The Orchestrator is the central component responsible for managing and executing Credit Analysis Capability Module (CACM) workflows. It interprets CACM definitions, invokes appropriate agents or Semantic Kernel skills, and manages data flow between steps.
*   **Key Responsibilities:**
    *   Load and validate CACM workflow definitions against the CACM JSON schema.
    *   Load the `compute_capability_catalog.json` to map logical capabilities to executable components (agents or skills).
    *   Initialize and manage a `SharedContext` for each CACM workflow run, facilitating data sharing.
    *   Iterate through workflow steps defined in a CACM.
    *   Resolve input bindings for each step from CACM inputs, previous step outputs, or `SharedContext`.
    *   Invoke the correct agent (e.g., `AnalysisAgent`, `DataIngestionAgent`) or Semantic Kernel skill based on the `computeCapabilityRef` and catalog.
    *   Manage the lifecycle of agent instances for a given workflow run.
    *   Provide a mechanism for agents to request instances of other agents (`get_or_create_agent_instance`).
    *   Aggregate results from steps and map them to final CACM outputs.
    *   Log the execution flow and any errors encountered.

## 2. Dependencies

*   **Internal Dependencies:**
    *   `cacm_adk_core.validator.Validator`: For validating CACM instances.
    *   `cacm_adk_core.semantic_kernel_adapter.KernelService`: For accessing the Semantic Kernel instance and invoking skills.
    *   All registered Agent classes (e.g., `DataIngestionAgent`, `AnalysisAgent`, `KnowledgeGraphAgent`, `ReportGenerationAgent`, etc.) located in `cacm_adk_core.agents`.
    *   `cacm_adk_core.context.shared_context.SharedContext`: For managing run-specific data.
*   **External Libraries:**
    *   `semantic-kernel`: For interacting with the Semantic Kernel.
    *   `logging`: Standard Python logging.
*   **Configuration Files:**
    *   `config/compute_capability_catalog.json`: Defines the mapping from capability IDs to agents/skills. This is critical for the Orchestrator's function.
    *   CACM JSON workflow files (various locations, typically `examples/`).
*   **Data Sources (if applicable):**
    *   Indirectly, through the agents it invokes, the Orchestrator relies on whatever data sources those agents connect to.

## 3. How to Test This Component

*   **Unit Tests:**
    *   Location of unit tests: `tests/core/test_orchestrator.py` (for core logic) and `tests/core/test_orchestrator_integration.py` (for workflow execution tests).
    *   Key test scenarios:
        *   Validation of valid and invalid CACM instances.
        *   Correct loading and interpretation of the compute capability catalog.
        *   Proper resolution of input bindings (from CACM inputs, step outputs, SharedContext).
        *   Correct invocation of mocked Agents and mocked Semantic Kernel skills.
        *   Accurate aggregation and mapping of outputs.
        *   Handling of missing capabilities or invalid step definitions.
        *   `SharedContext` management and data propagation.
        *   Agent lifecycle management (creation, reuse).
    *   How to run unit tests:
        ```bash
        pytest tests/core/test_orchestrator.py
        pytest tests/core/test_orchestrator_integration.py
        ```
*   **Integration Tests:**
    *   The `test_orchestrator_integration.py` file contains tests that run complete (though often mocked) CACM workflows like `examples/msft_comprehensive_analysis_workflow.json`.
*   **Mocking:**
    *   `Validator`: Mock its `validate_cacm_against_schema` method.
    *   `KernelService`: Mock `get_kernel` and the kernel's `invoke` method or specific skill calls.
    *   Agent classes: Mock their `run` methods to return predefined outputs and check inputs.
    *   `SharedContext`: Can be instantiated directly, or its methods mocked if specific interactions need to be controlled.
*   **Manual Testing/Verification Steps:**
    *   Use `scripts/adk_cli.py run <path_to_cacm_workflow.json>` to execute workflows.
    *   Examine orchestrator logs printed to the console.
    *   Verify generated output files (e.g., reports) and the structure of final CACM outputs.

## 4. Configuration Notes (If Applicable)

*   The primary configuration is `config/compute_capability_catalog.json`. The Orchestrator's behavior is heavily dependent on the correctness and completeness of this catalog.
*   CACM workflow files themselves are configurations that drive the Orchestrator.
*   Logging level for the Orchestrator can be configured via standard Python logging mechanisms (currently set globally in `scripts/adk_cli.py`).

## 5. Known Issues & TODOs

*   **Known Issues:**
    *   *Placeholder:* (Example) "Error reporting for deeply nested binding failures could be more specific."
*   **TODOs / Future Enhancements:**
    *   TODO: Implement more sophisticated error recovery or conditional branching in workflows.
    *   TODO: Explore dynamic workflow modification based on runtime conditions (advanced).
    *   TODO: Add support for explicit versioning of compute capabilities in the catalog and CACM files.
    *   TODO: Enhance logging with more structured data for easier parsing and analysis.

## 6. Versioning Information

*   **Current Version:** The Orchestrator is versioned as part of the overall CACM-ADK package. Refer to the project's main version.
*   **Change Log (Summary or Link):** Refer to the project's main changelog. Key changes affecting the Orchestrator would typically involve updates to workflow execution logic, agent interaction, or capability resolution.

## 7. Design Notes & Rationale (Optional)

*   The Orchestrator is designed to be stateless regarding individual workflow runs; all run-specific state is intended to be managed within the `SharedContext` object passed to agents.
*   The shift to an `async def run_cacm` method was made to support asynchronous agents and skills, improving potential I/O-bound performance.
*   The `get_or_create_agent_instance` mechanism allows agents to collaborate without the Orchestrator needing to pre-declare all agent interactions, promoting looser coupling.

---
*Self-reflect and double check: Content is specific to the Orchestrator, follows the template, includes relevant details from codebase (dependencies, testing paths), and uses placeholders for future items.*
