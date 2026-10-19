"""Step 1 check: schema applied, a real embedding stored and found by cosine search, then cleaned up."""
from pathlib import Path
from ragcap.db import connect
from ragcap.llm import embed
from ragcap.config import EMBED_DIM

conn = connect()
conn.execute(Path(__file__).with_name("schema.sql").read_text())
tables = [r[0] for r in conn.execute(
    "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1")]
print("tables:", tables)

texts = ["Kafka consumer lag alert threshold", "Chocolate cake recipe with butter"]
vecs = embed(texts)
print("embedding dim:", len(vecs[0]))
assert len(vecs[0]) == EMBED_DIM, "EMBED_DIM does not match the model"

doc_id = conn.execute("INSERT INTO documents(name) VALUES ('_step1_probe') RETURNING id").fetchone()[0]
for i, (t, v) in enumerate(zip(texts, vecs)):
    conn.execute("INSERT INTO chunks(doc_id,chunk_no,text,embedding) VALUES (%s,%s,%s,%s)", (doc_id, i, t, v))
q = embed(["when should the lag page someone?"])[0]
top = conn.execute("SELECT text, embedding <=> %s::vector AS dist FROM chunks WHERE doc_id=%s ORDER BY dist LIMIT 1",
                   (q, doc_id)).fetchone()
print("nearest:", top[0], round(top[1], 3))
assert "Kafka" in top[0]
conn.execute("DELETE FROM documents WHERE id=%s", (doc_id,))
print("STEP 1 OK")
