"""Ingestion: documents -> Markdown -> chunks -> embeddings -> pgvector; CSV/Excel -> SQL tables.

Usage: python -m ragcap.ingest <file-or-folder> [--version N]
"""
import argparse
import json
import re
import time
from pathlib import Path

import pandas as pd
from psycopg import sql

from .db import connect
from .llm import embed

DOC_EXT = {".md", ".txt", ".pdf", ".docx", ".pptx", ".html"}
TABLE_EXT = {".csv", ".xlsx", ".xls"}


# ---------- parsing ----------
def to_markdown(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".md", ".txt"}:
        return path.read_text(encoding="utf-8", errors="replace")
    try:  # Docling handles pdf/docx/pptx/html with layout and tables
        from docling.document_converter import DocumentConverter
        return DocumentConverter().convert(str(path)).document.export_to_markdown()
    except ImportError:
        if ext == ".pdf":
            from pypdf import PdfReader
            return "\n\n".join(p.extract_text() or "" for p in PdfReader(str(path)).pages)
        raise RuntimeError(f"{ext} needs Docling (not installed in this venv)")


# ---------- chunking ----------
def chunk(text: str, target_words: int = 180) -> list[str]:
    """Pack whole paragraphs up to ~target_words; split an oversized paragraph on sentences."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur, n = [], [], 0
    for p in paras:
        w = len(p.split())
        if cur and n + w > target_words:
            chunks.append("\n\n".join(cur)); cur, n = [], 0
        cur.append(p); n += w
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks


# ---------- documents ----------
def ingest_document(conn, path: Path, version: int = 1, superseded: bool = False) -> dict:
    t0 = time.perf_counter()
    name = path.stem
    chunks = chunk(to_markdown(path))
    # prepend the doc name so an orphan paragraph still says what it is about
    vecs = []
    for i in range(0, len(chunks), 16):
        vecs += embed([f"{name}\n{c}" for c in chunks[i:i + 16]])
    conn.execute("DELETE FROM documents WHERE name=%s AND version=%s", (name, version))
    doc_id = conn.execute(
        "INSERT INTO documents(name,version,superseded,source_path) VALUES (%s,%s,%s,%s) RETURNING id",
        (name, version, superseded, str(path))).fetchone()[0]
    for i, (c, v) in enumerate(zip(chunks, vecs)):
        conn.execute("INSERT INTO chunks(doc_id,chunk_no,text,embedding,meta) VALUES (%s,%s,%s,%s,%s)",
                     (doc_id, i, c, v, json.dumps({"doc": name, "version": version})))
    return {"file": path.name, "chunks": len(chunks), "seconds": round(time.perf_counter() - t0, 1)}


# ---------- tables ----------
def safe_name(s: str) -> str:
    s = re.sub(r"[^0-9a-zA-Z_]+", "_", s.strip().lower()).strip("_")
    return ("t_" + s) if not s or s[0].isdigit() else s


def ingest_table(conn, path: Path) -> list[dict]:
    frames = ({path.stem: pd.read_csv(path)} if path.suffix.lower() == ".csv"
              else pd.read_excel(path, sheet_name=None))
    out = []
    for sheet, df in frames.items():
        tname = safe_name(path.stem if path.suffix.lower() == ".csv" else f"{path.stem}_{sheet}")
        df.columns = [safe_name(str(c)) for c in df.columns]
        conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(tname)))
        types = {"int64": "bigint", "float64": "double precision", "bool": "boolean"}
        cols = sql.SQL(", ").join(
            sql.SQL("{} {}").format(sql.Identifier(c), sql.SQL(types.get(str(df[c].dtype), "text")))
            for c in df.columns)
        conn.execute(sql.SQL("CREATE TABLE {} ({})").format(sql.Identifier(tname), cols))
        with conn.cursor().copy(sql.SQL("COPY {} FROM STDIN").format(sql.Identifier(tname))) as cp:
            for row in df.astype(object).where(df.notna(), None).itertuples(index=False):
                cp.write_row(row)
        conn.execute("""INSERT INTO uploaded_tables(table_name,source_file,row_count) VALUES (%s,%s,%s)
                        ON CONFLICT (table_name) DO UPDATE SET source_file=EXCLUDED.source_file,
                        row_count=EXCLUDED.row_count, uploaded_at=now()""", (tname, path.name, len(df)))
        out.append({"table": tname, "rows": len(df), "columns": list(df.columns)})
    return out


def ingest_path(target: Path, version: int = 1) -> list[dict]:
    conn = connect()
    files = sorted(p for p in ([target] if target.is_file() else target.rglob("*")) if p.is_file())
    results = []
    for f in files:
        ext = f.suffix.lower()
        if ext in DOC_EXT:
            results.append(ingest_document(conn, f, version))
        elif ext in TABLE_EXT:
            results += ingest_table(conn, f)
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--version", type=int, default=1)
    a = ap.parse_args()
    for r in ingest_path(Path(a.path), a.version):
        print(r)
