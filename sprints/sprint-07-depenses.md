# Sprint 7 — Dépenses

**Durée estimée :** 1 semaine  
**Prérequis :** Sprint 6 (Sprint 3 minimum pour immeubles)  
**Dépendances pour le sprint suivant :** Sprint 8

---

## Objectif

Enregistrer et classifier toutes les dépenses liées au patrimoine (réparations, taxes, gardiennage, etc.), avec justificatifs, filtres multi-critères, et impact sur le calcul du bénéfice net.

---

## User stories

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S7-01 | Admin Familial | Enregistrer une dépense | Suivre les charges |
| S7-02 | Gestionnaire | Ajouter une dépense pour mon immeuble | Documenter les coûts |
| S7-03 | Admin Familial | Classer une dépense par catégorie | Analyser les postes de dépenses |
| S7-04 | Admin Familial | Joindre une facture | Justifier la dépense |
| S7-05 | Propriétaire | Voir les dépenses de mes biens | Connaître mes charges |
| S7-06 | Super Admin | Valider une dépense importante | Contrôler les grosses dépenses |

---

## Modèles de données

### Table `expense_categories`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| code | VARCHAR(50) | UNIQUE |
| label | VARCHAR(100) | NOT NULL |
| is_active | BOOLEAN | DEFAULT true |

**Seed catégories (cahier des charges) :**

| code | label |
|------|-------|
| `repair` | Réparation |
| `painting` | Peinture |
| `plumbing` | Plomberie |
| `electricity` | Électricité |
| `security` | Gardiennage |
| `cleaning` | Nettoyage |
| `taxes` | Taxes |
| `supplies` | Fournitures |
| `construction` | Travaux / Gros œuvre |
| `other` | Autre |

### Table `expenses`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| category_id | UUID | FK → expense_categories.id |
| building_id | UUID | FK → buildings.id, nullable |
| unit_id | UUID | FK → units.id, nullable |
| owner_profile_id | UUID | FK → owner_profiles.id, nullable |
| supplier_name | VARCHAR(200) | nullable |
| description | TEXT | NOT NULL |
| amount | DECIMAL(12,2) | NOT NULL |
| payment_method | ENUM | cash, orange_money, wave, bank_transfer |
| expense_date | DATE | NOT NULL |
| receipt_url | VARCHAR(500) | nullable |
| status | ENUM | `recorded`, `pending_validation`, `validated`, `rejected` |
| requires_validation | BOOLEAN | DEFAULT false |
| validated_by | UUID | FK → users.id, nullable |
| validated_at | TIMESTAMPTZ | nullable |
| repair_id | UUID | FK → repairs.id, nullable (Sprint 8) |
| recorded_by | UUID | FK → users.id |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

**Règle validation :** Si `amount >= SEUIL_VALIDATION` (configurable, défaut 500 000 FCFA) → `requires_validation = true`, `status = pending_validation`.

---

## Endpoints API

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/expenses` | admin+, gestionnaire*, proprietaire* | Liste dépenses |
| POST | `/api/v1/expenses` | admin+, gestionnaire | Créer dépense |
| GET | `/api/v1/expenses/{id}` | * filtré | Détail |
| PATCH | `/api/v1/expenses/{id}` | admin+, gestionnaire | Modifier |
| DELETE | `/api/v1/expenses/{id}` | super_admin | Supprimer (→ Sprint 10) |
| POST | `/api/v1/expenses/{id}/receipt` | admin+, gestionnaire | Upload justificatif |
| POST | `/api/v1/expenses/{id}/validate` | super_admin | Valider dépense importante |
| POST | `/api/v1/expenses/{id}/reject` | super_admin | Rejeter dépense |
| GET | `/api/v1/expense-categories` | auth | Liste catégories |
| GET | `/api/v1/expenses/summary` | admin+, proprietaire* | Agrégations |

### Filtres GET `/api/v1/expenses`

| Param | Description |
|-------|-------------|
| `building_id` | Par immeuble |
| `unit_id` | Par logement |
| `owner_profile_id` | Par propriétaire |
| `category_id` | Par catégorie |
| `date_from` / `date_to` | Période |
| `min_amount` / `max_amount` | Fourchette montant |
| `payment_method` | Mode paiement |
| `supplier` | Recherche fournisseur |
| `status` | Statut validation |

### POST `/api/v1/expenses` — Body

```json
{
  "category_id": "uuid",
  "building_id": "uuid",
  "unit_id": null,
  "owner_profile_id": "uuid",
  "supplier_name": "Plomberie Express",
  "description": "Réparation fuite canalisation étage 2",
  "amount": 75000.00,
  "payment_method": "cash",
  "expense_date": "2026-07-20"
}
```

### GET `/api/v1/expenses/summary` — Query

| Param | Description |
|-------|-------------|
| `year` | Année |
| `month` | Mois (optionnel) |
| `building_id` | Filtre immeuble |
| `group_by` | `category`, `building`, `month` |

**Réponse :**
```json
{
  "total_amount": 1250000.00,
  "count": 18,
  "by_category": [
    { "category": "Réparation", "amount": 450000.00, "count": 6 },
    { "category": "Gardiennage", "amount": 300000.00, "count": 3 }
  ]
}
```

---

## Tâches Backend

- [ ] Modèles `ExpenseCategory`, `Expense`
- [ ] Migration + seed catégories
- [ ] CRUD dépenses avec validation montant seuil
- [ ] Upload justificatif (photo/PDF)
- [ ] Workflow validation super admin pour dépenses importantes
- [ ] Endpoint summary avec agrégations SQL
- [ ] RBAC : gestionnaire limité à ses immeubles, propriétaire lecture seule filtrée
- [ ] Tests CRUD + validation seuil + summary

---

## Tâches Frontend

### Pages

| Route | Rôle | Description |
|-------|------|-------------|
| `/dashboard/depenses` | admin+, gestionnaire | Liste dépenses |
| `/dashboard/depenses/nouvelle` | admin+, gestionnaire | Formulaire création |
| `/dashboard/depenses/[id]` | admin+, gestionnaire, proprietaire* | Détail dépense |
| `/dashboard/depenses/validation` | super_admin | Dépenses en attente validation |

### Composants

- [ ] `ExpenseForm` — tous champs + sélection immeuble/logement/propriétaire
- [ ] `ExpenseTable` — tableau avec filtres multi-critères
- [ ] `ExpenseCategorySelect`
- [ ] `ReceiptUploader` — photo ou PDF facture
- [ ] `ExpenseSummaryCards` — total mois, par catégorie
- [ ] `ExpenseByCategoryChart` — camembert dépenses par catégorie
- [ ] `ValidationQueue` — liste dépenses pending_validation
- [ ] `ExpenseStatusBadge`

### Filtres UI (panneau latéral)

- Immeuble, Logement, Propriétaire
- Catégorie, Date (range picker)
- Fournisseur (recherche texte)
- Montant min/max
- Mode de paiement

---

## Règles métier

1. Au moins un lien : `building_id` OU `unit_id` OU `owner_profile_id` requis.
2. Dépense >= seuil → `pending_validation`, invisible dans rapports jusqu'à validation.
3. Super admin seul valide/rejette dépenses importantes.
4. Propriétaire : lecture seule, filtré par ses biens.
5. Gestionnaire : CRUD sur immeubles assignés uniquement.
6. Dépense liée à réparation (Sprint 8) : `repair_id` renseigné automatiquement.

---

## Critères d'acceptation

- [ ] CRUD dépenses avec toutes catégories du cahier des charges
- [ ] Filtres multi-critères fonctionnels
- [ ] Upload justificatif photo/PDF
- [ ] Dépense >= 500 000 FCFA → workflow validation
- [ ] Super admin peut valider/rejeter
- [ ] Summary par catégorie/immeuble/mois correct
- [ ] Propriétaire voit dépenses de ses biens (lecture seule)
- [ ] Tests backend passent

---

## Lien avec dashboard (Sprint 11)

Le KPI « Dépenses du mois » et « Bénéfice net » utiliseront :
```
bénéfice_net = loyers_encaissés - dépenses_validées
```
