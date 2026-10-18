"""FastAPI service: POST /upload, POST /chat (server-sent events, one event per graph node), POST /eval, GET /health.
Run: .venv/bin/uvicorn api:app --port 8000"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ragcap import graph
from ragcap.ingest import ingest_path
from ragcap.tracing import log_run

UPLOADS = Path(__file__).parent / "uploads"
UPLOADS.mkdir(exist_ok=True)
app = FastAPI(title="ragcap")


class ChatIn(BaseModel):
    question: str
    history: list[dict] = []


@app.get("/health")
def health():
    from ragcap.db import connect
    c = connect()
    return {"documents": c.execute("select count(*) from documents").fetchone()[0],
            "chunks": c.execute("select count(*) from chunks").fetchone()[0],
            "tables": [r[0] for r in c.execute("select table_name from uploaded_tables")]}


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    dest = UPLOADS / Path(file.filename).name
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"ingested": ingest_path(dest)}


@app.post("/chat")
def chat(body: ChatIn):
    def events():
        app_ = graph.build()
        t0 = time.perf_counter()
        state = {"question": body.question, "history": body.history, "trace": []}
        final = dict(state)
        for upd in app_.stream(state, stream_mode="updates"):
            for node, delta in upd.items():
                final.update(delta)
                yield f"event: node\ndata: {json.dumps({'node': node, 'ms': delta['trace'][-1]['ms']})}\n\n"
        final["total_ms"] = round((time.perf_counter() - t0) * 1000)
        log_run(final)
        cites = [{"doc": c["doc"], "version": c["version"]} for c in final.get("relevant", [])]
        yield f"event: answer\ndata: {json.dumps({'answer': final.get('answer'), 'route': final.get('route'), 'citations': cites, 'sql': final.get('sql'), 'total_ms': final['total_ms']})}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream")


@app.post("/eval")
def run_eval(limit: int | None = None):
    """Runs eval.py as a subprocess (it takes minutes on a local model); returns the saved report path."""
    cmd = [sys.executable, "eval.py"] + ([str(limit)] if limit else [])
    p = subprocess.run(cmd, cwd=Path(__file__).parent, capture_output=True, text=True)
    return {"returncode": p.returncode, "tail": p.stdout[-1500:]}
