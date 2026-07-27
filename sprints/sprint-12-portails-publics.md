# Sprint 12 — Portails Visiteur & Locataire

**Durée estimée :** 1 à 2 semaines  
**Prérequis :** Sprint 11  
**Dépendances pour le sprint suivant :** Sprint 13

---

## Objectif

Finaliser les espaces dédiés au **Visiteur** (annonces publiques, demande de visite, contact gestionnaire) et au **Locataire** (mon logement, contrat, paiements, reçus, impayés, réparations, messages).

---

## User stories — Visiteur

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S12-01 | Visiteur | Voir les logements disponibles | Trouver un logement |
| S12-02 | Visiteur | Voir photos et loyer | Évaluer le bien |
| S12-03 | Visiteur | Voir la localisation générale | Me situer |
| S12-04 | Visiteur | Demander une visite | Organiser une visite |
| S12-05 | Visiteur | Contacter le gestionnaire | Poser des questions |

---

## User stories — Locataire

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S12-06 | Locataire | Voir mon logement | Connaître mon bien |
| S12-07 | Locataire | Consulter mon contrat et loyer | Vérifier mes obligations |
| S12-08 | Locataire | Voir mon historique de paiement | Suivre mes règlements |
| S12-09 | Locataire | Télécharger mes reçus | Avoir mes justificatifs |
| S12-10 | Locataire | Voir mes mois impayés | Régulariser ma situation |
| S12-11 | Locataire | Signaler une panne | Demander une intervention |
| S12-12 | Locataire | Envoyer un message au gestionnaire | Communiquer |
| S12-13 | Locataire | Télécharger un avis ou document | Accéder à mes papiers |

---

## Modèles de données

### Table `visit_requests` (demandes de visite)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| unit_id | UUID | FK → units.id |
| visitor_name | VARCHAR(200) | NOT NULL |
| visitor_email | VARCHAR(255) | NOT NULL |
| visitor_phone | VARCHAR(20) | NOT NULL |
| preferred_date | DATE | nullable |
| preferred_time | VARCHAR(50) | nullable — ex: "14:00-16:00" |
| message | TEXT | nullable |
| status | ENUM | `pending`, `confirmed`, `cancelled`, `completed` |
| assigned_to | UUID | FK → users.id, nullable — gestionnaire |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

### Table `contact_messages` (messages visiteur/locataire → gestionnaire)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| sender_user_id | UUID | FK → users.id, nullable — null si visiteur |
| sender_name | VARCHAR(200) | NOT NULL |
| sender_email | VARCHAR(255) | NOT NULL |
| sender_phone | VARCHAR(20) | nullable |
| recipient_user_id | UUID | FK → users.id — gestionnaire |
| unit_id | UUID | FK → units.id, nullable |
| subject | VARCHAR(300) | NOT NULL |
| body | TEXT | NOT NULL |
| is_read | BOOLEAN | DEFAULT false |
| read_at | TIMESTAMPTZ | nullable |
| parent_message_id | UUID | FK → contact_messages.id, nullable — fil |
| created_at | TIMESTAMPTZ | NOT NULL |

### Table `tenant_notices` (avis/documents pour locataire)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| tenant_id | UUID | FK → tenants.id |
| document_id | UUID | FK → documents.id, nullable |
| title | VARCHAR(300) | NOT NULL |
| content | TEXT | nullable |
| notice_type | ENUM | `info`, `warning`, `payment_reminder`, `maintenance`, `other` |
| published_at | TIMESTAMPTZ | NOT NULL |
| published_by | UUID | FK → users.id |
| is_read | BOOLEAN | DEFAULT false |

---

## Endpoints API — Public (Visiteur)

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/public/units` | Non | Annonces logements libres |
| GET | `/api/v1/public/units/{id}` | Non | Détail annonce |
| POST | `/api/v1/public/visit-requests` | Non | Demander visite |
| POST | `/api/v1/public/contact` | Non | Contacter gestionnaire |

### Données publiques autorisées

| Champ | Visible |
|-------|---------|
| Photos logement | ✅ |
| Type (appartement, magasin) | ✅ |
| Loyer mensuel | ✅ |
| Commune / Quartier | ✅ |
| Description | ✅ |
| Adresse exacte | ❌ |
| Nom locataire | ❌ |
| Revenus | ❌ |
| Infos propriétaire | ❌ |

### POST `/api/v1/public/visit-requests`

```json
{
  "unit_id": "uuid",
  "visitor_name": "Kofi Mensah",
  "visitor_email": "kofi@email.com",
  "visitor_phone": "+2250700000099",
  "preferred_date": "2026-08-05",
  "preferred_time": "10:00-12:00",
  "message": "Je souhaite visiter cet appartement."
}
```

---

## Endpoints API — Locataire

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/tenant-portal/dashboard` | locataire | Résumé espace locataire |
| GET | `/api/v1/tenant-portal/my-unit` | locataire | Mon logement |
| GET | `/api/v1/tenant-portal/my-lease` | locataire | Mon contrat |
| GET | `/api/v1/tenant-portal/payments` | locataire | Historique paiements |
| GET | `/api/v1/tenant-portal/receipts` | locataire | Mes reçus |
| GET | `/api/v1/tenant-portal/overdues` | locataire | Mes impayés |
| GET | `/api/v1/tenant-portal/repairs` | locataire | Mes réparations |
| POST | `/api/v1/tenant-portal/repairs` | locataire | Signaler panne |
| GET | `/api/v1/tenant-portal/documents` | locataire | Mes documents |
| GET | `/api/v1/tenant-portal/notices` | locataire | Mes avis |
| GET | `/api/v1/tenant-portal/messages` | locataire | Mes messages |
| POST | `/api/v1/tenant-portal/messages` | locataire | Envoyer message |
| PATCH | `/api/v1/tenant-portal/notices/{id}/read` | locataire | Marquer avis lu |

### Réponse `/tenant-portal/dashboard`

```json
{
  "tenant": { "full_name": "Aminata Traoré" },
  "unit": { "code": "KM001-A101", "type": "Appartement" },
  "lease": { "rent_amount": 250000, "end_date": "2027-07-31" },
  "payment_status": {
    "current_month_paid": true,
    "total_unpaid": 0,
    "next_due_date": "2026-08-01"
  },
  "unread_notices": 2,
  "active_repairs": 1
}
```

---

## Endpoints API — Gestionnaire (gestion visites/messages)

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/visit-requests` | admin+, gestionnaire | Liste demandes visite |
| PATCH | `/api/v1/visit-requests/{id}` | admin+, gestionnaire | Confirmer/annuler |
| GET | `/api/v1/messages` | admin+, gestionnaire, locataire | Boîte messages |
| POST | `/api/v1/messages/{id}/reply` | admin+, gestionnaire | Répondre |
| PATCH | `/api/v1/messages/{id}/read` | auth | Marquer lu |
| POST | `/api/v1/tenant-notices` | admin+, gestionnaire | Publier avis locataire |

---

## Tâches Backend

- [ ] Modèles `VisitRequest`, `ContactMessage`, `TenantNotice`
- [ ] Migration Alembic
- [ ] Endpoints public sans fuite de données privées
- [ ] `TenantPortalService` — agrège données locataire depuis tenant.user_id
- [ ] Auto-assignation gestionnaire immeuble aux visit requests
- [ ] Validation locataire : accès uniquement à SES données (via tenant_id lié à user)
- [ ] Tests : endpoints public, isolation locataire, messages

---

## Tâches Frontend

### Layouts séparés

```
app/
├── (public)/
│   ├── annonces/
│   │   ├── page.tsx
│   │   └── [id]/page.tsx
│   ├── contact/page.tsx
│   └── layout.tsx          # Header public, pas sidebar
├── (tenant)/
│   └── espace-locataire/
│       ├── page.tsx        # Dashboard locataire
│       ├── mon-logement/
│       ├── mon-contrat/
│       ├── paiements/
│       ├── recus/
│       ├── impayes/
│       ├── reparations/
│       ├── documents/
│       ├── messages/
│       └── layout.tsx      # Sidebar locataire
└── (dashboard)/            # Admin (sprints précédents)
```

### Pages publiques

| Route | Description |
|-------|-------------|
| `/annonces` | Grille logements avec filtres (type, prix max, commune) |
| `/annonces/[id]` | Galerie photos, loyer, quartier, bouton « Demander visite » |
| `/contact` | Formulaire contact général |

### Pages espace locataire

| Route | Description |
|-------|-------------|
| `/espace-locataire` | Dashboard résumé |
| `/espace-locataire/mon-logement` | Infos logement + photos |
| `/espace-locataire/mon-contrat` | Bail, dates, loyer, download contrat |
| `/espace-locataire/paiements` | Historique avec statuts |
| `/espace-locataire/recus` | Liste + téléchargement PDF |
| `/espace-locataire/impayes` | Mois impayés + montants |
| `/espace-locataire/reparations` | Mes signalements + nouveau |
| `/espace-locataire/documents` | Contrat, reçus, avis |
| `/espace-locataire/messages` | Messagerie gestionnaire |

### Composants

- [ ] `PublicHeader` — logo, liens Annonces, Contact, Connexion
- [ ] `ListingGrid` — cartes annonces responsive
- [ ] `ListingDetail` — galerie, infos, carte quartier
- [ ] `VisitRequestForm` — modal demande visite
- [ ] `ContactForm` — message au gestionnaire
- [ ] `TenantSidebar` — navigation espace locataire
- [ ] `TenantDashboard` — widgets résumé
- [ ] `PaymentHistoryTable` — historique locataire
- [ ] `ReceiptDownloadList`
- [ ] `OverdueAlert` — bandeau si impayés
- [ ] `MessageThread` — fil conversation
- [ ] `NoticeCard` — avis/documents

### Redirect post-login par rôle

| Rôle | Redirect |
|------|----------|
| super_admin, admin_familial | `/dashboard` |
| gestionnaire | `/dashboard` |
| proprietaire | `/dashboard` |
| locataire | `/espace-locataire` |
| visiteur | `/annonces` |

---

## Règles métier

1. Visiteur : aucune donnée privée (locataires, revenus, adresse exacte).
2. Locataire sans bail actif → message « Aucun logement associé ».
3. Locataire ne voit que ses propres paiements, reçus, documents.
4. Demande visite notifie gestionnaire de l'immeuble (Sprint 13).
5. Messages visiteur sans compte : `sender_user_id = null`.
6. Compte visiteur optionnel : peut s'inscrire ou rester anonyme pour visites.

---

## Critères d'acceptation

- [ ] Page `/annonces` affiche logements libres publics uniquement
- [ ] Détail annonce sans données privées
- [ ] Formulaire demande visite fonctionne sans compte
- [ ] Contact gestionnaire fonctionne
- [ ] Locataire connecté → redirect `/espace-locataire`
- [ ] Dashboard locataire avec résumé complet
- [ ] Historique paiements + téléchargement reçus
- [ ] Signalement panne depuis espace locataire
- [ ] Messagerie locataire ↔ gestionnaire
- [ ] Gestionnaire voit et traite demandes de visite
- [ ] Tests backend isolation données passent

---

## SEO (annonces publiques)

- Metadata Next.js par annonce (title, description, Open Graph)
- URLs propres : `/annonces/km001-a101` (slug optionnel)
