# ragcap: project status

Last updated 2026-10-21. Repo: https://github.com/shreenathacc22/ragcap · Live site: https://shreenathacc22.github.io/ragcap/

All 25 steps in scope are done and documented. The SOP (`docs/SOP_ragcap_build.pdf`) has the evidence for each one.

## Completed

| Area | What's done |
|---|---|
| Build (steps 1–8) | Postgres 16 + pgvector in Docker, ingestion (Markdown/PDF chunks, CSV/Excel to SQL tables), the LangGraph pipeline (router, retrieve, grade, rewrite, generate, SQL agent, general), FastAPI, Gradio, a frozen 27-case golden set |
| Improvement (9–14) | Router, SQL and grader fixes. Answers 77.8% → 85–93% on the tuned set |
| Honest measurement (15–18) | 25 unseen questions frozen before their first run; repeated runs. Unseen set: router 96%, answers 80–84%, retrieval 100% |
| Negative result (19) | An 8B grader (qwen3:8b) was too slow on a 2019 Intel CPU. Recorded with evidence; the switch `GRADE_MODE=escalate` is in the code |
| Version filter (20) | Superseded document versions retrieved: 51.6% → 0.0%; control cases unchanged; +1 ms. On by default (`VERSION_AWARE=1`) |
| Close-out (21–25) | Both interfaces checked in a real browser; LangSmith opt-in; static web front end on the streaming `/chat` API (Next.js descoped); P&ID branch on synthetic drawings (36/39 tags read, 5/12 answers); showcase site on GitHub Pages |
| Docs | SOP (10 pages), runbook (5), recreate guide (7), 15-slide deck, `recreate.sh` one-command rebuild with fingerprint checks, `docs/APPLE_SILICON.md` |

## Pending

| Item | Why not done | What's needed |
|---|---|---|
| Vercel deployment | Vercel login is an interactive browser step | vercel.com → sign in with GitHub → Add New → Project → import `shreenathacc22/ragcap` → Framework "Other", Output Directory `site` → Deploy (about 3 minutes; slide 13, SOP step 25). Then paste the URL into README.md and `site/index.html` and run `./publish_site.sh` |
| LangSmith tracing | Needs an API key | `.env`: `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY=...`, `LANGSMITH_PROJECT=ragcap` |
| Stronger grader | 8B model too slow on the Intel Mac | Apple Silicon or a GPU: see `docs/APPLE_SILICON.md` section 4 |
| Real P&ID drawings | Real drawings are confidential; needs a bigger vision model | A drawing set, its own golden questions (template: `pid/golden_pid.jsonl`), qwen2.5vl:7b or larger |
| Docling (layout-aware PDF parsing) | Cannot run on Intel macOS (torch 2.2.2 cap) | Works on Apple Silicon: `docs/APPLE_SILICON.md` section 5 |
| Optional ideas, not started | — | SQL retry on empty or implausible results; split multi-part questions before retrieval |
