"""LLM client — MockLLMClient (no API cost) + LLMClient (OpenAI)."""
from __future__ import annotations
import time
from dataclasses import dataclass

class FailMode:
    NONE = "none"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    TIMEOUT = "timeout"
    BAD_OUTPUT = "bad_output"

@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None

_MOCK_RESEARCHER = """## GraphRAG Research Notes

### Key Sources
1. Edge et al. (2024) "From Local to Global: A Graph RAG Approach" — arXiv:2404.16130
2. github.com/microsoft/graphrag — Official open-source pipeline
3. LangChain GraphRAG integration docs (2024)
4. Neo4j LLM Graph RAG tutorial (2024)
5. arXiv benchmark: GraphRAG vs naive RAG on ALCE and FRAMES datasets

### Core Findings
GraphRAG builds an entity-relationship graph from the corpus via LLM extraction,
then uses community detection (Leiden algorithm) to generate hierarchical summaries.

**Two query modes:**
- Local search: entity-level navigation for specific factual questions
- Global search: community report aggregation for sensemaking queries

**Performance benchmarks:**
- +15–40% comprehensiveness over naive RAG on multi-hop questions
- 72% human preference on sensemaking queries (Edge et al. 2024)
- 2–3× higher token cost during indexing phase

### Limitations
- Indexing latency: hours for large corpora
- Overkill for simple factual lookups
- High upfront compute cost
"""

_MOCK_ANALYST = """## Analysis — GraphRAG State of the Art

### Evidence Assessment
| Source | Credibility | Key Contribution |
|---|---|---|
| Edge et al. 2024 (arXiv) | HIGH | Core architecture + benchmarks |
| Microsoft github repo | HIGH | Reference implementation |
| LangChain/Neo4j docs | MEDIUM | Ecosystem adoption signals |

### Key Insights

**1. GraphRAG solves a genuine gap** — naive RAG fails at cross-document synthesis;
GraphRAG's community detection fills this exactly.

**2. Two-tier architecture is the differentiator** — local/global coverage outperforms
single-retrieval approaches (HyDE, multi-query RAG).

**3. Cost-benefit trade-off governs adoption** — justified when corpus > ~10K docs
and queries need cross-document reasoning; overkill otherwise.

**4. Ecosystem matured rapidly in 2024** — LangChain, LlamaIndex, Neo4j all ship
native integrations; Microsoft open-sourced full pipeline.

### Comparison Table
| Approach | Multi-hop | Cost | Setup |
|---|---|---|---|
| Naive RAG | No | Low | Easy |
| HyDE | Partial | Medium | Medium |
| GraphRAG | Yes | High | Hard |

### Verdict
GraphRAG is current state-of-the-art for sensemaking but NOT a universal upgrade.
Choose based on query type and corpus size.
"""

_MOCK_WRITER = """# GraphRAG: State of the Art (2024)

GraphRAG — Graph Retrieval-Augmented Generation — represents a significant advance in
how AI systems retrieve and synthesize information from large document collections.
Introduced by Microsoft Research (Edge et al., 2024), GraphRAG addresses the core
limitation of traditional RAG: the inability to reason *across* documents rather than
within a single retrieved chunk.

## How GraphRAG Works

Traditional RAG splits documents into chunks, embeds them, and retrieves the most
similar chunks for a given query. This works for targeted factual lookups but fails
when a question requires synthesizing patterns across an entire corpus — what researchers
call "sensemaking queries."

GraphRAG solves this with a two-phase pipeline. During indexing, an LLM extracts
entities and relationships from every document, building a knowledge graph. Community
detection (the Leiden algorithm) then clusters related entities into communities, and
an LLM generates a concise summary report for each community.

At query time, GraphRAG offers two modes:
- **Local search** navigates the entity graph for specific entity-centric questions
- **Global search** aggregates community reports for broad thematic questions

## Performance and Benchmarks

Benchmarks on public datasets (ALCE, FRAMES) show GraphRAG improving answer
comprehensiveness by 15–40% over naive RAG on multi-hop questions. For sensemaking
queries, human evaluators preferred GraphRAG responses approximately 72% of the time
(Edge et al., 2024, arXiv:2404.16130).

## Ecosystem and Adoption

The GraphRAG ecosystem expanded rapidly in 2024. Microsoft open-sourced the full
pipeline at github.com/microsoft/graphrag. LangChain, LlamaIndex, and Neo4j all
released native integrations, lowering the barrier from research prototype to
production system considerably.

## Limitations

GraphRAG is not a universal upgrade. Indexing a large corpus requires substantial
upfront compute — community summarization consumes 2–3× the tokens of naive RAG over
the corpus lifetime. For simple factual retrieval, naive RAG remains faster and cheaper.
GraphRAG earns its cost when the corpus exceeds roughly 10,000 documents and queries
genuinely require cross-document synthesis.

## Conclusion

GraphRAG is the current state of the art for knowledge-intensive, multi-document
sensemaking tasks. Its two-tier local/global architecture elegantly addresses the
limitations of flat chunk retrieval. For teams working with large, interconnected
document collections, GraphRAG is the recommended approach as of 2024.

*Sources: Edge et al. (2024) arXiv:2404.16130, github.com/microsoft/graphrag,
LangChain GraphRAG docs, Neo4j tutorial, Anthropic Building Effective Agents*
"""

_MOCK_SINGLE = """# GraphRAG: A Brief Overview

GraphRAG (Graph Retrieval-Augmented Generation) is an approach introduced by Microsoft
Research in 2024 that improves on standard RAG by building a knowledge graph from
source documents instead of relying on flat vector similarity.

## What is GraphRAG?

Standard RAG retrieves document chunks based on embedding similarity. GraphRAG builds
an entity-relationship graph from the corpus, enabling the system to reason across
multiple documents rather than within a single chunk.

## Key Features

GraphRAG has two query modes: local search for specific entity questions, and global
search for broad thematic questions across the entire document collection. During
indexing, community detection clusters related entities and generates summary reports.

## Performance

According to Microsoft Research (Edge et al. 2024), GraphRAG outperforms naive RAG
on multi-hop and sensemaking queries, with 15–40% improvement in comprehensiveness
and roughly 70% human preference on complex queries.

## Limitations

The main downside is cost. The indexing phase consumes significantly more tokens due
to LLM-generated community summaries. Not suited for small corpora or simple lookups.

## Summary

GraphRAG is powerful for complex multi-document reasoning. Best suited for large
document collections where cross-document synthesis is required.

*Source: Microsoft Research (2024)*
"""

_MOCK_CRITIC = """## Critic Agent — Fact-Check Report

| Claim | Status | Note |
|---|---|---|
| Microsoft Research / Edge et al. 2024 | Verified | arXiv:2404.16130 confirmed |
| Two-mode architecture (local/global) | Verified | Confirmed in paper |
| Leiden algorithm | Verified | Confirmed in implementation |
| 15-40% improvement range | Verified | Within benchmark bounds |
| ~72% human preference | Hedged | Add "approximately" — exact figure varies |

**Hallucination risk: LOW** — no fabricated citations.
**Citation coverage: 5/5**
**Verdict: PASS** — minor: hedge "72%" to "approximately 72%".
"""


class MockLLMClient:
    """Zero-cost mock. fail_mode: none/researcher/analyst/writer/timeout/bad_output."""
    _IN_COST = 0.00015
    _OUT_COST = 0.0006

    def __init__(self, fail_mode: str = FailMode.NONE):
        self.fail_mode = fail_mode
        self.call_count = 0
        self.total_cost_usd = 0.0

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        from multi_agent_research_lab.core.errors import AgentExecutionError
        self.call_count += 1
        role = self._detect_role(system_prompt)

        if self.fail_mode == FailMode.TIMEOUT:
            time.sleep(0.05)
            raise AgentExecutionError("Simulated timeout (injected via fail_mode=timeout)")

        if self.fail_mode not in (FailMode.NONE, FailMode.BAD_OUTPUT) and self.fail_mode == role:
            raise AgentExecutionError(
                f"Simulated {role} failure — HTTP 500 (injected via fail_mode={self.fail_mode})")

        content = "" if self.fail_mode == FailMode.BAD_OUTPUT else self._content(role)
        in_tok = max(1, len(user_prompt.split()) * 4 // 3)
        out_tok = max(1, len(content.split()) * 4 // 3)
        cost = round(in_tok/1000*self._IN_COST + out_tok/1000*self._OUT_COST, 6)
        self.total_cost_usd += cost
        return LLMResponse(content=content, input_tokens=in_tok, output_tokens=out_tok, cost_usd=cost)

    def _detect_role(self, sp: str) -> str:
        # Agents prefix their system prompts with [ROLE:X] for reliable detection
        sp = sp.lower()
        if "[role:researcher]" in sp: return FailMode.RESEARCHER
        if "[role:analyst]" in sp: return FailMode.ANALYST
        if "[role:writer]" in sp: return FailMode.WRITER
        if "[role:critic]" in sp: return "critic"
        return "unknown"

    def _content(self, role: str) -> str:
        return {FailMode.RESEARCHER: _MOCK_RESEARCHER, FailMode.ANALYST: _MOCK_ANALYST,
                FailMode.WRITER: _MOCK_WRITER, "critic": _MOCK_CRITIC}.get(role, "Mock response.")


class LLMClient:
    """OpenAI-backed client for real mode."""
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError("pip install openai") from e
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self.call_count = 0
        self.total_cost_usd = 0.0

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        self.call_count += 1
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],
            temperature=0.3)
        content = resp.choices[0].message.content or ""
        usage = resp.usage
        cost = None
        if usage:
            cost = round(usage.prompt_tokens/1000*0.00015 + usage.completion_tokens/1000*0.0006, 6)
            self.total_cost_usd += cost
        return LLMResponse(content=content,
                           input_tokens=usage.prompt_tokens if usage else None,
                           output_tokens=usage.completion_tokens if usage else None,
                           cost_usd=cost)


MOCK_SINGLE_AGENT_OUTPUT = _MOCK_SINGLE
