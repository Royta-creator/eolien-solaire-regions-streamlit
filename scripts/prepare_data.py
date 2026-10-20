"""Prepare a fixed 2013–2024 snapshot from the unmodified ODRE CSV exports."""
from pathlib import Path
import hashlib
import argparse
import json
import pandas as pd

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parent.parent / 'data', help='Directory containing the original ODRE CSV files')
ROOT = parser.parse_args().data_dir.resolve()
START_YEAR, END_YEAR = 2013, 2024
PRODUCTION_COLUMNS = {
    'Année': 'year', 'Code INSEE région': 'code', 'Région': 'region',
    'Production nucléaire (GWh)': 'nuclear', 'Production thermique (GWh)': 'thermal',
    'Production hydraulique (GWh)': 'hydro', 'Production éolienne (GWh)': 'wind_gwh',
    'Production solaire (GWh)': 'solar_gwh', 'Production bioénergies (GWh)': 'bioenergy',
}

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

prod = pd.read_csv(ROOT / 'production_brute.csv', sep=';', dtype={'Code INSEE région':str})
conso = pd.read_csv(ROOT / 'consommation_brute.csv', sep=';', dtype={'Code INSEE région':str})
assert not prod.duplicated(['Année', 'Code INSEE région']).any()
assert not conso.duplicated(['Année', 'Code INSEE région']).any()
prod_sel = prod[prod['Année'].between(START_YEAR, END_YEAR)].copy()
conso_sel = conso[conso['Année'].between(START_YEAR, END_YEAR)].copy()
assert set(conso_sel['Statut - RTE']) == {'Définitif'}
assert len(prod_sel) == len(conso_sel) == 13 * (END_YEAR-START_YEAR+1)

clean = prod_sel.rename(columns=PRODUCTION_COLUMNS)[list(PRODUCTION_COLUMNS.values())].copy()
coords = prod_sel['Géo-point région'].str.split(',', expand=True).astype(float)
clean['lat'], clean['lon'] = coords[0], coords[1]
cc = conso_sel.rename(columns={
    'Année':'year','Code INSEE région':'code',
    'Consommation brute électricité (GWh) - RTE':'consumption_gwh',
})[['year','code','consumption_gwh']]
clean = clean.merge(cc, on=['year','code'], validate='one_to_one', how='left')
clean = clean[['year','code','region','wind_gwh','solar_gwh','consumption_gwh','lat','lon']]
clean = clean.sort_values(['year','code']).reset_index(drop=True)
required = ['year','code','region','wind_gwh','solar_gwh','consumption_gwh','lat','lon']
assert clean[required].notna().all().all()
assert (clean[['wind_gwh','solar_gwh']] >= 0).all().all()
assert (clean['consumption_gwh'] > 0).all()
clean.to_csv(ROOT/'normalized.csv',index=False,encoding='utf-8',lineterminator='\n',float_format='%.9f')

features=[]
for code, group in prod_sel.groupby('Code INSEE région',sort=True):
    assert group['Géo-shape région'].nunique() == 1
    assert group['Géo-point région'].nunique() == 1
    row=group.iloc[0]
    features.append({'type':'Feature','id':code,'properties':{'code':code,'region':row['Région']},'geometry':json.loads(row['Géo-shape région'])})
geojson={'type':'FeatureCollection','features':features}
(ROOT/'regions.geojson').write_text(json.dumps(geojson,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')

quality={
    'production_raw_rows':len(prod),'consumption_raw_rows':len(conso),
    'rows_after_join':len(clean),'regions':int(clean.code.nunique()),
    'first_year':START_YEAR,'last_year':END_YEAR,
    'excluded_production_rows':int(len(prod)-len(prod_sel)),
    'excluded_consumption_rows':int(len(conso)-len(conso_sel)),
    'raw_production_duplicate_keys':int(prod.duplicated(['Année','Code INSEE région']).sum()),
    'raw_consumption_duplicate_keys':int(conso.duplicated(['Année','Code INSEE région']).sum()),
    'missing_by_column':{k:int(v) for k,v in clean.isna().sum().items()},
    'source_production_missing_by_column':{k:int(v) for k,v in prod.isna().sum().items()},
    'source_consumption_missing_by_column':{k:int(v) for k,v in conso.isna().sum().items()},
    'missing_nuclear_regions':sorted(prod_sel.loc[prod_sel['Production nucléaire (GWh)'].isna(),'Région'].unique().tolist()),
    'missing_value_policy':'Aucune imputation. Les 72 cases nucléaires vides restent dans le fichier brut et cette variable est exclue du fichier analytique. Les calculs du projet utilisent uniquement éolien, solaire et consommation, sans données manquantes dans le périmètre 2013–2024.',
    'consumption_status':'Définitif pour les 156 observations retenues; 2025 consolidé exclu.',
    'join_validation':'one_to_one sur année et code INSEE région',
    'negative_wind_solar_values':int((clean[['wind_gwh','solar_gwh']] < 0).sum().sum()),
    'nonpositive_consumption_values':int((clean.consumption_gwh<=0).sum()),
    'regions_per_year':{str(k):int(v) for k,v in clean.groupby('year').code.nunique().items()},
    'files_sha256':{name:sha256(ROOT/name) for name in ['production_brute.csv','consommation_brute.csv','normalized.csv','regions.geojson']},
}
(ROOT/'quality.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

annual=clean.groupby('year')[['wind_gwh','solar_gwh','consumption_gwh']].sum()
annual['wind_solar_gwh']=annual.wind_gwh+annual.solar_gwh
annual['coverage_pct']=annual.wind_solar_gwh/annual.consumption_gwh*100
annual.to_csv(ROOT/'annual_indicators.csv',encoding='utf-8',lineterminator='\n')
latest=clean[clean.year.eq(END_YEAR)].copy()
latest['wind_solar_gwh']=latest.wind_gwh+latest.solar_gwh
latest['coverage_pct']=latest.wind_solar_gwh/latest.consumption_gwh*100
baseline=clean[clean.year.eq(START_YEAR)].set_index('code')
latest['baseline_wind_solar_gwh']=latest.code.map(baseline.wind_gwh+baseline.solar_gwh)
latest['growth_pct']=(latest.wind_solar_gwh/latest.baseline_wind_solar_gwh-1)*100
latest['baseline_coverage_pct']=latest.code.map((baseline.wind_gwh+baseline.solar_gwh)/baseline.consumption_gwh*100)
latest['gain_percentage_points']=latest.coverage_pct-latest.baseline_coverage_pct
latest.sort_values('coverage_pct',ascending=False).to_csv(ROOT/'regional_indicators_2024.csv',index=False,encoding='utf-8',lineterminator='\n')
first,last=annual.loc[START_YEAR],annual.loc[END_YEAR]
findings={
    'scope':'France métropolitaine, Corse comprise, 13 régions, 2013–2024; consommation brute, pertes comprises, non corrigée du climat.',
    'national_2013':first.to_dict(),'national_2024':last.to_dict(),
    'wind_solar_growth_pct':(last.wind_solar_gwh/first.wind_solar_gwh-1)*100,
    'wind_solar_multiplier':last.wind_solar_gwh/first.wind_solar_gwh,
    'coverage_gain_percentage_points':last.coverage_pct-first.coverage_pct,
    'consumption_change_pct':(last.consumption_gwh/first.consumption_gwh-1)*100,
    'top_coverage_2024':latest.sort_values('coverage_pct',ascending=False)[['region','coverage_pct','wind_solar_gwh','consumption_gwh']].head(3).to_dict('records'),
    'bottom_coverage_2024':latest.sort_values('coverage_pct')[['region','coverage_pct','wind_solar_gwh','consumption_gwh']].head(3).to_dict('records'),
    'top_volume_2024':latest.sort_values('wind_solar_gwh',ascending=False)[['region','wind_solar_gwh']].head(3).to_dict('records'),
    'definitions':{
       'coverage_pct':'100 × somme des productions éolienne et solaire (GWh) / somme de la consommation brute électricité (GWh), pour la même année et les mêmes régions. Une agrégation est un ratio de sommes, jamais la moyenne des ratios régionaux.',
       'interpretation':'Rapport annuel de volumes, pas un indicateur d’autonomie électrique, pas la part de ces filières dans l’électricité effectivement consommée. Le réseau assure des échanges et la simultanéité n’est pas étudiée.',
    }
}
(ROOT/'findings.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(findings,ensure_ascii=False,indent=2))
