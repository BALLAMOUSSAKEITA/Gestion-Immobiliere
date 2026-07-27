from datetime import datetime

from pydantic import BaseModel


class AuditUserBrief(BaseModel):
    id: str
    full_name: str
    email: str


class AuditLogSummary(BaseModel):
    id: str
    user: AuditUserBrief
    action: str
    entity_type: str
    entity_id: str
    created_at: datetime


class AuditLogDetail(AuditLogSummary):
    old_values: dict | None = None
    new_values: dict | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class AuditLogListResponse(BaseModel):
    items: list[AuditLogSummary]
    total: int
    page: int
    page_size: int
    pages: int
