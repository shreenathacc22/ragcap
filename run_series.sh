#!/bin/bash
# Usage: ./run_series.sh <label> <model>  -- 3x held-out, 2x original (run 3 already exists for original)
cd "$(dirname "$0")"
export LLM_MODEL="${2:-llama3.2:3b}"
L="$1"
for i in 1 2 3; do .venv/bin/python eval.py --golden golden/golden_heldout.jsonl --tag "${L}_heldout_r$i" > "results/${L}_heldout_r$i.log" 2>&1; done
for i in 1 2; do .venv/bin/python eval.py --tag "${L}_orig_r$i" > "results/${L}_orig_r$i.log" 2>&1; done
echo done > "results/${L}_series.done"
