import ee
import geemap
import os

try:
    ee.Initialize(project='wide-origin-466923-d8')
except:
    ee.Authenticate()
    ee.Initialize(project='wide-origin-466923-d8')

region = ee.Geometry.Rectangle([-72.05, 4.1, -71.4, 4.5])

# Fechas clave que vimos en la fenología
fechas = ['2023-01-15', '2023-05-25', '2023-07-09', '2023-10-17']

carpeta_salida = 'Mapas_Figura6'
os.makedirs(carpeta_salida, exist_ok=True)

print("Iniciando descarga de las 4 fechas para la Figura 6...")

for fecha in fechas:
    # IDs de la original y la gapfilled
    id_orig = f'projects/wide-origin-466923-d8/assets/GPR_LAI_meta_2023/LAI_{fecha}'
    id_gf = f'projects/wide-origin-466923-d8/assets/GPR_LAI_meta_2023_gapfilled/LAI_gf_{fecha}'
    
    for asset_id in [id_orig, id_gf]:
        nombre = asset_id.split('/')[-1]
        ruta = os.path.join(carpeta_salida, f'{nombre}.tif')
        
        print(f"Descargando {nombre}...")
        try:
            # Como vimos que pesan unos 19MB, podemos usar la descarga directa que es rapidísima
            img = ee.Image(asset_id)
            geemap.download_ee_image(image=img, filename=ruta, scale=20, region=region, crs='EPSG:4326')
        except Exception as e:
            print(f"❌ Error con {nombre}: {e}")

print(f"\n¡Listo! Revisa la carpeta '{carpeta_salida}'.")
