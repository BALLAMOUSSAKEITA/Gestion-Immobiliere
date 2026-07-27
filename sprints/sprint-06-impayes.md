# Sprint 6 — Impayés & relances

**Durée estimée :** 1 semaine  
**Prérequis :** Sprint 5  
**Dépendances pour le sprint suivant :** Sprint 7

---

## Objectif

Détecter automatiquement les loyers impayés, afficher le tableau de bord des créances, calculer les retards, et gérer l'historique des relances (notifications détaillées en Sprint 13).

---

## User stories

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S6-01 | Système | Détecter automatiquement les impayés | Alerter sans intervention manuelle |
| S6-02 | Admin Familial | Voir la liste des impayés | Suivre les créances |
| S6-03 | Gestionnaire | Signaler un impayé manuellement | Remonter une situation |
| S6-04 | Admin Familial | Voir le total cumulé par locataire | Prioriser les relances |
| S6-05 | Admin Familial | Consulter l'historique des relances | Savoir ce qui a déjà été fait |
| S6-06 | Locataire | Voir mes mois impayés | Connaître ma situation |

---

## Modèles de données

### Table `overdue_records` (vue matérialisée ou table calculée)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| rent_period_id | UUID | FK → rent_periods.id, UNIQUE |
| lease_id | UUID | FK → leases.id |
| tenant_id | UUID | FK → tenants.id |
| unit_id | UUID | FK → units.id |
| period_year | INTEGER | NOT NULL |
| period_month | INTEGER | NOT NULL |
| amount_due | DECIMAL(12,2) | NOT NULL |
| amount_paid | DECIMAL(12,2) | NOT NULL |
| amount_remaining | DECIMAL(12,2) | NOT NULL |
| days_overdue | INTEGER | NOT NULL |
| status | ENUM | `open`, `partially_paid`, `resolved` |
| detected_at | TIMESTAMPTZ | NOT NULL |
| resolved_at | TIMESTAMPTZ | nullable |

### Table `reminders` (relances)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| tenant_id | UUID | FK → tenants.id |
| overdue_record_id | UUID | FK → overdue_records.id, nullable |
| reminder_type | ENUM | `before_due`, `after_due`, `manual`, `final_notice` |
| channel | ENUM | `in_app`, `email`, `sms`, `whatsapp` |
| message | TEXT | NOT NULL |
| sent_at | TIMESTAMPTZ | NOT NULL |
| sent_by | UUID | FK → users.id, nullable — null si automatique |
| status | ENUM | `sent`, `failed`, `pending` |

### Table `overdue_summaries` (cache agrégé par locataire)

Recalculé par job ou trigger :

| Colonne | Type |
|---------|------|
| tenant_id | UUID |
| total_overdue_amount | DECIMAL(12,2) |
| overdue_months_count | INTEGER |
| oldest_overdue_days | INTEGER |
| last_reminder_at | TIMESTAMPTZ |

---

## Logique de détection automatique

### Job planifié (cron / APScheduler)

Exécution : **tous les jours à 06:00**

```
Pour chaque rent_period WHERE status IN (pending, partial, overdue):
  IF today > due_date AND paid_amount < expected_amount:
    status → overdue
    Créer/mettre à jour overdue_record
    Calculer days_overdue = today - due_date
    IF days_overdue == 3: relance automatique (after_due)
    IF days_overdue == 15: relance automatique (final_notice)
```

### Job rappel avant échéance

Exécution : **tous les jours à 08:00**

```
Pour chaque rent_period WHERE status == pending:
  IF due_date - today == 3 jours:
    Créer reminder type before_due
```

---

## Endpoints API

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/overdues` | admin+, gestionnaire* | Liste impayés |
| GET | `/api/v1/overdues/summary` | admin+, gestionnaire* | Totaux globaux |
| GET | `/api/v1/overdues/by-tenant` | admin+ | Agrégé par locataire |
| GET | `/api/v1/overdues/{id}` | admin+, gestionnaire* | Détail impayé |
| POST | `/api/v1/overdues/{id}/resolve` | admin+ | Marquer résolu (après paiement auto) |
| GET | `/api/v1/tenants/{id}/overdues` | admin+, gestionnaire*, locataire* | Impayés locataire |
| GET | `/api/v1/reminders` | admin+ | Historique relances |
| POST | `/api/v1/reminders` | admin+, gestionnaire | Envoyer relance manuelle |
| GET | `/api/v1/tenants/{id}/reminders` | admin+, locataire* | Relances locataire |

### GET `/api/v1/overdues` — Filtres

| Param | Description |
|-------|-------------|
| `building_id` | Par immeuble |
| `tenant_id` | Par locataire |
| `min_days` | Retard minimum (jours) |
| `min_amount` | Montant minimum dû |
| `sort` | `days_overdue`, `amount`, `tenant_name` |

### Réponse liste impayés

```json
{
  "items": [
    {
      "id": "uuid",
      "tenant": { "id": "uuid", "full_name": "Aminata Traoré", "phone": "+225..." },
      "unit_code": "KM001-A101",
      "building_name": "Résidence Les Palmiers",
      "period": "2026-06",
      "amount_remaining": 250000.00,
      "days_overdue": 26,
      "reminders_count": 2,
      "last_reminder_at": "2026-07-20T10:00:00Z"
    }
  ],
  "summary": {
    "total_overdue_amount": 1750000.00,
    "total_tenants_affected": 5,
    "total_periods_overdue": 8
  }
}
```

### POST `/api/v1/reminders` — Body

```json
{
  "tenant_id": "uuid",
  "overdue_record_ids": ["uuid1", "uuid2"],
  "reminder_type": "manual",
  "channel": "email",
  "message": "Bonjour, nous vous rappelons que votre loyer de juin 2026 reste impayé..."
}
```

---

## Tâches Backend

- [ ] Modèles `OverdueRecord`, `Reminder`
- [ ] Migration Alembic
- [ ] `OverdueDetectionService` — détection et mise à jour
- [ ] `ReminderService` — envoi relances
- [ ] APScheduler ou Celery Beat pour jobs cron
- [ ] Résolution auto impayé quand paiement couvre le montant (hook PaymentService)
- [ ] Endpoint summary avec agrégations SQL
- [ ] Templates messages relance (FR)
- [ ] Tests : détection, calcul jours retard, résolution après paiement

### Templates relance (FR)

**Avant échéance (J-3) :**
> Bonjour {nom}, votre loyer de {mois} d'un montant de {montant} FCFA est exigible le {date}. Merci de procéder au règlement.

**Après échéance (J+3) :**
> Bonjour {nom}, sauf erreur, nous n'avons pas reçu votre loyer de {mois} ({montant} FCFA), en retard de {jours} jours.

**Mise en demeure (J+15) :**
> Bonjour {nom}, malgré nos relances, votre loyer de {mois} reste impayé. Montant total dû : {total} FCFA. Merci de régulariser sous 7 jours.

---

## Tâches Frontend

### Pages

| Route | Rôle | Description |
|-------|------|-------------|
| `/dashboard/impayes` | admin+, gestionnaire | Tableau impayés |
| `/dashboard/impayes/[id]` | admin+ | Détail + relances |
| `/dashboard/relances` | admin+ | Historique relances |
| `/espace-locataire/impayes` | locataire | Mes impayés (Sprint 12) |

### Composants

- [ ] `OverdueTable` — tableau triable (locataire, logement, mois, montant, jours retard)
- [ ] `OverdueSummaryCards` — KPI : total impayés, nb locataires, pire retard
- [ ] `OverdueByTenantChart` — bar chart top débiteurs
- [ ] `SendReminderModal` — composer et envoyer relance
- [ ] `ReminderHistory` — timeline relances par locataire
- [ ] `OverdueBadge` — badge rouge avec nb jours
- [ ] Filtres avancés (immeuble, retard min, montant min)

### Colonnes tableau impayés (cahier des charges)

| Colonne | Source |
|---------|--------|
| Mois non payé | period_year/month |
| Montant dû | amount_remaining |
| Jours de retard | days_overdue |
| Total cumulé | sum par tenant |
| Nom locataire | tenant.full_name |
| Logement | unit_code |
| Relances envoyées | reminders_count |

---

## Règles métier

1. Impayé = échéance dépassée ET `paid_amount < expected_amount`.
2. Résolution automatique dès que paiement couvre le solde.
3. Gestionnaire peut signaler impayé manuellement (crée reminder `manual`).
4. Gestionnaire voit impayés de ses immeubles assignés uniquement.
5. Locataire voit ses propres impayés (lecture seule).
6. Relances automatiques créent entrée `reminders` même si envoi différé (Sprint 13).

---

## Critères d'acceptation

- [ ] Job détection marque échéances en `overdue` après due_date
- [ ] Liste impayés affiche toutes colonnes du cahier des charges
- [ ] Total cumulé par locataire correct
- [ ] Relance manuelle enregistrée dans historique
- [ ] Paiement résout automatiquement l'impayé correspondant
- [ ] Locataire voit ses mois impayés
- [ ] Summary KPI correct (montant total, nb locataires)
- [ ] Tests backend passent

---

## Intégration Sprint 13

Les relances automatiques J-3, J+3, J+15 créeront des notifications in-app et emails via le module notifications.
