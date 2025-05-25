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

## Contributing
Please see `CONTRIBUTING.md`.
