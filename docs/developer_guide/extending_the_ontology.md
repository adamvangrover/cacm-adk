# Extending the Ontology

The project's ontology defines the concepts, properties, and relationships used to structure the Knowledge Graph (KG). Extending the ontology allows the system to represent new types of information and enhance its reasoning capabilities. This guide outlines the process for extending `credit_ontology_v0.3.ttl` (or its successors).

## Key Considerations

*   **Purpose:** Why is the extension needed? What new information needs to be represented?
*   **Scope:** How broad is the extension? Does it introduce a few new concepts or a whole new domain?
*   **Existing Concepts:** Can existing ontology concepts or properties be reused or adapted? Avoid redundancy.
*   **Naming Conventions:** Follow established naming conventions (e.g., CamelCase for classes, camelCase for properties, consistent use of prefixes).
*   **Hierarchy:** Where do new classes fit within the existing class hierarchy?
*   **Properties:** What properties do new classes need? What are their domains (the class they belong to) and ranges (the type of value they can have)?
*   **Relationships:** How do new concepts relate to existing ones?
*   **Impact:** How will the extension affect existing agents, skills, data, and queries?
*   **Tooling:** Use an ontology editor (e.g., Protégé) for easier editing and validation.

## Process for Extending the Ontology

1.  **Understand the Current Ontology:**
    *   Thoroughly review the existing `credit_ontology_v0.3.ttl` file.
    *   Consult the `docs/ontology_guide.md` for explanations and usage examples.
    *   Pay attention to existing namespaces, class hierarchies, property definitions, and design patterns.

2.  **Propose and Discuss Changes:**
    *   Before making changes, discuss the proposed extensions with the team.
    *   Clearly articulate the need for the extension and how it will benefit the system.
    *   This helps ensure consistency and avoid conflicts.

3.  **Choose an Ontology Editor (Recommended):**
    *   Using an ontology editor like [Protégé](https://protege.stanford.edu/) is highly recommended.
    *   Protégé provides a graphical interface for viewing and editing ontologies, helps manage namespaces, and can perform consistency checks.

4.  **Backup the Ontology:**
    *   Before making any changes, create a backup of the current ontology file.

5.  **Define New Classes:**
    *   Identify the new concepts (classes) you need to add.
    *   Determine their position in the class hierarchy (i.e., their superclasses).
    *   Provide clear `rdfs:label` and `rdfs:comment` (or `skos:definition`) annotations for each new class.
    *   Example (Turtle syntax):
        ```turtle
        myont:NewConceptClass rdf:type owl:Class ;
            rdfs:subClassOf someprefix:ExistingClass ;
            rdfs:label "New Concept Class" ;
            rdfs:comment "Represents a new type of concept for X, Y, Z purposes." .
        ```

6.  **Define New Properties:**
    *   Identify the new properties (attributes or relationships) required.
    *   Determine the type of property:
        *   `owl:DatatypeProperty`: Links individuals to data values (e.g., a string, number, date).
        *   `owl:ObjectProperty`: Links individuals to other individuals (representing relationships).
    *   Define `rdfs:domain` (the class(es) this property applies to) and `rdfs:range` (the type of value for DatatypeProperty, or the class(es) for ObjectProperty).
    *   Provide `rdfs:label` and `rdfs:comment` annotations.
    *   Example (Turtle syntax):
        ```turtle
        myont:hasNewAttribute rdf:type owl:DatatypeProperty ;
            rdfs:label "has new attribute" ;
            rdfs:comment "Describes a specific new attribute of NewConceptClass." ;
            rdfs:domain myont:NewConceptClass ;
            rdfs:range xsd:string .

        myont:hasRelationshipWith rdf:type owl:ObjectProperty ;
            rdfs:label "has relationship with" ;
            rdfs:comment "Links NewConceptClass to AnotherClass." ;
            rdfs:domain myont:NewConceptClass ;
            rdfs:range otheront:AnotherClass .
        ```

7.  **Update Existing Classes/Properties (If Necessary):**
    *   Sometimes, an extension might require modifying existing classes or properties (e.g., adding a new superclass, refining a domain/range).
    *   Proceed with caution and ensure backward compatibility if possible, or plan for data migration.

8.  **Add Annotations:**
    *   Use annotations (`rdfs:label`, `rdfs:comment`, `skos:definition`, `owl:versionInfo`, etc.) generously to make the ontology understandable and maintainable.

9.  **Validate the Ontology:**
    *   If using Protégé, use its built-in reasoner (e.g., HermiT, Pellet) to check for inconsistencies.
    *   Ensure the Turtle syntax is valid (e.g., using an online RDF validator or a command-line tool).

10. **Update Ontology Version (If Applicable):**
    *   If a versioning scheme is in place for the ontology (e.g., using `owl:versionIRI` or `owl:versionInfo`), update it accordingly.
    *   Consider how changes will be communicated (e.g., if the filename includes a version number, like `credit_ontology_v0.4.ttl`).

11. **Document the Changes:**
    *   Update `docs/ontology_guide.md` to reflect the new additions or modifications.
    *   Explain the purpose of the new concepts/properties and provide usage examples.

12. **Update KG Population Processes:**
    *   Modify any KG population scripts or skills (e.g., `KGPopulationSkill`) to correctly use the new ontology terms when creating RDF triples.

13. **Update Queries and Agent Logic:**
    *   Review and update any SPARQL queries or agent logic that might be affected by or could benefit from the ontology extension.

14. **Test Thoroughly:**
    *   Test the KG population, querying, and any agent functionalities that rely on the extended ontology.

## Best Practices

*   **Reuse Before Creating:** Prefer reusing existing terms (from your ontology or well-known external ontologies like FOAF, SKOS, Dublin Core) before creating new ones.
*   **Clarity and Simplicity:** Aim for a clear and simple design. Avoid unnecessary complexity.
*   **Consistency:** Maintain consistency with the existing ontology's design patterns and naming conventions.
*   **Modularity (if applicable):** For very large extensions, consider if they could be managed as separate ontology modules that import each other.
*   **Collaboration:** Ontology development is often a collaborative process.

Remember to commit the updated ontology file and related documentation to version control.
```
