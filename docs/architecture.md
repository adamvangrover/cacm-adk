# CACM-ADK System Architecture

## High-Level Overview

(This document will detail the architecture of the CACM-ADK system, including its components, their interactions, and how it fits into a larger enterprise ecosystem for credit analysis.)

## Key Architectural Layers & Components

### 1. User Interface / Entry Point
*   **REST API Layer (FastAPI):**
    *   The system exposes its functionalities via a RESTful API built using FastAPI (`api/main.py`).
    *   This API allows for programmatic interaction with the Template Engine, Validator, Orchestrator, and Report Generator.
    *   Endpoints cover template management (listing, instantiating), CACM validation, simulated workflow execution, and generation of detailed credit assessment reports.
    *   Interactive API documentation is available via Swagger UI (`/docs`) and ReDoc (`/redoc`) when the server is running.
*   **Web UI (Landing Page):**
    *   A simple HTML landing page (`static/index.html`) is served at the root (`/`) when running as a web service. It provides an overview and links to documentation and API demos.
*   **Command Line Interface (CLI):**
    *   The ADK CLI Tool (`scripts/adk_cli.py`) built with `click` provides direct access to core ADK functionalities.
    *   This serves as a primary means of interaction for developers, for scripting batch operations, and for testing ADK components.

### 2. CACM-ADK Core Engine (`cacm_adk_core/`)
This engine houses the primary logic for CACM authoring and processing.
*   **Orchestrator (`orchestrator.py`):**
    *   Loads a compute capability catalog (e.g., `config/compute_capability_catalog.json`) to understand available logical compute functions.
    *   Provides a `run_cacm` method that validates a CACM instance and then simulates its workflow execution. This includes logging each step, its capability reference, data bindings, and generating mocked-up outputs for the defined CACM outputs. Actual computation is currently simulated.
*   **Template Engine (`template_engine.py`):**
    *   Allows listing available `.json` templates from a directory.
    *   Loads template content (pure JSON, no comment stripping needed).
    *   Instantiates templates with new UUIDs, creation timestamps, and custom overrides.
*   **Semantic & Structural Validator (`validator.py`):**
    *   Initial implementation provides schema validation for CACM instances against the defined JSON schema (e.g., `cacm_schema_v0.2.json`) using the `jsonschema` library.
*   **Report Generator (`report_generator.py`):**
    *   The `ReportGenerator` now incorporates a 'multi-persona' simulation approach. Internal methods generate text snippets from fundamental, regulatory (SNC), market, and strategic perspectives. These are synthesized to create a more detailed and nuanced `detailedRationale` and `keyRiskFactors_XAI` in the final JSON report. It also includes improved mapping for S&P and SNC rating equivalents.
*   **(Future Components):**
    *   Ontology Navigator & Expert
    *   Workflow Assistant
    *   Metric & Factor Advisor
    *   Parameterization Helper
    *   Modular Design Prompter
    *   Documentation Generator (for CACM instances)

### 3. Data & Standards Layer
*   **CACM Standard (`cacm_standard/cacm_schema_v0.2.json`):**
    *   Defines the JSON schema for CACM definitions.
*   **Ontology (`ontology/credit_analysis_ontology_v0.1/credit_ontology.ttl`):**
    *   Provides semantic definitions for terms and concepts in credit analysis. The `credit_ontology.ttl` has been significantly expanded with new classes and properties (using `cacm_ont:`, `kgclass:`, `kgprop:` namespaces) from user feedback, focusing on more granular financial, risk, valuation, and regulatory concepts. These richer semantics are used in CACM templates and can inform report generation.
*   **Compute Capability Catalog (`config/compute_capability_catalog.json`):**
    *   A simple JSON file listing logical compute capabilities referenced in CACM workflows.
*   **CACM Templates (`cacm_library/templates/`):**
    *   A library of predefined, reusable CACM structures (now pure `.json` files).

### 4. External Dependencies & Services
*   (Placeholder for future integration, e.g., LLMs, dedicated Ontology Store, external Compute Services, etc.)

### 5. Developer/Analyst Tools
#### Jupyter Notebook: Interactive Report Crafter
The `notebooks/Interactive_Credit_Report_Generator.ipynb` provides a standalone environment for analysts to:
*   Define inputs for a credit report using interactive widgets.
*   Automatically generate a comprehensive prompt suitable for an advanced LLM, based on these inputs and a structured report template.
*   Simulate the generation of a Markdown report locally, allowing for rapid iteration on report content and structure based on varying inputs.
This tool aids in prompt engineering and understanding the linkage between input data and report output.

## Data Flows
(Details on how data, CACM definitions, and control signals flow through the system, particularly between the API, Orchestrator, and other core components.)

## Deployment Model

### Containerization (Docker)
*   The entire CACM-ADK application (including the FastAPI server and all components) can be built into a Docker container using the provided `Dockerfile`.
*   This ensures portability and simplifies deployment across different environments. See `docs/deployment.md` for details.

### Local Development
*   The application can also be run directly using Uvicorn for development purposes. See `docs/deployment.md`.
