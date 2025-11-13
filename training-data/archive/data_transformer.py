"""Helper utilities for transforming Bicep templates into agent-ready training data."""
from __future__ import annotations

import json
import re
from typing import Dict, List, Tuple

_PARAM_PATTERN = re.compile(r"^\s*param\s+(?P<name>\w+)\s+(?P<type>[\w\[\]]+)(?:\s*=\s*(?P<default>.+))?\s*$", re.MULTILINE)
_MODULE_PATTERN = re.compile(r"module\s+(?P<symbol>\w+)\s+'(?P<type>[^']+)'", re.IGNORECASE)
_RESOURCE_PATTERN = re.compile(r"resource\s+(?P<symbol>\w+)\s+'(?P<type>[^']+)'", re.IGNORECASE)


def _clean_default_value(raw_value: str) -> str:
    """Trim inline comments and trailing commas from a default value string."""
    value = raw_value.split('//', 1)[0].strip().rstrip(',')
    return value


def _coerce_default(value: str):
    """Best-effort coercion of a Bicep default literal into a Python type."""
    if not value:
        return "<YOUR_VALUE_HERE>"

    stripped = value.strip()

    if stripped.startswith("'") and stripped.endswith("'"):
        return stripped[1:-1]

    # Attempt numeric conversion
    try:
        if '.' in stripped:
            return float(stripped)
        return int(stripped)
    except ValueError:
        pass

    if stripped.startswith('[') and stripped.endswith(']'):
        candidate = stripped.replace("'", '"')
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return stripped

    if stripped in {"true", "false"}:
        return stripped == "true"

    return stripped or "<YOUR_VALUE_HERE>"


def generate_parameters_json(bicep_code: str) -> str:
    """Build a parameters.json payload from the provided Bicep code."""
    parameters: Dict[str, Dict[str, object]] = {}

    for match in _PARAM_PATTERN.finditer(bicep_code):
        name = match.group('name')
        default_raw = match.group('default')
        default_value = "<YOUR_VALUE_HERE>"

        if default_raw is not None:
            cleaned = _clean_default_value(default_raw)
            coerced = _coerce_default(cleaned)
            default_value = coerced

        parameters[name] = {"value": default_value}

    payload = {"parameters": parameters}
    return json.dumps(payload, indent=2)


def generate_plan_and_warnings(bicep_code: str) -> Tuple[Dict[str, object], List[str]]:
    """Construct the plan metadata and warnings list for the supplied Bicep code."""
    is_avm = 'br/public:avm' in bicep_code

    target_pattern = _MODULE_PATTERN if is_avm else _RESOURCE_PATTERN
    match = target_pattern.search(bicep_code)

    resources: List[Dict[str, str]] = []
    rationale = 'AVM module selected.' if is_avm else 'Classic Bicep resource selected.'

    if match:
        resources.append({
            "resourceType": match.group('type'),
            "name": match.group('symbol')
        })

    warnings: List[str] = [] if is_avm else ['Fell back to classic Bicep resource.']
    plan = {
        "resources": resources,
        "rationale": rationale
    }
    return plan, warnings
