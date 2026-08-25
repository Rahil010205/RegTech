import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.clause import Clause
from app.embeddings.embedding_generator import EmbeddingGenerator


VERSION_ID = "26787ca6-37ee-4ab7-b2c9-5eeb3400d193"

CLAUSES = [
    {
        "clause_number": "RBI-DR-1",
        "section": "Data Retention",
        "title": "Retention of Customer Data",
        "text": (
            "Regulated entities shall retain customer transaction records "
            "and associated financial data for a minimum period prescribed "
            "under applicable regulatory requirements. Records must remain "
            "accessible for audit, investigation, and regulatory inspection."
        ),
    },
    {
        "clause_number": "RBI-DR-2",
        "section": "Data Security",
        "title": "Protection of Stored Data",
        "text": (
            "Regulated entities shall implement appropriate technical and "
            "organizational safeguards to protect customer and transaction "
            "data against unauthorized access, alteration, disclosure, "
            "loss, or destruction."
        ),
    },
    {
        "clause_number": "RBI-DR-3",
        "section": "Audit and Compliance",
        "title": "Audit Trail Maintenance",
        "text": (
            "Regulated entities shall maintain complete and tamper-resistant "
            "audit trails for material financial transactions and system "
            "activities. Audit records shall be available for regulatory "
            "review and internal compliance assessments."
        ),
    },
    {
        "clause_number": "RBI-DR-4",
        "section": "Data Access",
        "title": "Regulatory Access to Records",
        "text": (
            "Financial records and customer information maintained by a "
            "regulated entity shall be made available to authorized "
            "regulatory authorities when required for examination, "
            "supervision, investigation, or enforcement."
        ),
    },
    {
        "clause_number": "RBI-DR-5",
        "section": "Data Disposal",
        "title": "Secure Disposal of Records",
        "text": (
            "When the applicable retention period has expired, regulated "
            "entities shall securely dispose of records containing customer "
            "or financial information in a manner that prevents unauthorized "
            "recovery or disclosure."
        ),
    },
]


def main():
    settings = get_settings()

    engine = create_engine(settings.database_url)

    print("Loading BGE-large-en-v1.5...")
    generator = EmbeddingGenerator()

    texts = [clause["text"] for clause in CLAUSES]

    print(f"Generating {len(texts)} real embeddings...")
    embeddings = generator.embed_texts(texts)

    print(f"Embedding dimension: {len(embeddings[0])}")

    with Session(engine) as session:
        for clause_data, embedding in zip(CLAUSES, embeddings):
            clause = Clause(
                version_id=VERSION_ID,
                clause_number=clause_data["clause_number"],
                section=clause_data["section"],
                title=clause_data["title"],
                text=clause_data["text"],
                metadata_={"source": "direct_test_seed", "embedding": "bge-large-en-v1.5"},
                embedding=embedding,
            )

            session.add(clause)

        session.commit()

    print(f"Successfully inserted {len(CLAUSES)} clauses with real BGE embeddings.")


if __name__ == "__main__":
    main()