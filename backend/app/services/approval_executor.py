from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core import approval_actions as actions
from app.models.audit import ApprovalRequest
from app.models.building import Building
from app.models.document import Document
from app.models.enums import (
    ExpenseStatus,
    PaymentRecordStatus,
    ReceiptStatus,
)
from app.models.expense import Expense
from app.models.payment import Payment, PaymentAllocation, Receipt
from app.models.tenant import Lease, Tenant
from app.models.user import User
from app.schemas.lease import LeaseUpdate
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService
from app.services.expense_service import ExpenseService
from app.services.lease_service import LeaseService
from app.services.rent_period_service import RentPeriodService
from app.services.storage_service import StorageService
from app.services.tenant_service import TenantService


class ApprovalExecutor:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def execute(
        self,
        request: ApprovalRequest,
        reviewer: User,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        handlers = {
            actions.PAYMENT_DELETE: self._payment_delete,
            actions.PAYMENT_UPDATE_AMOUNT: self._payment_update_amount,
            actions.TENANT_DELETE: self._tenant_delete,
            actions.BUILDING_CHANGE_OWNER: self._building_change_owner,
            actions.LEASE_UPDATE: self._lease_update,
            actions.EXPENSE_VALIDATE: self._expense_validate,
            actions.RECEIPT_CANCEL: self._receipt_cancel,
            actions.DOCUMENT_DELETE: self._document_delete,
        }
        handler = handlers.get(request.action_code)
        if handler is None:
            raise HTTPException(status_code=400, detail="Action non supportée")
        result = handler(request, reviewer)
        self.audit.log(
            user=reviewer,
            action=f"{request.action_code}.executed",
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            old_values=request.payload_before,
            new_values=request.payload_after or result,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return result

    def _payment_delete(self, request: ApprovalRequest, reviewer: User) -> dict:
        from app.services.payment_service import PaymentService

        payment = self._get_payment(request.entity_id)
        old = {"amount": str(payment.amount), "status": payment.status.value}
        PaymentService(self.db).delete_payment(reviewer, payment.id)
        return old

    def _payment_update_amount(self, request: ApprovalRequest, reviewer: User) -> dict:
        if not request.payload_after or "amount" not in request.payload_after:
            raise HTTPException(status_code=400, detail="Montant manquant dans la demande")
        payment = self._get_payment(request.entity_id)
        old_amount = payment.amount
        new_amount = Decimal(str(request.payload_after["amount"]))
        if new_amount <= 0:
            raise HTTPException(status_code=400, detail="Montant invalide")
        payment.amount = new_amount
        self.db.flush()
        return {"amount": str(old_amount), "new_amount": str(new_amount)}

    def _tenant_delete(self, request: ApprovalRequest, reviewer: User) -> dict:
        TenantService(self.db).deactivate_tenant(reviewer, request.entity_id)
        return {"is_active": False}

    def _building_change_owner(self, request: ApprovalRequest, reviewer: User) -> dict:
        if not request.payload_after or "owner_profile_id" not in request.payload_after:
            raise HTTPException(status_code=400, detail="Propriétaire manquant")
        building = self.db.get(Building, request.entity_id)
        if building is None:
            raise HTTPException(status_code=404, detail="Immeuble introuvable")
        old_owner = str(building.owner_profile_id) if building.owner_profile_id else None
        new_owner = request.payload_after["owner_profile_id"]
        building.owner_profile_id = UUID(new_owner) if new_owner else None
        self.db.flush()
        return {"owner_profile_id": old_owner, "new_owner_profile_id": new_owner}

    def _lease_update(self, request: ApprovalRequest, reviewer: User) -> dict:
        if not request.payload_after:
            raise HTTPException(status_code=400, detail="Modifications manquantes")
        payload = LeaseUpdate.model_validate(request.payload_after)
        LeaseService(self.db).update_lease(reviewer, request.entity_id, payload)
        return request.payload_after

    def _expense_validate(self, request: ApprovalRequest, reviewer: User) -> dict:
        ExpenseService(self.db).validate_expense(reviewer, request.entity_id)
        return {"status": ExpenseStatus.validated.value}

    def _receipt_cancel(self, request: ApprovalRequest, reviewer: User) -> dict:
        receipt = self._get_receipt(request.entity_id)
        if receipt.status == ReceiptStatus.cancelled:
            raise HTTPException(status_code=400, detail="Reçu déjà annulé")
        receipt.status = ReceiptStatus.cancelled
        payment = receipt.payment
        if payment.status != PaymentRecordStatus.cancelled:
            period_service = RentPeriodService(self.db)
            for allocation in list(payment.allocations):
                period = allocation.rent_period
                period.paid_amount = max(
                    period.paid_amount - allocation.allocated_amount, Decimal("0")
                )
                period_service.refresh_period_status(period, payment.payment_date)
            payment.status = PaymentRecordStatus.cancelled
        self.db.flush()
        return {"receipt_status": ReceiptStatus.cancelled.value}

    def _document_delete(self, request: ApprovalRequest, reviewer: User) -> dict:
        document = self.db.get(Document, request.entity_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document introuvable")
        snapshot = {"title": document.title, "file_name": document.file_name}
        StorageService().delete_file(document.file_url)
        self.db.delete(document)
        self.db.flush()
        return snapshot

    def _get_payment(self, payment_id: UUID) -> Payment:
        payment = (
            self.db.query(Payment)
            .options(
                joinedload(Payment.allocations).joinedload(PaymentAllocation.rent_period)
            )
            .filter(Payment.id == payment_id)
            .first()
        )
        if payment is None:
            raise HTTPException(status_code=404, detail="Paiement introuvable")
        return payment

    def _get_receipt(self, receipt_id: UUID) -> Receipt:
        receipt = (
            self.db.query(Receipt)
            .options(
                joinedload(Receipt.payment)
                .joinedload(Payment.allocations)
                .joinedload(PaymentAllocation.rent_period)
            )
            .filter(Receipt.id == receipt_id)
            .first()
        )
        if receipt is None:
            raise HTTPException(status_code=404, detail="Reçu introuvable")
        return receipt

    def capture_entity_snapshot(
        self, action_code: str, entity_type: str, entity_id: UUID
    ) -> dict | None:
        if action_code == actions.PAYMENT_DELETE or action_code == actions.PAYMENT_UPDATE_AMOUNT:
            payment = self.db.get(Payment, entity_id)
            if payment:
                return {"amount": str(payment.amount), "status": payment.status.value}
        if action_code == actions.TENANT_DELETE:
            tenant = self.db.get(Tenant, entity_id)
            if tenant:
                return {"is_active": tenant.is_active}
        if action_code == actions.BUILDING_CHANGE_OWNER:
            building = self.db.get(Building, entity_id)
            if building:
                return {
                    "owner_profile_id": str(building.owner_profile_id)
                    if building.owner_profile_id
                    else None
                }
        if action_code == actions.LEASE_UPDATE:
            lease = self.db.get(Lease, entity_id)
            if lease:
                return {
                    "start_date": lease.start_date.isoformat(),
                    "end_date": lease.end_date.isoformat() if lease.end_date else None,
                    "deposit_paid": str(lease.deposit_paid),
                }
        if action_code == actions.EXPENSE_VALIDATE:
            expense = self.db.get(Expense, entity_id)
            if expense:
                return {"status": expense.status.value, "amount": str(expense.amount)}
        if action_code == actions.RECEIPT_CANCEL:
            receipt = self.db.get(Receipt, entity_id)
            if receipt:
                return {"status": receipt.status.value}
        if action_code == actions.DOCUMENT_DELETE:
            document = self.db.get(Document, entity_id)
            if document:
                return {"title": document.title, "file_name": document.file_name}
        return None
