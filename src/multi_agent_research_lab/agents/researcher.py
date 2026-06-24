"""Researcher agent — collects sources and writes research notes."""
from __future__ import annotations
import time
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

_SYSTEM = """[ROLE:RESEARCHER]
You are a research specialist. Gather comprehensive information on the given topic.

Use EXACTLY these section headers:
## Key Facts
- Core definitions, background, key concepts

## Current State / Recent Developments
- Latest papers, benchmarks, tools, frameworks (2023-2024)

## Important Sources / References
- Real papers, GitHub repos, authors, URLs

## Arguments For
- Evidence-backed benefits and advantages

## Arguments Against / Limitations
- Weaknesses, failure modes, cost trade-offs

## Proposed Experiments
- 2-3 concrete experiments to test claims

Be factual. If uncertain about a detail, flag it explicitly. Cite sources inline."""

class ResearcherAgent(BaseAgent):
    """Collects sources and creates research notes."""
    name = AgentName.RESEARCHER

    def __init__(self, llm, search) -> None:
        self._llm = llm
        self._search = search

    def run(self, state: ResearchState) -> ResearchState:
        with trace_span("researcher", {"query": state.request.query}):
            t0 = time.perf_counter()
            try:
                sources = self._search.search(state.request.query, max_results=state.request.max_sources)
                if not sources:
                    raise AgentExecutionError("SearchClient returned 0 results")
                state.sources = sources
                context = "\n\n".join(f"[{i+1}] {s.title}\n{s.snippet}" for i, s in enumerate(sources))
                user_prompt = (
                    f"Query: {state.request.query}\n\n"
                    f"Sources:\n{context}\n\n"
                    f"Write comprehensive structured research notes."
                )
                response = self._llm.complete(_SYSTEM, user_prompt)
                if not response.content.strip():
                    raise AgentExecutionError("LLM returned empty content")
                state.research_notes = response.content
                state.agent_results.append(AgentResult(
                    agent=AgentName.RESEARCHER,
                    content=response.content,
                    metadata={
                        "sources_found": len(sources),
                        "cost_usd": response.cost_usd,
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "system_prompt": _SYSTEM,
                        "user_prompt": user_prompt,
                        "latency_s": round(time.perf_counter() - t0, 3),
                    },
                ))
                state.add_trace_event("researcher.done", {"sources": len(sources)})
            except AgentExecutionError:
                raise
            except Exception as exc:
                raise AgentExecutionError(f"ResearcherAgent error: {exc}") from exc
        return state
