import ee
import pandas as pd

# Autenticar (solo la primera vez)
ee.Authenticate()
ee.Initialize(project='wide-origin-466923-d8')

region = ee.Geometry.Rectangle([-72.062937, 4.206600, -71.492754, 4.5])

variables = ['LAI', 'FVC', 'laiCab', 'NDVI']

cols_keep = ['variable', 'municipio', 'intervalo', 'periodo', 'area_ha',
             'sos_mean', 'sos_stdDev',
             'pos_mean', 'pos_stdDev',
             'eos_mean', 'eos_stdDev',
             'los_mean', 'los_stdDev']

dfs = []
for var in variables:
    asset_id = f'projects/wide-origin-466923-d8/assets/LSP_{var}_meta_2023'
    fc = ee.FeatureCollection(asset_id).filterBounds(region)

    # Descargar como DataFrame directamente
    features = fc.getInfo()['features']
    rows = [f['properties'] for f in features]
    df = pd.DataFrame(rows)
    df['variable'] = var
    dfs.append(df)
    print(f"✅ {var}: {len(df)} parcelas descargadas")

# Unir todo en un solo CSV
df_all = pd.concat(dfs, ignore_index=True)

# Guardar solo columnas relevantes
df_all = df_all[[c for c in cols_keep if c in df_all.columns]]
df_all.to_csv('LSP_meta_2023_todas_variables.csv', index=False)
print(f"\n✅ Guardado: LSP_meta_2023_todas_variables.csv")
print(f"   Total filas: {len(df_all)}")
print(df_all.groupby('variable')[['sos_mean','pos_mean','eos_mean','los_mean']].mean().round(1))
