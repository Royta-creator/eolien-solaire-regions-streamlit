"""Chargement local, contrôles et calculs communs au tableau de bord."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
VALUES = ["wind_gwh", "solar_gwh", "consumption_gwh"]
TECHNOLOGIES = {
    "Éolien + solaire": ["wind_gwh", "solar_gwh"],
    "Éolien": ["wind_gwh"],
    "Solaire": ["solar_gwh"],
}


@st.cache_data(show_spinner=False)
def load_data():
    """Aucune connexion nécessaire : le rendu utilise une copie datée."""
    data = pd.read_csv(ROOT / "data" / "normalized.csv", dtype={"code": str})
    needed = ["year", "code", "region", *VALUES, "lat", "lon"]
    if set(needed) - set(data.columns):
        raise ValueError("Le fichier de données ne respecte pas le schéma attendu.")
    for col in ["year", *VALUES, "lat", "lon"]:
        data[col] = pd.to_numeric(data[col], errors="raise")
    if data[needed].isna().any().any():
        raise ValueError("Valeur manquante dans les champs utilisés.")
    if data.duplicated(["year", "code"]).any():
        raise ValueError("Plusieurs observations pour une même région et année.")
    if (data[VALUES] < 0).any().any() or (data.consumption_gwh <= 0).any():
        raise ValueError("Volumes incohérents ou consommation nulle.")
    expected = pd.MultiIndex.from_product([range(2013, 2025), data.code.unique()])
    observed = pd.MultiIndex.from_frame(data[["year", "code"]])
    if len(data.code.unique()) != 13 or len(expected.difference(observed)):
        raise ValueError("Le panel attendu de 13 régions sur 2013–2024 est incomplet.")
    geo = json.loads((ROOT / "data" / "regions.geojson").read_text(encoding="utf-8"))
    if set(data.code) - {f["properties"]["code"] for f in geo["features"]}:
        raise ValueError("Une région manque dans la carte.")
    sources = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
    return data.sort_values(["year", "code"]), geo, sources


def add_indicators(frame, technology):
    result = frame.copy()
    result["production_gwh"] = result[TECHNOLOGIES[technology]].sum(axis=1, min_count=1)
    result["production_twh"] = result.production_gwh / 1000
    result["coverage_pct"] = result.production_gwh / result.consumption_gwh * 100
    return result


def annual_totals(frame, technology):
    """Le rapport national est un rapport de sommes, pas une moyenne de régions."""
    totals = frame.groupby("year", as_index=False)[VALUES].sum(min_count=1)
    return add_indicators(totals, technology)


def french(value, decimals=1):
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")
