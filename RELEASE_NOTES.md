# SKEDS Acquisition Ontology -- Release Notes

RockWorx Aerospace's DoD acquisition-lifecycle extension ontology, published in two
modules. License: BSD-3-Clause. Creator: RockWorx Aerospace.

- Base:      https://w3id.org/rockworx/acq          (rwx-acq-base.ttl)
- Transform: https://w3id.org/rockworx/acq/transform (rwx-acq-transform.ttl)

## Headline: the ICE -> Objective shift

The single most important thing to understand before querying this ontology is that
the post-2025 Defense Acquisition System reform (Executive Order 14265) did not just
rename a document -- it changed the KIND of thing the requirements root IS.

- **Legacy: the Initial Capabilities Document (ICD/ICE).** Under JCIDS, the ICD is a
  **Prescriptive** information content entity (CCO `ont00000965`, Prescriptive ICE --
  in CCO 2.1 this class was renamed from "Directive ICE"). A prescriptive artifact
  states, or heavily implies, a preferred materiel solution: it identifies a
  capability gap AND a preferred materiel approach.
- **Reformed: the Key Operational Problem (KOP).** Under the Joint Force Requirements
  Process (JFRP), the requirements root is an **Objective** (CCO `ont00000476`): a
  prioritized joint-force operational problem, ranked by the re-oriented Joint
  Requirements Oversight Council (JROC). An objective states the PROBLEM and
  deliberately withholds the solution.

`InitialCapabilitiesDocument` is marked `owl:deprecated true` and carries an IAO
"term replaced by" (`obo:IAO_0100001`) edge to `KeyOperationalProblem` in the
transform module -- but **term-replaced-by is not sameness of kind.** Prescriptive
(solution-stating) and Objective (problem-stating) are different OWL/BFO classes with
different parents; an ICD-shaped answer is not the same shape as a KOP-shaped answer.

**Practical consequence: do not query legacy requirements input by class alone.** A
query that asks only "give me every `InitialCapabilitiesDocument`" (or only every
`KeyOperationalProblem`) silently returns just one side of the reform and will
under-count anyone auditing requirements traceability across the transition. See
"Querying across the reform" below for the pattern that avoids this trap.

## The two modules

### Base: `https://w3id.org/rockworx/acq`

The durable, era-neutral layer. Grounds the DoDI 5000.85 (6 Aug 2020, Chg 1
4 Nov 2021) Major Capability Acquisition (MCA) lifecycle to CCO/BFO: the five MCA
phases (MSA/TMRR/EMD/P&D/O&S), the milestone gates (MDD, MS A/B/C) and technical
reviews (PDR/CDR/etc.), funding sources, program-oversight organizations, and program
risk/risk-assessment. It defines two BASE ROLES that stay stable across acquisition
policy eras precisely so the transform module can subtype them without base-layer
churn:

- `RequirementDeterminationProcess` -- the planned process by which capability
  requirements are determined (played by JCIDS pre-reform, by the JFRP post-reform).
- `ProgramOversightOrganization` -- the organization holding acquisition oversight
  authority (played by a Program Executive Office pre-reform, by a Portfolio
  Acquisition Executive post-reform).

It also defines the bridging object property used to query across eras:
`isRequirementsInputTo` (domain: an information content entity; range: a
`RequirementDeterminationProcess`).

### Transform: `https://w3id.org/rockworx/acq/transform`

The WAS/JFRP reform overlay. `owl:imports` the base module and fills its two base
roles with concrete legacy and reformed classes:

- **Reformed fillers:** Joint Force Requirements Process, Portfolio Acquisition
  Executive, Joint Acceleration Reserve (the CAPE-maintained valley-of-death funding
  reserve), Capability Trade Council, Portfolio Scorecard, Key Operational Problem.
- **Legacy fillers:** JCIDS, Initial Capabilities Document, Program Executive Office,
  Configuration Steering Board -- each `owl:deprecated true` with an
  `obo:IAO_0100001` ("term replaced by") edge to its reformed successor.

Provenance and authority are captured explicitly rather than left implicit:

- **A reform `bfo:process` individual**, `DASReform2025`, with an explicit causal
  chain (`cco:has_input` the directing instrument, `bfo:has_participant` the PEOs
  being reorganized, `cco:has_output` the resulting PAEs) -- the reform is modeled as
  something that HAPPENED, not just asserted as a fact.
- **PROV-O** (`prov:wasDerivedFrom`): every reformed class is derived from
  `ExecutiveOrder14265` (Nov 2025), the directing instrument.
- **`authorityTier`**: every reformed class carries an annotation of
  `"POLICY"` -- this ontology's STATUTE > POLICY > GUIDANCE authority scale, so a
  consumer can tell at a glance that a construct rests on EO/policy authority, not
  statute.

## Querying across the reform

Use `isRequirementsInputTo`, not the legacy/reformed class names directly, to ask
"what feeds a requirement-determination process" without having to already know
which era's vocabulary applies. See `bridge-queries.rq` in this directory for two
runnable SPARQL patterns:

1. A restriction-based query that returns every requirement-input class (legacy AND
   reformed) uniformly, by asking the ontology which classes are asserted to feed
   SOME requirement-determination process -- rather than asking "does the caller
   already know both class names."
2. A UNION query retrieving requirement artifacts across both the legacy Prescriptive
   ICE class (`cco:ont00000965`) and the reformed Objective/KOP class
   (`cco:ont00000476`) in one result set, tagged with which era each result came
   from -- this is the pattern that avoids the "class-only query silently returns
   just one side of the reform" trap called out above.

## License

BSD-3-Clause. See `LICENSE` in this directory. Copyright (c) 2026 RockWorx
Aerospace.

## Creator

RockWorx Aerospace.

## Provenance

- **Grounded to CCO 2.1** (Common Core Ontologies) + BFO 2020, via `owl:imports` in
  both modules' headers.
- **Grounded to DoDI 5000.85**, "Major Capability Acquisition" (6 Aug 2020, Chg 1
  4 Nov 2021), Section 3 -- the base module's MCA spine (phases, milestone gates,
  technical reviews) is transcribed from this instruction, not invented.
- **Grounded to the 2025 Defense Acquisition System reform**, directed by Executive
  Order 14265 (Nov 2025) -- the transform module's reformed classes and their
  `authorityTier`/PROV-O provenance trace to this instrument.
- **BFO/CCO conformance-reviewed.** Both modules went through a RockWorxOS authored
  BFO/CCO conformance pass as part of the RockWorxDuo review protocol before this
  publish-prep: a design-level cross-check (base module) and a second pass against
  the actual serialized Turtle (transform module, output conformance: PASS, no red
  flags, 2 HIGH-severity fixes applied). These are RockWorxOS reviews of ontology
  conformance to BFO/CCO modeling conventions -- they are not a substitute for the
  machine-checked ROBOT/Widoco tooling QC run separately as part of this same
  publish-prep pass (see the publish-prep task record for verbatim tooling-QC
  results).

## Resolving these IRIs

The base and transform ontology IRIs (`https://w3id.org/rockworx/acq` and
`https://w3id.org/rockworx/acq/transform`) are **persistent identifiers under the
w3id.org permanent-identifier service.** The redirect from `w3id.org/rockworx/*` to
this ontology's actual hosting location is registered via a pull request to the
`perma-id/w3id.org` GitHub repository, submitted at publication time.

**Until that PR is merged, these IRIs are valid, stable identifiers that do not yet
resolve over HTTP.** Use them as-is for class/property identity and for `owl:imports`
-- do not substitute a placeholder or a different host, and do not treat a failed
HTTP GET against them (before the redirect is registered) as evidence the IRIs are
wrong.
