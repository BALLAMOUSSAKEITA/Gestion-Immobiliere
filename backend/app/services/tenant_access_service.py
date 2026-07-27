from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.building import Building, Unit
from app.models.user import User
from app.services.building_service import BuildingAccessService
from app.services.user_service import PermissionService


class TenantAccessService:
    @staticmethod
    def can_manage(actor: User) -> bool:
        if actor.role.code in ("super_admin", "gestionnaire"):
            return True
        if actor.role.code == "admin_familial":
            return PermissionService.check(actor, "tenants.manage")
        return False

    @staticmethod
    def can_read(actor: User) -> bool:
        return actor.role.code in (
            "super_admin",
            "admin_familial",
            "gestionnaire",
            "proprietaire",
        )

    @staticmethod
    def accessible_tenant_ids(db: Session, actor: User) -> set[UUID] | None:
        if actor.role.code in ("super_admin", "admin_familial"):
            return None

        allowed_buildings = BuildingAccessService.accessible_building_ids(db, actor)
        if allowed_buildings is None:
            return None
        if not allowed_buildings:
            return set()

        rows = (
            db.query(Lease.tenant_id)
            .join(Unit, Lease.unit_id == Unit.id)
            .filter(Unit.building_id.in_(allowed_buildings))
            .distinct()
            .all()
        )
        return {row[0] for row in rows}

    @staticmethod
    def ensure_tenant_access(db: Session, actor: User, tenant_id: UUID) -> None:
        allowed = TenantAccessService.accessible_tenant_ids(db, actor)
        if allowed is not None and tenant_id not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé",
            )

    @staticmethod
    def ensure_unit_access(db: Session, actor: User, unit_id: UUID) -> None:
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if unit is None:
            raise HTTPException(status_code=404, detail="Logement introuvable")
        BuildingAccessService.ensure_building_access(db, actor, unit.building_id)

    @staticmethod
    def mask_id_document(number: str) -> str:
        if len(number) <= 4:
            return "•" * len(number)
        prefix = number[:2] if len(number) > 6 else ""
        suffix = number[-4:]
        masked_middle = "•" * max(len(number) - len(prefix) - 4, 3)
        return f"{prefix}{masked_middle}{suffix}"
