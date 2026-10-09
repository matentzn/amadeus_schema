from __future__ import annotations

import re
import sys
from datetime import (
    date,
    datetime,
    time
)
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Literal,
    Optional,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer
)


metamodel_version = "1.11.0"
version = "0.1.0"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias = True,
        validate_by_name = True,
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )





class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value

    def __contains__(self, key:str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta({'default_prefix': 'amadeus',
     'default_range': 'string',
     'description': 'A candidate data model for the next-generation, '
                    'database-backed amadeus\n'
                    '("AmadeusDB"). Prototype for the Database-and-Schema agenda '
                    'item of the\n'
                    'Amadeus Next-Generation Maintenance and Modernization plan '
                    '(v1.0, 2026-09-18).\n'
                    '\n'
                    'Four layers, five modules\n'
                    '-------------------------\n'
                    '* `amadeus_common`      types, enums, shared slots — and the '
                    'reconciliation\n'
                    '                        record against EnVar and HEW\n'
                    '* `amadeus_catalog`     what data exists and what it means\n'
                    '                        (DataSource → Product → '
                    'ProductVariable →\n'
                    '                        CanonicalVariable; GridDefinition; '
                    'Asset)\n'
                    '* `amadeus_value`       the data rows, in four spatial '
                    'shapes\n'
                    '                        (StationObservation, GridCellValue, '
                    'AreaValue,\n'
                    '                        HexCellValue) plus VectorFeature\n'
                    '* `amadeus_request`     the query-first contract\n'
                    '                        (LocationSet, Location, '
                    'ExtractionRequest,\n'
                    '                        AmbientValueAtLocation)\n'
                    '* `amadeus_provenance`  ToolRun and the derivation DAG\n'
                    '\n'
                    'The three load-bearing claims\n'
                    '-----------------------------\n'
                    '1. **One schema, not one per source type.** The 24 amadeus '
                    'sources vary on\n'
                    '   five orthogonal axes recorded on `Product` and '
                    '`CanonicalVariable`\n'
                    '   (spatial support, temporal resolution, value kind, native '
                    'format,\n'
                    '   extensivity), and on exactly one axis that needs a '
                    'different table: what\n'
                    '   geometry identifies a value. Four value tables cover all '
                    'of them.\n'
                    '2. **`CanonicalVariable` ← `ProductVariable` answers the '
                    'actual question.**\n'
                    '   "Is the schema for this variable the same as for the same '
                    'variable from\n'
                    '   another source?" Yes at the canonical level, no at the '
                    'product level, and\n'
                    '   every reason for the difference is a slot.\n'
                    '3. **Extensivity makes aggregation checkable.** Intensive vs '
                    'extensive is not\n'
                    '   documentation; it is the precondition on which aggregation '
                    'methods are\n'
                    '   legal, enforced by a rule on `ExtractionRequest`.\n'
                    '\n'
                    'Relationship to the neighbouring schemas\n'
                    '----------------------------------------\n'
                    'This model sits *between* HEW and EnVar and is designed to be '
                    'projectable to\n'
                    'both, not to replace either:\n'
                    '\n'
                    '    HEW Catalog    dataset grain    what exists           ← '
                    'Product, DataSource roll up\n'
                    '    AmadeusDB      row grain        the values themselves  ← '
                    'this schema\n'
                    '    EnVar          run grain        what one number means  ← '
                    'Asset + ToolRun + Product project out\n'
                    '\n'
                    'Every slot that has an upstream equivalent carries '
                    '`exact_mappings` to it.\n'
                    'Every enum that extends an upstream one carries `annotations: '
                    'extends` plus a\n'
                    'note on why, so enum reconciliation is a finite list of '
                    'decisions rather than\n'
                    'a diff. Three things this model has that neither upstream '
                    'does — per-row\n'
                    '`data_status`, `VariableExtensivityEnum`, and '
                    '`GridDefinition` — are candidate\n'
                    'contributions upward.',
     'id': 'https://w3id.org/niehs/amadeus',
     'imports': ['linkml:types',
                 'amadeus_common',
                 'amadeus_catalog',
                 'amadeus_value',
                 'amadeus_request',
                 'amadeus_provenance'],
     'license': 'MIT',
     'name': 'amadeus-schema',
     'prefixes': {'amadeus': {'prefix_prefix': 'amadeus',
                              'prefix_reference': 'https://w3id.org/niehs/amadeus/'},
                  'envar': {'prefix_prefix': 'envar',
                            'prefix_reference': 'https://w3id.org/linkml/microschemas/envar/'},
                  'geo': {'prefix_prefix': 'geo',
                          'prefix_reference': 'http://www.opengis.net/ont/geosparql#'},
                  'hew': {'prefix_prefix': 'hew',
                          'prefix_reference': 'https://w3id.org/hew/schema/'},
                  'linkml': {'prefix_prefix': 'linkml',
                             'prefix_reference': 'https://w3id.org/linkml/'},
                  'prov': {'prefix_prefix': 'prov',
                           'prefix_reference': 'http://www.w3.org/ns/prov#'}},
     'see_also': ['https://monarch-initiative.github.io/linkml-microschemas-envar/overview/',
                  'https://github.com/NIEHS/HEW_Catalog_Data_Model/tree/develop',
                  'https://github.com/NIEHS/amadeus/issues/249'],
     'source_file': 'src/amadeus_schema/schema/amadeus_schema.yaml',
     'title': 'AmadeusDB — Data Model'} )

class SpatialSupportTypeEnum(str, Enum):
    """
    What a single value spatially *is* — the source-side question. Distinct from `TargetGeographyTypeEnum`, which says what a value gets attached to. Both are needed; neither replaces the other.
    """
    point = "point"
    """
    A dimensionless location.
    """
    monitoring_station = "monitoring_station"
    """
    A fixed instrument with an identity that persists across time.
    """
    raster_grid_cell = "raster_grid_cell"
    """
    A cell of an observational or retrieval grid.
    """
    model_grid_cell = "model_grid_cell"
    """
    A cell of a model or reanalysis grid.
    """
    polygon = "polygon"
    """
    An arbitrary polygon feature (a smoke plume, a drought area).
    """
    administrative_area = "administrative_area"
    """
    A governmental unit (county, state).
    """
    statistical_area = "statistical_area"
    """
    A statistical unit (census tract, block group, ZCTA).
    """
    hex_cell = "hex_cell"
    """
    A hierarchical hexagonal cell, in practice H3.
    """
    line_feature = "line_feature"
    """
    A linear feature (a road segment, a stream reach).
    """
    other = "other"


class TargetGeographyTypeEnum(str, Enum):
    """
    The geography a value is delivered against, after extraction.
    """
    point_location = "point_location"
    """
    A coordinate pair supplied by the user. Deliberately *not* named `point_residence` — amadeus knows nothing about residences.
    """
    buffered_point = "buffered_point"
    census_block_group = "census_block_group"
    census_tract = "census_tract"
    zcta = "zcta"
    county = "county"
    state = "state"
    hydrologic_unit = "hydrologic_unit"
    h3_hex = "h3_hex"
    grid_cell = "grid_cell"
    public_water_system = "public_water_system"


class TemporalResolutionEnum(str, Enum):
    instantaneous = "instantaneous"
    subhourly = "subhourly"
    hourly = "hourly"
    three_hourly = "three_hourly"
    daily = "daily"
    monthly = "monthly"
    seasonal = "seasonal"
    annual = "annual"
    multi_year_epoch = "multi_year_epoch"
    """
    Irregularly spaced named epochs rather than a regular series.
    """
    timeless = "timeless"
    """
    Static: the product asserts no valid time. Modelled as an unbounded valid interval rather than a null, so time predicates still work.
    """


class TemporalAlignmentEnum(str, Enum):
    """
    Where in the aggregation window the timestamp sits. Taken from HEW, which has it and EnVar does not — a genuine gap EnVar should close.
    """
    start = "start"
    center = "center"
    end = "end"
    interval = "interval"
    """
    The record carries both bounds explicitly.
    """
    unknown = "unknown"


class DayBoundaryConventionEnum(str, Enum):
    """
    Where a "day" starts for a daily product. This is the slot behind the Daymet/GridMET 1.26 °C discrepancy: same variable, same place, same date, different day boundary.
    """
    local_midnight = "local_midnight"
    utc_midnight = "utc_midnight"
    ending_1200_gmt = "ending_1200_gmt"
    solar_noon_centered = "solar_noon_centered"
    observation_dependent = "observation_dependent"
    not_applicable = "not_applicable"


class CalendarEnum(str, Enum):
    gregorian = "gregorian"
    proleptic_gregorian = "proleptic_gregorian"
    noleap = "noleap"
    daymet_365 = "daymet_365"
    all_leap = "all_leap"
    day_360 = "day_360"
    julian = "julian"


class AggregationMethodEnum(str, Enum):
    """
    How many values became one. Which members are *legal* for a given variable is determined by `VariableExtensivityEnum` — see the rules on `ExtractionRequest`.
    """
    instantaneous = "instantaneous"
    mean = "mean"
    minimum = "minimum"
    maximum = "maximum"
    median = "median"
    sum = "sum"
    count = "count"
    percentile = "percentile"
    cumulative = "cumulative"
    area_weighted_mean = "area_weighted_mean"
    population_weighted_mean = "population_weighted_mean"
    mode = "mode"
    class_proportion = "class_proportion"
    """
    Fraction of the support occupied by one categorical class.
    """
    density = "density"
    """
    Feature quantity per unit area.
    """
    nearest = "nearest"
    other = "other"


class ExtractionMethodEnum(str, Enum):
    """
    How a value was pulled out of its source support at a location.
    """
    nearest_cell = "nearest_cell"
    bilinear = "bilinear"
    inverse_distance_weighted_4_nearest_cells = "inverse_distance_weighted_4_nearest_cells"
    area_weighted_polygon_mean = "area_weighted_polygon_mean"
    population_weighted_mean = "population_weighted_mean"
    point_station_lookup = "point_station_lookup"
    nearest_station = "nearest_station"
    intersection_area_proportion = "intersection_area_proportion"
    raster_zonal_sum = "raster_zonal_sum"
    feature_density = "feature_density"
    exact_extract = "exact_extract"
    """
    `exactextractr::exact_extract` — fractional cell coverage weighting. amadeus's default for polygon and buffered-point extraction.
    """


class VariableExtensivityEnum(str, Enum):
    """
    Whether a quantity is intensive (independent of the size of its support — a temperature) or extensive (scales with it — a population count, an emission mass). **This is the slot that makes aggregation checkable.** Averaging an extensive variable over a buffer is a silent, plausible-looking error; summing an intensive one is worse. Requested explicitly by the project lead and tracked as amadeus issue #249.
    """
    intensive = "intensive"
    """
    Value is independent of support size. Legal aggregations: mean, min, max, median, percentile, area/population-weighted mean, nearest.
    """
    extensive = "extensive"
    """
    Value scales with support size; aggregation must conserve the total. Legal aggregations: sum, count, cumulative, raster zonal sum, density.
    """
    categorical = "categorical"
    """
    Nominal class label. Legal aggregations: mode, class_proportion.
    """
    unknown = "unknown"
    """
    Not yet assessed. Permitted so migration does not require assessing every legacy variable at once, but blocks strict-mode extraction.
    """


class ValueDataTypeEnum(str, Enum):
    """
    The measurement kind, not the storage type.
    """
    continuous_numeric = "continuous_numeric"
    categorical = "categorical"
    binary_flag = "binary_flag"
    count = "count"
    event_marker = "event_marker"
    proportion = "proportion"


class DataStatusEnum(str, Enum):
    """
    The quality state of a value *as the source declares it*. Load-bearing for the AQS/AirNow harmonization rule (plan §4.6.1): an AirNow preliminary value must never overwrite an AQS quality-controlled value in place, so status has to be carried on every row, not on the dataset.
    """
    preliminary = "preliminary"
    """
    Near-real-time, unvalidated. AirNow.
    """
    provisional = "provisional"
    quality_controlled = "quality_controlled"
    """
    Passed the producer's QA process. AQS.
    """
    final = "final"
    forecast = "forecast"
    """
    Model output valid in the future relative to its reference time.
    """
    reanalysis = "reanalysis"
    superseded = "superseded"
    """
    Replaced by a later revision. Retained rather than deleted — revisions create new records, they do not mutate old ones.
    """
    unknown = "unknown"


class NullSemanticsEnum(str, Enum):
    """
    Why a value is absent, or why a zero is a zero.
    """
    present = "present"
    structural_null = "structural_null"
    """
    The quantity cannot exist here (sea-surface temperature on land).
    """
    derived_null = "derived_null"
    """
    Inputs were missing so the derivation could not run.
    """
    true_zero = "true_zero"
    """
    A measured zero, not a missing value. The nodata-versus-zero edge case the plan's test matrix calls out.
    """


class MissingReasonEnum(str, Enum):
    """
    Why a *metadata* field is empty. Distinguishes "the source does not provide this" from "nobody has looked yet" — the difference that decides whether a gap is someone's task.
    """
    not_provided_by_source = "not_provided_by_source"
    available_but_not_extracted = "available_but_not_extracted"
    """
    It is in the source file and amadeus discards it. The Tier 1 gap — the cheapest possible win, and the one to count.
    """
    upstream_data_not_propagated = "upstream_data_not_propagated"
    under_investigation = "under_investigation"
    not_applicable = "not_applicable"


class ConceptStatusEnum(str, Enum):
    """
    State of the mapping from a variable to a target vocabulary. HEW's value set, which is strictly better than EnVar's three-valued one: it keeps standard/non-standard apart (OMOP-critical) and "nobody looked" apart from "we looked and there is nothing".
    """
    mapped_standard = "mapped_standard"
    mapped_nonstandard = "mapped_nonstandard"
    candidate_mapping = "candidate_mapping"
    vocabulary_gap = "vocabulary_gap"
    not_evaluated = "not_evaluated"


class NativeFormatEnum(str, Enum):
    """
    The format the source actually ships.
    """
    netcdf4_cf = "netcdf4_cf"
    netcdf3 = "netcdf3"
    hdf4 = "hdf4"
    """
    MODIS. Not in EnVar's enum; amadeus reads it today.
    """
    hdf5 = "hdf5"
    geotiff = "geotiff"
    cloud_optimized_geotiff = "cloud_optimized_geotiff"
    ascii_grid = "ascii_grid"
    """
    GMTED2010, PRISM `.asc`.
    """
    grib1 = "grib1"
    grib2 = "grib2"
    bil = "bil"
    """
    PRISM binary interleaved.
    """
    shapefile = "shapefile"
    geodatabase = "geodatabase"
    kml = "kml"
    csv_station_observations = "csv_station_observations"
    pipe_delimited_text = "pipe_delimited_text"
    """
    IMPROVE aerosol exports.
    """
    fixed_width_text = "fixed_width_text"
    zarr = "zarr"
    parquet = "parquet"
    geoparquet = "geoparquet"


class DataGenreEnum(str, Enum):
    """
    The thematic classification already used in the amadeus README's source table. Promoted from prose to an enum so it can drive discovery.
    """
    meteorology = "meteorology"
    climate = "climate"
    climate_classification = "climate_classification"
    air_pollution = "air_pollution"
    aerosols = "aerosols"
    atmosphere = "atmosphere"
    emissions = "emissions"
    chemicals = "chemicals"
    land_use = "land_use"
    agriculture = "agriculture"
    population = "population"
    hydrology = "hydrology"
    water = "water"
    elevation = "elevation"
    roadways = "roadways"
    wildfire_smoke = "wildfire_smoke"
    drought = "drought"
    satellite = "satellite"
    built_environment = "built_environment"


class AccessProtocolEnum(str, Enum):
    """
    How amadeus reaches a source. Determines whether subsetting can be pushed to the provider, which is the whole point of the "subset early" principle.
    """
    https_bulk_file = "https_bulk_file"
    """
    Fetch whole files over HTTPS. No server-side subsetting.
    """
    ftp = "ftp"
    s3_object_store = "s3_object_store"
    stac_api = "stac_api"
    """
    Spatio-temporal asset search. Supports geometry/time pushdown.
    """
    opendap = "opendap"
    """
    Supports variable and index-range pushdown.
    """
    thredds = "thredds"
    rest_api = "rest_api"
    """
    Provider-specific API with query parameters (AQS, AirNow, USGS).
    """
    harmony = "harmony"
    arcgis_service = "arcgis_service"


class MaterializationModeEnum(str, Enum):
    """
    How much of a source asset had to be brought local to answer a request. Taken verbatim from the modernization plan §4.7.2 so "streaming" is a recorded, auditable property of a run rather than an ungoverned side path.
    """
    direct_remote_scan = "direct_remote_scan"
    """
    Only the required columns, row groups, ranges or tiles were read.
    """
    server_side_subset = "server_side_subset"
    """
    The provider API returned exactly the requested subset.
    """
    bounded_cache = "bounded_cache"
    """
    Selected assets or chunks cached with checksums and a reuse policy.
    """
    full_materialization = "full_materialization"
    """
    The complete asset was downloaded because no reliable subset path exists. Cost and storage must be made visible before execution.
    """


class RunRoleEnum(str, Enum):
    """
    Which amadeus verb a tool run represents. The three public verbs plus the database-era additions.
    """
    download = "download"
    process = "process"
    calculate = "calculate"
    register = "register"
    """
    An asset was catalogued without materialising its values.
    """
    harmonize = "harmonize"
    """
    Cross-source reconciliation, hexification, unit conversion.
    """
    import_ = "import"
    """
    An externally supplied dataset was brought into the catalog.
    """
    export = "export"
    """
    An EnVar record or analysis-ready table was emitted.
    """


class PhiStatusEnum(str, Enum):
    """
    Whether a location set, and anything derived from it, is protected health information. An enum rather than a boolean for two reasons: it matches EnVar's `phi_status` exactly, and — see `ValueMaterializationEnum` — a boolean cannot be used as a LinkML rule precondition.
    """
    no_phi = "no_phi"
    aggregated_no_phi = "aggregated_no_phi"
    phi_present = "phi_present"


class ValueMaterializationEnum(str, Enum):
    """
    Whether an asset's values exist as rows in a value table, or the asset is catalogued for discovery only.
**This was a boolean and had to stop being one.** LinkML's only equality construct in a rule precondition is `equals_string`, which generates `{"const": "true"}` — the JSON *string* `"true"` — and therefore never matches the JSON boolean `true`. A rule keyed on a boolean silently never fires. Verified 2026-09-18 on linkml 1.9.x; see REPORT.md.
    """
    registered_only = "registered_only"
    """
    Catalogued and discoverable; no value rows written.
    """
    materialized = "materialized"
    """
    Value rows exist in a value table.
    """


class StatusMixingPolicyEnum(str, Enum):
    """
    Whether a request may combine values of different `data_status` — in practice, AirNow preliminary alongside AQS quality-controlled. Defaults to refusing. An enum for the same reason as `ValueMaterializationEnum`: it is a rule precondition, and booleans cannot be.
    """
    refuse = "refuse"
    """
    Reject the request if the candidate values differ in status. The default, per the harmonization rule in plan section 4.6.1.
    """
    allow_with_policy = "allow_with_policy"
    """
    Permitted, and `source_priority_policy` must state how values are reconciled.
    """


class StrictnessEnum(str, Enum):
    strict = "strict"
    permissive = "permissive"


class RunStatusEnum(str, Enum):
    succeeded = "succeeded"
    failed = "failed"
    partial = "partial"
    cancelled = "cancelled"


class GeometryTypeEnum(str, Enum):
    point = "point"
    multipoint = "multipoint"
    linestring = "linestring"
    multilinestring = "multilinestring"
    polygon = "polygon"
    multipolygon = "multipolygon"
    geometrycollection = "geometrycollection"


class TableOrientationEnum(str, Enum):
    wide = "wide"
    """
    One column per variable. What `calculate_covariates()` returns today (`weasd_0`, `tmmx_10000`, …).
    """
    long = "long"
    """
    One row per variable-time-location. The database-native orientation, and the only one that generalises across products.
    """


class TemporalGroupingEnum(str, Enum):
    """
    The `.by_time` argument of `calculate_covariates()`, made declarative.
    """
    none = "none"
    hour = "hour"
    day = "day"
    month = "month"
    year = "year"


class HomogenisationStatusEnum(str, Enum):
    homogenised = "homogenised"
    not_homogenised = "not_homogenised"
    partial = "partial"


class AreaTypeEnum(str, Enum):
    county = "county"
    state = "state"
    census_tract = "census_tract"
    census_block_group = "census_block_group"
    zcta = "zcta"
    hydrologic_unit = "hydrologic_unit"
    ecoregion = "ecoregion"
    smoke_plume = "smoke_plume"
    drought_area = "drought_area"
    public_water_system = "public_water_system"
    custom = "custom"


class AreaRoleEnum(str, Enum):
    """
    Whether an area's identity is externally stable or episodic. Determines whether cross-time aggregation over the area is meaningful.
    """
    administrative = "administrative"
    """
    Externally defined and stable across time (a county FIPS). Safe to aggregate over time; still subject to boundary revisions, which are handled as new areas rather than mutated ones.
    """
    episodic = "episodic"
    """
    The polygon exists because an event occurred (a smoke plume on one day). Aggregating across time is meaningless; the correct operation is intersection with a location.
    """


class ProvenanceChainTerminusEnum(str, Enum):
    raw_source_download = "raw_source_download"
    remote_asset_scan = "remote_asset_scan"
    """
    The chain bottoms out at a remote asset read in place, with nothing downloaded. The streaming case, which EnVar's enum does not have.
    """
    pre_existing_curated_dataset = "pre_existing_curated_dataset"
    externally_imported_dataset = "externally_imported_dataset"
    """
    A dataset contributed from outside amadeus, whose upstream derivation amadeus did not perform and cannot vouch for.
    """
    synthetic_data = "synthetic_data"



class DataSource(ConfiguredBaseModel):
    """
    A provider programme that publishes one or more products: EPA AQS, NASA MODIS, NOAA NARR, Climatology Lab. One row per row of the amadeus README source table.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'exact_mappings': ['hew:HEWResource'],
         'from_schema': 'https://w3id.org/niehs/amadeus/catalog',
         'slot_usage': {'amadeus_function_suffix': {'examples': [{'value': '_narr'},
                                                                 {'value': '_aqs'}],
                                                    'name': 'amadeus_function_suffix'},
                        'name': {'examples': [{'value': 'epa_aqs'},
                                              {'value': 'noaa_ncep_narr'}],
                                 'name': 'name',
                                 'required': True}},
         'title': 'Data Source'})

    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    name: str = Field(default=..., description="""A short machine-friendly name.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'LocationSet',
                       'ExtractionRequest'],
         'examples': [{'value': 'epa_aqs'}, {'value': 'noaa_ncep_narr'}]} })
    label: Optional[str] = Field(default=None, description="""A human-readable display label.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable']} })
    description: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource', 'Product', 'CanonicalVariable', 'LocationSet'],
         'slot_uri': 'dcterms:description'} })
    producer_institution: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource'],
         'exact_mappings': ['envar:source_producer_institution'],
         'examples': [{'value': 'US Environmental Protection Agency'}]} })
    homepage: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource']} })
    access_protocol: Optional[AccessProtocolEnum] = Field(default=None, description="""Primary access mechanism. Determines whether \"subset early\" is achievable at all for this source.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource']} })
    requires_authentication: Optional[bool] = Field(default=None, description="""Whether a credential is needed. True for all NASA Earthdata sources (`modis`, `merra2`, `geos`, SEDAC `population`).""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource']} })
    auth_mechanism: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource'],
         'examples': [{'value': 'NASA Earthdata bearer token'},
                      {'value': 'EPA AQS email + API key'}]} })
    rate_limit_requests_per_second: Optional[float] = Field(default=None, description="""Provider rate limit, as `download_data(rate_limit=)` already takes. In the catalog so a query planner can respect it without hard-coding.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource']} })
    license_spdx: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource', 'Product'],
         'exact_mappings': ['envar:source_license_spdx'],
         'examples': [{'value': 'CC0-1.0'}, {'value': 'NOASSERTION'}]} })
    citation_apa: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource', 'Product'],
         'exact_mappings': ['envar:source_citation_apa']} })
    doi: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource', 'Product']} })
    amadeus_function_suffix: Optional[str] = Field(default=None, description="""The suffix amadeus uses for this source's functions (`_narr` → `download_narr`, `process_narr`, `calculate_narr`). Recorded so the catalog and the R API can be checked against each other mechanically — a catalog entry with no implementing function, or a function with no catalog entry, is a test failure.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource'],
         'examples': [{'value': '_narr'}, {'value': '_aqs'}]} })

    @field_validator('doi')
    def pattern_doi(cls, v):
        pattern=re.compile(r"^10\.[0-9]{4,9}/.+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid doi format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid doi format: {v}"
            raise ValueError(err_msg)
        return v


class Product(ConfiguredBaseModel):
    """
    A specific, versioned data product from a source — the unit a user actually requests, and the unit that carries the *profile*: spatial support, temporal support, format, calendar, day boundary.
    This is where the answer to \"do we need different schemas for different types of source data?\" lives. We do not. The variation across the amadeus catalog decomposes into five orthogonal axes recorded here (`spatial_support_type`, `temporal_resolution`, `value` kind via the variables, `native_format`, and extensivity via the variables). One schema, one product table; a MODIS swath and an AQS monitor differ in their *values on these axes*, not in their structure.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'exact_mappings': ['hew:DatasetResource', 'envar:SourceDataset'],
         'from_schema': 'https://w3id.org/niehs/amadeus/catalog',
         'rules': [{'description': 'A gridded product must declare its grid. Without '
                                   'this, "1 km" lives in a description string and no '
                                   'query can reason about resolution.',
                    'postconditions': {'slot_conditions': {'grid_definition': {'name': 'grid_definition',
                                                                               'required': True}}},
                    'preconditions': {'slot_conditions': {'spatial_support_type': {'any_of': [{'equals_string': 'raster_grid_cell'},
                                                                                              {'equals_string': 'model_grid_cell'}],
                                                                                   'name': 'spatial_support_type'}}}},
                   {'description': 'A daily product must declare where its day starts. '
                                   'This rule alone would have caught the '
                                   'Daymet/GridMET 1.26 °C discrepancy at registration '
                                   'time.',
                    'postconditions': {'slot_conditions': {'day_boundary_convention': {'name': 'day_boundary_convention',
                                                                                       'required': True}}},
                    'preconditions': {'slot_conditions': {'temporal_resolution': {'equals_string': 'daily',
                                                                                  'name': 'temporal_resolution'}}}},
                   {'description': 'A timeless product (GMTED elevation, '
                                   'Köppen-Geiger) asserts no temporal coverage start. '
                                   'Modelled as absence rather than a sentinel date.',
                    'postconditions': {'slot_conditions': {'temporal_coverage_start': {'name': 'temporal_coverage_start',
                                                                                       'value_presence': 'ABSENT'}}},
                    'preconditions': {'slot_conditions': {'temporal_resolution': {'equals_string': 'timeless',
                                                                                  'name': 'temporal_resolution'}}}},
                   {'description': 'A timeless product asserts no temporal coverage '
                                   'end.',
                    'postconditions': {'slot_conditions': {'temporal_coverage_end': {'name': 'temporal_coverage_end',
                                                                                     'value_presence': 'ABSENT'}}},
                    'preconditions': {'slot_conditions': {'temporal_resolution': {'equals_string': 'timeless',
                                                                                  'name': 'temporal_resolution'}}}}],
         'slot_usage': {'data_source': {'name': 'data_source', 'required': True},
                        'grid_definition': {'description': 'Required when '
                                                           '`spatial_support_type` is '
                                                           'a grid cell type, '
                                                           'forbidden otherwise. '
                                                           'Enforced by the rules '
                                                           'below rather than by two '
                                                           'separate classes — the '
                                                           'project lead\'s "grid size '
                                                           'is a dataset-level '
                                                           'property" becomes a '
                                                           'foreign key, not a copied '
                                                           'field.',
                                            'name': 'grid_definition'},
                        'name': {'name': 'name', 'required': True},
                        'spatial_support_type': {'name': 'spatial_support_type',
                                                 'required': True},
                        'temporal_resolution': {'name': 'temporal_resolution',
                                                'required': True}},
         'title': 'Product'})

    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    name: str = Field(default=..., description="""A short machine-friendly name.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'LocationSet',
                       'ExtractionRequest']} })
    label: Optional[str] = Field(default=None, description="""A human-readable display label.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable']} })
    description: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource', 'Product', 'CanonicalVariable', 'LocationSet'],
         'slot_uri': 'dcterms:description'} })
    data_source: str = Field(default=..., description="""The publishing programme.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product']} })
    product_version: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Product'],
         'exact_mappings': ['envar:source_dataset_version'],
         'examples': [{'value': '061'}, {'value': 'v1.5'}, {'value': '2021'}]} })
    data_genre: Optional[list[DataGenreEnum]] = Field(default=None, description="""Thematic classification, from the README source table.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product']} })
    native_format: Optional[NativeFormatEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Product', 'Asset'],
         'exact_mappings': ['envar:source_native_format']} })
    spatial_support_type: SpatialSupportTypeEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Product'], 'exact_mappings': ['hew:support_type']} })
    grid_definition: Optional[str] = Field(default=None, description="""Required when `spatial_support_type` is a grid cell type, forbidden otherwise. Enforced by the rules below rather than by two separate classes — the project lead's \"grid size is a dataset-level property\" becomes a foreign key, not a copied field.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product', 'GridCellValue']} })
    crs: Optional[str] = Field(default=None, description="""Coordinate reference system as an authority code. Stored as the string form (`EPSG:4326`) because that is what both `terra` and the SQL engines accept; the numeric SRID is derived for `ST_SetSRID`.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product', 'GridDefinition', 'LocationSet'],
         'exact_mappings': ['envar:crs', 'hew:coordinate_reference_system_uri'],
         'examples': [{'value': 'EPSG:4326'}, {'value': 'EPSG:5070'}]} })
    srid: Optional[int] = Field(default=None, description="""Numeric spatial reference identifier, derived from `crs`. Materialised because `ST_SetSRID` takes an integer and the geometry views need it without a lookup.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product',
                       'GridDefinition',
                       'Asset',
                       'StationObservation',
                       'GridCellValue',
                       'AreaValue',
                       'HexCellValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location']} })
    spatial_extent_bbox_wkt: Optional[str] = Field(default=None, description="""Coverage footprint as WKT, so extent is a spatial predicate.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product']} })
    spatial_extent_descriptor: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Product'],
         'exact_mappings': ['envar:spatial_extent_descriptor'],
         'examples': [{'value': 'Contiguous United States'}, {'value': 'Global'}]} })
    native_spatial_resolution_m: Optional[float] = Field(default=None, description="""Nominal resolution in metres. Computable, and therefore the one a query planner uses — but meaningless for non-grid supports, hence the descriptor alongside it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product'],
         'exact_mappings': ['envar:native_spatial_resolution_m']} })
    native_spatial_resolution_descriptor: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Product'],
         'exact_mappings': ['envar:native_spatial_resolution_descriptor',
                            'hew:spatial_resolution'],
         'examples': [{'value': '4 km'}, {'value': 'census tract'}]} })
    temporal_resolution: TemporalResolutionEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Product'], 'exact_mappings': ['envar:temporal_resolution']} })
    temporal_resolution_iso: Optional[str] = Field(default=None, description="""The same fact as `temporal_resolution`, as an ISO 8601 duration. Both are kept because the enum is validatable and the duration is expressive (`P3D` has no enum member). HEW uses the duration, EnVar the enum; this is the reconciliation, and it is generated, not hand-maintained.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product'], 'exact_mappings': ['hew:temporal_resolution']} })
    temporal_alignment: Optional[TemporalAlignmentEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Product', 'ProductVariable'],
         'exact_mappings': ['hew:temporal_alignment']} })
    day_boundary_convention: Optional[DayBoundaryConventionEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Product'], 'exact_mappings': ['envar:day_boundary_convention']} })
    calendar: Optional[CalendarEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Product'], 'exact_mappings': ['envar:calendar']} })
    temporal_coverage_start: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Product'], 'exact_mappings': ['envar:temporal_coverage_start']} })
    temporal_coverage_end: Optional[date] = Field(default=None, description="""Absent means \"ongoing\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product'], 'exact_mappings': ['envar:temporal_coverage_end']} })
    update_cadence_iso: Optional[str] = Field(default=None, description="""How often the source publishes new data.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product']} })
    typical_latency_iso: Optional[str] = Field(default=None, description="""Typical delay between observation and availability. The field that makes the AQS-versus-AirNow trade-off explicit: AQS is quality-controlled and months late, AirNow is preliminary and hourly.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product']} })
    default_data_status: Optional[DataStatusEnum] = Field(default=None, description="""The status values from this product carry unless a row says otherwise.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product']} })
    homogenisation_status: Optional[HomogenisationStatusEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Product'],
         'exact_mappings': ['envar:source_homogenisation_status']} })
    doi: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource', 'Product']} })
    license_spdx: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource', 'Product'],
         'exact_mappings': ['envar:source_license_spdx'],
         'examples': [{'value': 'CC0-1.0'}, {'value': 'NOASSERTION'}]} })
    citation_apa: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource', 'Product'],
         'exact_mappings': ['envar:source_citation_apa']} })
    access_url: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Product'], 'exact_mappings': ['envar:source_access_url']} })
    amadeus_dataset_name: Optional[str] = Field(default=None, description="""The exact string accepted by `download_data(dataset_name=)`. The bridge between the catalog and the existing R API.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product'],
         'examples': [{'value': 'narr'}, {'value': 'gridmet'}]} })
    amadeus_process_covariate: Optional[str] = Field(default=None, description="""The string accepted by `process_covariates(covariate=)`.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product']} })
    amadeus_calculate_covariate: Optional[str] = Field(default=None, description="""The string accepted by `calculate_covariates(covariate=)`. Distinct from the process name — `modis_swath`/`modis_merge` both calculate as `modis`, and `aqs` processes but does not calculate.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product']} })
    supports_server_side_subset: Optional[bool] = Field(default=None, description="""Whether the provider will return a geometry/time/variable subset. Drives the achievable `MaterializationModeEnum`.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product']} })
    stac_collection_id: Optional[str] = Field(default=None, description="""STAC collection identifier, where the product is STAC-published.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product', 'Asset']} })

    @field_validator('crs')
    def pattern_crs(cls, v):
        pattern=re.compile(r"^[A-Za-z]+:[0-9]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid crs format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid crs format: {v}"
            raise ValueError(err_msg)
        return v

    @field_validator('doi')
    def pattern_doi(cls, v):
        pattern=re.compile(r"^10\.[0-9]{4,9}/.+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid doi format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid doi format: {v}"
            raise ValueError(err_msg)
        return v


class GridDefinition(ConfiguredBaseModel):
    """
    A reusable description of a raster or model grid. Its own entity because several products share one grid (all NARR monolevel variables) and because resolution, projection and vertical levels must be computable, not prose.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/niehs/amadeus/catalog',
         'slot_usage': {'crs': {'name': 'crs', 'required': True},
                        'resolution_x': {'name': 'resolution_x', 'required': True},
                        'resolution_y': {'name': 'resolution_y', 'required': True},
                        'vertical_levels': {'description': 'The pressure or height '
                                                           'levels present, when the '
                                                           'product is multi-level. '
                                                           'NARR and MERRA-2/GEOS '
                                                           'pressure-level products '
                                                           'encode the level in the '
                                                           '`terra` layer name '
                                                           '(`variable_level_YYYYMMDD`); '
                                                           'recording the level set '
                                                           'here is what lets that be '
                                                           'parsed reliably instead of '
                                                           'positionally.',
                                            'name': 'vertical_levels'}},
         'title': 'Grid Definition'})

    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    name: Optional[str] = Field(default=None, description="""A short machine-friendly name.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'LocationSet',
                       'ExtractionRequest']} })
    label: Optional[str] = Field(default=None, description="""A human-readable display label.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable']} })
    crs: str = Field(default=..., description="""Coordinate reference system as an authority code. Stored as the string form (`EPSG:4326`) because that is what both `terra` and the SQL engines accept; the numeric SRID is derived for `ST_SetSRID`.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product', 'GridDefinition', 'LocationSet'],
         'exact_mappings': ['envar:crs', 'hew:coordinate_reference_system_uri'],
         'examples': [{'value': 'EPSG:4326'}, {'value': 'EPSG:5070'}]} })
    srid: Optional[int] = Field(default=None, description="""Numeric spatial reference identifier, derived from `crs`. Materialised because `ST_SetSRID` takes an integer and the geometry views need it without a lookup.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product',
                       'GridDefinition',
                       'Asset',
                       'StationObservation',
                       'GridCellValue',
                       'AreaValue',
                       'HexCellValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location']} })
    grid_mapping_name: Optional[str] = Field(default=None, description="""CF grid mapping name.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition'],
         'examples': [{'value': 'lambert_conformal_conic'},
                      {'value': 'latitude_longitude'}]} })
    proj_string: Optional[str] = Field(default=None, description="""Full PROJ or WKT2 CRS definition, for grids with no authority code.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition']} })
    resolution_x: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition']} })
    resolution_y: float = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition']} })
    resolution_unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition'],
         'examples': [{'value': 'm'}, {'value': 'deg'}]} })
    n_columns: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition']} })
    n_rows: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition']} })
    origin_x: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition']} })
    origin_y: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition']} })
    vertical_level_type: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition', 'ProductVariable'],
         'examples': [{'value': 'isobaric_pressure_hPa'},
                      {'value': 'height_above_ground_m'}]} })
    vertical_level_unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition', 'AmbientValue']} })
    vertical_levels: Optional[list[float]] = Field(default=None, description="""The pressure or height levels present, when the product is multi-level. NARR and MERRA-2/GEOS pressure-level products encode the level in the `terra` layer name (`variable_level_YYYYMMDD`); recording the level set here is what lets that be parsed reliably instead of positionally.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition']} })

    @field_validator('crs')
    def pattern_crs(cls, v):
        pattern=re.compile(r"^[A-Za-z]+:[0-9]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid crs format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid crs format: {v}"
            raise ValueError(err_msg)
        return v


class CanonicalVariable(ConfiguredBaseModel):
    """
    A harmonised environmental quantity, independent of who publishes it. The cross-source identity anchor: `gridmet.tmmx`, `prism.tmax` and `daymet.tmax` are three `ProductVariable`s over *one* `CanonicalVariable`, and that is what makes \"is it the same variable?\" answerable by a join rather than by a conversation.
    Carries the semantics that must be identical across sources (`standard_name`, canonical units, extensivity, plausible range, concept bindings). Everything that legitimately differs per source lives on `ProductVariable`.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'exact_mappings': ['hew:EnvironmentalVariable', 'envar:VariableIdentity'],
         'from_schema': 'https://w3id.org/niehs/amadeus/catalog',
         'rules': [{'description': 'A categorical value must declare categorical '
                                   'extensivity.',
                    'postconditions': {'slot_conditions': {'extensivity': {'equals_string': 'categorical',
                                                                           'name': 'extensivity'}}},
                    'preconditions': {'slot_conditions': {'value_data_type': {'equals_string': 'categorical',
                                                                              'name': 'value_data_type'}}}},
                   {'description': 'A plausible numeric minimum is meaningless for a '
                                   'nominal class label.',
                    'postconditions': {'slot_conditions': {'plausible_min': {'name': 'plausible_min',
                                                                             'value_presence': 'ABSENT'}}},
                    'preconditions': {'slot_conditions': {'extensivity': {'equals_string': 'categorical',
                                                                          'name': 'extensivity'}}}},
                   {'description': 'A plausible numeric maximum is meaningless for a '
                                   'nominal class label.',
                    'postconditions': {'slot_conditions': {'plausible_max': {'name': 'plausible_max',
                                                                             'value_presence': 'ABSENT'}}},
                    'preconditions': {'slot_conditions': {'extensivity': {'equals_string': 'categorical',
                                                                          'name': 'extensivity'}}}}],
         'slot_usage': {'extensivity': {'name': 'extensivity', 'required': True},
                        'name': {'examples': [{'value': 'air_temperature_daily_maximum'},
                                              {'value': 'pm25_mass_concentration'}],
                                 'name': 'name',
                                 'required': True},
                        'standard_name': {'name': 'standard_name', 'required': True},
                        'units_ucum': {'name': 'units_ucum', 'required': True},
                        'value_data_type': {'name': 'value_data_type',
                                            'required': True}},
         'title': 'Canonical Variable'})

    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    name: str = Field(default=..., description="""A short machine-friendly name.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'LocationSet',
                       'ExtractionRequest'],
         'examples': [{'value': 'air_temperature_daily_maximum'},
                      {'value': 'pm25_mass_concentration'}]} })
    label: Optional[str] = Field(default=None, description="""A human-readable display label.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable']} })
    description: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource', 'Product', 'CanonicalVariable', 'LocationSet'],
         'slot_uri': 'dcterms:description'} })
    standard_name: str = Field(default=..., description="""The standard-name identifier for the physical quantity, as a CURIE so no single naming authority is privileged. Prefer a CF standard name where one exists; fall back to ECTO/ENVO or a minted `AMADEUS:` term. The prefix carries the authority; the slot name does not.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CanonicalVariable'],
         'exact_mappings': ['envar:standard_name', 'hew:measured_property'],
         'examples': [{'value': 'CF:air_temperature'},
                      {'value': 'CF:mass_concentration_of_pm2p5_ambient_aerosol_particles_in_air'}]} })
    standard_name_authority: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['CanonicalVariable'],
         'examples': [{'value': 'CF Standard Name Table v85'}]} })
    units_ucum: str = Field(default=..., description="""Canonical units in UCUM notation, bare (not CURIE-prefixed). HEW prefixes (`UCUM:Cel`), EnVar does not (`Cel`); we follow EnVar and note the difference, because it is exactly the kind of thing a mechanical mapper gets wrong silently.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CanonicalVariable'],
         'exact_mappings': ['envar:units_ucum', 'hew:unit'],
         'examples': [{'value': 'Cel'}, {'value': 'ug/m3'}]} })
    units_display: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['CanonicalVariable'], 'exact_mappings': ['envar:units_display']} })
    value_data_type: ValueDataTypeEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['CanonicalVariable', 'ProductVariable'],
         'exact_mappings': ['envar:value_data_type']} })
    extensivity: VariableExtensivityEnum = Field(default=..., description="""Intensive, extensive or categorical. Determines which aggregation methods are legal for this variable — see `ExtractionRequest`.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CanonicalVariable', 'ProductVariable']} })
    default_aggregation_method: Optional[AggregationMethodEnum] = Field(default=None, description="""The aggregation applied when a request does not name one. Must be legal for the declared extensivity.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CanonicalVariable']} })
    plausible_min: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['CanonicalVariable'],
         'exact_mappings': ['envar:value_range_plausible_min']} })
    plausible_max: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['CanonicalVariable'],
         'exact_mappings': ['envar:value_range_plausible_max']} })
    concept_mappings: Optional[list[str]] = Field(default=None, description="""Mappings to any target vocabulary. One generic list rather than a slot per standard, so adding a vocabulary is a new prefix, not a schema change. EnVar and HEW arrived at this identical design independently.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CanonicalVariable'],
         'exact_mappings': ['envar:concept_mappings', 'hew:concept_mappings']} })
    omop_concept_binding: Optional[OmopConceptBinding] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['CanonicalVariable'],
         'exact_mappings': ['hew:omop_concept_binding']} })
    envar_variable_family: Optional[str] = Field(default=None, description="""Which EnVar variable family this belongs to, and therefore which variable-specific extension block an emitted EnVar record must carry (`derived_heat_metric` for the heat family).""", json_schema_extra = { "linkml_meta": {'domain_of': ['CanonicalVariable'],
         'examples': [{'value': 'heat'}, {'value': 'air_quality'}]} })


class ProductVariable(ConfiguredBaseModel):
    """
    One source's delivery of one canonical variable: the native name, the native units and conversion, the CF metadata, the aggregation actually applied, and the layer-name template amadeus parses.
    Every slot here exists because it is a reason two sources of \"the same\" variable are not interchangeable. `native_units_ucum` + `native_value_scale_factor` + `native_value_offset` are the gridMET Kelvin→Celsius case, where the conversion happened at render time and was recorded nowhere.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'exact_mappings': ['envar:VariableIdentity'],
         'from_schema': 'https://w3id.org/niehs/amadeus/catalog',
         'rules': [{'description': 'A scale factor without the unit it scales from is '
                                   'uninterpretable.',
                    'postconditions': {'slot_conditions': {'native_units_ucum': {'name': 'native_units_ucum',
                                                                                 'required': True}}},
                    'preconditions': {'slot_conditions': {'native_value_scale_factor': {'name': 'native_value_scale_factor',
                                                                                        'value_presence': 'PRESENT'}}}},
                   {'description': "A multi-level variable's layer names must carry "
                                   'the level, or the level cannot be recovered when '
                                   'the raster is flattened.',
                    'postconditions': {'slot_conditions': {'layer_name_template': {'name': 'layer_name_template',
                                                                                   'pattern': '.*\\{level\\}.*'}}},
                    'preconditions': {'slot_conditions': {'vertical_level_type': {'name': 'vertical_level_type',
                                                                                  'value_presence': 'PRESENT'}}}}],
         'slot_usage': {'canonical_variable': {'name': 'canonical_variable',
                                               'required': True},
                        'extensivity': {'description': 'Optional override, same '
                                                       'semantics as '
                                                       '`value_data_type`. Overriding '
                                                       'it is a strong signal '
                                                       'something is wrong and should '
                                                       'be reviewed.',
                                        'name': 'extensivity'},
                        'layer_name_template': {'examples': [{'value': '{native_name}_{YYYYMMDD}'},
                                                             {'value': '{native_name}_{level}_{YYYYMMDD}'},
                                                             {'value': '{native_name}_{YYYYMMDD}_{HHMMSS}'}],
                                                'name': 'layer_name_template'},
                        'native_name': {'examples': [{'value': 'weasd'},
                                                     {'value': 'tmmx'},
                                                     {'value': '88101'}],
                                        'name': 'native_name',
                                        'required': True},
                        'product': {'name': 'product', 'required': True},
                        'value_data_type': {'description': 'Optional override. Absent '
                                                           'means "as the canonical '
                                                           'variable declares". '
                                                           'Present means this source '
                                                           'genuinely differs — e.g. a '
                                                           'source that publishes a '
                                                           'binary exceedance flag for '
                                                           'a quantity that is '
                                                           'continuous elsewhere.',
                                            'name': 'value_data_type'}},
         'title': 'Product Variable'})

    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    product: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable', 'Asset', 'VectorFeature']} })
    canonical_variable: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable', 'AmbientValue']} })
    native_name: str = Field(default=..., description="""The variable's name in the source: a netCDF variable name, a MODIS subdataset, an AQS parameter code.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable'],
         'examples': [{'value': 'weasd'}, {'value': 'tmmx'}, {'value': '88101'}]} })
    label: Optional[str] = Field(default=None, description="""A human-readable display label.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable']} })
    native_units_ucum: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable'],
         'exact_mappings': ['envar:native_units_ucum']} })
    native_value_scale_factor: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable'],
         'exact_mappings': ['envar:native_value_scale_factor']} })
    native_value_offset: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable'],
         'exact_mappings': ['envar:native_value_offset']} })
    unit_conversion_formula: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable'],
         'exact_mappings': ['envar:unit_conversion_formula'],
         'examples': [{'value': 'value_Cel = value_K - 273.15'}]} })
    cf_standard_name: Optional[str] = Field(default=None, description="""The CF `standard_name` attribute as it appears in the source file. A Tier 1 field: already in the netCDF, currently discarded on conversion to `terra`.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable']} })
    cf_cell_methods: Optional[str] = Field(default=None, description="""The CF `cell_methods` attribute verbatim. CF already has a standard way to say \"daily maximum\" and it is sitting unread in the file.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable'],
         'exact_mappings': ['envar:cf_cell_methods'],
         'examples': [{'value': 'time: maximum'},
                      {'value': 'time: mean within days time: maximum over days'}]} })
    aggregation_method: Optional[AggregationMethodEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable',
                       'ExtractionRequest',
                       'AmbientValueAtLocation'],
         'exact_mappings': ['envar:temporal_aggregation_method',
                            'hew:aggregation_method']} })
    aggregation_window_iso: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable'], 'exact_mappings': ['hew:aggregation_window']} })
    temporal_alignment: Optional[TemporalAlignmentEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Product', 'ProductVariable'],
         'exact_mappings': ['hew:temporal_alignment']} })
    vertical_level_type: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition', 'ProductVariable'],
         'examples': [{'value': 'isobaric_pressure_hPa'},
                      {'value': 'height_above_ground_m'}]} })
    missing_value_sentinel: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable'],
         'exact_mappings': ['envar:missing_value_sentinel'],
         'examples': [{'value': '-9999'}]} })
    quality_flag_vocabulary: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable'],
         'exact_mappings': ['envar:quality_flag_vocabulary']} })
    layer_name_template: Optional[str] = Field(default=None, description="""How amadeus composes `terra` layer names for this variable. Recorded because `calc_worker()` currently recovers variable, level and time by splitting the layer name on `_` and indexing by position; a declared template turns that from an implicit convention into a checkable one.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable'],
         'examples': [{'value': '{native_name}_{YYYYMMDD}'},
                      {'value': '{native_name}_{level}_{YYYYMMDD}'},
                      {'value': '{native_name}_{YYYYMMDD}_{HHMMSS}'}]} })
    amadeus_variable_code: Optional[str] = Field(default=None, description="""The string a user passes as `variable=` to the amadeus download/process functions, where it differs from `native_name`.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable']} })
    value_data_type: Optional[ValueDataTypeEnum] = Field(default=None, description="""Optional override. Absent means \"as the canonical variable declares\". Present means this source genuinely differs — e.g. a source that publishes a binary exceedance flag for a quantity that is continuous elsewhere.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CanonicalVariable', 'ProductVariable'],
         'exact_mappings': ['envar:value_data_type']} })
    extensivity: Optional[VariableExtensivityEnum] = Field(default=None, description="""Optional override, same semantics as `value_data_type`. Overriding it is a strong signal something is wrong and should be reviewed.""", json_schema_extra = { "linkml_meta": {'domain_of': ['CanonicalVariable', 'ProductVariable']} })
    harmonization_note: Optional[str] = Field(default=None, description="""Free text on why this delivery is not interchangeable with a sibling delivery of the same canonical variable. Deliberately unstructured: it is the intake queue for future first-class slots, not a permanent home.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable']} })
    metadata_gaps: Optional[list[MissingReasonEnum]] = Field(default=None, description="""Which metadata this delivery is missing, and why. Makes the Tier 1 backlog (\"in the file, discarded by amadeus\") countable and therefore reportable as progress.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable']} })


class OmopConceptBinding(ConfiguredBaseModel):
    """
    Binding of a canonical variable to an OMOP concept. Taken structurally from HEW so the two schemas exchange bindings without an adapter.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'exact_mappings': ['hew:OMOPConceptBinding'],
         'from_schema': 'https://w3id.org/niehs/amadeus/catalog',
         'slot_usage': {'concept_status': {'name': 'concept_status', 'required': True}},
         'title': 'OMOP Concept Binding'})

    omop_concept_id: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['OmopConceptBinding']} })
    omop_concept_name: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['OmopConceptBinding']} })
    omop_vocabulary_id: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['OmopConceptBinding']} })
    omop_domain_id: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['OmopConceptBinding']} })
    omop_standard_concept: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['OmopConceptBinding']} })
    concept_status: ConceptStatusEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['OmopConceptBinding']} })


class Asset(ConfiguredBaseModel):
    """
    A concrete byte stream: a file on disk, an object in a bucket, a STAC asset, or a provider API response. The unit of download, caching, integrity checking and idempotency.
    **Asset-centric by design.** The modernization plan's own instruction is \"adopt an asset-centric schema; avoid mandatory cell-row ingestion\". An asset can be registered — catalogued, discoverable, queryable by extent and time — without any of its values ever being materialised into a value table. `materialization_mode` records how much was actually read, so the four streaming modes of plan §4.7.2 become auditable properties of the catalog rather than an ungoverned side path.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/niehs/amadeus/catalog',
         'rules': [{'description': 'Anything cached or fully downloaded must record '
                                   'where it went and what it hashes to — otherwise '
                                   '"resumable, idempotent processing" is not '
                                   'checkable.',
                    'postconditions': {'slot_conditions': {'local_path': {'name': 'local_path',
                                                                          'required': True},
                                                           'sha256': {'name': 'sha256',
                                                                      'required': True}}},
                    'preconditions': {'slot_conditions': {'materialization_mode': {'any_of': [{'equals_string': 'bounded_cache'},
                                                                                              {'equals_string': 'full_materialization'}],
                                                                                   'name': 'materialization_mode'}}}},
                   {'description': 'If values were written into a value table, the run '
                                   'that wrote them must be identified. This is the '
                                   'link that makes every derived number resolve to a '
                                   'processing run (objective O-02).',
                    'postconditions': {'slot_conditions': {'produced_by_run': {'name': 'produced_by_run',
                                                                               'required': True}}},
                    'preconditions': {'slot_conditions': {'value_state': {'equals_string': 'materialized',
                                                                          'name': 'value_state'}}}}],
         'slot_usage': {'local_path': {'description': 'Present only when bytes were '
                                                      'actually written locally. '
                                                      'Absent for `direct_remote_scan` '
                                                      'and `server_side_subset`.',
                                       'name': 'local_path'},
                        'materialization_mode': {'name': 'materialization_mode',
                                                 'required': True},
                        'product': {'name': 'product', 'required': True},
                        'url': {'description': 'Where the bytes live upstream. '
                                               'Retained even after local caching so a '
                                               'result can be re-derived from source.',
                                'name': 'url'},
                        'value_state': {'name': 'value_state', 'required': True}},
         'title': 'Asset'})

    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    product: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable', 'Asset', 'VectorFeature']} })
    asset_key: Optional[str] = Field(default=None, description="""STAC asset key or other within-item key.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset']} })
    url: Optional[str] = Field(default=None, description="""Where the bytes live upstream. Retained even after local caching so a result can be re-derived from source.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset']} })
    local_path: Optional[str] = Field(default=None, description="""Present only when bytes were actually written locally. Absent for `direct_remote_scan` and `server_side_subset`.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset']} })
    media_type: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Asset'], 'examples': [{'value': 'application/x-netcdf'}]} })
    native_format: Optional[NativeFormatEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Product', 'Asset'],
         'exact_mappings': ['envar:source_native_format']} })
    size_bytes: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Asset']} })
    sha256: Optional[str] = Field(default=None, description="""SHA-256 of the byte stream, for integrity and idempotency.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset']} })
    source_last_modified: Optional[datetime ] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Asset']} })
    download_timestamp_utc: Optional[datetime ] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Asset']} })
    valid_time_start: Optional[datetime ] = Field(default=None, description="""Inclusive start of the interval the value is valid for. Left-closed, right-open by default (`[start, end)`) — declared here once so no individual dataset has to litigate it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    valid_time_end: Optional[datetime ] = Field(default=None, description="""Exclusive end of the validity interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    reference_time: Optional[datetime ] = Field(default=None, description="""Model initialisation / cycle time, distinct from valid time. Required for HRRR and any forecast product: \"valid versus reference time\" is called out explicitly in the P0 subdaily work.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    bbox_wkt: Optional[str] = Field(default=None, description="""Bounding geometry as WKT.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset']} })
    srid: Optional[int] = Field(default=None, description="""Numeric spatial reference identifier, derived from `crs`. Materialised because `ST_SetSRID` takes an integer and the geometry views need it without a lookup.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product',
                       'GridDefinition',
                       'Asset',
                       'StationObservation',
                       'GridCellValue',
                       'AreaValue',
                       'HexCellValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location']} })
    variables_present: Optional[list[str]] = Field(default=None, description="""Which variables this asset actually contains. Lets a request skip assets that cannot satisfy it without opening them.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset']} })
    vertical_levels_present: Optional[list[float]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Asset']} })
    stac_collection_id: Optional[str] = Field(default=None, description="""STAC collection identifier, where the product is STAC-published.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product', 'Asset']} })
    stac_item_id: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Asset']} })
    materialization_mode: MaterializationModeEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'ExtractionRequest', 'ToolRun']} })
    cache_expires_at: Optional[datetime ] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Asset']} })
    value_state: ValueMaterializationEnum = Field(default=..., description="""Whether rows for this asset exist in a value table. `registered_only` is the normal case for the asset-centric discovery path.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset']} })
    produced_by_run: Optional[str] = Field(default=None, description="""Identifier of the tool run that registered or materialised this asset. Typed as a string rather than an object reference to keep the catalog and provenance modules independently loadable; the FK is added by the SQL post-processor.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset']} })


class AmbientValue(ConfiguredBaseModel):
    """
    One value of one variable, at one place, over one time interval, from one asset, produced by one run. A property of the environment; not an exposure.
    Abstract: no table of its own. The SQL generator flattens these slots into each concrete child, which is the right physical design — a single polymorphic value table with mostly-null geometry columns would defeat both partitioning and spatial indexing.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'abstract': True,
         'from_schema': 'https://w3id.org/niehs/amadeus/value',
         'rules': [{'description': 'A missing value must say why it is missing. '
                                   'Prevents the failure mode where nodata and a '
                                   'genuine zero are indistinguishable downstream.',
                    'postconditions': {'slot_conditions': {'null_semantics': {'any_of': [{'equals_string': 'structural_null'},
                                                                                         {'equals_string': 'derived_null'}],
                                                                              'name': 'null_semantics'}}},
                    'preconditions': {'slot_conditions': {'value': {'name': 'value',
                                                                    'value_presence': 'ABSENT'}}}},
                   {'description': 'A true zero is a present value, not an absence.',
                    'postconditions': {'slot_conditions': {'value': {'name': 'value',
                                                                     'required': True}}},
                    'preconditions': {'slot_conditions': {'null_semantics': {'equals_string': 'true_zero',
                                                                             'name': 'null_semantics'}}}},
                   {'description': 'A forecast is meaningless without its '
                                   'initialisation time. HRRR\'s "cycle and '
                                   'forecast-hour identity" requirement, enforced.',
                    'postconditions': {'slot_conditions': {'reference_time': {'name': 'reference_time',
                                                                              'required': True}}},
                    'preconditions': {'slot_conditions': {'data_status': {'equals_string': 'forecast',
                                                                          'name': 'data_status'}}}},
                   {'description': 'A superseded row points at its replacement. '
                                   'Revisions create new records; they never mutate or '
                                   'delete old ones.',
                    'postconditions': {'slot_conditions': {'superseded_by': {'name': 'superseded_by',
                                                                             'required': True}}},
                    'preconditions': {'slot_conditions': {'data_status': {'equals_string': 'superseded',
                                                                          'name': 'data_status'}}}}],
         'slot_usage': {'canonical_variable': {'description': 'Denormalised from '
                                                              '`product_variable` on '
                                                              'purpose. Cross-source '
                                                              'queries ("all daily '
                                                              'maximum temperature '
                                                              'within this polygon") '
                                                              'are the common case, '
                                                              'and making them a '
                                                              'two-hop join is a '
                                                              'performance tax on the '
                                                              'query the whole '
                                                              'architecture exists to '
                                                              'serve.',
                                               'name': 'canonical_variable',
                                               'required': True},
                        'data_status': {'description': 'Per-row, not per-product. The '
                                                       'AQS/AirNow rule requires it: a '
                                                       'preliminary AirNow value and a '
                                                       'quality-controlled AQS value '
                                                       'for the same monitor, '
                                                       'parameter and hour must be '
                                                       'able to coexist as distinct '
                                                       'rows.',
                                        'name': 'data_status',
                                        'required': True},
                        'null_semantics': {'name': 'null_semantics', 'required': True},
                        'product_variable': {'description': 'Which source delivery '
                                                            'this is. Carries the '
                                                            'native units, the CF '
                                                            'metadata and the '
                                                            'aggregation — so the row '
                                                            'does not have to.',
                                             'name': 'product_variable',
                                             'required': True},
                        'source_system': {'name': 'source_system', 'required': True},
                        'valid_time_start': {'name': 'valid_time_start',
                                             'required': True},
                        'value': {'description': 'The value in the canonical '
                                                 "variable's units. Null when "
                                                 '`null_semantics` explains why.',
                                  'name': 'value'}},
         'title': 'Ambient Value'})

    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    product_variable: str = Field(default=..., description="""Which source delivery this is. Carries the native units, the CF metadata and the aggregation — so the row does not have to.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    canonical_variable: str = Field(default=..., description="""Denormalised from `product_variable` on purpose. Cross-source queries (\"all daily maximum temperature within this polygon\") are the common case, and making them a two-hop join is a performance tax on the query the whole architecture exists to serve.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable', 'AmbientValue']} })
    asset: Optional[str] = Field(default=None, description="""The byte stream this value came from. Every number resolves to a file and a hash — half of objective O-02's \"every derived output resolves to source assets and processing runs\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue', 'VectorFeature']} })
    processing_run: Optional[str] = Field(default=None, description="""Identifier of the `ToolRun` that produced this value. The other half of O-02. A plain string rather than an object reference so the value and provenance modules stay independently loadable; the SQL post-processor adds the foreign key.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue', 'VectorFeature']} })
    value: Optional[float] = Field(default=None, description="""The value in the canonical variable's units. Null when `null_semantics` explains why.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    value_unit_ucum: Optional[str] = Field(default=None, description="""Units of `value`, denormalised from the canonical variable. Redundant by design: a value row that travels out of the database as CSV or Parquet must not lose its units on the way.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    native_value: Optional[float] = Field(default=None, description="""The value exactly as the source shipped it, before scale, offset and unit conversion. Kept so a conversion bug is discoverable after the fact instead of being baked in irreversibly.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    native_value_unit_ucum: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    valid_time_start: datetime  = Field(default=..., description="""Inclusive start of the interval the value is valid for. Left-closed, right-open by default (`[start, end)`) — declared here once so no individual dataset has to litigate it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    valid_time_end: Optional[datetime ] = Field(default=None, description="""Exclusive end of the validity interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    reference_time: Optional[datetime ] = Field(default=None, description="""Model initialisation / cycle time, distinct from valid time. Required for HRRR and any forecast product: \"valid versus reference time\" is called out explicitly in the P0 subdaily work.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    retrieval_time_utc: Optional[datetime ] = Field(default=None, description="""When amadeus obtained the value. Required by the AQS/AirNow rule: with revisable sources, \"when we asked\" is part of the value's identity.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    vertical_level: Optional[float] = Field(default=None, description="""Pressure or height level for multi-level products (NARR, MERRA-2, GEOS-CF). Part of the value's identity, not an attribute of it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    vertical_level_unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition', 'AmbientValue']} })
    quality_flag: Optional[str] = Field(default=None, description="""The source's quality flag, verbatim, interpreted against the `quality_flag_vocabulary` on the product variable. Never normalised on ingest — normalising discards information, and the vocabularies do not align.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    data_status: DataStatusEnum = Field(default=..., description="""Per-row, not per-product. The AQS/AirNow rule requires it: a preliminary AirNow value and a quality-controlled AQS value for the same monitor, parameter and hour must be able to coexist as distinct rows.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    source_system: str = Field(default=..., description="""Which system supplied this row (`aqs`, `airnow`). Required on every row by the harmonization rule so preliminary and quality-controlled values for the same monitor-hour coexist rather than overwrite.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue'],
         'examples': [{'value': 'aqs'}, {'value': 'airnow'}]} })
    source_version: Optional[str] = Field(default=None, description="""The source's own version or revision identifier for this value, where it publishes one.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    null_semantics: NullSemanticsEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    superseded_by: Optional[str] = Field(default=None, description="""Identifier of the row that replaces this one. Revisions append; they do not mutate.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })


class StationObservation(AmbientValue):
    """
    A value from a fixed instrument with a persistent identity: EPA AQS, AirNow, IMPROVE, USGS water sites.
    The distinguishing feature is not the point geometry — it is that the *instrument* is an entity with a history. Monitors move, get replaced, and report the same parameter through several collocated units (the AQS POC). A grid cell has none of that. Collapsing stations into a generic point table loses the keys that make a revision traceable.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/niehs/amadeus/value',
         'slot_usage': {'poc': {'description': 'Parameter Occurrence Code — which of '
                                               'several collocated monitors measuring '
                                               'the same parameter this is. Part of '
                                               'the AQS primary key and routinely '
                                               'dropped by naive ingests, which then '
                                               'silently pick one monitor per site.',
                                'name': 'poc'},
                        'station_geom_wkt': {'name': 'station_geom_wkt',
                                             'required': True},
                        'station_id': {'name': 'station_id', 'required': True},
                        'station_valid_from': {'description': 'Station moves are '
                                                              'modelled as a validity '
                                                              'interval on the '
                                                              "observation's station "
                                                              'identity rather than by '
                                                              'mutating the station. '
                                                              '"Station moves/POC '
                                                              'changes" is a named '
                                                              "edge case in the plan's "
                                                              'test matrix.',
                                               'name': 'station_valid_from'}},
         'title': 'Station Observation'})

    station_id: str = Field(default=..., description="""The source's site identifier — an AQS state+county+site key, an IMPROVE site code, a USGS gauge number.""", json_schema_extra = { "linkml_meta": {'domain_of': ['StationObservation'], 'examples': [{'value': '37-063-0015'}]} })
    station_name: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['StationObservation']} })
    monitor_id: Optional[str] = Field(default=None, description="""Instrument identity, where distinct from the site.""", json_schema_extra = { "linkml_meta": {'domain_of': ['StationObservation']} })
    parameter_code: Optional[str] = Field(default=None, description="""The source's parameter code, retained verbatim alongside the canonical variable because it is part of the source's primary key.""", json_schema_extra = { "linkml_meta": {'domain_of': ['StationObservation'], 'examples': [{'value': '88101'}]} })
    poc: Optional[int] = Field(default=None, description="""Parameter Occurrence Code — which of several collocated monitors measuring the same parameter this is. Part of the AQS primary key and routinely dropped by naive ingests, which then silently pick one monitor per site.""", json_schema_extra = { "linkml_meta": {'domain_of': ['StationObservation']} })
    sampling_duration_iso: Optional[str] = Field(default=None, description="""The instrument's integration time — distinct from the reporting resolution. A 1-hour reported value from a 24-hour filter sample is not an hourly measurement.""", json_schema_extra = { "linkml_meta": {'domain_of': ['StationObservation']} })
    station_geom_wkt: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['StationObservation']} })
    srid: Optional[int] = Field(default=None, description="""Numeric spatial reference identifier, derived from `crs`. Materialised because `ST_SetSRID` takes an integer and the geometry views need it without a lookup.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product',
                       'GridDefinition',
                       'Asset',
                       'StationObservation',
                       'GridCellValue',
                       'AreaValue',
                       'HexCellValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location']} })
    elevation_m: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['StationObservation']} })
    station_valid_from: Optional[date] = Field(default=None, description="""Station moves are modelled as a validity interval on the observation's station identity rather than by mutating the station. \"Station moves/POC changes\" is a named edge case in the plan's test matrix.""", json_schema_extra = { "linkml_meta": {'domain_of': ['StationObservation']} })
    station_valid_to: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['StationObservation']} })
    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    product_variable: str = Field(default=..., description="""Which source delivery this is. Carries the native units, the CF metadata and the aggregation — so the row does not have to.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    canonical_variable: str = Field(default=..., description="""Denormalised from `product_variable` on purpose. Cross-source queries (\"all daily maximum temperature within this polygon\") are the common case, and making them a two-hop join is a performance tax on the query the whole architecture exists to serve.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable', 'AmbientValue']} })
    asset: Optional[str] = Field(default=None, description="""The byte stream this value came from. Every number resolves to a file and a hash — half of objective O-02's \"every derived output resolves to source assets and processing runs\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue', 'VectorFeature']} })
    processing_run: Optional[str] = Field(default=None, description="""Identifier of the `ToolRun` that produced this value. The other half of O-02. A plain string rather than an object reference so the value and provenance modules stay independently loadable; the SQL post-processor adds the foreign key.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue', 'VectorFeature']} })
    value: Optional[float] = Field(default=None, description="""The value in the canonical variable's units. Null when `null_semantics` explains why.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    value_unit_ucum: Optional[str] = Field(default=None, description="""Units of `value`, denormalised from the canonical variable. Redundant by design: a value row that travels out of the database as CSV or Parquet must not lose its units on the way.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    native_value: Optional[float] = Field(default=None, description="""The value exactly as the source shipped it, before scale, offset and unit conversion. Kept so a conversion bug is discoverable after the fact instead of being baked in irreversibly.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    native_value_unit_ucum: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    valid_time_start: datetime  = Field(default=..., description="""Inclusive start of the interval the value is valid for. Left-closed, right-open by default (`[start, end)`) — declared here once so no individual dataset has to litigate it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    valid_time_end: Optional[datetime ] = Field(default=None, description="""Exclusive end of the validity interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    reference_time: Optional[datetime ] = Field(default=None, description="""Model initialisation / cycle time, distinct from valid time. Required for HRRR and any forecast product: \"valid versus reference time\" is called out explicitly in the P0 subdaily work.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    retrieval_time_utc: Optional[datetime ] = Field(default=None, description="""When amadeus obtained the value. Required by the AQS/AirNow rule: with revisable sources, \"when we asked\" is part of the value's identity.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    vertical_level: Optional[float] = Field(default=None, description="""Pressure or height level for multi-level products (NARR, MERRA-2, GEOS-CF). Part of the value's identity, not an attribute of it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    vertical_level_unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition', 'AmbientValue']} })
    quality_flag: Optional[str] = Field(default=None, description="""The source's quality flag, verbatim, interpreted against the `quality_flag_vocabulary` on the product variable. Never normalised on ingest — normalising discards information, and the vocabularies do not align.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    data_status: DataStatusEnum = Field(default=..., description="""Per-row, not per-product. The AQS/AirNow rule requires it: a preliminary AirNow value and a quality-controlled AQS value for the same monitor, parameter and hour must be able to coexist as distinct rows.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    source_system: str = Field(default=..., description="""Which system supplied this row (`aqs`, `airnow`). Required on every row by the harmonization rule so preliminary and quality-controlled values for the same monitor-hour coexist rather than overwrite.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue'],
         'examples': [{'value': 'aqs'}, {'value': 'airnow'}]} })
    source_version: Optional[str] = Field(default=None, description="""The source's own version or revision identifier for this value, where it publishes one.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    null_semantics: NullSemanticsEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    superseded_by: Optional[str] = Field(default=None, description="""Identifier of the row that replaces this one. Revisions append; they do not mutate.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })


class GridCellValue(AmbientValue):
    """
    A value at one cell of one grid — the flattened form of a raster layer. This is the class the SedonaDB decision hangs on: Sedona's raster support is thinner than `terra`'s, so the plan's proposal is to flatten raster to point or polygon and persist as GeoParquet.
    The cell is identified *twice*: by integer grid index (`cell_x`, `cell_y`) and by geometry. The index is the cheap, exact, join-stable key and the one to partition and deduplicate on; the geometry is what spatial predicates need. Storing only geometry makes idempotent re-ingestion a floating-point comparison, which is how duplicate rows appear.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/niehs/amadeus/value',
         'slot_usage': {'cell_centroid_wkt': {'name': 'cell_centroid_wkt',
                                              'required': True},
                        'cell_polygon_wkt': {'description': 'The cell footprint. '
                                                            'Optional: needed for '
                                                            'area-weighted extraction '
                                                            'and for honest polygon '
                                                            'intersection, redundant '
                                                            'for nearest-cell lookup. '
                                                            'Materialising it for a '
                                                            'continental hourly grid '
                                                            'is expensive, so this is '
                                                            'a deliberate per-product '
                                                            'choice, not a default.',
                                             'name': 'cell_polygon_wkt'},
                        'cell_x': {'name': 'cell_x', 'required': True},
                        'cell_y': {'name': 'cell_y', 'required': True},
                        'grid_definition': {'name': 'grid_definition',
                                            'required': True}},
         'title': 'Grid Cell Value',
         'unique_keys': {'cell_observation': {'description': 'One value per variable, '
                                                             'cell, level and valid '
                                                             'time — per source system '
                                                             'and status, so an AirNow '
                                                             'revision does not '
                                                             'collide with the '
                                                             'AQS-equivalent row.',
                                              'unique_key_name': 'cell_observation',
                                              'unique_key_slots': ['product_variable',
                                                                   'grid_definition',
                                                                   'cell_x',
                                                                   'cell_y',
                                                                   'vertical_level',
                                                                   'valid_time_start',
                                                                   'source_system',
                                                                   'data_status']}}})

    grid_definition: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Product', 'GridCellValue']} })
    cell_x: int = Field(default=..., description="""Zero-based column index in the grid.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GridCellValue']} })
    cell_y: int = Field(default=..., description="""Zero-based row index in the grid.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GridCellValue']} })
    cell_centroid_wkt: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['GridCellValue']} })
    cell_polygon_wkt: Optional[str] = Field(default=None, description="""The cell footprint. Optional: needed for area-weighted extraction and for honest polygon intersection, redundant for nearest-cell lookup. Materialising it for a continental hourly grid is expensive, so this is a deliberate per-product choice, not a default.""", json_schema_extra = { "linkml_meta": {'domain_of': ['GridCellValue']} })
    srid: Optional[int] = Field(default=None, description="""Numeric spatial reference identifier, derived from `crs`. Materialised because `ST_SetSRID` takes an integer and the geometry views need it without a lookup.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product',
                       'GridDefinition',
                       'Asset',
                       'StationObservation',
                       'GridCellValue',
                       'AreaValue',
                       'HexCellValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location']} })
    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    product_variable: str = Field(default=..., description="""Which source delivery this is. Carries the native units, the CF metadata and the aggregation — so the row does not have to.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    canonical_variable: str = Field(default=..., description="""Denormalised from `product_variable` on purpose. Cross-source queries (\"all daily maximum temperature within this polygon\") are the common case, and making them a two-hop join is a performance tax on the query the whole architecture exists to serve.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable', 'AmbientValue']} })
    asset: Optional[str] = Field(default=None, description="""The byte stream this value came from. Every number resolves to a file and a hash — half of objective O-02's \"every derived output resolves to source assets and processing runs\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue', 'VectorFeature']} })
    processing_run: Optional[str] = Field(default=None, description="""Identifier of the `ToolRun` that produced this value. The other half of O-02. A plain string rather than an object reference so the value and provenance modules stay independently loadable; the SQL post-processor adds the foreign key.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue', 'VectorFeature']} })
    value: Optional[float] = Field(default=None, description="""The value in the canonical variable's units. Null when `null_semantics` explains why.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    value_unit_ucum: Optional[str] = Field(default=None, description="""Units of `value`, denormalised from the canonical variable. Redundant by design: a value row that travels out of the database as CSV or Parquet must not lose its units on the way.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    native_value: Optional[float] = Field(default=None, description="""The value exactly as the source shipped it, before scale, offset and unit conversion. Kept so a conversion bug is discoverable after the fact instead of being baked in irreversibly.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    native_value_unit_ucum: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    valid_time_start: datetime  = Field(default=..., description="""Inclusive start of the interval the value is valid for. Left-closed, right-open by default (`[start, end)`) — declared here once so no individual dataset has to litigate it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    valid_time_end: Optional[datetime ] = Field(default=None, description="""Exclusive end of the validity interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    reference_time: Optional[datetime ] = Field(default=None, description="""Model initialisation / cycle time, distinct from valid time. Required for HRRR and any forecast product: \"valid versus reference time\" is called out explicitly in the P0 subdaily work.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    retrieval_time_utc: Optional[datetime ] = Field(default=None, description="""When amadeus obtained the value. Required by the AQS/AirNow rule: with revisable sources, \"when we asked\" is part of the value's identity.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    vertical_level: Optional[float] = Field(default=None, description="""Pressure or height level for multi-level products (NARR, MERRA-2, GEOS-CF). Part of the value's identity, not an attribute of it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    vertical_level_unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition', 'AmbientValue']} })
    quality_flag: Optional[str] = Field(default=None, description="""The source's quality flag, verbatim, interpreted against the `quality_flag_vocabulary` on the product variable. Never normalised on ingest — normalising discards information, and the vocabularies do not align.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    data_status: DataStatusEnum = Field(default=..., description="""Per-row, not per-product. The AQS/AirNow rule requires it: a preliminary AirNow value and a quality-controlled AQS value for the same monitor, parameter and hour must be able to coexist as distinct rows.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    source_system: str = Field(default=..., description="""Which system supplied this row (`aqs`, `airnow`). Required on every row by the harmonization rule so preliminary and quality-controlled values for the same monitor-hour coexist rather than overwrite.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue'],
         'examples': [{'value': 'aqs'}, {'value': 'airnow'}]} })
    source_version: Optional[str] = Field(default=None, description="""The source's own version or revision identifier for this value, where it publishes one.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    null_semantics: NullSemanticsEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    superseded_by: Optional[str] = Field(default=None, description="""Identifier of the row that replaces this one. Revisions append; they do not mutate.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })


class AreaValue(AmbientValue):
    """
    A value attached to a named or delineated polygon: HUC watersheds, EPA ecoregions, county-level NEI emissions, USDM drought polygons, NOAA HMS smoke plumes.
    Two sub-cases that must not be merged, distinguished by `area_role`: an *administrative* area whose identity is external and stable (a county FIPS), and an *episodic* polygon that exists only because something happened there (a smoke plume on one day). Aggregating across the second as if it were the first produces nonsense.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/niehs/amadeus/value',
         'slot_usage': {'area_geom_wkt': {'name': 'area_geom_wkt', 'required': True},
                        'area_id': {'name': 'area_id', 'required': True},
                        'area_km2': {'description': 'Materialised area. Needed to make '
                                                    'extensive values (an emission '
                                                    'mass) convertible to intensive '
                                                    'ones (a flux density) without '
                                                    'recomputing geodesic area per '
                                                    'query.',
                                     'name': 'area_km2'},
                        'area_role': {'name': 'area_role', 'required': True},
                        'area_type': {'name': 'area_type', 'required': True}},
         'title': 'Area Value'})

    area_id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['AreaValue']} })
    area_type: AreaTypeEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['AreaValue']} })
    area_role: AreaRoleEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['AreaValue']} })
    area_code: Optional[str] = Field(default=None, description="""The external code identifying the area.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AreaValue'],
         'examples': [{'value': '37063'}, {'value': '030202'}]} })
    area_name: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AreaValue']} })
    area_geom_wkt: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['AreaValue']} })
    srid: Optional[int] = Field(default=None, description="""Numeric spatial reference identifier, derived from `crs`. Materialised because `ST_SetSRID` takes an integer and the geometry views need it without a lookup.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product',
                       'GridDefinition',
                       'Asset',
                       'StationObservation',
                       'GridCellValue',
                       'AreaValue',
                       'HexCellValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location']} })
    area_km2: Optional[float] = Field(default=None, description="""Materialised area. Needed to make extensive values (an emission mass) convertible to intensive ones (a flux density) without recomputing geodesic area per query.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AreaValue']} })
    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    product_variable: str = Field(default=..., description="""Which source delivery this is. Carries the native units, the CF metadata and the aggregation — so the row does not have to.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    canonical_variable: str = Field(default=..., description="""Denormalised from `product_variable` on purpose. Cross-source queries (\"all daily maximum temperature within this polygon\") are the common case, and making them a two-hop join is a performance tax on the query the whole architecture exists to serve.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable', 'AmbientValue']} })
    asset: Optional[str] = Field(default=None, description="""The byte stream this value came from. Every number resolves to a file and a hash — half of objective O-02's \"every derived output resolves to source assets and processing runs\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue', 'VectorFeature']} })
    processing_run: Optional[str] = Field(default=None, description="""Identifier of the `ToolRun` that produced this value. The other half of O-02. A plain string rather than an object reference so the value and provenance modules stay independently loadable; the SQL post-processor adds the foreign key.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue', 'VectorFeature']} })
    value: Optional[float] = Field(default=None, description="""The value in the canonical variable's units. Null when `null_semantics` explains why.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    value_unit_ucum: Optional[str] = Field(default=None, description="""Units of `value`, denormalised from the canonical variable. Redundant by design: a value row that travels out of the database as CSV or Parquet must not lose its units on the way.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    native_value: Optional[float] = Field(default=None, description="""The value exactly as the source shipped it, before scale, offset and unit conversion. Kept so a conversion bug is discoverable after the fact instead of being baked in irreversibly.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    native_value_unit_ucum: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    valid_time_start: datetime  = Field(default=..., description="""Inclusive start of the interval the value is valid for. Left-closed, right-open by default (`[start, end)`) — declared here once so no individual dataset has to litigate it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    valid_time_end: Optional[datetime ] = Field(default=None, description="""Exclusive end of the validity interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    reference_time: Optional[datetime ] = Field(default=None, description="""Model initialisation / cycle time, distinct from valid time. Required for HRRR and any forecast product: \"valid versus reference time\" is called out explicitly in the P0 subdaily work.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    retrieval_time_utc: Optional[datetime ] = Field(default=None, description="""When amadeus obtained the value. Required by the AQS/AirNow rule: with revisable sources, \"when we asked\" is part of the value's identity.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    vertical_level: Optional[float] = Field(default=None, description="""Pressure or height level for multi-level products (NARR, MERRA-2, GEOS-CF). Part of the value's identity, not an attribute of it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    vertical_level_unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition', 'AmbientValue']} })
    quality_flag: Optional[str] = Field(default=None, description="""The source's quality flag, verbatim, interpreted against the `quality_flag_vocabulary` on the product variable. Never normalised on ingest — normalising discards information, and the vocabularies do not align.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    data_status: DataStatusEnum = Field(default=..., description="""Per-row, not per-product. The AQS/AirNow rule requires it: a preliminary AirNow value and a quality-controlled AQS value for the same monitor, parameter and hour must be able to coexist as distinct rows.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    source_system: str = Field(default=..., description="""Which system supplied this row (`aqs`, `airnow`). Required on every row by the harmonization rule so preliminary and quality-controlled values for the same monitor-hour coexist rather than overwrite.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue'],
         'examples': [{'value': 'aqs'}, {'value': 'airnow'}]} })
    source_version: Optional[str] = Field(default=None, description="""The source's own version or revision identifier for this value, where it publishes one.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    null_semantics: NullSemanticsEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    superseded_by: Optional[str] = Field(default=None, description="""Identifier of the row that replaces this one. Revisions append; they do not mutate.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })


class HexCellValue(AmbientValue):
    """
    A value aggregated to an H3 cell — the harmonization target for the C-HER collaboration (objective O-09).
    Hexification is lossy and the loss must be recorded, not assumed. Three slots do that: `source_support_type` (what was aggregated), `coverage_fraction` (how much of the hex the source actually covered) and `hexification_method` (how). A hex value whose provenance says \"area_weighted_mean from raster_grid_cell at 0.62 coverage\" is usable; the same number without them is not.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/niehs/amadeus/value',
         'rules': [{'description': 'A hex covered less than half by its source must be '
                                   'flagged. Partial coverage at the edge of a '
                                   "product's extent is the standard way a "
                                   'plausible-looking hex value turns out to be mostly '
                                   'nothing.',
                    'postconditions': {'slot_conditions': {'quality_flag': {'name': 'quality_flag',
                                                                            'required': True}}},
                    'preconditions': {'slot_conditions': {'coverage_fraction': {'maximum_value': 0.5,
                                                                                'name': 'coverage_fraction'}}}}],
         'slot_usage': {'coverage_fraction': {'name': 'coverage_fraction',
                                              'required': True},
                        'h3_cell': {'name': 'h3_cell', 'required': True},
                        'h3_resolution': {'name': 'h3_resolution', 'required': True},
                        'hexification_method': {'name': 'hexification_method',
                                                'required': True},
                        'source_support_type': {'name': 'source_support_type',
                                                'required': True}},
         'title': 'Hex Cell Value'})

    h3_cell: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['HexCellValue']} })
    h3_resolution: int = Field(default=..., ge=0, le=15, json_schema_extra = { "linkml_meta": {'domain_of': ['HexCellValue']} })
    hex_centroid_wkt: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['HexCellValue']} })
    srid: Optional[int] = Field(default=None, description="""Numeric spatial reference identifier, derived from `crs`. Materialised because `ST_SetSRID` takes an integer and the geometry views need it without a lookup.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product',
                       'GridDefinition',
                       'Asset',
                       'StationObservation',
                       'GridCellValue',
                       'AreaValue',
                       'HexCellValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location']} })
    source_support_type: SpatialSupportTypeEnum = Field(default=..., description="""The support type that was aggregated into this hex.""", json_schema_extra = { "linkml_meta": {'domain_of': ['HexCellValue']} })
    hexification_method: AggregationMethodEnum = Field(default=..., description="""How source supports were combined into the hex value. Must be legal for the canonical variable's extensivity — a population count hexifies by `sum`, a temperature by `area_weighted_mean`, and swapping them is a silent error.""", json_schema_extra = { "linkml_meta": {'domain_of': ['HexCellValue']} })
    coverage_fraction: float = Field(default=..., description="""Fraction of the hex actually covered by contributing source support.""", ge=0.0, le=1.0, json_schema_extra = { "linkml_meta": {'domain_of': ['HexCellValue', 'AmbientValueAtLocation']} })
    contributing_cell_count: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['HexCellValue']} })
    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    product_variable: str = Field(default=..., description="""Which source delivery this is. Carries the native units, the CF metadata and the aggregation — so the row does not have to.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    canonical_variable: str = Field(default=..., description="""Denormalised from `product_variable` on purpose. Cross-source queries (\"all daily maximum temperature within this polygon\") are the common case, and making them a two-hop join is a performance tax on the query the whole architecture exists to serve.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable', 'AmbientValue']} })
    asset: Optional[str] = Field(default=None, description="""The byte stream this value came from. Every number resolves to a file and a hash — half of objective O-02's \"every derived output resolves to source assets and processing runs\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue', 'VectorFeature']} })
    processing_run: Optional[str] = Field(default=None, description="""Identifier of the `ToolRun` that produced this value. The other half of O-02. A plain string rather than an object reference so the value and provenance modules stay independently loadable; the SQL post-processor adds the foreign key.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue', 'VectorFeature']} })
    value: Optional[float] = Field(default=None, description="""The value in the canonical variable's units. Null when `null_semantics` explains why.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    value_unit_ucum: Optional[str] = Field(default=None, description="""Units of `value`, denormalised from the canonical variable. Redundant by design: a value row that travels out of the database as CSV or Parquet must not lose its units on the way.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    native_value: Optional[float] = Field(default=None, description="""The value exactly as the source shipped it, before scale, offset and unit conversion. Kept so a conversion bug is discoverable after the fact instead of being baked in irreversibly.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    native_value_unit_ucum: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    valid_time_start: datetime  = Field(default=..., description="""Inclusive start of the interval the value is valid for. Left-closed, right-open by default (`[start, end)`) — declared here once so no individual dataset has to litigate it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    valid_time_end: Optional[datetime ] = Field(default=None, description="""Exclusive end of the validity interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    reference_time: Optional[datetime ] = Field(default=None, description="""Model initialisation / cycle time, distinct from valid time. Required for HRRR and any forecast product: \"valid versus reference time\" is called out explicitly in the P0 subdaily work.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    retrieval_time_utc: Optional[datetime ] = Field(default=None, description="""When amadeus obtained the value. Required by the AQS/AirNow rule: with revisable sources, \"when we asked\" is part of the value's identity.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    vertical_level: Optional[float] = Field(default=None, description="""Pressure or height level for multi-level products (NARR, MERRA-2, GEOS-CF). Part of the value's identity, not an attribute of it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    vertical_level_unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition', 'AmbientValue']} })
    quality_flag: Optional[str] = Field(default=None, description="""The source's quality flag, verbatim, interpreted against the `quality_flag_vocabulary` on the product variable. Never normalised on ingest — normalising discards information, and the vocabularies do not align.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    data_status: DataStatusEnum = Field(default=..., description="""Per-row, not per-product. The AQS/AirNow rule requires it: a preliminary AirNow value and a quality-controlled AQS value for the same monitor, parameter and hour must be able to coexist as distinct rows.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    source_system: str = Field(default=..., description="""Which system supplied this row (`aqs`, `airnow`). Required on every row by the harmonization rule so preliminary and quality-controlled values for the same monitor-hour coexist rather than overwrite.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue'],
         'examples': [{'value': 'aqs'}, {'value': 'airnow'}]} })
    source_version: Optional[str] = Field(default=None, description="""The source's own version or revision identifier for this value, where it publishes one.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    null_semantics: NullSemanticsEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    superseded_by: Optional[str] = Field(default=None, description="""Identifier of the row that replaces this one. Revisions append; they do not mutate.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })


class VectorFeature(ConfiguredBaseModel):
    """
    A reference geometry with attributes but no measured value over time: SEDAC gROADS road segments, hydrography lines, building footprints.
    Deliberately **not** an `AmbientValue`. These are inputs to density and distance covariates, not observations, and they have no valid-time interval in any meaningful sense. The distinction matters because the legal operations differ: you compute a length or a distance from these, never a mean.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/niehs/amadeus/value',
         'slot_usage': {'feature_geom_wkt': {'name': 'feature_geom_wkt',
                                             'required': True},
                        'geometry_type': {'name': 'geometry_type', 'required': True},
                        'product': {'name': 'product', 'required': True}},
         'title': 'Vector Feature'})

    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    product: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable', 'Asset', 'VectorFeature']} })
    feature_id: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['VectorFeature']} })
    feature_type: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['VectorFeature'], 'examples': [{'value': 'road_segment'}]} })
    geometry_type: GeometryTypeEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['VectorFeature', 'LocationSet']} })
    feature_geom_wkt: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['VectorFeature']} })
    srid: Optional[int] = Field(default=None, description="""Numeric spatial reference identifier, derived from `crs`. Materialised because `ST_SetSRID` takes an integer and the geometry views need it without a lookup.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product',
                       'GridDefinition',
                       'Asset',
                       'StationObservation',
                       'GridCellValue',
                       'AreaValue',
                       'HexCellValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location']} })
    feature_attributes: Optional[str] = Field(default=None, description="""Source attributes as a JSON object string. Deliberately opaque: road classifications and similar source-specific schemas should not be forced into the core model, and promoting one to a first-class slot is a decision to take when a real query needs it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['VectorFeature']} })
    length_m: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['VectorFeature']} })
    asset: Optional[str] = Field(default=None, description="""The byte stream this value came from. Every number resolves to a file and a hash — half of objective O-02's \"every derived output resolves to source assets and processing runs\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue', 'VectorFeature']} })
    processing_run: Optional[str] = Field(default=None, description="""Identifier of the `ToolRun` that produced this value. The other half of O-02. A plain string rather than an object reference so the value and provenance modules stay independently loadable; the SQL post-processor adds the foreign key.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue', 'VectorFeature']} })


class LocationSet(ConfiguredBaseModel):
    """
    A user-supplied collection of locations — the `locs` argument, promoted to an entity. Carries the identifier field name (`locs_id`), the CRS the user supplied, and a PHI declaration.
    `phi_status` defaults to `no_phi` and is the gate on everything else: if a location set is flagged, results derived from it must not be written to shared catalog tables or embedded in an exported EnVar record, whose `phi_status` is a required field precisely so this cannot be left implicit.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/niehs/amadeus/request',
         'slot_usage': {'crs': {'description': 'Declared, never assumed. '
                                               '`calculate_covariates()` currently '
                                               'reprojects `locs` to `crs(from)` '
                                               'silently; an undeclared input CRS is '
                                               'the most common way a spatial join '
                                               'goes quietly wrong.',
                                'name': 'crs',
                                'required': True},
                        'locs_id_field': {'description': "Name of the user's "
                                                         'identifier column. amadeus '
                                                         'already takes this as '
                                                         '`locs_id`; recording it '
                                                         'means the output column '
                                                         'names are derivable rather '
                                                         'than conventional.',
                                          'examples': [{'value': 'site_id'}],
                                          'name': 'locs_id_field',
                                          'required': True},
                        'phi_status': {'name': 'phi_status', 'required': True}},
         'title': 'Location Set'})

    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    name: Optional[str] = Field(default=None, description="""A short machine-friendly name.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'LocationSet',
                       'ExtractionRequest']} })
    description: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource', 'Product', 'CanonicalVariable', 'LocationSet'],
         'slot_uri': 'dcterms:description'} })
    locs_id_field: str = Field(default=..., description="""Name of the user's identifier column. amadeus already takes this as `locs_id`; recording it means the output column names are derivable rather than conventional.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LocationSet'], 'examples': [{'value': 'site_id'}]} })
    crs: str = Field(default=..., description="""Declared, never assumed. `calculate_covariates()` currently reprojects `locs` to `crs(from)` silently; an undeclared input CRS is the most common way a spatial join goes quietly wrong.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product', 'GridDefinition', 'LocationSet'],
         'exact_mappings': ['envar:crs', 'hew:coordinate_reference_system_uri'],
         'examples': [{'value': 'EPSG:4326'}, {'value': 'EPSG:5070'}]} })
    srid: Optional[int] = Field(default=None, description="""Numeric spatial reference identifier, derived from `crs`. Materialised because `ST_SetSRID` takes an integer and the geometry views need it without a lookup.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product',
                       'GridDefinition',
                       'Asset',
                       'StationObservation',
                       'GridCellValue',
                       'AreaValue',
                       'HexCellValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location']} })
    geometry_type: Optional[GeometryTypeEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['VectorFeature', 'LocationSet']} })
    location_count: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['LocationSet']} })
    phi_status: PhiStatusEnum = Field(default=PhiStatusEnum.no_phi, description="""Whether these locations are or derive from protected health information. Gates persistence and export. Same slot name, range and value set as EnVar's required `phi_status`, so an exported record carries it verbatim.""", json_schema_extra = { "linkml_meta": {'domain_of': ['LocationSet'],
         'exact_mappings': ['envar:phi_status'],
         'ifabsent': 'string(no_phi)'} })
    provided_by: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['LocationSet']} })
    created_at: Optional[datetime ] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['LocationSet']} })

    @field_validator('crs')
    def pattern_crs(cls, v):
        pattern=re.compile(r"^[A-Za-z]+:[0-9]+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid crs format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid crs format: {v}"
            raise ValueError(err_msg)
        return v


class Location(ConfiguredBaseModel):
    """
    One location in a set, with an optional validity interval.
    `valid_from` / `valid_to` exist because a residential address is not timeless. Address histories, known travel intervals and synthetic residence periods all need them, and without them a value is joined to a place the subject may not have occupied on that date. amadeus does not need to model *why* the interval exists — that is the health layer's business — only to honour it in the join.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/niehs/amadeus/request',
         'slot_usage': {'location_geom_wkt': {'name': 'location_geom_wkt',
                                              'required': True},
                        'location_key': {'description': "The user's own identifier "
                                                        'value, preserved verbatim.',
                                         'name': 'location_key',
                                         'required': True},
                        'location_set': {'name': 'location_set', 'required': True}},
         'title': 'Location'})

    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    location_set: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Location', 'ExtractionRequest']} })
    location_key: str = Field(default=..., description="""The user's own identifier value, preserved verbatim.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Location']} })
    location_geom_wkt: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Location']} })
    srid: Optional[int] = Field(default=None, description="""Numeric spatial reference identifier, derived from `crs`. Materialised because `ST_SetSRID` takes an integer and the geometry views need it without a lookup.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Product',
                       'GridDefinition',
                       'Asset',
                       'StationObservation',
                       'GridCellValue',
                       'AreaValue',
                       'HexCellValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location']} })
    buffer_radius_m: Optional[float] = Field(default=None, description="""Buffer radius in metres. Metres, explicitly — amadeus currently interprets `radius` in the units of the *projected* geometry's CRS, which for a geographic CRS means degrees, and the docs describe it as metres. Declaring the unit in the schema removes the ambiguity.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['Location', 'ExtractionRequest', 'AmbientValueAtLocation'],
         'exact_mappings': ['envar:extraction_buffer_m']} })
    valid_from: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Location']} })
    valid_to: Optional[date] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Location']} })
    target_geography_type: Optional[TargetGeographyTypeEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Location', 'ExtractionRequest']} })


class ExtractionRequest(ConfiguredBaseModel):
    """
    A declarative, reproducible specification of an extraction: which variables, over which locations, for which time window, with which buffer, aggregation, weighting and lags.
    The rules below are the ones that make the request *checkable before it runs*, which is the point. The extensivity rule in particular turns the project lead's \"intensive vs extensive should be explicit\" from documentation into a validation error.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/niehs/amadeus/request',
         'rules': [{'description': 'A buffer without an aggregation method is '
                                   'ambiguous — there are now many source values per '
                                   'location and nothing says how they combine. '
                                   'amadeus\'s current default (`fun = "mean"`) is '
                                   'silently wrong for every extensive variable.',
                    'postconditions': {'slot_conditions': {'aggregation_method': {'name': 'aggregation_method',
                                                                                  'required': True}}},
                    'preconditions': {'slot_conditions': {'buffer_radius_m': {'minimum_value': 1e-06,
                                                                              'name': 'buffer_radius_m'}}}},
                   {'description': 'Population weighting must name the population '
                                   'product it weighted by. "Population-weighted" with '
                                   'no stated population raster is not reproducible.',
                    'postconditions': {'slot_conditions': {'weighting_product_variable': {'name': 'weighting_product_variable',
                                                                                          'required': True}}},
                    'preconditions': {'slot_conditions': {'aggregation_method': {'any_of': [{'equals_string': 'population_weighted_mean'}],
                                                                                 'name': 'aggregation_method'}}}},
                   {'description': 'The AQS/AirNow rule, enforced at request time. '
                                   'Mixing preliminary and quality-controlled values '
                                   'into one result requires the user to have '
                                   'explicitly chosen a reconciliation policy. The '
                                   'default is to refuse.',
                    'postconditions': {'slot_conditions': {'source_priority_policy': {'name': 'source_priority_policy',
                                                                                      'required': True}}},
                    'preconditions': {'slot_conditions': {'status_mixing_policy': {'equals_string': 'allow_with_policy',
                                                                                   'name': 'status_mixing_policy'}}}}],
         'slot_usage': {'extraction_method': {'name': 'extraction_method',
                                              'required': True},
                        'generated_sql': {'description': 'The SQL actually issued. '
                                                         'Stored so the result is '
                                                         'auditable against the plan '
                                                         'the optimiser chose, and so '
                                                         'a user can take the query '
                                                         'away and run it themselves — '
                                                         'which is the "same contract '
                                                         'in R, SQL, Python or a '
                                                         'container" promise, made '
                                                         'concrete.',
                                          'name': 'generated_sql'},
                        'location_set': {'name': 'location_set', 'required': True},
                        'request_hash': {'description': 'Hash over the normalised '
                                                        'request. The idempotency key: '
                                                        'the same request re-submitted '
                                                        'resolves to the existing '
                                                        'result set instead of '
                                                        'recomputing it, and a changed '
                                                        'request is visibly a '
                                                        'different request.',
                                         'name': 'request_hash',
                                         'required': True},
                        'time_window_end': {'name': 'time_window_end',
                                            'required': True},
                        'time_window_start': {'name': 'time_window_start',
                                              'required': True}},
         'title': 'Extraction Request'})

    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    name: Optional[str] = Field(default=None, description="""A short machine-friendly name.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'LocationSet',
                       'ExtractionRequest']} })
    location_set: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['Location', 'ExtractionRequest']} })
    requested_canonical_variables: Optional[list[str]] = Field(default=None, description="""Request by canonical variable to let the planner choose a source. The preferred form: the user asks for daily maximum temperature, not for `gridmet.tmmx`.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest']} })
    requested_product_variables: Optional[list[str]] = Field(default=None, description="""Request a specific source delivery, pinning the answer. Required when reproducing a published result, since the planner's choice may change.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest']} })
    time_window_start: datetime  = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest']} })
    time_window_end: datetime  = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest']} })
    temporal_grouping: Optional[TemporalGroupingEnum] = Field(default=None, description="""The `.by_time` argument.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest', 'AmbientValueAtLocation']} })
    buffer_radius_m: Optional[float] = Field(default=None, description="""Buffer radius in metres. Metres, explicitly — amadeus currently interprets `radius` in the units of the *projected* geometry's CRS, which for a geographic CRS means degrees, and the docs describe it as metres. Declaring the unit in the schema removes the ambiguity.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['Location', 'ExtractionRequest', 'AmbientValueAtLocation'],
         'exact_mappings': ['envar:extraction_buffer_m']} })
    extraction_method: ExtractionMethodEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest', 'AmbientValueAtLocation']} })
    aggregation_method: Optional[AggregationMethodEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable',
                       'ExtractionRequest',
                       'AmbientValueAtLocation'],
         'exact_mappings': ['envar:temporal_aggregation_method',
                            'hew:aggregation_method']} })
    weighting_product_variable: Optional[str] = Field(default=None, description="""The product variable used as weights (a population density grid).""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest']} })
    lag_days: Optional[list[int]] = Field(default=None, description="""Lags to compute, in days. `calculate_lagged()` already does this; naming them in the request is what lets the result carry which lag it is.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest']} })
    target_geography_type: Optional[TargetGeographyTypeEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Location', 'ExtractionRequest']} })
    output_orientation: Optional[TableOrientationEnum] = Field(default=TableOrientationEnum.long, json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest'], 'ifabsent': 'string(long)'} })
    materialization_mode: Optional[MaterializationModeEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'ExtractionRequest', 'ToolRun']} })
    source_priority_policy: Optional[str] = Field(default=None, description="""Ordered source preference for reconciliation, e.g. `aqs > airnow`. Required whenever `status_mixing_policy` is `allow_with_policy`.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest'], 'examples': [{'value': 'aqs>airnow'}]} })
    status_mixing_policy: Optional[StatusMixingPolicyEnum] = Field(default=StatusMixingPolicyEnum.refuse, description="""Whether preliminary and quality-controlled values may appear in one result. Defaults to refusing.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest'], 'ifabsent': 'string(refuse)'} })
    strict_extensivity_check: Optional[StrictnessEnum] = Field(default=StrictnessEnum.strict, description="""Whether to reject a request whose aggregation is illegal for the variable's extensivity, or whose variable declares `extensivity: unknown`. Defaults to on: an aggregation that cannot be justified should fail loudly at request time, not produce a plausible number.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest'], 'ifabsent': 'string(strict)'} })
    requested_by: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest']} })
    request_timestamp_utc: Optional[datetime ] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest']} })
    request_hash: str = Field(default=..., description="""Hash over the normalised request. The idempotency key: the same request re-submitted resolves to the existing result set instead of recomputing it, and a changed request is visibly a different request.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest']} })
    generated_sql: Optional[str] = Field(default=None, description="""The SQL actually issued. Stored so the result is auditable against the plan the optimiser chose, and so a user can take the query away and run it themselves — which is the \"same contract in R, SQL, Python or a container\" promise, made concrete.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest']} })


class AmbientValueAtLocation(AmbientValue):
    """
    The output row: an ambient value assigned to a user location for a time interval, with the extraction that produced it recorded alongside. This is what `calculate_covariates()` returns today, plus the metadata it currently drops.
    Not an exposure. The location may be a person's address and the row may carry a cohort key, but the value is a property of the place: swap the person, keep the address, and it does not change.
    What today's output has, that this keeps: location key, time, value. What today's output lacks, that this adds: which product variable and which canonical variable (today encoded positionally in a column name like `weasd_0`), the extraction method and buffer actually used, how many source values contributed, coverage, distance to the contributing station, the quality and status of the inputs, and the run that produced it.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/niehs/amadeus/request',
         'slot_usage': {'contributing_value_count': {'description': 'How many source '
                                                                    'values went into '
                                                                    'this one. A '
                                                                    'buffer mean over '
                                                                    'one cell and over '
                                                                    'four hundred '
                                                                    'cells are '
                                                                    'different claims; '
                                                                    'today both come '
                                                                    'back as an '
                                                                    'undistinguished '
                                                                    'number.',
                                                     'name': 'contributing_value_count'},
                        'distance_to_source_m': {'description': 'Distance to the '
                                                                'contributing station, '
                                                                'for nearest-station '
                                                                'extraction. Paired '
                                                                "with the request's "
                                                                'max-distance setting, '
                                                                'this is what makes a '
                                                                'nearest-station '
                                                                'assignment '
                                                                'defensible.',
                                                 'name': 'distance_to_source_m'},
                        'extraction_method': {'name': 'extraction_method',
                                              'required': True},
                        'extraction_request': {'name': 'extraction_request',
                                               'required': True},
                        'location': {'name': 'location', 'required': True},
                        'output_column_name': {'description': 'The wide-format column '
                                                              'name this value would '
                                                              'occupy, for backward '
                                                              'compatibility with '
                                                              'existing amadeus and '
                                                              'beethoven consumers '
                                                              '(`weasd_0`, '
                                                              '`tmmx_10000`). '
                                                              'Generated from the '
                                                              'request, not parsed '
                                                              'back out of it — the '
                                                              'long form is canonical '
                                                              'and the wide form is a '
                                                              'projection.',
                                               'name': 'output_column_name'}},
         'title': 'Ambient Value at Location'})

    location: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValueAtLocation']} })
    extraction_request: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValueAtLocation']} })
    buffer_radius_m: Optional[float] = Field(default=None, description="""Buffer radius in metres. Metres, explicitly — amadeus currently interprets `radius` in the units of the *projected* geometry's CRS, which for a geographic CRS means degrees, and the docs describe it as metres. Declaring the unit in the schema removes the ambiguity.""", ge=0.0, json_schema_extra = { "linkml_meta": {'domain_of': ['Location', 'ExtractionRequest', 'AmbientValueAtLocation'],
         'exact_mappings': ['envar:extraction_buffer_m']} })
    extraction_method: ExtractionMethodEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest', 'AmbientValueAtLocation']} })
    aggregation_method: Optional[AggregationMethodEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable',
                       'ExtractionRequest',
                       'AmbientValueAtLocation'],
         'exact_mappings': ['envar:temporal_aggregation_method',
                            'hew:aggregation_method']} })
    contributing_value_count: Optional[int] = Field(default=None, description="""How many source values went into this one. A buffer mean over one cell and over four hundred cells are different claims; today both come back as an undistinguished number.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValueAtLocation']} })
    coverage_fraction: Optional[float] = Field(default=None, description="""Fraction of the hex actually covered by contributing source support.""", ge=0.0, le=1.0, json_schema_extra = { "linkml_meta": {'domain_of': ['HexCellValue', 'AmbientValueAtLocation']} })
    distance_to_source_m: Optional[float] = Field(default=None, description="""Distance to the contributing station, for nearest-station extraction. Paired with the request's max-distance setting, this is what makes a nearest-station assignment defensible.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValueAtLocation']} })
    lag_days_applied: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValueAtLocation']} })
    temporal_grouping: Optional[TemporalGroupingEnum] = Field(default=None, description="""The `.by_time` argument.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ExtractionRequest', 'AmbientValueAtLocation']} })
    output_column_name: Optional[str] = Field(default=None, description="""The wide-format column name this value would occupy, for backward compatibility with existing amadeus and beethoven consumers (`weasd_0`, `tmmx_10000`). Generated from the request, not parsed back out of it — the long form is canonical and the wide form is a projection.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValueAtLocation']} })
    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    product_variable: str = Field(default=..., description="""Which source delivery this is. Carries the native units, the CF metadata and the aggregation — so the row does not have to.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    canonical_variable: str = Field(default=..., description="""Denormalised from `product_variable` on purpose. Cross-source queries (\"all daily maximum temperature within this polygon\") are the common case, and making them a two-hop join is a performance tax on the query the whole architecture exists to serve.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProductVariable', 'AmbientValue']} })
    asset: Optional[str] = Field(default=None, description="""The byte stream this value came from. Every number resolves to a file and a hash — half of objective O-02's \"every derived output resolves to source assets and processing runs\".""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue', 'VectorFeature']} })
    processing_run: Optional[str] = Field(default=None, description="""Identifier of the `ToolRun` that produced this value. The other half of O-02. A plain string rather than an object reference so the value and provenance modules stay independently loadable; the SQL post-processor adds the foreign key.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue', 'VectorFeature']} })
    value: Optional[float] = Field(default=None, description="""The value in the canonical variable's units. Null when `null_semantics` explains why.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    value_unit_ucum: Optional[str] = Field(default=None, description="""Units of `value`, denormalised from the canonical variable. Redundant by design: a value row that travels out of the database as CSV or Parquet must not lose its units on the way.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    native_value: Optional[float] = Field(default=None, description="""The value exactly as the source shipped it, before scale, offset and unit conversion. Kept so a conversion bug is discoverable after the fact instead of being baked in irreversibly.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    native_value_unit_ucum: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    valid_time_start: datetime  = Field(default=..., description="""Inclusive start of the interval the value is valid for. Left-closed, right-open by default (`[start, end)`) — declared here once so no individual dataset has to litigate it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    valid_time_end: Optional[datetime ] = Field(default=None, description="""Exclusive end of the validity interval.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    reference_time: Optional[datetime ] = Field(default=None, description="""Model initialisation / cycle time, distinct from valid time. Required for HRRR and any forecast product: \"valid versus reference time\" is called out explicitly in the P0 subdaily work.""", json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'AmbientValue']} })
    retrieval_time_utc: Optional[datetime ] = Field(default=None, description="""When amadeus obtained the value. Required by the AQS/AirNow rule: with revisable sources, \"when we asked\" is part of the value's identity.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    vertical_level: Optional[float] = Field(default=None, description="""Pressure or height level for multi-level products (NARR, MERRA-2, GEOS-CF). Part of the value's identity, not an attribute of it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    vertical_level_unit: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['GridDefinition', 'AmbientValue']} })
    quality_flag: Optional[str] = Field(default=None, description="""The source's quality flag, verbatim, interpreted against the `quality_flag_vocabulary` on the product variable. Never normalised on ingest — normalising discards information, and the vocabularies do not align.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    data_status: DataStatusEnum = Field(default=..., description="""Per-row, not per-product. The AQS/AirNow rule requires it: a preliminary AirNow value and a quality-controlled AQS value for the same monitor, parameter and hour must be able to coexist as distinct rows.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    source_system: str = Field(default=..., description="""Which system supplied this row (`aqs`, `airnow`). Required on every row by the harmonization rule so preliminary and quality-controlled values for the same monitor-hour coexist rather than overwrite.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue'],
         'examples': [{'value': 'aqs'}, {'value': 'airnow'}]} })
    source_version: Optional[str] = Field(default=None, description="""The source's own version or revision identifier for this value, where it publishes one.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    null_semantics: NullSemanticsEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })
    superseded_by: Optional[str] = Field(default=None, description="""Identifier of the row that replaces this one. Revisions append; they do not mutate.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmbientValue']} })


class ToolRun(ConfiguredBaseModel):
    """
    One execution of one amadeus operation, with everything needed to decide whether it can be trusted and whether it can be skipped.
    \"Whether it can be skipped\" is the idempotency requirement: re-running a workflow with the same inputs and configuration should reuse valid outputs and recover from partial failures without silent duplication. That needs `input_file_sha256`, `output_file_sha256`, `run_arguments` and `status` — not a timestamp and a log line.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'prov:Activity',
         'exact_mappings': ['envar:ToolRun'],
         'from_schema': 'https://w3id.org/niehs/amadeus/provenance',
         'rules': [{'description': 'A successful processing or calculation run must '
                                   'state how many rows it produced. Row-count parity '
                                   'against a frozen baseline is the cheapest '
                                   'golden-regression check there is.',
                    'postconditions': {'slot_conditions': {'output_row_count': {'name': 'output_row_count',
                                                                                'required': True}}},
                    'preconditions': {'slot_conditions': {'run_role': {'any_of': [{'equals_string': 'process'},
                                                                                  {'equals_string': 'calculate'}],
                                                                       'name': 'run_role'},
                                                          'status': {'equals_string': 'succeeded',
                                                                     'name': 'status'}}}},
                   {'description': 'Anything downstream of download must name what it '
                                   'consumed. Without this the chain has a hole and '
                                   'provenance terminates in the wrong place.',
                    'postconditions': {'slot_conditions': {'upstream_runs': {'name': 'upstream_runs',
                                                                             'required': True}}},
                    'preconditions': {'slot_conditions': {'run_role': {'any_of': [{'equals_string': 'process'},
                                                                                  {'equals_string': 'calculate'},
                                                                                  {'equals_string': 'harmonize'}],
                                                                       'name': 'run_role'}}}},
                   {'description': 'A failed run must carry diagnostic output. "A '
                                   'failed run is diagnosable and can resume without '
                                   'corrupting accepted outputs" is an operability '
                                   'acceptance criterion, and it is unmeetable if '
                                   'failures record nothing.',
                    'postconditions': {'slot_conditions': {'log_excerpt': {'name': 'log_excerpt',
                                                                           'required': True}}},
                    'preconditions': {'slot_conditions': {'status': {'equals_string': 'failed',
                                                                     'name': 'status'}}}}],
         'slot_usage': {'bytes_transferred': {'description': 'Network bytes for this '
                                                             'run. The benchmark '
                                                             "plan's acceptance target "
                                                             'is "at least 75% fewer '
                                                             'bytes transferred for a '
                                                             'remote subset request '
                                                             'where the upstream '
                                                             'format/API supports '
                                                             'pushdown" — which '
                                                             'requires this to be '
                                                             'measured per run rather '
                                                             'than estimated.',
                                              'name': 'bytes_transferred'},
                        'container_image_digest': {'description': 'Immutable image '
                                                                  'digest, not a tag. '
                                                                  'Tags move; a digest '
                                                                  'is the only thing '
                                                                  'that makes "the '
                                                                  'same container" a '
                                                                  'checkable claim, '
                                                                  'and the plan '
                                                                  'requires digest '
                                                                  'references in run '
                                                                  'manifests.',
                                                   'name': 'container_image_digest'},
                        'function_name': {'description': 'The specific amadeus '
                                                         'function called '
                                                         '(`download_narr`, '
                                                         '`process_narr`, '
                                                         '`calculate_narr`). More '
                                                         'useful than `tool_name` '
                                                         'alone, since one package '
                                                         'version contains many '
                                                         'operations with different '
                                                         'failure modes.',
                                          'name': 'function_name'},
                        'run_arguments': {'description': "The call's arguments as a "
                                                         'JSON object string. The '
                                                         'single field that decides '
                                                         'whether a result is '
                                                         'reproducible. Kept opaque '
                                                         'because the argument sets '
                                                         'differ per function and per '
                                                         'source; validating them is '
                                                         "the `ExtractionRequest`'s "
                                                         'job for the calculate path, '
                                                         'and an adapter contract '
                                                         "test's job for the download "
                                                         'path.',
                                          'name': 'run_arguments'},
                        'run_role': {'name': 'run_role', 'required': True},
                        'run_timestamp_utc': {'name': 'run_timestamp_utc',
                                              'required': True},
                        'status': {'name': 'status', 'required': True},
                        'tool_name': {'ifabsent': 'string(amadeus)',
                                      'name': 'tool_name',
                                      'required': True},
                        'tool_version': {'name': 'tool_version', 'required': True}},
         'title': 'Tool Run'})

    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    run_role: RunRoleEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun']} })
    tool_name: str = Field(default="amadeus", json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun'],
         'exact_mappings': ['envar:tool_name'],
         'ifabsent': 'string(amadeus)'} })
    tool_version: str = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun'],
         'exact_mappings': ['envar:tool_version'],
         'examples': [{'value': '1.3.2.1'}]} })
    function_name: Optional[str] = Field(default=None, description="""The specific amadeus function called (`download_narr`, `process_narr`, `calculate_narr`). More useful than `tool_name` alone, since one package version contains many operations with different failure modes.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun']} })
    run_arguments: Optional[str] = Field(default=None, description="""The call's arguments as a JSON object string. The single field that decides whether a result is reproducible. Kept opaque because the argument sets differ per function and per source; validating them is the `ExtractionRequest`'s job for the calculate path, and an adapter contract test's job for the download path.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun'], 'exact_mappings': ['envar:run_arguments']} })
    container_image_repository: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun'],
         'exact_mappings': ['envar:container_image_repository']} })
    container_image_digest: Optional[str] = Field(default=None, description="""Immutable image digest, not a tag. Tags move; a digest is the only thing that makes \"the same container\" a checkable claim, and the plan requires digest references in run manifests.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun'], 'exact_mappings': ['envar:container_image_digest']} })
    run_timestamp_utc: datetime  = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun'], 'exact_mappings': ['envar:run_timestamp_utc']} })
    run_duration_seconds: Optional[float] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun'], 'exact_mappings': ['envar:run_duration_seconds']} })
    run_environment: Optional[str] = Field(default=None, description="""Runtime environment as a JSON object string — R version, platform, key package versions (`terra`, `sf`, `exactextractr`), and the database engine and version. The engine matters: a SedonaDB result and a DuckDB result of the same request are not guaranteed identical, and the capability matrix the plan calls for is only auditable if each run says which engine ran it.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun']} })
    input_asset_ids: Optional[list[str]] = Field(default=None, description="""Assets consumed by this run.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun']} })
    input_file_sha256: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun'], 'exact_mappings': ['envar:input_file_sha256']} })
    input_row_count: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun'], 'exact_mappings': ['envar:input_row_count']} })
    output_file_sha256: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun'], 'exact_mappings': ['envar:output_file_sha256']} })
    output_row_count: Optional[int] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun'], 'exact_mappings': ['envar:output_row_count']} })
    upstream_runs: Optional[list[str]] = Field(default=None, description="""Identifiers of the runs this one consumed. The DAG edge. Typed as strings rather than object references so the table is self-contained and loadable before its own foreign keys resolve — a run may be recorded before its parents are fully written.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun']} })
    status: RunStatusEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun']} })
    log_excerpt: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun'], 'exact_mappings': ['envar:run_log_excerpt']} })
    materialization_mode: Optional[MaterializationModeEnum] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['Asset', 'ExtractionRequest', 'ToolRun']} })
    bytes_transferred: Optional[int] = Field(default=None, description="""Network bytes for this run. The benchmark plan's acceptance target is \"at least 75% fewer bytes transferred for a remote subset request where the upstream format/API supports pushdown\" — which requires this to be measured per run rather than estimated.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun']} })
    request_count: Optional[int] = Field(default=None, description="""Number of HTTP or API requests issued, for rate-limit accounting.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ToolRun']} })

    @field_validator('container_image_digest')
    def pattern_container_image_digest(cls, v):
        pattern=re.compile(r"^sha256:[0-9a-f]{64}$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid container_image_digest format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid container_image_digest format: {v}"
            raise ValueError(err_msg)
        return v


class ProvenanceChain(ConfiguredBaseModel):
    """
    A materialised walk of `upstream_runs` from a derived value back to its terminus, plus what the terminus is. Stored rather than always recomputed because it is what an exported EnVar record carries, and because the recursive query is expensive to run per row at export time.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'exact_mappings': ['envar:ProvenanceChain'],
         'from_schema': 'https://w3id.org/niehs/amadeus/provenance',
         'slot_usage': {'terminus_type': {'name': 'terminus_type', 'required': True}},
         'title': 'Provenance Chain'})

    id: str = Field(default=..., description="""Stable identifier for this entity within an AmadeusDB instance.""", json_schema_extra = { "linkml_meta": {'domain_of': ['DataSource',
                       'Product',
                       'GridDefinition',
                       'CanonicalVariable',
                       'ProductVariable',
                       'Asset',
                       'AmbientValue',
                       'VectorFeature',
                       'LocationSet',
                       'Location',
                       'ExtractionRequest',
                       'ToolRun',
                       'ProvenanceChain']} })
    chain_steps: Optional[list[str]] = Field(default=None, description="""Run identifiers, ordered from the derived value back to the terminus.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProvenanceChain']} })
    terminus_type: ProvenanceChainTerminusEnum = Field(default=..., json_schema_extra = { "linkml_meta": {'domain_of': ['ProvenanceChain'],
         'exact_mappings': ['envar:provenance_chain_terminus_type']} })
    compatibility_assertions: Optional[list[str]] = Field(default=None, description="""Assertions that consecutive steps were compatible — matching CRS, units, calendar, day boundary. The seam between two steps belongs to neither step, and this is where a mismatch gets recorded instead of silently absorbed.""", json_schema_extra = { "linkml_meta": {'domain_of': ['ProvenanceChain']} })


class AmadeusDatabase(ConfiguredBaseModel):
    """
    Container for a complete or partial AmadeusDB instance. Exists so a catalog snapshot, a sample dataset or an import bundle can be validated as one document with `linkml-validate`, and so the SQL generator has a root from which to reach every table.
    All collections are optional: a catalog-only bundle (the normal shape of a curation pull request) is as valid as a full instance.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'https://w3id.org/niehs/amadeus',
         'title': 'Amadeus Database',
         'tree_root': True})

    schema_version: str = Field(default=..., description="""Version of the AmadeusDB schema a record conforms to, so consumers can branch on schema evolution rather than guess.""", json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase'], 'exact_mappings': ['envar:schema_version']} })
    data_sources: Optional[list[DataSource]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    products: Optional[list[Product]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    grid_definitions: Optional[list[GridDefinition]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    canonical_variables: Optional[list[CanonicalVariable]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    product_variables: Optional[list[ProductVariable]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    assets: Optional[list[Asset]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    station_observations: Optional[list[StationObservation]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    grid_cell_values: Optional[list[GridCellValue]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    area_values: Optional[list[AreaValue]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    hex_cell_values: Optional[list[HexCellValue]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    vector_features: Optional[list[VectorFeature]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    location_sets: Optional[list[LocationSet]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    locations: Optional[list[Location]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    extraction_requests: Optional[list[ExtractionRequest]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    ambient_values_at_location: Optional[list[AmbientValueAtLocation]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    tool_runs: Optional[list[ToolRun]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })
    provenance_chains: Optional[list[ProvenanceChain]] = Field(default=None, json_schema_extra = { "linkml_meta": {'domain_of': ['AmadeusDatabase']} })


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
DataSource.model_rebuild()
Product.model_rebuild()
GridDefinition.model_rebuild()
CanonicalVariable.model_rebuild()
ProductVariable.model_rebuild()
OmopConceptBinding.model_rebuild()
Asset.model_rebuild()
AmbientValue.model_rebuild()
StationObservation.model_rebuild()
GridCellValue.model_rebuild()
AreaValue.model_rebuild()
HexCellValue.model_rebuild()
VectorFeature.model_rebuild()
LocationSet.model_rebuild()
Location.model_rebuild()
ExtractionRequest.model_rebuild()
AmbientValueAtLocation.model_rebuild()
ToolRun.model_rebuild()
ProvenanceChain.model_rebuild()
AmadeusDatabase.model_rebuild()
