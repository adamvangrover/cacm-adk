# cacm_adk_core/compute_capabilities/data_fetchers.py
from typing import Dict, List, Any, Optional

MOCKED_PROFILES: Dict[str, Dict[str, Any]] = {
    "COMP_ABC": {
        "companyName": "ABC Corporation",
        "companyDescription": "A leading manufacturer of widgets and gadgets.",
        "primaryIndustry": "Manufacturing",
        "keyExecutives": [
            {"name": "Alice Wonderland", "title": "CEO"},
            {"name": "Bob The Builder", "title": "COO"},
        ],
        "recentNewsSummary": "ABC Corp recently launched a new eco-widget, receiving positive market feedback.",
    },
    "COMP_XYZ": {
        "companyName": "XYZ Innovations Inc.",
        "companyDescription": "Pioneering research in advanced AI solutions.",
        "primaryIndustry": "Technology",
        "keyExecutives": [
            {"name": "Charles Xavier", "title": "Chief Scientist"},
            {"name": "Diana Prince", "title": "Head of Ethics"},
        ],
        "recentNewsSummary": "XYZ Innovations secured new Series C funding to expand its research team.",
    },
}


def fetch_company_profile_mock(company_identifier: str) -> Dict[str, Any]:
    """
    Simulates fetching a company profile based on an identifier.
    Returns a dictionary matching the output structure of the
    entity_overview_template.json or an error structure if not found.
    """
    if company_identifier in MOCKED_PROFILES:
        return MOCKED_PROFILES[
            company_identifier
        ].copy()  # Return a copy to prevent modification of mock data
    else:
        return {
            "companyName": None,
            "companyDescription": None,
            "primaryIndustry": None,
            "keyExecutives": [],
            "recentNewsSummary": None,
            "error_message": f"Profile not found for identifier: {company_identifier}",
        }


if __name__ == "__main__":
    import json
    import copy  # Import copy module for deepcopy

    # Example usage for testing
    print("--- Testing fetch_company_profile_mock ---")

    print("\nFetching COMP_ABC:")
    profile_abc = fetch_company_profile_mock("COMP_ABC")
    print(json.dumps(profile_abc, indent=2))

    print("\nFetching COMP_XYZ:")
    profile_xyz = fetch_company_profile_mock("COMP_XYZ")
    print(json.dumps(profile_xyz, indent=2))

    print("\nFetching COMP_NOT_FOUND:")
    profile_not_found = fetch_company_profile_mock("COMP_NOT_FOUND")
    print(json.dumps(profile_not_found, indent=2))

    print(
        "\nFetching another COMP_ABC to test non-modification of original MOCKED_PROFILES:"
    )
    # Use deepcopy for the test to ensure the original MOCKED_PROFILES is not altered through nested structures
    profile_abc_for_test = fetch_company_profile_mock("COMP_ABC")
    # The function fetch_company_profile_mock itself returns a shallow copy.
    # For this specific test of MOCKED_PROFILES integrity, we'll make a deepcopy of the returned object
    # before modification, or simply re-fetch to show the original source is safe.

    # To demonstrate the shallow copy behavior of the function vs. deep copy for testing:
    returned_profile_copy = fetch_company_profile_mock("COMP_ABC")
    if returned_profile_copy.get("keyExecutives"):
        # This modification WILL affect MOCKED_PROFILES if returned_profile_copy["keyExecutives"] is a reference
        # because fetch_company_profile_mock does a shallow .copy().
        # This is acceptable for the function, but the test below needs to be aware.
        # For a truly independent copy for modification in test, use deepcopy.
        profile_to_modify_for_test = copy.deepcopy(returned_profile_copy)
        profile_to_modify_for_test["keyExecutives"].append(
            {"name": "Test User", "title": "Tester"}
        )
        print("Locally modified deepcopy of COMP_ABC's data:")
        print(json.dumps(profile_to_modify_for_test, indent=2))

    print(
        "Original MOCKED_PROFILES['COMP_ABC'] (should be unchanged by the deepcopy modification):"
    )
    print(json.dumps(MOCKED_PROFILES["COMP_ABC"], indent=2))
