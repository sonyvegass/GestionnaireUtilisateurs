# Système de Gestion des Utilisateurs Hospitaliers
## Documentation Technique Détaillée

### 1. Introduction

Ce système est une application de gestion des utilisateurs pour un réseau hospitalier, permettant une administration hiérarchique des accès selon les régions. L'application est développée en Python et utilise une base de données MySQL pour la persistance des données.

### 2. Architecture du Système

#### 2.1 Structure de la Base de Données

Le système utilise trois tables principales :

1. **utilisateurs**
   - Identifiants uniques (id, login)
   - Informations personnelles (nom, prénom)
   - Rôle (super_admin, admin, utilisateur)
   - Région d'affectation
   - Mot de passe hashé
   - Informations de création et d'expiration du mot de passe
   - Horodatage des modifications

2. **sessions**
   - Gestion des sessions utilisateurs
   - Tokens de session uniques
   - Dates d'expiration
   - Liaison avec la table utilisateurs

3. **tentatives_connexion**
   - Suivi des tentatives de connexion
   - Mécanisme anti-bruteforce : limité à 2 tentatives de connexion
   - Verrouillage temporaire après échecs

#### 2.2 Hiérarchie des Rôles

Le système implémente une hiérarchie à trois niveaux :

1. **Super Administrateur**
   - Dès lors où on lance le script, un super admin est créé automatiquement si celui-ci n'existe pas encore.
   - On se connecte avec les identifiants de ce super admin.
   - Création des administrateurs régionaux : une option est disponible pour créer automatiquement les 4 administrateurs principaux (option 6 du menu super admin)
   - Il n'existe aucun moyen de créer un second super admin : Aucun administrateur ni utilisateur standard ne peut créer un super admin
   - Le super admin gére les administrateurs + les utilisateurs standards
   - Les administrateurs gérent les utilisateurs standards de leur propres région seulement
   - Gestion globale du système : le super admin peut tout faire.
   - Création de nouvelles régions : le super admin peut créer de nouvelles régions dans le cas où le réseau hospotalier envisage d'inaugurer de nouveaux sites (Lyon, Montpellier...)

2. **Administrateurs Régionaux**
   - Gestion des utilisateurs de leur région
   - Droits limités à leur zone géographique

3. **Utilisateurs Standard**
   - Accès aux fonctionnalités de base
   - Restrictions selon leur région


Finalement, on peut se connecter en tant que :
   - Super Admin ou administrateur régional
   - Chacun des deux roles dispose de son propre menu (actions possibles)

### 3. Fonctionnalités Principales

#### 3.1 Gestion des Utilisateurs

##### a) Création d'Utilisateurs
- Vérification des droits selon la hiérarchie
- Génération automatique des identifiants
- Création de mots de passe sécurisés + hash
- Attribution des rôles et régions
- Validation des données saisies

##### b) Modification d'Utilisateurs
- Modification des informations personnelles
- Changement de rôle (avec restrictions)
- Changement de région
- Vérification des autorisations

##### c) Suppression d'Utilisateurs
- Contrôles de sécurité
- Vérification des permissions
- Protection des comptes critiques

##### d) Consultation des Utilisateurs
- Filtrage par rôle et région
- Affichage structuré des informations
- Respect des restrictions d'accès

#### 3.2 Gestion des Régions

##### a) Administration Régionale
- Ajout de nouvelles régions
- Suppression de régions (avec contrôles)
- Transfert d'utilisateurs entre régions
- Statistiques par région

##### b) Contrôles Régionaux
- Validation des noms de région
- Vérification des dépendances
- Protection de la région principale

#### 3.3 Sécurité et Authentification

##### a) Gestion des Sessions
- Création de sessions sécurisées
- Tokens uniques
- Expiration automatique
- Validation continue

##### b) Sécurité des Mots de Passe
- Hashage SHA-256
- Génération sécurisée
- Politique d'expiration
- Réinitialisation contrôlée

##### c) Protection Contre les Attaques
- Limitation des tentatives de connexion à 2 
- Verrouillage temporaire des comptes
- Journalisation des tentatives

### 4. Validation et Contrôle des Données

#### 4.1 Système de Validation
- Validation des noms et prénoms
- Contrôle des rôles
- Vérification des régions
- Validation des dates

#### 4.2 Règles de Validation
- Longueur minimale et maximale
- Caractères autorisés
- Format des données
- Cohérence des informations

### 5. Tests et Qualité

#### 5.1 Tests Unitaires
- Tests des fonctionnalités principales
- Validation des contrôles d'accès
- Tests des cas limites
- Simulation des erreurs

#### 5.2 Couverture des Tests
- Authentification
- Gestion des sessions
- Opérations CRUD
- Validations de données

### 6. Interface Utilisateur

#### 6.1 Menu Principal
- Interface en ligne de commande
- Navigation intuitive
- Adaptations selon les rôles
- Messages d'erreur clairs

#### 6.2 Retours Utilisateur
- Émojis pour la clarté
- Messages d'erreur explicites
- Confirmations d'actions
- Guides utilisateur

### 7. Aspects Techniques

#### 7.1 Structure du Code
- Organisation modulaire
- Séparation des responsabilités
- Réutilisation du code

#### 7.2 Gestion des Erreurs
- Capture structurée
- Messages explicites
- Rollback des opérations
- Journalisation

### 8. Évolutivité et Maintenance

#### 8.1 Points d'Extension
- Ajout de nouveaux rôles
- Extension des régions
- Nouvelles fonctionnalités
- Personnalisation des règles

#### 8.2 Maintenance
- Code documenté
- Tests automatisés
- Structure modulaire
- Gestion des dépendances

### 9. Conclusion

Ce système offre une solution complète et sécurisée pour la gestion des utilisateurs dans un contexte hospitalier multi-régional. Sa structure modulaire, ses mécanismes de sécurité et sa couverture de tests en font une base solide pour les besoins de gestion d'accès dans un environnement médical.
