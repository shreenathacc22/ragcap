# Running ragcap on an Apple Silicon Mac (M1–M4, Pro/Max)

Written for: running this project on an Apple Silicon Mac for the first time. Everything was built on a 2019 Intel MacBook Pro; Apple Silicon is faster and removes two limits found there (8B models too slow, Docling unable to run). Time: about 30 minutes plus model downloads.

## 1. Install the prerequisites

```bash
# Homebrew (skip if `brew --version` works)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install python@3.12 git gh
brew install --cask docker ollama          # Docker Desktop and Ollama, both native arm64
open -a Docker && open -a Ollama           # start both; wait until `docker info` works

ollama pull llama3.2:3b                    # the LLM all results were recorded with
ollama pull nomic-embed-text               # embeddings (768 dimensions; must not change)
```

Check: `python3.12 --version` prints 3.12.x, `docker info` prints a server version, `ollama list` shows both models.

## 2. Clone and rebuild with one command

```bash
git clone https://github.com/shreenathacc22/ragcap && cd ragcap
PY=$(command -v python3.12) ./recreate.sh
```

`recreate.sh` keeps the Mac awake (`caffeinate`), creates `.env` with a random database password, starts Postgres + pgvector (`pgvector/pgvector:pg16` has a native arm64 image), builds `.venv`, ingests the 16 versioned runbooks and the broker table, runs the data checks, verifies the fingerprints, runs the version-filter ablation and three smoke questions. It ends with `RECREATE OK`, or stops with `FAIL: <reason>`.

Expected on Apple Silicon:

| Check | Expected |
|---|---|
| Counts | `16 docs, 16 chunks, 8 superseded, 1 tables` |
| Golden and corpus sha1 | match (plain text files) |
| Ablation headline | OFF `99/192 (51.6%)` → ON `0/192 (0.0%)`; control 20/20 |
| P&ID drawings sha1 | may differ: the PNGs depend on the Pillow version and the system font renderer. If only this line fails, the pipeline is fine; regenerate with `.venv/bin/python pid/make_pid.py` and update the value in `recreate.sh` |
| Latency | much lower than the Intel numbers (Intel: ~17–30 s per document question); compare OFF vs ON only on the same machine |

## 3. Use it

```bash
.venv/bin/uvicorn api:app --port 8000        # browser: http://127.0.0.1:8000/
.venv/bin/python ui.py                       # Gradio: http://127.0.0.1:7860
.venv/bin/python try.py "Which brokers are above 85% disk usage?"
VERSION_AWARE=0 .venv/bin/python try.py "At what disk utilisation should a broker page?"   # the trap: may say 85%
.venv/bin/python try.py "At what disk utilisation should a broker page?"                   # the fix: 75%
```

The scenario catalogue (`docs/RECREATE.md`, section 3) lists 18 questions with expected routes and answers.

## 4. What Apple Silicon makes possible (the pending items)

Run each experiment against the same frozen sets so it is comparable with the recorded results, and record it in the SOP as a new step.

**Stronger grader** (expected to fix the 3 held-out failures that the 3B grader causes):

```bash
ollama pull qwen3:8b
GRADE_MODEL=qwen3:8b GRADE_MODE=escalate GRADE_MAX_TOKENS=600 ./run_series.sh qwen3esc llama3.2:3b
.venv/bin/python summarize_series.py qwen3esc        # compare with results/llama3b_summary.md
```

**Bigger answering model** (all nodes):

```bash
ollama pull llama3.1:8b
./run_series.sh llama8b llama3.1:8b && .venv/bin/python summarize_series.py llama8b
```

**Bigger vision model for the P&ID branch**:

```bash
ollama pull qwen2.5vl:7b
VISION_MODEL=qwen2.5vl:7b .venv/bin/python pid_eval.py --ingest      # compare with results/pid_eval_summary.md
```

## 5. Docling (layout-aware PDF, Word, PowerPoint parsing)

Blocked on Intel; on Apple Silicon current torch wheels exist. Test in a separate venv first so the main one stays clean:

```bash
python3.12 -m venv .venv-docling && .venv-docling/bin/pip install docling
.venv-docling/bin/python tools/docling_convert.py some.pdf > some.md    # Markdown on stdout
.venv/bin/python -m ragcap.ingest some.md
```

If that works, `pip install docling` into `.venv` makes `ragcap/ingest.py` use it automatically for `.pdf`, `.docx`, `.pptx` and `.html` (it falls back to pypdf only when Docling is not importable).

## 6. Differences from the Intel Mac to keep in mind

- Results were recorded with llama3.2:3b on Intel. Same model on Apple Silicon should give the same routes and very similar answers; small run-to-run differences are normal for a 3B model (report ranges, as the SOP does).
- The Mac still sleeps: long scripts already run under `caffeinate`; for interactive work keep `caffeinate -d -i -t 14400 &` running, or Docker Desktop may stop on wake.
- Never commit `.env`. The database password is fixed when the Docker volume is first created; if you lose `.env`, run `docker rm -f ragcap-pg && docker volume rm ragcap_pgdata` and re-run `recreate.sh`.
- Vercel and LangSmith are machine-independent; see `STATUS.md`.
