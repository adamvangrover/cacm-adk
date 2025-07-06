# cacm_adk_core/agents/catalyst_agent.py

import json
import requests
from datetime import datetime
import logging


class CatalystAgent:
    def __init__(self, config_path="catalyst_config.json"):
        self.config = self.load_config(config_path)
        self.client_data_url = self.config["client_data_url"]
        self.market_data_url = self.config["market_data_url"]
        self.company_financials_url = self.config["company_financials_url"]
        self.industry_reports_url = self.config["industry_reports_url"]
        self.bank_product_data_url = self.config["bank_product_data_url"]
        self.knowledge_graph_url = self.config["knowledge_graph_url"]
        self.financial_modeling_url = self.config["financial_modeling_url"]
        self.reporting_url = self.config["reporting_url"]
        self.nlp_url = self.config["nlp_url"]
        self.client_data = {}
        self.market_data = {}
        self.company_financials = {}
        self.industry_reports = {}
        self.bank_product_data = {}
        self.logger = self.setup_logger()

    def setup_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger

    def load_config(self, config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Config file not found: {config_path}")
            return {}
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON format in config file: {config_path}")
            return {}

    def fetch_data(self, url, params=None):
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching data from {url}: {e}")
            return None

    def load_client_data(self, client_id):
        client_data = self.fetch_data(f"{self.client_data_url}/{client_id}")
        if client_data:
            self.client_data = client_data
            self.logger.info(f"Loaded client data for {client_id}")
        else:
            self.logger.warning(f"Failed to load client data for {client_id}")
        return self.client_data

    def load_market_data(self, date=None):
        market_data = self.fetch_data(self.market_data_url, params={"date": date})
        if market_data:
            self.market_data = market_data
            self.logger.info("Loaded market data")
        else:
            self.logger.warning("Failed to load market data")
        return self.market_data

    def load_company_financials(self, company_id):
        company_financials = self.fetch_data(
            f"{self.company_financials_url}/{company_id}"
        )
        if company_financials:
            self.company_financials = company_financials
            self.logger.info(f"Loaded company financials for {company_id}")
        else:
            self.logger.warning(f"Failed to load company financials for {company_id}")
        return self.company_financials

    def load_industry_reports(self, industry):
        industry_reports = self.fetch_data(
            self.industry_reports_url, params={"industry": industry}
        )
        if industry_reports:
            self.industry_reports = industry_reports
            self.logger.info(f"Loaded industry reports for {industry}")
        else:
            self.logger.warning(f"Failed to load industry reports for {industry}")
        return self.industry_reports

    def load_bank_product_data(self):
        bank_product_data = self.fetch_data(self.bank_product_data_url)
        if bank_product_data:
            self.bank_product_data = bank_product_data
            self.logger.info("Loaded bank product data")
        else:
            self.logger.warning("Failed to load bank product data")
        return self.bank_product_data

    def analyze_news_sentiment(self):
        # Placeholder: Call NLP service to analyze news sentiment
        sentiment_data = self.fetch_data(
            self.nlp_url + "/sentiment", params={"text": "news"}
        )
        if sentiment_data and "sentiment" in sentiment_data:
            return sentiment_data["sentiment"]
        else:
            self.logger.warning("Failed to analyze news sentiment")
            return 0.5  # Neutral sentiment as default

    def get_client_connections(self):
        # Placeholder: Call Knowledge Graph to get client connections
        connections = self.fetch_data(
            self.knowledge_graph_url + "/connections",
            params={"client_id": self.client_data.get("client_id")},
        )
        if connections:
            return connections
        else:
            self.logger.warning("Failed to get client connections")
            return []

    def get_client_needs(self):
        # Placeholder: Extract client needs from client data
        return {"needs": self.client_data.get("investment_goals")}

    def recommend_products(self, client_needs):
        # Placeholder: Recommend products based on client needs
        if client_needs.get("needs") == "growth":
            return [{"product": "leveraged loan", "rationale": "Growth financing"}]
        else:
            return []

    def generate_report_summary(
        self, opportunities, client_data, deal_structure, recommended_products
    ):
        # Placeholder: Call NLP service to generate report summary
        summary_data = self.fetch_data(
            self.nlp_url + "/summary",
            params={
                "data": json.dumps(
                    {
                        "opportunities": opportunities,
                        "client_data": client_data,
                        "deal_structure": deal_structure,
                        "recommended_products": recommended_products,
                    }
                )
            },
        )
        if summary_data and "summary" in summary_data:
            return summary_data["summary"]
        else:
            self.logger.warning("Failed to generate report summary")
            return "Report Summary Unavailable."

    def identify_opportunities(self):
        news_sentiment = self.analyze_news_sentiment()
        client_connections = self.get_client_connections()
        if news_sentiment > 0.7 and client_connections:
            return [
                {
                    "opportunity_type": "strategic_alliance",
                    "rationale": "Positive market sentiment and strong client connections",
                }
            ]
        return []

    def structure_deal(self, opportunity):
        client_needs = self.get_client_needs()
        product_recommendation = self.recommend_products(client_needs)
        return {
            "opportunity": opportunity,
            "solution": product_recommendation,
            "negotiation_strategy": "relationship-focused",
        }

    def generate_report(
        self, opportunities, client_data, deal_structure, recommended_products
    ):
        report_summary = self.generate_report_summary(
            opportunities, client_data, deal_structure, recommended_products
        )
        return {
            "summary": report_summary,
            "details": {
                "opportunities": opportunities,
                "client_data": client_data,
                "deal_structure": deal_structure,
                "recommended_products": recommended_products,
            },
        }

    def run(self, client_id, company_id, industry):
        self.load_client_data(client_id)
        self.load_market_data()
        self.load_company_financials(company_id)
        self.load_industry_reports(industry)
        self.load_bank_product_data()

        opportunities = self.identify_opportunities()
        if opportunities:
            deal_structure = self.structure_deal(opportunities[0])
            recommended_products = deal_structure.get("solution", [])
            report = self.generate_report(
                opportunities, self.client_data, deal_structure, recommended_products
            )
            return report
        else:
            return {"message": "No opportunities identified."}


if __name__ == "__main__":
    agent = CatalystAgent()
    result = agent.run("client123", "company456", "tech")
    print(json.dumps(result, indent=4))
