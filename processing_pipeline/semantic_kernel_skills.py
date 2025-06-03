# processing_pipeline/semantic_kernel_skills.py
import json
import os 
import re
from typing import Dict, List, Any, Optional 
import logging

# from cacm_adk_core.semantic_kernel_adapter import KernelService # Not directly used by skills if kernel passed in
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function # Correct decorator import
from semantic_kernel import Kernel

class SK_EntityInfoExtractorSkill:
    def extract_entity_info(self, sectioned_data: dict) -> dict:
        # print("Placeholder: SK_EntityInfoExtractorSkill.extract_entity_info called.")
        text_to_search = sectioned_data.get("ITEM_1_BUSINESS", "")
        if not text_to_search: text_to_search = sectioned_data.get("__UNMATCHED_PREAMBLE__", "")
        company_name = "N/A"; state_of_incorporation = "N/A"; phone_number = "N/A"
        name_match = re.search(r"([A-Z][A-Z\s.&',-]{5,}\b(?:CORPORATION|INC\.|INCORPORATED|LLC|L\.L\.C\.|LIMITED|PLC|CORP\.?))", text_to_search, re.IGNORECASE)
        if name_match: company_name = re.sub(r"[,.]?\s*(CORPORATION|INC\.|INCORPORATED|LLC|L\.L\.C\.|LIMITED|PLC|CORP\.)$", "", name_match.group(1).strip(), flags=re.IGNORECASE).strip()
        incorp_match = re.search(r"incorporated in the State of (\w+)", text_to_search, re.IGNORECASE)
        if not incorp_match: incorp_match = re.search(r"State of Incorporation[:\s]+(\w+)", text_to_search, re.IGNORECASE)
        if not incorp_match: 
            incorp_match_cand = re.search(r"a\s+(\w+)\s+corporation", text_to_search, re.IGNORECASE)
            if incorp_match_cand and incorp_match_cand.group(1).lower() not in ["delaware", "nevada", "washington", "california", "new york"]: incorp_match_cand = None
            incorp_match = incorp_match_cand
        if incorp_match: state_of_incorporation = incorp_match.group(1).strip()
        phone_match = re.search(r"(\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4}|\d{3}\.\d{3}\.\d{4})", text_to_search)
        if phone_match: phone_number = phone_match.group(1)
        return {"company_name": company_name, "state_of_incorporation": state_of_incorporation, "phone_number": phone_number}

class SK_FinancialDataExtractorSkill:
    def extract_key_financials(self, sectioned_data: dict, target_period_hint: str = "2024") -> dict:
        # print(f"Placeholder: SK_FinancialDataExtractorSkill.extract_key_financials called for period hint: {target_period_hint}.")
        financials_text = sectioned_data.get("ITEM_8_FINANCIAL_STATEMENTS", "") or sectioned_data.get("ITEM_8_FINANCIAL_STATEMENTS_AND_SUPPLEMENTARY_DATA","")
        extracted_data = {}
        key_metrics = {
            f"Total_Revenue_{target_period_hint}": r"(?:Total\s+Revenues|Revenues|Total\s+Revenue|Sales)[\s:]*([\$0-9,.]+)",
            f"Net_Income_{target_period_hint}": r"Net\s+Income(?:/(Loss))?[\s:]*([\$0-9,.]+)"}
        for key, pattern in key_metrics.items():
            match = re.search(pattern, financials_text, re.IGNORECASE | re.MULTILINE)
            if match:
                value_str = match.group(len(match.groups())).replace('$', '').replace(',', '')
                try: extracted_data[key] = float(value_str)
                except ValueError: extracted_data[key] = f"N/A (unparseable: {value_str})"
            else: extracted_data[key] = "N/A (not found)"
        return extracted_data

class SK_MDNA_SummarizerSkill:
    def __init__(self):
        try:
            # This import is here to avoid circular dependency if KernelService also imports skills from here at module level
            from cacm_adk_core.semantic_kernel_adapter import KernelService 
            self.kernel_service = KernelService()
            self.kernel = self.kernel_service.get_kernel()
        except Exception as e: 
            logging.getLogger(self.__class__.__name__).warning(f"Could not get KernelService or kernel during __init__: {e}. Placeholder mode will be active.")
            self.kernel = None
            self.kernel_service = None
            
        self.use_placeholder = True 
        self.summarize_function = None 

        if self.kernel:
            try:
                # Check for the specific service type class
                if self.kernel.get_service(OpenAIChatCompletion):
                    self.use_placeholder = False
                    logging.info("SK_MDNA_SummarizerSkill: Chat Completion service found. Semantic function will be used if available.")
                    self.summarization_prompt = """
Summarize the following text in approximately {{max_sentences}} sentences.
Focus on the key points and main ideas. Text to summarize: {{$input}} Summary:"""
                    self.summarize_function = self.kernel.create_semantic_function(
                        self.summarization_prompt, max_tokens=500, temperature=0.2, top_p=0.5
                    )
                    logging.info("SK_MDNA_SummarizerSkill: SEMANTIC summarize_function created for LLM calls.")
                else:
                    logging.warning("SK_MDNA_SummarizerSkill: Kernel available, but no Chat Completion service configured. Will use NATIVE placeholder logic.")
            except sk.exceptions.KernelServiceNotFoundError:
                logging.warning("SK_MDNA_SummarizerSkill: Chat Completion service not found. Will use NATIVE placeholder logic.")
            except Exception as e: 
                logging.error(f"SK_MDNA_SummarizerSkill: Error setting up semantic function: {e}. Will use NATIVE placeholder logic.")
                self.use_placeholder = True 
        else:
            logging.warning("SK_MDNA_SummarizerSkill: Kernel instance not available. Will use NATIVE placeholder logic.")

    @kernel_function(description="A simple test echo function.", name="test_echo") # Using correct decorator
    def test_echo(self, text_to_echo: str) -> str:
        logging.info(f"SK_MDNA_SummarizerSkill.test_echo called with: {text_to_echo}")
        return f"Echo from SK_MDNA_SummarizerSkill: {text_to_echo}"

    @kernel_function( # Using correct decorator
        description="Summarizes a section of text using placeholder or (if configured) LLM logic.",
        name="summarize_section"
    )
    async def summarize_section(self, input: str, max_sentences: str = "7") -> str:
        if not input: return "Input text is empty. Cannot summarize."

        if self.use_placeholder or not self.summarize_function:
            logging.warning("SK_MDNA_SummarizerSkill.summarize_section: Using NATIVE placeholder (generic string).")
            return "[Placeholder LLM Summary: Content would be generated here based on provided input.]"
        
        try:
            logging.info(f"SK_MDNA_SummarizerSkill.summarize_section: Invoking SEMANTIC function (max_sentences: {max_sentences}).")
            kernel_args = KernelArguments(input=input, max_sentences=max_sentences) 
            result = await self.kernel.invoke(self.summarize_function, kernel_args)
            summary = str(result).strip()
            logging.info("SK_MDNA_SummarizerSkill.summarize_section: SEMANTIC summarization successful.")
            return summary
        except Exception as e:
            logging.error(f"SK_MDNA_SummarizerSkill.summarize_section: Error during SEMANTIC function invocation: {e}. Falling back to NATIVE placeholder.")
            return "[Placeholder LLM Summary: Error during semantic function invocation. Native placeholder returned.]"

class SK_RiskAnalysisSkill:
    def identify_risk_keywords_sentences(self, section_text: str) -> list:
        if not section_text: return []
        keywords = ["risk", "compete", "challenging", "loss", "adverse"]
        sentences = re.split(r'(?<=[.!?])\s+', section_text.strip())
        risk_sentences = set()
        for sentence in sentences:
            for keyword in keywords:
                if keyword in sentence.lower(): risk_sentences.add(sentence.strip()); break
        return list(risk_sentences)

class CustomReportingSkills:
    def __init__(self, kernel: Optional[Kernel] = None, logger_instance: Optional[logging.Logger] = None): # Renamed logger to logger_instance
        self.kernel = kernel
        self.logger = logger_instance or logging.getLogger(self.__class__.__name__)
        self.use_placeholder = True 

        if self.kernel:
            try:
                # Check for the specific service type class
                if self.kernel.get_service(OpenAIChatCompletion):
                    self.use_placeholder = False
                    self.logger.info("CustomReportingSkills: Chat Completion service found. LLM calls will be attempted if skill logic includes them.")
                else:
                    self.logger.warning("CustomReportingSkills: Kernel available, but no Chat Completion service. Will use placeholders.")
            except sk.exceptions.KernelServiceNotFoundError:
                self.logger.warning("CustomReportingSkills: Chat Completion service not found in Kernel. Will use placeholders.")
            except Exception as e:
                self.logger.error(f"CustomReportingSkills: Error checking for AI services: {e}. Will use placeholders.")
        else:
            self.logger.warning("CustomReportingSkills: Kernel not provided. Will use placeholders.")

    @kernel_function(description="Generates a placeholder financial performance summary.", name="generate_financial_summary") # Using correct decorator
    async def generate_financial_summary(self, financial_data: Dict[str, Any]) -> str:
        self.logger.info(f"CustomReportingSkills.generate_financial_summary called. Placeholder mode: {self.use_placeholder}")
        if self.use_placeholder:
            self.logger.info("Conceptual LLM call for generate_financial_summary: Would construct a prompt with financial_data and ask for a narrative summary.")
        
        if not isinstance(financial_data, dict): financial_data = {"error": "Invalid input, expected dict."}
        rev_y1 = financial_data.get("revenue_y1", "N/A"); rev_y2 = financial_data.get("revenue_y2", "N/A")
        ni_y1 = financial_data.get("net_income_y1", "N/A"); ni_y2 = financial_data.get("net_income_y2", "N/A")
        currency = financial_data.get("currency", ""); period_y1 = financial_data.get("period_y1_label", "Y1"); period_y2 = financial_data.get("period_y2_label", "Y2")
        return (f"[LLM Placeholder: Financial Performance Summary. Inputs: "
                f"{period_y1} Revenue {rev_y1} {currency}, {period_y2} Revenue {rev_y2} {currency}; "
                f"{period_y1} Net Income {ni_y1} {currency}, {period_y2} Net Income {ni_y2} {currency}. "
                f"Actual LLM output would be here.]")

    @kernel_function(description="Generates a placeholder key risks summary.", name="generate_key_risks_summary") # Using correct decorator
    async def generate_key_risks_summary(self, risk_factors_text: str) -> str:
        self.logger.info(f"CustomReportingSkills.generate_key_risks_summary called. Placeholder mode: {self.use_placeholder}")
        if self.use_placeholder:
            self.logger.info("Conceptual LLM call for generate_key_risks_summary: Would construct a prompt with risk_factors_text.")
        first_50_chars = risk_factors_text[:50] if isinstance(risk_factors_text, str) else "N/A (Invalid risk text)"
        return (f"[LLM Placeholder: Key Risks Summary. Input text started with: '{first_50_chars}...'. "
                f"Actual LLM output would be here.]")

    @kernel_function(description="Generates a placeholder overall assessment.", name="generate_overall_assessment") # Using correct decorator
    async def generate_overall_assessment(self, ratios_json_str: str, financial_summary_text: str, key_risks_summary_text: str) -> str:
        self.logger.info(f"CustomReportingSkills.generate_overall_assessment called. Placeholder mode: {self.use_placeholder}")
        if self.use_placeholder:
             self.logger.info("Conceptual LLM call for generate_overall_assessment: Would use ratios, financial summary, and risk summary to synthesize an assessment.")
        current_ratio_val = "N/A"
        if isinstance(ratios_json_str, str):
            try: ratios_data = json.loads(ratios_json_str); current_ratio_val = ratios_data.get("current_ratio", "N/A (key missing)")
            except json.JSONDecodeError: current_ratio_val = "N/A (error parsing ratios JSON)"
        else: current_ratio_val = "N/A (invalid ratios input type)"
        fin_sum_snippet = financial_summary_text[:30] if isinstance(financial_summary_text, str) else "N/A"
        risk_sum_snippet = key_risks_summary_text[:30] if isinstance(key_risks_summary_text, str) else "N/A"
        return (f"[LLM Placeholder: Overall Assessment. Based on Ratios (e.g., Current Ratio: {current_ratio_val}), "
                f"Financial Summary ('{fin_sum_snippet}...'), and Risk Summary ('{risk_sum_snippet}...'). "
                f"Actual LLM output would be here.]")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO) # Ensure logging is configured for __main__
    print("\n--- Testing Semantic Kernel Placeholder Skills ---")
    async def main():
        summarizer = SK_MDNA_SummarizerSkill() 
        summarizer.use_placeholder = True 
        summary1 = await summarizer.summarize_section(input="This is a long text that needs summarization.", max_sentences="2")
        print(f"Forced Placeholder Summary: {summary1}")
        echo_text = summarizer.test_echo(text_to_echo="Hello Echo from MDNA Skill")
        print(f"Echo Test (MDNA Skill): {echo_text}")

        custom_reporter = CustomReportingSkills(kernel=None, logger_instance=logging.getLogger("TestCustomReporter"))
        print(f"\n--- CustomReportingSkills (Placeholder Mode: {custom_reporter.use_placeholder}) ---")
        fin_sum = await custom_reporter.generate_financial_summary(
            financial_data={"revenue_y1": 1000, "net_income_y1": 100, "currency": "USD", "period_y1_label": "FY2022"}
        )
        print(f"Custom Financial Summary: {fin_sum}")
        risk_sum = await custom_reporter.generate_key_risks_summary(
            risk_factors_text="Significant market competition and dependency on key suppliers are major risks."
        )
        print(f"Custom Risk Summary: {risk_sum}")
        overall_as = await custom_reporter.generate_overall_assessment(
            ratios_json_str=json.dumps({"current_ratio": 1.5, "debt_to_equity": 0.8}),
            financial_summary_text=fin_sum, key_risks_summary_text=risk_sum
        )
        print(f"Custom Overall Assessment: {overall_as}")
    if os.name == 'nt': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) # For Windows compatibility
    asyncio.run(main())
