# Sprint 1 — Authentification & rôles (RBAC)

**Durée estimée :** 1 à 2 semaines  
**Prérequis :** Sprint 0  
**Dépendances pour le sprint suivant :** Sprint 2

---

## Objectif

Implémenter l'authentification JWT, la gestion des 6 rôles utilisateurs, et un système de permissions (RBAC) appliqué sur toutes les routes protégées.

---

## User stories

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S1-01 | Utilisateur | Me connecter avec email/mot de passe | Accéder à mon espace |
| S1-02 | Utilisateur | Me déconnecter | Sécuriser ma session |
| S1-03 | Super Admin | Avoir un compte seed au premier démarrage | Administrer la plateforme |
| S1-04 | Système | Vérifier les permissions par rôle | Restreindre l'accès aux données |
| S1-05 | Utilisateur | Rafraîchir mon token | Rester connecté sans re-login |

---

## Rôles et permissions (matrice de base)

| Permission | super_admin | admin_familial | proprietaire | gestionnaire | visiteur | locataire |
|------------|:-----------:|:--------------:|:------------:|:------------:|:--------:|:---------:|
| auth.login | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| users.manage | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| buildings.manage | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| units.read | ✅ | ✅ | ✅* | ✅* | ❌ | ✅* |
| tenants.manage | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| payments.manage | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| payments.read | ✅ | ✅ | ✅* | ❌ | ✅* |
| expenses.manage | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| expenses.read | ✅ | ✅ | ✅* | ❌ | ❌ | ❌ |
| repairs.manage | ✅ | ✅ | ❌ | ✅ | ❌ | ✅* |
| reports.read | ✅ | ✅ | ✅* | ❌ | ❌ | ❌ |
| public.listings | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

`*` = accès filtré aux biens/données assignés uniquement (implémenté progressivement dès Sprint 3)

---

## Modèles de données

### Table `roles`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| code | VARCHAR(50) | UNIQUE, NOT NULL |
| label | VARCHAR(100) | NOT NULL |
| description | TEXT | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |

**Données seed :**

| code | label |
|------|-------|
| `super_admin` | Super Administrateur |
| `admin_familial` | Administrateur Familial |
| `proprietaire` | Propriétaire |
| `gestionnaire` | Gestionnaire |
| `visiteur` | Visiteur |
| `locataire` | Locataire |

### Table `users`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| first_name | VARCHAR(100) | NOT NULL |
| last_name | VARCHAR(100) | NOT NULL |
| phone | VARCHAR(20) | nullable |
| role_id | UUID | FK → roles.id |
| is_active | BOOLEAN | DEFAULT true |
| last_login_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

### Table `refresh_tokens`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| token_hash | VARCHAR(255) | NOT NULL |
| expires_at | TIMESTAMPTZ | NOT NULL |
| revoked_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |

---

## Endpoints API

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| POST | `/api/v1/auth/login` | Non | Connexion, retourne access + refresh token |
| POST | `/api/v1/auth/refresh` | Non | Renouveler l'access token |
| POST | `/api/v1/auth/logout` | Oui | Révoquer le refresh token |
| GET | `/api/v1/auth/me` | Oui | Profil utilisateur connecté |
| POST | `/api/v1/auth/change-password` | Oui | Changer son mot de passe |

### POST `/api/v1/auth/login`

**Body :**
```json
{
  "email": "admin@example.com",
  "password": "SecurePass123!"
}
```

**Réponse 200 :**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "admin@example.com",
    "first_name": "Super",
    "last_name": "Admin",
    "role": "super_admin"
  }
}
```

### GET `/api/v1/auth/me`

**Réponse 200 :**
```json
{
  "id": "uuid",
  "email": "admin@example.com",
  "first_name": "Super",
  "last_name": "Admin",
  "phone": "+2250700000000",
  "role": {
    "code": "super_admin",
    "label": "Super Administrateur"
  },
  "is_active": true,
  "last_login_at": "2026-07-26T14:30:00Z"
}
```

---

## Tâches Backend

- [ ] Modèles SQLAlchemy `Role`, `User`, `RefreshToken`
- [ ] Migration Alembic + seed des 6 rôles
- [ ] Script seed super admin (`admin@gestion-immo.local` / mot de passe configurable)
- [ ] Hashage bcrypt des mots de passe
- [ ] Génération JWT access (1h) et refresh (7 jours)
- [ ] Dependency `get_current_user` (FastAPI Depends)
- [ ] Dependency `require_roles(*roles)` pour RBAC
- [ ] Enum `Permission` + mapping rôle → permissions
- [ ] Gestion erreurs : 401 (non auth), 403 (non autorisé)
- [ ] Tests unitaires auth (login, refresh, logout, me)

### Fichiers à créer

```
backend/app/
├── models/user.py
├── models/role.py
├── schemas/auth.py
├── schemas/user.py
├── services/auth_service.py
├── api/v1/auth.py
├── core/security.py          # JWT encode/decode, bcrypt
└── core/permissions.py       # RBAC helpers
```

---

## Tâches Frontend

- [ ] Page `/login` (formulaire email + mot de passe)
- [ ] Page `/logout` (action + redirect)
- [ ] Stockage tokens (httpOnly cookie recommandé, ou localStorage en dev)
- [ ] Contexte React `AuthProvider` + hook `useAuth()`
- [ ] Intercepteur fetch : ajouter header `Authorization: Bearer`
- [ ] Redirect automatique vers `/login` si 401
- [ ] Layout protégé `/dashboard/*` (placeholder)
- [ ] Affichage nom + rôle dans header
- [ ] Page `/profil` (lecture infos `/auth/me`)
- [ ] Formulaire changement de mot de passe

### Pages UI

| Route | Accès | Contenu |
|-------|-------|---------|
| `/login` | Public | Formulaire connexion |
| `/dashboard` | Auth | « Bienvenue » + rôle affiché |
| `/profil` | Auth | Infos utilisateur |

### Composants

- `LoginForm` — validation Zod (email, password min 8 chars)
- `ProtectedRoute` — wrapper vérifiant auth
- `RoleBadge` — badge coloré par rôle

---

## Sécurité

- [ ] Mot de passe min 8 caractères, 1 majuscule, 1 chiffre
- [ ] Rate limiting login : 5 tentatives / 15 min / IP (optionnel Sprint 1, obligatoire prod)
- [ ] Refresh token stocké hashé en BDD
- [ ] Révocation refresh token au logout
- [ ] HTTPS en production (documenté)

---

## Critères d'acceptation

- [ ] Super admin seed créé au premier `alembic upgrade`
- [ ] Login retourne tokens valides
- [ ] Route protégée sans token → 401
- [ ] Route admin sans rôle admin → 403
- [ ] Refresh token renouvelle l'access token
- [ ] Logout invalide le refresh token
- [ ] Frontend : connexion → redirect dashboard
- [ ] Frontend : déconnexion → redirect login
- [ ] Tests backend auth passent à 100%

---

## Dépendances Sprint 2

Le Sprint 2 utilisera `require_roles("super_admin")` pour CRUD utilisateurs et l'attribution de rôles.
