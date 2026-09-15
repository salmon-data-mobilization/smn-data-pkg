# ADR 0002: SOSA Procedure reachability for method and code IRIs

- Status: accepted
- Date: 2026-09-14
- Applies to: sdp-0.3.0 rules `methods_are_sosa_procedures` and
  `row_varying_procedures_use_codes`
- Supersedes: ADR 0001's sentence *"Every allowed code enumerated for that
  attribute resolves to a registered method"*, on this point only. Its registry
  half was already dropped by sdp-0.3.0, which removed `metadata/methods.csv`.
  ADR 0001 is not edited — a dated record is superseded, not corrected.

**The normative statement of both rules is `schema/sdp.rules.yaml`, and this
document does not restate it.** This is the reasoning behind that statement,
which the rules file points here for rather than carrying inline.

## Context

Both rules said a method IRI *"resolves to a shared vocabulary concept typed as
a SOSA Procedure"*. That sentence had two problems, and no test could catch
either, because neither rule has ever been executed by any implementation (hub
backlog #48).

**It never said which of two readings it meant** — direct typing, or
reachability through a concept hierarchy — so the wording and the shipped
modelling drifted apart with nothing to catch it. Measured against the released
vocabularies:

- Released **gcdfo 0.0.9** carries exactly one `rdf:type sosa:Procedure`
  assertion in the whole graph, and its subject is **`smn:EnumerationMethod`** —
  a Salmon Domain Ontology term whose typing gcdfo restates, not a gcdfo term.
  Every one of the ten gcdfo concepts in `gcdfo:EnumerationMethodScheme`
  (`gcdfo:VisualGroundCount`, `gcdfo:FixedSiteCensusManual`,
  `gcdfo:AerialSurveyCount`, `gcdfo:HydroacousticSonarCount`,
  `gcdfo:TrapCount`, `gcdfo:ReddCount`, `gcdfo:ElectrofishingCount`,
  `gcdfo:MarkRecaptureFieldProgram`, `gcdfo:VisualSnorkelCount`,
  `gcdfo:FixedSiteCensusElectronic`) is an untyped `skos:Concept` that reaches
  it by a single `skos:broader` step. **So the qualifying path crosses a
  vocabulary boundary**, from gcdfo into smn — see Consequences.
- **smn** does the same. It types exactly six concepts
  `skos:Concept, sosa:Procedure` in
  `ontology/modules/07-controlled-vocabularies.ttl` and expresses the narrower
  constraint as a `skos:broader` path in `ontology/shapes/method-shapes.ttl`,
  with an in-file comment saying why: `owl:someValuesFrom` cannot range over
  concept individuals, so the OWL restriction can only target the generic
  `sosa:Procedure` class and the specific constraint moved to SHACL.

So the direct-typing reading makes every **gcdfo** method target non-conformant —
smn's six directly typed concepts would still pass — while the reachability
reading is the shape both vocabularies already have.

**And "resolves to" read as a per-IRI HTTP dereference.** Neither smn nor gcdfo
is served for one, so the phrase described an operation no validator can
perform.

## Decision

Brett ruled reachability, as a validator condition, on 2026-09-14 (metasalmon
`knowledge/questions.md`, Q47: *"May a SKOS method concept have `skos:broader`
to an OWL class?"*). The ruling has two halves and both are in the rules:
**yes** to the reading the question intended, **no** to the literal shape it
asked about.

### Why reachability, at zero or more steps

Reachability **subsumes** direct typing rather than overruling it: the
zero-length path is a pass, so the stricter reading survives inside the looser
one. That is why it is the correct reading and not merely the lenient one.

It is also the shape smn's own `ontology/shapes/method-shapes.ttl` already uses
(`sh:zeroOrMorePath skos:broader`), so the specification and the shipped shape
now agree by construction instead of by coincidence.

### Why an asserted edge to an OWL class is refused, and refused by name

The shortcut is to write `<method> skos:broader sosa:Procedure` and declare the
rule satisfied. It does not work, and pointing the edge the other way does not
help either.

`skos:broader`, `skos:broadMatch` and the rest are sub-properties of
`skos:semanticRelation`, which SKOS gives both `rdfs:domain skos:Concept` and
`rdfs:range skos:Concept` (integrity conditions **S19–S22**; **S41** makes
`skos:broadMatch` a sub-property of `skos:broader`, so it is caught by the same
argument). A domain and a range are **entailments, not checks**. So that triple
does not assert that the method is a Procedure. It asserts that
`sosa:Procedure` — which SOSA declares `a rdfs:Class , owl:Class` — is also a
SKOS concept, that is, an individual. That is OWL punning: W3C's class is
re-typed as a thing, and in exchange nothing whatsoever is learned about the
method. The entailment runs in the unhelpful direction, and only in the
unhelpful direction.

Measured rather than argued: under OWL 2 RL closure the punned graph yields
`sosa:Procedure rdf:type skos:Concept` **true** and
`<method> rdf:type sosa:Procedure` **false**. It costs a metamodelling
commitment and buys no entailment.

It is refused **by name** rather than left unpermitted because it is the shape
someone reaches for on the way to satisfying this rule, and it looks like it
would work. An absence of permission is not a refusal, and a reader who has to
infer a prohibition from silence will infer the other thing.

### Why this is a check and not an entailment

Nothing in the vocabularies supplies either half, so both have to be read from
them:

- `sosa:usedProcedure` declares only `schema:rangeIncludes sosa:Procedure` — a
  Schema.org annotation property with informal semantics and no inferential
  force, chosen that way deliberately (the SSN specification's §3 lists it among
  the notable differences from SSN). No reasoner will infer that a bound term is
  a Procedure.
- `skos:broader` carries no subclass entailment, so it does not supply the
  reachability either.

### Why estimate-type and data-quality vocabularies are named

gcdfo's Hyatt (1997) estimate types (`gcdfo:Type1`–`gcdfo:Type6`, under
`gcdfo:EstimateType`) are ordinal quality ratings for escapement estimates, and
Brett ruled on 2026-08-17 that that scheme is specifically only for escapement
measurements and must not be the mapping target for general data-quality codes.
An ordinal information- or index-quality rating, or a reliability flag, says the
same kind of thing: how good a value is, not how it was produced.

Such terms sit in the same tables and next to the same method columns, so they
are the ones most likely to be offered to these two rules by mistake — hardest
of all on `codes.csv` `term_iri`, which is where a classification is most easily
mistaken for a method. The rules therefore say that such a term satisfies
neither rule **at any path length**, which closes the loophole that it might
qualify through some ancestor, and that its column is an ordinary categorical
attribute rather than one bound with `sosa:usedProcedure`. Naming them costs two
sentences in the rules; catching it per package in review costs more.

## The `unresolved` outcome is a skip, and this is what retires it

A check of either rule reports one of three outcomes per IRI — **absent**,
**unreachable**, **unresolved** — each with its own message, and never passes
silently. `unresolved` is skipped rather than passed. A skip owes a retirement
condition, so here is its:

> The `unresolved` outcome exists only because a validator may hold no copy of
> the vocabulary that declares a namespace. **It becomes unnecessary once
> pinned `smn` and `gcdfo` snapshots ship in metasalmon's `inst/extdata` and in
> the metasalmonpy equivalent**, because every namespace will then either
> resolve against the pinned snapshot or be genuinely outside this
> specification's knowledge, and the check can report `absent` or `unreachable`
> in every case. At that point the outcome is removed rather than left as a
> disabled path.

Until then, a run whose IRIs were all `unresolved` has checked nothing. That is
why `unresolved` does not count as an executing check for the rule id — so it
does not satisfy hub backlog #48's test that every rule id has an executing
check — and why a strict mode that requires IRIs (`require_iris = TRUE`) reports
it as an error instead of skipping it.

## Consequences

- The gcdfo survey-method targets that direct typing would have rejected are
  conformant under the ruled reading. **This does not make every emitted target
  conformant**, and the difference is not covered by this decision: gcdfo's
  *estimate* branch terminates in an untyped `gcdfo:EstimateMethod`, so targets
  under it reach no typed ancestor and fail under **either** reading. That is a
  gap in the vocabulary rather than in the wording, and it is why hub backlog
  #48 is gated — wiring the check up without fixing it would turn a bundled
  example red on day one.
- **The qualifying path can cross a vocabulary boundary, and in practice it
  always does.** Every gcdfo survey-method concept qualifies through
  `smn:EnumerationMethod`, an smn term. A check therefore cannot decide either
  rule by reading only the vocabulary that declares the IRI; it has to follow
  `skos:broader` into whatever vocabulary the next hop lands in, and treat a hop
  it cannot resolve as `unresolved` rather than `unreachable`. Nothing in the
  rule restricts the path to one vocabulary — this records that the distinction
  is load-bearing rather than hypothetical.
- A validator author implementing hub backlog #48 reads the condition from
  `schema/sdp.rules.yaml` and the reasoning from here. The rules file carries a
  two-line pointer to this document and no longer carries the argument inline.
- Prose copies of the old reading in `SPECIFICATION.md` and four other documents
  are **not** corrected by this decision and remain outstanding. That is hub
  queue item **B-167**, which is blocked on the rules rewording landing; the
  rewording it produces may cite this document as the justification it is
  required to carry.

## Alternatives considered

- **Direct typing only** — every method or protocol IRI carries
  `rdf:type sosa:Procedure` itself. Rejected as measured rather than as a
  preference: it makes **all ten** of gcdfo 0.0.9's survey-method concepts
  non-conformant — gcdfo types none of its own terms — and contradicts smn's own
  shipped shape. It is not discarded either, because reachability contains it as
  the zero-length case.
- **Accept an asserted `skos:broader`/`skos:broadMatch` to `sosa:Procedure`** —
  refused; see above. It is the literal shape Q47 asked about, and the "no" half
  of the ruling.
- **Leave it to a reasoner** — rejected: neither `sosa:usedProcedure`'s
  `schema:rangeIncludes` annotation nor `skos:broader` has inferential force, so
  there is no entailment to rely on.
- **Leave the asserted edge merely unpermitted rather than refused by name** —
  rejected: an absence of permission is not a refusal, and this is the shape a
  reader arrives at first.
- **Keep the reasoning as adjacent comments in `schema/sdp.rules.yaml`** —
  rejected on review (pull request #8, 2026-09-15): roughly fifty lines of
  comment clutter a file whose job is to state rules. The reasoning is not
  deleted, it is here, and the rules file points at it.

## References

- SKOS Simple Knowledge Organization System Reference — integrity conditions
  S19–S22 and S41: <https://www.w3.org/TR/skos-reference/>
- Semantic Sensor Network Ontology — §3 and `sosa:usedProcedure`:
  <https://www.w3.org/TR/vocab-ssn/>
- Brett's ruling Q47 (2026-09-14) and the 2026-08-17 Hyatt-scheme constraint —
  metasalmon `knowledge/questions.md`
- `schema/sdp.rules.yaml` — the normative statement of both rules
