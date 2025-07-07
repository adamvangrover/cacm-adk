# AGENTS.md - [Directory/Module Name]

This document provides guidance for AI agents (like Jules) working with the code in the `[directory/module path]` directory and its subdirectories.

## 1. Overview & Purpose

*   **What is this directory/module about?** Briefly describe the main purpose of the code in this part of the project.
*   **Key functionalities:** List the 1-3 most important things this module does.

## 2. Coding Conventions

*   **General Style:** Adhere to PEP 8 for Python. If other languages are present, specify their style guides (e.g., Google Java Style Guide).
*   **Naming Conventions:**
    *   Classes: `PascalCase`
    *   Functions/Methods: `snake_case`
    *   Variables: `snake_case`
    *   Constants: `UPPER_SNAKE_CASE`
    *   Modules: `lowercase_snake_case.py`
    *   [Add any module-specific conventions]
*   **Docstrings:**
    *   Use Google-style docstrings for Python.
    *   Every public class, method, and function must have a docstring.
    *   Module-level docstrings are encouraged.
*   **Logging:**
    *   Use the standard Python `logging` module.
    *   Acquire loggers via `logging.getLogger(__name__)`.
    *   Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    *   Provide context in log messages.
*   **Error Handling:**
    *   Use specific exception types where possible.
    *   Handle exceptions gracefully; avoid broad `except Exception:`.
    *   Log errors with stack traces when appropriate.
*   **Configuration:**
    *   How is configuration managed for this module? (e.g., YAML files in `/config`, environment variables, passed from Orchestrator).
    *   Avoid hardcoding configuration values.
*   **[Add any other relevant conventions, e.g., for API design if this module exposes APIs]**

## 3. Testing Procedures

*   **Test Location:** Unit tests should be located in `tests/[path_corresponding_to_module]/`. For example, tests for `adk/agents/my_agent.py` should be in `tests/agents/test_my_agent.py`.
*   **Test Framework:** [Specify test framework, e.g., pytest, unittest].
*   **Running Tests:**
    *   Command to run all tests for this module: `[e.g., pytest tests/module_path/]`
    *   Command to run a specific test file: `[e.g., pytest tests/module_path/test_specific_file.py]`
*   **Test Coverage:** Aim for high test coverage. [Specify target if any, e.g., ">80%"].
*   **Mocking:** Use `unittest.mock` (or `pytest-mock`) for mocking dependencies.
*   **Integration Tests:** [If applicable, describe where integration tests are and how to run them].
*   **Semantic Kernel Skill Testing (if applicable):**
    *   Native function skills: Test as regular Python functions.
    *   Semantic (prompt-based) skills: Testing may involve evaluating prompt outputs for typical inputs. Store test cases (input/expected output snippets) if possible.
*   **Agent Testing (if applicable):**
    *   Focus on testing agent methods and their interactions with skills or other services.
    *   Mock external dependencies (other agents, KG, APIs).

## 4. Interaction with Knowledge Graph (KG) & Ontology

*   **Primary Ontology:** `ontology/credit_analysis_ontology_v0.3/credit_ontology_v0.3.ttl`
*   **Key Classes/Properties Used:** List any specific ontology classes or properties that are frequently created, queried, or updated by this module.
    *   `[e.g., kgclass:Obligor, kgprop:hasFinancialStatement, esg:CarbonEmission]`
*   **Querying the KG:**
    *   If this module queries the KG, mention common query patterns or important SPARQL query files.
    *   Agents should typically use methods of `KnowledgeGraphAgent` or similar KG interface, not raw SPARQL unless necessary for highly specialized queries.
*   **Populating the KG:**
    *   If this module populates the KG, describe the types of data it adds and the ontology terms used.
    *   Ensure data conforms to the ontology definitions (e.g., correct datatypes for literal values).
*   **Ontology Extensions:** If you identify a need to extend the ontology based on the work in this module, follow the guidelines in `docs/developer_guide/extending_the_ontology.md` and discuss with the team.

## 5. Versioning (Agents, Skills, Data)

*   **Code Versioning:** All code changes must be managed through Git (feature branches, PRs, reviews).
*   **Agent Versioning (Conceptual):** If an agent's API (methods, parameters) changes significantly, this might be considered a new "version" of the agent. Document such changes clearly in PRs and relevant documentation.
*   **Skill Versioning (Conceptual):**
    *   Native skills: Changes are tracked via Git. Significant changes to a skill's function signature or behavior should be clearly communicated.
    *   Semantic skills: Prompt changes are versioned in Git. If a prompt/config changes behavior significantly, treat it as a new version.
*   **Ontology Versioning:** The ontology itself is versioned (e.g., `credit_ontology_v0.3.ttl`). Changes follow the process in `docs/developer_guide/extending_the_ontology.md`.
*   **CACM Template/Instance Versioning:** [To be defined more broadly, but if this module handles CACM templates/instances, note any local conventions or considerations].

## 6. Key Dependencies & Setup

*   **External Libraries:** List any major external libraries used by this module that are not part of the standard Python library or core project dependencies.
    *   `[e.g., pandas, scikit-learn, specific API client libraries]`
*   **Services:** Does this module depend on external services? (e.g., a specific database, a third-party API).
    *   `[e.g., Requires access to CompanyFinancialsDB, AlphaVantage API key]`
*   **Setup:** Any specific setup steps required to develop or run this module (beyond standard `pip install -r requirements.txt`).
    *   `[e.g., Set environment variable XYZ_API_KEY, Ensure local Redis server is running]`

## 7. Important Notes & Gotchas

*   [Add any specific complexities, known issues, or important things an AI agent should be aware of when working with this module.]
*   [Example: "The `LegacyDataConverter` class has known limitations with date parsing for pre-2000 dates." ]
*   [Example: "Ensure that KG updates are idempotent if this module performs them repeatedly."]

## 8. Verification Checks for Agents

*Before submitting changes to this module, an AI agent (like Jules) MUST perform the following checks:*

1.  **Run all unit tests for this module and ensure they pass.**
    *   Command: `[e.g., pytest tests/module_path/]`
2.  **Run linters (e.g., Flake8, Black) and address all reported issues.**
    *   Command: `[e.g., flake8 adk/module_path/ ; black adk/module_path/]`
3.  **Verify that all new public functions, classes, and methods have clear docstrings adhering to the specified style.**
4.  **If KG interactions were modified, manually review a sample of generated/queried triples to ensure conformance with the ontology and expectations.**
5.  **Ensure no sensitive information (API keys, passwords) has been hardcoded.**
6.  **Update this `AGENTS.md` file if any of the above instructions (e.g., testing commands, key dependencies, conventions) have changed due to your work.**

---
*This `AGENTS.md` is a living document. If you find it to be inaccurate or incomplete, please update it (or suggest updates).*
```
