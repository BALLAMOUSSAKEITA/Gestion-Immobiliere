# Sprint 2 — Gestion des utilisateurs

**Durée estimée :** 1 semaine  
**Prérequis :** Sprint 1  
**Dépendances pour le sprint suivant :** Sprint 3

---

## Objectif

Permettre au Super Administrateur de créer, modifier, désactiver et supprimer des utilisateurs, d'attribuer des rôles, et de définir les autorisations granulaires pour les Administrateurs Familiaux.

---

## User stories

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S2-01 | Super Admin | Créer un compte pour un membre de la famille | Lui donner accès lecture seule à ses biens |
| S2-02 | Super Admin | Créer un compte gestionnaire | Lui confier la gestion opérationnelle |
| S2-03 | Super Admin | Créer un compte locataire | Lui donner accès à son espace |
| S2-04 | Super Admin | Désactiver un compte | Bloquer l'accès sans supprimer l'historique |
| S2-05 | Super Admin | Modifier les autorisations d'un Admin Familial | Limiter son périmètre de gestion |
| S2-06 | Super Admin | Voir la liste de tous les utilisateurs | Administrer la plateforme |

---

## Modèles de données

### Table `user_permissions` (autorisations granulaires Admin Familial)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| permission_code | VARCHAR(100) | NOT NULL |
| granted | BOOLEAN | DEFAULT true |
| scope_type | VARCHAR(50) | nullable — `building`, `owner`, `all` |
| scope_id | UUID | nullable — ID immeuble ou propriétaire |
| created_at | TIMESTAMPTZ | NOT NULL |

**Codes permission pour admin_familial :**

| Code | Description |
|------|-------------|
| `buildings.manage` | Gérer immeubles |
| `units.manage` | Gérer logements |
| `tenants.manage` | Gérer locataires |
| `payments.manage` | Gérer paiements |
| `expenses.manage` | Gérer dépenses |
| `repairs.manage` | Gérer réparations |
| `reports.read` | Consulter rapports |
| `documents.manage` | Gérer documents |

### Table `user_building_assignments` (gestionnaire → immeubles)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| building_id | UUID | FK → buildings.id (Sprint 3) |
| assigned_at | TIMESTAMPTZ | NOT NULL |
| assigned_by | UUID | FK → users.id |

> Note : `building_id` FK sera ajoutée au Sprint 3. Créer la table sans FK stricte ou avec migration différée.

### Table `user_owner_assignments` (propriétaire → biens)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| owner_profile_id | UUID | FK → owner_profiles.id |
| created_at | TIMESTAMPTZ | NOT NULL |

### Table `owner_profiles` (membres de la famille propriétaires)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id, UNIQUE, nullable |
| first_name | VARCHAR(100) | NOT NULL |
| last_name | VARCHAR(100) | NOT NULL |
| phone | VARCHAR(20) | nullable |
| email | VARCHAR(255) | nullable |
| notes | TEXT | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

---

## Endpoints API

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/users` | super_admin | Liste paginée utilisateurs |
| POST | `/api/v1/users` | super_admin | Créer utilisateur |
| GET | `/api/v1/users/{id}` | super_admin | Détail utilisateur |
| PATCH | `/api/v1/users/{id}` | super_admin | Modifier utilisateur |
| DELETE | `/api/v1/users/{id}` | super_admin | Désactiver (soft delete) |
| POST | `/api/v1/users/{id}/reset-password` | super_admin | Réinitialiser mot de passe |
| GET | `/api/v1/users/{id}/permissions` | super_admin | Permissions admin familial |
| PUT | `/api/v1/users/{id}/permissions` | super_admin | Mettre à jour permissions |
| GET | `/api/v1/owner-profiles` | super_admin, admin_familial | Liste propriétaires famille |
| POST | `/api/v1/owner-profiles` | super_admin | Créer profil propriétaire |
| PATCH | `/api/v1/owner-profiles/{id}` | super_admin | Modifier profil |

### POST `/api/v1/users` — Body

```json
{
  "email": "gestionnaire@example.com",
  "password": "TempPass123!",
  "first_name": "Jean",
  "last_name": "Kouassi",
  "phone": "+2250700000001",
  "role_code": "gestionnaire",
  "is_active": true,
  "permissions": [],
  "building_ids": []
}
```

### GET `/api/v1/users` — Query params

| Param | Type | Description |
|-------|------|-------------|
| `page` | int | Page (default 1) |
| `page_size` | int | Taille (default 20, max 100) |
| `role` | string | Filtrer par rôle |
| `search` | string | Recherche nom/email |
| `is_active` | bool | Filtrer actifs/inactifs |

### Réponse liste paginée

```json
{
  "items": [...],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

---

## Tâches Backend

- [ ] Modèles `OwnerProfile`, `UserPermission`, `UserBuildingAssignment`, `UserOwnerAssignment`
- [ ] Migration Alembic
- [ ] CRUD utilisateurs avec validation Pydantic
- [ ] Soft delete (`is_active = false`, pas de suppression physique)
- [ ] Envoi email bienvenue avec mot de passe temporaire (mock SMTP en dev)
- [ ] Service `PermissionService.check(user, permission, scope)`
- [ ] Filtres et pagination sur liste utilisateurs
- [ ] Tests CRUD + permissions

### Fichiers

```
backend/app/
├── models/owner_profile.py
├── models/user_permission.py
├── schemas/user.py           # CreateUser, UpdateUser, UserList
├── schemas/owner_profile.py
├── services/user_service.py
├── services/permission_service.py
└── api/v1/users.py
```

---

## Tâches Frontend

### Pages

| Route | Rôle | Description |
|-------|------|-------------|
| `/dashboard/utilisateurs` | super_admin | Liste utilisateurs |
| `/dashboard/utilisateurs/nouveau` | super_admin | Formulaire création |
| `/dashboard/utilisateurs/[id]` | super_admin | Détail + édition |
| `/dashboard/utilisateurs/[id]/permissions` | super_admin | Matrice permissions (admin familial) |
| `/dashboard/proprietaires` | super_admin, admin_familial | Liste membres famille |

### Composants UI

- [ ] `UserTable` — tableau avec filtres rôle, recherche, statut
- [ ] `UserForm` — création/édition (email, nom, rôle, téléphone)
- [ ] `RoleSelect` — dropdown des 6 rôles
- [ ] `PermissionMatrix` — checkboxes permissions pour admin familial
- [ ] `OwnerProfileForm` — fiche membre famille
- [ ] Modale confirmation désactivation
- [ ] Badge statut actif/inactif

### UX

- Mot de passe généré automatiquement avec option « définir manuellement »
- Toast succès/erreur après chaque action
- Validation Zod côté client

---

## Règles métier

1. Seul `super_admin` peut créer/modifier/supprimer des utilisateurs.
2. Un utilisateur désactivé ne peut plus se connecter (vérifier `is_active` au login — Sprint 1).
3. Un `gestionnaire` doit être assigné à au moins un immeuble (validation Sprint 3).
4. Un `proprietaire` doit être lié à un `owner_profile`.
5. Un `locataire` sera lié à un enregistrement `tenant` (Sprint 4).
6. Impossible de désactiver le dernier `super_admin` actif.
7. Impossible de modifier son propre rôle (sécurité).

---

## Critères d'acceptation

- [ ] Super admin peut créer les 6 types de comptes
- [ ] Liste utilisateurs paginée avec filtres fonctionne
- [ ] Désactivation empêche la connexion
- [ ] Permissions admin familial persistées et relues correctement
- [ ] Profils propriétaires CRUD fonctionnel
- [ ] UI responsive (mobile + desktop)
- [ ] Tests backend CRUD utilisateurs passent
- [ ] Aucun utilisateur non super_admin n'accède à `/dashboard/utilisateurs`

---

## Notes Sprint 3

Les assignations `building_ids` pour gestionnaires seront validées quand le module immeubles existera.
