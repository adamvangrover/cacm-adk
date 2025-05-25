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
    *   Initial implementation allows listing available `.jsonc` templates from a directory.
    *   Loads template content (with basic comment stripping for JSONC).
    *   Instantiates templates with new UUIDs, creation timestamps, and custom overrides.
*   **Semantic & Structural Validator (`validator.py`):**
    *   Initial implementation provides schema validation for CACM instances against the defined JSON schema (e.g., `cacm_schema_v0.2.json`) using the `jsonschema` library.
*   **Report Generator (`report_generator.py`):**
    *   The `ReportGenerator` component is responsible for taking the (simulated) outputs of a CACM execution from the Orchestrator and formatting them into a detailed, structured JSON report.
    *   This report includes elements like mapped credit ratings (S&P, SNC scales), outlook, (mocked) XAI/rationale, and key supporting metrics.
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
    *   Provides semantic definitions for terms and concepts in credit analysis.
*   **Compute Capability Catalog (`config/compute_capability_catalog.json`):**
    *   A simple JSON file listing logical compute capabilities referenced in CACM workflows.
*   **CACM Templates (`cacm_library/templates/`):**
    *   A library of predefined, reusable CACM structures.

### 4. External Dependencies & Services
*   (Placeholder for future integration, e.g., LLMs, dedicated Ontology Store, external Compute Services, etc.)

## Data Flows
(Details on how data, CACM definitions, and control signals flow through the system, particularly between the API, Orchestrator, and other core components.)

## Deployment Model

### Containerization (Docker)
*   The entire CACM-ADK application (including the FastAPI server and all components) can be built into a Docker container using the provided `Dockerfile`.
*   This ensures portability and simplifies deployment across different environments. See `docs/deployment.md` for details.

### Local Development
*   The application can also be run directly using Uvicorn for development purposes. See `docs/deployment.md`.
