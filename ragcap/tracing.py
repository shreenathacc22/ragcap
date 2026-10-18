"""JSONL trace: one line per question with per-node timing and tokens. Optional LangSmith via env (LANGSMITH_TRACING=true)."""
import json
import time
from .config import ROOT

TRACE_FILE = ROOT / "traces.jsonl"


def log_run(out: dict) -> None:
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "question": out.get("question"), "route": out.get("route"),
           "rewrites": out.get("rewrites"), "sql_attempts": out.get("sql_attempts"), "total_ms": out.get("total_ms"),
           "tokens_in": sum(t["tokens_in"] for t in out["trace"]), "tokens_out": sum(t["tokens_out"] for t in out["trace"]),
           "llm_calls": sum(t["llm_calls"] for t in out["trace"]), "trace": out["trace"], "answer": out.get("answer")}
    with TRACE_FILE.open("a") as f:
        f.write(json.dumps(rec) + "\n")
