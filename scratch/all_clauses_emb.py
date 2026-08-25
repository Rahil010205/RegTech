from sqlalchemy import create_engine, text
from app.core.config import get_settings

engine = create_engine(get_settings().database_url)

with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT c.id, c.clause_number, left(c.text, 30) as text_snippet, c.version_id, r.title, left(c.embedding::text, 80) as emb
        FROM clauses c
        JOIN regulation_versions rv ON c.version_id = rv.id
        JOIN regulations r ON rv.regulation_id = r.id;
    """)).mappings().all()
    for row in rows:
        print(f"ID: {row['id']} | Ver: {row['version_id']} | Title: {row['title']} | Snippet: {row['text_snippet']} | Emb: {row['emb']}")
