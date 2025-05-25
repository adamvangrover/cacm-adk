# api/main.py
import json
import os
import uuid
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import pathlib # To construct absolute path for static files
from pydantic import BaseModel, Field

# Corrected import paths assuming API is run from project root or PYTHONPATH is set
import sys
# Add project root to sys.path if not already there, common for running FastAPI apps with uvicorn from root
# This ensures that 'cacm_adk_core' can be found
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from cacm_adk_core.template_engine.template_engine import TemplateEngine
    from cacm_adk_core.validator.validator import Validator
    from cacm_adk_core.orchestrator.orchestrator import Orchestrator
    from cacm_adk_core.report_generator.report_generator import ReportGenerator
except ImportError as e:
    print(f"Critical Import Error: {e}. Ensure PYTHONPATH includes the project root or run with 'python -m api.main'.")
    # Optionally, re-raise or exit if core components cannot be loaded. For now, FastAPI might start but endpoints will fail.
    raise

app = FastAPI(
    title="CACM Authoring & Development Kit API",
    description="API for managing and interacting with Credit Analysis Capability Modules (CACMs).",
    version="0.1.0" # Corresponds to Phase 4 target
)

# Get the absolute path to the 'static' directory
# Assumes 'static' directory is at the same level as the 'api' directory,
# or more robustly, relative to the project root if 'api/main.py' is PROJECT_ROOT/api/main.py
static_dir = pathlib.Path(PROJECT_ROOT) / "static" # PROJECT_ROOT defined earlier

if not static_dir.is_dir():
    print(f"Warning: Static directory not found at {static_dir}. Will attempt to create for basic functionality.")
    # In a real app, you might raise an error or handle this more gracefully.
    # For this subtask, let's try to create it if it's missing, assuming it's for development.
    try:
        static_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created static directory at: {static_dir}")
        # Note: This won't populate it with index.html or style.css if they weren't created by previous steps.
    except Exception as e:
        print(f"Error creating static directory {static_dir}: {e}")


app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# --- Global Instances of Core Components ---
# These paths assume the API server (e.g., uvicorn) is run from the project's root directory.
SCHEMA_PATH = "cacm_standard/cacm_schema_v0.2.json"
CATALOG_PATH = "config/compute_capability_catalog.json"
TEMPLATES_PATH = "cacm_library/templates"

# Initialize Validator
if not os.path.exists(SCHEMA_PATH):
    print(f"FATAL: CACM Schema not found at {SCHEMA_PATH}. API cannot function correctly.")
    # In a real app, you might prevent FastAPI from starting or have a health check fail.
    # For this script, endpoints relying on validator will fail at runtime.
validator_instance = Validator(schema_filepath=SCHEMA_PATH)

# Initialize TemplateEngine
template_engine_instance = TemplateEngine(templates_dir=TEMPLATES_PATH)

# Initialize Orchestrator
# Orchestrator's __init__ handles catalog not found by creating an empty one, but logs an error.
orchestrator_instance = Orchestrator(validator=validator_instance, catalog_filepath=CATALOG_PATH)

# ReportGenerator instance
report_generator_instance = ReportGenerator()


# --- Pydantic Models for Request/Response Bodies ---
class TemplateOverride(BaseModel):
    cacm_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    # Add other common top-level fields you might want to override simply
    # For complex overrides (like specific input values), a Dict[str, Any] might be needed.
    metadata_overrides: Optional[Dict[str, Any]] = Field(None, description="Overrides for the metadata section.")
    # inputs_override: Optional[Dict[str, Any]] = Field(None, description="Overrides for the inputs section.") # More complex

class CacmInstance(BaseModel):
    cacm_data: Dict[str, Any] = Field(..., description="The full CACM instance as a JSON object (dictionary).")

class SmeInputData(BaseModel):
    # Simplified structure for initial SME data input
    # Matches the 'value' part of the sme_scoring_model_template's inputs
    smeFinancialsValue: Dict[str, Any] = Field(..., description="Financial data for the SME (e.g., balanceSheet, incomeStatement figures).")
    qualitativeDataValue: Dict[str, Any] = Field(..., description="Qualitative data for the SME (e.g., managementExperience, industryOutlook).")
    # Optional: Allow overriding some parameters of the SME model for this run
    parameters_override: Optional[List[Dict[str, Any]]] = Field(None, description="Optional list of parameter objects to override in the template for this run.")


class ValidationResponse(BaseModel):
    is_valid: bool
    errors: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None
    
class RunResponse(BaseModel): # Will be enhanced later
    success: bool
    message: str
    # log_messages: Optional[List[str]] = None # To be added when Orchestrator returns them
    # mocked_outputs: Optional[Dict[str, Any]] = None # To be added

# (Within api/main.py)
class ReportHeaderModel(BaseModel):
    reportTitle: str
    generatedDate: str # datetime as str
    smeIdentifier: str
    dataSource: str

class CreditRatingModel(BaseModel):
    spScaleEquivalent: str
    sncRegulatoryEquivalent: str

class ExecutiveSummaryModel(BaseModel):
    overallAssessment: str
    outlook: str

class ReportResponse(BaseModel): # Was previously a placeholder
    reportHeader: ReportHeaderModel
    creditRating: CreditRatingModel
    executiveSummary: ExecutiveSummaryModel
    keyRiskFactors_XAI: List[str] # Or List[Dict[str, Any]] if more structured
    detailedRationale: str
    supportingMetrics: Dict[str, Any] # Contains the raw mocked_outputs for now
    disclaimer: str


# --- API Endpoints ---
@app.get("/templates/", summary="List Available CACM Templates")
async def list_templates_api():
    """Retrieves a list of available CACM templates with their names and descriptions."""
    if not os.path.isdir(template_engine_instance.templates_dir):
        raise HTTPException(status_code=503, detail=f"Templates directory not found: {template_engine_instance.templates_dir}. Server misconfiguration.")
    templates = template_engine_instance.list_templates()
    if not templates:
        return {"message": "No templates found."}
    return templates

@app.post("/templates/{template_filename}/instantiate", summary="Instantiate a CACM Template")
async def instantiate_template_api(template_filename: str, overrides: Optional[TemplateOverride] = None):
    """
    Instantiates a specified CACM template.
    Allows overriding certain fields like `cacm_id`, `name`, `description`, and `metadata`.
    """
    if not os.path.isdir(template_engine_instance.templates_dir): # Check again
         raise HTTPException(status_code=503, detail=f"Templates directory not found: {template_engine_instance.templates_dir}. Server misconfiguration.")

    # Convert Pydantic model to a plain dict for overrides, handling None
    override_dict = {}
    if overrides:
        if overrides.name: override_dict["name"] = overrides.name
        if overrides.description: override_dict["description"] = overrides.description
        if overrides.metadata_overrides: override_dict["metadata"] = overrides.metadata_overrides
        # Note: TemplateEngine's instantiate_template does deep merge for 'overrides' dict.
        # For simplicity, this API endpoint only exposes a few common overrides.
        # A more advanced version might take a full 'overrides: Dict[str, Any]'.

    instance = template_engine_instance.instantiate_template(
        template_filename, 
        cacm_id=overrides.cacm_id if overrides else None, 
        overrides=override_dict if override_dict else None
    )
    if not instance:
        # Check if template file actually exists to give a more specific error
        template_path = os.path.join(template_engine_instance.templates_dir, template_filename)
        if not os.path.exists(template_path):
            raise HTTPException(status_code=404, detail=f"Template file '{template_filename}' not found.")
        raise HTTPException(status_code=500, detail=f"Could not instantiate template '{template_filename}'. Possible parsing error or internal issue.")
    return instance

@app.post("/cacm/validate/", response_model=ValidationResponse, summary="Validate a CACM Instance")
async def validate_cacm_api(cacm_payload: CacmInstance = Body(...)):
    """Validates a given CACM instance (JSON payload) against the official CACM JSON schema."""
    if not validator_instance or not validator_instance.schema:
        raise HTTPException(status_code=503, detail="Validator or schema not initialized on server.")
    
    is_valid, errors = validator_instance.validate_cacm_against_schema(cacm_payload.cacm_data)
    if is_valid:
        return ValidationResponse(is_valid=True, message="CACM instance is valid.")
    else:
        return ValidationResponse(is_valid=False, errors=errors, message="CACM instance is invalid.")

@app.post("/cacm/run/", response_model=RunResponse, summary="Simulate Execution of a CACM Workflow")
async def run_cacm_api(cacm_payload: CacmInstance = Body(...)):
    """
    Simulates the execution of a CACM instance's workflow.
    (Note: Actual computation is mocked. Orchestrator will be updated to return logs and mocked outputs).
    """
    if not orchestrator_instance:
         raise HTTPException(status_code=503, detail="Orchestrator not initialized on server.")
    if not validator_instance or not validator_instance.schema: # Orchestrator needs validator
        raise HTTPException(status_code=503, detail="Validator for Orchestrator not initialized on server.")

    # Orchestrator's run_cacm currently returns bool. Will be updated to return (bool, logs, mocked_outputs)
    success = orchestrator_instance.run_cacm(cacm_payload.cacm_data)
    
    if success:
        # Placeholder until Orchestrator returns more details
        return RunResponse(success=True, message="CACM workflow simulation initiated and completed (simulated).")
    else:
        # Orchestrator's run_cacm prints validation errors to console if validation fails.
        # We might want to capture those errors here if Orchestrator is refactored.
        return RunResponse(success=False, message="CACM workflow simulation failed or did not run (e.g., due to validation errors).")


@app.post("/reports/generate/sme_credit_score/", response_model=ReportResponse, summary="Generate Enhanced SME Credit Score Report")
async def generate_sme_report_api(sme_data: SmeInputData = Body(...)):
    """
    Generates an enhanced, simulated SME credit score report.
    Takes SME financial and qualitative data, instantiates the SME scoring template,
    simulates its run via the Orchestrator, and then formats a detailed report.
    """
    template_filename = "sme_scoring_model_template.jsonc"
    
    # Prepare overrides for instantiation (same as before)
    instantiation_overrides = {
        "inputs": {
            "smeFinancials": {"value": sme_data.smeFinancialsValue},
            "qualitativeData": {"value": sme_data.qualitativeDataValue}
        }
    }
    if sme_data.parameters_override:
        instantiation_overrides["parameters"] = sme_data.parameters_override

    sme_cacm_instance = template_engine_instance.instantiate_template(
        template_filename,
        overrides=instantiation_overrides
    )

    if not sme_cacm_instance:
        template_path = os.path.join(template_engine_instance.templates_dir, template_filename)
        if not os.path.exists(template_path):
             raise HTTPException(status_code=404, detail=f"SME scoring template '{template_filename}' not found.")
        raise HTTPException(status_code=500, detail=f"Could not instantiate SME scoring template '{template_filename}'. Possible parsing error or internal issue.")

    if not orchestrator_instance:
         raise HTTPException(status_code=503, detail="Orchestrator not initialized on server.")
    
    # Orchestrator.run_cacm now returns (success: bool, log_messages: List[str], mocked_outputs: Dict[str, Any])
    run_success, _run_logs, mocked_outputs = orchestrator_instance.run_cacm(sme_cacm_instance) # We'll use logs later if needed
    
    if not run_success:
        # Orchestrator's run_cacm logs validation errors.
        # Consider capturing logs from orchestrator to return more specific error details here.
        raise HTTPException(status_code=422, detail="Failed to run the instantiated SME CACM, likely due to data validation issues after instantiation. Check server logs for details from Orchestrator.")

    if not report_generator_instance: # Should not happen if initialized globally
        raise HTTPException(status_code=503, detail="ReportGenerator not initialized on server.")

    # Extract a potential SME identifier from the input data if available, or use a default
    # This depends on how sme_data is structured; for now, let's assume it might be part of smeFinancialsValue or qualitativeDataValue
    sme_id_from_input = sme_data.smeFinancialsValue.get("companyId", sme_data.qualitativeDataValue.get("companyId", "N/A_from_API_input"))


    # Generate the detailed report using the ReportGenerator
    generated_report_content = report_generator_instance.generate_sme_score_report(
        mocked_outputs=mocked_outputs,
        sme_identifier=sme_id_from_input,
        cacm_inputs=sme_cacm_instance.get("inputs") # Pass inputs for potential XAI context
    )
    
    # The generated_report_content should now match the ReportResponse Pydantic model
    return generated_report_content # FastAPI will validate against ReportResponse

# --- Main execution for uvicorn ---
# This part is typically not included if you run with `uvicorn api.main:app`
# but can be useful for simple testing `python api/main.py` if uvicorn is installed.
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)


@app.get("/", response_class=HTMLResponse, summary="Serve Landing Page")
async def serve_index():
    """Serves the main index.html landing page.""""
    index_html_path = static_dir / "index.html" # Use static_dir defined above
    try:
        with open(index_html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        # Fallback content if index.html is missing, though previous steps should create it.
        return HTMLResponse(content="<html><body><h1>CACM-ADK</h1><p>Welcome. Index.html not found in static directory.</p></body></html>", status_code=404)
    except Exception as e:
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>Could not load index.html: {e}</p></body></html>", status_code=500)
