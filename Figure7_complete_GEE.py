import rasterio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.ndimage import zoom

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

# =====================================================================
# PASO 1 — Leer y normalizar el fondo RGB
# =====================================================================
print("Leyendo fondo RGB...")
with rasterio.open(FONDO_RGB) as src:
    r = src.read(1).astype(float)
    g = src.read(2).astype(float)
    b = src.read(3).astype(float)

def norm_banda(banda):
    banda = banda.copy()
    mascara = banda > 0
    if mascara.sum() == 0:
        return np.zeros_like(banda)
    p2  = np.percentile(banda[mascara], 2)
    p98 = np.percentile(banda[mascara], 98)
    banda = np.clip(banda, p2, p98)
    return (banda - p2) / (p98 - p2 + 1e-9)

rgb_full = np.dstack([norm_banda(r), norm_banda(g), norm_banda(b)])
rgb_full = np.clip(rgb_full, 0, 1)
H_rgb, W_rgb = rgb_full.shape[:2]
print(f"  RGB completo: {W_rgb} x {H_rgb} px")

# =====================================================================
# PASO 2 — Leer banda LSP y ajustar al tamaño del RGB
# =====================================================================
def leer_banda_lsp(ruta_tif, banda_idx):
    with rasterio.open(ruta_tif) as src:
        data = src.read(banda_idx).astype(float)
    data[data <= 0]   = np.nan
    data[data > 9000] = np.nan
    factor_h = H_rgb / data.shape[0]
    factor_w = W_rgb / data.shape[1]
    mascara_nan = np.isnan(data)
    data_filled = np.where(mascara_nan, 0.0, data)
    data_zoom   = zoom(data_filled, (factor_h, factor_w), order=1)
    mask_zoom   = zoom(mascara_nan.astype(float), (factor_h, factor_w), order=0) > 0.5
    data_zoom[mask_zoom] = np.nan
    return data_zoom

# =====================================================================
# PASO 3 — CALCULAR BOUNDING BOX AUTOMÁTICO de los datos válidos
# =====================================================================
print("Calculando bounding box de los datos...")

filas_validas = []
cols_validas  = []

for ruta_tif in VARIABLES.values():
    for i in range(4):
        banda = leer_banda_lsp(ruta_tif, i + 1)
        validos = ~np.isnan(banda)
        if validos.any():
            rows = np.where(validos.any(axis=1))[0]
            cols = np.where(validos.any(axis=0))[0]
            filas_validas.extend([rows[0], rows[-1]])
            cols_validas.extend([cols[0], cols[-1]])

PADDING = 30  # píxeles de margen alrededor de los datos
r_min = max(0,     min(filas_validas) - PADDING)
r_max = min(H_rgb, max(filas_validas) + PADDING)
c_min = max(0,     min(cols_validas)  - PADDING)
c_max = min(W_rgb, max(cols_validas)  + PADDING)

print(f"  Recorte: filas [{r_min}:{r_max}], cols [{c_min}:{c_max}]")

# Recortar el fondo RGB al bounding box
rgb = rgb_full[r_min:r_max, c_min:c_max]
H_crop, W_crop = rgb.shape[:2]
print(f"  RGB recortado: {W_crop} x {H_crop} px")

# =====================================================================
# PASO 4 — Leer y recortar bandas al mismo bounding box
# =====================================================================
def leer_banda_recortada(ruta_tif, banda_idx):
    banda = leer_banda_lsp(ruta_tif, banda_idx)
    return banda[r_min:r_max, c_min:c_max]

# =====================================================================
# PASO 5 — Función para dibujar panel (RGB + overlay)
# =====================================================================
def dibujar_panel(ax, rgb, banda, cmap, vmin, vmax, titulo, alpha=0.82):
    ax.imshow(rgb)
    cmap_obj = plt.get_cmap(cmap).copy()
    cmap_obj.set_bad(alpha=0)
    overlay = np.ma.masked_invalid(banda)
    im = ax.imshow(overlay, cmap=cmap_obj, vmin=vmin, vmax=vmax,
                   alpha=alpha, interpolation='nearest')
    ax.set_title(titulo, fontsize=13, fontweight='bold', pad=10)
    ax.axis('off')
    return im

# =====================================================================
# PASO 6A — Figura 2×2 por variable
# =====================================================================
print("\nGenerando figuras individuales (2×2)...")

for var_name, ruta_tif in VARIABLES.items():
    print(f"  → {var_name}")
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.flatten()

    for i in range(4):
        banda = leer_banda_recortada(ruta_tif, i + 1)
        if i == 3:
            cmap, vmin, vmax, label = 'viridis', 40, 180, 'Duration (Days)'
        else:
            cmap, vmin, vmax, label = 'turbo', 1, 365, 'Day of Year (DOY)'

        im = dibujar_panel(axes[i], rgb, banda, cmap, vmin, vmax, TITULOS[i])
        cbar = fig.colorbar(im, ax=axes[i], fraction=0.046, pad=0.04)
        cbar.set_label(label, rotation=270, labelpad=20, fontsize=12)

    plt.tight_layout()
    plt.suptitle(
        f'Figure 7: Land Surface Phenology Metrics ({var_name})\n'
        f'Maíz Industrial · Puerto Gaitán, Meta · Colombia 2023',
        fontsize=16, fontweight='bold', y=1.03,
    )
    nombre = f'Figura_7_LSP_{var_name}.png'
    plt.savefig(nombre, dpi=300, bbox_inches='tight')
    print(f"  ✅ Guardada: {nombre}")
    plt.show()
    plt.close()

# =====================================================================
# PASO 6B — Figura UNIFICADA (3 filas × 4 columnas)
# =====================================================================
print("\nGenerando figura UNIFICADA...")

fig_u = plt.figure(figsize=(22, 16), facecolor='white')
fig_u.suptitle(
    'Figure 7. Land Surface Phenology (LSP) Metrics\n'
    'Maíz Industrial · Puerto Gaitán, Meta · Colombia 2023',
    fontsize=16, fontweight='bold', y=1.01,
)
gs = gridspec.GridSpec(3, 4, figure=fig_u,
                       wspace=0.04, hspace=0.08,
                       left=0.07, right=0.97,
                       top=0.93, bottom=0.06)

im_refs = [None, None, None, None]

for row, (var_name, ruta_tif) in enumerate(VARIABLES.items()):
    for col in range(4):
        banda = leer_banda_recortada(ruta_tif, col + 1)
        if col == 3:
            cmap, vmin, vmax = 'viridis', 40, 180
        else:
            cmap, vmin, vmax = 'turbo', 1, 365

        ax = fig_u.add_subplot(gs[row, col])
        im = dibujar_panel(ax, rgb, banda, cmap, vmin, vmax,
                           titulo=TITULOS[col] if row == 0 else '')
        if row == 0:
            im_refs[col] = im

    fig_u.text(0.01, 0.88 - row * 0.30, var_name,
               fontsize=13, fontweight='bold',
               color=COLOR_VAR[var_name],
               va='center', ha='left', rotation=90)

# Colorbars en la parte inferior
cbar_labels = ['DOY', 'DOY', 'DOY', 'Days']
for col in range(4):
    cbar_ax = fig_u.add_axes([0.08 + col * 0.228, 0.01, 0.19, 0.012])
    fig_u.colorbar(im_refs[col], cax=cbar_ax, orientation='horizontal')
    cbar_ax.set_xlabel(cbar_labels[col], fontsize=9)

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
    'Maíz Industrial · Puerto Gaitán, Meta · Colombia 2023',
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

nombre_u = 'Figura_7_LSP_UNIFICADA.png'
plt.savefig(nombre_u, dpi=300, bbox_inches='tight', facecolor='white')
print(f"  ✅ Guardada: {nombre_u}")
plt.show()
plt.close()
