import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.building import Building, Unit
from app.models.enums import UnitType


class CodeGeneratorService:
    def __init__(self, db: Session, prefix: str = "KM") -> None:
        self.db = db
        self.prefix = prefix.upper()

    def generate_building_code(self) -> str:
        pattern = re.compile(rf"^{re.escape(self.prefix)}(\d{{3}})$")
        codes = [row[0] for row in self.db.query(Building.code).all()]
        numbers = []
        for code in codes:
            match = pattern.match(code)
            if match:
                numbers.append(int(match.group(1)))
        next_number = max(numbers, default=0) + 1
        return f"{self.prefix}{next_number:03d}"

    def generate_unit_code(
        self,
        building_code: str,
        unit_type: UnitType,
        number: str,
        floor: int | None = None,
    ) -> str:
        normalized_number = number.strip().zfill(2)
        if unit_type == UnitType.apartment:
            floor_part = str(floor if floor is not None else 0)
            candidate = f"{building_code}-A{floor_part}{normalized_number}"
        elif unit_type == UnitType.shop:
            candidate = f"{building_code}-M{normalized_number}"
        else:
            candidate = f"{building_code}-B{normalized_number}"

        if self.db.query(Unit.id).filter(Unit.code == candidate).first():
            suffix = 1
            while True:
                alt = f"{candidate}-{suffix}"
                if not self.db.query(Unit.id).filter(Unit.code == alt).first():
                    return alt
                suffix += 1
        return candidate

    def ensure_building_code_unique(self, code: str) -> None:
        if self.db.query(Building.id).filter(Building.code == code).first():
            raise ValueError(f"Le code immeuble {code} existe déjà")

    def ensure_unit_code_unique(self, code: str) -> None:
        if self.db.query(Unit.id).filter(Unit.code == code).first():
            raise ValueError(f"Le code logement {code} existe déjà")
