# toolkit/modules/llm_wrapper.py
import json
import os
import click  # For potential echo, though not strictly necessary here

try:
    from cacm_adk_core.semantic_kernel_adapter import KernelService
    import semantic_kernel as sk  # For sk.exceptions
except ImportError:
    import sys

    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    )
    from cacm_adk_core.semantic_kernel_adapter import KernelService
    import semantic_kernel as sk


class LLMWrapperModule:
    def __init__(self):
        self._kernel_service = None
        self._kernel = None
        self._initialize_kernel_service()

    def _initialize_kernel_service(self):
        try:
            self._kernel_service = KernelService()
            self._kernel = self._kernel_service.get_kernel()
            if not self._kernel:
                raise RuntimeError(
                    "Failed to get a valid kernel instance from KernelService."
                )
        except Exception as e:
            # This error will be caught by the CLI commands and reported to the user.
            # Allow module to instantiate, but it won't be functional.
            self._kernel = None
            # We can store the error to be more specific later if needed
            self._init_error = e

    def list_skills(self) -> dict:
        if not self._kernel:
            return {
                "error": f"KernelService not initialized properly. OpenAI API key might be missing or other configuration issue. Error: {getattr(self, '_init_error', 'Unknown error')}"
            }

        skills_list = []
        if self._kernel.plugins and len(self._kernel.plugins) > 0:
            for plugin_name, plugin_instance in self._kernel.plugins.items():
                if hasattr(plugin_instance, "functions") and isinstance(
                    plugin_instance.functions, dict
                ):
                    for func_name, func_view in plugin_instance.functions.items():
                        skills_list.append(
                            {
                                "plugin_name": plugin_name,
                                "function_name": func_view.name,
                                "description": func_view.description,
                                # Parameters could be added here if needed by inspecting func_view.parameters
                            }
                        )
                else:  # Should not happen with SK v1 structure
                    skills_list.append(
                        {
                            "plugin_name": plugin_name,
                            "function_name": "N/A (plugin structure not as expected)",
                            "description": "Could not retrieve functions for this plugin.",
                        }
                    )
        if not skills_list:
            return {
                "skills": [],
                "message": "No plugins or functions found in the kernel.",
            }
        return {"skills": skills_list}

    async def invoke_skill_async(
        self, plugin_name: str, function_name: str, arguments: dict = None
    ):
        if not self._kernel:
            return {
                "error": f"KernelService not initialized properly. OpenAI API key might be missing or other configuration issue. Error: {getattr(self, '_init_error', 'Unknown error')}"
            }

        if not plugin_name or not function_name:
            return {"error": "Plugin name and function name are required."}

        try:
            # Ensure arguments is a dict, even if empty
            args_to_pass = arguments if arguments is not None else {}

            # For SK v1, invoke is the primary method
            result = await self._kernel.invoke(
                plugin_name=plugin_name, function_name=function_name, **args_to_pass
            )
            # The result from kernel.invoke is typically a KernelContent object or similar.
            # We want to extract the primary string representation or value.

            # The actual result is often in result.value or str(result)
            # If it's a FunctionResult:
            if hasattr(result, "value"):
                processed_result = result.value
            else:  # Fallback to string representation
                processed_result = str(result)

            # If the result itself is complex (e.g. a Pydantic model from a native function),
            # it might need further serialization if we want to return it as JSON directly.
            # For now, let's assume it's often text or can be stringified.
            if isinstance(processed_result, (dict, list)):  # If it's already dict/list
                return {"result": processed_result}
            elif hasattr(processed_result, "model_dump_json") and callable(
                getattr(processed_result, "model_dump_json")
            ):  # Pydantic v2
                return {"result": json.loads(processed_result.model_dump_json())}
            elif hasattr(processed_result, "dict") and callable(
                getattr(processed_result, "dict")
            ):  # Pydantic v1
                return {"result": processed_result.dict()}
            else:  # Otherwise, treat as plain text/value
                return {"result": str(processed_result)}

        except sk.exceptions.KernelServiceNotFoundError:
            return {
                "error": f"Service required by '{plugin_name}.{function_name}' not found. Ensure LLM service is configured (e.g. OpenAI API key)."
            }
        except sk.exceptions.FunctionNameNotAvailableError:
            return {
                "error": f"Function '{function_name}' not found in plugin '{plugin_name}'."
            }
        except sk.exceptions.PluginNameNotAvailableError:
            return {"error": f"Plugin '{plugin_name}' not found."}
        except Exception as e:
            return {
                "error": f"Error invoking skill '{plugin_name}.{function_name}': {str(e)}"
            }
