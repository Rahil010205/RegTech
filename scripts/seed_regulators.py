"""Seed regulator reference data."""

REGULATORS = [
    {"code": "RBI", "name": "Reserve Bank of India", "jurisdiction": "IN"},
    {"code": "SEBI", "name": "Securities and Exchange Board of India", "jurisdiction": "IN"},
    {"code": "IRDAI", "name": "Insurance Regulatory and Development Authority of India", "jurisdiction": "IN"},
    {"code": "GDPR", "name": "General Data Protection Regulation", "jurisdiction": "EU"},
    {"code": "ISO", "name": "International Organization for Standardization", "jurisdiction": "GLOBAL"},
]


def main() -> None:
    """Insert regulator records. Requires database connection — implementation pending."""
    print(f"Seeding {len(REGULATORS)} regulators...")
    # TODO: use SQLAlchemy session to upsert regulators


if __name__ == "__main__":
    main()
