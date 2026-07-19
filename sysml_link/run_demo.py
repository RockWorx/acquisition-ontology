"""Reproducible SysML-v2 <-> acquisition-ontology link demonstrator (Python-only).

Loads the committed model Turtle (the acquisition RDF extracted from a real SysML v2 pilot
AST -- see TOOLCHAIN.md / transform.py). The model records the verification's RESULT (FAIL)
but asserts NO program risk. The risk is DERIVED by a rule (derive_risk.rq) -- an Open,
HIGH-severity ProgramRisk from the FAIL -- so nothing is hand-asserted.

Then it validates the Milestone-B SHACL gate rule -- which is SELF-CONTAINED (it keys on the
recorded FAIL + riskDisposition directly, so it is sound on the raw model without first
running the derivation) -- under three states, proving the link ENFORCES the acquisition
rule AND responds to the program's state:
  1. as-built                       -> failed KPP verification, not accepted -> gate BLOCKED;
  2. fix the design (result->PASS)   -> no failed verification              -> gate PASSES;
  3. accept the risk (disp->Accepted)-> failed test retained but accepted   -> gate PASSES.

Run:  wsl ... ~/.venvs/f16union/bin/python -m rwx.skeds.sysml_link.run_demo
"""

import os

import rdflib
from pyshacl import validate

HERE = os.path.dirname(__file__)
DEMO = os.path.join(HERE, "demo")
SYSML_NS = "https://w3id.org/rockworx/acq/sysml#"


def load_model():
    """The acquisition RDF extracted from the SysML v2 model (structure + verificationResult)."""
    g = rdflib.Graph()
    g.parse(os.path.join(DEMO, "RiskDrivenMilestone.model.ttl"))
    return g


def _copy(graph):
    g = rdflib.Graph()
    for triple in graph:
        g.add(triple)
    return g


def derive_risk(graph):
    """Apply the risk-derivation rule (a FAIL verification -> Open/HIGH ProgramRisk)."""
    rule = open(os.path.join(DEMO, "queries", "derive_risk.rq"), encoding="utf-8").read()
    out = _copy(graph)
    for triple in graph.query(rule):
        out.add(triple)
    return out


def fix_the_design(graph):
    """Mitigation 1 -- the design is fixed: result FAIL -> PASS, so no risk is derived."""
    out = rdflib.Graph()
    vr = rdflib.URIRef(SYSML_NS + "verificationResult")
    for s, p, o in graph:
        out.add((s, p, rdflib.Literal("PASS")) if (p == vr and str(o) == "FAIL") else (s, p, o))
    return out


def accept_the_risk(graph):
    """Mitigation 2 -- risk-management action: riskDisposition -> Accepted (failed test retained)."""
    out = rdflib.Graph()
    rd = rdflib.URIRef(SYSML_NS + "riskDisposition")
    for s, p, o in graph:
        out.add((s, p, rdflib.Literal("Accepted")) if p == rd else (s, p, o))
    return out


def blocking_findings(graph):
    query = open(os.path.join(DEMO, "queries", "whats_blocking_msb.rq"), encoding="utf-8").read()
    return list(graph.query(query))


def gate_passes(graph):
    """True iff the Milestone-B SHACL gate rule is satisfied (gate is passable)."""
    shapes = rdflib.Graph().parse(os.path.join(DEMO, "shapes", "msb_gate.shape.ttl"))
    conforms, _, text = validate(graph, shacl_graph=shapes, inference="none", advanced=True)
    return conforms, text


def vocabulary_conforms(graph):
    """True iff every string-valued link property is within its controlled vocabulary
    (so a typo like 'fail'/'open' is a reported violation, not a silent false-negative)."""
    shapes = rdflib.Graph().parse(os.path.join(DEMO, "shapes", "vocab.shape.ttl"))
    conforms, _, _ = validate(graph, shacl_graph=shapes, inference="none")
    return conforms


def main():
    model = load_model()
    print("=" * 68)
    print("QUERY: What is preventing a successful Milestone B decision?")
    print("=" * 68)
    for row in blocking_findings(derive_risk(model)):  # derive the risk for the narrative
        print(f"  gate         : {row.gate}")
        print(f"  blocked-KPP  : {row.kpp}")
        print(f"  verification : {row.verification} (recorded result: FAIL)")
        print(f"  program-risk : DERIVED (Open, HIGH) from the failed verification")
        print(f"  KPP authority: {row.authority}")

    # the SHACL shape is SELF-CONTAINED: it validates the raw model directly (no derive pass)
    print("\nSHACL Milestone-B gate rule (validated on the raw model):")
    print("  as-built                               -> gate passable:", gate_passes(model)[0])
    print("  fix the design (result -> PASS)        -> gate passable:", gate_passes(fix_the_design(model))[0])
    print("  accept the risk (disposition->Accepted)-> gate passable:", gate_passes(accept_the_risk(model))[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
