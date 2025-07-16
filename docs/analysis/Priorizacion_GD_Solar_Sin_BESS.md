Análisis Técnico y Metodología de Priorización para la Integración de Generación Solar Distribuida en Redes de Distribución con Calidad de Servicio Deficiente
Resumen Ejecutivo
Este informe presenta un análisis técnico exhaustivo y una metodología de priorización para la instalación de Generación Distribuida (GD) solar fotovoltaica sin sistemas de almacenamiento de energía en baterías (BESS) en redes de distribución que presentan problemas de calidad de servicio. Ante el desafío de mejorar la calidad en 2,690 transformadores de distribución sin disponer de curvas de demanda horaria, se ha desarrollado un marco de análisis que combina fundamentos teóricos, criterios de selección robustos y una metodología de estimación basada en proxies para cuantificar los impactos. El objetivo final es la creación de un "Índice de Aptitud Solar sin BESS" (IAS), un sistema de puntuación multi-criterio diseñado para identificar y priorizar aquellos clusters de transformadores donde la GD solar puede ofrecer el máximo beneficio técnico (mejora de tensión, reducción de pérdidas) con el mínimo riesgo de impacto adverso (sobretensión, sobrecarga de activos). La metodología propuesta es transparente, defendible y adaptable a las prioridades estratégicas de la empresa distribuidora, proveyendo una herramienta de planificación para optimizar las inversiones en un contexto de datos limitados. Se incluyen consideraciones específicas para el marco regulatorio y las características de consumo de Argentina, con un enfoque en la provincia de Río Negro.

1. Fundamentos del Impacto de la GD Solar en Redes de Distribución
La integración de generación solar fotovoltaica en redes de distribución, concebidas históricamente para un flujo de potencia unidireccional, introduce cambios fundamentales en su operación. Comprender estos cambios es esencial para aprovechar sus beneficios y mitigar sus riesgos.

1.1. Interacción con el Perfil de Tensión
El impacto más directo de la GD solar es sobre el perfil de tensión del alimentador. Las redes de distribución, especialmente las radiales, experimentan una caída de tensión progresiva a medida que la distancia desde la subestación aumenta, debido a la impedancia de los conductores.   

Soporte de Tensión (Beneficio): La inyección de potencia activa (P 
GD
​
 ) por parte de un sistema solar en un punto del alimentador contrarresta la caída de tensión, elevando el voltaje local. El cambio de tensión (ΔV) en un nodo puede aproximarse por la siguiente ecuación, donde R y X son la resistencia y reactancia de la línea, y P 
GD
​
  y Q 
GD
​
  son las potencias activa y reactiva inyectadas :   

ΔV≈ 
V 
nominal
​
 
R⋅P 
GD
​
 +X⋅Q 
GD
​
 
​
 
Dado que los sistemas solares sin BESS operan típicamente con un factor de potencia unitario (Q 
GD
​
 ≈0), el principal efecto de soporte de tensión proviene de la inyección de potencia activa (P 
GD
​
 ) actuando sobre la resistencia (R) de la línea. En alimentadores largos, con alta carga diurna y problemas de subtensión, la GD solar funciona como un soporte de tensión localizado, mejorando la calidad del suministro en los puntos más críticos.   

Sobretensión (Riesgo): El principal desafío técnico surge cuando la generación solar excede la demanda local, provocando un Flujo de Potencia Inverso (Reverse Power Flow, RPF) hacia la subestación. En este escenario, la misma física que provee el soporte de tensión causa ahora una elevación de la misma por encima de los límites operativos permitidos (típicamente    

+5% a +10% del valor nominal), un fenómeno conocido como sobretensión. Las redes más "débiles" (con alta impedancia), que son las que más se benefician del soporte de tensión, son también las más vulnerables a la sobretensión por RPF.   

Interacción con Reguladores de Tensión: La variabilidad de la generación solar, causada por el paso de nubes, puede provocar un ciclado excesivo de los equipos de regulación de tensión como los cambiadores de tomas bajo carga (OLTC) y los reguladores de línea. Este aumento en las operaciones acelera su desgaste mecánico y puede complicar la coordinación de la regulación a lo largo del alimentador.   

1.2. Efecto sobre las Pérdidas Técnicas
Las pérdidas técnicas por efecto Joule en los conductores de la red son proporcionales al cuadrado de la corriente que circula por ellos (P 
p 
e
ˊ
 rdidas
​
 =I 
2
 R). Al generar energía cerca de los centros de consumo, la GD solar reduce la magnitud de la corriente que debe ser transportada desde la subestación, disminuyendo así las pérdidas totales del sistema.   

La ubicación de la GD es crucial para maximizar este beneficio. Una heurística comúnmente aceptada, conocida como la "regla de los 2/3", sugiere que la ubicación óptima para la reducción de pérdidas se encuentra aproximadamente a dos tercios de la longitud del alimentador desde la subestación. Una instalación demasiado cercana a la subestación no alivia significativamente la corriente en la mayor parte del alimentador, mientras que una instalación demasiado lejana puede inducir un RPF que aumente las pérdidas en el tramo inicial del mismo. En escenarios óptimos, la reducción de pérdidas puede ser sustancial, con estudios mostrando disminuciones del 50-60%.   

1.3. Impacto en la Cargabilidad de Activos de Red
La GD solar impacta directamente la cargabilidad de los transformadores y conductores de la red.

Transformadores de Distribución: Durante las horas de máxima irradiación solar, la GD reduce la carga neta que alimenta el transformador, disminuyendo su carga y temperatura de operación. Esto es especialmente beneficioso para transformadores que operan cerca de su límite térmico en picos diurnos, ya que puede extender su vida útil y posponer la necesidad de inversiones en repotenciación. Sin embargo, el RPF presenta un riesgo severo. Los transformadores de distribución estándar (según IEEE C57.12.00) están diseñados para una operación "step-down" (reductora). Un flujo inverso significativo puede sobrecargarlos, causando sobrecalentamiento, aumento de las pérdidas del núcleo por sobreexcitación y una degradación acelerada del aislamiento, lo que reduce drásticamente su vida útil.   

Conductores: De manera similar, los conductores se benefician de la reducción de la corriente durante los picos de demanda diurnos. No obstante, deben estar dimensionados para soportar la corriente máxima, independientemente de la dirección del flujo.

1.4. Limitaciones Inherentes de la GD Solar sin Almacenamiento
A pesar de sus beneficios, la GD solar sin BESS presenta limitaciones intrínsecas que deben ser gestionadas.

Intermitencia y No Despachabilidad: La generación solar es variable e intermitente, dependiente de las condiciones climáticas, y no es despachable, es decir, no puede ser controlada para seguir las variaciones de la demanda. Esto puede causar fluctuaciones rápidas de potencia, resultando en parpadeo (flicker) y oscilaciones de tensión.   

Calidad de la Onda: Los inversores, necesarios para convertir la corriente continua (CC) de los paneles a corriente alterna (CA) compatible con la red, son dispositivos de electrónica de potencia que pueden introducir distorsión armónica. Una alta concentración de inversores puede elevar la Distorsión Armónica Total (THD) por encima de los límites normativos (ej. IEEE 519). Adicionalmente, fallos en los inversores pueden provocar la inyección de corriente continua (DC Injection), un fenómeno que puede saturar los núcleos de los transformadores, causando sobrecalentamiento, ruido y fallas operativas.   

Desafíos para la Protección: El RPF altera los principios de funcionamiento de los sistemas de protección de redes radiales, que asumen un flujo unidireccional. Esto puede llevar a disparos incorrectos de relés, ceguera de protección (la falla no es vista por el dispositivo) o una des-coordinación entre fusibles y reconectadores, comprometiendo la seguridad y confiabilidad del sistema.   

Estándares de Interconexión: La familia de estándares IEEE 1547 establece los requisitos técnicos para la interconexión segura y fiable de recursos distribuidos. La versión más reciente, IEEE 1547-2018, dota a los inversores modernos ("smart inverters") de capacidades avanzadas para soportar la red, como el control de potencia reactiva y la respuesta a variaciones de frecuencia y tensión, ayudando a mitigar algunos de estos desafíos.   

La efectividad de la GD solar para mejorar la calidad de la red y no degradarla depende fundamentalmente de un factor: la coincidencia temporal y espacial entre la generación y la demanda. Cuando la energía se consume localmente en el momento en que se produce, los beneficios se maximizan y los riesgos se minimizan. Cuando hay un desajuste, los riesgos de sobretensión y sobrecarga de activos se vuelven predominantes.

2. Criterios Técnicos para la Priorización de Emplazamientos
La selección de ubicaciones óptimas para la GD solar sin BESS debe basarse en un análisis que integre las características de la demanda y de la red. El objetivo es encontrar aquellos puntos donde los beneficios son máximos y los riesgos, mínimos.

2.1. Criterios Basados en la Demanda: La Clave del Éxito sin Almacenamiento
La naturaleza de la carga es el factor más determinante para el éxito de la GD solar sin almacenamiento.

2.1.1. Coincidencia Horaria Demanda-Generación
El principio fundamental es maximizar el autoconsumo local en tiempo real, lo que ocurre cuando el perfil de consumo del cluster se alinea con la curva de generación solar. Dado que no se dispone de datos horarios, el tipo de usuario se convierte en el proxy más potente para estimar esta coincidencia.   

Alta Prioridad (Perfil Favorable): Se deben priorizar los clusters con una alta proporción de usuarios Comerciales e Industriales (C&I). Sus perfiles de consumo son típicamente diurnos, con picos de demanda durante las horas de trabajo (aprox. 8:00 a 18:00), lo que coincide de manera natural con las horas de máxima irradiación solar. Esta sincronía asegura que la mayor parte de la energía generada se consuma localmente, aliviando la red y minimizando el RPF.   

Baja Prioridad (Perfil Desfavorable): Los clusters con una composición mayoritariamente residencial deben recibir una prioridad baja. El consumo residencial típicamente presenta un pico matutino y un pico principal por la tarde-noche (aprox. 18:00 a 23:00), cuando la generación solar es nula o muy baja. En estos clusters, la alta generación solar al mediodía coincidiría con un valle de demanda, garantizando un RPF significativo y los problemas de sobretensión asociados.   

2.1.2. Densidad de Carga
Los clusters con una alta densidad de carga (alta demanda concentrada en un área geográfica reducida) poseen una mayor capacidad inherente para "absorber" la generación solar local. Esto reduce la probabilidad de que los excedentes de energía se exporten a la red principal, mitigando el riesgo de sobretensión en el alimentador. Por el contrario, las cargas de baja densidad y muy dispersas son más propensas a saturar la capacidad de consumo local rápidamente.   

2.1.3. Factor de Potencia de las Cargas
Aunque es un criterio secundario, las cargas con un factor de potencia (FP) más cercano a la unidad (predominantemente resistivas) se benefician de manera más directa del soporte de tensión proporcionado por la inyección de potencia activa de la GD solar. Esto es especialmente cierto en redes de distribución con una alta relación Resistencia/Reactancia (R/X).

2.2. Criterios Basados en la Red: Identificando los Puntos Más Vulnerables y Receptivos
Las características físicas y eléctricas del alimentador determinan su capacidad para beneficiarse de la GD.

2.2.1. Características del Alimentador
Longitud e Impedancia Acumulada: Se debe dar prioridad a los alimentadores largos y con alta impedancia acumulada. Estos son, por definición, los más "débiles" eléctricamente y, por lo tanto, los que sufren las mayores caídas de tensión y pérdidas técnicas. En estos alimentadores, el beneficio marginal de una fuente de generación local es máximo. Los datos de distancia eléctrica e impedancia calculada son entradas directas para este criterio.   

Topología de la Red: Se debe dar prioridad a las redes radiales, que constituyen la gran mayoría de las redes de distribución. Su estructura simple, con un único camino de alimentación, las hace más susceptibles a problemas de tensión en sus extremos y, por lo tanto, más receptivas a los beneficios de la GD. Las redes malladas, aunque más robustas, presentan flujos de potencia más complejos que requieren estudios más detallados para predecir el impacto de la GD.   

2.2.2. Ubicación Eléctrica Respecto a la Subestación
El punto de conexión a lo largo del alimentador es fundamental. La efectividad de la GD para mejorar la tensión y reducir las pérdidas aumenta a medida que se aleja eléctricamente de la subestación. Por lo tanto, se deben priorizar los clusters ubicados en los    

tramos medio y final de los alimentadores. La "regla de los 2/3" puede usarse como una guía para identificar la zona de máximo beneficio potencial para la reducción de pérdidas.   

La sinergia entre estos criterios es fundamental. Un alimentador eléctricamente débil (criterio de red) solo es un candidato ideal si sirve a una carga con un perfil de consumo diurno favorable (criterio de demanda). La metodología de priorización debe, por tanto, identificar los clusters que satisfacen simultáneamente ambas condiciones.

3. Metodología de Cuantificación de Impacto sin Datos Horarios
La ausencia de datos de demanda horaria es un desafío significativo, pero superable mediante el uso de metodologías de estimación basadas en proxies. El objetivo es construir perfiles de carga y generación sintéticos para cada cluster, permitiendo así la cuantificación de los beneficios técnicos.

3.1. Estimación de Perfiles de Carga y Generación (Proxies)
Se propone una metodología de tres pasos para generar los perfiles horarios necesarios para el análisis.

Obtención de Perfiles Base de Usuario: El primer paso consiste en recopilar perfiles de carga horarios normalizados (expresados en por unidad del pico diario de cada perfil) para arquetipos de usuarios representativos de Argentina. Las fuentes primarias para estos perfiles son los informes públicos de CAMMESA, que a menudo desglosan la demanda por tipo de usuario , y los estudios de caracterización de la demanda realizados por las propias distribuidoras (como el de EDESUR citado en la normativa del ENRE ). Se buscarán perfiles para "Residencial", "Comercial" e "Industrial" para días típicos laborables, sábados y domingos, diferenciando entre temporada de verano e invierno para capturar la estacionalidad.   

Creación del Perfil Sintético del Cluster: Para cada uno de los 2,690 transformadores, se construirá un perfil de carga horario agregado (P 
cluster
​
 (t)). Este se obtendrá ponderando los perfiles base por la composición de usuarios de cada transformador, un dato disponible en el proyecto. La fórmula para el perfil normalizado del cluster es:
$$ P_{cluster_norm}(t) = (%Res \cdot P_{base_Res}(t)) + (%Com \cdot P_{base_Com}(t)) + (%Ind \cdot P_{base_Ind}(t)) $$
Posteriormente, este perfil normalizado se escalará utilizando la capacidad nominal del transformador (S 
nom_tx
​
 ) y un factor de carga (FC) supuesto para el tipo de carga mixta, para obtener un perfil en kW:

P 
cluster
​
 (t)=P 
cluster_norm
​
 (t)⋅(S 
nom_tx
​
 ⋅FC)

Este enfoque de construcción de perfiles sintéticos a partir de datos agregados y arquetipos es una práctica estándar en la planificación de redes a gran escala cuando los datos de medición detallados no están disponibles.   

Generación del Perfil Solar: Utilizando herramientas de acceso público como PVWatts de NREL  o el Global Solar Atlas , se generará un perfil de generación solar horario (   

P 
solar
​
 (t)) para un sistema de 1 kWp de referencia, utilizando las coordenadas geográficas de la provincia de Río Negro. Este perfil base se escalará linealmente según la capacidad de GD que se esté evaluando para cada cluster.

3.2. Métricas Clave de Desempeño (KPIs) y su Cálculo Estimado
Con los perfiles sintéticos de carga y generación, es posible calcular los KPIs que medirán el impacto de la GD. La Tabla 3.1 resume estos indicadores.

Tabla 3.1: KPIs para la Evaluación de Impacto de GD Solar y Metodología de Estimación

KPI (Indicador Clave de Desempeño)	Símbolo y Unidad	Descripción del Beneficio	Fórmula de Estimación (Método Proxy)	Datos de Entrada Requeridos
Reducción de Caída de Tensión Pico	ΔV 
pico
​
  (%)	Mitiga el riesgo de disparos por subtensión y mejora el rendimiento de los equipos del cliente, abordando directamente las fallas de calidad.	ΔV 
pico
​
 ≈ 
V 
nom
​
 
R 
eq
​
 ⋅P 
GD_pico
​
 
​
 	Impedancia equivalente del alimentador (R 
eq
​
 ), Potencia pico de GD (P 
GD_pico
​
 ), Tensión nominal (V 
nom
​
 ).
Disminución de Pérdidas Técnicas Diurnas	ΔE 
loss
​
  (kWh/día)	Reduce los costos operativos para la distribuidora y mejora la eficiencia energética global del sistema.	ΔE 
loss
​
 =∑ 
t=1
24
​
 [( 
V 
nom
​
 
P 
cluster
​
 (t)
​
 ) 
2
 −( 
V 
nom
​
 
P 
cluster
​
 (t)−P 
solar
​
 (t)
​
 ) 
2
 ]⋅R 
eq
​
 ⋅1h	Perfiles P 
cluster
​
 (t) y P 
solar
​
 (t), R 
eq
​
 , V 
nom
​
 .
Mejora en Factor de Utilización del Transformador	ΔFU 
tx
​
  (%)	Reduce el estrés térmico en el transformador durante picos diurnos, potencialmente extendiendo su vida útil y posponiendo inversiones.	ΔFU 
tx
​
 = 
S 
nom_tx
​
 
max(P 
cluster
​
 (t))−max(P 
cluster
​
 (t)−P 
solar
​
 (t))
​
 	Perfiles P 
cluster
​
 (t) y P 
solar
​
 (t), Capacidad nominal del transformador (S 
nom_tx
​
 ).
Reducción de Energía No Suministrada (Proxy)	ΔH 
riesgo
​
  (horas/día)	Mejora la confiabilidad del suministro para los clientes al reducir la probabilidad de interrupciones por subtensión.	ΔH 
riesgo
​
 =H 
sin_GD
​
 −H 
con_GD
​
 , donde H es el número de horas que V(t)<V 
min
​
 .	Perfil de tensión estimado V(t), Tensión mínima admisible (V 
min
​
 ).

Exportar a Hojas de cálculo
Es crucial reconocer que esta metodología transforma un problema de "falta de datos" en un problema de "modelado y suposición". La validez del análisis depende de la calidad de los perfiles base y de las suposiciones de escalado. Por ello, se recomienda realizar un análisis de sensibilidad para evaluar cómo cambiarían los resultados ante variaciones en los perfiles de carga supuestos, lo que añade robustez al estudio.

4. Desarrollo del Índice de "Aptitud Solar sin BESS" (Scoring Multicriterio)
Para integrar los diversos factores técnicos y operativos en una única métrica de priorización, se propone el "Índice de Aptitud Solar sin BESS" (IAS). Este índice se construye mediante un modelo de scoring multicriterio, que permite una evaluación sistemática y transparente de los 2,690 transformadores.

4.1. Definición de Criterios de Puntuación Normalizados
Se definen cinco criterios fundamentales, cada uno normalizado en una escala de 0 a 10 para permitir su comparación y ponderación.

C1: Criticidad Actual del Servicio (Puntuación 0-10): Refleja la urgencia de intervención. Se basa en los datos de "modos de falla" identificados.

Puntuación alta (8-10): Clusters con fallas frecuentes documentadas por subtensión o sobrecarga térmica diurna.

Puntuación media (4-7): Clusters con problemas de calidad moderados o intermitentes.

Puntuación baja (0-3): Clusters con problemas no relacionados con la tensión (ej. fallas mecánicas) o con alta fiabilidad histórica.

C2: Perfil de Carga Favorable (Puntuación 0-10): Mide la coincidencia intrínseca entre la generación y la demanda, siendo el factor más crítico para el éxito sin almacenamiento.

Cálculo: La puntuación es una función directa del porcentaje de carga No Residencial (Comercial + Industrial) del cluster.

Score 
C2
​
 =10×(%Carga 
Comercial
​
 +%Carga 
Industrial
​
 )

C3: Vulnerabilidad de la Red (Puntuación 0-10): Evalúa qué tan "débil" es eléctricamente el punto de conexión, lo que magnifica tanto los beneficios como los riesgos.

Cálculo: Combina la distancia eléctrica (L) y la impedancia acumulada (Z) del alimentador, normalizadas a través de toda la población de transformadores.

Score 
C3
​
 =5×(L 
norm
​
 )+5×(Z 
norm
​
 )

C4: Potencial de Beneficio Técnico (Puntuación 0-10): Cuantifica el impacto positivo esperado utilizando los KPIs de la Sección 3.

Cálculo: Se basa en la reducción de caída de tensión (ΔV 
pico
​
 ) y la reducción de pérdidas (ΔE 
loss
​
 ) calculadas para una instalación de GD de tamaño estandarizado (ej. 30% de la capacidad del transformador) y normalizadas.

Score 
C4
​
 =5×(ΔV 
pico_norm
​
 )+5×(ΔE 
loss_norm
​
 )

C5: Riesgo de Impacto Negativo (Puntuación 0-10): Es un criterio de penalización que evalúa el riesgo de RPF y sobretensión.

Cálculo: Se basa en la relación entre la potencia pico solar (P 
solar_pico
​
 ) y la carga mínima diurna del cluster (P 
cluster_min_diurna
​
 ), estimada a partir de los perfiles sintéticos.

Ratio 
RPF
​
 = 
P 
cluster_min_diurna
​
 
P 
solar_pico
​
 
​
 

Score 
C5
​
 =10×max(0,1−Ratio 
RPF
​
 ). Una puntuación alta (cercana a 10) indica un bajo riesgo de RPF (el ratio es menor a 1), mientras que una puntuación de 0 indica un RPF garantizado.

4.2. Metodología de Ponderación: Proceso Analítico Jerárquico (AHP)
Para asignar pesos a cada criterio de forma objetiva y defendible, se utiliza el Proceso Analítico Jerárquico (AHP). Este método estructura el problema y deriva los pesos a partir de comparaciones por pares que reflejan la estrategia de la distribuidora. La Tabla 4.1 muestra la matriz de comparación por pares recomendada y los pesos resultantes, que priorizan la favorabilidad del perfil de carga y la mitigación de riesgos.   

Tabla 4.1: Matriz de Comparación por Pares (AHP) y Pesos de Criterios Recomendados

Criterio	C1 (Criticidad)	C2 (Perfil Carga)	C3 (Vulnerabilidad)	C4 (Beneficio)	C5 (Riesgo)	Peso (w)
C1 (Criticidad)	1	1/3	3	2	1/2	14.8%
C2 (Perfil Carga)	3	1	7	5	3	50.1%
C3 (Vulnerabilidad)	1/3	1/7	1	1/2	1/5	4.9%
C4 (Beneficio)	1/2	1/5	2	1	1/3	9.6%
C5 (Riesgo)	2	1/3	5	3	1	20.6%
Ratio de Consistencia (CR)						0.05 (< 0.1)

Exportar a Hojas de cálculo
La estrategia reflejada en estos pesos es clara: priorizar ubicaciones donde la demanda absorba naturalmente la generación (C2), minimizando activamente el riesgo de RPF (C5), para luego enfocarse en resolver los problemas de calidad más urgentes (C1).

4.3. Fórmula del Índice de Aptitud Solar (IAS)
El IAS para cada cluster j se calcula como la suma ponderada de sus puntuaciones normalizadas:

IAS 
j
​
 = 
i=1
∑
5
​
 w 
i
​
 ⋅Score 
C 
i
​
 ,j
​
 
$$ IAS_j = (0.148 \cdot Score_{C1,j}) + (0.501 \cdot Score_{C2,j}) + (0.049 \cdot Score_{C3,j}) + (0.096 \cdot Score_{C4,j}) + (0.206 \cdot Score_{C5,j}) $$

Al aplicar esta fórmula a los 2,690 transformadores, se obtiene un ranking que ordena los clusters desde el más apto hasta el menos apto para la integración de GD solar sin BESS. Este scoring no solo sirve para clasificar, sino también como herramienta de diagnóstico. Un puntaje bajo en un criterio específico (ej. C5, alto riesgo de RPF) puede indicar la necesidad de una solución diferente, como GD con almacenamiento o refuerzos de red, transformando el modelo en una herramienta de planificación estratégica integral.

5. Aplicación Práctica y Casos de Estudio
La validación de la metodología propuesta se refuerza mediante el análisis de experiencias reales y la simulación de escenarios prácticos.

5.1. Casos de Éxito: GD Solar como Solución a Problemas de Calidad
Existen numerosos casos en América Latina donde la GD ha sido implementada exitosamente para mejorar la calidad del servicio, especialmente en redes débiles o rurales.

Caso de Estudio - Red Rural con Carga Agroindustrial: En un estudio de una red de distribución en Cochabamba, Bolivia, se analizaron los impactos de la inyección fotovoltaica, demostrando su potencial para modificar los parámetros eléctricos de la red. El éxito en estos casos se fundamenta en la alta coincidencia entre la carga diurna (ej. bombeo para riego, operación de galpones de empaque, frigoríficos) y la curva de generación solar. Al dimensionar la GD para que su producción sea mayormente consumida in situ, se logra un soporte de tensión efectivo y una reducción de pérdidas sin inducir sobretensiones problemáticas.   

Caso de Estudio - Electrificación Rural: Proyectos de electrificación rural en Perú y Bolivia han utilizado sistemas fotovoltaicos para mejorar la calidad de vida y la fiabilidad del suministro en zonas aisladas. Aunque muchos son sistemas aislados, los principios de coincidencia carga-generación son los mismos. Estos proyectos demuestran que la GD solar es una solución técnica y económicamente viable para mejorar el servicio donde la red es más débil.   

5.2. Casos de Fracaso o Impacto Negativo: Lecciones Aprendidas
La implementación de GD sin una planificación adecuada puede llevar a resultados contraproducentes.

Sobretensión en Zonas Residenciales: El error más común es la instalación de alta penetración de GD solar en alimentadores con carga predominantemente residencial. Durante las horas centrales del día, la baja demanda local no puede absorber la generación, lo que resulta en un flujo inverso de potencia (RPF) que causa sobretensiones crónicas, violando los límites normativos y afectando a todos los usuarios conectados.   

Desgaste de Equipos de Regulación: La variabilidad de la generación solar puede provocar un número excesivo de operaciones en los cambiadores de tomas de los transformadores (OLTCs), como se ha observado en simulaciones con apenas un 20% de penetración de GD. Esto acelera el desgaste mecánico y aumenta los costos de mantenimiento.   

Impacto en Transformadores por RPF: Estudios técnicos detallados, incluyendo los del IEEE, han demostrado que el RPF altera los patrones de flujo magnético de dispersión en los transformadores, pudiendo causar sobrecalentamiento en partes metálicas estructurales y en los devanados, lo que no fue considerado en su diseño original. Esto lleva a una degradación acelerada del aislamiento y a una reducción significativa de la vida útil del activo.   

La lección fundamental de estos casos es que los problemas no surgen de la GD en sí, sino de un desajuste entre la tecnología y el sistema receptor. Una planificación que solo considera la carga máxima o promedio, ignorando las condiciones de carga mínima diurna, está destinada a encontrar problemas de RPF. Esto valida la necesidad de utilizar perfiles horarios completos (incluso si son sintéticos) en el análisis.

5.3. Simulación de Aplicación del Índice de Aptitud Solar (IAS)
Para ilustrar la metodología, se evalúan dos clusters hipotéticos con los pesos derivados en la Sección 4.

Cluster A (Candidato Ideal):

Características: Alimentador largo (L_norm=0.9), alta impedancia (Z_norm=0.8), fallas de subtensión reportadas (Score_C1=9). Carga 80% industrial, 20% residencial (Score_C2=8). Riesgo de RPF bajo (Ratio_RPF=0.4, Score_C5=6). Potencial de beneficio técnico alto (ΔV_norm=0.9, ΔE_norm=0.8).

Cálculo de Scores:

Score 
C1
​
 =9.0

Score 
C2
​
 =10×(0.80)=8.0

Score 
C3
​
 =5×0.9+5×0.8=8.5

Score 
C4
​
 =5×0.9+5×0.8=8.5

Score 
C5
​
 =10×(1−0.4)=6.0

IAS Final:

IAS 
A
​
 =(0.148⋅9.0)+(0.501⋅8.0)+(0.049⋅8.5)+(0.096⋅8.5)+(0.206⋅6.0)=1.33+4.01+0.42+0.82+1.24=7.82

Cluster B (Candidato Pobre):

Características: Alimentador corto (L_norm=0.2), baja impedancia (Z_norm=0.1), sin fallas de tensión (Score_C1=1). Carga 10% comercial, 90% residencial (Score_C2=1). Riesgo de RPF muy alto (Ratio_RPF=2.5, Score_C5=0). Potencial de beneficio técnico bajo (ΔV_norm=0.2, ΔE_norm=0.1).

Cálculo de Scores:

Score 
C1
​
 =1.0

Score 
C2
​
 =10×(0.10)=1.0

Score 
C3
​
 =5×0.2+5×0.1=1.5

Score 
C4
​
 =5×0.2+5×0.1=1.5

Score 
C5
​
 =10×max(0,1−2.5)=0.0

IAS Final:

IAS 
B
​
 =(0.148⋅1.0)+(0.501⋅1.0)+(0.049⋅1.5)+(0.096⋅1.5)+(0.206⋅0.0)=0.15+0.50+0.07+0.14+0.0=0.86

La simulación demuestra cómo el IAS integra los diferentes factores para distinguir claramente entre un candidato excelente (IAS = 7.82) y uno pobre (IAS = 0.86), validando la capacidad del modelo para guiar las decisiones de inversión.

6. Consideraciones Específicas para Argentina y la Provincia de Río Negro
La aplicación exitosa de la metodología requiere su adaptación al contexto regulatorio, geográfico y económico específico de Argentina, y en particular, de la provincia de Río Negro.

6.1. Caracterización del Recurso Solar y Demanda Local en Río Negro
Recurso Solar: La provincia de Río Negro posee un recurso solar de alta calidad. Datos del Global Solar Atlas indican valores de Irradiación Global Horizontal (GHI) que pueden superar los 5.0 kWh/m²/día en promedio anual, y valores de Irradiación Directa Normal (DNI) también significativos, especialmente en la zona norte y este de la provincia (departamentos de General Roca, El Cuy, Avellaneda). Por ejemplo, en la zona de General Roca, el GHI anual promedio es de aproximadamente 1800-1900 kWh/m² y el DNI es de 1600-1700 kWh/m², valores excelentes para la generación fotovoltaica.   

Perfiles de Consumo y Factor de Coincidencia: La estructura productiva de Río Negro presenta una oportunidad estratégica. Además del consumo residencial con picos nocturnos , la provincia tiene una fuerte actividad agroindustrial ligada a la fruticultura (galpones de empaque, cámaras frigoríficas). Esta actividad tiene una demanda eléctrica intensiva y marcadamente diurna, con una estacionalidad que coincide con los meses de mayor irradiación solar (verano y otoño). Esto crea un    

alto factor de coincidencia natural entre la generación solar y la demanda en los clusters que sirven a estas industrias. Mientras un cluster residencial podría tener un factor de coincidencia del 20-30%, un cluster agroindustrial podría superar el 70-80%, lo que reduce drásticamente el riesgo de RPF y maximiza los beneficios locales.

6.2. Marco Regulatorio y sus Implicaciones Técnicas
La integración de GD en Argentina está regida por un marco normativo a nivel nacional y provincial.

Ley Nacional 27.424 y su Reglamentación (Decreto 986/2018): Esta ley establece el "Régimen de Fomento a la Generación Distribuida". Sus puntos técnicos clave son:   

Figura del Usuario-Generador: Permite a cualquier cliente de la red generar energía para su autoconsumo e inyectar los excedentes.   

Esquema de Facturación: Adopta un modelo de "Balance Neto de Facturación". La energía inyectada a la red se valora a un precio mayorista y se acredita en la factura del usuario. Este incentivo económico a la inyección hace que la gestión técnica del RPF por parte de la distribuidora sea aún más crítica.   

Proceso de Conexión: Requiere una solicitud de conexión al distribuidor, quien debe realizar un estudio de viabilidad técnica para asegurar que la instalación no afecte negativamente la red. Se establecen requisitos para los equipos de interconexión (inversores certificados) para garantizar la seguridad y calidad del servicio.   

Límites de Potencia: La ley nacional establece un marco, pero las jurisdicciones pueden definir límites específicos. La potencia máxima del inversor conectada a una fase suele estar limitada (ej. 5 kW), y la potencia total para usuarios residenciales puede tener un tope (ej. 10 kW).   

Regulación Provincial (Ley 5.617 y rol del EPRE): Río Negro ha adherido a la ley nacional y cuenta con su propia reglamentación, lo que ha impulsado el crecimiento de la GD en la provincia. El Ente Provincial Regulador de la Electricidad (EPRE) de Río Negro es la autoridad de fiscalización en la jurisdicción, responsable de resolver controversias y asegurar el cumplimiento de la normativa por parte de las distribuidoras. La distribuidora debe usar análisis técnicos, como el propuesto en este informe, para justificar sus decisiones de conexión ante el EPRE.   

6.3. Conclusiones y Recomendaciones Finales
La priorización de emplazamientos para GD solar sin almacenamiento en redes con problemas de calidad es un desafío técnico complejo pero abordable. La metodología propuesta en este informe, basada en la creación de un Índice de Aptitud Solar (IAS), ofrece una herramienta robusta y transparente para guiar las decisiones de inversión de la distribuidora.

Se concluye que el éxito de la GD solar sin BESS depende críticamente de la sincronización entre la generación y la demanda local. Por lo tanto, los criterios relacionados con el perfil de los usuarios y el riesgo de flujo inverso de potencia deben tener la máxima ponderación en cualquier modelo de priorización.

Las recomendaciones clave para la implementación son:

Adoptar el Índice de Aptitud Solar (IAS): Utilizar el IAS y la metodología de scoring multicriterio descrita para clasificar los 2,690 transformadores. Esto permitirá enfocar las inversiones iniciales en los clusters de "alta aptitud", donde el retorno técnico y la mejora de la calidad del servicio serán máximos con el mínimo riesgo.

Priorizar Clusters Agroindustriales: Dada la estructura productiva de Río Negro, se debe buscar activamente la implementación de GD en clusters que atienden a la industria frutícola y otras cargas diurnas. Esto representa una ventaja estratégica para la provincia.

Implementación Piloto y Monitoreo: Iniciar con un número manejable de proyectos piloto en los clusters mejor calificados. Es fundamental instalar equipos de medición horaria en estos pilotos para recopilar datos reales de carga y generación. Estos datos permitirán validar y refinar los perfiles sintéticos y la metodología de scoring para futuras fases de expansión.

Utilizar el Scoring como Herramienta de Planificación Estratégica: El IAS no solo debe usarse para ranking. El análisis de los componentes del score para cada cluster (ej. un score bajo en C5 indica alto riesgo de RPF) debe usarse para planificar a largo plazo. Los clusters con alto riesgo de RPF pero con otros atributos positivos son candidatos ideales para futuras inversiones en almacenamiento (BESS) o refuerzos de red.

Diálogo Técnico con el Regulador: Utilizar este marco de análisis técnico como base para el diálogo con el EPRE de Río Negro, justificando las decisiones de conexión, las solicitudes de adecuación de proyectos o la necesidad de inversiones complementarias en la red.

Al seguir este enfoque estructurado, la empresa distribuidora puede transformar la GD solar de un potencial problema técnico a una solución costo-efectiva para mejorar la calidad y la fiabilidad del servicio eléctrico en sus redes de distribución.


Fuentes usadas en el informe

nrel.gov
IEEE 1547-2018 Standard Guidance | Grid Modernization - NREL
Se abre en una ventana nueva

researchgate.net
Impact DG on voltage regulation - ResearchGate
Se abre en una ventana nueva

standards.ieee.org
P1547 - IEEE SA
Se abre en una ventana nueva

reddit.com
Does distributed generation (e.g. rooftop solar) on a power grid reduce transmission demand? : r/askscience - Reddit
Se abre en una ventana nueva

knowledgecenter.ubt-uni.net
Technical Impacts of Distributed Generation in Distribution Network, Voltage Drops - UBT Knowledge Center
Se abre en una ventana nueva

standards.ieee.org
IEEE 1547-2003 - IEEE SA
Se abre en una ventana nueva

pscp.engr.tamu.edu
Technical and Economic Impact of PV-BESS Charging Station on Transformer Life: A Case Study - Power System Control & Protection Lab
Se abre en una ventana nueva

mdpi.com
Voltage Regulation Strategies in Photovoltaic-Energy Storage System Distribution Network: A Review - MDPI
Se abre en una ventana nueva

docs.nrel.gov
IEEE 1547 National Standard for Interconnecting Distributed Generation - Publications
Se abre en una ventana nueva

apqi.org
Impact of Distributed Generation (especially in solar photovoltaic industry) on PQ | Blog
Se abre en una ventana nueva

icrepq.com
Impact of Distributed Generation and Energy Storage on Power Quality
Se abre en una ventana nueva

docs.nrel.gov
Grid-Integrated Distributed Solar: Addressing Challenges for Operations and Planning - Publications
Se abre en una ventana nueva

fglongatt.org
Impact of Distributed Generation over Power Losses on Distribution System - Fglongatt.org
Se abre en una ventana nueva

mdpi.com
Efficient Modeling of Distributed Energy Resources' Impact on Electric Grid Technical Losses: A Dynamic Regression Approach - MDPI
Se abre en una ventana nueva

camus.energy
4 Ways Utilities Can Tackle Distributed Solar Challenges - Camus Energy
Se abre en una ventana nueva

researchgate.net
Impact of Reverse Power Flow on Distributed Transformers in a Solar-Photovoltaic-Integrated Low-Voltage Network - ResearchGate
Se abre en una ventana nueva

www1.eere.energy.gov
Distributed Photovoltaic Systems Design and Technology Requirements
Se abre en una ventana nueva

researchgate.net
(PDF) Impact on Voltage Regulation in Medium Voltage Distribution ...
Se abre en una ventana nueva

en.wikipedia.org
IEEE 1547 - Wikipedia
Se abre en una ventana nueva

researchgate.net
(PDF) Distributed generation impact on power system case study ...
Se abre en una ventana nueva

ripublication.com
Characterization of Voltage Rise Issue due to Distributed Solar PV Penetration - Research India Publications
Se abre en una ventana nueva

mdpi.com
Solar PV Grid Power Flow Analysis - MDPI
Se abre en una ventana nueva

clouglobal.com
Handling Transformer Load Stress as Renewable Energy Sources Grow - clou global
Se abre en una ventana nueva

azadproject.ir
Impact of Distributed Generation on Voltage Profile and Losses of Distribution Systems
Se abre en una ventana nueva

mdpi.com
Impact of Reverse Power Flow on Distributed Transformers in a Solar-Photovoltaic-Integrated Low-Voltage Network - MDPI
Se abre en una ventana nueva

energycentral.com
Distributed Energy Resources (DERs): Impact of Reverse Power Flow on Transformer
Se abre en una ventana nueva

eeeic.org
Distributed Generation and Power Quality - EEEIC International
Se abre en una ventana nueva

tandfonline.com
Full article: The influences of including solar photovoltaic system on ...
Se abre en una ventana nueva

researchgate.net
(PDF) Analysis on Voltage Profile of Distribution Network with ...
Se abre en una ventana nueva

eurasiareview.com
Electricity Demand During Lockdown: Evidence From Argentina – Analysis - Eurasia Review
Se abre en una ventana nueva

cigrecolombia.org
Full Papers PS1 - Experience and New Requirements for Transformers for Renewable Generation - CIGRE Colombia
Se abre en una ventana nueva

grouper.ieee.org
Reverse Power Flow Impact on Transformers - of IEEE Standards Working Groups
Se abre en una ventana nueva

climate-laws.org
Law 27.424 instituting the regime to promote the distributed generation of renewable energy integrated into the public electricity network
Se abre en una ventana nueva

climate-laws.org
Law no 27424 creating the Promotion Regime for Distributed Generation of Renewable Energy Integrated in the Public Electricity Grid
Se abre en una ventana nueva

climatepolicydatabase.org
Law Nr 27,424 on the Promotion Regime for Distributed Generation of Renewable Energy Integrated in the Public Electricity Grid | Climate Policy Database
Se abre en una ventana nueva

trsym.com
Renewable Energy: Regulation of Distributed Generation Law No. 27424 - TRSyM
Se abre en una ventana nueva

rionegro.gov.ar
STUDY ON THE PRODUCTION OF GREEN HYDROGEN IN THE RIO NEGRO PROVINCE Report
Se abre en una ventana nueva

mdpi.com
A Multi-Criteria AHP Framework for Solar PV End-of-Life Management - MDPI
Se abre en una ventana nueva

pvwatts.nrel.gov
Solar Resource Data - PVWatts Calculator - NREL
Se abre en una ventana nueva

rise.esmap.org
Informe Anual 2020 | RISE
Se abre en una ventana nueva

catedras.facet.unt.edu.ar
Curvas de Carga y Generación - sitios de cátedras facet
Se abre en una ventana nueva

tecnicasmm.com.ar
Perfil de carga - TecnicasMM
Se abre en una ventana nueva

enre.gov.ar
EDESUR SA - Estudio de caracterización de la carga Informe Final - Versión Preliminar Marzo 2021
Se abre en una ventana nueva

researchgate.net
3: Typical load curves used for residential, commercial and industrial ...
Se abre en una ventana nueva

globalsolaratlas.info
Global Solar Atlas
Se abre en una ventana nueva

boletinoficial.gob.ar
ENTE NACIONAL REGULADOR DE LA ELECTRICIDAD - Resolución 303/2025 - BOLETIN OFICIAL REPUBLICA ARGENTINA
Se abre en una ventana nueva

pmi.org
Prioritizing project risks using AHP - Project Management Institute
Se abre en una ventana nueva

research.chalmers.se
Generating low-voltage grid proxies in order to estimate grid capacity for residential end-use technologies - Chalmers Research
Se abre en una ventana nueva

researchgate.net
(PDF) Generating low-voltage grid proxies in order to estimate grid capacity for residential end-use technologies: The case of residential solar PV - ResearchGate
Se abre en una ventana nueva

saij.gob.ar
Reglamentación de la Ley 27.424 sobre Régimen de Fomento a la Generación Distribuída de Energía Renovable Integrada a la Red Eléctrica Pública - SAIJ
Se abre en una ventana nueva

portalsolar.com.ar
Inyección de energía a la red – Ley N° 27.424 - Portal Solar
Se abre en una ventana nueva

scielo.org.bo
CASO DE ESTUDIO: IMPACTO DE LA GENERACIÓN DISTRIBUIDA EN REDES ELÉCTRICAS DE DISTRIBUCIÓN - SciELO Bolivia
Se abre en una ventana nueva

researchgate.net
(PDF) CASO DE ESTUDIO: IMPACTO DE LA GENERACIÓN DISTRIBUIDA EN REDES ELÉCTRICAS DE DISTRIBUCIÓN - ResearchGate
Se abre en una ventana nueva

core.ac.uk
An Analytic Hierarchy Process Based Approach for Evaluating Renewable Energy Sources - CORE
Se abre en una ventana nueva

dspace.ups.edu.ec
Clasificación de perfiles de carga en consumidores comerciales mediante análisis de conglomerados
Se abre en una ventana nueva

rionegro.gov.ar
El EPRE atenderá reclamos y consultas sobre el servicio eléctrico en la zona de Campo Grande | Gobierno de Río Negro
Se abre en una ventana nueva

rionegro.gov.ar
El EPRE atenderá reclamos y consultas sobre el servicio eléctrico en San Antonio Oeste
Se abre en una ventana nueva

rionegro.gov.ar
Río Negro superó los 100 usuarios generadores de energía renovable
Se abre en una ventana nueva

rionegro.gov.ar
El sol en Río Negro es una oportunidad como fuente energética
Se abre en una ventana nueva

rid.unrn.edu.ar
Mapas recursos eólico y solar provincia de Río Negro - RID-UNRN
Se abre en una ventana nueva

patagoniambiental.com.ar
Río Negro alcanza los 100 generadores solares y lidera en energía limpia
Se abre en una ventana nueva

infoenergia.info
Río Negro alcanza un hito en autogeneración con energías renovables - InfoEnergía
Se abre en una ventana nueva

revistas.untrm.edu.pe
Meta Análisis de los Sistemas Fotovoltaicos en Viviendas Rurales. Casos: Perú y Bolivia
Se abre en una ventana nueva

editorialinnova.com
Modelo de optimización no lineal para estimación de perfiles de carga en sistemas eléctricos de distribución Nonlinear optim - EDITORIAL INNOVA
Se abre en una ventana nueva

cdi.mecon.gob.ar
INFORME técnico
Se abre en una ventana nueva

cammesaweb.cammesa.com
Informes y estadisticas | CAMMESA
Se abre en una ventana nueva

Fuentes consultadas, pero no usadas en el informe
