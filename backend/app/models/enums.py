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
