# Auto generated from amadeus_schema.yaml by pythongen.py version: 0.0.1
# Generation date: 2026-09-25T06:44:27
# Schema: amadeus-schema
#
# id: https://w3id.org/niehs/amadeus
# description: A candidate data model for the next-generation, database-backed amadeus
#   ("AmadeusDB"). Prototype for the Database-and-Schema agenda item of the
#   Amadeus Next-Generation Maintenance and Modernization plan (v1.0, 2026-09-18).
#
#   Four layers, five modules
#   -------------------------
#   * `amadeus_common`      types, enums, shared slots — and the reconciliation
#                           record against EnVar and HEW
#   * `amadeus_catalog`     what data exists and what it means
#                           (DataSource → Product → ProductVariable →
#                           CanonicalVariable; GridDefinition; Asset)
#   * `amadeus_value`       the data rows, in four spatial shapes
#                           (StationObservation, GridCellValue, AreaValue,
#                           HexCellValue) plus VectorFeature
#   * `amadeus_request`     the query-first contract
#                           (LocationSet, Location, ExtractionRequest,
#                           AmbientValueAtLocation)
#   * `amadeus_provenance`  ToolRun and the derivation DAG
#
#   The three load-bearing claims
#   -----------------------------
#   1. **One schema, not one per source type.** The 24 amadeus sources vary on
#      five orthogonal axes recorded on `Product` and `CanonicalVariable`
#      (spatial support, temporal resolution, value kind, native format,
#      extensivity), and on exactly one axis that needs a different table: what
#      geometry identifies a value. Four value tables cover all of them.
#   2. **`CanonicalVariable` ← `ProductVariable` answers the actual question.**
#      "Is the schema for this variable the same as for the same variable from
#      another source?" Yes at the canonical level, no at the product level, and
#      every reason for the difference is a slot.
#   3. **Extensivity makes aggregation checkable.** Intensive vs extensive is not
#      documentation; it is the precondition on which aggregation methods are
#      legal, enforced by a rule on `ExtractionRequest`.
#
#   Relationship to the neighbouring schemas
#   ----------------------------------------
#   This model sits *between* HEW and EnVar and is designed to be projectable to
#   both, not to replace either:
#
#       HEW Catalog    dataset grain    what exists           ← Product, DataSource roll up
#       AmadeusDB      row grain        the values themselves  ← this schema
#       EnVar          run grain        what one number means  ← Asset + ToolRun + Product project out
#
#   Every slot that has an upstream equivalent carries `exact_mappings` to it.
#   Every enum that extends an upstream one carries `annotations: extends` plus a
#   note on why, so enum reconciliation is a finite list of decisions rather than
#   a diff. Three things this model has that neither upstream does — per-row
#   `data_status`, `VariableExtensivityEnum`, and `GridDefinition` — are candidate
#   contributions upward.
# license: MIT

import dataclasses
import re
from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    time
)
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Union
)

from jsonasobj2 import (
    JsonObj,
    as_dict
)
from linkml_runtime.linkml_model.meta import (
    EnumDefinition,
    PermissibleValue,
    PvFormulaOptions
)
from linkml_runtime.utils.curienamespace import CurieNamespace
from linkml_runtime.utils.enumerations import EnumDefinitionImpl
from linkml_runtime.utils.formatutils import (
    camelcase,
    sfx,
    underscore
)
from linkml_runtime.utils.metamodelcore import (
    bnode,
    empty_dict,
    empty_list
)
from linkml_runtime.utils.slot import Slot
from linkml_runtime.utils.yamlutils import (
    YAMLRoot,
    extended_float,
    extended_int,
    extended_str
)
from rdflib import (
    Namespace,
    URIRef
)

from linkml_runtime.linkml_model.types import Boolean, Date, Datetime, Float, Integer, String, Uri, Uriorcurie
from linkml_runtime.utils.metamodelcore import Bool, URI, URIorCURIE, XSDDate, XSDDateTime

metamodel_version = "1.11.0"
version = "0.1.0"

# Namespaces
AMADEUS = CurieNamespace('amadeus', 'https://w3id.org/niehs/amadeus/')
DCTERMS = CurieNamespace('dcterms', 'http://purl.org/dc/terms/')
ENVAR = CurieNamespace('envar', 'https://w3id.org/linkml/microschemas/envar/')
GEO = CurieNamespace('geo', 'http://www.opengis.net/ont/geosparql#')
HEW = CurieNamespace('hew', 'https://w3id.org/hew/schema/')
LINKML = CurieNamespace('linkml', 'https://w3id.org/linkml/')
PROV = CurieNamespace('prov', 'http://www.w3.org/ns/prov#')
XSD = CurieNamespace('xsd', 'http://www.w3.org/2001/XMLSchema#')
DEFAULT_ = AMADEUS


# Types
class WktLiteral(String):
    """ A geometry serialised as OGC Well-Known Text. Stored as text in every backend; promoted to a native geometry by the generated `*_geo` views via `ST_SetSRID(ST_GeomFromText(...), srid)`. """
    type_class_uri = GEO["wktLiteral"]
    type_class_curie = "geo:wktLiteral"
    type_name = "WktLiteral"
    type_model_uri = AMADEUS.WktLiteral


class Iso8601Duration(String):
    """ An ISO 8601 duration. Used wherever the HEW catalog uses one (it encodes `P3D`, which EnVar's `TemporalResolutionEnum` cannot); the enum-valued companion slot is kept alongside for validation. """
    type_class_uri = XSD["duration"]
    type_class_curie = "xsd:duration"
    type_name = "Iso8601Duration"
    type_model_uri = AMADEUS.Iso8601Duration


class Sha256(String):
    """ A lowercase hex SHA-256 digest. """
    type_class_uri = XSD["string"]
    type_class_curie = "xsd:string"
    type_name = "Sha256"
    type_model_uri = AMADEUS.Sha256


class H3CellIndex(String):
    """ An H3 cell index in its canonical 15-character lowercase hex form. The harmonization target for the C-HER hexification work (objective O-09). """
    type_class_uri = XSD["string"]
    type_class_curie = "xsd:string"
    type_name = "H3CellIndex"
    type_model_uri = AMADEUS.H3CellIndex


# Class references
class DataSourceId(URIorCURIE):
    pass


class ProductId(URIorCURIE):
    pass


class GridDefinitionId(URIorCURIE):
    pass


class CanonicalVariableId(URIorCURIE):
    pass


class ProductVariableId(URIorCURIE):
    pass


class AssetId(URIorCURIE):
    pass


class AmbientValueId(URIorCURIE):
    pass


class StationObservationId(AmbientValueId):
    pass


class GridCellValueId(AmbientValueId):
    pass


class AreaValueId(AmbientValueId):
    pass


class HexCellValueId(AmbientValueId):
    pass


class VectorFeatureId(URIorCURIE):
    pass


class LocationSetId(URIorCURIE):
    pass


class LocationId(URIorCURIE):
    pass


class ExtractionRequestId(URIorCURIE):
    pass


class AmbientValueAtLocationId(AmbientValueId):
    pass


class ToolRunId(URIorCURIE):
    pass


class ProvenanceChainId(URIorCURIE):
    pass


@dataclass(repr=False)
class AmadeusDatabase(YAMLRoot):
    """
    Container for a complete or partial AmadeusDB instance. Exists so a catalog snapshot, a sample dataset or an
    import bundle can be validated as one document with `linkml-validate`, and so the SQL generator has a root from
    which to reach every table.
    All collections are optional: a catalog-only bundle (the normal shape of a curation pull request) is as valid as a
    full instance.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["AmadeusDatabase"]
    class_class_curie: ClassVar[str] = "amadeus:AmadeusDatabase"
    class_name: ClassVar[str] = "AmadeusDatabase"
    class_model_uri: ClassVar[URIRef] = AMADEUS.AmadeusDatabase

    schema_version: str = None
    data_sources: Optional[Union[dict[Union[str, DataSourceId], Union[dict, "DataSource"]], list[Union[dict, "DataSource"]]]] = empty_dict()
    products: Optional[Union[dict[Union[str, ProductId], Union[dict, "Product"]], list[Union[dict, "Product"]]]] = empty_dict()
    grid_definitions: Optional[Union[dict[Union[str, GridDefinitionId], Union[dict, "GridDefinition"]], list[Union[dict, "GridDefinition"]]]] = empty_dict()
    canonical_variables: Optional[Union[dict[Union[str, CanonicalVariableId], Union[dict, "CanonicalVariable"]], list[Union[dict, "CanonicalVariable"]]]] = empty_dict()
    product_variables: Optional[Union[dict[Union[str, ProductVariableId], Union[dict, "ProductVariable"]], list[Union[dict, "ProductVariable"]]]] = empty_dict()
    assets: Optional[Union[dict[Union[str, AssetId], Union[dict, "Asset"]], list[Union[dict, "Asset"]]]] = empty_dict()
    station_observations: Optional[Union[dict[Union[str, StationObservationId], Union[dict, "StationObservation"]], list[Union[dict, "StationObservation"]]]] = empty_dict()
    grid_cell_values: Optional[Union[dict[Union[str, GridCellValueId], Union[dict, "GridCellValue"]], list[Union[dict, "GridCellValue"]]]] = empty_dict()
    area_values: Optional[Union[dict[Union[str, AreaValueId], Union[dict, "AreaValue"]], list[Union[dict, "AreaValue"]]]] = empty_dict()
    hex_cell_values: Optional[Union[dict[Union[str, HexCellValueId], Union[dict, "HexCellValue"]], list[Union[dict, "HexCellValue"]]]] = empty_dict()
    vector_features: Optional[Union[dict[Union[str, VectorFeatureId], Union[dict, "VectorFeature"]], list[Union[dict, "VectorFeature"]]]] = empty_dict()
    location_sets: Optional[Union[dict[Union[str, LocationSetId], Union[dict, "LocationSet"]], list[Union[dict, "LocationSet"]]]] = empty_dict()
    locations: Optional[Union[dict[Union[str, LocationId], Union[dict, "Location"]], list[Union[dict, "Location"]]]] = empty_dict()
    extraction_requests: Optional[Union[dict[Union[str, ExtractionRequestId], Union[dict, "ExtractionRequest"]], list[Union[dict, "ExtractionRequest"]]]] = empty_dict()
    ambient_values_at_location: Optional[Union[dict[Union[str, AmbientValueAtLocationId], Union[dict, "AmbientValueAtLocation"]], list[Union[dict, "AmbientValueAtLocation"]]]] = empty_dict()
    tool_runs: Optional[Union[dict[Union[str, ToolRunId], Union[dict, "ToolRun"]], list[Union[dict, "ToolRun"]]]] = empty_dict()
    provenance_chains: Optional[Union[dict[Union[str, ProvenanceChainId], Union[dict, "ProvenanceChain"]], list[Union[dict, "ProvenanceChain"]]]] = empty_dict()

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.schema_version):
            self.MissingRequiredField("schema_version")
        if not isinstance(self.schema_version, str):
            self.schema_version = str(self.schema_version)

        self._normalize_inlined_as_list(slot_name="data_sources", slot_type=DataSource, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="products", slot_type=Product, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="grid_definitions", slot_type=GridDefinition, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="canonical_variables", slot_type=CanonicalVariable, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="product_variables", slot_type=ProductVariable, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="assets", slot_type=Asset, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="station_observations", slot_type=StationObservation, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="grid_cell_values", slot_type=GridCellValue, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="area_values", slot_type=AreaValue, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="hex_cell_values", slot_type=HexCellValue, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="vector_features", slot_type=VectorFeature, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="location_sets", slot_type=LocationSet, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="locations", slot_type=Location, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="extraction_requests", slot_type=ExtractionRequest, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="ambient_values_at_location", slot_type=AmbientValueAtLocation, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="tool_runs", slot_type=ToolRun, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="provenance_chains", slot_type=ProvenanceChain, key_name="id", keyed=True)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class DataSource(YAMLRoot):
    """
    A provider programme that publishes one or more products: EPA AQS, NASA MODIS, NOAA NARR, Climatology Lab. One row
    per row of the amadeus README source table.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["DataSource"]
    class_class_curie: ClassVar[str] = "amadeus:DataSource"
    class_name: ClassVar[str] = "DataSource"
    class_model_uri: ClassVar[URIRef] = AMADEUS.DataSource

    id: Union[str, DataSourceId] = None
    name: str = None
    label: Optional[str] = None
    description: Optional[str] = None
    producer_institution: Optional[str] = None
    homepage: Optional[Union[str, URI]] = None
    access_protocol: Optional[Union[str, "AccessProtocolEnum"]] = None
    requires_authentication: Optional[Union[bool, Bool]] = None
    auth_mechanism: Optional[str] = None
    rate_limit_requests_per_second: Optional[float] = None
    license_spdx: Optional[str] = None
    citation_apa: Optional[str] = None
    doi: Optional[str] = None
    amadeus_function_suffix: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, DataSourceId):
            self.id = DataSourceId(self.id)

        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, str):
            self.name = str(self.name)

        if self.label is not None and not isinstance(self.label, str):
            self.label = str(self.label)

        if self.description is not None and not isinstance(self.description, str):
            self.description = str(self.description)

        if self.producer_institution is not None and not isinstance(self.producer_institution, str):
            self.producer_institution = str(self.producer_institution)

        if self.homepage is not None and not isinstance(self.homepage, URI):
            self.homepage = URI(self.homepage)

        if self.access_protocol is not None and not isinstance(self.access_protocol, AccessProtocolEnum):
            self.access_protocol = AccessProtocolEnum(self.access_protocol)

        if self.requires_authentication is not None and not isinstance(self.requires_authentication, Bool):
            self.requires_authentication = Bool(self.requires_authentication)

        if self.auth_mechanism is not None and not isinstance(self.auth_mechanism, str):
            self.auth_mechanism = str(self.auth_mechanism)

        if self.rate_limit_requests_per_second is not None and not isinstance(self.rate_limit_requests_per_second, float):
            self.rate_limit_requests_per_second = float(self.rate_limit_requests_per_second)

        if self.license_spdx is not None and not isinstance(self.license_spdx, str):
            self.license_spdx = str(self.license_spdx)

        if self.citation_apa is not None and not isinstance(self.citation_apa, str):
            self.citation_apa = str(self.citation_apa)

        if self.doi is not None and not isinstance(self.doi, str):
            self.doi = str(self.doi)

        if self.amadeus_function_suffix is not None and not isinstance(self.amadeus_function_suffix, str):
            self.amadeus_function_suffix = str(self.amadeus_function_suffix)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Product(YAMLRoot):
    """
    A specific, versioned data product from a source — the unit a user actually requests, and the unit that carries
    the *profile*: spatial support, temporal support, format, calendar, day boundary.
    This is where the answer to "do we need different schemas for different types of source data?" lives. We do not.
    The variation across the amadeus catalog decomposes into five orthogonal axes recorded here
    (`spatial_support_type`, `temporal_resolution`, `value` kind via the variables, `native_format`, and extensivity
    via the variables). One schema, one product table; a MODIS swath and an AQS monitor differ in their *values on
    these axes*, not in their structure.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["Product"]
    class_class_curie: ClassVar[str] = "amadeus:Product"
    class_name: ClassVar[str] = "Product"
    class_model_uri: ClassVar[URIRef] = AMADEUS.Product

    id: Union[str, ProductId] = None
    name: str = None
    data_source: Union[str, DataSourceId] = None
    spatial_support_type: Union[str, "SpatialSupportTypeEnum"] = None
    temporal_resolution: Union[str, "TemporalResolutionEnum"] = None
    label: Optional[str] = None
    description: Optional[str] = None
    product_version: Optional[str] = None
    data_genre: Optional[Union[Union[str, "DataGenreEnum"], list[Union[str, "DataGenreEnum"]]]] = empty_list()
    native_format: Optional[Union[str, "NativeFormatEnum"]] = None
    grid_definition: Optional[Union[str, GridDefinitionId]] = None
    crs: Optional[str] = None
    srid: Optional[int] = None
    spatial_extent_bbox_wkt: Optional[Union[str, WktLiteral]] = None
    spatial_extent_descriptor: Optional[str] = None
    native_spatial_resolution_m: Optional[float] = None
    native_spatial_resolution_descriptor: Optional[str] = None
    temporal_resolution_iso: Optional[Union[str, Iso8601Duration]] = None
    temporal_alignment: Optional[Union[str, "TemporalAlignmentEnum"]] = None
    day_boundary_convention: Optional[Union[str, "DayBoundaryConventionEnum"]] = None
    calendar: Optional[Union[str, "CalendarEnum"]] = None
    temporal_coverage_start: Optional[Union[str, XSDDate]] = None
    temporal_coverage_end: Optional[Union[str, XSDDate]] = None
    update_cadence_iso: Optional[Union[str, Iso8601Duration]] = None
    typical_latency_iso: Optional[Union[str, Iso8601Duration]] = None
    default_data_status: Optional[Union[str, "DataStatusEnum"]] = None
    homogenisation_status: Optional[Union[str, "HomogenisationStatusEnum"]] = None
    doi: Optional[str] = None
    license_spdx: Optional[str] = None
    citation_apa: Optional[str] = None
    access_url: Optional[Union[str, URI]] = None
    amadeus_dataset_name: Optional[str] = None
    amadeus_process_covariate: Optional[str] = None
    amadeus_calculate_covariate: Optional[str] = None
    supports_server_side_subset: Optional[Union[bool, Bool]] = None
    stac_collection_id: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, ProductId):
            self.id = ProductId(self.id)

        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, str):
            self.name = str(self.name)

        if self._is_empty(self.data_source):
            self.MissingRequiredField("data_source")
        if not isinstance(self.data_source, DataSourceId):
            self.data_source = DataSourceId(self.data_source)

        if self._is_empty(self.spatial_support_type):
            self.MissingRequiredField("spatial_support_type")
        if not isinstance(self.spatial_support_type, SpatialSupportTypeEnum):
            self.spatial_support_type = SpatialSupportTypeEnum(self.spatial_support_type)

        if self._is_empty(self.temporal_resolution):
            self.MissingRequiredField("temporal_resolution")
        if not isinstance(self.temporal_resolution, TemporalResolutionEnum):
            self.temporal_resolution = TemporalResolutionEnum(self.temporal_resolution)

        if self.label is not None and not isinstance(self.label, str):
            self.label = str(self.label)

        if self.description is not None and not isinstance(self.description, str):
            self.description = str(self.description)

        if self.product_version is not None and not isinstance(self.product_version, str):
            self.product_version = str(self.product_version)

        if not isinstance(self.data_genre, list):
            self.data_genre = [self.data_genre] if self.data_genre is not None else []
        self.data_genre = [v if isinstance(v, DataGenreEnum) else DataGenreEnum(v) for v in self.data_genre]

        if self.native_format is not None and not isinstance(self.native_format, NativeFormatEnum):
            self.native_format = NativeFormatEnum(self.native_format)

        if self.grid_definition is not None and not isinstance(self.grid_definition, GridDefinitionId):
            self.grid_definition = GridDefinitionId(self.grid_definition)

        if self.crs is not None and not isinstance(self.crs, str):
            self.crs = str(self.crs)

        if self.srid is not None and not isinstance(self.srid, int):
            self.srid = int(self.srid)

        if self.spatial_extent_bbox_wkt is not None and not isinstance(self.spatial_extent_bbox_wkt, WktLiteral):
            self.spatial_extent_bbox_wkt = WktLiteral(self.spatial_extent_bbox_wkt)

        if self.spatial_extent_descriptor is not None and not isinstance(self.spatial_extent_descriptor, str):
            self.spatial_extent_descriptor = str(self.spatial_extent_descriptor)

        if self.native_spatial_resolution_m is not None and not isinstance(self.native_spatial_resolution_m, float):
            self.native_spatial_resolution_m = float(self.native_spatial_resolution_m)

        if self.native_spatial_resolution_descriptor is not None and not isinstance(self.native_spatial_resolution_descriptor, str):
            self.native_spatial_resolution_descriptor = str(self.native_spatial_resolution_descriptor)

        if self.temporal_resolution_iso is not None and not isinstance(self.temporal_resolution_iso, Iso8601Duration):
            self.temporal_resolution_iso = Iso8601Duration(self.temporal_resolution_iso)

        if self.temporal_alignment is not None and not isinstance(self.temporal_alignment, TemporalAlignmentEnum):
            self.temporal_alignment = TemporalAlignmentEnum(self.temporal_alignment)

        if self.day_boundary_convention is not None and not isinstance(self.day_boundary_convention, DayBoundaryConventionEnum):
            self.day_boundary_convention = DayBoundaryConventionEnum(self.day_boundary_convention)

        if self.calendar is not None and not isinstance(self.calendar, CalendarEnum):
            self.calendar = CalendarEnum(self.calendar)

        if self.temporal_coverage_start is not None and not isinstance(self.temporal_coverage_start, XSDDate):
            self.temporal_coverage_start = XSDDate(self.temporal_coverage_start)

        if self.temporal_coverage_end is not None and not isinstance(self.temporal_coverage_end, XSDDate):
            self.temporal_coverage_end = XSDDate(self.temporal_coverage_end)

        if self.update_cadence_iso is not None and not isinstance(self.update_cadence_iso, Iso8601Duration):
            self.update_cadence_iso = Iso8601Duration(self.update_cadence_iso)

        if self.typical_latency_iso is not None and not isinstance(self.typical_latency_iso, Iso8601Duration):
            self.typical_latency_iso = Iso8601Duration(self.typical_latency_iso)

        if self.default_data_status is not None and not isinstance(self.default_data_status, DataStatusEnum):
            self.default_data_status = DataStatusEnum(self.default_data_status)

        if self.homogenisation_status is not None and not isinstance(self.homogenisation_status, HomogenisationStatusEnum):
            self.homogenisation_status = HomogenisationStatusEnum(self.homogenisation_status)

        if self.doi is not None and not isinstance(self.doi, str):
            self.doi = str(self.doi)

        if self.license_spdx is not None and not isinstance(self.license_spdx, str):
            self.license_spdx = str(self.license_spdx)

        if self.citation_apa is not None and not isinstance(self.citation_apa, str):
            self.citation_apa = str(self.citation_apa)

        if self.access_url is not None and not isinstance(self.access_url, URI):
            self.access_url = URI(self.access_url)

        if self.amadeus_dataset_name is not None and not isinstance(self.amadeus_dataset_name, str):
            self.amadeus_dataset_name = str(self.amadeus_dataset_name)

        if self.amadeus_process_covariate is not None and not isinstance(self.amadeus_process_covariate, str):
            self.amadeus_process_covariate = str(self.amadeus_process_covariate)

        if self.amadeus_calculate_covariate is not None and not isinstance(self.amadeus_calculate_covariate, str):
            self.amadeus_calculate_covariate = str(self.amadeus_calculate_covariate)

        if self.supports_server_side_subset is not None and not isinstance(self.supports_server_side_subset, Bool):
            self.supports_server_side_subset = Bool(self.supports_server_side_subset)

        if self.stac_collection_id is not None and not isinstance(self.stac_collection_id, str):
            self.stac_collection_id = str(self.stac_collection_id)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class GridDefinition(YAMLRoot):
    """
    A reusable description of a raster or model grid. Its own entity because several products share one grid (all NARR
    monolevel variables) and because resolution, projection and vertical levels must be computable, not prose.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["GridDefinition"]
    class_class_curie: ClassVar[str] = "amadeus:GridDefinition"
    class_name: ClassVar[str] = "GridDefinition"
    class_model_uri: ClassVar[URIRef] = AMADEUS.GridDefinition

    id: Union[str, GridDefinitionId] = None
    crs: str = None
    resolution_x: float = None
    resolution_y: float = None
    name: Optional[str] = None
    label: Optional[str] = None
    srid: Optional[int] = None
    grid_mapping_name: Optional[str] = None
    proj_string: Optional[str] = None
    resolution_unit: Optional[str] = None
    n_columns: Optional[int] = None
    n_rows: Optional[int] = None
    origin_x: Optional[float] = None
    origin_y: Optional[float] = None
    vertical_level_type: Optional[str] = None
    vertical_level_unit: Optional[str] = None
    vertical_levels: Optional[Union[float, list[float]]] = empty_list()

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, GridDefinitionId):
            self.id = GridDefinitionId(self.id)

        if self._is_empty(self.crs):
            self.MissingRequiredField("crs")
        if not isinstance(self.crs, str):
            self.crs = str(self.crs)

        if self._is_empty(self.resolution_x):
            self.MissingRequiredField("resolution_x")
        if not isinstance(self.resolution_x, float):
            self.resolution_x = float(self.resolution_x)

        if self._is_empty(self.resolution_y):
            self.MissingRequiredField("resolution_y")
        if not isinstance(self.resolution_y, float):
            self.resolution_y = float(self.resolution_y)

        if self.name is not None and not isinstance(self.name, str):
            self.name = str(self.name)

        if self.label is not None and not isinstance(self.label, str):
            self.label = str(self.label)

        if self.srid is not None and not isinstance(self.srid, int):
            self.srid = int(self.srid)

        if self.grid_mapping_name is not None and not isinstance(self.grid_mapping_name, str):
            self.grid_mapping_name = str(self.grid_mapping_name)

        if self.proj_string is not None and not isinstance(self.proj_string, str):
            self.proj_string = str(self.proj_string)

        if self.resolution_unit is not None and not isinstance(self.resolution_unit, str):
            self.resolution_unit = str(self.resolution_unit)

        if self.n_columns is not None and not isinstance(self.n_columns, int):
            self.n_columns = int(self.n_columns)

        if self.n_rows is not None and not isinstance(self.n_rows, int):
            self.n_rows = int(self.n_rows)

        if self.origin_x is not None and not isinstance(self.origin_x, float):
            self.origin_x = float(self.origin_x)

        if self.origin_y is not None and not isinstance(self.origin_y, float):
            self.origin_y = float(self.origin_y)

        if self.vertical_level_type is not None and not isinstance(self.vertical_level_type, str):
            self.vertical_level_type = str(self.vertical_level_type)

        if self.vertical_level_unit is not None and not isinstance(self.vertical_level_unit, str):
            self.vertical_level_unit = str(self.vertical_level_unit)

        if not isinstance(self.vertical_levels, list):
            self.vertical_levels = [self.vertical_levels] if self.vertical_levels is not None else []
        self.vertical_levels = [v if isinstance(v, float) else float(v) for v in self.vertical_levels]

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class CanonicalVariable(YAMLRoot):
    """
    A harmonised environmental quantity, independent of who publishes it. The cross-source identity anchor:
    `gridmet.tmmx`, `prism.tmax` and `daymet.tmax` are three `ProductVariable`s over *one* `CanonicalVariable`, and
    that is what makes "is it the same variable?" answerable by a join rather than by a conversation.
    Carries the semantics that must be identical across sources (`standard_name`, canonical units, extensivity,
    plausible range, concept bindings). Everything that legitimately differs per source lives on `ProductVariable`.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["CanonicalVariable"]
    class_class_curie: ClassVar[str] = "amadeus:CanonicalVariable"
    class_name: ClassVar[str] = "CanonicalVariable"
    class_model_uri: ClassVar[URIRef] = AMADEUS.CanonicalVariable

    id: Union[str, CanonicalVariableId] = None
    name: str = None
    standard_name: Union[str, URIorCURIE] = None
    units_ucum: str = None
    value_data_type: Union[str, "ValueDataTypeEnum"] = None
    extensivity: Union[str, "VariableExtensivityEnum"] = None
    label: Optional[str] = None
    description: Optional[str] = None
    standard_name_authority: Optional[str] = None
    units_display: Optional[str] = None
    default_aggregation_method: Optional[Union[str, "AggregationMethodEnum"]] = None
    plausible_min: Optional[float] = None
    plausible_max: Optional[float] = None
    concept_mappings: Optional[Union[Union[str, URIorCURIE], list[Union[str, URIorCURIE]]]] = empty_list()
    omop_concept_binding: Optional[Union[dict, "OmopConceptBinding"]] = None
    envar_variable_family: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, CanonicalVariableId):
            self.id = CanonicalVariableId(self.id)

        if self._is_empty(self.name):
            self.MissingRequiredField("name")
        if not isinstance(self.name, str):
            self.name = str(self.name)

        if self._is_empty(self.standard_name):
            self.MissingRequiredField("standard_name")
        if not isinstance(self.standard_name, URIorCURIE):
            self.standard_name = URIorCURIE(self.standard_name)

        if self._is_empty(self.units_ucum):
            self.MissingRequiredField("units_ucum")
        if not isinstance(self.units_ucum, str):
            self.units_ucum = str(self.units_ucum)

        if self._is_empty(self.value_data_type):
            self.MissingRequiredField("value_data_type")
        if not isinstance(self.value_data_type, ValueDataTypeEnum):
            self.value_data_type = ValueDataTypeEnum(self.value_data_type)

        if self._is_empty(self.extensivity):
            self.MissingRequiredField("extensivity")
        if not isinstance(self.extensivity, VariableExtensivityEnum):
            self.extensivity = VariableExtensivityEnum(self.extensivity)

        if self.label is not None and not isinstance(self.label, str):
            self.label = str(self.label)

        if self.description is not None and not isinstance(self.description, str):
            self.description = str(self.description)

        if self.standard_name_authority is not None and not isinstance(self.standard_name_authority, str):
            self.standard_name_authority = str(self.standard_name_authority)

        if self.units_display is not None and not isinstance(self.units_display, str):
            self.units_display = str(self.units_display)

        if self.default_aggregation_method is not None and not isinstance(self.default_aggregation_method, AggregationMethodEnum):
            self.default_aggregation_method = AggregationMethodEnum(self.default_aggregation_method)

        if self.plausible_min is not None and not isinstance(self.plausible_min, float):
            self.plausible_min = float(self.plausible_min)

        if self.plausible_max is not None and not isinstance(self.plausible_max, float):
            self.plausible_max = float(self.plausible_max)

        if not isinstance(self.concept_mappings, list):
            self.concept_mappings = [self.concept_mappings] if self.concept_mappings is not None else []
        self.concept_mappings = [v if isinstance(v, URIorCURIE) else URIorCURIE(v) for v in self.concept_mappings]

        if self.omop_concept_binding is not None and not isinstance(self.omop_concept_binding, OmopConceptBinding):
            self.omop_concept_binding = OmopConceptBinding(**as_dict(self.omop_concept_binding))

        if self.envar_variable_family is not None and not isinstance(self.envar_variable_family, str):
            self.envar_variable_family = str(self.envar_variable_family)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ProductVariable(YAMLRoot):
    """
    One source's delivery of one canonical variable: the native name, the native units and conversion, the CF
    metadata, the aggregation actually applied, and the layer-name template amadeus parses.
    Every slot here exists because it is a reason two sources of "the same" variable are not interchangeable.
    `native_units_ucum` + `native_value_scale_factor` + `native_value_offset` are the gridMET Kelvin→Celsius case,
    where the conversion happened at render time and was recorded nowhere.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["ProductVariable"]
    class_class_curie: ClassVar[str] = "amadeus:ProductVariable"
    class_name: ClassVar[str] = "ProductVariable"
    class_model_uri: ClassVar[URIRef] = AMADEUS.ProductVariable

    id: Union[str, ProductVariableId] = None
    product: Union[str, ProductId] = None
    canonical_variable: Union[str, CanonicalVariableId] = None
    native_name: str = None
    label: Optional[str] = None
    native_units_ucum: Optional[str] = None
    native_value_scale_factor: Optional[float] = None
    native_value_offset: Optional[float] = None
    unit_conversion_formula: Optional[str] = None
    cf_standard_name: Optional[str] = None
    cf_cell_methods: Optional[str] = None
    aggregation_method: Optional[Union[str, "AggregationMethodEnum"]] = None
    aggregation_window_iso: Optional[Union[str, Iso8601Duration]] = None
    temporal_alignment: Optional[Union[str, "TemporalAlignmentEnum"]] = None
    vertical_level_type: Optional[str] = None
    missing_value_sentinel: Optional[str] = None
    quality_flag_vocabulary: Optional[str] = None
    layer_name_template: Optional[str] = None
    amadeus_variable_code: Optional[str] = None
    value_data_type: Optional[Union[str, "ValueDataTypeEnum"]] = None
    extensivity: Optional[Union[str, "VariableExtensivityEnum"]] = None
    harmonization_note: Optional[str] = None
    metadata_gaps: Optional[Union[Union[str, "MissingReasonEnum"], list[Union[str, "MissingReasonEnum"]]]] = empty_list()

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, ProductVariableId):
            self.id = ProductVariableId(self.id)

        if self._is_empty(self.product):
            self.MissingRequiredField("product")
        if not isinstance(self.product, ProductId):
            self.product = ProductId(self.product)

        if self._is_empty(self.canonical_variable):
            self.MissingRequiredField("canonical_variable")
        if not isinstance(self.canonical_variable, CanonicalVariableId):
            self.canonical_variable = CanonicalVariableId(self.canonical_variable)

        if self._is_empty(self.native_name):
            self.MissingRequiredField("native_name")
        if not isinstance(self.native_name, str):
            self.native_name = str(self.native_name)

        if self.label is not None and not isinstance(self.label, str):
            self.label = str(self.label)

        if self.native_units_ucum is not None and not isinstance(self.native_units_ucum, str):
            self.native_units_ucum = str(self.native_units_ucum)

        if self.native_value_scale_factor is not None and not isinstance(self.native_value_scale_factor, float):
            self.native_value_scale_factor = float(self.native_value_scale_factor)

        if self.native_value_offset is not None and not isinstance(self.native_value_offset, float):
            self.native_value_offset = float(self.native_value_offset)

        if self.unit_conversion_formula is not None and not isinstance(self.unit_conversion_formula, str):
            self.unit_conversion_formula = str(self.unit_conversion_formula)

        if self.cf_standard_name is not None and not isinstance(self.cf_standard_name, str):
            self.cf_standard_name = str(self.cf_standard_name)

        if self.cf_cell_methods is not None and not isinstance(self.cf_cell_methods, str):
            self.cf_cell_methods = str(self.cf_cell_methods)

        if self.aggregation_method is not None and not isinstance(self.aggregation_method, AggregationMethodEnum):
            self.aggregation_method = AggregationMethodEnum(self.aggregation_method)

        if self.aggregation_window_iso is not None and not isinstance(self.aggregation_window_iso, Iso8601Duration):
            self.aggregation_window_iso = Iso8601Duration(self.aggregation_window_iso)

        if self.temporal_alignment is not None and not isinstance(self.temporal_alignment, TemporalAlignmentEnum):
            self.temporal_alignment = TemporalAlignmentEnum(self.temporal_alignment)

        if self.vertical_level_type is not None and not isinstance(self.vertical_level_type, str):
            self.vertical_level_type = str(self.vertical_level_type)

        if self.missing_value_sentinel is not None and not isinstance(self.missing_value_sentinel, str):
            self.missing_value_sentinel = str(self.missing_value_sentinel)

        if self.quality_flag_vocabulary is not None and not isinstance(self.quality_flag_vocabulary, str):
            self.quality_flag_vocabulary = str(self.quality_flag_vocabulary)

        if self.layer_name_template is not None and not isinstance(self.layer_name_template, str):
            self.layer_name_template = str(self.layer_name_template)

        if self.amadeus_variable_code is not None and not isinstance(self.amadeus_variable_code, str):
            self.amadeus_variable_code = str(self.amadeus_variable_code)

        if self.value_data_type is not None and not isinstance(self.value_data_type, ValueDataTypeEnum):
            self.value_data_type = ValueDataTypeEnum(self.value_data_type)

        if self.extensivity is not None and not isinstance(self.extensivity, VariableExtensivityEnum):
            self.extensivity = VariableExtensivityEnum(self.extensivity)

        if self.harmonization_note is not None and not isinstance(self.harmonization_note, str):
            self.harmonization_note = str(self.harmonization_note)

        if not isinstance(self.metadata_gaps, list):
            self.metadata_gaps = [self.metadata_gaps] if self.metadata_gaps is not None else []
        self.metadata_gaps = [v if isinstance(v, MissingReasonEnum) else MissingReasonEnum(v) for v in self.metadata_gaps]

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class OmopConceptBinding(YAMLRoot):
    """
    Binding of a canonical variable to an OMOP concept. Taken structurally from HEW so the two schemas exchange
    bindings without an adapter.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["OmopConceptBinding"]
    class_class_curie: ClassVar[str] = "amadeus:OmopConceptBinding"
    class_name: ClassVar[str] = "OmopConceptBinding"
    class_model_uri: ClassVar[URIRef] = AMADEUS.OmopConceptBinding

    concept_status: Union[str, "ConceptStatusEnum"] = None
    omop_concept_id: Optional[int] = None
    omop_concept_name: Optional[str] = None
    omop_vocabulary_id: Optional[str] = None
    omop_domain_id: Optional[str] = None
    omop_standard_concept: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.concept_status):
            self.MissingRequiredField("concept_status")
        if not isinstance(self.concept_status, ConceptStatusEnum):
            self.concept_status = ConceptStatusEnum(self.concept_status)

        if self.omop_concept_id is not None and not isinstance(self.omop_concept_id, int):
            self.omop_concept_id = int(self.omop_concept_id)

        if self.omop_concept_name is not None and not isinstance(self.omop_concept_name, str):
            self.omop_concept_name = str(self.omop_concept_name)

        if self.omop_vocabulary_id is not None and not isinstance(self.omop_vocabulary_id, str):
            self.omop_vocabulary_id = str(self.omop_vocabulary_id)

        if self.omop_domain_id is not None and not isinstance(self.omop_domain_id, str):
            self.omop_domain_id = str(self.omop_domain_id)

        if self.omop_standard_concept is not None and not isinstance(self.omop_standard_concept, str):
            self.omop_standard_concept = str(self.omop_standard_concept)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Asset(YAMLRoot):
    """
    A concrete byte stream: a file on disk, an object in a bucket, a STAC asset, or a provider API response. The unit
    of download, caching, integrity checking and idempotency.
    **Asset-centric by design.** The modernization plan's own instruction is "adopt an asset-centric schema; avoid
    mandatory cell-row ingestion". An asset can be registered — catalogued, discoverable, queryable by extent and time
    — without any of its values ever being materialised into a value table. `materialization_mode` records how much
    was actually read, so the four streaming modes of plan §4.7.2 become auditable properties of the catalog rather
    than an ungoverned side path.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["Asset"]
    class_class_curie: ClassVar[str] = "amadeus:Asset"
    class_name: ClassVar[str] = "Asset"
    class_model_uri: ClassVar[URIRef] = AMADEUS.Asset

    id: Union[str, AssetId] = None
    product: Union[str, ProductId] = None
    materialization_mode: Union[str, "MaterializationModeEnum"] = None
    value_state: Union[str, "ValueMaterializationEnum"] = None
    asset_key: Optional[str] = None
    url: Optional[Union[str, URI]] = None
    local_path: Optional[str] = None
    media_type: Optional[str] = None
    native_format: Optional[Union[str, "NativeFormatEnum"]] = None
    size_bytes: Optional[int] = None
    sha256: Optional[Union[str, Sha256]] = None
    source_last_modified: Optional[Union[str, XSDDateTime]] = None
    download_timestamp_utc: Optional[Union[str, XSDDateTime]] = None
    valid_time_start: Optional[Union[str, XSDDateTime]] = None
    valid_time_end: Optional[Union[str, XSDDateTime]] = None
    reference_time: Optional[Union[str, XSDDateTime]] = None
    bbox_wkt: Optional[Union[str, WktLiteral]] = None
    srid: Optional[int] = None
    variables_present: Optional[Union[Union[str, ProductVariableId], list[Union[str, ProductVariableId]]]] = empty_list()
    vertical_levels_present: Optional[Union[float, list[float]]] = empty_list()
    stac_collection_id: Optional[str] = None
    stac_item_id: Optional[str] = None
    cache_expires_at: Optional[Union[str, XSDDateTime]] = None
    produced_by_run: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, AssetId):
            self.id = AssetId(self.id)

        if self._is_empty(self.product):
            self.MissingRequiredField("product")
        if not isinstance(self.product, ProductId):
            self.product = ProductId(self.product)

        if self._is_empty(self.materialization_mode):
            self.MissingRequiredField("materialization_mode")
        if not isinstance(self.materialization_mode, MaterializationModeEnum):
            self.materialization_mode = MaterializationModeEnum(self.materialization_mode)

        if self._is_empty(self.value_state):
            self.MissingRequiredField("value_state")
        if not isinstance(self.value_state, ValueMaterializationEnum):
            self.value_state = ValueMaterializationEnum(self.value_state)

        if self.asset_key is not None and not isinstance(self.asset_key, str):
            self.asset_key = str(self.asset_key)

        if self.url is not None and not isinstance(self.url, URI):
            self.url = URI(self.url)

        if self.local_path is not None and not isinstance(self.local_path, str):
            self.local_path = str(self.local_path)

        if self.media_type is not None and not isinstance(self.media_type, str):
            self.media_type = str(self.media_type)

        if self.native_format is not None and not isinstance(self.native_format, NativeFormatEnum):
            self.native_format = NativeFormatEnum(self.native_format)

        if self.size_bytes is not None and not isinstance(self.size_bytes, int):
            self.size_bytes = int(self.size_bytes)

        if self.sha256 is not None and not isinstance(self.sha256, Sha256):
            self.sha256 = Sha256(self.sha256)

        if self.source_last_modified is not None and not isinstance(self.source_last_modified, XSDDateTime):
            self.source_last_modified = XSDDateTime(self.source_last_modified)

        if self.download_timestamp_utc is not None and not isinstance(self.download_timestamp_utc, XSDDateTime):
            self.download_timestamp_utc = XSDDateTime(self.download_timestamp_utc)

        if self.valid_time_start is not None and not isinstance(self.valid_time_start, XSDDateTime):
            self.valid_time_start = XSDDateTime(self.valid_time_start)

        if self.valid_time_end is not None and not isinstance(self.valid_time_end, XSDDateTime):
            self.valid_time_end = XSDDateTime(self.valid_time_end)

        if self.reference_time is not None and not isinstance(self.reference_time, XSDDateTime):
            self.reference_time = XSDDateTime(self.reference_time)

        if self.bbox_wkt is not None and not isinstance(self.bbox_wkt, WktLiteral):
            self.bbox_wkt = WktLiteral(self.bbox_wkt)

        if self.srid is not None and not isinstance(self.srid, int):
            self.srid = int(self.srid)

        if not isinstance(self.variables_present, list):
            self.variables_present = [self.variables_present] if self.variables_present is not None else []
        self.variables_present = [v if isinstance(v, ProductVariableId) else ProductVariableId(v) for v in self.variables_present]

        if not isinstance(self.vertical_levels_present, list):
            self.vertical_levels_present = [self.vertical_levels_present] if self.vertical_levels_present is not None else []
        self.vertical_levels_present = [v if isinstance(v, float) else float(v) for v in self.vertical_levels_present]

        if self.stac_collection_id is not None and not isinstance(self.stac_collection_id, str):
            self.stac_collection_id = str(self.stac_collection_id)

        if self.stac_item_id is not None and not isinstance(self.stac_item_id, str):
            self.stac_item_id = str(self.stac_item_id)

        if self.cache_expires_at is not None and not isinstance(self.cache_expires_at, XSDDateTime):
            self.cache_expires_at = XSDDateTime(self.cache_expires_at)

        if self.produced_by_run is not None and not isinstance(self.produced_by_run, str):
            self.produced_by_run = str(self.produced_by_run)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class AmbientValue(YAMLRoot):
    """
    One value of one variable, at one place, over one time interval, from one asset, produced by one run. A property
    of the environment; not an exposure.
    Abstract: no table of its own. The SQL generator flattens these slots into each concrete child, which is the right
    physical design — a single polymorphic value table with mostly-null geometry columns would defeat both
    partitioning and spatial indexing.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["AmbientValue"]
    class_class_curie: ClassVar[str] = "amadeus:AmbientValue"
    class_name: ClassVar[str] = "AmbientValue"
    class_model_uri: ClassVar[URIRef] = AMADEUS.AmbientValue

    id: Union[str, AmbientValueId] = None
    product_variable: Union[str, ProductVariableId] = None
    canonical_variable: Union[str, CanonicalVariableId] = None
    valid_time_start: Union[str, XSDDateTime] = None
    data_status: Union[str, "DataStatusEnum"] = None
    source_system: str = None
    null_semantics: Union[str, "NullSemanticsEnum"] = None
    asset: Optional[Union[str, AssetId]] = None
    processing_run: Optional[str] = None
    value: Optional[float] = None
    value_unit_ucum: Optional[str] = None
    native_value: Optional[float] = None
    native_value_unit_ucum: Optional[str] = None
    valid_time_end: Optional[Union[str, XSDDateTime]] = None
    reference_time: Optional[Union[str, XSDDateTime]] = None
    retrieval_time_utc: Optional[Union[str, XSDDateTime]] = None
    vertical_level: Optional[float] = None
    vertical_level_unit: Optional[str] = None
    quality_flag: Optional[str] = None
    source_version: Optional[str] = None
    superseded_by: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, AmbientValueId):
            self.id = AmbientValueId(self.id)

        if self._is_empty(self.product_variable):
            self.MissingRequiredField("product_variable")
        if not isinstance(self.product_variable, ProductVariableId):
            self.product_variable = ProductVariableId(self.product_variable)

        if self._is_empty(self.canonical_variable):
            self.MissingRequiredField("canonical_variable")
        if not isinstance(self.canonical_variable, CanonicalVariableId):
            self.canonical_variable = CanonicalVariableId(self.canonical_variable)

        if self._is_empty(self.valid_time_start):
            self.MissingRequiredField("valid_time_start")
        if not isinstance(self.valid_time_start, XSDDateTime):
            self.valid_time_start = XSDDateTime(self.valid_time_start)

        if self._is_empty(self.data_status):
            self.MissingRequiredField("data_status")
        if not isinstance(self.data_status, DataStatusEnum):
            self.data_status = DataStatusEnum(self.data_status)

        if self._is_empty(self.source_system):
            self.MissingRequiredField("source_system")
        if not isinstance(self.source_system, str):
            self.source_system = str(self.source_system)

        if self._is_empty(self.null_semantics):
            self.MissingRequiredField("null_semantics")
        if not isinstance(self.null_semantics, NullSemanticsEnum):
            self.null_semantics = NullSemanticsEnum(self.null_semantics)

        if self.asset is not None and not isinstance(self.asset, AssetId):
            self.asset = AssetId(self.asset)

        if self.processing_run is not None and not isinstance(self.processing_run, str):
            self.processing_run = str(self.processing_run)

        if self.value is not None and not isinstance(self.value, float):
            self.value = float(self.value)

        if self.value_unit_ucum is not None and not isinstance(self.value_unit_ucum, str):
            self.value_unit_ucum = str(self.value_unit_ucum)

        if self.native_value is not None and not isinstance(self.native_value, float):
            self.native_value = float(self.native_value)

        if self.native_value_unit_ucum is not None and not isinstance(self.native_value_unit_ucum, str):
            self.native_value_unit_ucum = str(self.native_value_unit_ucum)

        if self.valid_time_end is not None and not isinstance(self.valid_time_end, XSDDateTime):
            self.valid_time_end = XSDDateTime(self.valid_time_end)

        if self.reference_time is not None and not isinstance(self.reference_time, XSDDateTime):
            self.reference_time = XSDDateTime(self.reference_time)

        if self.retrieval_time_utc is not None and not isinstance(self.retrieval_time_utc, XSDDateTime):
            self.retrieval_time_utc = XSDDateTime(self.retrieval_time_utc)

        if self.vertical_level is not None and not isinstance(self.vertical_level, float):
            self.vertical_level = float(self.vertical_level)

        if self.vertical_level_unit is not None and not isinstance(self.vertical_level_unit, str):
            self.vertical_level_unit = str(self.vertical_level_unit)

        if self.quality_flag is not None and not isinstance(self.quality_flag, str):
            self.quality_flag = str(self.quality_flag)

        if self.source_version is not None and not isinstance(self.source_version, str):
            self.source_version = str(self.source_version)

        if self.superseded_by is not None and not isinstance(self.superseded_by, str):
            self.superseded_by = str(self.superseded_by)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class StationObservation(AmbientValue):
    """
    A value from a fixed instrument with a persistent identity: EPA AQS, AirNow, IMPROVE, USGS water sites.
    The distinguishing feature is not the point geometry — it is that the *instrument* is an entity with a history.
    Monitors move, get replaced, and report the same parameter through several collocated units (the AQS POC). A grid
    cell has none of that. Collapsing stations into a generic point table loses the keys that make a revision
    traceable.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["StationObservation"]
    class_class_curie: ClassVar[str] = "amadeus:StationObservation"
    class_name: ClassVar[str] = "StationObservation"
    class_model_uri: ClassVar[URIRef] = AMADEUS.StationObservation

    id: Union[str, StationObservationId] = None
    product_variable: Union[str, ProductVariableId] = None
    canonical_variable: Union[str, CanonicalVariableId] = None
    valid_time_start: Union[str, XSDDateTime] = None
    data_status: Union[str, "DataStatusEnum"] = None
    source_system: str = None
    null_semantics: Union[str, "NullSemanticsEnum"] = None
    station_id: str = None
    station_geom_wkt: Union[str, WktLiteral] = None
    station_name: Optional[str] = None
    monitor_id: Optional[str] = None
    parameter_code: Optional[str] = None
    poc: Optional[int] = None
    sampling_duration_iso: Optional[Union[str, Iso8601Duration]] = None
    srid: Optional[int] = None
    elevation_m: Optional[float] = None
    station_valid_from: Optional[Union[str, XSDDate]] = None
    station_valid_to: Optional[Union[str, XSDDate]] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, StationObservationId):
            self.id = StationObservationId(self.id)

        if self._is_empty(self.station_id):
            self.MissingRequiredField("station_id")
        if not isinstance(self.station_id, str):
            self.station_id = str(self.station_id)

        if self._is_empty(self.station_geom_wkt):
            self.MissingRequiredField("station_geom_wkt")
        if not isinstance(self.station_geom_wkt, WktLiteral):
            self.station_geom_wkt = WktLiteral(self.station_geom_wkt)

        if self.station_name is not None and not isinstance(self.station_name, str):
            self.station_name = str(self.station_name)

        if self.monitor_id is not None and not isinstance(self.monitor_id, str):
            self.monitor_id = str(self.monitor_id)

        if self.parameter_code is not None and not isinstance(self.parameter_code, str):
            self.parameter_code = str(self.parameter_code)

        if self.poc is not None and not isinstance(self.poc, int):
            self.poc = int(self.poc)

        if self.sampling_duration_iso is not None and not isinstance(self.sampling_duration_iso, Iso8601Duration):
            self.sampling_duration_iso = Iso8601Duration(self.sampling_duration_iso)

        if self.srid is not None and not isinstance(self.srid, int):
            self.srid = int(self.srid)

        if self.elevation_m is not None and not isinstance(self.elevation_m, float):
            self.elevation_m = float(self.elevation_m)

        if self.station_valid_from is not None and not isinstance(self.station_valid_from, XSDDate):
            self.station_valid_from = XSDDate(self.station_valid_from)

        if self.station_valid_to is not None and not isinstance(self.station_valid_to, XSDDate):
            self.station_valid_to = XSDDate(self.station_valid_to)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class GridCellValue(AmbientValue):
    """
    A value at one cell of one grid — the flattened form of a raster layer. This is the class the SedonaDB decision
    hangs on: Sedona's raster support is thinner than `terra`'s, so the plan's proposal is to flatten raster to point
    or polygon and persist as GeoParquet.
    The cell is identified *twice*: by integer grid index (`cell_x`, `cell_y`) and by geometry. The index is the
    cheap, exact, join-stable key and the one to partition and deduplicate on; the geometry is what spatial predicates
    need. Storing only geometry makes idempotent re-ingestion a floating-point comparison, which is how duplicate rows
    appear.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["GridCellValue"]
    class_class_curie: ClassVar[str] = "amadeus:GridCellValue"
    class_name: ClassVar[str] = "GridCellValue"
    class_model_uri: ClassVar[URIRef] = AMADEUS.GridCellValue

    id: Union[str, GridCellValueId] = None
    product_variable: Union[str, ProductVariableId] = None
    canonical_variable: Union[str, CanonicalVariableId] = None
    valid_time_start: Union[str, XSDDateTime] = None
    data_status: Union[str, "DataStatusEnum"] = None
    source_system: str = None
    null_semantics: Union[str, "NullSemanticsEnum"] = None
    grid_definition: Union[str, GridDefinitionId] = None
    cell_x: int = None
    cell_y: int = None
    cell_centroid_wkt: Union[str, WktLiteral] = None
    cell_polygon_wkt: Optional[Union[str, WktLiteral]] = None
    srid: Optional[int] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, GridCellValueId):
            self.id = GridCellValueId(self.id)

        if self._is_empty(self.grid_definition):
            self.MissingRequiredField("grid_definition")
        if not isinstance(self.grid_definition, GridDefinitionId):
            self.grid_definition = GridDefinitionId(self.grid_definition)

        if self._is_empty(self.cell_x):
            self.MissingRequiredField("cell_x")
        if not isinstance(self.cell_x, int):
            self.cell_x = int(self.cell_x)

        if self._is_empty(self.cell_y):
            self.MissingRequiredField("cell_y")
        if not isinstance(self.cell_y, int):
            self.cell_y = int(self.cell_y)

        if self._is_empty(self.cell_centroid_wkt):
            self.MissingRequiredField("cell_centroid_wkt")
        if not isinstance(self.cell_centroid_wkt, WktLiteral):
            self.cell_centroid_wkt = WktLiteral(self.cell_centroid_wkt)

        if self.cell_polygon_wkt is not None and not isinstance(self.cell_polygon_wkt, WktLiteral):
            self.cell_polygon_wkt = WktLiteral(self.cell_polygon_wkt)

        if self.srid is not None and not isinstance(self.srid, int):
            self.srid = int(self.srid)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class AreaValue(AmbientValue):
    """
    A value attached to a named or delineated polygon: HUC watersheds, EPA ecoregions, county-level NEI emissions,
    USDM drought polygons, NOAA HMS smoke plumes.
    Two sub-cases that must not be merged, distinguished by `area_role`: an *administrative* area whose identity is
    external and stable (a county FIPS), and an *episodic* polygon that exists only because something happened there
    (a smoke plume on one day). Aggregating across the second as if it were the first produces nonsense.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["AreaValue"]
    class_class_curie: ClassVar[str] = "amadeus:AreaValue"
    class_name: ClassVar[str] = "AreaValue"
    class_model_uri: ClassVar[URIRef] = AMADEUS.AreaValue

    id: Union[str, AreaValueId] = None
    product_variable: Union[str, ProductVariableId] = None
    canonical_variable: Union[str, CanonicalVariableId] = None
    valid_time_start: Union[str, XSDDateTime] = None
    data_status: Union[str, "DataStatusEnum"] = None
    source_system: str = None
    null_semantics: Union[str, "NullSemanticsEnum"] = None
    area_id: str = None
    area_type: Union[str, "AreaTypeEnum"] = None
    area_role: Union[str, "AreaRoleEnum"] = None
    area_geom_wkt: Union[str, WktLiteral] = None
    area_code: Optional[str] = None
    area_name: Optional[str] = None
    srid: Optional[int] = None
    area_km2: Optional[float] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, AreaValueId):
            self.id = AreaValueId(self.id)

        if self._is_empty(self.area_id):
            self.MissingRequiredField("area_id")
        if not isinstance(self.area_id, str):
            self.area_id = str(self.area_id)

        if self._is_empty(self.area_type):
            self.MissingRequiredField("area_type")
        if not isinstance(self.area_type, AreaTypeEnum):
            self.area_type = AreaTypeEnum(self.area_type)

        if self._is_empty(self.area_role):
            self.MissingRequiredField("area_role")
        if not isinstance(self.area_role, AreaRoleEnum):
            self.area_role = AreaRoleEnum(self.area_role)

        if self._is_empty(self.area_geom_wkt):
            self.MissingRequiredField("area_geom_wkt")
        if not isinstance(self.area_geom_wkt, WktLiteral):
            self.area_geom_wkt = WktLiteral(self.area_geom_wkt)

        if self.area_code is not None and not isinstance(self.area_code, str):
            self.area_code = str(self.area_code)

        if self.area_name is not None and not isinstance(self.area_name, str):
            self.area_name = str(self.area_name)

        if self.srid is not None and not isinstance(self.srid, int):
            self.srid = int(self.srid)

        if self.area_km2 is not None and not isinstance(self.area_km2, float):
            self.area_km2 = float(self.area_km2)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class HexCellValue(AmbientValue):
    """
    A value aggregated to an H3 cell — the harmonization target for the C-HER collaboration (objective O-09).
    Hexification is lossy and the loss must be recorded, not assumed. Three slots do that: `source_support_type` (what
    was aggregated), `coverage_fraction` (how much of the hex the source actually covered) and `hexification_method`
    (how). A hex value whose provenance says "area_weighted_mean from raster_grid_cell at 0.62 coverage" is usable;
    the same number without them is not.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["HexCellValue"]
    class_class_curie: ClassVar[str] = "amadeus:HexCellValue"
    class_name: ClassVar[str] = "HexCellValue"
    class_model_uri: ClassVar[URIRef] = AMADEUS.HexCellValue

    id: Union[str, HexCellValueId] = None
    product_variable: Union[str, ProductVariableId] = None
    canonical_variable: Union[str, CanonicalVariableId] = None
    valid_time_start: Union[str, XSDDateTime] = None
    data_status: Union[str, "DataStatusEnum"] = None
    source_system: str = None
    null_semantics: Union[str, "NullSemanticsEnum"] = None
    h3_cell: Union[str, H3CellIndex] = None
    h3_resolution: int = None
    source_support_type: Union[str, "SpatialSupportTypeEnum"] = None
    hexification_method: Union[str, "AggregationMethodEnum"] = None
    coverage_fraction: float = None
    hex_centroid_wkt: Optional[Union[str, WktLiteral]] = None
    srid: Optional[int] = None
    contributing_cell_count: Optional[int] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, HexCellValueId):
            self.id = HexCellValueId(self.id)

        if self._is_empty(self.h3_cell):
            self.MissingRequiredField("h3_cell")
        if not isinstance(self.h3_cell, H3CellIndex):
            self.h3_cell = H3CellIndex(self.h3_cell)

        if self._is_empty(self.h3_resolution):
            self.MissingRequiredField("h3_resolution")
        if not isinstance(self.h3_resolution, int):
            self.h3_resolution = int(self.h3_resolution)

        if self._is_empty(self.source_support_type):
            self.MissingRequiredField("source_support_type")
        if not isinstance(self.source_support_type, SpatialSupportTypeEnum):
            self.source_support_type = SpatialSupportTypeEnum(self.source_support_type)

        if self._is_empty(self.hexification_method):
            self.MissingRequiredField("hexification_method")
        if not isinstance(self.hexification_method, AggregationMethodEnum):
            self.hexification_method = AggregationMethodEnum(self.hexification_method)

        if self._is_empty(self.coverage_fraction):
            self.MissingRequiredField("coverage_fraction")
        if not isinstance(self.coverage_fraction, float):
            self.coverage_fraction = float(self.coverage_fraction)

        if self.hex_centroid_wkt is not None and not isinstance(self.hex_centroid_wkt, WktLiteral):
            self.hex_centroid_wkt = WktLiteral(self.hex_centroid_wkt)

        if self.srid is not None and not isinstance(self.srid, int):
            self.srid = int(self.srid)

        if self.contributing_cell_count is not None and not isinstance(self.contributing_cell_count, int):
            self.contributing_cell_count = int(self.contributing_cell_count)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class VectorFeature(YAMLRoot):
    """
    A reference geometry with attributes but no measured value over time: SEDAC gROADS road segments, hydrography
    lines, building footprints.
    Deliberately **not** an `AmbientValue`. These are inputs to density and distance covariates, not observations, and
    they have no valid-time interval in any meaningful sense. The distinction matters because the legal operations
    differ: you compute a length or a distance from these, never a mean.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["VectorFeature"]
    class_class_curie: ClassVar[str] = "amadeus:VectorFeature"
    class_name: ClassVar[str] = "VectorFeature"
    class_model_uri: ClassVar[URIRef] = AMADEUS.VectorFeature

    id: Union[str, VectorFeatureId] = None
    product: Union[str, ProductId] = None
    geometry_type: Union[str, "GeometryTypeEnum"] = None
    feature_geom_wkt: Union[str, WktLiteral] = None
    feature_id: Optional[str] = None
    feature_type: Optional[str] = None
    srid: Optional[int] = None
    feature_attributes: Optional[str] = None
    length_m: Optional[float] = None
    asset: Optional[Union[str, AssetId]] = None
    processing_run: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, VectorFeatureId):
            self.id = VectorFeatureId(self.id)

        if self._is_empty(self.product):
            self.MissingRequiredField("product")
        if not isinstance(self.product, ProductId):
            self.product = ProductId(self.product)

        if self._is_empty(self.geometry_type):
            self.MissingRequiredField("geometry_type")
        if not isinstance(self.geometry_type, GeometryTypeEnum):
            self.geometry_type = GeometryTypeEnum(self.geometry_type)

        if self._is_empty(self.feature_geom_wkt):
            self.MissingRequiredField("feature_geom_wkt")
        if not isinstance(self.feature_geom_wkt, WktLiteral):
            self.feature_geom_wkt = WktLiteral(self.feature_geom_wkt)

        if self.feature_id is not None and not isinstance(self.feature_id, str):
            self.feature_id = str(self.feature_id)

        if self.feature_type is not None and not isinstance(self.feature_type, str):
            self.feature_type = str(self.feature_type)

        if self.srid is not None and not isinstance(self.srid, int):
            self.srid = int(self.srid)

        if self.feature_attributes is not None and not isinstance(self.feature_attributes, str):
            self.feature_attributes = str(self.feature_attributes)

        if self.length_m is not None and not isinstance(self.length_m, float):
            self.length_m = float(self.length_m)

        if self.asset is not None and not isinstance(self.asset, AssetId):
            self.asset = AssetId(self.asset)

        if self.processing_run is not None and not isinstance(self.processing_run, str):
            self.processing_run = str(self.processing_run)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class LocationSet(YAMLRoot):
    """
    A user-supplied collection of locations — the `locs` argument, promoted to an entity. Carries the identifier field
    name (`locs_id`), the CRS the user supplied, and a PHI declaration.
    `phi_status` defaults to `no_phi` and is the gate on everything else: if a location set is flagged, results
    derived from it must not be written to shared catalog tables or embedded in an exported EnVar record, whose
    `phi_status` is a required field precisely so this cannot be left implicit.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["LocationSet"]
    class_class_curie: ClassVar[str] = "amadeus:LocationSet"
    class_name: ClassVar[str] = "LocationSet"
    class_model_uri: ClassVar[URIRef] = AMADEUS.LocationSet

    id: Union[str, LocationSetId] = None
    locs_id_field: str = None
    crs: str = None
    phi_status: Union[str, "PhiStatusEnum"] = 'no_phi'
    name: Optional[str] = None
    description: Optional[str] = None
    srid: Optional[int] = None
    geometry_type: Optional[Union[str, "GeometryTypeEnum"]] = None
    location_count: Optional[int] = None
    provided_by: Optional[str] = None
    created_at: Optional[Union[str, XSDDateTime]] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, LocationSetId):
            self.id = LocationSetId(self.id)

        if self._is_empty(self.locs_id_field):
            self.MissingRequiredField("locs_id_field")
        if not isinstance(self.locs_id_field, str):
            self.locs_id_field = str(self.locs_id_field)

        if self._is_empty(self.crs):
            self.MissingRequiredField("crs")
        if not isinstance(self.crs, str):
            self.crs = str(self.crs)

        if self._is_empty(self.phi_status):
            self.MissingRequiredField("phi_status")
        if not isinstance(self.phi_status, PhiStatusEnum):
            self.phi_status = PhiStatusEnum(self.phi_status)

        if self.name is not None and not isinstance(self.name, str):
            self.name = str(self.name)

        if self.description is not None and not isinstance(self.description, str):
            self.description = str(self.description)

        if self.srid is not None and not isinstance(self.srid, int):
            self.srid = int(self.srid)

        if self.geometry_type is not None and not isinstance(self.geometry_type, GeometryTypeEnum):
            self.geometry_type = GeometryTypeEnum(self.geometry_type)

        if self.location_count is not None and not isinstance(self.location_count, int):
            self.location_count = int(self.location_count)

        if self.provided_by is not None and not isinstance(self.provided_by, str):
            self.provided_by = str(self.provided_by)

        if self.created_at is not None and not isinstance(self.created_at, XSDDateTime):
            self.created_at = XSDDateTime(self.created_at)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Location(YAMLRoot):
    """
    One location in a set, with an optional validity interval.
    `valid_from` / `valid_to` exist because a residential address is not timeless. Address histories, known travel
    intervals and synthetic residence periods all need them, and without them a value is joined to a place the subject
    may not have occupied on that date. amadeus does not need to model *why* the interval exists — that is the health
    layer's business — only to honour it in the join.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["Location"]
    class_class_curie: ClassVar[str] = "amadeus:Location"
    class_name: ClassVar[str] = "Location"
    class_model_uri: ClassVar[URIRef] = AMADEUS.Location

    id: Union[str, LocationId] = None
    location_set: Union[str, LocationSetId] = None
    location_key: str = None
    location_geom_wkt: Union[str, WktLiteral] = None
    srid: Optional[int] = None
    buffer_radius_m: Optional[float] = None
    valid_from: Optional[Union[str, XSDDate]] = None
    valid_to: Optional[Union[str, XSDDate]] = None
    target_geography_type: Optional[Union[str, "TargetGeographyTypeEnum"]] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, LocationId):
            self.id = LocationId(self.id)

        if self._is_empty(self.location_set):
            self.MissingRequiredField("location_set")
        if not isinstance(self.location_set, LocationSetId):
            self.location_set = LocationSetId(self.location_set)

        if self._is_empty(self.location_key):
            self.MissingRequiredField("location_key")
        if not isinstance(self.location_key, str):
            self.location_key = str(self.location_key)

        if self._is_empty(self.location_geom_wkt):
            self.MissingRequiredField("location_geom_wkt")
        if not isinstance(self.location_geom_wkt, WktLiteral):
            self.location_geom_wkt = WktLiteral(self.location_geom_wkt)

        if self.srid is not None and not isinstance(self.srid, int):
            self.srid = int(self.srid)

        if self.buffer_radius_m is not None and not isinstance(self.buffer_radius_m, float):
            self.buffer_radius_m = float(self.buffer_radius_m)

        if self.valid_from is not None and not isinstance(self.valid_from, XSDDate):
            self.valid_from = XSDDate(self.valid_from)

        if self.valid_to is not None and not isinstance(self.valid_to, XSDDate):
            self.valid_to = XSDDate(self.valid_to)

        if self.target_geography_type is not None and not isinstance(self.target_geography_type, TargetGeographyTypeEnum):
            self.target_geography_type = TargetGeographyTypeEnum(self.target_geography_type)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ExtractionRequest(YAMLRoot):
    """
    A declarative, reproducible specification of an extraction: which variables, over which locations, for which time
    window, with which buffer, aggregation, weighting and lags.
    The rules below are the ones that make the request *checkable before it runs*, which is the point. The extensivity
    rule in particular turns the project lead's "intensive vs extensive should be explicit" from documentation into a
    validation error.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["ExtractionRequest"]
    class_class_curie: ClassVar[str] = "amadeus:ExtractionRequest"
    class_name: ClassVar[str] = "ExtractionRequest"
    class_model_uri: ClassVar[URIRef] = AMADEUS.ExtractionRequest

    id: Union[str, ExtractionRequestId] = None
    location_set: Union[str, LocationSetId] = None
    time_window_start: Union[str, XSDDateTime] = None
    time_window_end: Union[str, XSDDateTime] = None
    extraction_method: Union[str, "ExtractionMethodEnum"] = None
    request_hash: Union[str, Sha256] = None
    name: Optional[str] = None
    requested_canonical_variables: Optional[Union[Union[str, CanonicalVariableId], list[Union[str, CanonicalVariableId]]]] = empty_list()
    requested_product_variables: Optional[Union[Union[str, ProductVariableId], list[Union[str, ProductVariableId]]]] = empty_list()
    temporal_grouping: Optional[Union[str, "TemporalGroupingEnum"]] = None
    buffer_radius_m: Optional[float] = None
    aggregation_method: Optional[Union[str, "AggregationMethodEnum"]] = None
    weighting_product_variable: Optional[Union[str, ProductVariableId]] = None
    lag_days: Optional[Union[int, list[int]]] = empty_list()
    target_geography_type: Optional[Union[str, "TargetGeographyTypeEnum"]] = None
    output_orientation: Optional[Union[str, "TableOrientationEnum"]] = 'long'
    materialization_mode: Optional[Union[str, "MaterializationModeEnum"]] = None
    source_priority_policy: Optional[str] = None
    status_mixing_policy: Optional[Union[str, "StatusMixingPolicyEnum"]] = 'refuse'
    strict_extensivity_check: Optional[Union[str, "StrictnessEnum"]] = 'strict'
    requested_by: Optional[str] = None
    request_timestamp_utc: Optional[Union[str, XSDDateTime]] = None
    generated_sql: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, ExtractionRequestId):
            self.id = ExtractionRequestId(self.id)

        if self._is_empty(self.location_set):
            self.MissingRequiredField("location_set")
        if not isinstance(self.location_set, LocationSetId):
            self.location_set = LocationSetId(self.location_set)

        if self._is_empty(self.time_window_start):
            self.MissingRequiredField("time_window_start")
        if not isinstance(self.time_window_start, XSDDateTime):
            self.time_window_start = XSDDateTime(self.time_window_start)

        if self._is_empty(self.time_window_end):
            self.MissingRequiredField("time_window_end")
        if not isinstance(self.time_window_end, XSDDateTime):
            self.time_window_end = XSDDateTime(self.time_window_end)

        if self._is_empty(self.extraction_method):
            self.MissingRequiredField("extraction_method")
        if not isinstance(self.extraction_method, ExtractionMethodEnum):
            self.extraction_method = ExtractionMethodEnum(self.extraction_method)

        if self._is_empty(self.request_hash):
            self.MissingRequiredField("request_hash")
        if not isinstance(self.request_hash, Sha256):
            self.request_hash = Sha256(self.request_hash)

        if self.name is not None and not isinstance(self.name, str):
            self.name = str(self.name)

        if not isinstance(self.requested_canonical_variables, list):
            self.requested_canonical_variables = [self.requested_canonical_variables] if self.requested_canonical_variables is not None else []
        self.requested_canonical_variables = [v if isinstance(v, CanonicalVariableId) else CanonicalVariableId(v) for v in self.requested_canonical_variables]

        if not isinstance(self.requested_product_variables, list):
            self.requested_product_variables = [self.requested_product_variables] if self.requested_product_variables is not None else []
        self.requested_product_variables = [v if isinstance(v, ProductVariableId) else ProductVariableId(v) for v in self.requested_product_variables]

        if self.temporal_grouping is not None and not isinstance(self.temporal_grouping, TemporalGroupingEnum):
            self.temporal_grouping = TemporalGroupingEnum(self.temporal_grouping)

        if self.buffer_radius_m is not None and not isinstance(self.buffer_radius_m, float):
            self.buffer_radius_m = float(self.buffer_radius_m)

        if self.aggregation_method is not None and not isinstance(self.aggregation_method, AggregationMethodEnum):
            self.aggregation_method = AggregationMethodEnum(self.aggregation_method)

        if self.weighting_product_variable is not None and not isinstance(self.weighting_product_variable, ProductVariableId):
            self.weighting_product_variable = ProductVariableId(self.weighting_product_variable)

        if not isinstance(self.lag_days, list):
            self.lag_days = [self.lag_days] if self.lag_days is not None else []
        self.lag_days = [v if isinstance(v, int) else int(v) for v in self.lag_days]

        if self.target_geography_type is not None and not isinstance(self.target_geography_type, TargetGeographyTypeEnum):
            self.target_geography_type = TargetGeographyTypeEnum(self.target_geography_type)

        if self.output_orientation is not None and not isinstance(self.output_orientation, TableOrientationEnum):
            self.output_orientation = TableOrientationEnum(self.output_orientation)

        if self.materialization_mode is not None and not isinstance(self.materialization_mode, MaterializationModeEnum):
            self.materialization_mode = MaterializationModeEnum(self.materialization_mode)

        if self.source_priority_policy is not None and not isinstance(self.source_priority_policy, str):
            self.source_priority_policy = str(self.source_priority_policy)

        if self.status_mixing_policy is not None and not isinstance(self.status_mixing_policy, StatusMixingPolicyEnum):
            self.status_mixing_policy = StatusMixingPolicyEnum(self.status_mixing_policy)

        if self.strict_extensivity_check is not None and not isinstance(self.strict_extensivity_check, StrictnessEnum):
            self.strict_extensivity_check = StrictnessEnum(self.strict_extensivity_check)

        if self.requested_by is not None and not isinstance(self.requested_by, str):
            self.requested_by = str(self.requested_by)

        if self.request_timestamp_utc is not None and not isinstance(self.request_timestamp_utc, XSDDateTime):
            self.request_timestamp_utc = XSDDateTime(self.request_timestamp_utc)

        if self.generated_sql is not None and not isinstance(self.generated_sql, str):
            self.generated_sql = str(self.generated_sql)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class AmbientValueAtLocation(AmbientValue):
    """
    The output row: an ambient value assigned to a user location for a time interval, with the extraction that
    produced it recorded alongside. This is what `calculate_covariates()` returns today, plus the metadata it
    currently drops.
    Not an exposure. The location may be a person's address and the row may carry a cohort key, but the value is a
    property of the place: swap the person, keep the address, and it does not change.
    What today's output has, that this keeps: location key, time, value. What today's output lacks, that this adds:
    which product variable and which canonical variable (today encoded positionally in a column name like `weasd_0`),
    the extraction method and buffer actually used, how many source values contributed, coverage, distance to the
    contributing station, the quality and status of the inputs, and the run that produced it.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["AmbientValueAtLocation"]
    class_class_curie: ClassVar[str] = "amadeus:AmbientValueAtLocation"
    class_name: ClassVar[str] = "AmbientValueAtLocation"
    class_model_uri: ClassVar[URIRef] = AMADEUS.AmbientValueAtLocation

    id: Union[str, AmbientValueAtLocationId] = None
    product_variable: Union[str, ProductVariableId] = None
    canonical_variable: Union[str, CanonicalVariableId] = None
    valid_time_start: Union[str, XSDDateTime] = None
    data_status: Union[str, "DataStatusEnum"] = None
    source_system: str = None
    null_semantics: Union[str, "NullSemanticsEnum"] = None
    location: Union[str, LocationId] = None
    extraction_request: Union[str, ExtractionRequestId] = None
    extraction_method: Union[str, "ExtractionMethodEnum"] = None
    buffer_radius_m: Optional[float] = None
    aggregation_method: Optional[Union[str, "AggregationMethodEnum"]] = None
    contributing_value_count: Optional[int] = None
    coverage_fraction: Optional[float] = None
    distance_to_source_m: Optional[float] = None
    lag_days_applied: Optional[int] = None
    temporal_grouping: Optional[Union[str, "TemporalGroupingEnum"]] = None
    output_column_name: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, AmbientValueAtLocationId):
            self.id = AmbientValueAtLocationId(self.id)

        if self._is_empty(self.location):
            self.MissingRequiredField("location")
        if not isinstance(self.location, LocationId):
            self.location = LocationId(self.location)

        if self._is_empty(self.extraction_request):
            self.MissingRequiredField("extraction_request")
        if not isinstance(self.extraction_request, ExtractionRequestId):
            self.extraction_request = ExtractionRequestId(self.extraction_request)

        if self._is_empty(self.extraction_method):
            self.MissingRequiredField("extraction_method")
        if not isinstance(self.extraction_method, ExtractionMethodEnum):
            self.extraction_method = ExtractionMethodEnum(self.extraction_method)

        if self.buffer_radius_m is not None and not isinstance(self.buffer_radius_m, float):
            self.buffer_radius_m = float(self.buffer_radius_m)

        if self.aggregation_method is not None and not isinstance(self.aggregation_method, AggregationMethodEnum):
            self.aggregation_method = AggregationMethodEnum(self.aggregation_method)

        if self.contributing_value_count is not None and not isinstance(self.contributing_value_count, int):
            self.contributing_value_count = int(self.contributing_value_count)

        if self.coverage_fraction is not None and not isinstance(self.coverage_fraction, float):
            self.coverage_fraction = float(self.coverage_fraction)

        if self.distance_to_source_m is not None and not isinstance(self.distance_to_source_m, float):
            self.distance_to_source_m = float(self.distance_to_source_m)

        if self.lag_days_applied is not None and not isinstance(self.lag_days_applied, int):
            self.lag_days_applied = int(self.lag_days_applied)

        if self.temporal_grouping is not None and not isinstance(self.temporal_grouping, TemporalGroupingEnum):
            self.temporal_grouping = TemporalGroupingEnum(self.temporal_grouping)

        if self.output_column_name is not None and not isinstance(self.output_column_name, str):
            self.output_column_name = str(self.output_column_name)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ToolRun(YAMLRoot):
    """
    One execution of one amadeus operation, with everything needed to decide whether it can be trusted and whether it
    can be skipped.
    "Whether it can be skipped" is the idempotency requirement: re-running a workflow with the same inputs and
    configuration should reuse valid outputs and recover from partial failures without silent duplication. That needs
    `input_file_sha256`, `output_file_sha256`, `run_arguments` and `status` — not a timestamp and a log line.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = PROV["Activity"]
    class_class_curie: ClassVar[str] = "prov:Activity"
    class_name: ClassVar[str] = "ToolRun"
    class_model_uri: ClassVar[URIRef] = AMADEUS.ToolRun

    id: Union[str, ToolRunId] = None
    run_role: Union[str, "RunRoleEnum"] = None
    tool_version: str = None
    run_timestamp_utc: Union[str, XSDDateTime] = None
    status: Union[str, "RunStatusEnum"] = None
    tool_name: str = "amadeus"
    function_name: Optional[str] = None
    run_arguments: Optional[str] = None
    container_image_repository: Optional[str] = None
    container_image_digest: Optional[str] = None
    run_duration_seconds: Optional[float] = None
    run_environment: Optional[str] = None
    input_asset_ids: Optional[Union[str, list[str]]] = empty_list()
    input_file_sha256: Optional[Union[str, Sha256]] = None
    input_row_count: Optional[int] = None
    output_file_sha256: Optional[Union[str, Sha256]] = None
    output_row_count: Optional[int] = None
    upstream_runs: Optional[Union[str, list[str]]] = empty_list()
    log_excerpt: Optional[str] = None
    materialization_mode: Optional[Union[str, "MaterializationModeEnum"]] = None
    bytes_transferred: Optional[int] = None
    request_count: Optional[int] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, ToolRunId):
            self.id = ToolRunId(self.id)

        if self._is_empty(self.run_role):
            self.MissingRequiredField("run_role")
        if not isinstance(self.run_role, RunRoleEnum):
            self.run_role = RunRoleEnum(self.run_role)

        if self._is_empty(self.tool_name):
            self.MissingRequiredField("tool_name")
        if not isinstance(self.tool_name, str):
            self.tool_name = str(self.tool_name)

        if self._is_empty(self.tool_version):
            self.MissingRequiredField("tool_version")
        if not isinstance(self.tool_version, str):
            self.tool_version = str(self.tool_version)

        if self._is_empty(self.run_timestamp_utc):
            self.MissingRequiredField("run_timestamp_utc")
        if not isinstance(self.run_timestamp_utc, XSDDateTime):
            self.run_timestamp_utc = XSDDateTime(self.run_timestamp_utc)

        if self._is_empty(self.status):
            self.MissingRequiredField("status")
        if not isinstance(self.status, RunStatusEnum):
            self.status = RunStatusEnum(self.status)

        if self.function_name is not None and not isinstance(self.function_name, str):
            self.function_name = str(self.function_name)

        if self.run_arguments is not None and not isinstance(self.run_arguments, str):
            self.run_arguments = str(self.run_arguments)

        if self.container_image_repository is not None and not isinstance(self.container_image_repository, str):
            self.container_image_repository = str(self.container_image_repository)

        if self.container_image_digest is not None and not isinstance(self.container_image_digest, str):
            self.container_image_digest = str(self.container_image_digest)

        if self.run_duration_seconds is not None and not isinstance(self.run_duration_seconds, float):
            self.run_duration_seconds = float(self.run_duration_seconds)

        if self.run_environment is not None and not isinstance(self.run_environment, str):
            self.run_environment = str(self.run_environment)

        if not isinstance(self.input_asset_ids, list):
            self.input_asset_ids = [self.input_asset_ids] if self.input_asset_ids is not None else []
        self.input_asset_ids = [v if isinstance(v, str) else str(v) for v in self.input_asset_ids]

        if self.input_file_sha256 is not None and not isinstance(self.input_file_sha256, Sha256):
            self.input_file_sha256 = Sha256(self.input_file_sha256)

        if self.input_row_count is not None and not isinstance(self.input_row_count, int):
            self.input_row_count = int(self.input_row_count)

        if self.output_file_sha256 is not None and not isinstance(self.output_file_sha256, Sha256):
            self.output_file_sha256 = Sha256(self.output_file_sha256)

        if self.output_row_count is not None and not isinstance(self.output_row_count, int):
            self.output_row_count = int(self.output_row_count)

        if not isinstance(self.upstream_runs, list):
            self.upstream_runs = [self.upstream_runs] if self.upstream_runs is not None else []
        self.upstream_runs = [v if isinstance(v, str) else str(v) for v in self.upstream_runs]

        if self.log_excerpt is not None and not isinstance(self.log_excerpt, str):
            self.log_excerpt = str(self.log_excerpt)

        if self.materialization_mode is not None and not isinstance(self.materialization_mode, MaterializationModeEnum):
            self.materialization_mode = MaterializationModeEnum(self.materialization_mode)

        if self.bytes_transferred is not None and not isinstance(self.bytes_transferred, int):
            self.bytes_transferred = int(self.bytes_transferred)

        if self.request_count is not None and not isinstance(self.request_count, int):
            self.request_count = int(self.request_count)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ProvenanceChain(YAMLRoot):
    """
    A materialised walk of `upstream_runs` from a derived value back to its terminus, plus what the terminus is.
    Stored rather than always recomputed because it is what an exported EnVar record carries, and because the
    recursive query is expensive to run per row at export time.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = AMADEUS["ProvenanceChain"]
    class_class_curie: ClassVar[str] = "amadeus:ProvenanceChain"
    class_name: ClassVar[str] = "ProvenanceChain"
    class_model_uri: ClassVar[URIRef] = AMADEUS.ProvenanceChain

    id: Union[str, ProvenanceChainId] = None
    terminus_type: Union[str, "ProvenanceChainTerminusEnum"] = None
    chain_steps: Optional[Union[str, list[str]]] = empty_list()
    compatibility_assertions: Optional[Union[str, list[str]]] = empty_list()

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, ProvenanceChainId):
            self.id = ProvenanceChainId(self.id)

        if self._is_empty(self.terminus_type):
            self.MissingRequiredField("terminus_type")
        if not isinstance(self.terminus_type, ProvenanceChainTerminusEnum):
            self.terminus_type = ProvenanceChainTerminusEnum(self.terminus_type)

        if not isinstance(self.chain_steps, list):
            self.chain_steps = [self.chain_steps] if self.chain_steps is not None else []
        self.chain_steps = [v if isinstance(v, str) else str(v) for v in self.chain_steps]

        if not isinstance(self.compatibility_assertions, list):
            self.compatibility_assertions = [self.compatibility_assertions] if self.compatibility_assertions is not None else []
        self.compatibility_assertions = [v if isinstance(v, str) else str(v) for v in self.compatibility_assertions]

        super().__post_init__(**kwargs)


# Enumerations
class SpatialSupportTypeEnum(EnumDefinitionImpl):
    """
    What a single value spatially *is* — the source-side question. Distinct from `TargetGeographyTypeEnum`, which says
    what a value gets attached to. Both are needed; neither replaces the other.
    """
    point = PermissibleValue(
        text="point",
        description="A dimensionless location.")
    monitoring_station = PermissibleValue(
        text="monitoring_station",
        description="A fixed instrument with an identity that persists across time.")
    raster_grid_cell = PermissibleValue(
        text="raster_grid_cell",
        description="A cell of an observational or retrieval grid.")
    model_grid_cell = PermissibleValue(
        text="model_grid_cell",
        description="A cell of a model or reanalysis grid.")
    polygon = PermissibleValue(
        text="polygon",
        description="An arbitrary polygon feature (a smoke plume, a drought area).")
    administrative_area = PermissibleValue(
        text="administrative_area",
        description="A governmental unit (county, state).")
    statistical_area = PermissibleValue(
        text="statistical_area",
        description="A statistical unit (census tract, block group, ZCTA).")
    hex_cell = PermissibleValue(
        text="hex_cell",
        description="A hierarchical hexagonal cell, in practice H3.")
    line_feature = PermissibleValue(
        text="line_feature",
        description="A linear feature (a road segment, a stream reach).")
    other = PermissibleValue(text="other")

    _defn = EnumDefinition(
        name="SpatialSupportTypeEnum",
        description="""What a single value spatially *is* — the source-side question. Distinct from `TargetGeographyTypeEnum`, which says what a value gets attached to. Both are needed; neither replaces the other.""",
    )

class TargetGeographyTypeEnum(EnumDefinitionImpl):
    """
    The geography a value is delivered against, after extraction.
    """
    point_location = PermissibleValue(
        text="point_location",
        description="""A coordinate pair supplied by the user. Deliberately *not* named `point_residence` — amadeus knows nothing about residences.""")
    buffered_point = PermissibleValue(text="buffered_point")
    census_block_group = PermissibleValue(text="census_block_group")
    census_tract = PermissibleValue(text="census_tract")
    zcta = PermissibleValue(text="zcta")
    county = PermissibleValue(text="county")
    state = PermissibleValue(text="state")
    hydrologic_unit = PermissibleValue(text="hydrologic_unit")
    h3_hex = PermissibleValue(text="h3_hex")
    grid_cell = PermissibleValue(text="grid_cell")
    public_water_system = PermissibleValue(text="public_water_system")

    _defn = EnumDefinition(
        name="TargetGeographyTypeEnum",
        description="The geography a value is delivered against, after extraction.",
    )

class TemporalResolutionEnum(EnumDefinitionImpl):

    instantaneous = PermissibleValue(text="instantaneous")
    subhourly = PermissibleValue(text="subhourly")
    hourly = PermissibleValue(text="hourly")
    three_hourly = PermissibleValue(text="three_hourly")
    daily = PermissibleValue(text="daily")
    monthly = PermissibleValue(text="monthly")
    seasonal = PermissibleValue(text="seasonal")
    annual = PermissibleValue(text="annual")
    multi_year_epoch = PermissibleValue(
        text="multi_year_epoch",
        description="Irregularly spaced named epochs rather than a regular series.")
    timeless = PermissibleValue(
        text="timeless",
        description="""Static: the product asserts no valid time. Modelled as an unbounded valid interval rather than a null, so time predicates still work.""")

    _defn = EnumDefinition(
        name="TemporalResolutionEnum",
    )

class TemporalAlignmentEnum(EnumDefinitionImpl):
    """
    Where in the aggregation window the timestamp sits. Taken from HEW, which has it and EnVar does not — a genuine
    gap EnVar should close.
    """
    start = PermissibleValue(text="start")
    center = PermissibleValue(text="center")
    end = PermissibleValue(text="end")
    interval = PermissibleValue(
        text="interval",
        description="The record carries both bounds explicitly.")
    unknown = PermissibleValue(text="unknown")

    _defn = EnumDefinition(
        name="TemporalAlignmentEnum",
        description="""Where in the aggregation window the timestamp sits. Taken from HEW, which has it and EnVar does not — a genuine gap EnVar should close.""",
    )

class DayBoundaryConventionEnum(EnumDefinitionImpl):
    """
    Where a "day" starts for a daily product. This is the slot behind the Daymet/GridMET 1.26 °C discrepancy: same
    variable, same place, same date, different day boundary.
    """
    local_midnight = PermissibleValue(text="local_midnight")
    utc_midnight = PermissibleValue(text="utc_midnight")
    ending_1200_gmt = PermissibleValue(text="ending_1200_gmt")
    solar_noon_centered = PermissibleValue(text="solar_noon_centered")
    observation_dependent = PermissibleValue(text="observation_dependent")
    not_applicable = PermissibleValue(text="not_applicable")

    _defn = EnumDefinition(
        name="DayBoundaryConventionEnum",
        description="""Where a \"day\" starts for a daily product. This is the slot behind the Daymet/GridMET 1.26 °C discrepancy: same variable, same place, same date, different day boundary.""",
    )

class CalendarEnum(EnumDefinitionImpl):

    gregorian = PermissibleValue(text="gregorian")
    proleptic_gregorian = PermissibleValue(text="proleptic_gregorian")
    noleap = PermissibleValue(text="noleap")
    daymet_365 = PermissibleValue(text="daymet_365")
    all_leap = PermissibleValue(text="all_leap")
    day_360 = PermissibleValue(text="day_360")
    julian = PermissibleValue(text="julian")

    _defn = EnumDefinition(
        name="CalendarEnum",
    )

class AggregationMethodEnum(EnumDefinitionImpl):
    """
    How many values became one. Which members are *legal* for a given variable is determined by
    `VariableExtensivityEnum` — see the rules on `ExtractionRequest`.
    """
    instantaneous = PermissibleValue(text="instantaneous")
    mean = PermissibleValue(text="mean")
    minimum = PermissibleValue(text="minimum")
    maximum = PermissibleValue(text="maximum")
    median = PermissibleValue(text="median")
    sum = PermissibleValue(text="sum")
    count = PermissibleValue(text="count")
    percentile = PermissibleValue(text="percentile")
    cumulative = PermissibleValue(text="cumulative")
    area_weighted_mean = PermissibleValue(text="area_weighted_mean")
    population_weighted_mean = PermissibleValue(text="population_weighted_mean")
    mode = PermissibleValue(text="mode")
    class_proportion = PermissibleValue(
        text="class_proportion",
        description="Fraction of the support occupied by one categorical class.")
    density = PermissibleValue(
        text="density",
        description="Feature quantity per unit area.")
    nearest = PermissibleValue(text="nearest")
    other = PermissibleValue(text="other")

    _defn = EnumDefinition(
        name="AggregationMethodEnum",
        description="""How many values became one. Which members are *legal* for a given variable is determined by `VariableExtensivityEnum` — see the rules on `ExtractionRequest`.""",
    )

class ExtractionMethodEnum(EnumDefinitionImpl):
    """
    How a value was pulled out of its source support at a location.
    """
    nearest_cell = PermissibleValue(text="nearest_cell")
    bilinear = PermissibleValue(text="bilinear")
    inverse_distance_weighted_4_nearest_cells = PermissibleValue(text="inverse_distance_weighted_4_nearest_cells")
    area_weighted_polygon_mean = PermissibleValue(text="area_weighted_polygon_mean")
    population_weighted_mean = PermissibleValue(text="population_weighted_mean")
    point_station_lookup = PermissibleValue(text="point_station_lookup")
    nearest_station = PermissibleValue(text="nearest_station")
    intersection_area_proportion = PermissibleValue(text="intersection_area_proportion")
    raster_zonal_sum = PermissibleValue(text="raster_zonal_sum")
    feature_density = PermissibleValue(text="feature_density")
    exact_extract = PermissibleValue(
        text="exact_extract",
        description="""`exactextractr::exact_extract` — fractional cell coverage weighting. amadeus's default for polygon and buffered-point extraction.""")

    _defn = EnumDefinition(
        name="ExtractionMethodEnum",
        description="How a value was pulled out of its source support at a location.",
    )

class VariableExtensivityEnum(EnumDefinitionImpl):
    """
    Whether a quantity is intensive (independent of the size of its support — a temperature) or extensive (scales with
    it — a population count, an emission mass). **This is the slot that makes aggregation checkable.** Averaging an
    extensive variable over a buffer is a silent, plausible-looking error; summing an intensive one is worse.
    Requested explicitly by the project lead and tracked as amadeus issue #249.
    """
    intensive = PermissibleValue(
        text="intensive",
        description="""Value is independent of support size. Legal aggregations: mean, min, max, median, percentile, area/population-weighted mean, nearest.""")
    extensive = PermissibleValue(
        text="extensive",
        description="""Value scales with support size; aggregation must conserve the total. Legal aggregations: sum, count, cumulative, raster zonal sum, density.""")
    categorical = PermissibleValue(
        text="categorical",
        description="Nominal class label. Legal aggregations: mode, class_proportion.")
    unknown = PermissibleValue(
        text="unknown",
        description="""Not yet assessed. Permitted so migration does not require assessing every legacy variable at once, but blocks strict-mode extraction.""")

    _defn = EnumDefinition(
        name="VariableExtensivityEnum",
        description="""Whether a quantity is intensive (independent of the size of its support — a temperature) or extensive (scales with it — a population count, an emission mass). **This is the slot that makes aggregation checkable.** Averaging an extensive variable over a buffer is a silent, plausible-looking error; summing an intensive one is worse. Requested explicitly by the project lead and tracked as amadeus issue #249.""",
    )

class ValueDataTypeEnum(EnumDefinitionImpl):
    """
    The measurement kind, not the storage type.
    """
    continuous_numeric = PermissibleValue(text="continuous_numeric")
    categorical = PermissibleValue(text="categorical")
    binary_flag = PermissibleValue(text="binary_flag")
    count = PermissibleValue(text="count")
    event_marker = PermissibleValue(text="event_marker")
    proportion = PermissibleValue(text="proportion")

    _defn = EnumDefinition(
        name="ValueDataTypeEnum",
        description="The measurement kind, not the storage type.",
    )

class DataStatusEnum(EnumDefinitionImpl):
    """
    The quality state of a value *as the source declares it*. Load-bearing for the AQS/AirNow harmonization rule (plan
    §4.6.1): an AirNow preliminary value must never overwrite an AQS quality-controlled value in place, so status has
    to be carried on every row, not on the dataset.
    """
    preliminary = PermissibleValue(
        text="preliminary",
        description="Near-real-time, unvalidated. AirNow.")
    provisional = PermissibleValue(text="provisional")
    quality_controlled = PermissibleValue(
        text="quality_controlled",
        description="Passed the producer's QA process. AQS.")
    final = PermissibleValue(text="final")
    forecast = PermissibleValue(
        text="forecast",
        description="Model output valid in the future relative to its reference time.")
    reanalysis = PermissibleValue(text="reanalysis")
    superseded = PermissibleValue(
        text="superseded",
        description="""Replaced by a later revision. Retained rather than deleted — revisions create new records, they do not mutate old ones.""")
    unknown = PermissibleValue(text="unknown")

    _defn = EnumDefinition(
        name="DataStatusEnum",
        description="""The quality state of a value *as the source declares it*. Load-bearing for the AQS/AirNow harmonization rule (plan §4.6.1): an AirNow preliminary value must never overwrite an AQS quality-controlled value in place, so status has to be carried on every row, not on the dataset.""",
    )

class NullSemanticsEnum(EnumDefinitionImpl):
    """
    Why a value is absent, or why a zero is a zero.
    """
    present = PermissibleValue(text="present")
    structural_null = PermissibleValue(
        text="structural_null",
        description="The quantity cannot exist here (sea-surface temperature on land).")
    derived_null = PermissibleValue(
        text="derived_null",
        description="Inputs were missing so the derivation could not run.")
    true_zero = PermissibleValue(
        text="true_zero",
        description="""A measured zero, not a missing value. The nodata-versus-zero edge case the plan's test matrix calls out.""")

    _defn = EnumDefinition(
        name="NullSemanticsEnum",
        description="Why a value is absent, or why a zero is a zero.",
    )

class MissingReasonEnum(EnumDefinitionImpl):
    """
    Why a *metadata* field is empty. Distinguishes "the source does not provide this" from "nobody has looked yet" —
    the difference that decides whether a gap is someone's task.
    """
    not_provided_by_source = PermissibleValue(text="not_provided_by_source")
    available_but_not_extracted = PermissibleValue(
        text="available_but_not_extracted",
        description="""It is in the source file and amadeus discards it. The Tier 1 gap — the cheapest possible win, and the one to count.""")
    upstream_data_not_propagated = PermissibleValue(text="upstream_data_not_propagated")
    under_investigation = PermissibleValue(text="under_investigation")
    not_applicable = PermissibleValue(text="not_applicable")

    _defn = EnumDefinition(
        name="MissingReasonEnum",
        description="""Why a *metadata* field is empty. Distinguishes \"the source does not provide this\" from \"nobody has looked yet\" — the difference that decides whether a gap is someone's task.""",
    )

class ConceptStatusEnum(EnumDefinitionImpl):
    """
    State of the mapping from a variable to a target vocabulary. HEW's value set, which is strictly better than
    EnVar's three-valued one: it keeps standard/non-standard apart (OMOP-critical) and "nobody looked" apart from "we
    looked and there is nothing".
    """
    mapped_standard = PermissibleValue(text="mapped_standard")
    mapped_nonstandard = PermissibleValue(text="mapped_nonstandard")
    candidate_mapping = PermissibleValue(text="candidate_mapping")
    vocabulary_gap = PermissibleValue(text="vocabulary_gap")
    not_evaluated = PermissibleValue(text="not_evaluated")

    _defn = EnumDefinition(
        name="ConceptStatusEnum",
        description="""State of the mapping from a variable to a target vocabulary. HEW's value set, which is strictly better than EnVar's three-valued one: it keeps standard/non-standard apart (OMOP-critical) and \"nobody looked\" apart from \"we looked and there is nothing\".""",
    )

class NativeFormatEnum(EnumDefinitionImpl):
    """
    The format the source actually ships.
    """
    netcdf4_cf = PermissibleValue(text="netcdf4_cf")
    netcdf3 = PermissibleValue(text="netcdf3")
    hdf4 = PermissibleValue(
        text="hdf4",
        description="MODIS. Not in EnVar's enum; amadeus reads it today.")
    hdf5 = PermissibleValue(text="hdf5")
    geotiff = PermissibleValue(text="geotiff")
    cloud_optimized_geotiff = PermissibleValue(text="cloud_optimized_geotiff")
    ascii_grid = PermissibleValue(
        text="ascii_grid",
        description="GMTED2010, PRISM `.asc`.")
    grib1 = PermissibleValue(text="grib1")
    grib2 = PermissibleValue(text="grib2")
    bil = PermissibleValue(
        text="bil",
        description="PRISM binary interleaved.")
    shapefile = PermissibleValue(text="shapefile")
    geodatabase = PermissibleValue(text="geodatabase")
    kml = PermissibleValue(text="kml")
    csv_station_observations = PermissibleValue(text="csv_station_observations")
    pipe_delimited_text = PermissibleValue(
        text="pipe_delimited_text",
        description="IMPROVE aerosol exports.")
    fixed_width_text = PermissibleValue(text="fixed_width_text")
    zarr = PermissibleValue(text="zarr")
    parquet = PermissibleValue(text="parquet")
    geoparquet = PermissibleValue(text="geoparquet")

    _defn = EnumDefinition(
        name="NativeFormatEnum",
        description="The format the source actually ships.",
    )

class DataGenreEnum(EnumDefinitionImpl):
    """
    The thematic classification already used in the amadeus README's source table. Promoted from prose to an enum so
    it can drive discovery.
    """
    meteorology = PermissibleValue(text="meteorology")
    climate = PermissibleValue(text="climate")
    climate_classification = PermissibleValue(text="climate_classification")
    air_pollution = PermissibleValue(text="air_pollution")
    aerosols = PermissibleValue(text="aerosols")
    atmosphere = PermissibleValue(text="atmosphere")
    emissions = PermissibleValue(text="emissions")
    chemicals = PermissibleValue(text="chemicals")
    land_use = PermissibleValue(text="land_use")
    agriculture = PermissibleValue(text="agriculture")
    population = PermissibleValue(text="population")
    hydrology = PermissibleValue(text="hydrology")
    water = PermissibleValue(text="water")
    elevation = PermissibleValue(text="elevation")
    roadways = PermissibleValue(text="roadways")
    wildfire_smoke = PermissibleValue(text="wildfire_smoke")
    drought = PermissibleValue(text="drought")
    satellite = PermissibleValue(text="satellite")
    built_environment = PermissibleValue(text="built_environment")

    _defn = EnumDefinition(
        name="DataGenreEnum",
        description="""The thematic classification already used in the amadeus README's source table. Promoted from prose to an enum so it can drive discovery.""",
    )

class AccessProtocolEnum(EnumDefinitionImpl):
    """
    How amadeus reaches a source. Determines whether subsetting can be pushed to the provider, which is the whole
    point of the "subset early" principle.
    """
    https_bulk_file = PermissibleValue(
        text="https_bulk_file",
        description="Fetch whole files over HTTPS. No server-side subsetting.")
    ftp = PermissibleValue(text="ftp")
    s3_object_store = PermissibleValue(text="s3_object_store")
    stac_api = PermissibleValue(
        text="stac_api",
        description="Spatio-temporal asset search. Supports geometry/time pushdown.")
    opendap = PermissibleValue(
        text="opendap",
        description="Supports variable and index-range pushdown.")
    thredds = PermissibleValue(text="thredds")
    rest_api = PermissibleValue(
        text="rest_api",
        description="Provider-specific API with query parameters (AQS, AirNow, USGS).")
    harmony = PermissibleValue(text="harmony")
    arcgis_service = PermissibleValue(text="arcgis_service")

    _defn = EnumDefinition(
        name="AccessProtocolEnum",
        description="""How amadeus reaches a source. Determines whether subsetting can be pushed to the provider, which is the whole point of the \"subset early\" principle.""",
    )

class MaterializationModeEnum(EnumDefinitionImpl):
    """
    How much of a source asset had to be brought local to answer a request. Taken verbatim from the modernization plan
    §4.7.2 so "streaming" is a recorded, auditable property of a run rather than an ungoverned side path.
    """
    direct_remote_scan = PermissibleValue(
        text="direct_remote_scan",
        description="Only the required columns, row groups, ranges or tiles were read.")
    server_side_subset = PermissibleValue(
        text="server_side_subset",
        description="The provider API returned exactly the requested subset.")
    bounded_cache = PermissibleValue(
        text="bounded_cache",
        description="Selected assets or chunks cached with checksums and a reuse policy.")
    full_materialization = PermissibleValue(
        text="full_materialization",
        description="""The complete asset was downloaded because no reliable subset path exists. Cost and storage must be made visible before execution.""")

    _defn = EnumDefinition(
        name="MaterializationModeEnum",
        description="""How much of a source asset had to be brought local to answer a request. Taken verbatim from the modernization plan §4.7.2 so \"streaming\" is a recorded, auditable property of a run rather than an ungoverned side path.""",
    )

class RunRoleEnum(EnumDefinitionImpl):
    """
    Which amadeus verb a tool run represents. The three public verbs plus the database-era additions.
    """
    download = PermissibleValue(text="download")
    process = PermissibleValue(text="process")
    calculate = PermissibleValue(text="calculate")
    register = PermissibleValue(
        text="register",
        description="An asset was catalogued without materialising its values.")
    harmonize = PermissibleValue(
        text="harmonize",
        description="Cross-source reconciliation, hexification, unit conversion.")
    export = PermissibleValue(
        text="export",
        description="An EnVar record or analysis-ready table was emitted.")

    _defn = EnumDefinition(
        name="RunRoleEnum",
        description="Which amadeus verb a tool run represents. The three public verbs plus the database-era additions.",
    )

    @classmethod
    def _addvals(cls):
        setattr(cls, "import",
            PermissibleValue(
                text="import",
                description="An externally supplied dataset was brought into the catalog."))

class PhiStatusEnum(EnumDefinitionImpl):
    """
    Whether a location set, and anything derived from it, is protected health information. An enum rather than a
    boolean for two reasons: it matches EnVar's `phi_status` exactly, and — see `ValueMaterializationEnum` — a boolean
    cannot be used as a LinkML rule precondition.
    """
    no_phi = PermissibleValue(text="no_phi")
    aggregated_no_phi = PermissibleValue(text="aggregated_no_phi")
    phi_present = PermissibleValue(text="phi_present")

    _defn = EnumDefinition(
        name="PhiStatusEnum",
        description="""Whether a location set, and anything derived from it, is protected health information. An enum rather than a boolean for two reasons: it matches EnVar's `phi_status` exactly, and — see `ValueMaterializationEnum` — a boolean cannot be used as a LinkML rule precondition.""",
    )

class ValueMaterializationEnum(EnumDefinitionImpl):
    """
    Whether an asset's values exist as rows in a value table, or the asset is catalogued for discovery only.
    **This was a boolean and had to stop being one.** LinkML's only equality construct in a rule precondition is
    `equals_string`, which generates `{"const": "true"}` — the JSON *string* `"true"` — and therefore never matches
    the JSON boolean `true`. A rule keyed on a boolean silently never fires. Verified 2026-09-18 on linkml 1.9.x; see
    REPORT.md.
    """
    registered_only = PermissibleValue(
        text="registered_only",
        description="Catalogued and discoverable; no value rows written.")
    materialized = PermissibleValue(
        text="materialized",
        description="Value rows exist in a value table.")

    _defn = EnumDefinition(
        name="ValueMaterializationEnum",
        description="""Whether an asset's values exist as rows in a value table, or the asset is catalogued for discovery only.
**This was a boolean and had to stop being one.** LinkML's only equality construct in a rule precondition is `equals_string`, which generates `{\"const\": \"true\"}` — the JSON *string* `\"true\"` — and therefore never matches the JSON boolean `true`. A rule keyed on a boolean silently never fires. Verified 2026-09-18 on linkml 1.9.x; see REPORT.md.""",
    )

class StatusMixingPolicyEnum(EnumDefinitionImpl):
    """
    Whether a request may combine values of different `data_status` — in practice, AirNow preliminary alongside AQS
    quality-controlled. Defaults to refusing. An enum for the same reason as `ValueMaterializationEnum`: it is a rule
    precondition, and booleans cannot be.
    """
    refuse = PermissibleValue(
        text="refuse",
        description="""Reject the request if the candidate values differ in status. The default, per the harmonization rule in plan section 4.6.1.""")
    allow_with_policy = PermissibleValue(
        text="allow_with_policy",
        description="Permitted, and `source_priority_policy` must state how values are reconciled.")

    _defn = EnumDefinition(
        name="StatusMixingPolicyEnum",
        description="""Whether a request may combine values of different `data_status` — in practice, AirNow preliminary alongside AQS quality-controlled. Defaults to refusing. An enum for the same reason as `ValueMaterializationEnum`: it is a rule precondition, and booleans cannot be.""",
    )

class StrictnessEnum(EnumDefinitionImpl):

    strict = PermissibleValue(text="strict")
    permissive = PermissibleValue(text="permissive")

    _defn = EnumDefinition(
        name="StrictnessEnum",
    )

class RunStatusEnum(EnumDefinitionImpl):

    succeeded = PermissibleValue(text="succeeded")
    failed = PermissibleValue(text="failed")
    partial = PermissibleValue(text="partial")
    cancelled = PermissibleValue(text="cancelled")

    _defn = EnumDefinition(
        name="RunStatusEnum",
    )

class GeometryTypeEnum(EnumDefinitionImpl):

    point = PermissibleValue(text="point")
    multipoint = PermissibleValue(text="multipoint")
    linestring = PermissibleValue(text="linestring")
    multilinestring = PermissibleValue(text="multilinestring")
    polygon = PermissibleValue(text="polygon")
    multipolygon = PermissibleValue(text="multipolygon")
    geometrycollection = PermissibleValue(text="geometrycollection")

    _defn = EnumDefinition(
        name="GeometryTypeEnum",
    )

class TableOrientationEnum(EnumDefinitionImpl):

    wide = PermissibleValue(
        text="wide",
        description="""One column per variable. What `calculate_covariates()` returns today (`weasd_0`, `tmmx_10000`, …).""")
    long = PermissibleValue(
        text="long",
        description="""One row per variable-time-location. The database-native orientation, and the only one that generalises across products.""")

    _defn = EnumDefinition(
        name="TableOrientationEnum",
    )

class TemporalGroupingEnum(EnumDefinitionImpl):
    """
    The `.by_time` argument of `calculate_covariates()`, made declarative.
    """
    none = PermissibleValue(text="none")
    hour = PermissibleValue(text="hour")
    day = PermissibleValue(text="day")
    month = PermissibleValue(text="month")
    year = PermissibleValue(text="year")

    _defn = EnumDefinition(
        name="TemporalGroupingEnum",
        description="The `.by_time` argument of `calculate_covariates()`, made declarative.",
    )

class HomogenisationStatusEnum(EnumDefinitionImpl):

    homogenised = PermissibleValue(text="homogenised")
    not_homogenised = PermissibleValue(text="not_homogenised")
    partial = PermissibleValue(text="partial")

    _defn = EnumDefinition(
        name="HomogenisationStatusEnum",
    )

class AreaTypeEnum(EnumDefinitionImpl):

    county = PermissibleValue(text="county")
    state = PermissibleValue(text="state")
    census_tract = PermissibleValue(text="census_tract")
    census_block_group = PermissibleValue(text="census_block_group")
    zcta = PermissibleValue(text="zcta")
    hydrologic_unit = PermissibleValue(text="hydrologic_unit")
    ecoregion = PermissibleValue(text="ecoregion")
    smoke_plume = PermissibleValue(text="smoke_plume")
    drought_area = PermissibleValue(text="drought_area")
    public_water_system = PermissibleValue(text="public_water_system")
    custom = PermissibleValue(text="custom")

    _defn = EnumDefinition(
        name="AreaTypeEnum",
    )

class AreaRoleEnum(EnumDefinitionImpl):
    """
    Whether an area's identity is externally stable or episodic. Determines whether cross-time aggregation over the
    area is meaningful.
    """
    administrative = PermissibleValue(
        text="administrative",
        description="""Externally defined and stable across time (a county FIPS). Safe to aggregate over time; still subject to boundary revisions, which are handled as new areas rather than mutated ones.""")
    episodic = PermissibleValue(
        text="episodic",
        description="""The polygon exists because an event occurred (a smoke plume on one day). Aggregating across time is meaningless; the correct operation is intersection with a location.""")

    _defn = EnumDefinition(
        name="AreaRoleEnum",
        description="""Whether an area's identity is externally stable or episodic. Determines whether cross-time aggregation over the area is meaningful.""",
    )

class ProvenanceChainTerminusEnum(EnumDefinitionImpl):

    raw_source_download = PermissibleValue(text="raw_source_download")
    remote_asset_scan = PermissibleValue(
        text="remote_asset_scan",
        description="""The chain bottoms out at a remote asset read in place, with nothing downloaded. The streaming case, which EnVar's enum does not have.""")
    pre_existing_curated_dataset = PermissibleValue(text="pre_existing_curated_dataset")
    externally_imported_dataset = PermissibleValue(
        text="externally_imported_dataset",
        description="""A dataset contributed from outside amadeus, whose upstream derivation amadeus did not perform and cannot vouch for.""")
    synthetic_data = PermissibleValue(text="synthetic_data")

    _defn = EnumDefinition(
        name="ProvenanceChainTerminusEnum",
    )

# Slots
class slots:
    pass

slots.data_sources = Slot(uri=AMADEUS.data_sources, name="data_sources", curie=AMADEUS.curie('data_sources'),
                   model_uri=AMADEUS.data_sources, domain=None, range=Optional[Union[dict[Union[str, DataSourceId], Union[dict, DataSource]], list[Union[dict, DataSource]]]])

slots.products = Slot(uri=AMADEUS.products, name="products", curie=AMADEUS.curie('products'),
                   model_uri=AMADEUS.products, domain=None, range=Optional[Union[dict[Union[str, ProductId], Union[dict, Product]], list[Union[dict, Product]]]])

slots.grid_definitions = Slot(uri=AMADEUS.grid_definitions, name="grid_definitions", curie=AMADEUS.curie('grid_definitions'),
                   model_uri=AMADEUS.grid_definitions, domain=None, range=Optional[Union[dict[Union[str, GridDefinitionId], Union[dict, GridDefinition]], list[Union[dict, GridDefinition]]]])

slots.canonical_variables = Slot(uri=AMADEUS.canonical_variables, name="canonical_variables", curie=AMADEUS.curie('canonical_variables'),
                   model_uri=AMADEUS.canonical_variables, domain=None, range=Optional[Union[dict[Union[str, CanonicalVariableId], Union[dict, CanonicalVariable]], list[Union[dict, CanonicalVariable]]]])

slots.product_variables = Slot(uri=AMADEUS.product_variables, name="product_variables", curie=AMADEUS.curie('product_variables'),
                   model_uri=AMADEUS.product_variables, domain=None, range=Optional[Union[dict[Union[str, ProductVariableId], Union[dict, ProductVariable]], list[Union[dict, ProductVariable]]]])

slots.assets = Slot(uri=AMADEUS.assets, name="assets", curie=AMADEUS.curie('assets'),
                   model_uri=AMADEUS.assets, domain=None, range=Optional[Union[dict[Union[str, AssetId], Union[dict, Asset]], list[Union[dict, Asset]]]])

slots.station_observations = Slot(uri=AMADEUS.station_observations, name="station_observations", curie=AMADEUS.curie('station_observations'),
                   model_uri=AMADEUS.station_observations, domain=None, range=Optional[Union[dict[Union[str, StationObservationId], Union[dict, StationObservation]], list[Union[dict, StationObservation]]]])

slots.grid_cell_values = Slot(uri=AMADEUS.grid_cell_values, name="grid_cell_values", curie=AMADEUS.curie('grid_cell_values'),
                   model_uri=AMADEUS.grid_cell_values, domain=None, range=Optional[Union[dict[Union[str, GridCellValueId], Union[dict, GridCellValue]], list[Union[dict, GridCellValue]]]])

slots.area_values = Slot(uri=AMADEUS.area_values, name="area_values", curie=AMADEUS.curie('area_values'),
                   model_uri=AMADEUS.area_values, domain=None, range=Optional[Union[dict[Union[str, AreaValueId], Union[dict, AreaValue]], list[Union[dict, AreaValue]]]])

slots.hex_cell_values = Slot(uri=AMADEUS.hex_cell_values, name="hex_cell_values", curie=AMADEUS.curie('hex_cell_values'),
                   model_uri=AMADEUS.hex_cell_values, domain=None, range=Optional[Union[dict[Union[str, HexCellValueId], Union[dict, HexCellValue]], list[Union[dict, HexCellValue]]]])

slots.vector_features = Slot(uri=AMADEUS.vector_features, name="vector_features", curie=AMADEUS.curie('vector_features'),
                   model_uri=AMADEUS.vector_features, domain=None, range=Optional[Union[dict[Union[str, VectorFeatureId], Union[dict, VectorFeature]], list[Union[dict, VectorFeature]]]])

slots.location_sets = Slot(uri=AMADEUS.location_sets, name="location_sets", curie=AMADEUS.curie('location_sets'),
                   model_uri=AMADEUS.location_sets, domain=None, range=Optional[Union[dict[Union[str, LocationSetId], Union[dict, LocationSet]], list[Union[dict, LocationSet]]]])

slots.locations = Slot(uri=AMADEUS.locations, name="locations", curie=AMADEUS.curie('locations'),
                   model_uri=AMADEUS.locations, domain=None, range=Optional[Union[dict[Union[str, LocationId], Union[dict, Location]], list[Union[dict, Location]]]])

slots.extraction_requests = Slot(uri=AMADEUS.extraction_requests, name="extraction_requests", curie=AMADEUS.curie('extraction_requests'),
                   model_uri=AMADEUS.extraction_requests, domain=None, range=Optional[Union[dict[Union[str, ExtractionRequestId], Union[dict, ExtractionRequest]], list[Union[dict, ExtractionRequest]]]])

slots.ambient_values_at_location = Slot(uri=AMADEUS.ambient_values_at_location, name="ambient_values_at_location", curie=AMADEUS.curie('ambient_values_at_location'),
                   model_uri=AMADEUS.ambient_values_at_location, domain=None, range=Optional[Union[dict[Union[str, AmbientValueAtLocationId], Union[dict, AmbientValueAtLocation]], list[Union[dict, AmbientValueAtLocation]]]])

slots.tool_runs = Slot(uri=AMADEUS.tool_runs, name="tool_runs", curie=AMADEUS.curie('tool_runs'),
                   model_uri=AMADEUS.tool_runs, domain=None, range=Optional[Union[dict[Union[str, ToolRunId], Union[dict, ToolRun]], list[Union[dict, ToolRun]]]])

slots.provenance_chains = Slot(uri=AMADEUS.provenance_chains, name="provenance_chains", curie=AMADEUS.curie('provenance_chains'),
                   model_uri=AMADEUS.provenance_chains, domain=None, range=Optional[Union[dict[Union[str, ProvenanceChainId], Union[dict, ProvenanceChain]], list[Union[dict, ProvenanceChain]]]])

slots.id = Slot(uri=AMADEUS.id, name="id", curie=AMADEUS.curie('id'),
                   model_uri=AMADEUS.id, domain=None, range=URIRef)

slots.name = Slot(uri=AMADEUS.name, name="name", curie=AMADEUS.curie('name'),
                   model_uri=AMADEUS.name, domain=None, range=Optional[str])

slots.label = Slot(uri=AMADEUS.label, name="label", curie=AMADEUS.curie('label'),
                   model_uri=AMADEUS.label, domain=None, range=Optional[str])

slots.description = Slot(uri=DCTERMS.description, name="description", curie=DCTERMS.curie('description'),
                   model_uri=AMADEUS.description, domain=None, range=Optional[str])

slots.schema_version = Slot(uri=AMADEUS.schema_version, name="schema_version", curie=AMADEUS.curie('schema_version'),
                   model_uri=AMADEUS.schema_version, domain=None, range=str)

slots.crs = Slot(uri=AMADEUS.crs, name="crs", curie=AMADEUS.curie('crs'),
                   model_uri=AMADEUS.crs, domain=None, range=Optional[str],
                   pattern=re.compile(r'^[A-Za-z]+:[0-9]+$'))

slots.srid = Slot(uri=AMADEUS.srid, name="srid", curie=AMADEUS.curie('srid'),
                   model_uri=AMADEUS.srid, domain=None, range=Optional[int])

slots.bbox_wkt = Slot(uri=AMADEUS.bbox_wkt, name="bbox_wkt", curie=AMADEUS.curie('bbox_wkt'),
                   model_uri=AMADEUS.bbox_wkt, domain=None, range=Optional[Union[str, WktLiteral]])

slots.valid_time_start = Slot(uri=AMADEUS.valid_time_start, name="valid_time_start", curie=AMADEUS.curie('valid_time_start'),
                   model_uri=AMADEUS.valid_time_start, domain=None, range=Optional[Union[str, XSDDateTime]])

slots.valid_time_end = Slot(uri=AMADEUS.valid_time_end, name="valid_time_end", curie=AMADEUS.curie('valid_time_end'),
                   model_uri=AMADEUS.valid_time_end, domain=None, range=Optional[Union[str, XSDDateTime]])

slots.retrieval_time_utc = Slot(uri=AMADEUS.retrieval_time_utc, name="retrieval_time_utc", curie=AMADEUS.curie('retrieval_time_utc'),
                   model_uri=AMADEUS.retrieval_time_utc, domain=None, range=Optional[Union[str, XSDDateTime]])

slots.sha256 = Slot(uri=AMADEUS.sha256, name="sha256", curie=AMADEUS.curie('sha256'),
                   model_uri=AMADEUS.sha256, domain=None, range=Optional[Union[str, Sha256]])

slots.missing_reason = Slot(uri=AMADEUS.missing_reason, name="missing_reason", curie=AMADEUS.curie('missing_reason'),
                   model_uri=AMADEUS.missing_reason, domain=None, range=Optional[Union[str, "MissingReasonEnum"]])

slots.materialization_mode = Slot(uri=AMADEUS.materialization_mode, name="materialization_mode", curie=AMADEUS.curie('materialization_mode'),
                   model_uri=AMADEUS.materialization_mode, domain=None, range=Optional[Union[str, "MaterializationModeEnum"]])

slots.producer_institution = Slot(uri=AMADEUS.producer_institution, name="producer_institution", curie=AMADEUS.curie('producer_institution'),
                   model_uri=AMADEUS.producer_institution, domain=None, range=Optional[str])

slots.homepage = Slot(uri=AMADEUS.homepage, name="homepage", curie=AMADEUS.curie('homepage'),
                   model_uri=AMADEUS.homepage, domain=None, range=Optional[Union[str, URI]])

slots.access_protocol = Slot(uri=AMADEUS.access_protocol, name="access_protocol", curie=AMADEUS.curie('access_protocol'),
                   model_uri=AMADEUS.access_protocol, domain=None, range=Optional[Union[str, "AccessProtocolEnum"]])

slots.requires_authentication = Slot(uri=AMADEUS.requires_authentication, name="requires_authentication", curie=AMADEUS.curie('requires_authentication'),
                   model_uri=AMADEUS.requires_authentication, domain=None, range=Optional[Union[bool, Bool]])

slots.auth_mechanism = Slot(uri=AMADEUS.auth_mechanism, name="auth_mechanism", curie=AMADEUS.curie('auth_mechanism'),
                   model_uri=AMADEUS.auth_mechanism, domain=None, range=Optional[str])

slots.rate_limit_requests_per_second = Slot(uri=AMADEUS.rate_limit_requests_per_second, name="rate_limit_requests_per_second", curie=AMADEUS.curie('rate_limit_requests_per_second'),
                   model_uri=AMADEUS.rate_limit_requests_per_second, domain=None, range=Optional[float])

slots.license_spdx = Slot(uri=AMADEUS.license_spdx, name="license_spdx", curie=AMADEUS.curie('license_spdx'),
                   model_uri=AMADEUS.license_spdx, domain=None, range=Optional[str])

slots.citation_apa = Slot(uri=AMADEUS.citation_apa, name="citation_apa", curie=AMADEUS.curie('citation_apa'),
                   model_uri=AMADEUS.citation_apa, domain=None, range=Optional[str])

slots.doi = Slot(uri=AMADEUS.doi, name="doi", curie=AMADEUS.curie('doi'),
                   model_uri=AMADEUS.doi, domain=None, range=Optional[str],
                   pattern=re.compile(r'^10\.[0-9]{4,9}/.+$'))

slots.amadeus_function_suffix = Slot(uri=AMADEUS.amadeus_function_suffix, name="amadeus_function_suffix", curie=AMADEUS.curie('amadeus_function_suffix'),
                   model_uri=AMADEUS.amadeus_function_suffix, domain=None, range=Optional[str])

slots.data_source = Slot(uri=AMADEUS.data_source, name="data_source", curie=AMADEUS.curie('data_source'),
                   model_uri=AMADEUS.data_source, domain=None, range=Optional[Union[str, DataSourceId]])

slots.product_version = Slot(uri=AMADEUS.product_version, name="product_version", curie=AMADEUS.curie('product_version'),
                   model_uri=AMADEUS.product_version, domain=None, range=Optional[str])

slots.data_genre = Slot(uri=AMADEUS.data_genre, name="data_genre", curie=AMADEUS.curie('data_genre'),
                   model_uri=AMADEUS.data_genre, domain=None, range=Optional[Union[Union[str, "DataGenreEnum"], list[Union[str, "DataGenreEnum"]]]])

slots.native_format = Slot(uri=AMADEUS.native_format, name="native_format", curie=AMADEUS.curie('native_format'),
                   model_uri=AMADEUS.native_format, domain=None, range=Optional[Union[str, "NativeFormatEnum"]])

slots.spatial_support_type = Slot(uri=AMADEUS.spatial_support_type, name="spatial_support_type", curie=AMADEUS.curie('spatial_support_type'),
                   model_uri=AMADEUS.spatial_support_type, domain=None, range=Optional[Union[str, "SpatialSupportTypeEnum"]])

slots.grid_definition = Slot(uri=AMADEUS.grid_definition, name="grid_definition", curie=AMADEUS.curie('grid_definition'),
                   model_uri=AMADEUS.grid_definition, domain=None, range=Optional[Union[str, GridDefinitionId]])

slots.spatial_extent_bbox_wkt = Slot(uri=AMADEUS.spatial_extent_bbox_wkt, name="spatial_extent_bbox_wkt", curie=AMADEUS.curie('spatial_extent_bbox_wkt'),
                   model_uri=AMADEUS.spatial_extent_bbox_wkt, domain=None, range=Optional[Union[str, WktLiteral]])

slots.spatial_extent_descriptor = Slot(uri=AMADEUS.spatial_extent_descriptor, name="spatial_extent_descriptor", curie=AMADEUS.curie('spatial_extent_descriptor'),
                   model_uri=AMADEUS.spatial_extent_descriptor, domain=None, range=Optional[str])

slots.native_spatial_resolution_m = Slot(uri=AMADEUS.native_spatial_resolution_m, name="native_spatial_resolution_m", curie=AMADEUS.curie('native_spatial_resolution_m'),
                   model_uri=AMADEUS.native_spatial_resolution_m, domain=None, range=Optional[float])

slots.native_spatial_resolution_descriptor = Slot(uri=AMADEUS.native_spatial_resolution_descriptor, name="native_spatial_resolution_descriptor", curie=AMADEUS.curie('native_spatial_resolution_descriptor'),
                   model_uri=AMADEUS.native_spatial_resolution_descriptor, domain=None, range=Optional[str])

slots.temporal_resolution = Slot(uri=AMADEUS.temporal_resolution, name="temporal_resolution", curie=AMADEUS.curie('temporal_resolution'),
                   model_uri=AMADEUS.temporal_resolution, domain=None, range=Optional[Union[str, "TemporalResolutionEnum"]])

slots.temporal_resolution_iso = Slot(uri=AMADEUS.temporal_resolution_iso, name="temporal_resolution_iso", curie=AMADEUS.curie('temporal_resolution_iso'),
                   model_uri=AMADEUS.temporal_resolution_iso, domain=None, range=Optional[Union[str, Iso8601Duration]])

slots.temporal_alignment = Slot(uri=AMADEUS.temporal_alignment, name="temporal_alignment", curie=AMADEUS.curie('temporal_alignment'),
                   model_uri=AMADEUS.temporal_alignment, domain=None, range=Optional[Union[str, "TemporalAlignmentEnum"]])

slots.day_boundary_convention = Slot(uri=AMADEUS.day_boundary_convention, name="day_boundary_convention", curie=AMADEUS.curie('day_boundary_convention'),
                   model_uri=AMADEUS.day_boundary_convention, domain=None, range=Optional[Union[str, "DayBoundaryConventionEnum"]])

slots.calendar = Slot(uri=AMADEUS.calendar, name="calendar", curie=AMADEUS.curie('calendar'),
                   model_uri=AMADEUS.calendar, domain=None, range=Optional[Union[str, "CalendarEnum"]])

slots.temporal_coverage_start = Slot(uri=AMADEUS.temporal_coverage_start, name="temporal_coverage_start", curie=AMADEUS.curie('temporal_coverage_start'),
                   model_uri=AMADEUS.temporal_coverage_start, domain=None, range=Optional[Union[str, XSDDate]])

slots.temporal_coverage_end = Slot(uri=AMADEUS.temporal_coverage_end, name="temporal_coverage_end", curie=AMADEUS.curie('temporal_coverage_end'),
                   model_uri=AMADEUS.temporal_coverage_end, domain=None, range=Optional[Union[str, XSDDate]])

slots.update_cadence_iso = Slot(uri=AMADEUS.update_cadence_iso, name="update_cadence_iso", curie=AMADEUS.curie('update_cadence_iso'),
                   model_uri=AMADEUS.update_cadence_iso, domain=None, range=Optional[Union[str, Iso8601Duration]])

slots.typical_latency_iso = Slot(uri=AMADEUS.typical_latency_iso, name="typical_latency_iso", curie=AMADEUS.curie('typical_latency_iso'),
                   model_uri=AMADEUS.typical_latency_iso, domain=None, range=Optional[Union[str, Iso8601Duration]])

slots.default_data_status = Slot(uri=AMADEUS.default_data_status, name="default_data_status", curie=AMADEUS.curie('default_data_status'),
                   model_uri=AMADEUS.default_data_status, domain=None, range=Optional[Union[str, "DataStatusEnum"]])

slots.homogenisation_status = Slot(uri=AMADEUS.homogenisation_status, name="homogenisation_status", curie=AMADEUS.curie('homogenisation_status'),
                   model_uri=AMADEUS.homogenisation_status, domain=None, range=Optional[Union[str, "HomogenisationStatusEnum"]])

slots.access_url = Slot(uri=AMADEUS.access_url, name="access_url", curie=AMADEUS.curie('access_url'),
                   model_uri=AMADEUS.access_url, domain=None, range=Optional[Union[str, URI]])

slots.amadeus_dataset_name = Slot(uri=AMADEUS.amadeus_dataset_name, name="amadeus_dataset_name", curie=AMADEUS.curie('amadeus_dataset_name'),
                   model_uri=AMADEUS.amadeus_dataset_name, domain=None, range=Optional[str])

slots.amadeus_process_covariate = Slot(uri=AMADEUS.amadeus_process_covariate, name="amadeus_process_covariate", curie=AMADEUS.curie('amadeus_process_covariate'),
                   model_uri=AMADEUS.amadeus_process_covariate, domain=None, range=Optional[str])

slots.amadeus_calculate_covariate = Slot(uri=AMADEUS.amadeus_calculate_covariate, name="amadeus_calculate_covariate", curie=AMADEUS.curie('amadeus_calculate_covariate'),
                   model_uri=AMADEUS.amadeus_calculate_covariate, domain=None, range=Optional[str])

slots.supports_server_side_subset = Slot(uri=AMADEUS.supports_server_side_subset, name="supports_server_side_subset", curie=AMADEUS.curie('supports_server_side_subset'),
                   model_uri=AMADEUS.supports_server_side_subset, domain=None, range=Optional[Union[bool, Bool]])

slots.stac_collection_id = Slot(uri=AMADEUS.stac_collection_id, name="stac_collection_id", curie=AMADEUS.curie('stac_collection_id'),
                   model_uri=AMADEUS.stac_collection_id, domain=None, range=Optional[str])

slots.grid_mapping_name = Slot(uri=AMADEUS.grid_mapping_name, name="grid_mapping_name", curie=AMADEUS.curie('grid_mapping_name'),
                   model_uri=AMADEUS.grid_mapping_name, domain=None, range=Optional[str])

slots.proj_string = Slot(uri=AMADEUS.proj_string, name="proj_string", curie=AMADEUS.curie('proj_string'),
                   model_uri=AMADEUS.proj_string, domain=None, range=Optional[str])

slots.resolution_x = Slot(uri=AMADEUS.resolution_x, name="resolution_x", curie=AMADEUS.curie('resolution_x'),
                   model_uri=AMADEUS.resolution_x, domain=None, range=Optional[float])

slots.resolution_y = Slot(uri=AMADEUS.resolution_y, name="resolution_y", curie=AMADEUS.curie('resolution_y'),
                   model_uri=AMADEUS.resolution_y, domain=None, range=Optional[float])

slots.resolution_unit = Slot(uri=AMADEUS.resolution_unit, name="resolution_unit", curie=AMADEUS.curie('resolution_unit'),
                   model_uri=AMADEUS.resolution_unit, domain=None, range=Optional[str])

slots.n_columns = Slot(uri=AMADEUS.n_columns, name="n_columns", curie=AMADEUS.curie('n_columns'),
                   model_uri=AMADEUS.n_columns, domain=None, range=Optional[int])

slots.n_rows = Slot(uri=AMADEUS.n_rows, name="n_rows", curie=AMADEUS.curie('n_rows'),
                   model_uri=AMADEUS.n_rows, domain=None, range=Optional[int])

slots.origin_x = Slot(uri=AMADEUS.origin_x, name="origin_x", curie=AMADEUS.curie('origin_x'),
                   model_uri=AMADEUS.origin_x, domain=None, range=Optional[float])

slots.origin_y = Slot(uri=AMADEUS.origin_y, name="origin_y", curie=AMADEUS.curie('origin_y'),
                   model_uri=AMADEUS.origin_y, domain=None, range=Optional[float])

slots.vertical_level_type = Slot(uri=AMADEUS.vertical_level_type, name="vertical_level_type", curie=AMADEUS.curie('vertical_level_type'),
                   model_uri=AMADEUS.vertical_level_type, domain=None, range=Optional[str])

slots.vertical_level_unit = Slot(uri=AMADEUS.vertical_level_unit, name="vertical_level_unit", curie=AMADEUS.curie('vertical_level_unit'),
                   model_uri=AMADEUS.vertical_level_unit, domain=None, range=Optional[str])

slots.vertical_levels = Slot(uri=AMADEUS.vertical_levels, name="vertical_levels", curie=AMADEUS.curie('vertical_levels'),
                   model_uri=AMADEUS.vertical_levels, domain=None, range=Optional[Union[float, list[float]]])

slots.standard_name = Slot(uri=AMADEUS.standard_name, name="standard_name", curie=AMADEUS.curie('standard_name'),
                   model_uri=AMADEUS.standard_name, domain=None, range=Optional[Union[str, URIorCURIE]])

slots.standard_name_authority = Slot(uri=AMADEUS.standard_name_authority, name="standard_name_authority", curie=AMADEUS.curie('standard_name_authority'),
                   model_uri=AMADEUS.standard_name_authority, domain=None, range=Optional[str])

slots.units_ucum = Slot(uri=AMADEUS.units_ucum, name="units_ucum", curie=AMADEUS.curie('units_ucum'),
                   model_uri=AMADEUS.units_ucum, domain=None, range=Optional[str])

slots.units_display = Slot(uri=AMADEUS.units_display, name="units_display", curie=AMADEUS.curie('units_display'),
                   model_uri=AMADEUS.units_display, domain=None, range=Optional[str])

slots.value_data_type = Slot(uri=AMADEUS.value_data_type, name="value_data_type", curie=AMADEUS.curie('value_data_type'),
                   model_uri=AMADEUS.value_data_type, domain=None, range=Optional[Union[str, "ValueDataTypeEnum"]])

slots.extensivity = Slot(uri=AMADEUS.extensivity, name="extensivity", curie=AMADEUS.curie('extensivity'),
                   model_uri=AMADEUS.extensivity, domain=None, range=Optional[Union[str, "VariableExtensivityEnum"]])

slots.default_aggregation_method = Slot(uri=AMADEUS.default_aggregation_method, name="default_aggregation_method", curie=AMADEUS.curie('default_aggregation_method'),
                   model_uri=AMADEUS.default_aggregation_method, domain=None, range=Optional[Union[str, "AggregationMethodEnum"]])

slots.plausible_min = Slot(uri=AMADEUS.plausible_min, name="plausible_min", curie=AMADEUS.curie('plausible_min'),
                   model_uri=AMADEUS.plausible_min, domain=None, range=Optional[float])

slots.plausible_max = Slot(uri=AMADEUS.plausible_max, name="plausible_max", curie=AMADEUS.curie('plausible_max'),
                   model_uri=AMADEUS.plausible_max, domain=None, range=Optional[float])

slots.concept_mappings = Slot(uri=AMADEUS.concept_mappings, name="concept_mappings", curie=AMADEUS.curie('concept_mappings'),
                   model_uri=AMADEUS.concept_mappings, domain=None, range=Optional[Union[Union[str, URIorCURIE], list[Union[str, URIorCURIE]]]])

slots.omop_concept_binding = Slot(uri=AMADEUS.omop_concept_binding, name="omop_concept_binding", curie=AMADEUS.curie('omop_concept_binding'),
                   model_uri=AMADEUS.omop_concept_binding, domain=None, range=Optional[Union[dict, OmopConceptBinding]])

slots.envar_variable_family = Slot(uri=AMADEUS.envar_variable_family, name="envar_variable_family", curie=AMADEUS.curie('envar_variable_family'),
                   model_uri=AMADEUS.envar_variable_family, domain=None, range=Optional[str])

slots.omop_concept_id = Slot(uri=AMADEUS.omop_concept_id, name="omop_concept_id", curie=AMADEUS.curie('omop_concept_id'),
                   model_uri=AMADEUS.omop_concept_id, domain=None, range=Optional[int])

slots.omop_concept_name = Slot(uri=AMADEUS.omop_concept_name, name="omop_concept_name", curie=AMADEUS.curie('omop_concept_name'),
                   model_uri=AMADEUS.omop_concept_name, domain=None, range=Optional[str])

slots.omop_vocabulary_id = Slot(uri=AMADEUS.omop_vocabulary_id, name="omop_vocabulary_id", curie=AMADEUS.curie('omop_vocabulary_id'),
                   model_uri=AMADEUS.omop_vocabulary_id, domain=None, range=Optional[str])

slots.omop_domain_id = Slot(uri=AMADEUS.omop_domain_id, name="omop_domain_id", curie=AMADEUS.curie('omop_domain_id'),
                   model_uri=AMADEUS.omop_domain_id, domain=None, range=Optional[str])

slots.omop_standard_concept = Slot(uri=AMADEUS.omop_standard_concept, name="omop_standard_concept", curie=AMADEUS.curie('omop_standard_concept'),
                   model_uri=AMADEUS.omop_standard_concept, domain=None, range=Optional[str])

slots.concept_status = Slot(uri=AMADEUS.concept_status, name="concept_status", curie=AMADEUS.curie('concept_status'),
                   model_uri=AMADEUS.concept_status, domain=None, range=Optional[Union[str, "ConceptStatusEnum"]])

slots.product = Slot(uri=AMADEUS.product, name="product", curie=AMADEUS.curie('product'),
                   model_uri=AMADEUS.product, domain=None, range=Optional[Union[str, ProductId]])

slots.canonical_variable = Slot(uri=AMADEUS.canonical_variable, name="canonical_variable", curie=AMADEUS.curie('canonical_variable'),
                   model_uri=AMADEUS.canonical_variable, domain=None, range=Optional[Union[str, CanonicalVariableId]])

slots.native_name = Slot(uri=AMADEUS.native_name, name="native_name", curie=AMADEUS.curie('native_name'),
                   model_uri=AMADEUS.native_name, domain=None, range=Optional[str])

slots.native_units_ucum = Slot(uri=AMADEUS.native_units_ucum, name="native_units_ucum", curie=AMADEUS.curie('native_units_ucum'),
                   model_uri=AMADEUS.native_units_ucum, domain=None, range=Optional[str])

slots.native_value_scale_factor = Slot(uri=AMADEUS.native_value_scale_factor, name="native_value_scale_factor", curie=AMADEUS.curie('native_value_scale_factor'),
                   model_uri=AMADEUS.native_value_scale_factor, domain=None, range=Optional[float])

slots.native_value_offset = Slot(uri=AMADEUS.native_value_offset, name="native_value_offset", curie=AMADEUS.curie('native_value_offset'),
                   model_uri=AMADEUS.native_value_offset, domain=None, range=Optional[float])

slots.unit_conversion_formula = Slot(uri=AMADEUS.unit_conversion_formula, name="unit_conversion_formula", curie=AMADEUS.curie('unit_conversion_formula'),
                   model_uri=AMADEUS.unit_conversion_formula, domain=None, range=Optional[str])

slots.cf_standard_name = Slot(uri=AMADEUS.cf_standard_name, name="cf_standard_name", curie=AMADEUS.curie('cf_standard_name'),
                   model_uri=AMADEUS.cf_standard_name, domain=None, range=Optional[str])

slots.cf_cell_methods = Slot(uri=AMADEUS.cf_cell_methods, name="cf_cell_methods", curie=AMADEUS.curie('cf_cell_methods'),
                   model_uri=AMADEUS.cf_cell_methods, domain=None, range=Optional[str])

slots.aggregation_method = Slot(uri=AMADEUS.aggregation_method, name="aggregation_method", curie=AMADEUS.curie('aggregation_method'),
                   model_uri=AMADEUS.aggregation_method, domain=None, range=Optional[Union[str, "AggregationMethodEnum"]])

slots.aggregation_window_iso = Slot(uri=AMADEUS.aggregation_window_iso, name="aggregation_window_iso", curie=AMADEUS.curie('aggregation_window_iso'),
                   model_uri=AMADEUS.aggregation_window_iso, domain=None, range=Optional[Union[str, Iso8601Duration]])

slots.missing_value_sentinel = Slot(uri=AMADEUS.missing_value_sentinel, name="missing_value_sentinel", curie=AMADEUS.curie('missing_value_sentinel'),
                   model_uri=AMADEUS.missing_value_sentinel, domain=None, range=Optional[str])

slots.quality_flag_vocabulary = Slot(uri=AMADEUS.quality_flag_vocabulary, name="quality_flag_vocabulary", curie=AMADEUS.curie('quality_flag_vocabulary'),
                   model_uri=AMADEUS.quality_flag_vocabulary, domain=None, range=Optional[str])

slots.layer_name_template = Slot(uri=AMADEUS.layer_name_template, name="layer_name_template", curie=AMADEUS.curie('layer_name_template'),
                   model_uri=AMADEUS.layer_name_template, domain=None, range=Optional[str])

slots.amadeus_variable_code = Slot(uri=AMADEUS.amadeus_variable_code, name="amadeus_variable_code", curie=AMADEUS.curie('amadeus_variable_code'),
                   model_uri=AMADEUS.amadeus_variable_code, domain=None, range=Optional[str])

slots.harmonization_note = Slot(uri=AMADEUS.harmonization_note, name="harmonization_note", curie=AMADEUS.curie('harmonization_note'),
                   model_uri=AMADEUS.harmonization_note, domain=None, range=Optional[str])

slots.metadata_gaps = Slot(uri=AMADEUS.metadata_gaps, name="metadata_gaps", curie=AMADEUS.curie('metadata_gaps'),
                   model_uri=AMADEUS.metadata_gaps, domain=None, range=Optional[Union[Union[str, "MissingReasonEnum"], list[Union[str, "MissingReasonEnum"]]]])

slots.asset_key = Slot(uri=AMADEUS.asset_key, name="asset_key", curie=AMADEUS.curie('asset_key'),
                   model_uri=AMADEUS.asset_key, domain=None, range=Optional[str])

slots.url = Slot(uri=AMADEUS.url, name="url", curie=AMADEUS.curie('url'),
                   model_uri=AMADEUS.url, domain=None, range=Optional[Union[str, URI]])

slots.local_path = Slot(uri=AMADEUS.local_path, name="local_path", curie=AMADEUS.curie('local_path'),
                   model_uri=AMADEUS.local_path, domain=None, range=Optional[str])

slots.media_type = Slot(uri=AMADEUS.media_type, name="media_type", curie=AMADEUS.curie('media_type'),
                   model_uri=AMADEUS.media_type, domain=None, range=Optional[str])

slots.size_bytes = Slot(uri=AMADEUS.size_bytes, name="size_bytes", curie=AMADEUS.curie('size_bytes'),
                   model_uri=AMADEUS.size_bytes, domain=None, range=Optional[int])

slots.source_last_modified = Slot(uri=AMADEUS.source_last_modified, name="source_last_modified", curie=AMADEUS.curie('source_last_modified'),
                   model_uri=AMADEUS.source_last_modified, domain=None, range=Optional[Union[str, XSDDateTime]])

slots.download_timestamp_utc = Slot(uri=AMADEUS.download_timestamp_utc, name="download_timestamp_utc", curie=AMADEUS.curie('download_timestamp_utc'),
                   model_uri=AMADEUS.download_timestamp_utc, domain=None, range=Optional[Union[str, XSDDateTime]])

slots.reference_time = Slot(uri=AMADEUS.reference_time, name="reference_time", curie=AMADEUS.curie('reference_time'),
                   model_uri=AMADEUS.reference_time, domain=None, range=Optional[Union[str, XSDDateTime]])

slots.variables_present = Slot(uri=AMADEUS.variables_present, name="variables_present", curie=AMADEUS.curie('variables_present'),
                   model_uri=AMADEUS.variables_present, domain=None, range=Optional[Union[Union[str, ProductVariableId], list[Union[str, ProductVariableId]]]])

slots.vertical_levels_present = Slot(uri=AMADEUS.vertical_levels_present, name="vertical_levels_present", curie=AMADEUS.curie('vertical_levels_present'),
                   model_uri=AMADEUS.vertical_levels_present, domain=None, range=Optional[Union[float, list[float]]])

slots.stac_item_id = Slot(uri=AMADEUS.stac_item_id, name="stac_item_id", curie=AMADEUS.curie('stac_item_id'),
                   model_uri=AMADEUS.stac_item_id, domain=None, range=Optional[str])

slots.cache_expires_at = Slot(uri=AMADEUS.cache_expires_at, name="cache_expires_at", curie=AMADEUS.curie('cache_expires_at'),
                   model_uri=AMADEUS.cache_expires_at, domain=None, range=Optional[Union[str, XSDDateTime]])

slots.value_state = Slot(uri=AMADEUS.value_state, name="value_state", curie=AMADEUS.curie('value_state'),
                   model_uri=AMADEUS.value_state, domain=None, range=Optional[Union[str, "ValueMaterializationEnum"]])

slots.produced_by_run = Slot(uri=AMADEUS.produced_by_run, name="produced_by_run", curie=AMADEUS.curie('produced_by_run'),
                   model_uri=AMADEUS.produced_by_run, domain=None, range=Optional[str])

slots.product_variable = Slot(uri=AMADEUS.product_variable, name="product_variable", curie=AMADEUS.curie('product_variable'),
                   model_uri=AMADEUS.product_variable, domain=None, range=Optional[Union[str, ProductVariableId]])

slots.asset = Slot(uri=AMADEUS.asset, name="asset", curie=AMADEUS.curie('asset'),
                   model_uri=AMADEUS.asset, domain=None, range=Optional[Union[str, AssetId]])

slots.processing_run = Slot(uri=AMADEUS.processing_run, name="processing_run", curie=AMADEUS.curie('processing_run'),
                   model_uri=AMADEUS.processing_run, domain=None, range=Optional[str])

slots.value = Slot(uri=AMADEUS.value, name="value", curie=AMADEUS.curie('value'),
                   model_uri=AMADEUS.value, domain=None, range=Optional[float])

slots.value_unit_ucum = Slot(uri=AMADEUS.value_unit_ucum, name="value_unit_ucum", curie=AMADEUS.curie('value_unit_ucum'),
                   model_uri=AMADEUS.value_unit_ucum, domain=None, range=Optional[str])

slots.native_value = Slot(uri=AMADEUS.native_value, name="native_value", curie=AMADEUS.curie('native_value'),
                   model_uri=AMADEUS.native_value, domain=None, range=Optional[float])

slots.native_value_unit_ucum = Slot(uri=AMADEUS.native_value_unit_ucum, name="native_value_unit_ucum", curie=AMADEUS.curie('native_value_unit_ucum'),
                   model_uri=AMADEUS.native_value_unit_ucum, domain=None, range=Optional[str])

slots.vertical_level = Slot(uri=AMADEUS.vertical_level, name="vertical_level", curie=AMADEUS.curie('vertical_level'),
                   model_uri=AMADEUS.vertical_level, domain=None, range=Optional[float])

slots.quality_flag = Slot(uri=AMADEUS.quality_flag, name="quality_flag", curie=AMADEUS.curie('quality_flag'),
                   model_uri=AMADEUS.quality_flag, domain=None, range=Optional[str])

slots.data_status = Slot(uri=AMADEUS.data_status, name="data_status", curie=AMADEUS.curie('data_status'),
                   model_uri=AMADEUS.data_status, domain=None, range=Optional[Union[str, "DataStatusEnum"]])

slots.source_system = Slot(uri=AMADEUS.source_system, name="source_system", curie=AMADEUS.curie('source_system'),
                   model_uri=AMADEUS.source_system, domain=None, range=Optional[str])

slots.source_version = Slot(uri=AMADEUS.source_version, name="source_version", curie=AMADEUS.curie('source_version'),
                   model_uri=AMADEUS.source_version, domain=None, range=Optional[str])

slots.null_semantics = Slot(uri=AMADEUS.null_semantics, name="null_semantics", curie=AMADEUS.curie('null_semantics'),
                   model_uri=AMADEUS.null_semantics, domain=None, range=Optional[Union[str, "NullSemanticsEnum"]])

slots.superseded_by = Slot(uri=AMADEUS.superseded_by, name="superseded_by", curie=AMADEUS.curie('superseded_by'),
                   model_uri=AMADEUS.superseded_by, domain=None, range=Optional[str])

slots.station_id = Slot(uri=AMADEUS.station_id, name="station_id", curie=AMADEUS.curie('station_id'),
                   model_uri=AMADEUS.station_id, domain=None, range=Optional[str])

slots.station_name = Slot(uri=AMADEUS.station_name, name="station_name", curie=AMADEUS.curie('station_name'),
                   model_uri=AMADEUS.station_name, domain=None, range=Optional[str])

slots.monitor_id = Slot(uri=AMADEUS.monitor_id, name="monitor_id", curie=AMADEUS.curie('monitor_id'),
                   model_uri=AMADEUS.monitor_id, domain=None, range=Optional[str])

slots.parameter_code = Slot(uri=AMADEUS.parameter_code, name="parameter_code", curie=AMADEUS.curie('parameter_code'),
                   model_uri=AMADEUS.parameter_code, domain=None, range=Optional[str])

slots.poc = Slot(uri=AMADEUS.poc, name="poc", curie=AMADEUS.curie('poc'),
                   model_uri=AMADEUS.poc, domain=None, range=Optional[int])

slots.sampling_duration_iso = Slot(uri=AMADEUS.sampling_duration_iso, name="sampling_duration_iso", curie=AMADEUS.curie('sampling_duration_iso'),
                   model_uri=AMADEUS.sampling_duration_iso, domain=None, range=Optional[Union[str, Iso8601Duration]])

slots.station_geom_wkt = Slot(uri=AMADEUS.station_geom_wkt, name="station_geom_wkt", curie=AMADEUS.curie('station_geom_wkt'),
                   model_uri=AMADEUS.station_geom_wkt, domain=None, range=Optional[Union[str, WktLiteral]])

slots.elevation_m = Slot(uri=AMADEUS.elevation_m, name="elevation_m", curie=AMADEUS.curie('elevation_m'),
                   model_uri=AMADEUS.elevation_m, domain=None, range=Optional[float])

slots.station_valid_from = Slot(uri=AMADEUS.station_valid_from, name="station_valid_from", curie=AMADEUS.curie('station_valid_from'),
                   model_uri=AMADEUS.station_valid_from, domain=None, range=Optional[Union[str, XSDDate]])

slots.station_valid_to = Slot(uri=AMADEUS.station_valid_to, name="station_valid_to", curie=AMADEUS.curie('station_valid_to'),
                   model_uri=AMADEUS.station_valid_to, domain=None, range=Optional[Union[str, XSDDate]])

slots.cell_x = Slot(uri=AMADEUS.cell_x, name="cell_x", curie=AMADEUS.curie('cell_x'),
                   model_uri=AMADEUS.cell_x, domain=None, range=Optional[int])

slots.cell_y = Slot(uri=AMADEUS.cell_y, name="cell_y", curie=AMADEUS.curie('cell_y'),
                   model_uri=AMADEUS.cell_y, domain=None, range=Optional[int])

slots.cell_centroid_wkt = Slot(uri=AMADEUS.cell_centroid_wkt, name="cell_centroid_wkt", curie=AMADEUS.curie('cell_centroid_wkt'),
                   model_uri=AMADEUS.cell_centroid_wkt, domain=None, range=Optional[Union[str, WktLiteral]])

slots.cell_polygon_wkt = Slot(uri=AMADEUS.cell_polygon_wkt, name="cell_polygon_wkt", curie=AMADEUS.curie('cell_polygon_wkt'),
                   model_uri=AMADEUS.cell_polygon_wkt, domain=None, range=Optional[Union[str, WktLiteral]])

slots.area_id = Slot(uri=AMADEUS.area_id, name="area_id", curie=AMADEUS.curie('area_id'),
                   model_uri=AMADEUS.area_id, domain=None, range=Optional[str])

slots.area_type = Slot(uri=AMADEUS.area_type, name="area_type", curie=AMADEUS.curie('area_type'),
                   model_uri=AMADEUS.area_type, domain=None, range=Optional[Union[str, "AreaTypeEnum"]])

slots.area_role = Slot(uri=AMADEUS.area_role, name="area_role", curie=AMADEUS.curie('area_role'),
                   model_uri=AMADEUS.area_role, domain=None, range=Optional[Union[str, "AreaRoleEnum"]])

slots.area_code = Slot(uri=AMADEUS.area_code, name="area_code", curie=AMADEUS.curie('area_code'),
                   model_uri=AMADEUS.area_code, domain=None, range=Optional[str])

slots.area_name = Slot(uri=AMADEUS.area_name, name="area_name", curie=AMADEUS.curie('area_name'),
                   model_uri=AMADEUS.area_name, domain=None, range=Optional[str])

slots.area_geom_wkt = Slot(uri=AMADEUS.area_geom_wkt, name="area_geom_wkt", curie=AMADEUS.curie('area_geom_wkt'),
                   model_uri=AMADEUS.area_geom_wkt, domain=None, range=Optional[Union[str, WktLiteral]])

slots.area_km2 = Slot(uri=AMADEUS.area_km2, name="area_km2", curie=AMADEUS.curie('area_km2'),
                   model_uri=AMADEUS.area_km2, domain=None, range=Optional[float])

slots.h3_cell = Slot(uri=AMADEUS.h3_cell, name="h3_cell", curie=AMADEUS.curie('h3_cell'),
                   model_uri=AMADEUS.h3_cell, domain=None, range=Optional[Union[str, H3CellIndex]])

slots.h3_resolution = Slot(uri=AMADEUS.h3_resolution, name="h3_resolution", curie=AMADEUS.curie('h3_resolution'),
                   model_uri=AMADEUS.h3_resolution, domain=None, range=Optional[int])

slots.hex_centroid_wkt = Slot(uri=AMADEUS.hex_centroid_wkt, name="hex_centroid_wkt", curie=AMADEUS.curie('hex_centroid_wkt'),
                   model_uri=AMADEUS.hex_centroid_wkt, domain=None, range=Optional[Union[str, WktLiteral]])

slots.source_support_type = Slot(uri=AMADEUS.source_support_type, name="source_support_type", curie=AMADEUS.curie('source_support_type'),
                   model_uri=AMADEUS.source_support_type, domain=None, range=Optional[Union[str, "SpatialSupportTypeEnum"]])

slots.hexification_method = Slot(uri=AMADEUS.hexification_method, name="hexification_method", curie=AMADEUS.curie('hexification_method'),
                   model_uri=AMADEUS.hexification_method, domain=None, range=Optional[Union[str, "AggregationMethodEnum"]])

slots.coverage_fraction = Slot(uri=AMADEUS.coverage_fraction, name="coverage_fraction", curie=AMADEUS.curie('coverage_fraction'),
                   model_uri=AMADEUS.coverage_fraction, domain=None, range=Optional[float])

slots.contributing_cell_count = Slot(uri=AMADEUS.contributing_cell_count, name="contributing_cell_count", curie=AMADEUS.curie('contributing_cell_count'),
                   model_uri=AMADEUS.contributing_cell_count, domain=None, range=Optional[int])

slots.feature_id = Slot(uri=AMADEUS.feature_id, name="feature_id", curie=AMADEUS.curie('feature_id'),
                   model_uri=AMADEUS.feature_id, domain=None, range=Optional[str])

slots.feature_type = Slot(uri=AMADEUS.feature_type, name="feature_type", curie=AMADEUS.curie('feature_type'),
                   model_uri=AMADEUS.feature_type, domain=None, range=Optional[str])

slots.geometry_type = Slot(uri=AMADEUS.geometry_type, name="geometry_type", curie=AMADEUS.curie('geometry_type'),
                   model_uri=AMADEUS.geometry_type, domain=None, range=Optional[Union[str, "GeometryTypeEnum"]])

slots.feature_geom_wkt = Slot(uri=AMADEUS.feature_geom_wkt, name="feature_geom_wkt", curie=AMADEUS.curie('feature_geom_wkt'),
                   model_uri=AMADEUS.feature_geom_wkt, domain=None, range=Optional[Union[str, WktLiteral]])

slots.feature_attributes = Slot(uri=AMADEUS.feature_attributes, name="feature_attributes", curie=AMADEUS.curie('feature_attributes'),
                   model_uri=AMADEUS.feature_attributes, domain=None, range=Optional[str])

slots.length_m = Slot(uri=AMADEUS.length_m, name="length_m", curie=AMADEUS.curie('length_m'),
                   model_uri=AMADEUS.length_m, domain=None, range=Optional[float])

slots.grid_definition_ref = Slot(uri=AMADEUS.grid_definition_ref, name="grid_definition_ref", curie=AMADEUS.curie('grid_definition_ref'),
                   model_uri=AMADEUS.grid_definition_ref, domain=None, range=Optional[Union[str, GridDefinitionId]])

slots.locs_id_field = Slot(uri=AMADEUS.locs_id_field, name="locs_id_field", curie=AMADEUS.curie('locs_id_field'),
                   model_uri=AMADEUS.locs_id_field, domain=None, range=Optional[str])

slots.location_count = Slot(uri=AMADEUS.location_count, name="location_count", curie=AMADEUS.curie('location_count'),
                   model_uri=AMADEUS.location_count, domain=None, range=Optional[int])

slots.phi_status = Slot(uri=AMADEUS.phi_status, name="phi_status", curie=AMADEUS.curie('phi_status'),
                   model_uri=AMADEUS.phi_status, domain=None, range=Optional[Union[str, "PhiStatusEnum"]])

slots.provided_by = Slot(uri=AMADEUS.provided_by, name="provided_by", curie=AMADEUS.curie('provided_by'),
                   model_uri=AMADEUS.provided_by, domain=None, range=Optional[str])

slots.created_at = Slot(uri=AMADEUS.created_at, name="created_at", curie=AMADEUS.curie('created_at'),
                   model_uri=AMADEUS.created_at, domain=None, range=Optional[Union[str, XSDDateTime]])

slots.location_set = Slot(uri=AMADEUS.location_set, name="location_set", curie=AMADEUS.curie('location_set'),
                   model_uri=AMADEUS.location_set, domain=None, range=Optional[Union[str, LocationSetId]])

slots.location_key = Slot(uri=AMADEUS.location_key, name="location_key", curie=AMADEUS.curie('location_key'),
                   model_uri=AMADEUS.location_key, domain=None, range=Optional[str])

slots.location_geom_wkt = Slot(uri=AMADEUS.location_geom_wkt, name="location_geom_wkt", curie=AMADEUS.curie('location_geom_wkt'),
                   model_uri=AMADEUS.location_geom_wkt, domain=None, range=Optional[Union[str, WktLiteral]])

slots.buffer_radius_m = Slot(uri=AMADEUS.buffer_radius_m, name="buffer_radius_m", curie=AMADEUS.curie('buffer_radius_m'),
                   model_uri=AMADEUS.buffer_radius_m, domain=None, range=Optional[float])

slots.valid_from = Slot(uri=AMADEUS.valid_from, name="valid_from", curie=AMADEUS.curie('valid_from'),
                   model_uri=AMADEUS.valid_from, domain=None, range=Optional[Union[str, XSDDate]])

slots.valid_to = Slot(uri=AMADEUS.valid_to, name="valid_to", curie=AMADEUS.curie('valid_to'),
                   model_uri=AMADEUS.valid_to, domain=None, range=Optional[Union[str, XSDDate]])

slots.target_geography_type = Slot(uri=AMADEUS.target_geography_type, name="target_geography_type", curie=AMADEUS.curie('target_geography_type'),
                   model_uri=AMADEUS.target_geography_type, domain=None, range=Optional[Union[str, "TargetGeographyTypeEnum"]])

slots.requested_canonical_variables = Slot(uri=AMADEUS.requested_canonical_variables, name="requested_canonical_variables", curie=AMADEUS.curie('requested_canonical_variables'),
                   model_uri=AMADEUS.requested_canonical_variables, domain=None, range=Optional[Union[Union[str, CanonicalVariableId], list[Union[str, CanonicalVariableId]]]])

slots.requested_product_variables = Slot(uri=AMADEUS.requested_product_variables, name="requested_product_variables", curie=AMADEUS.curie('requested_product_variables'),
                   model_uri=AMADEUS.requested_product_variables, domain=None, range=Optional[Union[Union[str, ProductVariableId], list[Union[str, ProductVariableId]]]])

slots.time_window_start = Slot(uri=AMADEUS.time_window_start, name="time_window_start", curie=AMADEUS.curie('time_window_start'),
                   model_uri=AMADEUS.time_window_start, domain=None, range=Optional[Union[str, XSDDateTime]])

slots.time_window_end = Slot(uri=AMADEUS.time_window_end, name="time_window_end", curie=AMADEUS.curie('time_window_end'),
                   model_uri=AMADEUS.time_window_end, domain=None, range=Optional[Union[str, XSDDateTime]])

slots.temporal_grouping = Slot(uri=AMADEUS.temporal_grouping, name="temporal_grouping", curie=AMADEUS.curie('temporal_grouping'),
                   model_uri=AMADEUS.temporal_grouping, domain=None, range=Optional[Union[str, "TemporalGroupingEnum"]])

slots.extraction_method = Slot(uri=AMADEUS.extraction_method, name="extraction_method", curie=AMADEUS.curie('extraction_method'),
                   model_uri=AMADEUS.extraction_method, domain=None, range=Optional[Union[str, "ExtractionMethodEnum"]])

slots.weighting_product_variable = Slot(uri=AMADEUS.weighting_product_variable, name="weighting_product_variable", curie=AMADEUS.curie('weighting_product_variable'),
                   model_uri=AMADEUS.weighting_product_variable, domain=None, range=Optional[Union[str, ProductVariableId]])

slots.lag_days = Slot(uri=AMADEUS.lag_days, name="lag_days", curie=AMADEUS.curie('lag_days'),
                   model_uri=AMADEUS.lag_days, domain=None, range=Optional[Union[int, list[int]]])

slots.output_orientation = Slot(uri=AMADEUS.output_orientation, name="output_orientation", curie=AMADEUS.curie('output_orientation'),
                   model_uri=AMADEUS.output_orientation, domain=None, range=Optional[Union[str, "TableOrientationEnum"]])

slots.source_priority_policy = Slot(uri=AMADEUS.source_priority_policy, name="source_priority_policy", curie=AMADEUS.curie('source_priority_policy'),
                   model_uri=AMADEUS.source_priority_policy, domain=None, range=Optional[str])

slots.status_mixing_policy = Slot(uri=AMADEUS.status_mixing_policy, name="status_mixing_policy", curie=AMADEUS.curie('status_mixing_policy'),
                   model_uri=AMADEUS.status_mixing_policy, domain=None, range=Optional[Union[str, "StatusMixingPolicyEnum"]])

slots.strict_extensivity_check = Slot(uri=AMADEUS.strict_extensivity_check, name="strict_extensivity_check", curie=AMADEUS.curie('strict_extensivity_check'),
                   model_uri=AMADEUS.strict_extensivity_check, domain=None, range=Optional[Union[str, "StrictnessEnum"]])

slots.requested_by = Slot(uri=AMADEUS.requested_by, name="requested_by", curie=AMADEUS.curie('requested_by'),
                   model_uri=AMADEUS.requested_by, domain=None, range=Optional[str])

slots.request_timestamp_utc = Slot(uri=AMADEUS.request_timestamp_utc, name="request_timestamp_utc", curie=AMADEUS.curie('request_timestamp_utc'),
                   model_uri=AMADEUS.request_timestamp_utc, domain=None, range=Optional[Union[str, XSDDateTime]])

slots.request_hash = Slot(uri=AMADEUS.request_hash, name="request_hash", curie=AMADEUS.curie('request_hash'),
                   model_uri=AMADEUS.request_hash, domain=None, range=Optional[Union[str, Sha256]])

slots.generated_sql = Slot(uri=AMADEUS.generated_sql, name="generated_sql", curie=AMADEUS.curie('generated_sql'),
                   model_uri=AMADEUS.generated_sql, domain=None, range=Optional[str])

slots.location = Slot(uri=AMADEUS.location, name="location", curie=AMADEUS.curie('location'),
                   model_uri=AMADEUS.location, domain=None, range=Optional[Union[str, LocationId]])

slots.extraction_request = Slot(uri=AMADEUS.extraction_request, name="extraction_request", curie=AMADEUS.curie('extraction_request'),
                   model_uri=AMADEUS.extraction_request, domain=None, range=Optional[Union[str, ExtractionRequestId]])

slots.contributing_value_count = Slot(uri=AMADEUS.contributing_value_count, name="contributing_value_count", curie=AMADEUS.curie('contributing_value_count'),
                   model_uri=AMADEUS.contributing_value_count, domain=None, range=Optional[int])

slots.distance_to_source_m = Slot(uri=AMADEUS.distance_to_source_m, name="distance_to_source_m", curie=AMADEUS.curie('distance_to_source_m'),
                   model_uri=AMADEUS.distance_to_source_m, domain=None, range=Optional[float])

slots.lag_days_applied = Slot(uri=AMADEUS.lag_days_applied, name="lag_days_applied", curie=AMADEUS.curie('lag_days_applied'),
                   model_uri=AMADEUS.lag_days_applied, domain=None, range=Optional[int])

slots.output_column_name = Slot(uri=AMADEUS.output_column_name, name="output_column_name", curie=AMADEUS.curie('output_column_name'),
                   model_uri=AMADEUS.output_column_name, domain=None, range=Optional[str])

slots.run_role = Slot(uri=AMADEUS.run_role, name="run_role", curie=AMADEUS.curie('run_role'),
                   model_uri=AMADEUS.run_role, domain=None, range=Optional[Union[str, "RunRoleEnum"]])

slots.tool_name = Slot(uri=AMADEUS.tool_name, name="tool_name", curie=AMADEUS.curie('tool_name'),
                   model_uri=AMADEUS.tool_name, domain=None, range=Optional[str])

slots.tool_version = Slot(uri=AMADEUS.tool_version, name="tool_version", curie=AMADEUS.curie('tool_version'),
                   model_uri=AMADEUS.tool_version, domain=None, range=Optional[str])

slots.function_name = Slot(uri=AMADEUS.function_name, name="function_name", curie=AMADEUS.curie('function_name'),
                   model_uri=AMADEUS.function_name, domain=None, range=Optional[str])

slots.run_arguments = Slot(uri=AMADEUS.run_arguments, name="run_arguments", curie=AMADEUS.curie('run_arguments'),
                   model_uri=AMADEUS.run_arguments, domain=None, range=Optional[str])

slots.container_image_repository = Slot(uri=AMADEUS.container_image_repository, name="container_image_repository", curie=AMADEUS.curie('container_image_repository'),
                   model_uri=AMADEUS.container_image_repository, domain=None, range=Optional[str])

slots.container_image_digest = Slot(uri=AMADEUS.container_image_digest, name="container_image_digest", curie=AMADEUS.curie('container_image_digest'),
                   model_uri=AMADEUS.container_image_digest, domain=None, range=Optional[str],
                   pattern=re.compile(r'^sha256:[0-9a-f]{64}$'))

slots.run_timestamp_utc = Slot(uri=AMADEUS.run_timestamp_utc, name="run_timestamp_utc", curie=AMADEUS.curie('run_timestamp_utc'),
                   model_uri=AMADEUS.run_timestamp_utc, domain=None, range=Optional[Union[str, XSDDateTime]])

slots.run_duration_seconds = Slot(uri=AMADEUS.run_duration_seconds, name="run_duration_seconds", curie=AMADEUS.curie('run_duration_seconds'),
                   model_uri=AMADEUS.run_duration_seconds, domain=None, range=Optional[float])

slots.run_environment = Slot(uri=AMADEUS.run_environment, name="run_environment", curie=AMADEUS.curie('run_environment'),
                   model_uri=AMADEUS.run_environment, domain=None, range=Optional[str])

slots.input_asset_ids = Slot(uri=AMADEUS.input_asset_ids, name="input_asset_ids", curie=AMADEUS.curie('input_asset_ids'),
                   model_uri=AMADEUS.input_asset_ids, domain=None, range=Optional[Union[str, list[str]]])

slots.input_file_sha256 = Slot(uri=AMADEUS.input_file_sha256, name="input_file_sha256", curie=AMADEUS.curie('input_file_sha256'),
                   model_uri=AMADEUS.input_file_sha256, domain=None, range=Optional[Union[str, Sha256]])

slots.input_row_count = Slot(uri=AMADEUS.input_row_count, name="input_row_count", curie=AMADEUS.curie('input_row_count'),
                   model_uri=AMADEUS.input_row_count, domain=None, range=Optional[int])

slots.output_file_sha256 = Slot(uri=AMADEUS.output_file_sha256, name="output_file_sha256", curie=AMADEUS.curie('output_file_sha256'),
                   model_uri=AMADEUS.output_file_sha256, domain=None, range=Optional[Union[str, Sha256]])

slots.output_row_count = Slot(uri=AMADEUS.output_row_count, name="output_row_count", curie=AMADEUS.curie('output_row_count'),
                   model_uri=AMADEUS.output_row_count, domain=None, range=Optional[int])

slots.upstream_runs = Slot(uri=AMADEUS.upstream_runs, name="upstream_runs", curie=AMADEUS.curie('upstream_runs'),
                   model_uri=AMADEUS.upstream_runs, domain=None, range=Optional[Union[str, list[str]]])

slots.status = Slot(uri=AMADEUS.status, name="status", curie=AMADEUS.curie('status'),
                   model_uri=AMADEUS.status, domain=None, range=Optional[Union[str, "RunStatusEnum"]])

slots.log_excerpt = Slot(uri=AMADEUS.log_excerpt, name="log_excerpt", curie=AMADEUS.curie('log_excerpt'),
                   model_uri=AMADEUS.log_excerpt, domain=None, range=Optional[str])

slots.bytes_transferred = Slot(uri=AMADEUS.bytes_transferred, name="bytes_transferred", curie=AMADEUS.curie('bytes_transferred'),
                   model_uri=AMADEUS.bytes_transferred, domain=None, range=Optional[int])

slots.request_count = Slot(uri=AMADEUS.request_count, name="request_count", curie=AMADEUS.curie('request_count'),
                   model_uri=AMADEUS.request_count, domain=None, range=Optional[int])

slots.chain_steps = Slot(uri=AMADEUS.chain_steps, name="chain_steps", curie=AMADEUS.curie('chain_steps'),
                   model_uri=AMADEUS.chain_steps, domain=None, range=Optional[Union[str, list[str]]])

slots.terminus_type = Slot(uri=AMADEUS.terminus_type, name="terminus_type", curie=AMADEUS.curie('terminus_type'),
                   model_uri=AMADEUS.terminus_type, domain=None, range=Optional[Union[str, "ProvenanceChainTerminusEnum"]])

slots.compatibility_assertions = Slot(uri=AMADEUS.compatibility_assertions, name="compatibility_assertions", curie=AMADEUS.curie('compatibility_assertions'),
                   model_uri=AMADEUS.compatibility_assertions, domain=None, range=Optional[Union[str, list[str]]])

slots.DataSource_name = Slot(uri=AMADEUS.name, name="DataSource_name", curie=AMADEUS.curie('name'),
                   model_uri=AMADEUS.DataSource_name, domain=DataSource, range=str)

slots.DataSource_amadeus_function_suffix = Slot(uri=AMADEUS.amadeus_function_suffix, name="DataSource_amadeus_function_suffix", curie=AMADEUS.curie('amadeus_function_suffix'),
                   model_uri=AMADEUS.DataSource_amadeus_function_suffix, domain=DataSource, range=Optional[str])

slots.Product_name = Slot(uri=AMADEUS.name, name="Product_name", curie=AMADEUS.curie('name'),
                   model_uri=AMADEUS.Product_name, domain=Product, range=str)

slots.Product_data_source = Slot(uri=AMADEUS.data_source, name="Product_data_source", curie=AMADEUS.curie('data_source'),
                   model_uri=AMADEUS.Product_data_source, domain=Product, range=Union[str, DataSourceId])

slots.Product_spatial_support_type = Slot(uri=AMADEUS.spatial_support_type, name="Product_spatial_support_type", curie=AMADEUS.curie('spatial_support_type'),
                   model_uri=AMADEUS.Product_spatial_support_type, domain=Product, range=Union[str, "SpatialSupportTypeEnum"])

slots.Product_temporal_resolution = Slot(uri=AMADEUS.temporal_resolution, name="Product_temporal_resolution", curie=AMADEUS.curie('temporal_resolution'),
                   model_uri=AMADEUS.Product_temporal_resolution, domain=Product, range=Union[str, "TemporalResolutionEnum"])

slots.Product_grid_definition = Slot(uri=AMADEUS.grid_definition, name="Product_grid_definition", curie=AMADEUS.curie('grid_definition'),
                   model_uri=AMADEUS.Product_grid_definition, domain=Product, range=Optional[Union[str, GridDefinitionId]])

slots.GridDefinition_crs = Slot(uri=AMADEUS.crs, name="GridDefinition_crs", curie=AMADEUS.curie('crs'),
                   model_uri=AMADEUS.GridDefinition_crs, domain=GridDefinition, range=str,
                   pattern=re.compile(r'^[A-Za-z]+:[0-9]+$'))

slots.GridDefinition_resolution_x = Slot(uri=AMADEUS.resolution_x, name="GridDefinition_resolution_x", curie=AMADEUS.curie('resolution_x'),
                   model_uri=AMADEUS.GridDefinition_resolution_x, domain=GridDefinition, range=float)

slots.GridDefinition_resolution_y = Slot(uri=AMADEUS.resolution_y, name="GridDefinition_resolution_y", curie=AMADEUS.curie('resolution_y'),
                   model_uri=AMADEUS.GridDefinition_resolution_y, domain=GridDefinition, range=float)

slots.GridDefinition_vertical_levels = Slot(uri=AMADEUS.vertical_levels, name="GridDefinition_vertical_levels", curie=AMADEUS.curie('vertical_levels'),
                   model_uri=AMADEUS.GridDefinition_vertical_levels, domain=GridDefinition, range=Optional[Union[float, list[float]]])

slots.CanonicalVariable_name = Slot(uri=AMADEUS.name, name="CanonicalVariable_name", curie=AMADEUS.curie('name'),
                   model_uri=AMADEUS.CanonicalVariable_name, domain=CanonicalVariable, range=str)

slots.CanonicalVariable_standard_name = Slot(uri=AMADEUS.standard_name, name="CanonicalVariable_standard_name", curie=AMADEUS.curie('standard_name'),
                   model_uri=AMADEUS.CanonicalVariable_standard_name, domain=CanonicalVariable, range=Union[str, URIorCURIE])

slots.CanonicalVariable_units_ucum = Slot(uri=AMADEUS.units_ucum, name="CanonicalVariable_units_ucum", curie=AMADEUS.curie('units_ucum'),
                   model_uri=AMADEUS.CanonicalVariable_units_ucum, domain=CanonicalVariable, range=str)

slots.CanonicalVariable_value_data_type = Slot(uri=AMADEUS.value_data_type, name="CanonicalVariable_value_data_type", curie=AMADEUS.curie('value_data_type'),
                   model_uri=AMADEUS.CanonicalVariable_value_data_type, domain=CanonicalVariable, range=Union[str, "ValueDataTypeEnum"])

slots.CanonicalVariable_extensivity = Slot(uri=AMADEUS.extensivity, name="CanonicalVariable_extensivity", curie=AMADEUS.curie('extensivity'),
                   model_uri=AMADEUS.CanonicalVariable_extensivity, domain=CanonicalVariable, range=Union[str, "VariableExtensivityEnum"])

slots.ProductVariable_product = Slot(uri=AMADEUS.product, name="ProductVariable_product", curie=AMADEUS.curie('product'),
                   model_uri=AMADEUS.ProductVariable_product, domain=ProductVariable, range=Union[str, ProductId])

slots.ProductVariable_canonical_variable = Slot(uri=AMADEUS.canonical_variable, name="ProductVariable_canonical_variable", curie=AMADEUS.curie('canonical_variable'),
                   model_uri=AMADEUS.ProductVariable_canonical_variable, domain=ProductVariable, range=Union[str, CanonicalVariableId])

slots.ProductVariable_native_name = Slot(uri=AMADEUS.native_name, name="ProductVariable_native_name", curie=AMADEUS.curie('native_name'),
                   model_uri=AMADEUS.ProductVariable_native_name, domain=ProductVariable, range=str)

slots.ProductVariable_layer_name_template = Slot(uri=AMADEUS.layer_name_template, name="ProductVariable_layer_name_template", curie=AMADEUS.curie('layer_name_template'),
                   model_uri=AMADEUS.ProductVariable_layer_name_template, domain=ProductVariable, range=Optional[str])

slots.ProductVariable_value_data_type = Slot(uri=AMADEUS.value_data_type, name="ProductVariable_value_data_type", curie=AMADEUS.curie('value_data_type'),
                   model_uri=AMADEUS.ProductVariable_value_data_type, domain=ProductVariable, range=Optional[Union[str, "ValueDataTypeEnum"]])

slots.ProductVariable_extensivity = Slot(uri=AMADEUS.extensivity, name="ProductVariable_extensivity", curie=AMADEUS.curie('extensivity'),
                   model_uri=AMADEUS.ProductVariable_extensivity, domain=ProductVariable, range=Optional[Union[str, "VariableExtensivityEnum"]])

slots.OmopConceptBinding_concept_status = Slot(uri=AMADEUS.concept_status, name="OmopConceptBinding_concept_status", curie=AMADEUS.curie('concept_status'),
                   model_uri=AMADEUS.OmopConceptBinding_concept_status, domain=OmopConceptBinding, range=Union[str, "ConceptStatusEnum"])

slots.Asset_product = Slot(uri=AMADEUS.product, name="Asset_product", curie=AMADEUS.curie('product'),
                   model_uri=AMADEUS.Asset_product, domain=Asset, range=Union[str, ProductId])

slots.Asset_materialization_mode = Slot(uri=AMADEUS.materialization_mode, name="Asset_materialization_mode", curie=AMADEUS.curie('materialization_mode'),
                   model_uri=AMADEUS.Asset_materialization_mode, domain=Asset, range=Union[str, "MaterializationModeEnum"])

slots.Asset_value_state = Slot(uri=AMADEUS.value_state, name="Asset_value_state", curie=AMADEUS.curie('value_state'),
                   model_uri=AMADEUS.Asset_value_state, domain=Asset, range=Union[str, "ValueMaterializationEnum"])

slots.Asset_url = Slot(uri=AMADEUS.url, name="Asset_url", curie=AMADEUS.curie('url'),
                   model_uri=AMADEUS.Asset_url, domain=Asset, range=Optional[Union[str, URI]])

slots.Asset_local_path = Slot(uri=AMADEUS.local_path, name="Asset_local_path", curie=AMADEUS.curie('local_path'),
                   model_uri=AMADEUS.Asset_local_path, domain=Asset, range=Optional[str])

slots.AmbientValue_product_variable = Slot(uri=AMADEUS.product_variable, name="AmbientValue_product_variable", curie=AMADEUS.curie('product_variable'),
                   model_uri=AMADEUS.AmbientValue_product_variable, domain=AmbientValue, range=Union[str, ProductVariableId])

slots.AmbientValue_canonical_variable = Slot(uri=AMADEUS.canonical_variable, name="AmbientValue_canonical_variable", curie=AMADEUS.curie('canonical_variable'),
                   model_uri=AMADEUS.AmbientValue_canonical_variable, domain=AmbientValue, range=Union[str, CanonicalVariableId])

slots.AmbientValue_value = Slot(uri=AMADEUS.value, name="AmbientValue_value", curie=AMADEUS.curie('value'),
                   model_uri=AMADEUS.AmbientValue_value, domain=AmbientValue, range=Optional[float])

slots.AmbientValue_valid_time_start = Slot(uri=AMADEUS.valid_time_start, name="AmbientValue_valid_time_start", curie=AMADEUS.curie('valid_time_start'),
                   model_uri=AMADEUS.AmbientValue_valid_time_start, domain=AmbientValue, range=Union[str, XSDDateTime])

slots.AmbientValue_data_status = Slot(uri=AMADEUS.data_status, name="AmbientValue_data_status", curie=AMADEUS.curie('data_status'),
                   model_uri=AMADEUS.AmbientValue_data_status, domain=AmbientValue, range=Union[str, "DataStatusEnum"])

slots.AmbientValue_source_system = Slot(uri=AMADEUS.source_system, name="AmbientValue_source_system", curie=AMADEUS.curie('source_system'),
                   model_uri=AMADEUS.AmbientValue_source_system, domain=AmbientValue, range=str)

slots.AmbientValue_null_semantics = Slot(uri=AMADEUS.null_semantics, name="AmbientValue_null_semantics", curie=AMADEUS.curie('null_semantics'),
                   model_uri=AMADEUS.AmbientValue_null_semantics, domain=AmbientValue, range=Union[str, "NullSemanticsEnum"])

slots.StationObservation_station_id = Slot(uri=AMADEUS.station_id, name="StationObservation_station_id", curie=AMADEUS.curie('station_id'),
                   model_uri=AMADEUS.StationObservation_station_id, domain=StationObservation, range=str)

slots.StationObservation_station_geom_wkt = Slot(uri=AMADEUS.station_geom_wkt, name="StationObservation_station_geom_wkt", curie=AMADEUS.curie('station_geom_wkt'),
                   model_uri=AMADEUS.StationObservation_station_geom_wkt, domain=StationObservation, range=Union[str, WktLiteral])

slots.StationObservation_poc = Slot(uri=AMADEUS.poc, name="StationObservation_poc", curie=AMADEUS.curie('poc'),
                   model_uri=AMADEUS.StationObservation_poc, domain=StationObservation, range=Optional[int])

slots.StationObservation_station_valid_from = Slot(uri=AMADEUS.station_valid_from, name="StationObservation_station_valid_from", curie=AMADEUS.curie('station_valid_from'),
                   model_uri=AMADEUS.StationObservation_station_valid_from, domain=StationObservation, range=Optional[Union[str, XSDDate]])

slots.GridCellValue_grid_definition = Slot(uri=AMADEUS.grid_definition, name="GridCellValue_grid_definition", curie=AMADEUS.curie('grid_definition'),
                   model_uri=AMADEUS.GridCellValue_grid_definition, domain=GridCellValue, range=Union[str, GridDefinitionId])

slots.GridCellValue_cell_x = Slot(uri=AMADEUS.cell_x, name="GridCellValue_cell_x", curie=AMADEUS.curie('cell_x'),
                   model_uri=AMADEUS.GridCellValue_cell_x, domain=GridCellValue, range=int)

slots.GridCellValue_cell_y = Slot(uri=AMADEUS.cell_y, name="GridCellValue_cell_y", curie=AMADEUS.curie('cell_y'),
                   model_uri=AMADEUS.GridCellValue_cell_y, domain=GridCellValue, range=int)

slots.GridCellValue_cell_centroid_wkt = Slot(uri=AMADEUS.cell_centroid_wkt, name="GridCellValue_cell_centroid_wkt", curie=AMADEUS.curie('cell_centroid_wkt'),
                   model_uri=AMADEUS.GridCellValue_cell_centroid_wkt, domain=GridCellValue, range=Union[str, WktLiteral])

slots.GridCellValue_cell_polygon_wkt = Slot(uri=AMADEUS.cell_polygon_wkt, name="GridCellValue_cell_polygon_wkt", curie=AMADEUS.curie('cell_polygon_wkt'),
                   model_uri=AMADEUS.GridCellValue_cell_polygon_wkt, domain=GridCellValue, range=Optional[Union[str, WktLiteral]])

slots.AreaValue_area_id = Slot(uri=AMADEUS.area_id, name="AreaValue_area_id", curie=AMADEUS.curie('area_id'),
                   model_uri=AMADEUS.AreaValue_area_id, domain=AreaValue, range=str)

slots.AreaValue_area_type = Slot(uri=AMADEUS.area_type, name="AreaValue_area_type", curie=AMADEUS.curie('area_type'),
                   model_uri=AMADEUS.AreaValue_area_type, domain=AreaValue, range=Union[str, "AreaTypeEnum"])

slots.AreaValue_area_role = Slot(uri=AMADEUS.area_role, name="AreaValue_area_role", curie=AMADEUS.curie('area_role'),
                   model_uri=AMADEUS.AreaValue_area_role, domain=AreaValue, range=Union[str, "AreaRoleEnum"])

slots.AreaValue_area_geom_wkt = Slot(uri=AMADEUS.area_geom_wkt, name="AreaValue_area_geom_wkt", curie=AMADEUS.curie('area_geom_wkt'),
                   model_uri=AMADEUS.AreaValue_area_geom_wkt, domain=AreaValue, range=Union[str, WktLiteral])

slots.AreaValue_area_km2 = Slot(uri=AMADEUS.area_km2, name="AreaValue_area_km2", curie=AMADEUS.curie('area_km2'),
                   model_uri=AMADEUS.AreaValue_area_km2, domain=AreaValue, range=Optional[float])

slots.HexCellValue_h3_cell = Slot(uri=AMADEUS.h3_cell, name="HexCellValue_h3_cell", curie=AMADEUS.curie('h3_cell'),
                   model_uri=AMADEUS.HexCellValue_h3_cell, domain=HexCellValue, range=Union[str, H3CellIndex])

slots.HexCellValue_h3_resolution = Slot(uri=AMADEUS.h3_resolution, name="HexCellValue_h3_resolution", curie=AMADEUS.curie('h3_resolution'),
                   model_uri=AMADEUS.HexCellValue_h3_resolution, domain=HexCellValue, range=int)

slots.HexCellValue_hexification_method = Slot(uri=AMADEUS.hexification_method, name="HexCellValue_hexification_method", curie=AMADEUS.curie('hexification_method'),
                   model_uri=AMADEUS.HexCellValue_hexification_method, domain=HexCellValue, range=Union[str, "AggregationMethodEnum"])

slots.HexCellValue_source_support_type = Slot(uri=AMADEUS.source_support_type, name="HexCellValue_source_support_type", curie=AMADEUS.curie('source_support_type'),
                   model_uri=AMADEUS.HexCellValue_source_support_type, domain=HexCellValue, range=Union[str, "SpatialSupportTypeEnum"])

slots.HexCellValue_coverage_fraction = Slot(uri=AMADEUS.coverage_fraction, name="HexCellValue_coverage_fraction", curie=AMADEUS.curie('coverage_fraction'),
                   model_uri=AMADEUS.HexCellValue_coverage_fraction, domain=HexCellValue, range=float)

slots.VectorFeature_product = Slot(uri=AMADEUS.product, name="VectorFeature_product", curie=AMADEUS.curie('product'),
                   model_uri=AMADEUS.VectorFeature_product, domain=VectorFeature, range=Union[str, ProductId])

slots.VectorFeature_feature_geom_wkt = Slot(uri=AMADEUS.feature_geom_wkt, name="VectorFeature_feature_geom_wkt", curie=AMADEUS.curie('feature_geom_wkt'),
                   model_uri=AMADEUS.VectorFeature_feature_geom_wkt, domain=VectorFeature, range=Union[str, WktLiteral])

slots.VectorFeature_geometry_type = Slot(uri=AMADEUS.geometry_type, name="VectorFeature_geometry_type", curie=AMADEUS.curie('geometry_type'),
                   model_uri=AMADEUS.VectorFeature_geometry_type, domain=VectorFeature, range=Union[str, "GeometryTypeEnum"])

slots.LocationSet_locs_id_field = Slot(uri=AMADEUS.locs_id_field, name="LocationSet_locs_id_field", curie=AMADEUS.curie('locs_id_field'),
                   model_uri=AMADEUS.LocationSet_locs_id_field, domain=LocationSet, range=str)

slots.LocationSet_phi_status = Slot(uri=AMADEUS.phi_status, name="LocationSet_phi_status", curie=AMADEUS.curie('phi_status'),
                   model_uri=AMADEUS.LocationSet_phi_status, domain=LocationSet, range=Union[str, "PhiStatusEnum"])

slots.LocationSet_crs = Slot(uri=AMADEUS.crs, name="LocationSet_crs", curie=AMADEUS.curie('crs'),
                   model_uri=AMADEUS.LocationSet_crs, domain=LocationSet, range=str,
                   pattern=re.compile(r'^[A-Za-z]+:[0-9]+$'))

slots.Location_location_set = Slot(uri=AMADEUS.location_set, name="Location_location_set", curie=AMADEUS.curie('location_set'),
                   model_uri=AMADEUS.Location_location_set, domain=Location, range=Union[str, LocationSetId])

slots.Location_location_key = Slot(uri=AMADEUS.location_key, name="Location_location_key", curie=AMADEUS.curie('location_key'),
                   model_uri=AMADEUS.Location_location_key, domain=Location, range=str)

slots.Location_location_geom_wkt = Slot(uri=AMADEUS.location_geom_wkt, name="Location_location_geom_wkt", curie=AMADEUS.curie('location_geom_wkt'),
                   model_uri=AMADEUS.Location_location_geom_wkt, domain=Location, range=Union[str, WktLiteral])

slots.ExtractionRequest_location_set = Slot(uri=AMADEUS.location_set, name="ExtractionRequest_location_set", curie=AMADEUS.curie('location_set'),
                   model_uri=AMADEUS.ExtractionRequest_location_set, domain=ExtractionRequest, range=Union[str, LocationSetId])

slots.ExtractionRequest_time_window_start = Slot(uri=AMADEUS.time_window_start, name="ExtractionRequest_time_window_start", curie=AMADEUS.curie('time_window_start'),
                   model_uri=AMADEUS.ExtractionRequest_time_window_start, domain=ExtractionRequest, range=Union[str, XSDDateTime])

slots.ExtractionRequest_time_window_end = Slot(uri=AMADEUS.time_window_end, name="ExtractionRequest_time_window_end", curie=AMADEUS.curie('time_window_end'),
                   model_uri=AMADEUS.ExtractionRequest_time_window_end, domain=ExtractionRequest, range=Union[str, XSDDateTime])

slots.ExtractionRequest_extraction_method = Slot(uri=AMADEUS.extraction_method, name="ExtractionRequest_extraction_method", curie=AMADEUS.curie('extraction_method'),
                   model_uri=AMADEUS.ExtractionRequest_extraction_method, domain=ExtractionRequest, range=Union[str, "ExtractionMethodEnum"])

slots.ExtractionRequest_request_hash = Slot(uri=AMADEUS.request_hash, name="ExtractionRequest_request_hash", curie=AMADEUS.curie('request_hash'),
                   model_uri=AMADEUS.ExtractionRequest_request_hash, domain=ExtractionRequest, range=Union[str, Sha256])

slots.ExtractionRequest_generated_sql = Slot(uri=AMADEUS.generated_sql, name="ExtractionRequest_generated_sql", curie=AMADEUS.curie('generated_sql'),
                   model_uri=AMADEUS.ExtractionRequest_generated_sql, domain=ExtractionRequest, range=Optional[str])

slots.AmbientValueAtLocation_location = Slot(uri=AMADEUS.location, name="AmbientValueAtLocation_location", curie=AMADEUS.curie('location'),
                   model_uri=AMADEUS.AmbientValueAtLocation_location, domain=AmbientValueAtLocation, range=Union[str, LocationId])

slots.AmbientValueAtLocation_extraction_request = Slot(uri=AMADEUS.extraction_request, name="AmbientValueAtLocation_extraction_request", curie=AMADEUS.curie('extraction_request'),
                   model_uri=AMADEUS.AmbientValueAtLocation_extraction_request, domain=AmbientValueAtLocation, range=Union[str, ExtractionRequestId])

slots.AmbientValueAtLocation_extraction_method = Slot(uri=AMADEUS.extraction_method, name="AmbientValueAtLocation_extraction_method", curie=AMADEUS.curie('extraction_method'),
                   model_uri=AMADEUS.AmbientValueAtLocation_extraction_method, domain=AmbientValueAtLocation, range=Union[str, "ExtractionMethodEnum"])

slots.AmbientValueAtLocation_contributing_value_count = Slot(uri=AMADEUS.contributing_value_count, name="AmbientValueAtLocation_contributing_value_count", curie=AMADEUS.curie('contributing_value_count'),
                   model_uri=AMADEUS.AmbientValueAtLocation_contributing_value_count, domain=AmbientValueAtLocation, range=Optional[int])

slots.AmbientValueAtLocation_distance_to_source_m = Slot(uri=AMADEUS.distance_to_source_m, name="AmbientValueAtLocation_distance_to_source_m", curie=AMADEUS.curie('distance_to_source_m'),
                   model_uri=AMADEUS.AmbientValueAtLocation_distance_to_source_m, domain=AmbientValueAtLocation, range=Optional[float])

slots.AmbientValueAtLocation_output_column_name = Slot(uri=AMADEUS.output_column_name, name="AmbientValueAtLocation_output_column_name", curie=AMADEUS.curie('output_column_name'),
                   model_uri=AMADEUS.AmbientValueAtLocation_output_column_name, domain=AmbientValueAtLocation, range=Optional[str])

slots.ToolRun_run_role = Slot(uri=AMADEUS.run_role, name="ToolRun_run_role", curie=AMADEUS.curie('run_role'),
                   model_uri=AMADEUS.ToolRun_run_role, domain=ToolRun, range=Union[str, "RunRoleEnum"])

slots.ToolRun_tool_name = Slot(uri=AMADEUS.tool_name, name="ToolRun_tool_name", curie=AMADEUS.curie('tool_name'),
                   model_uri=AMADEUS.ToolRun_tool_name, domain=ToolRun, range=str)

slots.ToolRun_tool_version = Slot(uri=AMADEUS.tool_version, name="ToolRun_tool_version", curie=AMADEUS.curie('tool_version'),
                   model_uri=AMADEUS.ToolRun_tool_version, domain=ToolRun, range=str)

slots.ToolRun_run_timestamp_utc = Slot(uri=AMADEUS.run_timestamp_utc, name="ToolRun_run_timestamp_utc", curie=AMADEUS.curie('run_timestamp_utc'),
                   model_uri=AMADEUS.ToolRun_run_timestamp_utc, domain=ToolRun, range=Union[str, XSDDateTime])

slots.ToolRun_status = Slot(uri=AMADEUS.status, name="ToolRun_status", curie=AMADEUS.curie('status'),
                   model_uri=AMADEUS.ToolRun_status, domain=ToolRun, range=Union[str, "RunStatusEnum"])

slots.ToolRun_function_name = Slot(uri=AMADEUS.function_name, name="ToolRun_function_name", curie=AMADEUS.curie('function_name'),
                   model_uri=AMADEUS.ToolRun_function_name, domain=ToolRun, range=Optional[str])

slots.ToolRun_run_arguments = Slot(uri=AMADEUS.run_arguments, name="ToolRun_run_arguments", curie=AMADEUS.curie('run_arguments'),
                   model_uri=AMADEUS.ToolRun_run_arguments, domain=ToolRun, range=Optional[str])

slots.ToolRun_container_image_digest = Slot(uri=AMADEUS.container_image_digest, name="ToolRun_container_image_digest", curie=AMADEUS.curie('container_image_digest'),
                   model_uri=AMADEUS.ToolRun_container_image_digest, domain=ToolRun, range=Optional[str],
                   pattern=re.compile(r'^sha256:[0-9a-f]{64}$'))

slots.ToolRun_bytes_transferred = Slot(uri=AMADEUS.bytes_transferred, name="ToolRun_bytes_transferred", curie=AMADEUS.curie('bytes_transferred'),
                   model_uri=AMADEUS.ToolRun_bytes_transferred, domain=ToolRun, range=Optional[int])

slots.ProvenanceChain_terminus_type = Slot(uri=AMADEUS.terminus_type, name="ProvenanceChain_terminus_type", curie=AMADEUS.curie('terminus_type'),
                   model_uri=AMADEUS.ProvenanceChain_terminus_type, domain=ProvenanceChain, range=Union[str, "ProvenanceChainTerminusEnum"])
