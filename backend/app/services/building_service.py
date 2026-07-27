from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models.building import Building, Unit
from app.models.enums import UnitStatus, UnitType
from app.models.user import User
from app.schemas.building import (
    BuildingCreate,
    BuildingDetail,
    BuildingListResponse,
    BuildingSummary,
    BuildingUpdate,
)
from app.services.code_generator_service import CodeGeneratorService
from app.services.user_service import PermissionService


class BuildingAccessService:
    @staticmethod
    def can_manage(actor: User) -> bool:
        if actor.role.code in ("super_admin", "admin_familial"):
            if actor.role.code == "super_admin":
                return True
            return PermissionService.check(actor, "buildings.manage")
        return False

    @staticmethod
    def get_owner_profile_id(actor: User) -> UUID | None:
        if actor.owner_profile:
            return actor.owner_profile.id
        if actor.owner_assignment:
            return actor.owner_assignment.owner_profile_id
        return None

    @staticmethod
    def accessible_building_ids(db: Session, actor: User) -> set[UUID] | None:
        role = actor.role.code
        if role == "super_admin":
            return None
        if role == "admin_familial":
            if PermissionService.check(actor, "buildings.manage"):
                return None
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")
        if role == "proprietaire":
            owner_profile_id = BuildingAccessService.get_owner_profile_id(actor)
            if owner_profile_id is None:
                return set()
            ids = {
                row[0]
                for row in db.query(Building.id)
                .filter(
                    Building.owner_profile_id == owner_profile_id,
                    Building.is_active.is_(True),
                )
                .all()
            }
            return ids
        if role == "gestionnaire":
            return {
                assignment.building_id
                for assignment in actor.building_assignments
            }
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    @staticmethod
    def ensure_building_access(db: Session, actor: User, building_id: UUID) -> None:
        allowed = BuildingAccessService.accessible_building_ids(db, actor)
        if allowed is not None and building_id not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")


class BuildingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        settings = get_settings()
        self.code_generator = CodeGeneratorService(db, prefix=settings.building_code_prefix)

    def list_buildings(
        self,
        actor: User,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        is_active: bool | None = True,
    ) -> BuildingListResponse:
        self._ensure_read_access(actor)
        query = self.db.query(Building)
        allowed = BuildingAccessService.accessible_building_ids(self.db, actor)
        if allowed is not None:
            query = query.filter(Building.id.in_(allowed) if allowed else Building.id.is_(None))
        if is_active is not None:
            query = query.filter(Building.is_active == is_active)
        if search:
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Building.code).like(term),
                    func.lower(Building.name).like(term),
                    func.lower(Building.commune).like(term),
                )
            )

        total = query.count()
        items = (
            query.order_by(Building.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        pages = ceil(total / page_size) if total else 0
        return BuildingListResponse(
            items=[self._to_summary(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_building(self, actor: User, building_id: UUID) -> BuildingDetail:
        self._ensure_read_access(actor)
        building = self._get_or_404(building_id)
        BuildingAccessService.ensure_building_access(self.db, actor, building_id)
        return self._to_detail(building)

    def create_building(self, actor: User, payload: BuildingCreate) -> BuildingDetail:
        self._ensure_manage_access(actor)
        code = self.code_generator.generate_building_code()
        building = Building(
            code=code,
            name=payload.name.strip(),
            address=payload.address.strip(),
            commune=payload.commune.strip(),
            quartier=payload.quartier.strip() if payload.quartier else None,
            floor_count=payload.floor_count,
            owner_profile_id=UUID(payload.owner_profile_id)
            if payload.owner_profile_id
            else None,
            manager_user_id=UUID(payload.manager_user_id) if payload.manager_user_id else None,
            observations=payload.observations,
            created_by=actor.id,
        )
        self.db.add(building)
        self.db.commit()
        self.db.refresh(building)
        return self._to_detail(building)

    def update_building(
        self, actor: User, building_id: UUID, payload: BuildingUpdate
    ) -> BuildingDetail:
        self._ensure_manage_access(actor)
        building = self._get_or_404(building_id)
        BuildingAccessService.ensure_building_access(self.db, actor, building_id)

        if payload.name is not None:
            building.name = payload.name.strip()
        if payload.address is not None:
            building.address = payload.address.strip()
        if payload.commune is not None:
            building.commune = payload.commune.strip()
        if payload.quartier is not None:
            building.quartier = payload.quartier.strip() if payload.quartier else None
        if payload.floor_count is not None:
            building.floor_count = payload.floor_count
        if payload.owner_profile_id is not None:
            building.owner_profile_id = (
                UUID(payload.owner_profile_id) if payload.owner_profile_id else None
            )
        if payload.manager_user_id is not None:
            building.manager_user_id = (
                UUID(payload.manager_user_id) if payload.manager_user_id else None
            )
        if payload.observations is not None:
            building.observations = payload.observations
        if payload.is_active is not None:
            building.is_active = payload.is_active

        self.db.commit()
        self.db.refresh(building)
        return self._to_detail(building)

    def deactivate_building(self, actor: User, building_id: UUID) -> None:
        if actor.role.code != "super_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")
        building = self._get_or_404(building_id)
        occupied = (
            self.db.query(Unit)
            .filter(
                Unit.building_id == building_id,
                Unit.status == UnitStatus.occupied,
                Unit.is_active.is_(True),
            )
            .count()
        )
        if occupied > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible de supprimer un immeuble avec des logements occupés",
            )
        building.is_active = False
        self.db.commit()

    def set_photo_url(self, actor: User, building_id: UUID, photo_url: str) -> BuildingDetail:
        self._ensure_manage_access(actor)
        building = self._get_or_404(building_id)
        BuildingAccessService.ensure_building_access(self.db, actor, building_id)
        building.photo_url = photo_url
        self.db.commit()
        self.db.refresh(building)
        return self._to_detail(building)

    def recalculate_unit_counts(self, building_id: UUID) -> None:
        building = self._get_or_404(building_id)
        units = (
            self.db.query(Unit)
            .filter(Unit.building_id == building_id, Unit.is_active.is_(True))
            .all()
        )
        building.apartment_count = sum(1 for unit in units if unit.type == UnitType.apartment)
        building.shop_count = sum(
            1 for unit in units if unit.type in (UnitType.shop, UnitType.office)
        )
        self.db.commit()

    def _get_or_404(self, building_id: UUID) -> Building:
        building = (
            self.db.query(Building)
            .options(joinedload(Building.units))
            .filter(Building.id == building_id)
            .first()
        )
        if building is None:
            raise HTTPException(status_code=404, detail="Immeuble introuvable")
        return building

    def _ensure_read_access(self, actor: User) -> None:
        if actor.role.code not in ("super_admin", "admin_familial", "proprietaire", "gestionnaire"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    def _ensure_manage_access(self, actor: User) -> None:
        if not BuildingAccessService.can_manage(actor):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    def _to_summary(self, building: Building) -> BuildingSummary:
        return BuildingSummary(
            id=str(building.id),
            code=building.code,
            name=building.name,
            address=building.address,
            commune=building.commune,
            quartier=building.quartier,
            photo_url=building.photo_url,
            floor_count=building.floor_count,
            apartment_count=building.apartment_count,
            shop_count=building.shop_count,
            owner_profile_id=str(building.owner_profile_id)
            if building.owner_profile_id
            else None,
            manager_user_id=str(building.manager_user_id) if building.manager_user_id else None,
            is_active=building.is_active,
            created_at=building.created_at,
        )

    def _to_detail(self, building: Building) -> BuildingDetail:
        active_units = [
            unit for unit in building.units if unit.is_active
        ] if building.units else (
            self.db.query(Unit)
            .filter(Unit.building_id == building.id, Unit.is_active.is_(True))
            .all()
        )
        total_units = len(active_units)
        occupied_units = sum(1 for unit in active_units if unit.status == UnitStatus.occupied)
        free_units = sum(1 for unit in active_units if unit.status == UnitStatus.free)
        under_repair_units = sum(
            1 for unit in active_units if unit.status == UnitStatus.under_repair
        )
        occupancy_rate = (occupied_units / total_units * 100) if total_units else 0.0
        monthly_expected_rent = sum(
            unit.rent_amount
            for unit in active_units
            if unit.status in (UnitStatus.occupied, UnitStatus.reserved)
        )

        summary = self._to_summary(building)
        return BuildingDetail(
            **summary.model_dump(),
            observations=building.observations,
            total_units=total_units,
            occupied_units=occupied_units,
            free_units=free_units,
            under_repair_units=under_repair_units,
            occupancy_rate=round(occupancy_rate, 1),
            monthly_expected_rent=monthly_expected_rent,
            updated_at=building.updated_at,
        )
