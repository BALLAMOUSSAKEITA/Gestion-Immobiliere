# Sprint 8 — Réparations

**Durée estimée :** 1 à 2 semaines  
**Prérequis :** Sprint 7  
**Dépendances pour le sprint suivant :** Sprint 9

---

## Objectif

Permettre la déclaration, le suivi et la clôture des demandes de réparation par locataires et gestionnaires, avec niveaux d'urgence, statuts, coûts, et lien avec les dépenses.

---

## User stories

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S8-01 | Locataire | Signaler une panne | Faire intervenir un technicien |
| S8-02 | Gestionnaire | Déclarer une réparation | Lancer le processus |
| S8-03 | Gestionnaire | Suivre le statut des réparations | Piloter les interventions |
| S8-04 | Admin Familial | Voir les réparations en cours | Superviser la maintenance |
| S8-05 | Gestionnaire | Enregistrer le coût final | Clôturer avec la facture |
| S8-06 | Propriétaire | Voir les réparations sur mes biens | Suivre l'entretien |

---

## Modèles de données

### Table `repairs`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| unit_id | UUID | FK → units.id |
| building_id | UUID | FK → buildings.id |
| reported_by | UUID | FK → users.id |
| assigned_to | UUID | FK → users.id, nullable — gestionnaire |
| title | VARCHAR(200) | NOT NULL |
| description | TEXT | NOT NULL |
| urgency | ENUM | `low`, `medium`, `high` |
| status | ENUM | voir ci-dessous |
| estimated_cost | DECIMAL(12,2) | nullable |
| final_cost | DECIMAL(12,2) | nullable |
| expense_id | UUID | FK → expenses.id, nullable |
| reported_at | TIMESTAMPTZ | NOT NULL |
| started_at | TIMESTAMPTZ | nullable |
| completed_at | TIMESTAMPTZ | nullable |
| cancelled_at | TIMESTAMPTZ | nullable |
| cancellation_reason | TEXT | nullable |
| notes | TEXT | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

### Enum `RepairStatus`

| Valeur | Label FR | Icône |
|--------|----------|-------|
| `new` | Nouvelle demande | 📝 |
| `under_review` | En cours d'analyse | 🔍 |
| `technician_assigned` | Technicien affecté | 🔧 |
| `in_progress` | Réparation en cours | 🛠️ |
| `completed` | Terminée | ✅ |
| `cancelled` | Annulée | ❌ |

### Enum `UrgencyLevel`

| Valeur | Label FR | Couleur |
|--------|----------|---------|
| `low` | Faible | Vert |
| `medium` | Moyen | Orange |
| `high` | Élevé | Rouge |

### Table `repair_attachments`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| repair_id | UUID | FK → repairs.id |
| file_url | VARCHAR(500) | NOT NULL |
| file_type | ENUM | `photo`, `video`, `document` |
| uploaded_by | UUID | FK → users.id |
| uploaded_at | TIMESTAMPTZ | NOT NULL |

### Table `repair_status_history`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| repair_id | UUID | FK → repairs.id |
| old_status | VARCHAR(50) | nullable |
| new_status | VARCHAR(50) | NOT NULL |
| changed_by | UUID | FK → users.id |
| changed_at | TIMESTAMPTZ | NOT NULL |
| comment | TEXT | nullable |

---

## Machine à états (transitions autorisées)

```
new → under_review → technician_assigned → in_progress → completed
  ↘ cancelled (depuis tout statut sauf completed)
```

Validation backend : refuser transitions invalides (ex: `new` → `completed` direct).

---

## Endpoints API

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/repairs` | admin+, gestionnaire*, proprietaire*, locataire* | Liste réparations |
| POST | `/api/v1/repairs` | admin+, gestionnaire, locataire* | Déclarer réparation |
| GET | `/api/v1/repairs/{id}` | * filtré | Détail |
| PATCH | `/api/v1/repairs/{id}` | admin+, gestionnaire | Modifier infos |
| PATCH | `/api/v1/repairs/{id}/status` | admin+, gestionnaire | Changer statut |
| POST | `/api/v1/repairs/{id}/attachments` | admin+, gestionnaire, locataire* | Upload photo/vidéo |
| POST | `/api/v1/repairs/{id}/complete` | admin+, gestionnaire | Clôturer avec coût final |
| POST | `/api/v1/repairs/{id}/cancel` | admin+, gestionnaire | Annuler |
| GET | `/api/v1/repairs/{id}/history` | admin+, gestionnaire | Historique statuts |

### POST `/api/v1/repairs` — Body

```json
{
  "unit_id": "uuid",
  "title": "Fuite d'eau salle de bain",
  "description": "Eau qui coule du plafond depuis ce matin",
  "urgency": "high"
}
```

**Locataire :** `unit_id` auto-rempli depuis son bail actif (pas de choix).

### POST `/api/v1/repairs/{id}/complete` — Body

```json
{
  "final_cost": 85000.00,
  "create_expense": true,
  "expense_category_id": "uuid",
  "notes": "Remplacement joint + main d'œuvre"
}
```

**Action :** Si `create_expense=true`, créer dépense liée (`repair_id`, `expense_id`).

### Filtres GET `/api/v1/repairs`

| Param | Description |
|-------|-------------|
| `building_id` | Par immeuble |
| `unit_id` | Par logement |
| `status` | Par statut |
| `urgency` | Par urgence |
| `assigned_to` | Par gestionnaire |
| `date_from` / `date_to` | Période déclaration |

---

## Tâches Backend

- [ ] Modèles `Repair`, `RepairAttachment`, `RepairStatusHistory`
- [ ] Migration Alembic
- [ ] State machine validation transitions
- [ ] Auto-assignation gestionnaire de l'immeuble à la création
- [ ] Upload photos/vidéos
- [ ] Clôture avec création dépense optionnelle
- [ ] Passage unit → `under_repair` si réparation majeure (option configurable)
- [ ] Notification nouvelle demande (placeholder Sprint 13)
- [ ] RBAC : locataire ne voit que ses demandes
- [ ] Tests : transitions statut, clôture, création dépense

---

## Tâches Frontend

### Pages

| Route | Rôle | Description |
|-------|------|-------------|
| `/dashboard/reparations` | admin+, gestionnaire | Liste + kanban |
| `/dashboard/reparations/nouvelle` | admin+, gestionnaire | Nouvelle déclaration |
| `/dashboard/reparations/[id]` | admin+, gestionnaire, proprietaire* | Détail + actions |
| `/espace-locataire/reparations` | locataire | Mes signalements |
| `/espace-locataire/reparations/nouvelle` | locataire | Signaler une panne |

### Composants

- [ ] `RepairKanban` — colonnes par statut (drag & drop optionnel)
- [ ] `RepairTable` — vue liste alternative
- [ ] `RepairForm` — titre, description, urgence, logement
- [ ] `RepairDetail` — fiche complète
- [ ] `StatusTransitionButtons` — boutons action selon statut courant
- [ ] `UrgencyBadge` — badge coloré
- [ ] `RepairStatusBadge`
- [ ] `MediaUploader` — photos + vidéos
- [ ] `CompleteRepairModal` — coût final + création dépense
- [ ] `RepairTimeline` — historique statuts
- [ ] `RepairSummaryCards` — nb en cours, urgentes, terminées ce mois

### Vue Kanban (colonnes)

| Colonne | Statuts |
|---------|---------|
| Nouvelles | `new` |
| Analyse | `under_review` |
| En cours | `technician_assigned`, `in_progress` |
| Terminées | `completed` |
| Annulées | `cancelled` |

---

## Règles métier

1. Locataire ne peut déclarer que sur son logement actif.
2. Gestionnaire voit réparations de ses immeubles assignés.
3. Urgence `high` → notification immédiate gestionnaire + admin.
4. Clôture enregistre `completed_at` et optionnellement une dépense.
5. Propriétaire : lecture seule sur ses biens.
6. Statut `cancelled` requiert une raison.

---

## Critères d'acceptation

- [ ] Locataire peut signaler une panne avec photo
- [ ] Gestionnaire peut faire évoluer le statut (workflow complet)
- [ ] Kanban/liste affiche réparations filtrées par rôle
- [ ] Clôture avec coût final crée dépense liée
- [ ] Historique statuts tracé
- [ ] KPI « Réparations en cours » alimenté (dashboard Sprint 11)
- [ ] Tests backend passent

---

## Widget dashboard (Sprint 11)

```
🔧 Réparations en cours : COUNT(status IN (new, under_review, technician_assigned, in_progress))
```
