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

        # MSFT-specific data package
        elif company_id == "MSFT":
            self.logger.info(f"Returning MSFT-specific data for company_id: {company_id}, data_type: {data_type}")
            msft_data_package = {
              "company_info": {
                "name": "Microsoft Corp.",
                "ticker": "MSFT",
                "industry_sector": "Technology",
                "country": "USA"
              },
              "financial_data_detailed": {
                "income_statement": {
                  "revenue": [211915000000, 227583000000, 243100000000],
                  "net_income": [72738000000, 73307000000, 75150000000],
                  "ebitda": [102475000000, 108750000000, 115300000000]
                },
                "balance_sheet": {
                  "total_assets": [380098000000, 402150000000, 425300000000],
                  "total_liabilities": [191791000000, 198230000000, 205750000000],
                  "shareholders_equity": [188307000000, 203920000000, 219550000000],
                  "cash_and_equivalents": [139316000000, 143900000000, 150200000000],
                  "short_term_debt": [15000000000, 16000000000, 17000000000],
                  "long_term_debt": [47033000000, 45000000000, 42000000000]
                },
                "cash_flow_statement": {
                  "operating_cash_flow": [89035000000, 93120000000, 97300000000],
                  "investing_cash_flow": [-22345000000, -25300000000, -28450000000],
                  "financing_cash_flow": [-46000000000, -48000000000, -50000000000],
                  "free_cash_flow": [66690000000, 67820000000, 68850000000]
                },
                "key_ratios": {
                  "debt_to_equity_ratio": 0.33,
                  "net_profit_margin": 0.35,
                  "current_ratio": 2.0,
                  "interest_coverage_ratio": 20.0
                },
                "dcf_assumptions": {
                  "fcf_projection_years_total": 10,
                  "initial_high_growth_period_years": 5,
                  "initial_high_growth_rate": 0.12,
                  "stable_growth_rate": 0.05,
                  "discount_rate": 0.085,
                  "terminal_growth_rate_perpetuity": 0.025
                },
                "market_data": {
                  "share_price": 420.00,
                  "shares_outstanding": 7430000000,
                  "annual_debt_service_placeholder": "5000000000",
                  "payment_history_placeholder": "Current",
                  "interest_capitalization_placeholder": "No"
                }
              },
              "qualitative_company_info": {
                "management_assessment": "Strong and experienced leadership team.",
                "competitive_advantages": "Significant moat in enterprise software, cloud computing (Azure), gaming (Xbox), and growing AI capabilities.",
                "business_model_strength": "Diversified revenue streams across software, services, cloud, and devices.",
                "revenue_cashflow_stability_notes_placeholder": "Generally stable with strong growth in cloud services.",
                "financial_deterioration_notes_placeholder": "No significant deterioration noted; strong financial position."
              },
              "industry_data_context": {
                "outlook": "Positive for cloud computing and AI, competitive in other segments."
              },
              "economic_data_context": {
                "overall_outlook": "Stable but with macroeconomic headwinds (inflation, interest rates)."
              },
              "collateral_and_debt_details": {
                "loan_to_value_ratio": 0.1,
                "collateral_type": "Primarily unsecured corporate debt; specific project finance might have asset backing.",
                "other_credit_enhancements": "Strong balance sheet and cash flows are primary credit mitigants."
              }
            }
            return {"status": "success", "data": msft_data_package}

        # Mock data for TESTCORP (should be checked after MSFT)
        elif company_id == "TESTCORP":
            self.logger.info(f"Returning mock data for TESTCORP, data_type: {data_type}")
            testcorp_data = {
                "company_info": {"name": "TESTCORP Inc.", "industry_sector": "Technology", "country": "USA"},
                "financial_data_detailed": {
                    "income_statement": {"revenue": [1000, 1100, 1250], "net_income": [100, 120, 150], "ebitda": [150, 170, 200]},
                    "balance_sheet": {"total_assets": [2000, 2100, 2200], "total_liabilities": [800, 850, 900],
                                      "shareholders_equity": [1200, 1250, 1300], "cash_and_equivalents": [200, 250, 300],
                                      "short_term_debt": [50,50,50], "long_term_debt": [500,450, 400]},
                    "cash_flow_statement": {"operating_cash_flow": [180, 200, 230], "investing_cash_flow": [-50, -60, -70],
                                            "financing_cash_flow": [-30, -40, -50], "free_cash_flow": [130, 140, 160]},
                    "key_ratios": {"debt_to_equity_ratio": 0.6923, "net_profit_margin": 0.12, "current_ratio": 2.44, "interest_coverage_ratio": 5.0},
                    "dcf_assumptions": {
                        "fcf_projection_years_total": 10,
                        "initial_high_growth_period_years": 5,
                        "initial_high_growth_rate": 0.10,
                        "stable_growth_rate": 0.05,
                        "discount_rate": 0.09,
                        "terminal_growth_rate_perpetuity": 0.025
                    },
                    "market_data": {"share_price": 65.00, "shares_outstanding": 10000000, "annual_debt_service_placeholder": "60", "payment_history_placeholder": "Current", "interest_capitalization_placeholder": "No"}
                },
                "qualitative_company_info": {"management_assessment": "Experienced", "competitive_advantages": "Strong IP", "revenue_cashflow_stability_notes_placeholder": "Stable", "financial_deterioration_notes_placeholder": "None noted."},
                "industry_data_context": {"outlook": "Positive"},
                "economic_data_context": {"overall_outlook": "Stable"},
                "collateral_and_debt_details": {"loan_to_value_ratio": 0.6, "collateral_type": "Accounts Receivable, Inventory", "other_credit_enhancements": "Standard covenants in place."}
            }
            return {"status": "success", "data": testcorp_data}

        # Fallback error if no other conditions met
        self.logger.warning(f"No specific data retrieval logic implemented for company_id: {company_id} and data_type: {data_type}")
        return {"status": "error", "message": f"Data not found for company_id: {company_id}, data_type: {data_type}"}
