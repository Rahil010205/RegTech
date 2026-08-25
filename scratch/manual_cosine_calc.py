import numpy as np
from sqlalchemy import create_engine, text
from app.core.config import get_settings
from app.ingestion.embedding_service import EmbeddingService

engine = create_engine(get_settings().database_url)
svc = EmbeddingService()
q_emb = np.array(svc.embed_query("What are the requirements for customer data retention?"))

with engine.connect() as conn:
    row = conn.execute(text("SELECT embedding FROM clauses WHERE id = '316bb0ff-1ce5-4fc1-be1e-90781c6a4499'")).mappings().one()
    c_emb = np.array(row['embedding'])

print('Query Embedding Norm:', np.linalg.norm(q_emb))
print('Clause Embedding Norm:', np.linalg.norm(c_emb))
dot_prod = np.dot(q_emb, c_emb)
print('Dot Product:', dot_prod)
print('Cosine Similarity:', dot_prod / (np.linalg.norm(q_emb) * np.linalg.norm(c_emb)))
print('1 - Cosine Distance:', 1.0 - (1.0 - dot_prod / (np.linalg.norm(q_emb) * np.linalg.norm(c_emb))))
