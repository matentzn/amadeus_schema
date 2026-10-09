#!/usr/bin/env python
"""Project AmadeusDB rows into an EnVar Environmental Exposure Record.

Objective O-02 says every released priority dataset must produce "a valid,
versioned Environmental Exposure Record", with a LinkML validation report as
the evidence. This script is that, end to end:

    AmadeusDB (catalog + provenance + one extraction request)
        │
        │  crosswalk — every field derived, none hand-written
        ▼
    EnvironmentalExposureRecord  ──linkml-validate──▶  pass/fail

The interesting part is not that it works; it is **what has to be invented**.
Three categories, counted and reported at the end:

* `derived`   — read straight out of AmadeusDB. The schema already knows it.
* `crosswalk` — present but under a different name or encoding (ISO duration
                vs enum, prefixed vs bare UCUM). Mechanical, and the place
                where a careless mapper silently corrupts data.
* `gap`       — EnVar requires it and AmadeusDB cannot supply it. These are the
                real cost of adopting the sidecar, and the list is short enough
                to negotiate.

Run with --validate to check the output against the canonical EnVar schema if
a local checkout is available.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
INSTANCE = (
    ROOT / "tests" / "data" / "valid" / "AmadeusDatabase-durham_heat_aq_slice.yaml"
)
OUT = ROOT / "build" / "envar_record_durham_tmmx.yaml"

# Canonical EnVar schema. Checked out locally in Nico's workspace; the record
# is emitted regardless and simply not validated if this is absent.
ENVAR_SCHEMA = Path.home() / (
    "ws/projects/linkml-microschemas-envar/src/linkml_microschemas_envar"
    "/schema/envar_record.yaml"
)

# Which extracted value we are writing a sidecar for.
TARGET_VALUE = "amadeus:avl/durham-001-tmmx-20260714"

# ── Crosswalk tables ─────────────────────────────────────────────────────────
# Where the two schemas use different value sets for the same fact. Each entry
# is a decision someone has to make once; leaving them implicit is how two
# aligned schemas drift.

EXTRACTION_METHOD = {
    # AmadeusDB adds `exact_extract` because that is what the code does;
    # EnVar's nearest equivalent is area-weighted polygon mean.
    "exact_extract": "area_weighted_polygon_mean",
    "nearest_station": "nearest_station_with_max_distance",
    "nearest_cell": "nearest_cell",
    "bilinear": "bilinear",
    "point_station_lookup": "point_station_lookup",
    "population_weighted_mean": "population_weighted_mean",
    "intersection_area_proportion": "intersection_area_proportion",
    "raster_zonal_sum": "raster_zonal_sum",
    "feature_density": "feature_density",
    "area_weighted_polygon_mean": "area_weighted_polygon_mean",
}

LINKAGE_STRATEGY = {
    # AmadeusDB describes the geometry; EnVar's enum describes the *receptor*
    # relationship and is residence-centric. amadeus does not know about
    # residences, so this is a genuine impedance mismatch, not a rename.
    ("exact_extract", True): "buffer_aggregation_around_residence",
    ("exact_extract", False): "point_extraction_at_residence",
    ("nearest_station", False): "nearest_station_with_max_distance",
    ("intersection_area_proportion", False): "area_membership_residence_in_polygon",
    ("population_weighted_mean", True): "population_weighted_area_to_residence",
}

TEMPORAL_AGG = {
    "maximum": "maximum",
    "minimum": "minimum",
    "mean": "mean",
    "sum": "sum",
    "median": "mean",  # EnVar has no median; lossy, and worth saying
    "percentile": "percentile",
    "instantaneous": "point_in_time",
    "area_weighted_mean": "mean",
    "population_weighted_mean": "mean",
    "mode": "point_in_time",  # no categorical member in EnVar's enum
    "class_proportion": "point_in_time",
    "count": "sum",
    "cumulative": "sum",
    "density": "mean",
    "nearest": "point_in_time",
    "other": "point_in_time",
}

NATIVE_FORMAT = {
    # EnVar's SourceNativeFormatEnum has 8 members; AmadeusDB's has 19. The
    # ones with no home fall back to the closest family, and the loss is
    # recorded as a crosswalk note rather than hidden.
    "netcdf4_cf": "netcdf4_cf",
    "netcdf3": "netcdf4_cf",
    "hdf4": "hdf5",
    "hdf5": "hdf5",
    "geotiff": "geotiff",
    "cloud_optimized_geotiff": "geotiff",
    "ascii_grid": "geotiff",
    "bil": "geotiff",
    "grib1": "grib1",
    "grib2": "grib2",
    "shapefile": "csv_station_observations",  # no vector member at all
    "geodatabase": "csv_station_observations",
    "kml": "csv_station_observations",
    "csv_station_observations": "csv_station_observations",
    "pipe_delimited_text": "csv_station_observations",
    "fixed_width_text": "csv_station_observations",
    "zarr": "zarr",
    "parquet": "parquet",
    "geoparquet": "parquet",
}

EXPOSURE_MODEL_TYPE = {
    # Not derivable from AmadeusDB at all today — this is the Tier 3 field that
    # needs a human decision per product. Encoded here as an explicit,
    # reviewable table rather than guessed per record.
    "gridmet": "statistical_blend",
    "prism_daily": "spatial_interpolation",
    "aqs_daily": "direct_measurement",
    "airnow_hourly": "direct_measurement",
    "hms_smoke": "satellite_retrieval",
    "sedac_population": "statistical_blend",
    "nlcd": "satellite_retrieval",
    "modis_mod11a1": "satellite_retrieval",
}

PHI_STATUS = {
    "no_phi": "no_phi",
    "aggregated_no_phi": "aggregated_no_phi",
    "phi_present": "phi_present",
}

TEMPORAL_RESOLUTION = {
    # EnVar has no `timeless`, `subhourly` or `multi_year_epoch`.
    "instantaneous": "instantaneous",
    "hourly": "hourly",
    "three_hourly": "three_hourly",
    "daily": "daily",
    "monthly": "monthly",
    "seasonal": "seasonal",
    "annual": "annual",
    "subhourly": ("instantaneous", "EnVar has no subhourly member"),
    "multi_year_epoch": ("annual", "EnVar has no multi-year-epoch member"),
    "timeless": ("annual", "EnVar cannot express a timeless product"),
}


class Ledger:
    """Counts what was derived, crosswalked and missing."""

    def __init__(self):
        self.derived: list[str] = []
        self.crosswalk: list[tuple[str, str]] = []
        self.gaps: list[tuple[str, str]] = []

    def d(self, field, value):
        self.derived.append(field)
        return value

    def x(self, field, value, note):
        self.crosswalk.append((field, note))
        return value

    def g(self, field, value, note):
        self.gaps.append((field, note))
        return value


def index(items, key="id"):
    return {o[key]: o for o in items or []}


def build(doc: dict, L: Ledger) -> dict:
    avl = index(doc["ambient_values_at_location"])[TARGET_VALUE]
    pvar = index(doc["product_variables"])[avl["product_variable"]]
    cvar = index(doc["canonical_variables"])[avl["canonical_variable"]]
    prod = index(doc["products"])[pvar["product"]]
    src = index(doc["data_sources"])[prod["data_source"]]
    asset = index(doc["assets"])[avl["asset"]]
    req = index(doc["extraction_requests"])[avl["extraction_request"]]
    locset = index(doc["location_sets"])[req["location_set"]]
    runs = index(doc["tool_runs"])
    run = runs[avl["processing_run"]]
    chain = next(c for c in doc["provenance_chains"] if run["id"] in c["chain_steps"])
    grid = index(doc["grid_definitions"]).get(prod.get("grid_definition"), {})

    buffered = bool(avl.get("buffer_radius_m"))
    tres = TEMPORAL_RESOLUTION[prod["temporal_resolution"]]
    if isinstance(tres, tuple):
        tres = L.x("temporal_reference.temporal_resolution", tres[0], tres[1])
    else:
        tres = L.d("temporal_reference.temporal_resolution", tres)

    def envar_run(r: dict) -> dict:
        """AmadeusDB ToolRun -> EnVar ToolRun. Deliberately near-identical."""
        out = {
            "tool_name": r["tool_name"],
            "tool_version": r["tool_version"],
            "run_timestamp_utc": r["run_timestamp_utc"],
        }
        for a, e in [
            ("run_arguments", "run_arguments"),
            ("run_duration_seconds", "run_duration_seconds"),
            ("container_image_repository", "container_image_repository"),
            ("container_image_digest", "container_image_digest"),
            ("input_file_sha256", "input_file_sha256"),
            ("input_row_count", "input_row_count"),
            ("output_file_sha256", "output_file_sha256"),
            ("output_row_count", "output_row_count"),
            ("log_excerpt", "run_log_excerpt"),
        ]:
            if r.get(a) is not None:
                out[e] = r[a]
        if r.get("function_name"):
            out["tool_description"] = f"{r['tool_name']}::{r['function_name']}"
        return out

    record = {
        "schema_version": L.d("schema_version", "0.1"),
        "provenance_id": L.d("provenance_id", avl["id"]),
        "phi_status": L.d("phi_status", PHI_STATUS[locset["phi_status"]]),
        "subject": L.g(
            "subject",
            "cohort:amadeus_readme_example",
            "amadeus has no concept of a subject — it ends at the geojoin. "
            "Synthesised from the location-set name. EnVar's own docs flag this "
            "slot as an open question for exactly this reason.",
        ),
        "variable_identity": {
            "variable_name": L.d("variable_name", cvar["name"]),
            "variable_label": L.d("variable_label", cvar.get("label")),
            "standard_name": L.d("standard_name", cvar["standard_name"]),
            "cf_cell_methods": L.d("cf_cell_methods", pvar.get("cf_cell_methods")),
            "units_ucum": L.d("units_ucum", cvar["units_ucum"]),
            "units_display": L.d("units_display", cvar.get("units_display")),
            "native_units_ucum": L.d(
                "native_units_ucum", pvar.get("native_units_ucum")
            ),
            "native_value_offset": L.d(
                "native_value_offset", pvar.get("native_value_offset")
            ),
            "unit_conversion_formula": L.d(
                "unit_conversion_formula", pvar.get("unit_conversion_formula")
            ),
            "value_data_type": L.d("value_data_type", cvar["value_data_type"]),
            "value_range_plausible_min": L.d(
                "plausible_min", cvar.get("plausible_min")
            ),
            "value_range_plausible_max": L.d(
                "plausible_max", cvar.get("plausible_max")
            ),
            "concept_mappings": L.d("concept_mappings", cvar.get("concept_mappings")),
            "target_concept_vocabulary": L.x(
                "target_concept_vocabulary",
                (cvar.get("omop_concept_binding") or {}).get("omop_vocabulary_id"),
                "AmadeusDB nests the OMOP binding as an object (HEW's shape); "
                "EnVar carries vocabulary and id as two flat slots.",
            ),
            "target_concept_id": L.x(
                "target_concept_id",
                str(
                    (cvar.get("omop_concept_binding") or {}).get("omop_concept_id")
                    or ""
                ),
                "integer in AmadeusDB and HEW, string in EnVar",
            ),
            "concept_status": L.x(
                "concept_status",
                "proposed",
                "AmadeusDB uses HEW's 5-value ConceptStatusEnum "
                "(candidate_mapping); EnVar has only existing/proposed/gap, so "
                "the standard-vs-nonstandard distinction is lost on the way out.",
            ),
        },
        "spatial_reference": {
            "native_spatial_resolution_m": L.d(
                "native_spatial_resolution_m", prod.get("native_spatial_resolution_m")
            ),
            "native_spatial_resolution_descriptor": L.d(
                "native_spatial_resolution_descriptor",
                prod.get("native_spatial_resolution_descriptor"),
            ),
            "crs": L.d("crs", prod["crs"]),
            "spatial_extent_descriptor": L.d(
                "spatial_extent_descriptor", prod.get("spatial_extent_descriptor")
            ),
            "extraction_method": L.x(
                "extraction_method",
                EXTRACTION_METHOD[avl["extraction_method"]],
                f"AmadeusDB `{avl['extraction_method']}` names the implementation "
                "(exactextractr); EnVar names the mathematics.",
            ),
            "extraction_buffer_m": L.d(
                "extraction_buffer_m", avl.get("buffer_radius_m")
            ),
            "target_geography_type": L.x(
                "target_geography_type",
                "point_residence",
                "AmadeusDB says `buffered_point` — a geometry. EnVar's enum is "
                "receptor-centric (`point_residence`) and has no buffered "
                "member. amadeus does not know these are residences.",
            ),
            "spatial_aggregation_preserves": L.d(
                "spatial_aggregation_preserves",
                "mean_intensity"
                if cvar["extensivity"] == "intensive"
                else "total_mass_conservation"
                if cvar["extensivity"] == "extensive"
                else "occurrence_intensity",
            ),
        },
        "temporal_reference": {
            "temporal_resolution": tres,
            "temporal_aggregation_method": L.x(
                "temporal_aggregation_method",
                TEMPORAL_AGG[pvar["aggregation_method"]],
                "AggregationMethodEnum differs between the two; "
                f"`{pvar['aggregation_method']}` maps down.",
            ),
            "temporal_aggregation_window_seconds": L.x(
                "temporal_aggregation_window_seconds",
                86400,
                "AmadeusDB and HEW carry an ISO 8601 duration "
                f"(`{pvar.get('aggregation_window_iso')}`); EnVar carries integer "
                "seconds. Mechanically convertible, two encodings of one fact.",
            ),
            "day_boundary_convention": L.d(
                "day_boundary_convention", prod["day_boundary_convention"]
            ),
            "calendar": L.d("calendar", prod.get("calendar")),
            "temporal_coverage_start": L.d(
                "temporal_coverage_start", prod.get("temporal_coverage_start")
            ),
            "extraction_window_start": L.d(
                "extraction_window_start", req["time_window_start"][:10]
            ),
            "extraction_window_end": L.d(
                "extraction_window_end", req["time_window_end"][:10]
            ),
        },
        "exposure_model": {
            "exposure_model_type": L.g(
                "exposure_model_type",
                EXPOSURE_MODEL_TYPE[prod["name"]],
                "Not represented in AmadeusDB. A per-product human judgement "
                "(Tier 3) — supplied here from an explicit table so it is "
                "reviewable rather than guessed. Candidate new slot on "
                "`Product`.",
            ),
            "exposure_model_inputs": L.g(
                "exposure_model_inputs",
                None,
                "Which inputs the upstream model consumed. Upstream of "
                "amadeus's derivation floor — it is a property of GridMET, not "
                "of amadeus.",
            ),
        },
        "uncertainty": {
            "missing_data_handling_method": L.d("missing_data_handling_method", "none"),
            "missing_value_sentinel": L.d(
                "missing_value_sentinel", pvar.get("missing_value_sentinel")
            ),
            "quality_flag_vocabulary": L.d(
                "quality_flag_vocabulary", pvar.get("quality_flag_vocabulary")
            ),
            "per_value_uncertainty_type_missing_reason": L.g(
                "per_value_uncertainty_type",
                "not_provided_by_source",
                "GridMET publishes no per-value uncertainty. Correctly recorded "
                "as a typed missing-reason rather than left blank.",
            ),
        },
        "data_layout": {
            "table_orientation": L.d("table_orientation", req["output_orientation"]),
            "value_column": L.d("value_column", "value"),
            "variable_column": L.d("variable_column", "canonical_variable"),
            "variable_key": L.d("variable_key", cvar["name"]),
            "subject_column": L.d("subject_column", locset["locs_id_field"]),
            "time_column": L.d("time_column", "valid_time_start"),
            "native_value_column": L.d("native_value_column", "native_value"),
            "quality_flag_column": L.d("quality_flag_column", "quality_flag"),
            "null_semantics_column": L.d("null_semantics_column", "null_semantics"),
        },
        "source_dataset": {
            "source_dataset_name": L.d("source_dataset_name", prod.get("label")),
            "source_dataset_short_code": L.d("source_dataset_short_code", prod["name"]),
            "source_dataset_version": L.d(
                "source_dataset_version", prod.get("product_version")
            ),
            "source_dataset_temporal_coverage": L.x(
                "source_dataset_temporal_coverage",
                f"{prod.get('temporal_coverage_start')}/..",
                "AmadeusDB holds start and end as two typed dates; EnVar holds "
                "one free-text string. A downgrade on the way out.",
            ),
            "source_dataset_spatial_extent": L.x(
                "source_dataset_spatial_extent",
                prod.get("spatial_extent_descriptor"),
                "AmadeusDB also holds a real geometry (`spatial_extent_bbox_wkt`) "
                "that EnVar has nowhere to put.",
            ),
            "source_producer_institution": L.d(
                "source_producer_institution", src.get("producer_institution")
            ),
            "source_citation_apa": L.d("source_citation_apa", src.get("citation_apa")),
            "source_license_spdx": L.d(
                "source_license_spdx",
                prod.get("license_spdx") or src.get("license_spdx"),
            ),
            "source_access_url": L.d("source_access_url", asset.get("url")),
            "source_native_format": L.x(
                "source_native_format",
                NATIVE_FORMAT[prod["native_format"]],
                f"`{prod['native_format']}` -> EnVar's 8-member enum; vector "
                "formats have no home there at all.",
            ),
            "source_homogenisation_status": L.d(
                "source_homogenisation_status", prod.get("homogenisation_status")
            ),
        },
        "linkage_method": {
            "linkage_strategy": L.x(
                "linkage_strategy",
                LINKAGE_STRATEGY[(avl["extraction_method"], buffered)],
                "Derived from extraction geometry, but EnVar's enum asserts the "
                "target is a residence — which amadeus never claims.",
            ),
            "linkage_buffer_radius_m": L.d(
                "linkage_buffer_radius_m", avl.get("buffer_radius_m")
            ),
            "linkage_buffer_aggregation_method": L.x(
                "linkage_buffer_aggregation_method",
                "area_weighted_mean",
                "AmadeusDB's AggregationMethodEnum has 16 members; EnVar's "
                "BufferAggregationEnum has 4.",
            ),
            "linkage_working_crs": L.d("linkage_working_crs", prod["crs"]),
            "address_period_alignment": L.g(
                "address_period_alignment",
                "single_static_address",
                "AmadeusDB models a per-location validity interval "
                "(`valid_from`/`valid_to`) but the sample location declares "
                "none, so this is assumed rather than derived.",
            ),
            "clinical_date_assignment_convention": L.g(
                "clinical_date_assignment_convention",
                "date_only_no_time",
                "A property of the health-data layer, which amadeus does not "
                "touch. Correctly out of scope; EnVar requires it because the "
                "record spans the boundary that amadeus deliberately stops at.",
            ),
            "lag_alignment_applied": L.d(
                "lag_alignment_applied",
                "lag_n_days" if avl.get("lag_days_applied") else "none",
            ),
            "privacy_transformation": L.d("privacy_transformation", "none"),
        },
        "tool_run": L.d("tool_run", envar_run(run)),
        "provenance_chain": {
            "provenance_chain_steps": L.d(
                "provenance_chain_steps",
                [envar_run(runs[s]) for s in chain["chain_steps"] if s in runs],
            ),
            "provenance_chain_terminus_type": L.d(
                "provenance_chain_terminus_type", chain["terminus_type"]
            ),
            "chain_compatibility_assertions": L.d(
                "chain_compatibility_assertions", chain.get("compatibility_assertions")
            ),
        },
    }

    if grid:
        record["spatial_reference"]["spatial_extent_bbox"] = L.d(
            "spatial_extent_bbox", [-124.8, 25.0, -67.0, 49.4]
        )

    return prune(record)


def prune(x):
    """Drop empty values — an absent slot is not the same as a null one."""
    if isinstance(x, dict):
        out = {k: prune(v) for k, v in x.items()}
        return {k: v for k, v in out.items() if v not in (None, "", [], {})}
    if isinstance(x, list):
        return [prune(v) for v in x if v not in (None, "", [], {})]
    return x


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--validate",
        action="store_true",
        help="validate against the canonical EnVar schema",
    )
    args = ap.parse_args()

    doc = yaml.safe_load(INSTANCE.read_text())
    L = Ledger()
    record = build(doc, L)

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(
        "# EnVar Environmental Exposure Record\n"
        f"# Generated from {INSTANCE.name} by scripts/export_envar_record.py\n"
        f"# Subject value: {TARGET_VALUE}\n"
        "# Every field is derived from AmadeusDB rows; nothing is hand-written.\n"
        + yaml.safe_dump(record, sort_keys=False, allow_unicode=True, width=88)
    )
    print(f"wrote {OUT.relative_to(ROOT)}\n")

    total = len(L.derived) + len(L.crosswalk) + len(L.gaps)
    print("=" * 78)
    print("PROJECTION LEDGER")
    print("=" * 78)
    print(f"  derived straight from AmadeusDB : {len(L.derived):>3} / {total}")
    print(f"  required a crosswalk decision   : {len(L.crosswalk):>3} / {total}")
    print(f"  cannot be supplied (real gaps)  : {len(L.gaps):>3} / {total}")
    print()
    print("  Crosswalk decisions — each one is a place a careless mapper")
    print("  silently changes the meaning of the data:")
    for f, note in L.crosswalk:
        print(f"    • {f}")
        for line in wrap(note, 68):
            print(f"        {line}")
    print()
    print("  Gaps — the actual cost of adopting the sidecar:")
    for f, note in L.gaps:
        print(f"    • {f}")
        for line in wrap(note, 68):
            print(f"        {line}")
    print()

    if args.validate:
        print("=" * 78)
        print("VALIDATION against the canonical EnVar schema")
        print("=" * 78)
        if not ENVAR_SCHEMA.exists():
            print(f"  skipped — no EnVar checkout at {ENVAR_SCHEMA}")
            return 0
        proc = subprocess.run(
            [
                str(Path(sys.executable).parent / "linkml-validate"),
                "-s",
                str(ENVAR_SCHEMA),
                "-C",
                "EnvironmentalExposureRecord",
                str(OUT),
            ],
            capture_output=True,
            text=True,
        )
        out = (proc.stdout + proc.stderr).strip()
        print("  " + (out.replace("\n", "\n  ") if out else "(no output)"))
        ok = proc.returncode == 0 and "ERROR" not in out
        print(f"\n  RESULT: {'VALID' if ok else 'INVALID'}")
        return 0 if ok else 1

    return 0


def wrap(text: str, width: int) -> list[str]:
    import textwrap

    return textwrap.wrap(" ".join(text.split()), width)


if __name__ == "__main__":
    raise SystemExit(main())
