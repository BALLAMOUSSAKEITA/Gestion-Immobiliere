import shutil
from math import ceil
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models.building import Building, Unit, UnitPhoto, UnitTenantHistory
from app.models.enums import UnitStatus, UnitType
from app.models.user import User
from app.schemas.unit import (
    PublicUnitDetail,
    PublicUnitListResponse,
    PublicUnitSummary,
    UnitCreate,
    UnitDetail,
    UnitHistoryItem,
    UnitListResponse,
    UnitPhotoResponse,
    UnitRelease,
    UnitSummary,
    UnitUpdate,
)
from app.schemas.lease import LeaseDetail
from app.services.building_service import BuildingAccessService, BuildingService
from app.services.code_generator_service import CodeGeneratorService
from app.services.lease_service import LeaseService
from app.services.user_service import PermissionService


class UnitService:
    def __init__(self, db: Session) -> None:
        self.db = db
        settings = get_settings()
        self.code_generator = CodeGeneratorService(db, prefix=settings.building_code_prefix)
        self.upload_dir = Path(settings.upload_dir)

    def list_units(
        self,
        actor: User,
        page: int = 1,
        page_size: int = 20,
        building_id: UUID | None = None,
        unit_type: UnitType | None = None,
        status_filter: UnitStatus | None = None,
        owner_profile_id: UUID | None = None,
        search: str | None = None,
    ) -> UnitListResponse:
        self._ensure_read_access(actor)
        query = (
            self.db.query(Unit)
            .join(Building)
            .options(joinedload(Unit.building))
            .filter(Unit.is_active.is_(True), Building.is_active.is_(True))
        )

        allowed = BuildingAccessService.accessible_building_ids(self.db, actor)
        if allowed is not None:
            query = query.filter(Unit.building_id.in_(allowed) if allowed else Unit.id.is_(None))

        if building_id:
            BuildingAccessService.ensure_building_access(self.db, actor, building_id)
            query = query.filter(Unit.building_id == building_id)
        if unit_type:
            query = query.filter(Unit.type == unit_type)
        if status_filter:
            query = query.filter(Unit.status == status_filter)
        if owner_profile_id:
            query = query.filter(Building.owner_profile_id == owner_profile_id)
        if search:
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Unit.code).like(term),
                    func.lower(Unit.number).like(term),
                )
            )

        total = query.count()
        items = (
            query.order_by(Unit.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        pages = ceil(total / page_size) if total else 0
        return UnitListResponse(
            items=[self._to_summary(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_unit(self, actor: User, unit_id: UUID) -> UnitDetail:
        self._ensure_read_access(actor)
        unit = self._get_or_404(unit_id)
        BuildingAccessService.ensure_building_access(self.db, actor, unit.building_id)
        return self._to_detail(unit)

    def create_unit(
        self, actor: User, building_id: UUID, payload: UnitCreate
    ) -> UnitDetail:
        self._ensure_manage_access(actor)
        building = self._get_building_or_404(building_id)
        BuildingAccessService.ensure_building_access(self.db, actor, building_id)

        code = self.code_generator.generate_unit_code(
            building.code, payload.type, payload.number, payload.floor
        )
        unit = Unit(
            building_id=building_id,
            code=code,
            type=payload.type,
            number=payload.number.strip(),
            floor=payload.floor,
            rent_amount=payload.rent_amount,
            deposit_amount=payload.deposit_amount,
            status=payload.status,
            description=payload.description,
            is_public_listing=payload.is_public_listing,
        )
        self.db.add(unit)
        self.db.commit()
        self.db.refresh(unit)
        BuildingService(self.db).recalculate_unit_counts(building_id)
        return self._to_detail(unit)

    def update_unit(self, actor: User, unit_id: UUID, payload: UnitUpdate) -> UnitDetail:
        self._ensure_manage_access(actor)
        unit = self._get_or_404(unit_id)
        BuildingAccessService.ensure_building_access(self.db, actor, unit.building_id)

        if payload.status == UnitStatus.free and unit.status == UnitStatus.occupied:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible de libérer un logement occupé sans clôturer le bail",
            )

        if payload.rent_amount is not None:
            unit.rent_amount = payload.rent_amount
        if payload.deposit_amount is not None:
            unit.deposit_amount = payload.deposit_amount
        if payload.status is not None:
            unit.status = payload.status
        if payload.description is not None:
            unit.description = payload.description
        if payload.is_public_listing is not None:
            unit.is_public_listing = payload.is_public_listing
        if payload.is_active is not None:
            unit.is_active = payload.is_active

        self.db.commit()
        self.db.refresh(unit)
        return self._to_detail(unit)

    def deactivate_unit(self, actor: User, unit_id: UUID) -> None:
        if actor.role.code != "super_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")
        unit = self._get_or_404(unit_id)
        if unit.status == UnitStatus.occupied:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible de supprimer un logement occupé",
            )
        unit.is_active = False
        self.db.commit()
        BuildingService(self.db).recalculate_unit_counts(unit.building_id)

    def release_unit(self, actor: User, unit_id: UUID, payload: UnitRelease) -> LeaseDetail:
        unit = self._get_or_404(unit_id)
        BuildingAccessService.ensure_building_access(self.db, actor, unit.building_id)
        return LeaseService(self.db).release_unit(actor, unit_id, payload.termination_reason)

    def get_history(self, actor: User, unit_id: UUID) -> list[UnitHistoryItem]:
        self._ensure_read_access(actor)
        unit = self._get_or_404(unit_id)
        BuildingAccessService.ensure_building_access(self.db, actor, unit.building_id)
        history = (
            self.db.query(UnitTenantHistory)
            .options(joinedload(UnitTenantHistory.tenant))
            .filter(UnitTenantHistory.unit_id == unit_id)
            .order_by(UnitTenantHistory.entry_date.desc())
            .all()
        )
        return [
            UnitHistoryItem(
                id=str(item.id),
                tenant_id=str(item.tenant_id) if item.tenant_id else None,
                tenant_name=(
                    f"{item.tenant.first_name} {item.tenant.last_name}"
                    if item.tenant
                    else None
                ),
                entry_date=item.entry_date,
                exit_date=item.exit_date,
                rent_amount=item.rent_amount,
                notes=item.notes,
            )
            for item in history
        ]

    def upload_photo(self, actor: User, unit_id: UUID, file: UploadFile) -> UnitPhotoResponse:
        self._ensure_manage_access(actor)
        unit = self._get_or_404(unit_id)
        BuildingAccessService.ensure_building_access(self.db, actor, unit.building_id)

        extension = Path(file.filename or "photo.jpg").suffix.lower() or ".jpg"
        filename = f"{uuid4()}{extension}"
        target_dir = self.upload_dir / "units"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename

        with target_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        url = f"/uploads/units/{filename}"
        photo = UnitPhoto(
            unit_id=unit_id,
            url=url,
            is_primary=len(unit.photos) == 0,
            sort_order=len(unit.photos),
        )
        self.db.add(photo)
        self.db.commit()
        self.db.refresh(photo)
        return self._photo_to_response(photo)

    def delete_photo(self, actor: User, unit_id: UUID, photo_id: UUID) -> None:
        self._ensure_manage_access(actor)
        unit = self._get_or_404(unit_id)
        BuildingAccessService.ensure_building_access(self.db, actor, unit.building_id)
        photo = (
            self.db.query(UnitPhoto)
            .filter(UnitPhoto.id == photo_id, UnitPhoto.unit_id == unit_id)
            .first()
        )
        if photo is None:
            raise HTTPException(status_code=404, detail="Photo introuvable")
        self.db.delete(photo)
        self.db.commit()

    def list_public_units(self, page: int = 1, page_size: int = 20) -> PublicUnitListResponse:
        query = (
            self.db.query(Unit)
            .join(Building)
            .options(joinedload(Unit.photos), joinedload(Unit.building))
            .filter(
                Unit.is_active.is_(True),
                Unit.status == UnitStatus.free,
                Unit.is_public_listing.is_(True),
                Building.is_active.is_(True),
            )
        )
        total = query.count()
        items = (
            query.order_by(Unit.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        pages = ceil(total / page_size) if total else 0
        return PublicUnitListResponse(
            items=[self._to_public_summary(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_public_unit(self, unit_id: UUID) -> PublicUnitDetail:
        unit = (
            self.db.query(Unit)
            .join(Building)
            .options(joinedload(Unit.photos), joinedload(Unit.building))
            .filter(
                Unit.id == unit_id,
                Unit.is_active.is_(True),
                Unit.status == UnitStatus.free,
                Unit.is_public_listing.is_(True),
                Building.is_active.is_(True),
            )
            .first()
        )
        if unit is None:
            raise HTTPException(status_code=404, detail="Annonce introuvable")
        summary = self._to_public_summary(unit)
        return PublicUnitDetail(
            **summary.model_dump(),
            photos=[self._photo_to_response(photo) for photo in unit.photos],
        )

    def _get_or_404(self, unit_id: UUID) -> Unit:
        unit = (
            self.db.query(Unit)
            .options(joinedload(Unit.building), joinedload(Unit.photos))
            .filter(Unit.id == unit_id, Unit.is_active.is_(True))
            .first()
        )
        if unit is None:
            raise HTTPException(status_code=404, detail="Logement introuvable")
        return unit

    def _get_building_or_404(self, building_id: UUID) -> Building:
        building = (
            self.db.query(Building)
            .filter(Building.id == building_id, Building.is_active.is_(True))
            .first()
        )
        if building is None:
            raise HTTPException(status_code=404, detail="Immeuble introuvable")
        return building

    def _ensure_read_access(self, actor: User) -> None:
        if actor.role.code not in ("super_admin", "admin_familial", "proprietaire", "gestionnaire"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    def _ensure_manage_access(self, actor: User) -> None:
        role = actor.role.code
        if role == "super_admin":
            return
        if role == "admin_familial" and PermissionService.check(actor, "units.manage"):
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    def _to_summary(self, unit: Unit) -> UnitSummary:
        building = unit.building
        return UnitSummary(
            id=str(unit.id),
            building_id=str(unit.building_id),
            code=unit.code,
            type=unit.type,
            number=unit.number,
            floor=unit.floor,
            rent_amount=unit.rent_amount,
            deposit_amount=unit.deposit_amount,
            status=unit.status,
            is_public_listing=unit.is_public_listing,
            is_active=unit.is_active,
            building_code=building.code if building else None,
            building_name=building.name if building else None,
            commune=building.commune if building else None,
            quartier=building.quartier if building else None,
        )

    def _to_public_summary(self, unit: Unit) -> PublicUnitSummary:
        building = unit.building
        primary = next((photo for photo in unit.photos if photo.is_primary), None)
        if primary is None and unit.photos:
            primary = unit.photos[0]
        return PublicUnitSummary(
            id=str(unit.id),
            code=unit.code,
            type=unit.type,
            rent_amount=unit.rent_amount,
            deposit_amount=unit.deposit_amount,
            description=unit.description,
            commune=building.commune,
            quartier=building.quartier,
            primary_photo_url=primary.url if primary else None,
        )

    def _to_detail(self, unit: Unit) -> UnitDetail:
        summary = self._to_summary(unit)
        return UnitDetail(
            **summary.model_dump(),
            description=unit.description,
            photos=[self._photo_to_response(photo) for photo in unit.photos],
            created_at=unit.created_at,
            updated_at=unit.updated_at,
        )

    def _photo_to_response(self, photo: UnitPhoto) -> UnitPhotoResponse:
        return UnitPhotoResponse(
            id=str(photo.id),
            url=photo.url,
            is_primary=photo.is_primary,
            sort_order=photo.sort_order,
            uploaded_at=photo.uploaded_at,
        )
