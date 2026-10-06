import logging

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import remember_plain_password, verify_password
from app.models.user import User

logger = logging.getLogger(__name__)

LEGACY_SUPER_ADMIN = ("admin@gestion-immo.local", "Admin123!")


def sync_recoverable_password_secrets(db: Session) -> None:
    """Enregistre le mot de passe lisible quand il correspond encore au hash connu."""
    settings = get_settings()
    candidates: list[tuple[str, str]] = [
        (settings.super_admin_email, settings.super_admin_password),
        LEGACY_SUPER_ADMIN,
    ]
    seen: set[str] = set()
    updated = 0

    for email, password in candidates:
        normalized = email.strip().lower()
        if normalized in seen or len(password) < 8:
            continue
        seen.add(normalized)

        user = db.query(User).filter(User.email.ilike(normalized)).first()
        if user is None or user.password_secret:
            continue
        if not verify_password(password, user.password_hash):
            continue
        remember_plain_password(user, password)
        updated += 1

    if updated:
        db.commit()
        logger.info("Mots de passe récupérables synchronisés pour %s compte(s)", updated)
