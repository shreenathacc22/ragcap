#!/bin/bash
# Usage: ./run_series.sh <label> <model>  -- 3x held-out, 2x original (run 3 already exists for original)
cd "$(dirname "$0")"
export LLM_MODEL="${2:-llama3.2:3b}"
L="$1"
N_HELD="${N_HELD:-3}"; N_ORIG="${N_ORIG:-2}"     # override for slow models, e.g. N_HELD=1 N_ORIG=1
# pre-flight: both services must be up, or every run would fail on its first call
docker exec ragcap-pg pg_isready -q -U ragcap -d ragcap || { echo "Postgres container not ready: open -a Docker; docker start ragcap-pg" >&2; exit 1; }
curl -sf localhost:11434/api/tags >/dev/null || { echo "Ollama not running: open -a Ollama" >&2; exit 1; }
rm -f "results/${L}_series.done"
for i in $(seq 1 "$N_HELD"); do .venv/bin/python eval.py --golden golden/golden_heldout.jsonl --tag "${L}_heldout_r$i" > "results/${L}_heldout_r$i.log" 2>&1; done
for i in $(seq 1 "$N_ORIG"); do .venv/bin/python eval.py --tag "${L}_orig_r$i" > "results/${L}_orig_r$i.log" 2>&1; done
echo done > "results/${L}_series.done"
