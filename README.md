# Éolien et solaire dans les régions françaises

**Roy TAMWO - 20230840 - I2-DE_02**  
Projet individuel Streamlit, EFREI, 2026

## Liens du rendu

- [Application Streamlit](https://roy-tamwo-eolien-solaire.streamlit.app/)
- [Dépôt GitHub](https://github.com/Royta-creator/eolien-solaire-regions-streamlit)
- [Rapport et storyboard](docs/Rapport_Roy_TAMWO.pdf)
- [Présentation simple](docs/Presentation_Roy_TAMWO.pdf)
- [Vidéo de démonstration — 2 min 40](demo/Demo_Roy_TAMWO.mp4)
- [Sous-titres de la vidéo](demo/Demo_Roy_TAMWO.srt)

## La question

Quelle place la production éolienne et solaire prend-elle dans la consommation annuelle des régions françaises entre 2013 et 2024 ? Le tableau de bord s'adresse à une personne qui souhaite comparer les territoires sans connaissances particulières sur le réseau électrique.

Sur les 13 régions métropolitaines, Corse comprise, la production éolienne et solaire passe de 20,6 à 71,6 TWh. Son rapport à la consommation brute passe de 4,2 % à 16,2 %. La hausse n'est pas continue : le rapport atteint 16,7 % en 2023, puis diminue en 2024.

Ce rapport annuel ne mesure pas l'autonomie d'une région. Il ne représente pas non plus la part exacte d'éolien et de solaire dans l'électricité effectivement consommée. Les échanges entre régions et le décalage entre production et demande ne sont pas étudiés ici.

## Lancement

Python **3.12** est la version utilisée pour les vérifications. Ouvrir un terminal dans le dossier qui contient `app.py`.

Windows PowerShell :

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

macOS / Linux :

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m streamlit run app.py
```

Ouvrir l'adresse locale affichée par Streamlit, généralement `http://localhost:8501`. L'installation des dépendances nécessite Internet. Ensuite, l'application utilise uniquement les fichiers fournis : aucun jeton, aucune clé d'API et aucun téléchargement à l'ouverture. La carte utilise les contours locaux, sans fond de carte distant.

`requirements.txt` référence `requirements-lock.txt`, qui fixe les 38 dépendances directes et transitives telles qu'elles ont été testées. Les bibliothèques principales sont Streamlit 1.50.0, Pandas 2.3.3 et Plotly 6.3.1. Pour reproduire le rendu fourni, conserver ce verrouillage et les données incluses.

## Utiliser le tableau de bord

Le haut de la barre latérale affiche Roy TAMWO, son adresse étudiante, le programme DE et l'année 2026–2027. Le bloc du bas présente le cours **Data Analysis & Visualization** (ST2DVZ-2627PSA01), Mano Joseph Mathew, son LinkedIn et le logo EFREI.

Le sélecteur **Français / English** traduit l'interface, les explications, les indicateurs et les graphiques. Les filtres sont conservés lors d'un changement de langue. Les noms officiels des régions et des jeux de données restent en français ; les en-têtes du CSV brut exporté restent stables pour permettre sa réutilisation.

1. Ouvrir **Explorer les données / Explore the data**, puis choisir les régions, la période et la filière.
2. Lire les chiffres de la dernière année de la période et la courbe d'évolution.
3. Comparer le classement et la carte. Passer du rapport en pourcentage aux volumes en TWh pour comprendre la différence.
4. Regarder les volumes par filière, puis la méthode et les limites. Les tableaux détaillés et le CSV filtré se trouvent en bas de page.

Tous les graphiques proposent le survol, le zoom et le téléchargement d'image Plotly. Les descriptions sous les graphiques et les tableaux donnent une alternative textuelle. Une sélection de régions vide affiche une invitation à choisir une région. Une période d'une seule année reste utilisable, sans calcul d'évolution trompeur.

## Sources

Deux jeux cohérents du même portail **Open Data Réseaux Énergies (ODRE)**, référencés sur data.gouv.fr. Les champs électriques sont produits par **RTE**.

- [Production régionale annuelle par filière](https://www.data.gouv.fr/datasets/production-regionale-annuelle-par-filiere-2008-a-2025)
- [Consommation annuelle brute régionale](https://www.data.gouv.fr/datasets/consommation-annuelle-brute-regionale)

Copie téléchargée le **20 octobre 2026**, réutilisable sous [Licence Ouverte 2.0](https://www.etalab.gouv.fr/wp-content/uploads/2017/04/ETALAB-Licence-Ouverte-v2.0.pdf). Les géométries sont incluses dans la ressource ODRE, avec attribution source **INSEE, IGN, NaturalEarth**. Les liens directs, dates et empreintes SHA-256 se trouvent dans `data/sources.json`. Les métadonnées API d'origine sont conservées.

## Préparation et calculs

Les fichiers bruts restent inchangés. Le script retient 2013–2024, sélectionne les champs utiles, vérifie les clés puis joint les deux séries par année et code INSEE région. La jointure impose une correspondance un-à-un. Le résultat contient **156 lignes = 13 régions × 12 années**. Il ne manque aucune valeur utile, les clés ne sont pas dupliquées, les productions sont positives ou nulles et toutes les consommations sont strictement positives. Aucune imputation ni aucun échantillonnage.

Les champs sources sont en **GWh**. La conversion utilise **1 TWh = 1 000 GWh**. Le rapport affiché est :

```text
Rapport (%) = 100 × somme des productions sélectionnées (GWh)
                  / somme des consommations brutes (GWh)
```

L'application additionne les volumes avant de diviser. Elle ne fait jamais une moyenne simple des pourcentages régionaux. L'écart entre deux rapports s'exprime en **points de pourcentage**.

Reproduire la préparation depuis les CSV inclus :

```powershell
.\.venv\Scripts\python.exe scripts/prepare_data.py
```

Le téléchargement possède un cache : `scripts/download_data.py` réutilise les fichiers déjà présents. L'option `--refresh` remplace les CSV par la version en ligne. Pour explorer une nouvelle version sans modifier le rendu de référence :

```powershell
.\.venv\Scripts\python.exe scripts/download_data.py --data-dir data_nouvelles
.\.venv\Scripts\python.exe scripts/prepare_data.py --data-dir data_nouvelles
```

Les données en ligne peuvent être révisées. Le manifeste `sources.json` décrit uniquement la copie fournie. Une nouvelle copie demande un nouveau manifeste et une nouvelle validation des résultats. Aucun tirage aléatoire n'est utilisé, donc aucune graine n'est nécessaire.

## Limites à garder en tête

- 2013 est le début commun des séries. La consommation 2024 est définitive. L'année 2025, consolidée lors du téléchargement, est exclue.
- La consommation est brute, pertes comprises, et non corrigée du climat.
- ODRE indique une révision de l'autoconsommation photovoltaïque sur 2022–2024. La copie fournie intègre cette révision.
- Une description générale du portail mentionne les TWh. Les colonnes CSV utilisées sont explicitement en GWh : ce sont leurs libellés qui déterminent les unités du calcul.
- Les valeurs manquantes d'autres filières restent dans le fichier brut. Elles n'entrent dans aucun calcul et ne sont pas remplacées par zéro.
- Éolien et solaire ne représentent pas toutes les énergies renouvelables. Aucune estimation de CO₂, de prix ou de causalité n'est proposée.
- Les régions diffèrent par leur taille, leurs équipements et leur demande. Un classement n'est pas une note de performance.
- Les données sont annuelles et agrégées. Une analyse horaire, avec puissance installée et météo, serait nécessaire pour aller plus loin. Les fichiers ne contiennent aucune donnée personnelle.

## Fichiers

```text
app.py                      application Streamlit
utils/data.py               chargement en cache et agrégations
utils/charts.py             graphiques Plotly
utils/profile.py            identité, cours et informations de la barre latérale
assets/efrei-logo.png        logo officiel EFREI, disponible hors ligne
data/                       CSV bruts, panel, carte, métadonnées et contrôles
scripts/                    téléchargement et préparation reproductible
tests/test_project.py       vérifications données, calculs, filtres et carte
docs/                       rapport, présentation simple et storyboard
demo/                       vidéo de démonstration sous-titrée
requirements*.txt           versions des dépendances
.streamlit/config.toml      thème et configuration
```

## Vérifications

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Les 13 tests passent avec Python 3.12 sur Windows x64. Ils comparent les chiffres préparés aux sources brutes, contrôlent les calculs et exercent les filtres via AppTest. Ils vérifient aussi le changement de langue dans les deux sens, les graphiques traduits et la conservation des sélections et des chiffres. La préparation reconstruit le même contenu analytique, indépendamment des fins de ligne Windows/Linux. Les quatre graphiques ont aussi été ouverts dans un navigateur. Les commandes Linux/macOS sont fournies, mais n'ont pas été exécutées dans cet environnement.

## Mise en ligne et dépôt

L'application est publiée sur [Streamlit Community Cloud](https://roy-tamwo-eolien-solaire.streamlit.app/) depuis la branche `main` du [dépôt GitHub](https://github.com/Royta-creator/eolien-solaire-regions-streamlit), avec `app.py` et Python 3.12. Aucun secret n'est requis. `requirements.txt` charge le même verrouillage qu'en local. PyArrow est fixé à 24.0.0, la version retenue par la plateforme lors du déploiement. [Procédure officielle Streamlit](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app).

Les graphiques et le recalcul des indicateurs ont été vérifiés sur l'application publiée. Le rapport contient le storyboard ; la vidéo dure 2 min 40 et présente les interactions avec des sous-titres. Les liens complets à joindre à la remise se trouvent aussi dans `LIENS_REMISE.txt`.

Nom de remise : **StApp26_20230840_TAMWO_DE2.zip**. Le suffixe DE2 correspond au groupe indiqué **I2-DE_02**.

## Mise à jour du 24 octobre 2026

Barre latérale réorganisée et interface bilingue français/anglais. Le logo est une copie du [logo diffusé sur le site officiel EFREI](https://www.efrei.fr/wp-content/uploads/2025/09/Logo-Efrei-CMJN-1024x512.png), téléchargée le 24 octobre 2026 et utilisée pour identifier l'établissement. Le rapport, la présentation et la vidéo du rendu initial sont conservés ; la vidéo montre l'ancienne disposition de la barre latérale.
