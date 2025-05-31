# Conceptual Design: Mapping External Financial Data to Knowledge Graph

## A. Introduction

The purpose of this document is to outline a conceptual strategy for mapping financial data from a typical external source (e.g., a financial data API or structured data file) into our Knowledge Graph (KG). This mapping will leverage the classes and properties defined in `ontology/credit_analysis_ontology_v0.3/credit_ontology_v0.3.ttl`, and will identify new ontological terms that may be necessary to accurately represent this external data. The goal is to transform raw external data into a structured, queryable, and semantically rich format within our KG.

## B. Example External Data Structure

For this conceptual exercise, we will consider a simplified JSON structure representing a hypothetical API response for company financial data:

```json
{
  "companyInfo": {
    "ticker": "XYZ",
    "companyName": "XYZ Corp",
    "sector": "Technology",
    "industry": "Software",
    "description": "XYZ Corp develops innovative software solutions."
  },
  "financials": [
    {
      "reportPeriod": "2023-Q4",
      "revenue": 1000000,
      "netIncome": 150000,
      "totalAssets": 5000000,
      "totalLiabilities": 2000000,
      "operatingCashFlow": 250000
    },
    {
      "reportPeriod": "2023-Q3",
      "revenue": 950000,
      "netIncome": 140000,
      "totalAssets": 4800000,
      "totalLiabilities": 1900000,
      "operatingCashFlow": 230000
    }
    // ... more periods
  ]
}
```

## C. Mapping Strategy

The general approach involves the following:

1.  **Obligor Creation:** For each unique company identified in the external data, an instance of `kgclass:Obligor` will be created in the KG. This instance will serve as the central node for all information related to that company.
2.  **Financial Period Report Creation:** For each distinct financial reporting period provided for a company (e.g., "2023-Q4", "2023"), a new instance of a proposed class, `kgclass:FinancialPeriodReport`, will be created.
3.  **Linking:** Each `kgclass:FinancialPeriodReport` instance will be linked to its respective `kgclass:Obligor` instance and will store the financial data specific to that period.

## D. Detailed Field Mappings

### Company Information (`companyInfo` section)

Let's assume we create an instance `kb_instance:XYZ_Company` of type `kgclass:Obligor` for "XYZ Corp".

*   **`ticker` ("XYZ"):**
    *   This could be mapped to `kgprop:hasTickerSymbol` on the `kb_instance:XYZ_Company`.
    *   **Ontology Consideration:** The current domain of `kgprop:hasTickerSymbol` is `kgclass:EquityInstrument`. This would need to be broadened to include `kgclass:Obligor` (or a new common superclass, or a more specific subclass of `Obligor` like `kgclass:ListedCompany`). Alternatively, a new property like `kgprop:hasStockTicker` specifically for obligors could be created.
*   **`companyName` ("XYZ Corp"):**
    *   Map to `rdfs:label` of `kb_instance:XYZ_Company`.
    *   Example: `kb_instance:XYZ_Company rdfs:label "XYZ Corp"@en .`
*   **`sector` ("Technology") and `industry` ("Software"):**
    *   **Sector:** Create an instance of a new class `kgclass:Sector`, e.g., `kb_instance:Sector_Technology`.
        *   `kb_instance:Sector_Technology rdf:type kgclass:Sector .`
        *   `kb_instance:Sector_Technology rdfs:label "Technology"@en .`
        *   Link `kb_instance:XYZ_Company` to this sector: `kb_instance:XYZ_Company kgprop:hasSector kb_instance:Sector_Technology .` (Requires new property `kgprop:hasSector`).
    *   **Industry:** Create an instance of the existing `kgclass:Industry`, e.g., `kb_instance:Industry_Software`.
        *   `kb_instance:Industry_Software rdf:type kgclass:Industry .`
        *   `kb_instance:Industry_Software rdfs:label "Software"@en .`
        *   Link `kb_instance:XYZ_Company` to this industry using the existing `kgprop:hasIndustry`: `kb_instance:XYZ_Company kgprop:hasIndustry kb_instance:Industry_Software .`
*   **`description` ("XYZ Corp develops innovative software solutions."):**
    *   Map to `dcterms:description` or `rdfs:comment` of `kb_instance:XYZ_Company`.
    *   Example: `kb_instance:XYZ_Company dcterms:description "XYZ Corp develops innovative software solutions."@en .`

### Financial Data (`financials` array - for each item)

For each object in the `financials` array, we propose creating an instance of a new class `kgclass:FinancialPeriodReport`.

*   **New Class: `kgclass:FinancialPeriodReport`**
    *   `rdf:type owl:Class`
    *   `rdfs:subClassOf owl:Thing` (or perhaps `cacm_ont:DataInput` if it represents a set of input data).
    *   `rdfs:label "Financial Period Report"@en`.
    *   `rdfs:comment "A collection of financial data for a specific obligor over a defined reporting period."@en`.

*   **Instance Example (for "2023-Q4"):**
    *   URI: `kb_instance:XYZ_Company_Financials_2023_Q4`
    *   `kb_instance:XYZ_Company_Financials_2023_Q4 rdf:type kgclass:FinancialPeriodReport .`
    *   **Link to Obligor:** `kb_instance:XYZ_Company_Financials_2023_Q4 kgprop:reportsForObligor kb_instance:XYZ_Company .` (New property `kgprop:reportsForObligor`).
    *   **`reportPeriod` ("2023-Q4"):**
        *   Map to a new property `kgprop:hasReportingPeriod` on the `FinancialPeriodReport` instance.
        *   `kb_instance:XYZ_Company_Financials_2023_Q4 kgprop:hasReportingPeriod "2023-Q4"^^xsd:string .` (or `xsd:gYearMonth` if appropriate, though "Q4" makes it a string).
    *   **Mapping Financial Line Items:** These would be datatype properties of the `kgclass:FinancialPeriodReport` instance.
        *   `revenue` (1000000):
            *   `kb_instance:XYZ_Company_Financials_2023_Q4 kgprop:hasRevenue "1000000"^^xsd:decimal .` (New property `kgprop:hasRevenue`).
        *   `netIncome` (150000):
            *   `kb_instance:XYZ_Company_Financials_2023_Q4 kgprop:hasNetIncome "150000"^^xsd:decimal .` (New property `kgprop:hasNetIncome`).
        *   `totalAssets` (5000000):
            *   `kb_instance:XYZ_Company_Financials_2023_Q4 kgprop:hasTotalAssets "5000000"^^xsd:decimal .` (New property `kgprop:hasTotalAssets`).
        *   `totalLiabilities` (2000000):
            *   `kb_instance:XYZ_Company_Financials_2023_Q4 kgprop:hasTotalLiabilities "2000000"^^xsd:decimal .` (New property `kgprop:hasTotalLiabilities`).
        *   `operatingCashFlow` (250000):
            *   `kb_instance:XYZ_Company_Financials_2023_Q4 kgprop:hasOperatingCashFlow "250000"^^xsd:decimal .` (New property `kgprop:hasOperatingCashFlow`).

This process would be repeated for each period in the `financials` array, creating distinct `kgclass:FinancialPeriodReport` instances, each linked to the same `kgclass:Obligor`.

## E. Ontology Considerations / New Terms Needed

To fully support this mapping, the following new classes and properties would be beneficial to add to `credit_ontology_v0.3.ttl`:

**New Classes:**

*   **`kgclass:FinancialPeriodReport`**:
    *   `rdfs:subClassOf owl:Thing` (or `cacm_ont:DataInput`).
    *   `rdfs:label "Financial Period Report"@en`.
    *   `rdfs:comment "A collection of financial data for a specific obligor over a defined reporting period."@en`.
*   **`kgclass:Sector`**:
    *   `rdfs:subClassOf owl:Thing`.
    *   `rdfs:label "Sector"@en`.
    *   `rdfs:comment "A broad classification of economic activity, e.g., Technology, Healthcare, Financials."@en`.

**New Properties:**

*   **`kgprop:reportsForObligor`** (ObjectProperty):
    *   `rdfs:domain kgclass:FinancialPeriodReport`.
    *   `rdfs:range kgclass:Obligor`.
    *   `rdfs:label "reports for obligor"@en`.
    *   `rdfs:comment "Links a financial period report to the obligor it describes."@en`.
*   **`kgprop:hasReportingPeriod`** (DatatypeProperty):
    *   `rdfs:domain kgclass:FinancialPeriodReport`.
    *   `rdfs:range xsd:string` (or `xsd:gYearMonth`, `xsd:date` depending on desired granularity and validation).
    *   `rdfs:label "has reporting period"@en`.
    *   `rdfs:comment "The specific period (e.g., year, quarter) covered by a financial report."@en`.
*   **`kgprop:hasRevenue`** (DatatypeProperty):
    *   `rdfs:domain kgclass:FinancialPeriodReport`.
    *   `rdfs:range xsd:decimal`.
    *   `rdfs:label "has revenue"@en`.
    *   `rdfs:comment "Revenue figure for a specific period."@en`.
*   **`kgprop:hasNetIncome`** (DatatypeProperty):
    *   `rdfs:domain kgclass:FinancialPeriodReport`.
    *   `rdfs:range xsd:decimal`.
    *   `rdfs:label "has net income"@en`.
    *   `rdfs:comment "Net income figure for a specific period."@en`.
*   **`kgprop:hasTotalAssets`** (DatatypeProperty):
    *   `rdfs:domain kgclass:FinancialPeriodReport`.
    *   `rdfs:range xsd:decimal`.
    *   `rdfs:label "has total assets"@en`.
    *   `rdfs:comment "Total assets figure for a specific period."@en`.
*   **`kgprop:hasTotalLiabilities`** (DatatypeProperty):
    *   `rdfs:domain kgclass:FinancialPeriodReport`.
    *   `rdfs:range xsd:decimal`.
    *   `rdfs:label "has total liabilities"@en`.
    *   `rdfs:comment "Total liabilities figure for a specific period."@en`.
*   **`kgprop:hasOperatingCashFlow`** (DatatypeProperty):
    *   `rdfs:domain kgclass:FinancialPeriodReport`.
    *   `rdfs:range xsd:decimal`.
    *   `rdfs:label "has operating cash flow"@en`.
    *   `rdfs:comment "Operating cash flow figure for a specific period."@en`.
*   **`kgprop:hasSector`** (ObjectProperty):
    *   `rdfs:domain kgclass:Obligor`.
    *   `rdfs:range kgclass:Sector`.
    *   `rdfs:label "has sector"@en`.
    *   `rdfs:comment "Links an obligor to its economic sector."@en`.

**Potential Adjustments to Existing Terms:**

*   **`kgprop:hasTickerSymbol`**:
    *   Current domain: `kgclass:EquityInstrument`.
    *   Consider broadening the domain to include `kgclass:Obligor` or creating a new property like `kgprop:hasStockTicker` for obligors if `hasTickerSymbol` is strictly for tradable instruments.

This conceptual mapping provides a foundational strategy for integrating external financial data into the Knowledge Graph, enabling richer analysis and querying capabilities.
