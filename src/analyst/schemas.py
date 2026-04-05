from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MarketLine:
    market: str
    selection: str
    odds: float
    source: str | None = None


@dataclass(slots=True)
class ParsedEvent:
    event_id: str
    home_team: str
    away_team: str
    league: str | None = None
    sport: str | None = None
    commence_time: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    lines: list[MarketLine] = field(default_factory=list)


@dataclass(slots=True)
class MarketInsight:
    event_id: str
    match_label: str
    sport: str | None
    league: str | None
    commence_time: str | None
    market: str
    selection: str
    implied_probability: float
    confidence: float
    consensus_odds: float | None
    data_points: int
    summary: str
