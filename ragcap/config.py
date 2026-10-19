"""One place for settings. Local Ollama by default; set LLM_BASE_URL/LLM_API_KEY to use another OpenAI-compatible endpoint."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

PG_DSN = (f"host={os.getenv('PGHOST','localhost')} port={os.getenv('PGPORT','5433')} "
          f"dbname={os.getenv('PGDATABASE','ragcap')} user={os.getenv('PGUSER','ragcap')} "
          f"password={os.getenv('PGPASSWORD','')}")

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
# Grader experiment switch (step 19). Defaults reproduce the llama3b series exactly.
GRADE_MODEL = os.getenv("GRADE_MODEL", LLM_MODEL)          # e.g. qwen3:8b
GRADE_MODE = os.getenv("GRADE_MODE", "per_passage")         # per_passage | single | escalate
# escalate: per_passage with LLM_MODEL first; if it keeps nothing, one single-call grade with GRADE_MODEL as a second opinion
GRADE_PASSAGE_CHARS = int(os.getenv("GRADE_PASSAGE_CHARS", "900"))
GRADE_MAX_TOKENS = int(os.getenv("GRADE_MAX_TOKENS", "15"))  # qwen3 needs ~600 for its hidden reasoning
EMBED_DIM = 768
TOP_K = 6
# step 20: exclude superseded document versions in the vector query, before ranking. OFF/ON ablation switch.
VERSION_AWARE = os.getenv("VERSION_AWARE", "1") == "1"   # default ON since step 20g (ablation recorded); 0 = ablation OFF setting
