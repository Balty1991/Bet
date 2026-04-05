from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from analyst.engine import AnalystEngine
from analyst.io import export_insights, load_events


def main() -> None:
    parser = argparse.ArgumentParser(description="Sports market analytics for scraper JSON exports")
    parser.add_argument("--input", required=True, help="Path to JSON input")
    parser.add_argument(
        "--markets",
        default="1x2,double_chance,over_1_5,over_2_5,under_3_5,btts",
        help="Comma-separated market names to analyze",
    )
    parser.add_argument("--top", type=int, default=25, help="Maximum rows to keep")
    parser.add_argument("--min-confidence", type=float, default=55.0, help="Minimum confidence 0-100")
    parser.add_argument("--output", default="analysis.json", help="Output file path")
    parser.add_argument("--output-format", choices=["json", "csv"], default="json", help="Output format")
    args = parser.parse_args()

    events = load_events(Path(args.input))
    engine = AnalystEngine()
    rows = engine.analyze_many(
        events=events,
        markets=[m.strip() for m in args.markets.split(",") if m.strip()],
        top=args.top,
        min_confidence=args.min_confidence,
    )
    export_insights(rows, Path(args.output), args.output_format)
    print(json.dumps([asdict(item) for item in rows[: min(5, len(rows))]], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
