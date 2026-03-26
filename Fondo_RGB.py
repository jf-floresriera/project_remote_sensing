import ee
import geemap
import os

try:
    ee.Initialize(project='wide-origin-466923-d8')
except:
    ee.Authenticate()
    ee.Initialize(project='wide-origin-466923-d8')

# Mismo zoom que usamos en los mapas
region = ee.Geometry.Rectangle([-72.05, 4.1, -71.4, 4.5])

# Sentinel-2 verano 2023 (poca nube)
s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(region)
      .filterDate('2023-06-01', '2023-08-31')
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
      .median())

# --- OPCIÓN 1: RGB Natural (B4=Rojo, B3=Verde, B2=Azul) ---
rgb_natural = s2.select(['B4', 'B3', 'B2'])

# --- OPCIÓN 2: Falso Color (B8=NIR, B4=Rojo, B3=Verde) resalta más los cultivos ---
rgb_falso = s2.select(['B8', 'B4', 'B3'])

os.makedirs('Mapas_Figura6', exist_ok=True)

print("Descargando fondo RGB natural...")
geemap.download_ee_image(
    image=rgb_natural,
    filename='Mapas_Figura6/fondo_RGB_natural.tif',
    scale=20,
    region=region,
    crs='EPSG:4326'
)

print("Descargando fondo falso color (NIR)...")
geemap.download_ee_image(
    image=rgb_falso,
    filename='Mapas_Figura6/fondo_RGB_falsocolor.tif',
    scale=20,
    region=region,
    crs='EPSG:4326'
)

print("✅ ¡Fondos descargados en 'Mapas_Figura6'!")
