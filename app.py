"""Projet individuel de data storytelling - Roy TAMWO, I2-DE_02."""
from html import escape
from pathlib import Path

import streamlit as st

from utils.data import load_data, add_indicators, annual_totals, TECHNOLOGIES
from utils.charts import trend, ranking, region_map, production_mix
from utils import profile

ROOT = Path(__file__).resolve().parent
lang = st.session_state.get("language", "fr")


def tr(fr, en):
    return en if lang == "en" else fr


def number(value, decimals=1):
    result = f"{value:,.{decimals}f}"
    return result if lang == "en" else result.replace(",", " ").replace(".", ",")


TECH_LABELS = {"Éolien + solaire": tr("Éolien + solaire", "Wind + solar"),
               "Éolien": tr("Éolien", "Wind"), "Solaire": tr("Solaire", "Solar")}
INDICATOR_LABELS = {
    "Rapport à la consommation (%)": tr("Rapport à la consommation (%)", "Generation / consumption (%)"),
    "Production (TWh)": tr("Production (TWh)", "Generation (TWh)"),
}

st.set_page_config(page_title=tr("Éolien et solaire | Roy TAMWO", "Wind and solar | Roy TAMWO"), layout="wide")
st.markdown("""<style>
[data-testid="stSidebarUserContent"] {padding-top: 1rem; padding-bottom: 1rem;}
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {
    min-height: calc(100dvh - 6.75rem); gap: 1rem;
}
[data-testid="stLayoutWrapper"]:has(> .st-key-sidebar-footer) {margin-top: auto;}
.st-key-sidebar-footer {padding-top: .5rem; gap: .5rem;}
.sidebar-profile {border-bottom: 1px solid #d4dde2; padding-bottom: 1rem;}
.sidebar-profile h2 {font-size: 1.3rem; margin: 0 0 .45rem; padding: 0;}
.sidebar-profile p {font-size: .9rem; margin: .3rem 0; overflow-wrap: anywhere;}
.sidebar-profile a {color: #17617b;}
.sidebar-course {border-top: 1px solid #d4dde2; padding-top: 1rem;}
.sidebar-course p {font-size: .9rem; margin: .35rem 0;}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    email = escape(profile.STUDENT_EMAIL)
    st.markdown(f'''<div class="sidebar-profile">
<h2>{escape(profile.STUDENT_NAME)}</h2>
<p><a href="mailto:{email}">{email}</a></p>
<p><strong>{tr("Programme", "Programme")} :</strong> {escape(profile.PROGRAMME)}</p>
<p><strong>{tr("Année", "Academic year")} :</strong> {escape(profile.ACADEMIC_YEAR)}</p>
</div>''', unsafe_allow_html=True)
    st.radio("Langue / Language", ["fr", "en"],
             format_func=lambda value: {"fr": "Français", "en": "English"}[value],
             horizontal=True, key="language")

try:
    data, geography, sources = load_data()
except (ValueError, OSError):
    st.error(tr("Impossible de charger les données. Vérifiez les fichiers du dossier data.",
                "Unable to load the data. Check the files in the data folder."))
    st.stop()

# Les sélections sont indépendantes des libellés traduits des widgets.
defaults = {"regions": sorted(data.region.unique()), "period": (2013, 2024),
            "technology": "Éolien + solaire", "indicator": "Rapport à la consommation (%)"}
filters = st.session_state.setdefault("filters", defaults.copy())


def remember_filter(name, key):
    st.session_state["filters"][name] = st.session_state[key]


def widget_options(name):
    key = f"{name}_{lang}"
    st.session_state[key] = filters[name]
    return {"key": key, "on_change": remember_filter, "args": (name, key)}


with st.sidebar:
    with st.expander(tr("Explorer les données", "Explore the data"), expanded=False):
        regions = st.multiselect(tr("Régions", "Regions"), sorted(data.region.unique()),
                                 **widget_options("regions"))
        period = st.slider(tr("Période", "Period"), 2013, 2024, **widget_options("period"))
        technology = st.selectbox(tr("Filière", "Technology"), list(TECHNOLOGIES),
                                 format_func=TECH_LABELS.get, **widget_options("technology"))
        indicator = st.selectbox(tr("Indicateur des graphiques", "Chart indicator"), list(INDICATOR_LABELS),
                                format_func=INDICATOR_LABELS.get, **widget_options("indicator"))
        st.caption(tr("La carte, le classement et les chiffres clés utilisent la dernière année de la période.",
                      "The map, ranking and key figures use the last year of the selected period."))
    st.caption(tr(f"{len(regions)} région(s) · {period[0]}–{period[1]}",
                  f"{len(regions)} region(s) · {period[0]}–{period[1]}"))
    with st.container(key="sidebar-footer"):
        st.markdown(f'''<div class="sidebar-course">
<p><strong>{tr("Cours", "Course")} :</strong><br>{escape(profile.COURSE_NAME)}</p>
<p>{escape(profile.MODULE_CODE)}</p>
<p><strong>{tr("Professeur", "Lecturer")} :</strong><br>{escape(profile.TEACHER_NAME)}</p>
</div>''', unsafe_allow_html=True)
        st.markdown(f"[LinkedIn · {profile.TEACHER_NAME}]({profile.TEACHER_LINKEDIN})")
        st.image(str(ROOT / "assets" / "efrei-logo.png"), width=160)

st.title(tr("Éolien et solaire", "Wind and solar"))
st.subheader(tr("Quelle place dans la consommation des régions ?", "How much of regional consumption do they represent?"))
st.write(tr("En France, la production éolienne et solaire a augmenté depuis 2013. Mais les régions n'ont pas le même profil. Ce tableau de bord compare les volumes produits et leur rapport à la consommation annuelle, pour un public qui souhaite comprendre ces écarts sans entrer dans les détails techniques du réseau.",
            "Wind and solar generation in France has increased since 2013, but regions have different profiles. This dashboard compares generation and its ratio to annual electricity consumption, for anyone who wants to understand these differences without going into the technical details of the grid."))

if not regions:
    st.info(tr("Choisissez au moins une région dans le menu de gauche.", "Select at least one region in the sidebar."))
    st.stop()

selected = data[data.region.isin(regions) & data.year.between(*period)].copy()
annual = annual_totals(selected, technology)
first, last = annual.iloc[0], annual.iloc[-1]
latest = add_indicators(selected[selected.year == period[1]], technology)
metric = "coverage_pct" if indicator == "Rapport à la consommation (%)" else "production_twh"
unit = "%" if metric == "coverage_pct" else "TWh"
tech_label = TECH_LABELS[technology]
scope = tr("13 régions métropolitaines, Corse incluse", "13 metropolitan regions, including Corsica") if len(regions) == 13 else tr(f"{len(regions)} région(s) sélectionnée(s)", f"{len(regions)} selected region(s)")
st.caption(f"{scope} · {period[0]}–{period[1]} · {tech_label}")

c1, c2, c3, c4 = st.columns(4)
c1.metric(tr(f"Production {tech_label.lower()}", f"{tech_label} generation"), f"{number(last.production_twh)} TWh")
c2.metric(tr("Consommation d'électricité", "Electricity consumption"), f"{number(last.consumption_gwh / 1000)} TWh")
c3.metric(tr("Rapport production / consommation", "Generation / consumption"), f"{number(last.coverage_pct)} %",
          help=tr("100 × production de la filière / consommation brute d'électricité. Les volumes sont annuels.", "100 × generation from the selected technology / gross electricity consumption. All volumes are annual."))
change = last.coverage_pct - first.coverage_pct
c4.metric(tr(f"Écart depuis {period[0]}", f"Change since {period[0]}"),
          tr(f"{number(change)} points", f"{number(change)} pp") if period[0] != period[1] else tr("Une seule année", "One year only"))

st.info(tr("Lecture : un rapport de 20 % signifie que la production annuelle étudiée équivaut à un cinquième de la consommation annuelle. Les échanges entre régions et les variations horaires empêchent d'en déduire une autonomie électrique.",
           "How to read this: a ratio of 20% means annual generation is equivalent to one fifth of annual consumption. Exchanges between regions and hourly variations mean this does not measure electricity self-sufficiency."))

st.header(tr("1. Une progression à regarder sur plusieurs années", "1. Look at the trend over several years"))
if period[0] != period[1]:
    st.write(tr(f"Sur le périmètre choisi, la production passe de **{number(first.production_twh)} à {number(last.production_twh)} TWh**. Le rapport à la consommation passe de **{number(first.coverage_pct)} % à {number(last.coverage_pct)} %**.",
                f"Across the selected regions, generation changes from **{number(first.production_twh)} to {number(last.production_twh)} TWh**. The ratio to consumption changes from **{number(first.coverage_pct)}% to {number(last.coverage_pct)}%**."))
    previous = annual.iloc[-2]
    if last.coverage_pct < previous.coverage_pct:
        st.caption(tr(f"La progression n'est pas continue : le rapport baisse de {number(previous.coverage_pct)} % en {int(previous.year)} à {number(last.coverage_pct)} % en {int(last.year)}.",
                      f"Growth is not continuous: the ratio falls from {number(previous.coverage_pct)}% in {int(previous.year)} to {number(last.coverage_pct)}% in {int(last.year)}."))
else:
    st.write(tr("Une seule année est sélectionnée. Élargissez la période pour étudier une évolution.", "Only one year is selected. Widen the period to explore a trend."))
st.plotly_chart(trend(annual, metric, unit, lang=lang), use_container_width=True, key="trend")
st.caption(tr(f"Description du graphique : évolution annuelle de {tech_label.lower()}, exprimée en {unit}, dans les régions sélectionnées. Les valeurs exactes figurent dans le tableau accessible en bas de page.",
              f"Chart description: annual trend for {tech_label.lower()}, expressed in {unit}, across the selected regions. Exact values are available in the accessible table at the bottom of the page."))

st.header(tr(f"2. Des profils régionaux différents en {period[1]}", f"2. Different regional profiles in {period[1]}"))
leader = latest.sort_values(metric, ascending=False).iloc[0]
st.write(tr(f"**{leader.region}** affiche la valeur la plus élevée parmi les régions choisies : **{number(leader[metric])} {unit}**. Le classement change selon que l'on compare des volumes ou un rapport à la consommation.",
            f"**{leader.region}** has the highest value among the selected regions: **{number(leader[metric])} {unit}**. Rankings differ depending on whether you compare volumes or the ratio to consumption."))
left, right = st.columns(2)
with left:
    st.plotly_chart(ranking(latest, metric, unit, lang=lang), use_container_width=True, key="ranking")
with right:
    st.plotly_chart(region_map(latest, geography, metric, unit, lang=lang), use_container_width=True, key="map")
st.caption(tr(f"Description : le classement et la carte représentent le même indicateur ({unit}) pour la dernière année sélectionnée. Survolez une barre ou une région pour lire sa valeur. Les zones blanches ne font pas partie de la sélection.",
              f"Description: the ranking and map show the same indicator ({unit}) for the last selected year. Hover over a bar or a region to see its value. White areas are outside the selection."))

st.header(tr("3. Séparer l'éolien et le solaire aide à comprendre le total", "3. Separate wind and solar to understand the total") if technology == "Éolien + solaire" else tr(f"3. Les volumes produits : {tech_label.lower()}", f"3. Generation volumes: {tech_label.lower()}"))
st.write(tr("Le rapport à la consommation dépend à la fois de la production et de la demande. Ce graphique revient aux volumes produits pour rendre leur évolution plus facile à lire.",
            "The ratio to consumption depends on both generation and demand. This chart returns to generation volumes to make their changes easier to read."))
st.plotly_chart(production_mix(annual, TECHNOLOGIES[technology], lang=lang), use_container_width=True, key="mix")
st.caption(tr(f"Description : chaque barre représente une année. Filière affichée : {tech_label.lower()}. L'éolien est bleu, le solaire orange. L'axe vertical mesure la production en TWh (1 TWh = 1 000 GWh).",
              f"Description: each bar represents a year. Technology shown: {tech_label.lower()}. Wind is blue and solar is orange. The vertical axis measures generation in TWh (1 TWh = 1,000 GWh)."))

st.header(tr("Ce que l'on peut en retenir", "What we can learn"))
st.write(tr(f"Pour {scope.lower()}, le rapport annuel atteint **{number(last.coverage_pct)} % en {period[1]}**. Comparer les régions aide à situer la production, mais ne suffit pas à expliquer les écarts : il faudrait aussi connaître la puissance installée, la météo et la demande locale.",
            f"For {scope.lower()}, the annual ratio reaches **{number(last.coverage_pct)}% in {period[1]}**. Comparing regions helps put generation in context, but does not explain the differences on its own: installed capacity, weather and local demand also matter."))
st.write(tr("Pour prolonger l'analyse, je regarderais les séries horaires et les capacités installées. Cela permettrait de distinguer l'effet des nouveaux équipements de celui des conditions de production.",
            "To extend this analysis, I would look at hourly time series and installed capacity. This would help separate the effect of new equipment from that of generation conditions."))

st.header(tr("Qualité des données et méthode", "Data quality and methodology"))
q1, q2, q3 = st.columns(3)
q1.metric(tr("Observations sélectionnées", "Selected observations"), str(len(selected)))
q2.metric(tr("Valeurs manquantes utiles", "Missing values in used fields"), str(int(selected[["wind_gwh", "solar_gwh", "consumption_gwh"]].isna().sum().sum())))
q3.metric(tr("Doublons région / année", "Duplicate region / year pairs"), str(int(selected.duplicated(["code", "year"]).sum())))
st.write(tr("Le panel complet contient 156 observations : 13 régions sur 12 années. Les deux jeux ODRE sont joints par code INSEE et année, avec une seule ligne de chaque côté. Les volumes retenus sont positifs ou nuls et la consommation est strictement positive. Aucune valeur utile n'a été imputée.",
            "The full panel contains 156 observations: 13 regions over 12 years. The two ODRE datasets are joined by INSEE code and year, with one row on each side. Generation volumes are non-negative and consumption is strictly positive. No values in the fields used have been imputed."))
st.write(tr("Le périmètre s'arrête en 2024 : le statut RTE de la consommation est définitif pour toutes les observations retenues. Les données 2025, consolidées au téléchargement, sont exclues. Les autres filières du fichier de production ne sont pas utilisées.",
            "The analysis ends in 2024: RTE marks consumption as final for all included observations. The 2025 data, marked as consolidated when downloaded, are excluded. Other technologies in the generation file are not used."))
st.write(tr("La consommation brute inclut les pertes et n'est pas corrigée du climat. ODRE signale une révision de l'autoconsommation photovoltaïque sur 2022–2024, déjà intégrée à cette copie. Les calculs suivent les colonnes explicitement libellées en GWh, malgré une mention générale en TWh dans la description du portail.",
            "Gross consumption includes losses and is not weather-adjusted. ODRE reports a revision of solar self-consumption for 2022–2024, already included in this snapshot. Calculations use columns explicitly labelled in GWh, despite a general reference to TWh in the portal description."))
st.write(tr("Calcul : rapport (%) = 100 × somme des productions sélectionnées / somme des consommations. Les rapports régionaux ne sont pas moyennés. Les volumes annuels ne décrivent ni les pointes de demande, ni les importations, ni les émissions de CO₂. Ces données agrégées ne contiennent aucune information personnelle.",
            "Calculation: ratio (%) = 100 × sum of selected generation / sum of consumption. Regional ratios are not averaged. Annual volumes do not describe peak demand, imports or CO₂ emissions. These aggregated datasets contain no personal information."))

with st.expander(tr("Tableaux accessibles et téléchargement", "Accessible tables and download")):
    st.write(tr("Série annuelle du périmètre sélectionné", "Annual series for the selected regions"))
    readable = annual[["year", "production_twh", "consumption_gwh", "coverage_pct"]].rename(columns={"year": tr("Année", "Year"), "production_twh": tr("Production (TWh)", "Generation (TWh)"), "consumption_gwh": tr("Consommation (GWh)", "Consumption (GWh)"), "coverage_pct": tr("Rapport (%)", "Ratio (%)")})
    st.dataframe(readable, hide_index=True, width="stretch")
    st.write(tr(f"Valeurs régionales en {period[1]}", f"Regional values in {period[1]}"))
    st.dataframe(latest[["region", "wind_gwh", "solar_gwh", "consumption_gwh", "coverage_pct"]].rename(columns={"region": tr("Région", "Region"), "wind_gwh": tr("Éolien (GWh)", "Wind (GWh)"), "solar_gwh": tr("Solaire (GWh)", "Solar (GWh)"), "consumption_gwh": tr("Consommation (GWh)", "Consumption (GWh)"), "coverage_pct": tr("Rapport (%)", "Ratio (%)")}), hide_index=True, width="stretch")
    st.download_button(tr("Télécharger les données filtrées (CSV)", "Download filtered data (CSV)"), selected.to_csv(index=False).encode("utf-8-sig"), file_name="electricite_regions_selection.csv", mime="text/csv")

with st.expander(tr("Sources et définitions", "Sources and definitions")):
    st.markdown(tr("**Producteur : RTE.** Portail de diffusion : Open Data Réseaux Énergies (ODRE). Jeux référencés sur data.gouv.fr. Réutilisation sous Licence Ouverte 2.0, avec attribution.",
                   "**Producer: RTE.** Distribution portal: Open Data Réseaux Énergies (ODRE). Datasets listed on data.gouv.fr. Reuse under the French Open Licence 2.0, with attribution."))
    for source in sources["datasets"]:
        st.markdown(f"[{source['name']}]({source['portal_url']}) · [{tr('Ressource ODRE', 'ODRE resource')}]({source['source_url']})")
    st.caption(tr("Copie téléchargée le 20 octobre 2026. Contours géographiques inclus dans la source ODRE : attribution INSEE, IGN, NaturalEarth. Licence Ouverte 2.0.",
                  "Snapshot downloaded on 20 October 2026. Geographic boundaries included in the ODRE source: attribution INSEE, IGN, NaturalEarth. French Open Licence 2.0."))
    st.caption(tr("Sources, dates, empreintes des fichiers et transformations : data/sources.json et scripts/prepare_data.py dans le dossier du projet.",
                  "Sources, dates, file hashes and transformations: data/sources.json and scripts/prepare_data.py in the project folder."))

st.divider()
st.caption(tr("Projet individuel de data storytelling · Roy TAMWO · 20230840 · I2-DE_02 · EFREI · 2026–2027",
              "Individual data storytelling project · Roy TAMWO · 20230840 · I2-DE_02 · EFREI · 2026–2027"))
