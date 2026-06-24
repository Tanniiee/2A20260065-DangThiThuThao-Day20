"""Critic agent — fact-checks the final answer (bonus, non-blocking)."""
from __future__ import annotations
import time
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

_SYSTEM = """[ROLE:CRITIC]
You are a rigorous fact-checker. Review the answer against the provided sources.

For each major claim in the answer:
1. Mark as ✅ VERIFIED if supported by sources
2. Mark as ⚠️ HEDGED if partially supported
3. Mark as ❌ UNSUPPORTED if not backed by sources

Produce a markdown table:
| Claim | Status | Note |
|---|---|---|

Then state: Hallucination risk (LOW/MEDIUM/HIGH), Citation coverage (N/M), and an overall Verdict."""

class CriticAgent(BaseAgent):
    """Non-blocking fact-check agent."""
    name = AgentName.CRITIC

    def __init__(self, llm) -> None:
        self._llm = llm

    def run(self, state: ResearchState) -> ResearchState:
        with trace_span("critic", {}):
            t0 = time.perf_counter()
            try:
                if not state.final_answer:
                    raise AgentExecutionError("No final_answer to check")
                sources_ctx = "\n".join(
                    f"[{i+1}] {s.title}: {s.snippet[:120]}"
                    for i, s in enumerate(state.sources or [])
                )
                user_prompt = (
                    f"Answer to fact-check:\n{state.final_answer}\n\n"
                    f"Sources:\n{sources_ctx or '(none)'}\n\n"
                    f"Fact-check the answer against these sources."
                )
                response = self._llm.complete(_SYSTEM, user_prompt)
                state.agent_results.append(AgentResult(
                    agent=AgentName.CRITIC,
                    content=response.content,
                    metadata={
                        "cost_usd": response.cost_usd,
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "system_prompt": _SYSTEM,
                        "user_prompt": user_prompt,
                        "latency_s": round(time.perf_counter() - t0, 3),
                    },
                ))
                state.add_trace_event("critic.done", {})
            except AgentExecutionError:
                raise
            except Exception as exc:
                raise AgentExecutionError(f"CriticAgent error: {exc}") from exc
        return state
