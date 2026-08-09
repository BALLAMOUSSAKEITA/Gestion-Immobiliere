import logging
import secrets
import shutil
import string
from math import ceil
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.security import hash_password
from decimal import Decimal

from app.models.building import Unit
from app.models.enums import LeaseStatus, OverdueStatus
from app.models.overdue import OverdueRecord
from app.models.payment import Payment
from app.models.role import Role
from app.models.tenant import Lease, Tenant
from app.models.user import User
from app.schemas.tenant import (
    CreateTenantAccountRequest,
    CreateTenantAccountResponse,
    CurrentLeaseSummary,
    PaymentSummary,
    TenantCreate,
    TenantDetail,
    TenantListResponse,
    TenantSummary,
    TenantUpdate,
)
from app.services.tenant_access_service import TenantAccessService

logger = logging.getLogger(__name__)


class TenantService:
    def __init__(self, db: Session) -> None:
        self.db = db
        settings = get_settings()
        self.upload_dir = Path(settings.upload_dir)

    def list_tenants(
        self,
        actor: User,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        building_id: UUID | None = None,
        unit_id: UUID | None = None,
        is_active: bool | None = True,
    ) -> TenantListResponse:
        self._ensure_read_access(actor)
        query = self.db.query(Tenant)

        allowed_tenants = TenantAccessService.accessible_tenant_ids(self.db, actor)
        if allowed_tenants is not None:
            query = query.filter(
                Tenant.id.in_(allowed_tenants) if allowed_tenants else Tenant.id.is_(None)
            )

        if is_active is not None:
            query = query.filter(Tenant.is_active == is_active)
        if building_id:
            from app.services.building_service import BuildingAccessService

            BuildingAccessService.ensure_building_access(self.db, actor, building_id)
            tenant_ids = self._tenant_ids_for_building(building_id)
            query = query.filter(Tenant.id.in_(tenant_ids) if tenant_ids else Tenant.id.is_(None))
        if unit_id:
            tenant_ids = self._tenant_ids_for_unit(unit_id)
            query = query.filter(Tenant.id.in_(tenant_ids) if tenant_ids else Tenant.id.is_(None))
        if search:
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Tenant.first_name).like(term),
                    func.lower(Tenant.last_name).like(term),
                    func.lower(Tenant.phone_primary).like(term),
                    func.lower(Tenant.id_document_number).like(term),
                )
            )

        total = query.count()
        tenants = (
            query.order_by(Tenant.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        pages = ceil(total / page_size) if total else 0
        return TenantListResponse(
            items=[self._to_summary(tenant) for tenant in tenants],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_tenant(self, actor: User, tenant_id: UUID) -> TenantDetail:
        self._ensure_read_access(actor)
        tenant = self._get_or_404(tenant_id)
        TenantAccessService.ensure_tenant_access(self.db, actor, tenant_id)
        return self._to_detail(tenant, actor)

    def create_tenant(self, actor: User, payload: TenantCreate) -> TenantDetail:
        self._ensure_manage_access(actor)
        tenant = Tenant(
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            phone_primary=payload.phone_primary.strip(),
            phone_secondary=payload.phone_secondary,
            profession=payload.profession,
            previous_address=payload.previous_address,
            id_document_type=payload.id_document_type,
            id_document_number=payload.id_document_number.strip(),
            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_phone=payload.emergency_contact_phone,
            payment_method=payload.payment_method,
            observations=payload.observations,
            created_by=actor.id,
        )
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return self._to_detail(tenant, actor)

    def update_tenant(
        self, actor: User, tenant_id: UUID, payload: TenantUpdate
    ) -> TenantDetail:
        self._ensure_manage_access(actor)
        tenant = self._get_or_404(tenant_id)
        TenantAccessService.ensure_tenant_access(self.db, actor, tenant_id)

        if payload.first_name is not None:
            tenant.first_name = payload.first_name.strip()
        if payload.last_name is not None:
            tenant.last_name = payload.last_name.strip()
        if payload.phone_primary is not None:
            tenant.phone_primary = payload.phone_primary.strip()
        if payload.phone_secondary is not None:
            tenant.phone_secondary = payload.phone_secondary
        if payload.profession is not None:
            tenant.profession = payload.profession
        if payload.previous_address is not None:
            tenant.previous_address = payload.previous_address
        if payload.id_document_type is not None:
            tenant.id_document_type = payload.id_document_type
        if payload.id_document_number is not None:
            tenant.id_document_number = payload.id_document_number.strip()
        if payload.emergency_contact_name is not None:
            tenant.emergency_contact_name = payload.emergency_contact_name
        if payload.emergency_contact_phone is not None:
            tenant.emergency_contact_phone = payload.emergency_contact_phone
        if payload.payment_method is not None:
            tenant.payment_method = payload.payment_method
        if payload.observations is not None:
            tenant.observations = payload.observations
        if payload.is_active is not None:
            tenant.is_active = payload.is_active

        self.db.commit()
        self.db.refresh(tenant)
        return self._to_detail(tenant, actor)

    def deactivate_tenant(self, actor: User, tenant_id: UUID) -> None:
        if actor.role.code != "super_admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")
        tenant = self._get_or_404(tenant_id)
        active_lease = (
            self.db.query(Lease)
            .filter(Lease.tenant_id == tenant_id, Lease.status == LeaseStatus.active)
            .first()
        )
        if active_lease:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Désolé, si le locataire a déjà un bail actif, "
                    "il faut d'abord résilier le bail."
                ),
            )
        tenant.is_active = False
        self.db.commit()

    def upload_photo(
        self, actor: User, tenant_id: UUID, file: UploadFile
    ) -> TenantDetail:
        self._ensure_manage_access(actor)
        tenant = self._get_or_404(tenant_id)
        TenantAccessService.ensure_tenant_access(self.db, actor, tenant_id)
        tenant.photo_url = self._save_file(file, "tenants/photos")
        self.db.commit()
        self.db.refresh(tenant)
        return self._to_detail(tenant, actor)

    def upload_id_document(
        self, actor: User, tenant_id: UUID, file: UploadFile
    ) -> TenantDetail:
        self._ensure_manage_access(actor)
        tenant = self._get_or_404(tenant_id)
        TenantAccessService.ensure_tenant_access(self.db, actor, tenant_id)
        tenant.id_document_url = self._save_file(file, "tenants/documents")
        self.db.commit()
        self.db.refresh(tenant)
        return self._to_detail(tenant, actor)

    def create_account(
        self, actor: User, tenant_id: UUID, payload: CreateTenantAccountRequest
    ) -> CreateTenantAccountResponse:
        if actor.role.code not in ("super_admin", "admin_familial"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")
        tenant = self._get_or_404(tenant_id)
        if tenant.user_id:
            raise HTTPException(status_code=400, detail="Compte déjà lié à ce locataire")

        role = self.db.query(Role).filter(Role.code == "locataire").first()
        if role is None:
            raise HTTPException(status_code=500, detail="Rôle locataire introuvable")

        email = payload.email.strip().lower()
        if self.db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

        password = payload.password or self._generate_password()
        user = User(
            email=email,
            password_hash=hash_password(password),
            first_name=tenant.first_name,
            last_name=tenant.last_name,
            phone=tenant.phone_primary,
            role_id=role.id,
            is_active=True,
        )
        self.db.add(user)
        self.db.flush()
        tenant.user_id = user.id
        self.db.commit()
        logger.info("Compte locataire créé pour %s", email)
        return CreateTenantAccountResponse(
            user_id=str(user.id),
            email=user.email,
            temporary_password=password if not payload.password else None,
        )

    def _get_or_404(self, tenant_id: UUID) -> Tenant:
        tenant = (
            self.db.query(Tenant)
            .options(joinedload(Tenant.leases))
            .filter(Tenant.id == tenant_id)
            .first()
        )
        if tenant is None:
            raise HTTPException(status_code=404, detail="Locataire introuvable")
        return tenant

    def _tenant_ids_for_building(self, building_id: UUID) -> list[UUID]:
        from app.models.building import Unit

        rows = (
            self.db.query(Lease.tenant_id)
            .join(Unit, Lease.unit_id == Unit.id)
            .filter(Unit.building_id == building_id)
            .distinct()
            .all()
        )
        return [row[0] for row in rows]

    def _tenant_ids_for_unit(self, unit_id: UUID) -> list[UUID]:
        rows = (
            self.db.query(Lease.tenant_id)
            .filter(Lease.unit_id == unit_id)
            .distinct()
            .all()
        )
        return [row[0] for row in rows]

    def _get_active_lease(self, tenant_id: UUID) -> Lease | None:
        return (
            self.db.query(Lease)
            .options(joinedload(Lease.unit).joinedload(Unit.building))
            .filter(Lease.tenant_id == tenant_id, Lease.status == LeaseStatus.active)
            .first()
        )

    def _ensure_read_access(self, actor: User) -> None:
        if not TenantAccessService.can_read(actor):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    def _ensure_manage_access(self, actor: User) -> None:
        if not TenantAccessService.can_manage(actor):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    def _to_summary(self, tenant: Tenant) -> TenantSummary:
        active_lease = self._get_active_lease(tenant.id)
        return TenantSummary(
            id=str(tenant.id),
            first_name=tenant.first_name,
            last_name=tenant.last_name,
            phone_primary=tenant.phone_primary,
            profession=tenant.profession,
            is_active=tenant.is_active,
            has_active_lease=active_lease is not None,
            current_unit_code=active_lease.unit.code if active_lease else None,
            created_at=tenant.created_at,
        )

    def _to_detail(self, tenant: Tenant, actor: User) -> TenantDetail:
        active_lease = self._get_active_lease(tenant.id)
        current_lease = None
        if active_lease and active_lease.unit:
            current_lease = CurrentLeaseSummary(
                id=str(active_lease.id),
                unit_code=active_lease.unit.code,
                building_name=active_lease.unit.building.name,
                rent_amount=active_lease.rent_amount,
                start_date=active_lease.start_date,
                status=active_lease.status.value,
            )

        id_number = tenant.id_document_number
        if actor.role.code == "proprietaire":
            id_number = TenantAccessService.mask_id_document(id_number)

        summary = self._to_summary(tenant)
        return TenantDetail(
            **summary.model_dump(),
            phone_secondary=tenant.phone_secondary,
            previous_address=tenant.previous_address,
            id_document_type=tenant.id_document_type,
            id_document_number=id_number,
            id_document_url=tenant.id_document_url if actor.role.code != "proprietaire" else None,
            photo_url=tenant.photo_url,
            emergency_contact_name=tenant.emergency_contact_name,
            emergency_contact_phone=tenant.emergency_contact_phone,
            payment_method=tenant.payment_method,
            observations=tenant.observations,
            user_id=str(tenant.user_id) if tenant.user_id else None,
            current_lease=current_lease,
            payment_summary=self._payment_summary(tenant.id),
            updated_at=tenant.updated_at,
        )

    def _payment_summary(self, tenant_id: UUID) -> PaymentSummary:
        total_paid = (
            self.db.query(func.sum(Payment.amount)).filter(Payment.tenant_id == tenant_id).scalar()
        ) or Decimal("0")
        total_unpaid = (
            self.db.query(func.sum(OverdueRecord.amount_remaining))
            .filter(
                OverdueRecord.tenant_id == tenant_id,
                OverdueRecord.status != OverdueStatus.resolved,
            )
            .scalar()
        ) or Decimal("0")
        return PaymentSummary(total_paid=total_paid, total_unpaid=total_unpaid)

    def _save_file(self, file: UploadFile, subdir: str) -> str:
        extension = Path(file.filename or "file.bin").suffix.lower() or ".bin"
        filename = f"{uuid4()}{extension}"
        target_dir = self.upload_dir / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        with target_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return f"/uploads/{subdir}/{filename}"

    def _generate_password(self, length: int = 12) -> str:
        alphabet = string.ascii_letters + string.digits
        while True:
            password = "".join(secrets.choice(alphabet) for _ in range(length))
            if any(c.isupper() for c in password) and any(c.isdigit() for c in password):
                return password + "!"
