import pandas as pd
import matplotlib.pyplot as plt

archivo_csv = 'Series_Tiempo_Maiz_Meta_2023.csv'

try:
    df = pd.read_csv(archivo_csv)
    
    # Crear figura con 3 paneles (uno para LAI, otro FVC, otro laiCab)
    fig, axes = plt.subplots(3, 1, figsize=(12, 14), sharex=True)
    
    variables = ['LAI', 'FVC', 'laiCab']
    nombres_eje = ['LAI (m²/m²)', 'FVC (0-1)', 'Canopy Chlorophyll (laiCab)']
    colores = ['forestgreen', 'darkorange', 'teal']
    
    for i, var in enumerate(variables):
        ax = axes[i]
        
        # Graficar puntos crudos
        ax.scatter(df['DOY'], df[f'{var}_Original'], color='gray', alpha=0.6, 
                   label='Sentinel-2 Original', zorder=2)
                   
        # Graficar línea suavizada GPR
        ax.plot(df['DOY'], df[f'{var}_Gapfilled'], color=colores[i], linewidth=3, 
                label='GPR Gap-Filled', zorder=3)
        
        # --- AÑADIR CONTEXTO AGRONÓMICO DE LA ALTILLANURA ---
        # Semestre A: Aprox Abril a Agosto
        ax.axvspan(105, 227, color='green', alpha=0.1, label='Semestre A (Apr-Aug)' if i==0 else "")
        # Semestre B: Aprox Septiembre a Diciembre
        ax.axvspan(244, 365, color='blue', alpha=0.1, label='Semestre B (Sep-Dec)' if i==0 else "")
        
        ax.set_ylabel(nombres_eje[i], fontsize=13, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Ajustar límite Y para que no se vea cortado
        y_max = df[f'{var}_Gapfilled'].max() * 1.2
        if pd.notna(y_max):
            ax.set_ylim(0, y_max)
        
        if i == 0:
            # Poner la leyenda arriba, fuera de la gráfica para no tapar los datos
            ax.legend(fontsize=11, loc='upper center', bbox_to_anchor=(0.5, 1.25), ncol=4)

    # Configuración del eje X compartido
    axes[-1].set_xlabel('Day of Year (DOY)', fontsize=14, fontweight='bold')
    axes[-1].set_xlim(1, 365)
    
    plt.suptitle('Figure 8: Maize Phenological Profile vs Agronomic Cycles (Meta, Colombia)', 
                 fontsize=18, y=0.96, fontweight='bold')
    
    plt.savefig('Figura_8_Completa_Agronomica.png', dpi=300, bbox_inches='tight')
    print("✅ ¡Gráfica agronómica guardada como 'Figura_8_Completa_Agronomica.png'!")
    plt.show()
    
except Exception as e:
    print(f"❌ Error: {e}")
