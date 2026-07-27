from fastapi import HTTPException, Request, status

from app.core import approval_actions as actions
from app.models.user import User
from app.schemas.approval import ApprovalRequestCreate, ApprovalRequestDetail
from app.services.approval_service import ApprovalService, request_meta
from sqlalchemy.orm import Session


def handle_sensitive_action(
    db: Session,
    actor: User,
    *,
    action_code: str,
    entity_type: str,
    entity_id: str,
    reason: str | None,
    payload_after: dict | None = None,
    http_request: Request | None = None,
    execute_direct,
) -> ApprovalRequestDetail | None:
    """Exécute directement si super_admin, sinon crée une demande de validation."""
    if not ApprovalService.requires_approval(actor):
        execute_direct()
        return None
    if not reason or not reason.strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette action nécessite une validation. Fournissez une raison.",
        )
    ip, ua = request_meta(http_request)
    return ApprovalService(db).create_request(
        actor,
        ApprovalRequestCreate(
            action_code=action_code,
            entity_type=entity_type,
            entity_id=entity_id,
            reason=reason.strip(),
            payload_after=payload_after,
        ),
        ip_address=ip,
        user_agent=ua,
    )
