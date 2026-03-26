import ee

ee.Initialize(project='wide-origin-466923-d8')

# Leer la primera imagen de tu colección original
folder = 'projects/wide-origin-466923-d8/assets/GPR_LAI_meta_2023'
assets = ee.data.listAssets({'parent': folder})['assets']
primera_imagen = ee.Image(assets[0]['name'])

# Imprimir los nombres reales de las bandas
print("Las bandas que tiene tu imagen son:")
print(primera_imagen.bandNames().getInfo())
