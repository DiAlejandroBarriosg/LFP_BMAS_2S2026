# MarkdownCheck

Analizador léxico-sintáctico de un subconjunto de Markdown, escrito en Python
sin librerías de parsing ni de conversión. Lee un archivo `.md`, lo analiza
con un autómata finito determinista (AFD) escrito a mano y un parser
descendente recursivo, y traduce el documento a HTML **recorriendo su árbol
de derivación**.

Proyecto 2 — Lenguajes Formales y de Programación, Facultad de Ingeniería,
Universidad de San Carlos de Guatemala. Segundo semestre 2026, sección B+.

**Autor:** Diego Alejandro Barrios — carné 201900158

## Qué hace

- **Análisis léxico:** un AFD manual, sin el módulo `re`, con tokens
  virtuales `INDENT`/`DEDENT` para el anidamiento de listas y modo literal
  para los bloques de código.
- **Análisis sintáctico:** un parser descendente recursivo con una función
  por cada no terminal de una gramática LL(1) y recuperación de errores en
  modo pánico. Reporta todos los errores en una sola pasada.
- **Reportes HTML,** generados a partir del árbol:
  1. el documento traducido a HTML;
  2. estadísticas del documento;
  3. tabla de contenido con enlaces al Reporte 1.
- **Tabla de tokens, tabla de errores** y el **árbol de derivación** en
  Graphviz (`arbol.dot`).
- **Interfaz gráfica** en Tkinter: editor con números de línea, tablas,
  árbol navegable y acceso directo a los reportes.
- **Alcance opcional completo:** listas numeradas, listas de tareas,
  tachado, enlaces, imágenes y tablas (con su léxico, gramática y
  traducción); **vista previa en vivo** del documento en la ventana;
  **advertencia de anidamiento** con un máximo configurable; y **resaltado
  de sintaxis** de los bloques de código en el Reporte 1 con highlight.js,
  incluido en el proyecto para que funcione sin internet.

## Requisitos

| Dependencia | Versión | Uso |
|---|---|---|
| Python | 3.10 o superior | Ejecución. Se probó con 3.10, 3.12 y 3.13. |
| Tkinter | incluido con Python en Windows | Interfaz gráfica. En Linux: `sudo apt install python3-tk`. |
| Graphviz | cualquiera (opcional) | Convertir `arbol.dot` en `arbol.png`. Sin Graphviz, todo lo demás funciona. |

No usa paquetes externos: no hace falta instalar nada con `pip`. El
resaltado de sintaxis usa highlight.js 11.9.0 (licencia BSD-3), que ya viene
en `src/reportes/recursos/`.

## Ejecución

Desde la carpeta `Proyecto2`:

```bash
python src/main.py                              # abre la ventana vacía
python src/main.py examples/ejemplo_valido.md   # abre ese archivo
```

En la ventana: **Abrir .md** (Ctrl+O) y **Analizar** (F5). Las pestañas
muestran la tabla de tokens, la tabla de errores y el árbol de derivación.
Los botones de la barra abren los reportes, que se guardan en
`salida/<nombre del archivo>/`.

En Visual Studio Code, la carpeta `.vscode` trae configuraciones listas en
**Ejecutar y depurar** (Ctrl+Shift+D): la ventana, el ejemplo y cada suite de
pruebas.

La guía completa, con capturas, está en
[docs/Manual_Usuario.pdf](docs/Manual_Usuario.pdf).

## Estructura

```
Proyecto2/
├── src/
│   ├── main.py                    punto de entrada
│   ├── lexico/                    alfabeto, Token y AnalizadorLexico (AFD)
│   ├── sintactico/                NodoAST y AnalizadorSintactico
│   ├── errores/                   ErrorAnalisis y GestorErrores
│   ├── reportes/                  generadores de los reportes y de arbol.dot
│   │   └── recursos/              highlight.js para el Reporte 1
│   └── gui/                       VentanaPrincipal y VistaPrevia (Tkinter)
├── tests/                         pruebas desde consola, una suite por fase
├── examples/                      archivos .md de entrada
│   └── casos/                     los 15 casos de prueba documentados
├── docs/
│   ├── Manual_Tecnico.pdf
│   ├── Manual_Usuario.pdf
│   ├── Casos_de_Prueba.pdf
│   ├── diseno/                    diseño de la gramática y del AFD
│   ├── manual_tecnico/            fuente del Manual Técnico
│   ├── manual_usuario/            fuente del Manual de Usuario y capturas
│   └── casos_de_prueba/           informe generado por tests/prueba_casos.py
├── README.md
└── .gitignore
```

## Pruebas

Desde la carpeta `Proyecto2`:

```bash
python tests/prueba_lexico.py        # analizador léxico (AFD): 109 verificaciones
python tests/prueba_sintactico.py    # parser descendente recursivo: 101
python tests/prueba_reportes.py      # reportes y arbol.dot: 76
python tests/prueba_interfaz.py      # la ventana, sin hacer clic: 37
python tests/prueba_casos.py         # los 15 casos documentados: 82

python tests/ver_tokens.py examples/ejemplo_valido.md   # tabla de tokens en consola
python tests/ver_arbol.py examples/ejemplo_valido.md    # árbol de derivación en consola
```

Cada suite imprime `[OK]` o `[FALLO]` por verificación y termina con un
resumen. `prueba_casos.py` además regenera el informe
`docs/casos_de_prueba/casos_de_prueba.html`.

## Documentación

| Documento | Contenido |
|---|---|
| [Manual Técnico](docs/Manual_Tecnico.pdf) | Arquitectura, diagrama de clases, AFD, gramática, parser, recuperación de errores y decisiones de diseño. |
| [Manual de Usuario](docs/Manual_Usuario.pdf) | Instalación, uso de la ventana, sintaxis soportada, errores, reportes, vista previa y advertencia de anidamiento. |
| [Casos de Prueba](docs/Casos_de_Prueba.pdf) | 15 casos con entrada, resultado esperado y resultado obtenido. |
| [Diseño](docs/diseno/01_Diseno_Gramatica_AFD.md) | Documento de trabajo con los tokens, el AFD, la gramática y las 36 decisiones de diseño. |

Para regenerar un PDF después de cambiar una captura o un texto: abra el
`.html` correspondiente (`docs/manual_usuario/manual_usuario.html`,
`docs/manual_tecnico/manual_tecnico.html` o
`docs/casos_de_prueba/casos_de_prueba.html`) en el navegador e imprímalo
con **Guardar como PDF**, activando **Gráficos de fondo**.
