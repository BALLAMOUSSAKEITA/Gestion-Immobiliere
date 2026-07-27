from enum import Enum


class Permission(str, Enum):
    AUTH_LOGIN = "auth.login"
    USERS_MANAGE = "users.manage"
    BUILDINGS_MANAGE = "buildings.manage"
    UNITS_READ = "units.read"
    TENANTS_MANAGE = "tenants.manage"
    PAYMENTS_MANAGE = "payments.manage"
    PAYMENTS_READ = "payments.read"
    EXPENSES_MANAGE = "expenses.manage"
    EXPENSES_READ = "expenses.read"
    REPAIRS_MANAGE = "repairs.manage"
    REPORTS_READ = "reports.read"
    PUBLIC_LISTINGS = "public.listings"


ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    "super_admin": {
        Permission.AUTH_LOGIN,
        Permission.USERS_MANAGE,
        Permission.BUILDINGS_MANAGE,
        Permission.UNITS_READ,
        Permission.TENANTS_MANAGE,
        Permission.PAYMENTS_MANAGE,
        Permission.PAYMENTS_READ,
        Permission.EXPENSES_MANAGE,
        Permission.EXPENSES_READ,
        Permission.REPAIRS_MANAGE,
        Permission.REPORTS_READ,
    },
    "admin_familial": {
        Permission.AUTH_LOGIN,
        Permission.BUILDINGS_MANAGE,
        Permission.UNITS_READ,
        Permission.TENANTS_MANAGE,
        Permission.PAYMENTS_MANAGE,
        Permission.PAYMENTS_READ,
        Permission.EXPENSES_MANAGE,
        Permission.EXPENSES_READ,
        Permission.REPAIRS_MANAGE,
        Permission.REPORTS_READ,
    },
    "proprietaire": {
        Permission.AUTH_LOGIN,
        Permission.UNITS_READ,
        Permission.PAYMENTS_READ,
        Permission.EXPENSES_READ,
        Permission.REPAIRS_MANAGE,
        Permission.REPORTS_READ,
    },
    "gestionnaire": {
        Permission.AUTH_LOGIN,
        Permission.UNITS_READ,
        Permission.TENANTS_MANAGE,
        Permission.PAYMENTS_MANAGE,
        Permission.EXPENSES_MANAGE,
        Permission.REPAIRS_MANAGE,
    },
    "visiteur": {
        Permission.AUTH_LOGIN,
        Permission.PUBLIC_LISTINGS,
    },
    "locataire": {
        Permission.AUTH_LOGIN,
        Permission.UNITS_READ,
        Permission.PAYMENTS_READ,
        Permission.REPAIRS_MANAGE,
    },
}


def role_has_permission(role_code: str, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role_code, set())
