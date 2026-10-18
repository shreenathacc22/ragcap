"""LangGraph pipeline: router -> (retrieve -> grade -> [rewrite -> retrieve -> grade] -> generate)
                              | (sql -> generate_sql) | general.
Every node appends {node, ms, llm_calls, tokens_in, tokens_out} to state['trace']."""
import json
import re
import time
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .config import LLM_MODEL, TOP_K
from .db import connect
from .llm import client, embed
from .tracing import log_run


class State(TypedDict, total=False):
    question: str
    history: list[dict]
    route: str
    standalone: str
    chunks: list[dict]
    relevant: list[dict]
    rewrites: int
    sql: str
    sql_error: str
    sql_attempts: int
    rows: list
    columns: list
    answer: str
    trace: list[dict]


# ---------- helpers ----------
def chat(messages, json_mode=False, max_tokens=400):
    kw = {"response_format": {"type": "json_object"}} if json_mode else {}
    r = client().chat.completions.create(model=LLM_MODEL, messages=messages, temperature=0,
                                         max_tokens=max_tokens, **kw)
    u = r.usage
    return r.choices[0].message.content or "", (u.prompt_tokens if u else 0), (u.completion_tokens if u else 0)


def parse_json(s: str) -> dict:
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"\{.*\}", s, re.S)
        return json.loads(m.group(0)) if m else {}


def timed(name):
    """Decorator: time a node and record trace; the node returns (update, llm_calls, tin, tout)."""
    def deco(fn):
        def wrapper(state: State) -> dict:
            t0 = time.perf_counter()
            update, calls, tin, tout = fn(state)
            update["trace"] = state.get("trace", []) + [{
                "node": name, "ms": round((time.perf_counter() - t0) * 1000),
                "llm_calls": calls, "tokens_in": tin, "tokens_out": tout}]
            return update
        wrapper.__name__ = name
        return wrapper
    return deco


def table_catalog(conn) -> str:
    """Columns, 3 sample rows and allowed values of low-cardinality text columns, per uploaded table."""
    parts = []
    for (t,) in conn.execute("SELECT table_name FROM uploaded_tables ORDER BY 1").fetchall():
        cols = conn.execute("SELECT column_name,data_type FROM information_schema.columns "
                            "WHERE table_name=%s ORDER BY ordinal_position", (t,)).fetchall()
        cur = conn.execute(f'SELECT * FROM "{t}" LIMIT 3')
        rows = cur.fetchall()
        desc = [f"TABLE {t} ({', '.join(f'{c} {d}' for c, d in cols)})", f"  sample rows: {rows}"]
        for c, d in cols:
            if d == "text":
                vals = [r[0] for r in conn.execute(f'SELECT DISTINCT "{c}" FROM "{t}" LIMIT 12').fetchall()]
                if len(vals) < 12:
                    desc.append(f"  allowed values of {c}: {vals}")
        parts.append("\n".join(desc))
    return "\n".join(parts)


def has_tables() -> bool:
    return connect().execute("SELECT count(*) FROM uploaded_tables").fetchone()[0] > 0


# ---------- nodes ----------
@timed("router")
def router(s: State):
    tables = has_tables()
    hist = "\n".join(f"{m['role']}: {m['content']}" for m in s.get("history", [])[-6:])
    sys = ("You route user messages. Reply as JSON: {\"route\": ..., \"standalone\": ...}.\n"
           "route is one of:\n"
           "- documents: asks for information that would be written in uploaded documents (runbooks, policies, procedures, thresholds, ports, steps).\n"
           + ("- database: asks for exact numbers, counts, filters, totals or lists from an uploaded spreadsheet/table (brokers, rows, disk percentages).\n" if tables else "")
           + "- general: only a greeting, thanks, or a question about the assistant itself. NEVER for factual questions.\n"
           "standalone: the user's message rewritten as a self-contained question using the chat history.")
    out, ti, to = chat([{"role": "system", "content": sys},
                        {"role": "user", "content": f"Chat history:\n{hist or '(none)'}\n\nMessage: {s['question']}"}],
                       json_mode=True, max_tokens=120)
    j = parse_json(out)
    route = j.get("route", "documents")
    if route not in {"documents", "database", "general"} or (route == "database" and not tables):
        route = "documents"
    return {"route": route, "standalone": j.get("standalone") or s["question"], "rewrites": 0, "sql_attempts": 0}, 1, ti, to


@timed("retrieve")
def retrieve(s: State):
    q = s["standalone"]
    qv = embed([q])[0]
    rows = connect().execute(
        """SELECT c.id, d.name, d.version, c.chunk_no, c.text, c.embedding <=> %s::vector AS dist
           FROM chunks c JOIN documents d ON d.id=c.doc_id
           ORDER BY dist LIMIT %s""", (qv, TOP_K)).fetchall()
    chunks = [dict(id=r[0], doc=r[1], version=r[2], chunk_no=r[3], text=r[4], dist=round(float(r[5]), 3)) for r in rows]
    return {"chunks": chunks}, 0, 0, 0


@timed("grade")
def grade(s: State):
    listing = "\n\n".join(f"[{i}] ({c['doc']})\n{c['text'][:900]}" for i, c in enumerate(s["chunks"]))
    out, ti, to = chat([
        {"role": "system", "content": "You filter search results. A passage is relevant if it covers the same topic as the question "
         "and could contain the answer, even if the answer is not stated in the first lines. Be inclusive: when unsure, keep it. "
         "Reply JSON: {\"relevant\": [indices]}. Use [] only if every passage is about a clearly different subject."},
        {"role": "user", "content": f"Question: {s['standalone']}\n\nPassages:\n{listing}"}], json_mode=True, max_tokens=60)
    idx = [i for i in parse_json(out).get("relevant", []) if isinstance(i, int) and 0 <= i < len(s["chunks"])]
    return {"relevant": [s["chunks"][i] for i in idx]}, 1, ti, to


@timed("rewrite")
def rewrite(s: State):
    out, ti, to = chat([
        {"role": "system", "content": "Rewrite the search query using synonyms and expanded terms to improve retrieval. "
         "Reply JSON: {\"query\": \"...\"}."},
        {"role": "user", "content": s["standalone"]}], json_mode=True, max_tokens=60)
    return {"standalone": parse_json(out).get("query") or s["standalone"], "rewrites": s.get("rewrites", 0) + 1}, 1, ti, to


@timed("generate")
def generate(s: State):
    ctx = s.get("relevant") or []
    if not ctx:
        return {"answer": "That information is not in the knowledge base."}, 0, 0, 0
    listing = "\n\n".join(f"[{i + 1}] ({c['doc']})\n{c['text']}" for i, c in enumerate(ctx))
    out, ti, to = chat([
        {"role": "system", "content": "Answer using ONLY the numbered passages. Cite sources like [1]. "
         "If the passages do not contain the answer, say it is not in the knowledge base."},
        {"role": "user", "content": f"Question: {s['standalone']}\n\nPassages:\n{listing}"}], max_tokens=300)
    return {"answer": out.strip()}, 1, ti, to


FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|call|do|execute)\b", re.I)


def validate_select(q: str) -> str:
    q = q.strip().rstrip(";").strip()
    if ";" in q or not re.match(r"(?is)^(select|with)\b", q) or FORBIDDEN.search(q):
        raise ValueError("only a single read-only SELECT is allowed")
    return q


def run_readonly(q: str):
    conn = connect(autocommit=False)
    try:
        conn.execute("SET TRANSACTION READ ONLY")
        conn.execute("SET LOCAL statement_timeout = '5s'")
        cur = conn.execute(q)
        cols = [d.name for d in cur.description]
        rows = cur.fetchmany(50)
        return cols, [list(r) for r in rows]
    finally:
        conn.rollback()
        conn.close()


@timed("sql_agent")
def sql_agent(s: State):
    catalog = table_catalog(connect())
    calls = ti = to = 0
    err = None
    q = ""
    for attempt in range(2):  # first try + one retry with the DB error fed back
        msg = f"Question: {s['standalone']}\n\n{catalog}"
        if err:
            msg += f"\n\nYour previous query:\n{q}\nfailed with: {err}\nFix it."
        out, a, b = chat([
            {"role": "system", "content": "Write ONE PostgreSQL SELECT statement answering the question using only the tables shown. "
             "Reply JSON: {\"sql\": \"...\"}."},
            {"role": "user", "content": msg}], json_mode=True, max_tokens=200)
        calls, ti, to = calls + 1, ti + a, to + b
        q = parse_json(out).get("sql", "")
        try:
            cols, rows = run_readonly(validate_select(q))
            return {"sql": q, "columns": cols, "rows": rows, "sql_error": "", "sql_attempts": attempt + 1}, calls, ti, to
        except Exception as e:  # noqa: BLE001
            err = str(e).splitlines()[0]
    return {"sql": q, "columns": [], "rows": [], "sql_error": err or "failed", "sql_attempts": 2}, calls, ti, to


@timed("generate_sql")
def generate_sql(s: State):
    if s.get("sql_error"):
        return {"answer": f"I could not compute that from the tables ({s['sql_error']})."}, 0, 0, 0
    out, ti, to = chat([
        {"role": "system", "content": "Answer in plain language from the query result. State that it was computed from the table. Be concise."},
        {"role": "user", "content": f"Question: {s['standalone']}\nSQL: {s['sql']}\nColumns: {s['columns']}\nRows: {s['rows']}"}], max_tokens=200)
    return {"answer": out.strip()}, 1, ti, to


@timed("general")
def general(s: State):
    out, ti, to = chat([
        {"role": "system", "content": "You are a document and data assistant. Reply briefly to greetings or questions about yourself. "
         "NEVER state facts about the world or any subject; if asked, say you will look it up in the documents."},
        {"role": "user", "content": s["question"]}], max_tokens=120)
    return {"answer": out.strip()}, 1, ti, to


# ---------- wiring ----------
def after_router(s: State):
    return {"documents": "retrieve", "database": "sql_agent", "general": "general"}[s["route"]]


def after_grade(s: State):
    return "generate" if s.get("relevant") or s.get("rewrites", 0) >= 1 else "rewrite"


def build():
    g = StateGraph(State)
    for fn in (router, retrieve, grade, rewrite, generate, sql_agent, generate_sql, general):
        g.add_node(fn.__name__, fn)
    g.add_edge(START, "router")
    g.add_conditional_edges("router", after_router, ["retrieve", "sql_agent", "general"])
    g.add_edge("retrieve", "grade")
    g.add_conditional_edges("grade", after_grade, ["generate", "rewrite"])
    g.add_edge("rewrite", "retrieve")
    g.add_edge("sql_agent", "generate_sql")
    for end in ("generate", "generate_sql", "general"):
        g.add_edge(end, END)
    return g.compile()


_app = None


def ask(question: str, history: list[dict] | None = None) -> dict:
    global _app
    _app = _app or build()
    t0 = time.perf_counter()
    out = _app.invoke({"question": question, "history": history or [], "trace": []})
    out["total_ms"] = round((time.perf_counter() - t0) * 1000)
    log_run(out)
    return out
