# Sprint 11 — Tableau de bord & rapports

**Durée estimée :** 2 semaines  
**Prérequis :** Sprint 10  
**Dépendances pour le sprint suivant :** Sprint 12

---

## Objectif

Construire le tableau de bord professionnel avec tous les KPI, graphiques mensuels/annuels, et le module de rapports automatiques exportables en PDF et Excel.

---

## User stories

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S11-01 | Super Admin | Voir un tableau de bord global | Piloter l'activité |
| S11-02 | Admin Familial | Voir les KPI du mois | Suivre la performance |
| S11-03 | Propriétaire | Voir mes revenus et bénéfices | Connaître ma rentabilité |
| S11-04 | Admin Familial | Générer un rapport mensuel | Archiver et analyser |
| S11-05 | Admin Familial | Exporter en PDF ou Excel | Partager ou approfondir |
| S11-06 | Admin Familial | Filtrer par immeuble/propriétaire | Analyses ciblées |

---

## KPI tableau de bord (cahier des charges)

| Indicateur | Source de calcul |
|------------|------------------|
| 🏢 Nombre total d'immeubles | COUNT(buildings WHERE is_active) |
| 🏠 Nombre total d'appartements | COUNT(units WHERE type=apartment) |
| 🏪 Nombre total de magasins | COUNT(units WHERE type=shop) |
| ✅ Logements occupés | COUNT(units WHERE status=occupied) |
| 📭 Logements libres | COUNT(units WHERE status=free) |
| 💰 Loyers attendus du mois | SUM(rent_periods.expected_amount) mois courant |
| 💵 Loyers encaissés | SUM(payments.amount) mois courant, status≠cancelled |
| ⚠️ Montant des impayés | SUM(overdue_records.amount_remaining) |
| 📊 Dépenses du mois | SUM(expenses.amount) mois courant, status=validated |
| 📈 Bénéfice net | loyers_encaissés - dépenses_mois |
| 📄 Contrats expirant | COUNT(leases WHERE end_date <= today+30) |
| 🔧 Réparations en cours | COUNT(repairs WHERE status NOT IN completed,cancelled) |

---

## Graphiques

### Graphique 1 — Revenus vs Dépenses (mensuel, 12 mois)

- Barres : loyers encaissés par mois
- Ligne : dépenses par mois
- Aire : bénéfice net

### Graphique 2 — Taux d'occupation (mensuel)

- Ligne : % logements occupés sur 12 mois

### Graphique 3 — Répartition dépenses par catégorie

- Camembert : montants par catégorie (mois ou année)

### Graphique 4 — Top impayés

- Barres horizontales : top 10 locataires par montant dû

### Graphique 5 — Paiements par mode

- Camembert : espèces, Orange Money, Wave, virement

---

## Modèles de données

### Table `report_snapshots` (cache rapports générés)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| report_type | ENUM | `daily`, `weekly`, `monthly`, `annual` |
| period_start | DATE | NOT NULL |
| period_end | DATE | NOT NULL |
| filters | JSONB | nullable — immeuble, propriétaire, etc. |
| data | JSONB | NOT NULL — données agrégées |
| pdf_url | VARCHAR(500) | nullable |
| excel_url | VARCHAR(500) | nullable |
| generated_by | UUID | FK → users.id, nullable — null si auto |
| generated_at | TIMESTAMPTZ | NOT NULL |

---

## Endpoints API

### Dashboard

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/dashboard/kpis` | admin+, proprietaire* | Tous KPI |
| GET | `/api/v1/dashboard/charts/revenue-expenses` | admin+, proprietaire* | Graphique revenus/dépenses |
| GET | `/api/v1/dashboard/charts/occupancy` | admin+, proprietaire* | Taux occupation |
| GET | `/api/v1/dashboard/charts/expenses-by-category` | admin+, proprietaire* | Dépenses catégories |
| GET | `/api/v1/dashboard/charts/payment-methods` | admin+ | Modes paiement |
| GET | `/api/v1/dashboard/alerts` | admin+ | Alertes (impayés, baux expirants, validations pending) |
| GET | `/api/v1/dashboard/recent-activity` | admin+ | Dernières actions (audit) |

### Query params communs (filtres)

| Param | Description |
|-------|-------------|
| `building_id` | Par immeuble |
| `owner_profile_id` | Par propriétaire |
| `year` | Année (default: courante) |
| `month` | Mois (default: courant) |

### Rapports

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/reports` | admin+, proprietaire* | Liste rapports générés |
| POST | `/api/v1/reports/generate` | admin+, proprietaire* | Générer rapport |
| GET | `/api/v1/reports/{id}` | * filtré | Détail rapport |
| GET | `/api/v1/reports/{id}/pdf` | * filtré | Télécharger PDF |
| GET | `/api/v1/reports/{id}/excel` | * filtré | Télécharger Excel |

### POST `/api/v1/reports/generate` — Body

```json
{
  "report_type": "monthly",
  "period_start": "2026-07-01",
  "period_end": "2026-07-31",
  "filters": {
    "building_id": "uuid",
    "owner_profile_id": null,
    "tenant_id": null,
    "manager_user_id": null,
    "unit_type": null
  },
  "export_formats": ["pdf", "excel"]
}
```

### Filtres rapports (cahier des charges)

| Filtre | Champ |
|--------|-------|
| Par immeuble | `building_id` |
| Par propriétaire | `owner_profile_id` |
| Par locataire | `tenant_id` |
| Par gestionnaire | `manager_user_id` |
| Par type logement | `unit_type` |

---

## Contenu rapport mensuel (PDF)

1. **En-tête** — Période, filtres appliqués, date génération
2. **Résumé KPI** — Tous indicateurs du dashboard
3. **Tableau loyers** — Par logement : attendu, encaissé, impayé
4. **Tableau dépenses** — Par catégorie et immeuble
5. **Liste impayés** — Locataires, montants, jours retard
6. **Baux expirants** — Contrats finissant dans 30 jours
7. **Réparations** — En cours et terminées dans la période
8. **Bénéfice net** — Calcul détaillé

---

## Tâches Backend

- [ ] `DashboardService` — agrégations SQL optimisées
- [ ] `ReportService` — génération données + exports
- [ ] Génération PDF rapport (template Jinja2 + WeasyPrint)
- [ ] Génération Excel (openpyxl ou xlsxwriter)
- [ ] Jobs cron rapports automatiques :
  - Journalier : 23:00
  - Hebdomadaire : dimanche 23:00
  - Mensuel : 1er du mois 06:00
  - Annuel : 1er janvier 06:00
- [ ] Cache KPI (Redis optionnel, ou recalcul à la demande)
- [ ] RBAC : propriétaire filtré par ses biens
- [ ] Tests : calculs KPI, génération rapport, filtres

### Librairies export Excel

```
openpyxl>=3.1.0
```

Feuilles Excel :
- `Résumé`, `Loyers`, `Dépenses`, `Impayés`, `Réparations`

---

## Tâches Frontend

### Pages

| Route | Rôle | Description |
|-------|------|-------------|
| `/dashboard` | admin+, proprietaire*, gestionnaire* | Tableau de bord principal |
| `/dashboard/rapports` | admin+, proprietaire* | Liste rapports |
| `/dashboard/rapports/generer` | admin+, proprietaire* | Formulaire génération |
| `/dashboard/rapports/[id]` | * filtré | Détail + téléchargements |

### Layout dashboard

```
┌─────────────────────────────────────────────────┐
│  Header : Bienvenue + filtres (immeuble, mois)  │
├──────────┬──────────┬──────────┬────────────────┤
│ KPI Card │ KPI Card │ KPI Card │ KPI Card       │
├──────────┴──────────┴──────────┴────────────────┤
│  Graphique Revenus vs Dépenses (2/3)  │ Occup. │
├───────────────────────────────────────┴─────────┤
│  Alertes          │  Activité récente           │
├───────────────────┴─────────────────────────────┤
│  Impayés récents  │  Baux expirants           │
└─────────────────────────────────────────────────┘
```

### Composants

- [ ] `KpiCard` — icône, valeur, label, trend (↑↓ vs mois précédent)
- [ ] `DashboardFilters` — immeuble, propriétaire, période
- [ ] `RevenueExpenseChart` — Recharts composé bar+line
- [ ] `OccupancyChart` — Recharts line
- [ ] `ExpenseCategoryChart` — Recharts pie
- [ ] `PaymentMethodChart` — Recharts pie
- [ ] `AlertsPanel` — impayés critiques, baux expirants, validations
- [ ] `RecentActivityFeed` — dernières actions audit
- [ ] `OverdueQuickList` — top 5 impayés
- [ ] `ExpiringLeasesList` — baux finissant bientôt
- [ ] `ReportGeneratorForm` — type, période, filtres, formats
- [ ] `ReportList` — historique rapports générés
- [ ] `ReportPreview` — preview PDF inline

### Librairie graphiques

```bash
npm install recharts
```

---

## RBAC dashboard

| Rôle | Périmètre KPI |
|------|---------------|
| super_admin | Tout le patrimoine |
| admin_familial | Selon permissions (scope building/owner) |
| proprietaire | Ses biens uniquement — revenus, dépenses, bénéfice |
| gestionnaire | Immeubles assignés — sans infos financières famille globale |

**Restriction gestionnaire (cahier des charges) :** Ne voit pas revenus/dépenses/bénéfice globaux famille. Dashboard gestionnaire limité à :
- Logements assignés (occupés/libres)
- Réparations en cours
- Impayés de ses immeubles (montants oui, mais pas bénéfice net global)

---

## Critères d'acceptation

- [ ] Dashboard affiche les 12 KPI du cahier des charges
- [ ] Graphiques mensuels (12 mois) et filtres fonctionnels
- [ ] Propriétaire voit dashboard filtré à ses biens
- [ ] Gestionnaire voit dashboard limité (pas bénéfice global famille)
- [ ] Génération rapport mensuel PDF + Excel
- [ ] Filtres rapport : immeuble, propriétaire, locataire, gestionnaire, type
- [ ] Rapports automatiques cron configurés
- [ ] Alertes : impayés, baux expirants, validations pending
- [ ] Tests calculs KPI backend passent

---

## Performance

- Requêtes KPI : utiliser vues SQL ou CTE optimisées
- Index recommandés : `rent_periods(period_year, period_month)`, `payments(payment_date)`, `expenses(expense_date)`
- Cache dashboard : TTL 5 min (optionnel)
