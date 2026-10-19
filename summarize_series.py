"""Aggregate repeated eval runs: python summarize_series.py <label> [<label2> ...]
Reads results/<label>_heldout_r*.json and results/<label>_orig_r*.json (plus the earlier eval_*.json runs for the
original set when label == llama3b) and prints mean / min / max per metric, the per-flow table averaged over runs,
and which case ids failed in how many runs. Writes results/<label>_summary.md."""
import glob
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

P_IN, P_OUT = 0.40 / 1e6, 1.60 / 1e6


def load(pattern):
    return [json.load(open(f)) for f in sorted(glob.glob(pattern))]


def agg(runs, name):
    if not runs:
        return [f"### {name}: no runs"]
    lines = [f"### {name} ({len(runs)} runs)", "", "| Metric | Mean | Min | Max |", "|---|---|---|---|"]
    for k in ("router_accuracy", "answer_correct", "retrieval_hit_rate_doc"):
        v = [r["metrics"][k] for r in runs if r["metrics"].get(k) is not None]
        if v:
            lines.append(f"| {k} | {st.mean(v):.1%} | {min(v):.1%} | {max(v):.1%} |")
    errs = [r["metrics"].get("errors", 0) for r in runs]
    lines.append(f"| errors (cases hitting an exception) | {st.mean(errs):.1f} | {min(errs)} | {max(errs)} |")
    # by type, mean of fraction
    bt = defaultdict(list)
    for r in runs:
        for t, frac in r["metrics"]["answer_correct_by_type"].items():
            a, b = frac.split("/")
            bt[t].append(int(a) / int(b))
    lines += ["", "| Type | Mean correct | Range |", "|---|---|---|"]
    for t, v in bt.items():
        lines.append(f"| {t} | {st.mean(v):.0%} | {min(v):.0%} - {max(v):.0%} |")
    # failures by case id
    fails = Counter()
    for r in runs:
        for row in r["rows"]:
            if not (row["route_ok"] and row["answer_ok"]):
                fails[row["id"]] += 1
    lines += ["", f"Failing case ids (times failed out of {len(runs)}): " +
              (", ".join(f"{k} x{v}" for k, v in sorted(fails.items(), key=lambda x: -x[1])) or "none")]
    # per-flow averaged over all rows of all runs
    flows = defaultdict(list)
    for r in runs:
        for row in r["rows"]:
            flows[row["flow"]].append(row)
    lines += ["", "| Flow | Answers (all runs) | Avg LLM calls | Tokens in / out | Avg latency | Equiv. cost |", "|---|---|---|---|---|---|"]
    for f, rows in flows.items():
        tin, tout = st.mean(x["tin"] for x in rows), st.mean(x["tout"] for x in rows)
        lines.append(f"| {f} | {len(rows)} | {st.mean(x['calls'] for x in rows):.1f} | {tin:.0f} / {tout:.0f} | "
                     f"{st.mean(x['total_ms'] for x in rows) / 1000:.1f} s | ${tin * P_IN + tout * P_OUT:.5f} |")
    return lines


for label in sys.argv[1:]:
    held = load(f"results/{label}_heldout_r*.json")
    orig = load(f"results/{label}_orig_r*.json")
    if label == "llama3b":   # runs 2 and 3 from the tuning phase used the same code except the hardening commit
        orig = load("results/eval_20261018_20*.json") + orig
    out = [f"# Series summary: {label}", ""] + agg(held, "Held-out set (25 unseen cases)") + [""] + agg(orig, "Original set (27 cases, tuned on)")
    Path(f"results/{label}_summary.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))
