# Sprint 10 — Validation & traçabilité (Audit)

**Durée estimée :** 1 semaine  
**Prérequis :** Sprint 9  
**Dépendances pour le sprint suivant :** Sprint 11

---

## Objectif

Implémenter le workflow de validation super admin pour les opérations sensibles, et l'historique complet de toutes les modifications (audit trail) avec ancienne/nouvelle valeur, date, et auteur.

---

## User stories

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S10-01 | Super Admin | Valider/annuler une suppression de paiement | Contrôler les opérations critiques |
| S10-02 | Super Admin | Approuver une modification de montant | Éviter les erreurs |
| S10-03 | Super Admin | Consulter l'historique des modifications | Résoudre les contestations |
| S10-04 | Admin Familial | Demander une action sensible | Soumettre à validation |
| S10-05 | Super Admin | Voir les demandes en attente | Traiter le backlog |

---

## Actions nécessitant validation (cahier des charges)

| Action | Code | Endpoint concerné |
|--------|------|-------------------|
| Suppression paiement | `payment.delete` | DELETE `/payments/{id}` |
| Modification montant paiement | `payment.update_amount` | PATCH `/payments/{id}` |
| Suppression locataire | `tenant.delete` | DELETE `/tenants/{id}` |
| Changement propriétaire | `building.change_owner` | PATCH `/buildings/{id}` (owner) |
| Modification contrat | `lease.update` | PATCH `/leases/{id}` |
| Dépense importante | `expense.validate` | POST `/expenses/{id}/validate` |
| Annulation reçu | `receipt.cancel` | POST `/receipts/{id}/cancel` |
| Suppression document | `document.delete` | DELETE `/documents/{id}` |

---

## Modèles de données

### Table `approval_requests` (demandes de validation)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| action_code | VARCHAR(100) | NOT NULL |
| entity_type | VARCHAR(50) | NOT NULL |
| entity_id | UUID | NOT NULL |
| requested_by | UUID | FK → users.id |
| requested_at | TIMESTAMPTZ | NOT NULL |
| status | ENUM | `pending`, `approved`, `rejected`, `cancelled` |
| reviewed_by | UUID | FK → users.id, nullable |
| reviewed_at | TIMESTAMPTZ | nullable |
| review_comment | TEXT | nullable |
| payload_before | JSONB | nullable — état avant |
| payload_after | JSONB | nullable — état après / action demandée |
| reason | TEXT | NOT NULL — justification demandeur |
| executed_at | TIMESTAMPTZ | nullable |

### Table `audit_logs` (historique immutable)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| action | VARCHAR(100) | NOT NULL — ex: `payment.update`, `lease.create` |
| entity_type | VARCHAR(50) | NOT NULL |
| entity_id | UUID | NOT NULL |
| old_values | JSONB | nullable |
| new_values | JSONB | nullable |
| ip_address | VARCHAR(45) | nullable |
| user_agent | TEXT | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |

**Index :** `(entity_type, entity_id)`, `(user_id)`, `(created_at DESC)`

> Table append-only : pas de UPDATE/DELETE sur audit_logs.

---

## Architecture audit

### Décorateur / Middleware FastAPI

```python
@audit_action("payment.create")
async def create_payment(...):
    ...
```

### Service `AuditService.log()`

Appelé automatiquement sur :
- CREATE → `new_values` only
- UPDATE → `old_values` + `new_values`
- DELETE → `old_values` only

### Hook SQLAlchemy (optionnel)

Event listeners `after_insert`, `after_update`, `after_delete` pour audit automatique.

---

## Workflow validation

```
1. Admin/Gestionnaire demande action sensible
   → POST /api/v1/approval-requests
   → status = pending

2. Super Admin consulte file d'attente
   → GET /api/v1/approval-requests?status=pending

3. Super Admin approuve ou rejette
   → POST /api/v1/approval-requests/{id}/approve
   → POST /api/v1/approval-requests/{id}/reject

4. Si approuvé → exécuter action + audit log
   → status = approved, executed_at = now

5. Si rejeté → notifier demandeur
   → status = rejected
```

---

## Endpoints API

### Demandes de validation

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/approval-requests` | super_admin | File d'attente |
| POST | `/api/v1/approval-requests` | admin+, gestionnaire | Créer demande |
| GET | `/api/v1/approval-requests/{id}` | super_admin, requester | Détail |
| POST | `/api/v1/approval-requests/{id}/approve` | super_admin | Approuver + exécuter |
| POST | `/api/v1/approval-requests/{id}/reject` | super_admin | Rejeter |
| POST | `/api/v1/approval-requests/{id}/cancel` | requester | Annuler sa demande |
| GET | `/api/v1/approval-requests/mine` | admin+, gestionnaire | Mes demandes |

### Audit

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/audit-logs` | super_admin | Liste historique |
| GET | `/api/v1/audit-logs/{id}` | super_admin | Détail entrée |
| GET | `/api/v1/audit-logs/entity/{type}/{id}` | super_admin, admin_familial | Historique entité |

### POST `/api/v1/approval-requests` — Body

```json
{
  "action_code": "payment.delete",
  "entity_type": "payment",
  "entity_id": "uuid",
  "reason": "Doublon — paiement enregistré deux fois par erreur",
  "payload_after": null
}
```

### Filtres GET `/api/v1/audit-logs`

| Param | Description |
|-------|-------------|
| `user_id` | Par utilisateur |
| `entity_type` | Par type entité |
| `entity_id` | Par entité |
| `action` | Par action |
| `date_from` / `date_to` | Période |

---

## Tâches Backend

- [ ] Modèles `ApprovalRequest`, `AuditLog`
- [ ] Migration Alembic
- [ ] `AuditService` — logging centralisé
- [ ] `ApprovalService` — workflow approve/reject/execute
- [ ] Intégrer audit sur TOUS endpoints CRUD existants
- [ ] Intercepter actions sensibles → créer approval_request au lieu d'exécuter directement (sauf super_admin)
- [ ] Super admin exécute directement + audit
- [ ] Executors par action_code (strategy pattern)
- [ ] Capturer IP + user agent depuis Request
- [ ] Tests : workflow complet, audit immutabilité, RBAC

### Executors à implémenter

| action_code | Executor |
|-------------|----------|
| `payment.delete` | Soft delete payment, recalcul échéances, annule reçu |
| `payment.update_amount` | Update amount, recalcul allocations |
| `tenant.delete` | Soft delete tenant |
| `building.change_owner` | Update owner_profile_id |
| `lease.update` | Apply lease changes |
| `receipt.cancel` | Cancel receipt + payment |
| `document.delete` | Delete file + record |

---

## Tâches Frontend

### Pages

| Route | Rôle | Description |
|-------|------|-------------|
| `/dashboard/validations` | super_admin | File d'attente validations |
| `/dashboard/validations/[id]` | super_admin | Détail + approve/reject |
| `/dashboard/historique` | super_admin | Journal audit complet |
| `/dashboard/historique/entite/[type]/[id]` | super_admin, admin_familial | Historique entité |
| `/dashboard/mes-demandes` | admin+, gestionnaire | Mes demandes en cours |

### Composants

- [ ] `ApprovalQueue` — tableau demandes pending
- [ ] `ApprovalDetail` — diff before/after (JSON viewer formaté)
- [ ] `ApproveRejectButtons` — avec commentaire obligatoire pour reject
- [ ] `AuditLogTable` — historique paginé
- [ ] `AuditLogEntry` — détail : qui, quand, quoi, avant/après
- [ ] `RequestApprovalModal` — formulaire demande avec raison
- [ ] `DiffViewer` — comparaison visuelle old vs new values
- [ ] `EntityAuditTimeline` — timeline intégrée dans fiches (locataire, paiement…)

### Intégration boutons « Demander suppression »

Remplacer boutons delete directs par « Demander suppression » pour non-super-admin :
- Paiements, Locataires, Documents

---

## Exemple entrée audit

```json
{
  "id": "uuid",
  "user": { "id": "uuid", "full_name": "Administrateur Y" },
  "action": "lease.rent_update",
  "entity_type": "lease",
  "entity_id": "uuid",
  "old_values": { "rent_amount": 250000.00 },
  "new_values": { "rent_amount": 275000.00 },
  "created_at": "2026-07-26T14:30:00Z"
}
```

---

## Règles métier

1. Seul `super_admin` approuve/rejette.
2. `super_admin` exécute actions sensibles directement (pas de workflow).
3. Audit logs immuables — jamais modifiés ni supprimés.
4. Admin familial peut consulter audit des entités qu'il gère.
5. Notification au demandeur lors approve/reject (Sprint 13).
6. Dépense importante déjà en workflow Sprint 7 — unifier avec approval_requests.

---

## Critères d'acceptation

- [ ] Action sensible par non-super-admin crée approval_request
- [ ] Super admin approuve → action exécutée + audit log
- [ ] Super admin rejette → action non exécutée, demandeur notifié
- [ ] Audit log enregistré sur create/update/delete de toutes entités
- [ ] Historique consultable par entité (ex: historique loyer)
- [ ] Diff before/after visible dans UI
- [ ] Impossible de modifier/supprimer audit_logs
- [ ] Tests backend passent

---

## Rétrofit sprints précédents

- [ ] Ajouter `@audit_action` sur endpoints Sprint 1-9
- [ ] Remplacer DELETE directs par workflow approval
- [ ] Unifier validation dépenses Sprint 7 avec approval_requests
