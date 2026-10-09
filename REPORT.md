# Can LinkML machinery serve as the schema interface for AmadeusDB?

**Verdict: yes, with one ~250-line post-processor that you write once.**

Everything below was executed on 2026-09-18 on macOS 15 (arm64) against
`linkml` 1.9.x, `duckdb` 1.5.5, `sedonadb` 0.4.1. Reproduce with `just all`.

| Question | Answer |
|---|---|
| Does LinkML express the model? | Yes. 5 modules, 20 classes, 31 enums, 235 slots, 21 rules. |
| Does `gen-sqltables` produce usable DDL? | Not as-is. Fails on **both** engines for four fixable reasons. |
| Does it work after post-processing? | Yes. DuckDB 42/42 statements, SedonaDB 40/40. |
| Can both engines hold the data and answer the same SQL? | Yes. 121/121 rows, 8/8 queries, **identical results**. |
| Does validation actually catch things? | Yes. 18 rules have a dedicated counter-example and all 18 fire. |
| Can it emit a valid EnVar record? | Yes. 57/75 fields derived, 12 crosswalked, 6 genuine gaps. |
| Is SedonaDB viable as the primary engine? | Yes for this workload, with three caveats below. |
| **Does it force Python on an R package?** | **No.** `just gen-r` emits pure-R `checkmate` validators; 13/13 agree with the Python validator. LinkML is build-time only. |

---

## 1. What worked out of the box

* **`gen-linkml`** compiles the five modules with no errors. Multi-module
  imports, cross-module slot reuse and `exact_mappings` to EnVar/HEW URIs all
  behave.
* **`gen-sqltables` flattens `is_a` inheritance correctly.** `AmbientValue`'s 21
  shared slots are copied into each of the five concrete child tables. This is
  the right physical design — a single polymorphic value table with mostly-null
  geometry columns would defeat both partitioning and spatial indexing — and it
  is what the generator does by default.
* **Multivalued slots become junction tables** with composite primary keys and
  foreign keys on both sides (`ToolRun_upstream_runs`,
  `Asset_variables_present`). Proper relational output, not arrays.
* **`unique_keys` becomes `UNIQUE`.** The `GridCellValue` composite key
  (variable, grid, cell_x, cell_y, level, valid_time, source_system,
  data_status) survives into the DDL, which is what makes idempotent
  re-ingestion possible.
* **Custom generators are easy to write against `SchemaView`** — which is
  fortunate, because **LinkML ships 41 generators and none of them target R**
  (Python, Pydantic, Rust, Java, TypeScript, Go, C++, Proto; the nearest
  relatives are `gen-pandera` and `gen-sqlvalidation`). So
  `scripts/gen_r_validators.py` is ~320 lines *we* wrote and now maintain. It
  emits validators for all 18 concrete classes including all 18 conditional
  rules, and `just test-r` shows them agreeing with `linkml-validate` on 13/13
  cases. §4a is honest about what it does and does not cover.
* **`gen-doc`** produced 307 Markdown pages. **`gen-erdiagram`** produced a
  427-line Mermaid ER diagram. **`gen-pydantic`** produced a working ingest
  contract. **`gen-json-schema`** is what `linkml-validate` actually runs.
* **`datetime` is validated as RFC 3339** and *rejects* a timestamp without an
  offset. This looks like friction and is not: the plan requires "canonical UTC
  timestamps", and this enforces it at the door. It was the only error class in
  the first validation run of the sample data.

## 2. What broke, and why

### 2.1 The generated DDL fails on both engines

Running `gen-sqltables` output directly: **1 of 31 statements succeeded on
DuckDB, 1 of 31 on SedonaDB.** Four independent causes:

| # | Problem | DuckDB | SedonaDB | Fix |
|---|---|:-:|:-:|---|
| 1 | **Tables are not emitted in foreign-key order.** `DataSource` references `AmadeusDatabase`, which is emitted 450 lines later. Every FK-bearing table fails. | ✗ | n/a | Topological sort on the FK graph. ~20 lines. |
| 2 | **`DATETIME` is not a SedonaDB type** (`SedonaError: Unsupported SQL type DATETIME`). | ok | ✗ | Rewrite to `TIMESTAMP`. |
| 3 | **SedonaDB does not support foreign key constraints at all** (`Foreign key constraints are not currently supported`). | ok | ✗ | Strip for that dialect; the relationships stay in the schema and are checked by `linkml-validate`. |
| 4 | **The tree-root container becomes a table**, and its auto-created `AmadeusDatabase_id` back-reference is added to every child table. | noise | noise | Drop the container and its back-references. |

On #4 there is also a **generator inconsistency worth reporting upstream**:
`--generate_abstract_class_ddl false` suppresses the `CREATE TABLE` for the
container *but leaves every `FOREIGN KEY ... REFERENCES "AmadeusDatabase"`
clause in place*, producing DDL that cannot execute on any engine. The flag is
only safe if you also strip the dangling references.

### 2.2 Geometry is the structural gap

LinkML has no spatial type, and **SedonaDB will not accept a `GEOMETRY` column
in `CREATE TABLE`**. (DuckDB's spatial extension *does*, once `LOAD spatial` has
run — an earlier draft of this report wrongly said neither engine did. The
design below is still right, for the reason given underneath, but the
justification is portability rather than universal refusal.)

```
sedonadb> CREATE TABLE t (id VARCHAR, g GEOMETRY)
SedonaError: Unsupported SQL type GEOMETRY
```

Geometry therefore arrives as `TEXT`. This is fine, and the fix is clean:

```sql
-- generated, one view per table with WKT columns
CREATE OR REPLACE VIEW "GridCellValue_geo" AS
SELECT *,
  ST_SetSRID(ST_GeomFromText(cell_centroid_wkt), CAST(COALESCE(srid, 4326) AS INTEGER)) AS cell_centroid,
  ST_SetSRID(ST_GeomFromText(cell_polygon_wkt),  CAST(COALESCE(srid, 4326) AS INTEGER)) AS cell_polygon
FROM "GridCellValue";
```

Geometry at runtime is a real `geometry<Wkb>`, and `ST_Intersects`,
`ST_Contains`, `ST_DWithin` and `ST_Distance` all work against the view.

The generator is driven by the **custom type `WktLiteral`**, not by a hardcoded
column list — adding a geometry slot anywhere in the schema is enough to get it
promoted. That makes the type the contract, which is the property you want.

Text is the common denominator, and that is the actual argument for it. DuckDB
would take a real `GEOMETRY` column; SedonaDB will not, so a single generated
DDL that runs on both has to be text. Two further benefits fall out: the base
tables load from CSV or Parquet with **no spatial extension present at all**,
which the register-don't-ingest path needs, and the stored form is the one that
survives a round trip through any tool.

Every spelling was tried against SedonaDB before concluding this —
`GEOMETRY`, `GEOMETRY(POINT)`, `GEOMETRY(POINT,4326)`, `GEOGRAPHY`,
`ST_GEOMETRY`, `POINT`, `WKB` — all refused with `Unsupported SQL type`. Only
`BYTEA` is accepted, which would hold WKB but loses the CRS that Sedona
otherwise tracks so well.

### 2.3 Enum constraints are silently lost in SQL

`gen-sqltables` renders an enum-ranged slot as `VARCHAR(n)` with **no `CHECK`
constraint** — zero in the whole 1070-line, 33-table output. The permissible values are
enforced by `linkml-validate` and by nothing in the database, so anything
inserted by a path that skips validation can hold an arbitrary string.

The post-processor emits them, reading the values from the schema:

```sql
CONSTRAINT "ck_DataSource_access_protocol" CHECK (access_protocol IN
  ('https_bulk_file', 'ftp', 's3_object_store', 'stac_api', 'opendap',
   'thredds', 'rest_api', 'harmony', 'arcgis_service'))
```

DuckDB accepts these. **SedonaDB 0.4.1 does not support `CHECK` in
`CREATE TABLE`**, so for that dialect the enum remains validation-only — a real
difference in guarantees between the two backends, and one the capability
matrix the plan calls for should record.

### 2.4 `rules:` do not reach the database at all

The 21 conditional rules — a daily product must declare its day boundary, a
forecast must carry a reference time, a missing value must say why — generate
**no** SQL. Some are expressible as `CHECK` constraints and some are not.

We deliberately did **not** half-implement them. A rule set that is enforced in
the application layer and partially in the database is worse than one that is
clearly enforced in exactly one place: it invites the assumption that the
database is authoritative when it is not. **All 21 are enforced before data reaches the
database** — by `linkml-validate` on the Python side and by the generated R
`checkmate` validators on the R side (§4a) — and the database is treated as a
store that trusts its writer. If AmadeusDB later accepts writes from paths that
bypass both, this decision has to be revisited, and that is a deployment
decision rather than a schema one.

## 3. Two LinkML limitations that changed the model

These are the findings worth carrying upstream, because in both cases *the
rule looked fine and silently did nothing*.

### 3.1 A boolean cannot be a rule precondition

```yaml
preconditions:
  slot_conditions:
    values_materialized:      # range: boolean
      equals_string: "true"
```

compiles to `{"const": "true"}` — the JSON **string** `"true"` — which never
matches the JSON boolean `true`. The rule never fires, and validation reports
nothing. `equals_string` is LinkML's only equality construct in a precondition,
and it stringifies; there is no `equals_boolean`.

Caught only because the counter-example `16_materialized_asset_without_run.yaml`
was accepted when it should have been rejected.

**Fix applied:** the two flags used as rule preconditions became enums —
`values_materialized: boolean` → `value_state: ValueMaterializationEnum`
(`registered_only` | `materialized`), and `allow_status_mixing: boolean` →
`status_mixing_policy: StatusMixingPolicyEnum` (`refuse` |
`allow_with_policy`). Both rules now fire. The enums also read better, so this
is not purely a workaround — but it was forced, not chosen.

**Rule of thumb for the team: if a field participates in a rule, do not model
it as a boolean.**

### 3.2 Several `ABSENT` postconditions collapse into one weak constraint

```yaml
postconditions:
  slot_conditions:
    temporal_coverage_start: {value_presence: ABSENT}
    temporal_coverage_end:   {value_presence: ABSENT}
```

compiles to:

```json
"then": {"not": {"required": ["temporal_coverage_start", "temporal_coverage_end"]}}
```

`required: [a, b]` means "both present"; negating it means "**not both**
present". A timeless product declaring only a start date validates. What is
needed is `{"allOf": [{"not": {"required": ["a"]}}, {"not": {"required": ["b"]}}]}`.

**Fix applied:** one rule per slot. Two rules where the intent reads as one.

**And it happened twice.** After writing the fix for the `timeless` rule, the
same mistake was still present on `CanonicalVariable` — a single rule asserting
that a categorical variable has neither `plausible_min` nor `plausible_max`.
The counter-example declared *both*, so it was rejected, and the defect was
invisible; a variable declaring only a minimum would have validated.

It was caught by
`tests/test_schema.py::test_at_most_one_absent_postcondition_per_rule`, which
walks every rule in the schema and fails on any with more than one `ABSENT`
postcondition. That is the useful lesson here: **this class of bug is not
catchable by reading the schema, and it is not catchable by a counter-example
unless the counter-example happens to be the weak case.** It is catchable by an
invariant over the model, cheaply, forever. The counter-example was
subsequently narrowed to declare only `plausible_min`, so the specific case is
now covered both ways.

### 3.3 What LinkML rules structurally cannot express

Rules see one object. They cannot see across a reference. So this is not
expressible and is *not* a bug:

> A request whose `aggregation_method` is `mean` must not target a
> `CanonicalVariable` whose `extensivity` is `extensive`.

The check spans `ExtractionRequest → requested_canonical_variables →
CanonicalVariable`.
`tests/data/problem/invalid/AmadeusDatabase-20_unknown_extensivity_strict_request.yaml`
therefore **validates**, and the test suite asserts that it validates, so the
limitation stays visible rather than looking like coverage.

These checks belong in the query planner, and `scripts/import_external.py`
stage 3 implements them (extensivity-versus-aggregation, CF-name agreement,
units-without-conversion). "LinkML cannot express it" is not a reason to leave
it unchecked — it is a reason to know where the check lives.

## 4a. No Python in the runtime

The plan's first assumption (**A-01**) is *"core users require R and SQL first;
Python interoperability is desirable through open database/Arrow interfaces"*,
and §4.2 item 6 floats `checkmate` for schema checks. The obvious objection to
LinkML is that it drags a Python runtime into an R package. It does not, and
demonstrating that is cheap.

LinkML here is a **build-time** tool, in the same category as `roxygen2`: it
runs in CI, and its outputs are committed. `scripts/gen_r_validators.py`
(~260 lines against `SchemaView`) emits `check_<Class>()` / `assert_<Class>()`
for all 18 concrete classes — required slots, types, enum membership, numeric
bounds, regex patterns, and all 18 conditional rules — as plain readable R:

```r
  # rule 2: A daily product must declare where its day starts.
  if ((!is.null(x[["temporal_resolution"]]) &&
       identical(as.character(x[["temporal_resolution"]]), "daily"))) {
    if (is.null(x[["day_boundary_convention"]]))
      return("Product: rule 2 — `day_boundary_convention` is required here")
  }
```

`just test-r` pushes the same cases as `tests/data/invalid/` through the generated
R: **13 of 13 behave identically to `linkml-validate`.** If the two ever
diverge, that test fails — which is what makes one schema the single source of
truth instead of two copies that drift.

The dependency this adds to `amadeus` is `checkmate`, a zero-dependency CRAN
package the plan was already considering.

### What it cost, and what it does not cover

Honest accounting, because a generator that looks complete and is not is worse
than no generator at all:

* **It is ours to maintain.** LinkML has no R generator, so this is ~320 lines
  of Python we wrote. Contributing it upstream is the obvious move if this
  direction is taken.
* **One round of fixes.** The first pass scored 10/13. Two root causes: the
  generator read `pattern:` off the *type* but not off the *slot*, and handled
  `minimum_value` in rule preconditions but not `maximum_value`. Both were
  caught by the R test, not by reading the code.
* **It implements the subset of LinkML this schema uses**, not the language.
  Preconditions: `equals_string`, `equals_number`, `value_presence`,
  `minimum_value`, `maximum_value`, `any_of`. Postconditions: `required`,
  `value_presence`, `equals_string`, `pattern`. Multivalued and inlined slots
  are skipped by design — they become junction tables and are validated
  relationally.
* **It fails loudly rather than skipping.** A real defect found while writing
  this up: the first version silently ignored ten precondition and twelve
  postcondition constructs — exactly the failure mode this whole schema effort
  exists to prevent. It now collects everything it cannot express, writes
  nothing, and exits non-zero:

  ```
  ERROR: this schema uses constructs the R generator cannot express.
  The R validators would silently not enforce them, so nothing was written.
    - Product rule 2 precondition on `temporal_resolution`: operator 'none_of' is not implemented
  ```

  Verified by injecting a `none_of` rule into the schema and confirming the
  build fails. A schema edit that outruns the generator is now a CI failure
  instead of a quietly unenforced rule.

## 4. SedonaDB versus DuckDB, measured

Both engines took the full generated DDL, all 121 sample rows, and all 8
demonstration queries — including spatial joins — and **returned identical
results**. On the evidence of this workload, the backend abstraction the plan
wants is achievable at the schema level.

```
DuckDB     DDL  42 ok/0 err | rows 121/121 | queries 8 ok/0 failed
SedonaDB   DDL  40 ok/0 err | rows 121/121 | queries 8 ok/0 failed
```

**SedonaDB, in favour**
* Installs cleanly from PyPI (48 MB wheel), no JVM, no Spark.
* Genuine spatial-native: geometry is a first-class Arrow type
  (`geometry<Wkb>`), not an extension bolted onto a scalar engine.
* **Tracks SRID on the geometry value.** DuckDB's spatial extension has no
  `ST_SRID` or `ST_SetSRID` at all — it exposes `ST_SetCRS`/`ST_CRS`, a
  different and looser model — so in Sedona the CRS is part of the value rather
  than an attribute of the row that a join can drop. (This is why the generated
  DuckDB views call bare `ST_GeomFromText` and the SedonaDB views wrap it in
  `ST_SetSRID`: the dialect profiles differ because the engines genuinely do.)
* `CREATE TABLE` / `INSERT` / `VIEW` all work — it is not a read-only query
  engine, which was the main thing worth checking.
* Reads and writes GeoParquet natively, which is the persistence story.

**SedonaDB, against — the three caveats**
1. **No foreign keys and no `CHECK` constraints.** The database enforces
   nothing about referential integrity or domains. Everything rests on
   validation before write. With DuckDB you get both for free. This is the most
   consequential difference and it is not a performance question.
2. **No persistent database file.** SedonaDB is in-memory plus external tables;
   persistence *is* Parquet/GeoParquet on disk. This answers the plan's open
   question 4 directly: with SedonaDB, "persistent versus non-persistent" is
   not a choice you get to make — the answer is Parquet. With DuckDB you can
   have a single `.duckdb` file with constraints inside it.
3. **A thinner SQL surface.** `SUBSTR` is not planned (`Substring could not be
   planned by registered expr planner`), and the Arrow export path needs
   `geoarrow-pyarrow` installed separately or every `to_arrow_table()` call
   raises `ModuleNotFoundError`. Expect to find more of these; pin the version.

Two further facts found while testing:
* `COPY (...) TO '*.parquet'` **fails if the geometry has no CRS** — "Can't
  write GeoParquet from null CRS". `ST_SetSRID` is not optional if you intend
  to export, which is why the generated views always set it.
* `sedonadb` is not CRAN-compatible (already noted in the plan). The schema
  layer is indifferent to this — the DDL and the SQL are the contract, and
  they are the same from R, Python or a shell.

**Recommendation.** Nothing here argues against SedonaDB as the primary engine.
But the constraint gap is a real cost, and the cheap way to have both is to
**keep DuckDB as the validating gate in CI**: generate both DDLs from the same
schema, load fixtures into DuckDB *with* its foreign keys and `CHECK`
constraints, and let a violation fail the build. You then get constraint
enforcement as a test even though production runs on an engine that cannot
enforce it. That is a better use of "DuckDB as contingency backend" than
keeping it warm in case SedonaDB disappoints.

## 5. The EnVar round trip

`scripts/export_envar_record.py` projects one extracted value into an EnVar
`EnvironmentalExposureRecord` and validates it against the canonical schema at
`monarch-initiative/linkml-microschemas-envar`. Result: **`No issues found`**.

That is objective O-02's stated evidence — "LinkML validation report, schema
migrations, crosswalk, sample records" — produced mechanically rather than
promised.

The projection ledger is the useful output:

| | count | meaning |
|---|---:|---|
| **derived** | 57 / 75 | read straight out of AmadeusDB |
| **crosswalk** | 12 / 75 | present but differently named or encoded |
| **gap** | 6 / 75 | EnVar requires it, AmadeusDB cannot supply it |

**The 12 crosswalks are the dangerous category**, because each is a place a
careless mapper changes the meaning without erroring. Examples:

* `units_ucum` — HEW prefixes (`UCUM:Cel`), EnVar does not (`Cel`).
* `temporal_aggregation_window_seconds` — ISO 8601 duration here and in HEW,
  integer seconds in EnVar.
* `extraction_method` — AmadeusDB's `exact_extract` names the *implementation*
  (`exactextractr`); EnVar's `area_weighted_polygon_mean` names the
  *mathematics*.
* `concept_status` — AmadeusDB uses HEW's five values; EnVar has three, so the
  OMOP-critical standard-versus-nonstandard distinction is lost on the way out.
* `source_native_format` — 19 members here, 8 in EnVar, and **no vector format
  at all** in EnVar's enum, so shapefiles map to
  `csv_station_observations`. That one is bad enough to raise upstream.

**The 6 gaps are the honest cost of adopting the sidecar**, and three of them
are the same finding: EnVar requires fields about the *person* (`subject`,
`address_period_alignment`, `clinical_date_assignment_convention`) that amadeus
cannot supply because it ends at the geojoin. EnVar's own documentation already
flags `subject` as an open question for precisely this reason. The other three
(`exposure_model_type`, `exposure_model_inputs`, `per_value_uncertainty_type`)
are per-product human judgements — supplied here from an explicit reviewable
table, and `exposure_model_type` is a good candidate for a new slot on
`Product`.

## 6. Three things to send upstream

Found while modelling, and each one is a gap in a schema that is not ours:

1. **`VariableExtensivityEnum`** — intensive / extensive / categorical. Neither
   EnVar nor HEW models it, and without it no schema can say whether a buffer
   mean is a legal operation. Requested independently by the project lead and
   tracked as amadeus #249.
2. **Per-row `data_status`** — EnVar has dataset-level
   `source_homogenisation_status` only. The AQS/AirNow rule needs it per row,
   or preliminary and quality-controlled values for the same monitor-hour
   cannot coexist.
3. **`GridDefinition` as an entity** — HEW's `spatial_resolution` is a string
   (`"1 km"`) and EnVar's is a number in metres. Neither can express a grid's
   projection, origin, dimensions or vertical levels, so "grid size is a
   dataset-level property" stays prose.

Plus enum extensions with nowhere to go upstream today: `timeless` and
`multi_year_epoch` temporal resolutions (a third of the amadeus catalog is
otherwise unrepresentable), `hex_cell` and `line_feature` spatial supports, and
eleven native formats.

## 7. Reproducing this

```bash
uv sync --group dev
just all
```

| Target | What it does |
|---|---|
| `just compile` | schema compiles |
| `just test-examples` | 1 valid + 20 counter-examples behave as expected (19 rejected, 1 asserted to pass) |
| `just gen-sql` | generic DDL → DuckDB and SedonaDB DDL |
| `just load` | load the sample instance into both engines, run 8 queries |
| `just export-envar` | emit an EnVar record and validate it |
| `just import-demo` | the six-stage external-dataset import |
| `just check` | the CI gate |

**A caveat on the numbers.** The *metadata* in the examples is real — sources,
products, units, day boundaries, calendars, resolutions, DOIs and citations
were taken from the actual products. The *values* are illustrative: the 1.18 °C
GridMET-versus-Daymet difference that `just import-demo` prints comes from
plausible invented cell values, not from downloading the files. It is the right
order of magnitude (the literature figure for this comparison is ~1.26 °C) and
it demonstrates the mechanism, but it is not a measurement. Reproducing it
against real assets is a genuinely useful next step and needs network access
and an Earthdata token.
