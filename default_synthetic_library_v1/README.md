# Default Synthetic Library v1

This directory contains a synthetically generated library of comprehensive analysis reports.
It serves as a baseline demonstration of the capabilities of the multi-agent financial analysis system
as of its current version.

## Contents

-   **`synthetic_reports.jsonl`**:
    *   A JSON Lines (JSONL) file where each line is a complete JSON object representing a "Full Report Object" for a single analyzed company.
    *   **Structure of each JSON object:**
        *   `company_id`: The primary identifier for the company (e.g., "MSFT").
        *   `company_name_processed`: Company name used during the workflow.
        *   `execution_timestamp_utc`: ISO 8601 timestamp of the generation.
        *   `workflow_id_used`: ID of the CACM workflow instance.
        *   `inputs_to_workflow`: Key inputs that drove the specific analysis run.
        *   `ingested_data_summary`: Output from the DataIngestionAgent.
        *   `text_inputs_provided`:
            *   `business_overview`: Text used for the company's business overview.
            *   `risk_factors`: Text used for the company's risk factors.
        *   `catalyst_parameters_used`: Inputs provided to the CatalystWrapperAgent.
        *   `fundamental_analysis_raw`: Structured JSON output from FundamentalAnalystAgent (includes status, financial ratios, DCF valuation, enterprise value, financial health assessment, and LLM-generated analysis summary).
        *   `snc_analysis_raw`: Structured JSON output from SNCAnalystAgent (includes status, SNC rating, and LLM-generated rationale).
        *   `catalyst_output_raw`: Structured JSON output from CatalystWrapperAgent (includes status and data from the original Catalyst agent).
        *   `generated_markdown_report`: The final human-readable comprehensive report in Markdown format.
    *   **Companies Included in v1:**
        *   `MSFT`: Uses detailed, MSFT-specific mock financial data.
        *   `TESTCORP`: Uses specific mock financial data for TESTCORP.
        *   `GENERIC_TECH_CO`: Uses generic placeholder financial data.
        *   `GENERIC_RETAIL_CO`: Uses generic placeholder financial data.

## Purpose

-   **Demonstration**: Showcases the end-to-end analytical capabilities of the integrated agent system.
-   **Baseline**: Provides a snapshot of the system's output quality based on current agent logic, prompts, and (mocked) data sources.
-   **Development & Testing**: Can be used as a reference for future development, testing changes, and ensuring consistency.
-   **Future Machine Learning**: The structured data within these report objects can potentially serve as a dataset for training or fine-tuning machine learning models related to financial analysis, report summarization, or agent behavior.

## Notes

-   This is a **synthetic** library. While "MSFT" and "TESTCORP" use more detailed mock data, the financial figures are still examples and not real-time or audited financial statements.
-   The "generic" company reports are illustrative of the system's processing pipeline but use highly simplified placeholder financial data.
-   The quality and depth of LLM-generated text (summaries, rationales) are dependent on the underlying models and prompts used at the time of generation.
