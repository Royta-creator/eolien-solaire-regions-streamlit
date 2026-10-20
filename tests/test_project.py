"""Contrôles des calculs et des interactions principales.

Lancer depuis le dossier du projet : python -m unittest discover -s tests -v
"""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.data import load_data, annual_totals, add_indicators, TECHNOLOGIES
from utils.charts import region_map, production_mix


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.geo, cls.sources = load_data()

    def test_selected_values_match_original_exports(self):
        """La normalisation conserve les volumes source et les bonnes clés."""
        production = pd.read_csv(ROOT / "data/production_brute.csv", sep=";", dtype={"Code INSEE région": str})
        consumption = pd.read_csv(ROOT / "data/consommation_brute.csv", sep=";", dtype={"Code INSEE région": str})
        production = production.set_index(["Année", "Code INSEE région"])
        consumption = consumption.set_index(["Année", "Code INSEE région"])
        for row in self.data.itertuples():
            key = (row.year, row.code)
            self.assertEqual(row.wind_gwh, production.loc[key, "Production éolienne (GWh)"])
            self.assertEqual(row.solar_gwh, production.loc[key, "Production solaire (GWh)"])
            self.assertEqual(row.consumption_gwh, consumption.loc[key, "Consommation brute électricité (GWh) - RTE"])
            self.assertEqual("Définitif", consumption.loc[key, "Statut - RTE"])

    def test_aggregation_uses_ratio_of_sums(self):
        """Deux régions de poids différents distinguent ratio et moyenne."""
        frame = pd.DataFrame({"year": [2024, 2024], "wind_gwh": [1., 90.],
                              "solar_gwh": [0., 0.], "consumption_gwh": [10., 100.]})
        result = annual_totals(frame, "Éolien").iloc[0]
        self.assertAlmostEqual(result.coverage_pct, 100 * 91 / 110)
        self.assertNotAlmostEqual(result.coverage_pct, 50.)
        self.assertAlmostEqual(result.production_twh, .091)

    def test_known_2024_totals(self):
        latest = self.data[self.data.year == 2024]
        result = annual_totals(latest, "Éolien + solaire").iloc[0]
        self.assertEqual(result.production_gwh, latest.wind_gwh.sum() + latest.solar_gwh.sum())
        self.assertAlmostEqual(result.production_twh * 1000, result.production_gwh)
        for technology, columns in TECHNOLOGIES.items():
            selected = add_indicators(latest, technology)
            self.assertAlmostEqual(selected.production_gwh.sum(), latest[columns].sum().sum())

    def test_map_keeps_filtered_codes_and_values(self):
        selected = add_indicators(self.data[(self.data.year == 2024) & self.data.code.isin(["11", "94"])], "Solaire")
        chart = region_map(selected, self.geo, "coverage_pct", "%")
        trace = chart.data[0]
        self.assertEqual(set(trace.locations), {"11", "94"})
        self.assertEqual(list(trace.z), selected.coverage_pct.tolist())
        feature_codes = {feature["properties"]["code"] for feature in trace.geojson["features"]}
        self.assertTrue(set(trace.locations).issubset(feature_codes))
        self.assertEqual(chart.layout.map.style, "white-bg")

    def test_mix_respects_selected_technology(self):
        annual = annual_totals(self.data, "Solaire")
        chart = production_mix(annual, TECHNOLOGIES["Solaire"])
        self.assertEqual(len(chart.data), 1)
        self.assertEqual(chart.data[0].name, "Solaire")
        self.assertEqual(list(chart.data[0].y), (annual.solar_gwh / 1000).tolist())

    def test_source_files_reproduce_the_snapshot(self):
        """Le script peut reconstruire le panel et la géographie depuis les bruts."""
        with tempfile.TemporaryDirectory(prefix="streamlit-test-") as folder:
            target = Path(folder)
            for name in ["production_brute.csv", "consommation_brute.csv"]:
                shutil.copy2(ROOT / "data" / name, target / name)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/prepare_data.py"), "--data-dir", str(target)],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in ["normalized.csv", "regions.geojson", "annual_indicators.csv", "regional_indicators_2024.csv"]:
                self.assertEqual((ROOT / "data" / name).read_bytes(), (target / name).read_bytes(), name)


class InterfaceTests(unittest.TestCase):
    def app(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0)
        return app

    def test_default_view(self):
        app = self.app()
        self.assertEqual(len(app.get("plotly_chart")), 4)
        self.assertEqual(len(app.sidebar.multiselect[0].value), 13)

    def test_empty_regions_shows_guidance(self):
        app = self.app()
        app.sidebar.multiselect[0].set_value([]).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.get("plotly_chart")), 0)
        self.assertTrue(any("au moins une région" in element.value for element in app.info))

    def test_one_year_and_one_region(self):
        app = self.app()
        app.sidebar.multiselect[0].set_value(["Corse"])
        app.sidebar.slider[0].set_value((2024, 2024))
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.get("plotly_chart")), 4)
        self.assertEqual(app.metric[3].value, "Une seule année")
        self.assertEqual(app.metric[4].value, "1")

    def test_technology_updates_kpis(self):
        app = self.app()
        app.sidebar.selectbox[0].set_value("Solaire").run()
        self.assertEqual(len(app.exception), 0)
        data, _, _ = load_data()
        expected = data[data.year == 2024].solar_gwh.sum() / 1000
        observed = float(app.metric[0].value.replace(" TWh", "").replace(" ", "").replace(",", "."))
        self.assertAlmostEqual(observed, expected, delta=.051)
        self.assertIn("solaire", app.metric[0].label)

    def test_volume_indicator(self):
        app = self.app()
        app.sidebar.selectbox[1].set_value("Production (TWh)").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.get("plotly_chart")), 4)
        self.assertTrue(any("TWh" in element.value and "Description du graphique" in element.value for element in app.caption))


if __name__ == "__main__":
    unittest.main()
