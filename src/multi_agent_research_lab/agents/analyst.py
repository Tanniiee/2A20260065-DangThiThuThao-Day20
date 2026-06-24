"""Analyst agent — critical analysis of research notes."""
from __future__ import annotations
import time
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

_SYSTEM = """[ROLE:ANALYST]
You are a critical analyst. Receive research notes and produce structured analysis.

Use EXACTLY these section headers:
## Core Claims
- The main assertions made in the notes (1 sentence each)

## Strengths
- Well-supported points with strong evidence

## Weaknesses / Gaps
- Claims lacking evidence; flag with [WEAK EVIDENCE]

## Key Insights
- Non-obvious conclusions or patterns

## Open Questions
- What is still unclear or worth investigating?

## Comparison Table
| Approach | Strength | Weakness | Best For |
| ...      | ...      | ...      | ...      |

Be concise and critical. Flag weak evidence explicitly."""

class AnalystAgent(BaseAgent):
    """Critical analysis of research notes."""
    name = AgentName.ANALYST

    def __init__(self, llm) -> None:
        self._llm = llm

    def run(self, state: ResearchState) -> ResearchState:
        with trace_span("analyst", {}):
            t0 = time.perf_counter()
            try:
                if not state.research_notes:
                    raise AgentExecutionError("No research_notes to analyse")
                user_prompt = (
                    f"Original query: {state.request.query}\n\n"
                    f"Research notes:\n{state.research_notes}\n\n"
                    f"Produce structured critical analysis."
                )
                response = self._llm.complete(_SYSTEM, user_prompt)
                if not response.content.strip():
                    raise AgentExecutionError("LLM returned empty content")
                state.analysis_notes = response.content
                state.agent_results.append(AgentResult(
                    agent=AgentName.ANALYST,
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
                state.add_trace_event("analyst.done", {})
            except AgentExecutionError:
                raise
            except Exception as exc:
                raise AgentExecutionError(f"AnalystAgent error: {exc}") from exc
        return state
