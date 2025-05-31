import os
import logging
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

class KernelService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KernelService, cls).__new__(cls)
            cls._instance._initialize_kernel()
        return cls._instance

    def _initialize_kernel(self):
        # The Kernel can use the standard Python logging, no need to pass it directly
        # to the constructor in recent versions of semantic-kernel.
        # Logging can be configured globally for the application.
        self.kernel = sk.Kernel() 
        logger = logging.getLogger(__name__)

        # Import and register native skills
        try:
            from cacm_adk_core.native_skills import BasicCalculationSkill, FinancialAnalysisSkill
            self.kernel.add_plugin(BasicCalculationSkill(), plugin_name="BasicCalculations")
            self.kernel.add_plugin(FinancialAnalysisSkill(), plugin_name="FinancialAnalysis")
            logger.info("Successfully registered BasicCalculationSkill and FinancialAnalysisSkill.")

            # Register placeholder LLM skills
            from processing_pipeline.semantic_kernel_skills import SK_MDNA_SummarizerSkill #, SK_RiskAnalysisSkill
            # Using SK_MDNA_SummarizerSkill for generic text summarization tasks
            # Its __init__ will try to get the kernel from KernelService itself if one isn't passed.
            self.kernel.add_plugin(SK_MDNA_SummarizerSkill(), plugin_name="SummarizationSkills")
            logger.info("Registered SK_MDNA_SummarizerSkill as SummarizationSkills.")

            # Register CustomReportingSkills
            from processing_pipeline.semantic_kernel_skills import CustomReportingSkills
            # Pass the kernel and logger to CustomReportingSkills instance
            self.kernel.add_plugin(CustomReportingSkills(kernel=self.kernel, logger=logger), plugin_name="ReportingAnalysisSkills")
            logger.info("Registered CustomReportingSkills with the kernel under plugin ReportingAnalysisSkills.")

        except ImportError as e:
            logger.error(f"Failed to import native or placeholder skills: {e}. Some functions may not be available.")
        except Exception as e: # Other potential errors during plugin registration
            logger.error(f"Error registering native skills: {e}. Native functions may not be available.")

        # Configure LLM service
        # IMPORTANT: Set the OPENAI_API_KEY and OPENAI_ORG_ID environment variables
        # before running the application.
        api_key = os.environ.get("OPENAI_API_KEY")
        org_id = os.environ.get("OPENAI_ORG_ID")

        if not api_key:
            logging.warning("OPENAI_API_KEY environment variable not set. OpenAI services will not be available.")
            # You might want to raise an error here or handle it differently
            # depending on whether OpenAI is strictly required.
            return

        try:
            # For SK >= 0.9, use add_service.
            # The first argument to OpenAIChatCompletion is ai_model_id.
            # service_id is specified in add_service if needed, or it's auto-named.
            self.kernel.add_service(
                OpenAIChatCompletion(
                    ai_model_id="gpt-3.5-turbo", 
                    api_key=api_key,
                    org_id=org_id
                )#,
                # service_id="openai_chat_completion" # Optional: if you need to name it explicitly
            )
            logger.info("Semantic Kernel initialized with OpenAI Chat Completion service.")
        except Exception as e:
            logger.error(f"Error initializing Semantic Kernel with OpenAI: {e}")
            # Handle specific exceptions from semantic_kernel if needed

    def get_kernel(self):
        return self.kernel

# Example of how to get the kernel instance
if __name__ == '__main__':
    # This is for demonstration. In a real application, you'd import and use KernelService.
    # Ensure environment variables are set if you run this directly for testing.
    # For example:
    # export OPENAI_API_KEY="your_api_key"
    # export OPENAI_ORG_ID="your_org_id"
    
    # Setup basic logging for the __main__ example
    example_logger = logging.getLogger(__name__ + "_example")
    logging.basicConfig(level=logging.INFO) # Configure root logger
    
    # Test if OPENAI_API_KEY is set, otherwise provide a dummy for local testing
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "dummy_key_for_local_test_only" 
        example_logger.warning("Using a DUMMY OpenAI API key for local testing. Real calls will fail.")

    kernel_service = KernelService() # This will trigger _initialize_kernel
    kernel_instance = kernel_service.get_kernel()

    if kernel_instance:
        # Check if the chat service was added, which depends on API key being present
        # The kernel.ai_services property might not exist or be the correct check.
        # Let's check for a specific service type if possible, or rely on logs from initialization.
        # The previous check kernel_instance.ai_services might be from an older SK version.
        # A more robust check is to see if a service for a specific type (e.g., chat completion) is available.
        try:
            chat_service = kernel_instance.get_service(OpenAIChatCompletion) # Pass the class type directly
            if chat_service:
                example_logger.info("Kernel instance obtained and OpenAI Chat Completion service seems configured.")
            else:
                # This case might occur if API key is missing and add_chat_service was skipped.
                example_logger.warning("Kernel instance obtained, but OpenAI service might NOT be configured (API key likely missing or other init error).")
        except sk.exceptions.KernelServiceNotFoundError: # Corrected exception type
             example_logger.warning("Kernel instance obtained, but OpenAI Chat Completion service was NOT found (API key likely missing).")
        except Exception as e:
            example_logger.error(f"Error checking for chat service: {e}")

        # Verification: List available functions
        if kernel_instance: # This inner check is redundant as it's already inside 'if kernel_instance:'
            example_logger.info("\n--- Registered Functions in Kernel ---")
            # For SK v1.x, kernel.plugins is KernelPluginCollection, which is dict-like
            if kernel_instance.plugins and len(kernel_instance.plugins) > 0:
                for plugin_name, plugin_instance in kernel_instance.plugins.items():
                    # Each plugin_instance should be a KernelPlugin object
                    if hasattr(plugin_instance, 'functions') and isinstance(plugin_instance.functions, dict):
                        for func_name, func_view in plugin_instance.functions.items():
                             # func_view is KernelFunctionMetadata
                            example_logger.info(
                                f"- Plugin: {plugin_name}, Function: {func_view.name}, Description: {func_view.description}"
                            )
                    else:
                        example_logger.info(f"Plugin {plugin_name} does not have a standard 'functions' dictionary attribute.")
            else:
                example_logger.info("No plugins found in the kernel or plugins collection is empty.")
        
    else: # This matches the outer 'if kernel_instance:'
        example_logger.error("Failed to obtain Kernel instance.")
