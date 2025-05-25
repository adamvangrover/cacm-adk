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
    *   `sme_scoring_model_template.jsonc`: For simplified SME credit scoring.
    *   `data_aggregation_task_template.jsonc`: For aggregating data from multiple sources.
    *   `basic_ratio_analysis_template.jsonc`: (Updated) For basic financial ratio calculations.
    *   These templates now include `ontologyRef` fields linking to the defined ontology.
*   **Examples (`examples/`):**
    *   `sme_credit_score_example_01.json`
    *   `customer_data_aggregation_example_01.json`

## Repository Structure

-   `cacm_adk_core/`: Source code for the core engine components.
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
    *   `TEMPLATE_FILENAME`: The filename of the template from `cacm_library/templates` (e.g., `basic_ratio_analysis_template.jsonc`).
    *   `OUTPUT_FILEPATH.json`: Path where the instantiated CACM JSON file will be saved.
    *   Options:
        *   `--cacm-id TEXT`: Specific UUID for the new CACM.
        *   `--name TEXT`: Name for the new CACM (overrides template's default name).
        *   `--description TEXT`: Description for the new CACM.
    ```bash
    python scripts/adk_cli.py instantiate basic_ratio_analysis_template.jsonc examples/my_ratio_cacm.json --name "My Custom Ratio Analysis"
    ```
    *(Note: CLI instantiation may currently be affected by TemplateEngine parsing issues.)*

*   **`validate <CACM_FILEPATH.json>`**: Validates a CACM JSON file against the schema.
    ```bash
    python scripts/adk_cli.py validate examples/sme_credit_score_example_01.json
    ```

*   **`run <CACM_FILEPATH.json>`**: Simulates the execution of a CACM file's workflow.
    ```bash
    python scripts/adk_cli.py run examples/sme_credit_score_example_01.json
    ```

## API, Web UI, and Dockerization

The CACM-ADK can be run as a web service, providing a REST API for its functionalities and a simple web-based landing page. It is also containerizable using Docker for easy deployment.

*   **Landing Page:** The `index.html` landing page (accessible at `/` when the service is running) now serves as an interactive walkthrough of the CACM-ADK. It demonstrates a conceptual end-to-end scenario (e.g., DoorDash M&A analysis) by showcasing an example 'Blended Prompt', the conceptual structured JSON-LD output from CACM execution, and a synthesized human-readable report.
*   **REST API:** For detailed API usage, see the [API Usage Guide](./docs/api_usage.md).
*   **Deployment (Docker & Local):** For instructions on building/running the Docker container or running locally for development, see the [Deployment Guide](./docs/deployment.md).

## Features & Tools Overview (Highlights)
*   The internal credit ontology (`ontology/credit_analysis_ontology_v0.1/credit_ontology.ttl`) has been expanded with more granular terms.
*   The report generator (`cacm_adk_core/report_generator/report_generator.py`) now simulates multiple analytical 'personas' for richer rationale in generated reports.
*   All CACM templates in `cacm_library/templates/` now use the `.json` extension and expect pure JSON content.

### Jupyter Notebook for Interactive Prompting & Simulation
Located in `notebooks/Interactive_Credit_Report_Generator.ipynb`, this Jupyter Notebook provides a hands-on tool for:
*   Interactively inputting company data, financial metrics, and qualitative assessments.
*   Dynamically generating a detailed LLM prompt based on these inputs and a predefined report structure.
*   Locally simulating (without actual LLM calls) the generation of a Markdown-based credit report from the provided inputs.
This is useful for prompt engineering, understanding input-to-report mapping, and iterative development of report structures.

## Contributing
Please see `CONTRIBUTING.md`.
