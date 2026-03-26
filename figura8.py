import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file
df_final = pd.read_csv('Series_Tiempo_Maiz_Meta_2023.csv')

# Ensure datetime format and sort by date
df_final['Fecha'] = pd.to_datetime(df_final['Fecha'])
df_final = df_final.sort_values('Fecha')

# Monthly ticks and labels in English
month_starts = pd.date_range('2023-01-01', '2023-12-01', freq='MS')
month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# Create figure with 3 panels
fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

variables = ['LAI', 'FVC', 'laiCab']
ylabels = ['LAI (m²/m²)', 'FVC (1)', 'laiCab (g/m²)']
colors = ['forestgreen', 'darkorange', 'royalblue']

for ax, var, ylabel, color in zip(axes, variables, ylabels, colors):
    ax.plot(
        df_final['Fecha'],
        df_final[f'{var}_Original'],
        marker='o',
        linestyle='--',
        color='gray',
        alpha=0.7,
        label=f'{var} Original'
    )

    ax.plot(
        df_final['Fecha'],
        df_final[f'{var}_Gapfilled'],
        linestyle='-',
        linewidth=2.2,
        color=color,
        label=f'{var} Gap-filled'
    )

    ax.set_ylabel(ylabel, fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(frameon=False, fontsize=10)

# ---- Agronomic windows based on sowing authorization and crop duration ----
sowing_windows = [
    {
        'start': pd.Timestamp('2023-04-20'),
        'end': pd.Timestamp('2023-04-30'),
        'label': 'ICA Authorized Sowing Window (P1)'
    },
    {
        'start': pd.Timestamp('2023-08-25'),
        'end': pd.Timestamp('2023-08-31'),
        'label': 'ICA Authorized Sowing Window (P2)'
    }
]

crop_cycles = [
    {
        'start': pd.Timestamp('2023-04-20'),
        'end': pd.Timestamp('2023-09-27'),
        'label': 'Expected crop cycle 1'
    },
    {
        'start': pd.Timestamp('2023-08-25'),
        'end': pd.Timestamp('2023-12-31'),
        'label': 'Expected crop cycle 2'
    }
]

for ax in axes:
    ymin, ymax = ax.get_ylim()
    yrange = ymax - ymin

    # Light broad shading for expected crop cycle
    for cycle in crop_cycles:
        ax.axvspan(
            cycle['start'],
            cycle['end'],
            color='lightsteelblue',
            alpha=0.18,
            zorder=0
        )

        xmid = cycle['start'] + (cycle['end'] - cycle['start']) / 2
        ax.text(
            xmid,
            ymax - 0.08 * yrange,
            cycle['label'],
            ha='center',
            va='top',
            fontsize=9,
            color='steelblue',
            fontweight='bold'
        )

    # Darker narrow shading for authorized sowing windows
    for sow in sowing_windows:
        ax.axvspan(
            sow['start'],
            sow['end'],
            color='navy',
            alpha=0.22,
            zorder=1
        )

        xmid = sow['start'] + (sow['end'] - sow['start']) / 2
        ax.text(
            xmid,
            ymax - 0.18 * yrange,
            sow['label'],
            ha='center',
            va='top',
            fontsize=8,
            color='navy',
            rotation=90
        )

# X-axis formatting
axes[-1].set_xticks(month_starts)
axes[-1].set_xticklabels(month_labels, fontsize=11)
axes[-1].set_xlim(pd.Timestamp('2023-01-01'), pd.Timestamp('2023-12-31'))
axes[-1].set_xlabel('Date', fontsize=12)

# Figure title
fig.suptitle(
    'Original and gap-filled time series of LAI, FVC, and laiCab\n'
    'for maize croplands in Meta, Colombia (2023)',
    fontsize=14,
    y=0.98
)

plt.tight_layout()
plt.subplots_adjust(top=0.92)
plt.savefig('Figure_8_gapfilled_time_series_with_seasons.png', dpi=300, bbox_inches='tight')
plt.show()
