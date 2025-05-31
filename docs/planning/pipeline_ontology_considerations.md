# Conceptual Ontology Considerations for Data Pipeline Artifacts

## A. Introduction

This document outlines initial conceptual considerations for extending our Knowledge Graph ontology (`credit_ontology_v0.3.ttl`) to semantically describe the artifacts, processes, and data flows within the newly defined data ingestion, processing, and feedback pipeline. The purpose is to identify potential new classes and properties that will enable a richer, more queryable, and traceable representation of our analytical activities. These are preliminary ideas intended for future ontology evolution and refinement.

Standard namespaces like `prov:` (for provenance) and `dcterms:` (for metadata) should be leveraged where appropriate.

## B. Proposed New Ontology Classes

Below are proposals for new classes to represent key entities in the data pipeline.

*   **`kgclass:RawDocument`**
    *   **Description:** "Represents an original, unprocessed input document, such as a 10-K PDF, a press release DOCX, or a news article URL. This is the starting point for data ingestion."
    *   **Potential Parent Class:** `owl:Thing` or `cacm_ont:DataInput` (if viewed as a primary input to the system).
    *   **Potential Properties/Links:**
        *   `dcterms:source` (xsd:anyURI or xsd:string for file path/URL)
        *   `dcterms:format` (xsd:string, e.g., "application/pdf", "text/html")
        *   `dcterms:created` (xsd:dateTime, for when the document itself was created/published)
        *   `dcterms:retrieved` (xsd:dateTime, for when it was fetched by our system)
        *   `kgprop:hasUniqueIdentifier` (xsd:string, e.g., a hash of the file or a persistent ID)
        *   `kgprop:hasOriginalFileName` (xsd:string)

*   **`kgclass:ProcessedTextDocument`**
    *   **Description:** "Represents the extracted and cleaned textual content derived from a `kgclass:RawDocument`. This could be plain text or text structured into sections."
    *   **Potential Parent Class:** `owl:Thing` or `cacm_ont:DataInput` (as it's input to vectorization/analysis).
    *   **Potential Properties/Links:**
        *   `prov:wasDerivedFrom` (range: `kgclass:RawDocument`)
        *   `dcterms:language` (xsd:string, e.g., "en")
        *   `kgprop:hasTextContent` (xsd:string, for the full text)
        *   `kgprop:hasSectionBreakdown` (xsd:string or a custom datatype like rdf:JSON, if text is structured, e.g., JSON representing sections like "Risk Factors", "MD&A")
        *   `kgprop:processingTimestamp` (xsd:dateTime)

*   **`kgclass:VectorEmbeddingSet`**
    *   **Description:** "Represents a set of vector embeddings derived from a `kgclass:ProcessedTextDocument` (or specific sections of it) using a particular embedding model."
    *   **Potential Parent Class:** `owl:Thing`.
    *   **Potential Properties/Links:**
        *   `prov:wasDerivedFrom` (range: `kgclass:ProcessedTextDocument` or a specific section URI)
        *   `kgprop:hasEmbeddingModelName` (xsd:string, e.g., "text-embedding-ada-002")
        *   `kgprop:hasVectorDimension` (xsd:integer)
        *   `kgprop:hasStoragePath` (xsd:anyURI, path to the stored vector data, e.g., a pickle file, database reference)
        *   `kgprop:vectorizationTimestamp` (xsd:dateTime)

*   **`kgclass:AnalysisRun`**
    *   **Description:** "Represents a single, complete execution of an analysis workflow or a specific CACM, linking inputs, configurations, parameters, outputs, and any associated feedback. This is key for auditability and reproducibility."
    *   **Potential Parent Class:** `kgclass:Analysis` or `cacm_ont:CreditActivity`.
    *   **Potential Properties/Links:**
        *   `prov:used` (can point to `kgclass:RawDocument`, `kgclass:ProcessedTextDocument`, `kgclass:VectorEmbeddingSet`, or other specific data inputs used)
        *   `prov:wasAssociatedWith` (range: `kgclass:User` or `xsd:string` for analyst ID initiating the run)
        *   `kgprop:usedWorkflowTemplate` (xsd:string for template ID like "urn:adk:template:corporate_credit_report:entity_overview:v1", or ideally an object property linking to an instance representing the template definition)
        *   `kgprop:usedCacmInstance` (if a full CACM JSON instance was executed)
        *   `kgprop:hasConfigurationParameters` (xsd:string or rdf:JSON for runtime parameters)
        *   `prov:generated` (range: `kgclass:MachineOutput`, `kgclass:FinalReport`, `kgclass:MonitoringAlert`)
        *   `kgprop:receivedFeedback` (range: `kgclass:HumanFeedbackEntry`)
        *   `dcterms:created` (xsd:dateTime, for when the run was initiated)
        *   `kgprop:hasStatus` (xsd:string, e.g., "Started", "Completed", "Failed")

*   **`kgclass:LLMPromptRecord`**
    *   **Description:** "Records the details of a specific prompt sent to an Large Language Model (LLM) as part of an analysis run, along with context about its usage."
    *   **Potential Parent Class:** `owl:Thing`.
    *   **Potential Properties/Links:**
        *   `dcterms:text` (xsd:string, the full text of the prompt)
        *   `kgprop:usedInAnalysisRun` (range: `kgclass:AnalysisRun`)
        *   `kgprop:usedForStep` (xsd:string, e.g., "SummarizeRecentNews", "GenerateRatingRationale")
        *   `kgprop:hasLLMModelName` (xsd:string, e.g., "gpt-4-turbo")
        *   `kgprop:hasTimestamp` (xsd:dateTime)
        *   `kgprop:hadResponse` (range: `kgclass:MachineOutput`, linking to the LLM's raw response)

*   **`kgclass:MachineOutput`**
    *   **Description:** "The raw, direct output from an analytical capability, LLM, or a step in a CACM workflow, before any significant human review or reformatting for a final report."
    *   **Potential Parent Class:** `owl:Thing`.
    *   **Potential Properties/Links:**
        *   `prov:wasGeneratedBy` (range: `kgclass:AnalysisRun`, or a more specific `kgclass:AnalysisStep` if modeled)
        *   `dcterms:format` (xsd:string, e.g., "application/json", "text/plain")
        *   `kgprop:hasRawContent` (xsd:string or rdf:XMLLiteral for complex structures)
        *   `kgprop:generatedAtTime` (xsd:dateTime)

*   **`kgclass:FinalReport`**
    *   **Description:** "A finalized report artifact, which could be predominantly machine-generated or significantly human-augmented and reviewed. This represents a key deliverable of an analysis."
    *   **Potential Parent Class:** `kgclass:CreditReport` (if it's suitable, or a more general `kgclass:ReportOutput`).
    *   **Potential Properties/Links:**
        *   `prov:wasDerivedFrom` (can link to `kgclass:MachineOutput`, `kgclass:HumanFeedbackEntry`, etc.)
        *   `dcterms:title` (xsd:string)
        *   `dcterms:created` (xsd:dateTime, for report finalization)
        *   `dcterms:creator` (xsd:string or link to User, for analyst responsible)
        *   `dcterms:format` (xsd:string, e.g., "application/pdf", "text/markdown")
        *   `kgprop:hasStoragePath` (xsd:anyURI)

*   **`kgclass:HumanFeedbackEntry`**
    *   **Description:** "A structured entry containing qualitative and quantitative feedback provided by a human reviewer on an analysis run, a specific report, or its components."
    *   **Potential Parent Class:** `owl:Thing`.
    *   **Potential Properties/Links:**
        *   `prov:wasAssociatedWith` (range: `kgclass:AnalysisRun` or `kgclass:FinalReport`)
        *   `kgprop:hasReviewer` (xsd:string for reviewer ID/name, or link to a `kgclass:User` if users are modeled)
        *   `kgprop:hasOverallScore` (xsd:integer, e.g., 1-5 scale)
        *   `dcterms:created` (xsd:dateTime, for when feedback was submitted)
        *   `rdfs:comment` (for overall textual feedback)
        *   `kgprop:hasSectionalFeedback` (range: `kgclass:FeedbackSectionScore`)

*   **`kgclass:FeedbackSectionScore`**
    *   **Description:** "Detailed feedback scores and comments for a specific, named section or stage of an analysis or report, forming part of a `kgclass:HumanFeedbackEntry`."
    *   **Potential Parent Class:** `owl:Thing`.
    *   **Potential Properties/Links:**
        *   `prov:isPartOf` (range: `kgclass:HumanFeedbackEntry`)
        *   `kgprop:forSectionName` (xsd:string, e.g., "Entity Overview", "Financial Ratio Accuracy")
        *   `kgprop:hasAccuracyScore` (xsd:integer)
        *   `kgprop:hasClarityScore` (xsd:integer)
        *   `kgprop:hasCompletenessScore` (xsd:integer)
        *   `kgprop:hasRelevanceScore` (xsd:integer)
        *   `rdfs:comment` (for specific textual feedback on this section)

## C. Proposed New Ontology Properties

Many new properties were suggested above within the class definitions. Here's a summary and a few others:

*   **Provenance-related (using `prov:` namespace where possible, e.g., by importing `PROV = Namespace("http://www.w3.org/ns/prov#")`):**
    *   `prov:wasDerivedFrom`
    *   `prov:used`
    *   `prov:wasGeneratedBy`
    *   `prov:wasAssociatedWith`
    *   `prov:isPartOf`
*   **`kgprop:hasUniqueIdentifier`**: domain `kgclass:RawDocument`, range `xsd:string`.
*   **`kgprop:hasOriginalFileName`**: domain `kgclass:RawDocument`, range `xsd:string`.
*   **`kgprop:hasTextContent`**: domain `kgclass:ProcessedTextDocument`, range `xsd:string`.
*   **`kgprop:hasSectionBreakdown`**: domain `kgclass:ProcessedTextDocument`, range `xsd:string` or `rdf:JSON`.
*   **`kgprop:processingTimestamp`**: domain `kgclass:ProcessedTextDocument`, range `xsd:dateTime`.
*   **`kgprop:hasEmbeddingModelName`**: domain `kgclass:VectorEmbeddingSet`, range `xsd:string`.
*   **`kgprop:hasVectorDimension`**: domain `kgclass:VectorEmbeddingSet`, range `xsd:integer`.
*   **`kgprop:hasStoragePath`**: domain (e.g., `kgclass:VectorEmbeddingSet`, `kgclass:FinalReport`), range `xsd:anyURI`.
*   **`kgprop:vectorizationTimestamp`**: domain `kgclass:VectorEmbeddingSet`, range `xsd:dateTime`.
*   **`kgprop:usedWorkflowTemplate`**: domain `kgclass:AnalysisRun`, range `xsd:string` (or URI of template).
*   **`kgprop:usedCacmInstance`**: domain `kgclass:AnalysisRun`, range (URI of specific CACM instance JSON).
*   **`kgprop:hasConfigurationParameters`**: domain `kgclass:AnalysisRun`, range `xsd:string` or `rdf:JSON`.
*   **`kgprop:receivedFeedback`**: domain `kgclass:AnalysisRun`, range `kgclass:HumanFeedbackEntry`.
*   **`kgprop:hasStatus`**: domain `kgclass:AnalysisRun`, range `xsd:string`.
*   **`kgprop:usedInAnalysisRun`**: domain `kgclass:LLMPromptRecord`, range `kgclass:AnalysisRun`.
*   **`kgprop:usedForStep`**: domain `kgclass:LLMPromptRecord`, range `xsd:string`.
*   **`kgprop:hasLLMModelName`**: domain `kgclass:LLMPromptRecord`, range `xsd:string`.
*   **`kgprop:hadResponse`**: domain `kgclass:LLMPromptRecord`, range `kgclass:MachineOutput`.
*   **`kgprop:hasRawContent`**: domain `kgclass:MachineOutput`, range `xsd:string` or `rdf:XMLLiteral`.
*   **`kgprop:generatedAtTime`**: domain `kgclass:MachineOutput`, range `xsd:dateTime`.
*   **`kgprop:hasReviewer`**: domain `kgclass:HumanFeedbackEntry`, range `xsd:string` (or `kgclass:User`).
*   **`kgprop:hasOverallScore`**: domain `kgclass:HumanFeedbackEntry`, range `xsd:integer`.
*   **`kgprop:hasSectionalFeedback`**: domain `kgclass:HumanFeedbackEntry`, range `kgclass:FeedbackSectionScore`.
*   **`kgprop:forSectionName`**: domain `kgclass:FeedbackSectionScore`, range `xsd:string`.
*   **`kgprop:hasAccuracyScore`**: domain `kgclass:FeedbackSectionScore`, range `xsd:integer`.
*   **`kgprop:hasClarityScore`**: domain `kgclass:FeedbackSectionScore`, range `xsd:integer`.
*   **`kgprop:hasCompletenessScore`**: domain `kgclass:FeedbackSectionScore`, range `xsd:integer`.
*   **`kgprop:hasRelevanceScore`**: domain `kgclass:FeedbackSectionScore`, range `xsd:integer`.

## D. Relationships to Existing Ontology

*   **`kgclass:AnalysisRun`** could naturally be a subclass of the existing `kgclass:Analysis` or `cacm_ont:CreditActivity`, as it represents a specific instance of an analytical process.
*   **`kgclass:RawDocument`** and **`kgclass:ProcessedTextDocument`** could be considered subclasses of `cacm_ont:DataInput`, as they represent inputs to different stages of the pipeline.
*   **`kgclass:FinalReport`** could be a subclass of the existing `kgclass:CreditReport` if the generated reports are indeed credit reports. If they are more general analytical reports, a new superclass for "Report" might be needed, or it could be a direct subclass of `owl:Thing`.
*   Existing properties like `dcterms:title`, `dcterms:description`, `dcterms:format`, `dcterms:created`, `dcterms:source` should be reused where appropriate for new classes to maintain consistency with standard vocabularies.
*   The new classes and properties will link extensively to existing core classes like `kgclass:Obligor` and `kgclass:FinancialInstrument` through various relationship properties.

These conceptual additions aim to provide a semantic layer for the data pipeline, enabling better tracking, querying, and understanding of the analytical processes and their artifacts. Formal definition in Turtle syntax and integration into the main ontology file would be the next step after refining these concepts.
