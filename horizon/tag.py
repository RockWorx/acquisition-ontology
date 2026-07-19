"""TAG stage -- assemble a candidate change from its provision + the polled instrument status + the
SHRED extraction. The legislative-maturity comes straight from the poll (the source's real status); the
enactment LIKELIHOOD is an explicit, sourced JUDGMENT (never a fact) paired with its basis.
"""

# Annual must-pass vehicles get a higher forward likelihood than a standalone bill.
_MUST_PASS = ("NDAA", "National Defense Authorization", "Appropriations")


def _likelihood(maturity, instrument_label, enacted_in_fy26, latest_action):
    """Return (likelihood_label, basis). A flagged judgment, grounded in the real status."""
    if maturity == "enacted":
        return "N/A", "Enacted -- no longer prospective; graduates into the asserted transform/base layer."
    must_pass = any(k in instrument_label for k in _MUST_PASS)
    if maturity == "passed-one-chamber":
        tail = (" but was not incorporated into the enacted FY2026 NDAA (PL 119-60); it may return in the "
                "FY2027 cycle" if enacted_in_fy26 is False else "; awaiting the other chamber")
        return "MEDIUM", f"Passed one chamber ({latest_action}){tail}. Judgment, not a fact."
    if maturity == "reported":
        if must_pass:
            return "MEDIUM-HIGH", ("Committee-reported and carried on a must-pass annual vehicle "
                                   f"({instrument_label}); {latest_action}. Judgment, not a fact.")
        return "MEDIUM", f"Committee-reported ({latest_action}). Judgment, not a fact."
    if maturity == "introduced":
        return "LOW-MEDIUM", f"Introduced/referred ({latest_action}); early on the ladder. Judgment, not a fact."
    return "LOW", f"Early-stage ({maturity}). Judgment, not a fact."


def tag(provision, instrument_id, instrument_rec, shred_result):
    """Assemble one candidate-change record."""
    maturity = instrument_rec["maturity"]
    graduated = maturity == "enacted"
    likelihood, basis = _likelihood(maturity, instrument_rec["label"],
                                    provision.get("enacted_in_fy26"), instrument_rec.get("latest_action", ""))
    cand = {
        "id": "cand_" + provision["id"],
        "label": f"{provision['section']} -- {instrument_rec['label'].split(' -- ')[0]}",
        "instrument_id": instrument_id,
        "instrument_label": instrument_rec["label"],
        "section": provision["section"],
        "source": provision["source"],
        "maturity": maturity,
        "wouldAffect": shred_result["wouldAffect"],
        "changeType": shred_result["changeType"],
        "impactAssessment": shred_result["impactAssessment"],
        "enactmentLikelihood": likelihood,
        "likelihoodBasis": basis,
        "graduated": graduated,
    }
    if graduated:
        # The enacted construct carries rwxt:authorityTier "STATUTE" via the graduation migration
        # (graduation_proposed.ttl), NOT the deprecated candidate itself. wouldAffect is a list; the
        # primary (first) construct is the one codified.
        cand["graduatedTo"] = shred_result["wouldAffect"][0]
    else:
        # A horizon-layer annotation about the PROPOSAL -- distinct from the transform's asserted tier.
        cand["prospectiveAuthorityTier"] = "STATUTE-PENDING"
    return cand
