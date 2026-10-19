## Metrics

- cases: 27
- router_accuracy: 0.8888888888888888
- answer_correct: 0.7777777777777778
- retrieval_hit_rate_doc: 0.8125
- answer_correct_by_type: {'version_current': '5/8', 'exact_string': '6/6', 'multi_hop': '1/2', 'sql': '4/6', 'general': '3/3', 'unanswerable': '2/2'}

## Per-flow

| Flow | Answers | Avg LLM calls | Tokens in / out | Avg latency | Equiv. cost / question |
|---|---|---|---|---|---|
| document | 15 | 3.0 | 2044 / 66 | 37.8 s | $0.00092 |
| general | 4 | 2.0 | 230 / 44 | 4.1 s | $0.00016 |
| database | 8 | 3.0 | 465 / 76 | 9.5 s | $0.00031 |
