# Tests para Sistema PSFV+BESS

Este directorio contiene la suite completa de tests para validar la consistencia de datos y correcta operación del sistema de simulación PSFV+BESS.

## Estructura de Tests

```
tests/
├── unit/                    # Tests unitarios
│   ├── test_data_manager_bess.py    # Tests de funciones BESS en DataManager
│   ├── test_bess_model.py           # Tests del modelo físico BESS
│   └── test_bess_validator.py       # Tests del validador de eficiencia
├── integration/             # Tests de integración
│   └── test_solar_bess_pipeline.py  # Pipeline completo Solar→BESS→Validación
├── audit/                   # Tests de auditoría de datos
│   └── test_data_consistency.py     # Verificación de leyes físicas
├── regression/              # Tests de regresión (futuro)
├── conftest.py             # Fixtures compartidos de pytest
└── run_test_matrix.py      # Script para ejecutar matriz completa

```

## Ejecución de Tests

### Ejecutar todos los tests:
```bash
pytest
```

### Ejecutar con reporte de cobertura:
```bash
pytest --cov --cov-report=html
```

### Ejecutar solo tests unitarios:
```bash
pytest tests/unit -v
```

### Ejecutar solo tests de auditoría:
```bash
pytest -m audit -v
```

### Ejecutar matriz completa de configuraciones:
```bash
python tests/run_test_matrix.py
```

## Tests Implementados

### 1. Tests Unitarios

#### DataManager BESS (`test_data_manager_bess.py`)
- ✓ Estructura correcta de perfiles solares
- ✓ Valores físicamente razonables
- ✓ Conservación de energía
- ✓ Métricas diarias correctas
- ✓ Optimización BESS funcional
- ✓ Diferentes estrategias producen diferentes resultados

#### BESS Model (`test_bess_model.py`)
- ✓ Inicialización correcta
- ✓ Límites de carga/descarga respetados
- ✓ Conservación de energía en carga
- ✓ Conservación de energía en descarga
- ✓ Eficiencia round-trip 95%
- ✓ Límites SOC nunca violados (10-95%)
- ✓ Límites de potencia respetados
- ✓ Conteo correcto de ciclos

#### BESS Validator (`test_bess_validator.py`)
- ✓ Validación multi-tecnología (90%, 93%, 95%)
- ✓ Conversión correcta anual→diario
- ✓ Validación con curtailment
- ✓ Extracción de features ML
- ✓ Sugerencias de mejora

### 2. Tests de Integración

#### Pipeline Completo (`test_solar_bess_pipeline.py`)
- ✓ Flujo completo Solar→BESS→Validación
- ✓ Optimización→Simulación
- ✓ Comparación de múltiples estrategias
- ✓ Diferentes ratios BESS/Solar
- ✓ Escenarios extremos
- ✓ Consistencia de días típicos

### 3. Tests de Auditoría

#### Consistencia de Datos (`test_data_consistency.py`)
- ✓ Conservación de energía: Solar = Entregada + Pérdidas + Curtailed
- ✓ Eficiencias dentro de límites físicos (85-100%)
- ✓ Potencias nunca exceden límites nominales
- ✓ SOC siempre en [10%, 95%]
- ✓ Pérdidas siempre positivas y < 10%
- ✓ Consistencia mensual vs anual

## Configuraciones de Test Matrix

El script `run_test_matrix.py` ejecuta automáticamente:

- **Estaciones**: MAQUINCHAO, LOS MENUCOS, JACOBACCI
- **PSFV**: 0.5, 1.0, 2.0, 5.0 MW
- **BESS Power**: 0.5, 1.0, 2.0 MW
- **BESS Duration**: 1, 2, 4, 6 horas
- **Estrategias**: cap_shaving, flat_day, night_shift, ramp_limit

Total: ~432 configuraciones

## Métricas de Calidad

### Objetivo de Cobertura
- Componentes críticos: >80%
- DataManager BESS: >90%
- Modelos físicos: >85%

### Validaciones Críticas
1. **Conservación de Energía**: Error < 0.1%
2. **Eficiencia BESS**: 90-95% según tecnología
3. **Límites Físicos**: Siempre respetados
4. **Métricas Diarias**: Correctamente escaladas

## Ejecución en CI/CD

Para integración continua, agregar a `.github/workflows/tests.yml`:

```yaml
- name: Run tests
  run: |
    pip install pytest pytest-cov
    pytest --cov --cov-report=xml
    
- name: Run audit matrix
  run: |
    python tests/run_test_matrix.py
```

## Debugging

Si un test falla:

1. Ejecutar test específico con `-v` para ver detalles:
   ```bash
   pytest tests/unit/test_bess_model.py::TestBESSModel::test_energy_conservation_charge -v
   ```

2. Usar `--pdb` para debugging interactivo:
   ```bash
   pytest --pdb tests/unit/test_data_manager_bess.py
   ```

3. Ver logs detallados:
   ```bash
   pytest --log-cli-level=DEBUG
   ```

## Próximos Pasos

1. Implementar tests para estrategias BESS individuales
2. Agregar tests de regresión con resultados conocidos
3. Tests de performance para simulaciones grandes
4. Tests de UI/Dashboard (Selenium)