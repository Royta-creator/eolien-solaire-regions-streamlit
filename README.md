# Éolien et solaire dans les régions françaises

**Roy TAMWO - 20230840 - I2-DE_02**  
Projet individuel Streamlit, EFREI, 2026

## Liens du rendu

- [Application Streamlit](https://roy-tamwo-eolien-solaire.streamlit.app/)
- [Dépôt GitHub](https://github.com/Royta-creator/eolien-solaire-regions-streamlit)
- [Rapport et storyboard](docs/Rapport_Roy_TAMWO.pdf)
- [Présentation simple](docs/Presentation_Roy_TAMWO.pdf)
- [Vidéo de démonstration — 2 min 55, version du 24 octobre 2026](demo/Demo_Roy_TAMWO.mp4)
- [Sous-titres de la vidéo](demo/Demo_Roy_TAMWO.srt)

## La question

Quelle place prennent l'éolien et le solaire dans la consommation annuelle des régions françaises entre 2013 et 2024 ? Ce tableau de bord permet de comparer les régions, même sans connaître le fonctionnement du réseau électrique.

Dans les 13 régions métropolitaines, Corse comprise, la production éolienne et solaire passe de 20,6 à 71,6 TWh. Comparée à la consommation brute, elle passe de 4,2 % à 16,2 %. Cette hausse n'est pas régulière : le rapport atteint 16,7 % en 2023, puis baisse en 2024.

Ce pourcentage ne dit pas si une région est autonome. Il ne donne pas non plus la part exacte d'éolien et de solaire dans l'électricité réellement consommée. Le projet ne tient pas compte des échanges entre régions, ni du fait que l'électricité n'est pas toujours produite au moment où elle est demandée.

## Lancement

Le projet a été testé avec Python **3.12**. Pour le lancer, ouvrir un terminal dans le dossier qui contient `app.py`.

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

Ouvrir ensuite l'adresse affichée par Streamlit, généralement `http://localhost:8501`. Il faut Internet pour installer les bibliothèques. Après l'installation, l'application fonctionne avec les fichiers fournis, sans jeton, clé d'API ou téléchargement au démarrage. Les contours de la carte sont aussi inclus : aucun fond de carte n'est chargé en ligne.

`requirements.txt` renvoie vers `requirements-lock.txt`. Ce fichier fixe les versions des 38 bibliothèques nécessaires, y compris celles utilisées par les autres bibliothèques. Les principales sont Streamlit 1.50.0, Pandas 2.3.3 et Plotly 6.3.1. Garder ces versions et les données incluses permet de retrouver le même résultat.

## Utiliser le tableau de bord

En haut de la barre latérale se trouvent le nom Roy TAMWO, l'adresse étudiante, le programme DE et l'année 2026–2027. En bas figurent le cours **Data Analysis & Visualization** (ST2DVZ-2627PSA01), Mano Joseph Mathew, son lien LinkedIn et le logo EFREI.

Le choix **Français / English** change la langue de l'interface, des explications, des indicateurs et des graphiques. Les filtres restent les mêmes quand on change de langue. Les noms officiels des régions et des jeux de données restent en français. Les en-têtes du CSV brut exporté ne changent pas non plus, pour pouvoir réutiliser le fichier facilement.

1. Ouvrir **Explorer les données / Explore the data**, puis choisir les régions, la période et la filière.
2. Lire les chiffres de la dernière année de la période et la courbe d'évolution.
3. Comparer le classement et la carte. Passer du pourcentage aux volumes en TWh pour voir ce qui change.
4. Regarder les volumes par filière, puis la méthode et les limites. Les tableaux détaillés et le CSV filtré se trouvent en bas de page.

On peut survoler les graphiques pour lire les valeurs, zoomer et télécharger une image avec les outils Plotly. Les textes sous les graphiques et les tableaux permettent aussi de lire les résultats. Si aucune région n'est sélectionnée, un message invite à en choisir une. On peut choisir une seule année ; dans ce cas, l'application ne calcule pas d'évolution.

## Sources

Le projet utilise deux jeux de données du portail **Open Data Réseaux Énergies (ODRE)**, disponibles sur data.gouv.fr. Les données sur l'électricité viennent de **RTE**.

- [Production régionale annuelle par filière](https://www.data.gouv.fr/datasets/production-regionale-annuelle-par-filiere-2008-a-2025)
- [Consommation annuelle brute régionale](https://www.data.gouv.fr/datasets/consommation-annuelle-brute-regionale)

Les fichiers ont été téléchargés le **20 octobre 2026**. Ils sont réutilisables sous [Licence Ouverte 2.0](https://www.etalab.gouv.fr/wp-content/uploads/2017/04/ETALAB-Licence-Ouverte-v2.0.pdf). Les contours des régions sont inclus dans les données ODRE, qui citent **INSEE, IGN, NaturalEarth** comme sources. Les liens directs, les dates et les empreintes SHA-256 sont dans `data/sources.json`. Les métadonnées d'origine de l'API sont aussi conservées.

## Préparation et calculs

Les fichiers bruts sont conservés tels quels. Le script garde les années 2013–2024 et les colonnes utiles. Il vérifie ensuite les identifiants, puis rassemble la production et la consommation à partir de l'année et du code INSEE de la région. Chaque ligne doit correspondre à une seule ligne de l'autre fichier.

Le résultat contient **156 lignes = 13 régions × 12 années**. Aucune valeur utilisée ne manque et chaque couple région-année est unique. Les productions sont positives ou nulles et toutes les consommations sont strictement positives. Aucune valeur manquante n'est remplacée et aucun échantillon n'est tiré.

Les valeurs d'origine sont en **GWh**, avec **1 TWh = 1 000 GWh**. Le pourcentage affiché se calcule ainsi :

```text
Rapport (%) = 100 × somme des productions sélectionnées (GWh)
                  / somme des consommations brutes (GWh)
```

L'application additionne d'abord les volumes, puis fait la division. Elle ne calcule pas la moyenne simple des pourcentages des régions. La différence entre deux rapports est donnée en **points de pourcentage**.

Pour refaire la préparation à partir des CSV inclus :

```powershell
.\.venv\Scripts\python.exe scripts/prepare_data.py
```

`scripts/download_data.py` réutilise les fichiers déjà présents au lieu de les télécharger à nouveau. L'option `--refresh` les remplace par la version en ligne. Pour essayer une nouvelle version dans un autre dossier :

```powershell
.\.venv\Scripts\python.exe scripts/download_data.py --data-dir data_nouvelles
.\.venv\Scripts\python.exe scripts/prepare_data.py --data-dir data_nouvelles
```

Les données en ligne peuvent changer. Le fichier `sources.json` décrit seulement la copie fournie avec ce projet. Si les données sont remplacées, il faut aussi mettre à jour ce fichier et vérifier les résultats. Le projet n'utilise pas de tirage aléatoire, donc il n'a pas besoin de graine.

## Limites à garder en tête

- Les deux séries commencent en commun en 2013. Les données de consommation de 2024 sont définitives. Celles de 2025 avaient encore le statut « Consolidé » au moment du téléchargement : cette année n'est donc pas utilisée.
- La consommation est brute : elle inclut les pertes et n'est pas corrigée des effets du climat.
- ODRE signale une révision de l'autoconsommation photovoltaïque sur 2022–2024. Les fichiers fournis contiennent cette révision.
- Une description générale du portail mentionne les TWh, mais les colonnes CSV utilisées indiquent bien des GWh. Le calcul suit les unités indiquées dans ces colonnes.
- Les valeurs manquantes d'autres filières restent dans le fichier brut. Elles n'entrent dans aucun calcul et ne sont pas remplacées par zéro.
- L'éolien et le solaire ne représentent pas toutes les énergies renouvelables. Le projet n'estime ni les émissions de CO₂, ni les prix, et ne cherche pas à établir des liens de cause à effet.
- Les régions n'ont pas la même taille, les mêmes équipements ou la même demande. Le classement ne suffit donc pas à juger leur performance.
- Les données sont regroupées par région et par année. Pour aller plus loin, il faudrait des données par heure, la puissance installée et la météo. Les fichiers de données ne contiennent aucune information personnelle.

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

Les 13 tests passent avec Python 3.12 sur Windows x64. Ils comparent les données préparées aux fichiers bruts, vérifient les calculs et testent les filtres avec AppTest. Ils contrôlent aussi le passage du français à l'anglais et le retour en français : les graphiques doivent être traduits, les sélections et les chiffres doivent rester identiques.

Le script de préparation retrouve les mêmes données, même si les fins de ligne diffèrent entre Windows et Linux. Les quatre graphiques ont aussi été ouverts dans un navigateur. Les commandes pour Linux et macOS sont fournies, mais elles n'ont pas été testées dans cet environnement.

## Mise en ligne et dépôt

L'application est publiée sur [Streamlit Community Cloud](https://roy-tamwo-eolien-solaire.streamlit.app/) depuis la branche `main` du [dépôt GitHub](https://github.com/Royta-creator/eolien-solaire-regions-streamlit). Le point d'entrée est `app.py`, avec Python 3.12. Aucun secret n'est nécessaire. `requirements.txt` utilise les mêmes versions qu'en local. PyArrow est fixé à 24.0.0, la version choisie par la plateforme lors du déploiement. Les étapes sont décrites dans la [procédure officielle Streamlit](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app).

Les graphiques et le recalcul des indicateurs ont été vérifiés sur l'application en ligne. Le rapport contient le storyboard. La vidéo du 24 octobre 2026 dure 2 min 55. C'est un montage de captures réelles successives du tableau de bord, avec des sous-titres français et sans piste audio. Les vues montrent la barre latérale, le choix de langue et les résultats obtenus avec les filtres ; il ne s'agit pas d'une capture continue des manipulations. Tous les liens à joindre au rendu sont aussi dans `LIENS_REMISE.txt`.

Nom de remise : **StApp26_20230840_TAMWO_DE2.zip**. Le suffixe DE2 correspond au groupe indiqué **I2-DE_02**.

## Mise à jour du 24 octobre 2026

La barre latérale a été réorganisée et l'application est maintenant disponible en français et en anglais. Le [logo officiel EFREI](https://www.efrei.fr/wp-content/uploads/2025/09/Logo-Efrei-CMJN-1024x512.png) a été téléchargé le 24 octobre 2026 pour identifier l'école. La vidéo et ses sous-titres ont été mis à jour pour présenter cette version. Le rapport et la présentation PDF du premier rendu sont conservés.
