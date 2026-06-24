"""Supervisor agent — routing decision logic."""
from __future__ import annotations
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName
from multi_agent_research_lab.core.state import ResearchState

PIPELINE = [AgentName.RESEARCHER, AgentName.ANALYST, AgentName.WRITER]

class SupervisorAgent(BaseAgent):
    """Deterministic router: researcher → analyst → writer → done.

    Routing rules:
    - If research_notes missing  → researcher
    - If analysis_notes missing  → analyst
    - If final_answer missing    → writer
    - Otherwise                  → done
    - If iteration >= max        → done (safety guard)
    """
    name = AgentName.SUPERVISOR

    def __init__(self, max_iterations: int = 6) -> None:
        self.max_iterations = max_iterations

    def decide(self, state: ResearchState) -> str:
        """Return next agent name, or 'done'."""
        if state.iteration >= self.max_iterations:
            state.errors.append(f"Supervisor: max_iterations ({self.max_iterations}) reached, forcing done")
            return "done"
        if not state.research_notes:
            return AgentName.RESEARCHER
        if not state.analysis_notes:
            return AgentName.ANALYST
        if not state.final_answer:
            return AgentName.WRITER
        return "done"

    def run(self, state: ResearchState) -> ResearchState:
        """Not called directly in simple workflow — use decide() instead."""
        next_agent = self.decide(state)
        state.record_route(next_agent)
        return state
