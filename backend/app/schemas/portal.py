from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import NoticeType, VisitRequestStatus


class VisitRequestCreate(BaseModel):
    unit_id: str
    visitor_name: str = Field(min_length=2, max_length=200)
    visitor_email: EmailStr
    visitor_phone: str = Field(min_length=6, max_length=20)
    preferred_date: date | None = None
    preferred_time: str | None = Field(default=None, max_length=50)
    message: str | None = None


class VisitRequestUpdate(BaseModel):
    status: VisitRequestStatus | None = None
    assigned_to: str | None = None


class VisitRequestSummary(BaseModel):
    id: str
    unit_id: str
    unit_code: str
    visitor_name: str
    visitor_email: str
    visitor_phone: str
    preferred_date: date | None
    preferred_time: str | None
    message: str | None
    status: VisitRequestStatus
    assigned_to_name: str | None
    created_at: datetime


class VisitRequestListResponse(BaseModel):
    items: list[VisitRequestSummary]
    total: int


class PublicContactCreate(BaseModel):
    sender_name: str = Field(min_length=2, max_length=200)
    sender_email: EmailStr
    sender_phone: str | None = Field(default=None, max_length=20)
    unit_id: str | None = None
    subject: str = Field(min_length=3, max_length=300)
    body: str = Field(min_length=3, max_length=5000)


class MessageCreate(BaseModel):
    recipient_user_id: str | None = None
    unit_id: str | None = None
    subject: str = Field(min_length=3, max_length=300)
    body: str = Field(min_length=3, max_length=5000)


class MessageReplyCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class MessageSummary(BaseModel):
    id: str
    sender_name: str
    sender_email: str
    subject: str
    body: str
    is_read: bool
    created_at: datetime
    parent_message_id: str | None = None


class MessageListResponse(BaseModel):
    items: list[MessageSummary]
    total: int


class TenantNoticeCreate(BaseModel):
    tenant_id: str
    title: str = Field(min_length=3, max_length=300)
    content: str | None = None
    notice_type: NoticeType = NoticeType.info
    document_id: str | None = None


class TenantNoticeSummary(BaseModel):
    id: str
    title: str
    content: str | None
    notice_type: NoticeType
    published_at: datetime
    is_read: bool


class TenantPortalDashboard(BaseModel):
    tenant: dict
    unit: dict | None
    lease: dict | None
    payment_status: dict
    unread_notices: int
    active_repairs: int
    has_active_lease: bool


class TenantUnitInfo(BaseModel):
    id: str
    code: str
    type: str
    number: str
    rent_amount: float
    building_name: str
    commune: str
    quartier: str | None
    description: str | None
    photos: list[dict]


class TenantLeaseInfo(BaseModel):
    id: str
    start_date: str
    end_date: str | None
    rent_amount: float
    deposit_amount: float
    status: str
    contract_document_url: str | None
