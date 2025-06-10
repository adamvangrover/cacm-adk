#!/usr/bin/env python3
"""
Interactive Expertise Builder for Data Mesh Ontology Framework.

Purpose:
This script provides an interactive command-line interface (CLI) to guide users
through the process of defining a new area of expertise. It captures user requirements
and intentions regarding data sources, machine learning tasks, and potential federated
learning setups.

How to Run:
- If `framework.py` and this script are in the same directory:
  `python interactive_expertise_builder.py`
- If the `ontology` directory is part of a larger Python package and in PYTHONPATH:
  `python -m ontology.data_mesh_ontology.interactive_expertise_builder`

Input:
The script takes input interactively from the user via command-line prompts.
It asks a series of questions about the expertise goal, relevant concepts,
information needs, data sources, potential ML tasks, and federated learning considerations.

Output:
The script generates several JSON files in the same directory where it is run.
These files are named using a unique `expertise_id` generated for each session:
  - `{expertise_id}_data_artifacts.json`: Contains a list of DataArtifact definitions.
  - `{expertise_id}_ml_model.json`: Contains the definition for a proposed MLModel.
  - `{expertise_id}_federated_setup.json`: Contains the definition for a federated learning setup, if configured.
  (Optionally, a full dump of all user inputs can be saved for debugging or regeneration purposes.)

Intended Usage of Output:
The generated JSON files contain structured definitions that *mirror the attributes* of the
classes defined in `framework.py` (e.g., DataArtifact, MLModel). These files are
designed to be ingested by other processes, scripts, or a dedicated "Ontology Population"
module. Such a module would then parse these JSON definitions and use the actual methods
provided by `framework.py` (e.g., `KnowledgeStore.register_artifact()`,
`MachineLearningGuidance.register_model()`) to instantiate and register these components
within a live instance of the data mesh ontology framework. This script *prepares*
the definitions; it does not directly instantiate or modify live framework objects.

Key Dependencies:
- `framework.py`: This script generates definitions that are structurally based on the classes
  (DataArtifact, MLModel, FederatedLearningInfra, etc.) defined in `framework.py`.
  For direct execution (`python interactive_expertise_builder.py`), `framework.py`
  should ideally be in the same directory or accessible via PYTHONPATH.
- Standard Python libraries: `json`, `uuid`, `datetime`, `typing`.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

# --- Framework Interaction Note ---
# This script is a definition generator. It creates dictionary representations (JSON)
# that are *structurally similar* to the classes in `framework.py`.
# It does NOT directly instantiate objects from `framework.py` (e.g., DataArtifact instances)
# or interact with a live KnowledgeStore or other active framework components.
# The output JSON files are intended to be used by a separate process that *would*
# use `framework.py` to populate the ontology.

# Framework imports:
# For this script to run directly and for clarity, framework.py is assumed to be
# in the same directory or accessible in PYTHONPATH.
from framework import (
    OntologyElement, KnowledgeStore, DataArtifact, MLModel,
    SkillDefinition, MachineLearningGuidance, FederatedLearningInfra,
    FederatedLearningNode, OntologyAgent, ContextManager, Concept, Relationship
    # Logger, VersionControl # Not directly used for definition generation here yet
)


def get_user_input(prompt_message: str, default_value: Optional[str] = None) -> str:
    """
    A simple wrapper around input() that can display a default value
    and return it if the user enters nothing.
    """
    if default_value:
        prompt_with_default = f"{prompt_message} (default: {default_value}): "
    else:
        prompt_with_default = f"{prompt_message}: "

    user_response = input(prompt_with_default).strip()

    if not user_response and default_value is not None:
        return default_value
    return user_response

def save_to_json(data: Any, filename: str):
    """Helper function to save data to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully saved configuration to: {filename}")
    except IOError as e:
        print(f"Error saving configuration to {filename}: {e}")
    except TypeError as e:
        print(f"Error serializing data to JSON for {filename}: {e}")


def get_expertise_goal(config: Dict[str, Any]) -> None:
    """Gathers information about the main expertise goal."""
    print("\n--- Defining Expertise Goal ---")
    goal = get_user_input(
        "What subject or domain of expertise do you want the system to develop?",
        "Understanding sentiment in financial news for tech companies"
    )
    config['expertise_goal'] = goal

    description = get_user_input(
        "Provide a brief description for this expertise goal.",
        f"To analyze financial news articles and determine the sentiment towards specific tech companies mentioned."
    )
    config['expertise_description'] = description
    config['timestamp_goal_defined'] = datetime.now(timezone.utc).isoformat()

def get_keywords_and_concepts(config: Dict[str, Any]) -> None:
    """Gathers related keywords and their optional definitions."""
    print("\n--- Identifying Key Concepts and Keywords ---")
    keywords_str = get_user_input(
        "List key terms, concepts, or entities related to this expertise (comma-separated).",
        "financial news, tech companies, sentiment analysis, stock market, NLP"
    )
    config['related_keywords'] = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]

    concept_definitions: Dict[str, str] = {}
    if config['related_keywords']:
        print("\nLet's define some of these terms (optional):")
        # This part could be expanded to generate Concept object definitions.
        for term in config['related_keywords']:
            definition = get_user_input(f"Can you provide a brief definition for '{term}'? (Press Enter to skip)")
            if definition:
                concept_definitions[term] = definition
    config['concept_definitions'] = concept_definitions

def determine_information_needs(config: Dict[str, Any]) -> None:
    """Determines categories of information and potential data sources."""
    print("\n--- Determining Information Needs and Data Sources ---")
    # This section gathers raw user input about data sources.
    # The `generate_data_artifact_definitions` function will later process this
    # into structured DataArtifact-like dictionaries.
    config['data_sources_input'] = []

    categories_str = get_user_input(
        "To achieve this expertise, what general categories of information should the system learn about? (comma-separated)",
        "financial news articles, list of publicly traded tech companies, sentiment lexicons, stock price data"
    )
    config['information_categories'] = [cat.strip() for cat in categories_str.split(',') if cat.strip()]

    if config['information_categories']:
        print("\nFor each category, let's specify data source types and potential URIs:")
        for category in config['information_categories']:
            print(f"\nCategory: {category}")
            source_types_desc = get_user_input(
                f"  What specific types of data sources should the system look for or what kind of information should be gathered for '{category}'?",
                "News APIs, financial data providers, company databases, pre-built sentiment word lists"
            )
            specific_uris_str = get_user_input(
                f"  Do you know any specific URIs (websites, API endpoints, dataset names) for '{category}'? (comma-separated, or press Enter to skip)"
            )
            specific_uris = [uri.strip() for uri in specific_uris_str.split(',') if uri.strip()]

            config['data_sources_input'].append({
                "category_name": category,
                "source_types_description": source_types_desc,
                "specific_uris": specific_uris
            })

def configure_federated_learning(config: Dict[str, Any]) -> None:
    """Configures federated learning if applicable, based on user input."""
    print("\n--- Configuring Federated Learning (Optional) ---")
    config['federated_learning_setup'] = {} # Initialize the setup dictionary

    use_fl = get_user_input(
        "Given that data for this expertise might come from multiple, potentially sensitive or distributed sources, "
        "would a federated learning approach be suitable for training a model? (yes/no)",
        "no"
    ).lower()

    if use_fl == 'yes':
        config['federated_learning_setup']['enabled'] = True

        # Use the categories defined in `determine_information_needs`
        available_categories = [ds_input['category_name'] for ds_input in config.get('data_sources_input', [])]
        if not available_categories:
            print("Warning: No data source categories were defined in the previous step. Cannot select sources for federated learning.")
            config['federated_learning_setup']['source_categories'] = []
        else:
            print(f"Available data source categories for potential FL participation: {', '.join(available_categories)}")
            fl_source_categories_str = get_user_input(
                "Which of the identified data source categories should be considered for federated learning? (Provide comma-separated names, or type 'ALL')",
                "ALL"
            )
            if fl_source_categories_str.upper() == 'ALL':
                config['federated_learning_setup']['source_categories'] = available_categories
            else:
                # Filter user input to include only valid, previously defined categories
                config['federated_learning_setup']['source_categories'] = [
                    cat.strip() for cat in fl_source_categories_str.split(',') if cat.strip() in available_categories
                ]

        aggregation_strategy = get_user_input(
            "What aggregation strategy would you prefer for federated learning? (e.g., FedAvg, FedProx, or press Enter for default 'FedAvg')",
            "FedAvg"
        )
        config['federated_learning_setup']['aggregation_strategy'] = aggregation_strategy
    else:
        config['federated_learning_setup']['enabled'] = False

def define_learning_task(config: Dict[str, Any]) -> None:
    """Defines the primary learning task and suggestive model characteristics based on user input."""
    print("\n--- Defining the Primary Learning Task ---")
    config['learning_task'] = {} # Initialize the task dictionary

    goal_for_prompt = config.get('expertise_goal', 'the defined expertise goal')
    task_type = get_user_input(
        f"Based on the expertise goal ('{goal_for_prompt}'), what kind of primary learning task does this translate to?",
        "text classification for sentiment"
    )
    config['learning_task']['task_type'] = task_type

    model_type_suggestion = get_user_input(
        "What type of model might be appropriate for this task? (e.g., 'transformer-based classifier', 'BERT for NER', 'custom knowledge graph population model')",
        "transformer-based classifier (e.g., FinBERT)"
    )
    config['learning_task']['model_type_suggestion'] = model_type_suggestion

    # These descriptions will help in formulating the input/output schemas for the MLModel definition.
    input_description = get_user_input(
        "Can you describe the desired input for this model? (e.g., 'a block of text from a news article', 'list of company financials')",
        "A news article text and the name of the tech company in focus."
    )
    config['learning_task']['input_description'] = input_description

    output_description = get_user_input(
        "Can you describe the desired output of this model? (e.g., 'sentiment label: positive/negative/neutral', 'list of recognized company names and their stock symbols')",
        "Sentiment label (positive, negative, neutral) for the company in the article."
    )
    config['learning_task']['output_description'] = output_description


# --- Processing Functions to Generate Definitions ---

def generate_data_artifact_definitions(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generates a list of DataArtifact-like dictionary definitions from user input.
    These dictionaries mirror the structure of the `DataArtifact` class in `framework.py`.
    """
    artifact_defs: List[Dict[str, Any]] = []
    timestamp = datetime.now(timezone.utc).isoformat()

    # Process the 'data_sources_input' collected from the user.
    for source_input in config.get('data_sources_input', []):
        category_name = source_input['category_name']

        # Assumption: Infer data_type and mime_type conceptually based on user descriptions/URIs.
        # This is a heuristic and might need refinement or more direct user input in a production tool.
        data_type = "user_specified_collection" # Default if not inferable
        mime_type = None # Optional
        first_uri = source_input['specific_uris'][0] if source_input['specific_uris'] else ""

        if "api" in source_input['source_types_description'].lower() or "api" in first_uri.lower():
            data_type = "structured_api_feed" # Conceptual type
            mime_type = "application/json"
        elif "news" in category_name.lower() or \
             "website" in source_input['source_types_description'].lower() or \
             first_uri.startswith("http"):
            data_type = "unstructured_text_webpage" # Conceptual type
            mime_type = "text/html"
        elif "database" in source_input['source_types_description'].lower():
            data_type = "structured_database_table" # Conceptual type
        elif "lexicon" in category_name.lower() or "word list" in source_input['source_types_description'].lower():
            data_type = "semi_structured_lexicon" # Conceptual type
            mime_type = "text/plain"

        # Mapping user input to DataArtifact fields:
        if source_input['specific_uris']:
            for uri_count, uri in enumerate(source_input['specific_uris']):
                artifact_def = {
                    "id": str(uuid.uuid4()),
                    "name": f"DS: {category_name} - URI {uri_count+1}", # More specific name
                    "description": f"Data source for category '{category_name}'. User description: {source_input['source_types_description']}. Specific URI: {uri}",
                    "version": "0.1.0", # Initial version for a new definition
                    "created_at": timestamp, # Align with DataArtifact class attribute
                    "updated_at": timestamp, # Align with DataArtifact class attribute
                    "source_uri": uri,
                    "data_type": data_type, # Inferred data_type
                    "mime_type": mime_type, # Inferred mime_type
                    "metadata": {
                        "original_category": category_name,
                        "user_input_source_description": source_input['source_types_description'],
                        "builder_script_version": config.get("builder_version")
                    },
                    "status": "raw_unverified" # Initial status for a newly defined artifact
                }
                artifact_defs.append(artifact_def)
        else: # If no specific URIs, create a general placeholder artifact for the category.
            artifact_def = {
                "id": str(uuid.uuid4()),
                "name": f"Data Collection Area: {category_name}",
                "description": f"Represents a need to collect data for category '{category_name}'. User description: {source_input['source_types_description']}.",
                "version": "0.1.0",
                "created_at": timestamp,
                "updated_at": timestamp,
                "source_uri": f"placeholder_collection_uri_for_{category_name.lower().replace(' ', '_')}", # Placeholder URI
                "data_type": data_type, # Broadly inferred data_type
                "mime_type": mime_type,
                "metadata": {
                    "original_category": category_name,
                    "user_input_source_description": source_input['source_types_description'],
                    "requires_identification": True, # Flag that specific sources are needed
                    "builder_script_version": config.get("builder_version")
                },
                "status": "definition_pending_sources"
            }
            artifact_defs.append(artifact_def)

    return artifact_defs

def generate_ml_model_definition(config: Dict[str, Any], data_artifact_ids: List[str]) -> Optional[Dict[str, Any]]:
    """
    Generates an MLModel-like dictionary definition from user input.
    This dictionary mirrors the structure of the `MLModel` class in `framework.py`.
    """
    learning_task = config.get('learning_task')
    # Only generate a model if a learning task was defined.
    if not learning_task or not learning_task.get('task_type'):
        print("Skipping ML Model definition: No learning task was specified by the user.")
        return None

    timestamp = datetime.now(timezone.utc).isoformat()
    model_id = str(uuid.uuid4())

    # Simplified schema generation based on user descriptions.
    # A more advanced builder might ask for specific field names and types for schema properties.
    input_schema = {
        "description": learning_task['input_description'],
        "type": "object",
        "properties": {"input_feature_1": {"type": "string", "description": "Example input feature based on user description."}}
    }
    if "text" in learning_task['input_description'].lower():
        input_schema["properties"]["input_feature_1"]["format"] = "text_content"

    output_schema = {
        "description": learning_task['output_description'],
        "type": "object",
        "properties": {"output_value_1": {"type": "string", "description": "Example output value based on user description."}}
    }
    if "label" in learning_task['output_description'].lower() or "category" in learning_task['output_description'].lower():
         output_schema["properties"]["output_value_1"]["format"] = "categorical_label"

    # Mapping user input to MLModel fields:
    model_def = {
        "id": model_id,
        "name": f"ML Model for: {config.get('expertise_goal', 'Undefined Expertise Goal')[:40]}...", # Truncate for brevity
        "description": f"Proposed ML model to address the expertise goal: '{config.get('expertise_goal', '')}'. Based on user-defined learning task: '{learning_task['task_type']}'.",
        "version": "0.1.0", # Initial version
        "created_at": timestamp, # Align with MLModel class attribute
        "updated_at": timestamp, # Align with MLModel class attribute
        "model_type": learning_task['model_type_suggestion'],
        "input_schema": input_schema,
        "output_schema": output_schema,
        "context_dependencies": config.get('related_keywords', []), # Keywords can be context dependencies
        "training_data_artifacts": data_artifact_ids, # Link to generated DataArtifact IDs
        "model_uri_or_identifier": f"placeholder_model_uri_for_{config.get('expertise_id', 'default_model_id')}", # To be replaced after training
        "performance_metrics": {}, # To be populated after evaluation
        "metadata": {
            "source_expertise_goal": config.get('expertise_goal'),
            "defined_learning_task": learning_task,
            "builder_script_version": config.get("builder_version")
        }
    }
    return model_def

def generate_federated_learning_setup(config: Dict[str, Any], model_id: Optional[str],
                                      artifact_category_to_id_map: Dict[str, List[str]]) -> Optional[Dict[str, Any]]:
    """
    Generates a FederatedLearningInfra-like dictionary definition if FL is enabled.
    This dictionary mirrors the structure of the `FederatedLearningInfra` class in `framework.py`.
    """
    fl_setup_input = config.get('federated_learning_setup', {})
    # Only generate if FL is enabled and a model ID is available (as FL trains a specific model).
    if not fl_setup_input.get('enabled') or not model_id:
        return None

    timestamp = datetime.now(timezone.utc).isoformat()
    participating_artifact_ids_by_category: Dict[str, List[str]] = {}

    # Map selected categories for FL to their respective DataArtifact IDs.
    for category in fl_setup_input.get('source_categories', []):
        if category in artifact_category_to_id_map and artifact_category_to_id_map[category]:
            participating_artifact_ids_by_category[category] = artifact_category_to_id_map[category]
        else:
            print(f"Warning (FL Setup): Category '{category}' selected for FL, but no corresponding DataArtifacts found. It will be excluded.")

    if not participating_artifact_ids_by_category:
        print("Warning (FL Setup): No valid DataArtifacts found for any selected FL categories. Skipping FL setup generation.")
        return None

    num_potential_nodes = len(participating_artifact_ids_by_category) # Assuming one node per category for this conceptual setup.

    # Mapping user input to FederatedLearningInfra fields:
    fl_setup_def = {
        "id": str(uuid.uuid4()), # ID for the FL infrastructure setup itself
        "name": f"FL Setup: {config.get('expertise_goal', 'Undefined Expertise Goal')[:40]}...",
        "version": "0.1.0",
        "created_at": timestamp, # Align with OntologyElement attributes
        "updated_at": timestamp, # Align with OntologyElement attributes
        "current_global_model_id": model_id, # Link to the MLModel to be trained
        "aggregation_strategy": fl_setup_input.get('aggregation_strategy', 'FedAvg'),
        # This maps category names to lists of DataArtifact IDs that would conceptually reside on nodes associated with that category.
        "data_distribution_plan_by_category": participating_artifact_ids_by_category,
        "conceptual_nodes_count": num_potential_nodes, # Indicates how many nodes might be needed.
                                                       # Actual FederatedLearningNode definitions would be separate.
        "training_rounds_completed": 0,
        "metadata": {
            "description": "Initial setup definition for federated learning, generated by the interactive builder.",
            "source_expertise_goal": config.get('expertise_goal'),
            "user_selected_fl_categories": fl_setup_input.get('source_categories', []),
            "builder_script_version": config.get("builder_version")
        }
    }
    return fl_setup_def


def build_expertise_interactively():
    """
    Main function to drive the interactive expertise building process.
    This function guides the user through defining various ontology elements
    and then saves the generated definitions (as dictionaries) to JSON files.
    """
    print("Welcome to the Interactive Expertise Builder for the Data Mesh Ontology!")
    print("This tool will help you define components for your data mesh.\n")

    # Initialize a dictionary to hold all configuration gathered from the user.
    expertise_config: Dict[str, Any] = {
        "builder_version": "0.3.0", # Version of this builder script.
        "generation_date": datetime.now(timezone.utc).isoformat(),
        "expertise_id": str(uuid.uuid4()) # Unique ID for this entire expertise definition session.
    }

    # --- Interactive Dialogue Flow ---
    # Each function populates parts of the `expertise_config` dictionary.
    get_expertise_goal(expertise_config)
    get_keywords_and_concepts(expertise_config)
    determine_information_needs(expertise_config)
    configure_federated_learning(expertise_config) # Depends on data_sources_input being populated
    define_learning_task(expertise_config)

    print("\n\n--- Generating Ontology Element Definitions (JSON) ---")

    # --- Process collected configuration and generate structured definitions ---

    # 1. Generate DataArtifact definitions
    artifact_defs = generate_data_artifact_definitions(expertise_config)
    if artifact_defs:
        artifact_filename = f"{expertise_config['expertise_id']}_data_artifacts.json"
        save_to_json(artifact_defs, artifact_filename)
        # Guidance for the user:
        print(f"  - The '{artifact_filename}' contains definitions for potential DataArtifacts.")
        print(f"    These can be used to register artifacts in a KnowledgeStore instance from framework.py.")
        print(f"    Each definition includes a 'source_uri', 'data_type', and initial 'status'.")
    else:
        print("  - No data artifact definitions were generated based on your input.")

    # Create a map of data source category_name to a list of generated DataArtifact IDs.
    # This is useful for linking in the Federated Learning setup.
    artifact_category_to_id_map: Dict[str, List[str]] = {}
    for art_def in artifact_defs:
        category = art_def.get('metadata', {}).get('original_category')
        if category: # Ensure category exists
            if category not in artifact_category_to_id_map:
                artifact_category_to_id_map[category] = []
            artifact_category_to_id_map[category].append(art_def['id'])

    # 2. Generate MLModel definition
    # Pass IDs of all generated artifacts as potential training data.
    # A more refined process might let the user select specific artifacts for training.
    all_artifact_ids = [art['id'] for art in artifact_defs]
    model_def = generate_ml_model_definition(expertise_config, all_artifact_ids)
    model_id_for_fl: Optional[str] = None # To store the model ID if a model is defined.

    if model_def:
        model_filename = f"{expertise_config['expertise_id']}_ml_model.json"
        save_to_json(model_def, model_filename)
        model_id_for_fl = model_def['id']
        # Guidance for the user:
        print(f"  - The '{model_filename}' contains a definition for a proposed MLModel.")
        print(f"    This can be used to register a model with MachineLearningGuidance from framework.py.")
        print(f"    It includes suggested 'model_type', I/O schemas, and links to 'training_data_artifacts'.")

    else:
        print("  - No ML model definition was generated based on your input (e.g., learning task not specified).")

    # 3. Generate FederatedLearningInfra setup definition (if applicable)
    if model_id_for_fl: # Only attempt to generate FL setup if an ML model was defined.
        fl_setup_def = generate_federated_learning_setup(expertise_config, model_id_for_fl, artifact_category_to_id_map)
        if fl_setup_def:
            fl_filename = f"{expertise_config['expertise_id']}_federated_setup.json"
            save_to_json(fl_setup_def, fl_filename)
            # Guidance for the user:
            print(f"  - The '{fl_filename}' contains a definition for a Federated Learning setup.")
            print(f"    This can be used to configure a FederatedLearningInfra instance from framework.py.")
            print(f"    It links to the global model and maps data categories to artifact IDs for FL participation.")
        else:
            if expertise_config.get('federated_learning_setup', {}).get('enabled'):
                 print("  - Federated learning was enabled, but its setup definition could not be fully generated (e.g., no suitable data artifacts found for selected categories).")
            else:
                 print("  - Federated learning was not enabled by the user; no FL setup file generated.")
    else:
        print("  - Skipping federated learning setup generation as no ML model was defined.")

    # Optionally, save the raw collected configuration for debugging or full context.
    # full_config_filename = f"{expertise_config['expertise_id']}_full_user_input_config.json"
    # save_to_json(expertise_config, full_config_filename)
    # print(f"  - For reference, the complete set of your inputs has been saved to '{full_config_filename}'.")

    print("\nInteractive expertise building and definition generation session finished.")
    print("You can now use the generated JSON files to populate your data mesh ontology framework.")

if __name__ == '__main__':
    # This is the entry point when the script is run directly.
    build_expertise_interactively()
