# CACM-ADK Ontology Guide (v0.1)

This document provides a basic guide to the ontology used within the CACM-ADK project.
The primary ontology file is `ontology/credit_analysis_ontology_v0.1/credit_ontology.ttl`.

## Namespaces

The ontology utilizes several namespaces (prefixes):

*   **`cacm_ont:`**: `<http://example.com/ontology/cacm_credit_ontology/0.1#>` - Core concepts defined specifically for the CACM-ADK initial modeling.
*   **`kgclass:`**: `<http://example.org/kg/class/>` - For new classes largely based on recent user feedback, often more granular or from broader financial domains.
*   **`kgprop:`**: `<http://example.org/kg/property/>` - For new properties based on recent user feedback.
*   **`rdf:`**: `<http://www.w3.org/1999/02/22-rdf-syntax-ns#>`
*   **`rdfs:`**: `<http://www.w3.org/2000/01/rdf-schema#>`
*   **`owl:`**: `<http://www.w3.org/2002/07/owl#>`
*   **`xsd:`**: `<http://www.w3.org/2001/XMLSchema#>`

## Key Classes (Examples)

This is not an exhaustive list but highlights some important classes:

*   **`cacm_ont:FinancialStatement`**: Represents a formal record of financial activities.
    *   *Used in:* CACM input schemas.
*   **`cacm_ont:Metric`**: A quantifiable measure. Subclasses include `cacm_ont:Ratio`, `cacm_ont:RiskScore`.
*   **`kgclass:LeverageRatio`**: (Subclass of `cacm_ont:Ratio`) Specific type of ratio measuring debt.
    *   *Example:* Debt-to-Equity.
    *   *Used in:* Template outputs, Report Generator logic.
*   **`kgclass:ValuationMethod`**: A method to determine economic worth (e.g., `kgclass:IntrinsicValuationMethod`).
    *   *Used in:* Conceptually for defining CACMs related to valuation.
*   **`kgclass:RiskCategory`**: Classification for risk types (e.g., `kgclass:LiquidityRiskType`).
*   **`kgclass:Assumption`**: An underlying assumption for an analysis.
*   **`kgclass:Rationale`**: Justification for an analysis or rating.

## Key Properties (Examples)

*   **`cacm_ont:requiresInput`**: Specifies data input for a capability/metric.
*   **`kgprop:calculatedFrom`**: Indicates a metric is derived from specific inputs.
*   **`kgprop:hasAssumption`**: Links an analysis to an assumption.
*   **`kgprop:providesRationale`**: Connects an assessment to its rationale.

## Usage

These ontology terms are primarily used in:
*   **CACM Templates (`cacm_library/templates/`):** In `ontologyRef` fields to semantically define inputs, outputs, and parameters.
*   **Report Generator (`cacm_adk_core/report_generator/`):** To inform the structure and language of generated reports.
*   **CACM Schema (`cacm_standard/cacm_schema_v0.2.json`):** Referenced conceptually in descriptions for schema elements.
*   **Interactive Exploration**: The ontology can be interactively explored via the 'Ontology Explorer' section on the main web landing page (`index.html`) or programmatically through the `/ontology/*` API endpoints.

(This guide will be expanded as the ontology matures.)
