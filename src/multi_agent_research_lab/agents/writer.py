"""Writer agent — synthesises notes into final answer."""
from __future__ import annotations
import time
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

_SYSTEM = """[ROLE:WRITER]
You are a technical writer. Synthesise research notes and analysis into a polished response.

Requirements:
- Write in flowing prose (not just bullet lists)
- Include a brief introduction and a conclusion
- Cite sources inline where available (e.g. [Author, Year] or [URL])
- Target length: ~500 words
- Use markdown headings (##) to structure sections
- Do NOT copy section headers verbatim from notes — synthesise them
- End with a balanced judgment: when to use this approach and when not to"""

class WriterAgent(BaseAgent):
    """Synthesises research + analysis into a final answer."""
    name = AgentName.WRITER

    def __init__(self, llm) -> None:
        self._llm = llm

    def run(self, state: ResearchState) -> ResearchState:
        with trace_span("writer", {}):
            t0 = time.perf_counter()
            try:
                user_prompt = (
                    f"Query: {state.request.query}\n\n"
                    f"Research notes:\n{state.research_notes or '(none)'}\n\n"
                    f"Analysis:\n{state.analysis_notes or '(none)'}\n\n"
                    f"Write the final response."
                )
                response = self._llm.complete(_SYSTEM, user_prompt)
                if not response.content.strip():
                    raise AgentExecutionError("LLM returned empty content")
                state.final_answer = response.content
                state.agent_results.append(AgentResult(
                    agent=AgentName.WRITER,
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
                state.add_trace_event("writer.done", {})
            except AgentExecutionError:
                raise
            except Exception as exc:
                raise AgentExecutionError(f"WriterAgent error: {exc}") from exc
        return state
