# CACM Authoring & Development Kit (CACM-ADK)

## Overview

The CACM-ADK is an intelligent development environment and toolset designed to assist users (credit analysts, domain experts, developers) in authoring standardized Credit Analysis Capability Modules (CACMs).

A CACM is a declarative, machine-readable blueprint (ideally JSON-LD or YAML) that defines a specific credit analysis capability. It specifies:
- *What* analysis is performed.
- *What* data is needed.
- *How* it can adapt (configurable parameters).
- *What* results are produced.
- *How* quality is ensured (validation rules).
- It references *logical* compute capabilities rather than specific code implementations.

This project aims to build the core infrastructure and software for the CACM-ADK, enabling modular, intelligent, and governed development of credit analysis capabilities. The system is designed to be portable, modular, lightweight, and deeply expert, potentially packaged as a microservice or REST API.
It now incorporates an agent-based architecture and leverages Semantic Kernel for enhanced modularity in defining and executing computational and AI-driven tasks.

## Project Goals

-   Develop a core engine for CACM authoring, including components for ontology navigation, template management, workflow assistance, metric/factor advice, parameterization help, validation, modular design prompting, and documentation generation.
-   Define a clear standard for CACM definitions.
-   Develop a comprehensive credit analysis ontology.
-   Build a library of CACM templates.
-   Create an authoring and development kit (ADK) to guide the building process, train users, and improve over time.
-   Ensure the system is scalable, future-proof, and can integrate with external services like LLMs, schema validators, and compute catalogs.

### Key Components & Recent Additions

*   **Ontology (`ontology/credit_analysis_ontology_v0.1/credit_ontology.ttl`):**
    *   Core concepts recently added include: `FinancialInstrument`, `FinancialStatement`, `Metric`, `Ratio`, `RiskScore`, `EligibilityRule`, `DataInput`, `Policy`.
    *   Core relationships include: `hasDataSource`, `calculatesMetric`, `appliesRule`, `requiresInput`, `producesOutput`.
*   **CACM Templates (`cacm_library/templates/`):**
    *   `sme_scoring_model_template.json`: For simplified SME credit scoring.
    *   `data_aggregation_task_template.json`: For aggregating data from multiple sources.
    *   `basic_ratio_analysis_template.json`: (Updated) For basic financial ratio calculations.
    *   These templates now include `ontologyRef` fields linking to the defined ontology.
*   **Examples (`examples/`):**
    *   `sme_credit_score_example_01.json`
    *   `customer_data_aggregation_example_01.json`
*   **Agent-Based Architecture & Semantic Kernel:**
    *   **Core Agents:** The system now uses specialized agents like `DataIngestionAgent` (handles data intake), `AnalysisAgent` (performs analytical tasks, including invoking skills), and `ReportGenerationAgent` (compiles findings into reports).
    *   **Semantic Kernel Integration:** Manages and executes `Semantic Skills`. These can be native Python functions (see `cacm_adk_core/native_skills.py`) wrapped for kernel use, or potentially LLM-driven functions (conceptualized in `processing_pipeline/semantic_kernel_skills.py`). The `KernelService` (`cacm_adk_core/semantic_kernel_adapter.py`) centralizes kernel access.
    *   **SharedContext:** A `SharedContext` object (`cacm_adk_core/context/shared_context.py`) facilitates data sharing and session state management between agents and during a workflow execution.
    *   **Orchestrator Evolution:** The `Orchestrator` (`cacm_adk_core/orchestrator/orchestrator.py`) now functions as an agent workflow manager, dispatching tasks to agents or skills based on CACM definitions and managing the overall execution flow, including agent communication.
    *   **Compute Capability Catalog:** The catalog (`config/compute_capability_catalog.json`) has been updated to map capabilities to specific agents (via `agent_type`) or Semantic Kernel skills (via `skill_plugin_name` and `skill_function_name`), guiding the Orchestrator.

## Repository Structure

-   `cacm_adk_core/`: Source code for the core engine components.
    -   `agents/`: Contains the base agent class and specific agent implementations.
    -   `context/`: Holds the `SharedContext` class for data sharing.
    -   `orchestrator/`: The main workflow orchestrator and agent manager.
    -   `semantic_kernel_adapter.py`: Manages Semantic Kernel instance.
    -   `native_skills.py`: Wrappers for Python functions as native Semantic Kernel skills.
    -   `compute_capabilities/`: (Legacy direct Python functions, being replaced by skills/agents)
    -   `validator/`, `template_engine/`, `ontology_navigator/`, `report_generator/`
-   `cacm_library/`: Definitions of CACMs and reusable templates.
-   `cacm_standard/`: The CACM definition standard/schema.
-   `ontology/`: The credit analysis semantic ontology.
-   `docs/`: Project documentation.
-   `tests/`: Automated tests.
-   `examples/`: Example CACMs and usage scenarios.
-   `config/`: Configuration files.
-   `scripts/`: Utility and automation scripts.
-   `interfaces/`: API definitions and schemas.

## Getting Started

### Prerequisites
- Python 3.8+ (recommended)

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd cacm-adk
    ```

2.  **Create and activate a virtual environment:**
    (Recommended to avoid conflicts with global Python packages)
    ```bash
    python -m venv .venv
    # On Windows
    # .venv\Scripts\activate
    # On macOS/Linux
    # source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running Components (Examples)
(Details to be added as components become more runnable)

To run the example usage within `cacm_adk_core/validator/validator.py` (assuming you are in the project root):
```bash
python cacm_adk_core/validator/validator.py
```
To run the example usage within `cacm_adk_core/template_engine/template_engine.py`:
```bash
python cacm_adk_core/template_engine/template_engine.py
```

## ADK Command Line Interface (CLI)

The ADK provides a Command Line Interface (`adk_cli.py`) for interacting with its components.
Ensure you have installed dependencies (`pip install -r requirements.txt`) and activated your virtual environment.
Run commands from the project root directory.

**General Usage:**
```bash
python scripts/adk_cli.py [COMMAND] [OPTIONS] [ARGS]...
```

**Available Commands:**

*   **`list-templates`**: Lists available CACM templates.
    ```bash
    python scripts/adk_cli.py list-templates
    ```

*   **`instantiate <TEMPLATE_FILENAME> <OUTPUT_FILEPATH.json>`**: Instantiates a template.
    *   `TEMPLATE_FILENAME`: The filename of the template from `cacm_library/templates` (e.g., `basic_ratio_analysis_template.json`).
    *   `OUTPUT_FILEPATH.json`: Path where the instantiated CACM JSON file will be saved.
    *   Options:
        *   `--cacm-id TEXT`: Specific UUID for the new CACM.
        *   `--name TEXT`: Name for the new CACM (overrides template's default name).
        *   `--description TEXT`: Description for the new CACM.
    ```bash
    python scripts/adk_cli.py instantiate basic_ratio_analysis_template.json examples/my_ratio_cacm.json --name "My Custom Ratio Analysis"
    ```
    *(Note: CLI instantiation should now work reliably with pure JSON templates.)*

*   **`validate <CACM_FILEPATH.json>`**: Validates a CACM JSON file against the schema.
    ```bash
    python scripts/adk_cli.py validate examples/sme_credit_score_example_01.json
    ```

*   **`run <CACM_FILEPATH.json>`**: Simulates the execution of a CACM file's workflow.
    ```bash
    python scripts/adk_cli.py run examples/sme_credit_score_example_01.json
    ```

## ADK Control Chatbot

A new experimental chatbot interface has been added to allow for controlling ADK sub-systems (e.g., Python or Java agents) via a C control program. This provides a user-friendly web interface to send commands and view responses.

**Features:**

*   Simple web-based chat interface (`chatbot/index.html`).
*   Backend API (`api/backend_app.py`) using Flask to process commands.
*   Interfaces with a C control program (`adk_controller`) which is responsible for the actual communication with Python/Java ADK sub-systems.

**Running the Chatbot:**

1.  **Ensure the C Control Program is available:**
    *   The backend expects a compiled C program named `adk_controller` (or `adk_controller.exe` on Windows) to be present in the `api/` directory or accessible via the system's PATH.
    *   This C program is responsible for translating commands from the chatbot into actions for the respective ADK sub-systems (Python/Java). Its development is separate from this ADK project.
    *   A placeholder script `api/adk_controller` is provided for basic testing of the backend.

2.  **Start the Flask backend server:**
    *   Navigate to the project root directory.
    *   Ensure you have installed dependencies (`pip install -r requirements.txt`) and activated your virtual environment.
    *   Run the backend application:
        ```bash
        python api/backend_app.py
        ```
    *   The server will start, typically on `http://0.0.0.0:5001/`. The API endpoint will be `http://localhost:5001/api/chatbot`.

3.  **Access the Chatbot UI:**
    *   Open the `chatbot/index.html` file directly in your web browser (e.g., by navigating to `file:///path/to/your/project/chatbot/index.html` where `/path/to/your/project/` is the actual path to the cloned repository).
    *   The JavaScript within `chatbot.js` is configured to send requests to the Flask server running at `http://localhost:5001`.

**Using the Chatbot:**

*   Type commands into the input field. Example commands depend on what your `adk_controller` C program supports, e.g.:
    *   `python_test_command`
    *   `java_test_command details --id=123`
    *   `system_status --target python`
    *   `error_test` (to test error handling with the placeholder)
    *   `no_output_test` (to test commands with no output with the placeholder)

## API, Web UI, and Dockerization

The CACM-ADK can be run as a web service, providing a REST API for its functionalities and a simple web-based landing page. It is also containerizable using Docker for easy deployment.

*   **Landing Page:** The `index.html` landing page (accessible at `/` when the service is running) now serves as an interactive walkthrough of the CACM-ADK. It demonstrates a conceptual end-to-end scenario (e.g., DoorDash M&A analysis) by showcasing an example 'Blended Prompt', the conceptual structured JSON-LD output from CACM execution, a synthesized human-readable report, and an 'Ontology Explorer' section for browsing ontology terms live via API calls.
*   **REST API:** For detailed API usage, see the [API Usage Guide](./docs/api_usage.md).
*   **Deployment (Docker & Local):** For instructions on building/running the Docker container or running locally for development, see the [Deployment Guide](./docs/deployment.md).

## Features & Tools Overview (Highlights)
*   **Orchestrator Execution:** The Orchestrator is now capable of executing actual Python functions for some compute capabilities defined in a CACM workflow (e.g., basic ratio calculations), alongside its existing output mocking for other capabilities. This allows for a mix of real and simulated processing.
*   **Ontology Navigator & API:** The internal credit ontology (`ontology/credit_analysis_ontology_v0.1/credit_ontology.ttl`) has been expanded with more granular terms and is now explorable via new API endpoints (`/ontology/*`).
*   **Enhanced Report Generator:** The report generator (`cacm_adk_core/report_generator/report_generator.py`) now simulates multiple analytical 'personas' for richer rationale in generated reports.
*   **Pure JSON Templates:** All CACM templates in `cacm_library/templates/` now use the `.json` extension and expect pure JSON content.

### Jupyter Notebook for Interactive Prompting & Simulation
Located in `notebooks/Interactive_Credit_Report_Generator.ipynb`, this Jupyter Notebook provides a hands-on tool for:
*   Interactively inputting company data, financial metrics, and qualitative assessments.
*   Dynamically generating a detailed LLM prompt based on these inputs and a predefined report structure.
*   Locally simulating (without actual LLM calls) the generation of a Markdown-based credit report from the provided inputs.
This is useful for prompt engineering, understanding input-to-report mapping, and iterative development of report structures.

## Contributing
Please see `CONTRIBUTING.md`.
