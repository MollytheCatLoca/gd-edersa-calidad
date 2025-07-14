# Guía de Referencia – Modelar un Sistema PV + BESS para Optimizar la Exportación en Redes Débiles

*Enfocado en plantas de 1 – 5 MW, resolución 15 min, con opción de batería "serie", "paralelo" y configuraciones híbridas*

## 1. Conceptos Fundamentales

| Término | "Paralelo" (bus AC común) | "Serie" (bus DC común, cascada rara) |
|---------|---------------------------|--------------------------------------|
| **Ruta de energía** | PV ⇒ inversor FV ⇒ bus AC ⇄ red ↔ BESS ⇄ bus AC | PV ⇒ bus DC ⇒ BESS ⇒ inversor híbrido ⇒ red |
| **¿PV pasa por la batería?** | No, salvo fracción que el control decida | Sí, toda la potencia sale vía la batería/inversor |
| **Uso típico** | Retro-fit de BESS a parque FV existente; microred C&I; apoyo de distribución | Plantas híbridas diseñadas desde cero (utility-scale DC-coupled) o sistemas off-grid compactos |

## 2. Fórmulas Básicas de Agregación

### 2.1 Paralelo (n módulos idénticos)

**Potencia total:**
```
P_tot = Σ(i=1 to n) P_i
```

**Energía nominal:**
```
E_tot = Σ(i=1 to n) E_i
```

**SOC equivalente:**
```
SOC_eq = Σ_i(E_i · SOC_i) / E_tot
```
*(ponderación por energía de cada string)*

**Pérdidas instantáneas (inversores + AC):**
```
P_loss = n(P_fixed) + Σ_i(P_i² / (η_inv · V_bus² · R))
```

### 2.2 Serie (bus DC común)

**Potencia total DC:**
```
P_DC = P_PV + P_BESS
```
*(signo de BESS según carga/descarga)*

**Potencia AC exportada:**
```
P_AC = η_inv(P_DC - P_aux)
```

**SOC batería:**
```
SOC(t) = SOC(t₀) + ∫(P_BESS/E_nom)dt
```

**Pérdidas globales:** doble conversión PV→DC→AC cuando la energía no entra al BESS.

> Para tu simulador bastan dos bloques: un balanceador DC (PV+BESS) y un inversor.

## 3. Ventajas y Limitaciones

| Aspecto | Paralelo | Serie (DC-coupled) |
|---------|----------|-------------------|
| **Ventajas** | • Flexibilidad: PV exporta directo<br>• Retrofit sencillo<br>• Fácil expansión modular<br>• Inversores estándar FV + PCS | • Mayor eficiencia si gran parte del PV va a batería<br>• Un solo trafo y protecciones<br>• El BESS absorbe excedente antes de que aparezca curtailment (modo "clipping recapture") |
| **Limitaciones** | • Doble conversión cuando el BESS absorbe PV (≈ −10% round-trip)<br>• Cada PCS añade pérdidas fijas<br>• Más protecciones AC | • El inversor híbrido es "cuello de botella"<br>• Menos flexibilidad operativa; ampliar potencia exige más DC/DC o inverter rating<br>• Diseño más complejo para retrofit |
| **Confiabilidad** | Falla de un PCS reduce potencia proporcional; la planta sigue operativa. Por diseño n+1 es sencillo. | Falla del inversor híbrido → deja fuera a PV + BESS. Se mitiga con redundancia interna, pero el punto único existe. |

## 4. Control y Operación

### Distribución de potencia en paralelo – dos bucles típicos:

**Volt-Watt droop:**
```
P_BESS = k_V(V_set - V_PCC)
```
*para soporte de tensión*

**Ramp-rate filter:**
```
P_BESS = -α(dP_PV/dt)
```
*(opuesto a la derivada PV)*

### Balanceo de SOC
Si las unidades son idénticas basta droop `P_i = f(SOC_i)`. Dos métodos:

1. **Charge-share droop:** más SOC ⇒ menor corriente de carga; menos SOC ⇒ priorizar carga.
2. **State-of-charge scheduler:** rotar la unidad "maestra" cada x ciclos.

### Fallo de módulo
- **En paralelo:** se aísla con breaker; la potencia se redistribuye.
- **En serie DC-coupled:** se pierde toda la ruta AC si cae el inversor central (por eso se indica diseño N ≥ 2 inversores).

## 5. Integración con Solar FV

| Pregunta | Respuesta práctica |
|----------|-------------------|
| **Topología recomendada** | Paralelo AC para retrofit o si querés modularidad/flexibilidad.<br>Bus DC común si diseñás de cero y tu target es cero-curtail + alta eficiencia. |
| **Modelo energético** | Paralelo: `P_net = P_PV + P_BESS,AC` (restricciones de rampa, cap, V).<br>Serie: control DC decide cuánto va a batería vs inversor. |
| **AC-coupled vs DC-coupled** | AC-coupled se alinea con topología paralela; DC-coupled con la serie. |

## 6. Eficiencia del Sistema

**Round-trip paralelo:**
```
η_rt = η_bat · η_PCS²
```
*(≈ 0.9·0.96² ≈ 0.83)*

**Round-trip serie DC:** Una sola conversión DC⇄AC para descarga, evitarás una etapa al cargar desde PV (≈ 0.9·0.96 ≈ 0.86).

**Desbalance:** pérdidas por corriente circulante entre strings (< 1%) si droop mal ajustado.

**Topología & pérdidas:** AC-coupled suma pérdidas fijas por cada PCS (~100 W por 100 kW); DC-coupled ahorra un trafo y un inversor.

## 7. Caso Práctico – 4 × (1 MW / 2 MWh)

| Configuración | Potencia total | Energía total | Uso recomendado | Modularidad futura |
|---------------|----------------|---------------|-----------------|-------------------|
| **Paralelo AC (4 PCS)** | 4 MW | 8 MWh | • Suavizar rampas hasta ±2 MW/min<br>• Volt-VAR local<br>• Picos de demanda nocturna (2 h a 4 MW) | Altísima: se añade 1 contenedor extra sin tocar los existentes |
| **Serie DC (2 inversores híbridos)** | 4 MW | 8 MWh | • Evitar curtailment de clipping del PV<br>• Time-shift 4 h<br>• Máx. eficiencia | Media: ampliar potencia exige nuevo inversor / secciones DC |

### Comportamiento ante variación de demanda

- **En paralelo:** cada string entra en droop; la tensión se mantiene reparto proporcional → resistencia a fallos.
- **En serie:** el inversor central ve toda la carga; la batería modula internamente. Respuesta rápida igual, pero single-point-of-failure.

**Configuración óptima para una red débil:** 4 módulos en paralelo con control Volt-Watt (±0.05 pu dead-band) y ramp-rate ≤ 10%/min. Permite operar aun si un cubículo queda fuera.

## 8. Aspectos de Implementación

| Tema | Paralelo AC | Serie / DC-coupled |
|------|-------------|-------------------|
| **Inversores** | Uno por contenedor (PCS). PV mantiene su inversor propio. | Uno o dos inversores híbridos "grid-tie". |
| **Protecciones** | Breaker individual por contenedor + interlock neutro; relés 50/51, 27/59. | Protección DC adicional (fuses, contactores). Protección de bus DC contra arco. |
| **Sincronización** | Cada PCS sigue PLL de red. Compartir fase via droop P-f para repartir carga. | Inversor híbrido único se sincroniza; si hay dos, uno actúa master, otro follower vía comunicación óptica. |

## Estrategias Básicas de Exportación para tu Dashboard de Perfiles

**Hipótesis:** un día cualquiera, ⚡ E_gen = E_exp + E_pérdidas_BESS. Se busca E_gen ≈ E_exp (caso optimista, pérdidas < 10%).

| Estrategia | Lógica | Parámetros a tunear | Resultado esperado |
|------------|--------|-------------------|-------------------|
| **Ramp-limit** | BESS absorbe/inyecta para limitar dP/dt ≤ r_max | r_max (kW/min) | ≈ 1–2% energía perdida; voltaje estable; potencia no plana |
| **Cap-shaving** | BESS evita superar cap P_max | Cap, h de storage | Curtail < 3%; perfil meseta; tensión controlada |
| **Flat-day** | BESS mantiene potencia fija P_flat 10 h; descarga resto | P_flat, h de storage | Curva "mesa"; toda energía salida, pérdidas ≈ rt-loss |
| **Night-shift** | Carga en pico solar, descarga 18 – 23 h | SOC trigger, ventana descarga | Tensión elevada en valle vespertino; potencia cero al mediodía |

Para cada caso tu simulador evaluará: V(PCC), FR, RoCoF, curtail, y CAPEX. Aplica la topología paralela o serie según quieras maximizar flexibilidad o eficiencia.

## 9. Cómo Dimensionar el BESS para Cero Curtailment

**Objetivo:** todo lo que produce el parque (E_gen) debe salir a red el mismo día
```
E_exp = E_gen - E_pérdidas_BESS
```
*(≈ 95–97% de E_gen)*

### 9.1 Lógica de Cálculo Paso-a-Paso

**Entradas del usuario:**
- `P_pv` [MW] - potencia pico FV (1 – 10)
- `Estrategia` - 'cap' (límite) ó 'flat' (potencia plana)
- `P_target` [MW] - cap o nivel plano
- `η_rt` [-] - round-trip (0.85–0.9)
- `Δt` [h] - resolución = 0.25

**Salidas:**
- `P_BESS_req` [MW] - potencia PCS necesaria
- `E_BESS_req` [MWh] - capacidad útil necesaria

#### 9.1.1 Cargar o generar la curva P_PV(t)
En prototipo se usa la campana "sin²" normalizada al pico y escalada a:
```
E_día = 1850/365 ≈ 5.07 MWh/MWp
```

#### 9.1.2 Definir la referencia de exportación P_ref(t)

| Modo | Fórmula |
|------|---------|
| **Cap-shaving** | P_ref(t) = min(P_PV(t), P_cap) |
| **Flat** | P_ref(t) = P_flat si h_ini ≤ t < h_fin, 0 otro |

#### 9.1.3 Calcular excedentes y déficits
```
ΔP(t) = P_PV(t) - P_ref(t)
```
- Excedente (ΔP > 0): hay que cargar la batería
- Déficit (ΔP < 0): hay que descargar

#### 9.1.4 Integrar para obtener requisitos mínimos
```python
E_cumsum = 0
E_max = 0      # MWh ⇒ capacidad mínima
P_max = 0      # MW  ⇒ potencia PCS mínima

for ΔP in curva:
    E_cumsum += ΔP * Δt
    if E_cumsum < 0:           # batería no puede ser negativa
        E_cumsum = 0
    E_max = max(E_max, E_cumsum)
    P_max = max(P_max, ΔP)     # pico positivo (carga)
    P_max = max(P_max, -ΔP)    # pico negativo (descarga)
```

```
E_BESS_req = E_max / η_c     # corrige la eficiencia de carga
P_BESS_req = P_max           # si PCS simétrico
```

#### 9.1.5 Verificación de pérdidas
Con η_rt y los flujos reales, comprueba:
```
E_exp = E_gen - E_carga/η_rt + E_descarga·η_rt
```
En dashboard se muestra el gap; si > 2% se pide batería un poco mayor.

### 9.2 Reglas Rápidas (campana tipo sin², 1 MWp)

| Estrategia | Límite elegido | P_BESS | E_BESS | Comentario |
|------------|----------------|---------|---------|------------|
| **Cap-shave suave** | 0.7 MW | ≈ 0.3 MW | ≈ 0.8 MWh (≈ 0.8 h) | Curtail 0% con 4% pérdidas |
| **Cap-shave fuerte** | 0.5 MW | ≈ 0.5 MW | ≈ 2.0 MWh (≈ 4 h) | Cero curtail; plano visible |
| **Flat 10–18 h** | 0.5 MW | ≈ 0.5 MW | ≈ 2.0 MWh | Igual que arriba pero salida constante |
| **Shift tarde** | 0 MW día / 0.6 MW 18-22 h | ≈ 0.6 MW | ≈ 2.4 MWh | Exporta solo al atardecer |

**Escalado lineal:** para 10 MW basta multiplicar resultados por 10 (mismo perfil).

### 9.3 Algoritmo Resumen para tu Dashboard

```python
def size_bess(P_pv_mw, mode, target_kw, window=(8,22), η_rt=0.9):
    curve = pv_sin2(P_pv_mw)                # genera 96 puntos de 15 min
    if mode == "cap":
        Pref = np.minimum(curve, target_kw)
    elif mode == "flat":
        Pref = np.where((hours >= window[0]) & (hours < window[1]), target_kw, 0)
    
    ΔP = curve - Pref
    Ecum = 0; Emax = 0; Pmax = 0
    
    for dP in ΔP:
        Ecum = max(0, Ecum + dP * 0.25)
        Emax = max(Emax, Ecum)
        Pmax = max(Pmax, abs(dP))
    
    Ereq = Emax / np.sqrt(η_rt)
    return Pmax, Ereq            # MW, MWh
```

Integrás, mostrás potencias/energías y el CAPEX estimado con:
```
C = P_BESS · 150 + E_BESS · 300 USD
```
*(o los que cargue el usuario)*

### 9.4 Híbridos "serie + paralelo"

Si querés probar algo intermedio:
- PV paralelo (AC directo) + rama DC-coupled de ~30% del campo para clipping-recapture

**Modelo:**
- Parte de la potencia PV va a la batería en DC (alto rendimiento)
- El resto se vuelca a red sin pasar por BESS
- Algoritmo se ejecuta solo sobre la fracción "cedida" al buffer

Con eso podés reducir E_BESS ≈ 1.5 h y aun así llegar a 0% curtailment.

### 9.5 Tabla de Entrada Recomendada en el Dashboard

| Campo | Rango sugerido | Uso |
|-------|----------------|-----|
| Potencia PV (MW) | 1 – 10 | slider |
| Estrategia | "Cap", "Flat", "Shift" | dropdown |
| Target kW | 0.5–1.0·P_pv | num |
| Duración ventana | h_ini, h_fin | time-pick |
| η round-trip | 0.85–0.92 | slider |
| Capex $/kW, $/kWh | editables | cost analysis |

El motor calcula P_BESS, E_BESS, pérdidas y grafica la curva sin curtailment.

### 9.6 Ideas Clave y "Cuidados" para Usar el Snippet

**Resolución fija**
- Usa 15 min (Δt = 0.25 h). Si necesitas 5 min, cambia step_h y recuerda escalar las rampas.

**Curva PV sintética**
- La función `pv_sin2_curve()` da una campana tipo sin² ajustada a 5.07 MWh/MWp-día
- Sustituila por datos reales (vector curve) para tu sitio y estación si querés precisión

**Algoritmo "sin curtailment"**
- Integra el excedente positivo (cum_energy) y encuentra su máximo → energía mínima
- Toma el pico de |ΔP| → potencia PCS mínima
- Corrige la energía por eficiencia (√η_rt)
- Ojo: el inversor debe ser bidireccional y simétrico; si tu PCS es 0.5 C, verificá que P_bess ≤ 0.5·E_bess

**Eficiencia real**
- 90% round-trip ⇒ η_c ≈ η_d ≈ 0.95. Ajustalo si usás otras químicas
- El modelo ignora pérdidas auxiliares (HVAC, BMS). Añadí +3% energía si querés ser conservador

**Ventanas planas**
- Para mode="flat" cambiá window=(h_ini,h_fin) y target
- Si la batería no alcanza (E_bess insuficiente) la función te dará un P_bess gigante

**Escalabilidad**
- El algoritmo es lineal: P y E se multiplican casi exactamente por la potencia PV
- Ejemplo: 1 MW con cap 0.6·P requiere ≈ 0.3 MW / 0.8 MWh; para 10 MW ⇒ 3 MW / 8 MWh

**Validación**
- Después de dimensionar, simula el despacho real y comprueba que cum_energy nunca supera E_bess
- Ajusta un 10% de margen en campo por degradación y variabilidad meteorológica

**Protecciones y rampas**
- Si tu código de red limita ramp-rate (ej. 10%/min), introduce ese chequeo en la fase de simulación

**GUI**
- Conecta sliders para P_pv, target, η_rt; muestra la tabla y un gráfico PV vs exportación
- Permite editar costo $/kWh y $/kW para mostrar CAPEX

**Series vs paralelo**
- El cálculo es idéntico; sólo cambia cómo distribuyas P_bess y E_bess entre contenedores
- En paralelo AC basta dividir; en DC compartido vigila que el inversor híbrido ≥ P_bess

Con el snippet, obtendrás automáticamente la tabla "Dimensionado_BESS_zero_curtail" para cualquier potencia y estrategia básica.