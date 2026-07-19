"""LOAD stage -- emit tagged candidate changes as NON-ASSERTED individuals in the rwx-acq-horizon layer.

Every triple has as its SUBJECT an information entity that really exists today (a bill; a candidate-change
description) and states what that proposal SAYS or WOULD do -- a true fact ABOUT THE PROPOSAL. No triple
asserts a fact about the acquisition world that is not currently true. `wouldAffect` references the target
construct's class IRI via OWL 2 punning and carries no propagating semantics.
"""
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS

HORIZON_NS = "https://w3id.org/rockworx/acq/horizon#"
H = Namespace(HORIZON_NS)
RWXA = Namespace("https://w3id.org/rockworx/acq#")
RWXT = Namespace("https://w3id.org/rockworx/acq/transform#")
PROV = Namespace("http://www.w3.org/ns/prov#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")


def _term_uri(qname):
    pfx, local = qname.split(":")
    return {"rwxa": RWXA, "rwxt": RWXT}[pfx][local]


def _bind(g):
    g.bind("rwxh", H); g.bind("rwxa", RWXA); g.bind("rwxt", RWXT)
    g.bind("prov", PROV); g.bind("owl", OWL); g.bind("dcterms", DCTERMS); g.bind("skos", SKOS)


def load_candidates(candidates, instruments, out_ttl):
    """Emit the horizon A-Box: instruments + prospective candidate changes (non-asserted).
    An enacted candidate is emitted as owl:deprecated + graduatedTo (it has left the horizon)."""
    g = Graph(); _bind(g)
    seen_instruments = set()
    for c in candidates:
        iid = c["instrument_id"]
        if iid not in seen_instruments:
            inst = H[iid]
            g.add((inst, RDF.type, H.LegislativeInstrument))
            g.add((inst, RDFS.label, Literal(instruments[iid]["label"])))
            g.add((inst, H.legislativeMaturity, Literal(instruments[iid]["maturity"])))
            seen_instruments.add(iid)
        cu = H[c["id"]]
        g.add((cu, RDF.type, H.LegislativeCandidateChange))
        g.add((cu, RDFS.label, Literal(c["label"])))
        g.add((cu, PROV.wasDerivedFrom, H[iid]))
        for term in c["wouldAffect"]:                                  # multi-target: one triple per construct
            g.add((cu, H.wouldAffect, _term_uri(term)))                # punned class-as-individual
        g.add((cu, H.legislativeMaturity, Literal(c["maturity"])))
        g.add((cu, H.changeType, Literal(c["changeType"])))
        g.add((cu, H.enactmentLikelihood, Literal(c["enactmentLikelihood"])))
        g.add((cu, H.likelihoodBasis, Literal(c["likelihoodBasis"])))
        g.add((cu, H.impactAssessment, Literal(c["impactAssessment"])))
        if c.get("prospectiveAuthorityTier"):                      # horizon-native; never the transform's tier
            g.add((cu, H.prospectiveAuthorityTier, Literal(c["prospectiveAuthorityTier"])))
        g.add((cu, DCTERMS.source, Literal(c["source"])))
        if c.get("graduated"):
            g.add((cu, OWL.deprecated, Literal(True)))
            g.add((cu, H.graduatedTo, _term_uri(c["graduatedTo"])))
    g.serialize(destination=out_ttl, format="turtle")
    return g


def emit_graduation_proposals(candidates, out_ttl):
    """For each ENACTED candidate, emit the PROPOSED append-only migration into the transform layer:
    add the now-real construct's STATUTE provenance, KEEPING its prior POLICY link (a dated authority
    history). This is a PROPOSAL for CCB ratification -- the pipeline proposes, a human disposes; no
    reasoner auto-promotes anything."""
    g = Graph(); _bind(g)
    n = 0
    for c in candidates:
        if not c.get("graduated"):
            continue
        target = _term_uri(c["graduatedTo"])
        law = H[c["instrument_id"] + "_" + c["id"].replace("cand_", "")]
        g.add((law, RDF.type, H.LegislativeInstrument))
        g.add((law, RDFS.label, Literal(f"{c['section']} of {c['instrument_label']}")))
        g.add((law, H.legislativeMaturity, Literal("enacted")))
        # the append-only migration (PROPOSED): STATUTE provenance added to the existing construct
        g.add((target, PROV.wasDerivedFrom, law))
        g.add((target, RWXT.authorityTier, Literal("STATUTE")))
        g.add((target, RDFS.comment,
               Literal(f"GRADUATION PROPOSAL (CCB to ratify): {c['section']} of {c['instrument_label']} "
                       f"codifies this construct in statute. Append STATUTE provenance; KEEP the existing "
                       f"POLICY (EO 14265) link. Source: {c['source']}.")))
        n += 1
    g.serialize(destination=out_ttl, format="turtle")
    return n
