#!/bin/bash
# One-command rebuild and verification of ragcap. Usage: ./recreate.sh [--with-answer-eval]
# Follows docs/RECREATE.md sections 2.1-2.6 and checks the fingerprints in section 4. Exit 1 on any mismatch.
if [ -z "$CAFFEINATED" ]; then CAFFEINATED=1 exec caffeinate -i "$0" "$@"; fi
set -e
cd "$(dirname "$0")"
step() { printf '\n=== %s\n' "$1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

step "pre-flight"
docker info >/dev/null 2>&1 || fail "Docker Desktop not running (open -a Docker)"
curl -sf localhost:11434/api/tags >/dev/null || fail "Ollama not running (open -a Ollama)"
for m in llama3.2:3b nomic-embed-text; do ollama list | grep -q "^$m" || ollama pull "$m"; done

step "2.1 database"
if [ ! -f .env ]; then
  PW=$(openssl rand -hex 12)
  printf 'PGHOST=localhost\nPGPORT=5433\nPGUSER=ragcap\nPGPASSWORD=%s\nPGDATABASE=ragcap\n' "$PW" > .env; chmod 600 .env
fi
PGPASSWORD=$(sed -n 's/^PGPASSWORD=//p' .env)
if docker ps -a --format '{{.Names}}' | grep -qx ragcap-pg; then docker start ragcap-pg >/dev/null; sleep 3
else
  docker run -d --name ragcap-pg -e POSTGRES_USER=ragcap -e POSTGRES_PASSWORD="$PGPASSWORD" -e POSTGRES_DB=ragcap \
    -p 127.0.0.1:5433:5432 -v ragcap_pgdata:/var/lib/postgresql/data --restart unless-stopped pgvector/pgvector:pg16 >/dev/null
  sleep 8
fi
docker exec ragcap-pg pg_isready -q -U ragcap -d ragcap || fail "Postgres not ready"
docker exec ragcap-pg psql -U ragcap -d ragcap -qc "CREATE EXTENSION IF NOT EXISTS vector;"
echo "pgvector $(docker exec ragcap-pg psql -U ragcap -d ragcap -tAc "select extversion from pg_extension where extname='vector'")"

step "2.2 python env + schema"
if [ ! -x .venv/bin/python ]; then
  PY=${PY:-$(command -v python3.12 || echo ../../mai-practitioner-labs/.venv/bin/python)}
  "$PY" -m venv .venv
fi
.venv/bin/python --version | grep -q "3.12" || fail "venv is not Python 3.12 (set PY=<path to 3.12>)"
.venv/bin/pip install -q -r requirements.txt
.venv/bin/python step1_check.py | tail -1 | grep -q "STEP 1 OK" || fail "step1_check"

step "2.3 ingest"
docker exec ragcap-pg psql -U ragcap -d ragcap -qc "DELETE FROM documents"
.venv/bin/python -m ragcap.ingest data/docs_versioned | wc -l | xargs echo "documents ingested:"
.venv/bin/python -m ragcap.ingest data/tables
COUNTS=$(docker exec ragcap-pg psql -U ragcap -d ragcap -tAc "select (select count(*) from documents)||' docs, '||(select count(*) from chunks)||' chunks, '||(select count(*) from documents where superseded)||' superseded, '||(select count(*) from uploaded_tables)||' tables'")
echo "$COUNTS"; [ "$COUNTS" = "16 docs, 16 chunks, 8 superseded, 1 tables" ] || fail "counts differ from the fingerprint"

step "2.4 data checks"
.venv/bin/python b1_check.py --no-trap --negative | tail -4
.venv/bin/python b1_check.py | tail -2 | grep -q PASS || fail "b1_check"

step "4 fingerprints"
check_sha() { got=$(shasum "$1" | cut -c1-40); [ "$got" = "$2" ] && echo "match  $1" || fail "$1 sha1 $got != $2 (the frozen set was changed)"; }
check_sha golden/golden.jsonl         68ec09bdfcf99d62999ccfbe708f6f8ac3eaa4d3
check_sha golden/golden_heldout.jsonl 02ddcfd613d4784f59bdf8ad20df971b8c9db899
check_sha golden/amendments.jsonl     36a0e6e0d637a48ff43755fd579a1e7b9e80ecce
[ "$(cat data/docs_versioned/*.md | shasum | cut -c1-12)" = "c2b025608d03" ] && echo "match  corpus" || fail "corpus files differ"

step "2.6 retrieval ablation OFF/ON"
.venv/bin/python b1_eval.py --latency 3 | tail -3
grep -q "| 99/192 (51.6%) | 0/192 (0.0%) |" results/ablation_summary.md || fail "ablation headline differs from the fingerprint"
grep -q "| 2/12 | 12/12 |" results/ablation_summary.md || fail "trap-case row differs"

step "2.5 smoke, one question per route"
.venv/bin/python try.py "Thanks!" "How many brokers are in rack-b?" 2>&1 | grep -E "^Q|route=|A:"
VERSION_AWARE=1 .venv/bin/python try.py "At what disk utilisation should a broker page?" 2>&1 | grep -E "^Q|route=|A:"

if [ "$1" = "--with-answer-eval" ]; then step "2.7 answer-level OFF/ON (about 40 min)"; ./run_answer_ablation.sh; tail -3 results/answer_on.log; fi
printf '\nRECREATE OK\n'
