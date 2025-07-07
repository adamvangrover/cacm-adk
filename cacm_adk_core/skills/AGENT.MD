# AGENT.MD - Skills Module (`cacm_adk_core/skills`)

**Parent AGENT.MD:** `../../AGENT.MD`

This document provides specific guidance for working with Semantic Kernel Skills defined within the `cacm_adk_core/skills` directory. Skills in other locations (e.g., `native_skills.py`, `processing_pipeline/semantic_kernel_skills.py`) should also follow these general principles where applicable.

## 1. Purpose & Key Responsibilities of This Directory

*   **Purpose:** This directory is intended to house custom, domain-specific Semantic Kernel skills developed for the CACM-ADK project. These skills encapsulate discrete pieces of logic or functionality that can be invoked by Agents via the Semantic Kernel.
*   **Key Responsibilities:**
    *   Provide modular, reusable functions that can be easily integrated into different analytical workflows.
    *   Define clear input and output contracts for each skill function.
    *   Separate concerns, allowing complex agent logic to be broken down into smaller, manageable skill units.
    *   Enable the use of Semantic Kernel features like prompt templating (for LLM-based skills) and native Python function execution.

## 2. General Guidelines for Developing Skills

*   **Skill Class Structure:**
    *   Skills are typically organized into Python classes (e.g., `KGPopulationSkill`, `ESGAnalysisSkill`).
    *   Each method within the class that is intended to be a kernel skill function should be decorated with `@kernel_function`.
    *   Use `@kernel_function_context_parameter` decorator for parameters that should be injected by the kernel, if any (less common for direct inputs).
    *   Use descriptive names for skill classes and functions.
*   **Skill Functions:**
    *   **Inputs:** Clearly define input parameters using type hints. Use descriptive names. For LLM-based skills, these parameters often correspond to variables in a prompt template.
    *   **Outputs:** Functions should return values that are meaningful and can be easily consumed by the calling agent or subsequent skills. For complex outputs, consider returning a dictionary or a Pydantic model.
    *   **Asynchronous:** If a skill involves I/O (especially LLM calls), it should be an `async def` function.
    *   **Docstrings:** Provide clear docstrings for each skill function, explaining its purpose, arguments (`Args:`), and what it returns (`Returns:`). This is used by Semantic Kernel for describing the function.
    *   **Error Handling:** Implement appropriate error handling. If a skill cannot complete its operation, it should raise an informative exception.
*   **LLM-Based Skills:**
    *   **Prompts:**
        *   Store prompts in separate `.txt` files (e.g., within a `prompts` subdirectory or alongside the skill class if closely tied). (Ref Plan 1.3.2)
        *   Use Semantic Kernel's prompt templating syntax (e.g., `{{$input}}`) for dynamic values.
        *   Write clear, effective prompts designed to elicit the desired response from the LLM.
    *   **Configuration:** LLM service configuration (endpoint, API key) is handled by `KernelService`, not within individual skills.
*   **Native Python Skills:**
    *   These are regular Python functions that perform specific computations or operations.
    *   They should be pure functions as much as possible (i.e., output depends only on input, with no side effects).
*   **Registration:**
    *   Skills are typically registered with the `KernelService` instance, often by importing the skill class and using `kernel.add_plugin(plugin_instance=MySkillClass(), plugin_name="MyPluginName")`. This is usually handled centrally (e.g., in `KernelService` or where the kernel is initialized for the application).
    *   *Note:* The `plugin_name` is how Agents will refer to this group of skills.

## 3. Dependencies

*   **Internal Dependencies (Module Level):**
    *   `semantic_kernel` library (specifically decorators like `kernel_function`).
    *   Potentially other utility functions or classes within the `cacm_adk_core`.
*   **External Libraries:**
    *   Any libraries specific to the skill's functionality (e.g., `rdflib` for a KG-related skill, `numpy` for a numerical skill).

## 4. How to Test Skills in This Module

*   **General Approach:**
    *   Unit tests for skills should focus on testing the skill function's logic in isolation.
    *   For LLM-based skills, mock the LLM call itself (e.g., mock the `kernel.invoke_prompt_async` or the specific LLM connector method) to return predefined responses. Test that the skill correctly prepares the prompt and handles various LLM responses (success, error, empty).
    *   For native Python skills, provide a range of inputs and assert the outputs.
*   **Location of Tests:** Ideally, `tests/core/skills/test_[skill_name]_skill.py`.
*   **Running Tests:**
    ```bash
    pytest tests/core/skills/
    ```
    Or for a specific skill test file:
    ```bash
    pytest tests/core/skills/test_my_skill.py
    ```

## 5. Configuration Notes

*   **Prompt Files:** For LLM-based skills, the path to prompt files can be considered a configuration.
*   **Skill Registration:** The `plugin_name` used when registering a skill class with the kernel is important for how it's invoked. This is typically managed in `KernelService`.

## 6. Known Issues & TODOs (Module Level)

*   **TODO:** Establish a clear naming convention for skill plugins and functions to ensure consistency.
*   **TODO:** Develop a strategy for managing and versioning prompt templates for LLM-based skills more formally.

## 7. Versioning Information

*   Individual skills or skill classes are versioned as part of the overall CACM-ADK package.
*   If a skill function's signature (inputs/outputs) changes significantly, it might warrant a new function name or clear documentation of the breaking change.

---
*Self-reflect and double check: This AGENT.MD for the skills module provides general guidelines for skill development, covering structure, testing, and LLM considerations. It's a good companion to the specific AGENT.MD files that will be created for individual skills.*
