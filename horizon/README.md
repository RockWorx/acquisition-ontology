# Legislative-Horizon Layer -- `rwx-acq-horizon` (reproducible reference)

**What this is.** The THIRD acquisition-ontology layer, above **base** (what IS law) and **transform**
(the 2025 WAS/JFRP reform): a model of what MIGHT become law -- pending U.S. defense-acquisition bills,
carried as **non-asserted candidate changes** -- so leadership can query *"what is Congress about to
change to the acquisition system, and how likely?"* Nothing else publicly models the legislative horizon
on a DoD acquisition ontology.

**The credibility linchpin: prospective != asserted.** OWL 2 is monotonic and has no modality, so the
whole thing collapses if a reasoner concludes a *proposed* change is *real*. The mechanism keeps
prospective strictly out of the asserted model, and the separation is **machine-proven, not asserted**:

- Every triple's SUBJECT is an information entity that really exists today (a bill; a candidate-change
  description) and states what the proposal SAYS or WOULD do -- a true fact ABOUT THE PROPOSAL. "H.R. 3838
  proposes to raise the MDAP threshold" is true today; "the MDAP threshold is raised" is never asserted.
- `rwxh:LegislativeCandidateChange` is a Descriptive ICE (`cco:ont00000853`), `owl:disjointWith` the
  base/transform role classes; `rwxh:wouldAffect` references the affected construct's class IRI by OWL 2
  **punning** (a plain object property, no range axiom, not a subproperty of any base relation -- so a
  reasoner infers nothing about the referenced construct).
- Maturity, likelihood, change-type, and impact are **annotation properties** -- outside the OWL-DL
  logical model, so a likelihood/impact JUDGMENT can never be entailed as a fact. Every likelihood is a
  flagged judgment paired with a sourced basis.
- **Graduation on enactment is a governed act, not an inference:** when a candidate reaches
  maturity=enacted, an append-only migration adds the now-real construct's STATUTE provenance while
  KEEPING its prior POLICY link (a dated authority history). No reasoner auto-promotes anything.

The machine-checkable invariant: reasoning **base + transform + horizon + A-Box** yields NO new class
subsumption among base/transform classes vs base+transform alone. See `qc/check_horizon.py`.

## The pipeline

```
POLL  (each bill's REAL status from the Congress.gov API -> the legislative-maturity ladder:
       proposed -> introduced -> reported -> passed-one-chamber -> in-conference -> enacted)
  -> SHRED  (an LLM extracts, from real provision text, the acquisition constructs a provision would
             affect (a LIST -- a provision may change several), the change type, and a one-line impact,
             GROUNDED in the text, never invented; the LLM is pluggable -- see shred.set_extractor)
  -> TAG    (maturity from the source; the enactment likelihood is an explicit, sourced JUDGMENT)
  -> LOAD   (non-asserted individuals into the horizon layer; a graduation proposal for enacted candidates)
```

Full-text ingestion (`bill_text.py`) fetches a bill's actual text and extracts its acquisition-title
sections (dynamic section boundaries); discovery (`discover.py`) auto-finds acquisition-relevant bills via
a watchlist plus title-keyword-filtered enumeration of recent enacted public laws (the Congress.gov API
cannot free-text search), with change-detection for a scheduled poll.

## The demonstrator (all real bills, as of 2026-07-19)

- **SPEED Act (H.R. 3838)** -- passed the House, dropped from the enacted FY26 NDAA -> live on the horizon
  (sec. 303 thresholds -> AcquisitionGate + FundingSource; sec. 402 prototype-OTA -> FundingSource).
- **FY26 NDAA (Public Law 119-60) sec. 1802** codified the Portfolio Acquisition Executive -> the
  **graduation** demo: the PAE moves POLICY (EO 14265) -> STATUTE (PL 119-60), keeping both dated links.
- **FY27** -- H.R. 8800 + S. 4784 (committee-reported) and the House FY27 Defense Appropriations Act;
  H.R. 8800 Title VIII (Acquisition Policy) is ingested from the real bill text (SEC. 801, PAE authorities).

The query *"what is on the legislative horizon for Milestone B / the MCA spine, and how likely?"* returns
the live prospective candidates ranked by maturity + a sourced likelihood.

## Reproduce it

```
python -m horizon.run_demo          # offline + reproducible (rdflib; no LLM, no network) from cached real data
python -m horizon.run_demo --live   # re-poll Congress.gov (DATAGOV_API_KEY) + re-shred (your own LLM)
python horizon/qc/check_horizon.py  # ELK-consistency + the prospective!=asserted invariant (offline; ROBOT + qc/)
```

The offline run needs only `rdflib`; the committed `demo/shred_cache.json` holds the extractions, so no LLM
is required to reproduce. To run `--live`, register your own model with `horizon.shred.set_extractor(fn)`.

## Provenance + honest scope

- **Grounded, never invented.** Every candidate traces to a real bill number, its real Congress.gov
  status, and a cited provision text; the likelihood is an explicit judgment with a sourced basis.
- **Reviewed three ways** (RockWorxOS / RockWorxDuo): a design-level vet of the modal mechanism (ADOPT),
  an output-level conformance review, and an adversarial Red Team pass -- all folded. These are conformance
  *reviews*, distinct from the machine-checked reasoning QC.
- **Warranted scope.** A buildable, standards-based, DoD-directed-semantics layer demonstrated on a handful
  of real bills; the demo shreds the first 3 of H.R. 8800's 46 acquisition sections (a full run shreds all).
  Not a finished platform.

## Why it matters

Acquisition policy is a moving target -- policy gets codified into statute, statute overrides policy, and
the two conflict. Base + transform capture what IS; the horizon layer captures what is ABOUT to change, as
a live, sourced, non-asserted radar -- so a program's acquisition context can be read against not just
today's rules but the rules Congress is poised to change. Data via the Congress.gov API. Not an official
U.S. Government product.
