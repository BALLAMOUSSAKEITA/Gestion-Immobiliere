from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.building import Unit
from app.models.payment import Payment, Receipt
from app.models.tenant import Lease
from app.models.user import User
from app.schemas.receipt import (
    ReceiptDetail,
    ReceiptListResponse,
    ReceiptSummary,
    SendReceiptResponse,
)
from app.schemas.notification import WhatsAppLinkResponse
from app.services.building_service import BuildingAccessService
from app.services.notification_service import NotificationService
from app.services.receipt_service import ReceiptService

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.get("", response_model=ReceiptListResponse)
def list_receipts(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ReceiptListResponse:
    _ensure_read_access(current_user)
    query = (
        db.query(Receipt)
        .join(Payment)
        .join(Payment.lease)
        .join(Unit)
        .options(
            joinedload(Receipt.payment).joinedload(Payment.tenant),
            joinedload(Receipt.payment).joinedload(Payment.lease).joinedload(Lease.unit),
            joinedload(Receipt.issuer),
        )
    )

    allowed = BuildingAccessService.accessible_building_ids(db, current_user)
    if allowed is not None:
        query = query.filter(Unit.building_id.in_(allowed) if allowed else Unit.id.is_(None))

    if current_user.role.code == "locataire":
        if current_user.tenant_profile is None:
            query = query.filter(Receipt.id.is_(None))
        else:
            query = query.filter(Payment.tenant_id == current_user.tenant_profile.id)

    total = query.count()
    receipts = (
        query.order_by(Receipt.issued_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    pages = ceil(total / page_size) if total else 0
    return ReceiptListResponse(
        items=[_to_summary(receipt) for receipt in receipts],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{receipt_id}", response_model=ReceiptDetail)
def get_receipt(
    receipt_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReceiptDetail:
    receipt = _get_receipt_or_404(db, receipt_id)
    _ensure_receipt_access(db, current_user, receipt)
    return _to_detail(receipt)


@router.get("/{receipt_id}/pdf")
def download_receipt_pdf(
    receipt_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    receipt = _get_receipt_or_404(db, receipt_id)
    _ensure_receipt_access(db, current_user, receipt)
    try:
        path = ReceiptService(db).get_pdf_path(receipt_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="PDF introuvable") from exc
    return FileResponse(path, media_type="application/pdf", filename=f"{receipt.receipt_number}.pdf")


@router.post("/{receipt_id}/send-email", response_model=SendReceiptResponse)
def send_receipt_email(
    receipt_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SendReceiptResponse:
    if current_user.role.code not in ("super_admin", "admin_familial", "gestionnaire"):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    receipt = _get_receipt_or_404(db, receipt_id)
    _ensure_receipt_access(db, current_user, receipt)
    sent_at = ReceiptService(db).send_email(receipt_id)
    return SendReceiptResponse(message="Reçu envoyé par email", sent_at=sent_at)


@router.post("/{receipt_id}/send-whatsapp", response_model=WhatsAppLinkResponse)
def send_receipt_whatsapp(
    receipt_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> WhatsAppLinkResponse:
    if current_user.role.code not in ("super_admin", "admin_familial", "gestionnaire"):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    receipt = _get_receipt_or_404(db, receipt_id)
    _ensure_receipt_access(db, current_user, receipt)
    tenant = receipt.payment.tenant
    phone = tenant.phone_primary
    from app.core.config import get_settings

    settings = get_settings()
    message = (
        f"Bonjour {tenant.first_name}, voici votre reçu {receipt.receipt_number}. "
        f"Téléchargement : {settings.public_api_url}{receipt.pdf_url}"
    )
    url = NotificationService(db).build_whatsapp_link(phone, message)
    return WhatsAppLinkResponse(url=url, message=message)


def _ensure_read_access(actor: User) -> None:
    if actor.role.code not in (
        "super_admin",
        "admin_familial",
        "gestionnaire",
        "locataire",
    ):
        raise HTTPException(status_code=403, detail="Accès non autorisé")


def _get_receipt_or_404(db: Session, receipt_id: UUID) -> Receipt:
    receipt = (
        db.query(Receipt)
        .options(
            joinedload(Receipt.payment).joinedload(Payment.tenant),
            joinedload(Receipt.payment).joinedload(Payment.lease).joinedload(Lease.unit),
            joinedload(Receipt.issuer),
        )
        .filter(Receipt.id == receipt_id)
        .first()
    )
    if receipt is None:
        raise HTTPException(status_code=404, detail="Reçu introuvable")
    return receipt


def _ensure_receipt_access(db: Session, actor: User, receipt: Receipt) -> None:
    lease: Lease = receipt.payment.lease
    BuildingAccessService.ensure_building_access(db, actor, lease.unit.building_id)
    if actor.role.code == "locataire":
        if actor.tenant_profile is None or receipt.payment.tenant_id != actor.tenant_profile.id:
            raise HTTPException(status_code=403, detail="Accès non autorisé")


def _to_summary(receipt: Receipt) -> ReceiptSummary:
    payment = receipt.payment
    return ReceiptSummary(
        id=str(receipt.id),
        payment_id=str(receipt.payment_id),
        receipt_number=receipt.receipt_number,
        pdf_url=receipt.pdf_url,
        issued_at=receipt.issued_at,
        issued_by_name=f"{receipt.issuer.first_name} {receipt.issuer.last_name}",
        tenant_name=f"{payment.tenant.first_name} {payment.tenant.last_name}",
        unit_code=payment.lease.unit.code,
        amount=str(payment.amount),
        status=receipt.status,
        sent_email_at=receipt.sent_email_at,
    )


def _to_detail(receipt: Receipt) -> ReceiptDetail:
    payment = receipt.payment
    summary = _to_summary(receipt)
    return ReceiptDetail(
        **summary.model_dump(),
        payment_date=payment.payment_date.isoformat(),
        payment_method=payment.payment_method.value,
    )
