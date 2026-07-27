from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.building import Unit
from app.models.enums import VisitRequestStatus
from app.models.portal import VisitRequest
from app.models.role import Role
from app.models.user import User
from app.schemas.portal import (
    VisitRequestCreate,
    VisitRequestListResponse,
    VisitRequestSummary,
    VisitRequestUpdate,
)
from app.services.building_service import BuildingAccessService
from app.services.unit_service import UnitService


class VisitRequestService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_public(self, payload: VisitRequestCreate) -> VisitRequestSummary:
        unit_id = UUID(payload.unit_id)
        UnitService(self.db).get_public_unit(unit_id)
        unit_row = (
            self.db.query(Unit)
            .options(joinedload(Unit.building))
            .filter(Unit.id == unit_id)
            .first()
        )
        if unit_row is None:
            raise HTTPException(status_code=404, detail="Logement introuvable")

        assigned_to = unit_row.building.manager_user_id or self._default_manager_id()

        request = VisitRequest(
            unit_id=unit_id,
            visitor_name=payload.visitor_name.strip(),
            visitor_email=str(payload.visitor_email),
            visitor_phone=payload.visitor_phone.strip(),
            preferred_date=payload.preferred_date,
            preferred_time=payload.preferred_time,
            message=payload.message,
            status=VisitRequestStatus.pending,
            assigned_to=assigned_to,
        )
        self.db.add(request)
        self.db.commit()
        from app.services.notification_hooks import notify_visit_requested

        notify_visit_requested(self.db, request)
        return self._to_summary(self._get_or_404(request.id))

    def list_requests(self, actor: User) -> VisitRequestListResponse:
        if actor.role.code not in ("super_admin", "admin_familial", "gestionnaire"):
            raise HTTPException(status_code=403, detail="Accès non autorisé")

        query = (
            self.db.query(VisitRequest)
            .join(Unit)
            .options(joinedload(VisitRequest.unit), joinedload(VisitRequest.assignee))
            .order_by(VisitRequest.created_at.desc())
        )
        allowed = BuildingAccessService.accessible_building_ids(self.db, actor)
        if allowed is not None:
            query = query.filter(
                Unit.building_id.in_(allowed) if allowed else Unit.id.is_(None)
            )
        items = query.all()
        return VisitRequestListResponse(
            items=[self._to_summary(item) for item in items],
            total=len(items),
        )

    def update_request(
        self, actor: User, request_id: UUID, payload: VisitRequestUpdate
    ) -> VisitRequestSummary:
        if actor.role.code not in ("super_admin", "admin_familial", "gestionnaire"):
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        request = self._get_or_404(request_id)
        BuildingAccessService.ensure_building_access(
            self.db, actor, request.unit.building_id
        )
        if payload.status is not None:
            request.status = payload.status
        if payload.assigned_to is not None:
            request.assigned_to = UUID(payload.assigned_to)
        self.db.commit()
        return self._to_summary(self._get_or_404(request_id))

    def _default_manager_id(self) -> UUID | None:
        manager = (
            self.db.query(User)
            .join(Role)
            .filter(Role.code.in_(("gestionnaire", "super_admin")), User.is_active.is_(True))
            .first()
        )
        return manager.id if manager else None

    def _get_or_404(self, request_id: UUID) -> VisitRequest:
        request = (
            self.db.query(VisitRequest)
            .options(joinedload(VisitRequest.unit), joinedload(VisitRequest.assignee))
            .filter(VisitRequest.id == request_id)
            .first()
        )
        if request is None:
            raise HTTPException(status_code=404, detail="Demande introuvable")
        return request

    def _to_summary(self, request: VisitRequest) -> VisitRequestSummary:
        return VisitRequestSummary(
            id=str(request.id),
            unit_id=str(request.unit_id),
            unit_code=request.unit.code,
            visitor_name=request.visitor_name,
            visitor_email=request.visitor_email,
            visitor_phone=request.visitor_phone,
            preferred_date=request.preferred_date,
            preferred_time=request.preferred_time,
            message=request.message,
            status=request.status,
            assigned_to_name=(
                f"{request.assignee.first_name} {request.assignee.last_name}"
                if request.assignee
                else None
            ),
            created_at=request.created_at,
        )
