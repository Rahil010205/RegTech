import os
from app.core.config import get_settings
from sqlalchemy import create_engine, text, bindparam
from app.ingestion.embedding_service import EmbeddingService
from pgvector.sqlalchemy import Vector

engine = create_engine(get_settings().database_url)
svc = EmbeddingService()
q_emb = svc.embed_query("What are the requirements for customer data retention?")

with engine.connect() as conn:
    # We need to bind the query_embedding with type_=Vector(1024)
    stmt_hello = text("""
        SELECT text, embedding <=> :q_emb as dist, 1 - (embedding <=> :q_emb) as sim
        FROM clauses WHERE text LIKE '%Hello RegTech%';
    """).bindparams(bindparam("q_emb", type_=Vector(1024)))
    res_hello = conn.execute(stmt_hello, {'q_emb': q_emb}).mappings().all()
    print('Hello RegTech:', res_hello)

    stmt_rbi = text("""
        SELECT id, text, embedding <=> :q_emb as dist, 1 - (embedding <=> :q_emb) as sim
        FROM clauses WHERE text LIKE '%retain customer records%';
    """).bindparams(bindparam("q_emb", type_=Vector(1024)))
    res_rbi = conn.execute(stmt_rbi, {'q_emb': q_emb}).mappings().all()
    print('RBI Retention clauses:')
    for r in res_rbi:
        print(r['id'], r['dist'], r['sim'], r['text'][:40])
