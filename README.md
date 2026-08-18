# Torneo de Sudoku — Numerix Academy

Motor de calificación y análisis de partidas de Sudoku, desarrollado en Python 3
para la Práctica 1 del curso de **Lenguajes Formales y de Programación**.

El programa lee tres archivos `.lfp` (tableros, jugadores e intentos), reconstruye
cada tablero como una matriz de 9×9, valida cada intento contra las reglas del
Sudoku, calcula métricas de desempeño y genera reportes analíticos en HTML.

---

## Requisitos

- Python 3.8 o superior (no requiere instalar librerías adicionales)
- Consola o terminal
- Navegador web para ver los reportes generados

---

## Estructura del proyecto

Los cinco archivos `.py` están en la carpeta principal, sin subcarpetas de código,
para que las importaciones sean directas y fáciles de seguir.

```
Practica1/
├── main.py           Menú de consola y flujo del programa
├── clases.py         Clases Tablero, Jugador e Intento
├── lectura.py        Lectura de los archivos .lfp y validación de formato
├── validacion.py     Validación matricial del Sudoku
├── reportes.py       Cálculo de estadísticas y generación de HTML
├── README.md
├── entrada/
│   ├── sudokus.lfp
│   ├── jugadores.lfp
│   └── intentos.lfp
└── reportes/         Salida .html (se crea automáticamente)
```

### Qué hace cada archivo

| Archivo | Responsabilidad |
|---|---|
| `clases.py` | Define los tres moldes de objetos y la función que convierte una cadena de 81 dígitos en matriz 9×9 |
| `lectura.py` | Abre los archivos, separa cada línea con `split(',')`, valida los datos y crea los objetos |
| `validacion.py` | Extrae filas, columnas y cajas; revisa si cumplen la regla; califica cada intento |
| `reportes.py` | Calcula promedios y tasas de éxito, ordena los datos y arma los archivos HTML |
| `main.py` | Muestra el menú y llama a las funciones anteriores según la opción elegida |

---

## Ejecución

```bash
cd Practica1
python main.py
```

Menú del sistema:

```
==========================================================
           TORNEO DE SUDOKU - NUMERIX ACADEMY
==========================================================
Sudokus: 8 | Jugadores: 10 | Intentos: 55 | Calificados: Si
==========================================================
 1. Cargar archivo de sudokus
 2. Cargar archivo de jugadores
 3. Cargar archivo de intentos
 4. Validar y calificar intentos
 5. Generar Reporte: Resumen por Sudoku
 6. Generar Reporte: Rendimiento por Jugador
 7. Generar Reporte: Top 10 Mejores Tiempos
 8. Generar Reporte: Sudokus mas dificiles
 9. Generar Reporte: Analisis por nivel
10. Generar todos los reportes
11. Ver detalle de un intento
 0. Salir
==========================================================
```

**Orden recomendado:** 1 → 2 → 3 → 4 → 10.

Al cargar un archivo, presione **ENTER** para usar la ruta por defecto
(`entrada/<archivo>.lfp`) o escriba una ruta distinta.

---

## Formato de los archivos de entrada

**`sudokus.lfp`** — `id_sudoku,dificultad,tablero`

```
1,Facil,307026050040310269926845173063050081059078002000200090084600020000002007000084006
```

- `dificultad`: `Facil`, `Media`, `Dificil` o `Experto`
- `tablero`: 81 dígitos recorridos fila por fila; `0` = celda vacía

**`jugadores.lfp`** — `carnet,nombre,apellido,nivel`

```
202011234,Diego,Fuentes,Intermedio
```

- `nivel`: `Principiante`, `Intermedio` o `Experto`

**`intentos.lfp`** — `carnet,id_sudoku,solucion,tiempo_segundos,fecha`

```
202011234,1,317926458845317269926845173263459781459178632178263594784631925631592847592784316,213,20-03-2026
```

- `solucion`: 81 dígitos (1–9) en el mismo orden de recorrido
- `fecha`: formato `DD-MM-AAAA`

---

## Mecánica de validación

Cada intento se califica revisando **27 unidades**: 9 filas, 9 columnas y 9 cajas
de 3×3. Una unidad es válida si contiene los dígitos del 1 al 9 sin repetirse.

```
porcentaje_validez = (filas válidas + columnas válidas + cajas válidas) / 27 × 100
```

Adicionalmente se verifica que las **pistas originales** (celdas distintas de `0`
en el tablero publicado) no hayan sido modificadas. Un intento se marca como
*resuelto correctamente* solo si cumple ambas condiciones:

1. `porcentaje_validez == 100%`
2. Todas las pistas originales se respetaron

Ejemplo de salida de la opción 4:

```
CARNET     SUDOKU  VALIDEZ   TIEMPO   RESULTADO
----------------------------------------------------------
202011234  1       100.00%   213s     Resuelto correctamente
202017890  1       88.89%    245s     Cambio 1 pista(s) del tablero original
202017890  2       66.67%    184s     Incompleto: 9 de 27 unidades con error
```

---

## Reportes generados

| Archivo | Contenido |
|---|---|
| `reporte_resumen_sudokus.html` | Por tablero: dificultad declarada y real, pistas, intentos, tiempo promedio, validez promedio y tasa de éxito |
| `reporte_rendimiento_jugadores.html` | Por jugador: nombre, carnet, nivel, tableros intentados, validez promedio, tiempo promedio y tableros perfectos |
| `reporte_top_tiempos.html` | Top 10 mejores tiempos entre los intentos con 100% de validez |
| `reporte_sudokus_dificiles.html` | Tableros ordenados por menor tasa de éxito, contrastando dificultad declarada vs. observada |
| `reporte_analisis_nivel.html` | Desempeño agrupado por nivel de experiencia del jugador |

Los reportes usan solo etiquetas básicas de HTML (`h1`, `p`, `table`, `tr`,
`th`, `td`), sin hojas de estilo. La cuadrícula la dibuja el atributo
`border='1'` de la tabla. Al no depender de ningún recurso externo, se pueden
abrir o enviar tal cual.

La **dificultad real** se infiere de la tasa de éxito observada:

| Tasa de éxito | Dificultad observada |
|---|---|
| ≥ 80% | Facil |
| ≥ 60% | Media |
| ≥ 40% | Dificil |
| < 40% | Experto |

---

## Manejo de errores

Las líneas mal formadas **no detienen la carga**: se descartan y se reportan al
final con su número de línea y el motivo.

```
Intentos cargados correctamente: 55
Registros descartados por formato incorrecto: 3
  - Linea 56: la solucion debe tener 81 digitos y tiene 5
  - Linea 57: el tiempo 'abc' no es un numero entero
  - Linea 58: la fecha '2026-03-16' no tiene el formato DD-MM-AAAA
```

Validaciones implementadas:

- Cantidad de campos por registro
- Tipos de dato (carnet, id y tiempo enteros; fecha `DD-MM-AAAA`)
- Dominios cerrados (dificultad y nivel)
- Identificadores duplicados
- Longitud exacta de 81 dígitos en tableros y soluciones
- Archivo inexistente
- Intentos que apuntan a un carnet o a un sudoku que no existe (se descartan al calificar)

---

## Documentación

| Documento | Archivo |
|---|---|
| Manual Técnico | [`MANUAL_TECNICO.md`](MANUAL_TECNICO.md) |
| Manual de Usuario | [`MANUAL_USUARIO.md`](MANUAL_USUARIO.md) |
| Diagrama de Flujo | [`DIAGRAMA_FLUJO.md`](DIAGRAMA_FLUJO.md) |
| Informe de Desarrollo | [`INFORME_DESARROLLO.md`](INFORME_DESARROLLO.md) |

---

## Conceptos de programación utilizados

| Concepto | Dónde se usa |
|---|---|
| Clases y objetos | `clases.py`: Tablero, Jugador e Intento |
| Listas y listas anidadas (matrices) | La matriz 9×9 de cada tablero |
| Diccionarios | Agrupación de estadísticas en `reportes.py` |
| Ciclo `while` | Menú principal, relleno de espacios |
| Ciclo `for` con `range` | Recorridos de índices 0 a 8 |
| Ciclos `for` anidados | Construcción de la matriz y revisión de pistas |
| Condicionales `if / elif / else` | Validaciones y opciones del menú |
| Lectura de archivos | `with open(...)` y `readlines()` en `lectura.py` |
| Manejo de cadenas | `split(',')`, `strip()`, `isdigit()`, concatenación |
| Método de ordenamiento burbuja | `reportes.py`, para ordenar jugadores y tiempos |
| Escritura de archivos | Generación de los HTML |
