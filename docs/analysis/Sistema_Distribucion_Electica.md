
Un Marco Integral para el Análisis y la Predicción del Rendimiento en Sistemas de Distribución Eléctrica con Datos Limitados


Parte I: Principios Fundamentales de las Redes de Distribución

Esta primera parte establece los principios de ingeniería esenciales que gobiernan el comportamiento de los sistemas de distribución. La comprensión de estos fundamentos es un prerrequisito para cualquier análisis de datos o modelado predictivo significativo. Se cubrirán los componentes físicos, las estructuras de red y la física del flujo de potencia y la regulación de tensión.

Sección 1: Anatomía de un Alimentador de Distribución de Media Tensión

Esta sección deconstruye un alimentador de distribución, explicando su composición física y sus configuraciones topológicas. Este conocimiento es crucial para construir un modelo mental y, posteriormente, computacional de la red a partir de los datos limitados disponibles.

1.1 Estructura Física: Desde la Subestación hasta la Carga

Un alimentador de media tensión (MT) es el sistema arterial que transporta la energía eléctrica desde una subestación de distribución hasta los transformadores locales que alimentan a los consumidores finales.1 Estos circuitos operan a tensiones nominales estandarizadas, como 13.2 kV, 22.86 kV o 33 kV, para minimizar las pérdidas durante el transporte de energía a lo largo de distancias considerables.3 La estructura física de un alimentador es un sistema complejo de componentes diseñados para funcionar de manera coordinada, garantizando la seguridad y la fiabilidad del suministro.
Conductores: Son el componente principal para el transporte de energía. La elección del material y la construcción del conductor son decisiones de ingeniería fundamentales que equilibran el costo, la eficiencia y la durabilidad.
Materiales: Los materiales más comunes son el aluminio y el cobre. El aluminio, a menudo en forma de Conductor de Aluminio con Refuerzo de Acero (ACSR, por sus siglas en inglés), es ampliamente preferido en líneas aéreas debido a su menor peso y costo en comparación con el cobre para una capacidad de corriente equivalente.4
Construcción: Los alimentadores pueden ser aéreos o subterráneos. En las redes aéreas, los conductores pueden ser desnudos, montados sobre crucetas en los postes.1 Alternativamente, se utilizan cables aislados, especialmente en zonas urbanas o con alta densidad de árboles para mejorar la seguridad y reducir las interrupciones. Un cable de MT moderno es una estructura de ingeniería de precisión, compuesta por múltiples capas concéntricas: un conductor central, una pantalla semiconductora interna para suavizar el campo eléctrico, una gruesa capa de aislamiento (comúnmente de polietileno reticulado - XLPE, o caucho de etileno-propileno - EPR), una pantalla semiconductora externa, una pantalla metálica (de hilos o cinta de cobre) para conducir las corrientes de falla y de carga capacitiva, y una cubierta exterior robusta para proteger contra daños mecánicos y ambientales.6
Estructuras de Soporte y Equipos:
Postes y Herrajes: Las líneas aéreas se sostienen mediante postes, que pueden ser de hormigón, madera tratada o acero.3 A estos postes se fijan los herrajes, que incluyen crucetas, abrazaderas, y otros elementos metálicos que a su vez sostienen a los aisladores.8
Aisladores: Estos componentes, fabricados de porcelana, vidrio o materiales poliméricos, son críticos para soportar mecánicamente los conductores y, al mismo tiempo, aislarlos eléctricamente de las estructuras de soporte puestas a tierra.7
Equipos de Protección y Maniobra: A lo largo del alimentador se instalan diversos dispositivos para garantizar la operación segura y fiable de la red. Los reconectadores (reclosers) son interruptores automáticos que pueden despejar fallas temporales, mejorando la continuidad del servicio. Los seccionalizadores y fusibles se utilizan para aislar secciones más pequeñas de la red donde ha ocurrido una falla permanente, minimizando así el número de clientes afectados.10 Los
pararrayos (surge arresters) se instalan para proteger los equipos, como los transformadores, de sobretensiones transitorias causadas por descargas atmosféricas. Adicionalmente, se pueden encontrar bancos de condensadores para la compensación de potencia reactiva y la mejora del perfil de tensión.2
La estructura física de un alimentador revela una jerarquía de vulnerabilidad. El diseño, que se extiende desde un tronco principal robusto hacia ramales y derivaciones progresivamente más pequeños 2, implica que una falla en el tronco principal tiene un impacto desproporcionadamente mayor que una falla en un ramal terminal. Esto se debe a que el tronco principal transporta la potencia agregada para todas las cargas aguas abajo. Esta realidad física es la razón fundamental detrás de la estrategia de protección escalonada, donde los dispositivos de mayor capacidad y capacidad de maniobra, como los reconectadores, se sitúan cerca de la subestación, mientras que los fusibles, más simples y económicos, protegen los ramales laterales.10 Para el análisis de datos, esto sugiere que la posición de un transformador dentro de esta topología jerárquica es un indicador de riesgo más sofisticado que la simple distancia geográfica. Un transformador en el tronco principal que presenta problemas podría ser un síntoma de un problema sistémico más grave, mientras que una falla en un ramal distante es más probablemente un evento localizado.

1.2 Topología de Red: Configuraciones Radiales, en Anillo y Malladas

La topología de una red de distribución describe el patrón de interconexiones entre la subestación y los puntos de carga. Esta configuración es un factor determinante en la fiabilidad, el costo y la complejidad operativa del sistema.12
Topología Radial: Es la configuración más simple y extendida en los sistemas de distribución, especialmente en zonas suburbanas y rurales. La energía fluye en una sola dirección, desde la subestación hacia las cargas, a través de una estructura que se asemeja a las ramas de un árbol.4
Ventajas: Su principal atractivo es el bajo costo de inversión y la simplicidad en el diseño y la coordinación de las protecciones eléctricas.10
Desventajas: Su principal debilidad es la baja fiabilidad. Cualquier falla en un punto del alimentador principal provoca la interrupción del servicio para todos los clientes situados aguas abajo de la falla, ya que no existe una ruta de alimentación alternativa.10
Topología en Anillo (o Bucle): Esta topología se crea interconectando dos alimentadores radiales o conectando el final de un alimentador de vuelta a la subestación, formando un bucle. Sin embargo, es crucial entender que, en operación normal, el anillo se mantiene abierto en un punto específico, conocido como "punto normalmente abierto" (N.O.). Por lo tanto, opera como dos alimentadores radiales.10
Ventajas: La fiabilidad aumenta drásticamente. Ante una falla, el tramo afectado puede ser aislado abriendo los seccionadores en ambos extremos. Luego, al cerrar el punto N.O., se puede restablecer el suministro a la mayoría de los clientes desde la dirección opuesta, reduciendo significativamente la duración de la interrupción.10
Desventajas: El costo es mayor debido a la necesidad de más cableado y equipos de seccionamiento. La operación y la coordinación de protecciones se vuelven más complejas y a menudo requieren sistemas de automatización.14
Topología Mallada: Caracterizada por múltiples interconexiones entre diferentes alimentadores, proporciona varias rutas de alimentación para cada punto de carga. Esta configuración es típica de las redes de baja tensión en centros urbanos de alta densidad, pero es menos común en media tensión debido a su alta complejidad.12
Ventajas: Ofrece el más alto nivel de fiabilidad y flexibilidad operativa.15
Desventajas: Implica un costo de inversión muy elevado, un aumento significativo de las corrientes de cortocircuito y esquemas de protección extremadamente complejos que requieren una lógica direccional sofisticada.14
La elección de la topología es un compromiso directo entre el costo de la infraestructura y el nivel de fiabilidad deseado. Las empresas de servicios públicos tienden a implementar redes radiales en áreas de baja densidad de carga (rurales, residenciales de baja densidad) donde el costo de una red en anillo no se justifica económicamente.10 Por el contrario, las áreas con cargas críticas (hospitales, centros de datos) o alta densidad de carga (centros urbanos) justifican la inversión en topologías en anillo o malladas. Este patrón predecible de diseño permite hacer inferencias sobre el riesgo inherente de una zona. Se puede plantear la hipótesis de que los alimentadores que sirven a áreas geográficamente dispersas y con baja densidad de transformadores son predominantemente radiales. En consecuencia, las fallas en estas áreas probablemente resultarán en interrupciones más prolongadas (un SAIDI más alto), ya que las opciones de reconfiguración de la red son limitadas o inexistentes. Por lo tanto, el contexto geográfico de un transformador puede actuar como un proxy de la topología de su alimentador y, por extensión, de su perfil de riesgo y fiabilidad.

1.3 Integración de Transformadores

Los transformadores de distribución son el último eslabón en la cadena de media tensión, encargados de reducir la tensión del alimentador (p. ej., 13.2 kV) a un nivel de baja tensión (BT) utilizable por los consumidores (p. ej., 220/127 V o 400/230 V).1 Pueden ser instalados en postes, sobre plataformas de hormigón (pad-mounted) o dentro de cámaras o subestaciones de cliente.17
Métodos de Conexión: Los transformadores se conectan en derivación (en paralelo) a lo largo del alimentador. La configuración de los devanados es un aspecto clave del diseño. La conexión trifásica más común en redes de distribución es Delta (Δ) en el lado de alta tensión (primario) y Estrella con neutro puesto a tierra (Yn) en el lado de baja tensión (secundario).19 Esta configuración, conocida como grupo de conexión
Dyn, ofrece dos ventajas significativas:
El devanado en delta del primario proporciona una ruta para que circulen las corrientes armónicas de tercer orden, impidiendo que se propaguen aguas arriba hacia el resto del sistema.
El devanado en estrella del secundario proporciona un punto neutro estable y accesible, que es esencial para suministrar cargas monofásicas (conectadas entre una fase y el neutro).
Operación en Paralelo: Para aumentar la capacidad de suministro o mejorar la fiabilidad en un punto de la red, es posible operar dos o más transformadores en paralelo. Para que esta operación sea exitosa y se eviten corrientes de circulación perjudiciales que pueden sobrecargar y dañar los transformadores, se deben cumplir condiciones estrictas 19:
Misma Relación de Transformación y Grupo de Conexión: Los transformadores deben tener idénticas relaciones de tensión nominal y pertenecer al mismo grupo de conexión vectorial (p. ej., ambos Dyn11). Esto asegura que sus tensiones secundarias estén en fase.19
Misma Tensión de Cortocircuito (Impedancia Porcentual): Los transformadores deben tener valores de impedancia porcentual (vk​%) idénticos o muy similares (típicamente con una diferencia no mayor al 10%). Esta condición garantiza que la carga total se reparta entre los transformadores de forma proporcional a sus potencias nominales (kVA). Si las impedancias son diferentes, el transformador con la impedancia más baja tomará una parte mayor de la carga, arriesgándose a una sobrecarga.19

Sección 2: La Física de la Regulación de Tensión y el Flujo de Potencia

Esta sección aborda los principios eléctricos fundamentales que dictan el estado de la red. La caída de tensión no es simplemente un número; es la consecuencia física del flujo de potencia a través de un conductor imperfecto. La comprensión de estas ecuaciones es clave para estimar las condiciones de tensión sin mediciones directas.

2.1 Variables Eléctricas Fundamentales

El comportamiento de un sistema de corriente alterna (CA) se describe mediante un conjunto de variables interrelacionadas que definen cómo se genera, transporta y consume la energía.
Potencia Activa (P): Es la potencia que realiza un trabajo útil, como generar luz, calor o movimiento mecánico. Se mide en vatios (W) o kilovatios (kW) y representa el consumo real de energía por el cual se factura a los clientes.20
Potencia Reactiva (Q): Es la potencia necesaria para establecer y mantener los campos eléctricos y magnéticos en dispositivos como motores, transformadores y balastros. No realiza trabajo útil, pero es indispensable para el funcionamiento de estos equipos. Fluye de ida y vuelta entre la fuente y la carga en cada ciclo. Se mide en volt-amperios reactivos (VAR) o kilovars (kVAR).20
Potencia Aparente (S): Es la "potencia total" que la red debe transportar, y es la suma vectorial de la potencia activa y reactiva. La infraestructura de la red (generadores, transformadores, cables) debe dimensionarse para soportar la potencia aparente. Se mide en volt-amperios (VA) o kilovolt-amperios (kVA).20
El Triángulo de Potencias: Estas tres magnitudes forman un triángulo rectángulo donde la potencia activa (P) y la reactiva (Q) son los catetos, y la potencia aparente (S) es la hipotenusa. Su relación matemática se rige por el teorema de Pitágoras:S2=P2+Q2
.20
Factor de Potencia (FP): Es la relación entre la potencia activa y la potencia aparente (FP=P/S). También es igual al coseno del ángulo de desfase (ϕ) entre las ondas de tensión y corriente (FP=cos(ϕ)).25 Un FP ideal es 1.0 (o 100%), lo que significa que toda la potencia aparente es potencia activa. Un FP bajo (p. ej., 0.7) indica una alta proporción de potencia reactiva, lo que obliga a la red a transportar más corriente (y por tanto tener más pérdidas) para entregar la misma cantidad de trabajo útil.25
FP en Atraso (Lagging): Ocurre cuando la corriente se retrasa con respecto a la tensión. Es característico de cargas inductivas como motores y transformadores, que son predominantes en los sistemas de potencia.25
FP en Adelanto (Leading): Ocurre cuando la corriente se adelanta a la tensión. Es característico de cargas capacitivas.25
El factor de potencia actúa como una palanca que magnifica las ineficiencias del sistema. Para una misma potencia activa (P) requerida por una carga, una disminución en el factor de potencia (FP) implica un aumento en la potencia aparente (S=P/FP).25 Dado que la corriente que circula por la línea es proporcional a la potencia aparente (
I≈S/V), un FP más bajo se traduce directamente en una corriente más alta. Este aumento de corriente tiene un efecto perjudicial doble: la caída de tensión (ΔV), que es directamente proporcional a la corriente, aumenta; y las pérdidas de potencia en los conductores por efecto Joule (Ploss​=I2R), que son proporcionales al cuadrado de la corriente, se disparan. Por ejemplo, reducir el FP de un ideal 1.0 a 0.7 requiere aproximadamente un 43% más de corriente para entregar la misma potencia activa, lo que a su vez casi duplica las pérdidas en la línea (1.432≈2.04). Aunque no se disponga de mediciones directas del FP, se pueden hacer suposiciones informadas basadas en el tipo de carga, utilizando el número de usuarios y la potencia nominal del transformador como proxies. Las zonas residenciales suelen tener un FP alto (>0.9), mientras que las zonas industriales con gran cantidad de motores tienden a tener un FP más bajo. Asignar un FP estimado a cada transformador es un paso crucial para habilitar cálculos de caída de tensión realistas.
Desbalance de Fases y Corriente de Neutro: En un sistema trifásico idealmente balanceado, las corrientes en las tres fases son de igual magnitud y están desfasadas 120 grados entre sí. Su suma vectorial es cero, por lo que no circula corriente por el conductor neutro. Sin embargo, en la práctica, las cargas monofásicas (como electrodomésticos y alumbrado) no se distribuyen de manera perfectamente equitativa entre las tres fases. Este desequilibrio provoca que la suma vectorial de las corrientes de fase no sea nula, dando lugar a una corriente de neutro.26
Consecuencias del Desbalance: La corriente de neutro es una fuente de problemas. Genera pérdidas adicionales por efecto Joule (I2R) en el conductor neutro. Dado que los neutros a menudo no están protegidos por interruptores o fusibles, una corriente de neutro excesiva puede causar un sobrecalentamiento peligroso.28 Además, el desbalance de corriente conduce a un desbalance de tensión en el punto de carga, lo que somete a estrés a todos los equipos trifásicos conectados (como motores) y puede reducir su rendimiento y vida útil.29

2.2 Análisis de la Caída de Tensión (ΔV)

La caída de tensión es la reducción en la magnitud del voltaje que ocurre a lo largo de un conductor debido a la impedancia del mismo al paso de la corriente eléctrica.31 Es un fenómeno fundamental que limita la longitud y la capacidad de carga de los alimentadores.
Ecuación Fundamental: La caída de tensión (ΔV) es el producto vectorial de la corriente (I) y la impedancia de la línea (Z=R+jX). Para fines prácticos en ingeniería, se utilizan fórmulas escalares aproximadas que son muy precisas para la mayoría de las aplicaciones de distribución.
Para líneas trifásicas balanceadas:
ΔV≈3​⋅I⋅L⋅(R⋅cos(ϕ)+X⋅sin(ϕ))
Para líneas monofásicas (fase-neutro o fase-fase):
ΔV≈2⋅I⋅L⋅(R⋅cos(ϕ)+X⋅sin(ϕ))

(Ecuaciones adaptadas de 32).

Donde:
ΔV: Caída de tensión entre fases (en voltios).
I: Corriente de carga (en amperios).
L: Longitud del conductor (en kilómetros).
R: Resistencia del conductor por unidad de longitud (en Ω/km).
X: Reactancia inductiva del conductor por unidad de longitud (en Ω/km).
cos(ϕ): Factor de potencia de la carga.
sin(ϕ): Componente reactiva del factor de potencia, calculada como 1−cos2(ϕ)​.
Factores Influyentes: La fórmula evidencia que la caída de tensión se agrava con:
Mayor longitud del alimentador (L): La impedancia es acumulativa con la distancia.35
Mayor corriente de carga (I): Cargas más pesadas provocan mayores caídas.37
Mayor impedancia del conductor (R y X): Conductores de menor sección transversal tienen mayor resistencia.35
Menor factor de potencia (cos(ϕ)): Un FP bajo aumenta la corriente total y la contribución del término reactivo (Xsin(ϕ)), que es significativo en líneas de MT.25
Propagación en un Alimentador Radial: En una estructura radial, las caídas de tensión de cada tramo de línea son acumulativas. La tensión en un transformador dado es la tensión en la subestación menos la suma de las caídas de tensión de todos los segmentos de línea que lo preceden. Esto implica que los transformadores ubicados al final de los ramales largos y muy cargados son los que experimentan las peores condiciones de tensión y son los más vulnerables a problemas de subtensión.
Caída de Tensión Estática vs. Dinámica:
Caída de Tensión Estática (o en Régimen Permanente): Es la caída de tensión calculada bajo condiciones de carga estables y predecibles. Esta es la que se calcula principalmente con las fórmulas anteriores y define el perfil de tensión base del alimentador en condiciones normales de operación.39
Caída de Tensión Dinámica (o Transitoria): Se refiere a una disminución abrupta y de corta duración de la tensión, comúnmente conocida como hundimiento de tensión (voltage sag). Estos eventos son causados por fenómenos súbitos en la red, como la energización de grandes cargas (p. ej., el arranque de un motor industrial) o un cortocircuito en un alimentador adyacente.40 La corriente de arranque de un motor grande puede ser de 5 a 8 veces su corriente nominal, provocando un hundimiento de tensión severo pero temporal que puede causar el mal funcionamiento de equipos electrónicos sensibles.44 Aunque el análisis se centra en estimar la caída estática, la magnitud de la caída dinámica está directamente relacionada con la debilidad de la red, que a su vez se refleja en una alta caída estática.
La caída de tensión estática es más que un simple indicador de la calidad del servicio; es un proxy directo de la "debilidad" eléctrica de un punto en la red. Una alta caída de tensión estática implica que la impedancia entre ese punto y la fuente (la subestación) es elevada, ya sea por una gran distancia o por conductores subdimensionados.35 En un punto eléctricamente débil, cualquier perturbación de corriente, como el arranque de un motor, provocará un hundimiento de tensión dinámico mucho más pronunciado (
ΔVdinamica​=Iarranque​⋅Zlinea​). Estos severos hundimientos pueden causar la desconexión de contactores, el reinicio de equipos de control y someter a estrés dieléctrico y mecánico a los devanados de los transformadores. Por lo tanto, se puede establecer una cadena causal: alta impedancia de línea → alta caída de tensión estática → alta sensibilidad a hundimientos dinámicos → mayor estrés en los equipos → mayor probabilidad de falla. Esto convierte a la caída de tensión estática estimada en una característica predictiva de gran alcance para la probabilidad de falla de un transformador.

2.3 Marco Regulatorio y Estándares

Las empresas de distribución eléctrica no operan en un vacío; están obligadas por ley a mantener la calidad del suministro dentro de límites definidos para proteger los equipos de los consumidores y garantizar la estabilidad de la red.
Límites de Tensión Típicos: Las normativas establecen una banda de tensión permitida en el punto de entrega al cliente.
Un estándar común, como el ANSI C84.1 en Norteamérica, especifica un rango de servicio normal de ±5% sobre la tensión nominal (p. ej., para una tensión nominal de 120 V, el rango aceptable es de 114 V a 126 V).46
Normativas europeas como la EN 50160 o la IEC 60038 a menudo definen un rango de ±10%.47
Reglamentos específicos, como el REBT en España, detallan caídas de tensión máximas admisibles para diferentes partes de la instalación, por ejemplo, 3% para circuitos de alumbrado y 5% para otros usos en instalaciones interiores, sumando las caídas desde la acometida.34
Exceder estos límites puede resultar en penalizaciones para la empresa distribuidora y es un indicador clave de mala calidad del servicio.
Estándares de Referencia Clave:
IEEE 1366: Es el estándar de referencia para la definición y cálculo de los índices de fiabilidad de la distribución, incluyendo SAIDI, SAIFI y MAIFI.50
Serie IEEE C57: Un conjunto completo de normas que rigen el diseño, ensayo, operación y carga de transformadores. La IEEE C57.91 es la guía fundamental para la carga de transformadores de potencia inmersos en aceite y la estimación de su pérdida de vida.17
Serie IEC 61000: Se enfoca en la compatibilidad electromagnética (EMC). Partes como la 61000-3-x y 61000-4-x establecen límites para perturbaciones como armónicos y flicker.47
IEEE 519: Es el estándar recomendado en Norteamérica para el control de armónicos en sistemas de potencia, estableciendo límites tanto para la distorsión de tensión que la red puede tener como para la distorsión de corriente que los clientes pueden inyectar.55

Sección 3: Salud de la Red: Análisis de Fallas y Calidad de la Energía

Esta sección se desplaza desde la operación normal hacia las condiciones anómalas. Examina cómo fallan los transformadores y cómo se cuantifica la "salud" general de la red, proporcionando el contexto para lo que los modelos de Machine Learning buscarán predecir.

3.1 Modos de Falla de los Transformadores

Las fallas en los transformadores de distribución raramente son eventos instantáneos. Suelen ser el resultado de un proceso de degradación gradual de su sistema de aislamiento, compuesto principalmente por papel celulósico y aceite dieléctrico. Los principales factores de estrés que aceleran esta degradación son de naturaleza térmica, dieléctrica y mecánica.
Estrés Térmico (Sobrecarga y Temperatura): Es el modo de falla más común y mejor comprendido.
Cuando un transformador opera por encima de su potencia nominal (kVA), las pérdidas por efecto Joule (I2R) en sus devanados aumentan drásticamente, generando un calor excesivo.17
La vida útil del aislamiento de papel celulósico está inversamente relacionada con la temperatura. Esta relación se modela con la ecuación de Arrhenius, que postula que la tasa de envejecimiento químico del aislamiento se duplica aproximadamente por cada 6 a 10 °C de aumento en la temperatura de operación por encima de su valor nominal.56
El estándar IEEE C57.91 es la guía de referencia para la carga de transformadores. Proporciona modelos detallados para calcular la temperatura del punto más caliente ("hot-spot") del devanado en función de la carga, la temperatura ambiente y las características del transformador. A partir de esta temperatura, se calcula un "factor de aceleración del envejecimiento" y la "pérdida de vida" acumulada.57 Un transformador sometido a sobrecargas frecuentes y prolongadas verá su vida útil reducida de manera exponencial.
Estrés Dieléctrico (Problemas de Tensión): El sistema de aislamiento está diseñado para soportar la tensión nominal de operación, pero es vulnerable a sobretensiones y a la degradación a largo plazo.
Descargas Parciales (DP): Son pequeñas chispas o arcos eléctricos que ocurren en pequeñas burbujas de gas o impurezas dentro del aceite, o en vacíos en el aislamiento sólido. Individualmente son de baja energía, pero su ocurrencia repetida degrada químicamente el aislamiento, creando caminos conductores que eventualmente pueden llevar a una falla catastrófica.61 La mala calidad de la tensión, como las sobretensiones transitorias, puede iniciar o acelerar la actividad de DP.
Arcos Eléctricos: Son descargas de alta energía que representan una falla dieléctrica completa. Generan temperaturas extremadamente altas, descomponiendo rápidamente el aceite y produciendo grandes volúmenes de gas, lo que puede llevar a un aumento de presión y a una falla explosiva del tanque del transformador.62
Impacto de la Mala Calidad de la Energía:
Armónicos: Las corrientes armónicas, generadas por cargas no lineales (electrónica de potencia, variadores de frecuencia), son particularmente dañinas. Estas corrientes de alta frecuencia causan pérdidas adicionales tanto en los devanados (por efecto pelicular) como en el núcleo del transformador (por corrientes de Foucault e histéresis), lo que resulta en un sobrecalentamiento adicional que no es capturado por las mediciones de corriente a frecuencia fundamental.63 Además, los armónicos pueden interactuar con la capacitancia de la red y causar resonancia, generando sobretensiones extremas que estresan el aislamiento.65
Flicker y Hundimientos de Tensión: Las fluctuaciones rápidas de tensión, aunque principalmente son un problema de calidad visual, son sintomáticas de grandes cargas variables que imponen ciclos de estrés mecánico y eléctrico en los transformadores.66

3.2 Firmas de Diagnóstico

Aunque los datos disponibles no incluyen mediciones de diagnóstico avanzadas, es importante conocer las técnicas estándar de la industria para entender qué tipo de información se utiliza para la detección de fallas incipientes.
Análisis de Gases Disueltos (DGA): Es la herramienta de diagnóstico más poderosa para transformadores inmersos en aceite. A medida que el aceite y el papel aislante se degradan bajo estrés térmico o dieléctrico, generan gases que se disuelven en el aceite. El tipo y la proporción de estos gases actúan como una firma de la falla subyacente.61
Sobrecalentamiento de baja temperatura (<300 °C): Produce principalmente Metano (CH4​) y Etano (C2​H6​).
Sobrecalentamiento de alta temperatura (>300 °C): Genera Etileno (C2​H4​).
Descargas parciales (Corona): Producen Hidrógeno (H2​) y Metano (CH4​).
Arcos de alta energía: La firma inequívoca es la presencia de Acetileno (C2​H2​), que solo se forma a temperaturas muy elevadas.62

Métodos como las Relaciones de Rogers o el Triángulo de Duval utilizan las proporciones de estos gases clave para clasificar el tipo de falla con alta precisión.

3.3 Índices de Calidad y Fiabilidad a Nivel de Sistema

Los reguladores y las empresas de servicios públicos utilizan un conjunto de índices estandarizados, definidos en IEEE 1366, para medir el rendimiento general de la red de distribución desde la perspectiva del cliente.50
SAIFI (System Average Interruption Frequency Index - Índice de Frecuencia de Interrupción Promedio del Sistema): Mide la frecuencia con la que el cliente promedio experimenta una interrupción sostenida (generalmente de más de 5 minutos) en un período determinado (normalmente un año). Un SAIFI más bajo es mejor.
Fórmula:SAIFI=Nuˊmero Total de Clientes ServidosNuˊmero Total de Clientes Interrumpidos​
.51
SAIDI (System Average Interruption Duration Index - Índice de Duración de Interrupción Promedio del Sistema): Mide la duración total de las interrupciones para el cliente promedio. Se expresa comúnmente en minutos u horas por año. Un SAIDI más bajo es mejor.
Fórmula:SAIDI=Nuˊmero Total de Clientes Servidos∑(Duracioˊn de cada interrupcioˊn×Clientes Afectados)​
.69
MAIFI (Momentary Average Interruption Frequency Index - Índice de Frecuencia de Interrupción Momentánea Promedio): Similar al SAIFI, pero cuenta las interrupciones momentáneas (de corta duración, típicamente menos de 5 minutos), que a menudo son causadas por la operación de reconectadores que despejan fallas temporales.
THD (Total Harmonic Distortion - Distorsión Armónica Total): Mide cuánto se desvía una forma de onda de una sinusoide pura debido a la presencia de armónicos. El estándar IEEE 519 establece límites para la THD, típicamente alrededor del 5% para la tensión en el punto de acoplamiento común, para evitar problemas de calidad de energía.55
La variable de estado proporcionada ("Correcta", "Penalizada", "Fallida") es, en esencia, un indicador compuesto que refleja la culminación de uno o más de estos modos de falla y problemas de calidad. Un estado "Fallida" es el resultado final de un proceso de degradación. El estado "Penalizada" es particularmente informativo, ya que sugiere que el transformador ha violado un umbral de rendimiento operativo antes de una falla completa. Esta penalización podría deberse a una regulación de tensión deficiente (violando los límites de ±5%), a una contribución significativa a los índices de interrupción (SAIDI/SAIFI) de su zona, o a señales de alerta detectadas durante inspecciones. Esto implica que el objetivo del modelado no es solo predecir fallas binarias, sino un problema de clasificación multiclase que busca identificar diferentes estados de "salud" de la red. Un desafío clave del análisis será desentrañar las causas subyacentes de estos estados. Se puede formular la hipótesis de que los transformadores con una alta caída de tensión estática estimada tienen más probabilidades de ser clasificados como "Penalizada" debido a violaciones de los límites de tensión, mientras que aquellos con una alta carga estimada (p. ej., un alto Downstream_kVA) pueden ser "Penalizada" o "Fallida" debido al estrés térmico por sobrecarga. La importancia de las características del modelo predictivo será fundamental para validar estas hipótesis.

Parte II: Analítica Avanzada y Modelado Predictivo

Esta parte aborda directamente el desafío central: cómo realizar un análisis sofisticado con datos incompletos. Se desarrollará una metodología para inferir las propiedades de red que faltan y luego se utilizarán esas propiedades para construir modelos predictivos potentes.

Sección 4: Inferencia de Propiedades de la Red a partir de Datos Limitados

Este es el paso fundamental de nuestro enfoque basado en datos. Se creará un modelo simplificado pero eléctricamente significativo del alimentador utilizando los datos geográficos y nominales disponibles.

4.1 De la Distancia Geográfica a la Eléctrica

Es imperativo distinguir entre distancia geográfica y eléctrica. La distancia geográfica, medida en metros o kilómetros, es la separación física entre dos puntos. La distancia eléctrica, medida en ohmios (Ω), representa la impedancia total del circuito que conecta esos dos puntos. La caída de tensión y las pérdidas de potencia son una función directa de la distancia eléctrica, no de la geográfica.72 Dos transformadores pueden estar geográficamente cerca pero eléctricamente distantes si se encuentran en ramales diferentes de un alimentador.
Paso 1: Estimar la Longitud del Conductor: No se puede asumir que los conductores siguen una línea recta entre los transformadores. Siguen el trazado de calles, carreteras y derechos de paso. Un método heurístico de ingeniería comúnmente aceptado es calcular la distancia en línea recta (usando la fórmula de Haversine para coordenadas geográficas) y multiplicarla por un factor de corrección de enrutamiento. Este factor, típicamente en el rango de 1.2 a 1.4, representa la tortuosidad del camino real en comparación con una línea recta.
Paso 2: Estimar la Impedancia de la Línea: El siguiente paso es estimar la impedancia por unidad de longitud (R y X en Ω/km). Este valor depende críticamente del tipo y la sección del conductor, datos que no están disponibles. Sin embargo, se pueden hacer estimaciones razonables. Las empresas de servicios públicos utilizan un conjunto limitado de conductores estandarizados para cada nivel de tensión. Se puede construir una tabla de consulta con valores típicos de R y X para conductores comunes como el ACSR, basándose en manuales de ingeniería y estándares.74 Como primera aproximación, se pueden usar valores genéricos, como
X≈0.1Ω/km para cables aéreos trenzados o X≈0.08Ω/km para otras configuraciones.32
A continuación se presenta una tabla con valores de impedancia típicos que pueden ser utilizados para este propósito.
Tipo de Conductor (ACSR)
Tensión Nominal (kV)
Resistencia (R) (Ω/km)
Reactancia (X) (Ω/km)
Justificación de Aplicación Típica
1/0 AWG ("Pigeon")
13.2 - 15
0.55
0.48
Ramales rurales y de baja carga
4/0 AWG ("Penguin")
13.2 - 25
0.22
0.45
Líneas troncales de alimentadores comunes
336.4 MCM ("Linnet")
13.2 - 34.5
0.17
0.42
Alimentadores de alta capacidad
795 MCM ("Drake")
25 - 34.5
0.07
0.38
Salidas de subestación, cargas industriales pesadas

Paso 3: Calcular la Distancia Eléctrica Acumulada: Una vez inferida la topología (siguiente subsección), la distancia eléctrica de cada transformador a la subestación se calcula como la suma acumulada de las impedancias complejas de todos los segmentos de línea en la ruta que lo conecta a la fuente.
Ztotal​=segmentos en ruta∑​(Rsegmento​+jXsegmento​)

4.2 Reconstrucción de la Topología de la Red

Este es el paso de inferencia más crítico. Dado que todos los transformadores en el conjunto de datos están etiquetados con su ID de alimentador, el análisis se puede realizar de forma independiente para cada alimentador. El principio rector es que las empresas de servicios públicos diseñan las rutas de los alimentadores para minimizar la longitud total del conductor, que es un costo de capital importante. Este problema de optimización es análogo al problema del Árbol de Expansión Mínima (Minimum Spanning Tree - MST) en la teoría de grafos.77
Metodología Basada en MST:
Definición del Grafo: Para un alimentador dado, se construye un grafo donde cada transformador (con sus coordenadas geográficas) es un nodo. La ubicación de la subestación, si no se conoce, se puede estimar como el nodo geográficamente más cercano a una línea de transmisión conocida, o como el centroide de un clúster de transformadores de alta capacidad. Este nodo se designa como la raíz del árbol.
Ponderación de Aristas: Se crea un grafo completo donde el peso de la arista entre cada par de nodos es la distancia geográfica euclidiana o de Haversine entre ellos.
Aplicación del Algoritmo: Se ejecuta un algoritmo MST estándar, como el de Prim o el de Kruskal, sobre este grafo ponderado.
Resultado: El árbol resultante representa la topología radial más probable del alimentador de media tensión. Este árbol define la conectividad: qué transformador está conectado a cuál, formando el tronco principal y los ramales laterales. Este enfoque es validado por la literatura académica para la planificación y reconstrucción de redes eléctricas.77
La aplicación del MST no solo revela la conectividad, sino que también expone la jerarquía estructural de la red. A partir de esta estructura de árbol, se pueden derivar características topológicas potentes para cada transformador que van más allá de la simple distancia. Se puede calcular su "número de saltos" (hop count) desde la subestación, su "profundidad de rama", el "número de hijos aguas abajo" que alimenta, y su "centralidad de intermediación" (betweenness centrality), que mide cuántos caminos pasan a través de él. Estas características capturan el rol funcional de un transformador dentro de la red, lo que probablemente sea un predictor mucho más fuerte de fallas por sobrecarga o efectos en cascada que las coordenadas geográficas por sí solas. Este proceso transforma eficazmente simples coordenadas (X, Y) en un rico conjunto de características basadas en grafos.

4.3 Creación de un Modelo Eléctrico Simplificado

Al combinar la topología inferida (4.2) con la distancia eléctrica estimada por segmento (4.1), se obtiene un modelo eléctrico completo y simplificado del alimentador. Este modelo, representado como un grafo ponderado, contiene:
Nodos: La subestación y cada transformador.
Aristas: Las conexiones inferidas entre los nodos.
Pesos de las Aristas: La impedancia compleja estimada (R+jX) para cada tramo de línea.
Este modelo es ahora una herramienta suficientemente potente para ejecutar análisis de flujo de carga simplificados y, lo que es más importante, para estimar la magnitud de la tensión en cada nodo del transformador, abordando así uno de los objetivos principales del usuario.78 La incertidumbre en las estimaciones (p. ej., el tipo de conductor) puede incluso convertirse en una característica. Se puede ejecutar el modelo con un rango de parámetros plausibles (p. ej., impedancias para conductores pequeños, medianos y grandes) para calcular un rango de posibles caídas de tensión. La
varianza de la caída de tensión de un transformador ante estos cambios de parámetros puede ser en sí misma una característica predictiva, representando una "fragilidad de diseño" que puede correlacionarse con un estado de calidad deficiente.

Sección 5: Machine Learning para el Análisis Predictivo de Fallas

Con un modelo eléctrico inferido y un nuevo y rico conjunto de características, ahora es posible construir potentes modelos predictivos. Esta sección detalla el proceso de ingeniería de características, la selección de modelos y cómo incorporar el conocimiento de la red recién derivado.

5.1 Ingeniería de Características para el Conjunto de Datos Disponible

El objetivo es transformar los datos brutos y las propiedades inferidas en un conjunto de características que capture la física subyacente de los modos de falla. La literatura sobre el tema utiliza datos operativos como la carga, la temperatura y el análisis de gases disueltos (DGA) como predictores clave.79 En ausencia de estos, se deben diseñar proxies efectivos.
Características Brutas Disponibles:
Coordenadas (Lat, Lon)
Potencia_Nominal_kVA
Numero_Usuarios
Alimentador_ID
Estado_Calidad (Variable Objetivo)
Características de Ingeniería (Features):
Posicionales y Topológicas (derivadas de la Sección 4):
Distancia_Electrica_R: Resistencia acumulada desde la subestación (Ω).
Distancia_Electrica_X: Reactancia acumulada desde la subestación (Ω).
Distancia_Electrica_Z: Magnitud de la impedancia acumulada (∣Z∣=R2+X2​).
Numero_Saltos: Número de transformadores en la ruta desde la subestación.
Es_Nodo_Hoja: Variable binaria (1 si es el último en un ramal, 0 si no).
kVA_Aguas_Abajo: Suma de los kVA de todos los transformadores alimentados a través de este nodo.
Centralidad_Intermediacion: Medida de la importancia del nodo en la red.
Proxies Basados en la Carga:
kVA_por_Usuario (Potencia_Nominal_kVA / Numero_Usuarios): Un proxy potente para distinguir tipos de carga. Valores bajos sugieren áreas residenciales; valores altos sugieren clientes comerciales o industriales.
Carga_Estimada_P (kW): Potencia_Nominal_kVA × factor_de_diversidad × FP_estimado.
Carga_Estimada_Q (kVAR): P×tan(arccos(FPestimado​)).
Características de Vecindad:
Densidad_Vecinos: Número de otros transformadores dentro de un radio geográfico definido (p. ej., 500 m).
Estado_Padre: El Estado_Calidad del nodo padre en el MST. Un transformador aguas arriba con problemas es una señal de alerta importante.
A continuación se presenta una matriz que resume el proceso de ingeniería de características, sirviendo como guía práctica para el desarrollo del modelo.
Nombre de la Característica
Cálculo / Derivación
Datos Brutos Utilizados
Interpretación Física y Racionalidad
Distancia_Electrica_Z
(∑Rseg​)2+(∑Xseg​)2​ vía MST
Coordenadas, ID de Alimentador
Proxy de la impedancia total a la subestación; impulsor clave de la caída de tensión.
kVA_por_Usuario
Potencia_Nominal_kVA / Numero_Usuarios
kVA, # Usuarios
Proxy del tipo de cliente (bajo=residencial, alto=industrial/comercial), lo que influye en el FP y el perfil de carga.
kVA_Aguas_Abajo
∑kVAhijo​ para todos los nodos hijos en el MST
kVA, Topología Inferida
Proxy de la carga térmica acumulativa que el segmento de línea aguas arriba del transformador debe soportar.
Es_Nodo_Hoja
Comprobar si el nodo no tiene hijos en el MST
Topología Inferida
Identifica transformadores al final de los ramales, los más propensos a problemas de tensión.
Estado_Padre_Codificado
Estado_Calidad del nodo padre en el MST
Estado, Topología Inferida
Captura la correlación espacial y el riesgo de fallas en cascada.


5.2 Incorporación de la Topología de Red en Modelos de ML

Los modelos de ML estándar, como Random Forest, a menudo tratan las características de forma independiente. Sin embargo, las características de una red eléctrica son inherentemente relacionales.
Características Basadas en Grafos: Las características topológicas diseñadas anteriormente son una forma eficaz de inyectar el conocimiento del grafo en los modelos estándar.
Redes Neuronales de Grafos (GNN): Para un enfoque más avanzado y potente, las GNN están diseñadas específicamente para operar sobre datos estructurados en grafos. Una GNN puede aprender patrones complejos de propagación de fallas, donde el estado de un transformador está influenciado por el estado de sus vecinos inmediatos en el grafo de la red.82 El modelo aprende a pasar "mensajes" entre los nodos conectados, capturando de forma natural la física del flujo de potencia y la propagación de la tensión. Este es un enfoque de vanguardia para el diagnóstico de fallas en sistemas de potencia.84

5.3 Selección y Evaluación de Modelos

Modelos Candidatos:
Random Forest y XGBoost: Son excelentes modelos de base. Son robustos, manejan bien las relaciones no lineales y proporcionan puntuaciones de importancia de las características, que son cruciales para entender por qué ocurren las fallas.86 La literatura a menudo muestra que XGBoost supera ligeramente a Random Forest en precisión y eficiencia en tareas de clasificación similares.87
Redes Neuronales (Perceptrón Multicapa - MLP): Pueden capturar interacciones complejas entre las características.
Redes Neuronales de Grafos (GNN): El enfoque más sofisticado, que modela directamente la topología de la red.
Manejo del Desbalance de Datos: La clase "Fallida" será, con suerte, un evento raro. Este desbalance de clases debe ser abordado para evitar que el modelo simplemente ignore la clase minoritaria. Las técnicas efectivas incluyen:
SMOTE (Synthetic Minority Over-sampling Technique): Genera ejemplos sintéticos de la clase minoritaria para equilibrar el conjunto de datos de entrenamiento.
Pesos de Clase (Class Weights): Se penaliza más al modelo por clasificar erróneamente un ejemplo de la clase minoritaria durante el entrenamiento.
Métricas de Evaluación: La precisión (accuracy) es una métrica engañosa para conjuntos de datos desbalanceados. Se deben utilizar métricas más informativas:
Precisión (Precision): De todos los transformadores que el modelo predijo que fallarían, ¿cuántos realmente fallaron? (TP/(TP+FP)).
Recall (Sensibilidad): De todos los transformadores que realmente fallaron, ¿cuántos detectó el modelo? (TP/(TP+FN)).
Puntuación F1 (F1-Score): Es la media armónica de la precisión y el recall, proporcionando una única métrica que equilibra ambos.
AUC-ROC: Mide la capacidad del modelo para distinguir entre las clases positiva y negativa a través de todos los umbrales de clasificación.
La importancia de las características obtenida de un modelo de árbol (Random Forest o XGBoost) puede ser utilizada como una herramienta de diagnóstico para validar el modelo físico y diferenciar las causas raíz de las fallas. Si Distancia_Electrica_Z y kVA_por_Usuario (proxy de bajo FP) son los predictores más importantes para la clase "Penalizada", esto valida fuertemente la hipótesis de que la caída de tensión es una causa principal de la mala calidad. Si kVA_Aguas_Abajo es el predictor principal para la clase "Fallida", sugiere que la sobrecarga térmica crónica es una causa más probable de falla catastrófica. De este modo, el modelo de ML se convierte en una herramienta de diagnóstico que puede inferir la causa probable de la mala salud de un transformador y guiar las acciones de mantenimiento preventivo (p. ej., cambiar el conductor para problemas de tensión vs. aumentar el tamaño del transformador para problemas de sobrecarga).

Parte III: Síntesis y Recomendaciones Estratégicas

Esta parte final sintetiza todo el análisis anterior en un marco coherente, aborda el impacto de tecnologías emergentes como la Generación Distribuida (GD) y proporciona respuestas directas y procesables a las preguntas del usuario.

Sección 6: El Impacto de la Generación Distribuida (GD)

Aunque no esté presente en el conjunto de datos actual del usuario, la GD es un factor crítico en los sistemas de distribución modernos, y cualquier análisis prospectivo debe considerar su impacto.

6.1 Efectos sobre el Perfil de Tensión y el Flujo Bidireccional

La premisa fundamental del diseño de redes de distribución radiales es el flujo de potencia unidireccional, desde la subestación hacia las cargas. La GD subvierte este principio.
Aumento de Tensión (Voltage Rise): Tradicionalmente, la tensión siempre disminuye a medida que uno se aleja de la subestación. La GD, al inyectar potencia en puntos intermedios del alimentador, puede causar un aumento de tensión local.90 Durante períodos de alta generación (p. ej., un mediodía soleado para paneles solares fotovoltaicos) y baja carga local, este fenómeno puede empujar la tensión por encima de los límites regulatorios (p. ej., +5%), creando problemas de sobretensión que son tan perjudiciales como la subtensión.
Flujo de Potencia Bidireccional: Cuando la generación local excede el consumo local, el excedente de potencia fluye en sentido inverso, hacia la subestación.92 Este flujo bidireccional viola la suposición de diseño fundamental de las redes radiales y tiene profundas implicaciones para la protección y la operación de la red.

6.2 Capacidad de Alojamiento (Hosting Capacity)

Definición: La Capacidad de Alojamiento (Hosting Capacity - HC) de un alimentador es la cantidad máxima de GD que puede ser integrada sin necesidad de realizar mejoras significativas en la infraestructura y sin comprometer la calidad de la energía, la fiabilidad o la seguridad.94
Factores Limitantes: La HC no es un valor fijo; está limitada por varios factores técnicos, incluyendo el aumento de tensión, los límites térmicos de los conductores y transformadores, y la coordinación de los sistemas de protección.94
Métodos de Cálculo: La determinación de la HC es un área activa de investigación. Los métodos varían en complejidad 94:
Determinísticos: Utilizan escenarios de peor caso (p. ej., máxima generación y mínima carga) para encontrar un límite conservador.
Estocásticos: Utilizan simulaciones probabilísticas (como Monte Carlo) para tener en cuenta la variabilidad de la generación y la carga.
Basados en Optimización: Formulan el problema como la maximización de la penetración de GD sujeta a las restricciones operativas de la red.

6.3 Implicaciones para los Esquemas de Protección

El flujo bidireccional de corriente de falla introducido por la GD puede hacer que los esquemas de protección tradicionales, diseñados para un flujo unidireccional, operen incorrectamente.
Falso Disparo (Sympathetic Tripping): Una falla en un alimentador puede ser alimentada no solo desde la subestación, sino también por la GD en un alimentador adyacente sano. La corriente de falla que fluye desde el alimentador sano puede hacer que su propia protección se dispare innecesariamente, causando una interrupción en un área que no tenía problemas.92
Cegamiento de la Protección (Protection Blinding): La contribución de corriente de la GD a una falla puede alterar la corriente total vista por el relé de la subestación. En algunos casos, puede reducir la corriente que fluye desde la subestación por debajo del umbral de disparo del relé, "cegándolo" e impidiendo que despeje la falla de manera oportuna.92
Islanding no intencionado: Si una porción del alimentador se desconecta de la red principal pero la GD local es suficiente para seguir alimentando las cargas en esa sección, se crea una "isla" energética. Esto representa un grave riesgo para la seguridad del personal de mantenimiento y puede dañar los equipos si no se gestiona adecuadamente.
La alta penetración de GD exige una modernización de los sistemas de protección, pasando de esquemas simples de sobrecorriente a sistemas más inteligentes, adaptativos y basados en comunicaciones que puedan determinar la dirección de la falla y coordinarse en tiempo real.

Sección 7: Análisis Integrado y Perspectivas Accionables

Esta sección final consolida los hallazgos del informe para proporcionar respuestas directas a las preguntas clave del usuario y proponer un flujo de trabajo analítico práctico.

7.1 Respuestas a las Preguntas Clave

1. ¿Podemos estimar la distancia eléctrica entre transformadores?
Respuesta: Sí. Se puede lograr una estimación robusta mediante un proceso de dos pasos. Primero, inferir la topología física más probable del alimentador aplicando un algoritmo de Árbol de Expansión Mínima (MST) a las coordenadas geográficas de los transformadores pertenecientes al mismo alimentador. Segundo, asignar una impedancia por kilómetro a cada segmento del árbol inferido utilizando valores típicos de conductores para el nivel de tensión de la red (ver Tabla 1). La distancia eléctrica de un transformador a la subestación es la suma de las impedancias de los segmentos en su ruta. Este método se detalla en la Sección 4.
2. ¿Cómo correlacionar la posición en el alimentador con los problemas?
Respuesta: La posición no debe ser representada por coordenadas geográficas, sino por las características de ingeniería derivadas de la topología inferida: la distancia eléctrica y la jerarquía topológica (p. ej., número de saltos desde la subestación, si es un nodo hoja). Se espera una fuerte correlación positiva entre estas métricas y los estados de "Penalizada" o "Fallida", ya que son proxies directos de la debilidad del sistema y la magnitud de la caída de tensión. Esta correlación puede ser cuantificada y explotada por un modelo de machine learning.
3. ¿Qué características de ML serían más predictivas con nuestros datos?
Respuesta: Dada la naturaleza de los datos y la física del sistema, las características de ingeniería más predictivas probablemente serán:
Distancia_Electrica_Z: Como proxy principal de la caída de tensión y la debilidad de la red.
kVA_por_Usuario: Como proxy para el tipo de carga (industrial vs. residencial), lo que permite inferir perfiles de carga y factores de potencia.
kVA_Aguas_Abajo: Como proxy de la carga térmica acumulada que debe soportar el transformador y su segmento de línea aguas arriba.
Estado_Padre_Codificado: Como proxy del riesgo de fallas en cascada y la salud de la sección de red local.
4. ¿Cómo identificar si las fallas son por tensión vs. sobrecarga vs. edad?
Respuesta: Esta diferenciación se puede lograr analizando la importancia de las características del modelo de ML entrenado para predicciones específicas:
Falla por Tensión: Indicada cuando un transformador es clasificado como "Penalizada" o "Fallida" y las características más importantes para esa predicción son Distancia_Electrica_Z y Es_Nodo_Hoja. Esto sugiere que el transformador está eléctricamente lejos y es propenso a subtensión.
Falla por Sobrecarga: Indicada cuando las características dominantes son kVA_Aguas_Abajo o un valor muy bajo de kVA_por_Usuario (que implica un gran número de clientes residenciales cuya carga diversificada supera la capacidad térmica del transformador).
Falla por Edad (Fin de Vida Útil): Si se dispusiera de datos de edad, esta sería una característica importante para transformadores que fallan sin otros indicadores fuertes de estrés por tensión o sobrecarga. En su ausencia, se puede utilizar el número de mediciones temporales como un proxy imperfecto de la edad relativa o del tiempo en servicio.

7.2 Flujo de Trabajo Analítico Propuesto

Se propone un flujo de trabajo de extremo a extremo para implementar esta metodología:
Limpieza y Validación de Datos: Verificar la integridad de las coordenadas geográficas y los IDs de los alimentadores. Agrupar los datos por Alimentador_ID.
Inferencia de Topología: Para cada alimentador, ejecutar el algoritmo MST sobre las coordenadas de los transformadores para generar el grafo de la red. Identificar el nodo raíz (subestación).
Estimación de Parámetros: Asignar valores de impedancia (R+jX) a las aristas del grafo utilizando la Tabla 1 como referencia.
Ingeniería de Características: Calcular el conjunto completo de características detalladas en la Sección 5.1 y la Tabla 3 para cada transformador.
Entrenamiento del Modelo: Dividir los datos en conjuntos de entrenamiento y prueba. Abordar el desbalance de clases en el conjunto de entrenamiento (p. ej., con SMOTE). Entrenar un clasificador robusto como XGBoost o Random Forest para predecir la variable Estado_Calidad utilizando las características de ingeniería.
Evaluación y Despliegue: Evaluar el rendimiento del modelo utilizando métricas apropiadas como F1-Score y AUC-ROC. Una vez validado, utilizar el modelo para calificar todos los transformadores de la red, generando una lista de riesgo priorizada para acciones de mantenimiento preventivo.
Análisis de Causa Raíz: Para los transformadores identificados como de alto riesgo, analizar la importancia de las características (p. ej., con SHAP - SHapley Additive exPlanations) para inferir la causa raíz probable de la predicción, como se describe en la Sección 7.3.

7.3 Diferenciación de las Causas Raíz de Falla: Un Marco de Decisión

El resultado final del análisis no debe ser solo una predicción, sino una recomendación informada. Se puede utilizar un marco de decisión para interpretar las salidas del modelo.
Entrada: Un transformador clasificado como de "alto riesgo" (alta probabilidad de ser "Penalizada" o "Fallida") por el modelo de ML.
Proceso: Examinar las 3 características principales que contribuyen a su puntuación de riesgo (obtenidas a través de la importancia de características del modelo).
Salida: Una causa raíz probable y una acción recomendada.
Si Distancia_Electrica_Z es alta y Es_Nodo_Hoja es verdadero:
Diagnóstico Probable: Estrés por subtensión crónica y alta sensibilidad a hundimientos de tensión.
Acción Recomendada: Realizar mediciones de campo del perfil de tensión. Considerar la instalación de un banco de condensadores, el aumento de la sección del conductor (reconductoring) o la instalación de un regulador de tensión.
Si kVA_Aguas_Abajo es alto o kVA_por_Usuario es muy bajo:
Diagnóstico Probable: Estrés por sobrecarga térmica crónica.
Acción Recomendada: Instalar un medidor para monitorear el perfil de carga real. Considerar la actualización a un transformador de mayor capacidad (kVA) o rebalancear las cargas en el secundario.
Si Estado_Padre_Codificado indica una falla:
Diagnóstico Probable: Riesgo de falla en cascada debido a un problema aguas arriba.
Acción Recomendada: Inspeccionar urgentemente el transformador padre y el segmento de línea intermedio en busca de fallas incipientes o equipos de protección defectuosos.
Este marco transforma el modelo predictivo de una "caja negra" a una herramienta de diagnóstico transparente que capacita a los ingenieros de distribución para tomar decisiones proactivas, eficientes y basadas en datos para mejorar la fiabilidad y la resiliencia de la red eléctrica.
Obras citadas
Redes de Media Tension - Distribución de energía eléctrica - Scribd, fecha de acceso: julio 15, 2025, https://es.scribd.com/presentation/566666797/10-Redes-de-Media-Tension
REGLAMENTO DISEÑO Y CONSTRUCCIÓN PARA REDES ELÉCTRICAS DE DISTRIBUCIÓN AÉREAS, fecha de acceso: julio 15, 2025, https://sie.gob.do/wp-content/uploads/2023/01/VOLUMEN-I-Generalidades-y-Consideraciones-NRD-AE-I-.pdf
CONSTRUCCIÓN DE INSTALACIONES AÉREAS EN MEDIA Y BAJA TENSIÓN ESPECIFICACIÓN CFE DCCIAMBT, fecha de acceso: julio 15, 2025, https://lapem.cfe.gob.mx/normas/construccion/pdfs/T/DCCIAMBT.pdf
4 2. Sistemas de distribución Un sistema de distribución eléctrico o planta de distribución como comúnmente es llamado, es, fecha de acceso: julio 15, 2025, http://www.ptolomeo.unam.mx:8080/xmlui/bitstream/handle/132.248.52.100/784/A4%20SISTEMAS%20DE%20DISTRIBUCION.pdf?sequence=4
(PDF) Capitulo 1: Elementos de Líneas de Transmisión Aéreas - ResearchGate, fecha de acceso: julio 15, 2025, https://www.researchgate.net/publication/296282681_Capitulo_1_Elementos_de_Lineas_de_Transmision_Aereas
El cable de media tensión y sus principales características - Top Cable, fecha de acceso: julio 15, 2025, https://www.topcable.com/blog-electric-cable/caracteristicas-constructivas-de-un-cable-de-media-tension/
Guía Técnica de Aplicación ITC-LAT 07, fecha de acceso: julio 15, 2025, https://industria.gob.es/Calidad-Industrial/seguridadindustrial/instalacionesindustriales/lineas-alta-tension/Documents/guia-itc-lat-07-rev-2.pdf
MÉXICO RED AÉREA COMPACTA DE DISTRIBUCIÓN EN TENSIONES DE 15 kV HASTA 38 kV - lapem - CFE, fecha de acceso: julio 15, 2025, https://lapem.cfe.gob.mx/normas/pdfs/s/E0000-37.pdf
Líneas aéreas de Media Tensión (MT) - RTE, fecha de acceso: julio 15, 2025, https://rte.mx/lineas-aereas-de-media-tension-mt
Redes radiales, en anillo y malladas - YouTube, fecha de acceso: julio 15, 2025, https://www.youtube.com/watch?v=sTJfCU5UbMo
RECONECTADORES DE DISTRIBUCIÓN AÉREOS, fecha de acceso: julio 15, 2025, https://www.eneldistribuicao.com.br/ce/documentos/E-MT-004%20R-03.pdf
Topología de redes informáticas: Tipos, características y aplicaciones - OpenWebinars, fecha de acceso: julio 15, 2025, https://openwebinars.net/blog/topologia-de-redes-informaticas/
Topologías de las Redes de Distribución - Webnode, fecha de acceso: julio 15, 2025, https://distribucion.webnode.com.co/topologias-de-las-redes-de-distribucion/
Redes radiales y en anillo. - Formación para la Industria 4.0, fecha de acceso: julio 15, 2025, https://automatismoindustrial.com/curso-carnet-instalador-baja-tension/e-redes-aereas/generalidades-en-redes-aereas/redes-radiales-y-en-anillo/
¿Es mejor una red en anillo o una radial? | ValorEficaz - Ciencia, fecha de acceso: julio 15, 2025, https://www.esciencia.org/comparativa-red-radial-con-red-anillo/
Topologías de red: qué son y cuál es su clasificación - AXESS Networks, fecha de acceso: julio 15, 2025, https://axessnet.com/topologias-de-red/
Tipos de Transformadores de Media Tensión (Normativa IEEE) • LeiryChinchilla.com, fecha de acceso: julio 15, 2025, https://www.leirychinchilla.com/transformadores-media-tension/
Tipos de transformadores de distribución, fecha de acceso: julio 15, 2025, https://www.transformadores.cl/blog/tipos-transformador-distribucion/
Subestaciones transformadoras MT/BT: teoría y ejemplos del ... - ABB, fecha de acceso: julio 15, 2025, https://library.e.abb.com/public/f009ada997530ceac125791a0038a26e/1TXA007101G0701_CT2.pdf
LA RELACIÓN ENTRE POTENCIA APARENTE,POTENCIA ACTIVA Y POTENCIA REACTIVA - EverExceed, fecha de acceso: julio 15, 2025, https://es.everexceed.com/blog/the-relationship-between-apparent-power-active-power-and-reactive-power_b567
¿Qué es el factor de potencia? - Iberdrola, fecha de acceso: julio 15, 2025, https://www.iberdrola.es/ca/blog/luz/factor-de-potencia-que-es
Factor de Potencia - Reactivo Faltante - EPE, fecha de acceso: julio 15, 2025, https://www.epe.santafe.gov.ar/index.php?id=519
Potencia reactiva: definición, cálculo y medición | A. Eberle, fecha de acceso: julio 15, 2025, https://www.a-eberle.de/es/conocimiento/rendimiento-ciego/
Cálculadora de factor de potencia, potencias activa, aparente y reactiva. Coseno de phi., fecha de acceso: julio 15, 2025, https://www.herramientasingenieria.com/onlinecalc/spa/electricidad/factor-potencia.html
Factor de potencia - Wikipedia, la enciclopedia libre, fecha de acceso: julio 15, 2025, https://es.wikipedia.org/wiki/Factor_de_potencia
es.ytelect.com, fecha de acceso: julio 15, 2025, https://es.ytelect.com/blog/reasons-of-neutral-current_b198#:~:text=Desequilibrio%20de%20carga&text=En%20un%20sistema%20trif%C3%A1sico%2C%20si,resultante%20en%20el%20conductor%20neutro.
Trifásica desequilibrada y potencia - YouTube, fecha de acceso: julio 15, 2025, https://www.youtube.com/watch?v=7cPRyGsbKC8
Desequilibrio de carga trifásico y Active Load Balancer - ytelect.com, fecha de acceso: julio 15, 2025, https://es.ytelect.com/blog/3-phase-load-unbalance-and-active-load-balancer_b96
¿Qué son los desequilibrios de tensión y corriente? - Fluke Corporation, fecha de acceso: julio 15, 2025, https://www.fluke.com/es-ec/informacion/blog/motores-sistemas-de-impulsion-bombas-compresores/desequilibrio-de-tension
caracterización del desbalance en redes de distribución eléctricas argentinas, a través del factor de desbalance contempland - Tecnología y Ciencia, fecha de acceso: julio 15, 2025, https://rtyc.utn.edu.ar/index.php/rtyc/article/download/241/203/922
Caída de tensión - Wikipedia, la enciclopedia libre, fecha de acceso: julio 15, 2025, https://es.wikipedia.org/wiki/Ca%C3%ADda_de_tensi%C3%B3n
CÁLCULO DE CAÍDAS DE TENSIÓN., fecha de acceso: julio 15, 2025, https://industria.gob.es/Calidad-Industrial/seguridadindustrial/instalacionesindustriales/baja-tension/Documents/bt/guia_bt_anexo_2_sep03R1.pdf
Cálculo de las fórmulas para obtener la sección por caída de tensión - Prysmian Club, fecha de acceso: julio 15, 2025, https://www.prysmianclub.es/no1-calculo-para-obtener-la-seccion-por-caida-de-tension-ejemplo-de-calculo/
Caída de tensión, fecha de acceso: julio 15, 2025, https://www.miguelez.com/descargas/categoria14/caida-de-tension-es.pdf
Medición de la caída de tensión | A. Eberle, fecha de acceso: julio 15, 2025, https://www.a-eberle.de/es/conocimiento/medicion-de-la-caida-de-tension/
¿Qué es la caída de voltaje y cómo evitarlo? - Grupo Industronic, fecha de acceso: julio 15, 2025, https://grupoindustronic.com.co/caida-de-voltaje/
www.a-eberle.de, fecha de acceso: julio 15, 2025, https://www.a-eberle.de/es/conocimiento/medicion-de-la-caida-de-tension/#:~:text=Ca%C3%ADdas%20de%20tensi%C3%B3n%20en%20media%20y%20alta%20tensi%C3%B3n&text=Otras%20causas%20de%20ca%C3%ADdas%20de,transformadores%20con%20resistencias%20m%C3%A1s%20altas.
¿Por qué las líneas de transmisión de alta tensión tienen baja corriente? - Reddit, fecha de acceso: julio 15, 2025, https://www.reddit.com/r/ElectricalEngineering/comments/o2epdl/why_does_high_voltage_transmission_lines_have_low/?tl=es-es
Perturbaciones en la red eléctrica, fecha de acceso: julio 15, 2025, https://afinidadelectrica.com/2020/05/06/perturbaciones-en-la-red-electrica/
Soluciones permanentes para transitorios de potencia - LADWP.com, fecha de acceso: julio 15, 2025, https://www.ladwp.com/es/publicaciones/boletines/art%C3%ADculo/soluciones-permanentes-para-transitorios-de-potencia
TENSIONES TRANSITORIAS: PROBLEMAS Y SOLUCIONES REVISIÓN DE NORMAS Y OTRAS FUENTES DE INFORMACIÓN - CENYTEC, fecha de acceso: julio 15, 2025, https://www.cenytec.com/Publicaciones/24_TESIONES_TRANSITORIAS.pdf
Que son los fenómenos eléctricos transitorios?, como medirlos y analizarlo - YouTube, fecha de acceso: julio 15, 2025, https://www.youtube.com/watch?v=vFqscqrlHME
Generating Set considerations AGN 068 ... - STAMFORD | AvK, fecha de acceso: julio 15, 2025, https://www.stamford-avk.com/sites/stamfordavk/files/AGNs/Spanish-AGNs/AGN068_B_ES.pdf
El efecto de la variación del voltaje en los motores eléctricos - vyphidroasesores.com, fecha de acceso: julio 15, 2025, https://vyphidroasesores.com/el-efecto-de-la-variacion-del-voltaje-en-los-motores-electricos/
5 consejos para reducir la corriente de arranque del motor - iecmotores.com, fecha de acceso: julio 15, 2025, https://iecmotores.com/es/5-tips-to-reduce-motor-starting-current/
Caída de tensión o Voltaje, calculadora, formula, efecto, solución - Electricaplicada, fecha de acceso: julio 15, 2025, https://electricaplicada.com/calculadora-caida-de-tension/
ENERGÍA ELÉCTRICA | GUB.UY, fecha de acceso: julio 15, 2025, https://www.gub.uy/unidad-reguladora-servicios-energia-agua/sites/unidad-reguladora-servicios-energia-agua/files/2019-07/Revisado_TOR2_Energia_Electrica_2019_01_0.pdf
NIVELES DE TENSIÓN DE CONEXIÓN PARA CARGAS DE CLIENTES - Enel, fecha de acceso: julio 15, 2025, https://www.enel.com.co/en/company/technical-standards/otros-documentos/NIVELES-DE-TENSION.html
fecha de acceso: diciembre 31, 1969, https.miguelez.com/descargas/categoria14/caida-de-tension-es.pdf
Clase 09 | PDF | Ingenieria Eléctrica | Red eléctrica - Scribd, fecha de acceso: julio 15, 2025, https://es.scribd.com/presentation/558469952/Clase-09
Understanding SAIFI in Power Systems - Number Analytics, fecha de acceso: julio 15, 2025, https://www.numberanalytics.com/blog/ultimate-guide-saifi-power-systems
Manual para Redes Eléctricas de Distribución Subterránea. CAPITULO 1: CONDICIONES GENERALES 1.1 OBJETIVO. Establecer a nivel - CFIA, fecha de acceso: julio 15, 2025, https://cfia.or.cr/site/wp-content/uploads/2024/pdf/descargas/reglamentos/ejercicio/manual-de-distribucion-electrica.pdf
1 DIVISIÓN DE INGENIERÍA DE ELECTRICIDAD PLIEGO TÉCNICO NORMATIVO : RPTD N° 13. MATERIA - SEC, fecha de acceso: julio 15, 2025, https://www.sec.cl/sitio-web/wp-content/uploads/2020/09/Pliego-T%C3%A9cnico-Normativo-RPTD-N%C2%B013-L%C3%ADneas-el%C3%A9ctricas-de-media-y-baja-tensi%C3%B3n.pdf
ANÁLISIS DE FALLAS EN TRANSFORMADORES DE POTENCIA Y SU PREVENCIÓN INGENIERO ELECTRICISTA - Repositorio Institucional UES - Universidad de El Salvador, fecha de acceso: julio 15, 2025, https://repositorio.ues.edu.sv/bitstreams/6c6b1f2a-37b4-4bde-9e7e-0699fe0d9ef0/download
Límites de THD de Voltaje y Corrientes Permitidos en La IEEE | PDF | Armónico - Scribd, fecha de acceso: julio 15, 2025, https://es.scribd.com/document/153460529/Untitled
Temperatura de Transformadores: Guía Completa para su Control y Monitoreo, fecha de acceso: julio 15, 2025, https://trafomex.com.mx/temperatura-de-transformadores/
metodología para estimar la vida útil del autotransformador at-4, 700 ..., fecha de acceso: julio 15, 2025, https://ve.scielo.org/pdf/uct/v17n67/art01.pdf
IEEE Std C57.91-2011 | PDF | Instituto de Ingenieros Eléctricos y Electrónicos - Scribd, fecha de acceso: julio 15, 2025, https://es.scribd.com/document/838371069/IEEE-Std-C57-91-2011
Envejecimiento de la aislación eléctrica en transformadores de potencia. Desarrollo de un algoritmo de cálculo según guías - 44 Jaiio, fecha de acceso: julio 15, 2025, https://44jaiio.sadio.org.ar/sites/default/files/sii158-168.pdf
Comportamiento de Temperaturas Top Oil y Hot Spot en Transformadores Sumergidos en Aceite Mediante el Ingreso de Carga de - REVISTA INGENIO, fecha de acceso: julio 15, 2025, https://revistadigital.uce.edu.ec/index.php/INGENIO/article/download/4224/5085/23277
Determinación de fallas en transformadores de potencia inmersos en aceite mineral aislante basándose exclusivamente en el DGA - Repositorio CIATEQ, fecha de acceso: julio 15, 2025, https://ciateq.repositorioinstitucional.mx/jspui/bitstream/1020/564/1/Determinacion%20de%20fallas%20en%20transformadores.pdf
Gases y Detección de Fallas en Transformadores Parte 1 - Nova Miron, fecha de acceso: julio 15, 2025, https://www.novamiron.com.ar/Gases%20y%20Detecci%C3%B3n%20de%20Fallas%20en%20Transformadores.%20Parte%201.pdf
Generalidades sobre los armónicos y su influencia en los sistemas de distribución de energía, fecha de acceso: julio 15, 2025, http://www.fctunca.edu.py/application/files/6315/0487/9707/ArmonicosElisaRojas2011.pdf
Causas y efectos de armónicos en sistemas ... - ptolomeo.unam.mx, fecha de acceso: julio 15, 2025, http://www.ptolomeo.unam.mx:8080/xmlui/bitstream/handle/132.248.52.100/11159/tesis.pdf?sequence=1&isAllowed=y
COMPONENTES ARMÓNICAS EN REDES DE DISTRIBUCIÓN ELÉCTRICAS - Revista de Marina, fecha de acceso: julio 15, 2025, https://revistamarina.cl/revistas/2001/5/Acevedo.pdf
Flicker y Armonicos 11111 | PDF | Transformador - Scribd, fecha de acceso: julio 15, 2025, https://ru.scribd.com/doc/312394864/PPT-Flicker-y-Armonicos-11111
ESTUDIO DEL FLICKER EN UNA INSTALACIÓN ELÉCTRICA - Repositorio Institucional de la Universidad Politécnica Salesiana, fecha de acceso: julio 15, 2025, https://dspace.ups.edu.ec/bitstream/123456789/2142/14/UPS-GT000154.pdf
Electric System Reliability - California Public Utilities Commission, fecha de acceso: julio 15, 2025, https://www.cpuc.ca.gov/-/media/cpuc-website/transparency/commissioner-committees/emerging-trends/2021/2021-02-17-electric-system-reliability-presentation---final.pdf
SAIDI y SAIFI, la realidad de la calidad del suministro eléctrico - Electropendientes, fecha de acceso: julio 15, 2025, https://electropendientes.com.ar/saidi-y-saifi-la-realidad-de-la-calidad-del-suministro-electrico/
Distribution System Reliability Metrics - Electricity - State of Michigan, fecha de acceso: julio 15, 2025, https://www.michigan.gov/mpsc/consumer/electricity/distribution-system-reliability-metrics
SAIDI - Wikipedia, fecha de acceso: julio 15, 2025, https://en.wikipedia.org/wiki/SAIDI
DIVISIÓN DE INGENIERÍA DE ELECTRICIDAD PLIEGO TÉCNICO NORMATIVO : RPTD N° 07. MATERIA : FRANJA Y DISTANCIAS DE SEGURIDAD. - SEC, fecha de acceso: julio 15, 2025, https://www.sec.cl/sitio-web/wp-content/uploads/2020/09/Pliego-T%C3%A9cnico-Normativo-RPTD-N%C2%B007-Franja-y-distancia-seguridad.pdf
Anexo-14 Calculo de Distancias Eléctricas, fecha de acceso: julio 15, 2025, https://ria.utn.edu.ar/bitstreams/f1a74d22-4b72-4dcc-9b85-e3762d68aaf6/download
Transmission line data from EMTP examples - HYPERSIM Documentation - OPAL-RT, fecha de acceso: julio 15, 2025, https://opal-rt.atlassian.net/wiki/spaces/PDOCHS/pages/150307736/Typical+Electrical+Parameters
ECE 3600 Transmission Line notes - Electrical & Computer Engineering, fecha de acceso: julio 15, 2025, https://my.ece.utah.edu/~ece3600/Notes_TransmissionLines_S23.pdf
Overhead Line (OHL) Electrical Parameters 4 basic (primary) el. parameters (for each phase) • Resistance R1 (Ω/km) • - PowerWiki, fecha de acceso: julio 15, 2025, https://www.powerwiki.cz/attach/PPE/PPE_pr02_parametry.pdf
Holistic geospatial data-based procedure for electric network design ..., fecha de acceso: julio 15, 2025, https://www.researchgate.net/publication/343090299_Holistic_geospatial_data-based_procedure_for_electric_network_design_and_least-cost_energy_strategy
Métodos Suma de Potencias en sistemas de distribución - Dialnet, fecha de acceso: julio 15, 2025, https://dialnet.unirioja.es/descarga/articulo/4835481.pdf
Tutorial: Create, evaluate, and score a machine fault detection model - Microsoft Fabric, fecha de acceso: julio 15, 2025, https://learn.microsoft.com/en-us/fabric/data-science/predictive-maintenance
(PDF) Machine Learning-Based Predictive Maintenance for ..., fecha de acceso: julio 15, 2025, https://www.researchgate.net/publication/391526605_Machine_Learning-Based_Predictive_Maintenance_for_Transformers
Machine Learning Applications in Estimating Transformer Loss of Life - arXiv, fecha de acceso: julio 15, 2025, https://arxiv.org/pdf/1703.01397
(PDF) Power System Fault Diagnosis and Prediction System Based ..., fecha de acceso: julio 15, 2025, https://www.researchgate.net/publication/377467599_Power_System_Fault_Diagnosis_and_Prediction_System_Based_on_Graph_Neural_Network
[2111.08185] Graph neural network-based fault diagnosis: a review - arXiv, fecha de acceso: julio 15, 2025, https://arxiv.org/abs/2111.08185
Power System Fault Diagnosis and Prediction System Based on Graph Neural Network, fecha de acceso: julio 15, 2025, https://www.irma-international.org/article/power-system-fault-diagnosis-and-prediction-system-based-on-graph-neural-network/336475/
A Novel Fault Diagnosis and Accurate Localization Method for a Power System Based on GraphSAGE Algorithm - MDPI, fecha de acceso: julio 15, 2025, https://www.mdpi.com/2079-9292/14/6/1219
Predicting Electrical Faults in Power Distribution Network - RIT Digital Institutional Repository, fecha de acceso: julio 15, 2025, https://repository.rit.edu/cgi/viewcontent.cgi?article=12509&context=theses
Random Forest vs Xgboost - MLJAR Studio, fecha de acceso: julio 15, 2025, https://mljar.com/machine-learning/random-forest-vs-xgboost/
COMPARATIVE ANALYSIS OF XGBOOST AND RANDOM FOREST ALGORITHMS FOR TRANSFORMER FAILURE PREDICTION, fecha de acceso: julio 15, 2025, https://annals.fih.upt.ro/pdf-full/2024/ANNALS-2024-4-18.pdf
Prediction of Heart Failure Using Random Forest and XG Boost - Scholarly Review Journal, fecha de acceso: julio 15, 2025, https://www.scholarlyreview.org/api/v1/articles/121782-prediction-of-heart-failure-using-random-forest-and-xgboost.pdf
IMPACT OF DISTRIBUTED GENERATION (DG) ON THE DISTRIBUTION SYSTEM NETWORK, fecha de acceso: julio 15, 2025, https://annals.fih.upt.ro/pdf-full/2019/ANNALS-2019-1-25.pdf
The Problems of Modern Distribution Systems in the Age of Distributed Energy Resources (DERs) | EEP - Electrical Engineering Portal, fecha de acceso: julio 15, 2025, https://electrical-engineering-portal.com/problems-modern-distribution-systems-distributed-energy-resources-ders
(PDF) Review of Operational Challenges and Solutions for DER ..., fecha de acceso: julio 15, 2025, https://www.researchgate.net/publication/354983659_Review_of_Operational_Challenges_and_Solutions_for_DER_Integration_with_Distribution_Networks
Distributed Generation Challenges - Energy → Sustainability Directory, fecha de acceso: julio 15, 2025, https://energy.sustainability-directory.com/term/distributed-generation-challenges/
A Review of the Tools and Methods for Distribution Networks ... - MDPI, fecha de acceso: julio 15, 2025, https://www.mdpi.com/1996-1073/13/11/2758
Distribution Feeder Hosting Capacity: What Matters When Planning for DER? - EPRI, fecha de acceso: julio 15, 2025, https://restservice.epri.com/publicdownload/000000003002004777/0/Product
(PDF) A Review of the Tools and Methods for Distribution Networks' Hosting Capacity Calculation - ResearchGate, fecha de acceso: julio 15, 2025, https://www.researchgate.net/publication/341820679_A_Review_of_the_Tools_and_Methods_for_Distribution_Networks'_Hosting_Capacity_Calculation