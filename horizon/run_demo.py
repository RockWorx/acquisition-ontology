"""Run the SKEDS legislative-horizon demonstrator end to end:
    POLL (Congress.gov real status) -> SHRED (LLM-extract, grounded) -> TAG -> LOAD (non-asserted) ->
    QUERY ("what is on the horizon for Milestone B / the MCA spine, and how likely?") + GRADUATION.

Offline + reproducible from cached real data by default (rdflib; no LLM, no network); `--live` re-polls
Congress.gov and re-shreds (needs DATAGOV_API_KEY + your own LLM via horizon.shred.set_extractor).
    python -m horizon.run_demo            # offline, from cache
    python -m horizon.run_demo --live     # re-poll + re-shred against the live APIs
"""
import json
import os
import sys

from rdflib import Graph

from .poll import poll, MATURITY_LADDER
from .shred import shred
from .tag import tag
from .load import load_candidates, emit_graduation_proposals
from .bill_text import fulltext_provisions

HERE = os.path.dirname(__file__)
DEMO = os.path.join(HERE, "demo")
REPO = os.path.abspath(os.path.join(HERE, ".."))
SEED = os.path.join(DEMO, "seed_provisions.json")
POLL_CACHE = os.path.join(DEMO, "poll_cache.json")
SHRED_CACHE = os.path.join(DEMO, "shred_cache.json")
ABOX = os.path.join(DEMO, "rwx-acq-horizon-demo.ttl")
GRAD = os.path.join(DEMO, "graduation_proposed.ttl")
QUERY = os.path.join(DEMO, "queries", "whats_on_horizon.rq")
TBOX = os.path.join(HERE, "rwx-acq-horizon.ttl")
BASE = os.path.join(REPO, "rwx-acq-base.ttl")
TRANSFORM = os.path.join(REPO, "rwx-acq-transform.ttl")


def build(live=False):
    with open(SEED, encoding="utf-8") as fh:
        seed = json.load(fh)
    instruments = seed["instruments"]
    # curated FY26/FY27 provisions + FULL-TEXT-extracted H.R.8800 Title VIII acquisition sections
    ft = fulltext_provisions("hr8800_119", 119, "hr", 8800, DEMO, live=live, max_sections=3)
    provisions = list(seed["provisions"]) + ft
    polled = poll(instruments, POLL_CACHE, live=live)
    shredded = shred(provisions, SHRED_CACHE, live=live)
    candidates = [tag(p, p["instrument"], polled[p["instrument"]], shredded[p["id"]]) for p in provisions]
    load_candidates(candidates, polled, ABOX)
    n_grad = emit_graduation_proposals(candidates, GRAD)
    return seed, polled, candidates, n_grad


def _mrank(m):
    return MATURITY_LADDER.index(m) if m in MATURITY_LADDER else -1


def query_horizon():
    g = Graph()
    for f in (TBOX, BASE, TRANSFORM, ABOX):
        g.parse(f, format="turtle")
    with open(QUERY, encoding="utf-8") as fh:
        rows = list(g.query(fh.read()))
    rows.sort(key=lambda r: (_mrank(str(r.maturity)), str(r.likelihood)), reverse=True)
    return rows


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    live = "--live" in argv
    seed, polled, candidates, n_grad = build(live=live)

    print("=" * 92)
    print("SKEDS LEGISLATIVE-HORIZON DEMONSTRATOR  --  POLL -> SHRED -> TAG -> LOAD")
    print("  epistemic discipline: PROSPECTIVE != ASSERTED (horizon layer strictly separate from base/transform)")
    print("=" * 92)

    print("\nPOLLED INSTRUMENTS (legislative maturity straight from Congress.gov):")
    for iid, rec in polled.items():
        print(f"  [{rec['maturity']:>18}]  {rec['label']}")
    print(f"  omnibus/CR: {seed['omnibus_cr_status']}")
    if seed.get("fulltext_note"):
        print(f"  full-text ingest: {seed['fulltext_note']}")

    print('\nQUERY -- "What is on the legislative horizon for Milestone B / the MCA spine, and how likely?"')
    print("-" * 92)
    for r in query_horizon():
        print(f"  * {r.affects}  [{r.maturity} | likelihood {r.likelihood} | {r.changeType}]")
        print(f"      {r.candidate}")
        print(f"      -> {r.impact}")
    print("-" * 92)
    print("  (Every row is a PROPOSAL, not a fact. Likelihood is a flagged judgment with a sourced basis;")
    print("   see rwxh:likelihoodBasis in the A-Box. None of this is asserted into base/transform.)")

    print(f"\nGRADUATION -- {n_grad} enacted candidate(s) PROPOSED for append-only migration into transform:")
    for c in candidates:
        if c.get("graduated"):
            print(f"  * {c['section']} of {c['instrument_label']}  ->  {c['graduatedTo']}")
            print(f"      ENACTED; append STATUTE provenance, KEEP the existing POLICY (EO 14265) link.")
            print(f"      (proposal in graduation_proposed.ttl; CCB ratifies -- no reasoner auto-promotes it.)")
    print("\nArtifacts: rwx-acq-horizon-demo.ttl (A-Box)  |  graduation_proposed.ttl  |  poll_cache.json  |  shred_cache.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
