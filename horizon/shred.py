"""SHRED stage -- LLM-extract a structured acquisition-impact from a real legislative-provision text,
GROUNDED in that text (never invented). Maps free provision language onto the fixed acquisition-ontology
vocabulary: which construct it would affect, the change type, and a one-sentence impact.

The LLM is PLUGGABLE -- call set_extractor(fn) with your own model, where fn(prompt, system) -> str.
Results are cached to JSON so the demo runs offline with NO LLM (pass live=True to re-extract). The
committed shred_cache.json reproduces the demo from the cited real provision text.
"""
import json
import os
import re

# The construct vocabulary the SHRED may map a provision onto (base rwxa: + transform rwxt:),
# each with a one-line description so the extractor can pick the MOST SPECIFIC applicable construct.
VOCAB_DESC = {
    "rwxa:AcquisitionGate": "the milestone DECISION ACT (Milestone A/B/C) -- choose this for changes to which programs face a milestone decision, or how that decision is made/authorized",
    "rwxa:AcquisitionMilestone": "the milestone BOUNDARY as lifecycle STRUCTURE -- choose ONLY for changes that add, remove, or re-order the milestones themselves (NOT changes to which programs pass a decision -- that is AcquisitionGate)",
    "rwxa:AcquisitionPhase": "a lifecycle phase (MSA, TMRR, EMD, P&D, O&S)",
    "rwxa:TechnicalReview": "a technical review (SRR, PDR, CDR, TRR)",
    "rwxa:RequirementDeterminationProcess": "the process that determines capability requirements",
    "rwxa:FundingSource": "a source/appropriation of program funding (incl. contracting/OTA pathways)",
    "rwxa:KeyPerformanceParameter": "a KPP -- a minimum performance threshold",
    "rwxa:ProgramOversightOrganization": "an organization overseeing programs (generic; prefer PAE if portfolio-level)",
    "rwxa:ProgramRisk": "a program's disposition to an undesired outcome",
    "rwxt:PortfolioAcquisitionExecutive": "the PAE -- the portfolio-level acquisition authority (reform)",
    "rwxt:JointForceRequirementsProcess": "the JFRP that replaced JCIDS (reform)",
    "rwxt:KeyOperationalProblem": "the KOP -- the objective-form requirements root (reform)",
    "rwxt:CapabilityTradeCouncil": "the portfolio-level requirement-vs-cost trade body (reform)",
    "rwxt:PortfolioScorecard": "the data-driven portfolio performance record (reform)",
    "rwxt:JointAccelerationReserve": "the CAPE reserve bridging the valley of death (reform)",
}
VOCAB = list(VOCAB_DESC)
_LOCAL = {q.split(":")[1]: q for q in VOCAB}   # bare-local-name -> canonical qname

_SYSTEM = (
    "You are a defense-acquisition ontology EXTRACTION engine. Given one legislative provision and a "
    "fixed vocabulary of acquisition-ontology constructs (each with a description), output STRICT JSON "
    'with exactly these keys: {"wouldAffect": ["<one or more terms copied verbatim from the vocabulary, '
    'each WITH its rwxa:/rwxt: prefix>"], "changeType": "ADD | MODIFY | SUPERSEDE", '
    '"impactAssessment": "<one sentence: the downstream effect on the acquisition process if enacted>"}. '
    "wouldAffect is a LIST. Most provisions change ONE construct, but some genuinely change SEVERAL DISTINCT "
    "constructs (for instance an oversight ROLE and a funding mechanism, or a requirements process and a "
    "review). List every construct the provision text genuinely changes -- and ONLY those. Do NOT list two "
    "near-synonymous constructs for the same change (read each description; pick the one that fits). Prefer "
    "the MOST SPECIFIC construct (e.g. PortfolioAcquisitionExecutive over the generic "
    "ProgramOversightOrganization). Never invent. Output JSON only, no prose, no code fences."
)


def _extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(m.group(0) if m else text)


def _normalize_term(term):
    """Accept either a canonical qname (rwxa:Foo) or a bare local name (Foo); return the canonical qname."""
    if term in VOCAB:
        return term
    local = term.split(":")[-1].strip()
    if local in _LOCAL:
        return _LOCAL[local]
    raise ValueError(f"SHRED returned an out-of-vocabulary term: {term!r}")


def _normalize_terms(terms):
    """Normalize the wouldAffect field (a list, or a lone string) to an ordered, de-duplicated qname list."""
    if isinstance(terms, str):
        terms = [terms]
    out = []
    for t in terms:
        q = _normalize_term(t)
        if q not in out:
            out.append(q)
    if not out:
        raise ValueError("SHRED returned no in-vocabulary wouldAffect constructs")
    return out


# Plug in your own LLM to run --live: set_extractor(fn) where fn(prompt, system) -> str (JSON).
# The committed shred_cache.json reproduces the demo offline with NO LLM.
_EXTRACTOR = None


def set_extractor(fn):
    """Register the LLM extraction callable fn(prompt, system) -> str used by --live SHRED."""
    global _EXTRACTOR
    _EXTRACTOR = fn


def _shred_one_live(prov):
    if _EXTRACTOR is None:
        raise RuntimeError("no LLM extractor registered -- call set_extractor(fn) to run --live; "
                           "the committed shred_cache.json reproduces the demo offline with no LLM.")
    vocab_block = "\n  ".join(f"{q}  -- {d}" for q, d in VOCAB_DESC.items())
    prompt = ("VOCABULARY (choose one OR MORE wouldAffect terms, copied verbatim WITH the prefix):\n  "
              + vocab_block
              + f"\n\nPROVISION ({prov['section']} of {prov['instrument']}):\n{prov['provision_text']}\n\n"
              "Return the JSON.")
    raw = _EXTRACTOR(prompt, _SYSTEM)
    obj = _extract_json(raw)
    return {"wouldAffect": _normalize_terms(obj.get("wouldAffect", [])),
            "changeType": obj["changeType"], "impactAssessment": obj["impactAssessment"]}


def shred(provisions, cache_path, live=False):
    """Return {provision_id: {wouldAffect, changeType, impactAssessment}}.
    live=True calls the LLM on each real provision text (and rewrites the cache); else reads the cache."""
    if not live and os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as fh:
            return json.load(fh)
    out = {}
    for prov in provisions:
        out[prov["id"]] = _shred_one_live(prov)
    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    return out
