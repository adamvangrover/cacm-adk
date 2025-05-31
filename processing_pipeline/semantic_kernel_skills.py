# processing_pipeline/semantic_kernel_skills.py
import json
import os # <--- Added import
import re
from typing import Dict, List, Any
import logging

from cacm_adk_core.semantic_kernel_adapter import KernelService
import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments

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
    def __init__(self):
        self.kernel_service = KernelService()
        self.kernel = self.kernel_service.get_kernel()
        self.use_placeholder = True # Default to placeholder

        if self.kernel:
            try:
                # Attempt to get a chat service to see if one is configured
                chat_service = self.kernel.get_service(type="chat-completion")
                if chat_service:
                    self.use_placeholder = False
                    logging.info("SK_MDNA_SummarizerSkill: OpenAI Chat Completion service found. Kernel based summarization will be attempted.")
                else:
                    # This else might be redundant if get_service raises an error when not found,
                    # but kept for clarity if get_service can return None without error.
                    logging.warning("SK_MDNA_SummarizerSkill: Kernel obtained, but no Chat Completion service configured (e.g. API key missing). Summarization will use placeholder logic.")
            except sk.exceptions.KernelServiceNotFoundError: # Corrected exception type
                logging.warning("SK_MDNA_SummarizerSkill: Chat Completion service not found in Kernel. Summarization will use placeholder logic.")
            except Exception as e:
                logging.error(f"SK_MDNA_SummarizerSkill: Error checking for AI services: {e}. Summarization will use placeholder logic.")
        else:
            logging.error("SK_MDNA_SummarizerSkill: Kernel instance not available. Summarization will use placeholder logic.")

        if not self.use_placeholder:
            # Define a simple summarization prompt
            self.summarization_prompt = """
Summarize the following text in approximately {{max_sentences}} sentences.
Focus on the key points and main ideas.

Text to summarize:
{{$input}}

Summary:
"""
            try:
                self.summarize_function = self.kernel.create_semantic_function(
                    self.summarization_prompt,
                    max_tokens=500, # Adjust as needed
                    temperature=0.2,
                    top_p=0.5
                )
                logging.info("SK_MDNA_SummarizerSkill: Semantic function for summarization created.")
            except Exception as e:
                logging.error(f"SK_MDNA_SummarizerSkill: Error creating semantic function: {e}")
                self.use_placeholder = True # Fallback if function creation fails
        else:
            self.summarize_function = None # Ensure it's defined even if using placeholder


    async def summarize_section_async(self, section_text: str, max_sentences: int = 7) -> str:
        """
        Summarizes the provided text section using Semantic Kernel.
        Falls back to placeholder logic if the kernel is not available or fails.
        """
        if not section_text:
            return "Input text is empty. Cannot summarize."

        if self.use_placeholder or not self.summarize_function:
            logging.warning("SK_MDNA_SummarizerSkill: Using placeholder summarization logic as kernel/LLM service is not fully available.")
            # Return a generic placeholder string, ignoring section_text and max_sentences for this path
            return "[Placeholder LLM Summary: Content would be generated here based on provided input.]"

        try:
            logging.info(f"SK_MDNA_SummarizerSkill: Invoking semantic function for summarization (max_sentences: {max_sentences}).")
            kernel_args = KernelArguments(input=section_text, max_sentences=str(max_sentences))

            # Ensure the kernel and service are available before invoking
            if not self.kernel.get_service(): # Check if any text completion service is configured
                 logging.error("SK_MDNA_SummarizerSkill: No AI service configured in the kernel. Cannot invoke function.")
                 # Fallback to placeholder or return error
                 sentences = re.split(r'(?<=[.!?])\s+', section_text.strip())
                 summary = ' '.join(sentences[:max_sentences])
                 if len(sentences) > max_sentences:
                     summary += "..."
                 return f"Error: Semantic Kernel AI service not configured. Placeholder summary: {summary}"

            result = await self.kernel.invoke(self.summarize_function, kernel_args)

            summary = str(result).strip()
            # Post-processing: ensure it's roughly the number of sentences requested, if needed.
            # For now, we directly return the LLM's output.
            logging.info("SK_MDNA_SummarizerSkill: Summarization successful.")
            return summary
        except Exception as e:
            logging.error(f"SK_MDNA_SummarizerSkill: Error during Semantic Kernel invocation: {e}")
            # Fallback to placeholder logic in case of error
            logging.warning(f"SK_MDNA_SummarizerSkill: Error during kernel invocation ({e}). Falling back to generic placeholder.")
            return "[Placeholder LLM Summary: Error during kernel invocation. Content would be generated here.]"

    # Keep a synchronous version for compatibility if needed, or refactor calling code to be async
    def summarize_section(self, section_text: str, max_sentences: int = 7) -> str:
        """
        Synchronous wrapper for summarize_section_async.
        This is not ideal for production with async components but can serve as a bridge.
        """
        if hasattr(self.kernel, 'run_async'): # run_async is a common pattern for SK event loops
            # This is a simplified way to run an async method from sync code.
            # For robust applications, manage an asyncio event loop properly.
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If an event loop is already running, create a task
                    # This might happen in FastAPI contexts or similar.
                    # Note: This approach has limitations and might not always work as expected
                    # depending on the outer event loop management.
                    # For truly synchronous calls in an async environment, consider `async_to_sync` from `asgiref.sync`
                    # or ensure the calling context can `await` the async version.
                    # For this subtask, we'll log a warning and proceed with a new temp loop if needed,
                    # or just call the async function directly if no loop is running.
                    logging.warning("SK_MDNA_SummarizerSkill: Calling async from sync context with a running event loop. This might lead to issues. Consider using async_to_sync or awaiting the async method.")
                    # Depending on SK version and how it handles its own loop, this might vary.
                    # We'll try creating a task if loop is running, otherwise new loop.
                    # This part is tricky without knowing the exact SK execution model for invoke.
                    # Simplest for now: if loop running, try to schedule. If not, new_event_loop.
                    # However, creating a new event loop if one is already running is an error.
                    # Let's assume for now that if a loop is running, we should try to use it to run the task.
                    # This is still not fully robust.
                    task = loop.create_task(self.summarize_section_async(section_text, max_sentences))
                    # This is blocking, which defeats some async benefits but fulfills sync signature.
                    # It's problematic if the current thread cannot block.
                    return loop.run_until_complete(task)

                else: # No loop running, create one
                    return asyncio.run(self.summarize_section_async(section_text, max_sentences))
            except RuntimeError as e: # Handles "cannot call run_until_complete from a running event loop"
                 logging.error(f"SK_MDNA_SummarizerSkill: RuntimeError with asyncio in sync wrapper: {e}. Falling back to generic placeholder.")
                 # Fallback to generic placeholder
                 return "[Placeholder LLM Summary: Asyncio error in sync wrapper. Content would be generated here.]"

        else: # Fallback if kernel doesn't have run_async (older SK or different setup)
            logging.warning("SK_MDNA_SummarizerSkill: Kernel does not have 'run_async' or other issue with sync wrapper. Using generic placeholder.")
            # Fallback to generic placeholder
            return "[Placeholder LLM Summary: Kernel async setup issue in sync wrapper. Content would be generated here.]"


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
    # Setup basic logging for the test
    logging.basicConfig(level=logging.INFO)

    # IMPORTANT: For this test to attempt a real Semantic Kernel call,
    # ensure OPENAI_API_KEY and OPENAI_ORG_ID are set in your environment.
    # e.g., export OPENAI_API_KEY="your_key"
    # If not set, it will use placeholder logic due to KernelService initialization.
    print("\n--- Testing MD&A Summarizer ---")
    print("NOTE: If OPENAI_API_KEY is not set, this will use placeholder logic.")

    mdna_summarizer = SK_MDNA_SummarizerSkill()

    # Example: Test with OPENAI_API_KEY potentially not set (will use placeholder)
    # To truly test SK path, set the env var.
    # For CI/CD or automated tests without live keys, this test primarily checks integration,
    # and the KernelService/Skill should gracefully handle missing keys by using placeholders
    # or returning specific errors, which is what we are testing here.

    mdna_text_to_summarize = dummy_sections.get("ITEM_7_MDNA", "")
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set. Expecting placeholder logic or warning from KernelService.")
        # Provide a dummy key for the adapter to proceed with initialization for testing structure
        # but actual calls would fail or be blocked by SK if it tries to use a clearly invalid key.
        # The KernelService itself logs a warning if the key is missing.
        # Our skill's use_placeholder flag will be True.

    print(f"Attempting to summarize MD&A (max 3 sentences): '{mdna_text_to_summarize[:100]}...'")
    mdna_summary = mdna_summarizer.summarize_section(mdna_text_to_summarize, max_sentences=3)
    print(f"\nMD&A Summary (sync wrapper, target 3 sentences):\n{mdna_summary}")

    # Example of calling the async version directly (if you are in an async context)
    # async def main_async_test():
    #     mdna_summary_async = await mdna_summarizer.summarize_section_async(mdna_text_to_summarize, max_sentences=2)
    #     print(f"\nMD&A Summary (async, target 2 sentences):\n{mdna_summary_async}")
    #
    # if __name__ == '__main__':
    #    asyncio.run(main_async_test())
    # else:
    #    # If not main, the sync test above runs.
    #    # For more complex scenarios, consider how to manage event loops.
    #    pass


    # Risk Analysis
    risk_analyzer = SK_RiskAnalysisSkill()
    risk_highlights = risk_analyzer.identify_risk_keywords_sentences(dummy_sections.get("ITEM_1A_RISK_FACTORS", ""))
    print(f"\nRisk Factor Sentences Identified ({len(risk_highlights)}):")
    for sentence in risk_highlights:
        print(f"  - {sentence}")
