import logging
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models.building import Unit
from app.models.payment import Payment, PaymentAllocation, Receipt
from app.models.tenant import Lease, Tenant
from app.services.rent_period_service import ReceiptNumberService

logger = logging.getLogger(__name__)

PAYMENT_METHOD_LABELS = {
    "cash": "Espèces",
    "orange_money": "Orange Money",
    "wave": "Wave",
    "bank_transfer": "Virement bancaire",
}


class ReceiptService:
    def __init__(self, db: Session) -> None:
        self.db = db
        settings = get_settings()
        self.upload_dir = Path(settings.upload_dir)
        self.agency_name = settings.agency_name
        self.agency_address = settings.agency_address

    def generate_for_payment(self, payment: Payment, issuer_id: UUID) -> Receipt:
        if payment.receipt:
            return payment.receipt

        receipt_number = ReceiptNumberService(self.db).next_number(
            payment.payment_date.year
        )
        pdf_path = self.upload_dir / "receipts" / f"{receipt_number}.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        payment = (
            self.db.query(Payment)
            .options(
                joinedload(Payment.allocations).joinedload(PaymentAllocation.rent_period),
                joinedload(Payment.lease).joinedload(Lease.unit).joinedload(Unit.building),
                joinedload(Payment.tenant),
                joinedload(Payment.recorder),
            )
            .filter(Payment.id == payment.id)
            .first()
        )
        assert payment is not None

        self._write_pdf(pdf_path, payment, receipt_number)

        receipt = Receipt(
            payment_id=payment.id,
            receipt_number=receipt_number,
            pdf_url=f"/uploads/receipts/{receipt_number}.pdf",
            issued_by=issuer_id,
        )
        self.db.add(receipt)
        self.db.flush()
        return receipt

    def send_email(self, receipt_id: UUID) -> datetime:
        from app.core.config import get_settings
        from app.services.notification_hooks import notify_receipt_available

        receipt = self._get_or_404(receipt_id)
        sent_at = datetime.now(UTC)
        receipt.sent_email_at = sent_at
        self.db.commit()
        settings = get_settings()
        notify_receipt_available(self.db, receipt, settings.public_api_url)
        return sent_at

    def get_pdf_path(self, receipt_id: UUID) -> Path:
        receipt = self._get_or_404(receipt_id)
        relative = receipt.pdf_url.removeprefix("/uploads/")
        path = self.upload_dir / relative
        if not path.exists():
            raise FileNotFoundError("PDF introuvable")
        return path

    def _get_or_404(self, receipt_id: UUID) -> Receipt:
        receipt = (
            self.db.query(Receipt)
            .options(
                joinedload(Receipt.payment).joinedload(Payment.tenant).joinedload(Tenant.user),
                joinedload(Receipt.payment).joinedload(Payment.lease),
                joinedload(Receipt.issuer),
            )
            .filter(Receipt.id == receipt_id)
            .first()
        )
        if receipt is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Reçu introuvable")
        return receipt

    def _write_pdf(self, path: Path, payment: Payment, receipt_number: str) -> None:
        lease = payment.lease
        tenant = payment.tenant
        unit = lease.unit
        building = unit.building

        c = canvas.Canvas(str(path), pagesize=A4)
        width, height = A4
        y = height - 2 * cm

        c.setFont("Helvetica-Bold", 16)
        c.drawString(2 * cm, y, self.agency_name)
        y -= 0.7 * cm
        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y, self.agency_address)
        y -= 1.5 * cm

        c.setFont("Helvetica-Bold", 14)
        c.drawString(2 * cm, y, f"REÇU DE PAIEMENT N° {receipt_number}")
        y -= 1 * cm
        c.setFont("Helvetica", 11)
        c.drawString(2 * cm, y, f"Date d'émission : {payment.payment_date.isoformat()}")
        y -= 1.2 * cm

        c.drawString(2 * cm, y, f"Locataire : {tenant.first_name} {tenant.last_name}")
        y -= 0.6 * cm
        c.drawString(2 * cm, y, f"Téléphone : {tenant.phone_primary}")
        y -= 0.6 * cm
        c.drawString(
            2 * cm,
            y,
            f"Logement : {unit.code} — {building.name}",
        )
        y -= 1.2 * cm

        c.setFont("Helvetica-Bold", 11)
        c.drawString(2 * cm, y, "Détail des échéances payées")
        y -= 0.8 * cm
        c.setFont("Helvetica", 10)

        for allocation in payment.allocations:
            period = allocation.rent_period
            label = f"{period.period_month:02d}/{period.period_year}"
            line = f"  • {label} : {allocation.allocated_amount:,.0f} FG".replace(",", " ")
            c.drawString(2 * cm, y, line)
            y -= 0.5 * cm

        y -= 0.5 * cm
        c.setFont("Helvetica-Bold", 12)
        total_line = f"TOTAL : {payment.amount:,.0f} FG".replace(",", " ")
        c.drawString(2 * cm, y, total_line)
        y -= 1 * cm

        c.setFont("Helvetica", 10)
        method = PAYMENT_METHOD_LABELS.get(payment.payment_method.value, payment.payment_method.value)
        c.drawString(2 * cm, y, f"Mode de paiement : {method}")
        y -= 0.5 * cm
        if payment.reference:
            c.drawString(2 * cm, y, f"Référence : {payment.reference}")
            y -= 0.5 * cm

        y -= 1 * cm
        recorder_name = f"{payment.recorder.first_name} {payment.recorder.last_name}"
        c.drawString(2 * cm, y, f"Enregistré par : {recorder_name}")
        y -= 1.5 * cm
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(2 * cm, y, "Reçu non valable sans signature.")

        c.save()
