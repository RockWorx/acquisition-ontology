# RockWorx Acquisition Ontology + SysML v2 Link

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21445548.svg)](https://doi.org/10.5281/zenodo.21445548)

A BFO/CCO-conformant ontology of the U.S. DoD acquisition lifecycle -- **plus** a legislative-horizon
layer that models what Congress is about to change, **and** a working, standards-based link that
resolves SysML v2 system models into it. Published as three ontology modules plus two reproducible
demonstrators. License: BSD-3-Clause. Creator: RockWorx Aerospace.

- **Base:** `https://w3id.org/rockworx/acq` (`rwx-acq-base.ttl`) -- what IS law/policy.
- **Transform:** `https://w3id.org/rockworx/acq/transform` (`rwx-acq-transform.ttl`) -- the 2025 reform.
- **Legislative horizon:** `https://w3id.org/rockworx/acq/horizon` (`rwx-acq-horizon.ttl`) -- what MIGHT
  become law: pending bills as non-asserted candidate changes. Demonstrator + pipeline in `horizon/`.
- **SysML v2 link + demonstrator:** `sysml_link/`

## Why this exists

The Department of Defense has directed **BFO + CCO** as its baseline for formal ontology and
is moving to **SysML v2** for digital engineering -- yet no public ontology models the DoD
**acquisition lifecycle** on that base, and nothing links a SysML v2 system model to
acquisition-process semantics. This fills both gaps:

- **The ontology** -- what the acquisition process *is*: the DoDI 5000.85 Major Capability
  Acquisition lifecycle (phases, milestone gates, technical reviews, program risk, funding,
  oversight) plus the 2025 Warfighting Acquisition System / Joint Force Requirements Process
  reform, grounded to CCO 2.1 + BFO 2020.
- **The link** -- so a program's *actual* SysML v2 model becomes queryable against phases,
  gates, reviews, KPPs, program risk, and Title 10 authority.

## The ontology headline: the ICE -> Objective shift

The most important thing to understand before querying is that the post-2025 reform did not
just rename a document -- it changed the KIND of thing the requirements root **is**. Under
JCIDS the Initial Capabilities Document is a **Prescriptive** Information Content Entity (CCO
`ont00000965`) -- it implies a materiel solution. Under the Joint Force Requirements Process
the root is an **Objective** (CCO `ont00000476`) -- the Key Operational Problem, which states
the problem and withholds the solution. These are different OWL/BFO classes; the transform
module marks the legacy term `owl:deprecated` with an IAO "term replaced by" pointer, but
**term-replaced-by is not sameness of kind.** Query across the reform with the role-stable
`isRequirementsInputTo` property, not by class name (see `RELEASE_NOTES.md` and
`bridge-queries.rq`). Full module detail, conformance notes, and provenance:
[`RELEASE_NOTES.md`](RELEASE_NOTES.md).

## SysML v2 integration (`sysml_link/`)

SysML v2 gives a standard, ISO-track, vendor-neutral system model behind a standard API --
but a model is only meaning-bearing if its elements resolve to shared, *directed* semantics.
This link supplies exactly that, using SysML v2's **native** constructs:

- The RockWorx acquisition classes are emitted as a native SysML v2 **tag library**
  (`owl:Class -> metadata def`, `owl:ObjectProperty -> connection def`).
- A model tags its elements with those classes and uses first-class SysML v2 constructs -- a
  **`requirement`** (the KPP), **`satisfy`** (design satisfies requirement), and a
  **`verification`** case that **`verify`s** the requirement with a **`VerdictKind`** result.
- A transform reads the model's AST and resolves each tagged element and native relation into
  the acquisition ontology as RDF. Acquisition-process relations that SysML v2 has **no**
  native construct for (a requirement *assessed at* a review, a review that *informs* a gate,
  a KPP that *traces to* Title 10 authority) are carried by a small bridge overlay. That
  division -- native SysML v2 for the system model, the bridge for the acquisition process --
  is the point.

**The demonstrator ("Risk-Driven Milestone Validation").** A tiny SysML v2 model whose KPP
verification records a **FAIL**. From that failure a program risk is **derived** (not
hand-asserted), and a SHACL rule *enforces* the acquisition decision: a single SPARQL query
answers *"what is preventing a successful Milestone B decision?"* end-to-end
(KPP -> review -> gate + failed verification -> derived risk + Title 10 authority), and the
Milestone B gate is **blocked** while the risk is open -- and **passes** once the design is
fixed (result -> PASS) or the risk is formally accepted. Reproduce it Python-only (rdflib +
pySHACL) from the committed artifacts; see `sysml_link/` and its reference write-up.

**Warranted scope.** This is a *buildable, standards-based, DoD-directed* link demonstrated on
one small model -- not a finished platform. It rides the standard SysML v2 API (any conformant
tool, no lock-in), uses native v2 metadata (no brittle vendor mapping), and lands on the
DoD-directed BFO/CCO base.

## Legislative-horizon layer (`horizon/`)

Base + transform assert what IS law/policy. The horizon module (`rwx-acq-horizon`) adds a THIRD,
prospective layer: what MIGHT become law. Pending U.S. defense-acquisition bills are modeled as
**non-asserted candidate changes**, so a program's acquisition context can be read against not just
today's rules but the rules Congress is poised to change.

- **The credibility linchpin -- prospective != asserted, machine-proven.** OWL is monotonic and has no
  modality, so the layer keeps prospective strictly out of the asserted model: candidate changes are
  Descriptive ICEs `owl:disjointWith` the base roles; the affected construct is referenced by OWL 2
  punning (no propagating semantics); maturity/likelihood/impact are annotation properties (a judgment
  can never be entailed as a fact); graduation on enactment is a governed append-only migration, not an
  inference. Reasoning base + transform + horizon + the demo A-Box yields **no new class subsumption**
  among base/transform classes (verified in `horizon/qc/`).
- **The demonstrator** ingests real bills from the Congress.gov API (POLL real status -> SHRED provisions
  with an LLM, grounded in the text -> TAG maturity + a sourced likelihood judgment -> LOAD non-asserted).
  It answers *"what is on the legislative horizon for Milestone B / the MCA spine, and how likely?"* and
  shows the FY26 NDAA (PL 119-60) codification of the Portfolio Acquisition Executive **graduating** from
  policy (EO 14265) to statute. Reproduce Python-only: `python -m horizon.run_demo`. See `horizon/README.md`.

## Provenance

- **Grounded** to CCO 2.1 + BFO 2020 (via `owl:imports`), to DoDI 5000.85 for the MCA spine,
  and to the 2025 reform's directing instrument, **Executive Order 14265, "Modernizing Defense
  Acquisitions and Spurring Innovation in the Defense Industrial Base"** (9 April 2025).
- **Conformance-reviewed.** Both modules and the SysML v2 link went through RockWorxOS-authored
  BFO/CCO conformance passes under the RockWorxDuo review protocol -- design-level and
  output-level cross-checks, plus an adversarial red-team pass at a public-release bar. These
  are conformance *reviews*, distinct from the machine-checked tooling QC below.
- **Machine-checked.** Both modules reason **ELK-consistent, zero unsatisfiable classes**, and
  the demonstrator's instance graph reasons consistent against the full BFO/CCO + module stack
  (`qc/`, fully offline-reproducible). ROBOT reports clean apart from a deliberate, documented
  divergence around the retained deprecated-class axioms (see `RELEASE_NOTES.md`).

*Note on department naming:* the statutory name is the **Department of Defense** (used by EO
14265). Executive Order 14347 (5 Sep 2025) authorizes "Department of War" / "Secretary of War"
as an additional **secondary** title for public and non-statutory contexts; the two co-exist.
This ontology quotes each instrument in its own language.

## License

BSD-3-Clause. See [`LICENSE`](LICENSE). Copyright (c) 2026 RockWorx Aerospace.

## Resolving the IRIs

`https://w3id.org/rockworx/acq*` are persistent identifiers under the w3id.org service; the
redirect is registered by a pull request to `perma-id/w3id.org` at publication time. Until it
merges the IRIs are valid, stable identifiers that do not yet resolve over HTTP -- use them
as-is for class/property identity and `owl:imports`.
