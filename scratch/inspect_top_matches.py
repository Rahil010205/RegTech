from sqlalchemy import create_engine, text
from app.core.config import get_settings
from app.ingestion.embedding_service import EmbeddingService
from pgvector.sqlalchemy import Vector
import json

engine = create_engine(get_settings().database_url)
svc = EmbeddingService()
q_emb = svc.embed_query("What are the requirements for customer data retention?")

with engine.connect() as conn:
    stmt = text("""
        SELECT c.id, c.text, c.version_id, c.metadata, r.title, rv.version,
               c.embedding <=> :q_emb as dist, 1 - (c.embedding <=> :q_emb) as sim
        FROM clauses c
        JOIN regulation_versions rv ON c.version_id = rv.id
        JOIN regulations r ON rv.regulation_id = r.id
        ORDER BY c.embedding <=> :q_emb
        LIMIT 10;
    """).bindparams(bindparam("q_emb", type_=Vector(1024)))
    res = conn.execute(stmt, {'q_emb': q_emb}).mappings().all()
    for r in res:
        print(f"ID: {r['id']}")
        print(f"  Title: {r['title']} | Version: {r['version']}")
        print(f"  Text: {r['text'][:50]}")
        print(f"  Dist: {r['dist']:.4f} | Sim: {r['sim']:.4f}")
        print(f"  Metadata: {json.dumps(r['metadata'])}")
