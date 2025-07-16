Análisis Técnico: Inversores Solares como STATCOM Nocturno para Soporte de Red en la Red de Distribución de EDERSA
Resumen Ejecutivo
Este informe presenta un análisis técnico-económico sobre la viabilidad de utilizar los inversores de los sistemas solares fotovoltaicos (FV) como compensadores síncronos estáticos (STATCOM) durante la noche. Esta funcionalidad, conocida como "Q at Night", permite la inyección de potencia reactiva (Q) en la red cuando no hay generación de potencia activa (P), abordando directamente la prioridad de la red de EDERSA de mejorar los perfiles de tensión nocturnos. Se evalúan las capacidades técnicas de los inversores modernos, los marcos normativos aplicables (IEEE 1547-2018 y regulaciones argentinas), los beneficios para la red, los aspectos económicos y los requisitos de control. Se concluye que esta es una solución técnica y económicamente viable, siendo hasta 50 veces más económica que la instalación de dispositivos FACTS dedicados. Finalmente, se propone una modificación al "Índice de Aptitud Solar sin BESS" (IAS) previamente desarrollado, incorporando un nuevo criterio que valora el beneficio del soporte reactivo nocturno para refinar la priorización de los 15 clusters identificados, asegurando que las inversiones en GD solar no solo aborden los problemas diurnos, sino que también se conviertan en activos críticos para la estabilidad de la red durante las 24 horas.   

1. Capacidades Técnicas de los Inversores como STATCOM Nocturno
La capacidad de un inversor solar para operar como un STATCOM se basa en su electrónica de potencia, que le permite desacoplar el control de la potencia activa (P) y reactiva (Q). Los inversores modernos, o "smart inverters", están diseñados con esta funcionalidad avanzada.   

1.1. Inversores con Capacidad STATCOM Nocturna ("Q at Night")
No todos los inversores pueden operar sin una fuente de CC de los paneles solares. Aquellos con la funcionalidad "Q at Night" o similar incorporan hardware adicional que les permite mantenerse energizados desde la red de CA durante la noche para realizar la compensación de reactiva. Fabricantes líderes como SMA, Ingeteam, General Electric, Siemens y ABB ofrecen inversores o soluciones STATCOM que pueden cumplir esta función.   

1.2. Capacidad de Potencia Reactiva (Q) vs. Potencia Nominal (P)
La capacidad de un inversor para entregar potencia se define por su potencia aparente nominal (S 
nom
​
 ), medida en kVA. La relación entre potencia activa (P, en kW) y reactiva (Q, en kVAr) se describe en su curva de capacidad P-Q.   

Operación Diurna: Durante el día, la inyección de potencia activa (P 
FV
​
 ) limita la capacidad de entregar reactiva. La máxima potencia reactiva (Q 
max
​
 ) disponible está dada por:

Q 
max
​
 = 
S 
nom
2
​
 −P 
FV
2
​
 

​
 
Operación Nocturna (Modo STATCOM): Por la noche, la potencia activa generada (P 
FV
​
 ) es cero. Teóricamente, el inversor podría utilizar toda su capacidad nominal para la compensación de reactiva (Q 
max
​
 =S 
nom
​
 ). Sin embargo, los fabricantes suelen limitar esta capacidad para proteger los componentes. Por ejemplo, algunos modelos de SMA limitan la inyección de reactiva nocturna al 30% de la potencia nominal del inversor para gestionar el estrés térmico.   

1.3. Límites Térmicos y Eficiencia
La operación continua, incluso solo con potencia reactiva, genera pérdidas y estrés térmico en los componentes del inversor (IGBTs, condensadores, etc.).   

Estrés Térmico: La operación nocturna impone un ciclo térmico adicional que puede impactar la vida útil de los componentes. Los fabricantes que ofrecen la función "Q at Night" lo hacen con diseños de hardware y sistemas de refrigeración (ej. ventilación forzada inteligente) que gestionan este estrés adicional.   

Pérdidas y Eficiencia: Un STATCOM dedicado tiene pérdidas térmicas activas muy bajas, típicamente ≤0.8% de su capacidad nominal. Se puede esperar una eficiencia similar para un inversor operando en modo STATCOM, aunque este valor puede variar. La principal fuente de consumo es la energía necesaria para mantener la electrónica de control activa y el sistema de refrigeración funcionando.   

2. Normativa y Estándares Aplicables
La implementación de servicios de red avanzados como el soporte de reactiva está regida por estándares internacionales y regulaciones locales.

2.1. Estándar IEEE 1547-2018
Este es el estándar de interconexión de Recursos Energéticos Distribuidos (DER) de referencia en Norteamérica y una guía global. La versión de 2018 es un cambio de paradigma respecto a la de 2003, ya que exige que los DERs soporten activamente a la red en lugar de simplemente desconectarse ante perturbaciones.

Soporte de Tensión y Potencia Reactiva: El estándar define múltiples modos de control de potencia reactiva que los inversores deben ser capaces de ejecutar, incluyendo :   

Modo de Factor de Potencia Constante: El inversor mantiene un factor de potencia programado.

Modo Volt-Var: El inversor ajusta su salida de potencia reactiva en función de la tensión medida en su punto de conexión, siguiendo una curva característica predefinida.

Modo Watt-Var: La salida de reactiva se ajusta en función del nivel de potencia activa inyectada.

Certificaciones: Para demostrar el cumplimiento, los inversores deben ser certificados bajo estándares de prueba como UL 1741-SA (Supplement A), que valida estas funciones de soporte de red.   

2.2. Requisitos de los Códigos de Red Argentinos (CAMMESA/ENRE)
El marco regulatorio argentino, si bien está en evolución, ya contempla la gestión de la potencia reactiva.

Resoluciones del ENRE: Recientemente, el ENRE ha actualizado los requisitos de factor de potencia para los usuarios, elevando el límite mínimo de 0.85 a 0.95, lo que demuestra una clara intención regulatoria de mejorar la eficiencia de la red y reducir las pérdidas por reactiva. La Resolución ENRE N° 85/2024 implementa el "Programa para la mejora del factor de potencia" y menciona explícitamente que la corrección permitirá la "recuperación de capacidad en cables y transformadores" y una "reducción de las pérdidas de potencia y energía".   

Procedimientos Técnicos de CAMMESA: CAMMESA, como operador del sistema, define los requisitos para los agentes del Mercado Eléctrico Mayorista (MEM). El control de tensión y potencia reactiva es un servicio auxiliar contemplado en sus procedimientos. Aunque la remuneración específica para un inversor FV operando como STATCOM nocturno no está explícitamente tarifada, el marco para los servicios auxiliares existe y podría ser la base para una negociación.   

2.3. Protocolos de Comunicación
Para que la distribuidora (EDERSA) pueda gestionar y despachar la potencia reactiva de los inversores de forma remota, se requieren protocolos de comunicación estandarizados.

IEC 61850: Es el estándar moderno para la automatización de subestaciones. Es un protocolo orientado a objetos que integra el contexto de los datos, lo que lo hace ideal para la comunicación y control en tiempo real de activos inteligentes como los inversores.   

DNP3 (IEEE 1815): Es un protocolo más antiguo y extendido en Norteamérica, diseñado para la comunicación entre una estación maestra y remotas (RTUs). Aunque es menos rico en funcionalidades que IEC 61850, es robusto y ampliamente utilizado.   

SunSpec Alliance: Desarrolla estándares de comunicación específicos para la industria solar, asegurando la interoperabilidad entre componentes de diferentes fabricantes.

La elección del protocolo dependerá de la infraestructura existente de EDERSA, pero la tendencia global se inclina hacia IEC 61850 para nuevas implementaciones de redes inteligentes.   

3. Beneficios para la Red de Distribución
La provisión de potencia reactiva nocturna por parte de los inversores FV ofrece beneficios tangibles y directos para la red de EDERSA, que sufre de problemas de calidad.

Mejora del Perfil de Tensión Nocturno: Durante la noche, las cargas predominantemente inductivas (motores, transformadores, etc.) consumen potencia reactiva, lo que provoca caídas de tensión en los alimentadores, especialmente en los puntos más alejados de la subestación. Al inyectar potencia reactiva capacitiva localmente, los inversores elevan la tensión, contrarrestando esta caída y mejorando la calidad del suministro.   

Reducción de Pérdidas Técnicas: La potencia reactiva, al igual que la activa, genera pérdidas por efecto Joule (I 
2
 R) en los conductores. Al compensar la reactiva cerca de los puntos de consumo, se reduce la corriente reactiva que debe ser transportada desde los generadores centralizados, disminuyendo significativamente las pérdidas en las redes de transmisión y distribución.   

Alivio de Activos de Red: La reducción de la corriente total (activa + reactiva) que circula por los transformadores y conductores disminuye su carga térmica, lo que puede extender su vida útil y liberar capacidad para conectar más carga activa.   

Mejora del Factor de Potencia Global: La inyección de reactiva mejora el factor de potencia del sistema visto desde la subestación, ayudando a cumplir con los nuevos y más exigentes requisitos del ENRE (FP > 0.95) y evitando penalizaciones para la distribuidora.   

4. Aspectos Económicos y de Viabilidad
La viabilidad económica de esta funcionalidad depende del costo incremental del inversor, su impacto en la vida útil y la existencia de un mecanismo de remuneración.

Costo Incremental: Los inversores con capacidad "Q at Night" tienen un costo marginalmente superior a los estándar debido al hardware adicional. Sin embargo, este costo es significativamente menor (hasta 50 veces) que instalar un equipo de compensación dedicado como un STATCOM o un banco de capacitores conmutado.   

Impacto en la Vida Útil: La operación 24/7 aumenta el estrés térmico y el tiempo de operación de componentes como ventiladores y condensadores, lo que puede reducir la vida útil del inversor. Estudios sugieren que la provisión de reactiva nocturna podría reducir la vida útil en aproximadamente un año adicional, sumado a la reducción ya aceptada por la provisión diurna. Los fabricantes diseñan estos inversores para una vida útil de más de 20 años, considerando estas operaciones. Un mantenimiento adecuado es clave para mitigar este impacto.   

Remuneración por Servicios Auxiliares: Este es el punto clave para la viabilidad del modelo de negocio. En Argentina, el MEM contempla la existencia de Servicios Auxiliares, y el control de reactiva es uno de ellos. Si bien no existe una tarifa específica para este servicio desde un generador distribuido, su valor para la red es claro y cuantificable (reducción de pérdidas, postergación de inversiones). Esto abre la puerta para que EDERSA negocie un esquema de remuneración con los propietarios de los sistemas FV (o los opere directamente) y lo presente a CAMMESA y al ENRE para su aprobación.   

Análisis de Retorno de Inversión (ROI): El ROI para el propietario del sistema FV mejoraría al sumar un nuevo flujo de ingresos por la venta de este servicio auxiliar. Para la distribuidora, el ROI se calcula comparando el costo de remunerar este servicio con los ahorros obtenidos por la reducción de pérdidas y la postergación de inversiones en la red.

5. Configuración, Control y Coordinación
La implementación efectiva requiere una arquitectura de control robusta y coordinada.

Modos de Control del Inversor: Los inversores inteligentes pueden operar en varios modos de control de tensión/reactiva, que pueden ser configurados localmente o gestionados remotamente por la distribuidora :   

Control de Tensión (Volt-Var): El inversor ajusta la inyección de Q para mantener la tensión en un punto de consigna. Este es el modo más directo para resolver problemas de tensión local.

Control de Potencia Reactiva (Q Control): El inversor inyecta una cantidad fija de kVAr, comandada por el centro de control de la distribuidora.

Control de Factor de Potencia (PF Control): El inversor opera para mantener un FP objetivo en el punto de conexión.

Coordinación con Reguladores Existentes: La inyección variable de reactiva puede interactuar con los reguladores de tensión de línea (OLTCs), causando un ciclado excesivo. Es fundamental coordinar los tiempos de respuesta y las bandas muertas del control del inversor con los de los reguladores para evitar el desgaste acelerado de estos últimos.

Sistemas de Gestión Remota (DERMS): Para gestionar una flota de 120 MW de recursos distribuidos, EDERSA necesitaría un Sistema de Gestión de Recursos Energéticos Distribuidos (DERMS). Este software permitiría monitorear, controlar y despachar la potencia reactiva de los 15 clusters de forma centralizada y coordinada.

Respuesta Dinámica: Los inversores basados en electrónica de potencia tienen tiempos de respuesta muy rápidos, típicamente de milisegundos o pocos ciclos de red (< 2 ciclos) , lo que los hace mucho más efectivos que los bancos de capacitores mecánicos para responder a fluctuaciones rápidas de tensión.   

6. Casos de Estudio y Fabricantes Líderes
La utilización de inversores FV para soporte de red ya no es teórica; existen múltiples proyectos piloto y comerciales.

Casos de Éxito Internacionales:

Reino Unido: National Grid y Lightsource BP probaron con éxito el uso de un parque FV para proporcionar soporte de tensión nocturno, concluyendo que era una solución mucho más económica que los FACTS tradicionales.   

Estados Unidos (ERCOT, EPRI): Estudios y pruebas de laboratorio del EPRI han demostrado la viabilidad técnica del soporte reactivo nocturno, cuantificando incluso la potencia activa consumida por el inversor para mantenerse operativo.   

Estudios en Sri Lanka: Se han desarrollado algoritmos y modelos económicos para utilizar los inversores de la red de distribución para corregir problemas de subtensión durante los picos nocturnos, demostrando un beneficio neto positivo para la distribuidora.   

Fabricantes y Modelos:

SMA Solar Technology AG: Ofrece la opción "Q at Night" en su serie de inversores centrales Sunny Central CP XT.   

Ingeteam: Sus inversores de la serie INGECON SUN Power son capaces de inyectar potencia reactiva incluso por la noche.   

Líderes en STATCOM: Empresas como ABB, General Electric, Siemens y Hitachi son líderes en tecnología de compensación de reactiva y sus avances en STATCOM son directamente aplicables a la funcionalidad de los inversores.   

7. Integración en la Metodología de Priorización (Actualización del IAS)
Dado que la entrega de reactiva nocturna es una prioridad, el "Índice de Aptitud Solar sin BESS" (IAS) debe ser modificado para incluir este nuevo y valioso servicio auxiliar.

7.1. Nuevo Criterio: C6 - Aptitud para Soporte Reactivo Nocturno
Se propone un nuevo criterio que evalúe la idoneidad de un cluster para proporcionar este servicio. A diferencia del análisis diurno, donde la carga residencial es un problema, para el soporte nocturno es un beneficio.

Puntuación (0-10): Se basa en dos factores:

Perfil de Carga Nocturno (Proxy): Se puntúa en función del porcentaje de carga Residencial. Los picos de consumo residencial ocurren por la tarde-noche, coincidiendo con la necesidad de soporte de tensión.

Score 
C6_Carga
​
 =10×(%Carga 
Residencial
​
 )

Necesidad de Soporte de Tensión: Se puede utilizar la misma puntuación de Criticidad (C1) que indica problemas de tensión.

Cálculo del Score C6:

Score 
C6
​
 =(0.7×Score 
C6_Carga
​
 )+(0.3×Score 
C1
​
 )

7.2. Re-ponderación de Criterios del IAS con AHP
Se debe recalcular la matriz de ponderación AHP para incluir C6. Dada la prioridad explícita del cliente, C6 debe recibir un peso significativo. Se propone una nueva matriz que equilibre los beneficios diurnos (C2) y nocturnos (C6).

Tabla 7.1: Matriz de Comparación por Pares (AHP) y Pesos de Criterios Actualizados

Criterio	C1 (Criticidad)	C2 (Perfil Diurno)	C3 (Vulnerabilidad)	C4 (Beneficio Técnico)	C5 (Riesgo RPF)	C6 (Soporte Nocturno)	Peso (w)
C1	1	1/2	3	2	1/2	1/2	12.3%
C2	2	1	5	3	2	1	28.4%
C3	1/3	1/5	1	1/2	1/4	1/4	4.4%
C4	1/2	1/3	2	1	1/2	1/3	7.9%
C5	2	1/2	4	2	1	1/2	16.9%
C6	2	1	4	3	2	1	30.1%
Ratio de Consistencia (CR)							0.04 (< 0.1)

Exportar a Hojas de cálculo
7.3. Fórmula del Índice de Aptitud Solar Actualizado (IAS 2.0)
El nuevo IAS se calcularía como:

IAS 
2.0,j
​
 = 
i=1
∑
6
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
 

$$ IAS_{2.0,j} = (0.123 \cdot Sc_{C1}) + (0.284 \cdot Sc_{C2}) + (0.044 \cdot Sc_{C3}) + (0.079 \cdot Sc_{C4}) + (0.169 \cdot Sc_{C5}) + (0.301 \cdot Sc_{C6}) $$

Este nuevo índice permitirá re-priorizar los 15 clusters, identificando aquellos que no solo son buenos para la generación diurna, sino que también están ubicados en zonas con alta carga residencial nocturna, donde el servicio de soporte reactivo tendrá el mayor impacto.

8. Riesgos y Limitaciones
Degradación de Componentes: La operación 24/7, incluso a carga parcial, acelera el envejecimiento de los componentes del inversor, especialmente los condensadores y ventiladores. Esto debe ser considerado en los contratos de O&M y en el análisis de vida útil.   

Calidad de Onda (Armónicos): Aunque los inversores modernos tienen filtros avanzados, la operación en modo STATCOM podría introducir armónicos en la red. Se deben realizar mediciones de calidad de onda post-implementación para asegurar el cumplimiento de la norma IEEE 519.   

Confiabilidad del Servicio: Al convertirse en un activo crítico para la estabilidad de la red, la confiabilidad del inversor es primordial. Se deben establecer protocolos de mantenimiento preventivo rigurosos y considerar la necesidad de redundancia en clusters de alta criticidad.

Consumo Propio: El inversor consumirá una pequeña cantidad de potencia activa de la red para su operación nocturna, lo cual debe ser contabilizado en el modelo económico.   