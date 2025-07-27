Enfoquemos el modelo para cuantificar FlujoTotal = FlujoPSFV + FlujosRed y, con eso, dimensionar cada clúster para maximizar valor económico total (no solo el fotovoltaico).

1. Marco conceptual
Definí el flujo anual total de caja atribuible a un clúster GD multifunción (solar + almacenamiento + soporte reactivo + efectos sobre la red):

FlujoTotal
𝑦
=
AhorroAutoconsumo
𝑦
+
Cr
e
ˊ
ditosExport
𝑦
⏟
FlujoPSFV
𝑦
+
Δ
P
e
ˊ
rdidas
𝑦
+
ValorQNight
𝑦
+
DiferimientoCAPEX
𝑦
+
PenalizacionesEvitadas
𝑦
+
OtrosImpactos
𝑦
⏟
FlujosRed
𝑦
−
OPEX
𝑦
FlujoTotal 
y
​
 = 
FlujoPSFV 
y
​
 
AhorroAutoconsumo 
y
​
 +Cr 
e
ˊ
 ditosExport 
y
​
 
​
 
​
 + 
FlujosRed 
y
​
 
ΔP 
e
ˊ
 rdidas 
y
​
 +ValorQNight 
y
​
 +DiferimientoCAPEX 
y
​
 +PenalizacionesEvitadas 
y
​
 +OtrosImpactos 
y
​
 
​
 
​
 −OPEX 
y
​
 
Luego calculás NPV, TIR, payback, etc., descontando el CAPEX inicial (PV, BESS, interface, STATCOM si aplica, obras de conexión, ingeniería).

2. Variables de decisión por clúster
Para cada clúster 
𝑐
c:

Variable	Símbolo	Tipo	Comentario
Potencia FV instalada DC	
𝑃
𝑐
FV
P 
c
FV
​
 	continua	kWp módulo.
Potencia AC inversor	
𝑃
𝑐
INV
P 
c
INV
​
 	continua	kVA disponible p/ P y Q.
Energía BESS	
𝐸
𝑐
BESS
E 
c
BESS
​
 	continua	MWh útil.
Potencia BESS	
𝑃
𝑐
BESS
P 
c
BESS
​
 	continua	MW carga/descarga.
Capacidad Q nocturna	
𝑄
𝑐
night
Q 
c
night
​
 	continua	kvar capacitivo/inductivo neto. Puede provenir del inversor o STATCOM add-on.
Fracción de energía autoconsumida localmente	
𝑓
𝑐
auto
f 
c
auto
​
 	dependiente	Función de perfiles carga vs FV + BESS.
Selección de sitio dentro del clúster	
𝑠
𝑐
,
𝑖
s 
c,i
​
 	binaria	Opcional si hay múltiples nodos candidatos.
Año de puesta en servicio	
𝑌
𝑐
COD
Y 
c
COD
​
 	discreta	Para deflactar costos y escalonar CAPEX.

3. Datos mínimos de entrada por clúster
Carga representativa

Potencia pico estimada 
𝑃
𝑐
peak
P 
c
peak
​
  (de transformadores + usuarios).

Energía anual estimada 
𝐸
𝑐
load
E 
c
load
​
 .

Mix de clases tarifarias (residencial, comercial, industrial) → tarifas y perfiles típicos horarios.

Calidad / criticidad

Resultado histórico (Penalizada/Fallida).

Usuarios afectados.

Índice de tensión mínima observada o proxy.

Parámetros de red simplificados

Resistencia equivalente vista desde el punto de conexión 
𝑅
eq
R 
eq
​
 .

Reactancia equivalente 
𝑋
eq
X 
eq
​
 .

Límite térmico aguas arriba (kVA) y margen remanente.

Costo estimado de refuerzo diferible.

Estructura tarifaria / penalizaciones

Tarifa energía ($/kWh) por clase.

Cargo por demanda pico ($/kW) si aplica.

Penalizaciones por bajo factor de potencia / baja tensión.

Valor económico de pérdidas técnicas (precio energía upstream + cargos).

Costos tecnológicos

CAPEX unitario PV ($/kWp DC).

CAPEX BESS ($/kWh y $/kW).

CAPEX para capacidad reactiva nocturna (kvar-cost; si reutilizás inversor sobredimensionado, costo incremental).

BOS / interconexión / terreno.

4. Desglose de los componentes de flujo
4.1 Flujo PSFV (autoconsumo + export)
AhorroAutoconsumo_y

𝐸
𝑐
,
𝑦
auto
⋅
𝑇
𝑎
𝑟
𝑖
𝑓
𝑎
𝑐
marginal
E 
c,y
auto
​
 ⋅Tarifa 
c
marginal
​
 
Donde 
𝐸
auto
=
min
⁡
(
𝐸
FV+descargaBESS
,
𝐸
load
)
E 
auto
 =min(E 
FV+descargaBESS
 ,E 
load
 ) por intervalo; agregás al año. Tarifa marginal puede incluir energía + transporte + impuestos evitables según esquema regulatorio.

CréditosExport_y (si corresponde)

𝐸
𝑐
,
𝑦
export
⋅
𝑃
𝑟
𝑒
𝑐
𝑖
𝑜
𝑐
export
E 
c,y
export
​
 ⋅Precio 
c
export
​
 
Si la normativa de GD da crédito a precio menor, o net billing.

Reducción demanda pico (si hay cargo demand):

Δ
𝑃
𝑐
,
𝑦
demand
⋅
𝐶
𝑎
𝑟
𝑔
𝑜
𝑐
demand
⋅
𝐶
𝐹
coinc
ΔP 
c,y
demand
​
 ⋅Cargo 
c
demand
​
 ⋅CF 
coinc
 
4.2 FlujosRed
a) Reducción de pérdidas técnicas
Usá sensibilidad lineal o cuadrática con respecto a potencia inyectada aguas abajo.

Simplificado radial:

𝑃
loss
=
𝐼
2
𝑅
=
(
𝑃
2
+
𝑄
2
)
𝑅
𝑉
2
P 
loss
​
 =I 
2
 R= 
V 
2
 
(P 
2
 +Q 
2
 )R
​
 
Inyectar 
Δ
𝑃
ΔP local reduce flujo aguas arriba:

Δ
𝑃
loss
≈
𝑆
𝑐
loss
⋅
Δ
𝑃
inj
ΔP 
loss
​
 ≈S 
c
loss
​
 ⋅ΔP 
inj
​
 
Calibrá 
𝑆
loss
S 
loss
  con un estudio base (power flow simplificado usando impedancias o pandapower). Valor económico anual:

Δ
𝑃
loss
,
𝑦
⋅
𝑃
𝑟
𝑒
𝑐
𝑖
𝑜
𝑦
energ
ı
ˊ
a_upstream
ΔP 
loss,y
​
 ⋅Precio 
y
energ 
ı
ˊ
 a_upstream
​
 
b) Q at Night (mejora tensión / factor de potencia / penalizaciones)
Relación de sensibilidad de tensión:

Δ
𝑉
≈
𝑅
⋅
Δ
𝑃
+
𝑋
⋅
Δ
𝑄
𝑉
nom
ΔV≈ 
V 
nom
​
 
R⋅ΔP+X⋅ΔQ
​
 
De noche, 
Δ
𝑃
≈
0
ΔP≈0, así que 
Δ
𝑉
≈
(
𝑋
/
𝑉
)
⋅
𝑄
night
ΔV≈(X/V)⋅Q 
night
 .

Traducís a $$ de tres maneras (elegí según data disponible, podés usar más de una):

Penalizaciones evitadas por baja tensión: Si EDERSA paga multas cuando V < umbral, convertí horas violadas reducidas × $/hora/usuario.

Costo evitado de equipamiento de compensación: Capex STATCOM + O&M / vida → anualizado × fracción cubierta por GD inverters.

Mejora factor de potencia: Evita cargos por reactivo o sobrecarga térmica, traducido a $/kvar-año.

c) Diferimiento de inversiones
Si la carga neta pico aguas arriba cae o su tasa de crecimiento baja, se difiere upgrade de línea o trafo.

Regla práctica: cada clúster tiene un MargenRemanente 
𝑀
𝑐
M 
c
​
  (kVA) y un crecimiento esperado 
𝑔
𝑐
g 
c
​
 . Sin GD, año de sobrecarga 
𝑌
0
Y 
0
​
 . Con GD efectivo (reducción de pico 
Δ
𝑃
𝑐
𝑝
𝑒
𝑎
𝑘
ΔP 
c
peak
​
 ), nuevo año 
𝑌
1
Y 
1
​
 . Valor diferencial:

DiferimientoCAPEX
𝑐
=
𝐶
𝐴
𝑃
𝐸
𝑋
upgrade
(
1
+
𝑟
)
𝑌
1
−
𝐶
𝐴
𝑃
𝐸
𝑋
upgrade
(
1
+
𝑟
)
𝑌
0
DiferimientoCAPEX 
c
​
 = 
(1+r) 
Y 
1
​
 
 
CAPEX 
upgrade
​
 
​
 − 
(1+r) 
Y 
0
​
 
 
CAPEX 
upgrade
​
 
​
 
Si 
𝑌
1
>
𝑌
0
Y 
1
​
 >Y 
0
​
 , el valor es positivo (ahorro). Podés distribuirlo como ingreso equivalente anual usando factor de recuperación de capital (CRF).

d) Penalizaciones de calidad evitadas
Si el regulador aplica multas por KPIs (SAIDI/SAIFI, tensión fuera de rango, etc.), estimá reducción porcentual derivada de la intervención y multiplicá por el costo histórico anual de penalizaciones en esa sucursal/alimentador.

5. KPI integradores para comparar clústeres
KPI	Fórmula / Descripción	Uso
NPV	FlujoTotal descontado – CAPEX	Ranking inversión.
IRR	Tasa interna	Umbral 15 %.
Payback simple	Años CAPEX / Flujo bruto	Comunicación ejecutiva.
Beneficio/Costo (B/C)	Valor presente beneficios / CAPEX	Priorizar bajo restricción de capital.
$/usuario mejorado	CAPEX / usuarios beneficiados	Político / social.
Mejora tensión %	ΔV promedio o reducción horas <0.95 pu	Métrica técnica.
Reducción pérdidas %	(kWh perdidos base - post) / base	Eficiencia sistémica.
Capex diferido / MWh FV	Eficiencia sistémica normalizada.	

Podés armar un Índice Compuesto de Valor GD (ICV-GD) ponderando NPV, ΔV, pérdidas, usuarios.

6. Algoritmo de dimensionamiento (iterativo / optimización)
Paso A. Preparar “gemelo reducido” del clúster
Agregá cargas por transformador con pesos por criticidad.

Calculá impedancias equivalentes aguas arriba (MST ya generado te ayuda).

Paso B. Generar escenarios de perfiles
Para cada tipo de usuario (res/com/ind) tenés perfil horario típico verano/invierno. Escalalos para que el pico anual reproduzca 
𝑃
𝑐
𝑝
𝑒
𝑎
𝑘
P 
c
peak
​
  y energía 
𝐸
𝑐
𝑙
𝑜
𝑎
𝑑
E 
c
load
​
 .

Perfil FV típico por zona (factor de planta medio) → curva diaria normalizada.

Si BESS: estrategia simple (cargar con excedente solar, descargar en pico noche).

Paso C. Simulación rápida paramétrica
Barré rejilla de 
𝑃
𝐹
𝑉
P 
FV
 , 
𝐸
𝐵
𝐸
𝑆
𝑆
E 
BESS
 , 
𝑄
𝑛
𝑖
𝑔
ℎ
𝑡
Q 
night
 . Para cada punto:

Calcular autoconsumo, export, reducción demanda.

Calcular flujos en red (Δpérdidas, ΔV con Q, reducción pico).

Traducir a $ anuales.

Calcular métricas financieras.

Paso D. Ajuste fino (optimización)
Objetivo: Max NPV o Max ICV-GD sujeto a TIR≥X y límite CAPEX.

Usa Pyomo o pulp con funciones linealizadas (piecewise) o scipy.optimize si dejás continuo no lineal.

Si combinás selección de sitios → MILP.

Paso E. Curva de valor marginal
Generá “beneficio marginal acumulado” vs kW instalado para mostrar dónde el beneficio sistémico se satura. Ese punto define el tamaño económico óptimo (no solo técnico).

7. Traducción a código (stack Python)
Cálculo & datos

pandas, numpy, polars (opcional para velocidad).

geopandas + shapely para clustering espacial y buffers de red.

scikit-learn DBSCAN/HDBSCAN para identificar agrupamientos de trafo críticos.

Modelado de red liviano

networkx para MST / rutas.

pandapower (modo simple) para sensitividades P/Q→V y pérdidas en redes de distribución; podés auto-generar red equivalente por clúster.

Optimización

pyomo (flexible; soporta MILP/NLP).

pulp (más liviano) si mantenés lineal.

scipy.optimize.minimize para continuo sin enteros.

Análisis de incertidumbre

SALib para sensibilidad global.

numpy.random / @vectorized Monte Carlo.

Visualización

plotly para curvas económicas.

dash (ya tenés) para sliders interactivos de tamaño PV/BESS/Q y ver NPV en vivo.

8. Estructura de funciones recomendada
bash
Copiar
Editar
/model/
  economic.py          # tarifas, CRF, NPV, IRR
  loss_model.py        # sensitividades pérdidas
  voltage_model.py     # dV/dP, dV/dQ
  deferral_model.py    # valor CAPEX diferido
  penalty_model.py     # multas evitadas
  cluster_optimizer.py # función objetivo y solver
  scenarios.py         # perfiles carga/FV por zona
Clave: cada módulo devuelve $/año como función de (P_FV, E_BESS, Q_night, params_clúster).

9. Validación con datos reales (plan en 4 niveles)
Nivel 0 – Sanity check documental
Cruzar valores obtenidos por el modelo con: penalizaciones históricas EDERSA, costos estándar de refuerzo, tarifas vigentes. Ajustar supuestos.

Nivel 1 – Retro-cálculo sobre históricos
Tomar 2-3 alimentadores con datos de medidores (aunque sean mensuales). Calcular pérdidas estimadas vs energía vendida; validar orden de magnitud del modelo de pérdidas.

Nivel 2 – Mediciones dirigidas
En los 5 clusters top, instalar medidores temporales (tensión, corriente, PF) en cabecera y en trafo crítico durante 2-4 semanas. Usar estos datos para calibrar dV/dQ y dLoss/dP reales.

Nivel 3 – Piloto controlado
Instalar un sistema FV+BESS con capacidad de inyectar Q. Registrar antes/después (mínimo 90 días) y comparar:

Horas con V<0.95 pu.

Pérdidas estimadas (energía entrada vs salida).

Penalizaciones de calidad.

Esto genera evidencia empírica para regulador e inversores.

10. Datos que necesito de vos para arrancar los cálculos
Checklist inicial (prioridad alta → baja):

Tarifa marginal energía (USD/MWh o ARS/kWh) por clase en las zonas top 5.

Cargo por demanda pico (si existe) y método de medición (kW máx mensual, promedio, etc.).

Valor unitario de energía upstream para pérdidas (puede ser costo CAMMESA + cargos).

Historial de penalizaciones por baja tensión / calidad por sucursal o global EDERSA (aunque sea anual).

Lista de upgrades previstos: costo y año esperado (transformadores, líneas).

Costo unitario de STATCOM o equivalente por kvar vs costo incremental de sobredimensionar inversores FV.

Supuestos de factor de planta FV por zona (promedio anual y estacional).

Horizonte financiero y tasa de descuento a aplicar (r).

Con eso puedo ayudarte a armar plantillas de parámetros por clúster y scripts de cálculo.

11. Acción concreta propuesta
Te preparo un notebook base que, dado un CSV de clústeres con variables mínimas, barra tamaños PV/BESS/Q y devuelva tabla con FlujoPSFV, FlujosRed, NPV, TIR, ranking. Decime:

Formato del CSV (columnas disponibles hoy).

