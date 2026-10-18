import psycopg
from pgvector.psycopg import register_vector
from .config import PG_DSN


def connect(autocommit: bool = True) -> psycopg.Connection:
    conn = psycopg.connect(PG_DSN, autocommit=autocommit)
    register_vector(conn)
    return conn
