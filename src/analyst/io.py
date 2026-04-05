from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from analyst.parser import parse_event


def load_events(path: Path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        if isinstance(raw.get("data"), list):
            items = raw["data"]
        elif isinstance(raw.get("events"), list):
            items = raw["events"]
        else:
            items = [raw]
    elif isinstance(raw, list):
        items = raw
    else:
        raise ValueError("Unsupported JSON structure.")

    return [parse_event(item, fallback_id=str(idx + 1)) for idx, item in enumerate(items)]


def export_insights(rows, path: Path, output_format: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(row) for row in rows]
    if output_format == "json":
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return
    if output_format == "csv":
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(payload[0].keys()) if payload else [
                "event_id", "match_label", "sport", "league", "commence_time", "market", "selection",
                "implied_probability", "confidence", "consensus_odds", "data_points", "summary"
            ])
            writer.writeheader()
            writer.writerows(payload)
        return
    raise ValueError(f"Unsupported output format: {output_format}")
