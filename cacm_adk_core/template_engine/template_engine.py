# cacm_adk_core/template_engine/template_engine.py
import os
import json
import uuid
from datetime import datetime, timezone
import copy
import re

# TemplateEngine now expects pure JSON files.


class TemplateEngine:
    def __init__(self, templates_dir: str = "cacm_library/templates"):
        self.templates_dir = os.path.abspath(templates_dir)
        if not os.path.isdir(self.templates_dir):
            print(f"Warning: Templates directory not found: {self.templates_dir}")

    def list_templates(self) -> list[dict]:
        templates_info = []
        if not os.path.isdir(self.templates_dir):
            return templates_info
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".json"):  # Changed from .jsonc
                filepath = os.path.join(self.templates_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content_raw = f.read()
                    data = json.loads(content_raw)  # Directly parse raw content
                    metadata = data.get("metadata", {})
                    template_details = metadata.get("templateDetails", {})
                    name = template_details.get(
                        "templateName", data.get("name", filename.replace(".json", ""))
                    )  # Changed from .jsonc
                    description = template_details.get(
                        "intendedUsage",
                        data.get("description", "No description available."),
                    )
                    templates_info.append(
                        {"filename": filename, "name": name, "description": description}
                    )
                except Exception as e:
                    print(f"Warning: Error processing template file {filename}: {e}")
        return templates_info

    def load_template(self, template_filename: str) -> dict | None:
        filepath = os.path.join(self.templates_dir, template_filename)
        if not os.path.isfile(filepath):
            print(
                f"Error: Template file not found: {filepath}"
            )  # Error message already generic
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content_raw = f.read()
            return json.loads(content_raw)  # Directly parse raw content
        except Exception as e:
            print(
                f"Error loading/parsing template {template_filename}: {e}"
            )  # Error message already generic
            return None

    def _deep_merge_dicts(self, base: dict, updates: dict) -> dict:
        merged = copy.deepcopy(base)
        for key, value in updates.items():
            if (
                isinstance(value, dict)
                and key in merged
                and isinstance(merged[key], dict)
            ):
                merged[key] = self._deep_merge_dicts(merged[key], value)
            else:
                merged[key] = value
        return merged

    def instantiate_template(
        self, template_filename: str, cacm_id: str = None, overrides: dict = None
    ) -> dict | None:
        template_data = self.load_template(template_filename)
        if template_data is None:
            return None
        instantiated_cacm = copy.deepcopy(template_data)
        instantiated_cacm["cacmId"] = cacm_id if cacm_id else str(uuid.uuid4())
        if "metadata" not in instantiated_cacm:
            instantiated_cacm["metadata"] = {}
        instantiated_cacm["metadata"]["creationDate"] = datetime.now(
            timezone.utc
        ).isoformat(timespec="seconds")
        if overrides:
            instantiated_cacm = self._deep_merge_dicts(instantiated_cacm, overrides)
        return instantiated_cacm
