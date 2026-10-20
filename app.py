"""Projet individuel de data storytelling - Roy TAMWO, I2-DE_02."""
import streamlit as st

from utils.data import load_data, add_indicators, annual_totals, french, TECHNOLOGIES
from utils.charts import trend, ranking, region_map, production_mix

st.set_page_config(page_title="Éolien et solaire | Roy TAMWO", layout="wide")

try:
    data, geography, sources = load_data()
except (ValueError, OSError) as error:
    st.error(f"Impossible de charger les données : {error}")
    st.stop()

with st.sidebar:
    st.header("Explorer les données")
    st.caption("Roy TAMWO · 20230840 · I2-DE_02")
    regions = st.multiselect("Régions", sorted(data.region.unique()),
                             default=sorted(data.region.unique()), key="regions")
    period = st.slider("Période", 2013, 2024, (2013, 2024), key="period")
    technology = st.selectbox("Filière", list(TECHNOLOGIES), key="technology")
    indicator = st.selectbox("Indicateur des graphiques", ["Rapport à la consommation (%)", "Production (TWh)"], key="indicator")
    st.caption("La carte, le classement et les chiffres clés utilisent la dernière année de la période.")
    st.divider()
    st.caption("Sources : RTE / ODRE, référencées sur data.gouv.fr. Copie téléchargée le 20 octobre 2026. Licence Ouverte 2.0.")

st.title("Éolien et solaire")
st.subheader("Quelle place dans la consommation des régions ?")
st.write("En France, la production éolienne et solaire a augmenté depuis 2013. Mais les régions n'ont pas le même profil. Ce tableau de bord compare les volumes produits et leur rapport à la consommation annuelle, pour un public qui souhaite comprendre ces écarts sans entrer dans les détails techniques du réseau.")

if not regions:
    st.info("Choisissez au moins une région dans le menu de gauche.")
    st.stop()

selected = data[data.region.isin(regions) & data.year.between(*period)].copy()
annual = annual_totals(selected, technology)
first, last = annual.iloc[0], annual.iloc[-1]
latest = add_indicators(selected[selected.year == period[1]], technology)
metric = "coverage_pct" if indicator.startswith("Rapport") else "production_twh"
unit = "%" if metric == "coverage_pct" else "TWh"
scope = "13 régions métropolitaines, Corse incluse" if len(regions) == 13 else f"{len(regions)} région(s) sélectionnée(s)"
st.caption(f"{scope} · {period[0]}–{period[1]} · {technology}")

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Production {technology.lower()}", f"{french(last.production_twh)} TWh")
c2.metric("Consommation d'électricité", f"{french(last.consumption_gwh / 1000)} TWh")
c3.metric("Rapport production / consommation", f"{french(last.coverage_pct)} %",
          help="100 × production de la filière / consommation brute d'électricité. Les volumes sont annuels.")
change = last.coverage_pct - first.coverage_pct
c4.metric(f"Écart depuis {period[0]}", f"{french(change, 1)} points" if period[0] != period[1] else "Une seule année")

st.info("Lecture : un rapport de 20 % signifie que la production annuelle étudiée équivaut à un cinquième de la consommation annuelle. Les échanges entre régions et les variations horaires empêchent d'en déduire une autonomie électrique.")

st.header("1. Une progression à regarder sur plusieurs années")
if period[0] != period[1]:
    st.write(f"Sur le périmètre choisi, la production passe de **{french(first.production_twh)} à {french(last.production_twh)} TWh**. Le rapport à la consommation passe de **{french(first.coverage_pct)} % à {french(last.coverage_pct)} %**.")
    previous = annual.iloc[-2]
    if last.coverage_pct < previous.coverage_pct:
        st.caption(f"La progression n'est pas continue : le rapport baisse de {french(previous.coverage_pct)} % en {int(previous.year)} à {french(last.coverage_pct)} % en {int(last.year)}.")
else:
    st.write("Une seule année est sélectionnée. Élargissez la période pour étudier une évolution.")
st.plotly_chart(trend(annual, metric, unit), use_container_width=True, key="trend")
st.caption(f"Description du graphique : évolution annuelle de {technology.lower()}, exprimée en {unit}, dans les régions sélectionnées. Les valeurs exactes figurent dans le tableau accessible en bas de page.")

st.header(f"2. Des profils régionaux différents en {period[1]}")
leader = latest.sort_values(metric, ascending=False).iloc[0]
st.write(f"**{leader.region}** affiche la valeur la plus élevée parmi les régions choisies : **{french(leader[metric])} {unit}**. Le classement change selon que l'on compare des volumes ou un rapport à la consommation.")
left, right = st.columns([1, 1])
with left:
    st.plotly_chart(ranking(latest, metric, unit), use_container_width=True, key="ranking")
with right:
    st.plotly_chart(region_map(latest, geography, metric, unit), use_container_width=True, key="map")
st.caption(f"Description : le classement et la carte représentent le même indicateur ({unit}) pour la dernière année sélectionnée. Survolez une barre ou une région pour lire sa valeur. Les zones blanches ne font pas partie de la sélection.")

st.header("3. Séparer l'éolien et le solaire aide à comprendre le total" if technology == "Éolien + solaire" else f"3. Les volumes produits : {technology.lower()}")
st.write("Le rapport à la consommation dépend à la fois de la production et de la demande. Ce graphique revient aux volumes produits pour rendre leur évolution plus facile à lire.")
st.plotly_chart(production_mix(annual, TECHNOLOGIES[technology]), use_container_width=True, key="mix")
st.caption(f"Description : chaque barre représente une année. Filière affichée : {technology.lower()}. L'éolien est bleu, le solaire orange. L'axe vertical mesure la production en TWh (1 TWh = 1 000 GWh).")

st.header("Ce que l'on peut en retenir")
st.write(f"Pour {scope.lower()}, le rapport annuel atteint **{french(last.coverage_pct)} % en {period[1]}**. Comparer les régions aide à situer la production, mais ne suffit pas à expliquer les écarts : il faudrait aussi connaître la puissance installée, la météo et la demande locale.")
st.write("Pour prolonger l'analyse, je regarderais les séries horaires et les capacités installées. Cela permettrait de distinguer l'effet des nouveaux équipements de celui des conditions de production.")

st.header("Qualité des données et méthode")
q1, q2, q3 = st.columns(3)
q1.metric("Observations sélectionnées", str(len(selected)))
q2.metric("Valeurs manquantes utiles", str(int(selected[["wind_gwh", "solar_gwh", "consumption_gwh"]].isna().sum().sum())))
q3.metric("Doublons région / année", str(int(selected.duplicated(["code", "year"]).sum())))
st.write("Le panel complet contient 156 observations : 13 régions sur 12 années. Les deux jeux ODRE sont joints par code INSEE et année, avec une seule ligne de chaque côté. Les volumes retenus sont positifs ou nuls et la consommation est strictement positive. Aucune valeur utile n'a été imputée.")
st.write("Le périmètre s'arrête en 2024 : le statut RTE de la consommation est définitif pour toutes les observations retenues. Les données 2025, consolidées au téléchargement, sont exclues. Les autres filières du fichier de production ne sont pas utilisées.")
st.write("La consommation brute inclut les pertes et n'est pas corrigée du climat. ODRE signale une révision de l'autoconsommation photovoltaïque sur 2022–2024, déjà intégrée à cette copie. Les calculs suivent les colonnes explicitement libellées en GWh, malgré une mention générale en TWh dans la description du portail.")
st.write("Calcul : rapport (%) = 100 × somme des productions sélectionnées / somme des consommations. Les rapports régionaux ne sont pas moyennés. Les volumes annuels ne décrivent ni les pointes de demande, ni les importations, ni les émissions de CO₂. Ces données agrégées ne contiennent aucune information personnelle.")

with st.expander("Tableaux accessibles et téléchargement"):
    st.write("Série annuelle du périmètre sélectionné")
    readable = annual[["year", "production_twh", "consumption_gwh", "coverage_pct"]].rename(columns={"year": "Année", "production_twh": "Production (TWh)", "consumption_gwh": "Consommation (GWh)", "coverage_pct": "Rapport (%)"})
    st.dataframe(readable, hide_index=True, width="stretch")
    st.write(f"Valeurs régionales en {period[1]}")
    st.dataframe(latest[["region", "wind_gwh", "solar_gwh", "consumption_gwh", "coverage_pct"]].rename(columns={"region": "Région", "wind_gwh": "Éolien (GWh)", "solar_gwh": "Solaire (GWh)", "consumption_gwh": "Consommation (GWh)", "coverage_pct": "Rapport (%)"}), hide_index=True, width="stretch")
    st.download_button("Télécharger les données filtrées (CSV)", selected.to_csv(index=False).encode("utf-8-sig"), file_name="electricite_regions_selection.csv", mime="text/csv")

with st.expander("Sources et définitions"):
    st.markdown("**Producteur : RTE.** Portail de diffusion : Open Data Réseaux Énergies (ODRE). Jeux référencés sur data.gouv.fr. Réutilisation sous Licence Ouverte 2.0, avec attribution.")
    for source in sources["datasets"]:
        st.markdown(f"[{source['name']}]({source['portal_url']}) · [Ressource ODRE]({source['source_url']})")
    st.caption("Contours géographiques inclus dans la source ODRE : attribution INSEE, IGN, NaturalEarth. Licence Ouverte 2.0.")
    st.caption("Sources, dates, empreintes des fichiers et transformations : data/sources.json et scripts/prepare_data.py dans le dossier du projet.")

st.divider()
st.caption("Projet individuel de data storytelling · Roy TAMWO · 20230840 · I2-DE_02 · EFREI · 2026")
