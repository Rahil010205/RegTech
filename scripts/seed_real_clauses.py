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


from uuid import UUID
from app.core.constants import JobStatus
from app.models.regulation import Regulator, Regulation, RegulationVersion

VERSION_ID = UUID("26787ca6-37ee-4ab7-b2c9-5eeb3400d193")
REGULATION_ID = UUID("11111111-2222-3333-4444-555555555555")

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
        regulator = session.get(Regulator, "RBI")
        if not regulator:
            regulator = Regulator(code="RBI", name="Reserve Bank of India", jurisdiction="IN")
            session.add(regulator)
            session.flush()

        regulation = session.get(Regulation, REGULATION_ID)
        if not regulation:
            regulation = Regulation(
                id=REGULATION_ID,
                regulator_code="RBI",
                title="RBI Master Direction - IT Framework and Data Security",
                document_type="CIRCULAR",
            )
            session.add(regulation)
            session.flush()

        version = session.get(RegulationVersion, VERSION_ID)
        if not version:
            version = RegulationVersion(
                id=VERSION_ID,
                regulation_id=regulation.id,
                version="2026.1",
                content_hash="seed-hash-rbi-dr-2026",
                status=JobStatus.COMPLETED.value,
                is_current=True,
            )
            session.add(version)
            session.flush()

        # Remove existing seed clauses for this version
        for existing in session.query(Clause).filter_by(version_id=VERSION_ID).all():
            session.delete(existing)
        session.flush()

        for clause_data, embedding in zip(CLAUSES, embeddings):
            clause = Clause(
                version_id=VERSION_ID,
                clause_number=clause_data["clause_number"],
                section=clause_data["section"],
                title=clause_data["title"],
                text=clause_data["text"],
                metadata_={
                    "document_name": "RBI_IT_Framework_2026.pdf",
                    "regulator": "RBI",
                    "jurisdiction": "IN",
                    "embedding": "bge-large-en-v1.5",
                },
                embedding=embedding,
            )
            session.add(clause)

        session.commit()

    print(f"Successfully inserted {len(CLAUSES)} clauses with real BGE embeddings.")


if __name__ == "__main__":
    main()