## AmadeusDB-specific recipes. Imported by the main (template) justfile.
##
## The template's own recipes cover the LinkML basics: `gen-project`, `gen-doc`,
## `test`, `lint`, `site`. What lives here is the machinery that is specific to
## this schema — SQL backends, R validators, integrity checks, and the two
## interoperability demonstrations.
##
## Overriding recipes from the root justfile by adding a recipe with the same
## name in this file is not possible until a known issue in just is fixed,
## https://github.com/casey/just/issues/2540

build := "build"

# ── validation ───────────────────────────────────────────────────────────────

# Compile the schema — catches import, range and syntax errors
[group('amadeus')]
compile:
    @mkdir -p {{build}}
    uv run gen-linkml --format yaml {{source_schema_path}} > {{build}}/amadeus_merged.yaml
    @echo "OK: schema compiles -> {{build}}/amadeus_merged.yaml"

# Validate one instance document against the schema
[group('amadeus')]
validate FILE:
    uv run linkml-validate -s {{source_schema_path}} -C AmadeusDatabase {{FILE}}

# Every example: examples/valid must pass, examples/invalid must be rejected
[group('amadeus')]
test-examples:
    uv run python scripts/validate_examples.py

# ── generation ───────────────────────────────────────────────────────────────

# Generic SQL DDL, straight from LinkML with no post-processing
[group('amadeus')]
gen-sql-generic: compile
    uv run gen-sqltables --autogenerate_index false {{source_schema_path}} \
        > {{build}}/amadeus_generic.sql
    @echo "tables: $(grep -c 'CREATE TABLE' {{build}}/amadeus_generic.sql)"

# Engine-specific DDL with geometry views and enum CHECK constraints
[group('amadeus')]
gen-sql: gen-sql-generic
    uv run python scripts/gen_backend_ddl.py --dialect duckdb   > {{build}}/amadeus_duckdb.sql
    uv run python scripts/gen_backend_ddl.py --dialect sedonadb > {{build}}/amadeus_sedonadb.sql
    @echo "OK: {{build}}/amadeus_duckdb.sql, {{build}}/amadeus_sedonadb.sql"

# JSON Schema (what linkml-validate actually enforces)
[group('amadeus')]
gen-jsonschema:
    @mkdir -p {{build}}
    uv run gen-json-schema {{source_schema_path}} > {{build}}/amadeus.schema.json

# R checkmate validators — the R-side contract, no Python at runtime
[group('amadeus')]
gen-r:
    @mkdir -p {{build}}
    uv run python scripts/gen_r_validators.py > {{build}}/amadeus_validators.R
    @echo "OK: {{build}}/amadeus_validators.R"

# Prove the generated R validators enforce the same rules as the LinkML schema
[group('amadeus')]
test-r: gen-r
    Rscript tests/test_r_validators.R

# Integrity checks LinkML structurally cannot express: referential integrity,
# uniqueness and enum domains
[group('amadeus')]
gen-integrity:
    @mkdir -p {{build}}
    uv run python scripts/gen_integrity_checks.py > {{build}}/integrity.sql
    @echo "OK: {{build}}/integrity.sql ($(grep -c '^-- \[' {{build}}/integrity.sql) checks)"

# Run them against a loaded instance
[group('amadeus')]
check-integrity ENGINE="sedonadb": gen-sql
    uv run python scripts/gen_integrity_checks.py --run {{ENGINE}}

# Everything this schema generates beyond the template's `gen-project`
[group('amadeus')]
gen-all: gen-sql gen-jsonschema gen-r gen-integrity

# ── databases ────────────────────────────────────────────────────────────────

# Load the sample instance into both engines and run the demonstration queries
[group('amadeus')]
load: gen-sql
    uv run python scripts/load_and_query.py --engine both \
        --json-summary {{build}}/load_summary.json

[group('amadeus')]
load-duckdb: gen-sql
    uv run python scripts/load_and_query.py --engine duckdb

[group('amadeus')]
load-sedonadb: gen-sql
    uv run python scripts/load_and_query.py --engine sedonadb

# ── interoperability ─────────────────────────────────────────────────────────

# Project AmadeusDB rows into an EnVar record and validate against EnVar
[group('amadeus')]
export-envar:
    uv run python scripts/export_envar_record.py --validate

# Walk through importing an external dataset (ORNL Daymet V4)
[group('amadeus')]
import-demo: gen-sql
    uv run python scripts/import_external.py --engine duckdb

# ── aggregate targets ────────────────────────────────────────────────────────

# The CI gate
[group('amadeus')]
check: compile test-examples gen-sql load check-integrity
    uv run python -m pytest tests/ -v
    @echo
    @echo "=============================================="
    @echo " All checks passed."
    @echo "=============================================="

# Everything, in the order REPORT.md presents it
[group('amadeus')]
all: compile test-examples gen-all load export-envar import-demo

# Remove generated artifacts
[group('amadeus')]
clean-build:
    rm -rf {{build}}
