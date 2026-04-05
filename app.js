const MARKET_OPTIONS = ["1x2", "double_chance", "over_1_5", "over_2_5", "under_3_5", "btts"];

const state = {
  events: [],
  insights: [],
  selectedMarkets: new Set(MARKET_OPTIONS),
};

const el = {
  fileInput: document.getElementById("fileInput"),
  loadSampleBtn: document.getElementById("loadSampleBtn"),
  analyzeBtn: document.getElementById("analyzeBtn"),
  confidenceRange: document.getElementById("confidenceRange"),
  confidenceValue: document.getElementById("confidenceValue"),
  topSelect: document.getElementById("topSelect"),
  searchInput: document.getElementById("searchInput"),
  resultsBody: document.getElementById("resultsBody"),
  eventsCount: document.getElementById("eventsCount"),
  insightsCount: document.getElementById("insightsCount"),
  avgConfidence: document.getElementById("avgConfidence"),
  topMarket: document.getElementById("topMarket"),
  statusBadge: document.getElementById("statusBadge"),
  marketSelect: document.getElementById("marketSelect"),
  downloadBtn: document.getElementById("downloadBtn"),
};

function setStatus(text, type = "neutral") {
  el.statusBadge.textContent = text;
  el.statusBadge.className = `status ${type}`;
}

function safeFloat(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function clamp(value, low, high) {
  return Math.max(low, Math.min(high, value));
}

function normalizedProbabilities(oddsBySelection) {
  const raw = Object.entries(oddsBySelection)
    .filter(([, odd]) => Number(odd) > 1)
    .map(([key, odd]) => [key, 1 / Number(odd)]);
  const total = raw.reduce((acc, [, value]) => acc + value, 0);
  if (!total) return {};
  return Object.fromEntries(raw.map(([key, value]) => [key, value / total]));
}

function parseEvents(raw) {
  const items = Array.isArray(raw) ? raw : Array.isArray(raw?.data) ? raw.data : Array.isArray(raw?.events) ? raw.events : [raw];
  return items.map((item, index) => ({
    event_id: String(item.event_id || item.id || index + 1),
    home_team: item.home_team || item.home || item.team1 || "Home",
    away_team: item.away_team || item.away || item.team2 || "Away",
    league: item.league || item.competition || item.tournament || null,
    sport: item.sport || item.sport_name || null,
    commence_time: item.commence_time || item.start_time || item.kickoff || item.date || null,
    markets: item.markets || {},
  }));
}

function collectConsensus(event) {
  const result = {};
  Object.entries(event.markets || {}).forEach(([market, selections]) => {
    if (!selections || typeof selections !== "object") return;
    result[market] = {};
    Object.entries(selections).forEach(([selection, odd]) => {
      const parsed = safeFloat(odd);
      if (parsed && parsed > 1) result[market][selection] = { odds: parsed, count: 1 };
    });
  });
  return result;
}

function deriveProbabilities(consensus) {
  const probabilities = {};
  Object.entries(consensus).forEach(([market, selections]) => {
    probabilities[market] = normalizedProbabilities(
      Object.fromEntries(Object.entries(selections).map(([selection, meta]) => [selection, meta.odds]))
    );
  });

  if (!probabilities.double_chance && probabilities["1x2"]) {
    const p = probabilities["1x2"];
    probabilities.double_chance = {
      "1X": clamp((p.home || 0) + (p.draw || 0), 0, 1),
      "X2": clamp((p.away || 0) + (p.draw || 0), 0, 1),
      "12": clamp((p.home || 0) + (p.away || 0), 0, 1),
    };
  }

  return probabilities;
}

function analyzeEvents() {
  const minConfidence = Number(el.confidenceRange.value);
  const top = Number(el.topSelect.value);
  const search = el.searchInput.value.trim().toLowerCase();
  const markets = [...state.selectedMarkets];
  const rows = [];

  state.events.forEach((event) => {
    const matchLabel = `${event.home_team} vs ${event.away_team}`;
    if (search && !matchLabel.toLowerCase().includes(search)) return;
    const consensus = collectConsensus(event);
    const probabilities = deriveProbabilities(consensus);

    markets.forEach((market) => {
      const marketProbs = probabilities[market];
      if (!marketProbs) return;
      Object.entries(marketProbs).forEach(([selection, probability]) => {
        const meta = consensus[market]?.[selection] || { odds: null, count: 0 };
        const confidence = clamp(probability * 100 + Math.min(meta.count * 3, 12), 1, 99);
        if (confidence < minConfidence) return;
        rows.push({
          event_id: event.event_id,
          match_label: matchLabel,
          league: event.league || "-",
          sport: event.sport || "-",
          commence_time: event.commence_time || "-",
          market,
          selection,
          implied_probability: probability,
          confidence,
          consensus_odds: meta.odds,
          data_points: meta.count,
          summary: `${market}:${selection} evaluat din consensul pieței pe ${meta.count} sursă(e).`,
        });
      });
    });
  });

  rows.sort((a, b) => b.confidence - a.confidence || b.implied_probability - a.implied_probability);
  state.insights = rows.slice(0, top);
  render();
}

function renderSummary() {
  el.eventsCount.textContent = String(state.events.length);
  el.insightsCount.textContent = String(state.insights.length);
  const avg = state.insights.length
    ? state.insights.reduce((acc, item) => acc + item.confidence, 0) / state.insights.length
    : 0;
  el.avgConfidence.textContent = `${avg.toFixed(1)}`;
  const top = state.insights[0]?.market || "-";
  el.topMarket.textContent = top;
}

function renderRows() {
  if (!state.insights.length) {
    el.resultsBody.innerHTML = '<tr><td colspan="8" class="empty-state">Nu există rezultate pentru filtrele actuale.</td></tr>';
    return;
  }

  el.resultsBody.innerHTML = state.insights
    .map(
      (row) => `
        <tr>
          <td>
            <strong>${row.match_label}</strong><br />
            <span class="badge">${row.league}</span>
          </td>
          <td>${row.market}</td>
          <td>${row.selection}</td>
          <td>${(row.implied_probability * 100).toFixed(1)}%</td>
          <td>${row.confidence.toFixed(1)}</td>
          <td>${row.consensus_odds ? row.consensus_odds.toFixed(2) : '-'}</td>
          <td>${row.data_points}</td>
          <td>${row.summary}</td>
        </tr>
      `
    )
    .join("");
}

function render() {
  renderSummary();
  renderRows();
}

function buildMarketButtons() {
  el.marketSelect.innerHTML = MARKET_OPTIONS.map(
    (market) => `<button class="market-pill active" data-market="${market}">${market}</button>`
  ).join("");

  el.marketSelect.querySelectorAll(".market-pill").forEach((button) => {
    button.addEventListener("click", () => {
      const market = button.dataset.market;
      if (state.selectedMarkets.has(market)) {
        state.selectedMarkets.delete(market);
        button.classList.remove("active");
      } else {
        state.selectedMarkets.add(market);
        button.classList.add("active");
      }
    });
  });
}

async function loadSample() {
  try {
    setStatus("Se încarcă exemplul...", "neutral");
    const response = await fetch("examples/sample_upcoming.json", { cache: "no-store" });
    if (!response.ok) throw new Error("Nu am putut încărca exemplul.");
    const raw = await response.json();
    state.events = parseEvents(raw);
    analyzeEvents();
    setStatus(`Exemplu încărcat: ${state.events.length} evenimente`, "success");
  } catch (error) {
    setStatus(error.message || "Eroare la încărcare", "error");
  }
}

function exportJson() {
  const blob = new Blob([JSON.stringify(state.insights, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "bet-analyst-results.json";
  a.click();
  URL.revokeObjectURL(url);
}

el.fileInput.addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    setStatus(`Se citește ${file.name}...`, "neutral");
    const text = await file.text();
    const raw = JSON.parse(text);
    state.events = parseEvents(raw);
    analyzeEvents();
    setStatus(`Încărcat: ${state.events.length} evenimente`, "success");
  } catch (error) {
    setStatus("Fișier JSON invalid sau nesuportat.", "error");
  }
});

el.loadSampleBtn.addEventListener("click", loadSample);
el.analyzeBtn.addEventListener("click", analyzeEvents);
el.downloadBtn.addEventListener("click", exportJson);
el.confidenceRange.addEventListener("input", () => {
  el.confidenceValue.textContent = el.confidenceRange.value;
});
el.searchInput.addEventListener("input", analyzeEvents);
el.topSelect.addEventListener("change", analyzeEvents);
el.confidenceRange.addEventListener("change", analyzeEvents);

buildMarketButtons();
render();
