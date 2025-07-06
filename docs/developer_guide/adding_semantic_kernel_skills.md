# Adding Semantic Kernel Skills

Semantic Kernel (SK) skills are reusable components that encapsulate native functions or prompts for Large Language Models (LLMs). This guide explains how to add new SK skills to the project.

## Key Concepts

*   **Skill:** A collection of related functions (either native Python or LLM prompts).
*   **Native Function:** A Python method decorated to be exposed as a skill function.
*   **Semantic Function:** A function defined by a natural language prompt, typically stored in a `.txt` file alongside a `config.json` describing its parameters.

## Steps to Add a New Semantic Kernel Skill

1.  **Identify or Create a Skill Group:**
    *   Skills are typically organized into groups (e.g., `DataAnalysisSkill`, `KnowledgeGraphSkill`).
    *   Determine if your new function(s) fit into an existing skill group or if a new one is needed.
    *   Skill groups are usually represented as Python classes.

2.  **Create the Skill Directory (if new skill group):**
    *   If creating a new skill group, create a directory under `adk/skills/` (e.g., `adk/skills/my_new_skill/`).
    *   Inside this directory, you'll place the Python file for native functions or subdirectories for semantic functions.

3.  **Adding Native Functions:**
    *   In the skill's Python file (e.g., `adk/skills/my_new_skill/my_new_skill.py` or an existing skill file):
        *   Define your Python method.
        *   Decorate it with `@sk_function` from the Semantic Kernel library.
        *   Use `@sk_function_context_parameter` to define expected parameters from the SK context.
        *   Provide clear docstrings for the function and its parameters, as these are used by SK.

    ```python
    # Example: adk/skills/sample_skill/sample_skill.py
    from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter

    class SampleSkill:
        @sk_function(
            description="Adds two numbers.",
            name="add"
        )
        @sk_function_context_parameter(
            name="number1",
            description="First number to add."
        )
        @sk_function_context_parameter(
            name="number2",
            description="Second number to add."
        )
        def add_numbers(self, context: "SKContext") -> str:
            try:
                num1 = float(context["number1"])
                num2 = float(context["number2"])
                result = num1 + num2
                return str(result)
            except ValueError as e:
                return f"Error: Invalid input numbers. {e}"
            except Exception as e:
                return f"An unexpected error occurred: {e}"

    ```

4.  **Adding Semantic Functions (LLM Prompts):**
    *   Create a subdirectory within your skill group's directory (e.g., `adk/skills/my_new_skill/MySemanticFunctionName/`).
    *   Inside this subdirectory:
        *   Create `skprompt.txt`: This file contains the natural language prompt for the LLM.
        *   Create `config.json`: This file describes the semantic function, its input parameters, and LLM configuration (e.g., temperature, max tokens).

    **Example `config.json`:**
    ```json
    {
        "schema": 1,
        "type": "completion",
        "description": "Summarizes a given text.",
        "completion": {
            "max_tokens": 150,
            "temperature": 0.7,
            "top_p": 1.0,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0
        },
        "input": {
            "parameters": [
                {
                    "name": "input",
                    "description": "The text to summarize.",
                    "defaultValue": ""
                }
            ]
        }
    }
    ```

    **Example `skprompt.txt`:**
    ```
    Summarize the following text:

    {{$input}}

    Summary:
    ```

5.  **Registering the Skill with an Agent or Kernel:**
    *   Agents that need to use the skill must import it and register it with their Semantic Kernel instance.
    *   This typically happens in the agent's initialization.

    ```python
    # Example: In an agent's __init__ or a dedicated setup method
    # from adk.skills.sample_skill.sample_skill import SampleSkill # For native
    # self.kernel.import_skill(SampleSkill(), skill_name="SampleSkill")

    # For semantic skills:
    # skills_directory = "adk/skills"
    # self.kernel.import_semantic_skill_from_directory(skills_directory, "my_new_skill")
    ```

6.  **Write Unit Tests:**
    *   Create unit tests for new native functions in `tests/skills/` (e.g., `test_my_new_skill.py`).
    *   For semantic functions, testing might involve evaluating prompt effectiveness or consistency of outputs, which can be more complex. Start with basic invocation tests.

7.  **Update Documentation:**
    *   Document the new skill, its functions, parameters, and usage in relevant project documentation (e.g., this guide, or specific agent documentation).

## Best Practices

*   **Clear Descriptions:** Use descriptive names and comprehensive descriptions for skills and functions, as these are used by SK and can be exposed to LLMs.
*   **Parameter Handling:** Clearly define input parameters and handle them robustly in your native functions.
*   **Error Handling:** Implement proper error handling within native functions.
*   **Prompt Engineering (for Semantic Functions):** Iteratively refine prompts to achieve desired LLM behavior. Consider prompt templating for more complex scenarios.
*   **Configuration Management:** For semantic functions, manage `config.json` carefully, especially LLM parameters.
```
