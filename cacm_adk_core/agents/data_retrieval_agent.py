# cacm_adk_core/agents/data_retrieval_agent.py
import logging
from typing import Dict, Any, Optional

from cacm_adk_core.agents.base_agent import Agent
from cacm_adk_core.semantic_kernel_adapter import KernelService
from cacm_adk_core.context.shared_context import SharedContext

# --- Mock Data Packages ---
msft_data_package = { # Ensuring MSFT data is also at module level for consistency
  "company_info": {
    "name": "Microsoft Corp.", "ticker": "MSFT", "industry_sector": "Technology", "country": "USA"
  },
  "financial_data_detailed": {
    "income_statement": {
      "revenue": [211915000000, 227583000000, 243100000000], "net_income": [72738000000, 73307000000, 75150000000],
      "ebitda": [102475000000, 108750000000, 115300000000]
    },
    "balance_sheet": {
      "total_assets": [380098000000, 402150000000, 425300000000], "total_liabilities": [191791000000, 198230000000, 205750000000],
      "shareholders_equity": [188307000000, 203920000000, 219550000000], "cash_and_equivalents": [139316000000, 143900000000, 150200000000],
      "short_term_debt": [15000000000, 16000000000, 17000000000], "long_term_debt": [47033000000, 45000000000, 42000000000]
    },
    "cash_flow_statement": {
      "operating_cash_flow": [89035000000, 93120000000, 97300000000], "investing_cash_flow": [-22345000000, -25300000000, -28450000000],
      "financing_cash_flow": [-46000000000, -48000000000, -50000000000], "free_cash_flow": [66690000000, 67820000000, 68850000000]
    },
    "key_ratios": {
      "debt_to_equity_ratio": 0.33, "net_profit_margin": 0.35, "current_ratio": 2.0, "interest_coverage_ratio": 20.0
    },
    "dcf_assumptions": {
      "fcf_projection_years_total": 10, "initial_high_growth_period_years": 5, "initial_high_growth_rate": 0.12,
      "stable_growth_rate": 0.05, "discount_rate": 0.085, "terminal_growth_rate_perpetuity": 0.025
    },
    "market_data": {
      "share_price": 420.00, "shares_outstanding": 7430000000, "annual_debt_service_placeholder": "5000000000",
      "payment_history_placeholder": "Current", "interest_capitalization_placeholder": "No"
    }
  },
  "qualitative_company_info": {
    "management_assessment": "Strong and experienced leadership team.", "competitive_advantages": "Significant moat in enterprise software, cloud computing (Azure), gaming (Xbox), and growing AI capabilities.",
    "business_model_strength": "Diversified revenue streams across software, services, cloud, and devices.",
    "revenue_cashflow_stability_notes_placeholder": "Generally stable with strong growth in cloud services.",
    "financial_deterioration_notes_placeholder": "No significant deterioration noted; strong financial position."
  },
  "industry_data_context": {"outlook": "Positive for cloud computing and AI, competitive in other segments."},
  "economic_data_context": {"overall_outlook": "Stable but with macroeconomic headwinds (inflation, interest rates)."},
  "collateral_and_debt_details": {
    "loan_to_value_ratio": 0.1, "collateral_type": "Primarily unsecured corporate debt; specific project finance might have asset backing.",
    "other_credit_enhancements": "Strong balance sheet and cash flows are primary credit mitigants."
  }
}

aapl_data_package = {
  "company_info": {
    "name": "Apple Inc.", "ticker": "AAPL", "industry_sector": "Technology", "country": "USA"
  },
  "financial_data_detailed": {
    "income_statement": { # Figures in millions USD
      "revenue": [394328, 383285, 387540], # Illustrative TTM, TTM-1, TTM-2
      "net_income": [99803, 94680, 97000],
      "ebitda": [130541, 125820, 128000]
    },
    "balance_sheet": {
      "total_assets": [352755, 335050, 350000],
      "total_liabilities": [290435, 270500, 280000],
      "shareholders_equity": [62320, 64550, 70000],
      "cash_and_equivalents": [61555, 55700, 60000],
      "short_term_debt": [15000, 14000, 13000],
      "long_term_debt": [98967, 95000, 90000]
    },
    "cash_flow_statement": {
      "operating_cash_flow": [122151, 110540, 115000],
      "investing_cash_flow": [-22000, -20000, -18000],
      "financing_cash_flow": [-90000, -85000, -80000],
      "free_cash_flow": [100151, 90540, 97000]
    },
    "key_ratios": {},
    "dcf_assumptions": {
      "fcf_projection_years_total": 10, "initial_high_growth_period_years": 3,
      "initial_high_growth_rate": 0.08, "stable_growth_rate": 0.04,
      "discount_rate": 0.09, "terminal_growth_rate_perpetuity": 0.025
    },
    "market_data": {
      "share_price": 190.00, "shares_outstanding": 15500000000,
      "annual_debt_service_placeholder": "10000",
      "payment_history_placeholder": "Current", "interest_capitalization_placeholder": "No"
    }
  },
  "qualitative_company_info": {
    "management_assessment": "Strong, visionary leadership with proven execution.",
    "competitive_advantages": "Brand loyalty, ecosystem integration (hardware, software, services), strong innovation pipeline, global distribution.",
    "business_model_strength": "High-margin hardware, growing services revenue, direct-to-consumer channels.",
    "revenue_cashflow_stability_notes_placeholder": "Generally stable with product cycle dependency; services provide recurring revenue.",
    "financial_deterioration_notes_placeholder": "No significant deterioration; strong cash generation."
  },
  "industry_data_context": {"outlook": "Competitive smartphone market, growth in wearables and services, focus on AI integration."},
  "economic_data_context": {"overall_outlook": "Consumer spending sensitive to macroeconomic trends; global supply chain considerations."},
  "collateral_and_debt_details": {"loan_to_value_ratio": 0.05, "collateral_type": "Primarily unsecured corporate debt.", "other_credit_enhancements": "Strong brand and financials."}
}

jpm_data_package = {
  "company_info": {
    "name": "JPMorgan Chase & Co.", "ticker": "JPM", "industry_sector": "Financials", "country": "USA"
  },
  "financial_data_detailed": {
    "income_statement": {
      "revenue": [132250, 128695, 145000],
      "net_income": [48334, 37676, 42000],
      "ebitda": [65000, 55000, 60000]
    },
    "balance_sheet": {
      "total_assets": [3872000, 3744000, 3900000],
      "total_liabilities": [3560000, 3450000, 3600000],
      "shareholders_equity": [312000, 294000, 300000],
      "cash_and_equivalents": [500000, 480000, 520000],
      "short_term_debt": [200000, 180000, 190000],
      "long_term_debt": [300000, 280000, 290000]
    },
    "cash_flow_statement": {
      "operating_cash_flow": [70000, 60000, 65000],
      "investing_cash_flow": [-10000, -8000, -9000],
      "financing_cash_flow": [-30000, -25000, -28000],
      "free_cash_flow": [60000, 52000, 56000]
    },
    "key_ratios": {},
    "dcf_assumptions": {
      "fcf_projection_years_total": 5, "initial_high_growth_period_years": 2,
      "initial_high_growth_rate": 0.05, "stable_growth_rate": 0.03,
      "discount_rate": 0.10, "terminal_growth_rate_perpetuity": 0.02
    },
    "market_data": {
      "share_price": 195.00, "shares_outstanding": 2900000000,
      "annual_debt_service_placeholder": "20000",
      "payment_history_placeholder": "Current", "interest_capitalization_placeholder": "No"
    }
  },
  "qualitative_company_info": {
    "management_assessment": "Experienced and well-regarded management team.",
    "competitive_advantages": "Scale, diversified financial services (investment banking, commercial banking, asset management, consumer banking), strong brand, extensive global network.",
    "business_model_strength": "Diversified revenue streams across different financial services, large deposit base, strong capital position.",
    "revenue_cashflow_stability_notes_placeholder": "Revenue can be cyclical and market-sensitive, but diversification helps stability. Net interest income is a key driver.",
    "financial_deterioration_notes_placeholder": "Subject to credit cycles and market volatility; currently strong capital ratios."
  },
  "industry_data_context": {"outlook": "Rising interest rates (mixed impact), regulatory changes, fintech competition, cybersecurity risks."},
  "economic_data_context": {"overall_outlook": "Dependent on overall economic health, interest rate environment, and market stability."},
  "collateral_and_debt_details": {"loan_to_value_ratio": None, "collateral_type": "Various forms of collateral for specific loan types; parent company debt largely unsecured.", "other_credit_enhancements": "Regulatory capital, diversified assets."}
}


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
            # msft_data_package is now defined at module level
            return {"status": "success", "data": msft_data_package}

        elif company_id == "AAPL":
            self.logger.info(f"Returning AAPL-specific data for company_id: {company_id}, data_type: {data_type}")
            return {"status": "success", "data": aapl_data_package}

        elif company_id == "JPM":
            self.logger.info(f"Returning JPM-specific data for company_id: {company_id}, data_type: {data_type}")
            return {"status": "success", "data": jpm_data_package}

        # Mock data for TESTCORP (should be checked after MSFT, AAPL, JPM)
        elif company_id == "TESTCORP":
            self.logger.info(f"Returning mock data for TESTCORP, data_type: {data_type}")
            testcorp_data = { # Renamed from mock_data to avoid conflict if msft_data_package was not module level
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

        else: # For any other company_id
            self.logger.info(f"Returning generic placeholder data for company_id: {company_id}, data_type: {data_type}")
            generic_data_package = {
                "company_info": {"name": f"{company_id} (Generic Data)", "ticker": company_id, "industry_sector": "N/A", "country": "N/A"},
                "financial_data_detailed": {
                    "income_statement": {"revenue": [1000000, 1100000], "net_income": [10000, 12000], "ebitda": [15000, 17000]},
                    "balance_sheet": {"total_assets": [200000, 210000], "total_liabilities": [80000, 85000],
                                      "shareholders_equity": [120000, 125000], "cash_and_equivalents": [20000, 25000],
                                      "short_term_debt": [5000,5000], "long_term_debt": [50000,45000]},
                    "cash_flow_statement": {"operating_cash_flow": [18000, 20000], "investing_cash_flow": [-5000, -6000],
                                            "financing_cash_flow": [-3000, -4000], "free_cash_flow": [13000, 14000]},
                    "key_ratios": {}, # Let FAA calculate these
                    "dcf_assumptions": { # Generic assumptions
                        "fcf_projection_years_total": 5, "initial_high_growth_period_years": 2,
                        "initial_high_growth_rate": 0.05, "stable_growth_rate": 0.02,
                        "discount_rate": 0.10, "terminal_growth_rate_perpetuity": 0.02
                    },
                    "market_data": {"share_price": 10.00, "shares_outstanding": 1000000,
                                    "annual_debt_service_placeholder": "1000",
                                    "payment_history_placeholder": "Unknown",
                                    "interest_capitalization_placeholder": "Unknown"}
                },
                "qualitative_company_info": {
                    "management_assessment": "N/A", "competitive_advantages": "N/A",
                    "business_model_strength": "N/A",
                    "revenue_cashflow_stability_notes_placeholder": "Data not available for detailed assessment.",
                    "financial_deterioration_notes_placeholder": "Data not available for detailed assessment."
                },
                "industry_data_context": {"outlook": "N/A"},
                "economic_data_context": {"overall_outlook": "N/A"},
                "collateral_and_debt_details": {"loan_to_value_ratio": None, "collateral_type": "N/A", "other_credit_enhancements": "N/A"}
            }
            return {"status": "success", "data": generic_data_package, "message": f"Provided generic placeholder data for {company_id}."}
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

        else: # For any other company_id
            self.logger.info(f"Returning generic placeholder data for company_id: {company_id}, data_type: {data_type}")
            generic_data_package = {
                "company_info": {"name": f"{company_id} (Generic Data)", "ticker": company_id, "industry_sector": "N/A", "country": "N/A"},
                "financial_data_detailed": {
                    "income_statement": {"revenue": [1000000, 1100000], "net_income": [10000, 12000], "ebitda": [15000, 17000]},
                    "balance_sheet": {"total_assets": [200000, 210000], "total_liabilities": [80000, 85000],
                                      "shareholders_equity": [120000, 125000], "cash_and_equivalents": [20000, 25000],
                                      "short_term_debt": [5000,5000], "long_term_debt": [50000,45000]},
                    "cash_flow_statement": {"operating_cash_flow": [18000, 20000], "investing_cash_flow": [-5000, -6000],
                                            "financing_cash_flow": [-3000, -4000], "free_cash_flow": [13000, 14000]},
                    "key_ratios": {}, # Let FAA calculate these
                    "dcf_assumptions": { # Generic assumptions
                        "fcf_projection_years_total": 5, "initial_high_growth_period_years": 2,
                        "initial_high_growth_rate": 0.05, "stable_growth_rate": 0.02,
                        "discount_rate": 0.10, "terminal_growth_rate_perpetuity": 0.02
                    },
                    "market_data": {"share_price": 10.00, "shares_outstanding": 1000000,
                                    "annual_debt_service_placeholder": "1000",
                                    "payment_history_placeholder": "Unknown",
                                    "interest_capitalization_placeholder": "Unknown"}
                },
                "qualitative_company_info": {
                    "management_assessment": "N/A", "competitive_advantages": "N/A",
                    "business_model_strength": "N/A",
                    "revenue_cashflow_stability_notes_placeholder": "Data not available for detailed assessment.",
                    "financial_deterioration_notes_placeholder": "Data not available for detailed assessment."
                },
                "industry_data_context": {"outlook": "N/A"},
                "economic_data_context": {"overall_outlook": "N/A"},
                "collateral_and_debt_details": {"loan_to_value_ratio": None, "collateral_type": "N/A", "other_credit_enhancements": "N/A"}
            }
            return {"status": "success", "data": generic_data_package, "message": f"Provided generic placeholder data for {company_id}."}
