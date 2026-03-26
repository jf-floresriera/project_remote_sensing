import rasterio
import numpy as np
import matplotlib.pyplot as plt

# Archivo que acabas de descargar
archivo_tif = 'Mapas_Fenologia_Descargados/PHENO_LSP_LAI_meta_2023.tif'

# Configurar la figura: 2 filas, 2 columnas
fig, axes = plt.subplots(2, 2, figsize=(14, 12))
axes = axes.flatten()

# Títulos de cada sub-mapa
titulos = [
    'Start of Season (SOS)\nDay of Year', 
    'End of Season (EOS)\nDay of Year', 
    'Peak of Season (POS)\nDay of Year', 
    'Length of Season (LOS)\nDays'
]

# Abrir el mapa TIF
with rasterio.open(archivo_tif) as src:
    for i in range(4):
        # Leer la banda correspondiente (1: sos, 2: eos, 3: pos, 4: los)
        banda = src.read(i + 1)
        
        # Ocultar los píxeles que valen 0 (fondo sin datos)
        banda = np.where(banda == 0, np.nan, banda)
        
        ax = axes[i]
        
        # Lógica de colores (LOS usa escala de días de duración, las demás usan Días del Año)
        if i == 3: # Length of Season (LOS)
            vmin, vmax = 60, 180 # Rango de días que suele durar el maíz
            cmap = 'viridis'
            label_barra = 'Duration (Days)'
        else: # SOS, EOS, POS
            vmin, vmax = 1, 365 # Todo un año
            cmap = 'turbo' # Escala de arcoíris clásica para fenología
            label_barra = 'Day of Year (DOY)'
            
        # Dibujar el mapa
        im = ax.imshow(banda, cmap=cmap, vmin=vmin, vmax=vmax)
        
        ax.set_title(titulos[i], fontsize=14, fontweight='bold', pad=15)
        ax.axis('off') # Quitar ejes de coordenadas
        
        # Añadir barra de colores
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label(label_barra, rotation=270, labelpad=20, fontsize=12)

# Ajustes finales y guardar imagen
plt.tight_layout()
plt.suptitle('Figure 7: Land Surface Phenology Metrics (LAI) - Maize, Puerto Gaitán', 
             fontsize=18, y=1.05, fontweight='bold')

nombre_salida = 'Figura_7_LSP_LAI.png'
plt.savefig(nombre_salida, dpi=300, bbox_inches='tight')
print(f"✅ ¡Proceso terminado! Se ha guardado la imagen: {nombre_salida}")

# Mostrarla en pantalla
plt.show()
