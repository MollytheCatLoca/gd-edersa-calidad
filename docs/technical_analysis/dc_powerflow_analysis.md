# Análisis de Flujo de Potencia DC - Sistema Línea Sur

## Resumen del Sistema

- **Carga Total**: 13.5 MW
- **Generación GD**: 1.8 MW
- **Importación desde Red**: 11.7 MW
- **Pérdidas Totales**: 14.514 MW (107.5%)
- **Rango de Voltaje**: 0.800 - 0.950 pu
- **Costo Anual Pérdidas**: $2,383,913 USD

## Estado de Nodos

| Nodo        |   Distancia (km) |   Carga (MW) |   Generación (MW) |   Inyección Neta (MW) |   Ángulo (°) |   Voltaje (pu) |   Voltaje (kV) |
|:------------|-----------------:|-------------:|------------------:|----------------------:|-------------:|---------------:|---------------:|
| PILCANIYEU  |                0 |          3.5 |               0   |                  -3.5 |         0    |          0.95  |          31.35 |
| COMALLO     |                0 |          0   |               0   |                   0   |        19.2  |          0.827 |          27.29 |
| JACOBACCI   |              150 |          2.5 |               0   |                  -2.5 |        36.93 |          0.8   |          26.4  |
| MAQUINCHAO  |              210 |          4.5 |               0   |                  -4.5 |        47.07 |          0.8   |          26.4  |
| LOS_MENUCOS |              270 |          3   |               1.8 |                  -1.2 |        48.73 |          0.8   |          26.4  |

## Flujos y Pérdidas por Línea

| Línea                  |   Longitud (km) | Conductor   |   R (pu) |   Flujo (MW) |   Pérdidas (MW) |   Pérdidas (%) |   Energía Anual (MWh) |   Pérdidas Anuales (MWh) | Costo Pérdidas (USD/año)   |
|:-----------------------|----------------:|:------------|---------:|-------------:|----------------:|---------------:|----------------------:|-------------------------:|:---------------------------|
| PILCANIYEU → COMALLO   |              70 | N/A         |     0.05 |         -8.2 |          4.3378 |          52.9  |                 21550 |                    11400 | $712,489                   |
| COMALLO → JACOBACCI    |               0 | N/A         |     0.05 |         -8.2 |          5.6978 |          69.49 |                 21550 |                    14974 | $935,870                   |
| JACOBACCI → MAQUINCHAO |              60 | N/A         |     0.05 |         -5.7 |          4.3299 |          75.96 |                 14980 |                    11379 | $711,178                   |
| MAQUINCHAO → MENUCOS   |               0 | N/A         |     0.05 |         -1.2 |          0.1484 |          12.37 |                  3154 |                      390 | $24,376                    |

## Análisis de Costos

### Costos Operativos Actuales
- **Energía de Red**: $62.50/MWh
- **GD Los Menucos**: $122.70/MWh
- **Costo Pérdidas Anuales**: $2,383,913

### Costo Total Anual de Energía
- **Energía desde Red**: 30,748 MWh × $62.50 = $1,921,725
- **Energía desde GD**: 2,365 MWh × $122.70 = $290,210
- **Total**: $2,211,935

## Observaciones Clave

1. **Voltajes Críticos**: Todos los nodos operan por debajo de 0.95 pu
2. **Pérdidas Elevadas**: Las pérdidas aumentan significativamente en los tramos finales
3. **GD Insuficiente**: La GD actual (1.8 MW) no es suficiente para mejorar significativamente los voltajes
4. **Costo GD**: El alto costo de la GD térmica ($122.7/MWh) limita su operación