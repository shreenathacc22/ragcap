"""Gradio chat UI over the same graph. Run: .venv/bin/python ui.py  (http://127.0.0.1:7860)"""
import gradio as gr
from ragcap.graph import ask
from ragcap.ingest import ingest_path
from pathlib import Path


def respond(message, history):
    hist = [{"role": m["role"], "content": m["content"]} for m in history if isinstance(m, dict)]
    o = ask(message, hist)
    path = " > ".join(f"{t['node']} {t['ms']}ms" for t in o["trace"])
    extra = f"\n\n`route: {o['route']} | {path}`"
    if o.get("sql"):
        extra += f"\n\n`sql: {o['sql']}`"
    return o["answer"] + extra


def upload(files):
    return str([r for f in files or [] for r in ingest_path(Path(f))]) or "nothing uploaded"


with gr.Blocks() as demo:
    gr.Markdown("# ragcap: documents + database + general")
    gr.ChatInterface(respond)
    with gr.Accordion("Upload files", open=False):
        up = gr.File(file_count="multiple", type="filepath")
        out = gr.Textbox(label="ingest result")
        up.upload(upload, up, out)

if __name__ == "__main__":
    demo.launch()
