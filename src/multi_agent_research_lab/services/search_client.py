"""Search client — MockSearchClient + Tavily SearchClient."""
from __future__ import annotations
from multi_agent_research_lab.core.schemas import SourceDocument

_SOURCES = [
    SourceDocument(
        title="From Local to Global: A Graph RAG Approach (Edge et al., 2024)",
        url="https://arxiv.org/abs/2404.16130",
        snippet=(
            "We introduce Graph RAG, an approach to question answering over private text corpora "
            "that scales with both the generality of user questions and the quantity of source text. "
            "An LLM builds a graph-based text index: first an entity knowledge graph, then community "
            "summaries for all groups of closely-related entities (Leiden algorithm). "
            "Global search aggregates community reports; local search navigates entity neighbors."
        ),
        metadata={"year": 2024, "authors": "Edge et al.", "venue": "arXiv"},
    ),
    SourceDocument(
        title="microsoft/graphrag — Official Open-Source Implementation",
        url="https://github.com/microsoft/graphrag",
        snippet=(
            "GraphRAG is a structured, hierarchical RAG approach. The pipeline supports "
            "local search (entity-level), global search (community-level), pluggable LLM providers, "
            "and the Leiden community detection algorithm. Open-sourced by Microsoft in 2024."
        ),
        metadata={"year": 2024, "type": "code"},
    ),
    SourceDocument(
        title="LangChain GraphRAG Integration Guide",
        url="https://python.langchain.com/docs/integrations/graphrag",
        snippet=(
            "LangChain provides native GraphRAG integration via GraphRAGRetriever. "
            "Supports both local and global search. Requires a pre-built GraphRAG index. "
            "Drop-in replacement for standard vector retrievers."
        ),
        metadata={"year": 2024, "type": "documentation"},
    ),
    SourceDocument(
        title="Neo4j Knowledge Graph + LLM: GraphRAG Tutorial",
        url="https://neo4j.com/developer-blog/graphrag-llm-knowledge-graph/",
        snippet=(
            "Combining Neo4j property graphs with LLMs enables powerful GraphRAG pipelines. "
            "Entity extraction populates the graph; vector + graph hybrid search retrieves "
            "relevant subgraphs at query time. Outperforms naive RAG on multi-hop benchmarks."
        ),
        metadata={"year": 2024, "type": "tutorial"},
    ),
    SourceDocument(
        title="GraphRAG Benchmark — ALCE and FRAMES datasets (2024)",
        url="https://arxiv.org/abs/2404.16130",
        snippet=(
            "GraphRAG global search achieves 15-40% higher comprehensiveness over baseline RAG. "
            "Human evaluators preferred GraphRAG responses in approximately 72% of sensemaking "
            "query comparisons. Cost tradeoff: 2-3x higher token usage during indexing phase."
        ),
        metadata={"year": 2024, "type": "benchmark"},
    ),
]


class MockSearchClient:
    """Returns deterministic mock SourceDocuments — zero API cost."""
    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        return _SOURCES[:max_results]


class SearchClient:
    """Tavily-backed search for production use."""
    def __init__(self, api_key: str) -> None:
        try:
            from tavily import TavilyClient
        except ImportError as e:
            raise ImportError("pip install tavily-python") from e
        self._client = TavilyClient(api_key=api_key)

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        result = self._client.search(query=query, max_results=max_results)
        return [
            SourceDocument(title=r.get("title",""), url=r.get("url"), snippet=r.get("content",""))
            for r in result.get("results", [])
        ]
