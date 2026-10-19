"""Builds golden/golden.jsonl. Doc cases reuse Track A's b1 cases (current-version facts only); DB/general/unanswerable are new.
Fact strings may use '|' for accepted alternatives. Run once, then FREEZE the output in git before tuning anything."""
import json
from pathlib import Path

src = Path(__file__).resolve().parents[2] / ".." / "L2-RAG-B1-version-aware-retrieval/simple_rag/golden_b1.jsonl"
cases = []
for line in src.resolve().read_text().splitlines():
    d = json.loads(line)
    e = d["expect"]
    facts = e["facts"]
    if d["id"] == "b1-003":
        facts = ["drain"]
    cases.append({"id": d["id"].replace("b1-", "doc-"), "route": "documents", "type": d["type"], "question": d["question"],
                  "facts": facts, "must_not_contain": e["must_not_contain"]})

db = [
    ("db-001", "Which brokers are above 85% disk usage?", ["3", "5"], []),
    ("db-002", "How many brokers are in rack-b?", ["2|two"], []),
    ("db-003", "What is the total disk capacity across all brokers in GB?", ["16000|16,000"], []),
    ("db-004", "Which broker hosts the most topics, and how many?", ["5", "210"], []),
    ("db-005", "What is the average disk used percentage across brokers?", ["69.3|69.4"], []),
    ("db-006", "How many brokers have status healthy?", ["4|four"], []),
]
cases += [{"id": i, "route": "database", "type": "sql", "question": q, "facts": f, "must_not_contain": n} for i, q, f, n in db]
cases += [{"id": f"gen-00{i}", "route": "general", "type": "general", "question": q, "facts": [], "must_not_contain": []}
          for i, q in enumerate(["Hello!", "Thanks, that was helpful.", "What can you help me with?"], 1)]
cases += [{"id": f"una-00{i}", "route": "documents", "type": "unanswerable", "question": q, "facts": [], "must_not_contain": []}
          for i, q in enumerate(["What is the largest message size our brokers accept?",
                                 "What is our company's stock ticker symbol?"], 1)]
out = Path(__file__).with_name("golden.jsonl")
out.write_text("\n".join(json.dumps(c) for c in cases) + "\n")
print(len(cases), "cases ->", out)
