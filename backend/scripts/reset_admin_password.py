"""Reset or create the super admin account from environment variables.

Usage (local):
    cd backend
    python -m scripts.reset_admin_password

Usage (Railway):
    railway run python -m scripts.reset_admin_password
"""

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User


def main() -> None:
    settings = get_settings()
    email = settings.super_admin_email.strip().lower()
    password = settings.super_admin_password

    if len(password) < 8:
        raise SystemExit("SUPER_ADMIN_PASSWORD doit contenir au moins 8 caractères.")

    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.code == "super_admin").first()
        if role is None:
            raise SystemExit("Rôle super_admin introuvable. Exécutez d'abord: alembic upgrade head")

        user = db.query(User).filter(User.email.ilike(email)).first()
        password_hash = hash_password(password)

        if user is None:
            user = User(
                email=email,
                password_hash=password_hash,
                first_name="Super",
                last_name="Admin",
                phone="+2250700000000",
                role_id=role.id,
                is_active=True,
            )
            db.add(user)
            action = "créé"
        else:
            user.email = email
            user.password_hash = password_hash
            user.is_active = True
            user.role_id = role.id
            action = "mis à jour"

        db.commit()
        print(f"Compte super admin {action}: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
