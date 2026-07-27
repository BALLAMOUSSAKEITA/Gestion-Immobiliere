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


class RepairStatus(str, enum.Enum):
    new = "new"
    under_review = "under_review"
    technician_assigned = "technician_assigned"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class UrgencyLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RepairAttachmentType(str, enum.Enum):
    photo = "photo"
    video = "video"
    document = "document"


class EntityType(str, enum.Enum):
    building = "building"
    unit = "unit"
    tenant = "tenant"
    lease = "lease"
    payment = "payment"
    expense = "expense"
    repair = "repair"
    owner_profile = "owner_profile"
    receipt = "receipt"
    document = "document"


class ApprovalRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"


class ReportType(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    annual = "annual"


class VisitRequestStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class NoticeType(str, enum.Enum):
    info = "info"
    warning = "warning"
    payment_reminder = "payment_reminder"
    maintenance = "maintenance"
    other = "other"
