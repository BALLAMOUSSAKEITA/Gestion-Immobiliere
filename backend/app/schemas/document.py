from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import EntityType


class DocumentTypeResponse(BaseModel):
    id: str
    code: str
    label: str


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    is_archived: bool | None = None
    expires_at: date | None = None


class DocumentSummary(BaseModel):
    id: str
    document_type_code: str
    document_type_label: str
    title: str
    description: str | None
    file_name: str
    file_size: int
    mime_type: str
    entity_type: EntityType
    entity_id: str
    uploaded_by_name: str
    uploaded_at: datetime
    is_archived: bool
    expires_at: date | None


class DocumentDetail(DocumentSummary):
    file_url: str
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentSummary]
    total: int
    page: int
    page_size: int
    pages: int


class DocumentShareCreate(BaseModel):
    expires_in_days: int | None = Field(default=None, ge=1, le=30)
    max_access: int | None = Field(default=None, ge=1, le=100)


class DocumentShareResponse(BaseModel):
    id: str
    share_token: str
    share_url: str
    expires_at: datetime
    max_access: int
    accessed_count: int


class SharedDocumentResponse(BaseModel):
    title: str
    file_name: str
    mime_type: str
    file_size: int
    download_url: str
