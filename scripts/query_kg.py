from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS, XSD, OWL, DCTERMS

# Define Namespaces (ensure these match your ontology and instance files)
KGCLASS = Namespace("http://example.com/ontology/cacm_credit_ontology/0.3/classes/#")
KGPROP = Namespace("http://example.com/ontology/cacm_credit_ontology/0.3/properties/#")
KB_INSTANCE = Namespace("http://example.org/kb_instances/#")
CACM_ONT = Namespace("http://example.com/ontology/cacm_credit_ontology/0.3#")

def execute_queries():
    g = Graph()

    # Define ontology and instance file paths
    ontology_file = "ontology/credit_analysis_ontology_v0.3/credit_ontology_v0.3.ttl"
    instances_file = "knowledge_graph_instantiations/kb_core_instances.ttl" # Updated name from previous step

    try:
        g.parse(ontology_file, format="turtle")
        print(f"Successfully parsed ontology file: {ontology_file}")
    except Exception as e:
        print(f"Error parsing ontology file {ontology_file}: {e}")
        return

    try:
        g.parse(instances_file, format="turtle")
        print(f"Successfully parsed instances file: {instances_file}")
    except Exception as e:
        print(f"Error parsing instances file {instances_file}: {e}")
        # Decide if you want to proceed with only ontology data or return
        # For this script, we'll proceed to see what ontology-only queries might return
        pass # Or return

    # Bind prefixes for cleaner query display (optional but good practice)
    g.bind("kgclass", KGCLASS)
    g.bind("kgprop", KGPROP)
    g.bind("kb", KB_INSTANCE) # kb for kb_instance
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("owl", OWL)
    g.bind("xsd", XSD)
    g.bind("dcterms", DCTERMS)
    g.bind("cacm_ont", CACM_ONT)


    print("\n--- Query 1: List all Financial Formulas ---")
    q1 = """
    SELECT ?formula ?label WHERE {
        ?formula rdf:type kgclass:FinancialFormula ;
                 rdfs:label ?label .
    }
    """
    results1 = g.query(q1)
    if not results1: print("No results.")
    for row in results1:
        print(f"Formula: {row.formula}, Label: {row.label}")

    print("\n--- Query 2: List all Risk Factors and their descriptions ---")
    q2 = """
    SELECT ?risk_factor ?description WHERE {
        ?risk_factor rdf:type kgclass:RiskFactor ;
                     rdfs:comment ?description .
    }
    """
    results2 = g.query(q2)
    if not results2: print("No results.")
    for row in results2:
        print(f"Risk Factor: {row.risk_factor}, Description: {row.description}")

    print("\n--- Query 3: List all Macroeconomic Indicators and their sources ---")
    q3 = """
    SELECT ?indicator ?label ?source WHERE {
        ?indicator rdf:type kgclass:EconomicIndicator ;
                   rdfs:label ?label ;
                   dcterms:source ?source .
    }
    """
    results3 = g.query(q3)
    if not results3: print("No results.")
    for row in results3:
        print(f"Indicator: {row.indicator}, Label: {row.label}, Source: {row.source}")

    print("\n--- Query 4: Get details for a specific Financial Formula ('Debt-to-Equity Ratio') ---")
    q4 = """
    SELECT ?formula ?prop ?value WHERE {
        ?formula rdfs:label "Debt-to-Equity Ratio"@en ;
                 ?prop ?value .
    }
    """
    results4 = g.query(q4)
    if not results4: print("No results.")
    for row in results4:
        print(f"Formula: {row.formula}, Property: {row.prop}, Value: {row.value}")

    print("\n--- Query 5: Count instances per KGCLASS ---")
    # Note: STRSTARTS is case-sensitive. Ensure KGCLASS URI matches exactly.
    q5 = """
    SELECT (STR(?class) AS ?className) (COUNT(?instance) AS ?instanceCount)
    WHERE {
        ?instance rdf:type ?class .
        FILTER(STRSTARTS(STR(?class), "http://example.com/ontology/cacm_credit_ontology/0.3/classes/#"))
    }
    GROUP BY ?class
    ORDER BY DESC(?instanceCount)
    """
    results5 = g.query(q5)
    if not results5: print("No results.")
    for row in results5:
        print(f"Class Name: {row.className}, Instance Count: {row.instanceCount}")

if __name__ == "__main__":
    execute_queries()
