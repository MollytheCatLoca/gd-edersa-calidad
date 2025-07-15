# GUÍA DE IMPLEMENTACIÓN - METODOLOGÍA CLAUDE

## 🚀 Inicio Rápido

Esta guía te ayudará a implementar la metodología CLAUDE en tu proyecto de análisis de sistemas eléctricos paso a paso.

---

## 📋 Checklist Pre-Proyecto

Antes de comenzar, asegúrate de tener:

- [ ] **Datos del sistema**: Diagrama unifilar, parámetros de red
- [ ] **Datos históricos**: Mínimo 6 meses, idealmente 12+
- [ ] **Resolución temporal**: 15 minutos o mejor
- [ ] **Variables mínimas**: Voltaje, Potencia activa/reactiva
- [ ] **Python 3.10+** instalado
- [ ] **Git** para control de versiones

---

## 🏗️ Paso 1: Configuración Inicial

### 1.1 Crear Estructura del Proyecto

```bash
# Crear directorio del proyecto
mkdir mi_proyecto_gd
cd mi_proyecto_gd

# Inicializar git
git init

# Crear estructura de carpetas
mkdir -p src/{topology,solar,bess,analysis}
mkdir -p dashboard/pages
mkdir -p data/{raw,processed,solar}
mkdir -p docs/{technical_analysis,economic_analysis}
mkdir -p scripts/{analysis,validation}
mkdir -p tests/unit
```

### 1.2 Configurar Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias base
pip install pandas numpy scipy matplotlib plotly dash
pip install pytest black flake8 jupyter
```

### 1.3 Crear Archivos Base

```python
# src/constants.py
"""Constantes específicas del proyecto"""
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Parámetros del Sistema
SYSTEM_NAME = "Mi Sistema"
NOMINAL_VOLTAGE_KV = 33.0  # Ajustar según tu sistema
BASE_MVA = 100

# Límites operativos
VOLTAGE_LIMITS = {"min": 0.95, "max": 1.05}  # p.u.
FREQUENCY_LIMITS = {"min": 49.8, "max": 50.2}  # Hz

# Configuración temporal
DATA_FREQUENCY = "15min"
ANALYSIS_PERIOD = {"start": "2024-01-01", "end": "2024-12-31"}
```

---

## 📊 Paso 2: Implementación por Fases

### Fase 1: Comprensión del Sistema

**Objetivo**: Documentar y entender el problema

```python
# scripts/analysis/system_overview.py
"""Script para generar resumen del sistema"""

import pandas as pd
import json
from pathlib import Path

def analyze_system_overview():
    """Genera documento de comprensión del sistema"""
    
    system_info = {
        "metadata": {
            "name": SYSTEM_NAME,
            "voltage_level": f"{NOMINAL_VOLTAGE_KV} kV",
            "analysis_date": pd.Timestamp.now().isoformat()
        },
        "network": {
            "topology": "radial",  # o "mesh", "ring"
            "total_length_km": 0,  # Completar
            "substations": []      # Lista de subestaciones
        },
        "issues": {
            "voltage_drop": {},    # Documentar problemas
            "capacity": {},
            "reliability": {}
        }
    }
    
    # Guardar resumen
    output_path = Path("docs/phase1_system_overview.json")
    with open(output_path, 'w') as f:
        json.dump(system_info, f, indent=2)
    
    return system_info
```

### Fase 2: Modelado Topológico

**Objetivo**: Crear modelo digital de la red

```python
# src/topology/network_builder.py
"""Constructor del modelo de red"""

import networkx as nx
import pandas as pd

class NetworkBuilder:
    def __init__(self):
        self.graph = nx.Graph()
        
    def add_node(self, node_id, **attributes):
        """Añade nodo (barra) al sistema"""
        self.graph.add_node(node_id, **attributes)
        
    def add_line(self, from_node, to_node, **parameters):
        """Añade línea entre nodos"""
        self.graph.add_edge(from_node, to_node, **parameters)
        
    def build_from_excel(self, nodes_file, lines_file):
        """Construye red desde archivos Excel"""
        # Cargar nodos
        nodes_df = pd.read_excel(nodes_file)
        for _, node in nodes_df.iterrows():
            self.add_node(node['id'], 
                         name=node['name'],
                         load_mw=node.get('load_mw', 0))
        
        # Cargar líneas
        lines_df = pd.read_excel(lines_file)
        for _, line in lines_df.iterrows():
            self.add_line(line['from'], line['to'],
                         length_km=line['length_km'],
                         r_ohm_km=line['r_ohm_km'],
                         x_ohm_km=line['x_ohm_km'])
        
        return self.graph
```

### Fase 3: Procesamiento de Datos

**Objetivo**: Preparar datos para análisis

```python
# src/data_loaders.py
"""Cargadores y validadores de datos"""

import pandas as pd
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        
    def load_historical_data(self, station: str) -> pd.DataFrame:
        """Carga datos históricos de una estación"""
        try:
            # Adaptar según formato de datos
            df = pd.read_csv(
                self.data_path / f"{station}_data.csv",
                parse_dates=['timestamp'],
                index_col='timestamp'
            )
            
            # Validación básica
            required_cols = ['voltage_kv', 'power_mw', 'reactive_mvar']
            missing_cols = set(required_cols) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Columnas faltantes: {missing_cols}")
            
            # Calcular valores p.u.
            df['voltage_pu'] = df['voltage_kv'] / NOMINAL_VOLTAGE_KV
            
            logger.info(f"Cargados {len(df)} registros de {station}")
            return df
            
        except Exception as e:
            logger.error(f"Error cargando datos de {station}: {e}")
            raise
```

### Fase 4: Análisis de Recursos Renovables

**Objetivo**: Modelar GD y BESS

```python
# src/solar/pv_model.py
"""Modelo simplificado de generación FV"""

import numpy as np
import pandas as pd

class PVModel:
    def __init__(self, capacity_mw: float, location: dict):
        self.capacity_mw = capacity_mw
        self.location = location
        
    def generate_profile(self, timestamps: pd.DatetimeIndex) -> pd.Series:
        """Genera perfil de generación FV"""
        # Modelo simplificado - reemplazar con modelo real
        hour = timestamps.hour
        
        # Perfil típico de generación
        generation = np.where(
            (hour >= 6) & (hour <= 18),
            self.capacity_mw * np.sin((hour - 6) * np.pi / 12),
            0
        )
        
        # Aplicar variabilidad
        generation *= np.random.normal(1, 0.1, len(generation))
        generation = np.clip(generation, 0, self.capacity_mw)
        
        return pd.Series(generation, index=timestamps, name='pv_generation_mw')
```

```python
# src/bess/battery_model.py
"""Modelo de sistema de almacenamiento"""

class BatteryModel:
    def __init__(self, power_mw: float, energy_mwh: float):
        self.power_mw = power_mw
        self.energy_mwh = energy_mwh
        self.soc = 0.5  # Estado de carga inicial 50%
        self.efficiency = 0.95
        
    def charge(self, power: float, duration_h: float) -> float:
        """Carga la batería"""
        power = min(power, self.power_mw)
        energy = power * duration_h * self.efficiency
        
        available_capacity = self.energy_mwh * (1 - self.soc)
        energy_stored = min(energy, available_capacity)
        
        self.soc += energy_stored / self.energy_mwh
        return energy_stored
        
    def discharge(self, power: float, duration_h: float) -> float:
        """Descarga la batería"""
        power = min(power, self.power_mw)
        energy_requested = power * duration_h
        
        available_energy = self.energy_mwh * self.soc
        energy_delivered = min(energy_requested, available_energy) * self.efficiency
        
        self.soc -= energy_delivered / self.efficiency / self.energy_mwh
        return energy_delivered
```

---

## 🎯 Paso 3: Crear Dashboard

### Dashboard Multi-página Base

```python
# dashboard/app_multipagina.py
"""Dashboard principal del proyecto"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

# Inicializar app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Layout principal
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        html.H1("Análisis GD - Mi Sistema"),
        dcc.Link('Inicio | ', href='/'),
        dcc.Link('Fase 1 | ', href='/fase1'),
        dcc.Link('Fase 2 | ', href='/fase2'),
        dcc.Link('Fase 3 | ', href='/fase3'),
        dcc.Link('Fase 4', href='/fase4'),
    ]),
    html.Hr(),
    html.Div(id='page-content')
])

# Callback para navegación
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/fase1':
        return html.Div([
            html.H2("Fase 1: Comprensión del Sistema"),
            # Añadir visualizaciones
        ])
    # Más páginas...
    else:
        return html.Div([
            html.H2("Bienvenido al Dashboard"),
            html.P("Selecciona una fase para comenzar")
        ])

if __name__ == '__main__':
    app.run_server(debug=True)
```

---

## 📈 Paso 4: Análisis y Resultados

### Plantilla de Análisis Económico

```python
# scripts/analysis/economic_evaluation.py
"""Evaluación económica del proyecto"""

import numpy as np
import pandas as pd

def calculate_lcoe(capex, opex_annual, energy_annual, lifetime=25, discount_rate=0.1):
    """Calcula LCOE del proyecto"""
    # Valor presente de costos
    pv_costs = capex + sum(
        opex_annual / (1 + discount_rate)**year 
        for year in range(1, lifetime + 1)
    )
    
    # Valor presente de energía
    pv_energy = sum(
        energy_annual / (1 + discount_rate)**year 
        for year in range(1, lifetime + 1)
    )
    
    lcoe = pv_costs / pv_energy
    return lcoe

def calculate_npv(cash_flows, discount_rate=0.1):
    """Calcula VAN del proyecto"""
    npv = sum(
        cf / (1 + discount_rate)**i 
        for i, cf in enumerate(cash_flows)
    )
    return npv
```

---

## 🧪 Paso 5: Testing y Validación

### Tests Unitarios Base

```python
# tests/test_data_loader.py
"""Tests para cargador de datos"""

import pytest
import pandas as pd
from src.data_loaders import DataLoader

def test_load_historical_data():
    """Test carga de datos históricos"""
    loader = DataLoader("data/test")
    
    # Crear datos de prueba
    test_data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='15min'),
        'voltage_kv': 32.5,
        'power_mw': 1.5,
        'reactive_mvar': 0.5
    })
    
    # Guardar y cargar
    test_data.to_csv("data/test/station1_data.csv")
    df = loader.load_historical_data("station1")
    
    assert len(df) == 100
    assert 'voltage_pu' in df.columns
    assert df['voltage_pu'].mean() == pytest.approx(32.5/33.0, 0.01)
```

---

## 🎨 Personalización por Tipo de Proyecto

### Proyecto A: Red Urbana Densa
```python
# Ajustes específicos
VOLTAGE_LIMITS = {"min": 0.97, "max": 1.03}  # Límites más estrictos
MIN_POWER_FACTOR = 0.92  # Mayor exigencia
ANALYSIS_RESOLUTION = "5min"  # Mayor resolución
```

### Proyecto B: Red Rural Extensa (como Línea Sur)
```python
# Ajustes específicos
VOLTAGE_LIMITS = {"min": 0.90, "max": 1.05}  # Límites más flexibles
MAX_LINE_LENGTH_KM = 300  # Líneas largas
CONSIDER_TEMPERATURE = True  # Efectos térmicos importantes
```

### Proyecto C: Microrred Aislada
```python
# Ajustes específicos
ISOLATED_MODE = True
FREQUENCY_CONTROL = True  # Control de frecuencia crítico
SPINNING_RESERVE = 0.2  # 20% reserva rodante
```

---

## ❓ Troubleshooting Común

### Error: "No module named 'pandapower'"
```bash
# Instalar dependencia opcional
pip install pandapower
```

### Error: "Insufficient data quality"
```python
# Aumentar tolerancia en validación
MAX_MISSING_DATA_PCT = 10.0  # En vez de 5.0
```

### Error: "Memory overflow with large datasets"
```python
# Usar chunks para procesar
for chunk in pd.read_csv('large_file.csv', chunksize=10000):
    process_chunk(chunk)
```

---

## 📚 Recursos Adicionales

- [Metodología CLAUDE](../CLAUDE_METHODOLOGY.md) - Framework completo
- [Caso Línea Sur](../CLAUDE.md) - Ejemplo real implementado
- [Documentación Dash](https://dash.plotly.com/) - Para el dashboard
- [PandaPower Docs](http://www.pandapower.org/) - Para flujos de potencia

---

**¿Necesitas ayuda?** Abre un issue en el repositorio o consulta la documentación del caso de estudio.