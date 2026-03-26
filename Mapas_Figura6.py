import rasterio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors

fechas = ['2023-01-15', '2023-05-25', '2023-07-09', '2023-10-17']
etiquetas_fechas = ['Jan 15\n(Sowing)', 'May 25\n(Vegetative)',
                    'Jul 09\n(Peak)', 'Oct 17\n(Senescence)']
variables = ['LAI', 'FVC', 'laiCab']
etiquetas_vars = ['LAI [m²/m²]', 'FVC [0-1]', 'laiCab [g/m²]']

# FIX 3: laiCab cambia a 'hot_r' (negro→rojo→naranja→amarillo)
# Empieza en negro (no blanco) así los valores bajos se distinguen del fondo
colores_mapas  = ['plasma', 'Blues', 'hot_r']
vmax_list      = [6.0,       1.0,     4.0   ]

# FIX 3 extra: vmin dinámico para laiCab basado en el percentil 5 real
# (Calculado abajo antes de graficar)

# ── CARGAR FONDO RGB ──────────────────────────────────────────────
def leer_rgb_natural(archivo):
    with rasterio.open(archivo) as src:
        r, g, b = [src.read(i+1).astype(float) for i in range(3)]
        bounds  = src.bounds
    def norm(arr):
        arr = np.where(arr <= 0, np.nan, arr)
        p1, p99 = np.nanpercentile(arr[~np.isnan(arr)], [1, 99])
        return np.clip((arr - p1) / (p99 - p1), 0, 1)
    rgb = np.dstack([norm(r), norm(g), norm(b)])
    return np.nan_to_num(rgb, nan=0.25), bounds

try:
    fondo_rgb, fondo_bounds = leer_rgb_natural('Mapas_Figura6/fondo_RGB_sinNubes.tif')
    tiene_fondo = True
except Exception as e:
    print(f"⚠️ Fondo no disponible: {e}")
    tiene_fondo = False

# ── CALCULAR ZOOM ÚNICO DESDE LAI ─────────────────────────────────
zoom_bounds = None
for fecha in fechas:
    try:
        with rasterio.open(f'Mapas_Figura6/LAI_gf_{fecha}.tif') as s:
            banda = s.read(1)
            m = banda > 0
            if not m.any(): continue
            rmin, rmax = np.where(np.any(m, axis=1))[0][[0, -1]]
            cmin, cmax = np.where(np.any(m, axis=0))[0][[0, -1]]
            T, buf = s.transform, 0.04
            zoom_bounds = (T.c + cmin*T.a - buf, T.c + cmax*T.a + buf,
                           T.f + rmax*T.e - buf, T.f + rmin*T.e + buf)
            break
    except: continue

# FIX 3: Calcular vmin real del laiCab (percentil 5 de todos los píxeles)
vals_laicab = []
for fecha in fechas:
    try:
        with rasterio.open(f'Mapas_Figura6/laiCab_gf_{fecha}.tif') as s:
            b = s.read(1).astype(float)
            vals_laicab.extend(b[b > 0].flatten().tolist())
    except: pass

vmin_laicab = float(np.percentile(vals_laicab, 5)) if vals_laicab else 0.0
vmax_laicab = float(np.percentile(vals_laicab, 98)) if vals_laicab else 4.0
print(f"laiCab → vmin={vmin_laicab:.2f}  vmax={vmax_laicab:.2f}")

# Sobreescribir el vmax para laiCab con el real
vmax_list[2] = vmax_laicab

# ── FIGURA ────────────────────────────────────────────────────────
fig = plt.figure(figsize=(26, 14), dpi=150, facecolor='white')

# GridSpec: 3 filas × 4 columnas de mapas + 1 columna de barras
# FIX 2: columna dedicada a las barras → sin solapamiento
gs = gridspec.GridSpec(
    3, 5,
    figure       = fig,
    width_ratios = [1, 1, 1, 1, 0.04],
    wspace       = 0.02,
    hspace       = 0.03,
    left=0.06, right=0.95, top=0.91, bottom=0.05
)

im_por_fila = {}   # Guardamos el imshow de cada fila para la barra

for fila, var in enumerate(variables):
    for col, fecha in enumerate(fechas):
        ax = fig.add_subplot(gs[fila, col])
        ax.set_aspect('auto')

        archivo = f'Mapas_Figura6/{var}_gf_{fecha}.tif'
        try:
            with rasterio.open(archivo) as src:
                banda = src.read(1).astype(float)
                banda = np.where(banda <= 0, np.nan, banda)
                bounds = src.bounds
                ext_v = [bounds.left, bounds.right, bounds.bottom, bounds.top]
                ext_f = [fondo_bounds.left, fondo_bounds.right,
                         fondo_bounds.bottom, fondo_bounds.top]

                if tiene_fondo:
                    ax.imshow(fondo_rgb, extent=ext_f, zorder=1, aspect='auto')

                # vmin dinámico para laiCab
                vmin_uso = vmin_laicab if var == 'laiCab' else 0.0
                vmax_uso = vmax_list[fila]

                im = ax.imshow(banda,
                               cmap      = colores_mapas[fila],
                               vmin      = vmin_uso,
                               vmax      = vmax_uso,
                               extent    = ext_v,
                               zorder    = 2,
                               interpolation = 'nearest',
                               alpha     = 0.78)
                im_por_fila[fila] = im

                if zoom_bounds:
                    ax.set_xlim(zoom_bounds[0], zoom_bounds[1])
                    ax.set_ylim(zoom_bounds[2], zoom_bounds[3])

        except:
            ax.text(0.5, 0.5, 'TIF\nMissing', ha='center', va='center',
                    color='red', transform=ax.transAxes, fontsize=10)
            ax.set_facecolor('#cccccc')

        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_edgecolor('white'); sp.set_linewidth(1.0)

        # FIX 1: Fuente pequeña para títulos y etiquetas
        if fila == 0:
            ax.set_title(etiquetas_fechas[col], fontsize=10,
                         fontweight='bold', pad=6)
        if col == 0:
            ax.set_ylabel(etiquetas_vars[fila], fontsize=10,
                          fontweight='bold', labelpad=6)

# Renderizar primero para obtener posiciones reales de los ejes
fig.canvas.draw()

# Crear barras de color alineadas exactamente con la altura real de cada fila
for fila in range(3):
    if fila not in im_por_fila:
        continue

    # Recoger las posiciones de los 4 mapas de esta fila
    posiciones_fila = []
    for col in range(4):
        idx = fila * 4 + col + 1  # índice del subplot (empieza en 1)
        ax_mapa = fig.axes[idx - 1]  # fig.axes es 0-indexed
        posiciones_fila.append(ax_mapa.get_position())

    # Calcular los límites reales de la fila
    y0_real  = min(p.y0  for p in posiciones_fila)  # borde inferior
    y1_real  = max(p.y1  for p in posiciones_fila)  # borde superior
    altura   = y1_real - y0_real

    # Posición X de la columna de barras (justo a la derecha del último mapa)
    x_barra  = posiciones_fila[-1].x1 + 0.008
    ancho    = 0.012

    # Crear el eje de la barra en esa posición exacta
    cax = fig.add_axes([x_barra, y0_real, ancho, altura])
    cbar = fig.colorbar(im_por_fila[fila], cax=cax)
    cbar.ax.tick_params(labelsize=8)

# Crédito al pie
fig.text(0.5, 0.01,
         'Background: Sentinel-2 SR Median Composite 2023 (CLOUDY_PIXEL ≤10%) | © ESA Copernicus',
         ha='center', fontsize=7, color='gray', style='italic')

plt.savefig('Figura_6_FINAL_V4.png', dpi=300, bbox_inches='tight', facecolor='white')
print("✅  Figura_6_FINAL_V4.png guardada.")
plt.show()
