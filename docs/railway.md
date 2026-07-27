# Déploiement Railway — Gestion Immobilière

Guide pas à pas pour déployer **backend FastAPI**, **frontend Next.js** et **PostgreSQL** sur [Railway](https://railway.com).

## Architecture recommandée

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│     Backend     │────▶│   PostgreSQL    │
│  (Next.js)      │     │   (FastAPI)     │     │   (Railway)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

Créez **3 services** dans un même projet Railway (ou 2 si le frontend reste en local / Vercel).

---

## 1. Créer le projet Railway

1. Connectez votre repo GitHub `Gestion-Immobiliere`
2. **New Project** → **Deploy from GitHub repo**

---

## 2. Base PostgreSQL

1. Dans le projet : **+ New** → **Database** → **PostgreSQL**
2. Railway injecte automatiquement `DATABASE_URL` dans les services liés

> Liez Postgres au service **backend** : service backend → **Variables** → **Add Reference** → `DATABASE_URL` depuis Postgres.

---

## 3. Service Backend (API)

### Configuration du service

| Paramètre | Valeur |
|-----------|--------|
| **Root Directory** | `backend` |
| **Builder** | Dockerfile (via `railway.toml`) |

Le script `start.sh` exécute `alembic upgrade head` puis démarre l’API sur le port Railway (`PORT`).

### Variables d'environnement

| Variable | Obligatoire | Exemple / note |
|----------|-------------|----------------|
| `DATABASE_URL` | ✅ | Référence Railway Postgres (auto) |
| `SECRET_KEY` | ✅ | Chaîne aléatoire 32+ caractères |
| `CORS_ORIGINS` | ✅ | URL du frontend (voir ci-dessous) |
| `ENVIRONMENT` | ✅ | `production` |
| `PUBLIC_API_URL` | ✅ | URL publique du backend, ex. `https://gestion-immo-api.up.railway.app` |
| `SUPER_ADMIN_EMAIL` | ✅ | Email admin prod |
| `SUPER_ADMIN_PASSWORD` | ✅ | Mot de passe fort (utilisé à la 1ère migration) |
| `ENABLE_SCHEDULER` | | `true` (emails + rappels) |
| `SMTP_HOST` | | Optionnel |
| `SMTP_PORT` | | `587` |
| `SMTP_USERNAME` | | Optionnel |
| `SMTP_PASSWORD` | | Optionnel |
| `SMTP_FROM_EMAIL` | | Optionnel |

**CORS_ORIGINS** — séparez plusieurs origines par des virgules :

```
https://votre-frontend.up.railway.app,https://www.votredomaine.com
```

### Volume pour les uploads (recommandé)

Les fichiers uploadés (PDF reçus, documents) sont stockés dans `uploads/`. Sans volume, ils sont **effacés à chaque redéploiement**.

1. Service backend → **Settings** → **Volumes**
2. Mount path : `/app/uploads`

### Vérification

- Health : `https://VOTRE-BACKEND.up.railway.app/health`
- Swagger : `https://VOTRE-BACKEND.up.railway.app/docs`

Compte admin créé lors de la migration `002_auth` avec `SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_PASSWORD`.

---

## 4. Service Frontend (Next.js)

### Configuration du service

| Paramètre | Valeur |
|-----------|--------|
| **Root Directory** | `frontend` |
| **Builder** | Dockerfile |

### Variables d'environnement

| Variable | Obligatoire | Note |
|----------|-------------|------|
| `NEXT_PUBLIC_API_URL` | ✅ | URL publique du **backend** (sans slash final) |

Exemple :

```
NEXT_PUBLIC_API_URL=https://gestion-immo-api.up.railway.app
```

> Cette variable est lue **au build**. Après changement, forcez un **Redeploy**.

### Domaine public

Générez un domaine Railway pour le frontend, puis mettez à jour `CORS_ORIGINS` sur le backend avec cette URL.

---

## 5. Ordre de déploiement

1. PostgreSQL
2. Backend (attendre que `/health` réponde)
3. Copier l’URL backend → `NEXT_PUBLIC_API_URL` sur le frontend
4. Frontend
5. Copier l’URL frontend → `CORS_ORIGINS` sur le backend
6. Redéployer backend si CORS a changé

---

## 6. Checklist post-déploiement

- [ ] `GET /health` → `{"status":"ok"}`
- [ ] Login admin avec `SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_PASSWORD`
- [ ] Dashboard accessible depuis le frontend
- [ ] Annonces publiques (`/annonces`) sans auth
- [ ] Volume `/app/uploads` monté (si documents/reçus en prod)
- [ ] `SECRET_KEY` et mots de passe **jamais** commités

---

## 7. Dépannage

| Problème | Cause probable | Solution |
|----------|----------------|----------|
| Erreur CORS | `CORS_ORIGINS` incorrect | URL exacte du frontend, sans `/` final |
| 502 au démarrage | Migrations lentes | Augmenter healthcheck timeout (déjà 120s) |
| Login impossible | Mauvais admin | Vérifier variables avant 1er deploy |
| Fichiers perdus | Pas de volume | Monter volume sur `/app/uploads` |
| Frontend appelle localhost | Build sans bonne URL | Redéployer frontend avec `NEXT_PUBLIC_API_URL` |

---

## Alternative : backend seul sur Railway

Si le frontend reste sur **Vercel** ou en local :

- Déployez uniquement Postgres + backend sur Railway
- `CORS_ORIGINS` = URL Vercel ou `http://localhost:3000`
- `NEXT_PUBLIC_API_URL` = URL Railway backend
