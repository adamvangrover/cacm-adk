# toolkit/modules/workflow_runner.py
import json
import os
import asyncio
import click # For potential echo, though core logic is orchestrator based

# Attempt to import existing ADK core components
try:
    from cacm_adk_core.validator.validator import Validator
    from cacm_adk_core.orchestrator.orchestrator import Orchestrator
    from cacm_adk_core.semantic_kernel_adapter import KernelService
except ImportError:
    # Fallback for potential path issues during development,
    # though ideally the toolkit is installed or PYTHONPATH is set.
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from cacm_adk_core.validator.validator import Validator
    from cacm_adk_core.orchestrator.orchestrator import Orchestrator
    from cacm_adk_core.semantic_kernel_adapter import KernelService

# Default paths (mirroring scripts/adk_cli.py)
DEFAULT_SCHEMA_PATH = "cacm_standard/cacm_schema_v0.2.json"
DEFAULT_CATALOG_PATH = "config/compute_capability_catalog.json"

class WorkflowRunnerModule: # No need to inherit from ToolkitModule for now
    def get_name(self) -> str:
        return "workflow_runner"

    def get_description(self) -> str:
        return "Runs a CACM workflow using the project's Orchestrator."

    async def _run_workflow_async(self, orchestrator, cacm_instance_data):
        # Helper to run orchestrator's async run_cacm method.
        return await orchestrator.run_cacm(cacm_instance_data)

    def execute(self, cacm_filepath: str, output_dir: str = None) -> dict:
        """
        Loads a CACM file, runs it through the Orchestrator, and handles output.
        """
        runner_output = {"status": "failed", "logs": [], "outputs": None, "message": ""}

        if not os.path.exists(cacm_filepath):
            runner_output["message"] = f"Error: CACM file not found at {cacm_filepath}"
            return runner_output

        # Initialize Validator
        if not os.path.exists(DEFAULT_SCHEMA_PATH):
            runner_output["message"] = f"Error: CACM Schema not found at {DEFAULT_SCHEMA_PATH}. Cannot proceed."
            return runner_output
        validator = Validator(schema_filepath=DEFAULT_SCHEMA_PATH)
        if not validator.schema:
            runner_output["message"] = "Error: Validator schema could not be initialized."
            return runner_output

        # Initialize KernelService (required by Orchestrator)
        try:
            kernel_service_instance = KernelService()
        except Exception as e:
            runner_output["message"] = f"Error: Failed to initialize KernelService: {str(e)}"
            return runner_output
        
        # Initialize Orchestrator
        if not os.path.exists(DEFAULT_CATALOG_PATH):
            # Orchestrator handles this by creating an empty catalog, but we can log a warning
            runner_output["logs"].append(f"Warning: Compute Capability Catalog not found at {DEFAULT_CATALOG_PATH}. Orchestrator may have limited capability checks.")
        
        orchestrator = Orchestrator(validator=validator, catalog_filepath=DEFAULT_CATALOG_PATH, kernel_service=kernel_service_instance)
        if not orchestrator:
            runner_output["message"] = "Error: Orchestrator could not be initialized."
            return runner_output

        try:
            with open(cacm_filepath, "r") as f:
                cacm_instance_data = json.load(f)
        except json.JSONDecodeError as e:
            runner_output["message"] = f"Error: Invalid JSON in file {cacm_filepath}: {str(e)}"
            return runner_output
        except IOError as e:
            runner_output["message"] = f"Error reading file {cacm_filepath}: {str(e)}"
            return runner_output

        runner_output["logs"].append(f"Attempting to run CACM: {cacm_filepath}")
        
        try:
            success, logs, outputs = asyncio.run(self._run_workflow_async(orchestrator, cacm_instance_data))
            
            runner_output["logs"].extend(logs if logs else [])
            runner_output["outputs"] = outputs

            if success:
                runner_output["status"] = "success"
                runner_output["message"] = "CACM workflow execution completed successfully."
                
                if outputs:
                    for output_name, output_data_val in outputs.items():
                        output_value_dict = output_data_val.get('value', None)
                        if isinstance(output_value_dict, dict) and 'content' in output_value_dict and 'file_path' in output_value_dict:
                            report_content = output_value_dict['content']
                            conceptual_file_path = output_value_dict['file_path']
                            final_report_path = conceptual_file_path

                            if output_dir:
                                if not os.path.isabs(output_dir):
                                    output_dir = os.path.abspath(output_dir)
                                final_report_path = os.path.join(output_dir, os.path.basename(conceptual_file_path))
                            
                            try:
                                report_save_dir = os.path.dirname(final_report_path)
                                if not os.path.exists(report_save_dir):
                                    os.makedirs(report_save_dir, exist_ok=True)
                                with open(final_report_path, "w") as f:
                                    f.write(report_content)
                                runner_output["logs"].append(f"Report from '{output_name}' saved to: {final_report_path}")
                            except Exception as e:
                                runner_output["logs"].append(f"Error saving report from '{output_name}' to {final_report_path}: {str(e)}")
            else:
                runner_output["message"] = "CACM workflow execution failed or did not complete."

        except Exception as e:
            runner_output["message"] = f"An unexpected error occurred during workflow execution: {str(e)}"
            runner_output["logs"].append(str(e))
        
        return runner_output
