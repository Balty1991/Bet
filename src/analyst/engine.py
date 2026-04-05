from __future__ import annotations

from collections import defaultdict

from analyst.schemas import MarketInsight, ParsedEvent
from analyst.utils import clamp


def normalized_probabilities(odds_by_selection: dict[str, float]) -> dict[str, float]:
    raw = {key: 1.0 / odd for key, odd in odds_by_selection.items() if odd and odd > 1.0}
    total = sum(raw.values())
    if total <= 0:
        return {}
    return {key: value / total for key, value in raw.items()}


def collect_market_consensus(event: ParsedEvent) -> dict[str, dict[str, tuple[float, int]]]:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for line in event.lines:
        grouped[line.market][line.selection].append(line.odds)

    consensus: dict[str, dict[str, tuple[float, int]]] = {}
    for market, selections in grouped.items():
        consensus[market] = {}
        for selection, values in selections.items():
            consensus[market][selection] = (sum(values) / len(values), len(values))
    return consensus


def derive_probabilities(consensus: dict[str, dict[str, tuple[float, int]]]) -> dict[str, dict[str, float]]:
    probabilities: dict[str, dict[str, float]] = {}

    for market, selections in consensus.items():
        odds_only = {selection: odds for selection, (odds, _) in selections.items()}
        probabilities[market] = normalized_probabilities(odds_only)

    if "double_chance" not in probabilities and "1x2" in probabilities:
        p = probabilities["1x2"]
        probabilities["double_chance"] = {
            "1X": clamp(p.get("home", 0.0) + p.get("draw", 0.0), 0.0, 1.0),
            "X2": clamp(p.get("away", 0.0) + p.get("draw", 0.0), 0.0, 1.0),
            "12": clamp(p.get("home", 0.0) + p.get("away", 0.0), 0.0, 1.0),
        }
    return probabilities


class AnalystEngine:
    def analyze_event(self, event: ParsedEvent, markets: list[str], min_confidence: float = 55.0) -> list[MarketInsight]:
        consensus = collect_market_consensus(event)
        probabilities = derive_probabilities(consensus)
        rows: list[MarketInsight] = []

        for market in markets:
            market_probs = probabilities.get(market)
            if not market_probs:
                continue
            for selection, probability in market_probs.items():
                odds, samples = consensus.get(market, {}).get(selection, (None, 0))
                confidence = clamp((probability * 100.0) + min(samples * 3.0, 12.0), 1.0, 99.0)
                if confidence < min_confidence:
                    continue
                rows.append(
                    MarketInsight(
                        event_id=event.event_id,
                        match_label=f"{event.home_team} vs {event.away_team}",
                        sport=event.sport,
                        league=event.league,
                        commence_time=event.commence_time,
                        market=market,
                        selection=selection,
                        implied_probability=round(probability, 4),
                        confidence=round(confidence, 2),
                        consensus_odds=round(odds, 3) if odds else None,
                        data_points=samples,
                        summary=f"{market}:{selection} evaluated from market consensus across {samples} data point(s).",
                    )
                )
        rows.sort(key=lambda row: (row.confidence, row.implied_probability), reverse=True)
        return rows

    def analyze_many(self, events: list[ParsedEvent], markets: list[str], top: int = 25, min_confidence: float = 55.0) -> list[MarketInsight]:
        rows: list[MarketInsight] = []
        for event in events:
            rows.extend(self.analyze_event(event, markets=markets, min_confidence=min_confidence))
        rows.sort(key=lambda row: (row.confidence, row.implied_probability), reverse=True)
        return rows[:top]
