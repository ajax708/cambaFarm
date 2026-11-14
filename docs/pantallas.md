# [NOMBRE]: definición de pantallas

> NASA Space Apps 2026 · Reto *Field Shift: Adapting Farms with NASA Data* · Piloto: Santa Cruz, Bolivia (llanos).
> Documento de diseño (no toca código). El mockup visual está en `docs/mockup.html`. Todos los números del mockup salen de la API real (`POST /simulate` con valores por defecto: −17,40, −63,20, rotación actual A).

---

## 0. Identidad del producto

**[NOMBRE]** le muestra al productor de soya de Santa Cruz cuánta plata está dejando en la mesa en invierno. Hoy el lote queda en barbecho de marzo a noviembre: sin ingreso y con el suelo desnudo frente al viento. La app repasa 45 años de clima diario de la NASA (1981 a hoy) **sobre su propio lote** y responde una sola pregunta: *¿qué cultivo de invierno me habría pagado, y cuántas veces habría fallado?* Habla como un agrónomo de confianza: claro, sin jerga, honesto con lo que no sabe, y siempre compara contra **lo que el productor hace hoy**. Gancho: **"Gana plata en invierno"** (EN: *"Earn money in winter"*).

### Candidatos de nombre (en inglés, tono agro; la decisión es del equipo)

| Nombre | Por qué funciona |
|---|---|
| **Winterfield** | Dice el gancho entero en una palabra: el campo en invierno. Se pronuncia fácil en español. |
| **Second Season** | La promesa concreta: una segunda campaña por año. Funciona igual de bien como frase para los jueces. |
| **Furrow** | "Surco". Corto, de tierra, sin sonar a tecnología. Sirve como marca y como ícono. |
| **Tilth** | Palabra agronómica antigua para "suelo en buen estado". Une la plata con el cuidado del suelo. |
| **Field Almanac** | El almanaque es la herramienta clásica del agricultor para leer el clima; aquí con 45 años de datos de la NASA. |
| **Groundcover** | "Cobertura del suelo": nombra el beneficio que más se ve en la app (menos días de suelo desnudo). |
| **Seedtime** | "Tiempo de siembra": suena a campo y a calendario, y apunta a la decisión que se toma con la app. |
| **Sod & Sky** | Tierra y cielo: la granja leída desde el espacio, sin decir "tech". Tiene un guiño a la NASA sin nombrarla. |

---

## 1. Recorrido del usuario

### 1.1 Camino feliz (productor, en el celular)

```
Gancho ──► Tu campo (2 preguntas) ──► Repaso de 45 inviernos ──► Veredicto
                                                                   │
                         Ajustar (opcional) ◄── Esta campaña ◄── ¿Por qué? (pruebas NASA)
```

1. Abre el enlace (WhatsApp, por ejemplo). Lee "Gana plata en invierno" y toca **Ver mi campo**.
2. Marca su lote en el mapa (punto o polígono) y elige qué siembra hoy (una opción). Ve lo que la app encontró sola (suelo, altura, pendiente, clima) y toca **Repasar 45 inviernos**.
3. Ve cómo le habría ido a la mejor opción de invierno año por año, frente a dejar el campo descansar.
4. Lee **una** recomendación grande y 2 o 3 alternativas.
5. Si duda, toca **¿Por qué?** y ve las pruebas una por una.
6. Ve qué dice El Niño o La Niña de **esta** campaña, en palabras simples.
7. Solo si quiere, ajusta: prioridad (3 perfiles), cultivos que no puede sembrar, precios, "¿y si el clima cambia?".
8. Toca **Enviar a mi técnico** y comparte un resumen (enlace o imagen).

### 1.2 Guion de la demo (≤ 30 s) mapeado a pantallas

Recomendación: grabar con la interfaz en **inglés** (los jueces) y mostrar 1 s el botón ES ↔ EN en la escena 1 para demostrar que es bilingüe. Si se entrega en diapositivas, cada escena es una diapositiva (6 de 7; la 7.ª es "Datos NASA usados").

| # | Tiempo | Pantalla | Qué se ve | Texto en pantalla / voz (EN) |
|---|---|---|---|---|
| 1 | 0–4 s | Gancho | Titular, cambio ES→EN | "Santa Cruz soy farms sit bare for 9 months a year. What if winter paid?" |
| 2 | 4–8 s | Tu campo | Dedo dibuja el lote, toca "Soy, then fallow" | "Two questions. NASA data does the rest." |
| 3 | 8–15 s | Repaso | Las 45 barras crecen de 1981 a 2025; aparece la ✕ de 2016-17 | "We replay 45 years of NASA POWER climate on this exact field." |
| 4 | 15–21 s | Veredicto | Tarjeta: Soya → sorgo, +USD 323/ha/año | "+USD 323 per hectare a year. 174 fewer bare-soil days. Failed 1 winter in 45." |
| 5 | 21–26 s | ¿Por qué? | Calendario 9 meses → 3 meses desnudo; destello Landsat/SMAP | "Satellites confirm the field is bare May to October." |
| 6 | 26–30 s | Esta campaña | Tarjeta El Niño muy fuerte | "And this season's El Niño? On this field, those years were good ones." + logo |

---

## 2. Reglas de diseño que aplican a todas las pantallas

1. **Resultado primero, controles después.** Nada de formularios largos antes de ver valor.
2. **Una conclusión por bloque.** El titular de cada bloque *es* la conclusión; el gráfico la respalda.
3. **Siempre contra "lo que haces hoy".** Toda cifra se expresa como diferencia frente a la rotación actual (color tierra/terracota = hoy).
4. **Números en palabras.** "Falló 1 de 45 inviernos", "1 de cada 10 años"; nunca "2,2 %", "p10", "score", "ONI".
5. **Detalle a pedido.** Tablas, causas por año y metodología detrás de "Ver como tabla", "Ver detalle".
6. **Fuentes NASA visibles pero discretas.** Una línea `🛰 NASA POWER · …` al pie de cada prueba, en tinta suave.
7. **Honestidad.** Cada recomendación lleva un "Ojo:" (riesgo principal) y al final "Lo que no sabemos".

### Regla de "números en palabras" (para implementar en un helper)

| Situación | Texto |
|---|---|
| Conteo sobre los años simulados (eventos raros) | "1 de 45 inviernos", "ninguno de 45" |
| Proporción p < 0,5 | "1 de cada N" con N = round(1/p) (p = 0,111 → "1 de cada 9") |
| Proporción p ≥ 0,5 | "X de cada 10" con X = round(p·10) |
| p = 0 | "nunca", "ningún año" |
| Plata | "+USD 323 por hectárea al año"; miles con punto (es) / coma (en) |
| Días | "174 días menos de suelo desnudo"; si > 60, agregar meses ("9 meses") |

---

## 3. Pantallas / secciones

Toda la app es **una sola página con scroll** (la historia). En escritorio la columna de lectura mide máximo 760 px y algunas secciones se abren a 1080 px (campo, veredicto, esta campaña). Barra superior fija: wordmark `[NOMBRE]` + selector ES | EN.

### 3.1 Gancho

- **Objetivo:** que el productor entienda en 5 segundos para qué sirve la app y quiera probar.
- **Pregunta que responde:** *"¿Esto es para mí? ¿Qué gano?"*
- **Jerarquía:** titular → bajada → dato que duele (9 meses desnudo) → botón → línea de fuentes.

| Elemento | ES | EN | Fuente de datos |
|---|---|---|---|
| Titular | Gana plata en invierno. | Earn money in winter. | fijo |
| Bajada | Después de la soya, tu campo queda vacío hasta noviembre. Repasamos 45 años de clima de la NASA en tu lote para mostrarte qué cultivo de invierno habría pagado, y cuántas veces habría fallado. | After soybean, your field sits empty until November. We replay 45 years of NASA climate on your field to show which winter crop would have paid off, and how often it would have failed. | fijo; "45" = años de `period` |
| Dato | **9 meses** al año queda con el suelo desnudo un lote de soya con barbecho en Santa Cruz: sin ingreso y expuesto al viento. | **9 months** a year a soy-then-fallow field in Santa Cruz sits bare: no income, exposed to wind. | precalculado con el punto piloto: meses con `cover_by_month` < 0,3 de la estrategia A |
| Botón | Ver mi campo | See my field | — |
| Fuentes | Con datos de NASA POWER, Landsat, SMAP y GPM · gratis · 2 preguntas | With NASA POWER, Landsat, SMAP and GPM data · free · 2 questions | fijo |

- **Interacción:** el botón hace scroll a "Tu campo". Si el usuario vuelve (campo guardado en localStorage), el botón dice "Ver mi campo de nuevo" y salta directo al veredicto.
- **Estados:** no tiene (estático).
- **Móvil:** titular 40–44 px, todo en una columna, el botón visible sin scroll en 375×667. **Escritorio:** titular hasta 72 px, ilustración de brote a la derecha.

```
┌───────────────────────────────┐
│ 🌱 [NOMBRE]           [ES|EN] │
├───────────────────────────────┤
│ Gana plata en                 │
│ INVIERNO.                     │
│ Después de la soya, tu campo… │
│ ┌───────────────────────────┐ │
│ │ 9 meses │ al año queda con│ │
│ │         │ suelo desnudo…  │ │
│ └───────────────────────────┘ │
│ ( Ver mi campo → )            │
│ 🛰 NASA POWER, Landsat, SMAP… │
└───────────────────────────────┘
```

### 3.2 Tu campo (2 preguntas)

- **Objetivo:** ubicar el lote y saber la rotación actual. Nada más.
- **Pregunta:** *"¿Dónde está y qué hago hoy?"*
- **Jerarquía:** Pregunta 1 (mapa) → Pregunta 2 (opciones) → "Encontramos esto de tu campo" (automático, editable) → botón.

| Elemento | ES | EN | API |
|---|---|---|---|
| Título | Dos preguntas y listo. | Two questions, that's it. | — |
| Bajada | El resto (suelo, altura, pendiente, clima) lo buscamos nosotros. | We look up the rest (soil, elevation, slope, climate). | — |
| P1 | ¿Dónde está tu campo? | Where is your field? | `lat`, `lon`, `polygon` |
| Herramientas | Marcar punto · Dibujar lote · Mi ubicación | Drop a pin · Draw field · My location | geolocalización del navegador |
| Ayuda mapa | Toca las esquinas de tu lote. Puedes moverlas después. | Tap the corners of your field. You can move them later. | — |
| Área | ≈ 120 ha | ≈ 120 ha | **nuevo** `point.area_ha` (o calcular en el front) |
| P2 | ¿Qué siembras hoy? | What do you grow today? | `current` |
| Opciones | Soya en verano y lo dejo descansar en invierno (*Lo más común en Santa Cruz*) · Soya y trigo en invierno · Soya y sorgo o girasol en invierno · Otra cosa | Soybean in summer, fallow in winter · Soybean then wheat · Soybean then sorghum or sunflower · Something else | A · B · C (o D si elige girasol en un segundo toque) · A por defecto y se muestran todas |
| Automático | Encontramos esto de tu campo: ✓ Suelo franco arcilloso (SoilGrids) ✓ 314 m de altura · terreno plano (1 %) ✓ Clima diario 1981–2026 (NASA POWER) | We found this about your field: … | `point.soil` + `soil_source`, `point.field_elevation_m`, `point.slope_pct`, `period.start/end` |
| Enlace | ¿Algo no está bien? Corrígelo | Something wrong? Fix it | abre "Ajustar → Mi campo" (suelo manual) |
| Botón | Repasar 45 inviernos | Replay 45 winters | dispara `POST /simulate` y luego `POST /satellite` |

- **Interacciones:** por defecto el mapa centra en el piloto (−17,40, −63,20) y viene con un punto marcado, así que el botón funciona sin tocar nada (útil para la demo). La opción A viene preseleccionada. "Mi ubicación" pide permiso al GPS.
- **Pendiente:** si llega `warnings: ["slope_default"]`, mostrar "terreno plano (supuesto)" en vez de "(1 %)".
- **Estados:**
  - *Cargando (primera vez ≈ 13 s por SoilGrids):* el botón pasa a "Repasando…" y aparece una lista de pasos con check: "✓ Clima diario 1981–2026 (NASA POWER)", "◌ Tipo de suelo de tu lote (SoilGrids)", "Simulando 6 rotaciones, 45 campañas". Copy: *"Estamos repasando 45 años de clima en tu campo…"* / *"Replaying 45 years of climate on your field…"*. Si pasa 8 s: *"La primera vez tarda un poco más: estamos buscando el suelo de tu lote."*
  - *SoilGrids no responde* (`warnings: soilgrids_unavailable`): la fila dice "⚠ Suelo supuesto: franco arcillo arenoso. Elige el tuyo" con enlace.
  - *Error NASA POWER (502):* *"No pudimos conectarnos con NASA POWER. Tu campo quedó guardado: vuelve a intentar en un minuto."* + botón "Intentar de nuevo".
  - *Fuera de la región piloto:* aviso suave: *"Calibramos los cultivos para Santa Cruz. En otras zonas, tómalo como referencia."*
- **Móvil:** mapa arriba (4:3, ancho completo), opciones como tarjetas grandes (≥ 56 px de alto). **Escritorio:** mapa y preguntas lado a lado (1,2 : 1).

```
┌───────────────────────────────┐
│ ① TU CAMPO                    │
│ Dos preguntas y listo.        │
│ ┌───────────────────────────┐ │
│ │¿Dónde está tu campo?      │ │
│ │[Punto][Dibujar][Mi ubic.] │ │
│ │  ░░░░┌──────┐░░░░        │ │
│ │  ░░░░│120 ha│░░░░  mapa   │ │
│ │  ░░░░└──────┘░░░░         │ │
│ │ 📍 Toca las esquinas…      │ │
│ └───────────────────────────┘ │
│ ┌───────────────────────────┐ │
│ │¿Qué siembras hoy?         │ │
│ │ (●) Soya y descanso inv.  │ │
│ │ ( ) Soya y trigo          │ │
│ │ ( ) Soya y sorgo/girasol  │ │
│ │ ( ) Otra cosa             │ │
│ │ Encontramos: ✓suelo ✓alt. │ │
│ └───────────────────────────┘ │
│ ( Repasar 45 inviernos → )    │
└───────────────────────────────┘
```

### 3.3 El repaso: 45 inviernos en tu campo

- **Objetivo:** el momento "wow": ver que la opción de invierno habría pagado casi todos los años, y ver honestamente el año que falló.
- **Pregunta:** *"¿Cómo me habría ido de verdad, año por año?"*
- **Jerarquía:** titular condicional → gráfico de 45 barras → 3 contadores → suma acumulada → nota del año malo.

| Elemento | ES | EN | API |
|---|---|---|---|
| Titular | Si desde 1981 hubieras sembrado **sorgo** después de la soya… | If since 1981 you had planted **sorghum** after soybean… | nombre del cultivo de invierno de la mejor estrategia |
| Bajada | Pasamos el clima real de cada año, día por día, por tu lote. Así le habría ido al sorgo de invierno, frente a dejar el campo descansar. | We ran each year's real weather, day by day, through your field… | — |
| Gráfico | Lo que dejó cada invierno · USD por hectárea | What each winter left · USD per hectare | por campaña: margen del cultivo de invierno (hoy se deriva de `phases[0].campaigns[].winter.yield` × precio − costo; **nuevo** `replay[].winter_margin`) |
| Línea de hoy | Hoy: barbecho (−25, costo de mantenerlo limpio) | Today: fallow (−25, cost of keeping it clean) | costo del barbecho (`CROPS.barbecho.cost`) |
| Marca de fallo | ✕ No se pudo sembrar (2016-17) | ✕ Could not be sown (2016-17) | `winter.class == "not_sown"` |
| Contadores | **44** inviernos buenos · **0** inviernos con pérdida · **1** no se pudo sembrar | 44 good winters · 0 losing winters · 1 not sown | conteo de `winter.class` y signo del margen (**nuevo** `winter.*`) |
| Suma | **+USD 14.559** por hectárea en 45 años, comparado con lo que haces hoy. | +USD 14,559 per hectare over 45 years, compared with what you do today. | Σ (`campaign.margin` de la opción − `campaign.margin` de la actual) (**nuevo** `winter.cumulative_gain`) |
| Nota | 2016-17: la lluvia llegó tarde, la soya se sembró a fin de diciembre y se cosechó en mayo. Ya no hubo tiempo para el sorgo; ese invierno el campo quedó como hoy. | 2016-17: rains came late, soybean was sown in late December and harvested in May, leaving no time for sorghum… | `winter.note == "previous_crop_late"` + fechas `summer.sown/harvest` |
| Fuente | 🛰 Clima: NASA POWER, 1981–2026 · precios de referencia | | `sources`, `period` |
| Enlace | Ver como tabla | See as table | tabla año / cultivo / resultado / lluvia / USD |

- **Gráfico:** barras verticales, una serie (verde = opción), un solo eje (USD/ha), línea punteada terracota para "hoy". Los años fallidos no tienen barra: llevan una ✕ roja sobre el eje (forma + color, nunca solo color). Tooltip al tocar una barra: *"2010-11: sorgo +237 USD/ha · lluvia de invierno 119 mm · La Niña"*.
- **Animación (demo):** las barras crecen de izquierda a derecha, 1981→2025, en unos 3 s; el contador de la suma sube a la par. Respetar `prefers-reduced-motion`.
- **Estados:** *cargando:* esqueleto con 45 barras grises. *Ninguna opción gana:* titular alternativo *"En tu campo, dejar descansar en invierno sigue siendo lo más seguro"* y se muestra la opción de cobertura (protege el suelo).
- **Móvil:** gráfico a ancho completo (≈ 300 px, barras de ≈ 5 px), contadores en 3 columnas. **Escritorio:** igual dentro de la columna de 760 px.

```
┌───────────────────────────────┐
│ ② 45 INVIERNOS EN TU CAMPO    │
│ Si desde 1981 hubieras        │
│ sembrado sorgo…               │
│ ┌───────────────────────────┐ │
│ │■ Sorgo  -- Hoy  ✕ No sembr│ │
│ │300┃┃┃┃┃┃┃┃┃┃┃┃┃┃┃ ┃┃┃┃┃   │ │
│ │  0┻┻┻┻┻┻┻┻┻┻┻┻┻┻┻✕┻┻┻┻┻   │ │
│ │-25- - - - - - - - - - - - │ │
│ │ 1981   2001   2021        │ │
│ │ [44 buenos][0 pérd][1 ✕]  │ │
│ │ $ +USD 14.559 en 45 años  │ │
│ └───────────────────────────┘ │
└───────────────────────────────┘
```

### 3.4 Veredicto

- **Objetivo:** una sola recomendación clara, con plata, suelo y riesgo, y alternativas para quien piensa distinto.
- **Pregunta:** *"Entonces, ¿qué siembro en invierno?"*
- **Jerarquía:** etiqueta de por qué ganó → rotación → **número grande de plata** → 3 hechos (suelo, fallos, pérdidas) → comparación con hoy → "Ojo" → botones → 3 alternativas.

| Elemento | ES | EN | API |
|---|---|---|---|
| Etiqueta | El mejor equilibrio entre plata, riesgo y suelo | Best balance of money, risk and soil | perfil activo (ver 3.7) |
| Rotación | Soya → sorgo | Soybean → sorghum | `strategies[rank==1].name` |
| Número grande | **+USD 323** más por hectárea al año que hoy | +USD 323 more per hectare per year than today | `indicators.margin` (opción) − `indicators.margin` (actual) |
| Escala | en 120 ha, unos USD 38.800 por año | on 120 ha, about USD 38,800 a year | × `area_ha` (solo si dibujó polígono) |
| Hecho suelo | **174 días menos** de suelo desnudo al año (de 264 a 90). | 174 fewer bare-soil days a year (264 → 90). | `indicators.bare_days` actual − opción |
| Hecho fallos | **Falló 1 de 45 inviernos**, y fue porque no hubo tiempo para sembrarlo. | Failed 1 winter in 45, because there was no time to sow it. | **nuevo** `winter.fail_count`, `winter.n`, causa principal |
| Hecho pérdidas | **Ningún año perdió plata** frente a dejar el campo vacío. Su peor año igual dejó +USD 183/ha. | It never lost money compared with leaving the field empty. Its worst year still made +USD 183/ha. | **nuevo** `winter.years_worse_than_current`, `winter.worst_gain` |
| Comparación | Hoy, con soya y barbecho, ganas en promedio **USD 642/ha al año**. Con sorgo en invierno, **USD 965**. | Today, with soybean and fallow, you average USD 642/ha a year. With winter sorghum, USD 965. | `indicators.margin` de ambas |
| Ojo | Antes de decidir: el mercado de sorgo es más chico. Consulta si hay comprador cerca. | Before you decide: the sorghum market is smaller. Check for a buyer nearby. | `card.risks[0]` |
| Botones | ¿Por qué sorgo? · Enviar a mi técnico | Why sorghum? · Send to my agronomist | compartir: Web Share API con resumen de texto + enlace |
| Alternativas | **Más plata:** Soya → girasol · +USD 405/ha/año · 76 días menos de suelo desnudo · Falló 1 de 45 inviernos; 1 regular por sequía · Ojo: daño por aves y precio que cambia mucho. **Lo conocido:** Soya → trigo · +USD 274 · 109 días menos · Nunca falló; 3 de 45 inviernos regulares por sequía · Ojo: brusone y heladas tardías. **Cuidar el suelo:** Soya → cobertura · −USD 60 · 159 días menos · Deja nitrógeno para la soya siguiente · Ojo: no se cosecha, es una inversión en el suelo. | Most money / The familiar one / Care for the soil … | estrategias con mayor `margin`, la más elegida localmente (trigo) y la de menor `bare_days`; sin repetir la principal |
| Enlace | Comparar las 6 opciones lado a lado | Compare all 6 options side by side | abre la tabla de comparación (degradada desde la UI actual, ver §4) |

- **Etiquetas de alternativas:** se asignan por regla, no por ranking: "Más plata" = mayor `margin`; "Lo conocido" = trigo (B); "Cuidar el suelo" = menor `bare_days` o mayor `n_balance`. Si una coincide con la principal, se salta.
- **Interacciones:** tocar una alternativa la convierte en la tarjeta principal (con animación suave) y el repaso de arriba se redibuja con ese cultivo. Así el productor puede "probar" opciones sin sliders.
- **Si la actual ya es la mejor:** *"Lo que haces hoy ya es lo mejor para tu campo"* / *"What you do today is already the best for your field"* y se muestra la mejor alternativa con su diferencia.
- **Si la opción gana menos plata (p. ej. cobertura):** el número grande va en tinta normal con signo "−USD 60" y la etiqueta cambia a "Cuida el suelo, cuesta poco".
- **Móvil:** tarjeta principal a ancho completo, alternativas apiladas. **Escritorio:** tarjeta principal ancha, alternativas en 3 columnas.

```
┌───────────────────────────────┐
│ ③ NUESTRA RECOMENDACIÓN       │
│ ╔═══════════════════════════╗ │
│ ║ ✓ Mejor equilibrio…       ║ │
│ ║ Soya → sorgo              ║ │
│ ║ +USD 323                  ║ │
│ ║ más por ha al año que hoy ║ │
│ ║ 🌱 174 días menos desnudo  ║ │
│ ║ ✕ Falló 1 de 45 inviernos ║ │
│ ║ 🛡 Ningún año perdió plata ║ │
│ ║ ▪ Hoy: USD 642 → 965      ║ │
│ ║ ⚠ Ojo: mercado más chico  ║ │
│ ║ (¿Por qué sorgo?) (Enviar)║ │
│ ╚═══════════════════════════╝ │
│ [Más plata][Lo conocido][Suelo│
└───────────────────────────────┘
```

### 3.5 ¿Por qué? (pruebas NASA, una a la vez)

- **Objetivo:** dar confianza mostrando la evidencia, un dato por tarjeta, con la fuente NASA al pie.
- **Pregunta:** *"¿Por qué debería creerte?"*
- **Jerarquía:** indicador de pasos (4 barritas) → tarjeta con titular-conclusión → gráfico simple → fuente → "Siguiente prueba".

| # | Titular ES | Titular EN | Gráfico | API |
|---|---|---|---|---|
| 1 | Hoy tu campo pasa 9 meses desnudo. Con sorgo, solo 3. | Today your field is bare 9 months a year. With sorghum, only 3. | Calendario oct→sep, 2 filas (hoy / opción); mes cubierto = bloque de color, mes desnudo (< 30 %) = rayado + contorno; total "9 meses desnudo" al final de la fila | `cover_by_month` de A y de la opción |
| 2 | En tu zona llueve lo suficiente en invierno para el sorgo. | There is enough winter rain here for sorghum. | Barras: lluvia de cada invierno (siembra→cosecha), una serie; el año más seco resaltado en tinta neutra con leyenda: "2010-11, el más seco: 119 mm, y el sorgo igual rindió 9 de cada 10 kg" | `campaigns[].winter.rain_mm`, `winter.rel` |
| 3 | El satélite confirma: tu lote queda pelado de mayo a octubre. | Satellites confirm: your field is bare from May to October. | Tira de 12 meses: verde fuerte / verde suave / rayado según verdor | `/satellite` → `bare_month_share` (y `landsat` para el detalle) |
| 4 | Esta semana tu suelo está más seco (o húmedo) que lo normal. | This week your soil is drier (wetter) than normal. | Medidor horizontal con marca "Normal" al centro + frase "18 % más seco que lo normal para noviembre" | `/satellite` → `smap_anomaly`, `smap[]` |

- Subtítulos: (1) *"Suelo sin cobertura se lo lleva el viento del invierno y pierde materia orgánica."* (2) *"La mitad de los inviernos llovieron más de 366 mm entre la siembra y la cosecha. Y el sorgo aguanta la sequía."* (4) *"Si sigue así, conviene sembrar apenas cosechas la soya, con la humedad que queda."*
- **GPM IMERG** (lluvia anual) queda como detalle dentro de la prueba 2 ("Ver lluvia medida por satélite"), no como tarjeta propia.
- **Interacción:** en móvil, carrusel con deslizamiento horizontal (scroll-snap) o tarjetas apiladas con "Siguiente prueba" que hace scroll. En escritorio, apiladas; las 2 satelitales lado a lado.
- **Estados satélite:**
  - *Cargando:* tarjetas 3 y 4 con esqueleto y la frase *"Consultando satélites… (Landsat, SMAP)"*.
  - *No disponible* (`errors` con las claves, como hoy por falta de autenticación de Earth Engine): las tarjetas 3 y 4 se reemplazan por una sola: *"Hoy no pudimos consultar los satélites (Landsat, SMAP). La recomendación no cambia: se basa en 45 años de clima de la NASA."* + "Intentar de nuevo". El indicador de pasos baja a 2.
  - *Parcial:* se muestra solo la tarjeta que llegó.
- **Nota del mockup:** las pruebas 3 y 4 llevan la etiqueta "Ejemplo ilustrativo" porque Earth Engine no estaba autenticado al capturar los datos; los números (mayo–octubre, −18 %) son de ejemplo y hay que reemplazarlos por los reales.

```
┌───────────────────────────────┐
│ ④ ¿POR QUÉ SORGO?             │
│ ▬▬▬ ─── ─── ───               │
│ ┌ PRUEBA 1 DE 4 ────────────┐ │
│ │Hoy tu campo pasa 9 meses  │ │
│ │desnudo. Con sorgo, solo 3.│ │
│ │      O N D E F M A M J J A S│
│ │Hoy   ▨ ▨ ■ ■ ■ ▨ ▨ ▨ ▨ ▨ ▨ ▨ 9│
│ │Sorgo ▨ ▨ ■ ■ ■ ■ ■ ■ ■ ■ ■ ▨ 3│
│ │🛰 NASA POWER   Siguiente → │ │
│ └───────────────────────────┘ │
└───────────────────────────────┘
```

### 3.6 Esta campaña (El Niño / La Niña)

- **Objetivo:** conectar 45 años de historia con la decisión de *este* año, sin jerga.
- **Pregunta:** *"¿Y este año, cómo viene?"*
- **Jerarquía:** titular-conclusión → tarjeta de fase (ícono + intensidad en palabras + medidor de 4 niveles) → 2 frases con lo que pasó en tu campo en años parecidos → advertencia → barras por tipo de año.

| Elemento | ES | EN | API |
|---|---|---|---|
| Titular | Viene un El Niño muy fuerte. En tu campo, eso fue buena noticia. | A very strong El Niño is coming. On your field, that has been good news. | `outlook.phase`, `outlook.oni` → intensidad; conclusión según `by_enso[phase]` vs neutral |
| Fase | El Niño · muy fuerte. El mar del Pacífico central está 2,5 °C más caliente que lo normal (agosto–octubre 2026). | El Niño · very strong. The central Pacific is 2.5 °C warmer than normal (Aug–Oct 2026). | `outlook.oni` (+2,46), `outlook.season` ("ASO" → "agosto–octubre"), `outlook.year` |
| Medidor | Débil · Moderado · Fuerte · Muy fuerte | Weak · Moderate · Strong · Very strong | |ONI| 0,5–1 / 1–1,5 / 1,5–2 / ≥ 2 |
| Frase 1 | Hubo **15 años con El Niño** desde 1981. En ninguno la soya tuvo una mala campaña en tu campo. | There were 15 El Niño years since 1981. Soybean never had a bad season on your field in any of them. | `by_enso.el_nino.n`, `bad_summer_share` de la actual |
| Frase 2 | El sorgo de invierno **no falló ninguna vez** en esos años. | Winter sorghum never failed in those years. | **nuevo** `by_enso[phase].winter_fail_share` |
| Advertencia | El Niño es una tendencia, no una promesa: cada año es distinto. Úsalo para planificar, no para apostar. | El Niño is a tendency, not a promise… | fijo |
| Gráfico | Ganancia promedio por tipo de año · USD/ha al año: grupos Con El Niño (resaltado, "este año"), Años normales, Con La Niña; 2 barras cada uno (Hoy / Sorgo) con el valor escrito al final | Average margin by year type | `by_enso[*].mean_margin` de actual y opción (685/1.005, 631/949, 612/943) |
| Fuente | 🛰 NOAA CPC (índice ONI +2,5) · NASA POWER | | `sources` |

- **Neutral:** titular *"Este año no hay El Niño ni La Niña: un año normal."* y se muestran igual las barras.
- **Si la fase fue mala para la actual:** *"Viene La Niña. En tu campo, 1 de cada 6 de esos años la soya tuvo una mala campaña"* y, si la opción reduce ese riesgo, decirlo.
- **Móvil:** tarjeta de fase arriba, barras abajo. **Escritorio:** lado a lado.

```
┌───────────────────────────────┐
│ ⑤ ESTA CAMPAÑA                │
│ Viene un El Niño muy fuerte.  │
│ ┌───────────────────────────┐ │
│ │ ☀ El Niño · muy fuerte     │ │
│ │ ████ ████ ████ ████       │ │
│ │ ✓ 15 años con El Niño: la │ │
│ │   soya nunca tuvo mala…   │ │
│ │ ✓ El sorgo no falló nunca │ │
│ └───────────────────────────┘ │
│ ┌ Con El Niño [este año] ───┐ │
│ │ Hoy   ██████████     685  │ │
│ │ Sorgo ███████████████ 1005│ │
│ └───────────────────────────┘ │
└───────────────────────────────┘
```

### 3.7 Ajustar a tu realidad (opcional, plegado)

- **Objetivo:** que el productor adapte el resultado sin entender pesos ni puntajes.
- **Pregunta:** *"¿Y si mi caso es distinto?"*
- **Jerarquía:** 4 acordeones, solo el primero abierto. Cada cambio vuelve a llamar a `/simulate` (con *debounce* de 400 ms) y actualiza veredicto y repaso; una cinta arriba dice *"Recomendación actualizada"*.

| Acordeón | ES | EN | Mapea a |
|---|---|---|---|
| Prioridad | ¿Qué es lo más importante para ti? — *Ganar más* (La opción que más plata deja en promedio) · *Menos riesgo* (Menos inviernos malos, aunque gane un poco menos) · *Cuidar el suelo* (Menos suelo desnudo, más rastrojo y nitrógeno). Sin elegir: equilibrio. | What matters most to you? — Earn more · Less risk · Care for the soil | `weights` (ver tabla abajo) o **nuevo** `profile` |
| Cultivos | Cultivos que no puedo sembrar o vender (chips tachables) | Crops I can't grow or sell | `exclude_crops` |
| Precios | Mis precios (USD/kg) — Usamos precios de referencia de Santa Cruz | My prices | `prices` (valores de `/options`) |
| Clima | ¿Y si el clima cambia? Lluvia: −20 % · −10 % · Como siempre · +10 %. Temperatura: Como siempre · +1 °C · +2 °C | What if the climate changes? | `scenario.rain_scale`, `scenario.temp_shift_c` (botones segmentados, no sliders) |
| Mi campo | Tipo de suelo (si "Automático" falló o el productor sabe más) | Soil type | `soil_texture` |

Pesos sugeridos por perfil (si el backend no implementa `profile`):

| Perfil | income | stability | soil | water | pests | Resultado hoy (punto piloto) |
|---|---|---|---|---|---|---|
| Equilibrio (por defecto, sin elegir) | 0,30 | 0,25 | 0,25 | 0,10 | 0,10 | Soya → sorgo |
| Ganar más | 0,70 | 0,15 | 0,05 | 0,05 | 0,05 | Soya → girasol |
| Menos riesgo | 0,15 | 0,50 | 0,05 | 0,25 | 0,05 | Soya → sorgo (por muy poco frente a girasol: 92 vs 91) |
| Cuidar el suelo | 0,10 | 0,10 | 0,60 | 0,10 | 0,10 | Soya → sorgo (cobertura queda 3.ª) |

Verificado contra la API en el punto piloto. Ojo: con estos pesos tres de los cuatro perfiles dan sorgo, así que en la demo el cambio de perfil solo se nota con "Ganar más". Está bien (el sorgo es robusto), pero conviene que "Menos riesgo" cuente **fallos de invierno** (§5.4) y que "Cuidar el suelo" pese más `bare_days` para que la cobertura compita.

- Cada tarjeta de perfil muestra en pequeño qué recomendaría ("Recomendaría: soya → girasol"), así el productor ve el efecto antes de tocar.

### 3.8 Cierre: "Lo que no sabemos" y fuentes

- Tarjeta con `card.gaps` (4 frases ya existentes, están bien escritas) bajo el título **"Lo que no sabemos (y tu técnico sí)"** / *"What we don't know (and your agronomist does)"*.
- Chips de fuentes: NASA POWER · NASA SRTM · Landsat 8–9 · NASA SMAP · GPM IMERG · NOAA CPC (ONI) · ISRIC SoilGrids · FAO-56/FAO-33.
- Pie: *"[NOMBRE] es una guía basada en datos. Confírmala con tu técnico y tu experiencia en el campo."*
- Detalle técnico (lat/lon, elevación de la celda POWER, lapse rate, `compute_ms`) solo dentro de "Ver detalle técnico" (para jueces).

---

## 4. Qué QUITAR o bajar de nivel respecto a la UI actual

| UI actual | Decisión |
|---|---|
| Formulario de 4 pasos al inicio, a la izquierda | **Quitar.** Quedan 2 preguntas; el resto es automático o va a "Ajustar". |
| 5 sliders de pesos ("Lo que te importa") | **Quitar.** Reemplazar por 3 perfiles plegados. |
| "Puntos" / `score` / `subscores` / ranking #1–#6 con mini barras | **Quitar de la vista.** Se usa por dentro para ordenar; el productor ve USD, días y "1 de 45". |
| Panel "Explícame" con `**Soya → sorgo** (84 puntos frente a 15…)` | **Quitar.** Lo reemplazan el veredicto y la sección "Esta campaña". |
| Tabla comparativa de 11 criterios × 6 estrategias | **Bajar** a "Comparar las 6 opciones lado a lado" (modal / página aparte), con filas en palabras y sin p10, índices ni "balance de N" crudo. |
| "Ganancia en años malos (p10)", "Exposición a erosión (índice)", "Riesgo de plagas (índice)", "Escorrentía" | **Bajar** al detalle. Erosión se comunica como "días de suelo desnudo"; plagas como una frase ("corta el ciclo de plagas de la soya"). |
| "ONI +2,5" como titular | **Bajar.** Se dice "El Niño muy fuerte"; el número va solo en la línea de fuente. |
| Timeline de 6 filas × 45 columnas (verano/invierno, 5 colores) | **Reemplazar** por el repaso de una sola opción vs hoy. La versión completa queda en "Ver como tabla". |
| Calendario de cobertura de 6 estrategias + rojo/amarillo/verde | **Reducir** a 2 filas (hoy vs opción), cubierto/desnudo con textura, no semáforo. |
| 3 gráficos satelitales con ejes técnicos (NDVI 0–1, SMAP %, IMERG anual) | **Reemplazar** por 2 tarjetas-conclusión (verdor por mes, humedad vs normal). IMERG a detalle. |
| Glosario (NDVI, evapotranspiración, anomalía…) | **Quitar.** Si se necesita un término, se explica en la misma frase. |
| Etiquetas de base "Dato NASA / Regla agronómica / Dato tuyo" en cada fila | **Bajar** a la línea de fuente de cada prueba y al detalle. Mantener la distinción en la tabla comparativa. |
| Mapa satelital Esri + Leaflet | **Mantener**, con 3 botones grandes y "Mi ubicación". |

---

## 5. Cambios de backend recomendados

Ordenados por impacto en la historia. Ninguno cambia el motor de simulación; son agregados sobre lo que ya calcula.

1. **Bloque `winter` por estrategia** (en `analysis.run_strategy`): todo el producto gira alrededor del invierno, y hoy los indicadores mezclan verano + invierno.
   ```json
   "winter": {
     "crop": "sorgo", "n": 45,
     "good": 44, "fair": 0, "bad": 0, "not_sown": 1,
     "fail_count": 1,                     // bad + not_sown  -> "Falló 1 de 45 inviernos"
     "fail_words": {"es": "1 de 45 inviernos", "en": "1 winter in 45"},
     "mean_margin": 289,                  // solo el cultivo de invierno, USD/ha
     "gain_vs_current": 323,              // margin - margin(actual)
     "cumulative_gain": 14559,            // suma de 45 años vs actual
     "years_worse_than_current": 0,
     "worst_gain": 183, "worst_label": "2014-15",
     "main_fail_cause": "previous_crop_late"
   }
   ```
2. **Serie compacta `replay`** por estrategia, para el gráfico de 45 barras, en vez de mandar `phases` completas (la respuesta pesa hoy ≈ 335 KB):
   `[{label, campaign, winter_crop, winter_class, winter_cause, winter_margin, winter_rain_mm, winter_rel, gain_vs_current, enso}]`. Dejar `phases` solo con `?detail=1`.
3. **`verdict` armado en el servidor:** `best_id`, `alternatives: [{id, tag: "more_money"|"familiar"|"soil"}]`, y `risk_note` (primer elemento de `card.risks`). Así el front no repite la lógica de etiquetas.
4. **Parámetro `profile`** (`balanced` | `money` | `risk` | `soil`) que mapea a pesos en el servidor. Redefinir `stability` para "Menos riesgo" agregando la **proporción de fallos de invierno** (`winter.fail_count/n`) además de `loss_share` y `margin_p10`.
5. **`point.area_ha`** calculado del polígono (fórmula del área en coordenadas proyectadas), para "en 120 ha, unos USD 38.800 por año".
6. **ENSO en palabras:** `outlook.strength` (`weak|moderate|strong|very_strong`), `outlook.months` ("agosto–octubre"), y en `by_enso[phase]` agregar `winter_fail_share`. Frases del tipo "1 de cada 6 años" generadas con el helper de números en palabras.
7. **Causa en palabras:** traducir `note`/`cause` (`previous_crop_late`, `drought`, `frost`, `heat`, `not_sown`) a frases ES/EN ("la soya se cosechó tarde y no hubo tiempo para sembrar").
8. **`explain` nuevo:** sin "puntos", sin ONI, sin "%". Una frase por bloque (veredicto, esta campaña, satélite).
9. **SoilGrids lento (≈ 13 s la primera vez):** caché por lat/lon redondeado (0,01°), timeout de 5 s con suelo por defecto + `warnings`, o un endpoint separado `POST /field` (suelo, elevación, pendiente) que se llama apenas el usuario marca el mapa, **antes** de tocar "Repasar". Así la simulación sale en ≈ 1 s.
10. **Earth Engine:** hoy `/satellite` devuelve error de autenticación en los 4 bloques (`earthengine authenticate`). Resolver antes de grabar la demo, y cachear resultados del punto piloto para la demo. Agregar `bare_months_words` ("mayo a octubre") derivado de `bare_month_share`.
11. **Revisión agronómica (importante para la credibilidad):** en el punto piloto los cultivos de invierno casi nunca fallan (sorgo 1/45, trigo 0/45 malos) y el margen del sorgo es casi constante (≈ USD 300) porque el precio es fijo y el rendimiento rara vez baja. Un jurado puede verlo como demasiado optimista. Sugerencias: variar precios por año (o mostrar un rango), revisar ventana de siembra, heladas y `ky`; y que la app diga explícitamente que los precios son fijos.

---

## 6. Dirección visual

### 6.1 Paleta (tokens)

Tierra y campo, con contraste AA para texto. Los colores de datos se validaron con el validador de paletas (daltonismo protan/deutan/tritan y separación normal) en claro y oscuro.

| Token | Claro | Oscuro | Uso |
|---|---|---|---|
| `--bg` | `#f6f1e7` (papel) | `#121611` | fondo de página |
| `--surface` | `#fffcf5` | `#1a2019` | tarjetas |
| `--surface-2` | `#efe8d8` | `#232b21` | contadores, fondos suaves |
| `--border` | `#ded4bf` | `#333c30` | bordes |
| `--ink` | `#1d2419` | `#ece6d6` | texto principal, números grandes |
| `--ink-2` | `#48513f` | `#c3bfae` | texto secundario |
| `--muted` | `#666b5b` | `#9d9c8a` | fuentes, ejes |
| `--today` | `#c2622a` (terracota) | `#d4733a` | **lo que haces hoy** / barbecho |
| `--opt` | `#00806a` (verde campo) | `#1fa287` | **opción recomendada** |
| `--water` | `#2a6f8f` | `#5ab0c8` | lluvia, humedad |
| `--accent` | `#b9821a` | `#e0ac4a` | "invierno" del titular, sol de El Niño (solo decorativo, nunca texto chico) |
| `--good` / `--warn` / `--bad` | `#2d7a3a` / `#946000` / `#b3412e` | `#5cb867` / `#e0a63a` / `#e2725e` | estados, siempre con ícono (✓ ⚠ ✕) |
| `--hero-bg` | `#1f3a2c` | `#0e1f17` | fondo del gancho |

Reglas: el texto **nunca** lleva el color de la serie (siempre tinta); el color identifica la marca al lado. Terracota vs verde pasan las pruebas de daltonismo, pero igual siempre van con etiqueta o leyenda. El modo oscuro usa `prefers-color-scheme` y también `[data-theme="dark"|"light"]` por si se agrega un botón.

### 6.2 Tipografía

- **Titulares y números grandes:** *Fraunces* (serif suave, con carácter de almanaque) 650. Tamaños: gancho 40–72 px, H2 26–36 px, número del veredicto 44–68 px.
- **Texto e interfaz:** *Source Sans 3* 400/600/700, 17 px base (el productor lee en el celular, a veces al sol). Cifras tabulares (`font-variant-numeric: tabular-nums`).
- Mínimo 14 px para cualquier texto visible; 12 px solo en ejes de gráficos.

### 6.3 Iconografía

Línea de 1,8 px, esquinas redondeadas, estilo Lucide: brote (marca), satélite (fuentes), moneda (plata), suelo con brote (cobertura), escudo (sin pérdidas), ✕ (fallo), ⚠ (ojo), ☀ (El Niño), gota (lluvia/humedad), pin (mapa), compartir. Sin emojis en la interfaz.

### 6.4 Gráficos por dato

| Dato | Forma | Detalles |
|---|---|---|
| Resultado de cada invierno (45 años) | Barras verticales, una serie, un eje USD/ha | Línea punteada terracota = hoy; ✕ roja para "no se sembró"; tooltip por barra; "Ver como tabla" |
| Suma acumulada | Número grande (no gráfico) | "+USD 14.559 en 45 años" |
| Contadores buenos / pérdida / no sembrado | 3 tarjetas de número | Sin porcentajes |
| Plata, suelo y fallos del veredicto | Número grande + 3 filas con ícono | Nada de radar ni barras de puntaje |
| Cobertura por mes | Calendario de 12 celdas × 2 filas | Cubierto = color de la serie; desnudo = rayado con contorno (textura, no solo color); total al final en texto |
| Lluvia de invierno | Barras, una serie (`--water`) | El año más seco en tinta neutra, explicado en la leyenda (no texto encima de las barras) |
| Verdor Landsat | Tira de 12 meses, 3 niveles | Rayado = pelado |
| Humedad SMAP | Medidor horizontal con marca "Normal" | Frase con el valor en palabras debajo |
| Intensidad El Niño | Medidor de 4 segmentos con etiquetas | |
| Ganancia por tipo de año | Barras horizontales agrupadas (2 por grupo) | Valor escrito al final de cada barra; grupo de "este año" resaltado con fondo + etiqueta |

Comunes: un solo eje, grilla tenue, sin doble eje, leyenda siempre presente con ≥ 2 series, extremos de barra redondeados 2–4 px, 2 px de separación, texto en tinta neutra.

---

## 7. Lista de construcción para mañana (prioridad)

### MUST (sin esto no hay demo)
- [ ] Página única con las secciones 3.1 → 3.6 en orden, con los textos de este documento (ES + EN en `i18n.js`).
- [ ] Tu campo: mapa (punto por defecto en el piloto) + 4 opciones de "¿Qué siembras hoy?" + bloque "Encontramos esto" leyendo `point`.
- [ ] Estado de carga con pasos (POWER → SoilGrids → simulación) y estado de error con "Intentar de nuevo".
- [ ] Repaso de 45 barras (derivar `winter_margin` en el front si el backend aún no lo da) + 3 contadores + suma.
- [ ] Veredicto: tarjeta grande con +USD/ha/año, días menos de suelo desnudo, "falló X de 45 inviernos", comparación con hoy, "Ojo".
- [ ] 2–3 alternativas con etiqueta por regla.
- [ ] Prueba 1 (calendario de cobertura 2 filas).
- [ ] Esta campaña: fase + intensidad en palabras + 2 frases + barras por tipo de año.
- [ ] Helper de números en palabras (§2).
- [ ] Tokens de color claro/oscuro y tipografías de §6; probar a 375 px sin scroll horizontal.
- [ ] Autenticar Earth Engine **o** ocultar las pruebas satelitales con el estado "no disponible".
- [ ] Grabar la demo de 30 s siguiendo §1.2.

### SHOULD
- [ ] Backend: bloque `winter`, `replay` compacto, `verdict`, `profile`, `area_ha` (§5, puntos 1–5).
- [ ] Pruebas 2, 3 y 4 (lluvia, Landsat, SMAP) con datos reales.
- [ ] Ajustar: 3 perfiles, cultivos excluidos, precios, clima con botones segmentados.
- [ ] Tocar una alternativa la vuelve principal y redibuja el repaso.
- [ ] Caché/timeout de SoilGrids o endpoint `/field` anticipado.
- [ ] "Lo que no sabemos" + chips de fuentes.
- [ ] Animación de barras creciendo (con `prefers-reduced-motion`).

### COULD
- [ ] "Enviar a mi técnico" (Web Share API con resumen + imagen de la tarjeta).
- [ ] "Comparar las 6 opciones" como tabla en palabras.
- [ ] Recordar el campo en `localStorage` y saltar directo al veredicto al volver.
- [ ] Botón de tema claro/oscuro manual.
- [ ] Precios variables por año / rango de incertidumbre en la plata (§5.11).
- [ ] Modo presentación (una sección por pantalla) para las 7 diapositivas.
