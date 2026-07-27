from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ApprovalRequestStatus


class ApprovalRequestCreate(BaseModel):
    action_code: str = Field(min_length=1, max_length=100)
    entity_type: str = Field(min_length=1, max_length=50)
    entity_id: str
    reason: str = Field(min_length=3, max_length=2000)
    payload_after: dict | None = None


class ApprovalReviewRequest(BaseModel):
    review_comment: str | None = Field(default=None, max_length=2000)


class ApprovalUserBrief(BaseModel):
    id: str
    full_name: str
    email: str


class ApprovalRequestSummary(BaseModel):
    id: str
    action_code: str
    entity_type: str
    entity_id: str
    status: ApprovalRequestStatus
    reason: str
    requested_by: ApprovalUserBrief
    requested_at: datetime
    reviewed_by: ApprovalUserBrief | None = None
    reviewed_at: datetime | None = None
    review_comment: str | None = None
    executed_at: datetime | None = None


class ApprovalRequestDetail(ApprovalRequestSummary):
    payload_before: dict | None = None
    payload_after: dict | None = None


class ApprovalRequestListResponse(BaseModel):
    items: list[ApprovalRequestSummary]
    total: int
    page: int
    page_size: int
    pages: int
