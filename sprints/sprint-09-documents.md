# Sprint 9 — Contrats & documents

**Durée estimée :** 1 à 2 semaines  
**Prérequis :** Sprint 8  
**Dépendances pour le sprint suivant :** Sprint 10

---

## Objectif

Centraliser tous les documents de la plateforme (contrats, pièces d'identité, reçus, états des lieux, factures, etc.), avec upload, téléchargement, impression, partage, et organisation par entité liée.

---

## User stories

| ID | En tant que… | Je veux… | Afin de… |
|----|--------------|----------|----------|
| S9-01 | Admin Familial | Uploader un contrat de location | Archiver le bail |
| S9-02 | Admin Familial | Joindre un état des lieux | Documenter l'entrée/sortie |
| S9-03 | Super Admin | Voir tous les documents | Superviser l'archivage |
| S9-04 | Propriétaire | Consulter les documents de mes biens | Accéder à mes actes |
| S9-05 | Locataire | Télécharger mon contrat et mes documents | Avoir mes papiers |
| S9-06 | Utilisateur | Imprimer ou partager un document | Diffuser un justificatif |

---

## Modèles de données

### Table `document_types`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| code | VARCHAR(50) | UNIQUE |
| label | VARCHAR(100) | NOT NULL |

**Seed types (cahier des charges) :**

| code | label |
|------|-------|
| `lease_contract` | Contrat de location |
| `id_document` | Pièce d'identité |
| `receipt` | Reçu / Quittance |
| `payment_proof` | Preuve de paiement |
| `inventory_in` | État des lieux entrée |
| `inventory_out` | État des lieux sortie |
| `unit_photo` | Photo logement |
| `work_invoice` | Facture travaux |
| `property_deed` | Document de propriété |
| `notice_letter` | Lettre de préavis |
| `warning` | Avertissement |
| `other` | Autre |

### Table `documents`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| document_type_id | UUID | FK → document_types.id |
| title | VARCHAR(300) | NOT NULL |
| description | TEXT | nullable |
| file_url | VARCHAR(500) | NOT NULL |
| file_name | VARCHAR(255) | NOT NULL |
| file_size | INTEGER | NOT NULL — bytes |
| mime_type | VARCHAR(100) | NOT NULL |
| entity_type | ENUM | voir ci-dessous |
| entity_id | UUID | NOT NULL |
| uploaded_by | UUID | FK → users.id |
| uploaded_at | TIMESTAMPTZ | NOT NULL |
| is_archived | BOOLEAN | DEFAULT false |
| expires_at | DATE | nullable |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

### Enum `EntityType`

| Valeur | Description |
|--------|-------------|
| `building` | Immeuble |
| `unit` | Logement |
| `tenant` | Locataire |
| `lease` | Bail |
| `payment` | Paiement |
| `expense` | Dépense |
| `repair` | Réparation |
| `owner_profile` | Propriétaire |
| `receipt` | Reçu |

### Table `document_shares` (liens de partage temporaires)

| Colonne | Type | Contraintes |
|---------|------|-------------|
| id | UUID | PK |
| document_id | UUID | FK → documents.id |
| share_token | VARCHAR(64) | UNIQUE |
| expires_at | TIMESTAMPTZ | NOT NULL |
| created_by | UUID | FK → users.id |
| accessed_count | INTEGER | DEFAULT 0 |
| max_access | INTEGER | DEFAULT 10 |
| created_at | TIMESTAMPTZ | NOT NULL |

---

## Stockage fichiers

### Dev
- Dossier local `uploads/{entity_type}/{entity_id}/`
- Servir via endpoint proxy authentifié

### Prod
- **MinIO** ou **AWS S3**
- Bucket : `gestion-immo-documents`
- URLs signées (expiration 1h pour download)

### Limites

| Règle | Valeur |
|-------|--------|
| Taille max fichier | 10 Mo |
| Types acceptés | PDF, JPG, PNG, WEBP, MP4 (vidéos réparations) |
| Nom fichier | Sanitisé, UUID prefix |

---

## Endpoints API

| Méthode | Route | Rôle | Description |
|---------|-------|------|-------------|
| GET | `/api/v1/documents` | * filtré | Liste documents |
| POST | `/api/v1/documents` | admin+, gestionnaire | Upload document |
| GET | `/api/v1/documents/{id}` | * filtré | Métadonnées |
| GET | `/api/v1/documents/{id}/download` | * filtré | Télécharger fichier |
| GET | `/api/v1/documents/{id}/preview` | * filtré | Preview (PDF/image) |
| PATCH | `/api/v1/documents/{id}` | admin+ | Modifier titre/description |
| DELETE | `/api/v1/documents/{id}` | super_admin | Supprimer (→ Sprint 10) |
| POST | `/api/v1/documents/{id}/share` | admin+, gestionnaire | Créer lien partage |
| GET | `/api/v1/documents/shared/{token}` | Non (token) | Accès via lien partage |
| GET | `/api/v1/document-types` | auth | Types documents |

### Endpoints par entité (raccourcis)

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/v1/buildings/{id}/documents` | Documents immeuble |
| GET | `/api/v1/units/{id}/documents` | Documents logement |
| GET | `/api/v1/tenants/{id}/documents` | Documents locataire |
| GET | `/api/v1/leases/{id}/documents` | Documents bail |

### POST `/api/v1/documents` — Multipart

```
document_type_id: uuid
title: "Contrat bail KM001-A101"
description: "Bail signé Aminata Traoré"
entity_type: "lease"
entity_id: uuid
file: [binary]
```

### Filtres GET `/api/v1/documents`

| Param | Description |
|-------|-------------|
| `entity_type` + `entity_id` | Par entité liée |
| `document_type_id` | Par type |
| `building_id` | Tous docs d'un immeuble |
| `search` | Titre, description |
| `date_from` / `date_to` | Période upload |
| `is_archived` | Archivés ou actifs |

---

## Migration documents existants

Consolider les uploads des sprints précédents :

| Sprint | Champ existant | → document |
|--------|----------------|------------|
| 3 | `buildings.photo_url`, `unit_photos` | Migrer ou référencer |
| 4 | `tenants.id_document_url`, `leases.contract_document_url` | Migrer |
| 5 | `payments.proof_url`, `receipts.pdf_url` | Migrer |
| 7 | `expenses.receipt_url` | Migrer |
| 8 | `repair_attachments` | Migrer |

**Stratégie :** Garder champs existants + créer entrée `documents` en parallèle (double write) OU migration one-shot.

---

## Tâches Backend

- [ ] Modèles `DocumentType`, `Document`, `DocumentShare`
- [ ] Migration + seed types
- [ ] Service stockage abstrait (`StorageService` — local/S3)
- [ ] Upload multipart avec validation mime/size
- [ ] Download avec URL signée
- [ ] Preview PDF (Content-Disposition inline)
- [ ] Partage temporaire avec token
- [ ] Endpoints par entité
- [ ] RBAC strict par entité liée
- [ ] Script migration docs existants
- [ ] Tests upload/download/share/RBAC

---

## Tâches Frontend

### Pages

| Route | Rôle | Description |
|-------|------|-------------|
| `/dashboard/documents` | admin+, gestionnaire | Bibliothèque centrale |
| `/dashboard/documents/[id]` | * filtré | Détail + preview |
| `/documents/shared/[token]` | Public (token) | Accès document partagé |

### Composants réutilisables

- [ ] `DocumentLibrary` — grille/liste documents (intégrable dans fiches immeuble, locataire, bail…)
- [ ] `DocumentUploader` — drag & drop avec sélection type
- [ ] `DocumentPreview` — viewer PDF (react-pdf) + images
- [ ] `DocumentCard` — icône type, titre, date, taille
- [ ] `ShareDocumentModal` — générer lien, définir expiration
- [ ] `PrintButton` — window.print() sur preview
- [ ] `DownloadButton`
- [ ] `DocumentTypeIcon` — icône par type
- [ ] `DocumentFilters` — type, date, entité

### Intégration dans fiches existantes

Ajouter onglet « Documents » dans :
- Fiche immeuble (`/dashboard/immeubles/[id]`)
- Fiche logement (`/dashboard/logements/[id]`)
- Fiche locataire (`/dashboard/locataires/[id]`)
- Fiche bail (`/dashboard/baux/[id]`)
- Espace locataire (Sprint 12)

---

## Règles métier

1. Visiteur : aucun accès documents.
2. Locataire : documents de son bail, ses reçus, son contrat uniquement.
3. Propriétaire : documents de ses biens (actes, factures travaux).
4. Gestionnaire : documents des immeubles assignés.
5. Suppression document → validation super admin (Sprint 10).
6. Lien partage expire après 7 jours (configurable) ou max accès atteint.

---

## Critères d'acceptation

- [ ] Upload PDF/image fonctionne pour tous types du cahier des charges
- [ ] Bibliothèque centrale avec filtres
- [ ] Preview PDF et image in-browser
- [ ] Téléchargement et impression fonctionnels
- [ ] Partage via lien temporaire
- [ ] Onglet Documents intégré dans fiches immeuble, locataire, bail
- [ ] Locataire accède à son contrat et ses reçus
- [ ] RBAC respecté sur tous endpoints
- [ ] Tests backend passent

---

## Docker Compose (ajout MinIO)

```yaml
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
```
