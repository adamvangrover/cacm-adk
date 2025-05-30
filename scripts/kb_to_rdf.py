import json
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, OWL, DCTERMS

# Define Namespaces
KGCLASS = Namespace("http://example.com/ontology/cacm_credit_ontology/0.3/classes/#")
KGPROP = Namespace("http://example.com/ontology/cacm_credit_ontology/0.3/properties/#")
KB_INSTANCE = Namespace("http://example.org/kb_instances/#") # As per prompt

# Assumed new properties to be formally defined in the ontology later
# KGPROP.hasMitigationStrategy
# KGPROP.appliesToIndustryLiteral

def main():
    kb_file_path = "knowledge_base/KB_Valuation_Risk_Macro_TechAnalysis_v1.json"
    output_ttl_file_path = "knowledge_graph_instantiations/kb_core_instances.ttl"

    # Initialize RDF graph
    g = Graph()

    # Bind prefixes
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("owl", OWL)
    g.bind("xsd", XSD)
    g.bind("dcterms", DCTERMS)
    g.bind("kgclass", KGCLASS)
    g.bind("kgprop", KGPROP)
    g.bind("kb_instance", KB_INSTANCE)

    # Load and parse the JSON KB
    try:
        with open(kb_file_path, 'r') as f:
            kb_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Knowledge base file not found at {kb_file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {kb_file_path}")
        return

    # Process 'financialFormulas'
    if "financialFormulas" in kb_data:
        for formula in kb_data["financialFormulas"]:
            formula_id = formula.get("formulaId")
            if not formula_id:
                print(f"Warning: Skipping formula due to missing 'formulaId': {formula.get('name')}")
                continue

            subject_uri = KB_INSTANCE[formula_id]
            g.add((subject_uri, RDF.type, KGCLASS.FinancialFormula))

            if formula.get("name"):
                g.add((subject_uri, RDFS.label, Literal(formula["name"], lang="en")))
            if formula.get("description"):
                g.add((subject_uri, RDFS.comment, Literal(formula["description"], lang="en")))
            if formula.get("calculation"):
                g.add((subject_uri, KGPROP.hasCalculationString, Literal(formula["calculation"], datatype=XSD.string)))
            
            inputs = formula.get("inputs", [])
            for inp in inputs:
                g.add((subject_uri, KGPROP.hasInputLiteral, Literal(inp, datatype=XSD.string)))
            
            if formula.get("output"):
                g.add((subject_uri, KGPROP.hasOutputLiteral, Literal(formula["output"], datatype=XSD.string)))

    # Process 'riskFactors'
    if "riskFactors" in kb_data:
        for rf in kb_data["riskFactors"]:
            rf_id = rf.get("riskFactorId")
            if not rf_id:
                print(f"Warning: Skipping risk factor due to missing 'riskFactorId': {rf.get('name')}")
                continue

            subject_uri = KB_INSTANCE[rf_id]
            g.add((subject_uri, RDF.type, KGCLASS.RiskFactor))

            if rf.get("name"):
                g.add((subject_uri, RDFS.label, Literal(rf["name"], lang="en")))
            if rf.get("description"):
                g.add((subject_uri, RDFS.comment, Literal(rf["description"], lang="en")))

            strategies = rf.get("mitigationStrategies", [])
            for strat in strategies:
                g.add((subject_uri, KGPROP.hasMitigationStrategy, Literal(strat, datatype=XSD.string)))
            
            industries = rf.get("relevantIndustries", [])
            for ind in industries:
                g.add((subject_uri, KGPROP.appliesToIndustryLiteral, Literal(ind, datatype=XSD.string)))

    # Process 'macroeconomicIndicators'
    if "macroeconomicIndicators" in kb_data:
        for indicator in kb_data["macroeconomicIndicators"]:
            indicator_id = indicator.get("indicatorId")
            if not indicator_id:
                print(f"Warning: Skipping indicator due to missing 'indicatorId': {indicator.get('name')}")
                continue
            
            subject_uri = KB_INSTANCE[indicator_id]
            g.add((subject_uri, RDF.type, KGCLASS.EconomicIndicator))

            if indicator.get("name"):
                g.add((subject_uri, RDFS.label, Literal(indicator["name"], lang="en")))
            if indicator.get("description"):
                g.add((subject_uri, RDFS.comment, Literal(indicator["description"], lang="en")))
            if indicator.get("source"):
                # Using DCTERMS.source for the source string.
                # DCTERMS.source typically expects a URI, but can hold a string.
                # For more precise semantics, a custom property like kgprop:hasDataSourceName could be used
                # if the source is always a name string and not a URI to a source entity.
                # For this task, DCTERMS.source with a Literal is acceptable.
                g.add((subject_uri, DCTERMS.source, Literal(indicator["source"], lang="en")))


    # Serialize the graph to TTL file
    try:
        g.serialize(destination=output_ttl_file_path, format="turtle")
        print(f"Successfully generated RDF instances to {output_ttl_file_path}")
    except Exception as e:
        print(f"Error: Could not write TTL output to {output_ttl_file_path}: {e}")

if __name__ == "__main__":
    main()
