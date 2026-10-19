"""Step 20 retrieval-only ablation: the same frozen document cases with the version filter OFF and ON.
No LLM, no judge: deterministic, seconds not minutes.

    .venv/bin/python b1_eval.py               # OFF and ON, writes results/version_filter_{off,on}.json + ablation_summary.md
    .venv/bin/python b1_eval.py --latency 5   # also time OFF and ON interleaved, 5 rounds (fair: same process, warm)

Scoring per case (retrieved text = the k chunks joined):
  superseded rate   = superseded chunks / all chunks retrieved (headline; target 0% ON)
  version-trap case = has must_not_contain: passes when every fact is in the text AND no stale value is
  control case      = no must_not_contain: passes when every fact is in the text (must stay flat OFF -> ON)
Unanswerable cases are retrieval-unscorable and skipped (answer-level eval.py covers them).
"""
import argparse
import json
import statistics as st
import time
from pathlib import Path

import ragcap.graph as g
from ragcap.config import EMBED_MODEL, TOP_K
from ragcap.db import connect

GOLDEN = ["golden/golden.jsonl", "golden/golden_heldout.jsonl"]


def cases():
    out = []
    for f in GOLDEN:
        for l in Path(f).read_text().splitlines():
            c = json.loads(l)
            if c["route"] == "documents" and c["type"] != "unanswerable":
                out.append(c)
    amend = Path("golden/amendments.jsonl")
    if amend.exists():
        am = {a["id"]: a for a in (json.loads(l) for l in amend.read_text().splitlines() if l.strip())}
        for c in out:
            if c["id"] in am:
                c["facts"] = am[c["id"]]["facts"]
    return out


def has(text, fact):
    return any(alt.strip().lower() in text.lower() for alt in fact.split("|"))


def run(on: bool, cs):
    rows, sup, tot = [], 0, 0
    for c in cs:
        r = g.retrieve({"standalone": c["question"], "version_aware": on, "trace": []})
        ch = r["chunks"]
        text = " ".join(x["text"] for x in ch)
        sup += sum(1 for x in ch if x["superseded"]); tot += len(ch)
        facts_ok = all(has(text, f) for f in c["facts"])
        stale = [s for s in c["must_not_contain"] if s.lower() in text.lower()]
        rows.append({"id": c["id"], "trap": bool(c["must_not_contain"]), "facts_in_context": facts_ok,
                     "stale_in_context": stale, "pass": facts_ok and not stale,
                     "retrieved": [f"{x['doc']} v{x['version']}{' OLD' if x['superseded'] else ''}" for x in ch],
                     "ms": r["trace"][-1]["ms"]})
    trap = [r for r in rows if r["trap"]]; ctrl = [r for r in rows if not r["trap"]]
    m = {"version_aware": on, "cases": len(rows), "k": TOP_K, "embed_model": EMBED_MODEL,
         "superseded_chunks": sup, "chunks_total": tot, "superseded_rate": sup / tot if tot else None,
         "trap_cases": len(trap), "trap_pass": sum(r["pass"] for r in trap),
         "trap_stale_in_context": sum(bool(r["stale_in_context"]) for r in trap),
         "control_cases": len(ctrl), "control_pass": sum(r["pass"] for r in ctrl),
         "median_ms_single_pass": st.median(r["ms"] for r in rows)}
    return m, rows


def latency(cs, rounds):
    """Interleave OFF and ON for the same questions in one process, after a warm-up: cold start cannot favour either."""
    g.retrieve({"standalone": cs[0]["question"], "version_aware": False, "trace": []})
    ms = {False: [], True: []}
    for _ in range(rounds):
        for c in cs:
            for on in (False, True):
                ms[on].append(g.retrieve({"standalone": c["question"], "version_aware": on, "trace": []})["trace"][-1]["ms"])
    return {"rounds": rounds, "calls_each": len(ms[False]), "off_median_ms": st.median(ms[False]), "on_median_ms": st.median(ms[True])}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--latency", type=int, default=0, help="interleaved OFF/ON timing rounds")
    a = ap.parse_args()
    cs = cases()
    conn = connect()
    nd, nc = conn.execute("SELECT count(*) FROM documents").fetchone()[0], conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
    Path("results").mkdir(exist_ok=True)
    res = {}
    for on in (False, True):
        m, rows = run(on, cs)
        res[on] = m
        Path(f"results/version_filter_{'on' if on else 'off'}.json").write_text(json.dumps({"metrics": m, "rows": rows}, indent=1))
        print(f"{'ON ' if on else 'OFF'}: superseded {m['superseded_chunks']}/{m['chunks_total']} ({m['superseded_rate']:.1%}) | "
              f"trap {m['trap_pass']}/{m['trap_cases']} (stale in context {m['trap_stale_in_context']}) | control {m['control_pass']}/{m['control_cases']}")
    lat = latency(cs, a.latency) if a.latency else None
    o, n = res[False], res[True]
    md = [f"# Version filter ablation (retrieval only)", "",
          f"Corpus: {nd} documents, {nc} chunks in Postgres/pgvector; embed model {EMBED_MODEL}; k={TOP_K}; "
          f"{len(cs)} frozen document cases from {', '.join(GOLDEN)} ({o['trap_cases']} version-trap, {o['control_cases']} control). "
          f"Generated {time.strftime('%Y-%m-%d %H:%M')}.", "",
          "| Metric | Filter OFF | Filter ON |", "|---|---|---|",
          f"| Superseded chunks retrieved | {o['superseded_chunks']}/{o['chunks_total']} ({o['superseded_rate']:.1%}) | {n['superseded_chunks']}/{n['chunks_total']} ({n['superseded_rate']:.1%}) |",
          f"| Version-trap cases passing (facts present, stale value absent) | {o['trap_pass']}/{o['trap_cases']} | {n['trap_pass']}/{n['trap_cases']} |",
          f"| Version-trap cases with the stale value in context | {o['trap_stale_in_context']}/{o['trap_cases']} | {n['trap_stale_in_context']}/{n['trap_cases']} |",
          f"| Control cases passing (must stay flat) | {o['control_pass']}/{o['control_cases']} | {n['control_pass']}/{n['control_cases']} |",
          f"| Median retrieve ms, single pass (cold-start biased) | {o['median_ms_single_pass']} | {n['median_ms_single_pass']} |"]
    if lat:
        md.append(f"| Median retrieve ms, interleaved x{lat['rounds']} ({lat['calls_each']} calls each) | {lat['off_median_ms']} | {lat['on_median_ms']} |")
    md += ["", "Limits: retrieval only (no LLM); unanswerable cases unscored; a document may be more than one chunk, "
           "so chunk counts can exceed document counts; cases with no stale value listed can only test that facts are still found."]
    Path("results/ablation_summary.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[4:]))
    if lat:
        print("latency:", lat)
