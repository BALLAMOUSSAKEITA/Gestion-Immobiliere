import logging
import shutil
from datetime import UTC, date, datetime
from decimal import Decimal
from math import ceil
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.expense_categories_seed import EXPENSE_CATEGORY_SEED
from app.core.permissions import Permission, role_has_permission
from app.models.building import Building, Unit
from app.models.enums import (
    ExpenseStatus,
    LeaseStatus,
    RepairAttachmentType,
    RepairStatus,
    UnitStatus,
    UrgencyLevel,
)
from app.models.expense import Expense
from app.models.repair import Repair, RepairAttachment, RepairStatusHistory
from app.models.tenant import Lease
from app.models.user import User
from app.schemas.repair import (
    RepairAttachmentResponse,
    RepairCancel,
    RepairComplete,
    RepairCreate,
    RepairDetail,
    RepairHistoryItem,
    RepairListResponse,
    RepairStatusUpdate,
    RepairSummaryItem,
    RepairSummaryStats,
    RepairUpdate,
)
from app.services.building_service import BuildingAccessService

logger = logging.getLogger(__name__)

ALLOWED_TRANSITIONS: dict[RepairStatus, set[RepairStatus]] = {
    RepairStatus.new: {RepairStatus.under_review, RepairStatus.cancelled},
    RepairStatus.under_review: {RepairStatus.technician_assigned, RepairStatus.cancelled},
    RepairStatus.technician_assigned: {
        RepairStatus.in_progress,
        RepairStatus.completed,
        RepairStatus.cancelled,
    },
    RepairStatus.in_progress: {RepairStatus.completed, RepairStatus.cancelled},
    RepairStatus.completed: set(),
    RepairStatus.cancelled: set(),
}

REPAIR_CATEGORY_ID = EXPENSE_CATEGORY_SEED[0]["id"]


class RepairService:
    def __init__(self, db: Session) -> None:
        self.db = db
        settings = get_settings()
        self.upload_dir = Path(settings.upload_dir)
        self.validation_threshold = Decimal(str(settings.expense_validation_threshold))
        self.set_unit_under_repair = settings.repair_set_unit_under_repair

    def list_repairs(
        self,
        actor: User,
        page: int = 1,
        page_size: int = 20,
        building_id: UUID | None = None,
        unit_id: UUID | None = None,
        status_filter: RepairStatus | None = None,
        urgency: UrgencyLevel | None = None,
        assigned_to: UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> RepairListResponse:
        self._ensure_read_access(actor)
        query = self._base_query(actor)

        if building_id:
            BuildingAccessService.ensure_building_access(self.db, actor, building_id)
            query = query.filter(Repair.building_id == building_id)
        if unit_id:
            unit = self._get_unit_or_404(unit_id)
            BuildingAccessService.ensure_building_access(self.db, actor, unit.building_id)
            query = query.filter(Repair.unit_id == unit_id)
        if status_filter:
            query = query.filter(Repair.status == status_filter)
        if urgency:
            query = query.filter(Repair.urgency == urgency)
        if assigned_to:
            query = query.filter(Repair.assigned_to == assigned_to)
        if date_from:
            query = query.filter(func.date(Repair.reported_at) >= date_from)
        if date_to:
            query = query.filter(func.date(Repair.reported_at) <= date_to)

        query = query.order_by(Repair.reported_at.desc())
        total = query.count()
        records = query.offset((page - 1) * page_size).limit(page_size).all()
        pages = ceil(total / page_size) if total else 0
        return RepairListResponse(
            items=[self._to_summary(item) for item in records],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_summary(self, actor: User) -> RepairSummaryStats:
        self._ensure_read_access(actor)
        query = self._base_query(actor)
        active_statuses = (
            RepairStatus.new,
            RepairStatus.under_review,
            RepairStatus.technician_assigned,
            RepairStatus.in_progress,
        )
        in_progress = query.filter(Repair.status.in_(active_statuses)).count()
        urgent = query.filter(
            Repair.status.in_(active_statuses),
            Repair.urgency == UrgencyLevel.high,
        ).count()
        today = date.today()
        completed = query.filter(
            Repair.status == RepairStatus.completed,
            func.extract("year", Repair.completed_at) == today.year,
            func.extract("month", Repair.completed_at) == today.month,
        ).count()
        return RepairSummaryStats(
            in_progress_count=in_progress,
            urgent_count=urgent,
            completed_this_month=completed,
        )

    def get_repair(self, actor: User, repair_id: UUID) -> RepairDetail:
        self._ensure_read_access(actor)
        repair = self._get_or_404(repair_id)
        self._ensure_repair_access(actor, repair)
        return self._to_detail(repair)

    def create_repair(self, actor: User, payload: RepairCreate) -> RepairDetail:
        unit_id = self._resolve_unit_id(actor, payload.unit_id)
        unit = self._get_unit_or_404(unit_id)
        self._ensure_can_create(actor, unit)

        building = self.db.query(Building).filter(Building.id == unit.building_id).first()
        assigned_to = building.manager_user_id if building else None

        repair = Repair(
            unit_id=unit.id,
            building_id=unit.building_id,
            reported_by=actor.id,
            assigned_to=assigned_to,
            title=payload.title.strip(),
            description=payload.description.strip(),
            urgency=payload.urgency,
            status=RepairStatus.new,
        )
        self.db.add(repair)
        self.db.flush()
        self._record_status_change(repair, None, RepairStatus.new, actor.id, "Demande créée")
        self.db.commit()

        if payload.urgency == UrgencyLevel.high:
            logger.info("Notification placeholder: réparation urgente %s", repair.id)

        return self._to_detail(self._get_or_404(repair.id))

    def update_repair(
        self, actor: User, repair_id: UUID, payload: RepairUpdate
    ) -> RepairDetail:
        self._ensure_manage_access(actor)
        repair = self._get_or_404(repair_id)
        self._ensure_repair_access(actor, repair)
        if repair.status in (RepairStatus.completed, RepairStatus.cancelled):
            raise HTTPException(status_code=400, detail="Réparation non modifiable")

        if payload.title is not None:
            repair.title = payload.title.strip()
        if payload.description is not None:
            repair.description = payload.description.strip()
        if payload.urgency is not None:
            repair.urgency = payload.urgency
        if payload.estimated_cost is not None:
            repair.estimated_cost = payload.estimated_cost
        if payload.notes is not None:
            repair.notes = payload.notes
        if payload.assigned_to is not None:
            repair.assigned_to = UUID(payload.assigned_to)

        self.db.commit()
        return self._to_detail(self._get_or_404(repair_id))

    def update_status(
        self, actor: User, repair_id: UUID, payload: RepairStatusUpdate
    ) -> RepairDetail:
        self._ensure_manage_access(actor)
        repair = self._get_or_404(repair_id)
        self._ensure_repair_access(actor, repair)
        self._transition(repair, payload.status, actor.id, payload.comment)
        if payload.assigned_to:
            repair.assigned_to = UUID(payload.assigned_to)
        self._apply_status_side_effects(repair, payload.status)
        self.db.commit()
        return self._to_detail(self._get_or_404(repair_id))

    def cancel_repair(
        self, actor: User, repair_id: UUID, payload: RepairCancel
    ) -> RepairDetail:
        self._ensure_manage_access(actor)
        repair = self._get_or_404(repair_id)
        self._ensure_repair_access(actor, repair)
        if repair.status == RepairStatus.completed:
            raise HTTPException(status_code=400, detail="Réparation déjà terminée")
        if repair.status == RepairStatus.cancelled:
            raise HTTPException(status_code=400, detail="Réparation déjà annulée")
        self._transition(
            repair, RepairStatus.cancelled, actor.id, payload.cancellation_reason
        )
        repair.cancelled_at = datetime.now(UTC)
        repair.cancellation_reason = payload.cancellation_reason.strip()
        self.db.commit()
        return self._to_detail(self._get_or_404(repair_id))

    def complete_repair(
        self, actor: User, repair_id: UUID, payload: RepairComplete
    ) -> RepairDetail:
        self._ensure_manage_access(actor)
        repair = self._get_or_404(repair_id)
        self._ensure_repair_access(actor, repair)
        if repair.status == RepairStatus.completed:
            raise HTTPException(status_code=400, detail="Réparation déjà terminée")
        if repair.status == RepairStatus.cancelled:
            raise HTTPException(status_code=400, detail="Réparation annulée")

        self._transition(repair, RepairStatus.completed, actor.id, payload.notes)
        repair.final_cost = payload.final_cost
        repair.completed_at = datetime.now(UTC)
        if payload.notes:
            repair.notes = payload.notes

        if payload.create_expense:
            category_id = (
                UUID(payload.expense_category_id)
                if payload.expense_category_id
                else REPAIR_CATEGORY_ID
            )
            requires_validation = payload.final_cost >= self.validation_threshold
            expense = Expense(
                category_id=category_id,
                building_id=repair.building_id,
                unit_id=repair.unit_id,
                description=f"Réparation: {repair.title}",
                amount=payload.final_cost,
                payment_method=payload.payment_method,
                expense_date=date.today(),
                status=(
                    ExpenseStatus.pending_validation
                    if requires_validation
                    else ExpenseStatus.recorded
                ),
                requires_validation=requires_validation,
                repair_id=repair.id,
                recorded_by=actor.id,
            )
            self.db.add(expense)
            self.db.flush()
            repair.expense_id = expense.id

        unit = self.db.query(Unit).filter(Unit.id == repair.unit_id).first()
        if unit and unit.status == UnitStatus.under_repair:
            unit.status = UnitStatus.occupied

        self.db.commit()
        return self._to_detail(self._get_or_404(repair_id))

    def upload_attachment(
        self, actor: User, repair_id: UUID, file: UploadFile
    ) -> RepairDetail:
        repair = self._get_or_404(repair_id)
        self._ensure_repair_access(actor, repair)
        if actor.role.code == "locataire":
            if repair.reported_by != actor.id:
                raise HTTPException(status_code=403, detail="Accès non autorisé")
        else:
            self._ensure_manage_access(actor)

        extension = Path(file.filename or "file.bin").suffix.lower() or ".bin"
        if extension in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            file_type = RepairAttachmentType.photo
        elif extension in {".mp4", ".mov", ".webm", ".avi"}:
            file_type = RepairAttachmentType.video
        elif extension == ".pdf":
            file_type = RepairAttachmentType.document
        else:
            raise HTTPException(status_code=400, detail="Format de fichier non supporté")

        filename = f"{uuid4()}{extension}"
        target_dir = self.upload_dir / "repairs"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        with target_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        attachment = RepairAttachment(
            repair_id=repair.id,
            file_url=f"/uploads/repairs/{filename}",
            file_type=file_type,
            uploaded_by=actor.id,
        )
        self.db.add(attachment)
        self.db.commit()
        return self._to_detail(self._get_or_404(repair_id))

    def get_history(self, actor: User, repair_id: UUID) -> list[RepairHistoryItem]:
        self._ensure_manage_access(actor)
        repair = self._get_or_404(repair_id)
        self._ensure_repair_access(actor, repair)
        return [
            RepairHistoryItem(
                id=str(item.id),
                old_status=item.old_status,
                new_status=item.new_status,
                changed_by_name=f"{item.changer.first_name} {item.changer.last_name}",
                changed_at=item.changed_at,
                comment=item.comment,
            )
            for item in sorted(repair.status_history, key=lambda h: h.changed_at)
        ]

    def _base_query(self, actor: User):
        query = (
            self.db.query(Repair)
            .options(
                joinedload(Repair.unit),
                joinedload(Repair.building),
                joinedload(Repair.reporter),
                joinedload(Repair.assignee),
            )
        )
        role = actor.role.code
        if role in ("super_admin", "admin_familial"):
            return query

        if role == "gestionnaire":
            allowed = BuildingAccessService.accessible_building_ids(self.db, actor)
            if not allowed:
                return query.filter(Repair.id.is_(None))
            return query.filter(Repair.building_id.in_(allowed))

        if role == "proprietaire":
            allowed = BuildingAccessService.accessible_building_ids(self.db, actor) or set()
            if not allowed:
                return query.filter(Repair.id.is_(None))
            return query.filter(Repair.building_id.in_(allowed))

        if role == "locataire":
            if actor.tenant_profile is None:
                return query.filter(Repair.id.is_(None))
            return query.filter(Repair.reported_by == actor.id)

        raise HTTPException(status_code=403, detail="Accès non autorisé")

    def _resolve_unit_id(self, actor: User, unit_id: str | None) -> UUID:
        if actor.role.code == "locataire":
            if actor.tenant_profile is None:
                raise HTTPException(status_code=400, detail="Profil locataire introuvable")
            lease = (
                self.db.query(Lease)
                .filter(
                    Lease.tenant_id == actor.tenant_profile.id,
                    Lease.status == LeaseStatus.active,
                )
                .first()
            )
            if lease is None:
                raise HTTPException(status_code=400, detail="Aucun bail actif")
            return lease.unit_id
        if unit_id is None:
            raise HTTPException(status_code=400, detail="Logement requis")
        return UUID(unit_id)

    def _ensure_can_create(self, actor: User, unit: Unit) -> None:
        if actor.role.code == "locataire":
            lease = (
                self.db.query(Lease)
                .filter(
                    Lease.unit_id == unit.id,
                    Lease.tenant_id == actor.tenant_profile.id,
                    Lease.status == LeaseStatus.active,
                )
                .first()
            )
            if lease is None:
                raise HTTPException(status_code=403, detail="Accès non autorisé")
            return
        self._ensure_manage_access(actor)
        BuildingAccessService.ensure_building_access(self.db, actor, unit.building_id)

    def _ensure_repair_access(self, actor: User, repair: Repair) -> None:
        if actor.role.code == "locataire":
            if repair.reported_by != actor.id:
                raise HTTPException(status_code=403, detail="Accès non autorisé")
            return
        if actor.role.code == "proprietaire":
            BuildingAccessService.ensure_building_access(self.db, actor, repair.building_id)
            return
        if actor.role.code == "gestionnaire":
            BuildingAccessService.ensure_building_access(self.db, actor, repair.building_id)

    def _transition(
        self,
        repair: Repair,
        new_status: RepairStatus,
        actor_id: UUID,
        comment: str | None,
    ) -> None:
        allowed = ALLOWED_TRANSITIONS.get(repair.status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Transition {repair.status.value} → {new_status.value} non autorisée",
            )
        old_status = repair.status
        repair.status = new_status
        self._record_status_change(repair, old_status, new_status, actor_id, comment)

    def _record_status_change(
        self,
        repair: Repair,
        old_status: RepairStatus | None,
        new_status: RepairStatus,
        actor_id: UUID,
        comment: str | None,
    ) -> None:
        self.db.add(
            RepairStatusHistory(
                repair_id=repair.id,
                old_status=old_status.value if old_status else None,
                new_status=new_status.value,
                changed_by=actor_id,
                comment=comment,
            )
        )

    def _apply_status_side_effects(self, repair: Repair, new_status: RepairStatus) -> None:
        now = datetime.now(UTC)
        if new_status == RepairStatus.in_progress and repair.started_at is None:
            repair.started_at = now
        if (
            new_status == RepairStatus.in_progress
            and self.set_unit_under_repair
            and repair.urgency == UrgencyLevel.high
        ):
            unit = self.db.query(Unit).filter(Unit.id == repair.unit_id).first()
            if unit:
                unit.status = UnitStatus.under_repair

    def _get_unit_or_404(self, unit_id: UUID) -> Unit:
        unit = self.db.query(Unit).filter(Unit.id == unit_id).first()
        if unit is None:
            raise HTTPException(status_code=404, detail="Logement introuvable")
        return unit

    def _get_or_404(self, repair_id: UUID) -> Repair:
        repair = (
            self.db.query(Repair)
            .options(
                joinedload(Repair.unit),
                joinedload(Repair.building),
                joinedload(Repair.reporter),
                joinedload(Repair.assignee),
                joinedload(Repair.attachments).joinedload(RepairAttachment.uploader),
                joinedload(Repair.status_history).joinedload(RepairStatusHistory.changer),
            )
            .filter(Repair.id == repair_id)
            .first()
        )
        if repair is None:
            raise HTTPException(status_code=404, detail="Réparation introuvable")
        return repair

    def _ensure_read_access(self, actor: User) -> None:
        if actor.role.code in ("super_admin", "admin_familial", "gestionnaire", "proprietaire"):
            return
        if actor.role.code == "locataire" and role_has_permission(actor.role.code, Permission.REPAIRS_MANAGE):
            return
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    def _ensure_manage_access(self, actor: User) -> None:
        if actor.role.code in ("super_admin", "admin_familial", "gestionnaire"):
            if actor.role.code == "admin_familial" and not role_has_permission(
                actor.role.code, Permission.REPAIRS_MANAGE
            ):
                raise HTTPException(status_code=403, detail="Accès non autorisé")
            return
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    def _to_summary(self, repair: Repair) -> RepairSummaryItem:
        return RepairSummaryItem(
            id=str(repair.id),
            title=repair.title,
            unit_code=repair.unit.code if repair.unit else "",
            building_name=repair.building.name if repair.building else "",
            urgency=repair.urgency,
            status=repair.status,
            reported_by_name=f"{repair.reporter.first_name} {repair.reporter.last_name}",
            assigned_to_name=(
                f"{repair.assignee.first_name} {repair.assignee.last_name}"
                if repair.assignee
                else None
            ),
            reported_at=repair.reported_at,
            final_cost=repair.final_cost,
        )

    def _to_detail(self, repair: Repair) -> RepairDetail:
        summary = self._to_summary(repair)
        attachments = [
            RepairAttachmentResponse(
                id=str(item.id),
                file_url=item.file_url,
                file_type=item.file_type.value,
                uploaded_by_name=f"{item.uploader.first_name} {item.uploader.last_name}",
                uploaded_at=item.uploaded_at,
            )
            for item in repair.attachments
        ]
        return RepairDetail(
            **summary.model_dump(),
            unit_id=str(repair.unit_id),
            building_id=str(repair.building_id),
            description=repair.description,
            estimated_cost=repair.estimated_cost,
            expense_id=str(repair.expense_id) if repair.expense_id else None,
            started_at=repair.started_at,
            completed_at=repair.completed_at,
            cancelled_at=repair.cancelled_at,
            cancellation_reason=repair.cancellation_reason,
            notes=repair.notes,
            attachments=attachments,
            updated_at=repair.updated_at,
        )
