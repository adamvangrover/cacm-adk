# api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import os
import sys

# Adjust path to import Orchestrator
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)
# Ensure PROJECT_ROOT is /app for the imports below to work correctly from /app
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from cacm_adk_core.orchestrator import Orchestrator
except ImportError as e:
    print(
        f"Error importing Orchestrator: {e}. Current sys.path: {sys.path}",
        file=sys.stderr,
    )
    # This is a fallback if the above path adjustment doesn't work in all execution contexts.
    # A more robust solution is needed for package structure if this is hit often.
    # For now, we'll allow the server to start but the endpoint will fail.
    Orchestrator = None


app = FastAPI(title="Credit Intelligence SPA Backend", version="0.1.0")


# --- Pydantic Models for Request/Response Body ---
class FinancialStatementData(BaseModel):
    currentAssets: float
    currentLiabilities: float
    totalDebt: float
    totalEquity: float


class BasicRatioAnalysisInput(BaseModel):
    financialStatementData: FinancialStatementData


class RatioCalculationResult(BaseModel):
    current_ratio: float | None = None
    debt_to_equity_ratio: float | None = None


class BasicRatioAnalysisOutput(BaseModel):
    calculated_ratios: RatioCalculationResult | None = {}
    execution_errors: list[str] = []


# --- Orchestrator Instance ---
if Orchestrator:
    try:
        orchestrator_instance = Orchestrator(load_catalog_on_init=False)
    except Exception as e:
        print(f"Error initializing Orchestrator: {e}", file=sys.stderr)
        orchestrator_instance = None
else:
    orchestrator_instance = None
    print(
        "Orchestrator class not imported, API endpoint will not function.",
        file=sys.stderr,
    )


# --- API Endpoint ---
@app.post("/api/run_basic_ratio_analysis", response_model=BasicRatioAnalysisOutput)
async def run_basic_ratio_analysis_endpoint(input_data: BasicRatioAnalysisInput):
    if not orchestrator_instance:
        raise HTTPException(
            status_code=503,
            detail="Orchestrator service is not available. Check server logs.",
        )

    template_filename = "cacm_library/templates/basic_ratio_analysis_template.json"
    template_path = os.path.join(PROJECT_ROOT, template_filename)

    if not os.path.exists(template_path):
        print(f"Template file not found at: {template_path}", file=sys.stderr)
        raise HTTPException(
            status_code=500, detail=f"CACM template file not found on server."
        )

    input_dict = {
        "financialStatementData": input_data.financialStatementData.model_dump()
    }

    try:
        orchestrator_result = orchestrator_instance.execute_cacm(
            template_path=template_path, input_data=input_dict
        )

        ratios_data = orchestrator_result.get("calculatedRatios", {})
        errors_data = orchestrator_result.get("execution_errors", [])

        if ratios_data is None:  # Ensure it's a dict for Pydantic model
            ratios_data = {}

        response_payload = BasicRatioAnalysisOutput(
            calculated_ratios=(
                RatioCalculationResult(**ratios_data) if ratios_data else None
            ),
            execution_errors=errors_data,
        )
        return response_payload

    except FileNotFoundError:
        raise HTTPException(
            status_code=500, detail="CACM template not found during execution."
        )
    except Exception as e:
        print(f"Error during CACM execution via API: {e}", file=sys.stderr)
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred during analysis."
        )


# --- Static Files (to serve index.html and other assets) ---
app.mount("/", StaticFiles(directory=PROJECT_ROOT, html=True), name="static_root")


if __name__ == "__main__":
    import uvicorn

    # To run from PROJECT_ROOT: uvicorn api.main:app --reload
    # To run from api/ directory: uvicorn main:app --reload
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
