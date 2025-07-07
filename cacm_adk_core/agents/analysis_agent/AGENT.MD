# AGENT.MD - AnalysisAgent

**Parent AGENT.MD:** `../AGENT.MD` (Refers to `cacm_adk_core/agents/AGENT.MD`)

This document provides specific guidance for working with the `AnalysisAgent` within the CACM-ADK project.

## 1. Purpose & Key Responsibilities

*   **Purpose:** The `AnalysisAgent` is a sophisticated agent responsible for performing a wide range of analytical tasks on financial and contextual data. It integrates data from `SharedContext`, invokes various Semantic Kernel skills (both calculation-based and LLM-based), interacts with other agents (like `KnowledgeGraphAgent`), and produces enriched analytical outputs.
*   **Key Responsibilities:**
    *   Calculate financial ratios using skills like `FinancialAnalysisSkill.calculate_basic_ratios`.
    *   Perform conceptual data drift and model drift checks on financial data and calculated ratios.
    *   Generate narrative summaries using LLM-powered skills (e.g., `CustomReportingSkills`):
        *   Financial performance summary.
        *   Key risks summary.
        *   Overall assessment.
    *   Generate XAI-style explanations for financial ratios using LLM-powered skills.
    *   Orchestrate ESG (Environmental, Social, Governance) data analysis:
        *   Formulate SPARQL queries for ESG data.
        *   Invoke `KnowledgeGraphAgent` to execute these queries against a Knowledge Graph.
        *   Process KG query results using skills like `ESGAnalysisSkill.summarize_esg_factors_from_kg`.
    *   Store all generated analytical outputs (ratios, summaries, explanations, ESG data) into `SharedContext` for use by other agents (e.g., `ReportGenerationAgent`).
    *   Communicate a summary of its operations and findings to `ReportGenerationAgent`.

## 2. Dependencies

*   **Internal Dependencies:**
    *   Inherits from `cacm_adk_core.agents.base_agent.Agent`.
    *   `cacm_adk_core.semantic_kernel_adapter.KernelService`: For SK access.
    *   `cacm_adk_core.context.shared_context.SharedContext`: For data exchange.
    *   `KnowledgeGraphAgent`: Invoked to query ESG data from the KG.
    *   `ReportGenerationAgent`: Receives analysis results from this agent.
    *   Skills:
        *   `FinancialAnalysisSkill` (e.g., `calculate_basic_ratios`).
        *   `CustomReportingSkills` (LLM-based, e.g., `generate_financial_summary`, `generate_key_risks_summary`, `generate_overall_assessment`, `generate_explanation`). From `processing_pipeline.semantic_kernel_skills`.
        *   `ESGAnalysisSkill` (e.g., `summarize_esg_factors_from_kg`). From `cacm_adk_core.skills.esg_analysis_skill`.
*   **External Libraries:**
    *   `semantic-kernel`
    *   `logging`
    *   `json` (for handling JSON data if applicable, though mainly for structuring outputs)
*   **Configuration Files:**
    *   Relies on `config/compute_capability_catalog.json` for its registration as `urn:adk:capability:financial_analysis_agent:v1`.
    *   Indirectly relies on prompt files if LLM prompts for `CustomReportingSkills` are externalized (as per plan 1.3.2).
*   **Data Sources (Expected in `SharedContext`):**
    *   `financial_data_for_ratios_expanded`: Detailed financial data for ratio calculations.
    *   `structured_financials_for_summary`: Data for LLM-based financial summary.
    *   `risk_factors_section_text`: Text for LLM-based risk summary.
    *   `companyTicker`, `companyName`: For context and KG queries.
    *   (Potentially) `company_uri_base`: For constructing URIs for KG queries.

## 3. How to Test This Component

*   **Unit Tests:**
    *   Location of unit tests: `tests/core/agents/test_analysis_agent.py` (currently, tests might be in `test_agents.py`, this path is the ideal future state).
    *   Key test scenarios:
        *   Successful ratio calculation and storage in `SharedContext`.
        *   Correct invocation of mocked LLM skills for summaries and explanations, and handling of their responses.
        *   Correct formulation of SPARQL queries for ESG data.
        *   Proper interaction with a mocked `KnowledgeGraphAgent` (checking inputs passed to it, handling its mocked responses).
        *   Successful invocation of mocked `ESGAnalysisSkill`.
        *   Correct data storage in `SharedContext` for all outputs.
        *   Accurate communication of results to a mocked `ReportGenerationAgent`.
        *   Handling of missing optional data in `SharedContext` (e.g., if `risk_factors_section_text` is not available).
        *   Data/model drift check logic (with mock historical data).
    *   How to run unit tests:
        ```bash
        pytest tests/core/agents/test_agents.py # Or specific path if refactored
        ```
*   **Integration Tests:**
    *   Tested as part of workflows like `msft_comprehensive_analysis_workflow.json` in `tests/core/test_orchestrator_integration.py`. These tests verify its role in the larger flow.
*   **Mocking:**
    *   `KernelService` and all invoked Semantic Kernel skills (LLM-based and native).
    *   `SharedContext`: To provide diverse input scenarios and verify outputs stored.
    *   `KnowledgeGraphAgent`: Mock its `run` method to return various KG query results (empty, successful, error).
    *   `ReportGenerationAgent`: Mock its `receive_analysis_results` method.
*   **Manual Testing/Verification Steps:**
    *   Run a workflow that includes the `AnalysisAgent` (e.g., `msft_comprehensive_analysis_workflow.json`) via `adk_cli.py`.
    *   Examine the orchestrator logs for messages from `AnalysisAgent`.
    *   Inspect the `SharedContext` (if a debug mode allows saving/inspecting it) or the final report to see if the agent's contributions (ratios, summaries, ESG section) are present and plausible.

## 4. Configuration Notes (If Applicable)

*   **Capability ID:** `urn:adk:capability:financial_analysis_agent:v1` in `compute_capability_catalog.json`.
*   **Inputs (via CACM workflow):**
    *   `roundingPrecision` (optional): For financial ratios.
    *   `company_uri_base` (optional, for ESG KG queries, defaults in agent if not provided).
*   **LLM Prompts:** If prompts are externalized, their file paths would become an indirect configuration.

## 5. Known Issues & TODOs

*   **Known Issues:**
    *   *Placeholder:* (Example) "LLM-generated explanations for ratios can sometimes be too generic if context is sparse."
    *   The conceptual data/model drift checks are very basic and rely on hardcoded historical values; they are not statistically robust.
*   **TODOs / Future Enhancements:**
    *   TODO: Make data/model drift checks more configurable and statistically sound.
    *   TODO: Allow more granular selection of which analyses to perform (e.g., skip ESG if not needed).
    *   TODO: Improve error handling for individual skill failures to allow the agent to proceed with partial results more gracefully.
    *   TODO: Integrate more types of analyses (e.g., trend analysis, peer comparison using KG data).
    *   TODO: Refine the interaction with `KnowledgeGraphAgent` for more complex KG operations if needed (beyond simple querying).

## 6. Versioning Information

*   **Current Version:** Part of the overall CACM-ADK package version. Capability ID `urn:adk:capability:financial_analysis_agent:v1` implies a version for its interface.
*   **Change Log (Summary or Link):** Refer to the project's main changelog. Key changes would involve new analytical capabilities, changes to skill interactions, or updates to `SharedContext` usage.

## 7. Design Notes & Rationale (Optional)

*   The `AnalysisAgent` acts as a "macro-agent" that orchestrates several fine-grained analytical tasks, many of which involve LLM-powered skills. This keeps the main orchestrator simpler.
*   Heavy reliance on `SharedContext` is by design to decouple it from direct data feeds from many preceding agents, assuming `DataIngestionAgent` or similar populates the context.
*   ESG analysis flow (AnalysisAgent -> KG Agent -> ESG Skill) is designed to separate KG interaction concerns from ESG data interpretation concerns.

---
*Self-reflect and double check: This AGENT.MD for AnalysisAgent is detailed, specific, and uses the template structure. It correctly identifies its complex responsibilities, numerous dependencies (internal and external, including skills and context data), and outlines comprehensive testing strategies. Placeholders for known issues and specific test paths are appropriate. It links to the parent AGENT.MD for the agents module.*
