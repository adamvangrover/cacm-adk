# SPARQL Query Examples for the Knowledge Graph

This document provides examples of SPARQL queries that can be run against the local Knowledge Graph populated from our ontology and knowledge base instances. These queries demonstrate how to retrieve information using Python's `rdflib` library.

## Running the Query Script

The example queries are implemented in `scripts/query_kg.py`. To run this script:

1.  Ensure you have Python installed.
2.  Ensure `rdflib` is installed (if not, run `pip install rdflib`).
3.  Navigate to the root directory of this project in your terminal.
4.  Execute the script using: `python scripts/query_kg.py`

The script will load the ontology (`ontology/credit_analysis_ontology_v0.3/credit_ontology_v0.3.ttl`) and the instance data (`knowledge_graph_instantiations/kb_core_instances.ttl`) into an in-memory RDF graph and then run the predefined queries, printing their results to the console.

## Example Queries and Outputs

Below are the SPARQL queries used in the script and representative snippets of their output.

---

**Query 1: List all Financial Formulas**

*   **Purpose:** Retrieves all instances of `kgclass:FinancialFormula` along with their human-readable labels.
*   **SPARQL Query:**
    ```sparql
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX kgclass: <http://example.com/ontology/cacm_credit_ontology/0.3/classes/#>

    SELECT ?formula ?label WHERE { 
        ?formula rdf:type kgclass:FinancialFormula ; 
                 rdfs:label ?label . 
    }
    ```
*   **Example Output Snippet:**
    ```
    Formula: http://example.org/kb_instances/#FF_001, Label: Debt-to-Equity Ratio
    Formula: http://example.org/kb_instances/#FF_002, Label: Current Ratio
    Formula: http://example.org/kb_instances/#FF_003, Label: Net Profit Margin
    ```

---

**Query 2: List all Risk Factors and their descriptions**

*   **Purpose:** Retrieves all instances of `kgclass:RiskFactor` and their textual descriptions.
*   **SPARQL Query:**
    ```sparql
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX kgclass: <http://example.com/ontology/cacm_credit_ontology/0.3/classes/#>

    SELECT ?risk_factor ?description WHERE { 
        ?risk_factor rdf:type kgclass:RiskFactor ; 
                     rdfs:comment ?description . 
    }
    ```
*   **Example Output Snippet:**
    ```
    Risk Factor: http://example.org/kb_instances/#RF_001, Description: The risk that changes in interest rates will adversely affect a company's financials or the value of a financial instrument.
    Risk Factor: http://example.org/kb_instances/#RF_002, Description: The risk of losses in positions arising from movements in market prices.
    Risk Factor: http://example.org/kb_instances/#RF_003, Description: Risk associated with political changes, conflicts, or instability in a country or region that could impact investments or business operations.
    ```

---

**Query 3: List all Macroeconomic Indicators and their sources**

*   **Purpose:** Retrieves all instances of `kgclass:EconomicIndicator`, their labels, and their `dcterms:source`.
*   **SPARQL Query:**
    ```sparql
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX kgclass: <http://example.com/ontology/cacm_credit_ontology/0.3/classes/#>
    PREFIX dcterms: <http://purl.org/dc/terms/>

    SELECT ?indicator ?label ?source WHERE { 
        ?indicator rdf:type kgclass:EconomicIndicator ; 
                   rdfs:label ?label ; 
                   dcterms:source ?source . 
    }
    ```
*   **Example Output Snippet:**
    ```
    Indicator: http://example.org/kb_instances/#MI_001, Label: GDP Growth Rate, Source: National Statistics Office
    Indicator: http://example.org/kb_instances/#MI_002, Label: Unemployment Rate, Source: Bureau of Labor Statistics
    ```

---

**Query 4: Get details for a specific Financial Formula ("Debt-to-Equity Ratio")**

*   **Purpose:** Retrieves all properties and values associated with a specific `kgclass:FinancialFormula` identified by its label.
*   **SPARQL Query:**
    ```sparql
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?formula ?prop ?value WHERE { 
        ?formula rdfs:label "Debt-to-Equity Ratio"@en ; 
                 ?prop ?value . 
    }
    ```
*   **Example Output Snippet:**
    ```
    Formula: http://example.org/kb_instances/#FF_001, Property: http://www.w3.org/1999/02/22-rdf-syntax-ns#type, Value: http://example.com/ontology/cacm_credit_ontology/0.3/classes/#FinancialFormula
    Formula: http://example.org/kb_instances/#FF_001, Property: http://www.w3.org/2000/01/rdf-schema#label, Value: Debt-to-Equity Ratio
    Formula: http://example.org/kb_instances/#FF_001, Property: http://example.com/ontology/cacm_credit_ontology/0.3/properties/#hasCalculationString, Value: (TotalLiabilities / ShareholdersEquity)
    Formula: http://example.org/kb_instances/#FF_001, Property: http://example.com/ontology/cacm_credit_ontology/0.3/properties/#hasInputLiteral, Value: ShareholdersEquity
    Formula: http://example.org/kb_instances/#FF_001, Property: http://example.com/ontology/cacm_credit_ontology/0.3/properties/#hasInputLiteral, Value: TotalLiabilities
    Formula: http://example.org/kb_instances/#FF_001, Property: http://example.com/ontology/cacm_credit_ontology/0.3/properties/#hasOutputLiteral, Value: Ratio
    Formula: http://example.org/kb_instances/#FF_001, Property: http://www.w3.org/2000/01/rdf-schema#comment, Value: Measures the financial leverage of a company.
    ```

---

**Query 5: Count instances per KGCLASS**

*   **Purpose:** Counts the number of instances for each class defined under the `kgclass:` namespace.
*   **SPARQL Query:**
    ```sparql
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT (STR(?class) AS ?className) (COUNT(?instance) AS ?instanceCount) 
    WHERE { 
        ?instance rdf:type ?class . 
        FILTER(STRSTARTS(STR(?class), "http://example.com/ontology/cacm_credit_ontology/0.3/classes/#")) 
    } 
    GROUP BY ?class 
    ORDER BY DESC(?instanceCount)
    ```
*   **Example Output Snippet:**
    ```
    Class Name: http://example.com/ontology/cacm_credit_ontology/0.3/classes/#FinancialFormula, Instance Count: 3
    Class Name: http://example.com/ontology/cacm_credit_ontology/0.3/classes/#RiskFactor, Instance Count: 3
    Class Name: http://example.com/ontology/cacm_credit_ontology/0.3/classes/#EconomicIndicator, Instance Count: 2
    ```

---

This document serves as a basic guide to querying the project's Knowledge Graph using SPARQL and `rdflib`.
