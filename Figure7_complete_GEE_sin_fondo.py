import rasterio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# =====================================================================
# CONFIGURACIÓN
# =====================================================================
VARIABLES = {
    'LAI':    'Mapas_Fenologia_Descargados/PHENO_LSP_LAI_meta_2023.tif',
    'FVC':    'Mapas_Fenologia_Descargados/PHENO_LSP_FVC_meta_2023.tif',
    'laiCab': 'Mapas_Fenologia_Descargados/PHENO_LSP_laiCab_meta_2023.tif',
}

TITULOS = [
    'Start of Season (SOS)\nDay of Year',
    'End of Season (EOS)\nDay of Year',
    'Peak of Season (POS)\nDay of Year',
    'Length of Season (LOS)\nDays',
]

COLOR_VAR = {'LAI': '#2980b9', 'FVC': '#e67e22', 'laiCab': '#8e44ad'}

PADDING = 20  # píxeles de margen alrededor de los datos

# =====================================================================
# PASO 1 — Leer una banda LSP y enmascarar nodata
# =====================================================================
def leer_banda(ruta_tif, banda_idx):
    with rasterio.open(ruta_tif) as src:
        data = src.read(banda_idx).astype(float)
    data[data <= 0]   = np.nan
    data[data > 9000] = np.nan
    return data

# =====================================================================
# PASO 2 — Calcular bounding box automático sobre todos los datos
# =====================================================================
print("Calculando bounding box...")

filas_v, cols_v = [], []

for ruta_tif in VARIABLES.values():
    for i in range(4):
        banda = leer_banda(ruta_tif, i + 1)
        validos = ~np.isnan(banda)
        if validos.any():
            filas_v += [np.where(validos.any(axis=1))[0][[0, -1]]]
            cols_v  += [np.where(validos.any(axis=0))[0][[0, -1]]]

filas_v = np.concatenate(filas_v)
cols_v  = np.concatenate(cols_v)

# Referencia de forma usando el primer TIF
with rasterio.open(list(VARIABLES.values())[0]) as src:
    H, W = src.height, src.width

r_min = max(0, filas_v.min() - PADDING)
r_max = min(H, filas_v.max() + PADDING)
c_min = max(0, cols_v.min()  - PADDING)
c_max = min(W, cols_v.max()  + PADDING)

print(f"  Recorte: filas [{r_min}:{r_max}], cols [{c_min}:{c_max}]")

# =====================================================================
# PASO 3 — Leer banda ya recortada al bounding box
# =====================================================================
def leer_recortada(ruta_tif, banda_idx):
    banda = leer_banda(ruta_tif, banda_idx)
    return banda[r_min:r_max, c_min:c_max]

H_crop = r_max - r_min
W_crop = c_max - c_min

# =====================================================================
# PASO 4A — Figuras individuales 2×2 por variable
# =====================================================================
print("\nGenerando figuras individuales (2×2)...")

for var_name, ruta_tif in VARIABLES.items():
    print(f"  → {var_name}")
    fig, axes = plt.subplots(2, 2, figsize=(14, 12), facecolor='white')
    axes = axes.flatten()

    for i in range(4):
        banda = leer_recortada(ruta_tif, i + 1)
        ax    = axes[i]

        if i == 3:
            cmap, vmin, vmax, label = 'viridis', 40, 180, 'Duration (Days)'
        else:
            cmap, vmin, vmax, label = 'turbo', 1, 365, 'Day of Year (DOY)'

        cmap_obj = plt.get_cmap(cmap).copy()
        cmap_obj.set_bad(color='white')
        im = ax.imshow(np.ma.masked_invalid(banda),
                       cmap=cmap_obj, vmin=vmin, vmax=vmax,
                       interpolation='nearest')
        ax.set_title(TITULOS[i], fontsize=13, fontweight='bold', pad=10)
        ax.axis('off')
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label(label, rotation=270, labelpad=20, fontsize=12)

    plt.tight_layout()
    plt.suptitle(
        f'Figure 7: Land Surface Phenology Metrics ({var_name})\n'
        f'Maíz Industrial · Puerto Gaitán, Meta · Colombia 2023',
        fontsize=16, fontweight='bold', y=1.03,
    )
    nombre = f'Figura_7_LSP_{var_name}.png'
    plt.savefig(nombre, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"  ✅ Guardada: {nombre}")
    plt.show()
    plt.close()

# =====================================================================
# PASO 4B — Figura UNIFICADA sin espacios (3 filas × 4 columnas)
# =====================================================================
print("\nGenerando figura UNIFICADA sin fondo...")

aspect      = H_crop / W_crop
ANCHO_PANEL = 5.0
ALTO_PANEL  = ANCHO_PANEL * aspect
fig_ancho   = 4 * ANCHO_PANEL + 0.8
fig_alto    = 3 * ALTO_PANEL  + 1.4

fig_u = plt.figure(figsize=(fig_ancho, fig_alto), facecolor='white')
fig_u.suptitle(
    'Figure 7. Land Surface Phenology (LSP) Metrics\n'
    'Maíz Industrial · Puerto Gaitán, Meta · Colombia 2023',
    fontsize=14, fontweight='bold', y=1.01,
)
gs = gridspec.GridSpec(
    3, 4, figure=fig_u,
    wspace=0.03, hspace=0.06,
    left=0.06, right=0.98,
    top=0.93, bottom=0.09,
)

im_refs = [None, None, None, None]

for row, (var_name, ruta_tif) in enumerate(VARIABLES.items()):
    for col in range(4):
        banda = leer_recortada(ruta_tif, col + 1)

        if col == 3:
            cmap, vmin, vmax = 'viridis', 40, 180
        else:
            cmap, vmin, vmax = 'turbo', 1, 365

        ax = fig_u.add_subplot(gs[row, col])
        cmap_obj = plt.get_cmap(cmap).copy()
        cmap_obj.set_bad(color='white')
        im = ax.imshow(np.ma.masked_invalid(banda),
                       cmap=cmap_obj, vmin=vmin, vmax=vmax,
                       interpolation='nearest')
        ax.set_facecolor('white')
        ax.axis('off')

        if row == 0:
            ax.set_title(TITULOS[col], fontsize=10,
                         fontweight='bold', pad=6)
            im_refs[col] = im

    # Etiqueta lateral de variable
    fig_u.text(
        0.005, (2.5 - row) / 3,
        var_name,
        fontsize=12, fontweight='bold',
        color=COLOR_VAR[var_name],
        va='center', ha='left', rotation=90
    )

# Colorbars en la parte inferior
cbar_labels = ['DOY', 'DOY', 'DOY', 'Days']
for col in range(4):
    x0       = 0.06 + col * (0.92 / 4)
    ancho_cb = (0.92 / 4) - 0.012
    cbar_ax  = fig_u.add_axes([x0, 0.03, ancho_cb, 0.018])
    fig_u.colorbar(im_refs[col], cax=cbar_ax, orientation='horizontal')
    cbar_ax.set_xlabel(cbar_labels[col], fontsize=9)
    cbar_ax.tick_params(labelsize=8)

nombre_u = 'Figura_7_LSP_UNIFICADA.png'
plt.savefig(nombre_u, dpi=300, bbox_inches='tight', facecolor='white')
print(f"  ✅ Guardada: {nombre_u}")
plt.show()
plt.close()

print("\n" + "="*50)
print("🎉 PROCESO COMPLETADO")
print("="*50)
print("  Figura_7_LSP_LAI.png")
print("  Figura_7_LSP_FVC.png")
print("  Figura_7_LSP_laiCab.png")
print("  Figura_7_LSP_UNIFICADA.png")


# =====================================================================
# PASO 6B — Figura UNIFICADA SIN espacios (3 filas × 4 columnas)
# =====================================================================
print("\nGenerando figura UNIFICADA sin espacios...")

# Calcular aspect ratio real de los mapas recortados
aspect = H_crop / W_crop          # alto/ancho del mapa
ANCHO_PANEL = 5.0                  # ancho en pulgadas por panel
ALTO_PANEL  = ANCHO_PANEL * aspect # alto proporcional al mapa real

fig_ancho = 4 * ANCHO_PANEL + 0.6  # 4 columnas + margen lateral
fig_alto  = 3 * ALTO_PANEL  + 1.2  # 3 filas + espacio título + colorbars

fig_u = plt.figure(figsize=(fig_ancho, fig_alto), facecolor='white')
fig_u.suptitle(
    'Figure 7. Land Surface Phenology (LSP) Metrics\n'
    'maize and soybeans· Puerto Gaitán, Meta · Colombia 2023',
    fontsize=14, fontweight='bold', y=1.01,
)

gs = gridspec.GridSpec(
    3, 4, figure=fig_u,
    wspace=0.02,          # espacio mínimo horizontal
    hspace=0.06,          # espacio mínimo vertical
    left=0.06, right=0.98,
    top=0.93,
    bottom=0.08,
)

im_refs = [None, None, None, None]

for row, (var_name, ruta_tif) in enumerate(VARIABLES.items()):
    for col in range(4):
        banda = leer_banda_recortada(ruta_tif, col + 1)
        if col == 3:
            cmap, vmin, vmax = 'viridis', 40, 180
        else:
            cmap, vmin, vmax = 'turbo', 1, 365

        ax = fig_u.add_subplot(gs[row, col])

        ax.imshow(rgb)
        cmap_obj = plt.get_cmap(cmap).copy()
        cmap_obj.set_bad(alpha=0)
        overlay = np.ma.masked_invalid(banda)
        im = ax.imshow(overlay, cmap=cmap_obj, vmin=vmin, vmax=vmax,
                       alpha=0.82, interpolation='nearest')
        ax.axis('off')

        # Título solo en fila 0
        if row == 0:
            ax.set_title(TITULOS[col], fontsize=10,
                         fontweight='bold', pad=6)

        if row == 0:
            im_refs[col] = im

    # Etiqueta lateral de variable
    fig_u.text(
        0.005,
        (2.5 - row) / 3,
        var_name,
        fontsize=12, fontweight='bold',
        color=COLOR_VAR[var_name],
        va='center', ha='left', rotation=90
    )

# Colorbars pegadas a los paneles
cbar_labels = ['DOY', 'DOY', 'DOY', 'Days']
for col in range(4):
    # Posición automática basada en gridspec
    x0  = 0.06 + col * (0.92 / 4)
    ancho_cb = (0.92 / 4) - 0.01
    cbar_ax = fig_u.add_axes([x0, 0.03, ancho_cb, 0.018])
    fig_u.colorbar(im_refs[col], cax=cbar_ax, orientation='horizontal')
    cbar_ax.set_xlabel(cbar_labels[col], fontsize=9)
    cbar_ax.tick_params(labelsize=8)

nombre_u = 'Figura_7_LSP_UNIFICADA_2.png'
plt.savefig(nombre_u, dpi=300, bbox_inches='tight', facecolor='white')
print(f"  ✅ Guardada: {nombre_u}")
plt.show()
plt.close()