"""Centralized notification hooks for business events."""

from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.building import Unit
from app.models.payment import Payment, Receipt
from app.models.portal import VisitRequest
from app.models.repair import Repair
from app.models.role import Role
from app.models.tenant import Lease, Tenant
from app.models.user import User
from app.services.notification_service import NotificationService


def _manager_user_ids(db: Session, building_id: UUID | None = None) -> list[UUID]:
    query = (
        db.query(User.id)
        .join(Role)
        .filter(Role.code.in_(("gestionnaire", "super_admin", "admin_familial")), User.is_active.is_(True))
    )
    if building_id:
        from app.models.building import Building

        building = db.query(Building).filter(Building.id == building_id).first()
        if building and building.manager_user_id:
            return [building.manager_user_id]
    return [row[0] for row in query.all()]


def _admin_user_ids(db: Session) -> list[UUID]:
    rows = (
        db.query(User.id)
        .join(Role)
        .filter(Role.code.in_(("super_admin", "admin_familial")), User.is_active.is_(True))
        .all()
    )
    return [row[0] for row in rows]


def _tenant_user_id(tenant: Tenant) -> UUID | None:
    return tenant.user_id


def notify_payment_recorded(db: Session, payment: Payment) -> None:
    payment = (
        db.query(Payment)
        .options(
            joinedload(Payment.tenant),
            joinedload(Payment.lease).joinedload(Lease.unit),
        )
        .filter(Payment.id == payment.id)
        .first()
    )
    if payment is None:
        return
    tenant_user = _tenant_user_id(payment.tenant)
    if tenant_user is None:
        return
    unit_code = payment.lease.unit.code if payment.lease and payment.lease.unit else "—"
    amount = f"{payment.amount:,.0f}".replace(",", " ")
    NotificationService(db).dispatch(
        "payment.recorded",
        [tenant_user],
        title="Paiement enregistré",
        body=f"Votre paiement de {amount} FG pour {unit_code} a été enregistré.",
        entity_type="payment",
        entity_id=payment.id,
        email_template="payment_confirmation.html",
        email_context={"amount": amount, "unit_code": unit_code},
    )


def notify_receipt_available(db: Session, receipt: Receipt, base_url: str = "http://localhost:8000") -> None:
    receipt = (
        db.query(Receipt)
        .options(joinedload(Receipt.payment).joinedload(Payment.tenant))
        .filter(Receipt.id == receipt.id)
        .first()
    )
    if receipt is None:
        return
    tenant_user = _tenant_user_id(receipt.payment.tenant)
    if tenant_user is None:
        return
    NotificationService(db).dispatch(
        "receipt.available",
        [tenant_user],
        title="Reçu disponible",
        body=f"Votre reçu {receipt.receipt_number} est disponible au téléchargement.",
        entity_type="receipt",
        entity_id=receipt.id,
        email_template="receipt_available.html",
        email_context={
            "receipt_number": receipt.receipt_number,
            "receipt_url": f"{base_url}{receipt.pdf_url}",
        },
    )


def notify_repair_new(db: Session, repair: Repair) -> None:
    repair = (
        db.query(Repair)
        .options(joinedload(Repair.unit))
        .filter(Repair.id == repair.id)
        .first()
    )
    if repair is None:
        return
    recipients = _manager_user_ids(db, repair.building_id)
    NotificationService(db).dispatch(
        "repair.new",
        recipients,
        title="Nouvelle demande de réparation",
        body=f"{repair.title} — logement {repair.unit.code if repair.unit else '—'}.",
        entity_type="repair",
        entity_id=repair.id,
        email_template="repair_new.html",
        email_context={
            "unit_code": repair.unit.code if repair.unit else "—",
            "repair_title": repair.title,
        },
    )


def notify_visit_requested(db: Session, request: VisitRequest) -> None:
    request = (
        db.query(VisitRequest)
        .options(joinedload(VisitRequest.unit))
        .filter(VisitRequest.id == request.id)
        .first()
    )
    if request is None or request.unit is None:
        return
    recipients = _manager_user_ids(db, request.unit.building_id)
    NotificationService(db).dispatch(
        "visit.requested",
        recipients,
        title="Nouvelle demande de visite",
        body=f"{request.visitor_name} souhaite visiter {request.unit.code}.",
        entity_type="visit_request",
        entity_id=request.id,
        email_template="visit_request.html",
        email_context={
            "visitor_name": request.visitor_name,
            "visitor_email": request.visitor_email,
            "unit_code": request.unit.code,
        },
    )


def notify_message_received(db: Session, recipient_user_id: UUID, subject: str, sender_name: str) -> None:
    NotificationService(db).dispatch(
        "message.received",
        [recipient_user_id],
        title="Nouveau message",
        body=f"{sender_name} : {subject}",
        entity_type="message",
    )


def notify_approval_reviewed(
    db: Session, requester_id: UUID, approved: bool, comment: str | None = None
) -> None:
    status_label = "approuvée" if approved else "rejetée"
    NotificationService(db).dispatch(
        "approval.reviewed",
        [requester_id],
        title=f"Demande {status_label}",
        body=f"Votre demande de validation a été {status_label}.",
        entity_type="approval_request",
        email_template="approval_reviewed.html",
        email_context={"status_label": status_label.capitalize(), "comment": comment},
    )


def notify_expense_created(db: Session, building_id: UUID, amount: str, label: str) -> None:
    recipients = _admin_user_ids(db)
    NotificationService(db).dispatch(
        "expense.created",
        recipients,
        title="Nouvelle dépense",
        body=f"{label} — {amount} FG.",
        entity_type="expense",
    )


def notify_document_uploaded(db: Session, user_ids: list[UUID], title: str) -> None:
    if not user_ids:
        return
    NotificationService(db).dispatch(
        "document.uploaded",
        user_ids,
        title="Nouveau document",
        body=f"Document ajouté : {title}.",
        entity_type="document",
    )


def notify_rent_overdue(db: Session, tenant: Tenant, unit_code: str, amount: str) -> None:
    recipients: list[UUID] = []
    tenant_user = _tenant_user_id(tenant)
    if tenant_user:
        recipients.append(tenant_user)
    recipients.extend(_admin_user_ids(db))
    recipients.extend(_manager_user_ids(db))
    NotificationService(db).dispatch(
        "rent.overdue",
        recipients,
        title="Loyer en retard",
        body=f"Loyer impayé pour {unit_code} : {amount} FG restants.",
        email_template="rent_overdue.html",
        email_context={"unit_code": unit_code, "amount": amount},
    )


def notify_rent_due_soon(
    db: Session, tenant: Tenant, unit_code: str, amount: str, due_date: str
) -> None:
    tenant_user = _tenant_user_id(tenant)
    if tenant_user is None:
        return
    NotificationService(db).dispatch(
        "rent.due_soon",
        [tenant_user],
        title="Loyer bientôt exigible",
        body=f"Échéance le {due_date} pour {unit_code} : {amount} FG.",
        email_template="rent_due_soon.html",
        email_context={"due_date": due_date, "amount": amount},
    )


def notify_lease_expiring(
    db: Session, tenant_name: str, unit_code: str, end_date: str
) -> None:
    recipients = _admin_user_ids(db)
    NotificationService(db).dispatch(
        "lease.expiring",
        recipients,
        title="Contrat bientôt expiré",
        body=f"Bail de {tenant_name} ({unit_code}) expire le {end_date}.",
        email_template="lease_expiring.html",
        email_context={"tenant_name": tenant_name, "end_date": end_date},
    )
