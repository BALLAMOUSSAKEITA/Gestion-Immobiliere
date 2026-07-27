# Sprint 13 — Notifications, finitions & déploiement

**Durée estimée :** 1 à 2 semaines  
**Prérequis :** Sprint 12  
**Dépendances :** Aucun (sprint final)

---

## Objectif

Finaliser le système de notifications (in-app + email), intégrer l'envoi WhatsApp pour les reçus, effectuer les finitions UI/UX, tests end-to-end, et déployer l'application en production.

---

## User stories

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S13-01 | Utilisateur | Recevoir des notifications in-app | Être informé en temps réel |
| S13-02 | Locataire | Recevoir un rappel avant l'échéance | Payer à temps |
| S13-03 | Admin | Être alerté des impayés | Relancer rapidement |
| S13-04 | Gestionnaire | Recevoir les demandes de réparation | Intervenir vite |
| S13-05 | Gestionnaire | Envoyer un reçu par WhatsApp | Remettre le justificatif |
| S13-06 | Équipe | Déployer en production | Mettre l'app en ligne |

---

## Événements notifiés (cahier des charges)

| Événement | Code | Destinataires | Canaux |
|-----------|------|---------------|--------|
| Loyer bientôt exigible | `rent.due_soon` | locataire | in_app, email |
| Loyer en retard | `rent.overdue` | locataire, admin, gestionnaire | in_app, email |
| Contrat bientôt expiré | `lease.expiring` | admin, proprietaire | in_app, email |
| Nouvelle demande réparation | `repair.new` | gestionnaire, admin | in_app, email |
| Paiement enregistré | `payment.recorded` | locataire | in_app, email |
| Reçu disponible | `receipt.available` | locataire | in_app, email, whatsapp |
| Dépense ajoutée | `expense.created` | admin, proprietaire* | in_app |
| Nouveau document | `document.uploaded` | concernés | in_app |
| Logement disponible | `unit.available` | admin | in_app |
| Demande visite | `visit.requested` | gestionnaire | in_app, email |
| Validation approuvée/rejetée | `approval.reviewed` | demandeur | in_app, email |
| Nouveau message | `message.received` | destinataire | in_app, email |

---

## Modèles de données

### Table `notifications`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| event_code | VARCHAR(100) | NOT NULL |
| title | VARCHAR(300) | NOT NULL |
| body | TEXT | NOT NULL |
| entity_type | VARCHAR(50) | nullable |
| entity_id | UUID | nullable |
| channel | ENUM | `in_app`, `email`, `whatsapp` |
| is_read | BOOLEAN | DEFAULT false |
| read_at | TIMESTAMPTZ | nullable |
| sent_at | TIMESTAMPTZ | nullable |
| email_sent | BOOLEAN | DEFAULT false |
| email_sent_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |

### Table `notification_preferences`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| event_code | VARCHAR(100) | NOT NULL |
| in_app_enabled | BOOLEAN | DEFAULT true |
| email_enabled | BOOLEAN | DEFAULT true |
| whatsapp_enabled | BOOLEAN | DEFAULT false |

**Contrainte UNIQUE :** `(user_id, event_code)`

### Table `email_queue` (file d'envoi)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| to_email | VARCHAR(255) | NOT NULL |
| subject | VARCHAR(500) | NOT NULL |
| body_html | TEXT | NOT NULL |
| attachments | JSONB | nullable |
| status | ENUM | `pending`, `sent`, `failed` |
| attempts | INTEGER | DEFAULT 0 |
| last_error | TEXT | nullable |
| scheduled_at | TIMESTAMPTZ | NOT NULL |
| sent_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |

---

## Architecture notifications

```
Événement métier (ex: PaymentService.record)
    → NotificationService.dispatch(event_code, recipients, payload)
        → Créer notification in_app
        → Si email_enabled → enqueue email_queue
        → Si whatsapp_enabled → WhatsAppService.send (reçus)
```

### Service `NotificationService`

```python
class NotificationService:
    async def dispatch(self, event_code: str, user_ids: list[UUID], payload: dict):
        ...
    async def mark_read(self, notification_id: UUID, user_id: UUID):
        ...
    async def get_unread_count(self, user_id: UUID) -> int:
        ...
```

### Worker email (background)

- APScheduler job toutes les 30s : traiter `email_queue WHERE status=pending`
- Retry 3 fois en cas d'échec
- Provider prod : **Resend**, **SendGrid**, ou SMTP

---

## Endpoints API

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/notifications` | auth | Mes notifications |
| GET | `/api/v1/notifications/unread-count` | auth | Compteur non lues |
| PATCH | `/api/v1/notifications/{id}/read` | auth | Marquer lue |
| POST | `/api/v1/notifications/read-all` | auth | Tout marquer lu |
| GET | `/api/v1/notification-preferences` | auth | Mes préférences |
| PUT | `/api/v1/notification-preferences` | auth | Modifier préférences |
| POST | `/api/v1/receipts/{id}/send-whatsapp` | admin+, gestionnaire | Envoyer reçu WhatsApp |

---

## Intégration WhatsApp (reçus)

### Option A — WhatsApp Business API (Meta)

- Nécessite compte Meta Business vérifié
- Template message pré-approuvé
- Envoi PDF via media URL

### Option B — Lien wa.me (MVP)

```
https://wa.me/{phone}?text={message_encodé}
```

Frontend ouvre WhatsApp avec message pré-rempli + lien téléchargement reçu.

**Recommandation MVP :** Option B pour Sprint 13, Option A en évolution.

---

## Raccordement événements existants

| Sprint | Événement | Hook à ajouter |
|--------|-----------|----------------|
| 5 | Paiement enregistré | `PaymentService.record_payment()` |
| 5 | Reçu généré | `ReceiptService.generate_pdf()` |
| 6 | Impayé détecté | `OverdueDetectionService.run()` |
| 6 | Relance envoyée | `ReminderService.send()` |
| 7 | Dépense créée | `ExpenseService.create()` |
| 8 | Réparation déclarée | `RepairService.create()` |
| 9 | Document uploadé | `DocumentService.upload()` |
| 10 | Validation traitée | `ApprovalService.review()` |
| 12 | Demande visite | `VisitRequestService.create()` |
| 12 | Message reçu | `MessageService.create()` |

---

## Tâches Backend

- [ ] Modèles `Notification`, `NotificationPreference`, `EmailQueue`
- [ ] Migration Alembic
- [ ] `NotificationService` centralisé
- [ ] `EmailService` avec templates HTML (Jinja2)
- [ ] Worker email background
- [ ] Brancher hooks sur tous événements listés
- [ ] Jobs cron rappels (compléter Sprint 6) avec envoi réel
- [ ] Endpoint WhatsApp (lien wa.me ou API)
- [ ] Préférences notification par utilisateur
- [ ] Tests : dispatch, email queue, mark read

### Templates email

Créer `backend/app/templates/emails/` :
- `rent_due_soon.html`
- `rent_overdue.html`
- `payment_confirmation.html`
- `receipt_available.html`
- `repair_new.html`
- `lease_expiring.html`
- `visit_request.html`
- `approval_reviewed.html`

---

## Tâches Frontend

### Composants globaux

- [ ] `NotificationBell` — icône cloche + badge count (header dashboard + locataire)
- [ ] `NotificationDropdown` — liste 10 dernières + lien « Voir tout »
- [ ] `NotificationList` — page liste complète
- [ ] `NotificationPreferences` — page paramètres
- [ ] Toast temps réel (optionnel : polling 30s ou WebSocket)

### Pages

| Route | Rôle | Description |
|-------|------|-------------|
| `/dashboard/notifications` | auth | Toutes notifications |
| `/dashboard/parametres/notifications` | auth | Préférences |
| `/espace-locataire/notifications` | locataire | Notifications locataire |

### Finitions UI/UX

- [ ] Loading skeletons sur toutes pages dashboard
- [ ] Empty states (illustrations + message)
- [ ] Error boundaries React
- [ ] Responsive mobile complet (sidebar → drawer)
- [ ] Mode sombre (optionnel)
- [ ] Favicon + logo application
- [ ] Page 404 / 403 custom
- [ ] Breadcrumbs navigation
- [ ] Confirmations modales cohérentes partout

---

## Tests

### Tests backend

- [ ] Couverture >= 70% services critiques
- [ ] Tests intégration auth, payments, RBAC
- [ ] Tests notification dispatch

### Tests frontend (optionnel)

```bash
npm install -D @playwright/test
```

- [ ] E2E : login → dashboard KPI visible
- [ ] E2E : enregistrer paiement → reçu généré
- [ ] E2E : locataire voit ses paiements
- [ ] E2E : annonce publique accessible sans auth

---

## Déploiement

### Architecture production recommandée

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vercel    │────▶│   Railway   │────▶│  PostgreSQL │
│  (Next.js)  │     │  (FastAPI)  │     │  (Neon/Supa)│
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │    MinIO    │
                    │   (S3/R2)   │
                    └─────────────┘
```

### Fichiers à créer

- [ ] `docker-compose.prod.yml` — backend + worker + minio
- [ ] `backend/Dockerfile`
- [ ] `frontend/Dockerfile` (si pas Vercel)
- [ ] `.github/workflows/ci.yml` — lint + tests on push
- [ ] `.github/workflows/deploy.yml` — deploy on main (optionnel)

### Variables production

| Service | Variables |
|---------|-----------|
| Backend | `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`, `S3_*`, `SMTP_*` |
| Frontend | `NEXT_PUBLIC_API_URL` |
| MinIO/S3 | `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` |

### Checklist déploiement

- [ ] HTTPS activé (backend + frontend)
- [ ] CORS configuré pour domaine prod
- [ ] Migrations Alembic exécutées
- [ ] Seed super admin production (mot de passe fort)
- [ ] Backup BDD automatique configuré
- [ ] Logs centralisés (optionnel : Sentry)
- [ ] Rate limiting production activé
- [ ] Secrets jamais commités

---

## Documentation finale

- [ ] README racine mis à jour (setup, deploy, architecture)
- [ ] Documentation API (Swagger auto + guide authentification)
- [ ] Guide utilisateur par rôle (optionnel, markdown)

---

## Critères d'acceptation sprint final

- [ ] Notifications in-app fonctionnent pour tous événements du cahier des charges
- [ ] Emails envoyés pour événements critiques (paiement, impayé, réparation)
- [ ] Cloche notifications avec compteur non lues
- [ ] Préférences notification modifiables par utilisateur
- [ ] Envoi reçu WhatsApp (lien wa.me minimum)
- [ ] Jobs cron relances et rapports actifs
- [ ] UI responsive et finitions (loading, empty states, erreurs)
- [ ] CI pipeline lint + tests passe
- [ ] Application déployée et accessible en production
- [ ] Super admin peut se connecter et voir dashboard complet

---

## Definition of Done — Projet complet

L'application est considérée **terminée** quand :

1. ✅ Les 6 rôles utilisateurs fonctionnent avec RBAC complet
2. ✅ Tous les modules du cahier des charges sont implémentés
3. ✅ Tableau de bord avec 12 KPI + graphiques
4. ✅ Paiements, reçus PDF, impayés automatiques
5. ✅ Dépenses, réparations, documents centralisés
6. ✅ Validation super admin + audit trail
7. ✅ Rapports PDF/Excel exportables
8. ✅ Portails visiteur et locataire opérationnels
9. ✅ Notifications in-app + email
10. ✅ Application déployée en production

---

## Maintenance post-lancement (hors scope)

- Application mobile (React Native)
- Paiement en ligne intégré (Orange Money API, Wave API)
- Multi-tenant (plusieurs agences)
- Signature électronique contrats
- Intelligence artificielle (prédiction impayés)
