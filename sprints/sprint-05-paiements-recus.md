# Sprint 5 — Paiements & reçus

**Durée estimée :** 2 semaines  
**Prérequis :** Sprint 4  
**Dépendances pour le sprint suivant :** Sprint 6

---

## Objectif

Enregistrer tous les types de paiements (espèces, Orange Money, Wave, virement), gérer les paiements partiels et multi-mois, générer des reçus PDF numérotés, et permettre l'envoi par email/WhatsApp.

---

## User stories

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S5-01 | Gestionnaire | Enregistrer un paiement de loyer | Mettre à jour le solde locataire |
| S5-02 | Admin Familial | Enregistrer plusieurs mois en une fois | Simplifier l'encaissement |
| S5-03 | Gestionnaire | Joindre une preuve de paiement | Justifier la transaction |
| S5-04 | Système | Générer un reçu PDF automatiquement | Remettre un justificatif officiel |
| S5-05 | Gestionnaire | Envoyer le reçu par email | Informer le locataire |
| S5-06 | Locataire | Télécharger mes reçus | Avoir mes justificatifs |
| S5-07 | Super Admin | Voir qui a enregistré chaque paiement | Assurer la traçabilité |

---

## Modèles de données

### Table `rent_periods` (échéances mensuelles)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| lease_id | UUID | FK → leases.id |
| period_year | INTEGER | NOT NULL |
| period_month | INTEGER | NOT NULL — 1-12 |
| expected_amount | DECIMAL(12,2) | NOT NULL |
| paid_amount | DECIMAL(12,2) | DEFAULT 0 |
| status | ENUM | `pending`, `partial`, `paid`, `overdue` |
| due_date | DATE | NOT NULL |
| created_at | TIMESTAMPTZ | NOT NULL |

**Contrainte UNIQUE :** `(lease_id, period_year, period_month)`

> Génération automatique : créer les échéances à la création du bail (ou cron mensuel).

### Table `payments`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| lease_id | UUID | FK → leases.id |
| tenant_id | UUID | FK → tenants.id |
| amount | DECIMAL(12,2) | NOT NULL |
| payment_method | ENUM | cash, orange_money, wave, bank_transfer |
| payment_date | DATE | NOT NULL |
| reference | VARCHAR(100) | nullable — ref Orange Money, Wave, virement |
| proof_url | VARCHAR(500) | nullable |
| notes | TEXT | nullable |
| status | ENUM | `recorded`, `validated`, `cancelled` |
| recorded_by | UUID | FK → users.id |
| validated_by | UUID | FK → users.id, nullable |
| validated_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

### Table `payment_allocations` (affectation paiement → mois)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| payment_id | UUID | FK → payments.id |
| rent_period_id | UUID | FK → rent_periods.id |
| allocated_amount | DECIMAL(12,2) | NOT NULL |

### Table `receipts` (reçus)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| payment_id | UUID | FK → payments.id, UNIQUE |
| receipt_number | VARCHAR(30) | UNIQUE, NOT NULL — ex: `REC-2026-000001` |
| pdf_url | VARCHAR(500) | NOT NULL |
| issued_at | TIMESTAMPTZ | NOT NULL |
| issued_by | UUID | FK → users.id |
| sent_email_at | TIMESTAMPTZ | nullable |
| sent_whatsapp_at | TIMESTAMPTZ | nullable |
| status | ENUM | `issued`, `cancelled` |

---

## Numérotation des reçus

Format : `REC-{ANNÉE}-{SÉQUENCE}`  
Exemple : `REC-2026-000001`, `REC-2026-000042`

Service `ReceiptNumberService` :
- Séquence par année
- Thread-safe (lock DB ou sequence PostgreSQL)

---

## Endpoints API

### Échéances

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/leases/{id}/periods` | admin+, gestionnaire*, locataire* | Échéances du bail |
| POST | `/api/v1/leases/{id}/periods/generate` | admin+ | Générer échéances manquantes |

### Paiements

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/payments` | admin+, gestionnaire*, proprietaire*, locataire* | Liste paiements |
| POST | `/api/v1/payments` | admin+, gestionnaire | Enregistrer paiement |
| GET | `/api/v1/payments/{id}` | * filtré | Détail paiement |
| PATCH | `/api/v1/payments/{id}` | super_admin | Modifier montant (→ Sprint 10) |
| DELETE | `/api/v1/payments/{id}` | super_admin | Annuler (→ Sprint 10) |
| POST | `/api/v1/payments/{id}/proof` | admin+, gestionnaire | Upload preuve |
| POST | `/api/v1/payments/{id}/validate` | super_admin, admin_familial | Valider paiement |

### Reçus

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/receipts` | admin+, gestionnaire*, locataire* | Liste reçus |
| GET | `/api/v1/receipts/{id}` | * filtré | Détail reçu |
| GET | `/api/v1/receipts/{id}/pdf` | * filtré | Télécharger PDF |
| POST | `/api/v1/receipts/{id}/send-email` | admin+, gestionnaire | Envoyer par email |
| POST | `/api/v1/receipts/{id}/send-whatsapp` | admin+, gestionnaire | Envoyer WhatsApp (Sprint 13) |
| POST | `/api/v1/receipts/{id}/cancel` | super_admin | Annuler reçu (→ Sprint 10) |

### POST `/api/v1/payments` — Body

```json
{
  "lease_id": "uuid",
  "amount": 500000.00,
  "payment_method": "orange_money",
  "payment_date": "2026-07-26",
  "reference": "OM-123456789",
  "notes": "Paiement juillet + août 2026",
  "allocations": [
    { "period_year": 2026, "period_month": 7, "amount": 250000.00 },
    { "period_year": 2026, "period_month": 8, "amount": 250000.00 }
  ]
}
```

**Actions automatiques :**
1. Créer `payment` avec `recorded_by = current_user`
2. Créer `payment_allocations`
3. Mettre à jour `rent_periods.paid_amount` et `status`
4. Générer `receipt` + PDF
5. Notification « Paiement enregistré » (Sprint 13)

### Filtres GET `/api/v1/payments`

| Param | Description |
|-------|-------------|
| `tenant_id` | Par locataire |
| `lease_id` | Par bail |
| `building_id` | Par immeuble |
| `payment_method` | Mode paiement |
| `date_from` / `date_to` | Période |
| `status` | recorded / validated / cancelled |

---

## Génération PDF reçu

### Contenu du reçu

| Section | Contenu |
|---------|---------|
| En-tête | Logo, nom agence/gestion, adresse |
| Numéro | `REC-2026-000001` |
| Date | Date d'émission |
| Locataire | Nom, téléphone |
| Logement | Code, immeuble, adresse |
| Détail | Mois payés, montants par mois |
| Total | Montant total en lettres + chiffres |
| Mode | Espèces / Orange Money / etc. |
| Référence | Numéro transaction si applicable |
| Signature | Nom du gestionnaire qui a enregistré |
| Pied de page | « Reçu non valable sans signature » |

### Librairie

- **ReportLab** ou **WeasyPrint** (HTML → PDF template Jinja2)
- Stocker PDF dans MinIO/S3 → `pdf_url`

---

## Tâches Backend

- [ ] Modèles `RentPeriod`, `Payment`, `PaymentAllocation`, `Receipt`
- [ ] Migration Alembic
- [ ] `RentPeriodService.generate_for_lease()` — créer échéances mensuelles
- [ ] `PaymentService.record_payment()` — logique allocation
- [ ] `ReceiptService.generate_pdf()` — génération PDF
- [ ] `ReceiptNumberService` — numérotation séquentielle
- [ ] Upload preuve paiement
- [ ] Mise à jour statuts échéances (`pending` → `partial` → `paid`)
- [ ] Email service mock (envoi reçu PDF en pièce jointe)
- [ ] Tests : paiement simple, multi-mois, partiel, génération reçu

---

## Tâches Frontend

### Pages

| Route | Rôle | Description |
|-------|------|-------------|
| `/dashboard/paiements` | admin+, gestionnaire | Liste paiements |
| `/dashboard/paiements/nouveau` | admin+, gestionnaire | Enregistrer paiement |
| `/dashboard/paiements/[id]` | admin+, gestionnaire, locataire* | Détail paiement |
| `/dashboard/recus` | admin+, gestionnaire, locataire* | Liste reçus |
| `/dashboard/recus/[id]` | * filtré | Détail + preview PDF |

### Composants

- [ ] `PaymentForm` — sélection bail/locataire, montant, mode, allocations multi-mois
- [ ] `PeriodAllocationTable` — tableau mois avec montants dus/restants
- [ ] `PaymentMethodSelect` — icônes Espèces, OM, Wave, Virement
- [ ] `ProofUploader` — upload justificatif
- [ ] `ReceiptPreview` — iframe/preview PDF
- [ ] `SendReceiptModal` — choix email/WhatsApp
- [ ] `PaymentTimeline` — historique paiements locataire
- [ ] `AmountInWords` — affichage montant en lettres (FR)

### UX formulaire paiement

1. Sélectionner locataire (autocomplete)
2. Afficher bail actif + mois impayés/partiels
3. Saisir montant → répartition auto sur mois les plus anciens d'abord
4. Permettre ajustement manuel des allocations
5. Choisir mode + date + référence
6. Upload preuve (optionnel)
7. Confirmer → afficher reçu généré + boutons envoi

---

## Règles métier

1. Montant allocations = montant paiement (validation stricte).
2. Allocation prioritaire : mois les plus anciens impayés en premier.
3. Paiement partiel : échéance passe en `partial`.
4. Chaque paiement validé génère exactement 1 reçu.
5. Reçu annulé → paiement status `cancelled`, échéances recalculées.
6. Modification/suppression paiement → validation super admin (Sprint 10).
7. Traçabilité : `recorded_by`, `validated_by`, dates.

---

## Critères d'acceptation

- [ ] Enregistrement paiement simple (1 mois) fonctionne
- [ ] Paiement multi-mois avec allocations correctes
- [ ] Paiement partiel met échéance en `partial`
- [ ] Reçu PDF généré avec numéro unique
- [ ] Téléchargement PDF fonctionne
- [ ] Envoi email reçu (mock) fonctionne
- [ ] Locataire voit ses paiements et reçus (lecture seule)
- [ ] Traçabilité « enregistré par » visible
- [ ] Tests backend passent

---

## Template PDF

Créer `backend/app/templates/receipt.html` (WeasyPrint) ou `receipt_generator.py` (ReportLab).
