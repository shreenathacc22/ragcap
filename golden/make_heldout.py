"""Builds golden/golden_heldout.jsonl: 25 cases written from the runbooks AFTER prompt tuning on golden.jsonl.
Rule: never tune prompts against these; freeze in git before the first run."""
import json
from pathlib import Path

D = lambda i, q, f, n=(): {"id": f"h-doc-{i:02d}", "route": "documents", "type": "version_current", "question": q, "facts": f, "must_not_contain": list(n)}
S = lambda i, q, f: {"id": f"h-db-{i:02d}", "route": "database", "type": "sql", "question": q, "facts": f, "must_not_contain": []}
cases = [
    D(1, "How long is a broker TLS certificate valid?", ["90 days"]),
    D(2, "Which min.insync.replicas value goes with production topics?", ["2"]),
    D(3, "What casing must topic names use, and are hyphens allowed?", ["lowercase"]),
    D(4, "How long do audit topics keep their messages?", ["90 days"]),
    D(5, "How many minutes must consumer lag stay high before the alert fires?", ["5 minutes"]),
    D(6, "How much downtime should I expect when restarting one broker?", ["4 minutes"]),
    D(7, "Who is the secondary contact for a SEV-1 Kafka incident?", ["Infrastructure duty manager"]),
    D(8, "After how long without mitigation must a SEV-1 be escalated?", ["15 minutes"]),
    D(9, "Which template do I request for broker certificates?", ["kafka-broker-v2"]),
    D(10, "Do I need a full-cluster window to rotate certificates?", ["one at a time|one by one|individually"]),
    D(11, "At what disk percentage do we only warn instead of paging?", ["60%"]),
    D(12, "Which port does BROKER-EAST-02 use for plaintext traffic?", ["9092"]),
    D(13, "What rejects topics that still use the retired evt. prefix?", ["topic-admission|admission"]),
    D(14, "Consumer lag is still climbing after I scaled the group. What now?", ["escalate"]),
    D(15, "What replication factor and what default retention apply to a new standard production topic?", ["3", "72"], ["168"]),
    D(16, "Which host issues TLS certificates, and which port does BROKER-EAST-02 use for TLS?", ["pki.internal.example.com", "9093"], ["certs.internal.example.com is the"]),
    S(1, "What is the highest disk usage percentage and which broker has it?", ["91.8", "5"]),
    S(2, "How many brokers host more than 150 topics?", ["3|three"]),
    S(3, "List the brokers in rack-c.", ["5", "6"]),
    S(4, "What is the combined number of topics across all brokers?", ["880"]),
    S(5, "How many brokers have at least 4000 GB of disk?", ["2|two"]),
    {"id": "h-gen-01", "route": "general", "type": "general", "question": "Good morning!", "facts": [], "must_not_contain": []},
    {"id": "h-gen-02", "route": "general", "type": "general", "question": "Who are you?", "facts": [], "must_not_contain": []},
    {"id": "h-una-01", "route": "documents", "type": "unanswerable", "question": "How many partitions should a new topic have?", "facts": [], "must_not_contain": []},
    {"id": "h-una-02", "route": "documents", "type": "unanswerable", "question": "Which cloud provider hosts the Kafka cluster?", "facts": [], "must_not_contain": []},
]
out = Path(__file__).with_name("golden_heldout.jsonl")
out.write_text("\n".join(json.dumps(c) for c in cases) + "\n")
print(len(cases), "cases ->", out)
