# CACM-ADK Ontology Guide (Version for credit_ontology_v0.3.ttl)

This document provides a guide to the `credit_ontology_v0.3.ttl` ontology used within the CACM-ADK project. The primary ontology file is located at `ontology/credit_analysis_ontology_v0.3/credit_ontology_v0.3.ttl`.

## 1. Introduction

The Credit Analysis Capability Module (CACM) Ontology provides the semantic backbone for representing and reasoning about data within the ADK (Agent Development Kit). It defines a structured vocabulary of classes (concepts) and properties (relationships and attributes) relevant to credit analysis, risk management, financial instruments, ESG factors, alternative data, and the ADK's own architectural components like agents and skills.

By leveraging this ontology, the system can:
*   Standardize data representation across different agents and modules.
*   Facilitate complex queries against the Knowledge Graph (KG).
*   Enable more intelligent agent behavior based on semantic understanding.
*   Support automated reasoning and inference (future capability).

## 2. Namespaces

The ontology utilizes several namespaces (prefixes) to organize terms:

*   **`cacm_ont:`**: `<http://example.com/ontology/cacm_credit_ontology/0.3#>` - Core concepts defined specifically for CACM credit analysis.
*   **`kgclass:`**: `<http://example.com/ontology/cacm_credit_ontology/0.3/classes/#>` - Additional classes, often more granular or from broader financial domains, including those based on user feedback and specific use-cases.
*   **`kgprop:`**: `<http://example.com/ontology/cacm_credit_ontology/0.3/properties/#>` - Additional properties, corresponding to the `kgclass` extensions.
*   **`adkarch:`**: `<http://www.example.com/adk/architecture#>` - Terms related to the ADK architecture itself, such as agents and semantic skills.
*   **`altdata:`**: `<http://example.com/ontology/cacm_credit_ontology/0.3/alternative_data#>` - Concepts for representing alternative data sources and metrics.
*   **`esg:`**: `<http://example.com/ontology/cacm_credit_ontology/0.3/esg#>` - Concepts for Environmental, Social, and Governance (ESG) factors and metrics.
*   **`rdf:`**: `<http://www.w3.org/1999/02/22-rdf-syntax-ns#>` - Resource Description Framework.
*   **`rdfs:`**: `<http://www.w3.org/2000/01/rdf-schema#>` - RDF Schema.
*   **`owl:`**: `<http://www.w3.org/2002/07/owl#>` - Web Ontology Language.
*   **`xsd:`**: `<http://www.w3.org/2001/XMLSchema#>` - XML Schema Datatypes.
*   **`dcterms:`**: `<http://purl.org/dc/terms/>` - Dublin Core Metadata Terms.
*   **`skos:`**: `<http://www.w3.org/2004/02/skos/core#>` - Simple Knowledge Organization System.
*   **`foaf:`**: `<http://xmlns.com/foaf/0.1/>` - Friend of a Friend.

## 3. Core Concepts and Usage Examples

This section highlights key classes and properties, providing examples of how they are used to model information in the Knowledge Graph.

### 3.1. Entities and Financial Concepts

*   **`kgclass:Obligor`**: Represents an entity (company, individual) with financial obligations.
    *   **Example Instance:** `:CompanyX rdf:type kgclass:Obligor ; rdfs:label "Company X Inc." .`
*   **`kgclass:FinancialInstrument`**: Represents instruments like loans, bonds.
    *   Subclasses: `kgclass:Loan`, `kgclass:Bond`, `kgclass:EquityInstrument`.
    *   **Example Instance:** `:Loan123 rdf:type kgclass:Loan ; kgprop:hasPrincipalAmount "1000000"^^xsd:decimal ; kgprop:hasCurrency "USD" ; kgprop:hasInterestRate "5.2"^^xsd:decimal .`
*   **`cacm_ont:FinancialStatement`**: Represents financial reports (Balance Sheet, Income Statement).
    *   **Example Instance:** `:FS_CompanyX_2023 rdf:type cacm_ont:FinancialStatement ; dcterms:date "2023-12-31"^^xsd:date ; kgprop:pertainsTo :CompanyX .`
*   **`cacm_ont:Metric`**: A quantifiable measure.
    *   Subclasses: `cacm_ont:Ratio`, `cacm_ont:RiskScore`, `kgclass:CreditRiskMetric`, `esg:ESGMetric`.
    *   **Example Instance:** `:DebtToEquity_CompanyX_2023 rdf:type kgclass:LeverageRatio ; kgprop:hasValue "0.65"^^xsd:decimal ; kgprop:pertainsTo :CompanyX ; cacm_ont:hasDataSource :FS_CompanyX_2023 .`

### 3.2. Risk and Analysis

*   **`kgclass:RiskFactor`**: A factor that can introduce risk.
    *   **Example Instance:** `:MarketVolatilityRisk rdf:type kgclass:RiskFactor ; rdfs:label "Market Volatility Risk" .`
    *   An obligor can be linked: `:CompanyX kgprop:exposedTo :MarketVolatilityRisk .`
*   **`kgclass:Analysis`**: Represents an analytical process or its results.
    *   **Example Instance:** `:CreditAnalysis_CompanyX_Q1_2024 rdf:type kgclass:Analysis ; kgprop:pertainsTo :CompanyX ; dcterms:date "2024-04-15"^^xsd:date .`
*   **`kgclass:Rating`**: A creditworthiness classification.
    *   Subclasses: `kgclass:RegulatoryRating`, `esg:OverallESGRating`.
    *   **Example Instance:** `:Rating_CompanyX_SP rdf:type kgclass:Rating ; kgprop:hasValue "AA-" ; kgprop:pertainsTo :CompanyX ; esg:dataSource "S&P Global" .` (Using `esg:dataSource` broadly here for rating agency).

### 3.3. Data Inputs and Sources

*   **`cacm_ont:DataInput`**: Any data used for analysis.
    *   Subclasses: `cacm_ont:FinancialStatement`, `kgclass:MarketData`, `altdata:AlternativeDataRecord`.
    *   **Example Instance:** `:StockPrice_AAPL_20240715 rdf:type kgclass:MarketData ; rdfs:label "AAPL Stock Price 2024-07-15" ; kgprop:hasValue "150.25"^^xsd:decimal ; kgprop:hasCurrency "USD" .`
*   **`kgprop:hasDataSource` (from `cacm_ont`)**: Links a metric/analysis to its data origin.
    *   **Example:** `:LiquidityRatio_CompanyX cacm_ont:hasDataSource :BS_CompanyX_2023 .`
*   **`kgprop:hasSourceSystem`**: Specifies the IT system origin of data.
    *   **Example:** `:FS_CompanyX_2023 kgprop:hasSourceSystem "SAP FI/CO" .`

### 3.4. ESG (Environmental, Social, Governance)

*   **`esg:ESGMetric`**: Parent class for ESG-related metrics.
    *   Subclasses: `esg:EnvironmentalFactor`, `esg:SocialFactor`, `esg:GovernanceFactor`.
    *   Specific metrics: `esg:CarbonEmission`, `esg:WaterUsage`, `esg:BoardIndependenceRatio`.
*   **Example Instance (`esg:CarbonEmission`):**
    ```turtle
    :CO2_CompanyX_2023 rdf:type esg:CarbonEmission ;
        kgprop:pertainsTo :CompanyX ;
        esg:metricValue "15000"^^xsd:decimal ;
        esg:metricUnit "tonnes CO2e" ;
        esg:reportingPeriod "2023"^^xsd:gYear ;
        esg:emissionScope "Scope 1" ;
        esg:dataSource "Company Sustainability Report 2023" .
    ```
*   **`esg:OverallESGRating`**: An overall ESG rating for an entity.
    *   **Example:** `:CompanyX esg:hasESGRating [ rdf:type esg:OverallESGRating ; esg:ratingValue "A" ; esg:dataSource "MSCI" ] .`

### 3.5. Alternative Data

*   **`altdata:AlternativeDataRecord`**: Parent for various alternative data types.
    *   Subclasses: `altdata:UtilityPaymentRecord`, `altdata:SocialMediaSentiment`, `altdata:SupplyChainLink`.
*   **Example Instance (`altdata:SocialMediaSentiment`):**
    ```turtle
    :Sentiment_CompanyX_ProductY rdf:type altdata:SocialMediaSentiment ;
        kgprop:pertainsTo :CompanyX ; # Could also pertain to a product/service
        altdata:sentimentScore "0.75"^^xsd:float ;
        altdata:sentimentSource "TwitterMonitorAgent" ;
        altdata:sentimentDate "2024-07-15"^^xsd:date .
    ```

### 3.6. ADK Architecture (Agents and Skills)

*   **`adkarch:Agent`**: Represents a software agent in the ADK.
    *   Subclasses: `adkarch:AnalysisAgent`, `adkarch:DataIngestionAgent`.
    *   **Example Instance:** `:FinancialDataIngestionAgent rdf:type adkarch:DataIngestionAgent ; rdfs:label "Financial Data Ingestion Agent" .`
*   **`adkarch:SemanticSkill`**: A skill usable by the Semantic Kernel.
    *   **Example Instance:** `:CalculateRatioSkill rdf:type adkarch:SemanticSkill ; adkarch:skillName "calculateFinancialRatio" ; adkarch:pluginName "FinancialMetricsPlugin" .`
*   **`adkarch:usesSkill`**: Links an agent to a skill it uses.
    *   **Example:** `:BasicRatioAnalysisAgent adkarch:usesSkill :CalculateRatioSkill .`

## 4. How Current Agents Utilize the Ontology for KG Interactions

Agents interact with the Knowledge Graph (KG) by leveraging the ontology in several ways:

1.  **KG Population (e.g., `KnowledgeGraphAgent`, `DataIngestionAgent`):**
    *   When new data is ingested (e.g., financial statements, market data, ESG reports), ingestion agents use the ontology to structure this data as RDF triples.
    *   They map incoming data fields to appropriate `owl:DatatypeProperty` instances (e.g., `kgprop:hasPrincipalAmount`, `esg:metricValue`) and assign individuals to `owl:Class` types (e.g., creating an instance of `kgclass:Loan` or `esg:CarbonEmission`).
    *   Relationships between entities are created using `owl:ObjectProperty` instances (e.g., `:Loan123 kgprop:pertainsTo :CompanyX`, `:CompanyX esg:reportsESGMetric :CO2_CompanyX_2023`).
    *   The `KGPopulationSkill` would encapsulate logic to take structured input (like JSON) and transform it into RDF triples conforming to this ontology.

2.  **Data Retrieval and Querying (e.g., `KnowledgeGraphAgent`, various `AnalysisAgent` types):**
    *   Agents formulate SPARQL queries that use the ontology terms to retrieve specific information.
    *   **Example Query:** Find all companies with a debt-to-equity ratio greater than 1.0.
        ```sparql
        PREFIX kgclass: <http://example.com/ontology/cacm_credit_ontology/0.3/classes/#>
        PREFIX kgprop: <http://example.com/ontology/cacm_credit_ontology/0.3/properties/#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT ?company ?ratioValue
        WHERE {
          ?company rdf:type kgclass:Obligor .
          ?ratio rdf:type kgclass:LeverageRatio ;
                 kgprop:pertainsTo ?company ;
                 kgprop:hasValue ?ratioValue .
          FILTER (xsd:decimal(?ratioValue) > 1.0)
        }
        ```
    *   Analysis agents use such queries to gather necessary inputs for their calculations or analytical models (e.g., fetching all `kgclass:RiskFactor` instances associated with a `kgclass:Obligor`).

3.  **Semantic Understanding and Reasoning (Advanced/Future):**
    *   Agents can use the class hierarchy (`rdfs:subClassOf`) and property characteristics (`rdfs:domain`, `rdfs:range`) to make more informed decisions.
    *   For instance, if an agent is looking for any `cacm_ont:Metric` related to an obligor, a query for `cacm_ont:Metric` will also return instances of its subclasses like `kgclass:LeverageRatio` or `esg:ESGMetric` due to entailment.
    *   The ontology can help agents understand the *type* of data they are dealing with, enabling them to apply appropriate processing logic or skills. For example, data identified as `esg:CarbonEmission` might be processed by a specialized ESG analysis skill.

4.  **Defining Agent Capabilities and Inputs/Outputs:**
    *   CACM templates and agent configurations can reference ontology terms to semantically describe the inputs an agent expects and the outputs it produces.
    *   For example, a CACM for "Basic Ratio Analysis" might specify that it requires inputs of type `cacm_ont:FinancialStatement` and produces outputs of type `cacm_ont:Ratio`.
    *   The `adkarch:` terms help describe the agents themselves and their skills within the KG, allowing for meta-analysis of the system's capabilities.

## 5. Best Practices for Extension

Extending the ontology is a critical process that should be done thoughtfully. Refer to `docs/developer_guide/extending_the_ontology.md` for detailed steps. Key best practices include:

*   **Reuse Existing Terms:** Before adding a new class or property, check if a suitable term already exists in this ontology or in well-known external ontologies (e.g., FOAF, SKOS, FIBO - though FIBO is not currently imported, its patterns can be informative).
*   **Maintain Consistency:** Follow existing naming conventions (e.g., `CamelCase` for classes, `camelCaseForProperties`) and design patterns.
*   **Clear Definitions:** Provide `rdfs:label` and `rdfs:comment` (or `skos:definition`) for all new terms. Comments should explain the term's meaning and intended use.
*   **Define Domains and Ranges:** For properties, clearly define their `rdfs:domain` (which classes they apply to) and `rdfs:range` (the type of their values or the classes they link to).
*   **Incremental Changes:** Make extensions incrementally and test their impact on KG population and querying.
*   **Collaboration:** Discuss proposed extensions with the team to ensure they align with the overall goals and architecture.
*   **Use an Ontology Editor:** Tools like Protégé can greatly simplify ontology development, visualization, and validation (checking for inconsistencies).
*   **Versioning:** While the current file is `credit_ontology_v0.3.ttl`, significant changes might warrant a new version number in the filename and within the `owl:versionInfo` annotation. Minor additions can be part of the existing version until a threshold is met.

## 6. Browsing and Querying the Ontology

*   The ontology file (`credit_ontology_v0.3.ttl`) can be loaded into an ontology editor like Protégé for browsing and visualization.
*   SPARQL endpoints (if available through the `KnowledgeGraphAgent` or a dedicated triple store) can be used to query both the ontology schema (TBox) and the instance data (ABox).
    *   Example: Querying for all subclasses of `cacm_ont:Metric`.
        ```sparql
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX cacm_ont: <http://example.com/ontology/cacm_credit_ontology/0.3#>

        SELECT ?subClass ?label
        WHERE {
          ?subClass rdfs:subClassOf* cacm_ont:Metric .
          OPTIONAL { ?subClass rdfs:label ?label . }
        }
        ```

This guide will be updated as the ontology evolves and new use cases emerge.
```
