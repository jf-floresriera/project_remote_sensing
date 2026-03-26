import ee

ee.Initialize(project='wide-origin-466923-d8')

# Tomar una imagen original al azar (del inicio del año)
asset_id = 'projects/wide-origin-466923-d8/assets/GPR_LAI_meta_2023/LAI_2023-01-25'
img = ee.Image(asset_id)

print("\n--- RADIOGRAFÍA DE LA IMAGEN ---")
print("1. Nombres de TODAS las bandas:")
print(img.bandNames().getInfo())

print("\n2. Metadatos (Properties) guardados en la imagen:")
propiedades = img.propertyNames().getInfo()
print(propiedades)

print("\n--------------------------------")

