from datetime import datetime

from pydantic import BaseModel, Field


class NotificationSummary(BaseModel):
    id: str
    event_code: str
    title: str
    body: str
    entity_type: str | None
    entity_id: str | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationSummary]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    count: int


class NotificationPreferenceItem(BaseModel):
    event_code: str
    label: str
    in_app_enabled: bool
    email_enabled: bool
    whatsapp_enabled: bool


class NotificationPreferencesResponse(BaseModel):
    items: list[NotificationPreferenceItem]


class NotificationPreferenceUpdate(BaseModel):
    event_code: str
    in_app_enabled: bool | None = None
    email_enabled: bool | None = None
    whatsapp_enabled: bool | None = None


class NotificationPreferencesUpdateRequest(BaseModel):
    preferences: list[NotificationPreferenceUpdate] = Field(min_length=1)


class WhatsAppLinkResponse(BaseModel):
    url: str
    message: str
