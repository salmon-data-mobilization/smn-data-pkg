# Measure-specific observation structures

Use the optional `metadata/structure/` extension when one physical table stores
measures at different logical grains. Do not add it to a simple table merely to
repeat its primary key.

## Mental model

A physical row and a logical observation are not always the same thing. In a
wide stock-recruit table, total spawners might be a brood-year measure repeated
on several age-specific recruit rows. The structure metadata declares two
logical projections:

| Structure | Measure | Dimensions (logical key) | Attributes |
| --- | --- | --- | --- |
| total spawners | `total_spawners` | stock, brood year | none |
| recruits by age | `recruits` | stock, brood year, return year, age | estimation procedure |

The validator permits the repeated spawner value only when it is invariant for
the same stock/brood-year tuple. This protects downstream users from accidentally
summing a coarser-grain value once per age row.

## Files and rules

The two files are optional but paired:

- `observation_structures.csv` names and describes each logical structure.
- `observation_components.csv` binds table columns to `measure`, `dimension`, or
  `attribute` roles.

Each structure has exactly one measure. Dimensions define grain. Attributes add
observation context without changing grain. Components marked
`required_when_observed=TRUE` must be non-empty wherever the measure is
non-empty. Measure and dimension components always use `TRUE`. When the paired
extension is present, it covers every measurement column exactly once. The
validator compares grain and invariant values after normalizing them according
to the dictionary `value_type`, rather than treating harmless numeric lexical
variants as different observations.

See `examples/mixed-grain-example/` for a complete package.

## Relationship to W3C RDF Data Cube

The role vocabulary follows the same basic separation as Data Cube: measures
carry values, dimensions identify observations, and attributes qualify them.
The SDP extension is intentionally a CSV-level logical model, not a claim that
the package is already an RDF Data Cube.

An RDF exporter can normalize each structure into its own observation stream
and select or construct a compatible `qb:DataStructureDefinition`. Do not map
SDP's measure-specific dimension binding directly to `qb:measureDimension`.
That Data Cube term supports the specific `qb:measureType` pattern in which a
long-form observation identifies which measure it reports.

Primary reference: [W3C RDF Data Cube Vocabulary](https://www.w3.org/TR/vocab-data-cube/).

## Constraints are not dimensions

An I-ADOPT constraint records fixed semantic context in a variable definition,
such as spawner life stage. A dimension is a value-bearing coordinate that can
vary by row, such as `age`. The two can both be relevant:

- Use `constraint_iri` when fixed context is needed to decompose the compound
  measurement meaning.
- Bind a data column as a dimension when its values identify individual logical
  observations.

A readable column name is useful documentation but is not a substitute for
machine-readable decomposition unless the referenced compound term itself
publishes equivalent semantics for consumers.
