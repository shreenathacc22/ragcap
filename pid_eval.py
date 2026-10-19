"""Step 24 evaluation of the P&ID branch.

    .venv/bin/python pid_eval.py --ingest     # describe the 3 drawings with the vision model (~100 s each), then evaluate
    .venv/bin/python pid_eval.py              # evaluate only (drawings already in the index)

Two scores. (1) Tag extraction: tags in each drawing's description vs ground_truth.json (correct / invented / missed).
(2) Question answering: the 12 frozen questions in pid/golden_pid.jsonl through the full graph; a case passes when
every fact is in the answer and no must_not_contain string is; also whether the right drawing's chunk was retrieved.
Writes results/pid_eval_<ts>.json and .md. No prompt was changed after seeing these results.
"""
import argparse
import json
import re
import time
from pathlib import Path

from ragcap.db import connect
from ragcap.graph import ask

TAG = re.compile(r"\b(?:P&ID-\d{3}|[A-Z]{1,3}-\d{3})\b")


def has(text, fact):
    return any(alt.strip().lower() in text.lower() for alt in fact.split("|"))


def ingest():
    from ragcap.ingest import ingest_path
    res = ingest_path(Path("pid/drawings"))
    Path("results/pid_ingest.json").write_text(json.dumps(res, indent=1))
    for r in res:
        print(r)
    return res


def tag_scores(gt):
    conn = connect()
    out = []
    for g in gt:
        name = g["file"][:-4]
        rows = conn.execute("SELECT c.text FROM chunks c JOIN documents d ON d.id=c.doc_id WHERE d.name=%s ORDER BY c.chunk_no", (name,)).fetchall()
        text = " ".join(r[0] for r in rows)
        expected = {e["tag"] for e in g["equipment"]} | {v["tag"] for v in g["valves"]} | {i["tag"] for i in g["instruments"]} | {g["drawing"]}
        found = set(TAG.findall(text))
        out.append({"drawing": g["drawing"], "expected": len(expected), "correct": len(found & expected),
                    "invented": sorted(found - expected), "missed": sorted(expected - found), "description_chars": len(text)})
    return out


def qa(cases):
    rows = []
    for c in cases:
        o = ask(c["question"])
        ans = o["answer"]
        want = c["drawing"].replace("P&ID-", "PID-")
        rows.append({"id": c["id"], "kind": c["id"][-1], "question": c["question"], "route": o["route"],
                     "right_drawing_retrieved": any(ch["doc"] == want for ch in o.get("chunks", [])),
                     "pass": all(has(ans, f) for f in c["facts"]) and not any(n.lower() in ans.lower() for n in c["must_not_contain"]),
                     "answer": ans[:300], "total_ms": o["total_ms"]})
        print(f"{c['id']} route={o['route']:9} drawing={'ok ' if rows[-1]['right_drawing_retrieved'] else 'BAD'} answer={'ok ' if rows[-1]['pass'] else 'BAD'} {o['total_ms']} ms")
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--ingest", action="store_true"); a = ap.parse_args()
    ing = ingest() if a.ingest else (json.loads(Path("results/pid_ingest.json").read_text()) if Path("results/pid_ingest.json").exists() else [])
    gt = json.load(open("pid/ground_truth.json"))
    cases = [json.loads(l) for l in Path("pid/golden_pid.jsonl").read_text().splitlines()]
    tags = tag_scores(gt)
    rows = qa(cases)
    n = len(rows)
    kinds = {"a": "valve isolating a pump", "b": "controller + control valve", "c": "what an instrument measures, on what", "d": "which drawing / unit"}
    by_kind = {kinds[k]: f"{sum(r['pass'] for r in rows if r['kind']==k)}/{sum(1 for r in rows if r['kind']==k)}" for k in kinds}
    m = {"vision_model": ing[0].get("vision_model", "qwen2.5vl:3b") if ing else "qwen2.5vl:3b",
         "vision_seconds_per_drawing": [r.get("vision_seconds") for r in ing] if ing else None,
         "tags": tags, "tag_correct_total": sum(t["correct"] for t in tags), "tag_expected_total": sum(t["expected"] for t in tags),
         "tag_invented_total": sum(len(t["invented"]) for t in tags),
         "qa_cases": n, "qa_route_documents": sum(r["route"] == "documents" for r in rows) / n,
         "qa_right_drawing_retrieved": sum(r["right_drawing_retrieved"] for r in rows) / n,
         "qa_answer_correct": sum(r["pass"] for r in rows) / n, "qa_by_kind": by_kind,
         "qa_mean_ms": sum(r["total_ms"] for r in rows) / n}
    ts = time.strftime("%Y%m%d_%H%M%S")
    Path(f"results/pid_eval_{ts}.json").write_text(json.dumps({"metrics": m, "rows": rows}, indent=1))
    md = ["# P&ID branch evaluation (step 24)", "",
          f"Vision model {m['vision_model']} on CPU; seconds per drawing: {m['vision_seconds_per_drawing']}.", "",
          "| Drawing | Tags expected | Correct | Invented | Missed |", "|---|---|---|---|---|"]
    md += [f"| {t['drawing']} | {t['expected']} | {t['correct']} | {', '.join(t['invented']) or '-'} | {', '.join(t['missed']) or '-'} |" for t in tags]
    md += ["", "| QA metric (12 frozen questions, full graph) | Result |", "|---|---|",
           f"| Routed to documents | {m['qa_route_documents']:.0%} |", f"| Right drawing retrieved | {m['qa_right_drawing_retrieved']:.0%} |",
           f"| Answer correct | {m['qa_answer_correct']:.0%} ({sum(r['pass'] for r in rows)}/{n}) |"]
    md += [f"| {k} | {v} |" for k, v in by_kind.items()] + [f"| Mean latency | {m['qa_mean_ms']/1000:.1f} s |"]
    Path("results/pid_eval_summary.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[2:]))
