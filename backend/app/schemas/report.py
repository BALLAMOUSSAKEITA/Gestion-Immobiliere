from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import ReportType, UnitType


class ReportFilters(BaseModel):
    building_id: str | None = None
    owner_profile_id: str | None = None
    tenant_id: str | None = None
    manager_user_id: str | None = None
    unit_type: UnitType | None = None


class ReportGenerateRequest(BaseModel):
    report_type: ReportType
    period_start: date
    period_end: date
    filters: ReportFilters | None = None
    export_formats: list[str] = Field(default_factory=lambda: ["pdf", "excel"])


class ReportSummary(BaseModel):
    id: str
    report_type: ReportType
    period_start: date
    period_end: date
    filters: dict | None
    pdf_url: str | None
    excel_url: str | None
    generated_by_name: str | None
    generated_at: datetime


class ReportDetail(ReportSummary):
    data: dict


class ReportListResponse(BaseModel):
    items: list[ReportSummary]
    total: int
    page: int
    page_size: int
    pages: int
