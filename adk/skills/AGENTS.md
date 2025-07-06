# AGENTS.md - adk/skills/

This document provides guidance for AI agents (like Jules) working with the code in the `adk/skills/` directory and its subdirectories. This directory contains Semantic Kernel skill plugins, including both native Python functions and semantic (prompt-based) functions.

## 1. Overview & Purpose

*   **What is this directory/module about?** This directory is the central repository for all Semantic Kernel skills used by agents in the ADK. Skills encapsulate specific functionalities, making them reusable across different agents and CACMs.
*   **Key functionalities:**
    1.  Defining native Python functions as skills (e.g., for complex calculations, data transformations).
    2.  Defining semantic skills using LLM prompts (e.g., for summarization, text generation, classification).
    3.  Organizing skills into logical plugins (classes for native skills, directories for semantic skills).

## 2. Coding Conventions (for Native Skills)

*   **General Style:** Adhere to PEP 8.
*   **Naming Conventions:**
    *   Skill plugin classes: `PascalCase` ending with `Skill` (e.g., `FinancialAnalysisSkill`).
    *   Native skill functions (methods within plugin classes): `snake_case`.
    *   Semantic skill directories: `PascalCase` matching the conceptual function name (e.g., `SummarizeText`).
*   **Docstrings:**
    *   Google-style docstrings for Python plugin classes and native skill functions.
    *   **Crucially, the `@sk_function` decorator's `description` and `@sk_function_context_parameter` decorator's `description` are vital.** These descriptions are used by Semantic Kernel (and potentially by LLMs using function calling) to understand what the function does and what its parameters mean. Make them clear, concise, and accurate.
*   **Logging:**
    *   Use the standard Python `logging` module within native skill functions if complex logic requires it.
    *   Acquire loggers via `logging.getLogger(__name__)`.
*   **Error Handling:**
    *   Native skill functions should handle their own exceptions gracefully and can return error messages or raise specific exceptions that calling agents can catch.
    *   Avoid letting exceptions escape that would crash the Semantic Kernel planner or agent.
*   **Skill Function Signatures (Native Skills):**
    *   Native skill functions typically accept `self` and `context: SKContext` or individual parameters extracted from the context (e.g., `input: str`).
    *   If taking `SKContext`, clearly document the expected context variables in the `@sk_function_context_parameter` descriptions.
    *   Return types should generally be strings, or types easily convertible to strings, as this is common for SK interop. If returning complex objects, ensure the calling agent/skill knows how to handle them (often by serializing to JSON).

## 3. Semantic (Prompt-Based) Skill Structure

*   Each semantic skill should reside in its own subdirectory within a plugin directory, e.g., `adk/skills/MyPluginName/MySemanticSkillName/`.
*   **`skprompt.txt`**: Contains the LLM prompt.
    *   Use placeholders like `{{$input}}` or `{{$parameter_name}}` for variables.
    *   Write clear and effective prompts. Follow prompt engineering best practices.
*   **`config.json`**: Describes the semantic function.
    *   `type`: e.g., "completion", "embedding".
    *   `description`: **Crucial for planners.** Clearly explain what the skill does.
    *   `input`: Define input parameters, their descriptions, and default values.
        *   Parameter names here should match those in `skprompt.txt`.
    *   `completion` (or other type-specific settings): Configure LLM parameters (e.g., `max_tokens`, `temperature`).
*   **Externalize Prompts:** Always use this directory structure; do not embed large or complex prompts directly in Python code.

## 4. Testing Procedures

*   **Test Location:**
    *   Native skills: Unit tests in `tests/skills/test_my_plugin_name.py`.
    *   Semantic skills: Testing is more nuanced.
*   **Test Framework:** pytest.
*   **Running Tests:**
    *   Command to run all tests for skills: `pytest tests/skills/`
*   **Native Skill Testing:**
    *   Test the Python functions directly, providing appropriate inputs (mocking `SKContext` if necessary, or passing direct string/value inputs).
    *   Verify correct return values and any side effects.
*   **Semantic Skill Testing:**
    *   **Basic Invocation:** At a minimum, have a test that loads and invokes the semantic skill with sample input to ensure the prompt and config are valid and the LLM call can be made.
    *   **Output Evaluation (Qualitative):** For critical semantic skills, you might include "golden" input/output pairs (stored perhaps as test assets) and assert that the LLM output for a given input is "reasonable" or contains expected elements. This can be hard to automate perfectly.
    *   **Prompt Validation:** Consider tools or scripts to validate the syntax of `skprompt.txt` and `config.json` if they become complex.

## 5. Interaction with Knowledge Graph (KG) & Ontology

*   **Direct KG Interaction:** Skills should generally **not** interact directly with the KG. This responsibility usually lies with agents (e.g., `KnowledgeGraphAgent`).
*   **Ontology Awareness:**
    *   Skills might process data that *originates* from or is *destined for* the KG.
    *   A skill transforming financial data might be aware that its output needs to be structured in a way that an agent can easily map to `cacm_ont:FinancialStatement` concepts, but the skill itself doesn't perform the RDF conversion.
    *   Skills that generate natural language text (e.g., a `ReportSummarySkill`) might be designed to produce text that accurately reflects relationships defined in the ontology, even if not directly querying it.

## 6. Versioning

*   **Native Skills:** Changes to Python code are versioned in Git. Significant changes to a function's signature, behavior, or the descriptions provided to Semantic Kernel should be clearly communicated.
*   **Semantic Skills:** Changes to `skprompt.txt` or `config.json` are versioned in Git. If these changes significantly alter the skill's behavior or its interface (input parameters, LLM settings), this should be treated as a new version of the skill conceptually.
*   Refer to the root `AGENTS.md` for general versioning guidelines.

## 7. Key Dependencies & Setup

*   **Core Dependency:** `semantic-kernel`.
*   **LLM Access:** For semantic skills, the environment must be configured with API keys and endpoints for the relevant LLM service (e.g., Azure OpenAI, OpenAI). These are typically set as environment variables that Semantic Kernel reads.

## 8. Important Notes & Gotchas

*   **Skill Descriptions are Key:** The `description` fields in `@sk_function` (for native) and `config.json` (for semantic) are critical for how Semantic Kernel's planner discovers and uses skills. Make them accurate and descriptive.
*   **Parameter Name Consistency:** Ensure parameter names used in `@sk_function_context_parameter`, `config.json` (input parameters), and `skprompt.txt` (e.g., `{{$my_param}}`) are consistent.
*   **Cost and Performance:** Be mindful of the cost and latency of LLM-based semantic skills. Use them judiciously. Native skills are generally much faster and cheaper for deterministic tasks.
*   **Plugin Registration:** Agents are responsible for importing skill plugins (e.g., `kernel.import_skill(MyNativeSkillClass(), plugin_name="MyPlugin")`) or loading semantic skills from directories (e.g., `kernel.import_semantic_skill_from_directory("adk/skills/", "MyPlugin")`).

## 9. Verification Checks for Agents (AI)

*Before submitting changes to this module, an AI agent (like Jules) MUST perform the following checks:*

1.  **Run all unit tests for the `adk/skills/` directory and ensure they pass.**
    *   Command: `pytest tests/skills/`
2.  **Run linters (e.g., Flake8, Black) on `adk/skills/` (for Python files) and address all reported issues.**
    *   Command: `flake8 adk/skills/ ; black adk/skills/`
3.  **For new or modified native skills:**
    *   Verify Google-style docstrings for the skill class and its methods.
    *   **Critically review the `description` in `@sk_function` and all `@sk_function_context_parameter` decorators for clarity, accuracy, and usefulness to a planner.**
4.  **For new or modified semantic skills:**
    *   **Critically review the `description` and input parameter descriptions in `config.json` for clarity, accuracy, and usefulness to a planner.**
    *   Ensure `skprompt.txt` is well-crafted and that placeholders match `config.json`.
    *   Manually test the prompt (e.g., using the SK Python REPL or a simple script) with sample inputs if significant changes were made.
5.  **Ensure no sensitive information is hardcoded in skill definitions (especially in prompts or default values).**
6.  **Update this `AGENTS.md` file if any of the above instructions (e.g., testing methods, conventions) have changed due to your work.**

---
*This `AGENTS.md` is a living document. If you find it to be inaccurate or incomplete, please update it.*
```
