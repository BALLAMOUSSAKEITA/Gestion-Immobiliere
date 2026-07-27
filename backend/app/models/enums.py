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
