# Gestion Immobilière

Application web de gestion immobilière — **Next.js** (frontend) + **FastAPI** (backend) + **PostgreSQL**.

## Prérequis

- [Node.js](https://nodejs.org/) 20+
- [Python](https://www.python.org/) 3.11+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (pour PostgreSQL)

## Démarrage rapide

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

# Migrations
alembic upgrade head

# Lancer l'API
uvicorn app.main:app --reload
```

API disponible sur : http://localhost:8000  
Documentation Swagger : http://localhost:8000/docs

**Compte super admin (après migration) :**
- Email : `admin@gestion-immo.local`
- Mot de passe : `Admin123!` (modifiable via `SUPER_ADMIN_PASSWORD`)

### 3. Frontend (Next.js)

```bash
cd frontend
npm install
copy .env.local.example .env.local

npm run dev
```

Application disponible sur : http://localhost:3000

## Variables d'environnement

### Backend (`backend/.env`)

| Variable | Description | Exemple |
|----------|-------------|---------|
| `DATABASE_URL` | Connexion PostgreSQL | `postgresql://gestion_immo:gestion_immo@localhost:5432/gestion_immo` |
| `SECRET_KEY` | Clé secrète JWT | chaîne aléatoire 32+ caractères |
| `CORS_ORIGINS` | Origines autorisées | `http://localhost:3000` |
| `ENVIRONMENT` | Environnement | `dev` |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | URL du backend (`http://localhost:8000`) |

## Tests

```bash
cd backend
pytest
```

## Structure du projet

```
Gestion-Immobiliere/
├── backend/          # API FastAPI
├── frontend/         # Application Next.js
├── sprints/          # Plan de développement par sprint
├── docker-compose.yml
└── cahier_de_charge.md
```

## Plan de développement

Consultez le dossier [`sprints/`](./sprints/README.md) pour le plan détaillé sprint par sprint.

- **Sprint 0** ✅ Fondations
- **Sprint 1** ✅ Authentification & rôles
- **Sprint 2** ✅ Gestion des utilisateurs
- **Sprint 3** — Immeubles & logements
- …

## Conventions

| Sujet | Convention |
|-------|------------|
| Code | Anglais (variables, routes API) |
| Interface | Français |
| Commits | [Conventional Commits](https://www.conventionalcommits.org/) |
| Devise | FCFA |

## Licence

Projet personnel — tous droits réservés.
