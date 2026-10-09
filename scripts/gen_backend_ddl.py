#!/usr/bin/env python
"""Turn LinkML's generic SQL DDL into DDL that DuckDB and SedonaDB will accept.

`gen-sqltables` gets you most of the way: it flattens `is_a` inheritance into
concrete tables, turns multivalued slots into junction tables, and emits primary
keys, foreign keys and `unique_keys`. What it does not do is produce DDL either
target engine will execute, and it drops two things the schema knows and SQL
could express.

Five gaps, measured 2026-09-18 against linkml 1.9.x / duckdb 1.5.5 /
sedonadb 0.4.1:

1. **No topological ordering.** Tables are emitted before the tables their
   foreign keys reference, so the very first `CREATE TABLE` with an FK fails on
   DuckDB. Fixed here by sorting on the FK graph.
2. **`DATETIME` is not a SedonaDB type.** Rewritten to `TIMESTAMP`.
3. **SedonaDB does not support foreign key constraints at all.** Stripped for
   that dialect; the relationships stay in the schema and are checked by
   `linkml-validate` instead.
4. **Enum permissible values do not become `CHECK` constraints.** The enum is
   enforced by LinkML validation and by nothing in the database. Emitted here.
5. **Geometry is text.** LinkML has no spatial type, and SedonaDB refuses a
   `GEOMETRY` column in `CREATE TABLE` (DuckDB's spatial extension accepts one,
   so text is the common denominator). Slots typed `WktLiteral` therefore land as
   `TEXT`; this script emits a companion `*_geo` view per table that promotes
   them to real geometry, which is what makes `ST_Intersects`, `ST_DWithin` and
   spatial joins work.

What is deliberately *not* fixed: the `rules:` blocks (preconditions /
postconditions). Some are expressible as `CHECK` constraints and some are not,
and a half-enforced rule set is worse than a clearly unenforced one — the rules
are validated at the LinkML layer, before data reaches the database. See
`REPORT.md`.

Usage:
    python scripts/gen_backend_ddl.py --dialect duckdb   > build/amadeus_duckdb.sql
    python scripts/gen_backend_ddl.py --dialect sedonadb > build/amadeus_sedonadb.sql
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from linkml_runtime import SchemaView

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCHEMA = ROOT / "src" / "amadeus_schema" / "schema" / "amadeus_schema.yaml"

# The tree-root container exists so a bundle can be validated as one document.
# It is not a table: it has no identity of its own, and the generator's
# auto-created `<Container>_id` back-reference column on every child table is
# pure noise in a database.
CONTAINER_CLASS = "AmadeusDatabase"

DEFAULT_SRID = 4326


# ──────────────────────────────────────────────────────────────────────────────
# Dialect profiles
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class Dialect:
    name: str
    type_map: dict[str, str] = field(default_factory=dict)
    foreign_keys: bool = True
    check_constraints: bool = True
    quote: str = '"'
    # How to lift a WKT text column to a geometry
    geom_expr: str = "ST_GeomFromText({col})"
    preamble: list[str] = field(default_factory=list)


DIALECTS = {
    "duckdb": Dialect(
        name="duckdb",
        type_map={"DATETIME": "TIMESTAMP"},
        foreign_keys=True,
        check_constraints=True,
        # DuckDB's spatial extension does not track SRID on the geometry value,
        # so there is nothing to set. The CRS stays an attribute of the row.
        geom_expr="ST_GeomFromText({col})",
        preamble=["INSTALL spatial;", "LOAD spatial;"],
    ),
    "sedonadb": Dialect(
        name="sedonadb",
        # SedonaError: Unsupported SQL type DATETIME
        type_map={"DATETIME": "TIMESTAMP"},
        # SedonaError: Foreign key constraints are not currently supported
        foreign_keys=False,
        # Not supported in CREATE TABLE as of 0.4.1
        check_constraints=False,
        # Sedona *does* carry SRID, and GeoParquet export fails without one
        # ("Can't write GeoParquet from null CRS"), so set it explicitly.
        geom_expr="ST_SetSRID(ST_GeomFromText({col}), {srid})",
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# Parsing the generic DDL
# ──────────────────────────────────────────────────────────────────────────────

CREATE_RE = re.compile(r'CREATE TABLE "(?P<name>[^"]+)" \((?P<body>.*?)\n\);', re.DOTALL)
FK_RE = re.compile(r'FOREIGN KEY\("?(?P<col>[^")]+)"?\) REFERENCES "(?P<target>[^"]+)"')


@dataclass
class Table:
    name: str
    body: str

    @property
    def lines(self) -> list[str]:
        return [ln.strip().rstrip(",") for ln in self.body.strip().split("\n") if ln.strip()]

    @property
    def references(self) -> set[str]:
        return {m.group("target") for m in FK_RE.finditer(self.body)}


def generate_generic_ddl() -> str:
    """Run LinkML's own generator. No arguments that change semantics."""
    out = subprocess.run(
        [sys.executable, "-m", "linkml.generators.sqltablegen",
         "--autogenerate_index", "false", str(SCHEMA)],
        capture_output=True, text=True, check=True,
    )
    return out.stdout


def parse_tables(ddl: str) -> list[Table]:
    return [Table(m.group("name"), m.group("body")) for m in CREATE_RE.finditer(ddl)]


def topo_sort(tables: list[Table]) -> list[Table]:
    """Order tables so every FK target is created before its referrer.

    Self-references and cycles are tolerated: a table whose remaining
    dependencies are all already-emitted or unresolvable is emitted anyway,
    which keeps the output deterministic rather than raising on a cycle we
    would then have to break by hand.
    """
    by_name = {t.name: t for t in tables}
    emitted: list[Table] = []
    done: set[str] = set()
    remaining = list(tables)
    while remaining:
        progress = False
        for t in list(remaining):
            deps = {d for d in t.references if d in by_name and d != t.name}
            if deps <= done:
                emitted.append(t)
                done.add(t.name)
                remaining.remove(t)
                progress = True
        if not progress:  # cycle — emit the rest in input order
            emitted.extend(remaining)
            break
    return emitted


# ──────────────────────────────────────────────────────────────────────────────
# Schema-driven facts
# ──────────────────────────────────────────────────────────────────────────────


def schema_facts(sv: SchemaView):
    """Collect, from the schema itself, what the DDL transform needs.

    Nothing here is hardcoded per table: geometry columns are found by the
    `WktLiteral` type, enum columns by the slot's range. Adding a geometry slot
    to the schema is enough to get it promoted in the views.
    """
    geom_cols: dict[str, list[str]] = {}
    enum_cols: dict[str, dict[str, list[str]]] = {}
    has_srid: dict[str, bool] = {}

    for cls_name, cls in sv.all_classes().items():
        if cls.abstract or cls_name == CONTAINER_CLASS:
            continue
        geoms, enums = [], {}
        srid = False
        for slot in sv.class_induced_slots(cls_name):
            if slot.multivalued:
                continue  # lands in a junction table
            rng = slot.range
            if rng == "WktLiteral":
                geoms.append(slot.alias or slot.name)
            elif rng == "srid":
                pass
            if (slot.alias or slot.name) == "srid":
                srid = True
            enum_def = sv.get_enum(rng) if rng else None
            if enum_def is not None:
                enums[slot.alias or slot.name] = list(enum_def.permissible_values.keys())
        if geoms:
            geom_cols[cls_name] = geoms
            has_srid[cls_name] = srid
        if enums:
            enum_cols[cls_name] = enums
    return geom_cols, enum_cols, has_srid


# ──────────────────────────────────────────────────────────────────────────────
# Rendering
# ──────────────────────────────────────────────────────────────────────────────


def render_table(t: Table, d: Dialect, enum_cols: dict) -> str:
    kept: list[str] = []
    for ln in t.lines:
        if ln.startswith("--"):
            continue
        # drop the container back-reference column and its FK
        if f'"{CONTAINER_CLASS}_id"' in ln:
            continue
        if ln.startswith("FOREIGN KEY"):
            m = FK_RE.match(ln)
            if not d.foreign_keys:
                continue
            if m and m.group("target") == CONTAINER_CLASS:
                continue
        for src, dst in d.type_map.items():
            ln = re.sub(rf"\b{src}\b", dst, ln)
        kept.append(ln)

    if d.check_constraints:
        for col, values in enum_cols.get(t.name, {}).items():
            # only constrain columns this table actually has
            if not any(re.match(rf'"?{re.escape(col)}"?\s', ln) for ln in kept):
                continue
            vals = ", ".join(f"'{v}'" for v in values)
            kept.append(f'CONSTRAINT "ck_{t.name}_{col}" CHECK ({col} IN ({vals}))')

    inner = ",\n\t".join(kept)
    return f'CREATE TABLE "{t.name}" (\n\t{inner}\n);'


def render_geometry_view(cls: str, cols: list[str], d: Dialect, srid_col: bool) -> str:
    """Promote WKT text columns to real geometry in a companion view.

    The view, not the table, is what spatial SQL should target. Keeping the base
    table pure text means it loads from CSV/Parquet without a spatial extension
    present, which matters for the "register, don't ingest" path.
    """
    srid = f"CAST(COALESCE(srid, {DEFAULT_SRID}) AS INTEGER)" if srid_col else str(DEFAULT_SRID)
    exprs = []
    for c in cols:
        geom_name = c[:-4] if c.endswith("_wkt") else f"{c}_geom"
        exprs.append(f"\t{d.geom_expr.format(col=c, srid=srid)} AS {geom_name}")
    body = ",\n".join(exprs)
    return (
        f'-- geometry promotion for {cls}: WKT text -> native geometry\n'
        f'CREATE OR REPLACE VIEW "{cls}_geo" AS\nSELECT\n\t*,\n{body}\nFROM "{cls}";'
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dialect", choices=sorted(DIALECTS), required=True)
    ap.add_argument("--no-views", action="store_true", help="omit geometry views")
    args = ap.parse_args()
    d = DIALECTS[args.dialect]

    sv = SchemaView(str(SCHEMA))
    geom_cols, enum_cols, has_srid = schema_facts(sv)

    tables = [t for t in parse_tables(generate_generic_ddl()) if t.name != CONTAINER_CLASS]
    tables = topo_sort(tables)

    out: list[str] = [
        f"-- AmadeusDB DDL — dialect: {d.name}",
        f"-- Generated from {SCHEMA.name} via linkml gen-sqltables + scripts/gen_backend_ddl.py",
        f"-- {len(tables)} tables, {len(geom_cols)} geometry views",
        "",
    ]
    out += d.preamble + ([""] if d.preamble else [])
    out += [render_table(t, d, enum_cols) + "\n" for t in tables]

    if not args.no_views:
        out.append("")
        out.append("-- " + "=" * 74)
        out.append("-- Geometry views. LinkML has no spatial type, and SedonaDB refuses a")
        out.append("-- GEOMETRY column in CREATE TABLE, so `WktLiteral` slots are stored as text")
        out.append("-- and promoted here. Query the views, load the tables.")
        out.append("-- " + "=" * 74)
        out.append("")
        for cls, cols in sorted(geom_cols.items()):
            out.append(render_geometry_view(cls, cols, d, has_srid.get(cls, False)) + "\n")

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
