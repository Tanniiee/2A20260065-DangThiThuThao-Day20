"""Benchmark report — includes side-by-side single vs multi-agent answers."""
from __future__ import annotations

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState


def render_markdown_report(
    metrics: list[BenchmarkMetrics],
    states: list[ResearchState] | None = None,
) -> str:
    """Render full benchmark report with side-by-side answer comparison."""
    lines: list[str] = []

    lines += [
        "# Benchmark Report — Single Agent vs Multi-Agent",
        "",
        "## Summary Table",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality /10 | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for m in metrics:
        cost = f"${m.estimated_cost_usd:.4f}" if m.estimated_cost_usd is not None else "—"
        quality = f"{m.quality_score:.1f}" if m.quality_score is not None else "—"
        lines.append(f"| **{m.run_name}** | {m.latency_seconds:.2f} | {cost} | {quality} | {m.notes} |")

    lines += [""]

    # --- Analysis section ---
    if len(metrics) >= 2:
        single = next((m for m in metrics if "single" in m.run_name.lower()), None)
        multi = next((m for m in metrics if "multi" in m.run_name.lower()), None)
        if single and multi:
            lat_diff = single.latency_seconds - multi.latency_seconds
            q_diff = (multi.quality_score or 0) - (single.quality_score or 0)
            lines += [
                "## Analysis",
                "",
                f"- **Latency**: Multi-agent {'faster' if lat_diff > 0 else 'slower'} by {abs(lat_diff):.2f}s "
                f"({'mock mode — both near-instant' if abs(lat_diff) < 0.5 else ''})",
                f"- **Quality delta**: +{q_diff:.1f} pts for multi-agent "
                f"({'higher structure, more citations, better coverage' if q_diff > 0 else 'no improvement'})",
                f"- **Cost**: Multi-agent uses {len([m for m in metrics if 'multi' in m.run_name.lower()])} agent calls "
                f"vs 1 for single — higher API cost, justified by quality gain.",
                "",
                "> **When to use multi-agent:** corpus synthesis, multi-hop queries, high-stakes reports.  ",
                "> **When to stay single-agent:** simple factual Q&A, latency-sensitive apps, small corpora.",
                "",
            ]

    # --- Side-by-side answer comparison ---
    if states and len(states) >= 2:
        lines += [
            "---",
            "",
            "## Side-by-Side Answer Comparison",
            "",
            "> Cùng một query — so sánh output thực tế của hai pipeline.",
            "",
        ]

        single_state = next((s for s in states if hasattr(s, "_run_name") and "single" in (s._run_name or "").lower()), states[0])
        multi_state = next((s for s in states if hasattr(s, "_run_name") and "multi" in (s._run_name or "").lower()), states[1])

        single_ans = (single_state.final_answer or "*(no answer)*").strip()
        multi_ans = (multi_state.final_answer or "*(no answer)*").strip()

        single_wc = len(single_ans.split())
        multi_wc = len(multi_ans.split())

        lines += [
            f"### 🔵 Single-Agent Answer  *(~{single_wc} words)*",
            "",
            single_ans,
            "",
            "---",
            "",
            f"### 🟢 Multi-Agent Answer  *(~{multi_wc} words)*",
            "",
            multi_ans,
            "",
        ]

        # Fallback / error log
        all_errors: list[str] = []
        for i, state in enumerate(states):
            label = getattr(state, "_run_name", f"Run {i+1}")
            for e in state.errors:
                all_errors.append(f"[{label}] {e}")

        if all_errors:
            lines += [
                "---",
                "",
                "## Error & Fallback Log",
                "",
                "```",
            ]
            lines += all_errors
            lines += ["```", ""]

        # Trace for multi-agent
        if multi_state.trace:
            lines += [
                "---",
                "",
                "## Multi-Agent Trace",
                "",
                "| Event | Details |",
                "|---|---|",
            ]
            for event in multi_state.trace:
                payload = ", ".join(f"{k}={v}" for k, v in (event.get("payload") or {}).items())
                lines.append(f"| `{event['name']}` | {payload} |")
            lines.append("")

        # Agent breakdown
        if multi_state.agent_results:
            lines += [
                "---",
                "",
                "## Multi-Agent — Per-Agent Breakdown",
                "",
                "| Agent | Words | Cost (USD) | Latency (s) |",
                "|---|---:|---:|---:|",
            ]
            for r in multi_state.agent_results:
                wc = len(r.content.split())
                cost = r.metadata.get("cost_usd", "—")
                lat = r.metadata.get("latency_s", "—")
                cost_str = f"${cost:.5f}" if isinstance(cost, float) else str(cost)
                lines.append(f"| {r.agent} | {wc} | {cost_str} | {lat} |")
            lines.append("")

    return "\n".join(lines)
