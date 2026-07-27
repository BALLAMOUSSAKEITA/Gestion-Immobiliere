from datetime import UTC, datetime
from math import ceil
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.core.approval_actions import SENSITIVE_ACTIONS
from app.models.audit import ApprovalRequest, AuditLog
from app.models.enums import ApprovalRequestStatus
from app.models.user import User
from app.schemas.approval import (
    ApprovalRequestCreate,
    ApprovalRequestDetail,
    ApprovalRequestListResponse,
    ApprovalRequestSummary,
    ApprovalUserBrief,
)
from app.schemas.audit import (
    AuditLogDetail,
    AuditLogListResponse,
    AuditLogSummary,
    AuditUserBrief,
)
from app.services.approval_executor import ApprovalExecutor
from app.services.audit_service import AuditService


def _user_brief(user: User) -> ApprovalUserBrief:
    return ApprovalUserBrief(
        id=str(user.id),
        full_name=f"{user.first_name} {user.last_name}",
        email=user.email,
    )


def _audit_user_brief(user: User) -> AuditUserBrief:
    return AuditUserBrief(
        id=str(user.id),
        full_name=f"{user.first_name} {user.last_name}",
        email=user.email,
    )


class ApprovalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.executor = ApprovalExecutor(db)
        self.audit = AuditService(db)

    @staticmethod
    def requires_approval(actor: User) -> bool:
        return actor.role.code != "super_admin"

    def create_request(
        self,
        actor: User,
        payload: ApprovalRequestCreate,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ApprovalRequestDetail:
        if actor.role.code not in ("super_admin", "admin_familial", "gestionnaire"):
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        if payload.action_code not in SENSITIVE_ACTIONS:
            raise HTTPException(status_code=400, detail="Action non soumise à validation")

        entity_id = UUID(payload.entity_id)
        existing = (
            self.db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.action_code == payload.action_code,
                ApprovalRequest.entity_id == entity_id,
                ApprovalRequest.status == ApprovalRequestStatus.pending,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Une demande est déjà en attente pour cette action",
            )

        snapshot = self.executor.capture_entity_snapshot(
            payload.action_code, payload.entity_type, entity_id
        )
        request = ApprovalRequest(
            action_code=payload.action_code,
            entity_type=payload.entity_type,
            entity_id=entity_id,
            requested_by=actor.id,
            reason=payload.reason.strip(),
            payload_before=snapshot,
            payload_after=payload.payload_after,
            status=ApprovalRequestStatus.pending,
        )
        self.db.add(request)
        self.db.flush()
        self.audit.log(
            user=actor,
            action="approval_request.create",
            entity_type="approval_request",
            entity_id=request.id,
            new_values={
                "action_code": payload.action_code,
                "target_entity_type": payload.entity_type,
                "target_entity_id": payload.entity_id,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()
        return self._to_detail(self._get_or_404(request.id))

    def list_requests(
        self,
        actor: User,
        *,
        page: int = 1,
        page_size: int = 20,
        status_filter: ApprovalRequestStatus | None = None,
        mine: bool = False,
    ) -> ApprovalRequestListResponse:
        if mine:
            if actor.role.code not in ("super_admin", "admin_familial", "gestionnaire"):
                raise HTTPException(status_code=403, detail="Accès non autorisé")
            query = self.db.query(ApprovalRequest).filter(
                ApprovalRequest.requested_by == actor.id
            )
        else:
            if actor.role.code != "super_admin":
                raise HTTPException(status_code=403, detail="Accès non autorisé")
            query = self.db.query(ApprovalRequest)

        if status_filter:
            query = query.filter(ApprovalRequest.status == status_filter)

        total = query.count()
        items = (
            query.options(
                joinedload(ApprovalRequest.requester),
                joinedload(ApprovalRequest.reviewer),
            )
            .order_by(ApprovalRequest.requested_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        pages = ceil(total / page_size) if total else 0
        return ApprovalRequestListResponse(
            items=[self._to_summary(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_request(self, actor: User, request_id: UUID) -> ApprovalRequestDetail:
        request = self._get_or_404(request_id)
        if actor.role.code != "super_admin" and request.requested_by != actor.id:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        return self._to_detail(request)

    def approve(
        self,
        actor: User,
        request_id: UUID,
        *,
        review_comment: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ApprovalRequestDetail:
        if actor.role.code != "super_admin":
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        request = self._get_or_404(request_id)
        if request.status != ApprovalRequestStatus.pending:
            raise HTTPException(status_code=400, detail="Demande déjà traitée")

        self.executor.execute(
            request,
            actor,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        request.status = ApprovalRequestStatus.approved
        request.reviewed_by = actor.id
        request.reviewed_at = datetime.now(UTC)
        request.review_comment = review_comment
        request.executed_at = datetime.now(UTC)
        self.db.commit()
        from app.services.notification_hooks import notify_approval_reviewed

        notify_approval_reviewed(self.db, request.requested_by, True, review_comment)
        return self._to_detail(self._get_or_404(request_id))

    def reject(
        self,
        actor: User,
        request_id: UUID,
        *,
        review_comment: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ApprovalRequestDetail:
        if actor.role.code != "super_admin":
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        request = self._get_or_404(request_id)
        if request.status != ApprovalRequestStatus.pending:
            raise HTTPException(status_code=400, detail="Demande déjà traitée")
        if not review_comment or not review_comment.strip():
            raise HTTPException(status_code=400, detail="Commentaire obligatoire pour un rejet")

        request.status = ApprovalRequestStatus.rejected
        request.reviewed_by = actor.id
        request.reviewed_at = datetime.now(UTC)
        request.review_comment = review_comment.strip()
        self.audit.log(
            user=actor,
            action="approval_request.reject",
            entity_type="approval_request",
            entity_id=request.id,
            old_values={"status": ApprovalRequestStatus.pending.value},
            new_values={"status": ApprovalRequestStatus.rejected.value},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.commit()
        from app.services.notification_hooks import notify_approval_reviewed

        notify_approval_reviewed(self.db, request.requested_by, False, review_comment)
        return self._to_detail(self._get_or_404(request_id))

    def cancel(self, actor: User, request_id: UUID) -> ApprovalRequestDetail:
        request = self._get_or_404(request_id)
        if request.requested_by != actor.id:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        if request.status != ApprovalRequestStatus.pending:
            raise HTTPException(status_code=400, detail="Demande déjà traitée")
        request.status = ApprovalRequestStatus.cancelled
        self.db.commit()
        return self._to_detail(self._get_or_404(request_id))

    def _get_or_404(self, request_id: UUID) -> ApprovalRequest:
        request = (
            self.db.query(ApprovalRequest)
            .options(
                joinedload(ApprovalRequest.requester),
                joinedload(ApprovalRequest.reviewer),
            )
            .filter(ApprovalRequest.id == request_id)
            .first()
        )
        if request is None:
            raise HTTPException(status_code=404, detail="Demande introuvable")
        return request

    def _to_summary(self, request: ApprovalRequest) -> ApprovalRequestSummary:
        return ApprovalRequestSummary(
            id=str(request.id),
            action_code=request.action_code,
            entity_type=request.entity_type,
            entity_id=str(request.entity_id),
            status=request.status,
            reason=request.reason,
            requested_by=_user_brief(request.requester),
            requested_at=request.requested_at,
            reviewed_by=_user_brief(request.reviewer) if request.reviewer else None,
            reviewed_at=request.reviewed_at,
            review_comment=request.review_comment,
            executed_at=request.executed_at,
        )

    def _to_detail(self, request: ApprovalRequest) -> ApprovalRequestDetail:
        summary = self._to_summary(request)
        return ApprovalRequestDetail(
            **summary.model_dump(),
            payload_before=request.payload_before,
            payload_after=request.payload_after,
        )


class AuditLogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_logs(
        self,
        actor: User,
        *,
        page: int = 1,
        page_size: int = 20,
        user_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        action: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> AuditLogListResponse:
        if actor.role.code not in ("super_admin", "admin_familial"):
            raise HTTPException(status_code=403, detail="Accès non autorisé")

        query = self.db.query(AuditLog).options(joinedload(AuditLog.user))
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if date_from:
            query = query.filter(AuditLog.created_at >= date_from)
        if date_to:
            query = query.filter(AuditLog.created_at <= date_to)

        total = query.count()
        logs = (
            query.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        pages = ceil(total / page_size) if total else 0
        return AuditLogListResponse(
            items=[self._to_summary(log) for log in logs],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_log(self, actor: User, log_id: UUID) -> AuditLogDetail:
        if actor.role.code not in ("super_admin", "admin_familial"):
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        log = (
            self.db.query(AuditLog)
            .options(joinedload(AuditLog.user))
            .filter(AuditLog.id == log_id)
            .first()
        )
        if log is None:
            raise HTTPException(status_code=404, detail="Entrée introuvable")
        return self._to_detail(log)

    def list_entity_logs(
        self, actor: User, entity_type: str, entity_id: UUID
    ) -> list[AuditLogSummary]:
        if actor.role.code not in ("super_admin", "admin_familial"):
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        logs = (
            self.db.query(AuditLog)
            .options(joinedload(AuditLog.user))
            .filter(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(AuditLog.created_at.desc())
            .limit(100)
            .all()
        )
        return [self._to_summary(log) for log in logs]

    def _to_summary(self, log: AuditLog) -> AuditLogSummary:
        return AuditLogSummary(
            id=str(log.id),
            user=_audit_user_brief(log.user),
            action=log.action,
            entity_type=log.entity_type,
            entity_id=str(log.entity_id),
            created_at=log.created_at,
        )

    def _to_detail(self, log: AuditLog) -> AuditLogDetail:
        summary = self._to_summary(log)
        return AuditLogDetail(
            **summary.model_dump(),
            old_values=log.old_values,
            new_values=log.new_values,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
        )


def request_meta(http_request: Request | None) -> tuple[str | None, str | None]:
    if http_request is None:
        return None, None
    forwarded = http_request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else http_request.client.host if http_request.client else None
    return ip, http_request.headers.get("user-agent")
