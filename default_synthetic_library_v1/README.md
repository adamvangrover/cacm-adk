# Default Synthetic Library v2 (with Diversified Mock Data)

This directory contains a synthetically generated library of comprehensive analysis reports.
It serves as a baseline demonstration of the capabilities of the multi-agent financial analysis system
as of its current version, featuring a broader range of companies.

## Contents

1.  **`synthetic_reports.jsonl`**:
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
    *   **Companies Included in v2 (14 total):**
        *   `MSFT`: Uses detailed, MSFT-specific mock financial and qualitative data.
        *   `AAPL`: Uses detailed, AAPL-specific mock financial and qualitative data.
        *   `JPM`: Uses detailed, JPM-specific mock financial and qualitative data.
        *   `TESTCORP`: Uses specific mock financial data but generic qualitative texts.
        *   **10 Additional S&P 500 Companies**: `GOOGL`, `AMZN`, `JNJ`, `PFE`, `TSLA`, `MCD`, `BA`, `CAT`, `V`, `XOM`. These use generic placeholder financial data provided by `DataRetrievalAgent` and generic qualitative texts. The specific detailed mock financial data for these 10 (beyond the generic placeholder) was not implemented in `DataRetrievalAgent` in this iteration.

2.  **`human_readable_reports/` (Directory):**
    *   This directory contains individual Markdown files for each company analyzed.
    *   Each file (e.g., `MSFT_analysis_report.md`, `AAPL_analysis_report.md`) is the extracted `generated_markdown_report` from the corresponding entry in `synthetic_reports.jsonl`.
    *   This provides an easy way to read individual reports.

## Purpose

-   **Demonstration**: Showcases the end-to-end analytical capabilities of the integrated agent system across a diverse set of companies.
-   **Baseline**: Provides a snapshot of the system's output quality based on current agent logic, prompts, and varying levels of mock data detail.
-   **Development & Testing**: Can be used as a reference for future development, testing changes, and ensuring consistency.
-   **Future Machine Learning**: The structured data within these report objects can potentially serve as a dataset for training or fine-tuning machine learning models.

## Notes

-   This is a **synthetic** library.
    *   For `MSFT`, `AAPL`, and `JPM`, the financial data and qualitative texts are detailed mocks created by an LLM to be plausible and thematically appropriate. They are **not real-time or audited financial statements.**
    *   For `TESTCORP`, financial data is a detailed mock, but qualitative texts are generic.
    *   For the other 10 S&P 500 companies (`GOOGL`, `AMZN`, etc.), both the financial data (provided by `DataRetrievalAgent`'s generic placeholder mechanism) and qualitative texts are generic and illustrative of the *process* rather than company specifics.
-   The quality and depth of LLM-generated text (summaries, rationales) are dependent on the underlying models and prompts used at the time of generation.
