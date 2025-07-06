import json
import os
import re
import sys  # Added to allow path manipulation for direct script run if needed

# --- Configuration ---
# Assuming this script is in scripts/ and the library is one level up
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# Ensure project root is in sys.path for potential module imports if this script grows
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

INPUT_JSONL_FILE = os.path.join(
    PROJECT_ROOT, "default_synthetic_library_v1", "synthetic_reports.jsonl"
)
OUTPUT_REPORTS_DIR = os.path.join(
    PROJECT_ROOT, "default_synthetic_library_v1", "human_readable_reports"
)


def sanitize_filename(name):
    """Sanitize a string to be used as a valid filename."""
    name = str(name)  # Ensure name is a string
    name = (
        re.sub(r"[^\w\s-]", "", name).strip().lower()
    )  # Remove non-alphanumeric (except underscore, hyphen), strip, lowercase
    name = re.sub(r"[-\s]+", "_", name)  # Replace spaces and hyphens with underscore
    name = name[:200]  # Limit filename length
    if not name:  # if name becomes empty after sanitization
        name = "_invalid_name_"
    return name


def main():
    print(f"Starting extraction of Markdown reports from: {INPUT_JSONL_FILE}")
    print(f"Output directory for Markdown files: {OUTPUT_REPORTS_DIR}")

    if not os.path.exists(INPUT_JSONL_FILE):
        print(f"ERROR: Input file not found: {INPUT_JSONL_FILE}")
        print(
            "Please ensure `scripts/generate_synthetic_library.py` has been run successfully first."
        )
        return

    if not os.path.exists(OUTPUT_REPORTS_DIR):
        try:
            os.makedirs(OUTPUT_REPORTS_DIR)
            print(f"Created output directory: {OUTPUT_REPORTS_DIR}")
        except OSError as e:
            print(f"ERROR: Could not create output directory {OUTPUT_REPORTS_DIR}: {e}")
            return

    report_count = 0
    error_count = 0
    processed_lines = 0

    try:
        with open(INPUT_JSONL_FILE, "r", encoding="utf-8") as f_jsonl:  # Added encoding
            for line_number, line in enumerate(f_jsonl, 1):
                processed_lines += 1
                stripped_line = line.strip()
                if not stripped_line:  # Skip empty lines
                    print(f"WARNING: Line {line_number} is empty. Skipping.")
                    error_count += 1
                    continue

                current_company_id_for_error = f"unknown_at_line_{line_number}"
                try:
                    report_object = json.loads(stripped_line)

                    company_id = report_object.get(
                        "company_id", f"unknown_company_L{line_number}"
                    )
                    current_company_id_for_error = (
                        company_id  # Update for more specific error logging
                    )
                    markdown_report = report_object.get("generated_markdown_report")

                    if markdown_report is None:
                        print(
                            f"WARNING: Line {line_number} for company '{company_id}' has no 'generated_markdown_report' field. Skipping."
                        )
                        error_count += 1
                        continue

                    if not isinstance(markdown_report, str):
                        print(
                            f"WARNING: Line {line_number} for company '{company_id}', 'generated_markdown_report' is not a string (type: {type(markdown_report)}). Skipping."
                        )
                        error_count += 1
                        continue

                    sanitized_company_id = sanitize_filename(company_id)
                    output_md_filename = f"{sanitized_company_id}_analysis_report.md"
                    output_md_filepath = os.path.join(
                        OUTPUT_REPORTS_DIR, output_md_filename
                    )

                    try:
                        with open(
                            output_md_filepath, "w", encoding="utf-8"
                        ) as f_md:  # Added encoding
                            f_md.write(markdown_report)
                        print(
                            f"Successfully extracted and saved report for '{company_id}' to '{output_md_filepath}'"
                        )
                        report_count += 1
                    except IOError as e_write:
                        print(
                            f"ERROR: Could not write Markdown file for company '{company_id}' to '{output_md_filepath}': {e_write}"
                        )
                        error_count += 1

                except json.JSONDecodeError as e_json:
                    print(
                        f"ERROR: Could not parse JSON on line {line_number}: {e_json}. Line content (first 100 chars): '{stripped_line[:100]}'"
                    )
                    error_count += 1
                except (
                    KeyError
                ) as e_key:  # Should ideally not happen if JSON structure is consistent
                    print(
                        f"ERROR: Missing expected key {e_key} on line {line_number} for company '{current_company_id_for_error}'."
                    )
                    error_count += 1
                except (
                    Exception
                ) as e_general:  # Catch any other unexpected errors per line
                    print(
                        f"ERROR: Unexpected error processing line {line_number} for company '{current_company_id_for_error}': {e_general}"
                    )
                    error_count += 1

    except IOError as e_read:
        print(f"ERROR: Could not read input file {INPUT_JSONL_FILE}: {e_read}")
        return

    print(f"\nExtraction complete. Processed {processed_lines} lines.")
    print(f"Successfully extracted {report_count} Markdown reports.")
    if error_count > 0:
        print(f"Encountered {error_count} errors/warnings during extraction.")


if __name__ == "__main__":
    main()
