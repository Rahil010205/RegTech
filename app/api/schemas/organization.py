"""Organization related response schemas."""

from pydantic import BaseModel, Field
from .common import PaginatedResponse
from .organization_document import OrganizationResponse

class PaginatedOrganizationResponse(PaginatedResponse):
    items: list[OrganizationResponse] = Field(default_factory=list)
