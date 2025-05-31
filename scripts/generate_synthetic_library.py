import asyncio
import json
import os
import sys
import datetime
import pandas as pd # For timestamp, consistent with notebook

# --- Path Setup ---
# Add project root to sys.path to allow imports from cacm_adk_core
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cacm_adk_core.orchestrator.orchestrator import Orchestrator
from cacm_adk_core.semantic_kernel_adapter import KernelService
# Import other necessary components if direct interaction is needed, though orchestrator handles agents.

# --- Configuration ---
TARGET_COMPANIES = [
    "MSFT", "TESTCORP", 
    "AAPL", "GOOGL", "AMZN", "JNJ", "PFE", 
    "TSLA", "MCD", "BA", "CAT", "JPM", "V", "XOM"
]
OUTPUT_FILE_PATH = os.path.join(PROJECT_ROOT, "default_synthetic_library_v1", "synthetic_reports.jsonl")
OUTPUT_DIR = os.path.dirname(OUTPUT_FILE_PATH)

# --- Text Snippets (can be expanded or loaded from files if larger) ---
MSFT_BUSINESS_OVERVIEW = "Microsoft Corporation is a global technology leader that enables digital transformation for the era of an intelligent cloud and an intelligent edge. Its mission is to empower every person and every organization on the planet to achieve more. The company develops, licenses, and supports a wide range of software products, services, devices, and solutions. Key segments include Productivity and Business Processes (Office, LinkedIn, Dynamics), Intelligent Cloud (Azure, Server Products), and More Personal Computing (Windows, Devices, Gaming, Search). Microsoft's strategy focuses on innovation and growth in high-priority areas such as cloud computing, artificial intelligence, gaming, and business applications, while maintaining its strong position in traditional software markets."
MSFT_RISK_FACTORS = "Microsoft faces a variety of significant risks. Intense competition across all its markets, including from established and emerging technology companies, could adversely affect its business. Cybersecurity threats, data breaches, and disruptions to its cloud services (Azure) represent major operational risks. Evolving global regulations, particularly in areas of data privacy (like GDPR), antitrust, and AI ethics, could impose substantial compliance costs and impact business models. Changes in macroeconomic conditions, such as recessions, inflation, or fluctuating foreign currency exchange rates, may reduce IT spending and demand for Microsoft's products. The company's ability to innovate and adapt to rapidly changing technologies, such as the ongoing developments in AI, is critical to its continued success. Dependence on key personnel and the ability to attract and retain talent are also important risk factors."

AAPL_BUSINESS_OVERVIEW = "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. It also sells a variety of related services. The company's products include iPhone, Mac, iPad, AirPods, Apple TV, Apple Watch, Beats products, HomePod, and iPod touch. It offers services such as AppleCare, iCloud, Apple Arcade, Apple Music, Apple News+, Apple TV+, and Apple Pay. Apple is known for its strong brand, innovative products, and integrated ecosystem of hardware, software, and services, targeting consumer, enterprise, and creative professional markets."
AAPL_RISK_FACTORS = "Apple faces intense competition in all its markets. Its business is subject to rapid technological change and reliant on the timely introduction of new products and services. Supply chain disruptions, geopolitical risks (especially concerning manufacturing concentration), and dependence on third-party component suppliers pose significant risks. Regulatory scrutiny regarding app store policies, antitrust concerns, and data privacy is increasing globally. Economic downturns can impact consumer discretionary spending on Apple's premium products. Intellectual property litigation and the ability to protect its brand and innovations are also key concerns."

JPM_BUSINESS_OVERVIEW = "JPMorgan Chase & Co. is a leading global financial services firm and one of the largest banking institutions in the United States, with operations worldwide. The company is a leader in investment banking, financial services for consumers and small businesses, commercial banking, financial transaction processing, and asset management. It serves millions of customers, corporations, institutional investors, and governments under its J.P. Morgan and Chase brands. Key segments include Consumer & Community Banking (CCB), Corporate & Investment Bank (CIB), Commercial Banking (CB), and Asset & Wealth Management (AWM)."
JPM_RISK_FACTORS = "JPMorgan Chase faces significant risks including credit risk from its lending activities, market risk from trading and investment positions, and operational risks such as fraud, cybersecurity, and system failures. Interest rate volatility significantly impacts net interest income and asset valuations. The firm is subject to extensive regulation and supervision globally, with changes potentially affecting its business model and profitability. Economic recessions or slowdowns can lead to increased defaults and reduced demand for financial services. Competition from other large banks, non-bank financial institutions, and fintech companies is intense. Legal and reputational risks are also material."

GENERIC_BUSINESS_OVERVIEW_TEMPLATE = "This is a generic business overview for {company_id}. It operates in its respective industry, offering products/services to its target market. Key strategies involve market penetration, product development, and operational efficiency."
GENERIC_RISK_FACTORS_TEMPLATE = "Key risk factors for {company_id} include market competition, economic downturns affecting demand, operational challenges, regulatory changes, and dependence on supply chains and key personnel."

# --- Helper Functions ---
def get_company_specific_texts(company_id):
    if company_id == "MSFT":
        return {
            "business_overview": MSFT_BUSINESS_OVERVIEW,
            "risk_factors": MSFT_RISK_FACTORS
        }
    elif company_id == "AAPL":
        return {
            "business_overview": AAPL_BUSINESS_OVERVIEW,
            "risk_factors": AAPL_RISK_FACTORS
        }
    elif company_id == "JPM":
        return {
            "business_overview": JPM_BUSINESS_OVERVIEW,
            "risk_factors": JPM_RISK_FACTORS
        }
    elif company_id == "TESTCORP": 
        return {
            "business_overview": GENERIC_BUSINESS_OVERVIEW_TEMPLATE.format(company_id=company_id) + " (TESTCORP specific details would be here if available.)",
            "risk_factors": GENERIC_RISK_FACTORS_TEMPLATE.format(company_id=company_id) + " (TESTCORP specific risks would be here.)"
        }
    else: # Generic companies (including the new S&P 500 names not AAPL/JPM)
        return {
            "business_overview": GENERIC_BUSINESS_OVERVIEW_TEMPLATE.format(company_id=company_id),
            "risk_factors": GENERIC_RISK_FACTORS_TEMPLATE.format(company_id=company_id)
        }

def construct_cacm_for_company(company_id: str, company_texts: dict):
    # Based on examples/msft_comprehensive_analysis_workflow.json and notebook's dynamic construction
    # For synthetic library, FAA summary guidance and DCF overrides will use defaults (i.e., not passed or passed as None)
    
    workflow_id = f"synthetic_lib_analysis_{company_id.lower()}_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
    
    cacm_instance = {
      "cacmId": workflow_id,
      "name": f"Synthetic Library Analysis for {company_id}",
      "description": f"Automated comprehensive analysis run for {company_id} for the synthetic library.",
      "inputs": {
        "target_company_id": {"value": company_id, "description": "Target company ID"},
        "msft_business_overview_text": { # Key name from msft_comprehensive_analysis_workflow
          "value": company_texts["business_overview"],
          "description": "Business overview text."
        },
        "msft_risk_factors_text": { # Key name from msft_comprehensive_analysis_workflow
          "value": company_texts["risk_factors"],
          "description": "Risk factors text."
        },
        "catalyst_input_params": {
          "value": {
            "client_id": f"{company_id}_Synthetic_Client",
            "company_id": company_id,
            "industry": f"Synthetic{company_id.split('_')[-1] if '_' in company_id else 'General'}Industry",
            "task_description_catalyst": f"Evaluate strategic opportunities for {company_id} as part of synthetic library generation."
          }
        },
        "report_generation_title_detail": {
            "value": f"Synthetic Library Analysis: {company_id}",
        },
        # For synthetic library, we run with default FAA prompts/DCF.
        "user_faa_summary_guidance": {"value": "", "description": "User guidance for FAA summary - default for library."},
        "user_dcf_discount_rate": {"value": None, "description": "User DCF discount rate override - default for library."},
        "user_dcf_terminal_growth_rate": {"value": None, "description": "User DCF terminal growth override - default for library."}
      },
      "outputs": { # These are the keys the orchestrator's output dict will have
        "final_generated_report": {"type": "string"},
        "raw_fundamental_analysis": {"type": "object"},
        "raw_snc_analysis": {"type": "object"},
        "raw_catalyst_output": {"type": "object"}
      },
      "workflow": [ # Copied & adapted from msft_comprehensive_analysis_workflow.json
        {
          "stepId": "step1_ingest_data",
          "description": "Ingest specific text data and Catalyst parameters into SharedContext.",
          "computeCapabilityRef": "urn:adk:capability:standard_data_ingestor:v1",
          "inputBindings": {
            "companyName": {"value": f"{company_id} Corp."} , 
            "companyTicker": {"value": company_id},
            "riskFactorsText": "cacm.inputs.msft_risk_factors_text", 
            "mockStructuredFinancialsForLLMSummary": "cacm.inputs.msft_business_overview_text",
            # For DataIngestionAgent to potentially pick up Catalyst params for shared_context
            # (This part of DIA is not implemented yet, so Catalyst step below gets from cacm.inputs directly)
            # "catalystParamsForContext": "cacm.inputs.catalyst_input_params" 
          },
           "outputBindings": { "ingestion_summary": "intermediate.step1_ingestion_summary" }
        },
        {
          "stepId": "step2_fundamental_analysis",
          "description": "Perform fundamental financial analysis.",
          "computeCapabilityRef": "urn:adk:capability:fundamental_analyst_agent:v1",
          "inputBindings": {
            "company_id": "cacm.inputs.target_company_id",
            "summary_guidance_prompt_addon": "cacm.inputs.user_faa_summary_guidance",
            "dcf_override_discount_rate": "cacm.inputs.user_dcf_discount_rate",
            "dcf_override_terminal_growth_rate": "cacm.inputs.user_dcf_terminal_growth_rate"
          },
          "outputBindings": {"analysis_result": "cacm.outputs.raw_fundamental_analysis"}
        },
        {
          "stepId": "step3_snc_analysis",
          "description": "Perform SNC analysis.",
          "computeCapabilityRef": "urn:adk:capability:snc_analyst_agent:v1",
          "inputBindings": {"company_id": "cacm.inputs.target_company_id"},
          "outputBindings": {"snc_analysis_result": "cacm.outputs.raw_snc_analysis"}
        },
        {
          "stepId": "step4_catalyst_insights",
          "description": "Generate strategic insights using CatalystWrapperAgent.",
          "computeCapabilityRef": "urn:adk:capability:catalyst_wrapper_agent:v1",
          "inputBindings": { 
            "client_id": "cacm.inputs.catalyst_input_params.value.client_id", 
            "company_id": "cacm.inputs.catalyst_input_params.value.company_id",
            "industry": "cacm.inputs.catalyst_input_params.value.industry"
          },
          "outputBindings": {"catalyst_output": "cacm.outputs.raw_catalyst_output"}
        },
        {
          "stepId": "step5_generate_report",
          "description": "Compile all analysis into a final report.",
          "computeCapabilityRef": "urn:adk:capability:standard_report_generator:v1",
          "inputBindings": {
            "report_title_detail": "cacm.inputs.report_generation_title_detail",
            "fundamental_analysis_data_ref": "cacm.outputs.raw_fundamental_analysis",
            "snc_analysis_data_ref": "cacm.outputs.raw_snc_analysis",
            "catalyst_data_ref": "cacm.outputs.raw_catalyst_output"
          },
          "outputBindings": {"final_report_text": "cacm.outputs.final_generated_report"}
        }
      ]
    }
    return workflow_id, cacm_instance

def assemble_full_report_object(company_id: str, company_name_processed: str, workflow_id_used: str,
                                cacm_inputs: dict, workflow_outputs: dict, company_texts: dict):
    # Structure as defined in Plan Step 2
    report_obj = {
        "company_id": company_id,
        "company_name_processed": company_name_processed, # e.g. from DIA input
        "execution_timestamp_utc": datetime.datetime.utcnow().isoformat(),
        "workflow_id_used": workflow_id_used,
        "inputs_to_workflow": { # Capture key varying inputs
            "target_company_id": cacm_inputs["target_company_id"]["value"],
            "user_faa_summary_guidance": cacm_inputs["user_faa_summary_guidance"]["value"],
            "user_dcf_discount_rate": cacm_inputs["user_dcf_discount_rate"]["value"],
            "user_dcf_terminal_growth_rate": cacm_inputs["user_dcf_terminal_growth_rate"]["value"]
        },
        "ingested_data_summary": workflow_outputs.get("intermediate.step1_ingestion_summary", 
             # Try to get from SharedContext if DIA output binding failed or wasn't there
             # This part is conceptual as direct SC access post-run isn't trivial from here
             {"status": "info", "message": "Ingestion summary not directly bound in workflow outputs."}
        ),
        "text_inputs_provided": {
            "business_overview": company_texts["business_overview"],
            "risk_factors": company_texts["risk_factors"]
        },
        "catalyst_parameters_used": cacm_inputs["catalyst_input_params"]["value"],
        "fundamental_analysis_raw": workflow_outputs.get("raw_fundamental_analysis"),
        "snc_analysis_raw": workflow_outputs.get("raw_snc_analysis"),
        "catalyst_output_raw": workflow_outputs.get("raw_catalyst_output"),
        "generated_markdown_report": workflow_outputs.get("final_generated_report")
    }
    return report_obj

async def main():
    print("Starting Synthetic Library Generation...")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

    all_report_objects = []

    kernel_service = KernelService()
    orch = Orchestrator(kernel_service=kernel_service)
    # Ensure orchestrator validator is permissive for dynamically generated CACMs if necessary
    if orch.validator is None:
        from cacm_adk_core.validator.validator import Validator # Assuming Validator can be init'd simply
        class MockPermissiveValidator: # Copied from notebook
            schema = True 
            def validate_cacm_against_schema(self, data): return True, []
        orch.validator = MockPermissiveValidator()
        print("Orchestrator validator was None, using MockPermissiveValidator.")


    for company_id in TARGET_COMPANIES:
        print(f"--- Processing company: {company_id} ---")
        company_specific_texts = get_company_specific_texts(company_id)
        workflow_id, cacm_instance_data = construct_cacm_for_company(company_id, company_specific_texts)
        
        print(f"Running workflow {workflow_id} for {company_id}...")
        success, logs, outputs = await orch.run_cacm(cacm_instance_data)

        if success:
            print(f"Successfully processed {company_id}.")
            # Extract company name used in DataIngestionAgent input
            company_name_in_workflow = cacm_instance_data["workflow"][0]["inputBindings"]["companyName"]["value"]
            report_object = assemble_full_report_object(
                company_id,
                company_name_in_workflow,
                workflow_id,
                cacm_instance_data["inputs"], # Pass the inputs section of the CACM
                outputs,
                company_specific_texts
            )
            all_report_objects.append(report_object)
        else:
            print(f"ERROR processing {company_id}. Logs:")
            for log_entry in logs:
                print(log_entry)
            # Still add a partial error object if desired
            error_object = {
                "company_id": company_id,
                "execution_timestamp_utc": datetime.datetime.utcnow().isoformat(),
                "workflow_id_used": workflow_id,
                "status": "ERROR",
                "logs": logs,
                "outputs": outputs
            }
            all_report_objects.append(error_object)
        print(f"--- Finished company: {company_id} ---\n")

    # --- File Writing (Actual writing will be in Step 4's subtask) ---
    # This script will now just print the collected objects.
    # The subtask for Step 4 will take this script and add the file writing part.
    print("\n--- Collected Report Objects (to be written to JSONL) ---")
    for obj in all_report_objects:
        # For display here, pretty print. For JSONL, each obj is one line.
        print(json.dumps(obj, indent=2)) 
        print("---")
    
    print(f"\nWriting {len(all_report_objects)} report objects to JSONL file: {OUTPUT_FILE_PATH}...")
    try:
        with open(OUTPUT_FILE_PATH, 'w') as f:
            for entry in all_report_objects:
                f.write(json.dumps(entry) + '\n')
        print(f"Synthetic library successfully generated at {OUTPUT_FILE_PATH}")
    except IOError as e:
        print(f"ERROR: Could not write to output file {OUTPUT_FILE_PATH}: {e}")
    
    print("Synthetic Library Generation script finished.")


if __name__ == "__main__":
    if sys.platform == "win32" and sys.version_info >= (3, 8, 0):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
