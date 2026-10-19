# Series summary: llama3b

### Held-out set (25 unseen cases) (3 runs)

| Metric | Mean | Min | Max |
|---|---|---|---|
| router_accuracy | 96.0% | 96.0% | 96.0% |
| answer_correct | 81.3% | 80.0% | 84.0% |
| retrieval_hit_rate_doc | 100.0% | 100.0% | 100.0% |
| errors (cases hitting an exception) | 0.0 | 0 | 0 |

| Type | Mean correct | Range |
|---|---|---|
| version_current | 77% | 75% - 81% |
| sql | 80% | 80% - 80% |
| general | 100% | 100% - 100% |
| unanswerable | 100% | 100% - 100% |

Failing case ids (times failed out of 3): h-doc-05 x3, h-doc-08 x3, h-doc-15 x3, h-db-01 x3, h-doc-04 x2

| Flow | Answers (all runs) | Avg LLM calls | Tokens in / out | Avg latency | Equiv. cost |
|---|---|---|---|---|---|
| document+rewrite | 25 | 14.5 | 3743 / 158 | 26.3 s | $0.00175 |
| document | 32 | 8.0 | 2392 / 90 | 17.1 s | $0.00110 |
| database | 12 | 3.0 | 766 / 87 | 10.5 s | $0.00045 |
| general | 6 | 2.0 | 427 / 35 | 3.4 s | $0.00023 |

### Original set (27 cases, tuned on) (4 runs)

| Metric | Mean | Min | Max |
|---|---|---|---|
| router_accuracy | 100.0% | 100.0% | 100.0% |
| answer_correct | 88.9% | 85.2% | 92.6% |
| retrieval_hit_rate_doc | 100.0% | 100.0% | 100.0% |
| errors (cases hitting an exception) | 0.0 | 0 | 0 |

| Type | Mean correct | Range |
|---|---|---|
| version_current | 91% | 88% - 100% |
| exact_string | 88% | 67% - 100% |
| multi_hop | 62% | 50% - 100% |
| sql | 88% | 83% - 100% |
| general | 100% | 100% - 100% |
| unanswerable | 100% | 100% - 100% |

Failing case ids (times failed out of 4): doc-004 x3, doc-015 x3, db-004 x3, doc-009 x1, doc-011 x1, doc-014 x1

| Flow | Answers (all runs) | Avg LLM calls | Tokens in / out | Avg latency | Equiv. cost |
|---|---|---|---|---|---|
| document | 62 | 6.5 | 2337 / 84 | 23.8 s | $0.00107 |
| database | 24 | 3.0 | 757 / 67 | 8.7 s | $0.00041 |
| general | 12 | 2.0 | 422 / 44 | 3.9 s | $0.00024 |
| document+rewrite | 10 | 14.3 | 3683 / 129 | 30.5 s | $0.00168 |
