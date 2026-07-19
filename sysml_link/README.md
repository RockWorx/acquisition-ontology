# SysML v2 <-> Acquisition-Ontology Link -- Demonstrator (reproducible reference)

**What this is.** A working, standards-based link from an OMG SysML v2 system model to the
RockWorx BFO/CCO **DoD acquisition-lifecycle ontology** (base + WAS/JFRP transform modules).
It shows a program's actual SysML v2 model becoming *queryable and rule-checkable* against
acquisition phases, gates, reviews, KPPs, program risk, and Title 10 authority -- the
acquisition-process semantics SysML v2 deliberately does not carry. Design of record +
review provenance: `agent_governance/SKEDS_SYSML_LINK_DESIGN.md`.

**Warranted claim (and only that).** This is a *buildable, standards-based, DoD-directed-
semantics* link demonstrated on ONE small model, with the risk logic expressed as a single
derivation rule. ~70-80% of the plumbing is pre-published (OMG ships the metamodel JSON-LD
contexts; a BSD-3 tool established the tagging pattern). It is not a finished platform.

## Approach: Mode B (instance tagging), not metamodel alignment

We tag SPECIFIC SysML v2 model elements with acquisition classes (native `@metadata`, no
UML profile), then resolve those instances into the ontology. We deliberately do NOT assert
SysML-metaclass -> BFO subclass axioms (an M-level category error, and the first thing a
hostile ontologist would attack). A thin bridge (`rwx/skeds/sysml_link/bridge.ttl`) adds the
few object/datatype properties the link needs and REUSES existing properties where they
already fit (`rwxacq:informs`, `prov:wasDerivedFrom`) rather than minting duplicates.

## The pipeline

```
acquisition ontology (base + bridge, local .ttl)
      | taglib.generate_tag_library  (owl:Class -> metadata def, owl:ObjectProperty -> connection def)
      v
SysML v2 tag library (RWXAcqTags.sysml)  --imported by-->  RiskDrivenMilestone.sysml
      |                                                            |
      |  OMG SysML v2 pilot 0.60.1 (headless ASTGenerator; see TOOLCHAIN.md)
      v                                                            v
                                  model AST (JSON)
      | transform.transform  (tags -> rdf:type; connections -> object properties;
      |                        mapped attributes -> datatype literals; multi-namespace IRIs)
      v
RiskDrivenMilestone.model.ttl   (structure + verificationResult="FAIL"; NO hand-asserted risk)
      | derive_risk.rq  (a FAILED KPP verification DERIVES an Open/HIGH ProgramRisk)
      v
federated graph  ->  whats_blocking_msb.rq (SPARQL)  +  msb_gate.shape.ttl (pySHACL)
```

## What it proves (the demonstrator)

Query *"what is preventing a successful Milestone B decision?"* returns the digital thread:
the gate, the blocked KPP, the failed verification, the (derived) program risk, and the KPP's
Title 10 authority. The SHACL gate rule then ENFORCES the decision -- and responds to program
state:

| State | Result |
|---|---|
| as-built (verification FAIL -> Open/HIGH risk derived) | Milestone B **BLOCKED** |
| fix the design (result -> PASS; no risk derived) | Milestone B **PASSES** |
| accept the risk (status -> Closed; failed test + risk retained) | Milestone B **PASSES** |

The risk is **derived from the recorded FAIL**, not hand-asserted -- it exists *because* the
result is FAIL. Both mitigations preserve the audit trail (neither deletes data).

## Reproduce it

- **Python-only (no Java):** the extracted `model.ttl` + rules + shapes are committed, so:
  `wsl ... ~/.venvs/f16union/bin/python -m rwx.skeds.sysml_link.run_demo`
  (rdflib + pySHACL; prints the query result and the three gate states). Tests:
  `pytest tests/skeds/test_sysml_taglib.py test_sysml_bridge.py test_sysml_transform.py test_sysml_payoff.py`.
- **From SysML source (needs the toolchain):** regenerate the AST per `TOOLCHAIN.md`
  (Temurin 21 + pilot 0.60.1 fat jar, headless), then `transform.transform(...)`.
- **Vendored OMG @context** (for the optional JSON-LD/`gen_jsonld` standards export) are
  fetchable per `rwx/skeds/sysml_link/vendor/VENDOR.md`; the canonical transform does not
  need them.

## Reuse credited

The tag-library + AST->RDF PATTERN follows `max-thoma/semantic-tag-utility` (BSD-3, IEEE
INDIN 2024). We reimplemented it in-repo to fix two public-artifact defects (it stamps the
local file path as the namespace; it double-prefixes names) and, decisively, to resolve tags
across THREE namespaces (base / bridge / PROV) -- its single-namespace REPLACE cannot.

## Idiomatic SysML v2 (native constructs)

The demonstrator uses SysML v2's **first-class** constructs where they exist -- so it reads
as real SysML v2, not a generic graph with matching node names:

- the KPP is a native **`requirement`** (a `RequirementUsage`), not a part;
- the design **`satisfy kpp_Thrust by airVehicle`** (a `SatisfyRequirementUsage`) -- the
  transform reads `satisfyingFeature` -> `satisfiedRequirement`;
- a native **`verification`** case `verify`s the KPP (`verifiedRequirement`), and its
  **`VerdictKind`** result (`fail`) is read straight from the model as the
  `verificationResult` -- no separate result attribute.

The RockWorx bridge `connection`s carry only the relations SysML v2 has **no** native
construct for -- the acquisition-process links `assessedAt`, `informs`, `tracesToAuthority`
(PROV `wasDerivedFrom`). That division -- native SysML for the system model, the bridge for
the acquisition process -- is exactly the point of the link. The native constructs map to the
**same** RDF predicates, so the query/SHACL/derivation are unchanged.

## Honest limitations (deferred, tracked)
- **Peripheral typing.** The authority reference is now explicitly typed
  (`rwxacq:AuthorityReference`); the design element and the verification are typed by
  inference from the bridge property domains (material-entity / process), materialized and
  confirmed by the combined ELK pass. (The verification's idiomatic `VerificationCase`
  typing is part of the native-constructs item above.)

**Consistency + reproducibility.** Risk severity/status ride a `RiskAssessment` (a Descriptive
ICE linked by `assessesRisk`), not the disposition. The string link-properties are enforced by
a controlled-vocabulary SHACL shape. The demo A-Box reasons **ELK-consistent against the full
T-Box** (base + transform + bridge + BFO/CCO/IAO) -- run `publish/qc/check-combined.sh`; all
reasoning is offline-reproducible via `publish/qc/import-catalog.xml`.

## Why it matters (for a SysML-v2 audience)

SysML v2 gives a standard, ISO-track, vendor-neutral system model behind a standard API --
but a model is only meaning-bearing if its elements resolve to shared, *directed* semantics.
This supplies the semantics DoD has already directed (BFO + CCO) AND the acquisition-process
ontology no one else has, so a program's real SysML v2 design becomes queryable against
phases, gates, reviews, KPPs, and statute. It rides the standard API (any conformant tool),
uses native v2 metadata (no brittle vendor mapping), and lands on the DoD-blessed ontology
base (defensible in review). See also the strategic framing against the Acquisition
Transformation Strategy pillars in the design of record.
