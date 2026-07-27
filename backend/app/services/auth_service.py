from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    get_refresh_token_expiry,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    AuthUserSummary,
    ChangePasswordRequest,
    TokenResponse,
    UserProfileResponse,
)

settings = get_settings()


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def login(self, email: str, password: str) -> TokenResponse:
        user = (
            self.db.query(User)
            .options(joinedload(User.role))
            .filter(User.email == email.lower())
            .first()
        )
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Compte désactivé",
            )

        user.last_login_at = datetime.now(UTC)
        access_token = create_access_token(user.id)
        refresh_token = self._create_refresh_token(user)
        self.db.commit()
        self.db.refresh(user)

        return self._build_token_response(user, access_token, refresh_token)

    def refresh(self, refresh_token: str) -> TokenResponse:
        token_hash = hash_token(refresh_token)
        stored_token = (
            self.db.query(RefreshToken)
            .options(joinedload(RefreshToken.user).joinedload(User.role))
            .filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
            .first()
        )
        if stored_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token invalide",
            )

        expires_at = stored_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expiré",
            )

        user = stored_token.user
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Compte désactivé",
            )

        stored_token.revoked_at = datetime.now(UTC)
        access_token = create_access_token(user.id)
        new_refresh_token = self._create_refresh_token(user)
        self.db.commit()

        return self._build_token_response(user, access_token, new_refresh_token)

    def logout(self, user: User, refresh_token: str) -> None:
        token_hash = hash_token(refresh_token)
        stored_token = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user.id,
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
            .first()
        )
        if stored_token is not None:
            stored_token.revoked_at = datetime.now(UTC)
            self.db.commit()

    def change_password(self, user: User, payload: ChangePasswordRequest) -> None:
        if not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mot de passe actuel incorrect",
            )
        if payload.current_password == payload.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le nouveau mot de passe doit être différent",
            )

        user.password_hash = hash_password(payload.new_password)
        self._revoke_user_refresh_tokens(user)
        self.db.commit()

    def get_profile(self, user: User) -> UserProfileResponse:
        return UserProfileResponse(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            role={"code": user.role.code, "label": user.role.label},
            is_active=user.is_active,
            last_login_at=user.last_login_at,
        )

    def _create_refresh_token(self, user: User) -> str:
        refresh_token = generate_refresh_token()
        stored_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=get_refresh_token_expiry(),
        )
        self.db.add(stored_token)
        return refresh_token

    def _revoke_user_refresh_tokens(self, user: User) -> None:
        now = datetime.now(UTC)
        for token in user.refresh_tokens:
            if token.revoked_at is None:
                token.revoked_at = now

    def _build_token_response(
        self, user: User, access_token: str, refresh_token: str
    ) -> TokenResponse:
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=AuthUserSummary(
                id=str(user.id),
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role.code,
            ),
        )
