import requests
import click

# Assuming the ToolkitModule interface is defined or will be defined in a central place.
# For now, let's define a base class structure here or import if it exists.
# If ARCHITECTURE.md's Python interface was in a file, e.g., toolkit.core.module_base
# from toolkit.core.module_base import ToolkitModule

class ToolkitModule: # Placeholder for the actual base class from architecture
    def get_name(self) -> str:
        raise NotImplementedError

    def get_description(self) -> str:
        raise NotImplementedError

    def execute(self, context: dict, **kwargs) -> dict:
        raise NotImplementedError

class WebSearchModule(ToolkitModule):
    def get_name(self) -> str:
        return "web_search"

    def get_description(self) -> str:
        return "Performs a web search using DuckDuckGo Instant Answer API and returns a summary."

    def execute(self, context: dict, query: str) -> dict:
        """
        Performs a web search using DuckDuckGo API.
        Context might contain API keys or other configurations in the future.
        """
        if not query:
            return {"error": "Query cannot be empty."}

        # Removed skip_disambig=1 to potentially get broader results for some queries
        url = f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json&pretty=0&no_html=1"
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()

            # Extract relevant information. DDG Instant Answer API structure varies.
            # We'll try to get an abstract or an answer.
            result = {
                "query": query,
                "answer_type": data.get("AnswerType", ""),
                "answer": data.get("Answer", ""), # Explicitly add Answer
                "abstract_text": data.get("AbstractText", ""),
                "abstract_source": data.get("AbstractSource", ""),
                "abstract_url": data.get("AbstractURL", ""),
                "definition": data.get("Definition", ""),
                "definition_source": data.get("DefinitionSource", ""),
                "related_topics": [
                    {"text": topic.get("Text"), "url": topic.get("FirstURL")}
                    for topic in data.get("RelatedTopics", [])
                    if topic.get("Text") and topic.get("FirstURL") and not topic.get("Topics") # Only get main related topics, not sub-topics
                ],
                "results": [ # General results if available
                     {"text": topic.get("Text"), "url": topic.get("FirstURL")}
                    for topic in data.get("Results", [])
                    if topic.get("Text") and topic.get("FirstURL")
                ],
                "raw_ddg_url": f"https://duckduckgo.com/?q={requests.utils.quote(query)}" # For user to check directly
            }
            # Filter out empty fields for cleaner output
            return {k: v for k, v in result.items() if v}

        except requests.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except ValueError as e: # Handles JSON decoding errors
            return {"error": f"Failed to parse API response: {str(e)}"}

# Example usage (for testing this module directly)
if __name__ == "__main__":
    search_module = WebSearchModule()
    test_query = "python programming"
    print(f"Testing module: {search_module.get_name()} - {search_module.get_description()}")
    results = search_module.execute(context={}, query=test_query)
    import json
    print(json.dumps(results, indent=2))

    test_empty_query = ""
    results_empty = search_module.execute(context={}, query=test_empty_query)
    print(json.dumps(results_empty, indent=2))

    test_error_query = "a query that might return less structured data or an empty abstract"
    results_less_structured = search_module.execute(context={}, query=test_error_query)
    print(json.dumps(results_less_structured, indent=2))
