from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import PaymentMethod, PaymentRecordStatus, RentPeriodStatus


class PeriodAllocationInput(BaseModel):
    period_year: int = Field(ge=2000)
    period_month: int = Field(ge=1, le=12)
    amount: Decimal = Field(gt=0)


class PaymentCreate(BaseModel):
    lease_id: str
    amount: Decimal | None = Field(default=None, gt=0)
    payment_method: PaymentMethod
    payment_date: date
    covered_from: date | None = None
    covered_to: date | None = None
    reference: str | None = None
    notes: str | None = None
    allocations: list[PeriodAllocationInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_amount_or_period(self) -> "PaymentCreate":
        if self.covered_from and self.covered_to and self.covered_from > self.covered_to:
            raise ValueError(
                "La date de fin de période doit être postérieure à la date de début"
            )
        if (
            self.amount is None
            and not self.allocations
            and (self.covered_from is None or self.covered_to is None)
        ):
            raise ValueError("Indiquez un montant ou une période couverte par le paiement")
        return self


class PaymentAllocationResponse(BaseModel):
    period_year: int
    period_month: int
    allocated_amount: Decimal


class PaymentSummary(BaseModel):
    id: str
    lease_id: str
    tenant_id: str
    tenant_name: str
    unit_code: str
    amount: Decimal
    payment_method: PaymentMethod
    payment_date: date
    covered_from: date | None = None
    covered_to: date | None = None
    reference: str | None
    status: PaymentRecordStatus
    recorded_by_name: str
    created_at: datetime
    receipt_id: str | None = None
    receipt_number: str | None = None


class PaymentDetail(PaymentSummary):
    proof_url: str | None
    notes: str | None
    allocations: list[PaymentAllocationResponse]
    validated_by_name: str | None
    validated_at: datetime | None
    updated_at: datetime


class PaymentListResponse(BaseModel):
    items: list[PaymentSummary]
    total: int
    page: int
    page_size: int
    pages: int


class RentPeriodResponse(BaseModel):
    id: str
    period_year: int
    period_month: int
    expected_amount: Decimal
    paid_amount: Decimal
    remaining_amount: Decimal
    status: RentPeriodStatus
    due_date: date
