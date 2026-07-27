# Gestion Immobilière

Application web de gestion immobilière — **Next.js** (frontend) + **FastAPI** (backend) + **PostgreSQL**.

## Prérequis

- [Node.js](https://nodejs.org/) 20+
- [Python](https://www.python.org/) 3.12+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (PostgreSQL local ou déploiement prod)

## Démarrage rapide (développement)

### 1. Base de données

```bash
docker compose up -d
```

### 2. Backend (FastAPI)

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
copy .env.example .env

alembic upgrade head
uvicorn app.main:app --reload
```

- API : http://localhost:8000
- Swagger : http://localhost:8000/docs

**Compte super admin (après migration) :**
- Email : `admin@gestion-immo.local`
- Mot de passe : `Admin123!`

### 3. Frontend (Next.js)

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Application : http://localhost:3000

## Déploiement production (Docker)

```bash
# Configurer les variables dans .env à la racine ou exporter :
# SECRET_KEY, POSTGRES_PASSWORD, NEXT_PUBLIC_API_URL, PUBLIC_API_URL

docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

Architecture recommandée :
- **Frontend** : Vercel ou conteneur Docker (port 3000)
- **Backend** : Railway / Render / Docker (port 8000)
- **PostgreSQL** : Neon, Supabase ou conteneur Postgres

## Variables d'environnement

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Connexion PostgreSQL |
| `SECRET_KEY` | Clé JWT (32+ caractères) |
| `CORS_ORIGINS` | Origines frontend autorisées |
| `ENABLE_SCHEDULER` | Worker emails + rappels (`true`/`false`) |
| `PUBLIC_API_URL` | URL publique API (liens reçus, WhatsApp) |
| `SMTP_*` | Configuration email (optionnel en dev) |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | URL du backend |

## Tests & CI

```bash
cd backend
pytest
```

Pipeline GitHub Actions : lint + tests backend + build frontend (`.github/workflows/ci.yml`).

## Fonctionnalités principales

- RBAC 6 rôles (super admin, admin familial, propriétaire, gestionnaire, locataire, visiteur)
- Immeubles, logements, locataires, baux, paiements, reçus PDF
- Impayés automatiques, relances, dépenses, réparations
- Bibliothèque documentaire, validations super admin, audit trail
- Dashboard KPIs, rapports PDF/Excel
- Portails visiteur et locataire
- **Notifications in-app + file d'envoi email + WhatsApp (reçus via lien wa.me)**

## Structure

```
Gestion-Immobiliere/
├── backend/              # API FastAPI
├── frontend/             # Next.js
├── sprints/              # Plan sprint par sprint
├── docker-compose.yml    # Postgres dev
├── docker-compose.prod.yml
└── cahier_de_charge.md
```

## Plan de développement

Consultez [`sprints/README.md`](./sprints/README.md) — sprints 0 à 13.

## Licence

Projet personnel — tous droits réservés.
