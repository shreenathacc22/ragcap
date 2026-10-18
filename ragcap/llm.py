from openai import OpenAI
from .config import LLM_BASE_URL, LLM_API_KEY, EMBED_MODEL

_client = None


def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
    return _client


def embed(texts: list[str]) -> list[list[float]]:
    res = client().embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in res.data]
