import sys
from ragcap.graph import ask
for q in sys.argv[1:]:
    o = ask(q)
    print(f"\nQ: {q}\n route={o['route']} rewrites={o.get('rewrites')} total={o['total_ms']}ms")
    print(" path:", " > ".join(f"{t['node']}({t['ms']}ms)" for t in o["trace"]))
    if o.get("sql"): print(" sql:", o["sql"], "| err:", o.get("sql_error"))
    print(" A:", o["answer"][:400])
