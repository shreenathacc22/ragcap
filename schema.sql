CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id          serial PRIMARY KEY,
    name        text NOT NULL,
    version     integer NOT NULL DEFAULT 1,
    superseded  boolean NOT NULL DEFAULT false,
    source_path text,
    uploaded_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (name, version)
);
-- step 20: when this version took effect (from the document's front-matter); current must be later than old
ALTER TABLE documents ADD COLUMN IF NOT EXISTS effective_date date;

-- 768 = nomic-embed-text. Change the number AND re-ingest if the embedding model changes.
CREATE TABLE IF NOT EXISTS chunks (
    id         serial PRIMARY KEY,
    doc_id     integer NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_no   integer NOT NULL,
    text       text NOT NULL,
    embedding  vector(768) NOT NULL,
    meta       jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (doc_id, chunk_no)
);
CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);

-- registry of uploaded CSV/Excel tables the SQL agent may query
CREATE TABLE IF NOT EXISTS uploaded_tables (
    table_name  text PRIMARY KEY,
    source_file text NOT NULL,
    row_count   integer NOT NULL,
    uploaded_at timestamptz NOT NULL DEFAULT now()
);
