# cacm_adk_core/agents/data_retrieval_agent.py
import logging
from typing import Dict, Any, Optional

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext

class DataRetrievalAgent(Agent):
    """
    Agent responsible for retrieving data required by other agents.
    It can fetch data based on company_id and data_type.
    Includes a mechanism for data override for testing purposes.
    """

    def __init__(self, kernel_service: KernelService, agent_config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_name="DataRetrievalAgent", kernel_service=kernel_service)
        self.config = agent_config if agent_config else {}
        self.logger.info(f"DataRetrievalAgent initialized. Config: {self.config}")

    async def run(self, task_description: str, current_step_inputs: Dict[str, Any], shared_context: SharedContext) -> Dict[str, Any]:
        self.logger.info(f"{self.agent_name} received task: {task_description} with inputs: {current_step_inputs}")

        company_id = current_step_inputs.get("company_id")
        data_type = current_step_inputs.get("data_type", "get_company_financials") # Default data_type
        data_override = current_step_inputs.get("data_override")

        # Check shared_context for a global override if not provided in direct inputs
        # This allows the workflow to provide the override via cacm.inputs
        if not data_override:
            initial_inputs = shared_context.get_global_parameter("initial_inputs")
            if initial_inputs and isinstance(initial_inputs.get("dra_company_data_override"), dict):
                 # Assuming the override is passed as a dict with a "value" field, as per cacm.inputs structure
                override_input_value = initial_inputs["dra_company_data_override"].get("value")
                if override_input_value:
                    self.logger.info("Found 'dra_company_data_override' in shared_context initial_inputs.")
                    data_override = override_input_value


        if data_override:
            self.logger.info(f"Using data_override for company_id: {company_id}, data_type: {data_type}")
            return {"status": "success", "data": data_override}

        if not company_id:
            self.logger.error("Missing 'company_id' in inputs.")
            return {"status": "error", "message": "Missing 'company_id' in inputs."}

        # Mock data for TESTCORP as used in test_integrated_agents_workflow.json
        if company_id == "TESTCORP":
            self.logger.info(f"Returning mock data for TESTCORP, data_type: {data_type}")
            # This mock data should ideally match the structure expected by FAA and SNCAA,
            # similar to 'dra_company_data_override' in the test JSON.
            mock_data = {
                "company_info": {"name": "TESTCORP Inc.", "industry_sector": "Technology", "country": "USA"},
                "financial_data_detailed": {
                    "income_statement": {"revenue": [1000, 1100, 1250], "net_income": [100, 120, 150], "ebitda": [150, 170, 200]},
                    "balance_sheet": {"total_assets": [2000, 2100, 2200], "total_liabilities": [800, 850, 900],
                                      "shareholders_equity": [1200, 1250, 1300], "cash_and_equivalents": [200, 250, 300],
                                      "short_term_debt": [50,50,50], "long_term_debt": [500,450, 400]},
                    "cash_flow_statement": {"operating_cash_flow": [180, 200, 230], "investing_cash_flow": [-50, -60, -70],
                                            "financing_cash_flow": [-30, -40, -50], "free_cash_flow": [130, 140, 160]},
                    "key_ratios": {"debt_to_equity_ratio": 0.6923, "net_profit_margin": 0.12, "current_ratio": 2.44, "interest_coverage_ratio": 5.0}, # Populated for SNC
                    "dcf_assumptions": {
                        "fcf_projection_years_total": 10,
                        "initial_high_growth_period_years": 5,
                        "initial_high_growth_rate": 0.10,
                        "stable_growth_rate": 0.05,
                        "discount_rate": 0.09,
                        "terminal_growth_rate_perpetuity": 0.025
                    },
                    "market_data": {"share_price": 65.00, "shares_outstanding": 10000000, "annual_debt_service_placeholder": "60", "payment_history_placeholder": "Current", "interest_capitalization_placeholder": "No"} # Added SNC fields
                },
                "qualitative_company_info": {"management_assessment": "Experienced", "competitive_advantages": "Strong IP", "revenue_cashflow_stability_notes_placeholder": "Stable", "financial_deterioration_notes_placeholder": "None noted."}, # Added SNC fields
                "industry_data_context": {"outlook": "Positive"},
                "economic_data_context": {"overall_outlook": "Stable"},
                "collateral_and_debt_details": {"loan_to_value_ratio": 0.6, "collateral_type": "Accounts Receivable, Inventory", "other_credit_enhancements": "Standard covenants in place."} # Added SNC fields
            }
            return {"status": "success", "data": mock_data}

        # Placeholder for future actual data retrieval logic
        self.logger.warning(f"No data retrieval logic implemented for company_id: {company_id} and data_type: {data_type}")
        return {"status": "error", "message": f"Data not found for company_id: {company_id}, data_type: {data_type}"}
