# Proof that the generated R validators enforce the same rules as the LinkML
# schema, in pure R with checkmate and no Python present.
#
# The invalid cases are the same ones in tests/data/invalid/, so if the two
# validators ever disagree, one of them is wrong and this fails.
#
# Run: just test-r   (or: Rscript tests/test_r_validators.R from schema/)

source("build/amadeus_validators.R")
cat("classes with validators:", length(amadeus_validators), "\n\n")

pass <- 0; fail <- 0
t <- function(label, expr_ok, res) {
  ok <- if (expr_ok) isTRUE(res) else !isTRUE(res)
  cat(sprintf("  %-4s %s\n", if (ok) "PASS" else "FAIL", label))
  if (!ok) cat("        got:", if (isTRUE(res)) "TRUE" else res, "\n")
  else if (!expr_ok) cat("        rejected:", res, "\n")
  if (ok) pass <<- pass + 1 else fail <<- fail + 1
}

cat("VALID records must pass\n")
t("gridmet Product (daily, gridded, day boundary declared)", TRUE, check_Product(list(
  id="amadeus:product/gridmet", name="gridmet", data_source="amadeus:source/cl",
  spatial_support_type="raster_grid_cell", grid_definition="amadeus:grid/g",
  temporal_resolution="daily", day_boundary_convention="ending_1200_gmt",
  native_format="netcdf4_cf", crs="EPSG:4326")))
t("CanonicalVariable (intensive, continuous)", TRUE, check_CanonicalVariable(list(
  id="amadeus:var/tmax", name="air_temperature_daily_maximum",
  standard_name="CF:air_temperature", units_ucum="Cel",
  value_data_type="continuous_numeric", extensivity="intensive",
  plausible_min=-70, plausible_max=60)))

cat("\nINVALID records must be rejected (same cases as tests/data/invalid/)\n")
t("01 daily product with no day_boundary_convention", FALSE, check_Product(list(
  id="x", name="p", data_source="s", spatial_support_type="monitoring_station",
  temporal_resolution="daily")))
t("02 gridded product with no grid_definition", FALSE, check_Product(list(
  id="x", name="p", data_source="s", spatial_support_type="raster_grid_cell",
  temporal_resolution="monthly")))
t("03 timeless product carrying temporal_coverage_start", FALSE, check_Product(list(
  id="x", name="p", data_source="s", spatial_support_type="polygon",
  temporal_resolution="timeless", temporal_coverage_start="2001-01-01")))
t("04 categorical variable with a numeric range", FALSE, check_CanonicalVariable(list(
  id="x", name="lc", standard_name="AMADEUS:lc", units_ucum="1",
  value_data_type="categorical", extensivity="categorical", plausible_min=0)))
t("05 categorical type, non-categorical extensivity", FALSE, check_CanonicalVariable(list(
  id="x", name="lc", standard_name="AMADEUS:lc", units_ucum="1",
  value_data_type="categorical", extensivity="intensive")))
t("11 hex under 50% coverage, unflagged", FALSE, check_HexCellValue(list(
  id="x", product_variable="pv", canonical_variable="cv", value=34.1,
  valid_time_start="2026-07-14T00:00:00Z", data_status="final",
  source_system="gridmet", null_semantics="present",
  h3_cell="8844c0a9245ffff", h3_resolution=8L, source_support_type="raster_grid_cell",
  hexification_method="area_weighted_mean", coverage_fraction=0.38)))
t("17 failed run with no log_excerpt", FALSE, check_ToolRun(list(
  id="x", run_role="download", tool_name="amadeus", tool_version="1.3.2.1",
  run_timestamp_utc="2026-07-16T04:00:02Z", status="failed")))
t("19a bad enum value", FALSE, check_DataSource(list(
  id="x", name="a", access_protocol="carrier_pigeon")))
t("19b bad CRS pattern", FALSE, check_Product(list(
  id="x", name="p", data_source="s", spatial_support_type="polygon",
  temporal_resolution="annual", crs="4326")))
t("19c bad container digest pattern", FALSE, check_ToolRun(list(
  id="x", run_role="download", tool_name="amadeus", tool_version="1.0",
  run_timestamp_utc="2026-07-16T04:00:02Z", status="succeeded",
  container_image_digest="latest")))
t("datetime without a UTC offset", FALSE, check_ToolRun(list(
  id="x", run_role="download", tool_name="amadeus", tool_version="1.0",
  run_timestamp_utc="2026-07-16T04:00:02", status="succeeded")))

cat(sprintf("\n%d passed, %d failed\n", pass, fail))
quit(status = if (fail > 0) 1 else 0)
