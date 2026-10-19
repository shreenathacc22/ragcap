"""Rebuild site/data/replay.json from the recorded evaluation results (no model calls)."""
import glob, json
from pathlib import Path
HERE = Path(__file__).parent; R = HERE.parent / "results"
def latest(p): return json.load(open(sorted(glob.glob(str(R / p)))[-1]))
gold = {json.loads(l)["id"]: json.loads(l) for f in ["golden/golden.jsonl", "golden/golden_heldout.jsonl"]
        for l in (HERE.parent / f).read_text().splitlines()}
on = latest("answer_on_2*.json"); held = latest("llama3b_heldout_r1_2*.json"); pid = latest("pid_eval_2*.json")
voff = {r["id"]: r for r in latest("version_filter_off.json")["rows"]}; von = {r["id"]: r for r in latest("version_filter_on.json")["rows"]}
def rec(r, src):
    g = gold.get(r["id"], {})
    return {"id": r["id"], "set": src, "type": r.get("type"), "question": g.get("question") or r.get("question"), "route": r["route"],
            "nodes": [{"node": t["node"], "ms": t["ms"]} for t in r.get("trace", [])], "total_ms": r.get("total_ms"),
            "answer": r["answer"], "sql": r.get("sql"), "ok": bool(r.get("answer_ok", r.get("pass"))),
            "retrieved_off": voff.get(r["id"], {}).get("retrieved"), "retrieved_on": von.get(r["id"], {}).get("retrieved")}
runs = [rec(r, "tuned set, filter ON") for r in on["rows"]] + [rec(r, "held-out set") for r in held["rows"]] + [rec(r, "P&ID branch") for r in pid["rows"]]
out = HERE / "data" / "replay.json"
out.write_text(json.dumps({"generated": "2026-10-19", "model": "llama3.2:3b (vision: qwen2.5vl:3b)", "runs": runs}, indent=0))
print(len(runs), "recorded runs ->", out, f"{out.stat().st_size // 1024} KB")
