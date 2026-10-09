#!/usr/bin/env python
"""Load the validated sample instance into DuckDB and SedonaDB, then query it.

This is the end-to-end test of the claim that LinkML can serve as the schema
interface for AmadeusDB:

    amadeus_schema.yaml  ──linkml-validate──▶  a document known to be well-formed
         │
         ├──gen-sqltables + gen_backend_ddl.py──▶  DDL both engines accept
         │
         └──this script──▶  rows in both engines, answering the same SQL

Nothing here is hardcoded per table. The container class's slots give the
table list, the SchemaView gives each table's columns and which are
multivalued, and the junction-table naming follows LinkML's own convention
(`<Class>_<slot>`). Adding a class to the schema is enough to get it loaded.

The queries at the end are the point. Q3 in particular is the spatial join
sketched in the modernization plan's own figure, executed against this schema
on both engines — the smallest honest answer to "would this work".
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml
from linkml_runtime import SchemaView

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "src" / "amadeus_schema" / "schema" / "amadeus_schema.yaml"
INSTANCE = (
    ROOT / "tests" / "data" / "valid" / "AmadeusDatabase-durham_heat_aq_slice.yaml"
)
CONTAINER = "AmadeusDatabase"


# ──────────────────────────────────────────────────────────────────────────────
# Turning the instance document into rows
# ──────────────────────────────────────────────────────────────────────────────


def build_rows(sv: SchemaView, doc: dict) -> tuple[dict, dict]:
    """Return ({table: [row, ...]}, {junction_table: [row, ...]})."""
    tables: dict[str, list[dict]] = {}
    junctions: dict[str, list[dict]] = {}

    container_slots = {s.name: s for s in sv.class_induced_slots(CONTAINER)}

    for coll_name, payload in doc.items():
        slot = container_slots.get(coll_name)
        if slot is None or not slot.multivalued:
            continue  # schema_version and friends
        cls = slot.range
        if cls not in sv.all_classes():
            continue
        induced = {s.alias or s.name: s for s in sv.class_induced_slots(cls)}
        rows, jrows = [], {}

        for obj in payload:
            row, inline = {}, {}
            for key, val in obj.items():
                s = induced.get(key)
                if s is None:
                    continue
                if s.multivalued:
                    # LinkML's junction convention: <Class>_<slot>, with a
                    # backref column <Class>_id and a value column named after
                    # the slot (+ "_id" when the range is another class).
                    jt = f"{cls}_{key}"
                    suffix = "_id" if s.range in sv.all_classes() else ""
                    jrows.setdefault(jt, []).extend(
                        {f"{cls}_id": obj["id"], f"{key}{suffix}": v} for v in val
                    )
                elif s.range in sv.all_classes() and s.inlined:
                    # An inlined object (OmopConceptBinding) becomes its own row
                    # with a synthetic integer key, which is what the generator's
                    # DDL expects.
                    inline[key] = (s.range, val)
                else:
                    row[key] = val

            for key, (rng, val) in inline.items():
                sub = dict(val)
                sub["id"] = len(tables.setdefault(rng, [])) + 1
                tables[rng].append(sub)
                # The generator names the FK column for an inlined object
                # `<slot>_id`, not `<slot>`.
                row[f"{key}_id"] = sub["id"]

            rows.append(row)

        tables.setdefault(cls, []).extend(rows)
        for jt, jr in jrows.items():
            junctions.setdefault(jt, []).extend(jr)

    return tables, junctions


# ──────────────────────────────────────────────────────────────────────────────
# Engines
# ──────────────────────────────────────────────────────────────────────────────


def order_tables(tables: dict, generic_ddl: Path) -> list[tuple[str, list[dict]]]:
    """Insert in foreign-key dependency order.

    The instance document's collection order happens to be safe today, but
    relying on the order someone wrote a YAML file in is not a loader.
    """
    ddl = generic_ddl.read_text()
    refs: dict[str, set[str]] = {}
    for m in re.finditer(r'CREATE TABLE "([^"]+)" \((.*?)\n\);', ddl, re.DOTALL):
        name, body = m.group(1), m.group(2)
        refs[name] = {t for t in re.findall(r'REFERENCES "([^"]+)"', body) if t != name}
    ordered, done = [], set()
    pending = dict(tables)
    while pending:
        progress = False
        for name in list(pending):
            if (
                refs.get(name, set()) - done - {n for n in refs if n not in tables}
                <= done
            ):
                ordered.append((name, pending.pop(name)))
                done.add(name)
                progress = True
        if not progress:
            ordered.extend(pending.items())
            break
    return ordered


def split_statements(ddl: str) -> list[str]:
    out = []
    for chunk in ddl.split(";"):
        body = "\n".join(
            ln for ln in chunk.split("\n") if not ln.strip().startswith("--")
        )
        body = body.strip()
        if body and re.match(r"(?is)^(CREATE|INSTALL|LOAD)", body):
            out.append(body)
    return out


def sql_literal(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


class Engine:
    def __init__(self, name: str, ddl_path: Path):
        self.name = name
        self.ddl_path = ddl_path
        self.conn = None

    def connect(self):
        raise NotImplementedError

    def exec(self, sql: str):
        raise NotImplementedError

    def fetch(self, sql: str) -> tuple[list[str], list[tuple]]:
        raise NotImplementedError

    def create_schema(self) -> tuple[int, list[str]]:
        ok, errs = 0, []
        for s in split_statements(self.ddl_path.read_text()):
            try:
                self.exec(s)
                ok += 1
            except Exception as e:
                errs.append(f"{s.split(chr(34))[1] if chr(34) in s else s[:30]}: {e}")
        return ok, errs

    def insert(self, table: str, rows: list[dict]) -> tuple[int, list[str]]:
        n, errs = 0, []
        for r in rows:
            cols = ", ".join(f'"{c}"' for c in r)
            vals = ", ".join(sql_literal(v) for v in r.values())
            try:
                self.exec(f'INSERT INTO "{table}" ({cols}) VALUES ({vals})')
                n += 1
            except Exception as e:
                errs.append(f"{table}: {str(e)[:170]}")
        return n, errs


class DuckEngine(Engine):
    def connect(self):
        import duckdb

        self.conn = duckdb.connect(":memory:")
        try:
            self.conn.execute("INSTALL spatial;")
            self.conn.execute("LOAD spatial;")
            self.spatial = True
        except Exception as e:
            self.spatial = False
            print(
                f"  ! DuckDB spatial extension unavailable ({str(e)[:70]}); "
                "spatial queries will be skipped"
            )

    def exec(self, sql):
        return self.conn.execute(sql)

    def fetch(self, sql):
        cur = self.conn.execute(sql)
        return [d[0] for d in cur.description], cur.fetchall()


class SedonaEngine(Engine):
    def connect(self):
        import sedonadb

        self.conn = sedonadb.connect()
        self.spatial = True

    def exec(self, sql):
        r = self.conn.sql(sql)
        # DataFusion is lazy: a DML statement is not executed until the result
        # is consumed. Without this, every INSERT silently does nothing.
        try:
            r.to_arrow_table()
        except Exception:
            pass
        return r

    def fetch(self, sql):
        tbl = self.conn.sql(sql).to_arrow_table()
        cols = tbl.column_names
        rows = list(zip(*[c.to_pylist() for c in tbl.columns])) if cols else []
        return cols, rows


# ──────────────────────────────────────────────────────────────────────────────
# The queries
# ──────────────────────────────────────────────────────────────────────────────

QUERIES: list[tuple[str, str, str, bool]] = [
    (
        "Q1",
        "Cross-source variable identity: which products deliver 'daily maximum "
        "air temperature', and on what terms?",
        """
        SELECT pv.native_name,
               p.name                    AS product,
               pv.native_units_ucum      AS native_unit,
               cv.units_ucum             AS canonical_unit,
               p.native_spatial_resolution_descriptor AS resolution,
               p.day_boundary_convention AS day_boundary
        FROM "ProductVariable" pv
        JOIN "Product" p            ON pv.product = p.id
        JOIN "CanonicalVariable" cv ON pv.canonical_variable = cv.id
        WHERE cv.name = 'air_temperature_daily_maximum'
        ORDER BY p.name
        """,
        False,
    ),
    (
        "Q2",
        "Extensivity guard: which aggregation did each request ask for, and is "
        "it legal for the variable?",
        """
        SELECT cv.name          AS variable,
               cv.extensivity,
               cv.default_aggregation_method AS declared_default,
               avl.aggregation_method        AS used,
               CASE
                 WHEN cv.extensivity = 'intensive'
                      AND avl.aggregation_method IN
                          ('mean','minimum','maximum','median','percentile',
                           'area_weighted_mean','population_weighted_mean','nearest')
                   THEN 'legal'
                 WHEN cv.extensivity = 'extensive'
                      AND avl.aggregation_method IN ('sum','count','cumulative','density')
                   THEN 'legal'
                 WHEN cv.extensivity = 'categorical'
                      AND avl.aggregation_method IN ('mode','class_proportion','nearest')
                   THEN 'legal'
                 WHEN avl.aggregation_method IS NULL THEN 'n/a (point extraction)'
                 ELSE 'ILLEGAL'
               END AS verdict
        FROM "AmbientValueAtLocation" avl
        JOIN "CanonicalVariable" cv ON avl.canonical_variable = cv.id
        ORDER BY cv.name
        """,
        False,
    ),
    (
        "Q3",
        "The modernization plan's own figure: user points joined to gridded "
        "values by spatial predicate, with distance.",
        """
        SELECT l.location_key,
               g.cell_x, g.cell_y,
               ROUND(g.value, 2) AS value_cel,
               ROUND(ST_Distance(l.location_geom, g.cell_centroid), 4) AS deg_from_point
        FROM "Location_geo" l
        JOIN "GridCellValue_geo" g
          ON ST_DWithin(l.location_geom, g.cell_centroid, 0.10)
        WHERE g.product_variable = 'amadeus:pvar/gridmet.tmmx'
        ORDER BY deg_from_point
        """,
        True,
    ),
    (
        "Q4",
        "Polygon membership: is the user's point inside a smoke plume on that day?",
        """
        SELECT l.location_key,
               a.area_name,
               a.quality_flag AS density_class,
               a.data_status
        FROM "Location_geo" l
        JOIN "AreaValue_geo" a
          ON ST_Contains(a.area_geom, l.location_geom)
        """,
        True,
    ),
    (
        "Q5",
        "The AQS/AirNow harmonization rule: both rows survive, and the "
        "superseded one names its replacement.",
        """
        SELECT source_system,
               data_status,
               ROUND(value, 1) AS value,
               valid_time_start,
               COALESCE(superseded_by, '-') AS superseded_by
        FROM "StationObservation"
        WHERE station_id = '37-063-0015'
        ORDER BY source_system, valid_time_start
        """,
        False,
    ),
    (
        "Q6",
        "Provenance: resolve an extracted value back to the bytes it came from "
        "(one row per consumed upstream run).",
        """
        SELECT avl.id                     AS extracted_value,
               r.function_name            AS produced_by,
               r.tool_version,
               up.upstream_runs           AS consumed_run,
               a.url                      AS source_url,
               a.sha256                   AS source_sha256,
               a.materialization_mode
        FROM "AmbientValueAtLocation" avl
        JOIN "ToolRun" r               ON avl.processing_run = r.id
        LEFT JOIN "ToolRun_upstream_runs" up ON up."ToolRun_id" = r.id
        JOIN "Asset" a                 ON avl.asset = a.id
        WHERE avl.id = 'amadeus:avl/durham-001-tmmx-20260714'
        """,
        False,
    ),
    (
        "Q7",
        "Asset-centric discovery: what is registered but NOT materialized, and "
        "what did knowing about it cost?",
        """
        SELECT a.id,
               p.name                  AS product,
               a.value_state,
               a.materialization_mode,
               r.bytes_transferred,
               r.request_count
        FROM "Asset" a
        JOIN "Product" p  ON a.product = p.id
        JOIN "ToolRun" r  ON a.produced_by_run = r.id
        WHERE a.value_state = 'registered_only'
        """,
        False,
    ),
    (
        "Q8",
        "Hexification loss is visible: which hex cells are under-covered?",
        """
        SELECT h3_cell,
               h3_resolution,
               ROUND(value, 2)            AS value_cel,
               coverage_fraction,
               contributing_cell_count,
               COALESCE(quality_flag, '(none)') AS flag
        FROM "HexCellValue"
        ORDER BY coverage_fraction
        """,
        False,
    ),
]


def show(cols, rows, limit=12):
    if not rows:
        print("    (no rows)")
        return
    widths = [
        max(len(str(c)), *(len(str(r[i])) for r in rows[:limit]))
        for i, c in enumerate(cols)
    ]
    print("    " + " | ".join(str(c).ljust(w) for c, w in zip(cols, widths)))
    print("    " + "-+-".join("-" * w for w in widths))
    for r in rows[:limit]:
        print("    " + " | ".join(str(v).ljust(w) for v, w in zip(r, widths)))
    if len(rows) > limit:
        print(f"    ... {len(rows) - limit} more rows")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--engine", choices=["duckdb", "sedonadb", "both"], default="both")
    ap.add_argument(
        "--json-summary", type=Path, help="write a machine-readable summary"
    )
    args = ap.parse_args()

    print("Loading schema ...", flush=True)
    sv = SchemaView(str(SCHEMA))
    doc = yaml.safe_load(INSTANCE.read_text())
    tables, junctions = build_rows(sv, doc)
    total_rows = sum(len(v) for v in tables.values()) + sum(
        len(v) for v in junctions.values()
    )
    print(
        f"  {len(tables)} tables + {len(junctions)} junction tables, {total_rows} rows\n"
    )

    engines = []
    if args.engine in ("duckdb", "both"):
        engines.append(DuckEngine("DuckDB", ROOT / "build" / "amadeus_duckdb.sql"))
    if args.engine in ("sedonadb", "both"):
        engines.append(
            SedonaEngine("SedonaDB", ROOT / "build" / "amadeus_sedonadb.sql")
        )

    summary: dict = {"engines": {}}
    failed = False

    for eng in engines:
        print("=" * 78)
        print(f"  {eng.name}")
        print("=" * 78)
        eng.connect()

        n_ddl, ddl_errs = eng.create_schema()
        print(f"  DDL: {n_ddl} statements executed, {len(ddl_errs)} errors")
        for e in ddl_errs[:5]:
            print(f"    ! {e}")

        inserted, ins_errs = 0, []
        # tables in FK-dependency order, then junctions, so targets exist
        for tbl, rows in order_tables(tables, ROOT / "build" / "amadeus_generic.sql"):
            n, errs = eng.insert(tbl, rows)
            inserted += n
            ins_errs += errs
        for tbl, rows in junctions.items():
            n, errs = eng.insert(tbl, rows)
            inserted += n
            ins_errs += errs
        print(f"  INSERT: {inserted}/{total_rows} rows, {len(ins_errs)} errors")
        for e in ins_errs[:5]:
            print(f"    ! {e}")
        if ins_errs or ddl_errs:
            failed = True

        q_ok, q_fail = 0, 0
        for qid, title, sql, needs_spatial in QUERIES:
            print(f"\n  {qid}. {title}")
            if needs_spatial and not getattr(eng, "spatial", True):
                print("    (skipped: no spatial support in this engine build)")
                continue
            try:
                cols, rows = eng.fetch(sql)
                show(cols, rows)
                q_ok += 1
            except Exception as e:
                print(f"    QUERY FAILED: {type(e).__name__}: {str(e)[:220]}")
                q_fail += 1
                failed = True

        print()
        summary["engines"][eng.name] = {
            "ddl_statements": n_ddl,
            "ddl_errors": len(ddl_errs),
            "rows_inserted": inserted,
            "rows_expected": total_rows,
            "insert_errors": len(ins_errs),
            "queries_ok": q_ok,
            "queries_failed": q_fail,
        }

    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    for name, s in summary["engines"].items():
        print(
            f"  {name:10s} DDL {s['ddl_statements']:>3} ok/{s['ddl_errors']} err | "
            f"rows {s['rows_inserted']}/{s['rows_expected']} | "
            f"queries {s['queries_ok']} ok/{s['queries_failed']} failed"
        )

    if args.json_summary:
        args.json_summary.write_text(json.dumps(summary, indent=2))
        print(f"\n  summary written to {args.json_summary}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
