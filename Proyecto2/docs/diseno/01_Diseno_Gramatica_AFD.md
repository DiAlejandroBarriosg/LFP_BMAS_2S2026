# MarkdownCheck — Diseño de la Gramática y del AFD

**Proyecto 2 — Lenguajes Formales y de Programación, 2S2026**
**Sección B+ — Tutor: SamuelAguilar18**
**Repositorio:** `LFP_BMAS_2S2026/Proyecto2/`

Este documento es la base de la Sesión 1. Todo lo que se codifique después
(léxico, parser, reportes) tiene que coincidir con lo que dice aquí. Cuando
algo cambie, se cambia primero aquí y luego en el código.

---

## 1. Visión general del flujo

```
archivo .md ──► AnalizadorLexico ──► tokens ──► AnalizadorSintactico ──► AST
                 (AFD + balanceo)                (descendente recursivo)
                        │                                 │
                        └──────────► GestorErrores ◄──────┘
                                           │
                     sin errores ──► GeneradorHTML, GeneradorEstadisticas,
                                     GeneradorIndice  (3 reportes)
                     siempre     ──► GeneradorDOT (arbol.dot), tabla de tokens,
                                     tabla de errores
```

El léxico **no sabe nada de HTML** y el parser **no lee caracteres**: solo
recibe tokens. Los generadores **solo recorren el AST**, nunca el texto
original (criterio 2.6 del enunciado).

---

## 2. Catálogo de tokens

### 2.1 Tokens del enunciado (sección 4.5)

| Tipo | Lexema | Dónde se reconoce | Ejemplo |
|---|---|---|---|
| `NUMERAL` | `#` a `######` | Inicio de línea (o tras `CITA`), seguido de espacio | `## Título` |
| `VIÑETA` | `-`, `*`, `+` | Inicio de línea (tras la sangría), seguido de espacio | `- Elemento` |
| `INDENT` | vacío (virtual) | Sube un nivel de lista; uno por nivel | (sin lexema visible) |
| `DEDENT` | vacío (virtual) | Baja un nivel de lista; uno por nivel | (sin lexema visible) |
| `CITA` | `>`, `>>`, `> >`… | Inicio de línea; el nivel es la cantidad de `>` | `>> Cita` |
| `CERCA_CODIGO` | ```` ``` ```` | Inicio de línea | ```` ```python ```` |
| `REGLA_HORIZONTAL` | `---` o más | Línea que solo contiene guiones (y espacios al final) | `---` |
| `NEGRITA` | `**` | Dentro de una línea | `**importante**` |
| `CURSIVA` | `*` | Dentro de una línea, fuera de posición de viñeta | `*énfasis*` |
| `CODIGO_INLINE` | `` ` `` | Dentro de una línea | `` `variable` `` |
| `TEXTO` | texto plano | Todo lo que no es delimitador | `Lenguajes Formales` |
| `SALTO_PARRAFO` | `\n` | Línea vacía o de solo espacios | (línea vacía) |

### 2.2 Tokens agregados (ver D-01 y D-12)

| Tipo | Lexema | Para qué existe |
|---|---|---|
| `SALTO_LINEA` | `\n` | Marca el fin de cada línea **no vacía**. Sin él, el parser no sabe dónde termina un encabezado o un ítem. |
| `TEXTO_LITERAL` | contenido literal | Interior de un bloque de código (una por línea) o de un código en línea. Aparece en la gramática de referencia pero no en la tabla de tokens del enunciado. |
| `LENGUAJE_CODIGO` | `python`, `java`… | Texto que sigue a la cerca de apertura. Da el `class="language-python"`. |
| `FIN` | vacío | Fin de archivo. Le permite al parser saber que no queda nada. |

### 2.3 Reglas de prioridad

1. **Viñeta vs. cursiva.** `*` solo es `VIÑETA` en posición inicial de línea y
   seguido de espacio. En cualquier otro lugar entra al reconocimiento de
   énfasis.
2. **Negrita vs. cursiva (maximal munch).** Al ver `*`, el AFD mira el
   siguiente carácter: si es otro `*`, reconoce `NEGRITA`.
3. **Encabezado vs. texto.** `#` solo forma `NUMERAL` al inicio de línea y
   seguido de espacio. `#sinespacio` es `TEXTO`.
4. **Regla vs. viñeta.** `- ` (guion + espacio) es `VIÑETA`. Tres o más guiones
   y nada más en la línea es `REGLA_HORIZONTAL`. `--` o `--texto` es `TEXTO`.
5. **Bloque de código.** Tras ```` ``` ```` de apertura el léxico entra en
   **modo literal**: cada línea completa es un `TEXTO_LITERAL`, sin buscar
   ningún otro token, hasta la cerca de cierre.
6. **Código en línea.** Tras `` ` `` todo hasta el siguiente `` ` `` de la
   misma línea es `TEXTO_LITERAL`; adentro no se reconocen `*` ni `**`.

---

## 3. El AFD léxico

El diagrama está en `afd_markdowncheck.dot` / `.png`. El autómata trabaja en
dos modos, y el estado inicial de cada línea depende del modo.

### 3.1 Estados

| Estado | Significado | Acepta |
|---|---|---|
| `q0` | Inicio de línea (modo normal). Consume la sangría. | — |
| `q1` | Leyendo `#` consecutivos | — |
| `q2` | `#` + espacio | `NUMERAL` (≤ 6) / error `ENCABEZADO_INVALIDO` (> 6) |
| `q3` | Leído un `-` al inicio | — |
| `q4` | Leídos `--` | — |
| `q5` | Leídos `---` o más | `REGLA_HORIZONTAL` (al llegar a fin de línea) |
| `q6` | Marcador de lista + espacio | `VIÑETA` |
| `q7` | Leído `*` o `+` al inicio | — |
| `q8` | Leyendo `>` | `CITA` |
| `q9` | `>` + espacio (puede venir otro `>`) | `CITA` |
| `q10` | Leído `` ` `` al inicio | — |
| `q11` | Leídos ```` `` ```` al inicio | — |
| `q12` | Leídos ```` ``` ```` | `CERCA_CODIGO` |
| `q13` | Resto de la línea de apertura | `LENGUAJE_CODIGO` |
| `q14` | Inicio de elemento en línea | — |
| `q15` | Leyendo texto plano | `TEXTO` |
| `q16` | Leído `*` en línea | `CURSIVA` (si lo siguiente no es `*`) |
| `q17` | Leído `**` | `NEGRITA` |
| `q18` | Leído `` ` `` en línea | `CODIGO_INLINE` |
| `q19` | Dentro de código en línea | `TEXTO_LITERAL` |
| `q20` | Fin de línea | `SALTO_LINEA` |
| `q21` | Línea vacía | `SALTO_PARRAFO` |
| `b0` | Inicio de línea en **modo literal** | — |
| `b1`, `b2`, `b3` | `` ` ``, ```` `` ````, ```` ``` ```` en modo literal | `CERCA_CODIGO` (cierre) en `b3` |
| `b4` | Línea de contenido del bloque | `TEXTO_LITERAL` |

### 3.2 Transiciones principales (modo normal)

| Desde | Carácter | Hacia | Nota |
|---|---|---|---|
| `q0` | espacio, tab | `q0` | Cuenta la sangría |
| `q0` | `\n` (línea sin contenido) | `q21` | |
| `q0` | `#` | `q1` | |
| `q0` | `-` | `q3` | |
| `q0` | `*`, `+` | `q7` | |
| `q0` | `>` | `q8` | |
| `q0` | `` ` `` | `q10` | |
| `q0` | otro | `q14` | Sin consumir |
| `q1` | `#` | `q1` | |
| `q1` | espacio | `q2` | |
| `q1` | otro | `q15` | Los `#` se vuelven `TEXTO` |
| `q3` | espacio | `q6` | |
| `q3` | `-` | `q4` | |
| `q3` | otro | `q15` | |
| `q4` | `-` | `q5` | |
| `q4` | otro | `q15` | |
| `q5` | `-`, espacio | `q5` | |
| `q5` | `\n` | acepta | `REGLA_HORIZONTAL` |
| `q5` | otro | `q15` | Ej.: `---texto` |
| `q7` | espacio | `q6` | |
| `q7` | otro | `q14` | Sin consumir: el `*` se reevalúa como énfasis |
| `q8` | `>` | `q8` | |
| `q8` | espacio | `q9` | |
| `q9` | espacio | `q9` | Solo si más adelante viene otro `>` |
| `q8` | otro | acepta | `CITA` (el parser revisa la separación, D-11) |
| `q9` | `>` | `q8` | Notación `> >` |
| `q9` | otro | acepta | `CITA`; el contenido empieza en `q14` |
| `q10` | `` ` `` | `q11` | |
| `q10` | otro | `q14` | Sin consumir: es código en línea |
| `q11` | `` ` `` | `q12` | |
| `q11` | otro | `q14` | Sin consumir |
| `q12` | otro ≠ `\n` | `q13` | Cambia a **modo literal** al terminar la línea |
| `q14` | `*` | `q16` | |
| `q14` | `` ` `` | `q18` | |
| `q14` | `\n` o fin | `q20` | |
| `q14` | otro | `q15` | |
| `q15` | otro ≠ `*`, `` ` ``, `\n` | `q15` | |
| `q15` | `*`, `` ` ``, `\n` | acepta | `TEXTO`, sin consumir el delimitador |
| `q16` | `*` | `q17` | Maximal munch |
| `q16` | otro | acepta | `CURSIVA` |
| `q18` | otro ≠ `` ` ``, `\n` | `q19` | Solo si hay `` ` `` de cierre en la línea (D-03) |
| `q19` | otro ≠ `` ` ``, `\n` | `q19` | |
| `q19` | `` ` `` | acepta | `TEXTO_LITERAL`, luego `CODIGO_INLINE` |

### 3.3 Transiciones del modo literal

| Desde | Carácter | Hacia |
|---|---|---|
| `b0` | espacio | `b0` (solo para buscar la cerca) |
| `b0` | `` ` `` | `b1` → `b2` → `b3` |
| `b0` | otro | `b4` |
| `b3` | espacios hasta `\n` | acepta `CERCA_CODIGO`, vuelve a **modo normal** |
| `b1`, `b2`, `b3` | otro | `b4` (la línea es contenido) |
| `b4` | otro ≠ `\n` | `b4` |
| `b4` | `\n` | acepta `TEXTO_LITERAL` (la línea completa, con su sangría) |
| `b0` | `\n` (línea vacía) | acepta `TEXTO_LITERAL` vacío |
| `b0` | fin de archivo | error `BLOQUE_CODIGO_SIN_CERRAR` |

### 3.4 Capas posteriores al autómata

El AFD es determinista y no tiene memoria. Hay tres cosas que necesitan
memoria y por eso van **fuera** del autómata, como capas que el
`AnalizadorLexico` aplica después. En el manual técnico hay que decirlo así.

1. **Contador de nivel de lista.** Al aceptar una `VIÑETA`, el léxico compara
   el nivel de sangría (espacios ÷ 2) con `nivel_lista`. Si sube, emite un
   `INDENT` por cada nivel antes de la viñeta; si baja, un `DEDENT` por cada
   nivel. Una línea que no es ítem (incluida una línea vacía) baja el
   nivel a 0. Al final del archivo, también.
2. **Pila de delimitadores en línea.** Cada vez que el AFD acepta una
   `NEGRITA` o una `CURSIVA`, el token pasa por la pila: si es igual a la
   cima, la **cierra** (se saca); si no, **abre** (se mete). Al llegar al fin
   de línea, lo que quedó en la pila nunca se cerró: se reporta como
   `NEGRITA_SIN_CERRAR` o `CURSIVA_SIN_CERRAR` y ese token pasa a ser
   `TEXTO`. Como la línea completa se analiza antes de entregar sus tokens,
   el parser nunca recibe un delimitador sin pareja. La pila también la
   consulta el AFD en el caso `***` (D-04).
3. **Cola de tokens pendientes.** `siguiente_token()` entrega de esa cola;
   cuando se vacía, analiza la línea siguiente.

---

## 4. Gramática libre de contexto

### 4.1 Gramática formal (BNF, LL(1))

Partiendo de la referencia de la sección 4.6, con los cambios justificados
en la sección 6.

```
<documento>        ::= <elementos> FIN
<elementos>        ::= <elemento_doc> <elementos> | ε
<elemento_doc>     ::= <bloque> | SALTO_PARRAFO
<bloque>           ::= <encabezado> | <parrafo> | <lista> | <cita>
                     | <bloque_codigo> | <regla_horizontal>

<encabezado>       ::= NUMERAL <en_linea> SALTO_LINEA

<parrafo>          ::= <linea_texto> <resto_parrafo>
<resto_parrafo>    ::= <parrafo> | ε
<linea_texto>      ::= <elemento_linea> <en_linea> SALTO_LINEA

<lista>            ::= <item_lista> <resto_lista>
<resto_lista>      ::= <lista> | ε
<item_lista>       ::= VIÑETA <en_linea> SALTO_LINEA <sublista_opc>
<sublista_opc>     ::= <sublista> | ε
<sublista>         ::= INDENT <lista> DEDENT

<cita(n)>          ::= <elemento_cita(n)> <resto_cita(n)>
<resto_cita(n)>    ::= <cita(n)> | ε
<elemento_cita(n)> ::= CITA[n] <contenido_cita>
                     | <cita(n+1)>                  (cuando viene CITA[m], m > n)
<contenido_cita>   ::= <encabezado>
                     | <en_linea> SALTO_LINEA

<bloque_codigo>    ::= CERCA_CODIGO <lenguaje_opc> SALTO_LINEA
                       <contenido_codigo> CERCA_CODIGO SALTO_LINEA
<lenguaje_opc>     ::= LENGUAJE_CODIGO | ε
<contenido_codigo> ::= TEXTO_LITERAL SALTO_LINEA <contenido_codigo> | ε

<regla_horizontal> ::= REGLA_HORIZONTAL SALTO_LINEA

<en_linea>         ::= <elemento_linea> <en_linea> | ε
<elemento_linea>   ::= <negrita> | <cursiva> | <codigo_inline> | TEXTO

<negrita>          ::= NEGRITA <en_linea_n> NEGRITA
<en_linea_n>       ::= <elemento_n> <en_linea_n> | ε
<elemento_n>       ::= <cursiva> | <codigo_inline> | TEXTO

<cursiva>          ::= CURSIVA <en_linea_c> CURSIVA
<en_linea_c>       ::= <elemento_c> <en_linea_c> | ε
<elemento_c>       ::= <negrita> | <codigo_inline> | TEXTO

<codigo_inline>    ::= CODIGO_INLINE <literal_opc> CODIGO_INLINE
<literal_opc>      ::= TEXTO_LITERAL | ε
```

La cita usa el **atributo** `n` (nivel). `CITA[n]` significa "un token `CITA`
cuyo lexema tiene exactamente `n` símbolos `>`". La cita raíz es `<cita(1)>`.
Esto es una gramática con atributos: la estructura sigue siendo libre de
contexto y el atributo solo decide qué alternativa tomar, igual que un
predicado semántico.

`<linea_texto>` empieza con un `<elemento_linea>` obligatorio, así que un
párrafo nunca es vacío. Coincide con lo que entrega el léxico: toda línea sin
contenido llega como `SALTO_PARRAFO`, nunca como un `SALTO_LINEA` solo.

El desarrollo completo de esta gramática (comparación con la de referencia
4.6, conjuntos PRIMERO y SIGUIENTE de los 31 no terminales y árboles de
derivación) está en la Tarea 4 del curso.

### 4.2 Conjuntos FIRST relevantes

| No terminal | FIRST |
|---|---|
| `<bloque>` | `NUMERAL`, `TEXTO`, `NEGRITA`, `CURSIVA`, `CODIGO_INLINE`, `VIÑETA`, `CITA`, `CERCA_CODIGO`, `REGLA_HORIZONTAL` |
| `<encabezado>` | `NUMERAL` |
| `<parrafo>` | `TEXTO`, `NEGRITA`, `CURSIVA`, `CODIGO_INLINE` |
| `<lista>` | `VIÑETA` |
| `<cita(n)>` | `CITA` |
| `<contenido_cita>` | `NUMERAL` (→ `<encabezado>`) / `TEXTO`, `NEGRITA`, `CURSIVA`, `CODIGO_INLINE`, `SALTO_LINEA` |
| `<bloque_codigo>` | `CERCA_CODIGO` |
| `<regla_horizontal>` | `REGLA_HORIZONTAL` |
| `<en_linea>` | `NEGRITA`, `CURSIVA`, `CODIGO_INLINE`, `TEXTO`, ε |
| `<en_linea_n>` | `CURSIVA`, `CODIGO_INLINE`, `TEXTO`, ε |
| `<en_linea_c>` | `NEGRITA`, `CODIGO_INLINE`, `TEXTO`, ε |

Las alternativas de `<bloque>` tienen FIRST disjuntos, así que un solo token
de lookahead decide qué función llamar. Lo mismo en `<contenido_cita>`: como
la `CITA` ya se consumió, el token actual decide entre `<encabezado>` y una
línea de texto. **Toda la gramática es LL(1)**; el parser trabaja con un solo
token de lookahead (`self.actual`).

En `<elemento_cita(n)>` la decisión la toma el **atributo**: una `CITA` de
nivel mayor que `n` abre `<cita(n+1)>`; si no, es una línea de esta cita.

**Por qué hay tres versiones de `<en_linea>`.** Con una sola, dentro de una
negrita no se sabría si el siguiente `**` cierra la negrita actual o abre una
nueva: `NEGRITA` estaría a la vez en FIRST(`<elemento_linea>`) y en
FOLLOW(`<en_linea>`). Eso es un conflicto LL(1). Quitando la negrita de lo que
puede ir directamente dentro de una negrita (y la cursiva de una cursiva), el
conflicto desaparece. Negrita dentro de cursiva y cursiva dentro de negrita
siguen permitidas.

**Listas y párrafos consecutivos.** Formalmente FOLLOW(`<lista>`) incluye
`VIÑETA`, porque `<documento>` podría poner dos listas seguidas. Se resuelve
de forma **voraz**: mientras venga `VIÑETA`, se extiende la lista actual
(igual que el *dangling else*). Lo mismo para las líneas de un párrafo.

### 4.3 Forma EBNF (la que implementa el parser)

La recursión por la derecha `X ::= a X | a` es equivalente a la repetición
`X ::= a { a }`, y `X ::= a | ε` equivale a la parte opcional `[ a ]`. El
parser implementa esta forma: una repetición es un `while` y una parte
opcional es un `if`. Por eso desaparecen los no terminales auxiliares de la
BNF (`<resto_parrafo>`, `<resto_lista>`, `<resto_cita(n)>`, `<sublista_opc>`,
`<lenguaje_opc>`, `<literal_opc>`), y el árbol tiene, por ejemplo, un solo
nodo `<lista>` con todos sus `<item_lista>` como hijos, en vez de una cadena
de `<lista>` anidadas.

```
<documento>        ::= { <elemento_doc> } FIN
<elemento_doc>     ::= <bloque> | SALTO_PARRAFO
<bloque>           ::= <encabezado> | <parrafo> | <lista> | <cita(1)>
                     | <bloque_codigo> | <regla_horizontal>
<encabezado>       ::= NUMERAL <en_linea> SALTO_LINEA
<parrafo>          ::= <linea_texto> { <linea_texto> }
<linea_texto>      ::= <elemento_linea> <en_linea> SALTO_LINEA
<lista>            ::= <item_lista> { <item_lista> }
<item_lista>       ::= VIÑETA <en_linea> SALTO_LINEA [ <sublista> ]
<sublista>         ::= INDENT <lista> DEDENT
<cita(n)>          ::= <elemento_cita(n)> { <elemento_cita(n)> }
<elemento_cita(n)> ::= CITA[n] <contenido_cita> | <cita(n+1)>
<contenido_cita>   ::= <encabezado> | <en_linea> SALTO_LINEA
<bloque_codigo>    ::= CERCA_CODIGO [ LENGUAJE_CODIGO ] SALTO_LINEA
                       <contenido_codigo> CERCA_CODIGO SALTO_LINEA
<contenido_codigo> ::= { TEXTO_LITERAL SALTO_LINEA }
<regla_horizontal> ::= REGLA_HORIZONTAL SALTO_LINEA
<en_linea>         ::= { <elemento_linea> }
<elemento_linea>   ::= <negrita> | <cursiva> | <codigo_inline> | TEXTO
<negrita>          ::= NEGRITA <en_linea_n> NEGRITA
<en_linea_n>       ::= { <elemento_n> }
<elemento_n>       ::= <cursiva> | <codigo_inline> | TEXTO
<cursiva>          ::= CURSIVA <en_linea_c> CURSIVA
<en_linea_c>       ::= { <elemento_c> }
<elemento_c>       ::= <negrita> | <codigo_inline> | TEXTO
<codigo_inline>    ::= CODIGO_INLINE [ TEXTO_LITERAL ] CODIGO_INLINE
```

Son 24 no terminales y el `AnalizadorSintactico` tiene **una función por
cada uno** (`parsear_documento()`, `parsear_bloque()`…). El mapa completo
está en el encabezado de `analizador_sintactico.py`.

### 4.4 Propiedad comprobada: la frontera del árbol es la entrada

En un árbol de derivación, las hojas leídas de izquierda a derecha forman la
cadena de entrada. Las pruebas lo verifican: las hojas del árbol son
exactamente todos los tokens del léxico, en el mismo orden, para el ejemplo
del enunciado, para los archivos con errores (la recuperación no pierde
tokens) y para 400 documentos generados al azar. Durante el desarrollo se
comprobó también con 20 000 documentos al azar: ninguna excepción, ningún
`TOKEN_INESPERADO` y la frontera siempre completa.

---

## 5. Errores

| Tipo | Fase | Quién lo detecta | Recuperación |
|---|---|---|---|
| `NEGRITA_SIN_CERRAR` | Léxico | Pila de delimitadores, al fin de línea | El `**` pasa a `TEXTO` |
| `CURSIVA_SIN_CERRAR` | Léxico | Pila de delimitadores, al fin de línea | El `*` pasa a `TEXTO` |
| `CODIGO_INLINE_SIN_CERRAR` | Léxico | AFD, al ver `` ` `` sin cierre en la línea | El `` ` `` pasa a `TEXTO` |
| `BLOQUE_CODIGO_SIN_CERRAR` | Léxico | Modo literal al llegar a fin de archivo | El bloque llega hasta el fin de archivo; el parser no exige la cerca de cierre en ese caso |
| `ENCABEZADO_INVALIDO` | Léxico | AFD en `q2` con más de 6 `#` | La línea se analiza como texto |
| `INDENTACION_INVALIDA` | Léxico | Sangría que no es múltiplo de 2 | Se toma el nivel completo inferior |
| `INDENTACION_INVALIDA` | Sintáctico | `parsear_sublista()`: después de un `INDENT` viene otro (salto de 2+ niveles) | El nivel que sobra se analiza como otra `<sublista>` (llamada recursiva): cada `INDENT` encuentra su `DEDENT` |
| `INDENTACION_INVALIDA` | Sintáctico | `parsear_elemento_doc()`: un `INDENT` donde empieza un bloque (D-24) | Se analiza como `<sublista>` sin ítem padre, colgada del documento |
| `CITA_MAL_FORMADA` | Sintáctico | `_revisar_separacion_cita()`: el token siguiente está pegado al último `>` (D-11, D-23) | La línea se acepta como parte de la cita |
| `TOKEN_INESPERADO` | Sintáctico | `_coincidir()`: el token no es el que exige la gramática | Modo pánico: descarta hasta `SALTO_LINEA`, `SALTO_PARRAFO` o `FIN`. Si ese era el token esperado, se consume y se sigue |
| `TOKEN_INESPERADO` | Sintáctico | `parsear_elemento_doc()`: un token que no puede empezar un bloque | Se descarta el resto de la línea, incluido su `SALTO_LINEA` |

Mensajes: los del enunciado, con línea y columna del token que abre el
problema. El parser **no vuelve a reportar** algo que el léxico ya reportó.

Con este léxico, `TOKEN_INESPERADO` no aparece en la práctica: el léxico
siempre entrega secuencias que la gramática acepta, salvo los errores
diseñados (`INDENT` de más y citas pegadas). Es una red de seguridad, y se
prueba con un léxico falso que entrega secuencias de tokens al azar: el
modo pánico siempre llega a `FIN`.

---

## 6. Decisiones de diseño

**D-01 — Se agregan `SALTO_LINEA` y `FIN`.** La tabla del enunciado no tiene
un token de fin de línea, pero la gramática lo necesita: sin él,
`# Título` seguido de `texto` en la línea siguiente llega al parser como
`NUMERAL TEXTO TEXTO` y no hay forma de saber dónde terminó el encabezado.
Toda línea no vacía termina en `SALTO_LINEA`, aunque el archivo no termine en
`\n`. El `\r` de los archivos de Windows se ignora.

**D-02 — Los delimitadores en línea se cierran en la misma línea.** `**`,
`*` y `` ` `` deben cerrarse antes del `SALTO_LINEA`. Todos los bloques del
subconjunto se definen por línea, y así el léxico puede validar cada línea
por separado. Consecuencia: una negrita que cruce dos líneas de un mismo
párrafo se reporta como sin cerrar.

**D-03 — El balanceo de `**` y `*` es una capa posterior al AFD.** Decidir si
un `*` abre o cierra requiere memoria (una pila), y un AFD no la tiene. El
`AnalizadorLexico` arma los tokens de la línea con el AFD y luego los recorre
con una pila (sección 3.4). El código en línea no necesita pila: al ver `` ` ``
el AFD mira hacia adelante si hay otro `` ` `` en la línea.

**D-04 — Un delimitador igual a la cima de la pila siempre cierra.** Por eso
`**a **b** c**` produce dos negritas seguidas, no una negrita anidada, y eso
coincide con la gramática (D-05). Caso especial `***`: si la cima es una
`CURSIVA`, el primer `*` cierra la cursiva y luego `**` cierra la negrita, para
que `***texto***` funcione. La excepción aplica solo con **exactamente**
tres asteriscos y una cursiva en la cima; en cualquier otro caso manda el
*maximal munch*.

**D-05 — Tres variantes de `<en_linea>`.** Explicado en 4.2: elimina el
conflicto LL(1). Las tres se implementan en el parser con funciones
separadas para respetar "una función por no terminal".

**D-06 — Un `INDENT` o `DEDENT` por nivel.** Pasar de 0 a 4 espacios emite
**dos** `INDENT`. La gramática dice que después de un `INDENT` viene una
`VIÑETA`; si viene otro `INDENT`, el parser detecta `INDENTACION_INVALIDA`
como error sintáctico, tal como clasifica el enunciado. Como cada `INDENT`
tiene su `DEDENT`, la recuperación no desbalancea nada.

**D-07 — Sangría impar o con tabulador.** Un tabulador cuenta como 2
espacios. Una sangría impar (3 espacios) se reporta en el léxico como
`INDENTACION_INVALIDA` y se toma el nivel inferior (3 → nivel 1).

**D-08 — Una línea vacía termina la lista y la cita.** `- a`, línea vacía,
`- b` son dos listas. Simplifica la gramática: una lista nunca contiene
`SALTO_PARRAFO`.

**D-09 — Nivel de cita por cantidad de `>`.** `>>` y `> >` son nivel 2.
`<cita(n)>` se llama a sí misma con `n+1` cuando aparece una línea de nivel
mayor. Si se salta de nivel 1 a nivel 3, se crea una cita de nivel 2 vacía en
medio, igual que lo haría Markdown.

**D-10 — Qué puede ir dentro de una cita.** Encabezados y texto en línea.
Listas, código y reglas dentro de citas quedan fuera del subconjunto. Cada
línea de cita con texto es su propio `<p>`, y no cuenta como párrafo en el
Reporte 2 (se cuenta como "línea de cita", igual que en el ejemplo).

**D-11 — `CITA_MAL_FORMADA` la detecta el parser.** El enunciado la clasifica
como sintáctica. El léxico emite la `CITA` igual, y el parser compara
posiciones: si el token siguiente empieza en la columna inmediatamente
después del último `>`, falta el espacio.

**D-12 — Bloques de código.** El texto después de ```` ``` ```` es un token
`LENGUAJE_CODIGO`. El contenido se emite como un `TEXTO_LITERAL` por línea,
con su sangría intacta, incluidas las líneas vacías. Solo una línea que sea
exactamente ```` ``` ```` (con espacios alrededor) cierra el bloque.

**D-13 — Párrafo = líneas de texto consecutivas.** Termina en una línea vacía
o en una línea que empiece otro bloque. En el HTML, sus líneas van dentro de
un mismo `<p>`.

**D-14 — Conteo de palabras.** Se unen los textos de cada línea (sin los
delimitadores) y se separa por espacios. Cuenta encabezados, párrafos,
ítems, citas y código en línea; **no** cuenta bloques de código. Con esta
regla el ejemplo del enunciado da exactamente **67**, como en su Reporte 2.

**D-15 — Anclas del Reporte 3.** Cada encabezado recibe `id="seccion-1"`,
`seccion-2`… en orden de aparición. No hay que inventar *slugs* con tildes ni
manejar títulos repetidos.

**D-16 — Qué se genera y cuándo.** Los 3 reportes HTML solo sin errores, como
pide el enunciado. La tabla de tokens, la tabla de errores y `arbol.dot` se
generan siempre. Con errores, además se genera `reporte_errores.html`.

**D-17 — Forma del árbol.** Cada función del parser crea un nodo con el
nombre de su no terminal, y todo terminal consumido es una hoja. Las
repeticiones `{ }` son hijos de un mismo nodo y lo que va entre `[ ]` cuelga
del nodo padre (sección 4.3). Las **selecciones** `<elemento_doc>`,
`<elemento_cita(n)>`, `<elemento_linea>`, `<elemento_n>` y `<elemento_c>`
tienen su función, pero no crean nodo propio: agregan al padre lo que
reconocen. Así lo hace el ejemplo DOT del enunciado (sección 4.10), que
cuelga `TEXTO` directamente de `<en_linea>`. `<bloque>` sí crea nodo, porque
ese mismo ejemplo lo muestra.

**D-18 — Estilo del código.** Sin `if` ternarios, `lambda`, *slicing*,
`sorted()`, `enumerate`, `set()`, decoradores ni comprensiones. Recorridos
con `while` e índice. Todo tiene que poder explicarse y modificarse en vivo.

**D-19 — Posiciones.** La línea y la columna empiezan en 1. La columna cuenta
caracteres: un tabulador ocupa una columna (aunque en la sangría valga dos
espacios, D-07). El `\r` de Windows y la marca BOM se eliminan antes de
analizar, así que no ocupan columna. Los tokens virtuales (`INDENT`,
`DEDENT`, `FIN` y el `SALTO_LINEA` final sin `\n`) tienen lexema vacío;
`DEDENT` lleva la columna 1 de la línea que lo provoca.

**D-20 — Un `*` entre espacios también abre cursiva.** El enunciado dice que,
fuera de la posición de viñeta, `*` *siempre* inicia una cursiva. Por eso
`5 * 3` produce `CURSIVA_SIN_CERRAR`. Para escribir un asterisco literal se
usa código en línea: `` `5 * 3` ``.

**D-21 — Un `` ` `` abre código en línea si hay otro `` ` `` en la línea.**
Se decide con *lookahead* antes de consumir, así que no hace falta pila.
Dos acentos pegados (` `` `) forman un código en línea vacío.

**D-22 — Un error no se repite mientras el parser se recupera.** Si ya hay un
error sintáctico del mismo tipo en la misma línea, no se agrega otro. Un
salto de 0 a 6 espacios emite tres `INDENT`, pero se reporta una sola
`INDENTACION_INVALIDA`. La comparación incluye la fase: una sangría de 5
espacios tiene un error léxico (impar) y uno sintáctico (salto de nivel), y
se reportan los dos porque son problemas distintos.

**D-23 — Columna de `CITA_MAL_FORMADA`.** Se reporta en la columna del último
`>`, que es el símbolo al que le falta el espacio: `>>texto` da columna 2.

**D-24 — Una lista no puede empezar con sangría.** Un ítem con sangría
donde empieza un bloque (por ejemplo, después de una línea vacía, que ya
cerró la lista por D-08) no tiene ítem padre. Se reporta como
`INDENTACION_INVALIDA` (sintáctico), con el detalle "sublista sin ítem
padre". Markdown estándar tolera hasta 3 espacios antes de una lista; aquí
se exige que el nivel de sangría sea el de la estructura, porque así lo
define la regla de indentación del enunciado.

**D-25 — Traducción a HTML.** El `GeneradorHTML` tiene una función por cada
no terminal que produce etiquetas y recorre el árbol con la misma recursión
del parser. Detalles: la `<sublista>` no tiene etiqueta propia (su `<ul>`
queda dentro del `<li>` del ítem padre); una línea de cita vacía (`>`) no
produce un `<p>` vacío; `&`, `<`, `>` y `"` se escapan siempre, también
dentro del código. Las anclas salen de `recorridos.encabezados()`, la misma
función que usará el Reporte 3, así que los enlaces del índice siempre
apuntan al encabezado correcto.

**D-26 — Qué cuenta el Reporte 2.** Cada estadística es la cantidad de nodos
de un no terminal: "Listas" y "Citas" cuentan solo las de primer nivel
(`nivel 1`), porque una sublista es parte de su lista; "Ítems" y "Líneas de
cita" cuentan todos los `<item_lista>` y `<contenido_cita>`. Las líneas de
cita no cuentan como párrafos (D-10). Con estas reglas el ejemplo del
enunciado da exactamente los valores de su captura: 67 palabras, 2
párrafos, 2 encabezados, 8 ítems, 2 líneas de cita, 1 bloque de código y
profundidades 3 y 2.

**D-27 — La interfaz analiza lo que hay en el editor.** "Analizar" toma el
texto del editor, no el archivo del disco, para poder probar cambios sin
guardar. Los reportes de cada archivo van a `salida/<nombre>/`, así no se
mezclan. Al elegir un token o un error en las tablas, el editor salta a esa
posición y la resalta; los errores quedan marcados en rojo. Si Graphviz
está instalado, `arbol.dot` se convierte también en `arbol.png`.

---

## 7. Arquitectura

```
LFP_BMAS_2S2026/Proyecto2/
├── src/
│   ├── main.py
│   ├── lexico/
│   │   ├── alfabeto.py             listas de caracteres especiales
│   │   ├── token.py                Token y constantes de tipos
│   │   └── analizador_lexico.py    AnalizadorLexico, siguiente_token()
│   ├── sintactico/
│   │   ├── nodo_ast.py             NodoAST
│   │   └── analizador_sintactico.py
│   ├── errores/
│   │   ├── error_analisis.py       ErrorAnalisis (un registro de la tabla)
│   │   └── gestor_errores.py       GestorErrores
│   ├── reportes/
│   │   ├── estilos.py              CSS embebido compartido
│   │   ├── generador_html.py       Reporte 1
│   │   ├── generador_estadisticas.py   Reporte 2
│   │   ├── generador_indice.py     Reporte 3
│   │   ├── generador_errores.py    reporte_errores.html
│   │   └── generador_dot.py        arbol.dot
│   └── gui/
│       └── ventana_principal.py    VentanaPrincipal (Tkinter)
├── tests/        pruebas desde consola, una por fase
├── examples/     archivos .md de entrada
├── docs/         diseño, manuales y casos de prueba (PDF)
├── README.md
└── .gitignore
```

| Clase | Responsabilidad | No hace |
|---|---|---|
| `Token` | tipo, lexema, línea, columna, número | — |
| `AnalizadorLexico` | AFD, `INDENT`/`DEDENT`, pila de delimitadores, `siguiente_token()` | No conoce el AST ni el HTML |
| `NodoAST` | nombre del símbolo, token (si es hoja), hijos, atributos (nivel) | — |
| `AnalizadorSintactico` | Una función por no terminal, construye el AST, modo pánico | No lee caracteres |
| `GestorErrores` | Acumula errores léxicos y sintácticos en orden | — |
| `GeneradorHTML` | Recorre el AST y produce el Reporte 1 | No mira el texto original |
| `VentanaPrincipal` | Cargar, analizar, mostrar tablas, abrir reportes | No analiza nada por sí misma |

---

## 8. Ejemplo: tokens esperados (líneas 7 a 10 del ejemplo)

```
7  - Análisis léxico
8    - Autómatas finitos
9    - Expresiones regulares
10 - Análisis sintáctico
```

| Lexema | Tipo | Línea | Columna |
|---|---|---|---|
| `-` | VIÑETA | 7 | 1 |
| `Análisis léxico` | TEXTO | 7 | 3 |
| `\n` | SALTO_LINEA | 7 | 18 |
| (virtual) | INDENT | 8 | 1 |
| `-` | VIÑETA | 8 | 3 |
| `Autómatas finitos` | TEXTO | 8 | 5 |
| `\n` | SALTO_LINEA | 8 | 22 |
| `-` | VIÑETA | 9 | 3 |
| `Expresiones regulares` | TEXTO | 9 | 5 |
| `\n` | SALTO_LINEA | 9 | 26 |
| (virtual) | DEDENT | 10 | 1 |
| `-` | VIÑETA | 10 | 1 |
| `Análisis sintáctico` | TEXTO | 10 | 3 |
| `\n` | SALTO_LINEA | 10 | 22 |

Y la derivación correspondiente:

```
<lista>
├── <item_lista>            VIÑETA <en_linea>(Análisis léxico) SALTO_LINEA
│   └── <sublista>          INDENT
│       └── <lista>
│           ├── <item_lista>   Autómatas finitos
│           └── <item_lista>   Expresiones regulares
│                           DEDENT
└── <item_lista>            Análisis sintáctico …
```

---

## 9. Calendario (entrega: domingo 25 de octubre)

La Sesión 3 implementó el parser completo, incluidas listas, citas y
recuperación de errores, que estaban planificadas para una cuarta sesión.
Las sesiones siguientes se renumeraron.

| Sesión | Contenido | Fecha | Estado |
|---|---|---|---|
| 1 | Gramática, tokens, AFD, decisiones | mié 7 oct | Hecha |
| 2 | `Token` + `AnalizadorLexico` + pruebas de consola | mié 7 oct | Hecha |
| 3 | `NodoAST` + parser completo: bloques, listas, citas, recuperación | mié 7 oct | Hecha |
| 4 | `GeneradorHTML` (Reporte 1) + `arbol.dot` | mié 7 oct | Hecha |
| 5 | Reportes 2 y 3, reporte de errores | jue 8 oct | Hecha |
| 6 | GUI Tkinter e integración | jue 8 oct | Hecha |
| 7 | Casos de prueba (13) y su PDF | jue 8 oct | Hecha |
| 8 | Manual Técnico (PDF) | jue 8 oct | Hecha |
| 9 | Manual de Usuario (PDF), README, revisión de commits | vie 9 oct | Hecha |
| — | Holgura: alcance opcional si se quiere y práctica de modificación en vivo | dom 18 – dom 25 | |
