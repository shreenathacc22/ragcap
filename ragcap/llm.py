import os

from openai import OpenAI
from .config import LLM_BASE_URL, LLM_API_KEY, EMBED_MODEL

_client = None


def client() -> OpenAI:
    """One OpenAI-compatible client. Opt-in LangSmith: with LANGSMITH_TRACING=true (plus LANGSMITH_API_KEY and
    LANGSMITH_PROJECT in .env) every chat and embedding call is recorded as a LangSmith run, nested under the
    LangGraph node runs that langgraph itself reports when the same variable is set. Off by default: no change."""
    global _client
    if _client is None:
        _client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
        if os.getenv("LANGSMITH_TRACING", "").lower() == "true":
            from langsmith.wrappers import wrap_openai
            _client = wrap_openai(_client)
    return _client


def embed(texts: list[str]) -> list[list[float]]:
    res = client().embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in res.data]
