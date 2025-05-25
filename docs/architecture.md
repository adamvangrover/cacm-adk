# CACM-ADK System Architecture

## High-Level Overview

(This document will detail the architecture of the CACM-ADK system, including its components, their interactions, and how it fits into a larger enterprise ecosystem for credit analysis.)

Key components to be detailed:
-   User Interaction Layer (Agent/IDE/Web)
    -   ADK CLI Tool (`scripts/adk_cli.py`)
-   CACM-ADK Core Engine
    -   Orchestrator
        -   - Loads a compute capability catalog (e.g., `config/compute_capability_catalog.json`) to understand available logical compute functions.
        -   - Provides a `run_cacm` method that validates a CACM instance and then simulates its workflow execution by logging each step, its capability reference, and data bindings. Actual computation is currently mocked.
    -   Ontology Navigator & Expert
    -   Template Engine
    -   Workflow Assistant
    -   Metric & Factor Advisor
    -   Parameterization Helper
    -   Semantic & Structural Validator
        -   - Initial implementation provides schema validation for CACM instances against the defined JSON schema (e.g., `cacm_schema_v0.2.json`) using the `jsonschema` library.
    -   Modular Design Prompter
    -   Documentation Generator
-   External Dependencies & Services (LLM, Ontology Store, Template Repo, etc.)

## Data Flows
(Details on how data, CACM definitions, and control signals flow through the system.)

## Deployment Model
(Considerations for deploying the CACM-ADK, e.g., as a microservice.)

## Tooling

### ADK CLI Tool (`scripts/adk_cli.py`)

A command-line interface built with `click` provides direct access to core ADK functionalities:
- Listing and instantiating CACM templates.
- Validating CACM JSON instances against the schema.
- Simulating the run of a CACM workflow via the Orchestrator.
This serves as the primary means of interaction for developers and for testing ADK components.
