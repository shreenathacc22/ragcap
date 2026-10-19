"""Step 20 data checks for the versioned corpus in Postgres. Exit 1 on any failure.

    .venv/bin/python b1_check.py              # all checks incl. the similarity trap (8 embedding calls)
    .venv/bin/python b1_check.py --no-trap    # structural checks only, no model calls
    .venv/bin/python b1_check.py --negative   # break the data in memory three ways; each must be reported

Why: the version filter is only as good as the metadata. A wrong 'superseded' flag, a version
number stored as text, or a banner leaking into the embedded text silently invalidates the ablation.
"""
import argparse
import json
import math
import sys
from collections import defaultdict

from ragcap.db import connect

EXPECT_DOCS, EXPECT_PER_NAME = 16, 2


def load():
    conn = connect()
    docs = [dict(id=r[0], name=r[1], version=r[2], superseded=r[3], effective_date=r[4]) for r in conn.execute(
        "SELECT id,name,version,superseded,effective_date FROM documents ORDER BY name,version")]
    chunks = [dict(doc_id=r[0], chunk_no=r[1], text=r[2], meta=r[3], embedding=list(r[4])) for r in conn.execute(
        "SELECT doc_id,chunk_no,text,meta,embedding FROM chunks")]
    return docs, chunks


def structural(docs, chunks) -> list[str]:
    """Returns a list of failures (empty = pass)."""
    f = []
    by = defaultdict(list)
    for d in docs:
        by[d["name"]].append(d)
    if len(docs) != EXPECT_DOCS:
        f.append(f"expected {EXPECT_DOCS} documents, found {len(docs)}")
    for name, vs in by.items():
        if len(vs) != EXPECT_PER_NAME:
            f.append(f"{name}: expected {EXPECT_PER_NAME} versions, found {len(vs)}")
            continue
        cur = [v for v in vs if v["superseded"] is False]
        old = [v for v in vs if v["superseded"] is True]
        if len(cur) != 1 or len(old) != 1:
            f.append(f"{name}: need exactly one current and one superseded version, got superseded={[v['superseded'] for v in vs]}")
            continue
        c, o = cur[0], old[0]
        if not (isinstance(c["version"], int) and isinstance(o["version"], int)):
            f.append(f"{name}: version must be an integer")
        elif c["version"] <= o["version"]:
            f.append(f"{name}: current version {c['version']} is not greater than old {o['version']}")
        if c["effective_date"] is None or o["effective_date"] is None:
            f.append(f"{name}: effective_date missing")
        elif c["effective_date"] <= o["effective_date"]:
            f.append(f"{name}: current effective_date {c['effective_date']} is not after old {o['effective_date']}")
    doc_by_id = {d["id"]: d for d in docs}
    for ch in chunks:
        d = doc_by_id.get(ch["doc_id"])
        if d is None:
            f.append(f"chunk of unknown document id {ch['doc_id']}")
            continue
        t = ch["text"]
        if t.lstrip().startswith("---") or "\nstatus:" in t or "\nsuperseded:" in t or "effective_date:" in t:
            f.append(f"{d['name']} v{d['version']} chunk {ch['chunk_no']}: front-matter leaked into embedded text")
        if "SUPERSEDED" in t:
            f.append(f"{d['name']} v{d['version']} chunk {ch['chunk_no']}: a SUPERSEDED banner is in the embedded text")
        if ch["meta"].get("superseded") != d["superseded"]:
            f.append(f"{d['name']} v{d['version']} chunk {ch['chunk_no']}: meta.superseded {ch['meta'].get('superseded')} != document {d['superseded']}")
    return f


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def trap(docs, chunks) -> list[str]:
    """Measures why the filter is needed: old/current pairs are near-identical, and the old one often ranks first."""
    from ragcap.llm import embed
    out = []
    by = defaultdict(dict)
    for d in docs:
        vecs = [c["embedding"] for c in chunks if c["doc_id"] == d["id"]]
        by[d["name"]]["old" if d["superseded"] else "cur"] = vecs
    sims = []
    for name, v in sorted(by.items()):
        if "old" in v and "cur" in v and v["old"] and v["cur"]:
            s = max(cosine(a, b) for a in v["old"] for b in v["cur"])
            sims.append(s)
            out.append(f"  pair similarity {name}: {s:.3f}")
    questions = [json.loads(l)["question"] for l in open("golden/golden.jsonl") if '"version_current"' in l][:8]
    qv = embed(questions)
    old_first = 0
    for q, vec in zip(questions, qv):
        best = sorted(((cosine(vec, c["embedding"]), c["doc_id"]) for c in chunks), reverse=True)[0]
        d = next(d for d in docs if d["id"] == best[1])
        old_first += d["superseded"]
        out.append(f"  top-1 for '{q[:50]}...': {d['name']} v{d['version']} {'OLD' if d['superseded'] else 'current'}")
    out.append(f"  pair similarity min/max: {min(sims):.3f} / {max(sims):.3f}; old version ranked first for {old_first}/{len(questions)} plain questions")
    if min(sims) < 0.85:
        out.append("  WARNING: a pair is below 0.85 similarity; the trap is weaker than intended")
    return out


def negative(docs, chunks) -> int:
    """Break the data in memory three ways; each must produce at least one failure."""
    import copy
    bad = 0
    cases = {
        "old version marked current": lambda d, c: d[0].update(superseded=False),
        "version stored as text": lambda d, c: d[1].update(version="2"),
        "banner in embedded text": lambda d, c: c[0].update(text="SUPERSEDED\n" + c[0]["text"]),
    }
    for label, mut in cases.items():
        d2, c2 = copy.deepcopy(docs), copy.deepcopy(chunks)
        mut(d2, c2)
        found = structural(d2, c2)
        print(f"  negative test '{label}': {'reported' if found else 'NOT REPORTED'} ({found[0] if found else '-'})")
        bad += not found
    return bad


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-trap", action="store_true")
    ap.add_argument("--negative", action="store_true")
    a = ap.parse_args()
    docs, chunks = load()
    print(f"documents: {len(docs)}, chunks: {len(chunks)}")
    fails = structural(docs, chunks)
    for x in fails:
        print("  FAIL:", x)
    if not a.no_trap and not fails:
        print("similarity trap (pipeline's own embedder):")
        for line in trap(docs, chunks):
            print(line)
    if a.negative:
        print("negative tests:")
        fails += ["a negative test was not reported"] * negative(docs, chunks)
    print("PASS" if not fails else f"FAIL ({len(fails)})")
    sys.exit(1 if fails else 0)
