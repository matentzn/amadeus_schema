<a href="https://github.com/linkml/linkml-project-copier"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-teal.json" alt="Copier Badge" style="max-width:100%;"/></a>

# amadeus-schema — a LinkML data model for AmadeusDB

A candidate data model for the database-backed, next-generation `amadeus`,
built for the **Database and Schema** item on the Amadeus Next-Generation
Maintenance and Modernization agenda (v1.0, 2026-09-18) and for objective
**O-02**, "implement an EnVar/HEW aligned schema".

**This is a proposal for discussion, not a change to the R package.** It is a
standalone repository and adds no dependency to `amadeus` itself.

- **[REPORT.md](REPORT.md)** — can LinkML machinery actually serve as the
  schema interface? Measured findings, what broke, and the SedonaDB/DuckDB
  comparison. **Read this if you only read one thing.**

```bash
uv sync --group dev   # or: just install
just check            # the CI gate
just all              # everything, in the order REPORT.md presents it
```

---

## The model in one screen

```
CATALOG — what exists and what it means (small, curated)
  DataSource ──▶ Product ──▶ ProductVariable ──▶ CanonicalVariable
                   │  │                             ▲
                   │  └──▶ GridDefinition           │ four sources, one variable
                   └──▶ Asset (bytes, hash, STAC, materialization mode)

VALUES — the data rows (large, machine-written)
  AmbientValue (abstract)
    ├─ StationObservation   point + persistent instrument identity
    ├─ GridCellValue        grid + integer cell index (+ level)
    ├─ AreaValue            polygon with an identity
    └─ HexCellValue         H3 cell, with its coverage loss recorded
  VectorFeature             reference geometry, NOT a value

REQUEST — the query-first contract
  LocationSet ──▶ Location ──▶ ExtractionRequest ──▶ AmbientValueAtLocation

PROVENANCE — the derivation DAG
  ToolRun (download | process | calculate | register | harmonize | import)
  ProvenanceChain
```

Five modules under `src/amadeus_schema/schema/`: `amadeus_common`,
`amadeus_catalog`, `amadeus_value`, `amadeus_request`, `amadeus_provenance`,
with `amadeus_schema.yaml` as the umbrella and validation root.

## Three claims it makes

**1. One schema, not one per source type.** The 24 amadeus sources vary on five
orthogonal axes recorded on `Product` and `CanonicalVariable` — spatial
support, temporal resolution, value kind, native format, extensivity — and on
exactly one axis that needs a different table: *what geometry identifies a
value*. Four value tables cover all of them. An AQS monitor and a MODIS swath
are not structurally different; they hold different values on those axes.

**2. `CanonicalVariable` ← `ProductVariable` answers the actual question.**

> *"When we write a function for a variable — what is the schema for that
> variable, and is it the same as the schema for the same variable from another
> data source?"* — the project lead, 2026-09-09

Same at the canonical level; different at the product level; and every reason
for the difference is a slot. `gridmet.tmmx` (Kelvin, 4 km, day ending 12:00
GMT), `prism.tmax` (Celsius, 800 m, local midnight) and `daymet.tmax`
(Celsius, 1 km, local midnight, **365-day calendar**) are three deliveries of
one `air_temperature_daily_maximum`: comparable, not interchangeable.

**3. Extensivity makes aggregation checkable.** `VariableExtensivityEnum`
(intensive / extensive / categorical) is a precondition on which aggregations
are legal. Averaging a population count over a buffer is a silent,
plausible-looking error; `amadeus`'s current default `fun = "mean"` commits it
for every extensive variable. Tracked as [#249](https://github.com/NIEHS/amadeus/issues/249).

## Results

Run `just check`. Current state:

```
schema compiles                                       OK
examples: 1 valid pass, 19/20 invalid rejected        OK   (20th inexpressible, asserted)
DuckDB    DDL 42 ok/0 err | rows 121/121 | queries 8 ok/0 failed
SedonaDB  DDL 40 ok/0 err | rows 121/121 | queries 8 ok/0 failed
integrity 102/102 checks clean
```

Both engines return **identical results** on all eight queries, including the
spatial joins — which is the evidence that a single generated schema can serve
both backends.

## Where it sits relative to HEW and EnVar

| Layer | Grain | Question | Owner |
|---|---|---|---|
| **HEW Catalog** | dataset | what datasets exist? | Mike Conway, NIEHS |
| **AmadeusDB** | row | the values themselves | this schema |
| **EnVar** | run | what does this number mean, and where from? | Monarch / EnVar |

Designed to project to both, not to replace either. Every slot with an upstream
equivalent carries `exact_mappings`; every enum that extends an upstream one
carries `annotations: extends` with the reason, so enum reconciliation is a
finite list of decisions rather than a diff.

`just export-envar` demonstrates the EnVar direction end to end.

## Caveat on the numbers

The **metadata** in the examples is real — sources, products, units, day
boundaries, calendars, resolutions, DOIs, citations were taken from the actual
products. The **values** are illustrative. The 1.18 °C GridMET-versus-Daymet
difference `just import-demo` prints comes from plausible invented cell values,
not from downloading the files; it is the right order of magnitude (literature
gives ~1.26 °C for this comparison) and it demonstrates the mechanism, but it is
not a measurement.

## Documentation Website

[https://NIEHS.github.io/amadeus-schema](https://NIEHS.github.io/amadeus-schema)

## Repository Structure

* [docs/](docs/) - mkdocs-managed documentation
  * [elements/](docs/elements/) - generated schema documentation
* [examples/](examples/) - example usage
  * [import/](examples/import/) - the ORNL Daymet V4 import manifest and values
* [project/](project/) - project files (these files are auto-generated, do not edit)
* [scripts/](scripts/) - schema-specific tooling (backend DDL, R validators,
  integrity checks, EnVar export, external import)
* [src/](src/) - source files (edit these)
  * [amadeus_schema](src/amadeus_schema)
    * [schema/](src/amadeus_schema/schema) -- LinkML schema (edit this)
    * [datamodel/](src/amadeus_schema/datamodel) -- generated Python datamodel
* [tests/](tests/) - Python tests
  * [data/valid/](tests/data/valid) - one complete instance, all four value shapes
  * [data/invalid/](tests/data/invalid) - 19 counter-examples, one per rule
  * [data/problem/invalid/](tests/data/problem/invalid) - constraints LinkML
    cannot express, asserted to pass so the gap stays visible

## Developer Tools

There are several pre-defined command-recipes available.
They are written for the command runner [just](https://github.com/casey/just/).
To list all pre-defined commands, run `just` or `just --list`.

The recipes in the `[amadeus]` group are specific to this schema and live in
[project.justfile](project.justfile); the rest come from the project template.

## Credits

This project uses the template [linkml-project-copier](https://github.com/linkml/linkml-project-copier).
