from datetime import datetime

from pydantic import BaseModel

from app.models.enums import ReceiptStatus


class ReceiptSummary(BaseModel):
    id: str
    payment_id: str
    receipt_number: str
    pdf_url: str
    issued_at: datetime
    issued_by_name: str
    tenant_name: str
    unit_code: str
    amount: str
    status: ReceiptStatus
    sent_email_at: datetime | None


class ReceiptDetail(ReceiptSummary):
    payment_date: str
    payment_method: str


class ReceiptListResponse(BaseModel):
    items: list[ReceiptSummary]
    total: int
    page: int
    page_size: int
    pages: int


class SendReceiptResponse(BaseModel):
    message: str
    sent_at: datetime
