"""horizon -- the SKEDS legislative-horizon pipeline.

The THIRD acquisition-ontology layer: models what MIGHT become law (pending bills) as NON-asserted
candidate changes, so leadership can query "what is Congress about to change, and how likely."

Pipeline: POLL (Congress.gov real status) -> SHRED (LLM-extract provisions, grounded in real text)
-> TAG (legislative-maturity from the source; likelihood + impact as flagged judgments) -> LOAD
(emit non-asserted individuals into the rwx-acq-horizon layer).

EPISTEMIC DISCIPLINE (cross-family vetted, verdict ADOPT): prospective != asserted. The horizon
layer is strictly separated from the asserted base/transform; a "maybe" is never reasoned as a fact.
"""
from .poll import poll, derive_maturity
from .shred import shred
from .tag import tag
from .load import load_candidates, HORIZON_NS

__all__ = ["poll", "derive_maturity", "shred", "tag", "load_candidates", "HORIZON_NS"]
