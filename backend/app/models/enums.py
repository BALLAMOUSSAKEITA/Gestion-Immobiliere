import enum


class UnitType(str, enum.Enum):
    apartment = "apartment"
    shop = "shop"
    office = "office"


class UnitStatus(str, enum.Enum):
    free = "free"
    occupied = "occupied"
    reserved = "reserved"
    under_repair = "under_repair"


class IdDocumentType(str, enum.Enum):
    cni = "cni"
    passport = "passport"
    attestation = "attestation"
    other = "other"


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    orange_money = "orange_money"
    wave = "wave"
    bank_transfer = "bank_transfer"


class LeaseStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    expired = "expired"
    terminated = "terminated"


class RentPeriodStatus(str, enum.Enum):
    pending = "pending"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"


class PaymentRecordStatus(str, enum.Enum):
    recorded = "recorded"
    validated = "validated"
    cancelled = "cancelled"


class ReceiptStatus(str, enum.Enum):
    issued = "issued"
    cancelled = "cancelled"


class OverdueStatus(str, enum.Enum):
    open = "open"
    partially_paid = "partially_paid"
    resolved = "resolved"


class ReminderType(str, enum.Enum):
    before_due = "before_due"
    after_due = "after_due"
    manual = "manual"
    final_notice = "final_notice"


class ReminderChannel(str, enum.Enum):
    in_app = "in_app"
    email = "email"
    sms = "sms"
    whatsapp = "whatsapp"


class ReminderStatus(str, enum.Enum):
    sent = "sent"
    failed = "failed"
    pending = "pending"


class ExpenseStatus(str, enum.Enum):
    recorded = "recorded"
    pending_validation = "pending_validation"
    validated = "validated"
    rejected = "rejected"
