import logging
import secrets
import string
from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.permission_codes import ADMIN_FAMILIAL_PERMISSION_CODES
from app.core.security import hash_password
from app.models.audit import ApprovalRequest, AuditLog
from app.models.building import Building
from app.models.document import Document, DocumentShare
from app.models.expense import Expense
from app.models.notification import Notification, NotificationPreference
from app.models.owner_profile import (
    OwnerProfile,
    UserBuildingAssignment,
    UserOwnerAssignment,
)
from app.models.payment import Payment, Receipt
from app.models.portal import ContactMessage, TenantNotice, VisitRequest
from app.models.refresh_token import RefreshToken
from app.models.repair import Repair, RepairAttachment, RepairStatusHistory
from app.models.report import ReportSnapshot
from app.models.role import Role
from app.models.tenant import Lease, LeaseRentHistory, Tenant
from app.models.user import User
from app.models.user_permission import UserPermission
from app.schemas.user import (
    CreateUserRequest,
    PermissionItem,
    ResetPasswordResponse,
    UpdateUserRequest,
    UserDetailResponse,
    UserListResponse,
    UserSummaryResponse,
)

logger = logging.getLogger(__name__)


class PermissionService:
    @staticmethod
    def check(user: User, permission_code: str, scope_type: str | None = None) -> bool:
        if user.role.code == "super_admin":
            return True
        if user.role.code != "admin_familial":
            return False

        for permission in user.permissions:
            if (
                permission.permission_code == permission_code
                and permission.granted
                and (scope_type is None or permission.scope_type in (scope_type, "all"))
            ):
                return True
        return False


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role: str | None = None,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> UserListResponse:
        query = self.db.query(User).options(joinedload(User.role))

        if role:
            query = query.join(Role).filter(Role.code == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if search:
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(User.email).like(term),
                    func.lower(User.first_name).like(term),
                    func.lower(User.last_name).like(term),
                )
            )

        total = query.count()
        items = (
            query.order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        pages = ceil(total / page_size) if total else 0

        return UserListResponse(
            items=[self._to_summary(user) for user in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_user(self, user_id: UUID) -> UserDetailResponse:
        user = self._get_user_or_404(user_id)
        return self._to_detail(user)

    def create_user(self, payload: CreateUserRequest, actor: User) -> UserDetailResponse:
        role = self._get_role_by_code(payload.role_code)
        email = payload.email.strip().lower()

        if self.db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

        password = payload.password or self._generate_password()
        user = User(
            email=email,
            password_hash=hash_password(password),
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            phone=payload.phone,
            role_id=role.id,
            is_active=payload.is_active,
        )
        self.db.add(user)
        self.db.flush()

        if role.code == "admin_familial" and payload.permissions:
            self._replace_permissions(user, payload.permissions)

        if role.code == "gestionnaire" and payload.building_ids:
            self._replace_building_assignments(user, payload.building_ids, actor.id)

        if role.code == "proprietaire":
            if not payload.owner_profile_id:
                raise HTTPException(
                    status_code=400,
                    detail="Un profil propriétaire est requis pour ce rôle",
                )
            self._link_owner_profile(user, payload.owner_profile_id)

        self.db.commit()
        self.db.refresh(user)
        self._send_welcome_email(user.email, password)
        return self._to_detail(self._get_user_or_404(user.id))

    def update_user(
        self, user_id: UUID, payload: UpdateUserRequest, actor: User
    ) -> UserDetailResponse:
        user = self._get_user_or_404(user_id)

        if payload.role_code and user.id == actor.id:
            raise HTTPException(
                status_code=400, detail="Impossible de modifier votre propre rôle",
            )

        if payload.email:
            email = payload.email.strip().lower()
            existing = (
                self.db.query(User)
                .filter(User.email == email, User.id != user.id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
            user.email = email

        if payload.first_name is not None:
            user.first_name = payload.first_name.strip()
        if payload.last_name is not None:
            user.last_name = payload.last_name.strip()
        if payload.phone is not None:
            user.phone = payload.phone
        if payload.is_active is not None:
            if not payload.is_active:
                self._ensure_not_last_super_admin(user)
            user.is_active = payload.is_active

        if payload.role_code:
            role = self._get_role_by_code(payload.role_code)
            user.role_id = role.id

        if payload.permissions is not None and user.role.code == "admin_familial":
            self._replace_permissions(user, payload.permissions)

        if payload.building_ids is not None and user.role.code == "gestionnaire":
            self._replace_building_assignments(user, payload.building_ids, actor.id)

        if payload.owner_profile_id and user.role.code == "proprietaire":
            self._link_owner_profile(user, payload.owner_profile_id)

        self.db.commit()
        return self._to_detail(self._get_user_or_404(user.id))

    def delete_user(self, user_id: UUID, actor: User) -> None:
        user = self._get_user_or_404(user_id)
        if user.id == actor.id:
            raise HTTPException(
                status_code=400,
                detail="Impossible de supprimer votre propre compte",
            )
        self._ensure_not_last_super_admin(user)

        # Données personnelles / sessions
        self.db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete(
            synchronize_session=False
        )
        self.db.query(Notification).filter(Notification.user_id == user_id).delete(
            synchronize_session=False
        )
        self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).delete(synchronize_session=False)
        self.db.query(UserPermission).filter(UserPermission.user_id == user_id).delete(
            synchronize_session=False
        )
        self.db.query(UserBuildingAssignment).filter(
            UserBuildingAssignment.user_id == user_id
        ).delete(synchronize_session=False)
        self.db.query(UserOwnerAssignment).filter(
            UserOwnerAssignment.user_id == user_id
        ).delete(synchronize_session=False)
        self.db.query(ContactMessage).filter(
            (ContactMessage.sender_user_id == user_id)
            | (ContactMessage.recipient_user_id == user_id)
        ).delete(synchronize_session=False)

        # Délier les profils
        self.db.query(OwnerProfile).filter(OwnerProfile.user_id == user_id).update(
            {OwnerProfile.user_id: None}, synchronize_session=False
        )
        self.db.query(Tenant).filter(Tenant.user_id == user_id).update(
            {Tenant.user_id: None}, synchronize_session=False
        )

        # Réassigner / nullifier les références historiques
        self.db.query(Building).filter(Building.manager_user_id == user_id).update(
            {Building.manager_user_id: None}, synchronize_session=False
        )
        self.db.query(Building).filter(Building.created_by == user_id).update(
            {Building.created_by: actor.id}, synchronize_session=False
        )
        self.db.query(UserBuildingAssignment).filter(
            UserBuildingAssignment.assigned_by == user_id
        ).update({UserBuildingAssignment.assigned_by: actor.id}, synchronize_session=False)

        self.db.query(Tenant).filter(Tenant.created_by == user_id).update(
            {Tenant.created_by: actor.id}, synchronize_session=False
        )
        self.db.query(Lease).filter(Lease.created_by == user_id).update(
            {Lease.created_by: actor.id}, synchronize_session=False
        )
        self.db.query(LeaseRentHistory).filter(LeaseRentHistory.changed_by == user_id).update(
            {LeaseRentHistory.changed_by: actor.id}, synchronize_session=False
        )

        self.db.query(Payment).filter(Payment.recorded_by == user_id).update(
            {Payment.recorded_by: actor.id}, synchronize_session=False
        )
        self.db.query(Payment).filter(Payment.validated_by == user_id).update(
            {Payment.validated_by: None}, synchronize_session=False
        )
        self.db.query(Receipt).filter(Receipt.issued_by == user_id).update(
            {Receipt.issued_by: actor.id}, synchronize_session=False
        )

        self.db.query(Expense).filter(Expense.recorded_by == user_id).update(
            {Expense.recorded_by: actor.id}, synchronize_session=False
        )
        self.db.query(Expense).filter(Expense.validated_by == user_id).update(
            {Expense.validated_by: None}, synchronize_session=False
        )

        self.db.query(Repair).filter(Repair.reported_by == user_id).update(
            {Repair.reported_by: actor.id}, synchronize_session=False
        )
        self.db.query(Repair).filter(Repair.assigned_to == user_id).update(
            {Repair.assigned_to: None}, synchronize_session=False
        )
        self.db.query(RepairAttachment).filter(RepairAttachment.uploaded_by == user_id).update(
            {RepairAttachment.uploaded_by: actor.id}, synchronize_session=False
        )
        self.db.query(RepairStatusHistory).filter(
            RepairStatusHistory.changed_by == user_id
        ).update({RepairStatusHistory.changed_by: actor.id}, synchronize_session=False)

        self.db.query(Document).filter(Document.uploaded_by == user_id).update(
            {Document.uploaded_by: actor.id}, synchronize_session=False
        )
        self.db.query(DocumentShare).filter(DocumentShare.created_by == user_id).update(
            {DocumentShare.created_by: actor.id}, synchronize_session=False
        )

        self.db.query(ApprovalRequest).filter(ApprovalRequest.requested_by == user_id).update(
            {ApprovalRequest.requested_by: actor.id}, synchronize_session=False
        )
        self.db.query(ApprovalRequest).filter(ApprovalRequest.reviewed_by == user_id).update(
            {ApprovalRequest.reviewed_by: None}, synchronize_session=False
        )
        self.db.query(AuditLog).filter(AuditLog.user_id == user_id).update(
            {AuditLog.user_id: actor.id}, synchronize_session=False
        )

        self.db.query(VisitRequest).filter(VisitRequest.assigned_to == user_id).update(
            {VisitRequest.assigned_to: None}, synchronize_session=False
        )
        self.db.query(TenantNotice).filter(TenantNotice.published_by == user_id).update(
            {TenantNotice.published_by: actor.id}, synchronize_session=False
        )
        self.db.query(ReportSnapshot).filter(ReportSnapshot.generated_by == user_id).update(
            {ReportSnapshot.generated_by: None}, synchronize_session=False
        )

        self.db.delete(user)
        self.db.commit()

    def deactivate_user(self, user_id: UUID, actor: User) -> None:
        """Compatibilité : la suppression est désormais définitive."""
        self.delete_user(user_id, actor)

    def reset_password(self, user_id: UUID) -> ResetPasswordResponse:
        user = self._get_user_or_404(user_id)
        password = self._generate_password()
        user.password_hash = hash_password(password)
        self.db.commit()
        self._send_welcome_email(user.email, password)
        return ResetPasswordResponse(temporary_password=password)

    def get_permissions(self, user_id: UUID) -> list[PermissionItem]:
        user = self._get_user_or_404(user_id)
        if user.role.code != "admin_familial":
            raise HTTPException(status_code=400, detail="Utilisateur non admin familial")
        return self._permissions_to_items(user)

    def update_permissions(
        self, user_id: UUID, permissions: list[PermissionItem]
    ) -> list[PermissionItem]:
        user = self._get_user_or_404(user_id)
        if user.role.code != "admin_familial":
            raise HTTPException(status_code=400, detail="Utilisateur non admin familial")
        self._replace_permissions(user, permissions)
        self.db.commit()
        return self._permissions_to_items(self._get_user_or_404(user_id))

    def _get_user_or_404(self, user_id: UUID) -> User:
        user = (
            self.db.query(User)
            .options(
                joinedload(User.role),
                joinedload(User.permissions),
                joinedload(User.building_assignments),
                joinedload(User.owner_assignment),
                joinedload(User.owner_profile),
            )
            .filter(User.id == user_id)
            .first()
        )
        if user is None:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable")
        return user

    def _get_role_by_code(self, role_code: str) -> Role:
        role = self.db.query(Role).filter(Role.code == role_code).first()
        if role is None:
            raise HTTPException(status_code=400, detail="Rôle invalide")
        return role

    def _ensure_not_last_super_admin(self, user: User) -> None:
        if user.role.code != "super_admin" or not user.is_active:
            return
        active_super_admins = (
            self.db.query(User)
            .join(Role)
            .filter(Role.code == "super_admin", User.is_active.is_(True))
            .count()
        )
        if active_super_admins <= 1:
            raise HTTPException(
                status_code=400,
                detail="Impossible de supprimer le dernier super administrateur",
            )

    def _replace_permissions(self, user: User, permissions: list[PermissionItem]) -> None:
        user.permissions.clear()
        for item in permissions:
            if item.permission_code not in ADMIN_FAMILIAL_PERMISSION_CODES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Permission invalide: {item.permission_code}",
                )
            user.permissions.append(
                UserPermission(
                    permission_code=item.permission_code,
                    granted=item.granted,
                    scope_type=item.scope_type,
                    scope_id=item.scope_id,
                )
            )

    def _replace_building_assignments(
        self, user: User, building_ids: list[UUID], assigned_by: UUID
    ) -> None:
        user.building_assignments.clear()
        for building_id in building_ids:
            user.building_assignments.append(
                UserBuildingAssignment(
                    building_id=building_id,
                    assigned_by=assigned_by,
                )
            )

    def _link_owner_profile(self, user: User, owner_profile_id: UUID) -> None:
        profile = (
            self.db.query(OwnerProfile).filter(OwnerProfile.id == owner_profile_id).first()
        )
        if profile is None:
            raise HTTPException(status_code=404, detail="Profil propriétaire introuvable")

        if profile.user_id and profile.user_id != user.id:
            raise HTTPException(
                status_code=400,
                detail="Ce profil propriétaire est déjà lié à un utilisateur",
            )

        profile.user_id = user.id
        existing = user.owner_assignment
        if existing:
            existing.owner_profile_id = profile.id
        else:
            self.db.add(
                UserOwnerAssignment(user_id=user.id, owner_profile_id=profile.id)
            )

    def _permissions_to_items(self, user: User) -> list[PermissionItem]:
        existing = {item.permission_code: item for item in user.permissions}
        items: list[PermissionItem] = []
        for code in ADMIN_FAMILIAL_PERMISSION_CODES:
            permission = existing.get(code)
            items.append(
                PermissionItem(
                    permission_code=code,
                    granted=permission.granted if permission else False,
                    scope_type=permission.scope_type if permission else "all",
                    scope_id=permission.scope_id if permission else None,
                )
            )
        return items

    def _to_summary(self, user: User) -> UserSummaryResponse:
        return UserSummaryResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            role={"code": user.role.code, "label": user.role.label},
            is_active=user.is_active,
            created_at=user.created_at,
        )

    def _to_detail(self, user: User) -> UserDetailResponse:
        return UserDetailResponse(
            **self._to_summary(user).model_dump(),
            permissions=self._permissions_to_items(user)
            if user.role.code == "admin_familial"
            else [],
            building_ids=[str(item.building_id) for item in user.building_assignments],
            owner_profile_id=(
                str(user.owner_profile.id)
                if user.owner_profile
                else (
                    str(user.owner_assignment.owner_profile_id)
                    if user.owner_assignment
                    else None
                )
            ),
            last_login_at=user.last_login_at,
        )

    def _generate_password(self, length: int = 12) -> str:
        alphabet = string.ascii_letters + string.digits
        while True:
            password = "".join(secrets.choice(alphabet) for _ in range(length))
            if any(c.isupper() for c in password) and any(c.isdigit() for c in password):
                return password + "!"

    def _send_welcome_email(self, email: str, password: str) -> None:
        logger.info("Email de bienvenue simulé pour %s — mot de passe temporaire envoyé", email)
