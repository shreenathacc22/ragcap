#!/bin/bash
# Answer-level OFF/ON on the original golden set (27 cases, LLM in the loop). ~20 min each on this CPU.
if [ -z "$CAFFEINATED" ]; then CAFFEINATED=1 exec caffeinate -i "$0" "$@"; fi
cd "$(dirname "$0")"
docker exec ragcap-pg pg_isready -q -U ragcap -d ragcap || { echo "Postgres not ready" >&2; exit 1; }
curl -sf localhost:11434/api/tags >/dev/null || { echo "Ollama not running" >&2; exit 1; }
rm -f results/answer_ablation.done
VERSION_AWARE=0 .venv/bin/python eval.py --tag answer_off > results/answer_off.log 2>&1
VERSION_AWARE=1 .venv/bin/python eval.py --tag answer_on  > results/answer_on.log  2>&1
echo done > results/answer_ablation.done
