# Strategy for Basic Ontology Validation using Python and RDFLib

## A. Introduction

The purpose of this document is to define a strategy for performing basic automated validation and consistency checks on our project's ontology, specifically `ontology/credit_analysis_ontology_v0.3/ttl`. Utilizing Python with the `rdflib` library, we can implement a suite of tests to help maintain the ontology's quality, integrity, and adherence to best practices as it evolves.

This strategy focuses on "linting" the ontology schema (TBox) rather than deep logical consistency checking that would require a full OWL reasoner, though the latter is noted as a potential future enhancement.

## B. Setup and Loading

A Python script will be developed (e.g., `scripts/validate_ontology.py`) that uses `rdflib` to perform the checks.

1.  **Import `rdflib`:** The script will import necessary components from `rdflib`, such as `Graph`, `Namespace`, and standard RDF namespaces (`RDF`, `RDFS`, `OWL`, `XSD`).
2.  **Load Ontology:** The script will initialize an `rdflib.Graph` and parse the `credit_ontology_v0.3.ttl` file into it.
    ```python
    # Example snippet
    from rdflib import Graph
    g = Graph()
    try:
        g.parse("ontology/credit_analysis_ontology_v0.3/credit_ontology_v0.3.ttl", format="turtle")
        print("Ontology loaded successfully.")
    except Exception as e:
        print(f"Error loading ontology: {e}")
        # Handle error, perhaps exit
    ```
3.  **Define Namespaces:** Relevant namespaces used in the ontology (e.g., `kgclass:`, `kgprop:`, `cacm_ont:`) will be defined for use in SPARQL queries.

## C. Core Consistency Checks (using SPARQL)

The following checks will be implemented using SPARQL queries executed against the loaded graph. The script will report any violations found.

**Check 1: Classes not explicitly subclass of `owl:Thing` (or any other class)**

*   **Explanation:** While `owl:Thing` is the implicit superclass of all classes, explicitly defining a hierarchy or ensuring all classes are at least declared as `rdfs:subClassOf owl:Thing` (if they have no other parent) can be good practice for clarity, especially before advanced reasoning. This query identifies classes that are not `owl:Thing` itself and lack any `rdfs:subClassOf` axiom. A more advanced check with a reasoner would confirm if they are implicitly subclasses of `owl:Thing`.
*   **SPARQL Query:**
    ```sparql
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>

    SELECT ?class
    WHERE {
      ?class rdf:type owl:Class .
      FILTER NOT EXISTS { ?class rdfs:subClassOf ?superclass . }
      FILTER (?class != owl:Thing && ?class != owl:Nothing)
    }
    ```

**Check 2: Properties missing `rdfs:domain`**

*   **Explanation:** All object and datatype properties should ideally have at least one `rdfs:domain` specified to indicate which class(es) they apply to.
*   **SPARQL Query:**
    ```sparql
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>

    SELECT ?prop
    WHERE {
      { ?prop rdf:type owl:ObjectProperty . } UNION { ?prop rdf:type owl:DatatypeProperty . }
      FILTER NOT EXISTS { ?prop rdfs:domain ?domain . }
    }
    ```

**Check 3: Properties missing `rdfs:range`**

*   **Explanation:** All object and datatype properties should have at least one `rdfs:range` specified to indicate the type of values or resources they relate to.
*   **SPARQL Query:**
    ```sparql
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>

    SELECT ?prop
    WHERE {
      { ?prop rdf:type owl:ObjectProperty . } UNION { ?prop rdf:type owl:DatatypeProperty . }
      FILTER NOT EXISTS { ?prop rdfs:range ?range . }
    }
    ```

**Check 4: Potentially Undefined Classes or Properties Used in Axioms**

*   **Explanation:** This check aims to identify if any URIs used in `rdfs:domain`, `rdfs:range`, or `rdfs:subClassOf` positions have not been formally declared as `owl:Class`, `owl:ObjectProperty`, or `owl:DatatypeProperty`. This requires a two-step process without a reasoner:
    1.  Extract all unique URIs used in these positions.
    2.  For each extracted URI, check if it has an appropriate declaration in the graph.
*   **SPARQL Query (Step 1 - Extracting entities):**
    ```sparql
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?entity
    WHERE {
      { ?p rdfs:domain ?entity . } UNION
      { ?p rdfs:range ?entity . } UNION
      { ?c rdfs:subClassOf ?entity . }
      FILTER(isURI(?entity))
      # Optionally, filter out OWL and RDFS/RDF built-ins if not desired in this check
      # FILTER(!STRSTARTS(STR(?entity), STR(owl:)) && !STRSTARTS(STR(?entity), STR(rdfs:)) && !STRSTARTS(STR(?entity), STR(rdf:)))
    }
    ```
*   **Follow-up (in Python):** The Python script would iterate through these `?entity` results and run further queries for each, like:
    ```python
    # For each entity_uri from above query:
    # check_query = f"ASK {{ <{entity_uri}> rdf:type ?type . FILTER(?type IN (owl:Class, owl:ObjectProperty, owl:DatatypeProperty)) }}"
    # if not g.query(check_query): print(f"Warning: Entity {entity_uri} used in axioms but not declared as a class or property.")
    ```

## D. Labeling and Commenting Conventions

Ensuring all ontology terms are human-readable is crucial for usability and maintenance.

**Check 5: Classes missing `rdfs:label` (English)**

*   **Explanation:** All `owl:Class` definitions should have an `rdfs:label` in English.
*   **SPARQL Query:**
    ```sparql
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>

    SELECT ?class
    WHERE {
      ?class rdf:type owl:Class .
      FILTER NOT EXISTS { ?class rdfs:label ?label . FILTER(langMatches(lang(?label), "en") || lang(?label) = "") }
      # Allow for labels with no lang tag if that's an accepted convention, otherwise strict "en"
      # FILTER(!STRSTARTS(STR(?class), STR(owl:))) # Optionally exclude built-in OWL classes
    }
    ```

**Check 6: Properties missing `rdfs:label` (English)**

*   **Explanation:** All `owl:ObjectProperty` and `owl:DatatypeProperty` definitions should have an `rdfs:label` in English.
*   **SPARQL Query:**
    ```sparql
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>

    SELECT ?prop
    WHERE {
      { ?prop rdf:type owl:ObjectProperty . } UNION { ?prop rdf:type owl:DatatypeProperty . }
      FILTER NOT EXISTS { ?prop rdfs:label ?label . FILTER(langMatches(lang(?label), "en") || lang(?label) = "") }
    }
    ```

**Check 7 & 8: Classes/Properties missing `rdfs:comment` (English)**
*   Similar queries to Check 5 and 6 can be constructed for `rdfs:comment`.
    *   Replace `rdfs:label` with `rdfs:comment` in the `FILTER NOT EXISTS` clause.

## E. Domain/Range Adherence with Instance Data (Conceptual)

While the checks above focus on the ontology's TBox (schema), validating instance data (ABox) against declared `rdfs:domain` and `rdfs:range` restrictions is also a critical part of maintaining data quality.

*   **Strategy:** This typically involves loading the ontology *and* instance data into the same `rdflib.Graph`.
*   **Example Check (Conceptual):** To find instances where a property's value does not conform to its `rdfs:range` (e.g., `kgprop:hasInterestRate` having a non-decimal value when its range is `xsd:decimal`):
    ```sparql
    # This query is conceptual and might need refinement based on actual data types and reasoner capabilities.
    # It checks if an object of a property with a defined datatype range is not a literal of that datatype.
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?subject ?property ?object
    WHERE {
      ?property rdfs:range ?expectedDatatype .
      # Focus on common XSD datatypes for this example
      FILTER (?expectedDatatype IN (xsd:string, xsd:decimal, xsd:integer, xsd:boolean, xsd:date, xsd:dateTime))

      ?subject ?property ?object .
      FILTER (isLiteral(?object) && datatype(?object) != ?expectedDatatype)
    }
    ```
*   Validating `rdfs:domain` involves checking if the subject of a triple belongs to the class specified in the property's domain.
*   These checks are more about instance data validation rather than pure ontology schema validation but are a natural next step.

## F. Use of OWL Reasoner (Aspirational/Future Work)

For more advanced consistency checking, employing an OWL reasoner would be highly beneficial. A reasoner can:

*   **Infer implicit class hierarchies:** (e.g., if A subClassOf B and B subClassOf C, then A subClassOf C).
*   **Detect unsatisfiable classes:** Classes that cannot logically have any instances.
*   **Perform more comprehensive consistency checks:** Based on OWL axioms like disjointness, cardinality restrictions, etc.
*   **Fully check for undefined terms:** Reasoners typically report errors if terms used in axioms are not declared.

Python libraries like `rdflib-owlrl` provide some OWL reasoning capabilities directly within `rdflib`. Standalone reasoners like Pellet, HermiT, or ELK can also be used by exporting the ontology and then processing it. Integrating a reasoner is a valuable future enhancement to this testing strategy.

This strategy provides a starting point for automated ontology quality assurance, which can be expanded over time.
