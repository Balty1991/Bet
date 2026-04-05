from __future__ import annotations

from typing import Any, Iterable


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))



def safe_float(value: Any) -> float | None:
    try:
        if value is None or isinstance(value, bool):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None



def flatten_dict_items(data: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield path, value
            yield from flatten_dict_items(value, path)
    elif isinstance(data, list):
        for index, value in enumerate(data):
            path = f"{prefix}[{index}]"
            yield path, value
            yield from flatten_dict_items(value, path)
