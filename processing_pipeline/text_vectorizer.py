# processing_pipeline/text_vectorizer.py
import json
import os
import hashlib


def get_filename_from_section_key(base_filename_parts: list, section_key: str) -> str:
    """Helper to create a more readable filename for section embeddings."""
    # Normalize the section key for use in filename
    # e.g., "ITEM_1A_RISK_FACTORS" -> "Item1aRiskFactors"
    # or "ITEM_7_MDNA" -> "Item7Mdna"
    # This is a simplified normalization.
    normalized_key_parts = []
    for part in section_key.split("_"):
        if part.lower() == "item":
            normalized_key_parts.append(part.capitalize())
        elif len(part) > 0:
            if len(part) <= 2 and part.isalpha() and part.islower():  # e.g. 1A -> 1a
                normalized_key_parts.append(part)
            elif len(part) <= 2 and part.isalnum() and not part.isnumeric():  # 1A
                normalized_key_parts.append(part)
            else:
                normalized_key_parts.append(part.capitalize())
        else:  # Handle potential empty parts from multiple underscores
            pass

    # Ensure item numbers like "1A" or "7A" are handled without excessive capitalization if not desired
    # This is tricky with simple capitalize. A more robust solution might use regex or more rules.
    # For now, the above is a basic attempt.
    # A simpler approach might be:
    # normalized_section_name = "".join([p.capitalize() if not (len(p) <=2 and p.isalpha() and p.islower()) else p for p in section_key.split('_')])

    # Let's use a simpler normalization for filenames:
    # ITEM_1A_RISK_FACTORS -> Item1aRiskFactors (more or less)
    # This is still a bit complex for simple string ops, let's simplify further for filename:
    # ITEM_1A_RISK_FACTORS -> RiskFactors (if key contains common terms)
    # or just use the key directly if it's not too long.

    # Simplified approach for demo:
    name_part = section_key.replace("ITEM_", "").replace("ITEM", "")  # Remove "ITEM_"
    name_part = "".join([p.capitalize() for p in name_part.split("_")])  # CamelCase

    # For very common items, use a shorter name
    if "RISK_FACTORS" in section_key:
        name_part = "RiskFactors"
    elif "MDNA" in section_key:
        name_part = "MDNA"  # ITEM_7_MDNA
    elif "FINANCIAL_STATEMENTS" in section_key:
        name_part = "FinancialStatements"  # ITEM_8_FINANCIAL_STATEMENTS
    elif "BUSINESS" in section_key:
        name_part = "Business"  # ITEM_1_BUSINESS

    # Construct filename: MSFT_FY24Q4_10K_RiskFactors_embeddings_placeholder.txt
    return f"{'_'.join(base_filename_parts)}_{name_part}_embeddings_placeholder.txt"


def vectorize_text_content(sectioned_data_path: str) -> dict:
    """
    Placeholder implementation for text vectorization.
    This function simulates the vectorization process by creating placeholder files
    for key sections of a document.

    Ideally, this function would:
    1. Load sectioned text data.
    2. For each relevant section:
        a. Pre-process the text (chunking if necessary).
        b. Use a Semantic Kernel skill to call an embedding model (e.g., Azure OpenAI Embeddings, local model).
        c. Generate semantic vector embeddings for the text.
        d. Store these embeddings in a structured format (e.g., .npy, .pkl, or a vector database)
           and return paths or identifiers to these stored embeddings.

    Args:
        sectioned_data_path (str): Path to the JSON file containing sectioned document text.
                                   Filename is expected to be like 'COMPANY_FYXXQX_TYPE_sectioned.json'
                                   e.g., MSFT_FY24Q4_10K_sectioned.json

    Returns:
        dict: A dictionary mapping original section keys to the paths of newly created
              placeholder files for their embeddings.
    """
    output_paths = {}
    vectorized_content_dir = "data_ingestion/vectorized_content/"

    if not os.path.exists(vectorized_content_dir):
        os.makedirs(vectorized_content_dir)
        print(f"Created directory: {vectorized_content_dir}")

    try:
        with open(sectioned_data_path, "r", encoding="utf-8") as f:
            sectioned_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Sectioned data file not found at {sectioned_data_path}")
        return {"error": f"File not found: {sectioned_data_path}"}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {sectioned_data_path}")
        return {"error": f"JSON decode error in: {sectioned_data_path}"}

    # Extract base filename parts (e.g., MSFT_FY24Q4_10K)
    base_input_filename = os.path.basename(sectioned_data_path)
    filename_parts = base_input_filename.replace("_sectioned.json", "").split(
        "_"
    )  # MSFT, FY24Q4, 10K

    # Define key sections to create placeholders for
    # These keys should match those produced by doc_parser.py
    key_sections_to_vectorize = [
        "ITEM_1_BUSINESS",
        "ITEM_1A_RISK_FACTORS",
        "ITEM_7_MDNA",  # "ITEM_7_MANAGEMENT_S_DISCUSSION_AND_ANALYSIS" might be too long as key
        "ITEM_8_FINANCIAL_STATEMENTS",  # "ITEM_8_FINANCIAL_STATEMENTS_AND_SUPPLEMENTARY_DATA"
    ]

    print(
        f"Placeholder: Simulating vectorization for sections from {sectioned_data_path}"
    )

    for section_key, section_text in sectioned_data.items():
        if section_key in key_sections_to_vectorize and section_text:
            # Create a unique hash of the section text to simulate unique embeddings
            text_hash = hashlib.md5(section_text.encode("utf-8")).hexdigest()[:8]

            placeholder_filename = get_filename_from_section_key(
                filename_parts, section_key
            )
            output_file_path = os.path.join(
                vectorized_content_dir, placeholder_filename
            )

            content_for_placeholder = (
                f"Placeholder for semantic embeddings of {'_'.join(filename_parts)} {section_key} section.\n"
                f"Original text hash (MD5 prefix): {text_hash}\n"
                f"Actual embeddings would be generated by a Semantic Kernel skill calling an embedding model "
                f"(e.g., text-embedding-ada-002, sentence-transformers, etc.) and stored in a binary format or vector DB.\n"
                f"This file represents the *reference* to those embeddings."
            )

            try:
                with open(output_file_path, "w", encoding="utf-8") as f:
                    f.write(content_for_placeholder)
                output_paths[section_key] = output_file_path
                print(f"  Created placeholder embedding reference: {output_file_path}")
            except Exception as e:
                print(f"  Error creating placeholder file {output_file_path}: {e}")
        elif (
            section_key == "__UNMATCHED_PREAMBLE__" or section_key == "UNKNOWN_CONTENT"
        ):
            print(f"  Skipping vectorization for utility section: {section_key}")
        elif not section_text and section_key in key_sections_to_vectorize:
            print(f"  Skipping vectorization for empty section: {section_key}")

    if not output_paths:
        print(
            f"Warning: No key sections found or processed for vectorization from {sectioned_data_path}. Check input file and key_sections_to_vectorize list."
        )

    return output_paths


if __name__ == "__main__":
    # Example usage:
    # Ensure MSFT_FY24Q4_10K_sectioned.json exists from the doc_parser step
    # (It will use the placeholder content from doc_parser if real parsing hasn't happened)

    # First, create a dummy sectioned file for testing if doc_parser hasn't run with real content
    dummy_sectioned_data_dir = "data_ingestion/processed_text/"
    if not os.path.exists(dummy_sectioned_data_dir):
        os.makedirs(dummy_sectioned_data_dir)

    dummy_sectioned_file_path = os.path.join(
        dummy_sectioned_data_dir, "MSFT_FY24Q4_10K_sectioned.json"
    )
    if not os.path.exists(dummy_sectioned_file_path):
        print(
            f"Creating dummy sectioned file for text_vectorizer test: {dummy_sectioned_file_path}"
        )
        dummy_data = {
            "__UNMATCHED_PREAMBLE__": "Some preamble text.",
            "ITEM_1_BUSINESS": "Microsoft is a technology company.",
            "ITEM_1A_RISK_FACTORS": "Competition is a risk. Economic downturn is a risk.",
            "ITEM_7_MDNA": "Management discussion about performance.",
            "ITEM_8_FINANCIAL_STATEMENTS": "Balance sheet and income statement details here.",
            "OTHER_SECTION": "Some other less important section.",
        }
        with open(dummy_sectioned_file_path, "w") as f:
            json.dump(dummy_data, f, indent=2)

    print(f"\n--- Testing vectorize_text_content with {dummy_sectioned_file_path} ---")
    vectorization_references = vectorize_text_content(dummy_sectioned_file_path)
    print("\nReturned mapping to placeholder embedding files:")
    for section, path in vectorization_references.items():
        print(f"  Section '{section}': {path}")

    # Test with a non-existent file
    print(f"\n--- Testing vectorize_text_content with non_existent_file.json ---")
    non_existent_result = vectorize_text_content("non_existent_file.json")
    print(non_existent_result)
