# Sprint 4 — Gestion des locataires

**Durée estimée :** 1 à 2 semaines  
**Prérequis :** Sprint 3  
**Dépendances pour le sprint suivant :** Sprint 5

---

## Objectif

Gérer le cycle de vie complet des locataires : fiche détaillée, pièce d'identité, attribution logement, contrat de bail, historique, et liaison compte utilisateur locataire.

---

## User stories

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S4-01 | Admin Familial | Enregistrer un nouveau locataire | Constituer le dossier locataire |
| S4-02 | Gestionnaire | Ajouter un locataire | Enregistrer un nouveau bail |
| S4-03 | Admin Familial | Attribuer un logement à un locataire | Démarrer un bail |
| S4-04 | Admin Familial | Terminer un bail (sortie locataire) | Libérer le logement |
| S4-05 | Super Admin | Voir l'historique des anciens locataires | Avoir la traçabilité |
| S4-06 | Admin Familial | Créer un compte locataire lié | Donner accès à l'espace locataire |

---

## Modèles de données

### Table `tenants` (locataires)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id, UNIQUE, nullable |
| first_name | VARCHAR(100) | NOT NULL |
| last_name | VARCHAR(100) | NOT NULL |
| photo_url | VARCHAR(500) | nullable |
| phone_primary | VARCHAR(20) | NOT NULL |
| phone_secondary | VARCHAR(20) | nullable |
| profession | VARCHAR(200) | nullable |
| previous_address | TEXT | nullable |
| id_document_type | ENUM | `cni`, `passport`, `attestation`, `other` |
| id_document_number | VARCHAR(50) | NOT NULL |
| id_document_url | VARCHAR(500) | nullable |
| emergency_contact_name | VARCHAR(200) | nullable |
| emergency_contact_phone | VARCHAR(20) | nullable |
| payment_method | ENUM | `cash`, `orange_money`, `wave`, `bank_transfer` |
| observations | TEXT | nullable |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| created_by | UUID | FK → users.id |

### Table `leases` (baux / contrats)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| tenant_id | UUID | FK → tenants.id |
| unit_id | UUID | FK → units.id |
| start_date | DATE | NOT NULL |
| end_date | DATE | nullable |
| rent_amount | DECIMAL(12,2) | NOT NULL |
| deposit_amount | DECIMAL(12,2) | DEFAULT 0 |
| deposit_paid | BOOLEAN | DEFAULT false |
| status | ENUM | `active`, `expired`, `terminated`, `pending` |
| contract_document_url | VARCHAR(500) | nullable |
| termination_date | DATE | nullable |
| termination_reason | TEXT | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| created_by | UUID | FK → users.id |

**Contrainte :** Un seul bail `active` par logement à la fois.

### Table `lease_rent_history` (historique modifications loyer)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| lease_id | UUID | FK → leases.id |
| old_rent_amount | DECIMAL(12,2) | NOT NULL |
| new_rent_amount | DECIMAL(12,2) | NOT NULL |
| effective_date | DATE | NOT NULL |
| changed_by | UUID | FK → users.id |
| changed_at | TIMESTAMPTZ | NOT NULL |
| reason | TEXT | nullable |

### Enum `LeaseStatus`

| Valeur | Label FR |
|--------|----------|
| `pending` | En attente |
| `active` | Actif |
| `expired` | Expiré |
| `terminated` | Résilié |

### Enum `PaymentMethod`

| Valeur | Label FR |
|--------|----------|
| `cash` | Espèces |
| `orange_money` | Orange Money |
| `wave` | Wave |
| `bank_transfer` | Virement bancaire |

---

## Endpoints API

### Locataires

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/tenants` | admin+, gestionnaire* | Liste locataires |
| POST | `/api/v1/tenants` | admin+, gestionnaire | Créer locataire |
| GET | `/api/v1/tenants/{id}` | admin+, gestionnaire*, proprietaire* | Fiche complète |
| PATCH | `/api/v1/tenants/{id}` | admin+, gestionnaire | Modifier |
| DELETE | `/api/v1/tenants/{id}` | super_admin | Suppression (→ validation Sprint 10) |
| POST | `/api/v1/tenants/{id}/photo` | admin+, gestionnaire | Upload photo |
| POST | `/api/v1/tenants/{id}/id-document` | admin+, gestionnaire | Upload pièce identité |
| POST | `/api/v1/tenants/{id}/create-account` | super_admin, admin_familial | Créer compte user locataire |

### Baux

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/leases` | admin+, gestionnaire*, proprietaire* | Liste baux |
| POST | `/api/v1/leases` | admin+, gestionnaire | Créer bail (attribuer logement) |
| GET | `/api/v1/leases/{id}` | * filtré | Détail bail |
| PATCH | `/api/v1/leases/{id}` | admin+, gestionnaire | Modifier (dates, loyer) |
| POST | `/api/v1/leases/{id}/terminate` | admin+, gestionnaire | Terminer bail |
| POST | `/api/v1/leases/{id}/contract` | admin+, gestionnaire | Upload contrat PDF |
| PATCH | `/api/v1/leases/{id}/rent` | super_admin, admin_famial | Modifier loyer (→ audit Sprint 10) |
| GET | `/api/v1/leases/expiring` | admin+ | Baux expirant sous N jours |

### POST `/api/v1/leases` — Body

```json
{
  "tenant_id": "uuid",
  "unit_id": "uuid",
  "start_date": "2026-08-01",
  "end_date": "2027-07-31",
  "rent_amount": 250000.00,
  "deposit_amount": 500000.00,
  "deposit_paid": true
}
```

**Actions automatiques à la création :**
1. Vérifier que `unit.status == free`
2. Passer `unit.status` → `occupied`
3. Créer entrée `unit_tenant_history`
4. Mettre à jour lease status → `active`

### POST `/api/v1/leases/{id}/terminate` — Body

```json
{
  "termination_date": "2026-12-31",
  "termination_reason": "Fin de bail — départ volontaire"
}
```

**Actions automatiques :**
1. Lease status → `terminated`
2. `unit.status` → `free`
3. `unit_tenant_history.exit_date` = termination_date

### Filtres GET `/api/v1/tenants`

| Param | Description |
|-------|-------------|
| `search` | Nom, téléphone, numéro pièce |
| `building_id` | Locataires d'un immeuble |
| `unit_id` | Locataire d'un logement |
| `is_active` | Actifs / anciens |
| `has_unpaid` | Avec impayés (Sprint 6) |

### Réponse fiche locataire

```json
{
  "id": "uuid",
  "first_name": "Aminata",
  "last_name": "Traoré",
  "phone_primary": "+2250700000002",
  "current_lease": {
    "id": "uuid",
    "unit_code": "KM001-A101",
    "building_name": "Résidence Les Palmiers",
    "rent_amount": 250000.00,
    "start_date": "2026-08-01",
    "status": "active"
  },
  "payment_summary": {
    "total_paid": 0,
    "total_unpaid": 0
  }
}
```

---

## Tâches Backend

- [ ] Modèles `Tenant`, `Lease`, `LeaseRentHistory`
- [ ] Migration Alembic
- [ ] Service `LeaseService.assign_tenant()` — logique métier attribution
- [ ] Service `LeaseService.terminate()` — clôture bail
- [ ] Validation : un logement = un bail actif max
- [ ] Upload photo + pièce identité
- [ ] Endpoint baux expirants (query param `days=30`)
- [ ] Liaison tenant ↔ user (création compte locataire)
- [ ] Alimenter `unit_tenant_history` automatiquement
- [ ] Tests : création bail, termination, contraintes unicité

---

## Tâches Frontend

### Pages

| Route | Rôle | Description |
|-------|------|-------------|
| `/dashboard/locataires` | admin+, gestionnaire | Liste locataires |
| `/dashboard/locataires/nouveau` | admin+, gestionnaire | Formulaire création |
| `/dashboard/locataires/[id]` | admin+, gestionnaire, proprietaire* | Fiche locataire complète |
| `/dashboard/locataires/[id]/modifier` | admin+, gestionnaire | Édition |
| `/dashboard/baux` | admin+, gestionnaire | Liste baux actifs/expirés |
| `/dashboard/baux/nouveau` | admin+, gestionnaire | Nouveau bail |
| `/dashboard/baux/[id]` | admin+ | Détail bail + actions |

### Composants

- [ ] `TenantForm` — formulaire complet (tous champs cahier des charges)
- [ ] `TenantCard` — résumé locataire
- [ ] `LeaseForm` — sélection locataire + logement libre + dates
- [ ] `LeaseStatusBadge`
- [ ] `UnitSelectFree` — dropdown logements libres uniquement
- [ ] `TenantSelect` — autocomplete locataires
- [ ] `IdDocumentUploader` — upload scan CNI/passeport
- [ ] `LeaseTimeline` — historique bail
- [ ] `ExpiringLeasesAlert` — widget baux expirants (pour dashboard Sprint 11)
- [ ] Modale confirmation termination bail

### Onglets fiche locataire

1. **Informations** — identité, contacts, profession
2. **Bail actuel** — logement, dates, loyer, contrat
3. **Paiements** — placeholder Sprint 5
4. **Documents** — placeholder Sprint 9
5. **Historique** — anciens baux

---

## Règles métier

1. Impossible d'assigner un logement non `free`.
2. Un locataire peut avoir plusieurs baux dans l'historique, un seul actif.
3. Modification loyer en cours de bail → enregistrer dans `lease_rent_history` + audit (Sprint 10).
4. Suppression locataire → requiert validation super admin (Sprint 10).
5. Gestionnaire ne voit que locataires des immeubles assignés.
6. Propriétaire voit locataires de ses biens (lecture seule, sans pièce identité complète — masquer numéro partiellement : `CI•••••1234`).

---

## Critères d'acceptation

- [ ] CRUD locataire avec tous les champs du cahier des charges
- [ ] Création bail assigne logement et change statut unit
- [ ] Termination libère le logement
- [ ] Historique locataires par logement visible
- [ ] Upload photo et pièce identité fonctionnels
- [ ] Création compte utilisateur locataire lié
- [ ] Liste baux expirants sous 30 jours
- [ ] RBAC gestionnaire/propriétaire respecté
- [ ] Tests backend passent

---

## Seed dev

- 4 locataires
- 3 baux actifs sur KM001
- 1 bail terminé (historique)
