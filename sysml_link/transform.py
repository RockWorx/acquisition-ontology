"""Transform a SysML v2 model AST (OMG pilot export) into RDF typed in the acquisition ontology.

Reads the 0.60.1 `{identity, payload}` envelope AST and extracts the Mode-B assertions:
  - each @tagged element  -> `element rdf:type <acquisition class>`
  - each named connection -> `source <acquisition/bridge/PROV property> target`
Each tag/connection `declaredName` is resolved to its FULL ontology IRI via a name->IRI map
built from the base + bridge ontologies -- so tags spanning THREE namespaces (rwxacq /
rwxacq-sysml / PROV) each land in the right namespace. The reference tool's single
`REPLACE(..., input_ontology)` maps every tag to one namespace and cannot do this.

`gen_jsonld` additionally emits the AST enriched with OMG's per-metaclass JSON-LD @context
-- the standards-blessed "SysML-v2-AST-is-RDF" seam -- for consumers who want the model as
plain RDF. Pattern credit: max-thoma/semantic-tag-utility (BSD-3).
"""

import json
import os

from rdflib import RDF, RDFS, Graph, Literal, URIRef
from rdflib.namespace import OWL

from .taglib import _as_list, _local_name

DEFAULT_BASE = "https://w3id.org/rockworx/demo#"
SYSML_NS = "https://w3id.org/rockworx/acq/sysml#"
# SysML attribute name -> bridge datatype-property local name (e.g. a test's `result`
# attribute becomes rwxsysml:verificationResult, which the risk-derivation rule keys on).
DEFAULT_ATTR_MAP = {"result": "verificationResult", "riskDisposition": "riskDisposition"}


def _ref(value):
    """A SysML AST reference is {@id: ...} or [{@id: ...}]; return the id (or None)."""
    if isinstance(value, list):
        value = value[0] if value else None
    return value["@id"] if value else None


def _refs(value):
    """All ids from a reference that may be a single {@id} or a list of them."""
    if not value:
        return []
    if not isinstance(value, list):
        value = [value]
    return [v["@id"] for v in value if v]


# SysML usage @types that carry a modeler-facing name worth an rdfs:label.
_LABELLED_TYPES = {"PartUsage", "ActionUsage", "RequirementUsage", "AttributeUsage",
                   "PortUsage", "VerificationCaseUsage"}


def _flatten(ast):
    """0.60.1 `{identity, payload}` envelope -> {element_id: payload(+@id)}."""
    flat = {}
    for item in ast:
        payload = dict(item["payload"])
        payload["@id"] = item["identity"]["@id"]
        flat[payload["@id"]] = payload
    return flat


def name_to_iri(ttl_paths, namespaces):
    """Map each owl:Class / owl:ObjectProperty local name to its full IRI, across namespaces."""
    namespaces = [str(ns) for ns in _as_list(namespaces)]
    graph = Graph()
    for path in _as_list(ttl_paths):
        graph.parse(path)
    mapping = {}
    for rdf_type in (OWL.Class, OWL.ObjectProperty):
        for subject in graph.subjects(RDF.type, rdf_type, unique=True):
            local = _local_name(str(subject), namespaces)
            if local:
                mapping[local] = str(subject)
    return mapping


def gen_jsonld(ast_path, metadata_dir, base_uri, out_path):
    """Enrich the AST with OMG's per-metaclass JSON-LD @context (the standards RDF seam)."""
    ast = json.load(open(ast_path, encoding="utf-8"))
    entities = []
    for item in ast:
        entry = dict(item["payload"])
        entry["@id"] = item["identity"]["@id"]
        ctx = json.load(
            open(os.path.join(metadata_dir, entry["@type"] + ".jsonld"), encoding="utf-8")
        )
        entry["@context"] = ctx["@context"]
        entry["@context"]["@base"] = base_uri
        entities.append(entry)
    json.dump(entities, open(out_path, "w", encoding="utf-8"), indent=2)
    return out_path


def _literal_value(flat, element):
    """The value of the first Literal* member of an AttributeUsage, or None."""
    for mid in _refs(element.get("ownedMember")) + _refs(element.get("member")):
        member = flat.get(mid, {})
        if "Literal" in member.get("@type", "") and "value" in member:
            return member["value"]
    return None


def _verdict_value(flat, verification):
    """The VerdictKind enum name of a VerificationCaseUsage's result (e.g. 'fail'), or None.

    Native SysML v2: the case's `result` is a ReferenceUsage (verdict) whose owned
    FeatureReferenceExpression `referent`s the VerdictKind enumeration value.
    """
    for rid in _refs(verification.get("result")):
        verdict = flat.get(rid, {})
        for cid in _refs(verdict.get("ownedMember")):
            candidate = flat.get(cid, {})
            if "FeatureReferenceExpression" in candidate.get("@type", ""):
                for ref_id in _refs(candidate.get("referent")):
                    enum = flat.get(ref_id, {})
                    if enum.get("declaredName"):
                        return enum["declaredName"]
    return None


def transform(ast_path, ttl_paths, namespaces, base_uri=DEFAULT_BASE, attr_map=None):
    """Return (rdflib.Graph of Mode-B triples, sorted list of unresolved tag/connection names)."""
    attr_map = DEFAULT_ATTR_MAP if attr_map is None else attr_map
    flat = _flatten(json.load(open(ast_path, encoding="utf-8")))
    n2i = name_to_iri(ttl_paths, namespaces)

    graph = Graph()
    graph.bind("rwxacq", "https://w3id.org/rockworx/acq#")
    graph.bind("rwxsysml", "https://w3id.org/rockworx/acq/sysml#")
    graph.bind("prov", "http://www.w3.org/ns/prov#")

    def uri(element_id):
        return URIRef(base_uri + element_id)

    unresolved = set()
    for element in flat.values():
        etype = element["@type"]
        if etype == "MetadataUsage":
            def_id = _ref(element.get("metadataDefinition"))
            tag = flat.get(def_id, {}).get("declaredName") if def_id else None
            iri = n2i.get(tag)
            if iri:
                # a tag may annotate MORE THAN ONE element -- type all of them
                for ann in _refs(element.get("annotatedElement")):
                    graph.add((uri(ann), RDF.type, URIRef(iri)))
            elif tag:
                unresolved.add(tag)
        elif etype == "ConnectionUsage":
            pname = element.get("declaredName")
            iri = n2i.get(pname)
            src, tgt = _ref(element.get("source")), _ref(element.get("target"))
            if iri and src and tgt:            # skip dangling/partial connections safely
                graph.add((uri(src), URIRef(iri), uri(tgt)))
            elif pname and not iri:
                unresolved.add(pname)
        elif etype == "SatisfyRequirementUsage":
            # native SysML v2 `satisfy X by Y` -> Y (design) satisfies X (requirement)
            design = _ref(element.get("satisfyingFeature"))
            requirement = _ref(element.get("satisfiedRequirement"))
            iri = n2i.get("satisfies")
            if iri and design and requirement:
                graph.add((uri(design), URIRef(iri), uri(requirement)))
        elif etype == "VerificationCaseUsage":
            # native SysML v2 verification: the case `verify`s its requirement, and its
            # VerdictKind result becomes the verificationResult datum the rules key on.
            requirement = _ref(element.get("verifiedRequirement"))
            verifies_iri = n2i.get("verifies")
            if verifies_iri and requirement:
                graph.add((uri(element["@id"]), URIRef(verifies_iri), uri(requirement)))
            verdict = _verdict_value(flat, element)
            if verdict:
                graph.add((uri(element["@id"]), URIRef(SYSML_NS + "verificationResult"),
                           Literal(verdict.upper())))

    # mapped attribute values -> datatype-property triples on the owning element
    # (e.g. a verification's `result = "FAIL"` -> owner rwxsysml:verificationResult "FAIL")
    for element in flat.values():
        if element["@type"] == "AttributeUsage" and element.get("declaredName") in attr_map:
            owner = _ref(element.get("owningType") or element.get("owner"))
            value = _literal_value(flat, element)
            if owner and value is not None:
                prop = URIRef(SYSML_NS + attr_map[element["declaredName"]])
                graph.add((uri(owner), prop, Literal(value)))

    # human-readable labels for the model elements (parts, actions, requirements, ...)
    for element in flat.values():
        if element["@type"] in _LABELLED_TYPES and element.get("declaredName"):
            graph.add((uri(element["@id"]), RDFS.label, Literal(element["declaredName"])))

    return graph, sorted(unresolved)
