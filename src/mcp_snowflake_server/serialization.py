"""
Simple serialization utilities for Snowflake data types.
Handles both JSON and YAML serialization consistently.
"""

import json
import math
from datetime import date
from decimal import Decimal

import pandas as pd
import yaml


def _serialize_value(obj: object) -> object:
    """Convert Snowflake-specific types to serializable values"""
    if obj is pd.NaT:
        return None
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, float) and math.isnan(obj):
        return None
    else:
        return obj


def json_serializer(obj: object) -> object:
    """JSON serializer for Snowflake types"""
    return _serialize_value(obj)


def _yaml_representer(dumper: yaml.Dumper, data: object) -> yaml.Node:
    """YAML representer for Snowflake types"""
    serialized = _serialize_value(data)

    if serialized is None:
        return dumper.represent_scalar("tag:yaml.org,2002:null", "")
    elif isinstance(serialized, bool):
        return dumper.represent_scalar("tag:yaml.org,2002:bool", str(serialized).lower())
    elif isinstance(serialized, int):
        return dumper.represent_scalar("tag:yaml.org,2002:int", str(serialized))
    elif isinstance(serialized, float):
        return dumper.represent_scalar("tag:yaml.org,2002:float", str(serialized))
    else:
        return dumper.represent_scalar("tag:yaml.org,2002:str", str(serialized))


# Custom YAML dumper
class SnowflakeDumper(yaml.SafeDumper):
    pass


# Register all Snowflake types with YAML
SnowflakeDumper.add_representer(date, _yaml_representer)  # type: ignore[arg-type]
SnowflakeDumper.add_representer(pd.Timestamp, _yaml_representer)  # type: ignore[arg-type]
SnowflakeDumper.add_representer(type(pd.NaT), _yaml_representer)  # type: ignore[arg-type]
SnowflakeDumper.add_representer(Decimal, _yaml_representer)  # type: ignore[arg-type]
SnowflakeDumper.add_representer(float, _yaml_representer)  # type: ignore[arg-type]


# Public API
def to_yaml(data: object) -> str:
    """Convert data to YAML with Snowflake type handling"""
    result = yaml.dump(data, Dumper=SnowflakeDumper, indent=2, sort_keys=False)
    return result if result is not None else ""


def to_json(data: object) -> str:
    """Convert data to JSON with Snowflake type handling"""
    return json.dumps(data, default=json_serializer, indent=2)
