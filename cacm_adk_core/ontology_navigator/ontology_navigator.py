# cacm_adk_core/ontology_navigator/ontology_navigator.py
import logging
import json  # Moved to top
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import RDF, RDFS, OWL, XSD

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OntologyNavigator:
    """
    Helps users browse, search, and select relevant concepts from the
    domain ontology.
    """

    def __init__(
        self,
        ontology_path="ontology/credit_analysis_ontology_v0.3/credit_ontology_v0.3.ttl",
    ):
        self.graph = Graph()
        self.namespaces = {}
        try:
            self.graph.parse(ontology_path, format="turtle")
            logger.info(f"Successfully loaded ontology from {ontology_path}")
            self._bind_common_namespaces()
        except FileNotFoundError:
            logger.error(
                f"Ontology file not found at {ontology_path}. Navigator will be empty."
            )
        except Exception as e:
            logger.error(f"Error loading ontology from {ontology_path}: {e}")

    def _bind_common_namespaces(self):
        """Binds common namespaces and extracts all from the graph."""
        common_ns = {
            "rdf": RDF,
            "rdfs": RDFS,
            "owl": OWL,
            "xsd": XSD,
            "dcterms": Namespace("http://purl.org/dc/terms/"),
            "skos": Namespace("http://www.w3.org/2004/02/skos/core/"),
            "foaf": Namespace("http://xmlns.com/foaf/0.1/"),
            "cacm_ont": Namespace(
                "http://example.com/ontology/cacm_credit_ontology/0.3#"
            ),
            "kgclass": Namespace(
                "http://example.com/ontology/cacm_credit_ontology/0.3/classes/#"
            ),
            "kgprop": Namespace(
                "http://example.com/ontology/cacm_credit_ontology/0.3/properties/#"
            ),
            "adkarch": Namespace(
                "http://www.example.com/adk/architecture#"
            ),  # Added new namespace
        }
        for prefix, namespace_uri in common_ns.items():
            self.graph.bind(prefix, namespace_uri)
            self.namespaces[prefix] = namespace_uri

        # Also extract any other namespaces defined in the TTL file's @prefix directives
        for prefix, uri in self.graph.namespaces():
            if prefix not in self.namespaces:
                self.namespaces[prefix] = uri
        logger.info(f"Bound namespaces: {self.namespaces.keys()}")

    def _resolve_uri(self, term: str) -> URIRef:
        """Resolves a prefixed term (e.g., 'rdfs:Class') or a full URI to a URIRef."""
        if ":" in term and not term.startswith("http"):  # Likely a prefixed name
            prefix, local_name = term.split(":", 1)
            if prefix in self.namespaces:
                return self.namespaces[prefix][local_name]
            else:
                logger.warning(
                    f"Prefix '{prefix}' not found in known namespaces. Treating '{term}' as a full URI if possible."
                )
                return URIRef(term)  # Fallback, might be incorrect if not a full URI
        return URIRef(term)  # Assume full URI or needs no prefix

    def get_entity_details(self, entity_uri_or_prefixed_name: str) -> dict:
        """
        Retrieves details for a given ontology entity (class or property).
        """
        entity_uri = self._resolve_uri(entity_uri_or_prefixed_name)
        details = {"uri": str(entity_uri)}

        # Get label
        label = self.graph.value(subject=entity_uri, predicate=RDFS.label)
        if label:
            details["label"] = str(label)

        # Get comment
        comment = self.graph.value(subject=entity_uri, predicate=RDFS.comment)
        if comment:
            details["comment"] = str(comment)

        # Get rdf:type (especially for properties)
        rdf_types = [
            str(t) for t in self.graph.objects(subject=entity_uri, predicate=RDF.type)
        ]
        if rdf_types:
            details["rdf_type"] = rdf_types

        # For properties, get domain and range
        if OWL.ObjectProperty in self.graph.objects(
            subject=entity_uri, predicate=RDF.type
        ) or OWL.DatatypeProperty in self.graph.objects(
            subject=entity_uri, predicate=RDF.type
        ):
            domain = self.graph.value(subject=entity_uri, predicate=RDFS.domain)
            if domain:
                details["domain"] = str(domain)
            range_val = self.graph.value(subject=entity_uri, predicate=RDFS.range)
            if range_val:
                details["range"] = str(range_val)

        # For classes, get superclasses
        if OWL.Class in self.graph.objects(subject=entity_uri, predicate=RDF.type):
            superclasses = [
                str(sc)
                for sc in self.graph.objects(
                    subject=entity_uri, predicate=RDFS.subClassOf
                )
            ]
            if superclasses:
                details["subClassOf"] = superclasses

        return details

    def list_classes(self, namespace_filter: str = None) -> list:
        """
        Lists all OWL classes in the ontology, optionally filtered by namespace.
        """
        classes = []
        for s, p, o in self.graph.triples((None, RDF.type, OWL.Class)):
            if isinstance(s, URIRef):  # Ensure it's a URI, not a blank node
                if namespace_filter:
                    if str(s).startswith(
                        str(self.namespaces.get(namespace_filter, namespace_filter))
                    ):  # Allow full URI or prefix
                        classes.append(str(s))
                else:
                    classes.append(str(s))
        return sorted(classes)

    def find_concepts(
        self, keyword: str
    ):  # Kept for compatibility, simple label search
        """
        Finds concepts (classes or properties) by searching labels.
        """
        logger.info(f"Searching for concepts related to: {keyword.lower()}")
        results = []
        for s, p, o in self.graph.triples((None, RDFS.label, None)):
            if keyword.lower() in str(o).lower():
                details = self.get_entity_details(str(s))
                results.append(details)
        return results


if __name__ == "__main__":
    # Assuming the script is run from the project root or PYTHONPATH is set appropriately
    # For testing, ensure the path to ontology is correct relative to where this script is run from.
    # If running from /app, then "ontology/..." is correct.
    ontology_file_path = (
        "ontology/credit_analysis_ontology_v0.3/credit_ontology_v0.3.ttl"
    )
    navigator = OntologyNavigator(ontology_path=ontology_file_path)

    logger.info("\n--- Testing New ADK Architecture Terms ---")

    agent_details = navigator.get_entity_details("adkarch:Agent")
    logger.info(f"Details for adkarch:Agent:\n{json.dumps(agent_details, indent=2)}")

    analysis_agent_details = navigator.get_entity_details("adkarch:AnalysisAgent")
    logger.info(
        f"Details for adkarch:AnalysisAgent:\n{json.dumps(analysis_agent_details, indent=2)}"
    )

    semantic_skill_details = navigator.get_entity_details("adkarch:SemanticSkill")
    logger.info(
        f"Details for adkarch:SemanticSkill:\n{json.dumps(semantic_skill_details, indent=2)}"
    )

    uses_skill_details = navigator.get_entity_details("adkarch:usesSkill")
    logger.info(
        f"Details for adkarch:usesSkill:\n{json.dumps(uses_skill_details, indent=2)}"
    )

    skill_name_details = navigator.get_entity_details("adkarch:skillName")
    logger.info(
        f"Details for adkarch:skillName:\n{json.dumps(skill_name_details, indent=2)}"
    )

    logger.info("\n--- Listing All Classes (to check for new ADK classes) ---")
    all_classes = navigator.list_classes()
    adk_classes_found = []
    for cls_uri in all_classes:
        if "adk/architecture#" in cls_uri:
            adk_classes_found.append(cls_uri)
    if adk_classes_found:
        logger.info(f"Found ADK Architecture classes: {adk_classes_found}")
    else:
        logger.warning("No ADK Architecture classes found in the list of all classes.")
        # logger.info(f"All classes found: {all_classes}") # Uncomment for full list if needed

    logger.info("\n--- Example search for 'Agent' (should find adkarch:Agent) ---")
    # import json # No longer needed here, moved to top
    agent_search_results = navigator.find_concepts("Agent")
    logger.info(
        f"Search results for 'Agent':\n{json.dumps(agent_search_results, indent=2)}"
    )
