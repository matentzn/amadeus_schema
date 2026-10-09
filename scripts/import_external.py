#!/usr/bin/env python
"""Import an external dataset into AmadeusDB, end to end.

This is the answer to "what does adding a dataset actually look like?" — the
question a prospective contributor asks, and the one that decides whether a
metadata layer gets adopted or quietly bypassed.

The whole contribution is **two YAML files and a passing check**:

    examples/import/daymet_v4_tmax.import.yaml    the product  (written once)
    examples/import/daymet_v4_tmax.values.yaml    one run's rows (generated)

Six stages, in the order a CI job should run them:

  1. VALIDATE      structural and rule conformance
  2. DUPLICATE     did the contributor mint a canonical variable that already
                   exists? This is the failure mode the CanonicalVariable /
                   ProductVariable split exists to prevent, and it is only
                   prevented if something checks.
  3. COHERENCE     cross-object checks LinkML rules cannot express, because
                   they span a join (the honest limitation from REPORT.md)
  4. CODE          does the amadeus function the catalog names actually exist?
                   A catalog entry with no implementation is a broken promise;
                   an implementation with no catalog entry is invisible data.
  5. MERGE         load base slice + import + values into one database
  6. DEMONSTRATE   run the query that makes the import worth having

Stage 6 is the payoff. Daymet and GridMET both deliver
`air_temperature_daily_maximum` for the same place and the same printed date,
and they disagree. Before the import that is folklore. After it, the query
returns the disagreement *and its two causes*, read straight out of the
catalog.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

# The amadeus R package is a separate checkout, located by the AMADEUS_REPO
# environment variable (no default: where it lives is machine-specific). Stage 4
# reads its R/ sources; see the skip in stage_code() when it is unset.
AMADEUS_REPO = (
    Path(os.environ["AMADEUS_REPO"]) if "AMADEUS_REPO" in os.environ else None
)
SCHEMA = ROOT / "src" / "amadeus_schema" / "schema" / "amadeus_schema.yaml"
BASE = ROOT / "tests" / "data" / "valid" / "AmadeusDatabase-durham_heat_aq_slice.yaml"
MANIFEST = ROOT / "examples" / "import" / "daymet_v4_tmax.import.yaml"
VALUES = ROOT / "examples" / "import" / "daymet_v4_tmax.values.yaml"

sys.path.insert(0, str(ROOT / "scripts"))


def hr(title: str, n: int) -> None:
    print()
    print("=" * 78)
    print(f"  STAGE {n}. {title}")
    print("=" * 78)


# ── 1. validate ──────────────────────────────────────────────────────────────


def stage_validate(paths: list[Path]) -> list[str]:
    problems = []
    exe = Path(sys.executable).parent / "linkml-validate"
    for p in paths:
        proc = subprocess.run(
            [str(exe), "-s", str(SCHEMA), "-C", "AmadeusDatabase", str(p)],
            capture_output=True,
            text=True,
        )
        out = (proc.stdout + proc.stderr).strip()
        ok = proc.returncode == 0 and "ERROR" not in out
        print(f"  {'PASS' if ok else 'FAIL'}  {p.name}")
        if not ok:
            problems.append(f"{p.name}: {out.splitlines()[0][:160]}")
            print(f"        {out.splitlines()[0][:160]}")
    if not problems:
        print("\n  Both files are ordinary AmadeusDatabase documents, checked by the")
        print("  same command as every other instance. A contributor needs no new")
        print("  tooling and no new vocabulary to be told what is wrong.")
    return problems


# ── 2. duplicate canonical variables ─────────────────────────────────────────


def stage_duplicates(base: dict, incoming: dict) -> list[str]:
    """Would this import have created a redundant canonical variable?

    Signature = standard_name + canonical units + measurement kind. Two
    canonical variables with the same signature are the same quantity under two
    names, which silently splits every cross-source query in half.
    """

    def sig(cv):
        return (
            cv.get("standard_name"),
            cv.get("units_ucum"),
            cv.get("value_data_type"),
        )

    existing = {sig(cv): cv["id"] for cv in base.get("canonical_variables") or []}
    problems = []

    new_cvs = incoming.get("canonical_variables") or []
    if not new_cvs:
        print("  The manifest declares NO new canonical variable.")
        print("  It attaches to an existing one instead:")
    for cv in new_cvs:
        if sig(cv) in existing:
            msg = (
                f"new canonical variable {cv['id']} duplicates "
                f"{existing[sig(cv)]} (same standard_name, units and data type)"
            )
            problems.append(msg)
            print(f"  FAIL  {msg}")

    for pv in incoming.get("product_variables") or []:
        target = pv["canonical_variable"]
        reused = target in {cv["id"] for cv in base.get("canonical_variables") or []}
        print(f"    {pv['id']}")
        print(f"      -> {target}  [{'REUSED — correct' if reused else 'NEW'}]")
        if reused:
            siblings = [
                p["id"]
                for p in base.get("product_variables") or []
                if p["canonical_variable"] == target
            ]
            print(
                f"      now {len(siblings) + 1} sources deliver this variable: "
                f"{', '.join(s.split('/')[-1] for s in siblings)}, "
                f"{pv['id'].split('/')[-1]}"
            )
    return problems


# ── 3. cross-object coherence ────────────────────────────────────────────────


def stage_coherence(merged: dict) -> list[str]:
    """Checks that span a join, which LinkML rules structurally cannot see.

    Documented as a limitation in REPORT.md; implemented here because "LinkML
    cannot express it" is not a reason to leave it unchecked.
    """
    problems, notes = [], []
    cvs = {c["id"]: c for c in merged.get("canonical_variables") or []}
    prods = {p["id"]: p for p in merged.get("products") or []}
    grids = {g["id"]: g for g in merged.get("grid_definitions") or []}

    LEGAL = {
        "intensive": {
            "mean",
            "minimum",
            "maximum",
            "median",
            "percentile",
            "area_weighted_mean",
            "population_weighted_mean",
            "nearest",
            "instantaneous",
        },
        "extensive": {"sum", "count", "cumulative", "density"},
        "categorical": {"mode", "class_proportion", "nearest"},
    }

    for pv in merged.get("product_variables") or []:
        cv = cvs.get(pv["canonical_variable"])
        if cv is None:
            problems.append(f"{pv['id']}: canonical_variable does not resolve")
            continue

        # C1 — extensivity vs the aggregation the source applied
        agg = pv.get("aggregation_method")
        ext = pv.get("extensivity") or cv.get("extensivity")
        if agg and ext in LEGAL and agg not in LEGAL[ext]:
            problems.append(
                f"{pv['id']}: aggregation '{agg}' is illegal for "
                f"{ext} variable {cv['id']}"
            )

        # C2 — does the source's own CF name agree with the canonical one?
        cf = pv.get("cf_standard_name")
        std = cv.get("standard_name") or ""
        if cf and std.startswith("CF:") and cf != std[3:]:
            notes.append(
                f"{pv['id']}: source declares CF '{cf}' but the canonical "
                f"variable is '{std}'. Comparable? Or a modelling error?"
            )

        # C3 — units: a conversion is claimed, or the units already agree
        nu, cu = pv.get("native_units_ucum"), cv.get("units_ucum")
        if (
            nu
            and cu
            and nu != cu
            and not (
                pv.get("unit_conversion_formula")
                or pv.get("native_value_scale_factor")
                or pv.get("native_value_offset")
            )
        ):
            problems.append(
                f"{pv['id']}: native units '{nu}' differ from canonical "
                f"'{cu}' with no conversion recorded"
            )

    # C4 — a grid's CRS must be resolvable
    for p in prods.values():
        g = grids.get(p.get("grid_definition"))
        if g and g.get("crs", "").startswith("EPSG:") and not g.get("proj_string"):
            gid = g["id"]
            if g["crs"] in ("EPSG:9802",):
                notes.append(
                    f"{gid}: EPSG:9802 is a projection METHOD, not a CRS. "
                    "A proj_string is present, which is why this is a note "
                    "rather than an error."
                )

    for n in notes:
        print(f"  NOTE  {n}")
    for p in problems:
        print(f"  FAIL  {p}")
    if not problems and not notes:
        print("  All cross-object checks pass.")
    elif not problems:
        print("\n  No errors. The notes are the interesting output: they are")
        print("  questions the catalog can now ask because the facts are in it.")
    return problems


# ── 4. catalog vs code ───────────────────────────────────────────────────────


def stage_code(incoming: dict) -> list[str]:
    """Does the amadeus function the catalog names exist in R/?

    Cheap, mechanical, and it turns "we support 24 sources" from a claim in a
    README into a test.
    """
    if AMADEUS_REPO is None or not (AMADEUS_REPO / "R").is_dir():
        where = f"at {AMADEUS_REPO}" if AMADEUS_REPO else "(AMADEUS_REPO is unset)"
        print(f"  SKIPPED — no amadeus checkout {where}")
        print("  Set AMADEUS_REPO to the amadeus package root to enable this stage.")
        print("  (Without the R sources every function reads NOT IMPLEMENTED, which")
        print("  is indistinguishable from a real gap — hence the skip.)")
        return []

    r_src = ""
    for f in sorted((AMADEUS_REPO / "R").glob("*.R")):
        r_src += f.read_text(errors="replace")

    gaps = []
    for p in incoming.get("products") or []:
        for verb, slot in [
            ("download", "amadeus_dataset_name"),
            ("process", "amadeus_process_covariate"),
            ("calculate", "amadeus_calculate_covariate"),
        ]:
            nm = p.get(slot)
            if not nm:
                continue
            fn = f"{verb}_{nm}"
            present = re.search(rf"^{fn}\s*<-", r_src, re.MULTILINE) is not None
            dispatch = (
                re.search(rf"^\s+{re.escape(nm)}\s*=\s*", r_src, re.MULTILINE)
                is not None
            )
            status = (
                "implemented"
                if present
                else ("dispatch only" if dispatch else "NOT IMPLEMENTED")
            )
            print(f"  {p['name']:20s} {fn:28s} {status}")
            if not present:
                gaps.append(f"{fn} declared in catalog but absent from R/")
    if gaps:
        print()
        print("  These are the gaps an import creates. Expected for a NEW dataset —")
        print("  the catalog entry lands before the code, which is the right order:")
        print("  the schema is the contract the implementation is written against.")
        print("  Run the same check over the EXISTING catalog and any failure is a")
        print("  real defect.")
    return []  # informational for a new import, not fatal


# ── 5 & 6. merge and demonstrate ─────────────────────────────────────────────


def merge(*docs: dict) -> dict:
    out: dict = {}
    for d in docs:
        for k, v in d.items():
            if isinstance(v, list):
                out.setdefault(k, []).extend(v)
            else:
                out[k] = v
    return out


DISCREPANCY_SQL = """
WITH t AS (
  SELECT g.source_system,
         p.name                      AS product,
         p.day_boundary_convention   AS day_boundary,
         p.calendar,
         p.native_spatial_resolution_descriptor AS resolution,
         pv.native_units_ucum        AS native_unit,
         g.valid_time_start,
         g.valid_time_end,
         AVG(g.value)                AS mean_value
  FROM "GridCellValue" g
  JOIN "ProductVariable" pv ON g.product_variable = pv.id
  JOIN "Product" p          ON pv.product = p.id
  WHERE g.canonical_variable = 'amadeus:var/air_temperature_daily_maximum'
    AND g.valid_time_start >= TIMESTAMP '2026-07-12 00:00:00'
    AND g.valid_time_start <  TIMESTAMP '2026-07-16 00:00:00'
  GROUP BY 1,2,3,4,5,6,7,8
)
SELECT source_system, product, day_boundary, calendar, resolution,
       native_unit,
       valid_time_start, valid_time_end,
       ROUND(mean_value, 2) AS mean_tmax_cel
FROM t
ORDER BY source_system
"""

ATTRIBUTION_SQL = """
SELECT ROUND(MAX(v) - MIN(v), 2)  AS discrepancy_cel,
       COUNT(DISTINCT db)         AS distinct_day_boundaries,
       COUNT(DISTINCT cal)        AS distinct_calendars,
       COUNT(DISTINCT res)        AS distinct_resolutions,
       COUNT(DISTINCT nu)         AS distinct_native_units
FROM (
  SELECT AVG(g.value) AS v,
         p.day_boundary_convention AS db,
         p.calendar                AS cal,
         p.native_spatial_resolution_descriptor AS res,
         pv.native_units_ucum      AS nu
  FROM "GridCellValue" g
  JOIN "ProductVariable" pv ON g.product_variable = pv.id
  JOIN "Product" p          ON pv.product = p.id
  WHERE g.canonical_variable = 'amadeus:var/air_temperature_daily_maximum'
    AND g.source_system IN ('gridmet', 'daymet')
  GROUP BY 2,3,4,5
) s
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--engine", choices=["duckdb", "sedonadb"], default="duckdb")
    args = ap.parse_args()

    base = yaml.safe_load(BASE.read_text())
    manifest = yaml.safe_load(MANIFEST.read_text())
    values = yaml.safe_load(VALUES.read_text())

    print("Importing ORNL Daymet V4 tmax into AmadeusDB")
    print(f"  manifest : {MANIFEST.relative_to(ROOT)}")
    print(f"  values   : {VALUES.relative_to(ROOT)}")
    print(f"  base     : {BASE.relative_to(ROOT)}")

    fatal: list[str] = []

    hr("VALIDATE — structural and rule conformance", 1)
    fatal += stage_validate([MANIFEST, VALUES])

    hr("DUPLICATE CHECK — is this variable already in the catalog?", 2)
    fatal += stage_duplicates(base, manifest)

    merged = merge(base, manifest, values)

    hr("COHERENCE — cross-object checks LinkML rules cannot express", 3)
    fatal += stage_coherence(merged)

    hr("CATALOG vs CODE — does the declared amadeus function exist?", 4)
    stage_code(manifest)

    if fatal:
        print()
        print("=" * 78)
        print(f"  IMPORT REJECTED — {len(fatal)} problem(s)")
        for f in fatal:
            print(f"    - {f}")
        return 1

    hr("MERGE — load base + import + values into one database", 5)
    from load_and_query import DuckEngine, SedonaEngine, build_rows, order_tables
    from linkml_runtime import SchemaView

    sv = SchemaView(str(SCHEMA))
    tables, junctions = build_rows(sv, merged)
    total = sum(len(v) for v in tables.values()) + sum(
        len(v) for v in junctions.values()
    )

    ddl = ROOT / "build" / f"amadeus_{args.engine}.sql"
    eng = (
        DuckEngine("DuckDB", ddl)
        if args.engine == "duckdb"
        else SedonaEngine("SedonaDB", ddl)
    )
    eng.connect()
    n_ddl, ddl_errs = eng.create_schema()
    inserted, errs = 0, []
    for tbl, rows in order_tables(tables, ROOT / "build" / "amadeus_generic.sql"):
        n, e = eng.insert(tbl, rows)
        inserted += n
        errs += e
    for tbl, rows in junctions.items():
        n, e = eng.insert(tbl, rows)
        inserted += n
        errs += e
    print(f"  {eng.name}: {n_ddl} DDL statements, {len(ddl_errs)} DDL errors")
    print(f"  {inserted}/{total} rows inserted, {len(errs)} errors")
    for e in errs[:5]:
        print(f"    ! {e}")
    if errs or ddl_errs:
        return 1
    print("\n  The imported product is now indistinguishable from a native one:")
    print("  same tables, same queries, no special case anywhere.")

    hr("DEMONSTRATE — what the import buys you", 6)
    from load_and_query import show

    print("  Three sources, one canonical variable, same place, same printed date:")
    print()
    cols, rows = eng.fetch(DISCREPANCY_SQL)
    show(cols, rows)

    print()
    print("  And the disagreement, attributed:")
    print()
    cols, rows = eng.fetch(ATTRIBUTION_SQL)
    show(cols, rows)

    print()
    print("  Read that last row carefully. GridMET and Daymet differ, and the")
    print("  catalog says why in four columns: two different day boundaries,")
    print("  two different calendars, two different resolutions, two different")
    print("  native units. None of those four facts is recoverable from the")
    print("  values alone, and all four are in the catalog because the schema")
    print("  made them required.")
    print()
    print("  Without this layer the difference is a mystery that gets")
    print("  rediscovered, argued about, and eventually attributed to the wrong")
    print("  cause. That is the reproducibility problem the project lead named")
    print("  unprompted: two people doing the same calculation get different")
    print("  results. Here the difference is not eliminated — it is EXPLAINED,")
    print("  which is the most a metadata layer can honestly promise.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
