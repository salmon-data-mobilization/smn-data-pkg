# Mixed-grain observation structure example

This SDP demonstrates two measures stored in one wide table at different logical
grains. `total_spawners` is identified by stock and brood year, while `recruits`
is identified by stock, brood year, return year, and age. The repeated
`total_spawners` value must therefore be invariant within its declared dimension
tuple.

The example also shows both procedure patterns (sdp-0.3.0):

- The table cites an **in-package protocol** (`tables.csv.protocol_citation`
  names the *Collection protocol* section below), which specifies which method
  produces each measure — so no per-column method metadata is needed.
- `estimate_method` is a row-varying attribute bound with
  `sosa:usedProcedure`; its code IRIs resolve directly to shared-vocabulary
  `sosa:Procedure` concepts (placeholder `example.org` IRIs here).

## Collection protocol

Spawner abundance (`total_spawners`) is estimated by spawning-ground survey.
Recruit abundance (`recruits`) is estimated per row by the method named in
`estimate_method`: mark-recapture or expanded count. In a real package this
section (or an external protocol document referenced by `protocol_iri`) is
the authoritative statement of which method produces which measure.

The files under `reproducibility/` are optional sidecars. They preserve review
and workflow context but do not alter SDP observation semantics.
