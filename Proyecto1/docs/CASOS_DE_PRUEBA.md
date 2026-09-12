# Casos de prueba

**HorarioScript — Proyecto 1**
Lenguajes Formales y de Programación, sección B+, segundo semestre 2026

---

## Cómo reproducir estos resultados

```bash
python pruebas_casos.py
```

Los ocho casos están escritos como pruebas automáticas con aserciones, no como
una descripción en prosa. La razón es que así el resultado documentado aquí es
verificable: cualquiera puede correr el archivo y comparar. El script devuelve
código de salida 0 si todo pasa y 1 si algo falla, con el detalle de qué
esperaba y qué obtuvo.

**Resultado de la última ejecución: 67 verificaciones, 0 fallos.**

El registro completo está en `docs/salida_casos.txt`.

---

## Resumen

| # | Caso | Archivo de entrada | Verificaciones | Estado |
|---|---|---|---|---|
| 1 | Archivo válido del enunciado | `horario_valido.hor` | 10 | ✔ |
| 2 | Los cinco tipos de error léxico y la recuperación | `horario_errores.hor` | 6 | ✔ |
| 3 | Ambigüedad HORA / ENTERO y conteo de posición | `horario_ambiguedades.hor` + fragmentos | 13 | ✔ |
| 4 | CADENA vs CODIGO vs CODIGO_MAL_FORMADO | fragmentos | 12 | ✔ |
| 5 | Choques por catedrático y por aula | `horario_choques.hor` | 6 | ✔ |
| 6 | Casos que **no** son choque | `horario_choques_borde.hor` | 7 | ✔ |
| 7 | Validaciones estructurales y de referencia | `horario_choques.hor` | 5 | ✔ |
| 8 | Reportes, niveles de carga y ocupación | `horario_completo.hor` | 8 | ✔ |

---

## Caso 1 — Archivo válido del enunciado

**Qué prueba.** Que el AFD reconoce los 12 tipos de token sobre el ejemplo
oficial del enunciado, sin reportar un solo error, y que el estructurador arma
todos los elementos declarados.

| Verificación | Esperado | Obtenido |
|---|---|---|
| Tokens reconocidos | 149 | 149 |
| Errores léxicos | 0 | 0 |
| Avisos estructurales | 0 | 0 |
| Choques | 0 | 0 |
| Tipos de token distintos | 12 | 12 |
| Cursos / catedráticos / aulas / clases | 2 / 2 / 2 / 2 | 2 / 2 / 2 / 2 |
| Secciones | `A`, `N` | `A`, `N` |

Este caso es la línea base. Si falla, algo se rompió en el motor.

---

## Caso 2 — Los cinco tipos de error léxico y la recuperación en modo pánico

**Qué prueba.** Que un archivo con varios errores los reporta **todos en una
sola pasada**, sin detenerse en el primero, y que sigue produciendo tokens
válidos después de cada uno.

`horario_errores.hor` tiene un error por línea, uno de cada tipo.

| Verificación | Esperado | Obtenido |
|---|---|---|
| Los cinco tipos de error aparecen | `CADENA_SIN_CERRAR`, `CARACTER_NO_RECONOCIDO`, `CODIGO_MAL_FORMADO`, `DIA_NO_RECONOCIDO`, `HORA_FUERA_DE_RANGO` | los cinco |
| Errores totales | 10 | 10 |
| El análisis continúa y sigue tokenizando | 132 tokens | 132 |
| El estructurador no se cae | 1 curso armado | 1 |
| Avisos que explican lo incompleto | 13 | 13 |

**La verificación que más importa de este caso** es la última:
`VALOR_PERDIDO`. Cuando el AFD descarta un valor por ser un error léxico
—por ejemplo `dia: LUNEZ`— ese lexema nunca llega como token, y un lector
ingenuo tomaría la coma siguiente como si fuera el valor del atributo,
desfasando toda la lista. Aquí se comprueba que eso no pasa: el estructurador
rechaza los delimitadores como valor y reporta `VALOR_PERDIDO` apuntando a la
tabla de errores léxicos.

---

## Caso 3 — Ambigüedad entre HORA y ENTERO, y conteo de posición

**Qué prueba.** La decisión D-02: dos dígitos seguidos de `:` solo forman una
`HORA` si vienen dos dígitos más. El lookahead **no consume**, de modo que el
autómata nunca necesita retroceder el índice.

| Entrada | Esperado | Obtenido |
|---|---|---|
| `40: 5` | ENTERO, SIMBOLO, ENTERO | ✔ |
| `07:` | ENTERO, SIMBOLO | ✔ |
| `07:00` | una sola HORA | ✔ |
| `123:45` | ENTERO, SIMBOLO, ENTERO | ✔ |
| `06:00` | HORA (límite inferior) | ✔ |
| `21:00` | HORA (límite superior) | ✔ |
| `05:59` | `HORA_FUERA_DE_RANGO` | ✔ |
| `21:01` | `HORA_FUERA_DE_RANGO` | ✔ |
| `07:75` | `HORA_FUERA_DE_RANGO` (minutos) | ✔ |

También se verifica el conteo de posición, que es lo que hace utilizable la
tabla de errores:

| Verificación | Esperado | Obtenido |
|---|---|---|
| Un tabulador desplaza la columna a 5 | columna 5 | 5 |
| Con CRLF, `CURSOS` queda en línea 2 columna 1 | (2, 1) | (2, 1) |
| Archivo completo con CRLF y tabulaciones | 0 errores | 0 |
| Última línea del archivo CRLF | 20 | 20 |

`horario_ambiguedades.hor` está guardado **deliberadamente con terminadores
CRLF** para cubrir el caso de un archivo creado en Windows. El retorno de
carro no debe contar como columna ni disparar un salto de línea extra.

---

## Caso 4 — Clasificación de literales

**Qué prueba.** La decisión D-01, que es la que resuelve la contradicción del
enunciado: presenta los códigos entre comillas (`"LFP-0796"`) pero también
define `CADENA` como todo texto entre comillas.

La regla implementada: al cerrar el literal, si el contenido **no tiene
espacios** y tiene **exactamente un guión**, se valida como código; en
cualquier otro caso es una cadena.

| Entrada | Esperado | Obtenido |
|---|---|---|
| `"LFP-0796"` | CODIGO | ✔ |
| `"BD2-0812"` | CODIGO (prefijo con dígito) | ✔ |
| `"A-101"` | CODIGO | ✔ |
| `"N"` | CADENA | ✔ |
| `"Bases de Datos 2"` | CADENA | ✔ |
| `"Redes - Avanzadas"` | CADENA (tiene guión, pero con espacios) | ✔ |
| `"MAGNA"` | CADENA (sirve como nombre de aula) | ✔ |
| `"CMP-"` | `CODIGO_MAL_FORMADO` | ✔ |
| `"RED-08A2"` | `CODIGO_MAL_FORMADO` (letras en el sufijo) | ✔ |
| `"101-A"` | `CODIGO_MAL_FORMADO` (prefijo empieza con dígito) | ✔ |
| `A-101` sin comillas | CODIGO | ✔ |
| `"abierta` | `CADENA_SIN_CERRAR` en la posición de apertura | ✔ |

El caso `"BD2-0812"` merece atención: el enunciado describe el patrón como
"letras + guión + dígitos", pero su propio archivo de ejemplo usa `BD2-0812`,
cuyo prefijo tiene un dígito. El patrón real implementado es
`L (L|D)* - D+`. Tomarlo literal habría hecho fallar el ejemplo oficial.

---

## Caso 5 — Detección de choques por catedrático y por aula

**Qué prueba.** Que dos clases se reportan en conflicto cuando coinciden en
día, se traslapan en el tiempo y comparten catedrático o aula.

| Verificación | Esperado | Obtenido |
|---|---|---|
| Choques detectados | 2 | 2 |
| Desglose por motivo | 1 solo catedrático, 1 solo aula, 0 ambos | ✔ |
| Recursos en conflicto | catedrático `DOC-001`, aula `A-101` | ✔ |
| Clases marcadas en choque | 4 (dos por choque) | 4 |
| El choque de catedrático es el LUNES | LUNES | LUNES |
| Duración del traslape del choque de aula | 40 minutos | 40 |

---

## Caso 6 — Casos que **no** son choque

**Qué prueba.** Los falsos positivos que la implementación tiene que evitar.
Es el caso más importante del proyecto, porque el error típico aquí no es que
falten choques, sino que sobren.

| Situación | Esperado | Obtenido |
|---|---|---|
| Una termina 08:40 y otra empieza 08:40, mismo catedrático | **no** es choque | 0 choques ese día |
| Mismo horario, días distintos | **no** es choque | 0 |
| Misma hora, sin recurso compartido | **no** es choque | 0 |
| Contención total (07:00–12:00 vs 09:00–10:00) | 1 choque | ✔ |
| Comparten catedrático **y** aula | 1 choque con 2 motivos | ✔ |
| Tres clases mutuamente traslapadas | 3 pares | 3 |
| Día ocupado de 06:00 a 21:00 | sin bloques libres sugeridos | ✔ |

La condición de traslape usa desigualdad **estricta** en ambos lados:

```
traslapan(a, b)  ⟺  a.inicio < b.fin  ∧  b.inicio < a.fin
```

Con `<=` en lugar de `<`, todo horario encadenado de la facultad se
reportaría como conflicto. Dos clases que comparten un instante en el borde
son continuidad, no choque.

---

## Caso 7 — Validaciones estructurales y de referencia

**Qué prueba.** Que con el flujo de tokens ya válido, el estructurador
detecta problemas de contenido. Son **avisos**, no errores léxicos, y van en
una tabla aparte.

| Verificación | Esperado | Obtenido |
|---|---|---|
| Errores léxicos (el archivo es léxicamente correcto) | 0 | 0 |
| Avisos estructurales | 5 | 5 |
| Código duplicado | 1 | 1 |
| Referencias inexistentes | 3 | 3 |
| Rango invertido | 1 | 1 |
| Una clase sin día válido se descarta | 0 clases armadas | 0 |
| Ninguna carga docente resulta negativa | 0 negativas | 0 |

Las dos últimas verificaciones cubren bugs que aparecieron durante el
desarrollo. Una clase sin día no se puede evaluar para traslape, así que se
descarta en lugar de guardarla con valores vacíos, que produciría falsos
negativos en el detector. Y una clase con rango invertido aportaba duración
negativa al reporte de carga: el catedrático `DOC-003` llegó a mostrar
**−1.8 horas** antes de excluirlas del cálculo.

---

## Caso 8 — Reportes, niveles de carga y ocupación de aulas

**Qué prueba.** Que los cuatro reportes HTML y el DOT se generan, y que los
umbrales clasifican correctamente.

`horario_completo.hor` está calibrado para que los cuatro niveles de carga
queden representados a la vez:

| Catedrático | Horas semanales | Nivel esperado | Obtenido |
|---|---|---|---|
| DOC-001 | 15.0 | ALTA | ALTA |
| DOC-002 | 8.3 | NORMAL | NORMAL |
| DOC-003 | 3.3 | BAJA | BAJA |
| DOC-004 | 78.0 | SATURADA | SATURADA |

| Verificación | Esperado | Obtenido |
|---|---|---|
| Clases programadas | 22 | 22 |
| Choques detectados | 2 | 2 |
| Aulas sobre el 80% de ocupación | solo `LAB-3` | `LAB-3` |
| Archivos generados | los 5 | los 5 |
| Ningún archivo generado queda vacío | 0 vacíos | 0 |
| Los lexemas se escapan y no inyectan HTML | `<script>` no aparece | ✔ |

La última verificación es de seguridad: el reporte de errores muestra
lexemas inválidos tal como venían en el archivo. Si un archivo `.hor`
contiene `<script>`, escribirlo sin escapar rompería la página o inyectaría
etiquetas. Se comprueba que el escapado funciona.

---

---

## Prueba de robustez adicional

Ademas de los ocho casos, se ejecutaron **diez archivos deliberadamente
hostiles** por las tres capas y por el generador de reportes, para verificar
que el programa no se cae ante entradas que un usuario real podria producir
por error. Estan en `entradas/estres/` con su propio LEEME.

| Archivo | Que prueba | Resultado |
|---|---|---|
| `e01_vacio.hor` | Archivo de 0 bytes | 0 tokens, 5 avisos de bloque faltante, reportes generados |
| `e02_solo_espacios.hor` | Solo espacios y tabulaciones | igual que el anterior |
| `e03_solo_comentarios.hor` | Solo comentarios con simbolos fuera del alfabeto | 3 tokens, 0 errores |
| `e04_sin_bloques.hor` | Elemento suelto sin bloque contenedor | aviso BLOQUE_INCORRECTO, curso armado |
| `e05_orden_invertido.hor` | Los cuatro bloques en orden inverso | 0 avisos: el recorrido no depende del orden |
| `e06_bloques_vacios.hor` | Bloques declarados y vacios | 0 errores, 0 avisos |
| `e07_unicode.hor` | Tildes, enie y `& < >` dentro de comillas | 0 errores, escapado correcto en el HTML |
| `e08_una_linea.hor` | Archivo completo en una linea, sin salto final | 0 errores |
| `e09_extremos.hor` | Nombre vacio, nombre de 130 caracteres, capacidad 999999 | 0 errores |
| `e10_destrozado.hor` | Llaves desbalanceadas, `:` faltantes, `DOMINGO`, `seccion: 1` | 1 error, 16 avisos, sin excepciones |

**Excepciones lanzadas: 0 en los diez archivos.**

### Prueba de volumen

Se genero un archivo de 600 clases (100 por dia, todas con el mismo
catedratico y la misma aula, el peor caso para el detector O(n^2)):

| Etapa | Tiempo | Resultado |
|---|---|---|
| Analisis lexico | 126 ms | 15 059 tokens |
| Estructurador | 8 ms | 600 clases |
| Deteccion de choques | 84 ms | 29 700 choques |
| Sugerencia de bloques libres | 54 ms | — |

Un horario real de facultad tiene decenas de clases, no seiscientas, asi que
el O(n^2) del detector no representa un problema practico.

### Casos lexicos puntuales verificados

| Entrada | Resultado |
|---|---|
| `07:0` | ENTERO, SIMBOLO, ENTERO (no es hora: falta un digito) |
| `7:00` | ENTERO, SIMBOLO, ENTERO (no es hora: falta un digito en la hora) |
| `07:000` | `HORA_FUERA_DE_RANGO`, consumido completo |
| `""` | CADENA vacia, valida |
| `"` sola | `CADENA_SIN_CERRAR` |
| `#` sola | `CARACTER_NO_RECONOCIDO` |
| `####doble` | un solo COMENTARIO_LINEA |
| `A-` | `CODIGO_MAL_FORMADO` |
| `"-"` | `CODIGO_MAL_FORMADO` |
| `"A--1"` | CADENA: con dos guiones no es candidato a codigo (decision D-01) |
| `{[]};,:` | siete SIMBOLO separados |
| Comentario al final sin salto de linea | COMENTARIO_LINEA cerrado por EOF |

---

## Archivos de entrada usados

| Archivo | Para qué sirve |
|---|---|
| `horario_valido.hor` | El ejemplo del enunciado. Línea base: 149 tokens, cero errores. |
| `horario_errores.hor` | Los cinco tipos de error léxico, uno por línea. |
| `horario_ambiguedades.hor` | Límites de hora, clasificación de literales, tabulaciones y CRLF. |
| `horario_choques.hor` | Choques reales más duplicados y referencias inexistentes. |
| `horario_choques_borde.hor` | Contención, doble motivo, tres mutuos, día saturado. |
| `horario_completo.hor` | Horario realista: los cuatro niveles de carga y un aula sobre el 80%. |
