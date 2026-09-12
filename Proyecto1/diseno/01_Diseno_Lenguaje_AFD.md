# HorarioScript — Diseño del Lenguaje y del AFD

**Proyecto 1 — Lenguajes Formales y de Programación, 2S2026**
**Sección B+ — Tutor: SamuelAguilar18**
**Repositorio:** `LFP_B+_2S2026/Proyecto1/`

---

## 1. Definición formal del lenguaje

### 1.1 Alfabeto (Σ)

El alfabeto se divide en subconjuntos para poder escribir las transiciones de forma
compacta. Cada subconjunto se implementa como una función de pertenencia
(`es_letra(c)`, `es_digito(c)`, ...) que compara rangos de `ord(c)` — **no** se usa
`str.isalpha()` ni ningún método de alto nivel.

| Subconjunto | Símbolo | Contenido |
|---|---|---|
| Letras | `L` | `A`–`Z`, `a`–`z` |
| Dígitos | `D` | `0`–`9` |
| Guión | `G` | `-` |
| Dos puntos | `P` | `:` |
| Comilla | `Q` | `"` |
| Numeral | `N` | `#` |
| Símbolos estructurales | `S` | `{` `}` `[` `]` `,` `;` |
| Espacios | `W` | espacio, `\t`, `\r`, `\n` |
| Otro | `O` | cualquier carácter no clasificado arriba |

Formalmente: Σ = L ∪ D ∪ G ∪ P ∪ Q ∪ N ∪ S ∪ W

Nota: dentro de un literal entre comillas se acepta **cualquier** carácter de Unicode
excepto `\n` y `"`. Eso incluye tildes y `ñ`, que fuera de las comillas se reportan
como `CARACTER_NO_RECONOCIDO`.

### 1.2 Catálogo de tokens

Son 12 tipos, dos más del mínimo exigido (10).

| # | Tipo de token | Regla | Ejemplo |
|---|---|---|---|
| 1 | `RESERVADA_BLOQUE` | `HORARIO` `CURSOS` `CATEDRATICOS` `AULAS` `CLASES` | `HORARIO` |
| 2 | `RESERVADA_ELEMENTO` | `curso` `catedratico` `aula` `clase` | `curso` |
| 3 | `RESERVADA_RELACION` | `con` `en` | `con` |
| 4 | `RESERVADA_ATRIBUTO` | `codigo` `creditos` `categoria` `capacidad` `edificio` `dia` `inicio` `fin` `seccion` | `creditos` |
| 5 | `DIA` | `LUNES` `MARTES` `MIERCOLES` `JUEVES` `VIERNES` `SABADO` | `MARTES` |
| 6 | `CATEGORIA` | `TITULAR` `INTERINO` `AUXILIAR` | `TITULAR` |
| 7 | `CODIGO` | `L⁺ - D⁺`, con o sin comillas | `"LFP-0796"` |
| 8 | `CADENA` | `" (Σ* − {", \n}) "` | `"Bases de Datos 2"` |
| 9 | `HORA` | `D D : D D`, rango 06:00–21:00 | `07:00` |
| 10 | `ENTERO` | `D⁺` | `40` |
| 11 | `SIMBOLO` | `{` `}` `[` `]` `:` `,` `;` (uno por token) | `[` |
| 12 | `COMENTARIO_LINEA` | `##` hasta `\n` o EOF | `## Ciclo 2026` |

---

## 2. Decisiones de diseño que resuelven ambigüedades del enunciado

Estas cinco decisiones son las que hay que **justificar en el Manual Técnico** (criterio
1.1, 10 pts). El enunciado deja los casos abiertos y el auxiliar preguntará por ellos.

### D-01 · `"LFP-0796"` es CODIGO, no CADENA

El enunciado presenta los códigos entre comillas (`"LFP-0796"`, `"A-101"`) pero también
define `CADENA` como todo texto entre comillas. Se resuelve así: al cerrar el literal,
el AFD **clasifica el contenido** antes de emitir el token.

- Si el contenido **no tiene espacios** y contiene **exactamente un guión** → es un
  candidato a código. Se valida `L⁺-D⁺`:
  - válido → `CODIGO`
  - inválido (`"LFP-"`, `"-101"`, `"LFP-07A6"`, `"AB-1-2"`) → error `CODIGO_MAL_FORMADO`
- En cualquier otro caso → `CADENA`

Esta regla es puramente léxica (no mira el contexto) y hace **alcanzable** el error
`CODIGO_MAL_FORMADO`, que de otro modo nunca se dispararía. Ejemplos del archivo de
prueba oficial: `"T-3"` → `CODIGO`, `"N"` → `CADENA`, `"Bases de Datos 2"` → `CADENA`.

### D-02 · `07:00` vs `07` seguido de `:`

Al leer dígitos, el AFD cuenta cuántos lleva. Si lleva **exactamente 2** y el siguiente
carácter es `:`, hace un lookahead de 2 posiciones:

- si vienen dos dígitos → consume y emite `HORA`
- si no → **retrocede el índice** al `:` y emite `ENTERO` con los 2 dígitos; el `:` se
  tokeniza después como `SIMBOLO`

El retroceso se hace restaurando `self.pos` y `self.columna` a valores guardados antes
del lookahead. Es la única parte del AFD con retroceso y está aislada en un solo método.

### D-03 · Rango de la hora

`HH:MM` bien formado pero fuera de 06:00–21:00, o con `MM > 59`, **sí** se consume
completo como lexema y se reporta `HORA_FUERA_DE_RANGO`. Consumirlo completo evita
que los cinco caracteres restantes generen una cascada de errores falsos.

### D-04 · Cómo se detecta `DIA_NO_RECONOCIDO`

Un lexer puro no sabe que `LUNEZ` pretendía ser un día. Se resuelve con una **memoria
de un token**: el analizador guarda el último `RESERVADA_ATRIBUTO` emitido.

- palabra desconocida y el último atributo fue `dia` → `DIA_NO_RECONOCIDO`
- palabra desconocida y el último atributo fue `categoria` → `DIA_NO_RECONOCIDO` con
  mensaje adaptado a categoría (el enunciado no define un tipo aparte)
- palabra desconocida en cualquier otro punto → `CARACTER_NO_RECONOCIDO` sobre el
  lexema completo

Esto es una capa de clasificación **posterior** al AFD, no una transición del autómata.
Se documenta así para que quede claro que el AFD sigue siendo determinista y sin
contexto.

### D-05 · Nombre del repositorio

GitHub no admite `+` en el nombre de un repositorio: lo sustituye automáticamente por
`-`, de modo que `LFP_B+_2S2026` se convertiría en `LFP_B-_2S2026`, que colisiona con
la nomenclatura de la sección B-. **Hay que preguntarle al tutor** si prefiere
`LFP_BMAS_2S2026` o `LFP_B_2S2026`. No lo dejes para el día de la entrega.

---

## 3. Diseño del AFD

### 3.1 Estados

| Estado | Nombre | Descripción | Acepta |
|---|---|---|---|
| q0 | INICIAL | Punto de partida y retorno tras cada token | — |
| q1 | PALABRA | Consumiendo `L (L\|D)*` | ✔ palabra / desconocida |
| q2 | COD_GUION | Se leyó `L⁺-`, se esperan dígitos | ✘ |
| q3 | COD_DIGITOS | Se leyó `L⁺-D⁺` | ✔ `CODIGO` |
| q4 | NUMERO | Consumiendo `D⁺` | ✔ `ENTERO` |
| q5 | HORA_SEP | Se leyó `DD:`, se esperan minutos | ✘ |
| q6 | HORA_MIN1 | Se leyó `DD:D` | ✘ |
| q7 | HORA_COMPLETA | Se leyó `DD:DD` | ✔ `HORA` |
| q8 | CADENA_ABIERTA | Dentro de un literal, tras `"` | ✘ |
| q9 | CADENA_CERRADA | Se leyó el `"` de cierre | ✔ `CADENA`/`CODIGO` |
| q10 | NUMERAL1 | Se leyó un `#` | ✘ |
| q11 | COMENTARIO | Dentro de `##...` | ✔ `COMENTARIO_LINEA` |
| q12 | SIMBOLO | Se leyó un carácter de `S` o `:` | ✔ `SIMBOLO` |
| qE | ERROR | Carácter fuera del alfabeto | ✔ (emite error) |

Estados de aceptación: F = {q1, q3, q4, q7, q9, q11, q12, qE}

### 3.2 Tabla de transiciones

Un guión (`—`) significa que no hay transición: si el estado es de aceptación, se
emite el token y se vuelve a q0 **sin consumir** el carácter actual; si no lo es, se
emite un error.

| Estado \ Entrada | L | D | `-` | `:` | `"` | `#` | S | W | O |
|---|---|---|---|---|---|---|---|---|---|
| **q0** | q1 | q4 | qE | q12 | q8 | q10 | q12 | q0 | qE |
| **q1** | q1 | q1 | q2 | — | — | — | — | — | — |
| **q2** | qE | q3 | qE | — | — | — | — | — | — |
| **q3** | qE | q3 | qE | — | — | — | — | — | — |
| **q4** | qE | q4 | q2 | q5 ⁽¹⁾ | — | — | — | — | — |
| **q5** | qE | q6 | qE | qE | qE | qE | qE | qE | qE |
| **q6** | qE | q7 | qE | qE | qE | qE | qE | qE | qE |
| **q7** | — | — | — | — | — | — | — | — | — |
| **q8** | q8 | q8 | q8 | q8 | q9 | q8 | q8 | q8 ⁽²⁾ | q8 |
| **q9** | — | — | — | — | — | — | — | — | — |
| **q10** | qE | qE | qE | qE | qE | q11 | qE | qE | qE |
| **q11** | q11 | q11 | q11 | q11 | q11 | q11 | q11 | q11 ⁽³⁾ | q11 |
| **q12** | — | — | — | — | — | — | — | — | — |

⁽¹⁾ Solo si el contador de dígitos es exactamente 2 **y** el lookahead confirma dos
dígitos después. Si no, se retrocede y q4 acepta como `ENTERO` (decisión D-02).
⁽²⁾ Excepto `\n`, que dispara el error `CADENA_SIN_CERRAR` reportando la posición de
apertura del literal.
⁽³⁾ Excepto `\n`, que cierra el comentario y acepta `COMENTARIO_LINEA`.

### 3.3 Clasificación en q1 (post-aceptación)

Al aceptar en q1, el lexema se compara contra las listas en este orden. La comparación
es carácter a carácter contra tuplas constantes, sin `in` sobre strings ni `==` de
alto nivel disfrazado.

```
1. ¿Está en BLOQUES?     → RESERVADA_BLOQUE
2. ¿Está en ELEMENTOS?   → RESERVADA_ELEMENTO
3. ¿Está en RELACIONES?  → RESERVADA_RELACION
4. ¿Está en ATRIBUTOS?   → RESERVADA_ATRIBUTO   (y se guarda como último atributo)
5. ¿Está en DIAS?        → DIA
6. ¿Está en CATEGORIAS?  → CATEGORIA
7. en otro caso          → palabra desconocida → capa de errores (D-04)
```

Las palabras reservadas son **sensibles a mayúsculas**: `HORARIO` es bloque, `horario`
es palabra desconocida. Esto se declara explícitamente porque el enunciado usa
mayúsculas para bloques/enumeraciones y minúsculas para elementos y atributos.

---

## 4. Arquitectura del sistema

```
Proyecto1/
├── main.py                     punto de entrada, levanta la GUI
├── modelos/
│   ├── token.py                clase Token (numero, lexema, tipo, linea, columna)
│   ├── error_lexico.py         clase ErrorLexico
│   └── elementos.py            Curso, Catedratico, Aula, Clase
├── analizador/
│   ├── alfabeto.py             es_letra, es_digito, es_simbolo... (sin str.isX)
│   ├── analizador_lexico.py    AFD manual + siguiente_token()
│   └── gestor_errores.py       acumula errores, modo pánico
├── logica/
│   ├── estructurador.py        recorre la lista de tokens y arma los objetos
│   └── detector_choques.py     traslape de bloques por catedrático y por aula
├── reportes/
│   ├── generador.py            los 3 reportes HTML + reporte de errores
│   ├── estilos.py              CSS embebido
│   └── graficador.py           emite el código DOT de Graphviz
├── gui/
│   └── interfaz.py             ventana Tkinter con todos los paneles
└── entradas/                   archivos .hor de prueba
```

### 4.1 Relaciones entre clases

```
InterfazGrafica
    └── usa → AnalizadorLexico ──── crea → Token
                    └── usa → GestorErrores ── crea → ErrorLexico
    └── usa → Estructurador ─────── crea → Curso / Catedratico / Aula / Clase
                    └── usa → DetectorChoques ── crea → Choque
    └── usa → GeneradorReportes
                    └── usa → Estilos, Graficador
```

El punto importante: `AnalizadorLexico` **no sabe nada** de horarios ni de choques.
Solo produce tokens. Toda la semántica vive en `logica/`. Esa separación es la que
permite defender el diseño ante el auxiliar y la que hace que el motor sea reusable
en el Proyecto 2.

---

## 5. Algoritmo de detección de choques

Dos clases chocan si comparten **día** y se **traslapan en el tiempo**, y además
comparten catedrático o aula.

```
traslapan(a, b)  ⟺  a.inicio < b.fin  ∧  b.inicio < a.fin
```

Las horas se convierten a minutos desde medianoche (`HH*60 + MM`) para comparar con
enteros. Se usa `<` estricto en ambos lados para que una clase que termina 08:40 y
otra que empieza 08:40 **no** cuenten como choque: eso es continuidad, no conflicto.

El algoritmo agrupa las clases por día y luego compara todos los pares dentro de cada
grupo (O(n²) sobre grupos pequeños, perfectamente aceptable para un horario de
facultad). Para cada par que se traslapa se revisa si `catedratico_a == catedratico_b`
o `aula_a == aula_b`, y se registra un `Choque` con el motivo.

---

## 6. Qué sigue (Sesión 2)

Implementar `alfabeto.py`, `token.py` y `analizador_lexico.py`, y probarlos desde
consola contra `horario_valido.hor` antes de tocar la GUI.
