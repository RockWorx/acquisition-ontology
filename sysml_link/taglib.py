"""Generate a native SysML v2 tag library from the RockWorx acquisition ontology.

Pattern credit: max-thoma/semantic-tag-utility (BSD-3, IEEE INDIN 2024) -- every
`owl:Class` becomes a SysML v2 `metadata def`, every `owl:ObjectProperty` a
`connection def`. We reimplement it (rather than call the tool) so the emitted library
is fit for a PUBLIC artifact: it stamps the real class/property IRI as the comment (the
tool stamps the local .ttl file path) and it does not double-prefix names.

MULTI-NAMESPACE: a single demonstrator tag library must aggregate classes from the base
namespace with bridge properties from the SysML-link namespace AND reused properties from
base/PROV (e.g. `informs`, `wasDerivedFrom`). So `namespaces` is a LIST, and one or more
`ttl_paths` are merged into one graph before collection. Names are emitted WITHOUT a
prefix -- the SysML package already namespace-protects the identifiers.
"""

import rdflib
from rdflib.namespace import OWL, RDF

DEFAULT_PREFIX = ""
DEFAULT_PACKAGE = "RWXAcqTags"


def _as_list(value):
    if value is None:
        return None
    return [value] if isinstance(value, str) else list(value)


def _local_name(iri, namespaces):
    """Strip the first matching namespace; return the local name or None."""
    for ns in namespaces:
        if iri.startswith(ns):
            return iri[len(ns):]
    return None


def _collect(graph, rdf_type, namespaces, allow):
    """Local-name/IRI pairs for subjects of `rdf_type` in any of `namespaces`."""
    found = set()
    for subject in graph.subjects(RDF.type, rdf_type, unique=True):
        iri = str(subject)
        local = _local_name(iri, namespaces)
        if not local or (allow is not None and local not in allow):
            continue
        found.add((local, iri))
    return sorted(found)


def generate_tag_library(
    ttl_paths,
    namespaces,
    prefix=DEFAULT_PREFIX,
    package=DEFAULT_PACKAGE,
    classes=None,
    properties=None,
):
    """Return SysML v2 source text for a tag library.

    `ttl_paths` : one path or a list of Turtle files, merged into one graph.
    `namespaces`: one namespace or a list; a subject is included iff its IRI starts with
                  one of them (so base + bridge + PROV can coexist in one library).
    `classes` / `properties`: optional allow-lists of LOCAL names; None = all in the
                  namespaces, [] = none.
    """
    namespaces = [str(ns) for ns in _as_list(namespaces)]
    graph = rdflib.Graph()
    for path in _as_list(ttl_paths):
        graph.parse(path)

    class_defs = _collect(graph, OWL.Class, namespaces, classes)
    prop_defs = _collect(graph, OWL.ObjectProperty, namespaces, properties)

    lines = [
        f"package {package} {{",
        "\t//  This package was auto-generated from the RockWorx acquisition ontology",
        "",
    ]
    for local, iri in class_defs:
        lines.append(f"\t//  {iri}")
        lines.append(f"\tmetadata def {prefix}{local};")
        lines.append("")
    for local, iri in prop_defs:
        lines.append(f"\t//  {iri}")
        lines.append(f"\tconnection def {prefix}{local} {{")
        lines.append("\t\tend sub;")
        lines.append("\t\tend obj;")
        lines.append("\t}")
        lines.append("")
    lines.append("}")
    return "\n".join(lines) + "\n"
