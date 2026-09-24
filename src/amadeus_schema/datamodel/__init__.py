"""Data model package for amadeus-schema."""

from pathlib import Path
from .amadeus_schema import *  # noqa: F403

THIS_PATH = Path(__file__).parent

SCHEMA_DIRECTORY = THIS_PATH.parent / "schema"
MAIN_SCHEMA_PATH = SCHEMA_DIRECTORY / "amadeus_schema.yaml"
