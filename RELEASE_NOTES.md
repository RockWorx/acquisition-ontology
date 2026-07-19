# SKEDS Acquisition Ontology -- Release Notes

RockWorx Aerospace's DoD acquisition-lifecycle extension ontology, published in three
modules plus two demonstrators. License: BSD-3-Clause. Creator: RockWorx Aerospace.

- Base:      https://w3id.org/rockworx/acq           (rwx-acq-base.ttl)      -- what IS law/policy
- Transform: https://w3id.org/rockworx/acq/transform (rwx-acq-transform.ttl) -- the 2025 reform
- Horizon:   https://w3id.org/rockworx/acq/horizon   (rwx-acq-horizon.ttl)   -- what MIGHT become law

## New: the legislative-horizon layer (rwx-acq-horizon)

A third, PROSPECTIVE layer models what MIGHT become law -- pending U.S. defense-acquisition bills as
NON-asserted candidate changes -- so leadership can query "what is Congress about to change, and how
likely." The credibility linchpin is machine-proven: PROSPECTIVE != ASSERTED. Candidate changes are
Descriptive ICEs `owl:disjointWith` the base roles; the affected construct is referenced by OWL 2 punning
(no propagating semantics); maturity/likelihood/impact are annotation properties (a judgment can never be
entailed as a fact); graduation on enactment is a governed, append-only migration, not an inference.
Reasoning base + transform + horizon + the demo A-Box introduces NO new class subsumption among
base/transform classes. The demonstrator ingests real bills from the Congress.gov API (SPEED Act
H.R. 3838; FY26 NDAA PL 119-60 sec. 1802 -> the Portfolio Acquisition Executive graduating POLICY ->
STATUTE; FY27 H.R. 8800 / S. 4784). Reproduce with `python -m horizon.run_demo`; details in
`horizon/README.md`. Three cross-family conformance reviews folded (design vet, output review, Red Team).

## Headline: the ICE (Information Content Entity) -> Objective shift

The single most important thing to understand before querying this ontology is that
the post-2025 Defense Acquisition System reform (Executive Order 14265) did not just
rename a document -- it changed the KIND of thing the requirements root IS.

- **Legacy: the Initial Capabilities Document (ICD).** Under JCIDS, the ICD is a
  **Prescriptive** Information Content Entity (ICE) (CCO `ont00000965`, Prescriptive ICE --
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
  `ExecutiveOrder14265` ("Modernizing Defense Acquisitions and Spurring Innovation in the
  Defense Industrial Base"), the directing instrument.
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
  Order 14265, "Modernizing Defense Acquisitions and Spurring Innovation in the Defense
  Industrial Base" (9 April 2025; implemented later in 2025 by the Secretary of War
  memorandum transforming the DAS into the WAS) -- the transform module's reformed classes
  and their `authorityTier`/PROV-O provenance trace to this instrument.
  - *Department naming:* the statutory name is the **Department of Defense** (used by EO
    14265). Executive Order 14347, "Restoring the United States Department of War"
    (5 Sep 2025), authorizes **"Department of War" / "Secretary of War" as an additional
    SECONDARY title** for public, ceremonial, and non-statutory contexts -- the statutory
    name remains Department of Defense, so the two co-exist. This ontology quotes each
    instrument in its own language (EO 14265 = the acquisition-reform directing instrument;
    the later WAS memoranda use the secondary "Secretary of War" title).
- **BFO/CCO conformance-reviewed.** Both modules went through a RockWorxOS authored
  BFO/CCO conformance pass as part of the RockWorxDuo review protocol before this
  publish-prep: a design-level cross-check (base module) and a second pass against
  the actual serialized Turtle (transform module, output conformance: PASS, no red
  flags, 2 HIGH-severity fixes applied). These are RockWorxOS reviews of ontology
  conformance to BFO/CCO modeling conventions -- they are not a substitute for the
  machine-checked ROBOT/Widoco tooling QC run separately as part of this same
  publish-prep pass (see the publish-prep task record for verbatim tooling-QC
  results).

## Conformance notes

Both modules pass an OWL EL (ELK) consistency + satisfiability check under the imported
CCO 2.1 + BFO 2020 + IAO ontologies: **consistent, zero unsatisfiable classes.**

**Deliberate divergence from strict OBO obsolescence convention.** The four legacy
classes -- `JCIDS`, `InitialCapabilitiesDocument`, `ProgramExecutiveOffice`,
`ConfigurationSteeringBoard` -- are `owl:deprecated true` with an IAO "term replaced by"
(`obo:IAO_0100001`) link to their reformed successor, but this ontology deliberately
RETAINS their real logical axioms (their base-role `rdfs:subClassOf`; for the ICD, the
`isRequirementsInputTo` restriction to JCIDS) rather than stripping them to bare
deprecation metadata.

Strict OBO obsolescence convention says a deprecated class should carry little more than
`owl:deprecated true` and a replaced-by pointer -- ROBOT's `report` command flags a
deprecated class that still carries `rdfs:subClassOf`/restriction axioms as a
`deprecated_class_reference` ERROR (a real, expected finding here, not a bug: 6
occurrences across the four legacy classes plus the ICD's requirement-input restriction
blank node).

We keep the axioms anyway, on purpose, because this ontology's job is to model a
REFORM, and the legacy structure IS the content that makes that reform queryable.
Stripping `InitialCapabilitiesDocument` down to metadata-only would erase the one fact
that explains WHY the reform happened at the class level: the ICD was a **Prescriptive**
information content entity (CCO `ont00000965`) while its successor, the
`KeyOperationalProblem`, is an **Objective** (CCO `ont00000476`) -- see "Headline: the
ICE -> Objective shift" above. A metadata-only stub could not carry that distinction, and
a consumer doing cross-era requirements traceability (the whole point of
`isRequirementsInputTo`) would lose the ability to query "what did legacy requirements
artifacts actually feed" once the legacy class's own axioms were removed.

This is a considered deviation, not an oversight, and it is scoped narrowly to the four
legacy classes named above. Two ROBOT `report` findings follow from it, both expected:

- **6 `deprecated_class_reference` errors** -- the four classes' retained
  `rdfs:subClassOf` axioms plus the ICD's `isRequirementsInputTo` restriction blank node
  (described above).
- **4 `missing_obsolete_label` warnings** -- the four classes keep their real
  human-readable labels (e.g. "Initial Capabilities Document") rather than the strict-OBO
  `obsolete `-prefixed form. This is the same rationale: an `obsolete `-prefixed label
  signals "do not use this term," but this ontology deliberately keeps these classes
  *queryable* for cross-era requirements traceability -- they are superseded, not to be
  ignored. The `obo:IAO_0100001` "term replaced by" pointer IS present on all four (that
  check passes normally).

A strict-OBO consumer that wants the convention followed can trivially filter
`owl:deprecated true` classes out of any query -- the retained axioms and labels are
additive information, not a correctness violation of OWL/BFO semantics (the reasoning
check above confirms this: still consistent, zero unsatisfiable classes, with the axioms
in place).

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
