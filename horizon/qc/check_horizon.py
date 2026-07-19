"""Machine-QC for the legislative-horizon layer. Three checks, all offline (ROBOT + the shared
import-catalog.xml -> local BFO/CCO/IAO):

  1. CONSISTENCY  -- base + transform + horizon T-Box + demo A-Box reasons ELK-consistent,
                     0 unsatisfiable classes.
  2. INVARIANT (structural) -- the A-Box asserts NO fact about a base/transform term: every triple's
                     subject is a horizon individual; base/transform IRIs appear ONLY as punned objects
                     of wouldAffect / graduatedTo.
  3. INVARIANT (entailment) -- reasoning base+transform+horizon+A-Box yields NO new class subsumption
                     among base/transform classes vs base+transform alone (prospective != asserted,
                     proven by an OWL reasoner, not asserted).

  ROBOT=robot (on PATH)  PYTHON=a python with rdflib
  python horizon/qc/check_horizon.py
"""
import os
import subprocess
import sys

from rdflib import Graph, RDF, RDFS, URIRef
from rdflib.namespace import OWL

HERE = os.path.dirname(os.path.abspath(__file__))
HORIZON = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(HORIZON, ".."))
CATALOG = os.path.join(REPO, "qc", "import-catalog.xml")
ABOX = os.path.join(HORIZON, "demo", "rwx-acq-horizon-demo.ttl")
SHIM_FULL = os.path.join(HERE, "shim_full.ttl")
SHIM_BASE = os.path.join(HERE, "shim_baseline.ttl")
ROBOT = os.environ.get("ROBOT", "robot")
OUT_FULL = "/tmp/horizon-reasoned-full.ttl"
OUT_BASE = "/tmp/horizon-reasoned-baseline.ttl"

HORIZON_NS = "https://w3id.org/rockworx/acq/horizon#"
BT_NS = ("https://w3id.org/rockworx/acq#", "https://w3id.org/rockworx/acq/transform#")


def _robot_reason(inputs, out):
    cmd = [ROBOT, "merge", "--catalog", CATALOG]
    for i in inputs:
        cmd += ["--input", i]
    cmd += ["reason", "--reasoner", "ELK", "--output", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def _class_subsumptions(ttl, ns_filter):
    """Named-class subClassOf/equivalentClass axioms whose subject IRI starts with one of ns_filter."""
    g = Graph(); g.parse(ttl, format="turtle")
    out = set()
    for pred in (RDFS.subClassOf, OWL.equivalentClass):
        for s, o in g.subject_objects(pred):
            if isinstance(s, URIRef) and isinstance(o, URIRef) and str(s).startswith(ns_filter):
                out.add((str(s), str(pred), str(o)))
    return out


def check_consistency():
    rc, log = _robot_reason([SHIM_FULL, ABOX], OUT_FULL)
    ok = rc == 0 and "unsatisfiable" not in log.lower()
    return ok, ("ELK-consistent, 0 unsatisfiable" if ok else f"rc={rc}\n{log[-600:]}")


def check_structural():
    g = Graph(); g.parse(ABOX, format="turtle")
    offenders = []
    for s, p, o in g:
        if isinstance(s, URIRef) and not str(s).startswith(HORIZON_NS):
            offenders.append(f"base/transform IRI as SUBJECT: {s} {p}")
    # base/transform IRIs may appear only as objects of wouldAffect / graduatedTo
    allowed_obj_preds = {URIRef(HORIZON_NS + "wouldAffect"), URIRef(HORIZON_NS + "graduatedTo")}
    for s, p, o in g:
        if isinstance(o, URIRef) and any(str(o).startswith(ns) for ns in BT_NS):
            if p not in allowed_obj_preds:
                offenders.append(f"base/transform IRI as non-punned object: {s} {p} {o}")
    return (not offenders), ("A-Box asserts nothing about base/transform; they appear only as punned "
                             "wouldAffect/graduatedTo objects" if not offenders else "\n".join(offenders))


def check_invariant_entailment():
    rc, log = _robot_reason([SHIM_BASE], OUT_BASE)
    if rc != 0:
        return False, f"baseline reasoning failed rc={rc}\n{log[-400:]}"
    for ns in BT_NS:
        full = _class_subsumptions(OUT_FULL, ns)
        base = _class_subsumptions(OUT_BASE, ns)
        new = full - base
        if new:
            return False, f"horizon INTRODUCED subsumptions on {ns}:\n" + "\n".join(sorted(map(str, new)))
    return True, "no new class subsumption among base/transform classes -> prospective != asserted (reasoner-proven)"


def main():
    checks = [("CONSISTENCY (ELK, full stack)", check_consistency),
              ("INVARIANT structural (A-Box)", check_structural),
              ("INVARIANT entailment (reasoner diff)", check_invariant_entailment)]
    all_ok = True
    print("=" * 84)
    print("SKEDS legislative-horizon -- machine QC")
    print("=" * 84)
    for name, fn in checks:
        ok, detail = fn()
        all_ok = all_ok and ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        print(f"       {detail}")
    print("=" * 84)
    print("ALL CHECKS PASS" if all_ok else "QC FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
