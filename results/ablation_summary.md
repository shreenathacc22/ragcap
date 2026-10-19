# Version filter ablation (retrieval only)

Corpus: 16 documents, 16 chunks in Postgres/pgvector; embed model nomic-embed-text; k=6; 32 frozen document cases from golden/golden.jsonl, golden/golden_heldout.jsonl (12 version-trap, 20 control). Generated 2026-10-19 07:49.

| Metric | Filter OFF | Filter ON |
|---|---|---|
| Superseded chunks retrieved (headline) | 99/192 (51.6%) | 0/192 (0.0%) |
| Version-trap cases passing (facts present, no stale value from a superseded chunk) | 2/12 | 12/12 |
| Version-trap cases with the stale value arriving from a superseded chunk | 10/12 | 0/12 |
| Version-trap cases with the stale string anywhere in context (strict; the current runbook may quote its former value) | 10/12 | 6/12 |
| Control cases passing (must stay flat) | 20/20 | 20/20 |
| Median retrieve ms, single pass (cold-start biased) | 64.0 | 63.5 |
| Median retrieve ms, interleaved x3 (96 calls each, fair) | 64.0 | 65.0 |

Limits: retrieval only (no LLM); unanswerable cases unscored; a document may be more than one chunk, so chunk counts can exceed document counts; cases with no stale value listed can only test that facts are still found; the strict row counts the current document's own mention of its former value, which only the answer-level run can judge.
