# AGENTS.md - Root Level

This document provides general guidance for AI agents (like Jules) working with the CACM-ADK (Credit Analysis Capability Module - Agent Development Kit) repository.

## 1. Overview & Purpose

*   **What is this repository about?** This repository contains the codebase for an AI-powered platform for credit analysis. It includes agents, Semantic Kernel skills, knowledge graph components, ontology definitions, and supporting infrastructure to build, deploy, and manage Credit Analysis Capability Modules (CACMs).
*   **Key Project Goals:**
    1.  Develop modular and reusable AI components for credit analysis.
    2.  Leverage a knowledge graph and ontology for semantic data integration and reasoning.
    3.  Enable flexible composition of agents and skills into CACMs.
    4.  Facilitate advanced analytics, including ESG and alternative data integration.

## 2. General Coding Conventions

*   **Primary Language:** Python 3.x
*   **General Style:** Adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/) for all Python code.
*   **Naming Conventions:**
    *   Classes: `PascalCase`
    *   Functions/Methods: `snake_case`
    *   Variables: `snake_case`
    *   Constants: `UPPER_SNAKE_CASE`
    *   Modules: `lowercase_snake_case.py`
    *   Packages/Directories: `lowercase_snake_case`
*   **Docstrings:**
    *   Use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for all Python code.
    *   Every public class, method, and function must have a comprehensive docstring.
    *   Module-level docstrings explaining the purpose of the module are required.
*   **Logging:**
    *   Use the standard Python `logging` module.
    *   Acquire loggers via `logging.getLogger(__name__)`.
    *   Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    *   Provide contextual information in log messages. Avoid logging sensitive data.
*   **Error Handling:**
    *   Use specific exception types. Define custom exceptions in `adk/exceptions.py` (or similar) if appropriate.
    *   Handle exceptions gracefully. Avoid broad `except Exception: pass`.
    *   Log errors with stack traces when they are caught and handled at a high level.
*   **Configuration:**
    *   Configuration is primarily managed via YAML files in the `config/` directory and/or environment variables.
    *   The `Orchestrator` and individual agents are typically configured this way.
    *   Avoid hardcoding configuration values (e.g., API endpoints, file paths that might change).
*   **Type Hinting:**
    *   Use type hints for all function signatures (parameters and return types) and for variable declarations where ambiguity might arise.
    *   This improves code readability and allows for static analysis.

## 3. Project Structure Highlights

*   **`adk/`**: Core Agent Development Kit components.
    *   `adk/agents/`: Base agent classes and specific agent implementations (e.g., `KnowledgeGraphAgent`, `DataRetrievalAgent`).
    *   `adk/skills/`: Semantic Kernel skill plugins (both native Python and prompt-based).
    *   `adk/orchestrator/`: Code for the agent orchestrator.
*   **`cacm_library/`**: Library of Credit Analysis Capability Modules (CACMs).
    *   `cacm_library/templates/`: JSON or YAML templates defining CACM workflows.
*   **`config/`**: Configuration files for agents, services, and the application.
*   **`data/`**: Sample data, temporary data, or small datasets. (Large datasets should be external).
*   **`docs/`**: Project documentation, including developer guides, ontology guides, and this `AGENTS.md` system.
    *   `docs/developer_guide/`: Detailed guides for developers.
    *   `docs/ontology_guide.md`: Information about the project's ontology.
*   **`knowledge_graph_instantiations/`**: Instance data for the knowledge graph (e.g., TTL files).
*   **`ontology/`**: Ontology definitions (e.g., `credit_ontology_v0.3.ttl`).
*   **`tests/`**: Unit and integration tests. Structure mirrors the main codebase.
*   **`api/`**: If the project exposes a web API, relevant code (e.g., FastAPI app) would be here.

## 4. Testing Procedures

*   **Test Location:** Unit tests are located in the `tests/` directory, mirroring the project structure.
*   **Test Framework:** [pytest](https://docs.pytest.org/) is the primary test framework.
*   **Running Tests:**
    *   Run all tests: `pytest` (from the repository root).
    *   Run tests for a specific directory: `pytest tests/agents/`
    *   Run tests for a specific file: `pytest tests/agents/test_my_agent.py`
    *   Run a specific test function: `pytest tests/agents/test_my_agent.py::test_specific_functionality`
*   **Test Coverage:** Aim for high test coverage (e.g., >80%). Use `pytest-cov` to generate coverage reports: `pytest --cov=adk --cov-report=html`.
*   **Mocking:** Use `unittest.mock` (via `pytest-mock` plugin) for mocking dependencies.
*   **Fixtures:** Utilize pytest fixtures for setting up test preconditions.
*   **`AGENTS.md` in Subdirectories:** More specific testing procedures for modules (e.g., specific agents or skills) may be found in `AGENTS.md` files within those module directories.

## 5. Interaction with Knowledge Graph (KG) & Ontology

*   **Primary Ontology:** `ontology/credit_analysis_ontology_v0.3/credit_ontology_v0.3.ttl`. Refer to `docs/ontology_guide.md` for details.
*   **KG Interaction Agent:** The `KnowledgeGraphAgent` (or a similar designated agent/service) is the primary interface for interacting with the KG (e.g., running SPARQL queries, loading triples).
*   **Ontology Conformance:** All data added to the KG must conform to the defined ontology. This includes using correct class types, properties, and data types for literals.
*   **Ontology Extensions:** If new concepts or properties are needed:
    1.  Review `docs/developer_guide/extending_the_ontology.md`.
    2.  Propose changes to the team.
    3.  Update the `.ttl` file and relevant documentation upon approval.

## 6. Versioning

*   **Code Versioning:** All code changes are managed through Git.
    *   Work on feature branches (`feature/your-feature-name` or `bugfix/issue-number`).
    *   Submit changes via Pull Requests (PRs) to the main development branch (e.g., `develop` or `main`).
    *   PRs should be reviewed before merging.
    *   Commit messages should follow [Conventional Commits](https://www.conventionalcommits.org/) if adopted by the project, or at least have a clear subject line and optional body.
*   **Ontology Versioning:** The ontology file itself is versioned (e.g., `credit_ontology_v0.3.ttl`). Major changes that are not backward-compatible should result in a new version number.
*   **CACM Versioning:** Individual CACM templates and instances should have a versioning strategy. This might involve version numbers in their filenames or internal metadata. (Strategy to be fully defined).
*   **Agent/Skill Versioning (Conceptual):** Significant changes to an agent's public API or a skill's core functionality/signature should be treated as a new version and clearly documented in PRs and relevant guides.

## 7. AGENTS.md System

*   This root `AGENTS.md` provides global guidance.
*   More specific `AGENTS.md` files may exist in subdirectories (e.g., `adk/agents/AGENTS.md`, `adk/skills/AGENTS.md`).
*   These more specific files take precedence for instructions related to their scope.
*   A template for creating new `AGENTS.md` files can be found at `docs/AGENTS_TEMPLATE.md`.
*   **You, the AI Agent, are expected to read and follow instructions in any applicable `AGENTS.md` file for the code you are modifying.**

## 8. General Verification Checks for Agents (Global)

*Before submitting any changes, an AI agent (like Jules) MUST perform these general checks, in addition to any module-specific checks:*

1.  **Run all project tests and ensure they pass:** `pytest`
2.  **Run linters (e.g., Flake8, Black) and address all reported issues across modified files.**
    *   Example commands: `flake8 .`, `black .` (or on specific files/directories you changed).
3.  **Verify that all new public functions, classes, and methods have clear, Google-style docstrings.**
4.  **Ensure no sensitive information (API keys, passwords, personally identifiable information) has been hardcoded or committed.** Use configuration files or environment variables instead.
5.  **Update any relevant documentation (`.md` files in `docs/`, including other `AGENTS.md` files) if your changes impact instructions, architecture, or usage.** This is crucial.
6.  **Write clear and descriptive commit messages.** If multiple commits, ensure the PR message summarizes the changes effectively.

---
*This `AGENTS.md` is a living document. If you find it to be inaccurate or incomplete, please update it (or suggest updates as part of your work).*
```
