"""Benchmark: measure latency, cost, and quality for single vs multi-agent runs."""
from __future__ import annotations

import re
import time
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]

# GraphRAG key terms for quality scoring
_KEY_TERMS = [
    "graphrag", "knowledge graph", "community", "entity", "multi-hop",
    "local search", "global search", "leiden", "sensemaking", "microsoft",
    "edge et al", "arxiv", "indexing", "retrieval", "citation",
]


def _quality_score(text: str) -> float:
    """Heuristic quality score 0–10. Used in mock mode (no human eval)."""
    if not text or not text.strip():
        return 0.0

    score = 0.0
    t = text.lower()

    # 1. Word count (target ~500 words) — max 3 pts
    wc = len(text.split())
    if wc >= 400:
        score += 3.0
    elif wc >= 200:
        score += 2.0
    elif wc >= 100:
        score += 1.0

    # 2. Key term coverage — max 3 pts
    covered = sum(1 for term in _KEY_TERMS if term in t)
    score += min(3.0, covered * 0.4)

    # 3. Structure: markdown headings — max 2 pts
    headings = len(re.findall(r"^#{1,3}\s", text, re.MULTILINE))
    score += min(2.0, headings * 0.5)

    # 4. Citations / sources mentioned — max 2 pts
    citations = len(re.findall(r"(arxiv|github|http|source|ref|\[\d+\]|et al)", t))
    score += min(2.0, citations * 0.4)

    return round(min(10.0, score), 1)


def run_benchmark(
    run_name: str,
    query: str,
    runner: Runner,
    notes: str = "",
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Time a runner, score its output, estimate cost, return state + metrics."""
    t0 = time.perf_counter()
    state = runner(query)
    latency = round(time.perf_counter() - t0, 3)

    answer = state.final_answer or ""
    quality = _quality_score(answer)

    # Sum cost across all agent results
    cost = sum(
        r.metadata.get("cost_usd", 0.0) or 0.0
        for r in state.agent_results
    ) or None

    errors_note = f" | {len(state.errors)} error(s)" if state.errors else ""
    fallback_note = " [FALLBACK]" if any("[FALLBACK" in (e or "") for e in state.errors) else ""

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=round(cost, 6) if cost else None,
        quality_score=quality,
        notes=notes + errors_note + fallback_note,
    )
    return state, metrics
