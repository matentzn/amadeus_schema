#!/usr/bin/env python
"""Emit the integrity checks LinkML validation structurally cannot perform.

Measured, not assumed (see REPORT.md §3.3 and the tests in `tests/data/invalid/`):
`linkml-validate` accepts BOTH of these documents without complaint —

  * a `StationObservation` whose `product_variable` names an id that appears
    nowhere in the document; and
  * two `GridCellValue` rows identical on every slot of the `unique_keys`
    declared for that class.

Neither is a LinkML bug. A LinkML rule sees one object at a time, so
referential integrity and uniqueness are outside what it can express by
construction. They are *set* properties, and they need a query.

So: generate the queries. The FK graph and the `unique_keys` are already in the
generated DDL and in the schema, which means these checks cost nothing to
derive and stay correct as the schema changes.

Why not just rely on a database that enforces constraints? Because the engine
that will hold the data in production is SedonaDB, which enforces none of them
(`CHECK` and `FOREIGN KEY` refused outright; `PRIMARY KEY` and `UNIQUE` parse
and are silently ignored — only `NOT NULL` holds, via Arrow). Loading fixtures
into DuckDB proves the *fixtures* are sound; running these queries proves the
*data* is, in whatever engine actually holds it.

Emits three families:

  FK     an anti-join per foreign key            → rows pointing at nothing
  UNIQUE a GROUP BY … HAVING COUNT(*) > 1        → duplicate business keys
  ENUM   a NOT IN per enum-ranged column         → values outside the value set

Usage:
    python scripts/gen_integrity_checks.py                  > build/integrity.sql
    python scripts/gen_integrity_checks.py --run duckdb     # execute + report
    python scripts/gen_integrity_checks.py --run sedonadb
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from linkml_runtime import SchemaView

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "src" / "amadeus_schema" / "schema" / "amadeus_schema.yaml"
GENERIC_DDL = ROOT / "build" / "amadeus_generic.sql"
CONTAINER = "AmadeusDatabase"

CREATE_RE = re.compile(r'CREATE TABLE "(?P<name>[^"]+)" \((?P<body>.*?)\n\);', re.DOTALL)
FK_RE = re.compile(
    r'FOREIGN KEY\("?(?P<col>[^")]+)"?\) REFERENCES "(?P<target>[^"]+)" \("?(?P<tcol>[^")]+)"?\)'
)
UNIQUE_RE = re.compile(r"UNIQUE \((?P<cols>[^)]+)\)")


class Check:
    def __init__(self, kind: str, table: str, label: str, sql: str):
        self.kind, self.table, self.label, self.sql = kind, table, label, sql


def build_checks(sv: SchemaView) -> list[Check]:
    if not GENERIC_DDL.exists():
        sys.exit(f"{GENERIC_DDL} not found — run `just gen-sql-generic` first")
    ddl = GENERIC_DDL.read_text()
    checks: list[Check] = []

    for m in CREATE_RE.finditer(ddl):
        table, body = m.group("name"), m.group("body")
        if table == CONTAINER:
            continue

        # ── referential integrity ────────────────────────────────────────
        for fk in FK_RE.finditer(body):
            col, target, tcol = fk.group("col"), fk.group("target"), fk.group("tcol")
            if target == CONTAINER:
                continue
            checks.append(Check(
                "FK", table, f"{table}.{col} -> {target}.{tcol}",
                f'SELECT COUNT(*) AS n FROM "{table}" c\n'
                f'  LEFT JOIN "{target}" p ON c."{col}" = p."{tcol}"\n'
                f'  WHERE c."{col}" IS NOT NULL AND p."{tcol}" IS NULL'))

        # ── uniqueness ───────────────────────────────────────────────────
        for uq in UNIQUE_RE.finditer(body):
            cols = [c.strip().strip('"') for c in uq.group("cols").split(",")]
            # COALESCE every key column to a sentinel before grouping.
            # DataFusion's GROUP BY does NOT treat two NULLs as equal, so a
            # nullable key column silently puts every row in its own group and
            # the duplicate becomes invisible. Verified against sedonadb 0.4.1
            # with `vertical_level` NULL on both rows of a genuine duplicate.
            # Casting to VARCHAR keeps one expression valid for every type.
            sel = ", ".join(
                f"""COALESCE(CAST("{c}" AS VARCHAR), '\u2400NULL')""" for c in cols)
            checks.append(Check(
                "UNIQUE", table, f"{table} ({', '.join(cols)})",
                f'SELECT COUNT(*) AS n FROM (\n'
                f'  SELECT {sel} FROM "{table}"\n'
                f'  GROUP BY {sel} HAVING COUNT(*) > 1\n'
                f') d'))

    # ── enum domains (the CHECK constraints SedonaDB will not take) ──────
    for cls_name, cls in sv.all_classes().items():
        if cls.abstract or cls_name == CONTAINER:
            continue
        for slot in sv.class_induced_slots(cls_name):
            if slot.multivalued:
                continue
            e = sv.get_enum(slot.range) if slot.range else None
            if e is None:
                continue
            col = slot.alias or slot.name
            vals = ", ".join("'" + v.replace("'", "''") + "'"
                             for v in e.permissible_values)
            checks.append(Check(
                "ENUM", cls_name, f"{cls_name}.{col} in {slot.range}",
                f'SELECT COUNT(*) AS n FROM "{cls_name}"\n'
                f'  WHERE "{col}" IS NOT NULL AND "{col}" NOT IN ({vals})'))
    return checks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", choices=["duckdb", "sedonadb"],
                    help="execute the checks against a loaded instance")
    args = ap.parse_args()

    sv = SchemaView(str(SCHEMA))
    checks = build_checks(sv)

    if not args.run:
        print("-- Integrity checks LinkML cannot express: referential integrity,")
        print("-- uniqueness, and enum domains. Generated from the FK graph,")
        print("-- unique_keys and enum ranges. Every query must return n = 0.")
        print(f"-- {len(checks)} checks\n")
        for c in checks:
            print(f"-- [{c.kind}] {c.label}")
            print(c.sql + ";\n")
        return 0

    # execute against a freshly loaded instance
    sys.path.insert(0, str(ROOT / "scripts"))
    import yaml
    from load_and_query import (DuckEngine, SedonaEngine, build_rows, order_tables)

    doc = yaml.safe_load(
        (ROOT / "tests" / "data" / "valid" / "AmadeusDatabase-durham_heat_aq_slice.yaml").read_text())
    tables, junctions = build_rows(sv, doc)

    ddl = ROOT / "build" / f"amadeus_{args.run}.sql"
    eng = (DuckEngine("DuckDB", ddl) if args.run == "duckdb"
           else SedonaEngine("SedonaDB", ddl))
    eng.connect()
    eng.create_schema()
    for tbl, rows in order_tables(tables, GENERIC_DDL):
        eng.insert(tbl, rows)
    for tbl, rows in junctions.items():
        eng.insert(tbl, rows)

    print("=" * 74)
    print(f"  Integrity checks — {eng.name}")
    print("=" * 74)
    by_kind: dict[str, list[int]] = {}
    failures = []
    for c in checks:
        try:
            _, rows = eng.fetch(c.sql)
            n = rows[0][0] if rows else 0
        except Exception as e:
            failures.append((c, f"query error: {str(e)[:90]}"))
            by_kind.setdefault(c.kind, [0, 0])[1] += 1
            continue
        k = by_kind.setdefault(c.kind, [0, 0])
        k[0] += 1
        if n:
            failures.append((c, f"{n} offending row(s)"))
            k[1] += 1

    for kind, (total, bad) in sorted(by_kind.items()):
        print(f"  {kind:<7} {total - bad:>3}/{total} clean")
    if failures:
        print(f"\n  {len(failures)} FAILED:")
        for c, why in failures[:12]:
            print(f"    [{c.kind}] {c.label} — {why}")
        return 1
    print(f"\n  All {len(checks)} checks clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
