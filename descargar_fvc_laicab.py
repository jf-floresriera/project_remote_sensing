import ee
import geemap
import os

try:
    ee.Initialize(project='wide-origin-466923-d8')
except:
    ee.Authenticate()
    ee.Initialize(project='wide-origin-466923-d8')

region = ee.Geometry.Rectangle([-72.05, 4.1, -71.4, 4.5])

# Las fechas de tu ciclo
fechas = ['2023-01-15', '2023-05-25', '2023-07-09', '2023-10-17']
variables = ['FVC', 'laiCab']

carpeta_salida = 'Mapas_Figura6'
os.makedirs(carpeta_salida, exist_ok=True)

print("Iniciando descarga de las fechas para FVC y laiCab...")

for var in variables:
    for fecha in fechas:
        # ID para gap-filled (la que nos interesa para la figura 6 panel)
        id_gf = f'projects/wide-origin-466923-d8/assets/GPR_{var}_meta_2023_gapfilled/{var}_gf_{fecha}'
        
        nombre = f"{var}_gf_{fecha}.tif"
        ruta = os.path.join(carpeta_salida, nombre)
        
        if not os.path.exists(ruta):
            print(f"Descargando {nombre}...")
            try:
                img = ee.Image(id_gf)
                geemap.download_ee_image(image=img, filename=ruta, scale=20, region=region, crs='EPSG:4326')
            except Exception as e:
                print(f"❌ Error con {nombre}: {e}")
        else:
            print(f"⏭️ {nombre} ya estaba descargado.")

print(f"\n¡Listo! Revisa la carpeta '{carpeta_salida}'.")


