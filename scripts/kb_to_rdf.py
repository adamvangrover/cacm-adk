import json

def escape_literal(literal_string):
    """Escapes special characters for Turtle literals."""
    return literal_string.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')

def main():
    kb_file_path = "knowledge_base/KB_Valuation_Risk_Macro_TechAnalysis_v1.json"
    output_ttl_file_path = "knowledge_graph_instantiations/kb_formulas_instances.ttl"

    # Define RDF prefixes
    prefixes = {
        "rdf": "<http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
        "rdfs": "<http://www.w3.org/2000/01/rdf-schema#>",
        "owl": "<http://www.w3.org/2002/07/owl#>",
        "xsd": "<http://www.w3.org/2001/XMLSchema#>",
        "kgclass": "<http://example.com/ontology/cacm_credit_ontology/0.3/classes/#>",
        "kgprop": "<http://example.com/ontology/cacm_credit_ontology/0.3/properties/#>",
        "kb_instance": "<http://example.org/kb_instances/#>"
    }

    # Assumed new classes/properties for this script's output
    # These would ideally be formally defined in the main ontology file
    # For now, we are just using them in the generated Turtle.
    # kgclass:FinancialFormula
    # kgprop:hasCalculationString
    # kgprop:hasInputLiteral (to store input names as literals for now)
    # kgprop:hasOutputLiteral (to store output type as literal for now)


    ttl_output = []

    # Add prefixes to TTL output
    for prefix, uri in prefixes.items():
        ttl_output.append(f"@prefix {prefix}: {uri} .")
    ttl_output.append("") # Newline for readability

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

    # Process only the 'financialFormulas' section
    if "financialFormulas" in kb_data:
        for formula in kb_data["financialFormulas"]:
            formula_id = formula.get("formulaId")
            if not formula_id:
                print(f"Warning: Skipping formula due to missing 'formulaId': {formula.get('name')}")
                continue

            instance_uri = f"kb_instance:{formula_id}"
            ttl_output.append(f"{instance_uri} rdf:type kgclass:FinancialFormula ;") # Assumed class

            name = formula.get("name")
            if name:
                ttl_output.append(f'    rdfs:label "{escape_literal(name)}" ;')

            description = formula.get("description")
            if description:
                ttl_output.append(f'    rdfs:comment "{escape_literal(description)}" ;')

            calculation = formula.get("calculation")
            if calculation:
                # Assumed property kgprop:hasCalculationString
                ttl_output.append(f'    kgprop:hasCalculationString "{escape_literal(calculation)}" ;')

            inputs = formula.get("inputs")
            if inputs and isinstance(inputs, list):
                for inp in inputs:
                    # Assumed property kgprop:hasInputLiteral
                    ttl_output.append(f'    kgprop:hasInputLiteral "{escape_literal(inp)}" ;')
            
            output_type = formula.get("output")
            if output_type:
                # Assumed property kgprop:hasOutputLiteral
                ttl_output.append(f'    kgprop:hasOutputLiteral "{escape_literal(output_type)}" ;')


            # Remove trailing semicolon from the last property if it exists
            if ttl_output and ttl_output[-1].endswith(';'):
                ttl_output[-1] = ttl_output[-1][:-2] + " ." # Replace with period
            else: # Should not happen if properties were added
                ttl_output.append("    a owl:NamedIndividual .") # Fallback if no props, ensure valid triple

            ttl_output.append("") # Newline for readability between instances

    # Write the TTL output to file
    try:
        with open(output_ttl_file_path, 'w') as f:
            f.write("\n".join(ttl_output))
        print(f"Successfully generated RDF instances to {output_ttl_file_path}")
    except IOError:
        print(f"Error: Could not write TTL output to {output_ttl_file_path}")

if __name__ == "__main__":
    main()
