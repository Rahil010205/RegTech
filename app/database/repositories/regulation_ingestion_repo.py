"""Repository for regulatory document/version persistence."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import JobStatus
from app.models.regulation import Regulation, RegulationVersion, Regulator


class RegulationIngestionRepository:
    """Data access for regulatory ingestion records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_version_by_content_hash(self, content_hash: str) -> RegulationVersion | None:
        stmt = select(RegulationVersion).where(RegulationVersion.content_hash == content_hash)
        return self.session.scalar(stmt)

    def ensure_regulator(self, code: str, name: str, jurisdiction: str) -> Regulator:
        regulator = self.session.get(Regulator, code)
        if regulator is None:
            regulator = Regulator(code=code, name=name, jurisdiction=jurisdiction)
            self.session.add(regulator)
            self.session.flush()
        return regulator

    def get_regulation_by_title_and_regulator(
        self, regulator_code: str, title: str
    ) -> Regulation | None:
        stmt = select(Regulation).where(
            Regulation.regulator_code == regulator_code,
            Regulation.title == title,
        )
        return self.session.scalar(stmt)

    def create_regulation(
        self,
        *,
        regulator_code: str,
        title: str,
        document_type: str,
    ) -> Regulation:
        regulation = Regulation(
            regulator_code=regulator_code,
            title=title,
            document_type=document_type,
        )
        self.session.add(regulation)
        self.session.flush()
        return regulation

    def create_version(
        self,
        *,
        regulation_id: UUID,
        version: str,
        content_hash: str,
        effective_date: date | None,
        storage_path: str,
        status: str = JobStatus.PROCESSING.value,
    ) -> RegulationVersion:
        version_row = RegulationVersion(
            regulation_id=regulation_id,
            version=version,
            content_hash=content_hash,
            effective_date=effective_date,
            storage_path=storage_path,
            is_current=True,
            status=status,
        )
        self.session.add(version_row)
        self.session.flush()
        return version_row

    def mark_current(self, version: RegulationVersion) -> None:
        stmt = select(RegulationVersion).where(
            RegulationVersion.regulation_id == version.regulation_id,
            RegulationVersion.id != version.id,
        )
        for other in self.session.scalars(stmt).all():
            other.is_current = False
        version.is_current = True
        self.session.flush()

    def update_status(self, version: RegulationVersion, status: str) -> None:
        version.status = status
        self.session.flush()
