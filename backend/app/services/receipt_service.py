import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from reportlab.lib.colors import HexColor, white
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

PRIMARY = HexColor("#0F3D2E")
ACCENT = HexColor("#C4A35A")
MUTED = HexColor("#5C6B66")
LINE = HexColor("#D8E0DC")
LIGHT_BG = HexColor("#F4F7F5")


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
        left = 2 * cm
        right = width - 2 * cm
        content_width = right - left

        # Bandeau d'en-tête
        c.setFillColor(PRIMARY)
        c.rect(0, height - 3.4 * cm, width, 3.4 * cm, fill=1, stroke=0)
        c.setFillColor(ACCENT)
        c.rect(0, height - 3.55 * cm, width, 0.15 * cm, fill=1, stroke=0)

        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(left, height - 1.5 * cm, self.agency_name)
        c.setFont("Helvetica", 10)
        c.drawString(left, height - 2.2 * cm, self.agency_address)
        c.setFont("Helvetica", 9)
        c.drawRightString(right, height - 1.5 * cm, "REÇU DE PAIEMENT")
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(right, height - 2.2 * cm, receipt_number)

        y = height - 4.6 * cm
        c.setFillColor(PRIMARY)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(left, y, "Attestation de règlement")
        y -= 0.55 * cm
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 10)
        c.drawString(
            left,
            y,
            f"Émis le {payment.payment_date.strftime('%d/%m/%Y')}",
        )

        # Bloc infos locataire
        y -= 1.1 * cm
        box_top = y + 0.55 * cm
        box_height = 3.1 * cm
        c.setFillColor(LIGHT_BG)
        c.roundRect(left, box_top - box_height, content_width, box_height, 8, fill=1, stroke=0)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.8)
        c.roundRect(left, box_top - box_height, content_width, box_height, 8, fill=0, stroke=1)

        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawString(left + 0.4 * cm, y, "LOCATAIRE")
        c.setFillColor(PRIMARY)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left + 0.4 * cm, y - 0.5 * cm, f"{tenant.first_name} {tenant.last_name}")
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 10)
        c.drawString(left + 0.4 * cm, y - 1.05 * cm, f"Tél. {tenant.phone_primary}")
        c.drawString(
            left + 0.4 * cm,
            y - 1.55 * cm,
            f"Logement {unit.code} — {building.name}",
        )
        y = box_top - box_height - 0.9 * cm

        # Tableau échéances
        c.setFillColor(PRIMARY)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left, y, "Détail des échéances")
        y -= 0.55 * cm

        header_h = 0.7 * cm
        c.setFillColor(PRIMARY)
        c.rect(left, y - header_h + 0.15 * cm, content_width, header_h, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(left + 0.35 * cm, y - 0.3 * cm, "Période")
        c.drawRightString(right - 0.35 * cm, y - 0.3 * cm, "Montant")
        y -= header_h + 0.15 * cm

        c.setFont("Helvetica", 10)
        for index, allocation in enumerate(payment.allocations):
            period = allocation.rent_period
            label = f"{period.period_month:02d}/{period.period_year}"
            amount = f"{allocation.allocated_amount:,.0f} FG".replace(",", " ")
            row_h = 0.65 * cm
            if index % 2 == 0:
                c.setFillColor(LIGHT_BG)
                c.rect(left, y - row_h + 0.15 * cm, content_width, row_h, fill=1, stroke=0)
            c.setFillColor(PRIMARY)
            c.drawString(left + 0.35 * cm, y - 0.25 * cm, label)
            c.drawRightString(right - 0.35 * cm, y - 0.25 * cm, amount)
            y -= row_h

        # Total
        y -= 0.35 * cm
        c.setFillColor(ACCENT)
        c.roundRect(left, y - 1.1 * cm, content_width, 1.2 * cm, 6, fill=1, stroke=0)
        c.setFillColor(PRIMARY)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left + 0.4 * cm, y - 0.45 * cm, "TOTAL PAYÉ")
        c.setFont("Helvetica-Bold", 14)
        total = f"{payment.amount:,.0f} FG".replace(",", " ")
        c.drawRightString(right - 0.4 * cm, y - 0.5 * cm, total)
        y -= 1.8 * cm

        # Infos paiement
        method = PAYMENT_METHOD_LABELS.get(
            payment.payment_method.value, payment.payment_method.value
        )
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 9)
        c.drawString(left, y, "MODE DE PAIEMENT")
        c.drawString(left + 8 * cm, y, "ENREGISTRÉ PAR")
        y -= 0.45 * cm
        c.setFillColor(PRIMARY)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left, y, method)
        recorder_name = f"{payment.recorder.first_name} {payment.recorder.last_name}"
        c.drawString(left + 8 * cm, y, recorder_name)
        y -= 0.7 * cm
        if payment.reference:
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 9)
            c.drawString(left, y, "RÉFÉRENCE")
            y -= 0.4 * cm
            c.setFillColor(PRIMARY)
            c.setFont("Helvetica", 10)
            c.drawString(left, y, payment.reference)
            y -= 0.8 * cm

        # Zone signature
        y = min(y - 0.6 * cm, 5.5 * cm)
        c.setStrokeColor(LINE)
        c.setLineWidth(1)
        c.line(left, y, left + 7 * cm, y)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 9)
        c.drawString(left, y - 0.45 * cm, "Signature et cachet de l'agence")

        # Pied de page
        c.setFillColor(LINE)
        c.rect(0, 0, width, 1.4 * cm, fill=1, stroke=0)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawCentredString(
            width / 2,
            0.7 * cm,
            "Document généré automatiquement — valable sans signature manuscrite si émis par l'agence.",
        )
        c.setFillColor(PRIMARY)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(width / 2, 0.35 * cm, self.agency_address)

        c.save()
