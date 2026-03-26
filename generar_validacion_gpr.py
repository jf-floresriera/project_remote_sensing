import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

archivo_csv = 'Series_Tiempo_Maiz_Meta_2023.csv'

try:
    df = pd.read_csv(archivo_csv)
    
    variables = ['LAI', 'FVC', 'laiCab']
    titulos = ['Leaf Area Index (LAI)', 'Fractional Veg. Cover (FVC)', 'Canopy Chlorophyll (laiCab)']
    colores = ['forestgreen', 'darkorange', 'teal']
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for i, var in enumerate(variables):
        col_orig = f'{var}_Original'
        col_gf = f'{var}_Gapfilled'
        
        # Filtrar valores NaN (Huecos de nubes originales) para que el cálculo matemático funcione
        df_clean = df.dropna(subset=[col_orig, col_gf])
        x = df_clean[col_orig].values
        y = df_clean[col_gf].values
        
        # Calcular RMSE manualmente
        mse = np.mean((x - y) ** 2)
        rmse = np.sqrt(mse)
        
        # Calcular R2 manualmente
        ss_res = np.sum((x - y) ** 2)
        ss_tot = np.sum((x - np.mean(x)) ** 2)
        r2 = 1 - (ss_res / ss_tot)
        
        ax = axes[i]
        
        ax.scatter(x, y, color=colores[i], alpha=0.6, edgecolors='k', s=50)
        
        lim_min = min(x.min(), y.min()) * 0.9
        lim_max = max(x.max(), y.max()) * 1.1
        ax.plot([lim_min, lim_max], [lim_min, lim_max], 'k--', alpha=0.7, label='1:1 Line')
        
        m, b = np.polyfit(x, y, 1)
        ax.plot(x, m*x + b, color='red', linewidth=2, label='Regression Line')
        
        ax.set_title(titulos[i], fontsize=15, fontweight='bold', pad=15)
        ax.set_xlabel(f'Original S2 {var}', fontsize=13)
        if i == 0: 
            ax.set_ylabel(f'GPR Gap-filled {var}', fontsize=13)
            
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(loc='lower right', fontsize=11)
        
        texto_metricas = f'$R^2$ = {r2:.3f}\nRMSE = {rmse:.3f}'
        ax.text(0.05, 0.85, texto_metricas, transform=ax.transAxes, fontsize=12,
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray', boxstyle='round,pad=0.5'))
                
        ax.set_aspect('equal', 'box')
        ax.set_xlim(lim_min, lim_max)
        ax.set_ylim(lim_min, lim_max)

    plt.tight_layout()
    plt.suptitle('Validation of GPR Gap-filling Performance against S2 Raw Data', 
                 fontsize=18, fontweight='bold', y=1.05)
                 
    plt.savefig('Figura_9_Validacion_GPR.png', dpi=300, bbox_inches='tight')
    print("✅ ¡Gráfica de validación guardada exitosamente!")
    plt.show()
    
except Exception as e:
    print(f"❌ Error al generar la gráfica: {e}")
