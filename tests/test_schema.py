"""Regression tests for the AmadeusDB schema.

Deliberately thin wrappers around the scripts, plus a handful of assertions
about *design invariants* that a future edit could quietly break. The scripts
are the real work; these make them fail a build.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from linkml_runtime import SchemaView

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "src" / "amadeus_schema" / "schema" / "amadeus_schema.yaml"
BUILD = ROOT / "build"
BUILD.mkdir(exist_ok=True)
PY = sys.executable


@pytest.fixture(scope="session")
def sv() -> SchemaView:
    return SchemaView(str(SCHEMA))


@pytest.fixture(scope="session", autouse=True)
def generated_ddl() -> None:
    """Generate the SQL the engine tests load, before any of them run.

    Four tests read `build/*.sql`. Those files are produced by `just gen-sql`
    and `build/` is gitignored, so on a clean checkout they do not exist — which
    is exactly what CI is. `just check` happens to generate them first and
    `just test` does not, so the suite passed locally off leftover state and
    failed the moment it ran anywhere clean.

    Generating them here makes `pytest` self-sufficient: the suite is correct
    run on its own, by `just test`, or by CI, with no ordering assumption.
    """
    subprocess.run(
        [PY, "-m", "linkml.generators.sqltablegen",
         "--autogenerate_index", "false", str(SCHEMA)],
        stdout=(BUILD / "amadeus_generic.sql").open("w"),
        check=True,
        cwd=ROOT,
    )
    for dialect in ("duckdb", "sedonadb"):
        subprocess.run(
            [PY, str(ROOT / "scripts" / "gen_backend_ddl.py"), "--dialect", dialect],
            stdout=(BUILD / f"amadeus_{dialect}.sql").open("w"),
            check=True,
            cwd=ROOT,
        )


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, str(ROOT / "scripts" / script), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


# ── the scripts must pass ────────────────────────────────────────────────────


def test_examples_behave_as_expected():
    """Valid examples validate; invalid ones are rejected for the right reason."""
    p = run("validate_examples.py")
    assert p.returncode == 0, p.stdout + p.stderr


@pytest.mark.parametrize("engine", ["duckdb", "sedonadb"])
def test_engine_round_trip(engine: str):
    """DDL executes, all rows load, all demonstration queries answer."""
    p = run("load_and_query.py", "--engine", engine)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "queries 8 ok/0 failed" in p.stdout


def test_envar_record_is_valid():
    """The projected EnVar record validates against the canonical schema."""
    p = run("export_envar_record.py", "--validate")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "RESULT: VALID" in p.stdout or "skipped" in p.stdout


def test_external_import_walkthrough():
    p = run("import_external.py")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "REUSED — correct" in p.stdout, (
        "Daymet must reuse the existing canonical variable"
    )


def test_integrity_checks_pass_on_the_sample_data():
    """Referential integrity, uniqueness and enum domains — the three things
    `linkml-validate` structurally cannot check, verified in the engine."""
    p = run("gen_integrity_checks.py", "--run", "sedonadb")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "checks clean" in p.stdout


# ── design invariants ────────────────────────────────────────────────────────


def test_no_boolean_participates_in_a_rule(sv: SchemaView):
    """A boolean cannot be a rule precondition — LinkML compiles `equals_string:
    "true"` to the JSON string "true", which never matches boolean true, so the
    rule silently never fires. Guard the model against reintroducing one."""
    offenders = []
    for cls_name, cls in sv.all_classes().items():
        induced = {s.alias or s.name: s for s in sv.class_induced_slots(cls_name)}
        for rule in cls.rules or []:
            conds = getattr(rule.preconditions, "slot_conditions", {}) or {}
            for slot_name in conds:
                s = induced.get(slot_name)
                if s is not None and s.range == "boolean":
                    offenders.append(f"{cls_name}.{slot_name}")
    assert not offenders, (
        "boolean slots used as rule preconditions (the rule will never fire): "
        + ", ".join(offenders)
    )


def test_at_most_one_absent_postcondition_per_rule(sv: SchemaView):
    """Several ABSENT postconditions in one rule compile to a single negated
    `required: [a, b]`, i.e. "not BOTH present" — weaker than intended. Split
    into one rule per slot instead."""
    offenders = []
    for cls_name, cls in sv.all_classes().items():
        for i, rule in enumerate(cls.rules or []):
            conds = getattr(rule.postconditions, "slot_conditions", {}) or {}
            absents = [
                n
                for n, c in conds.items()
                if str(getattr(c, "value_presence", "")) == "ABSENT"
            ]
            if len(absents) > 1:
                offenders.append(f"{cls_name} rule[{i}]: {absents}")
    assert not offenders, (
        "rules with multiple ABSENT postconditions (weaker than intended): "
        + "; ".join(offenders)
    )


def test_every_value_class_carries_provenance(sv: SchemaView):
    """Objective O-02: every derived output must resolve to source assets and
    processing runs."""
    for cls in (
        "StationObservation",
        "GridCellValue",
        "AreaValue",
        "HexCellValue",
        "AmbientValueAtLocation",
    ):
        names = {s.alias or s.name for s in sv.class_induced_slots(cls)}
        assert "asset" in names, f"{cls} cannot resolve to its source bytes"
        assert "processing_run" in names, f"{cls} cannot resolve to its run"


def test_no_class_or_slot_is_named_exposure(sv: SchemaView):
    """amadeus ends at the geojoin: its outputs are ambient values, not
    exposures. Swap the person, keep the address — the number does not change.
    Guard the naming boundary, which is free to hold now and expensive to undo
    once downstream consumers depend on it."""
    bad = [n for n in sv.all_classes() if "exposure" in n.lower()]
    bad += [n for n in sv.all_slots() if "exposure" in n.lower()]
    assert not bad, (
        f"'exposure' names a person-level concept amadeus does not model: {bad}"
    )


def test_geometry_slots_use_the_wkt_type(sv: SchemaView):
    """The DDL post-processor finds geometry columns by the `WktLiteral` type,
    not by name. A geometry slot typed `string` gets no geometry view."""
    suspicious = [
        n
        for n, s in sv.all_slots().items()
        if n.endswith("_wkt") and s.range != "WktLiteral"
    ]
    assert not suspicious, f"*_wkt slots not typed WktLiteral: {suspicious}"


def test_canonical_variable_requires_extensivity(sv: SchemaView):
    """Extensivity is what makes aggregation checkable. It must not be optional."""
    slots = {s.alias or s.name: s for s in sv.class_induced_slots("CanonicalVariable")}
    assert slots["extensivity"].required, "extensivity must be required"
    assert slots["units_ucum"].required
    assert slots["standard_name"].required


def test_ambient_value_requires_status_and_source(sv: SchemaView):
    """The AQS/AirNow rule needs per-row status and source system, not per-dataset."""
    slots = {s.alias or s.name: s for s in sv.class_induced_slots("StationObservation")}
    assert slots["data_status"].required
    assert slots["source_system"].required
    assert slots["null_semantics"].required
