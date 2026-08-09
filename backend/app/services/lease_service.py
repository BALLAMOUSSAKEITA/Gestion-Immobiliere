import shutil
from datetime import date, timedelta
from decimal import Decimal
from math import ceil
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models.building import Unit, UnitTenantHistory
from app.models.enums import LeaseStatus, UnitStatus
from app.models.tenant import Lease, LeaseRentHistory, Tenant
from app.models.user import User
from app.schemas.lease import (
    LeaseCreate,
    LeaseDetail,
    LeaseListResponse,
    LeaseRentUpdate,
    LeaseSummary,
    LeaseTerminate,
    LeaseUpdate,
    RentHistoryItem,
)
from app.services.building_service import BuildingAccessService
from app.services.tenant_access_service import TenantAccessService


class LeaseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        settings = get_settings()
        self.upload_dir = Path(settings.upload_dir)

    def list_leases(
        self,
        actor: User,
        page: int = 1,
        page_size: int = 20,
        status_filter: LeaseStatus | None = None,
        building_id: UUID | None = None,
        tenant_id: UUID | None = None,
    ) -> LeaseListResponse:
        self._ensure_read_access(actor)
        query = (
            self.db.query(Lease)
            .join(Unit)
            .join(Tenant)
            .options(
                joinedload(Lease.unit).joinedload(Unit.building),
                joinedload(Lease.tenant),
            )
        )

        allowed_buildings = BuildingAccessService.accessible_building_ids(self.db, actor)
        if allowed_buildings is not None:
            query = query.filter(
                Unit.building_id.in_(allowed_buildings)
                if allowed_buildings
                else Unit.id.is_(None)
            )

        if status_filter:
            query = query.filter(Lease.status == status_filter)
        if building_id:
            BuildingAccessService.ensure_building_access(self.db, actor, building_id)
            query = query.filter(Unit.building_id == building_id)
        if tenant_id:
            TenantAccessService.ensure_tenant_access(self.db, actor, tenant_id)
            query = query.filter(Lease.tenant_id == tenant_id)

        total = query.count()
        leases = (
            query.order_by(Lease.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        pages = ceil(total / page_size) if total else 0
        return LeaseListResponse(
            items=[self._to_summary(lease) for lease in leases],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_lease(self, actor: User, lease_id: UUID) -> LeaseDetail:
        self._ensure_read_access(actor)
        lease = self._get_or_404(lease_id)
        self._ensure_lease_access(actor, lease)
        return self._to_detail(lease)

    def create_lease(self, actor: User, payload: LeaseCreate) -> LeaseDetail:
        self._ensure_manage_access(actor)
        tenant_id = UUID(payload.tenant_id)
        unit_id = UUID(payload.unit_id)

        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.is_active).first()
        if tenant is None:
            raise HTTPException(status_code=404, detail="Locataire introuvable")

        unit = (
            self.db.query(Unit)
            .options(joinedload(Unit.building))
            .filter(Unit.id == unit_id, Unit.is_active.is_(True))
            .first()
        )
        if unit is None:
            raise HTTPException(status_code=404, detail="Logement introuvable")

        TenantAccessService.ensure_tenant_access(self.db, actor, tenant_id)
        BuildingAccessService.ensure_building_access(self.db, actor, unit.building_id)

        if unit.status != UnitStatus.free:
            raise HTTPException(
                status_code=400,
                detail="Le logement n'est pas libre",
            )

        active_on_unit = (
            self.db.query(Lease)
            .filter(Lease.unit_id == unit_id, Lease.status == LeaseStatus.active)
            .first()
        )
        if active_on_unit:
            raise HTTPException(status_code=400, detail="Ce logement a déjà un bail actif")

        active_for_tenant = (
            self.db.query(Lease)
            .filter(Lease.tenant_id == tenant_id, Lease.status == LeaseStatus.active)
            .first()
        )
        if active_for_tenant:
            raise HTTPException(
                status_code=400,
                detail="Ce locataire a déjà un bail actif",
            )

        lease = Lease(
            tenant_id=tenant_id,
            unit_id=unit_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            rent_amount=payload.rent_amount,
            deposit_amount=payload.deposit_amount,
            deposit_paid=payload.deposit_paid,
            status=LeaseStatus.active,
            created_by=actor.id,
        )
        unit.status = UnitStatus.occupied

        history = UnitTenantHistory(
            unit_id=unit_id,
            tenant_id=tenant_id,
            entry_date=payload.start_date,
            rent_amount=payload.rent_amount,
            notes="Attribution bail",
        )

        self.db.add(lease)
        self.db.add(history)
        self.db.flush()
        from app.services.rent_period_service import RentPeriodService

        RentPeriodService(self.db).generate_for_lease(lease)
        self.db.commit()
        self.db.refresh(lease)
        return self._to_detail(self._get_or_404(lease.id))

    def update_lease(
        self, actor: User, lease_id: UUID, payload: LeaseUpdate
    ) -> LeaseDetail:
        self._ensure_manage_access(actor)
        lease = self._get_or_404(lease_id)
        self._ensure_lease_access(actor, lease)

        if payload.start_date is not None:
            lease.start_date = payload.start_date
        if payload.end_date is not None:
            lease.end_date = payload.end_date
        if payload.deposit_paid is not None:
            lease.deposit_paid = payload.deposit_paid

        self.db.commit()
        return self._to_detail(self._get_or_404(lease_id))

    def terminate_lease(
        self, actor: User, lease_id: UUID, payload: LeaseTerminate
    ) -> LeaseDetail:
        self._ensure_manage_access(actor)
        lease = self._get_or_404(lease_id)
        self._ensure_lease_access(actor, lease)

        if lease.status != LeaseStatus.active:
            raise HTTPException(status_code=400, detail="Seul un bail actif peut être terminé")

        lease.status = LeaseStatus.terminated
        lease.termination_date = payload.termination_date
        lease.termination_reason = payload.termination_reason.strip()

        unit = lease.unit
        unit.status = UnitStatus.free

        history = (
            self.db.query(UnitTenantHistory)
            .filter(
                UnitTenantHistory.unit_id == lease.unit_id,
                UnitTenantHistory.tenant_id == lease.tenant_id,
                UnitTenantHistory.exit_date.is_(None),
            )
            .order_by(UnitTenantHistory.entry_date.desc())
            .first()
        )
        if history:
            history.exit_date = payload.termination_date

        self.db.commit()
        return self._to_detail(self._get_or_404(lease_id))

    def release_unit(
        self, actor: User, unit_id: UUID, termination_reason: str
    ) -> LeaseDetail:
        if actor.role.code != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé",
            )

        unit = (
            self.db.query(Unit)
            .filter(Unit.id == unit_id, Unit.is_active.is_(True))
            .first()
        )
        if unit is None:
            raise HTTPException(status_code=404, detail="Logement introuvable")

        if unit.status not in (UnitStatus.occupied, UnitStatus.reserved):
            raise HTTPException(
                status_code=400,
                detail="Seul un logement occupé ou réservé peut être libéré",
            )

        lease = (
            self.db.query(Lease)
            .filter(Lease.unit_id == unit_id, Lease.status == LeaseStatus.active)
            .first()
        )
        if lease is None:
            raise HTTPException(
                status_code=400,
                detail="Aucun bail actif n'est associé à ce logement",
            )

        return self.terminate_lease(
            actor,
            lease.id,
            LeaseTerminate(
                termination_date=date.today(),
                termination_reason=termination_reason.strip(),
            ),
        )

    def update_rent(
        self, actor: User, lease_id: UUID, payload: LeaseRentUpdate
    ) -> LeaseDetail:
        if actor.role.code not in ("super_admin", "admin_familial"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

        lease = self._get_or_404(lease_id)
        self._ensure_lease_access(actor, lease)

        if lease.status != LeaseStatus.active:
            raise HTTPException(status_code=400, detail="Le bail n'est pas actif")

        old_rent = lease.rent_amount
        lease.rent_amount = payload.rent_amount
        self.db.add(
            LeaseRentHistory(
                lease_id=lease.id,
                old_rent_amount=old_rent,
                new_rent_amount=payload.rent_amount,
                effective_date=payload.effective_date,
                changed_by=actor.id,
                reason=payload.reason,
            )
        )
        self.db.commit()
        return self._to_detail(self._get_or_404(lease_id))

    def upload_contract(
        self, actor: User, lease_id: UUID, file: UploadFile
    ) -> LeaseDetail:
        self._ensure_manage_access(actor)
        lease = self._get_or_404(lease_id)
        self._ensure_lease_access(actor, lease)

        extension = Path(file.filename or "contract.pdf").suffix.lower() or ".pdf"
        filename = f"{uuid4()}{extension}"
        target_dir = self.upload_dir / "leases"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        with target_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        lease.contract_document_url = f"/uploads/leases/{filename}"
        self.db.commit()
        return self._to_detail(self._get_or_404(lease_id))

    def list_expiring(self, actor: User, days: int = 30) -> LeaseListResponse:
        self._ensure_read_access(actor)
        if actor.role.code not in ("super_admin", "admin_familial"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

        deadline = date.today() + timedelta(days=days)
        query = (
            self.db.query(Lease)
            .join(Unit)
            .options(
                joinedload(Lease.unit).joinedload(Unit.building),
                joinedload(Lease.tenant),
            )
            .filter(
                Lease.status == LeaseStatus.active,
                Lease.end_date.isnot(None),
                Lease.end_date <= deadline,
            )
        )
        leases = query.order_by(Lease.end_date.asc()).all()
        return LeaseListResponse(
            items=[self._to_summary(lease) for lease in leases],
            total=len(leases),
            page=1,
            page_size=len(leases) or 1,
            pages=1 if leases else 0,
        )

    def _get_or_404(self, lease_id: UUID) -> Lease:
        lease = (
            self.db.query(Lease)
            .options(
                joinedload(Lease.unit).joinedload(Unit.building),
                joinedload(Lease.tenant),
            )
            .filter(Lease.id == lease_id)
            .first()
        )
        if lease is None:
            raise HTTPException(status_code=404, detail="Bail introuvable")
        return lease

    def _ensure_lease_access(self, actor: User, lease: Lease) -> None:
        BuildingAccessService.ensure_building_access(
            self.db, actor, lease.unit.building_id
        )

    def _ensure_read_access(self, actor: User) -> None:
        if not TenantAccessService.can_read(actor):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    def _ensure_manage_access(self, actor: User) -> None:
        if not TenantAccessService.can_manage(actor):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    def _to_summary(self, lease: Lease) -> LeaseSummary:
        unit = lease.unit
        tenant = lease.tenant
        return LeaseSummary(
            id=str(lease.id),
            tenant_id=str(lease.tenant_id),
            tenant_name=f"{tenant.first_name} {tenant.last_name}",
            unit_id=str(lease.unit_id),
            unit_code=unit.code,
            building_name=unit.building.name,
            start_date=lease.start_date,
            end_date=lease.end_date,
            rent_amount=lease.rent_amount,
            deposit_amount=lease.deposit_amount,
            deposit_paid=lease.deposit_paid,
            status=lease.status,
            created_at=lease.created_at,
        )

    def _to_detail(self, lease: Lease) -> LeaseDetail:
        summary = self._to_summary(lease)
        return LeaseDetail(
            **summary.model_dump(),
            contract_document_url=lease.contract_document_url,
            termination_date=lease.termination_date,
            termination_reason=lease.termination_reason,
            updated_at=lease.updated_at,
        )
