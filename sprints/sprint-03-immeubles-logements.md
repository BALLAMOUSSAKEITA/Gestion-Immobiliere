# Sprint 3 — Immeubles & logements

**Durée estimée :** 2 semaines  
**Prérequis :** Sprint 2  
**Dépendances pour le sprint suivant :** Sprint 4

---

## Objectif

Gérer le patrimoine immobilier : immeubles, appartements, magasins et bureaux, avec codes uniques, photos, états, attribution propriétaire/gestionnaire, et vue publique des logements disponibles.

---

## User stories

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S3-01 | Super Admin | Créer un immeuble avec sa fiche complète | Référencer le patrimoine |
| S3-02 | Admin Familial | Ajouter des logements à un immeuble | Constituer le parc locatif |
| S3-03 | Super Admin | Attribuer un immeuble à un propriétaire | Lier le bien au membre famille |
| S3-04 | Super Admin | Assigner un gestionnaire à un immeuble | Déléguer la gestion |
| S3-05 | Propriétaire | Voir mes immeubles et logements | Suivre mon patrimoine (lecture seule) |
| S3-06 | Gestionnaire | Voir les logements de mes immeubles assignés | Gérer au quotidien |
| S3-07 | Visiteur | Voir les logements libres | Trouver un logement |

---

## Modèles de données

### Table `buildings` (immeubles)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| code | VARCHAR(20) | UNIQUE, NOT NULL — ex: `KM001` |
| name | VARCHAR(200) | NOT NULL |
| address | TEXT | NOT NULL |
| commune | VARCHAR(100) | NOT NULL |
| quartier | VARCHAR(100) | nullable |
| photo_url | VARCHAR(500) | nullable |
| floor_count | INTEGER | NOT NULL, DEFAULT 0 |
| apartment_count | INTEGER | NOT NULL, DEFAULT 0 |
| shop_count | INTEGER | NOT NULL, DEFAULT 0 |
| owner_profile_id | UUID | FK → owner_profiles.id, nullable |
| manager_user_id | UUID | FK → users.id, nullable |
| observations | TEXT | nullable |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
| created_by | UUID | FK → users.id |

### Table `units` (logements)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| building_id | UUID | FK → buildings.id |
| code | VARCHAR(30) | UNIQUE, NOT NULL — ex: `KM001-A101` |
| type | ENUM | `apartment`, `shop`, `office` |
| number | VARCHAR(20) | NOT NULL |
| floor | INTEGER | nullable |
| rent_amount | DECIMAL(12,2) | NOT NULL |
| deposit_amount | DECIMAL(12,2) | DEFAULT 0 |
| status | ENUM | `free`, `occupied`, `reserved`, `under_repair` |
| description | TEXT | nullable |
| is_public_listing | BOOLEAN | DEFAULT false — visible visiteurs |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

### Table `unit_photos`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| unit_id | UUID | FK → units.id |
| url | VARCHAR(500) | NOT NULL |
| is_primary | BOOLEAN | DEFAULT false |
| sort_order | INTEGER | DEFAULT 0 |
| uploaded_at | TIMESTAMPTZ | NOT NULL |

### Table `unit_tenant_history` (historique locataires — alimenté Sprint 4)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| unit_id | UUID | FK → units.id |
| tenant_id | UUID | FK → tenants.id (Sprint 4) |
| entry_date | DATE | NOT NULL |
| exit_date | DATE | nullable |
| rent_amount | DECIMAL(12,2) | NOT NULL |
| notes | TEXT | nullable |

### Enum `UnitType`

| Valeur | Label FR |
|--------|----------|
| `apartment` | Appartement |
| `shop` | Magasin |
| `office` | Bureau |

### Enum `UnitStatus`

| Valeur | Label FR | Couleur UI |
|--------|----------|------------|
| `free` | Libre | Vert |
| `occupied` | Occupé | Bleu |
| `reserved` | Réservé | Orange |
| `under_repair` | En réparation | Rouge |

---

## Génération automatique des codes

| Entité | Règle | Exemple |
|--------|-------|---------|
| Immeuble | `{PREFIX}{NNN}` — PREFIX configurable (défaut `KM`) | `KM001`, `KM002` |
| Appartement | `{BUILDING_CODE}-A{FLOOR}{NN}` | `KM001-A101` (étage 1, n°01) |
| Magasin | `{BUILDING_CODE}-M{NN}` | `KM001-M01` |
| Bureau | `{BUILDING_CODE}-B{NN}` | `KM001-B01` |

Service backend `CodeGeneratorService` :
- Vérifier unicité avant création
- Incrémenter automatiquement le numéro séquentiel

---

## Endpoints API

### Immeubles

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/buildings` | super_admin, admin_familial, proprietaire*, gestionnaire* | Liste immeubles |
| POST | `/api/v1/buildings` | super_admin, admin_familial | Créer immeuble |
| GET | `/api/v1/buildings/{id}` | * filtré | Détail immeuble + stats |
| PATCH | `/api/v1/buildings/{id}` | super_admin, admin_familial | Modifier |
| DELETE | `/api/v1/buildings/{id}` | super_admin | Soft delete |
| GET | `/api/v1/buildings/{id}/units` | * filtré | Logements de l'immeuble |
| POST | `/api/v1/buildings/{id}/units` | super_admin, admin_familial | Créer logement |
| POST | `/api/v1/buildings/{id}/photo` | super_admin, admin_familial | Upload photo immeuble |

### Logements

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/units` | * filtré | Liste tous logements |
| GET | `/api/v1/units/{id}` | * filtré | Détail logement |
| PATCH | `/api/v1/units/{id}` | super_admin, admin_familial | Modifier (loyer, état…) |
| DELETE | `/api/v1/units/{id}` | super_admin | Soft delete |
| POST | `/api/v1/units/{id}/photos` | super_admin, admin_familial | Upload photos |
| DELETE | `/api/v1/units/{id}/photos/{photo_id}` | super_admin, admin_familial | Supprimer photo |
| GET | `/api/v1/units/{id}/history` | super_admin, admin_familial, proprietaire* | Historique locataires |

### Public (Visiteur)

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/public/units` | Non | Logements libres publics |
| GET | `/api/v1/public/units/{id}` | Non | Détail public (sans données privées) |

**Données visibles publiquement :** photos, loyer, type, commune/quartier (pas adresse exacte), statut `free` uniquement.

### Filtres GET `/api/v1/units`

| Param | Description |
|-------|-------------|
| `building_id` | Par immeuble |
| `type` | apartment / shop / office |
| `status` | free / occupied / etc. |
| `owner_profile_id` | Par propriétaire |
| `search` | Code ou numéro |

### Détail immeuble — stats calculées

```json
{
  "id": "uuid",
  "code": "KM001",
  "name": "Résidence Les Palmiers",
  "total_units": 12,
  "occupied_units": 9,
  "free_units": 2,
  "under_repair_units": 1,
  "occupancy_rate": 75.0,
  "monthly_expected_rent": 2750000.00
}
```

---

## Tâches Backend

- [ ] Modèles `Building`, `Unit`, `UnitPhoto`, `UnitTenantHistory`
- [ ] Enums SQLAlchemy + Pydantic
- [ ] Migration Alembic + FK `user_building_assignments.building_id`
- [ ] `CodeGeneratorService`
- [ ] Upload photos (local dev → dossier `uploads/`, prod → S3/MinIO)
- [ ] Filtrage RBAC : propriétaire voit ses biens, gestionnaire ses immeubles assignés
- [ ] Endpoint public sans auth
- [ ] Recalcul compteurs immeuble (`apartment_count`, etc.) à la création/suppression unit
- [ ] Tests CRUD + génération codes + filtres RBAC

---

## Tâches Frontend

### Pages dashboard

| Route | Rôle | Description |
|-------|------|-------------|
| `/dashboard/immeubles` | admin+ | Liste immeubles (cartes ou tableau) |
| `/dashboard/immeubles/nouveau` | admin+ | Formulaire création immeuble |
| `/dashboard/immeubles/[id]` | admin+ | Fiche immeuble + liste logements |
| `/dashboard/immeubles/[id]/modifier` | admin+ | Édition immeuble |
| `/dashboard/logements` | admin+, gestionnaire* | Vue globale logements |
| `/dashboard/logements/[id]` | admin+, gestionnaire*, proprietaire* | Fiche logement |
| `/dashboard/logements/nouveau` | admin+ | Créer logement (sélection immeuble) |

### Pages publiques

| Route | Auth | Description |
|-------|------|-------------|
| `/annonces` | Non | Grille logements disponibles |
| `/annonces/[id]` | Non | Détail annonce publique |

### Composants

- [ ] `BuildingCard` — carte immeuble avec photo, stats
- [ ] `BuildingForm` — tous champs fiche immeuble
- [ ] `UnitTable` — tableau logements avec badges statut
- [ ] `UnitForm` — création/édition logement
- [ ] `UnitStatusBadge` — badge coloré par état
- [ ] `PhotoUploader` — drag & drop multi-photos
- [ ] `OwnerSelect` — dropdown propriétaires famille
- [ ] `ManagerSelect` — dropdown gestionnaires
- [ ] `PublicUnitCard` — carte annonce visiteur
- [ ] `OccupancyChart` — mini graphique taux occupation (placeholder dashboard)

### UX

- Carte interactive optionnelle (quartier seulement pour visiteurs)
- Preview photos avant upload
- Confirmation avant changement statut `occupied` → `free`
- Format montants : `250 000 FCFA`

---

## Règles métier

1. Code immeuble et logement uniques, non modifiables après création.
2. Un logement `occupied` ne peut pas passer à `free` sans clôturer le bail (Sprint 4).
3. Seuls les logements `free` + `is_public_listing=true` apparaissent en public.
4. Propriétaire : lecture seule, filtré par `owner_profile_id`.
5. Gestionnaire : lecture seulement sur immeubles assignés via `user_building_assignments`.
6. Suppression immeuble interdite s'il contient des logements occupés.

---

## Critères d'acceptation

- [ ] CRUD immeubles complet avec upload photo
- [ ] CRUD logements avec génération code automatique
- [ ] Filtres et recherche fonctionnels
- [ ] RBAC : propriétaire ne voit que ses biens
- [ ] RBAC : gestionnaire ne voit que ses immeubles assignés
- [ ] Page publique `/annonces` affiche logements libres sans données privées
- [ ] Stats immeuble (occupation, loyers attendus) calculées correctement
- [ ] Tests backend passent

---

## Données de test (seed)

Créer en dev :
- 2 immeubles (`KM001`, `KM002`)
- 6 appartements + 2 magasins répartis
- 1 propriétaire assigné à `KM001`
- 1 gestionnaire assigné à `KM001`
