"""CLI: ingest an organization policy PDF.

Usage:
    python -m app.ingestion.organization_policy \\
        --organization-id <uuid> \\
        --file data/organization/company_kyc_policy.pdf
"""

from __future__ import annotations

import argparse
from pathlib import Path
from uuid import UUID

from app.database.session import SessionLocal
from app.ingestion.organization_policy_pipeline import OrganizationPolicyPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest an organization policy PDF")
    parser.add_argument("--organization-id", type=UUID, required=True)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--document-type", default=None)
    parser.add_argument("--version", default=None)
    args = parser.parse_args()

    with SessionLocal() as session:
        pipeline = OrganizationPolicyPipeline(session)
        result = pipeline.ingest_file(
            organization_id=args.organization_id,
            file_path=args.file,
            document_type=args.document_type,
            version=args.version,
        )

    print(
        {
            "document_id": str(result.document_id),
            "organization_id": str(result.organization_id),
            "document_name": result.document_name,
            "status": result.status,
            "chunks_created": result.chunks_created,
            "error": result.error,
        }
    )


if __name__ == "__main__":
    main()
