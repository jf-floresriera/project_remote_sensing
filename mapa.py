import ee
import geemap
from geemap import cartoee
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# 1. Inicializar Earth Engine
try:
    ee.Initialize(project='wide-origin-466923-d8')
except Exception as e:
    ee.Authenticate()
    ee.Initialize(project='wide-origin-466923-d8')

print("Buscando polígonos y datos de la región...")

# 2. Definir el Área de Interés y los polígonos
region_coords = [-72.05, 4.1, -71.4, 4.5]
region = ee.Geometry.Rectangle(region_coords)

maiz_upra = ee.FeatureCollection('projects/wide-origin-466923-d8/assets/maiz_industrial_meta_2023').filterBounds(region)

# 3. Obtener la imagen RGB de fondo (Sentinel-2)
RGB = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
       .filterBounds(region)
       .filterDate('2023-01-01', '2023-06-30')  
       .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) 
       .median()
       .select(['B4', 'B3', 'B2'])
       .divide(10000))

# Convertir los polígonos a una imagen amarilla
parcelas_img = ee.Image.constant(1).clip(maiz_upra.geometry()).mask(ee.Image.constant(1).clip(maiz_upra.geometry()))

# Combinar RGB y parcelas 
vis_params = {'min': 0.0, 'max': 0.3, 'bands': ['B4', 'B3', 'B2']}
mapa_base = RGB.visualize(**vis_params)
mapa_base_con_parcelas = mapa_base.blend(parcelas_img.visualize(palette=['yellow']))

# ==========================================
# CONFIGURACIÓN DEL MAPA CON MATPLOTLIB / CARTOEE
# ==========================================

print("Generando el mapa principal de GEE...")
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

# Agregar capa de GEE a cartoee
cartoee.add_layer(ax, mapa_base_con_parcelas, region=region_coords, zoom=11)

# Estilos y grilla
cartoee.add_gridlines(ax, interval=[0.1, 0.1], linestyle=":")
ax.set_title("Área de Estudio: Cultivos de Maíz, Meta (Colombia) \n(UPRA 2023, Tile 118NZK)", fontsize=16, weight='bold', pad=20)
ax.coastlines(resolution='10m')

# Escala y norte (se mueven un poco para dar espacio)
cartoee.add_scale_bar_lite(ax, length=10, xy=(0.80, 0.05), fontsize=12, color='white')
cartoee.add_north_arrow(ax, xy=(0.05, 0.90))

# ==========================================
# LEYENDA PERSONALIZADA
# ==========================================
# Creamos un pequeño parche amarillo para la leyenda
yellow_patch = mpatches.Patch(color='yellow', label='Parcelas de Maíz')

# Texto de la leyenda
leyenda_texto = "Parcelas estudiadas: 408\nÁrea total: 25,114.53 ha"

# Agregamos la leyenda a la esquina inferior izquierda
legend = ax.legend(handles=[yellow_patch], loc='lower left', 
                   title=leyenda_texto, 
                   title_fontsize=11, 
                   fontsize=12, 
                   frameon=True, 
                   facecolor='white', 
                   framealpha=0.9,
                   edgecolor='black')
# Alinear el título de la leyenda a la izquierda
legend.get_title().set_multialignment('left')

# ==========================================
# MAPA INSET (COLOMBIA) EN LA DERECHA
# ==========================================
print("Generando mapa de ubicación (Colombia)...")

# Colocado en la esquina inferior derecha
axins = inset_axes(ax, width="25%", height="35%", loc='lower right', 
                   axes_class=cartopy.mpl.geoaxes.GeoAxes, 
                   axes_kwargs=dict(map_projection=ccrs.PlateCarree()))

axins.set_extent([-80, -66, -5, 13])
axins.add_feature(cfeature.LAND, facecolor='lightgray')
axins.add_feature(cfeature.OCEAN, facecolor='lightblue')
axins.add_feature(cfeature.BORDERS, linestyle=':')
axins.add_feature(cfeature.COASTLINE)

# Cuadro rojo indicando el Meta
x = [region_coords[0], region_coords[2], region_coords[2], region_coords[0], region_coords[0]]
y = [region_coords[1], region_coords[1], region_coords[3], region_coords[3], region_coords[1]]
axins.plot(x, y, color='red', linewidth=2, transform=ccrs.PlateCarree())

# Texto "Ubicación en Colombia" dentro del Inset
axins.set_title("Ubicación en Colombia", fontsize=10, weight='bold')

# ==========================================
# GUARDAR
# ==========================================
output_file = "Area_Estudio_PuertoGaitan.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"✅ ¡Mapa generado con éxito y guardado como {output_file}!")

plt.show()
