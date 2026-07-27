# RAPPORT DE FONCTIONNALITÉS
## Application de Gestion Immobilière

---

## 1. INTRODUCTION

### 1.1 Objectif du document
Ce document présente l'ensemble des fonctionnalités de l'application de gestion immobilière. Il détaille les différents types de comptes utilisateurs, les modules de gestion, les processus de validation, et les rapports disponibles.

### 1.2 Présentation générale de la plateforme
La plateforme permet de gérer :
- Plusieurs immeubles, appartements et magasins
- Plusieurs membres de la famille et locataires
- Les loyers, dépenses, contrats et documents
- Les revenus de chaque propriétaire

Chaque utilisateur possède son propre compte avec des droits spécifiques.

---

## 2. LES DIFFÉRENTS TYPES DE COMPTES

### 2.1 Super Administrateur
Ce compte dispose de tous les pouvoirs. Il peut :
- Créer et supprimer des utilisateurs
- Ajouter des immeubles, magasins et appartements
- Attribuer un bien à un membre de la famille
- Consulter tous les paiements et dépenses
- Modifier les loyers
- Voir tous les documents
- Valider ou annuler un paiement
- Consulter les rapports financiers
- Changer les autorisations des autres utilisateurs
- Consulter l'historique des modifications

### 2.2 Administrateur Familial
Il peut gérer une partie ou la totalité du patrimoine selon l'autorisation reçue. Il peut :
- Enregistrer les locataires
- Ajouter les contrats
- Enregistrer les loyers
- Ajouter les dépenses
- Envoyer des reçus
- Consulter les impayés
- Suivre les réparations
- Produire des rapports

**Restriction :** Il ne peut pas supprimer définitivement les données importantes sans validation du super administrateur.

### 2.3 Compte Propriétaire ou Membre de la Famille
Chaque membre de la famille peut avoir un compte personnel créé par le superadmin. Il peut consulter :
- Les immeubles ou logements lui appartenant
- Les revenus de ses biens
- Les loyers encaissés
- Les impayés, dépenses et réparations
- Les documents liés à ses biens
- Son bénéfice mensuel ou annuel

**Accès :** Lecture seule, sans possibilité de modifier les informations.

### 2.4 Compte Gestionnaire
Le gestionnaire peut :
- Enregistrer les paiements
- Ajouter un nouveau locataire
- Signaler un impayé
- Ajouter une dépense
- Déclarer une réparation
- Envoyer un reçu
- Consulter les logements attribués

**Restriction :** Il ne voit pas les informations financières de toute la famille.

### 2.5 Compte Visiteur
Accès très limité, peut :
- Consulter les logements disponibles
- Voir les photos et le montant du loyer
- Voir la localisation générale
- Envoyer une demande de visite
- Contacter le gestionnaire

**Restriction :** Ne voit pas les noms des locataires, les revenus ou les informations privées.

### 2.6 Compte Locataire
Chaque locataire peut avoir son propre compte pour :
- Voir son logement
- Consulter son contrat et le montant du loyer
- Consulter son historique de paiement
- Télécharger ses reçus
- Voir les mois impayés
- Signaler une panne
- Envoyer un message au gestionnaire
- Télécharger un avis ou un document

---

## 3. TABLEAU DE BORD PROFESSIONNEL

Le tableau de bord présente automatiquement :

| Indicateur | Description |
|------------|-------------|
| 🏢 Nombre total d'immeubles | Total des biens immobiliers |
| 🏠 Nombre total d'appartements | Total des appartements |
| 🏪 Nombre total de magasins | Total des commerces |
| ✅ Logements occupés | Taux d'occupation |
| 📭 Logements libres | Disponibilités |
| 💰 Loyers attendus du mois | Revenus prévisionnels |
| 💵 Loyers encaissés | Revenus perçus |
| ⚠️ Montant des impayés | Créances |
| 📊 Dépenses du mois | Charges |
| 📈 Bénéfice net | Résultat |
| 📄 Contrats arrivant à expiration | Alertes |
| 🔧 Réparations en cours | Suivi |

Des graphiques mensuels et annuels sont également disponibles.

---

## 4. GESTION DES IMMEUBLES ET DES LOGEMENTS

### 4.1 Fiche de l'immeuble
Chaque immeuble dispose d'une fiche contenant :

| Champ | Description |
|-------|-------------|
| Code de l'immeuble | Identifiant unique |
| Nom | Dénomination |
| Adresse | Localisation complète |
| Commune / Quartier | Zone géographique |
| Photo | Image de l'immeuble |
| Nombre d'étages | Hauteur |
| Nombre d'appartements | Logements |
| Nombre de magasins | Commerces |
| Propriétaire | Membre de la famille |
| Gestionnaire responsable | Compte gestionnaire affecté |
| Documents de propriété | Actes, titres |
| Observations | Notes diverses |

### 4.2 Fiche du logement
Chaque logement possède :

| Champ | Description |
|-------|-------------|
| Code unique | Ex: KM001-A101, KM001-M01 |
| Type | Appartement, magasin, bureau |
| Numéro et étage | Localisation précise |
| Montant du loyer | Prix mensuel |
| Montant de la caution | Dépôt de garantie |
| État | Libre, occupé, réservé, en réparation |
| Photos | Visuels du logement |
| Locataire actuel | Personne occupant |
| Date d'entrée | Début de bail |
| Date de sortie | Fin de bail |
| Historique des anciens locataires | Traçabilité |

**Exemples de codes :**
- KM001-A101
- KM001-A102
- KM001-M01
- KM002-M03

---

## 5. GESTION DES LOCATAIRES

La fiche du locataire contient :

| Champ | Description |
|-------|-------------|
| Nom et prénom | Identité complète |
| Photo | Photo d'identité |
| Numéro de téléphone | Principal |
| Second numéro | Téléphone secondaire |
| Profession | Activité |
| Adresse précédente | Domicile antérieur |
| Type de pièce d'identité | CNI, Passeport, etc. |
| Numéro de la pièce | Référence |
| Copie de la pièce | Scan ou photo |
| Personne à contacter en urgence | Référent |
| Date d'entrée | Début de bail |
| Logement occupé | Référence du bien |
| Montant du loyer | Loyer en vigueur |
| Caution versée | Montant |
| Mode de paiement | Espèces, Orange Money, Wave, Virement |
| Contrat | Document lié |
| Historique des paiements | Suivi |
| Observations | Notes |

---

## 6. PAIEMENTS ET REÇUS

### 6.1 Fonctionnalités de paiement
Le système permet :
- Enregistrer un paiement en espèces
- Enregistrer un paiement Orange Money
- Enregistrer un paiement Wave
- Enregistrer un virement bancaire
- Enregistrer un paiement partiel
- Gérer plusieurs mois payés en une seule fois
- Ajouter une preuve de paiement

### 6.2 Gestion des reçus
- Génération automatique d'un reçu PDF
- Envoi du reçu par WhatsApp ou par email
- Attribution d'un numéro unique à chaque reçu
- Consultation de l'historique complet

### 6.3 Traçabilité
Chaque paiement indique :
- Qui l'a enregistré
- À quelle date

---

## 7. GESTION DES IMPAYÉS

### 7.1 Détection automatique
Le système détecte automatiquement les impayés et affiche :

| Information | Détail |
|-------------|--------|
| Mois non payé | Période concernée |
| Montant dû | Arriérés |
| Nombre de jours de retard | Délai |
| Total cumulé | Montant global |
| Nom du locataire | Débiteur |
| Logement concerné | Bien loué |
| Relances déjà envoyées | Historique des relances |

### 7.2 Notifications
Des notifications automatiques sont prévues :
- Avant l'échéance
- Après l'échéance

---

## 8. GESTION DES DÉPENSES

### 8.1 Classification
Les dépenses peuvent être classées par :
- Immeuble
- Logement
- Propriétaire
- Catégorie
- Date
- Fournisseur
- Montant
- Mode de paiement

### 8.2 Types de dépenses
| Catégorie | Exemples |
|-----------|----------|
| Réparation | Plomberie, électricité |
| Peinture | Rénovation |
| Plomberie | Canalisations |
| Électricité | Câblage, installations |
| Gardiennage | Sécurité |
| Nettoyage | Entretien |
| Taxes | Foncières, ordures |
| Fournitures | Matériel |
| Travaux | Gros œuvre |

### 8.3 Justificatifs
La facture ou le reçu doit pouvoir être joint en photo ou en PDF.

---

## 9. GESTION DES RÉPARATIONS

### 9.1 Déclaration
Le locataire ou le gestionnaire peut déclarer un problème. La demande contient :

| Information | Description |
|-------------|-------------|
| Logement concerné | Référence du bien |
| Description | Explication du problème |
| Photo ou vidéo | Preuve visuelle |
| Niveau d'urgence | Faible, moyen, élevé |
| Date de déclaration | Date du signalement |
| Personne responsable | Gestionnaire affecté |
| Coût estimé | Devis |
| Coût final | Facture |
| Statut | État de l'intervention |

### 9.2 Statuts possibles
- 📝 Nouvelle demande
- 🔍 En cours d'analyse
- 🔧 Technicien affecté
- 🛠️ Réparation en cours
- ✅ Terminée
- ❌ Annulée

---

## 10. GESTION DES CONTRATS ET DOCUMENTS

### 10.1 Types de documents
La plateforme conserve :

| Document | Description |
|----------|-------------|
| Contrats de location | Baux |
| Pièces d'identité | CNI, passeports |
| Reçus | Quittances |
| Preuves de paiement | Justificatifs |
| États des lieux | Entrée/sortie |
| Photos des logements | Visuels |
| Factures de travaux | Justificatifs |
| Documents de propriété | Actes notariés |
| Lettres de préavis | Résiliations |
| Avertissements | Communications |

### 10.2 Actions disponibles
- Télécharger
- Imprimer
- Partager

---

## 11. VALIDATION DES OPÉRATIONS IMPORTANTES

### 11.1 Actions nécessitant une validation
Pour éviter les erreurs ou les conflits, certaines actions nécessitent une validation :

| Action | Niveau de validation |
|--------|---------------------|
| Suppression d'un paiement | Super Admin |
| Modification d'un montant encaissé | Super Admin |
| Suppression d'un locataire | Super Admin |
| Changement de propriétaire | Super Admin |
| Modification d'un contrat | Super Admin |
| Ajout d'une dépense importante | Super Admin |
| Annulation d'un reçu | Super Admin |

### 11.2 Traçabilité
Le système conserve :
- L'ancienne valeur
- La nouvelle valeur
- La date et heure
- L'utilisateur ayant effectué l'opération

---

## 12. HISTORIQUE ET TRACABILITÉ

### 12.1 Suivi des actions
Toutes les actions sont enregistrées :

| Information enregistrée | Exemple |
|-------------------------|---------|
| Qui a ajouté le paiement | Gestionnaire X |
| Qui a modifié le loyer | Administrateur Y |
| Qui a supprimé un document | Super Admin Z |
| Date et heure de l'action | 26/07/2026 14:30 |
| Ancienne information | 250 000 FCFA |
| Nouvelle information | 275 000 FCFA |

### 12.2 Utilité
Cela permet d'éviter les contestations entre les gestionnaires ou les membres de la famille.

---

## 13. NOTIFICATIONS

### 13.1 Événements notifiés
La plateforme envoie des notifications pour :

| Événement | Description |
|-----------|-------------|
| Loyer bientôt exigible | Rappel avant la date |
| Loyer en retard | Alerte impayé |
| Contrat bientôt expiré | Fin de bail |
| Nouvelle demande de réparation | Signalement |
| Paiement enregistré | Confirmation |
| Reçu disponible | Disponible |
| Dépense ajoutée | Nouvelle charge |
| Nouveau document | Ajout |
| Logement devenu disponible | Libre |

### 13.2 Modes de notification
- Dans l'application
- Par email

---

## 14. RAPPORTS AUTOMATIQUES

### 14.1 Types de rapports

| Périodicité | Description |
|-------------|-------------|
| Journalier | Activité du jour |
| Hebdomadaire | Résumé semaine |
| Mensuel | Bilan du mois |
| Annuel | Rapport annuel |

### 14.2 Filtres disponibles

| Filtre | Description |
|--------|-------------|
| Par immeuble | Rapport par bâtiment |
| Par propriétaire | Rapport par membre |
| Par locataire | Suivi individuel |
| Par gestionnaire | Performance |
| Par type de logement | Catégorie |

### 14.3 Exportation
Les rapports peuvent être exportés en :
- **PDF** pour l'archivage
- **Excel** pour l'analyse

---

## 15. ANNEXES

### 15.1 Récapitulatif des permissions par type de compte

| Fonctionnalité | Super Admin | Admin Familial | Propriétaire | Gestionnaire | Visiteur | Locataire |
|----------------|:-----------:|:--------------:|:------------:|:------------:|:--------:|:---------:|
| Gérer utilisateurs | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Gérer immeubles | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Gérer logements | ✅ | ✅ | Lecture | ❌ | ❌ | Lecture |
| Gérer locataires | ✅ | ✅ | Lecture | ✅ | ❌ | Lecture |
| Gérer paiements | ✅ | ✅ | Lecture | ✅ | ❌ | Lecture |
| Gérer dépenses | ✅ | ✅ | Lecture | ✅ | ❌ | ❌ |
| Gérer réparations | ✅ | ✅ | Lecture | ✅ | ❌ | ✅ |
| Consulter rapports | ✅ | ✅ | Lecture | ❌ | ❌ | ❌ |
| Notifications | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |

---

**Document confidentiel - Tous droits réservés**  
*Dernière mise à jour : 26 juillet 2026*