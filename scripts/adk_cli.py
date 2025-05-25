#!/usr/bin/env python3
# scripts/adk_cli.py
import json
import os
import click # type: ignore

# Adjust import paths based on running CLI from project root
# This assumes .venv is activated and project root is in PYTHONPATH, or running with python -m scripts.adk_cli
try:
    from cacm_adk_core.template_engine.template_engine import TemplateEngine
    from cacm_adk_core.validator.validator import Validator
    from cacm_adk_core.orchestrator.orchestrator import Orchestrator
except ImportError:
    # Fallback for direct execution from scripts/ if core modules are not found
    # This typically means PYTHONPATH isn't set up correctly for direct script execution.
    # Running as 'python -m scripts.adk_cli' from root is preferred.
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from cacm_adk_core.template_engine.template_engine import TemplateEngine
    from cacm_adk_core.validator.validator import Validator
    from cacm_adk_core.orchestrator.orchestrator import Orchestrator


# --- Reusable instances ---
# These paths assume the CLI is run from the project's root directory.
DEFAULT_SCHEMA_PATH = "cacm_standard/cacm_schema_v0.2.json"
DEFAULT_CATALOG_PATH = "config/compute_capability_catalog.json"
DEFAULT_TEMPLATES_PATH = "cacm_library/templates"

def get_validator():
    if not os.path.exists(DEFAULT_SCHEMA_PATH):
        click.echo(f"Error: CACM Schema not found at {DEFAULT_SCHEMA_PATH}. Cannot proceed.", err=True)
        return None
    return Validator(schema_filepath=DEFAULT_SCHEMA_PATH)

def get_template_engine():
    return TemplateEngine(templates_dir=DEFAULT_TEMPLATES_PATH)

def get_orchestrator(validator_instance):
    if validator_instance is None: return None # Already handled by get_validator
    if not os.path.exists(DEFAULT_CATALOG_PATH):
        click.echo(f"Error: Compute Capability Catalog not found at {DEFAULT_CATALOG_PATH}. Orchestrator may not function fully.", err=True)
        # Orchestrator init handles this by creating an empty catalog, so we can proceed
    return Orchestrator(validator=validator_instance, catalog_filepath=DEFAULT_CATALOG_PATH)


@click.group()
def cli():
    """CACM Authoring & Development Kit (ADK) CLI Tool"""
    pass

@cli.command("list-templates")
def list_templates():
    """Lists available CACM templates."""
    engine = get_template_engine()
    if not os.path.isdir(engine.templates_dir):
        click.echo(f"Error: Templates directory not found: {engine.templates_dir}", err=True)
        return

    templates = engine.list_templates()
    if not templates:
        click.echo("No templates found.")
        return
    
    click.echo("Available CACM Templates:")
    for template_info in templates:
        click.echo(f"  - {template_info['name']} ({template_info['filename']})")
        click.echo(f"    Description: {template_info['description']}")
        click.echo("-" * 20)

@cli.command("instantiate")
@click.argument("template_filename", type=str)
@click.argument("output_filepath", type=click.Path())
@click.option("--cacm-id", default=None, help="Specific UUID for the new CACM.")
@click.option("--name", default=None, help="Name for the new CACM (overrides template).")
@click.option("--description", default=None, help="Description for the new CACM (overrides template).")
# Add more override options as needed, e.g., --author, --tags (comma-separated)
def instantiate_template_cmd(template_filename, output_filepath, cacm_id, name, description):
    """Instantiates a CACM template and saves it to a file."""
    engine = get_template_engine()
    if not os.path.isdir(engine.templates_dir): # Check again in case it was created after engine init
        click.echo(f"Error: Templates directory not found: {engine.templates_dir}", err=True)
        return

    overrides = {}
    if name: overrides["name"] = name
    if description: overrides["description"] = description
    # Example for a nested override, assuming 'metadata' exists in template
    # if author: 
    #   if "metadata" not in overrides: overrides["metadata"] = {}
    #   overrides["metadata"]["author"] = author

    instance = engine.instantiate_template(template_filename, cacm_id=cacm_id, overrides=overrides if overrides else None)
    
    if instance:
        try:
            with open(output_filepath, "w") as f:
                json.dump(instance, f, indent=2)
            click.echo(f"Successfully instantiated template '{template_filename}' to '{output_filepath}'")
            click.echo(f"New CACM ID: {instance['cacmId']}")
        except IOError as e:
            click.echo(f"Error writing to output file {output_filepath}: {e}", err=True)
    else:
        click.echo(f"Error: Could not instantiate template '{template_filename}'. Check logs or template existence.", err=True)

@cli.command("validate")
@click.argument("cacm_filepath", type=click.Path(exists=True, dir_okay=False))
def validate_cacm_cmd(cacm_filepath):
    """Validates a CACM JSON file against the schema."""
    validator = get_validator()
    if not validator or not validator.schema:
        click.echo("Error: Validator or schema could not be initialized. Cannot validate.", err=True)
        return

    try:
        with open(cacm_filepath, "r") as f:
            cacm_instance_data = json.load(f)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON in file {cacm_filepath}: {e}", err=True)
        return
    except IOError as e:
        click.echo(f"Error reading file {cacm_filepath}: {e}", err=True)
        return
        
    is_valid, errors = validator.validate_cacm_against_schema(cacm_instance_data)
    
    if is_valid:
        click.echo(click.style(f"CACM file '{cacm_filepath}' is VALID according to the schema.", fg="green"))
    else:
        click.echo(click.style(f"CACM file '{cacm_filepath}' is INVALID:", fg="red"))
        for error in errors:
            click.echo(f"  - Path: {'.'.join(map(str, error.get('path', [])))}")
            click.echo(f"    Message: {error.get('message')}")
            click.echo(f"    Validator: {error.get('validator')}")


@cli.command("run")
@click.argument("cacm_filepath", type=click.Path(exists=True, dir_okay=False))
def run_cacm_cmd(cacm_filepath):
    """Simulates the execution of a CACM file's workflow."""
    validator = get_validator()
    if not validator or not validator.schema:
        click.echo("Error: Validator or schema could not be initialized for pre-run validation.", err=True)
        return
    
    orchestrator = get_orchestrator(validator)
    if not orchestrator:
         click.echo("Error: Orchestrator could not be initialized.", err=True)
         return
    if not orchestrator.compute_catalog: # Check if catalog loaded properly
        click.echo("Warning: Compute capability catalog was not loaded. 'run' may provide limited capability checks.", err=True)


    try:
        with open(cacm_filepath, "r") as f:
            cacm_instance_data = json.load(f)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON in file {cacm_filepath}: {e}", err=True)
        return
    except IOError as e:
        click.echo(f"Error reading file {cacm_filepath}: {e}", err=True)
        return

    click.echo(f"Attempting to run CACM: {cacm_filepath}")
    success = orchestrator.run_cacm(cacm_instance_data)
    
    if success:
        click.echo(click.style("CACM workflow simulation completed.", fg="green"))
    else:
        click.echo(click.style("CACM workflow simulation failed or did not run due to validation errors.", fg="red"))


if __name__ == '__main__':
    # Ensure the script can be executed directly for development/testing
    # For robust CLI, users should install the package and run the registered entry point.
    # To make it runnable from root as `python scripts/adk_cli.py ...`:
    import sys # Ensure sys is imported for __main__
    if "__file__" in globals() and os.path.dirname(__file__) not in sys.path:
         sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    cli()
