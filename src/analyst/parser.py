from __future__ import annotations

from typing import Any

from analyst.schemas import MarketLine, ParsedEvent
from analyst.utils import flatten_dict_items, safe_float

TEAM_KEYS_HOME = ("home_team", "home", "team1", "homeName", "participant1")
TEAM_KEYS_AWAY = ("away_team", "away", "team2", "awayName", "participant2")
LEAGUE_KEYS = ("league", "competition", "tournament", "category")
SPORT_KEYS = ("sport", "sport_name")
TIME_KEYS = ("commence_time", "start_time", "kickoff", "date")
ID_KEYS = ("id", "event_id", "match_id", "slug", "url")


def _first_value(data: dict[str, Any], names: tuple[str, ...]) -> Any | None:
    for key in names:
        if key in data and data[key] not in (None, ""):
            return data[key]
    for _, value in flatten_dict_items(data):
        if isinstance(value, dict):
            for key in names:
                if key in value and value[key] not in (None, ""):
                    return value[key]
    return None


def _deduplicate_lines(lines: list[MarketLine]) -> list[MarketLine]:
    seen: set[tuple[str, str, float]] = set()
    result: list[MarketLine] = []
    for line in lines:
        key = (line.market, line.selection, round(line.odds, 4))
        if key not in seen:
            seen.add(key)
            result.append(line)
    return result


def _collect_market_lines(data: dict[str, Any]) -> list[MarketLine]:
    lines: list[MarketLine] = []

    def add_line(market: str, selection: str, odds: Any, source: str | None = None):
        parsed_odds = safe_float(odds)
        if parsed_odds and parsed_odds > 1.0:
            lines.append(MarketLine(market=market, selection=selection, odds=parsed_odds, source=source))

    for path, value in flatten_dict_items(data):
        lowered = path.lower()
        if not isinstance(value, (int, float, str)):
            continue

        if "1x2" in lowered or lowered.endswith((".home", ".draw", ".away")):
            if lowered.endswith((".home", ".1")):
                add_line("1x2", "home", value, path)
            elif lowered.endswith((".draw", ".x")):
                add_line("1x2", "draw", value, path)
            elif lowered.endswith((".away", ".2")):
                add_line("1x2", "away", value, path)

        if "double" in lowered or lowered.endswith(("1x", "x2", "12")):
            if lowered.endswith("1x"):
                add_line("double_chance", "1X", value, path)
            elif lowered.endswith("x2"):
                add_line("double_chance", "X2", value, path)
            elif lowered.endswith("12"):
                add_line("double_chance", "12", value, path)

        if "btts" in lowered or "both" in lowered:
            if any(token in lowered for token in ("yes", "gg", "true")):
                add_line("btts", "yes", value, path)
            elif any(token in lowered for token in ("no", "ng", "false")):
                add_line("btts", "no", value, path)

        if "over" in lowered and "under" not in lowered:
            if any(token in lowered for token in ("1.5", "15")):
                add_line("over_1_5", "over", value, path)
            elif any(token in lowered for token in ("2.5", "25")):
                add_line("over_2_5", "over", value, path)
            elif any(token in lowered for token in ("3.5", "35")):
                add_line("over_3_5", "over", value, path)

        if "under" in lowered:
            if any(token in lowered for token in ("2.5", "25")):
                add_line("under_2_5", "under", value, path)
            elif any(token in lowered for token in ("3.5", "35")):
                add_line("under_3_5", "under", value, path)

    return _deduplicate_lines(lines)


def parse_event(data: dict[str, Any], fallback_id: str) -> ParsedEvent:
    home_team = _first_value(data, TEAM_KEYS_HOME) or "Home"
    away_team = _first_value(data, TEAM_KEYS_AWAY) or "Away"
    league = _first_value(data, LEAGUE_KEYS)
    sport = _first_value(data, SPORT_KEYS)
    commence_time = _first_value(data, TIME_KEYS)
    event_id = str(_first_value(data, ID_KEYS) or fallback_id)

    return ParsedEvent(
        event_id=event_id,
        home_team=str(home_team),
        away_team=str(away_team),
        league=str(league) if league is not None else None,
        sport=str(sport) if sport is not None else None,
        commence_time=str(commence_time) if commence_time is not None else None,
        raw=data,
        lines=_collect_market_lines(data),
    )
