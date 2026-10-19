"""Run golden/golden.jsonl through the graph and report quality + per-flow latency/tokens.
Equivalent cost uses gpt-4.1-mini list prices ($0.40/M in, $1.60/M out) so numbers compare with Kumar's table; the local model costs $0."""
import json
import re
import statistics as st
import sys
import time
from collections import defaultdict
from pathlib import Path

from ragcap.config import LLM_MODEL, VERSION_AWARE
from ragcap.graph import ask

P_IN, P_OUT = 0.40 / 1e6, 1.60 / 1e6
REFUSAL = re.compile(r"not in the knowledge base|not mentioned|does not (contain|mention|specify)|do not (contain|mention)|cannot (find|answer)|no information|not (provided|available)", re.I)


def has(text: str, fact: str) -> bool:
    return any(alt.strip().lower() in text.lower() for alt in fact.split("|"))


def flow_of(o):
    if o["route"] == "documents":
        return "document+rewrite" if o.get("rewrites") else "document"
    return o["route"]


def main(limit=None, golden="golden/golden.jsonl", tag="eval"):
    cases = [json.loads(l) for l in Path(golden).read_text().splitlines()]
    amend = {a["id"]: a for a in (json.loads(l) for l in Path("golden/amendments.jsonl").read_text().splitlines() if l.strip())} \
        if Path("golden/amendments.jsonl").exists() else {}
    for c in cases:
        if c["id"] in amend:
            c["facts"] = amend[c["id"]]["facts"]
            print(f"amended {c['id']}: {amend[c['id']]['reason'][:70]}...")
    cases = cases[:limit]
    rows = []
    for c in cases:
        try:
            o = ask(c["question"])
        except Exception as e:  # noqa: BLE001 — one broken case must not kill a 20-minute run
            o = {"answer": f"ERROR: {type(e).__name__}: {str(e)[:120]}", "route": "error", "rewrites": 0, "total_ms": 0,
                 "trace": [{"node": "error", "ms": 0, "llm_calls": 0, "tokens_in": 0, "tokens_out": 0}], "chunks": []}
        ans = o["answer"]
        r = {"id": c["id"], "type": c["type"], "expected_route": c["route"], "route": o["route"], "flow": flow_of(o),
             "route_ok": o["route"] == c["route"], "answer": ans, "total_ms": o["total_ms"],
             "calls": sum(t["llm_calls"] for t in o["trace"]), "tin": sum(t["tokens_in"] for t in o["trace"]),
             "tout": sum(t["tokens_out"] for t in o["trace"]), "trace": o["trace"]}
        if c["route"] == "documents" and c["type"] != "unanswerable":
            texts = " ".join(ch["text"] for ch in o.get("chunks", []))
            r["retrieval_hit"] = all(has(texts, f) for f in c["facts"])
            r["answer_ok"] = all(has(ans, f) for f in c["facts"]) and not any(n.lower() in ans.lower() for n in c["must_not_contain"])
        elif c["type"] == "unanswerable":
            r["answer_ok"] = bool(REFUSAL.search(ans))
        elif c["type"] == "sql":
            r["answer_ok"] = all(has(ans, f) for f in c["facts"]); r["sql"] = o.get("sql")
        else:
            r["answer_ok"] = o["route"] == "general"
        rows.append(r)
        print(f"{c['id']:8} route={'ok ' if r['route_ok'] else 'BAD'} answer={'ok ' if r['answer_ok'] else 'BAD'} {r['total_ms']}ms", flush=True)

    n = len(rows)
    m = {"cases": n, "model": LLM_MODEL, "version_aware": VERSION_AWARE, "errors": sum(r["route"] == "error" for r in rows),
         "router_accuracy": sum(r["route_ok"] for r in rows) / n,
         "answer_correct": sum(r["answer_ok"] for r in rows) / n}
    doc = [r for r in rows if "retrieval_hit" in r]
    m["retrieval_hit_rate_doc"] = sum(r["retrieval_hit"] for r in doc) / len(doc) if doc else None
    by_type = defaultdict(list)
    for r in rows:
        by_type[r["type"]].append(r["answer_ok"])
    m["answer_correct_by_type"] = {k: f"{sum(v)}/{len(v)}" for k, v in by_type.items()}
    flows = defaultdict(list)
    for r in rows:
        flows[r["flow"]].append(r)
    table = ["| Flow | Answers | Avg LLM calls | Tokens in / out | Avg latency | Equiv. cost / question |", "|---|---|---|---|---|---|"]
    for f, rs in flows.items():
        tin, tout = st.mean(r["tin"] for r in rs), st.mean(r["tout"] for r in rs)
        table.append(f"| {f} | {len(rs)} | {st.mean(r['calls'] for r in rs):.1f} | {tin:.0f} / {tout:.0f} | "
                     f"{st.mean(r['total_ms'] for r in rs) / 1000:.1f} s | ${tin * P_IN + tout * P_OUT:.5f} |")
    out = Path("results") / f"{tag}_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps({"metrics": m, "rows": rows}, indent=1))
    md = "## Metrics\n\n" + "\n".join(f"- {k}: {v}" for k, v in m.items()) + "\n\n## Per-flow\n\n" + "\n".join(table) + "\n"
    out.with_suffix(".md").write_text(md)
    print("\n" + md, "\nsaved", out)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("limit", nargs="?", type=int)
    ap.add_argument("--golden", default="golden/golden.jsonl")
    ap.add_argument("--tag", default="eval")
    a = ap.parse_args()
    main(a.limit, a.golden, a.tag)
