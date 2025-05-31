# processing_pipeline/doc_parser.py
import json
import os
import re

# Define common SEC filing section markers
# Using a list of tuples: (Canonical Key, List of Regex Patterns to find it)
# Regex patterns allow for some flexibility (e.g., optional periods, whitespace variations)
# Using re.IGNORECASE for matching
SECTION_MARKERS = [
    ("ITEM_1_BUSINESS", [r"ITEM\s+1\.\s*BUSINESS"]),
    ("ITEM_1A_RISK_FACTORS", [r"ITEM\s+1A\.\s*RISK\s*FACTORS"]),
    ("ITEM_1B_UNRESOLVED_STAFF_COMMENTS", [r"ITEM\s+1B\.\s*UNRESOLVED\s*STAFF\s*COMMENTS"]),
    ("ITEM_1C_CYBERSECURITY", [r"ITEM\s+1C\.\s*CYBERSECURITY"]), # New addition based on recent SEC rules
    ("ITEM_2_PROPERTIES", [r"ITEM\s+2\.\s*PROPERTIES"]),
    ("ITEM_3_LEGAL_PROCEEDINGS", [r"ITEM\s+3\.\s*LEGAL\s*PROCEEDINGS"]),
    ("ITEM_4_MINE_SAFETY_DISCLOSURES", [r"ITEM\s+4\.\s*MINE\s*SAFETY\s*DISCLOSURES"]),
    ("ITEM_5_MARKET_FOR_REGISTRANT_COMMON_EQUITY", [r"ITEM\s+5\.\s*MARKET\s*FOR\s*REGISTRANT’S\s*COMMON\s*EQUITY"]), # Simplified key
    ("ITEM_6_RESERVED", [r"ITEM\s+6\.\s*\[RESERVED\]", r"ITEM\s+6\.\s*RESERVED"]),
    ("ITEM_7_MDNA", [r"ITEM\s+7\.\s*MANAGEMENT’S\s*DISCUSSION\s*AND\s*ANALYSIS"]), # MD&A
    ("ITEM_7A_QUANTITATIVE_QUALITATIVE_MARKET_RISK", [r"ITEM\s+7A\.\s*QUANTITATIVE\s*AND\s*QUALITATIVE\s*DISCLOSURES\s*ABOUT\s*MARKET\s*RISK"]),
    ("ITEM_8_FINANCIAL_STATEMENTS", [r"ITEM\s+8\.\s*FINANCIAL\s*STATEMENTS\s*AND\s*SUPPLEMENTARY\s*DATA"]),
    ("ITEM_9_CHANGES_DISAGREEMENTS_ACCOUNTANTS", [r"ITEM\s+9\.\s*CHANGES\s*IN\s*AND\s*DISAGREEMENTS\s*WITH\s*ACCOUNTANTS"]),
    ("ITEM_9A_CONTROLS_PROCEDURES", [r"ITEM\s+9A\.\s*CONTROLS\s*AND\s*PROCEDURES"]),
    ("ITEM_9B_OTHER_INFORMATION", [r"ITEM\s+9B\.\s*OTHER\s*INFORMATION"]),
    ("ITEM_9C_DISCLOSURE_FOREIGN_JURISDICTIONS_INSPECTIONS", [r"ITEM\s+9C\.\s*DISCLOSURE\s*REGARDING\s*FOREIGN\s*JURISDICTIONS"]), # Simplified
    ("PART_II_OTHER_INFORMATION_GENERAL", [r"PART\s+II", r"PART\s+II\."]), # More generic PART II start, if specific items missed.
    ("PART_III_PROXY_INFORMATION_GENERAL", [r"PART\s+III", r"PART\s+III\."]),
    ("PART_IV_EXHIBITS_SCHEDULES_GENERAL", [r"PART\s+IV", r"PART\s+IV\."]),
    ("ITEM_15_EXHIBITS_FINANCIAL_STATEMENT_SCHEDULES", [r"ITEM\s+15\.\s*EXHIBITS,\s*FINANCIAL\s*STATEMENT\s*SCHEDULES", r"ITEM\s+15\.\s*EXHIBIT\s*AND\s*FINANCIAL\s*STATEMENT\s*SCHEDULES"]),
    ("SIGNATURES", [r"SIGNATURES"])
    # "EXHIBIT INDEX" can be part of Item 15 or separate, often very near the end.
]

def extract_sections_from_text_filing(document_path: str) -> dict:
    """
    Parses a text-based SEC filing (e.g., 10-K, 10-Q extracted from TXT format)
    and attempts to split it into standard sections.

    Args:
        document_path (str): Path to the input text document.

    Returns:
        dict: A dictionary where keys are normalized section titles 
              (e.g., "ITEM_1A_RISK_FACTORS") and values are the text content of these sections.
              Includes an "__UNMATCHED_PREAMBLE__" if there's text before the first known marker.
    """
    sections = {}
    try:
        with open(document_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Document not found at {document_path}")
        return {"error": f"File not found: {document_path}"}
    except Exception as e:
        print(f"Error reading document {document_path}: {e}")
        return {"error": f"Error reading file: {e}"}

    found_marker_positions = []

    for key, patterns in SECTION_MARKERS:
        for pattern in patterns:
            try:
                # re.IGNORECASE for case-insensitive matching of section titles
                # re.MULTILINE to handle titles that might be at the start of a line
                for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                    found_marker_positions.append({'key': key, 'start': match.start(), 'end': match.end(), 'match_text': match.group(0)})
                    break # Take the first match for this pattern set
            except Exception as e:
                print(f"Warning: Regex error for pattern '{pattern}' on key '{key}': {e}")


    # Sort markers by their start position
    found_marker_positions.sort(key=lambda x: x['start'])

    if not found_marker_positions:
        # If no markers found, return the whole content as a single "UNKNOWN_CONTENT" section
        # or handle as an error/specific case.
        sections["UNKNOWN_CONTENT"] = content.strip()
        return sections

    # Add preamble text if any content exists before the first marker
    first_marker_start = found_marker_positions[0]['start']
    if first_marker_start > 0:
        preamble = content[:first_marker_start].strip()
        if preamble:
            sections["__UNMATCHED_PREAMBLE__"] = preamble
            
    # Extract content for each section
    for i, marker_info in enumerate(found_marker_positions):
        section_key = marker_info['key']
        text_start_position = marker_info['end'] # Start extracting text *after* the marker itself

        if i + 1 < len(found_marker_positions):
            text_end_position = found_marker_positions[i+1]['start']
        else:
            text_end_position = len(content)
        
        section_content = content[text_start_position:text_end_position].strip()
        
        # Avoid overwriting if multiple patterns for the same key matched and were sorted closely.
        # This simple loop structure with prior sorting should generally handle it by taking the first one.
        if section_key not in sections: # Add only if key not already populated (first occurrence wins)
             sections[section_key] = section_content
        elif not sections[section_key] and section_content: # If previous was empty, fill it
             sections[section_key] = section_content


    # A simple cleanup for very short/empty sections that might be just leftover titles
    final_sections = {}
    for key, text in sections.items():
        # Heuristic: if a section is very short and mostly uppercase, it might be a missed sub-header
        # This is very basic, more sophisticated cleanup could be added.
        if len(text) < 100 and text.isupper() and key != "__UNMATCHED_PREAMBLE__": 
            # Check if this text is a known marker itself to avoid removing actual short sections
            is_another_marker = False
            for _, patterns in SECTION_MARKERS:
                for pattern in patterns:
                    if re.fullmatch(pattern, text.strip(), re.IGNORECASE):
                        is_another_marker = True
                        break
                if is_another_marker: break
            if not is_another_marker and len(text.split()) < 15 : # if less than 15 words and uppercase
                 print(f"Info: Potentially removing short/header-like section '{key}' with content: '{text[:50]}...'")
                 continue # Skip adding this as a section if it looks like a leftover title
        final_sections[key] = text
        
    return final_sections


if __name__ == '__main__':
    input_file_path = "data_ingestion/input_documents/MSFT_FY24Q4_10K_provided.txt"
    output_dir = "data_ingestion/processed_text/"
    output_file_path = os.path.join(output_dir, "MSFT_FY24Q4_10K_sectioned.json")

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    print(f"Starting section extraction for: {input_file_path}")
    sectioned_data = extract_sections_from_text_filing(input_file_path)

    if "error" not in sectioned_data:
        try:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(sectioned_data, f, indent=4, ensure_ascii=False)
            print(f"Successfully extracted sections and saved to: {output_file_path}")
            
            # Check if all actual section values (excluding preamble) are empty or None
            actual_sections_empty = True
            if sectioned_data:
                actual_sections_empty = all(not text for key, text in sectioned_data.items() if key != "__UNMATCHED_PREAMBLE__")
            
            if not sectioned_data or actual_sections_empty:
                 print("Warning: The output is empty or contains mostly preamble/empty actual sections. Check input file content and section markers.")
                 if "__UNMATCHED_PREAMBLE__" in sectioned_data and len(sectioned_data) == 1:
                     print("Info: Only preamble was found.")
            elif len(sectioned_data) <= 2 and "__UNMATCHED_PREAMBLE__" in sectioned_data and not actual_sections_empty: # Preamble + one actual section
                 print(f"Info: Few sections extracted. Found: {list(sectioned_data.keys())}.")
            elif len(sectioned_data) <=1 and not "__UNMATCHED_PREAMBLE__" in sectioned_data and not actual_sections_empty : # Only one actual section
                 print(f"Info: Only one actual section extracted. Found: {list(sectioned_data.keys())}.")


        except Exception as e:
            print(f"Error saving sectioned data to JSON: {e}")
    else:
        print(f"Failed to extract sections: {sectioned_data.get('error')}")

    # Example for 10-Q (demonstrating the function can be reused)
    input_10q_path = "data_ingestion/input_documents/MSFT_FY25Q3_10Q_provided.txt"
    output_10q_path = os.path.join(output_dir, "MSFT_FY25Q3_10Q_sectioned.json")
    print(f"\nStarting section extraction for: {input_10q_path}")
    sectioned_data_10q = extract_sections_from_text_filing(input_10q_path)
    if "error" not in sectioned_data_10q:
        try:
            with open(output_10q_path, 'w', encoding='utf-8') as f:
                json.dump(sectioned_data_10q, f, indent=4, ensure_ascii=False)
            print(f"Successfully extracted sections and saved to: {output_10q_path}")

            actual_sections_10q_empty = True
            if sectioned_data_10q:
                actual_sections_10q_empty = all(not text for key, text in sectioned_data_10q.items() if key != "__UNMATCHED_PREAMBLE__")

            if not sectioned_data_10q or actual_sections_10q_empty:
                 print("Warning: The 10-Q output is empty or contains mostly preamble/empty actual sections. Check input file content and section markers.")
        except Exception as e:
            print(f"Error saving 10-Q sectioned data to JSON: {e}")
    else:
        print(f"Failed to extract 10-Q sections: {sectioned_data_10q.get('error')}")
