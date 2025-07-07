# AGENT.MD - Agents Module (`cacm_adk_core/agents`)

**Parent AGENT.MD:** `../../AGENT.MD`

This document provides specific guidance for working with the Agents module and individual agent implementations within the CACM-ADK project.

## 1. Purpose & Key Responsibilities of the Agents Module

*   **Purpose:** This module contains the core building blocks for the agent-based architecture of the CACM-ADK. It defines the base `Agent` class and houses various specialized agent implementations that perform specific tasks within a CACM workflow (e.g., data ingestion, analysis, report generation, knowledge graph interaction).
*   **Key Responsibilities:**
    *   Define a common interface and core functionalities for all agents through `base_agent.py`.
    *   Provide concrete agent implementations that are addressable by the `Orchestrator` via the `compute_capability_catalog.json`.
    *   Encapsulate specific business logic and interaction with Semantic Kernel skills or external services within each agent.
    *   Interact with the `SharedContext` to read inputs and store results.
    *   Enable agent-to-agent communication when necessary, facilitated by the `Orchestrator`.

## 2. General Guidelines for Developing Agents

*   **Inheritance:** All agents MUST inherit from the `Agent` class in `base_agent.py`.
*   **Asynchronous Operations:** The primary `run` method of an agent MUST be an `async def` method to support non-blocking operations, especially when dealing with I/O (like LLM calls, file access, or future API calls).
*   **Constructor:** Agent constructors should typically accept `kernel_service: KernelService` and any other static configuration they might need. Avoid complex logic in constructors; prefer initialization in the `run` method or dedicated setup methods if needed.
*   **`run` Method Signature:** The `run` method should generally follow the signature:
    `async def run(self, task_description: str, current_step_inputs: Dict[str, Any], shared_context: SharedContext) -> Dict[str, Any]:`
    *   `task_description`: A string describing the current task, often derived from the CACM step description.
    *   `current_step_inputs`: A dictionary of inputs resolved by the Orchestrator for the current step.
    *   `shared_context`: The `SharedContext` object for the current workflow run. Agents should use this to get broader context data and store their primary outputs if they need to be accessed by subsequent, unrelated agents.
    *   Return value: A dictionary representing the structured output of the agent for that specific task invocation. This output is what the Orchestrator binds to CACM outputs or subsequent step inputs.
*   **Logging:** Use `self.logger` (available from the base `Agent` class) for all logging within agents. Provide informative log messages.
*   **Error Handling:** Implement robust error handling. If an agent cannot complete its task, it should log the error and return an appropriate error structure in its output dictionary (e.g., `{"status": "error", "message": "Details of error"}`). The Orchestrator will log this. Critical failures might need to raise exceptions if they should halt the entire workflow, but this should be used judiciously.
*   **Skill Usage:** Agents should interact with Semantic Kernel by:
    *   Getting the kernel instance: `kernel = self.get_kernel()`.
    *   Getting specific plugins/skills: `plugin = self.get_plugin("MyPluginName")` or `skill_function = kernel.plugins["MyPluginName"]["MySkillFunction"]`.
    *   Invoking skills: `await kernel.invoke(skill_function, KernelArguments(**skill_inputs))`.
*   **Idempotency (where applicable):** Consider if an agent's operations can be made idempotent, though this is often difficult with LLM-based agents.
*   **Modularity:** Keep agents focused on a specific set of responsibilities. If an agent becomes too large or complex, consider breaking it down into smaller, more specialized agents or utility classes/skills.

## 3. Dependencies

*   **Internal Dependencies (Module Level):**
    *   `cacm_adk_core.agents.base_agent.Agent`: The base class for all agents.
    *   `cacm_adk_core.semantic_kernel_adapter.KernelService`: Injected into agents for SK access.
    *   `cacm_adk_core.context.shared_context.SharedContext`: Passed to the `run` method.
    *   `cacm_adk_core.orchestrator.Orchestrator` (indirectly, for agent-to-agent communication via `self.agent_manager`).
    *   Specific skills from `cacm_adk_core.skills` or native skills from `cacm_adk_core.native_skills` and `cacm_adk_core.processing_pipeline.semantic_kernel_skills`.
*   **External Libraries:**
    *   `semantic-kernel`
    *   `logging`

## 4. How to Test Agents in This Module

*   **General Approach:**
    *   Unit tests for individual agents should mock `KernelService`, other agents (if interacted with directly), and `SharedContext`.
    *   Focus on testing the agent's internal logic: how it processes inputs, interacts with its mocked dependencies (skills, context), and produces outputs.
*   **Location of Tests:** `tests/core/agents/test_[agent_name]_agent.py`
*   **Running Tests:**
    ```bash
    pytest tests/core/agents/
    ```
    Or for a specific agent:
    ```bash
    pytest tests/core/agents/test_analysis_agent.py
    ```

## 5. Configuration Notes

*   Agents are typically configured via their entries in `config/compute_capability_catalog.json`, which specifies their `agent_type` and expected inputs/outputs for a given capability ID.
*   Further configuration can be passed through `current_step_inputs` during the `run` method, originating from the CACM workflow definition.

## 6. Known Issues & TODOs (Module Level)

*   **TODO:** Develop a more standardized error reporting structure for agents to return to the Orchestrator.
*   **TODO:** Explore common utility functions that could be added to the base `Agent` class or a shared agent utility module.

## 7. Versioning Information

*   Individual agents are versioned as part of the overall CACM-ADK package.
*   If an agent's interface (inputs/outputs for a registered capability) changes significantly, the corresponding entry in `compute_capability_catalog.json` should ideally be versioned (e.g., `urn:adk:capability:my_agent:v2`).

---
*Self-reflect and double check: This AGENT.MD for the agents module provides good high-level guidance for anyone developing or working with agents in this directory. It covers inheritance, async nature, run method signature, logging, error handling, and testing specific to agents. It correctly links to the parent AGENT.MD.*
