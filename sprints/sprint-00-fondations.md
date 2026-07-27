# Sprint 0 — Fondations & environnement

**Durée estimée :** 1 semaine  
**Prérequis :** Aucun  
**Dépendances pour le sprint suivant :** Sprint 1

---

## Objectif

Mettre en place l'infrastructure de développement, la structure du monorepo, la base de données, Docker, et les conventions de code pour Next.js et FastAPI.

---

## User stories

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S0-01 | Développeur | Un monorepo structuré backend/frontend | Travailler de façon organisée |
| S0-02 | Développeur | Docker Compose pour PostgreSQL | Démarrer la BDD en une commande |
| S0-03 | Développeur | CI locale (lint, format) | Garantir la qualité du code |
| S0-04 | Développeur | Documentation de setup | Onboarder rapidement |

---

## Livrables

- [ ] Repo Git initialisé avec `.gitignore`
- [ ] Backend FastAPI fonctionnel (`GET /health`)
- [ ] Frontend Next.js fonctionnel (page d'accueil)
- [ ] PostgreSQL via Docker Compose
- [ ] Alembic configuré (migrations prêtes)
- [ ] Variables d'environnement documentées
- [ ] README racine avec instructions de démarrage

---

## Tâches Backend (FastAPI)

### Structure à créer

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── config.py       # Settings via pydantic-settings
│   │   ├── database.py     # Session SQLAlchemy
│   │   └── security.py     # Placeholder JWT (Sprint 1)
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── router.py
│   ├── models/
│   │   └── base.py         # Base declarative SQLAlchemy
│   └── schemas/
│       └── common.py       # Réponses génériques
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   └── test_health.py
├── requirements.txt
└── .env.example
```

### Dépendances Python (`requirements.txt`)

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.0
alembic>=1.13.0
psycopg2-binary>=2.9.9
pydantic>=2.6.0
pydantic-settings>=2.2.0
python-dotenv>=1.0.0
python-multipart>=0.0.9
httpx>=0.27.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

### Configuration (`core/config.py`)

Variables d'environnement :

| Variable | Description | Exemple |
|----------|-------------|---------|
| `DATABASE_URL` | Connexion PostgreSQL | `postgresql://user:pass@localhost:5432/gestion_immo` |
| `SECRET_KEY` | Clé JWT | chaîne aléatoire 32+ chars |
| `CORS_ORIGINS` | Origines autorisées | `http://localhost:3000` |
| `ENVIRONMENT` | dev / staging / prod | `dev` |

### Endpoint à implémenter

| Méthode | Route | Description | Réponse |
|---------|-------|-------------|---------|
| GET | `/health` | Santé de l'API | `{ "status": "ok", "version": "0.1.0" }` |
| GET | `/api/v1/` | Info API | `{ "message": "Gestion Immobilière API" }` |

### CORS

- Autoriser `http://localhost:3000` en développement
- Configurer via `CORSMiddleware`

---

## Tâches Frontend (Next.js)

### Structure à créer

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── components/
│   └── ui/                 # shadcn/ui (installé)
├── lib/
│   ├── api.ts              # Client HTTP vers FastAPI
│   └── utils.ts
├── .env.local.example
├── package.json
├── tailwind.config.ts
└── tsconfig.json
```

### Commandes d'initialisation

```bash
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir=false
npx shadcn@latest init
```

### Page d'accueil (`app/page.tsx`)

- Titre : « Gestion Immobilière »
- Bouton « Connexion » (lien vers `/login` — page vide pour Sprint 1)
- Appel test à `GET /health` et affichage du statut API

### Client API (`lib/api.ts`)

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchHealth() {
  const res = await fetch(`${API_URL}/health`);
  return res.json();
}
```

### Variables d'environnement

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | URL du backend FastAPI |

---

## Docker Compose

Fichier `docker-compose.yml` à la racine :

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: gestion_immo
      POSTGRES_PASSWORD: gestion_immo
      POSTGRES_DB: gestion_immo
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Optionnel Sprint 0 : service `minio` pour stockage S3-compatible (utile dès Sprint 9).

---

## Alembic

```bash
cd backend
alembic init alembic
# Configurer alembic.ini et env.py avec DATABASE_URL
alembic revision --autogenerate -m "initial"
# Ne pas créer de tables métier encore — Sprint 1+
```

---

## Conventions à établir

| Sujet | Convention |
|-------|------------|
| Branches Git | `main`, `develop`, `feature/sprint-XX-description` |
| Commits | Conventional Commits (`feat:`, `fix:`, `chore:`) |
| Langue code | Anglais (noms variables, routes API) |
| Langue UI | Français |
| Format dates API | ISO 8601 (`2026-07-26T14:30:00Z`) |
| Devise | FCFA (affichage frontend, pas de conversion) |
| IDs | UUID v4 en base de données |

---

## Tests

| Test | Fichier | Assertion |
|------|---------|-----------|
| Health check | `tests/test_health.py` | Status 200, `status == "ok"` |

---

## Critères d'acceptation

- [ ] `docker compose up -d` démarre PostgreSQL sans erreur
- [ ] `uvicorn app.main:app --reload` démarre le backend sur `:8000`
- [ ] `npm run dev` démarre le frontend sur `:3000`
- [ ] La page d'accueil affiche le statut « API connectée »
- [ ] Swagger UI accessible sur `http://localhost:8000/docs`
- [ ] Alembic peut exécuter `upgrade head` sans erreur
- [ ] `.env.example` présent pour backend et frontend (sans secrets réels)

---

## Notes pour le sprint suivant

Le Sprint 1 ajoutera les modèles `User` et `Role`, l'authentification JWT, et les middlewares de permissions.
