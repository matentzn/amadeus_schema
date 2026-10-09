# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A **proposal**, not a shipping library: a LinkML data model ("AmadeusDB") for the
database-backed next generation of the NIEHS [`amadeus`](https://github.com/NIEHS/amadeus)
R package. It is standalone and adds no dependency to `amadeus` itself.
`REPORT.md` is the deliverable — it records what LinkML could and could not do,
measured. When a change alters a measured number (validation counts, DDL
tables, query results, integrity checks), `REPORT.md` and the "Results" block in
`README.md` are part of the change.

Repo scaffolding comes from the [`linkml-project-copier`](https://github.com/linkml/linkml-project-copier)
template; `just update` re-runs `copier update`, so template-owned files
(`justfile`, `.pre-commit-config.yaml`, CI workflows) should be edited sparingly.

## The amadeus R package — the other half of the cycle

This schema models a package that lives in a **different checkout**:
`~/ws/software/amadeus` (under `software/`, not `projects/` — the schema repo is
the odd one out). It is NIEHS's public repo, CRAN `amadeus` 2.0.2, currently at
a merge of PR #270.

**Read its two agent files before doing anything that spans both repos** — they
are long, current, and not duplicated here:

- `~/ws/software/amadeus/CLAUDE.md` — the strategic context: the NextGen plan
  v1.1 (`background/Amadeus_NextGen_Planning_v1_1.pdf`), objectives O-01…O-09
  (this schema is **O-02**), assumptions A-01…A-03 and constraints C-01…C-05
  cited by ID throughout `REPORT.md`, who the people are, the HEW/EnVar/amadeus
  three-layer framing, and the "amadeus ends at the geojoin" scope boundary that
  the no-`exposure`-in-any-name test enforces here.
- `~/ws/software/amadeus/AGENTS.md` — R package conventions: the dispatch
  pattern, file layout, testthat rules, and the five-step "adding a new dataset"
  recipe.

Nothing from this repo gets pushed there, and vice versa. That repo is a
stakeholder proposal surface, not Nico's.

### Two things live in the amadeus repo that this repo's work depends on

- `~/ws/software/amadeus/specs/2026-09-18-amadeus-data-model-design.md` — the
  durable design spec for this model. It is *there*, not in a `specs/` folder
  here. Design decisions land in that file.
- `~/ws/software/amadeus/schema/` — **the older, diverged draft of this very
  repo.** Same filenames (`REPORT.md`, `justfile`, `scripts/`, `examples/`), so
  it is easy to edit by mistake; a path starting `~/ws/software/amadeus/schema/`
  is almost always wrong. It is untracked and local-only. Retiring it is
  `issues/issue_retire_inrepo_schema_draft.md`.

### The coupling that the code actually checks

`Product` carries three slots naming amadeus functions, and they must resolve to
real definitions in `~/ws/software/amadeus/R/*.R`:

| Slot | Resolves to |
|---|---|
| `amadeus_dataset_name` | `download_<name> <- ` |
| `amadeus_process_covariate` | `process_<name> <- ` |
| `amadeus_calculate_covariate` | `calculate_<name> <- ` |

`amadeus` dispatches by string match on `dataset_name` inside the three wrapper
verbs (`download_data()` → `process_covariates()` → `calculate_covariates()`),
so a name can exist in a dispatch block without a function behind it — stage 4
of `scripts/import_external.py` distinguishes those two states. A catalog entry
ahead of the code is correct for a new dataset (`daymet` genuinely has no
`download_daymet`; `airnow` is P0-planned but unimplemented). The same check over
the *existing* catalog failing is a real defect.

That stage finds the sources at `$AMADEUS_REPO`, defaulting to
`~/ws/software/amadeus`. With neither present — CI, or any machine without the
checkout — it prints a **loud SKIP rather than reporting every function as
`NOT IMPLEMENTED`**, because those two states are otherwise indistinguishable
and the vacuous one reads as a plausible result.

Note `calculate_`, not `calc_`: amadeus has both prefixes in `R/`, and every
source named in the current examples uses the long form.

### Issue #249

[NIEHS/amadeus#249](https://github.com/NIEHS/amadeus/issues/249) is the
intensive-versus-extensive aggregation bug — `calculate_covariates()` defaults
to `fun = "mean"`, which silently corrupts every extensive variable. It is the
motivation for `VariableExtensivityEnum` being required on `CanonicalVariable`,
and the third of README's three claims.

## Commands

```bash
uv sync --group dev          # or: just install
just                         # list all recipes; the [amadeus] group is project-specific
just check                   # THE gate: compile + examples + DDL + load + integrity + pytest
just all                     # everything in the order REPORT.md presents it
```

Project-specific recipes live in `project.justfile`; the rest come from the
template's `justfile`. Note `just` cannot override an imported recipe
([just#2540](https://github.com/casey/just/issues/2540)), so names in the two
files must not collide.

| Need | Command |
|---|---|
| Schema compiles | `just compile` → `build/amadeus_merged.yaml` |
| Validate one document | `just validate FILE` |
| All examples behave (per-rule report) | `just test-examples` |
| Regenerate backend DDL | `just gen-sql` |
| Load both engines + 8 queries | `just load` (or `load-duckdb` / `load-sedonadb`) |
| Integrity checks in-engine | `just check-integrity [duckdb\|sedonadb]` |
| R validators + their test | `just test-r` (needs `Rscript`) |
| EnVar projection | `just export-envar` |
| External-import walkthrough | `just import-demo` |

Single test: `uv run python -m pytest tests/test_schema.py::test_no_boolean_participates_in_a_rule -v`.
Every script is runnable directly and is the real implementation —
`uv run python scripts/load_and_query.py --engine duckdb` — the pytest file is a
thin wrapper around them.

**`just lint` currently exits 1** on 159 linkml-lint *warnings* (zero errors),
mostly missing slot/enum descriptions. Not a gate; see
`issues/issue_lint_warnings_gate.md`.

**CI runs `just test`, not `just check`** (`.github/workflows/main.yaml`, Python
3.10–3.14). `just test` is the template's own recipe (`_test-schema`,
`_test-python`, `_test-examples` via `linkml-run-examples`); `just check` is the
richer project gate. Run `just check` locally before declaring work done.

## Architecture

### Source of truth and what is generated

Edit only `src/amadeus_schema/schema/*.yaml`. Everything else is regenerated:

- `project/`, `build/`, `tmp/`, `docs/elements/*.md` — git-ignored
  (`gen-project` artifacts; DDL, R validators, integrity SQL, merged YAML,
  load summaries)
- `src/amadeus_schema/datamodel/` — Python dataclasses + Pydantic. Generated but
  **not** ignored, so it is committed and drifts unless regenerated. `just
  gen-python` rewrites it, and `just test` runs that implicitly.

### Five modules, one validation root

`amadeus_schema.yaml` is the umbrella: it imports the five modules and defines
`AmadeusDatabase` (`tree_root: true`), the container every instance document and
every `linkml-validate -C AmadeusDatabase` call targets. Adding a class means
adding a container slot here too — the SQL loader derives its table list from
this class's slots, so a class not reachable from it is never loaded.

- `amadeus_common` — types, 27 enums, shared slots, and the EnVar/HEW
  reconciliation record
- `amadeus_catalog` — `DataSource → Product → ProductVariable → CanonicalVariable`,
  plus `GridDefinition` and `Asset`
- `amadeus_value` — abstract `AmbientValue` with four concrete shapes
  (`StationObservation`, `GridCellValue`, `AreaValue`, `HexCellValue`) and
  `VectorFeature`
- `amadeus_request` — `LocationSet → Location → ExtractionRequest → AmbientValueAtLocation`
- `amadeus_provenance` — `ToolRun`, `ProvenanceChain`

A slot's module must be reachable through the imports of every module that uses
it — `amadeus_provenance` imports only `amadeus_common`, which is why shared
slots like `materialization_mode` live there rather than in `amadeus_catalog`.

### Where each kind of constraint is enforced

This split is the repository's central design decision; do not move a check
without reading `REPORT.md` §2–3.

| Constraint | Enforced by |
|---|---|
| Structure, types, required, patterns, enums, single-object `rules:` | `linkml-validate` |
| Referential integrity, uniqueness, enum domains (set properties) | `scripts/gen_integrity_checks.py`, run in-engine |
| Cross-object checks spanning a join (e.g. aggregation vs extensivity) | `scripts/import_external.py` stage 3 / query planner |
| R-side runtime checks, no Python | generated `checkmate` validators |

SedonaDB enforces almost nothing (`CHECK`/`FOREIGN KEY` refused; `PRIMARY KEY`/
`UNIQUE` silently ignored; only `NOT NULL` holds), which is why the integrity
checks are generated queries rather than constraints.

### The DDL pipeline

`gen-sqltables` output is not executable on either engine. `scripts/gen_backend_ddl.py`
post-processes it: topological table ordering (FKs), `DATETIME`→`TIMESTAMP`,
FK stripping for SedonaDB, enum `CHECK` constraints, and a `*_geo` view per
table promoting WKT text to real geometry. `rules:` are deliberately *not*
translated to SQL.

**Geometry is typed, not named.** The DDL post-processor finds geometry columns
by the `WktLiteral` type. A geometry slot typed `string` silently gets no
geometry view, and a test guards `*_wkt` slots against it.

## LinkML pitfalls encoded as tests

`tests/test_schema.py` is half script-wrappers, half design invariants. The
invariants exist because the failures are silent:

- **A boolean cannot be a rule precondition.** `equals_string: "true"` compiles
  to the JSON string, never matches boolean `true`, and the rule never fires.
- **One `ABSENT` postcondition per rule.** Several collapse into a single
  negated `required: [a, b]` — "not both present", weaker than intended. Split
  into separate rules.
- `extensivity`, `units_ucum`, `standard_name` stay required on `CanonicalVariable`;
  every value class keeps `asset` and `processing_run` (objective O-02).
- **Nothing may be named "exposure."** `amadeus` ends at the geojoin and
  produces ambient values, not exposures. Enforced by a test over all class and
  slot names.

## Test data layout

- `tests/data/valid/` — must validate (one instance covering all four value shapes)
- `tests/data/invalid/` — 19 counter-examples, one per rule; each must be rejected
- `tests/data/problem/invalid/` — semantically wrong but asserted to **pass**,
  documenting what LinkML cannot express. Kept under `problem/` so the
  template's `linkml-run-examples` counter-example gate does not trip on them.
  Adding one here is an admission of a gap, not a workaround.

## Conventions

- Every slot with an upstream equivalent carries `exact_mappings` to EnVar or
  HEW; every enum extending an upstream one carries `annotations: extends` with
  the reason, so reconciliation is a list of decisions rather than a diff.
- Schema module docstrings carry the design rationale and are load-bearing
  documentation — update them with the model.
- The metadata in examples is real (sources, units, day boundaries, calendars,
  DOIs); the **values are illustrative**. Do not present numbers derived from
  them as measurements.
