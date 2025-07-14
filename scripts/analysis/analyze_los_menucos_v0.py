import pandas as pd
import numpy as np

# Read consolidated data
df = pd.read_csv('data/processed/consolidated_data.csv')

# Filter for Los Menucos
lm = df[df['station'] == 'Los Menucos'].copy()

# Análisis detallado de eventos con V=0
lm['timestamp'] = pd.to_datetime(lm['timestamp'])
lm = lm.sort_values('timestamp')

# Identificar eventos continuos de V=0
lm['v_zero'] = (lm['v_pu'] == 0).astype(int)
lm['event_id'] = (lm['v_zero'] != lm['v_zero'].shift()).cumsum()

# Solo eventos donde V=0
v_zero_events = lm[lm['v_zero'] == 1].groupby('event_id').agg({
    'timestamp': ['min', 'max', 'count'],
    'p_total': ['min', 'max', 'mean'],
    'v_pu': 'mean'
})

v_zero_events.columns = ['start', 'end', 'count', 'p_min', 'p_max', 'p_mean', 'v_mean']
v_zero_events['duration_hours'] = v_zero_events['count'] * 0.25

print('=== ANÁLISIS DETALLADO DE EVENTOS V=0 EN LOS MENUCOS ===')
print(f'Total de eventos separados con V=0: {len(v_zero_events)}')
print(f'\nEventos más largos (top 10):')
print('-' * 80)

for idx, event in v_zero_events.nlargest(10, 'duration_hours').iterrows():
    print(f'Evento {idx}:')
    print(f'  - Inicio: {event.start}')
    print(f'  - Fin: {event.end}')
    print(f'  - Duración: {event.duration_hours:.2f} horas')
    print(f'  - Potencia durante evento: min={event.p_min:.3f}, max={event.p_max:.3f}, prom={event.p_mean:.3f} MW')
    print()

# Análisis mensual
lm['year_month'] = lm['timestamp'].dt.to_period('M')
monthly_v_zero = lm[lm['v_pu'] == 0].groupby('year_month').size()

print('\n=== DISTRIBUCIÓN MENSUAL DE REGISTROS CON V=0 ===')
for month, count in monthly_v_zero.items():
    hours = count * 0.25
    print(f'{month}: {count} registros ({hours:.2f} horas)')

# Análisis de correlación V=0 con demanda
print('\n=== ANÁLISIS DE DEMANDA DURANTE EVENTOS V=0 ===')
normal_demand = lm[lm['v_pu'] > 0]['p_total'].mean()
v_zero_demand = lm[lm['v_pu'] == 0]['p_total'].mean()
print(f'Demanda promedio normal (V>0): {normal_demand:.3f} MW')
print(f'Demanda promedio durante V=0: {v_zero_demand:.3f} MW')
print(f'Pérdida de carga durante V=0: {(1 - v_zero_demand/normal_demand)*100:.1f}%')

# Análisis de interrupciones
print('\n=== RESUMEN DE INTERRUPCIONES ===')
print(f'Total horas con V=0: {len(lm[lm["v_pu"] == 0]) * 0.25:.2f} horas')
print(f'Total horas con P=0: {len(lm[lm["p_total"] == 0]) * 0.25:.2f} horas')
print(f'Porcentaje del tiempo con interrupciones: {len(lm[lm["v_pu"] == 0]) / len(lm) * 100:.2f}%')

# ENS más precisa
demand_when_available = lm[lm['p_total'] > 0]['p_total'].mean()
ens_total = len(lm[lm['p_total'] == 0]) * 0.25 * demand_when_available
days_total = len(lm) * 0.25 / 24
ens_annual = ens_total * 365 / days_total

print(f'\n=== ENERGÍA NO SUMINISTRADA (ENS) ===')
print(f'ENS total período: {ens_total:.2f} MWh')
print(f'ENS anualizada: {ens_annual:.2f} MWh/año')
print(f'Costo ENS @ $200 USD/MWh: ${ens_annual * 200:,.0f} USD/año')