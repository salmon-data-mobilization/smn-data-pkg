# Workpad: B-106

*(This file is per-branch. It carried B-90's report on `main`, which is
preserved in git history at `9541217`; this branch replaces it rather than
appending, so the pull request diff is this item's report and nothing else.)*

## Queue item

**B-106** — Reword the two `sdp.rules.yaml` SOSA Procedure rules to the ruled
reachability reading. Repo `smn-data-pkg`, kind `defect`, severity P4, legacy
`#106`, venue `claude-science`. Evidence: metasalmon `knowledge/backlog.md`
entry `#106`, and the ruling it rests on, **Q47** in metasalmon
`knowledge/questions.md` (ANSWERED 2026-09-14, Brett).

Despite the P4 this is on the critical path: **B-48** (the last P1 — three
error-severity rules loaded and never executed) builds its dispatch on the text
produced here, so the wording is the specification for code somebody else
writes.

`retires_when` (abridged): both rules carry the ruled reading — declared by a
shared vocabulary, reaching `rdf:type sosa:Procedure` by a zero-or-more-step
`skos:broader` path, a directly typed IRI passing as the zero-length case; the
asserted `skos:semanticRelation` sub-property edge to an `owl:Class` refused by
name with the SKOS S19–S22 reason; estimate-type and data-quality vocabularies
named as never method vocabularies; "resolves to" dropped — the three validator
outcomes expressible with the unresolved one a skip and not a pass; and
metasalmon's vendored copy re-vendored in the same change.

## What changed and where

### `schema/sdp.rules.yaml` — the two rules, and nothing else

Both descriptions moved from a plain multi-line scalar to a `>-` folded block
scalar. That is deliberate and not cosmetic: a plain YAML scalar cannot contain
`": "`, and the other twelve rules avoid colons by using dashes throughout. The
new text needs colons to read as a specification (`Zero or more is
load-bearing: …`), so the two rules that carry it use block scalars. Paragraph
breaks survive folding as single newlines; verified by parsing.

**No rule `id`, `severity`, `version` or `profile` changed.** All 14 ids are
byte-identical to `main`, because B-48's test keys on rule ids.

- **`methods_are_sosa_procedures`** — five paragraphs.
  1. Unchanged in substance: what a method is, the three placements in order of
     preference, no per-package method registry, no dictionary `method_iri`.
     (The last two clauses moved from the end of the rule to the end of this
     paragraph, where the placements they qualify are.)
  2. The reachability condition. *Declared by* a shared vocabulary (not
     "resolves to"), *reaches* a resource carrying
     `rdf:type http://www.w3.org/ns/sosa/Procedure` by a `skos:broader` path of
     **zero or more steps**, with the zero-length case stated as a pass in the
     rule text rather than left to be derived. Says it is a check and not an
     entailment, and why: `sosa:usedProcedure` declares only
     `schema:rangeIncludes sosa:Procedure`, an annotation property with no
     inferential force.
  3. The refused edge, **by name**: an asserted `skos:broader`,
     `skos:broadMatch`, or any other sub-property of `skos:semanticRelation`
     whose other side is an `owl:Class`. With the S19–S22 reason in the rule
     text, and "pointing it the other way does not help".
  4. The exclusion, with the vocabularies **named**: a Hyatt (1997) estimate
     type (`gcdfo:Type1`–`gcdfo:Type6`, under `gcdfo:EstimateType`); an ordinal
     quality rating, the 1–5 scales behind `INFORMATION_QUALITY` and
     `INDEX_QUALITY`, or a reliability flag. "Neither satisfies this rule at any
     path length" — that phrase closes the loophole that an estimate type might
     qualify via some ancestor.
  5. The three outcomes — **absent**, **unreachable**, **unresolved** — each
     with its own message, never passing silently, and the skip stated as a skip
     in three separate ways so a validator author cannot read it as a pass: it
     leaves the rule unchecked for that IRI, it does not count as an executing
     check for the rule id, and `require_iris = TRUE` reports it as an error.

- **`row_varying_procedures_use_codes`** — two paragraphs. Carries the same
  condition, the same refused edge and the same three outcomes named
  individually, so a validator dispatching on this rule id alone has enough to
  write the check, while pointing at `methods_are_sosa_procedures` for the full
  statement rather than keeping a second full copy that can drift. The second
  paragraph states the exclusion again because `codes.csv` `term_iri` is where it
  actually bites — and states the consequence precisely: such a `term_iri` is
  **outside this rule's scope**, not a term that fails it.

- **A two-line pointer** above each rule, and nothing more. The reasoning —
  why "resolves to" went, why reachability subsumes direct typing, the
  OWL-punning measurement, why the condition is a check, why the two
  vocabularies are named, and the unresolved outcome's retirement condition —
  moved out of the file on review; see **Review round 2** below. The file is
  input-only to `scripts/generate_artifacts.py` (it reads `version` and
  `profile`; it never writes the file), so comments are durable — checked before
  relying on it.

### `CHANGELOG.md`

One entry under `## [Unreleased]` → `### Changed`, opening with a plain-language
summary of what changed and what it means for someone using the package, then
the specification wording: the new reading, the clauses of the ruling, the three
outcomes, that no rule id changed, and that nothing executes either rule yet
(#48). A second entry under `### Added` for the new ADR. Both shaped by review;
see **Review round 2** below.

## Commands run, and results

Everything `docs/entrypoints.md` and `.github/workflows/ci.yml` name, plus both
example packages. Run in the worktree, after the edit:

```
python3 -m pytest tests/ -q                    -> 38 passed in 0.55s (exit 0)
python3 -m unittest discover -s tests          -> Ran 38 tests ... OK
python3 scripts/generate_artifacts.py --check  -> Generated artifacts are in sync. (exit 0)
python3 scripts/validate_package.py examples/minimal-example
                                               -> Strict SDP validation passed (exit 0)
python3 scripts/validate_package.py examples/mixed-grain-example
                                               -> Strict SDP validation passed (exit 0)
git diff --check                               -> clean
```

Parse check on the edited file — the one thing the suite does not do, because
nothing in this repo loads the rules in a test:

```
python3 -c "import yaml; d=yaml.safe_load(open('schema/sdp.rules.yaml')); ..."
  -> version sdp-0.3.0, profile unchanged, 14 rules,
     ids identical to main, the two descriptions 3266 and 1346 chars
```

Every command was re-run unchanged after the review-round-2 edit, with identical
results; the parse check was widened to compare ids, severities, `version`,
`profile` and all fourteen descriptions against both the first commit and
`origin/main`. See **Review round 2** below.

### Failing-before / passing-after

**There is no red-to-green to show, and that is the finding rather than a gap in
the evidence.** This item is a defect in *text*, and the reason the text drifted
is that **nothing executes either rule** — `methods_are_sosa_procedures` and
`row_varying_procedures_use_codes` are two of the three rules in #48, loaded and
never run. Measured on `main` before the edit: neither rule id appears anywhere
in this repository outside `schema/sdp.rules.yaml`, and the whole suite is green
with the old wording. So the before-and-after that exists is:

- **Before:** all six commands green on `main` with both rules reading "resolves
  to a shared vocabulary concept typed as a SOSA Procedure" — a literal reading
  under which every gcdfo method target this ecosystem emits is non-conformant.
  Green proves only that nothing checks it.
- **After:** all six commands green with the ruled wording. Same proof, same
  limit.

The first genuine red-to-green for this text belongs to **B-48**, which is gated
behind **B-148** precisely so that wiring the check up does not turn the bundled
NuSEDS example red on day one.

## What I did not do, and why

- **Did not reword `SPECIFICATION.md`.** It restates the old wording nearly
  verbatim in two places (lines 237–238 and 265) and now contradicts the rules
  file. That is a real defect and it is **out of this item's scope** — it is
  **B-167**, below. `retires_when` names the rules file and the vendored copy and
  stops there, and HUB.md forbids widening a claimed item. The one line added to
  its "Non-normative guides" list in review round 2 is an index entry at line
  302, nowhere near either stale passage, and restates no rule.
- **Did not touch `docs/field-reference.md`,
  `docs/i-adopt-integration-guide.md`, `templates/.../README.md`,
  `template-source/.../README.md`, or
  `examples/mixed-grain-example/README.md`**, all of which carry the same
  phrasing. Same reason; two of them are generated, so editing them also moves a
  generated artifact.
- **Did not touch `docs/adr/0001-...md`.** An ADR is a dated record of a
  decision and is not corrected in place. Review round 2 added
  `docs/adr/0002-sosa-procedure-reachability.md`, which **supersedes** 0001's
  "resolves to a registered method" sentence on that point and says so, rather
  than editing 0001.
- **Did not implement any check.** That is B-48.
- **Did not change a rule id, severity, `version` or `profile`.**

## Belongs to another item

- **B-48** (P1, `claimable: false`) — three error-severity rules loaded and
  never executed. Both rules reworded here are two of the three. Its dispatch
  reads the text landed here; its own gate is B-148.
- **B-148** — gcdfo's estimate branch terminates in an untyped
  `gcdfo:EstimateMethod`, so 22 of metasalmon's 45 non-missing `gcdfo:` method
  targets reach no typed ancestor and fail under *either* reading. Not affected
  by this wording; it is why B-48 must not unblock into a failing check.
- **B-76** — which method-modelling style is canonical, and whether gcdfo is
  recorded as the deliberate NuSEDS method source. Q47 deliberately left this
  half open.
- **B-147** — smn's `alignment-main.ttl` already asserts the shape this rule now
  refuses, in 17 rows, two of them `skos:broadMatch` and one of them on
  `sosa:Procedure` itself. This item makes the spec refuse it; fixing smn is
  B-147, in a repository agents may not push to.

### Now **B-167** (was "candidate new item, no id yet")

Promoted to an item after this branch was first pushed: **B-167**, `icebox`, P3,
`blocked_by: [B-106]`, repo `smn-data-pkg`. Its `retires_when` splits the sites
into four hand-edited and two generated, which this table did not, and adds a
requirement this item cannot discharge for it: *the reworded prose must carry its
own justification rather than inheriting B-106's*. The ADR added in review round
2 is the document that justification can cite.

**`SPECIFICATION.md` and four other documents restate the two rules' old
wording, and now contradict `schema/sdp.rules.yaml`.** Evidence, measured on
this branch:

| File | Line(s) | Text |
|---|---|---|
| `SPECIFICATION.md` | 236–240 | "Every method or protocol IRI resolves to a shared vocabulary concept typed as a `sosa:Procedure`" |
| `SPECIFICATION.md` | 262–265 | "has a `codes.csv` `term_iri` resolving to a shared-vocabulary `sosa:Procedure` concept" |
| `docs/field-reference.md` | 64 | generated from `column_dictionary.schema.json`; "SOSA Procedure IRI" |
| `templates/salmon-data-package-template/README.md` | 15–17 | generated from `template-source/` |
| `template-source/salmon-data-package-template/README.md` | 15–17 | source of the above |
| `examples/mixed-grain-example/README.md` | 15–16 | "its code IRIs resolve directly to shared-vocabulary `sosa:Procedure` concepts" |

`SPECIFICATION.md` line 10 makes `schema/sdp.rules.yaml` the home for exactly
these rules, so the five documents are the copies and they are the ones that are
wrong — the queue README's own rule, pointed at prose instead of a card. Worth
its own item because rewording normative spec prose is a second semantic choice
needing its own review, two of the six files are generated, and none of it is in
this item's `retires_when`. Suggested severity P3: nothing errors, but a reader
of `SPECIFICATION.md` is now told the literal reading the ruling rejected.

## Guards, suppressions, skips and workarounds added — and what retires them

One skip was added, **to the specification** rather than to code: the
**unresolved** outcome, where a check cannot resolve the namespace declaring an
IRI and therefore cannot decide between *absent* and *unreachable*.

- **What it routes around:** a validator may hold no copy of the vocabulary that
  declares a namespace, and neither `smn` nor `gcdfo` is served for per-IRI
  dereference — the same fact that removed the phrase "resolves to".
- **Why it is not a pass, stated three ways in the rule text** so a validator
  author cannot read it as one: it leaves the rule unchecked for that IRI; it
  does not count as an executing check for the rule id (so it does not satisfy
  B-48's test that every rule id has an executing check); and a strict mode that
  requires IRIs (`require_iris = TRUE`) reports it as an error.
- ***Retires when:*** pinned `smn` and `gcdfo` snapshots ship in metasalmon's
  `inst/extdata` and in the metasalmonpy equivalent, so every namespace either
  resolves against the pinned snapshot or is genuinely outside the spec's
  knowledge, and the check can report *absent* or *unreachable* in every case.
  Stated in `docs/adr/0002-sosa-procedure-reachability.md` under its own heading
  as well as here. Review round 2 moved it there out of the rules file; the rules
  file's pointer names it by name, `docs/entrypoints.md` names it, and
  `SPECIFICATION.md`'s guide list points at the ADR, so it is reachable from all
  three places a maintainer would start from.

## Paired change in another repository

metasalmon's vendored copy at `inst/extdata/schema/sdp.rules.yaml` was
**byte-identical to this repo's file on `main`** (md5 `3c702a37...` across the
upstream file, metasalmon's copy and the primary checkout), so there is **no
drift** and the re-vendor is a plain copy. No vendoring script exists in either
repo; metasalmon's `knowledge/orientation.md` (lines 130–131) says to keep the
copies in step by "re-vendoring from upstream, not by hand-editing either side",
which is what was done — the file was copied, not retyped.

It is a different repository, so it cannot be in this commit. It lands as a
**second branch and second draft pull request in metasalmon**, off current
`main`, which must not merge before this one.

**Review round 2 changed this file's bytes again**, so the vendored copy must be
re-vendored from *this* branch tip and not from the first commit. The
byte-identity property (verified last time by identical git blob SHA) has to
survive the merge; Brett re-vendors after merging.

## Review round 2 — 2026-09-15

Brett reviewed PR #8 and left two comments. Both addressed here; neither thread
replied to or resolved, which is his.

### 1. `schema/sdp.rules.yaml` line 52 — "Are these comments necessary here? I feel like they should be in other documentation so that we don't clutter up the rules"

Agreed, and done as a **move, not a cut**: B-106's `retires_when` requires the
unresolved skip to carry its own retirement condition, and metasalmon's
`AGENTS.md` requires any suppression to say what retires it, so deleting the
reasoning was not available.

**Where it went: `docs/adr/0002-sosa-procedure-reachability.md`** (new). Chosen
because `docs/adr/` is what this repository already uses for *why a modelling
decision went that way* — `docs/adr/0001-observation-structure-and-procedure-metadata.md`
exists and is listed in `SPECIFICATION.md`'s "Non-normative guides" — and
because the content is exactly an ADR: a dated ruling (Brett, Q47, 2026-09-14),
its context in measured vocabulary facts, its consequences, and the alternatives
rejected. Following the existing convention beat inventing a location.

Rejected locations:

- **`SPECIFICATION.md`** — it is normative, it is where the *old* wording still
  lives in two places, and putting new reasoning into it would entangle this
  change with **B-167**. One index line was added to its guide list at line 302;
  nothing was added near lines 237–238 or 265.
- **`docs/i-adopt-integration-guide.md`** — a usage guide, not a decision
  record. It answers "how do I record a method", not "why is this the condition".
- **Editing ADR 0001** — a dated record is superseded, not corrected in place.
  0002 says which sentence of 0001 it supersedes.

**Left in the rules file**, above `methods_are_sosa_procedures`:

```yaml
# Rationale, the ruled reading, the refused owl:Class edge and the unresolved
# outcome's retirement condition: docs/adr/0002-sosa-procedure-reachability.md
```

and above `row_varying_procedures_use_codes`:

```yaml
# Same condition, refused edge and three outcomes as
# methods_are_sosa_procedures; rationale in
# docs/adr/0002-sosa-procedure-reachability.md
```

The pointer names the retirement condition rather than merely the file, so a
reader of the rules file is told it exists and where. The file went from 200
lines to 144; the 58-line block and the 3-line pointer are gone.

Two indexes now carry the ADR so it is not findable only from the rules file:
`docs/entrypoints.md` ("Canonical Implementations") and `SPECIFICATION.md`
("Non-normative guides").

### 2. `CHANGELOG.md` line 10 — "Start with a concise summary in plain language"

The entry now opens with what changed and what it means, in language that does
not require knowing what `skos:broader` is: a method term may qualify through a
broader term in the vocabulary that defines it, instead of having to be labelled
a procedure itself; the survey-method terms both salmon vocabularies actually
publish ("aerial survey count", "redd count", "trap count") therefore work. It
then names the two things that got **stricter**, which is the part a package
author should check their own package against — a quality or estimate-type code
is never a method term, and an unfetchable vocabulary must be reported rather
than passed. The specification wording follows in a second paragraph, and the
SKOS/OWL argument is no longer restated there at all; it points at the ADR.

### A factual error found while moving the text, and corrected

The paragraph being moved said gcdfo 0.0.9 *"types only its broad enumeration
concept `rdf:type sosa:Procedure`"*. **That is wrong, and it was carried from the
first round of this item.** Re-measured this round by parsing
`docs/releases/0.0.9/gcdfo.ttl` with `rdflib` rather than by reading it:

```
gcdfo 0.0.9 subjects typed sosa:Procedure -> exactly one:
  https://w3id.org/smn/EnumerationMethod
gcdfo:EnumerationMethodScheme members      -> 11, of which 10 are gcdfo: terms,
  every one an untyped skos:Concept with skos:broader smn:EnumerationMethod
```

gcdfo types **none of its own terms** `sosa:Procedure`. The single typed subject
is an **smn** IRI whose typing gcdfo restates. So "ten of eleven gcdfo method
concepts" overcounted by one and attributed an smn term to gcdfo.

The consequence is not cosmetic and is now recorded in the ADR: **the qualifying
path crosses a vocabulary boundary, and in practice it always does.** A B-48
check cannot decide either rule from the vocabulary that declares the IRI alone
— it has to follow `skos:broader` into whatever vocabulary the next hop lands
in, and an unresolvable hop is `unresolved`, not `unreachable`. The rule text
never restricted the path to one vocabulary, so this records that the
distinction is load-bearing rather than changing the rule.

smn's side of the claim re-measured the same way and **held**: exactly six
concepts typed `skos:Concept, sosa:Procedure` in
`ontology/modules/07-controlled-vocabularies.ttl`, and
`sh:zeroOrMorePath skos:broader` present in `ontology/shapes/method-shapes.ttl`
with the `owl:someValuesFrom` explanation in module 02.

### Re-verified after the edit

```
python3 -m pytest tests/ -q                    -> 38 passed (exit 0)
python3 -m unittest discover -s tests          -> Ran 38 tests ... OK
python3 scripts/generate_artifacts.py --check  -> Generated artifacts are in sync. (exit 0)
python3 scripts/validate_package.py examples/minimal-example
                                               -> Strict SDP validation passed (exit 0)
python3 scripts/validate_package.py examples/mixed-grain-example
                                               -> Strict SDP validation passed (exit 0)
git diff --check                               -> clean
```

Identical to the first round, and to the baseline measured on this branch before
the edit. `generate_artifacts.py` writes only `docs/field-reference.md` under
`docs/`, so a new file in `docs/adr/` cannot desynchronise it — confirmed by
`--check` and by reading `FIELD_REFERENCE_PATH`.

Parse check, widened this round: `version` `sdp-0.3.0`, `profile`, 14 rules, and
the ids, severities **and all fourteen descriptions** identical to both the first
commit on this branch and `origin/main`. **Only comments changed**, so nothing
B-48 keys on moved. The rules file is still pure ASCII.

### Not done, deliberately

- **Not merged, and neither review thread replied to or resolved.** Brett's.
- **PR #8's body is now partly stale** — it says "An adjacent comment block
  carries what is reasoning rather than rule", and its verification table
  predates this round. Editing a pull request body is not a write `HUB.md`'s
  register permits, so it is flagged rather than fixed.
- **metasalmon untouched.** Its PR #120 carries the vendored copy; re-vendoring
  after this merges is Brett's, and it must come from this branch tip.
