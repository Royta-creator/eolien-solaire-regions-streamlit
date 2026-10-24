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
st.subheader(tr("Où en sont les régions françaises ?", "How do French regions compare?"))
st.write(tr("On produit plus d'électricité avec le vent et le soleil qu'en 2013. Mais cette hausse n'est pas la même partout. Ici, on regarde comment la production a évolué dans les régions françaises et ce qu'elle représente par rapport à leur consommation. Les filtres à gauche permettent de comparer les régions, les années et les deux énergies.",
            "France produces more electricity from wind and solar than it did in 2013, but growth varies from one region to another. Here, we look at how generation has changed and how it compares with each region's electricity use. Use the filters on the left to compare regions, years and the two energy sources."))

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

st.info(tr("Par exemple, 20 % veut dire que la production représente l'équivalent d'un cinquième de la consommation sur l'année. Cela ne veut pas dire que la région se suffit à elle-même : l'électricité circule entre les régions, et on ne produit pas toujours au moment où l'on en a besoin.",
           "For example, 20% means generation is equivalent to a fifth of the electricity used over the year. It doesn't mean the region can meet its own needs: electricity moves between regions, and generation doesn't always match when people need it."))

st.header(tr("1. La production au fil des années", "1. How generation has changed over time"))
if period[0] != period[1]:
    st.write(tr(f"Dans les régions choisies, la production passe de **{number(first.production_twh)} à {number(last.production_twh)} TWh** entre {period[0]} et {period[1]}. Cela représente **{number(first.coverage_pct)} % de la consommation au départ, contre {number(last.coverage_pct)} % à la fin**.",
                f"In the selected regions, generation goes from **{number(first.production_twh)} to {number(last.production_twh)} TWh** between {period[0]} and {period[1]}. That's equivalent to **{number(first.coverage_pct)}% of consumption at the start and {number(last.coverage_pct)}% at the end**."))
    previous = annual.iloc[-2]
    if last.coverage_pct < previous.coverage_pct:
        st.caption(tr(f"Ce rapport ne monte pas chaque année : il passe de {number(previous.coverage_pct)} % en {int(previous.year)} à {number(last.coverage_pct)} % en {int(last.year)}.",
                      f"This ratio doesn't rise every year: it goes from {number(previous.coverage_pct)}% in {int(previous.year)} to {number(last.coverage_pct)}% in {int(last.year)}."))
else:
    st.write(tr("Une seule année est sélectionnée. Choisissez plusieurs années pour voir comment les chiffres évoluent.", "You've selected one year. Choose a longer period to see how the figures change."))
st.plotly_chart(trend(annual, metric, unit, lang=lang), use_container_width=True, key="trend")
measure_label = tr("le rapport production / consommation", "the generation-to-consumption ratio") if metric == "coverage_pct" else tr("la production", "generation")
st.caption(tr(f"Description du graphique : la courbe montre {measure_label} année par année, en {unit}, pour la filière « {tech_label.lower()} ». Le tableau en bas de page donne les valeurs exactes.",
              f"Chart description: the line shows {measure_label} year by year, in {unit}, for {tech_label.lower()}. The table at the bottom of the page gives the exact values."))

st.header(tr(f"2. Quelles régions arrivent en tête en {period[1]} ?", f"2. Which regions come out on top in {period[1]}?"))
leader = latest.sort_values(metric, ascending=False).iloc[0]
st.write(tr(f"Avec **{number(leader[metric])} {unit}**, **{leader.region}** arrive en tête de la sélection. Essayez de passer des TWh au pourcentage dans les filtres : produire beaucoup et produire beaucoup par rapport à sa consommation, ce n'est pas la même chose.",
            f"**{leader.region}** comes out on top in this selection, with **{number(leader[metric])} {unit}**. Try switching between TWh and percentages in the filters: a region can produce a lot of electricity and still use much more."))
left, right = st.columns(2)
with left:
    st.plotly_chart(ranking(latest, metric, unit, lang=lang), use_container_width=True, key="ranking")
with right:
    st.plotly_chart(region_map(latest, geography, metric, unit, lang=lang), use_container_width=True, key="map")
st.caption(tr(f"Le classement et la carte montrent les mêmes chiffres, en {unit}, pour {period[1]}. Passez la souris sur une barre ou une région pour voir sa valeur. Les zones blanches sont les régions non sélectionnées.",
              f"The ranking and map show the same figures, in {unit}, for {period[1]}. Hover over a bar or a region to see its value. White areas are regions outside your selection."))

st.header(tr("3. L'éolien et le solaire, séparément", "3. How much comes from wind and solar?") if technology == "Éolien + solaire" else tr(f"3. La production de la filière {tech_label.lower()}", f"3. A closer look at {tech_label.lower()}"))
st.write(tr("Le pourcentage peut changer parce qu'on produit plus, mais aussi parce qu'on consomme moins. Pour voir ce qui se passe du côté de la production, ce graphique montre directement les quantités d'électricité produites.",
            "The percentage can change because generation rises, but also because consumption falls. To focus on generation, this chart shows how much electricity was actually produced."))
st.plotly_chart(production_mix(annual, TECHNOLOGIES[technology], lang=lang), use_container_width=True, key="mix")
st.caption(tr(f"Une barre par année, pour la filière « {tech_label.lower()} ». Le bleu correspond à l'éolien, l'orange au solaire. La hauteur donne la production en TWh : 1 TWh = 1 000 GWh.",
              f"One bar per year, showing {tech_label.lower()}. Blue is wind, orange is solar. The height shows generation in TWh: 1 TWh = 1,000 GWh."))

st.header(tr("Ce qu'on peut retenir", "What this tells us"))
st.write(tr(f"En {period[1]}, la production étudiée représente l'équivalent de **{number(last.coverage_pct)} % de la consommation** des régions choisies. On voit les écarts entre les régions, mais ces chiffres ne disent pas à eux seuls pourquoi ils existent. La météo, les équipements installés et les besoins en électricité comptent aussi.",
            f"In {period[1]}, the generation shown here is equivalent to **{number(last.coverage_pct)}% of consumption** in the selected regions. We can see the differences between regions, but these figures alone don't explain why they exist. Weather, installed equipment and electricity needs also matter."))
st.write(tr("Pour aller plus loin, il faudrait regarder la production heure par heure et les équipements de chaque région. On pourrait alors mieux comprendre ce qui vient des nouvelles installations et ce qui vient des conditions météo.",
            "A useful next step would be to look at hourly generation and the equipment in each region. That would help us understand how much of the change comes from new installations and how much comes from the weather."))

st.header(tr("D'où viennent les chiffres et comment sont-ils calculés ?", "Where do the figures come from, and how are they calculated?"))
q1, q2, q3 = st.columns(3)
q1.metric(tr("Observations sélectionnées", "Selected observations"), str(len(selected)))
q2.metric(tr("Valeurs manquantes utiles", "Missing values in used fields"), str(int(selected[["wind_gwh", "solar_gwh", "consumption_gwh"]].isna().sum().sum())))
q3.metric(tr("Doublons région / année", "Duplicate region / year pairs"), str(int(selected.duplicated(["code", "year"]).sum())))
st.write(tr("Les données couvrent 13 régions sur 12 ans, soit 156 lignes. Pour chaque région et chaque année, on rapproche la production et la consommation grâce au code INSEE. Chaque paire région–année n'apparaît qu'une fois. Il ne manque aucune valeur dans les colonnes utilisées, donc rien n'a été remplacé par une estimation. Les productions sont positives ou nulles, et la consommation est toujours supérieure à zéro.",
            "The data covers 13 regions over 12 years, giving 156 rows. Generation and consumption are matched using the INSEE region code and the year. Each region–year pair appears only once. None of the fields used has missing values, so nothing has been filled in with an estimate. Generation is zero or positive, and consumption is always above zero."))
st.write(tr("L'étude s'arrête en 2024, car les chiffres de consommation sont définitifs jusqu'à cette année-là. Au moment du téléchargement, ceux de 2025 étaient encore au statut « consolidé ». Ils ne sont donc pas utilisés ici. Les autres énergies présentes dans le fichier, comme le nucléaire, restent aussi en dehors de l'étude.",
            "The study stops in 2024 because consumption figures are final up to that year. When the data was downloaded, the 2025 figures were still marked as 'consolidated', so they aren't included here. Other energy sources in the file, such as nuclear, are also outside this study."))
st.write(tr("Quelques détails à garder en tête : la consommation inclut les pertes d'électricité et n'est pas ajustée pour tenir compte de la météo. ODRE a aussi revu les chiffres de l'électricité solaire consommée directement par ses producteurs sur 2022–2024 ; cette correction est déjà dans les fichiers. Pour les unités, on suit les colonnes du CSV, indiquées en GWh, même si la description du portail mentionne aussi les TWh.",
            "A few details matter: consumption includes electricity losses and isn't adjusted for the weather. ODRE also revised the figures for solar electricity used directly by its producers in 2022–2024; that correction is already in these files. For units, we use GWh as shown in the CSV columns, even though the portal description also mentions TWh."))
st.write(tr("Pour calculer le rapport, on additionne d'abord les productions des régions choisies, puis on divise par leur consommation totale et on multiplie par 100. On ne fait donc pas la moyenne de leurs pourcentages. Ces totaux annuels ne montrent pas les pics de consommation, les importations ou les émissions de CO₂. Les données sont regroupées par région et ne contiennent pas d'informations personnelles.",
            "To calculate the ratio, we first add up generation in the selected regions, divide by their total consumption, then multiply by 100. We don't average the regional percentages. These yearly totals don't show peak demand, imports or CO₂ emissions. The data is grouped by region and contains no personal information."))

with st.expander(tr("Voir les tableaux et télécharger les données", "View the tables and download the data")):
    st.write(tr("Les chiffres année par année", "The figures, year by year"))
    readable = annual[["year", "production_twh", "consumption_gwh", "coverage_pct"]].rename(columns={"year": tr("Année", "Year"), "production_twh": tr("Production (TWh)", "Generation (TWh)"), "consumption_gwh": tr("Consommation (GWh)", "Consumption (GWh)"), "coverage_pct": tr("Rapport (%)", "Ratio (%)")})
    st.dataframe(readable, hide_index=True, width="stretch")
    st.write(tr(f"Valeurs régionales en {period[1]}", f"Regional values in {period[1]}"))
    st.dataframe(latest[["region", "wind_gwh", "solar_gwh", "consumption_gwh", "coverage_pct"]].rename(columns={"region": tr("Région", "Region"), "wind_gwh": tr("Éolien (GWh)", "Wind (GWh)"), "solar_gwh": tr("Solaire (GWh)", "Solar (GWh)"), "consumption_gwh": tr("Consommation (GWh)", "Consumption (GWh)"), "coverage_pct": tr("Rapport (%)", "Ratio (%)")}), hide_index=True, width="stretch")
    st.download_button(tr("Télécharger les données filtrées (CSV)", "Download filtered data (CSV)"), selected.to_csv(index=False).encode("utf-8-sig"), file_name="electricite_regions_selection.csv", mime="text/csv")

with st.expander(tr("Sources et définitions", "Sources and definitions")):
    st.markdown(tr("Les données viennent de **RTE**. Elles sont disponibles sur Open Data Réseaux Énergies (ODRE) et référencées sur data.gouv.fr. La Licence Ouverte 2.0 permet de les réutiliser en citant la source.",
                   "The data comes from **RTE**. It's available on Open Data Réseaux Énergies (ODRE) and listed on data.gouv.fr. The French Open Licence 2.0 allows reuse as long as the source is credited."))
    for source in sources["datasets"]:
        st.markdown(f"[{source['name']}]({source['portal_url']}) · [{tr('Ressource ODRE', 'ODRE resource')}]({source['source_url']})")
    st.caption(tr("Copie téléchargée le 20 octobre 2026. Contours géographiques inclus dans la source ODRE : attribution INSEE, IGN, NaturalEarth. Licence Ouverte 2.0.",
                  "Snapshot downloaded on 20 October 2026. Geographic boundaries included in the ODRE source: attribution INSEE, IGN, NaturalEarth. French Open Licence 2.0."))
    st.caption(tr("Sources, dates, empreintes des fichiers et transformations : data/sources.json et scripts/prepare_data.py dans le dossier du projet.",
                  "Sources, dates, file hashes and transformations: data/sources.json and scripts/prepare_data.py in the project folder."))

st.divider()
st.caption(tr("Projet individuel de data storytelling · Roy TAMWO · 20230840 · I2-DE_02 · EFREI · 2026–2027",
              "Individual data storytelling project · Roy TAMWO · 20230840 · I2-DE_02 · EFREI · 2026–2027"))
