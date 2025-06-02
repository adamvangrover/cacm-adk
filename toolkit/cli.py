# toolkit/cli.py
import click
import json
import asyncio

from toolkit.modules.web_search import WebSearchModule
from toolkit.modules.workflow_runner import WorkflowRunnerModule
from toolkit.modules.llm_wrapper import LLMWrapperModule
from toolkit.modules.kb_querier import KBQuerierModule # New import

__version__ = "0.1.3" # Increment version

@click.group()
@click.version_option(__version__)
def main():
    """
    A new Command-Line Interface for the CACM ADK.
    Provides simplified access to core ADK functionalities.
    """
    pass

@main.command(name="commands") # Renamed 'modules' to 'commands' for clarity
def list_commands():
    """Lists available high-level toolkit commands/groups."""
    click.echo("Available toolkit command groups/commands:")
    click.echo("- toolkit run <cacm_filepath>    : Runs a CACM workflow.")
    click.echo("- toolkit search <query>         : Performs a general web search.")
    click.echo("- toolkit llm list-skills        : Lists available LLM/Semantic Kernel skills.")
    click.echo("- toolkit llm invoke <p> <f>     : Invokes an LLM/Semantic Kernel skill.")
    click.echo("- toolkit kb list-classes        : Lists ontology classes.")
    click.echo("- toolkit kb get-details <uri>   : Gets details for an ontology entity.")
    click.echo("- toolkit kb find <keyword>      : Finds ontology concepts by keyword.")
    pass

# ... (search, llm_group, llm_list_skills, llm_invoke, run_workflow commands remain unchanged) ...
# Web Search Command
@main.command()
@click.argument("query", nargs=-1)
@click.option('--raw', is_flag=True, help="Display raw JSON output.")
def search(query, raw):
    search_module_instance = WebSearchModule() 
    if not query:
        click.echo("Error: Please provide a search query.", err=True)
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit(1)
        return 
    full_query = " ".join(query)
    click.echo(f"Performing general web search for: '{full_query}'...")
    results = search_module_instance.execute(context={}, query=full_query)
    
    if raw:
        click.echo(json.dumps(results, indent=2))
    else:
        if results.get("error"):
            click.echo(f"Error: {results['error']}", err=True)
        else:
            click.echo("\n--- Web Search Results (DuckDuckGo) ---")
            if results.get("abstract_text"):
                click.echo(f"Abstract: {results['abstract_text']}")
                if results.get("abstract_source"):
                    click.echo(f"Source: {results['abstract_source']} ({results.get('abstract_url', '')})")
            elif results.get("definition"):
                 click.echo(f"Definition: {results['definition']}")
                 if results.get("definition_source"): 
                    click.echo(f"Source: {results['definition_source']}")
            elif results.get("related_topics"): 
                click.echo("Related Topics (DDG):")
                for topic in results.get("related_topics", [])[:5]: 
                    click.echo(f"- {topic.get('text','')} ({topic.get('url','')})")
            else:
                click.echo("No specific abstract, definition, or related topics found via DDG Instant Answer.")
            click.echo(f"Raw DDG URL: {results.get('raw_ddg_url', 'N/A')}")

# LLM Commands
@main.group(name="llm")
def llm_group():
    """Interacts with the ADK's Semantic Kernel capabilities."""
    pass

@llm_group.command(name="list-skills")
def llm_list_skills():
    """Lists all available skills registered in the ADK's KernelService."""
    click.echo("Fetching available skills from KernelService...")
    click.echo("Note: LLM-based skills require OPENAI_API_KEY and OPENAI_ORG_ID environment variables to be set.")
    
    llm_module = LLMWrapperModule()
    result = llm_module.list_skills()

    if result.get("error"):
        click.secho(f"Error: {result['error']}", fg="red")
        return
    
    if not result.get("skills"):
        click.echo("No skills found or KernelService not fully initialized.")
        return

    click.echo("\n--- Available Semantic Kernel Skills ---")
    for skill_info in result["skills"]:
        click.echo(f"  Plugin: {skill_info['plugin_name']}")
        click.echo(f"    Function: {skill_info['function_name']}")
        click.echo(f"    Description: {skill_info['description']}")
        click.echo("-" * 20)

@llm_group.command(name="invoke")
@click.argument("plugin_name", type=str)
@click.argument("function_name", type=str)
@click.option("--args", "args_json", type=str, default="{}", 
              help='JSON string of arguments to pass to the skill. E.g., \'{"numerator": 10, "denominator": 2}\'')
def llm_invoke(plugin_name, function_name, args_json):
    """
    Invokes a specific skill by plugin and function name.
    Arguments are passed as a JSON string.
    Example: toolkit llm invoke BasicCalculations calculate_ratio --args \'{"numerator": 10, "denominator": 2}\'
    """
    click.echo(f"Invoking skill '{plugin_name}.{function_name}'...")
    click.echo("Note: LLM-based skills require OPENAI_API_KEY and OPENAI_ORG_ID environment variables to be set.")

    try:
        parsed_args = json.loads(args_json)
        if not isinstance(parsed_args, dict):
            raise ValueError("Arguments JSON must be a dictionary (object).")
    except json.JSONDecodeError:
        click.secho("Error: Invalid JSON string for arguments.", fg="red")
        return
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        return

    llm_module = LLMWrapperModule()
    result = asyncio.run(llm_module.invoke_skill_async(plugin_name, function_name, parsed_args))

    if result.get("error"):
        click.secho(f"Error: {result['error']}", fg="red")
    else:
        click.echo("\n--- Skill Invocation Result ---")
        if isinstance(result.get("result"), (dict, list)):
            click.echo(json.dumps(result["result"], indent=2))
        else:
            click.echo(result.get("result"))

# Workflow Runner Command
@main.command(name="run")
@click.argument("cacm_filepath", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--output-dir', type=click.Path(file_okay=False, resolve_path=True), default=None, 
              help="Directory to save generated reports.")
@click.option('--verbose', is_flag=True, help="Print detailed logs.")
def run_workflow(cacm_filepath, output_dir, verbose):
    click.echo(f"Initializing workflow for CACM file: {cacm_filepath}")
    if output_dir:
        click.echo(f"Custom report output directory: {output_dir}")

    runner_module = WorkflowRunnerModule()
    results = runner_module.execute(cacm_filepath=cacm_filepath, output_dir=output_dir)

    if verbose or results.get("status") == "failed": 
        click.echo("\n--- Execution Logs ---")
        for log_entry in results.get("logs", []):
            click.echo(log_entry)
        click.echo("--- End of Logs ---")
    
    click.echo(f"\nStatus: {results.get('status')}")
    click.echo(f"Message: {results.get('message')}")

    if results.get("status") == "success" and results.get("outputs"):
        click.echo("\n--- Workflow Outputs (Summary) ---")
        for out_name, out_data in results.get("outputs", {}).items():
            out_val = out_data.get('value', 'N/A')
            if isinstance(out_val, dict) and 'content' in out_val and 'file_path' in out_val:
                click.echo(f"- {out_name}: Report package (see logs for save path if verbose)")
            else:
                click.echo(f"- {out_name}: (type: {type(out_val).__name__})")
    elif results.get("status") == "failed" and not verbose: 
         click.secho("Workflow execution failed. Use --verbose for detailed logs.", fg="yellow")


# --- Knowledge Base Commands ---
@main.group(name="kb")
def kb_group():
    """Interacts with the ADK's Knowledge Base via OntologyNavigator."""
    pass

@kb_group.command(name="list-classes")
@click.option("--namespace", default=None, help="Namespace prefix to filter classes (e.g., 'adkarch', 'cacm_ont').")
@click.option("--ontology-path", type=click.Path(exists=True, dir_okay=False, resolve_path=True), default=None, help="Custom path to the ontology TTL file.")
def kb_list_classes(namespace, ontology_path):
    """Lists OWL classes from the ontology."""
    click.echo("Fetching ontology classes...")
    querier = KBQuerierModule(ontology_path=ontology_path)
    results = querier.list_classes(namespace_filter=namespace)

    if results.get("error"):
        click.secho(f"Error: {results['error']}", fg="red")
    elif not results.get("classes"):
        click.echo(results.get("message", "No classes found."))
    else:
        click.echo("\n--- Ontology Classes ---")
        for cls_uri in results["classes"]:
            click.echo(f"- {cls_uri}")

@kb_group.command(name="get-details")
@click.argument("entity_uri", type=str)
@click.option("--ontology-path", type=click.Path(exists=True, dir_okay=False, resolve_path=True), default=None, help="Custom path to the ontology TTL file.")
def kb_get_details(entity_uri, ontology_path):
    """Retrieves details for a given ontology entity (class or property)."""
    click.echo(f"Fetching details for entity: {entity_uri}...")
    querier = KBQuerierModule(ontology_path=ontology_path)
    results = querier.get_entity_details(entity_uri)

    if results.get("error"):
        click.secho(f"Error: {results['error']}", fg="red")
    else:
        click.echo("\n--- Entity Details ---")
        click.echo(json.dumps(results, indent=2))

@kb_group.command(name="find")
@click.argument("keyword", type=str)
@click.option("--ontology-path", type=click.Path(exists=True, dir_okay=False, resolve_path=True), default=None, help="Custom path to the ontology TTL file.")
def kb_find(keyword, ontology_path):
    """Finds ontology concepts (classes, properties) by keyword in labels."""
    click.echo(f"Searching for concepts with keyword: {keyword}...")
    querier = KBQuerierModule(ontology_path=ontology_path)
    results = querier.find_concepts(keyword)

    if results.get("error"):
        click.secho(f"Error: {results['error']}", fg="red")
    elif not results.get("found_concepts"):
        click.echo("No concepts found matching the keyword.")
    else:
        click.echo("\n--- Found Concepts ---")
        click.echo(json.dumps(results["found_concepts"], indent=2))

if __name__ == "__main__":
    main()
