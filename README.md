# DataScope Studio — version 3

Application Python/Streamlit, données et modèles analytiques, comptes locaux et thème par utilisateur.

## Installation sur Arch Linux
Dans le dossier extrait `analyse_data` :
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage_users.py votre_identifiant
python -m streamlit run app.py
```
La création de compte demande un mot de passe de 12 caractères minimum, saisi de manière masquée. Aucun compte ou mot de passe n’est préconfiguré. Utiliser un mot de passe long, unique. Le formulaire de login apparaît avant tout accès aux imports et analyses.

## Version 3 : interface
- En-tête dans une carte, quatre cartes-boutons : Analyse, Tableaux de bord, Prédiction, Studio code.
- Survol animé, ombre, bordure et état actif ; focus clavier et prise en compte de prefers-reduced-motion.
- Sous-navigation Analyse : descriptive, inférentielle, préparation/jointures ; Prédiction : modèles et séries temporelles.
- Sélecteur Light/Dark dans Mon compte. Préférence enregistrée en SQLite et rechargée à la connexion. Graphiques Plotly et histogramme Matplotlib adaptés au thème ; certaines surfaces natives Streamlit, dont les grilles de données, peuvent conserver des couleurs claires. CSS dépendant de la structure Streamlit : à revalider lors des mises à jour.
- Inter pour le texte et Manrope pour les titres, chargées depuis Google Fonts. Connexion Internet nécessaire pour ces polices, fallback sans-serif hors ligne. Le navigateur effectue des requêtes à Google : pour un usage strictement privé, supprimer @import dans ui.py et utiliser des polices locales.

## Comptes et données
- Mots de passe hachés Argon2id via argon2-cffi ; aucune conservation en clair.
- Compte créé depuis le terminal administrateur, pas d’inscription publique.
- Limite : cinq tentatives par identifiant pendant quinze minutes. Ce n’est pas une limitation globale ni par IP ; cela ne protège pas d’une attaque distribuée ou par identifiants variables. Une personne peut aussi temporairement bloquer un compte en multipliant les erreurs.
- Session Streamlit authentifiée, expiration après 30 minutes sans interaction, vérifiée à la prochaine interaction. Rechargement/déconnexion peut nécessiter de se reconnecter. Aucun cookie de connexion persistante personnalisé.
- Déconnexion : purge des variables de session, des données importées et des modèles de cet utilisateur. Pas de cache global des fichiers importés dans cette version.
- Préférences/comptes persistants : base créée dans private/users.sqlite3, hors Git et hors archive distribuée. Le dossier doit être stocké sur un volume persistant au déploiement. Option DATASCOPE_AUTH_DB pour choisir un autre emplacement. Restreindre les accès et sauvegarder la base de façon sécurisée.
- Les données analytiques sont séparées par session et restent en mémoire ; elles ne sont pas enregistrées dans la base des comptes.
- Réinitialiser un mot de passe :
```bash
python manage_users.py votre_identifiant --reset-password
```
La réinitialisation n’invalide pas immédiatement les sessions existantes : arrêter/redémarrer le serveur pour les terminer. Pas de MFA, de récupération email, de permissions par rôle ou de fédération OIDC.

## Sécurité avant exposition publique
Cette authentification locale est un prototype, pas un audit de sécurité. HTTPS, proxy avec contrôle et limitation des requêtes, politiques de sauvegarde/rétention, mises à jour, protection de la base et audit sont nécessaires avant exposition publique. Ne pas utiliser le studio de code comme service d’exécution public : il n’a ni quotas CPU/mémoire ni isolation par processus. Importer seulement des documents de confiance.

## Tests
Depuis analyse_data :
```bash
python smoke_test.py
python test_v2.py
python test_v3.py
```
Le dernier test crée des comptes temporaires hors du stockage réel et teste connexion, blocage, préférence, navigation et purge à la déconnexion. Les tests automatisés ne vérifient pas pixel par pixel les effets de survol ou l’apparence dans tous les navigateurs.

## Documentation des fonctions analytiques (historique v1/v2)
Les remarques d’authentification et de cache des versions précédentes sont remplacées par celles de la version 3 ci-dessus.

# DataScope — site d’analyse de données

Application Python en français. Python 3.11 ou 3.12 recommandé.

## Installation et lancement
Depuis le dossier extrait :

```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell : .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Ouvrir l’adresse locale indiquée dans le terminal, normalement localhost:8501.

## Fonctionnalités
- CSV avec séparateur/encodage paramétrables, Excel XLSX avec sélection de feuille.
- Données synthétiques accessibles immédiatement.
- Statistiques descriptives, qualité, doublons, valeurs atypiques IQR.
- Sélection, renommage, conversion, filtres, tri, valeurs manquantes, groupby, pivot, concaténation et jointures validées.
- Plotly : histogrammes, boîtes, nuages, barres, courbes, corrélations. Matplotlib et export PNG.
- SciPy : Welch, Mann–Whitney, ANOVA, Kruskal–Wallis, Pearson, Spearman, khi-deux ; p-values, hypothèses et avertissements.
- Scikit-learn : régression/classification, modèle linéaire ou forêt aléatoire, pipeline d’imputation/encodage, jeu test indépendant, métriques et références naïves.
- Prédiction sur de nouveaux fichiers ; export CSV.
- Série temporelle régulière, Ridge autorégressif, séparation chronologique, prévision récursive.

## Utilisation de la démonstration
Pour une régression : cible `ventes`, variables `budget` et `segment`. Ne pas utiliser `objectif_atteint` (calculé depuis les ventes).
Pour une classification : cible `objectif_atteint`, variables `budget` et `segment`. Exclure `ventes` si elle n’est pas disponible au moment de la décision.
Pour les séries : date `date`, mesure `ventes`, fréquence Jour.
Les données synthétiques ne démontrent pas une efficacité sur des données réelles.

## Limites et sécurité
Prototype fonctionnel, pas un service de production clé en main. Pas d’authentification, rôles, base de données ou journal d’audit. Données et modèles conservés dans la session du serveur, pas de sauvegarde persistante. Sur un serveur distant, les fichiers sont transmis au serveur : ce n’est pas un traitement entièrement dans le navigateur.
Ne pas exposer des données sensibles sans HTTPS, contrôle d’accès, politique de rétention, limites de ressources et revue de sécurité. Les fichiers sont chargés en mémoire ; commencer avec des jeux modestes. Les imports XLSX uniquement évitent les fichiers à macros ; aucun code utilisateur n’est exécuté, aucune expression de filtre libre n’est proposée, aucun modèle pickle externe n’est chargé.
La préparation manuelle peut introduire une fuite d’information avant le split : garder des données brutes pour la modélisation. Le pipeline ajuste ses propres transformations sur l’entraînement uniquement. Le choix des variables, l’indépendance des observations, la qualité de mesure et les hypothèses statistiques restent à vérifier.
Les prédictions temporelles n’incluent pas saisonnalité explicite, intervalles d’incertitude, validation glissante ou variables externes. L’évaluation est à un pas, et non multi-horizon.
Les outils implémentent les opérations pandas courantes, pas l’intégralité de son API.

## Déploiement optionnel
Pour lancer sur une machine serveur après installation :
```bash
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```
Cette commande ouvre l’écoute réseau mais n’ajoute aucune sécurité. Utiliser un reverse proxy HTTPS et une authentification avant toute exposition publique. Le projet peut aussi être déployé via un hébergement compatible Streamlit ; vérifier les conditions et la confidentialité de l’hébergeur.

## Vérification
```bash
python smoke_test.py
```
Teste imports de données, jointure, classification, régression et prévision sans navigateur. Les dépendances utilisent des plages de versions, pas un environnement verrouillé ; valider avant une mise en production.


## Version 2 — DataScope Studio
- En-tête avec navigation directe : descriptive, inférentielle, tableaux de bord, prédiction, séries temporelles, préparation et studio de code.
- Nouveau thème clair : bandeau dégradé, cartes KPI et navigation adaptée aux petits écrans.
- Import CSV, XLSX, TXT, TSV, PDF, HTML/HTM, JSON et Parquet dans les données principales, les jointures et les nouvelles observations.
- XLSX : choix de feuille. HTML : choix de tableau, pas d’exécution de scripts ni d’affichage du HTML original. PDF : tableaux détectables, pas d’OCR ; chaque tableau est séparé, les tableaux multi-pages ne sont pas fusionnés automatiquement. Les champs PDF sont souvent textuels : convertir leurs types dans Préparation avant les analyses numériques.
- TXT : délimité ou texte libre (une colonne par ligne de texte). Le texte libre n’est pas transformé automatiquement en variables statistiques.
- Limites : 25 Mo, 100 pages PDF ; ces limites ne constituent pas une protection complète contre des documents malveillants ou des consommations mémoire excessives. Importer uniquement des fichiers de confiance. Cache serveur temporaire de lecture : 10 minutes, maximum quatre entrées, sans stockage disque explicite. Ne pas utiliser pour des données sensibles sur un hébergement partagé sans revue de confidentialité.
- Studio : zone de code multiligne et exemples ; sous-ensemble pandas interprété par AST, sans exec/eval. Affectations, filtres, groupby, statistiques et transformations autorisées ; résultat exportable CSV et code exportable Python. Le Python exporté est un fragment qui suppose que df existe déjà.
- Ce n’est pas un IDE Python complet : imports, fonctions, boucles, accès fichiers et réseau non pris en charge. Aucun quota CPU/mémoire ni isolation par processus : usage local de confiance, pas un environnement d’exécution public sécurisé.

### Arch Linux : mise à jour
Dans le dossier extrait, activer l’environnement puis installer les nouvelles dépendances :
```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Pour une nouvelle installation, créer d’abord l’environnement avec `python -m venv .venv`.

### Tests complémentaires
Depuis le dossier du projet :
```bash
python test_v2.py
```
Imports des formats, refus de syntaxes interdites, navigation des sept pages et exécution du studio. Ces tests ne constituent pas un audit de sécurité.
