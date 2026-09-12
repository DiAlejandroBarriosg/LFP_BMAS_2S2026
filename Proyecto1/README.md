# HorarioScript

Analizador lexico para el lenguaje `.hor`, con interfaz grafica, deteccion de
choques de horario y generacion de reportes HTML.

**Proyecto 1** &mdash; Lenguajes Formales y de Programacion
Escuela de Ingenieria en Ciencias y Sistemas, Facultad de Ingenieria
Universidad de San Carlos de Guatemala &middot; Segundo semestre 2026

| | |
|---|---|
| Estudiante | Diego Alejandro Barrios |
| Carne | 201900158 |
| Seccion | B+ |
| Tutor | SamuelAguilar18 |

---

## Requisitos

- Python 3.10 o superior
- Tkinter (viene incluido en el instalador oficial de Python para Windows y
  macOS; en Debian o Ubuntu: `sudo apt install python3-tk`)
- Graphviz, **solo opcional**, para convertir los archivos `.dot` en imagen

No se usan librerias externas. No hay `pip install` que correr.

## Como ejecutar

```bash
python main.py                              # abre la ventana vacia
python main.py entradas/horario_completo.hor  # abre y analiza un archivo
```

En VS Code hay cuatro configuraciones listas en `.vscode/launch.json`:
presiona F5 y elegi la que quieras.

## Ejemplos de uso

### Un archivo valido

Entrada (`entradas/horario_valido.hor`):

```
## Horario Lenguajes Formales - Segundo Semestre 2026
HORARIO {
    CURSOS {
        curso: "Lenguajes Formales y de Programacion" [codigo: "LFP-0796", creditos: 4],
    };
    CATEDRATICOS {
        catedratico: "Otto Rodriguez" [codigo: "DOC-001", categoria: TITULAR],
    };
    AULAS {
        aula: "A-101" [capacidad: 40, edificio: "T-3"],
    };
    CLASES {
        clase: "LFP-0796" con "DOC-001" en "A-101" [dia: LUNES, inicio: 07:00, fin: 08:40, seccion: "N"],
    };
};
```

Resultado en la barra de estado:

```
149 tokens, 0 errores lexicos, 0 avisos, 0 choques   |   1.12 ms
```

La tabla de tokens muestra cada pieza con su posicion:

| No. | Lexema | Tipo de token | Linea | Columna |
|---|---|---|---|---|
| 4 | `HORARIO` | RESERVADA_BLOQUE | 2 | 1 |
| 10 | `"Lenguajes Formales y de Programacion"` | CADENA | 4 | 16 |
| 14 | `"LFP-0796"` | CODIGO | 4 | 64 |
| 20 | `07:00` | HORA | 15 | 84 |

### Un archivo con errores

Entrada:

```
curso: "Compiladores 1" [codigo: "CMP-", creditos: 4],
clase: "CMP-0901" con "DOC-003" en "B-202" [dia: LUNEZ, inicio: 05:30, fin: 07:75, seccion: "A"],
```

El analisis no se detiene en el primer error. Salida:

| No. | Lexema | Tipo de error | Linea | Columna |
|---|---|---|---|---|
| 1 | `"CMP-"` | CODIGO_MAL_FORMADO | 4 | 42 |
| 2 | `LUNEZ` | DIA_NO_RECONOCIDO | 16 | 58 |
| 3 | `05:30` | HORA_FUERA_DE_RANGO | 16 | 73 |
| 4 | `07:75` | HORA_FUERA_DE_RANGO | 16 | 85 |

### Un choque de horario

Entrada:

```
clase: "LFP-0796" con "DOC-001" en "A-101" [dia: LUNES, inicio: 07:00, fin: 08:40, seccion: "N"],
clase: "BD2-0812" con "DOC-001" en "LAB-3" [dia: LUNES, inicio: 07:00, fin: 08:40, seccion: "A"],
```

`DOC-001` no puede estar en dos aulas a la vez. El programa reporta:

```
[C1] LUNES 07:00-08:40 | mismo catedratico (DOC-001) | LFP-0796 (L22) vs BD2-0812 (L23)
```

Y propone bloques libres del mismo dia para reprogramar:

```
LFP-0796  seccion N  LUNES 07:00-08:40
    libre: 08:40 - 10:20
    libre: 09:00 - 10:40
    libre: 09:20 - 11:00
```

En cambio, una clase que termina 08:40 y otra que empieza 08:40 con el mismo
catedratico **no** se reporta como choque: es continuidad, no conflicto.

## Pruebas desde consola

Cada capa se puede verificar por separado, sin abrir la interfaz:

```bash
python pruebas_casos.py        # los 8 casos de prueba con aserciones
python pruebas_consola.py      # motor lexico: tokens y errores
python pruebas_estructura.py   # objetos del horario y avisos
python pruebas_choques.py      # choques y bloques libres sugeridos
python pruebas_reportes.py     # genera los HTML en salida/
```

## Estructura

```
Proyecto1/
├── main.py                     punto de entrada
├── analizador/
│   ├── alfabeto.py             pertenencia al alfabeto (sin str.isX ni re)
│   ├── palabras_reservadas.py  catalogo de tokens y tipos de error
│   ├── analizador_lexico.py    el AFD, implementado a mano
│   └── gestor_errores.py       acumulacion de errores en modo panico
├── modelos/
│   ├── token.py                Token
│   ├── error_lexico.py         ErrorLexico
│   ├── elementos.py            Curso, Catedratico, Aula, Clase, Aviso
│   └── choque.py               Choque
├── logica/
│   ├── estructurador.py        del flujo de tokens a los objetos
│   └── detector_choques.py     traslapes y sugerencia de reprogramacion
├── reportes/
│   ├── estilos.py              CSS embebido y umbrales
│   ├── generador.py            los cuatro reportes HTML
│   └── graficador.py           codigo DOT de la jerarquia
├── gui/
│   └── interfaz.py             ventana Tkinter
├── entradas/                   archivos .hor de prueba
├── diseno/                     diagramas: AFD y clases (DOT y PNG)
├── docs/                       manuales y casos de prueba
├── capturas/                   capturas para los manuales
└── salida/                     reportes generados (no se versiona)
```

El punto importante de la arquitectura: `analizador/` no sabe nada de horarios
ni de choques, solo produce tokens. Toda la semantica vive en `logica/`. Esa
separacion permite reutilizar el motor lexico en el Proyecto 2.

## Archivos de prueba

| Archivo | Para que sirve |
|---|---|
| `horario_valido.hor` | El ejemplo del enunciado. 149 tokens, cero errores. |
| `horario_errores.hor` | Los cinco tipos de error lexico, uno por linea. |
| `horario_choques.hor` | Choques mas codigo duplicado y referencias inexistentes. |
| `horario_choques_borde.hor` | Casos borde del detector: contencion, doble motivo, dia saturado. |
| `horario_completo.hor` | Horario realista. Cubre los cuatro niveles de carga y un aula sobre el 80%. |

## Reportes generados

Salen en `salida/` y se abren en cualquier navegador sin conexion a internet:

1. `reporte1_horario_semanal.html` &mdash; rejilla Lunes a Sabado por seccion
2. `reporte2_carga_catedraticos.html` &mdash; horas semanales y nivel de carga
3. `reporte3_estadistico.html` &mdash; indicadores y ocupacion por aula
4. `reporte_errores.html` &mdash; errores lexicos, avisos y frecuencia de tokens
5. `jerarquia_horario.dot` &mdash; grafo de la jerarquia del horario

Para convertir un `.dot` en imagen:

```bash
dot -Tpng salida/jerarquia_horario.dot -o salida/jerarquia_horario.png
dot -Tpng diseno/afd_horarioscript.dot -o diseno/afd_horarioscript.png
dot -Tpng diseno/diagrama_clases.dot -o diseno/diagrama_clases.png
```

## Documentacion

| Documento | Ruta |
|---|---|
| Manual Tecnico | `docs/MANUAL_TECNICO.md` |
| Manual de Usuario | `docs/MANUAL_USUARIO.md` |
| Casos de Prueba | `docs/CASOS_DE_PRUEBA.md` |
| Registro de la ultima corrida de pruebas | `docs/salida_casos.txt` |

## Restricciones respetadas

El enunciado prohibe el modulo `re` y las funciones de alto nivel de cadenas
para la tokenizacion. En `analizador/`, `logica/` y `modelos/` no aparece
`re`, `split`, `find`, `strip`, `replace`, `join`, `isdigit`, `isalpha` ni
`int()`: todo se resuelve con indexacion caracter por caracter y comparacion
de codigos con `ord()`. Se puede verificar asi:

```bash
grep -rnE "import re|\.split\(|\.find\(|\.strip\(|\.isdigit\(" analizador/ logica/ modelos/
```

La unica coincidencia esperada es `os.path.join`, que es manejo de rutas de
archivo, no manipulacion de cadenas.

El alfabeto esta declarado como listas explicitas de caracteres en
`analizador/alfabeto.py`. Para aceptar un caracter nuevo se agrega a la lista
que corresponda y no hay que modificar ninguna funcion: agregar `'_'` a
`EXTRA_PALABRA` habilita identificadores como `mi_curso`, y agregar `'('` y
`')'` a `SIMBOLOS` los vuelve simbolos validos del lenguaje.
