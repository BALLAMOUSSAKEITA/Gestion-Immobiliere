from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.report import ReportDetail, ReportGenerateRequest, ReportListResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=ReportListResponse)
def list_reports(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ReportListResponse:
    return ReportService(db).list_reports(current_user, page=page, page_size=page_size)


@router.post("/generate", response_model=ReportDetail, status_code=201)
def generate_report(
    payload: ReportGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReportDetail:
    return ReportService(db).generate_report(current_user, payload)


@router.get("/{report_id}", response_model=ReportDetail)
def get_report(
    report_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReportDetail:
    return ReportService(db).get_report(current_user, report_id)


@router.get("/{report_id}/pdf")
def download_report_pdf(
    report_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    path = ReportService(db).get_pdf_path(current_user, report_id)
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@router.get("/{report_id}/excel")
def download_report_excel(
    report_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    path = ReportService(db).get_excel_path(current_user, report_id)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=path.name,
    )
