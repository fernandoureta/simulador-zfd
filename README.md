# Guía de presentación — Zonas de Falla Doble

> **Feria Universitaria · Palacio Pereira · 21 julio 2026**  
> Miguel Ureta · Fernando Ureta — Ingeniería Informática, UBO

---

## 1. El problema en 30 segundos

Chile tiene un sistema de salud segmentado: FONASA (público, ~80% de la población) e ISAPRE (privado). La red pública —hospitales, CESFAM, SAPU— se construyó históricamente y **no necesariamente está donde vive hoy la población más vulnerable**.

**La pregunta del proyecto:** ¿La exclusión en salud se distribuye al azar, o forma patrones espaciales sistemáticos donde los peores índices de vulnerabilidad coinciden con los peores accesos?

**La respuesta:** No es aleatoria. Forma clústeres. A eso llamamos **Zonas de Falla Doble (ZFD)**.

---

## 2. Los tres índices: qué miden y cómo

### IDS — Índice de Demanda Social `[0, 1]`

Mide **quién necesita más** la red pública en cada zona censal.

| Variable | Qué captura |
|---|---|
| % hogares hacinados | Precariedad habitacional |
| % adultos ≥ 60 años | Dependencia del sistema público |
| % personas con discapacidad | Mayor uso de servicios de salud |
| % jefatura femenina | Factor proxy de vulnerabilidad socioeconómica |

Fórmula: promedio de las 4 variables normalizadas por min-max → resultado en `[0,1]`.  
**IDS alto = zona más vulnerable.**

Fuente: Censo INE (geometría + variables de demanda).

---

### IFO v2 — Índice de Fricción de Oferta `[0, 1]`

Mide **qué tan difícil es acceder** a la red pública desde cada zona.  
Método: **2SFCA** (Two-Step Floating Catchment Area — Luo & Wang, 2003).

**Paso 1 — capacidad relativa de cada establecimiento j:**
```
Rj = Sj / Σ pop_i   (para todas las zonas i dentro del radio de j)
```
`Sj` = métrica de oferta del establecimiento:
- Hospitales: camas disponibles (REM20, DEIS)  
- Primaria (CESFAM, CECOSF): 1/(actividad_bruta + 1) (Series A/P, DEIS)  
- Urgencia (SAPU, SAR): misma lógica que primaria

Radios diferenciados por tipo:

| Tipo | Radio |
|---|---|
| Hospital | 5.000 m |
| Primaria (CESFAM) | 1.500 m |
| Urgencia (SAPU) | 2.000 m |

**Paso 2 — acceso de cada zona i:**
```
acceso_i = Σ Rj   (para todos los establecimientos j dentro del radio de i)
IFO_i = 1 - min_max(acceso_i)
```

**IFO alto = peor acceso** (poca oferta disponible en el entorno de la zona).  
Distancia: euclidiana (no se usa ruteo por red vial — limitación declarada).

Fuente: DEIS MINSAL (~534 establecimientos públicos Gran Santiago).

---

### IDH — Índice de Desacoplamiento Homeostático

Mide si el sistema está **compensando o abandonando** la vulnerabilidad.

**Lógica:** La regresión OLS muestra que, en promedio, cuando IDS sube, IFO también sube (más vulnerabilidad → menos acceso). El IDH mide si una zona específica está *por encima o por debajo* de esa tendencia general.

```
IFO_esperado = 0,9640 − 1,0213 × IDS   (OLS calibrado sobre las 1.636 zonas)
IDH = IFO_real − IFO_esperado
```

| Signo | Significado |
|---|---|
| **IDH > 0** | El sistema entrega MENOS acceso del que su propia tendencia predice → **falla sistémica** |
| **IDH < 0** | El sistema entrega MÁS acceso → la red está compensando la vulnerabilidad |

---

### IPSS v2 — Índice de Posición en el Sistema de Salud

```
IPSS = IDS × IFO
```

Alta cuando **ambas** dimensiones son altas. Una zona muy vulnerable con buen acceso tiene IPSS bajo. Una zona con buena oferta pero poca demanda también. Solo son críticas las que fallan en los dos ejes a la vez.

---

## 3. La Zona de Falla Doble (ZFD)

### Definición formal

```
ZFD = (LISA categoria == "HH")  AND  (IDH > 0)
```

**LISA HH** (High-High): zona con IDS alto rodeada de zonas con IDS alto → clúster de vulnerabilidad espacialmente concentrado.  
**Moran's I = 0,3776 (p = 0,001)**: la autocorrelación no es aleatoria.  
Parámetros LISA: contigüidad Queen orden 2, 999 permutaciones, p < 0,05.

### Dos subtipos

| Tipo | N zonas | Habitantes | % Gran Santiago | Causa |
|---|---|---|---|---|
| **ZFD-A** | 201 | 794.064 | 12,9% | Exclusión periférica: crecimiento urbano no compensado por la red pública |
| **ZFD-B** | 109 | 384.408 | — | Sustitución privada: el sistema público está ausente porque la población usa ISAPRE (Las Condes, Vitacura, Providencia, Ñuñoa, Lo Barnechea, La Reina) |

**Total ZFD (A+B):** 310 zonas · **1.178.472 personas** (19,2% del Gran Santiago)

---

## 4. Números clave para memorizar

| Dato | Valor |
|---|---|
| Zonas censales analizadas | **1.636** |
| Comunas | **34** |
| Población Gran Santiago | **6.134.685** hab. |
| Zonas ZFD-A | **201** (794.064 hab., 12,9%) |
| Zonas ZFD-B | **109** (384.408 hab.) |
| Zonas LL (acceso adecuado) | **402** |
| Zonas sin patrón (NS) | **924** |
| Zonas LISA HH totales | **315** |
| % zonas HH con IDH > 0 | **98,4%** (310/315) |
| Correlación IDS–IFO | **r = −0,491** (p < 0,001) |
| Moran's I | **0,3776** (p = 0,001) |
| IDH medio en HH | **+0,173** |
| IDH medio en LL | **−0,139** |
| Coeficientes OLS | β₀ = 0,9640 · β₁ = −1,0213 |
| Clústeres ZFD | **23** (top 3 = 64% de la población ZFD) |
| Maipú (mayor ZFD) | 81 zonas ZFD-A · 311.726 personas |
| Establecimientos incluidos | ~534 públicos Gran Santiago |

---

## 5. Preguntas del evaluador — y cómo responderlas

### Preguntas conceptuales (de un par que no conoce el tema)

**P: ¿Qué es una "zona de falla doble" en palabras simples?**  
R: Es una zona donde se juntan dos problemas: la gente es más vulnerable (necesita más el sistema de salud público) Y el sistema le da menos acceso del que debería. El sistema falla justo donde más se necesita.

**P: ¿Por qué usaron zonas censales y no comunas?**  
R: Porque agregar a nivel comunal oculta la heterogeneidad interna. Maipú tiene zonas con acceso adecuado y zonas con exclusión severa — si promedias la comuna entera, las malas quedan invisibles.

**P: ¿Qué es el 2SFCA?**  
R: Es un método para medir accesibilidad que considera tanto la distancia entre la gente y los establecimientos, como cuánta gente compite por cada establecimiento. Es como medir "cuánto hospital te toca" considerando que otros también lo usan.

---

### Preguntas técnicas difíciles (evaluador/profesor)

---

**P1: "¿Por qué IDH > 0 implica exclusión? Expliquen la lógica de la regresión."**

R: La regresión OLS modela la tendencia promedio del sistema: en el Gran Santiago, a mayor vulnerabilidad (IDS), mayor fricción de acceso (IFO). Esa recta describe cómo el sistema *ya está fallando sistemáticamente*. IDH > 0 significa que una zona está *por encima de esa recta*: el sistema le da aún menos acceso del que ya de por sí le corresponde según su propio patrón regresivo. Es una falla sobre la falla: la zona no solo está en la parte mala de la recta, sino que el sistema ni siquiera cumple con lo que predice su propia tendencia.

---

**P2: "¿Cuál es el R² de la OLS? ¿Por qué un modelo lineal si IDS e IFO están acotados en [0,1]?"**

R: El modelo OLS es un instrumento de residualización, no de predicción. Usamos la recta para obtener el residuo (IDH), no para predecir IFO. En ese uso, el R² importa menos que la interpretabilidad del residuo. El hecho de que r(IDS, IFO) = −0,491 (p < 0,001) confirma que la relación lineal captura una señal real. Para [0,1] acotados podría usarse un modelo beta o GLM, pero la linealidad es suficiente para el propósito de detectar desviaciones.  
*(Si preguntan el R²: r² = (−0,491)² ≈ 0,241 — el modelo explica ~24% de la varianza de IFO).*

---

**P3: "Moran's I = 0,3776. ¿Es alto o bajo? ¿Cómo lo interpretan?"**

R: En ciencias sociales con datos urbanos, Moran's I entre 0,3–0,5 es moderado-alto. La escala va de −1 (dispersión perfecta) a +1 (concentración perfecta). El valor de 0 indicaría distribución aleatoria. Con p = 0,001 en 999 permutaciones, la probabilidad de obtener ese I por azar es 0,1%. La conclusión es robusta: la exclusión forma clústeres espaciales no aleatorios.

---

**P4: "¿Cómo distinguen ZFD-A de ZFD-B en la práctica? La señal IFO es la misma."**

R: Tienen la misma señal IFO alta (poco acceso público) y misma señal IDH > 0, pero la causa es diferente. ZFD-B se concentra en comunas de alto ingreso (Las Condes, Vitacura, etc.) donde el mercado privado cubre la demanda. La forma de detectarlo es geográfica y por el patrón de establecimientos: en ZFD-B hay pocos o ningún establecimiento público no porque se olvidaron de construir, sino porque la planificación nunca los priorizó ahí. Para un habitante FONASA que viviera en ZFD-B, el acceso también sería malo — el modelo lo capta correctamente. La distinción importa para la política: ZFD-A necesita nuevos CESFAM; ZFD-B no es prioridad pública porque la demanda real la atiende el privado.

---

**P5: "¿Por qué usaron distancia euclidiana y no red vial?"**

R: La literatura 2SFCA valida distancia euclidiana en contextos urbanos densos (Wood et al., 2023; Contreras et al., 2020). En el Gran Santiago, la red vial es densa y relativamente homogénea en áreas residenciales, por lo que la distancia euclidiana aproxima bien la accesibilidad real. Además, el ruteo por red vial requiere datos de tiempos de viaje actualizados que no estaban disponibles para todas las zonas. Es una limitación declarada en el poster.

---

**P6: "¿Qué mide exactamente IFO? ¿Capacidad instalada o utilización real?"**

R: **Capacidad instalada, no utilización real.** Esto es una limitación explícita del modelo. IFO dice "cuánta oferta potencial tiene accesible esta zona" — no dice si la gente efectivamente va. No capta listas de espera, calidad de atención, ni barreras culturales o informacionales. Es por eso que se llama *fricción* de oferta, no demanda satisfecha.

---

**P7: "¿Cómo calcularon el numerador Sj del 2SFCA para hospitales y para primaria?"**

R (hospitales): Usamos camas disponibles del REM20 (DEIS), que registra camas ocupadas y disponibles por servicio.  
R (primaria/urgencia): Como no hay un equivalente a camas, usamos el inverso de la actividad bruta: `1/(actividad_bruta + 1)`. A mayor actividad, menor "capacidad libre disponible". Los datos vienen de las Series A y P del DEIS 2024.

---

**P8: "¿Validaron el modelo contra algún dato externo como morbimortalidad o listas de espera?"**

R: No en esta versión. La validación externa con datos de morbimortalidad, egresos hospitalarios o listas de espera por establecimiento es el paso siguiente del proyecto. El modelo actual predice accesibilidad potencial — un proxy validado en la literatura para detectar inequidades de acceso. Que el 98,4% de los clústeres LISA HH presenten IDH > 0 es consistencia interna fuerte, pero no reemplaza la validación con outcomes de salud.

---

**P9: "¿Por qué Maipú concentra tanto ZFD-A?"**

R: Maipú es una de las comunas con mayor crecimiento demográfico del Gran Santiago en las últimas dos décadas. La red pública (CESFAM, hospitales) se planificó para una población menor y no se amplió proporcionalmente. El resultado es el déficit de oferta relativa más grande de la región: 81 zonas ZFD-A, 311.726 personas. Es el ejemplo más claro de que el crecimiento urbano no fue compensado por la red pública.

---

**P10: "El simulador asume que un nuevo CESFAM reduce IFO en radio lineal. ¿Eso está calibrado empíricamente?"**

R: El parámetro `reduccion_max = 0.10` es la reducción máxima de IFO que el 2SFCA produce al agregar un establecimiento primario en el centroide de una zona ZFD-A típica. El decay lineal `ΔIFO = 0.10 × max(0, 1 − dist/radio)` modela que el impacto decae con la distancia hasta cero en el borde del radio. No es una predicción operacional: es una proyección de accesibilidad bajo supuestos declarados (sin redistribución de inscripciones, capacidad promedio de red pública).

---

## 6. Los 3 puntos más fuertes — defiéndanlos con confianza

1. **El IDH como residuo OLS es elegante:** No inventaron un umbral arbitrario. Usaron la propia tendencia del sistema para definir quién está por debajo de lo que el sistema mismo predice. Eso hace la definición de ZFD internamente consistente.

2. **El 98,4% de zonas HH con IDH > 0 es empíricamente poderoso:** Casi no hay excepciones. Si la correlación fuera espuria, esperarías ~50% de las zonas HH con IDH > 0. Tener 310/315 implica que la autocorrelación espacial y el desacoplamiento homeostático están capturando el mismo fenómeno desde dos ángulos independientes.

3. **El modelo sabe sus límites (ZFD-B):** La distinción ZFD-A / ZFD-B demuestra que el modelo entiende su propia frontera. Recomendar un CESFAM en Las Condes sería un error de política — el modelo no lo hace porque lo excluye al clasificarlo como sustitución privada, no como exclusión periférica.

---

## 7. Los 3 puntos más vulnerables — prepárense para defenderlos

1. **Datos de oferta desactualizados o imprecisos:** Los datos de capacidad (camas, actividad bruta) son de 2024 pero pueden tener inconsistencias entre establecimientos. Si preguntan, reconózcanlo: "usamos los mejores datos públicos disponibles; la cobertura fue 515/534 establecimientos (96,4%); los 19 sin dato recibieron la mediana de su tipo."

2. **Distancia euclidiana vs. red vial:** Si preguntan, no lo nieguen — es una limitación real. Pero tengan la justificación lista: la literatura lo valida en contextos urbanos densos, y el error sistemático en Gran Santiago es bajo porque la grilla urbana es relativamente regular.

3. **IFO mide capacidad, no uso:** Si un evaluador dice "¿cómo saben que esa gente realmente tiene problemas para acceder?", respondan: "el modelo captura la barrera estructural (oferta instalada), no la experiencia subjetiva. Es una metodología estándar en geografía de la salud. La validación con datos de uso real es el paso siguiente."

---

## 8. Cómo mostrar el simulador (flujo recomendado)

```
1. Escanear QR / abrir la app
2. Ir a "SIMULADOR"
3. Seleccionar: Comuna = Maipú (default)
   Tipo = CESFAM (primaria, radio 1.5 km)
4. Mostrar métricas: 81 zonas ZFD-A en radio, X rescatadas
5. Tab "Situación actual" → mapa rojo (exclusión concentrada)
6. Tab "Con intervención" → zonas rescatadas en verde
7. Cambiar a Hospital, radio 5 km → impacto mayor
8. Cambiar a Puente Alto → 36 ZFD, segundo foco más afectado
```

**Punto clave para el evaluador:** "El simulador no predice qué pasará — proyecta el efecto potencial de accesibilidad bajo supuestos declarados. El valor está en identificar *dónde* colocar un establecimiento tendría mayor impacto, no en cuantificar exactamente cuánto."

---

## 9. Arquitectura técnica (si preguntan)

- **Lenguaje:** Python
- **App:** Streamlit (Community Cloud, 1 GB RAM)
- **Datos:** GeoParquet (geometrías simplificadas ~44 m de precisión)
- **Mapas:** Folium (CartoDB DarkMatter), GeoJson por tipo
- **Simulador:** distance-decay lineal sobre GeoDataFrame en memoria
- **Análisis espacial:** GeoPandas, PySAL (LISA), scipy, statsmodels (OLS)
- **Repo:** github.com/fernandoureta/simulador-zfd

---

## 10. Frases para recordar (elevator pitch)

> *"Encontramos que el 19,2% del Gran Santiago vive en zonas donde el sistema de salud pública falla exactamente donde más se necesita. No es un accidente — es un patrón espacialmente sistemático que los datos confirman con Moran's I de 0,38 y una correlación de −0,49 entre vulnerabilidad y acceso."*

> *"Una zona de falla doble no es solo pobre: es una zona donde el sistema entrega menos acceso del que su propia tendencia predice. Es una falla sobre la falla."*

> *"Maipú tiene 81 de estas zonas. 311.000 personas. Un CESFAM nuevo en el centroide más afectado cubre aproximadamente [X] zonas según el simulador."*

---

## 11. Glosario

### Variables y siglas del estudio

| Término | Significado |
|---|---|
| **IDS** | Índice de Demanda Social. Mide la vulnerabilidad social de una zona censal en una escala [0,1]. Alto = más vulnerable. |
| **IFO v2** | Índice de Fricción de Oferta. Mide la dificultad de acceso a la red pública de salud desde una zona. Alto = peor acceso. |
| **IPSS v2** | Índice de Posición en el Sistema de Salud. Producto IDS × IFO: presión compuesta alta solo cuando ambas dimensiones fallan. |
| **IDH** | Índice de Desacoplamiento Homeostático. Residuo de la regresión OLS (IFO_real − IFO_esperado). Positivo = el sistema entrega menos de lo que predice su propia tendencia. |
| **ZFD** | Zona de Falla Doble. Zona censal donde coinciden clúster LISA HH e IDH > 0. |
| **ZFD-A** | Subtipo de ZFD en comunas periféricas. Exclusión por crecimiento urbano no compensado. 201 zonas, 794.064 hab. |
| **ZFD-B** | Subtipo de ZFD en comunas de alto ingreso. El sistema público está ausente porque la población usa ISAPRE. 109 zonas, 384.408 hab. |
| **LISA** | Local Indicators of Spatial Association. Estadístico que detecta clústeres espaciales locales (zonas similares rodeadas de zonas similares). |
| **HH** | High-High en LISA. Zona con IDS alto rodeada de vecinos con IDS alto — clúster de vulnerabilidad concentrada. |
| **LL** | Low-Low en LISA. Zona con IDS bajo rodeada de vecinos con IDS bajo — clúster de acceso adecuado. |
| **NS** | Not Significant. Zona sin patrón espacial estadísticamente relevante en LISA. |
| **OLS** | Mínimos Cuadrados Ordinarios (Ordinary Least Squares). Regresión lineal que busca la recta que mejor ajusta la nube de puntos. Aquí se usa para predecir IFO a partir de IDS y obtener el residuo (IDH). |
| **R²** | Coeficiente de determinación. Proporción de la varianza de la variable dependiente explicada por el modelo. R² = 0,241 significa que el modelo OLS explica el 24,1% de la varianza de IFO. |
| **r** | Correlación de Pearson. Mide la fuerza y dirección de la relación lineal entre dos variables. Va de −1 a +1. r = −0,491 indica correlación negativa moderada-alta. |
| **Moran's I** | Estadístico global de autocorrelación espacial. Va de −1 (dispersión) a +1 (concentración). 0 = distribución aleatoria. I = 0,3776 indica clusterización moderada-alta. |
| **p-valor** | Probabilidad de obtener el resultado observado si la hipótesis nula fuera verdadera. p = 0,001 significa que hay 0,1% de probabilidad de que el patrón se deba al azar. |
| **β₀, β₁** | Coeficientes de la regresión OLS. β₀ = 0,9640 (intercepto); β₁ = −1,0213 (pendiente). Indican que por cada unidad de aumento en IDS, IFO esperado baja 1,0213 puntos. |
| **B0, B1** | Mismos coeficientes OLS escritos en código. Nunca se recalculan en la app — están "congelados" en los valores calibrados con las 1.636 zonas. |
| **decay** | Decaimiento con la distancia (distance-decay). En el simulador: la reducción de IFO es máxima en el centro del radio y cae a cero en el borde. |
| **radio** | Radio de captación de un establecimiento. La distancia máxima desde la cual una zona "ve" a ese establecimiento en el cálculo 2SFCA. |
| **red_max / reduccion_max** | Reducción máxima de IFO que produce un nuevo establecimiento a distancia cero. CESFAM: 0,10; Hospital: 0,15; SAPU: 0,08. |
| **comp_zfd** | Componente conexa ZFD. Número de clúster al que pertenece la zona (clústeres contiguos de zonas ZFD). Hay 23 en total. |

---

### Conceptos metodológicos

| Término | Qué significa en este contexto |
|---|---|
| **2SFCA** | Two-Step Floating Catchment Area. Método de accesibilidad espacial en dos pasos: primero calcula cuánta "capacidad por persona" tiene cada establecimiento dentro de su radio; luego suma esa capacidad para cada zona dentro del radio de los establecimientos cercanos. |
| **Zona censal** | Unidad mínima del Censo INE. El Gran Santiago tiene 1.636 zonas, con entre 100 y 10.000 personas cada una. Más fina que la comuna: una comuna puede tener decenas de zonas con realidades muy distintas. |
| **Autocorrelación espacial** | Fenómeno en que los valores de una variable en zonas cercanas tienden a parecerse más entre sí que al azar. Si zonas vulnerables se agrupan con zonas vulnerables, hay autocorrelación positiva. |
| **Clúster espacial** | Grupo de zonas contiguas con valores similares y estadísticamente significativos. Un clúster HH es un conjunto de zonas de alta vulnerabilidad rodeadas de otras de alta vulnerabilidad. |
| **Homeostasis** | En sistemas biológicos, la capacidad de autorregularse para mantener equilibrio. Aquí se usa como metáfora: un sistema de salud "homeostático" compensaría la alta vulnerabilidad con mayor oferta. El IDH mide si el sistema está o no en homeostasis. |
| **Desacoplamiento** | Ruptura de la relación esperada entre dos variables. IDH positivo indica que la oferta (IFO) se "desacopló" de la vulnerabilidad (IDS): el sistema debería dar más acceso donde hay más vulnerabilidad, y no lo hace. |
| **Residuo** | Diferencia entre el valor real de una variable y el valor que predice el modelo de regresión. IDH es el residuo de la OLS: qué tanto se aleja el IFO real de la línea de tendencia. |
| **Percentil / min-max** | Formas de normalizar una variable a una escala común [0,1]. Min-max: (valor − mínimo) / (máximo − mínimo). Se usa para calcular IDS y para escalar el acceso en la construcción de IFO. |
| **Contigüidad Queen orden 2** | Definición de "vecino" en el análisis LISA. Orden 1: comparten borde o vértice. Orden 2: también incluye los vecinos de los vecinos. Se usa para suavizar el análisis en zonas pequeñas. |
| **999 permutaciones** | Número de rearreglos aleatorios de los datos usados para calcular el p-valor del Moran's I. El valor observado se compara con la distribución de 999 versiones aleatorias. Si solo 1 de 999 supera el valor real, p ≈ 0,001. |
| **Accesibilidad potencial** | Lo que el modelo mide: la oferta de salud pública disponible en el entorno de una zona, sin considerar si la gente realmente va o no. Contraste con accesibilidad real (utilización efectiva). |
| **Sustitución privada** | Fenómeno en que la red pública está ausente en un área porque la demanda es cubierta por el sector privado (ISAPRE). Explica las ZFD-B en comunas de alto ingreso. |
| **GeoParquet** | Formato de archivo que almacena datos geoespaciales (geometrías de polígonos) junto a atributos tabulares de forma compacta. Es lo que usa la app para cargar las 1.636 zonas con sus índices. |
| **CESFAM** | Centro de Salud Familiar. Establecimiento de atención primaria de la red pública (radio 1.500 m en el modelo). |
| **SAPU / SAR** | Servicio de Atención Primaria de Urgencia / Servicio de Atención de Urgencia. Urgencias ambulatorias de la red pública (radio 2.000 m). |
| **REM20** | Registro de Estadísticas Mensuales, formulario 20. Fuente DEIS MINSAL que reporta camas disponibles en hospitales. |
| **Series A / Serie P** | Estadísticas mensuales DEIS. Serie A: actividad (consultas, atenciones). Serie P: población bajo control. Se usan para estimar la producción de los CESFAM y SAPU. |
| **FONASA** | Fondo Nacional de Salud. Sistema de aseguramiento público de salud en Chile (~80% de la población). |
| **ISAPRE** | Institución de Salud Previsional. Aseguradora privada de salud. Las comunas ZFD-B tienen alta concentración de cotizantes ISAPRE. |
| **DEIS** | Departamento de Estadísticas e Información de Salud. Dependiente del Ministerio de Salud (MINSAL). Publica los datos de establecimientos y producción. |

---

## Referencias

1. Luo & Wang (2003) — 2SFCA original. *Environment and Planning B*
2. Anselin (1995) — LISA. *Geographical Analysis*
3. Contreras et al. (2020) — Santiago RMS, IDS, radio 1.5 km
4. Wood et al. (2023) — distancia euclidiana válida en fit-for-purpose. *Applied Network Science*
5. Fuentes DEIS MINSAL (2024) — REM20, Series A/P
6. INE Censo (2024) — geometría y variables censales

---

*Simulador online: https://simulador-zfd-jucq32bgktmgw82xeglshx.streamlit.app/*  
*Repo: github.com/fernandoureta/simulador-zfd*
