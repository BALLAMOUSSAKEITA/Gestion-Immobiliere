# Plan de sprints — Gestion Immobilière

Application web : **Next.js** (frontend) + **FastAPI** (backend)

Ce dossier contient **14 sprints** à réaliser **dans l'ordre**. Chaque sprint est autonome mais dépend des précédents.

---

## Vue d'ensemble

| Sprint | Titre | Durée estimée | Fichier |
|--------|-------|---------------|---------|
| 0 | Fondations & environnement | 1 semaine | [sprint-00-fondations.md](./sprint-00-fondations.md) |
| 1 | Authentification & rôles (RBAC) | 1–2 semaines | [sprint-01-auth-rbac.md](./sprint-01-auth-rbac.md) |
| 2 | Gestion des utilisateurs | 1 semaine | [sprint-02-utilisateurs.md](./sprint-02-utilisateurs.md) |
| 3 | Immeubles & logements | 2 semaines | [sprint-03-immeubles-logements.md](./sprint-03-immeubles-logements.md) |
| 4 | Gestion des locataires | 1–2 semaines | [sprint-04-locataires.md](./sprint-04-locataires.md) |
| 5 | Paiements & reçus | 2 semaines | [sprint-05-paiements-recus.md](./sprint-05-paiements-recus.md) |
| 6 | Impayés & relances | 1 semaine | [sprint-06-impayes.md](./sprint-06-impayes.md) |
| 7 | Dépenses | 1 semaine | [sprint-07-depenses.md](./sprint-07-depenses.md) |
| 8 | Réparations | 1–2 semaines | [sprint-08-reparations.md](./sprint-08-reparations.md) |
| 9 | Contrats & documents | 1–2 semaines | [sprint-09-documents.md](./sprint-09-documents.md) |
| 10 | Validation & traçabilité | 1 semaine | [sprint-10-validation-audit.md](./sprint-10-validation-audit.md) |
| 11 | Tableau de bord & rapports | 2 semaines | [sprint-11-dashboard-rapports.md](./sprint-11-dashboard-rapports.md) |
| 12 | Portails Visiteur & Locataire | 1–2 semaines | [sprint-12-portails-publics.md](./sprint-12-portails-publics.md) |
| 13 | Notifications, finitions & déploiement | 1–2 semaines | [sprint-13-notifications-deploiement.md](./sprint-13-notifications-deploiement.md) |

**Durée totale estimée : 18 à 24 semaines** (équipe solo ou petite équipe)

---

## Stack technique recommandée

| Couche | Technologie |
|--------|-------------|
| Frontend | Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python 3.11+, Pydantic v2, SQLAlchemy 2 |
| Base de données | PostgreSQL |
| Auth | JWT (access + refresh tokens) |
| Stockage fichiers | MinIO ou AWS S3 (local en dev) |
| PDF | ReportLab ou WeasyPrint (backend) |
| Email | SMTP (dev) / SendGrid ou Resend (prod) |
| WhatsApp | API WhatsApp Business (optionnel, sprint 13) |

---

## Rôles utilisateurs (rappel)

| Rôle | Code technique |
|------|----------------|
| Super Administrateur | `super_admin` |
| Administrateur Familial | `admin_familial` |
| Propriétaire / Membre famille | `proprietaire` |
| Gestionnaire | `gestionnaire` |
| Visiteur | `visiteur` |
| Locataire | `locataire` |

---

## Comment utiliser ces sprints

1. Lire entièrement le sprint avant de coder.
2. Cocher les critères d'acceptation au fur et à mesure.
3. Ne pas passer au sprint suivant tant que tous les critères du sprint courant ne sont pas validés.
4. Chaque sprint liste : objectifs, user stories, tâches backend/frontend, modèles de données, endpoints API, pages UI, tests et livrables.

---

## Structure du projet (cible finale)

```
Gestion-Immobiliere/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
├── docker-compose.yml
├── sprints/          ← vous êtes ici
└── cahier_de_charge.md
```
