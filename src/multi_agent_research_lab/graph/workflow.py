"""Multi-agent workflow — pure Python state machine (no LangGraph required).

Fallback strategy per agent:
  researcher fail → inject placeholder notes, continue pipeline (degraded)
  analyst fail    → inject placeholder analysis, continue to writer (degraded)
  writer fail     → inject emergency summary from notes, mark error
  critic fail     → log error, skip (non-blocking bonus agent)
  max_iterations  → force stop, log error
"""
from __future__ import annotations

import time
from typing import Any

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.critic import CriticAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.schemas import AgentName
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import (
    FailMode, LLMClient, MockLLMClient,
)
from multi_agent_research_lab.services.search_client import MockSearchClient, SearchClient

# Fallback content injected when an agent fails
_FALLBACK_RESEARCH = (
    "[FALLBACK] Researcher agent failed. Using minimal fallback context.\n"
    "GraphRAG is a graph-based RAG approach by Microsoft (2024) that enables "
    "multi-hop reasoning via knowledge graphs and community summarization."
)
_FALLBACK_ANALYSIS = (
    "[FALLBACK] Analyst agent failed. Skipping structured analysis.\n"
    "Key point: GraphRAG outperforms naive RAG on sensemaking queries at higher cost."
)
_FALLBACK_ANSWER = (
    "[FALLBACK — writer agent failed]\n\n"
    "GraphRAG (Graph Retrieval-Augmented Generation) is Microsoft's 2024 approach "
    "to RAG that builds a knowledge graph from source documents and uses community "
    "detection to enable multi-hop, cross-document reasoning. It outperforms naive RAG "
    "on sensemaking queries but requires significantly more upfront indexing cost.\n\n"
    "Note: this is an emergency fallback answer — the writer agent encountered an error."
)


def build_clients(
    use_mock: bool = True,
    fail_mode: str = FailMode.NONE,
    openai_api_key: str | None = None,
    tavily_api_key: str | None = None,
    model: str = "gpt-4o",
) -> tuple[Any, Any]:
    """Return (llm_client, search_client) based on mode."""
    if use_mock:
        return MockLLMClient(fail_mode=fail_mode), MockSearchClient()
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY required for real mode")
    llm = LLMClient(api_key=openai_api_key, model=model)
    search = MockSearchClient() if not tavily_api_key else SearchClient(api_key=tavily_api_key)
    return llm, search


class MultiAgentWorkflow:
    """Supervisor-orchestrated pipeline: researcher → analyst → writer → (critic)."""

    def __init__(
        self,
        use_mock: bool = True,
        fail_mode: str = FailMode.NONE,
        run_critic: bool = True,
        max_iterations: int = 6,
        openai_api_key: str | None = None,
        tavily_api_key: str | None = None,
        model: str = "gpt-4o",
    ) -> None:
        self.max_iterations = max_iterations
        self.run_critic = run_critic

        llm, search = build_clients(use_mock, fail_mode, openai_api_key, tavily_api_key, model=model)
        self._llm = llm

        self._supervisor = SupervisorAgent(max_iterations=max_iterations)
        self._workers = {
            AgentName.RESEARCHER: ResearcherAgent(llm=llm, search=search),
            AgentName.ANALYST: AnalystAgent(llm=llm),
            AgentName.WRITER: WriterAgent(llm=llm),
        }
        self._critic = CriticAgent(llm=llm)

    def run(self, state: ResearchState) -> ResearchState:
        t_start = time.perf_counter()
        with trace_span("workflow", {"query": state.request.query}):

            # --- Main pipeline loop ---
            while True:
                next_agent = self._supervisor.decide(state)
                if next_agent == "done":
                    break

                state.record_route(next_agent)
                worker = self._workers[next_agent]

                try:
                    state = worker.run(state)
                    state.add_trace_event(f"{next_agent}.success", {})

                except AgentExecutionError as exc:
                    err_msg = f"{next_agent} FAILED: {exc}"
                    state.errors.append(err_msg)
                    state.add_trace_event(f"{next_agent}.fallback", {"error": str(exc)})
                    self._apply_fallback(next_agent, state)

            # --- Bonus: Critic (non-blocking) ---
            if self.run_critic and state.final_answer:
                try:
                    state = self._critic.run(state)
                    state.add_trace_event("critic.success", {})
                except AgentExecutionError as exc:
                    state.errors.append(f"critic FAILED (non-blocking): {exc}")
                    state.add_trace_event("critic.skipped", {"error": str(exc)})

        state.add_trace_event("workflow.done", {
            "total_latency_s": round(time.perf_counter() - t_start, 3),
            "errors": len(state.errors),
            "route": state.route_history,
        })
        return state

    def _apply_fallback(self, agent_name: str, state: ResearchState) -> None:
        """Inject fallback content so the pipeline can continue despite agent failure."""
        if agent_name == AgentName.RESEARCHER:
            if not state.research_notes:
                state.research_notes = _FALLBACK_RESEARCH
        elif agent_name == AgentName.ANALYST:
            if not state.analysis_notes:
                state.analysis_notes = _FALLBACK_ANALYSIS
        elif agent_name == AgentName.WRITER:
            if not state.final_answer:
                state.final_answer = _FALLBACK_ANSWER


class SingleAgentWorkflow:
    """Baseline: single LLM call — no pipeline, no collaboration."""

    def __init__(
        self,
        use_mock: bool = True,
        fail_mode: str = FailMode.NONE,
        openai_api_key: str | None = None,
        model: str = "gpt-4o",
    ) -> None:
        if use_mock:
            from multi_agent_research_lab.services.llm_client import MOCK_SINGLE_AGENT_OUTPUT
            self._mock_output = MOCK_SINGLE_AGENT_OUTPUT
            self._llm = None
        else:
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY required")
            self._llm = LLMClient(api_key=openai_api_key, model=model)
            self._mock_output = None

    def run(self, state: ResearchState) -> ResearchState:
        t0 = time.perf_counter()
        if self._llm is None:
            # mock mode
            state.final_answer = self._mock_output
        else:
            system = "You are a research assistant. Answer the user's research query with a comprehensive ~500-word report using markdown."
            resp = self._llm.complete(system, state.request.query)
            state.final_answer = resp.content

        state.add_trace_event("single_agent.done", {
            "latency_s": round(time.perf_counter() - t0, 3),
            "word_count": len((state.final_answer or "").split()),
        })
        return state
