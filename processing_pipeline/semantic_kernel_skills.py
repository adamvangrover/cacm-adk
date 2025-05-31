# processing_pipeline/semantic_kernel_skills.py
import json
import re
from typing import Dict, List, Any

class SK_EntityInfoExtractorSkill:
    def extract_entity_info(self, sectioned_data: dict) -> dict:
        """
        Placeholder for a Semantic Kernel skill to extract key entity information.
        Ideally, this skill would use an LLM via Semantic Kernel to understand and
        extract key entity information (name, HQ, incorporation state, key identifiers)
        from early sections of a financial filing (e.g., Business section or preamble).

        Args:
            sectioned_data (dict): Dictionary loaded from the sectioned JSON
                                   (e.g., MSFT_FY24Q4_10K_sectioned.json).

        Returns:
            dict: Extracted entity information like
                  {"company_name": "...", "state_of_incorporation": "...", "phone_number": "..."}
                  with "N/A" for unfound items.
        """
        print("Placeholder: SK_EntityInfoExtractorSkill.extract_entity_info called.")

        text_to_search = sectioned_data.get("ITEM_1_BUSINESS", "")
        if not text_to_search:
            text_to_search = sectioned_data.get("__UNMATCHED_PREAMBLE__", "")

        company_name = "N/A"
        state_of_incorporation = "N/A"
        phone_number = "N/A"

        # Crude company name extraction (example: looking for all caps, common terms)
        # This is highly unreliable for real documents.
        name_match = re.search(r"([A-Z][A-Z\s.&',-]{5,}\b(?:CORPORATION|INC\.|INCORPORATED|LLC|L\.L\.C\.|LIMITED|PLC|CORP\.?))", text_to_search, re.IGNORECASE)
        if name_match:
            company_name = name_match.group(1).strip()
            # Further clean common suffixes if needed, e.g. remove ", INC." if it's part of the captured group
            company_name = re.sub(r"[,.]?\s*(CORPORATION|INC\.|INCORPORATED|LLC|L\.L\.C\.|LIMITED|PLC|CORP\.)$", "", company_name, flags=re.IGNORECASE).strip()


        # Crude state of incorporation
        incorp_match = re.search(r"incorporated in the State of (\w+)", text_to_search, re.IGNORECASE)
        if not incorp_match:
            incorp_match = re.search(r"State of Incorporation[:\s]+(\w+)", text_to_search, re.IGNORECASE)
        if not incorp_match: # Common pattern for Delaware
            incorp_match = re.search(r"a\s+(\w+)\s+corporation", text_to_search, re.IGNORECASE)
            if incorp_match and incorp_match.group(1).lower() not in ["delaware", "nevada", "washington", "california", "new york"]: # filter out generic "a general corporation"
                incorp_match = None


        if incorp_match:
            state_of_incorporation = incorp_match.group(1).strip()

        # Crude phone number
        phone_match = re.search(r"(\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4}|\d{3}\.\d{3}\.\d{4})", text_to_search)
        if phone_match:
            phone_number = phone_match.group(1)

        return {
            "company_name": company_name,
            "state_of_incorporation": state_of_incorporation,
            "phone_number": phone_number
        }

class SK_FinancialDataExtractorSkill:
    def extract_key_financials(self, sectioned_data: dict, target_period_hint: str = "2024") -> dict:
        """
        Placeholder for a Semantic Kernel skill to extract key financial figures.
        Ideally, this skill would use an LLM via Semantic Kernel, possibly with table
        parsing capabilities or targeted prompts, to accurately extract key financial
        figures for specified periods from the financial statements section (ITEM 8).
        It would handle variations in table formats, line item naming, and value scaling (e.g., in thousands).

        Args:
            sectioned_data (dict): Dictionary loaded from the sectioned JSON.
            target_period_hint (str): A hint for the most recent year/period to target.

        Returns:
            dict: Extracted financials like {"Total_Revenue_YYYY": 12345, ...}
                  with "N/A" or 0 for unfound items.
        """
        print(f"Placeholder: SK_FinancialDataExtractorSkill.extract_key_financials called for period hint: {target_period_hint}.")

        financials_text = sectioned_data.get("ITEM_8_FINANCIAL_STATEMENTS", "")
        if not financials_text:
            financials_text = sectioned_data.get("ITEM_8_FINANCIAL_STATEMENTS_AND_SUPPLEMENTARY_DATA","") # Try longer key

        extracted_data = {}

        # Extremely crude and error-prone keyword/regex searching for demonstration
        # This will likely NOT work well on real, complex documents.
        key_metrics = {
            f"Total_Revenue_{target_period_hint}": r"(?:Total\s+Revenues|Revenues|Total\s+Revenue|Sales)[\s:]*([\$0-9,.]+)",
            f"Net_Income_{target_period_hint}": r"Net\s+Income(?:/(Loss))?[\s:]*([\$0-9,.]+)",
            f"Total_Assets_{target_period_hint}": r"Total\s+Assets[\s:]*([\$0-9,.]+)",
            f"Total_Current_Assets_{target_period_hint}": r"Total\s+Current\s+Assets[\s:]*([\$0-9,.]+)",
            f"Total_Current_Liabilities_{target_period_hint}": r"Total\s+Current\s+Liabilities[\s:]*([\$0-9,.]+)",
            f"Total_Liabilities_{target_period_hint}": r"Total\s+Liabilities[\s:]*([\$0-9,.]+)",
            f"Operating_Cash_Flow_{target_period_hint}": r"(?:Net\s+Cash\s+(?:provided\s+by|from)\s+Operating\s+Activities|Cash\s+Flow\s+from\s+Operations)[\s:]*([\$0-9,.]+)"
        }

        for key, pattern in key_metrics.items():
            match = re.search(pattern, financials_text, re.IGNORECASE | re.MULTILINE)
            if match:
                value_str = match.group(len(match.groups())).replace('$', '').replace(',', '')
                try:
                    extracted_data[key] = float(value_str)
                except ValueError:
                    extracted_data[key] = f"N/A (unparseable: {value_str})"
            else:
                extracted_data[key] = "N/A (not found)"

        return extracted_data

class SK_MDNA_SummarizerSkill:
    def summarize_section(self, section_text: str, max_sentences: int = 7) -> str:
        """
        Placeholder for a Semantic Kernel skill for text summarization.
        Ideally, this skill would use a powerful LLM via Semantic Kernel with a
        sophisticated summarization prompt to generate a concise, coherent, and
        contextually relevant summary of the provided text section (e.g., MD&A).

        Args:
            section_text (str): The text of the document section to summarize.
            max_sentences (int): The target maximum number of sentences for the summary.

        Returns:
            str: The generated summary string.
        """
        print(f"Placeholder: SK_MDNA_SummarizerSkill.summarize_section called, aiming for max {max_sentences} sentences.")
        if not section_text:
            return "Input text is empty. Cannot summarize."

        # Simple summarization: take the first N sentences.
        # This is a very basic placeholder.
        sentences = re.split(r'(?<=[.!?])\s+', section_text.strip()) # Split by common sentence endings
        summary = ' '.join(sentences[:max_sentences])

        if len(sentences) > max_sentences:
            summary += "..." # Indicate truncation

        return summary

class SK_RiskAnalysisSkill:
    def identify_risk_keywords_sentences(self, section_text: str) -> list:
        """
        Placeholder for a Semantic Kernel skill for risk factor analysis.
        Ideally, this skill would use embeddings and an LLM via Semantic Kernel to
        semantically identify, categorize, and even summarize key risk factors from
        the "Risk Factors" section, going beyond simple keyword matching.

        Args:
            section_text (str): Text of the "Risk Factors" section.

        Returns:
            list: A list of unique sentences identified as potentially containing risk information.
        """
        print("Placeholder: SK_RiskAnalysisSkill.identify_risk_keywords_sentences called.")
        if not section_text:
            return []

        keywords = [
            "risk", "compete", "challenging", "loss", "adverse", "depend",
            "unable", "failure", "cybersecurity", "economic conditions", "regulatory",
            "volatility", "uncertainty", "disruption", "litigation"
        ]

        sentences = re.split(r'(?<=[.!?])\s+', section_text.strip())
        risk_sentences = set() # Use a set to store unique sentences

        for sentence in sentences:
            for keyword in keywords:
                if keyword in sentence.lower(): # Case-insensitive keyword search
                    risk_sentences.add(sentence.strip())
                    break # Move to next sentence once a keyword is found in current one

        return list(risk_sentences)

if __name__ == '__main__':
    # Example usage of the placeholder skills
    print("\n--- Testing Semantic Kernel Placeholder Skills ---")

    # Dummy sectioned data (replace with actual loaded data for real testing)
    dummy_sections = {
        "__UNMATCHED_PREAMBLE__": "XYZ CORPORATION. Located in Delaware. Phone: (123) 456-7890.",
        "ITEM_1_BUSINESS": "XYZ CORPORATION is a company incorporated in the State of Delaware. Our main business is making widgets. We face competition.",
        "ITEM_1A_RISK_FACTORS": "We face significant competition. Economic conditions could adversely affect our sales. Failure to innovate poses a risk. Cybersecurity is a major concern. Regulatory changes may impact us. Market volatility is a risk.",
        "ITEM_7_MDNA": "Revenue increased by 10%. This was good. However, costs also increased. This was due to supply chain disruptions. We are optimistic about future growth. We need to manage our expenses carefully. The economic outlook presents some uncertainty but also opportunities. Our strategy is sound.",
        "ITEM_8_FINANCIAL_STATEMENTS": "Financial Statements. Total Revenues: $1,000,000. Net Income: $100,000 for 2024. Total Assets $5,000,000. Total Current Assets $2,000,000. Total Current Liabilities $800,000. Total Liabilities $2,500,000. Net Cash from Operating Activities $150,000."
    }

    # Entity Info Extractor
    entity_extractor = SK_EntityInfoExtractorSkill()
    entity_info = entity_extractor.extract_entity_info(dummy_sections)
    print(f"\nExtracted Entity Info:\n{json.dumps(entity_info, indent=2)}")

    # Financial Data Extractor
    financial_extractor = SK_FinancialDataExtractorSkill()
    financials = financial_extractor.extract_key_financials(dummy_sections, target_period_hint="2024")
    print(f"\nExtracted Financials (for 2024 hint):\n{json.dumps(financials, indent=2)}")

    # MD&A Summarizer
    mdna_summarizer = SK_MDNA_SummarizerSkill()
    mdna_summary = mdna_summarizer.summarize_section(dummy_sections.get("ITEM_7_MDNA", ""), max_sentences=3)
    print(f"\nMD&A Summary (3 sentences):\n{mdna_summary}")

    # Risk Analysis
    risk_analyzer = SK_RiskAnalysisSkill()
    risk_highlights = risk_analyzer.identify_risk_keywords_sentences(dummy_sections.get("ITEM_1A_RISK_FACTORS", ""))
    print(f"\nRisk Factor Sentences Identified ({len(risk_highlights)}):")
    for sentence in risk_highlights:
        print(f"  - {sentence}")
