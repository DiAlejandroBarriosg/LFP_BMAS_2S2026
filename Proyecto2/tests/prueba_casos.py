# -*- coding: utf-8 -*-
"""
prueba_casos.py
Ejecuta los casos de prueba documentados (examples/casos/) y genera el
documento de casos de prueba.

Uso, desde la carpeta Proyecto2:
    python tests/prueba_casos.py

Para cada caso se corre el programa completo (lexico, parser y reportes) y
se compara cada RESULTADO ESPERADO, escrito a mano abajo, con el RESULTADO
OBTENIDO al ejecutar. Ademas de imprimir [OK] o [FALLO], escribe
docs/casos_de_prueba/casos_de_prueba.html con la entrada, lo esperado y lo
obtenido de cada caso. Ese HTML se imprime a PDF desde el navegador
(Ctrl+P, "Guardar como PDF").
"""

import os
import sys

CARPETA_TESTS = os.path.dirname(os.path.abspath(__file__))
CARPETA_PROYECTO = os.path.dirname(CARPETA_TESTS)
sys.path.insert(0, os.path.join(CARPETA_PROYECTO, 'src'))

from lexico.analizador_lexico import AnalizadorLexico
from lexico.token import FIN
from sintactico.analizador_sintactico import AnalizadorSintactico
from errores.gestor_errores import GestorErrores
from reportes.generador_html import GeneradorHTML
from reportes.generador_estadisticas import GeneradorEstadisticas
from reportes.generador_indice import GeneradorIndice
from reportes.generador_reportes import generar_todos
from reportes.plantilla import escapar, CSS

CARPETA_CASOS = os.path.join(CARPETA_PROYECTO, 'examples', 'casos')
CARPETA_SALIDA = os.path.join(CARPETA_PROYECTO, 'salida', 'casos')
CARPETA_DOCUMENTO = os.path.join(CARPETA_PROYECTO, 'docs',
                                 'casos_de_prueba')

L = 'Léxico'
S = 'Sintáctico'

# ======================================================================
# Definicion de los casos
# Cada verificacion es: [descripcion, que se mide, parametro, esperado]
# ======================================================================

CASOS = [
    {
        'archivo': 'caso01_documento_valido.md',
        'titulo': 'Documento válido con todos los elementos obligatorios',
        'categoria': 'Válido',
        'objetivo': 'Archivo de la sección 4.7 del enunciado. Contiene '
                    'encabezados, párrafo con negrita, cursiva y código en '
                    'línea, lista de 3 niveles, cita de 2 niveles, bloque de '
                    'código y regla horizontal. Debe analizarse sin errores '
                    'y producir los tres reportes.',
        'verificaciones': [
            ['Errores', 'errores', None, []],
            ['Cantidad de tokens', 'cantidad_tokens', None, 77],
            ['Bloques reconocidos, en orden', 'bloques', None,
             ['<encabezado>', '<parrafo>', '<encabezado>', '<lista>',
              '<cita>', '<bloque_codigo>', '<regla_horizontal>',
              '<parrafo>']],
            ['Profundidad máxima de lista', 'estadistica',
             'profundidad_listas', 3],
            ['Profundidad máxima de cita', 'estadistica',
             'profundidad_citas', 2],
            ['Palabras (Reporte 2 del enunciado)', 'estadistica',
             'palabras', 67],
            ['Archivos generados', 'reportes', None,
             ['documento', 'estadisticas', 'indice', 'arbol']],
            ['La frontera del árbol son todos los tokens', 'frontera',
             None, True],
        ],
    },
    {
        'archivo': 'caso02_lista_profunda.md',
        'titulo': 'Lista con 4 niveles de anidamiento',
        'categoria': 'Anidamiento',
        'objetivo': 'Una lista que baja hasta el nivel 4, sube un nivel, '
                    'vuelve dos niveles de golpe y tiene formato dentro de '
                    'un ítem. La jerarquía del HTML debe ser exactamente la '
                    'del archivo.',
        'verificaciones': [
            ['Errores', 'errores', None, []],
            ['Ítems de lista', 'estadistica', 'items', 8],
            ['Profundidad máxima de lista', 'estadistica',
             'profundidad_listas', 4],
            ['HTML de la lista (Reporte 1)', 'html_bloque', 1,
             '<ul><li>Nivel 1: Lenguajes formales<ul><li>Nivel 2: '
             'Gramáticas<ul><li>Nivel 3: Libres de contexto<ul><li>Nivel '
             '4: Recursivas por la derecha</li></ul></li><li>Nivel 3: '
             'Regulares</li></ul></li></ul></li><li>Nivel 1 otra vez, con '
             '<strong>negrita</strong> (vuelve dos niveles de golpe)<ul>'
             '<li>Nivel 2</li></ul></li><li>Último ítem</li></ul>'],
            ['Tokens de la línea 8 (bajan 2 niveles)', 'tipos_linea', 8,
             ['DEDENT', 'DEDENT', 'VIÑETA', 'TEXTO', 'NEGRITA', 'TEXTO',
              'NEGRITA', 'TEXTO', 'SALTO_LINEA']],
        ],
    },
    {
        'archivo': 'caso03_citas_anidadas.md',
        'titulo': 'Citas anidadas en 3 niveles',
        'categoria': 'Anidamiento',
        'objetivo': 'Citas de nivel 1, 2 y 3, con las dos notaciones (">>" '
                    'y "> >"), un encabezado dentro de la cita y el regreso '
                    'al primer nivel.',
        'verificaciones': [
            ['Errores', 'errores', None, []],
            ['Profundidad máxima de cita', 'estadistica',
             'profundidad_citas', 3],
            ['Líneas de cita', 'estadistica', 'lineas_cita', 6],
            ['HTML de la cita (Reporte 1)', 'html_bloque', 0,
             '<blockquote><h1 id="seccion-1">Cita con encabezado</h1><p>'
             'Primer nivel de la cita.</p><blockquote><p>Segundo nivel.</p>'
             '<p>Segundo nivel escrito con espacio.</p><blockquote><p>'
             'Tercer nivel, con <em>cursiva</em>.</p></blockquote>'
             '</blockquote><p>De vuelta al primer nivel.</p></blockquote>'],
            ['Lexema de la línea 4 ("> >" es nivel 2)', 'firmas_linea', 4,
             ['CITA "> >" 4:1', 'TEXTO "Segundo nivel escrito con '
              'espacio." 4:5', 'SALTO_LINEA "\\n" 4:39']],
        ],
    },
    {
        'archivo': 'caso04_formato_combinado.md',
        'titulo': 'Negrita, cursiva y código combinados',
        'categoria': 'Válido',
        'objetivo': 'Cursiva dentro de negrita, negrita dentro de cursiva, '
                    '"***", código en línea cuyo contenido no se '
                    'interpreta, y una negrita que empieza en una línea de '
                    'un párrafo y se cierra en la siguiente.',
        'verificaciones': [
            ['Errores', 'errores', None, []],
            ['HTML del párrafo 2', 'html_bloque', 1,
             '<p><strong>Negrita con <em>cursiva</em> adentro</strong> y '
             '<em>cursiva con <strong>negrita</strong> adentro</em>.</p>'],
            ['HTML del párrafo 3 ("***")', 'html_bloque', 2,
             '<p><strong><em>Negrita y cursiva a la vez</em></strong></p>'],
            ['HTML del párrafo 4 (código)', 'html_bloque', 3,
             '<p><code>**esto es código, no negrita**</code></p>'],
            ['HTML del párrafo 6 (negrita en dos líneas)', 'html_bloque',
             5, '<p>Esta negrita <strong>empieza en una línea\ny se cierra '
                'en la siguiente</strong> del mismo párrafo.</p>'],
            ['Tramos de negrita', 'estadistica', 'negritas', 7],
            ['Tramos de cursiva', 'estadistica', 'cursivas', 4],
            ['Tramos de código en línea', 'estadistica', 'codigos_inline',
             2],
        ],
    },
    {
        'archivo': 'caso05_delimitadores_sin_cerrar.md',
        'titulo': 'Negrita, cursiva y código en línea sin cerrar',
        'categoria': 'Error léxico',
        'objetivo': 'Un párrafo de tres líneas que abren un delimitador y '
                    'nunca lo cierran. Al terminar el párrafo, cada error '
                    'se reporta en su posición de apertura, y el análisis '
                    'continúa: el párrafo siguiente se reconoce bien.',
        'verificaciones': [
            ['Errores (tipo línea:columna)', 'errores', None,
             ['NEGRITA_SIN_CERRAR 3:17', 'CURSIVA_SIN_CERRAR 4:11',
              'CODIGO_INLINE_SIN_CERRAR 5:13']],
            ['Fase de los errores', 'fases', None, [L, L, L]],
            ['La línea 7 se sigue reconociendo', 'tipos_linea', 7,
             ['TEXTO', 'NEGRITA', 'TEXTO', 'NEGRITA', 'TEXTO',
              'SALTO_LINEA']],
            ['Archivos generados', 'reportes', None, ['errores', 'arbol']],
        ],
    },
    {
        'archivo': 'caso06_encabezados.md',
        'titulo': 'Encabezado inválido (más de 6 "#")',
        'categoria': 'Error léxico',
        'objetivo': 'H1 y H6 válidos, un encabezado con 7 "#" (error) y '
                    '"#sinespacio", que no es error sino texto.',
        'verificaciones': [
            ['Errores', 'errores', None, ['ENCABEZADO_INVALIDO 3:1']],
            ['Línea 2: H6 válido', 'tipos_linea', 2,
             ['NUMERAL', 'TEXTO', 'SALTO_LINEA']],
            ['Línea 4: "#sinespacio" es texto', 'tipos_linea', 4,
             ['TEXTO', 'SALTO_LINEA']],
            ['Mensaje del error', 'mensaje', 0,
             'Encabezado inválido en línea 3: máximo 6 niveles'],
        ],
    },
    {
        'archivo': 'caso07_codigo_sin_cerrar.md',
        'titulo': 'Bloque de código sin cerrar',
        'categoria': 'Error léxico',
        'objetivo': 'Un bloque abierto con "```python" que llega al final '
                    'del archivo. Su contenido tiene "#" y "**", que no '
                    'deben producir otros errores porque el bloque se '
                    'analiza en modo literal.',
        'verificaciones': [
            ['Errores', 'errores', None, ['BLOQUE_CODIGO_SIN_CERRAR 3:1']],
            ['Líneas literales del bloque', 'contar_tipo', 'TEXTO_LITERAL',
             2],
            ['Mensaje del error', 'mensaje', 0,
             'Bloque de código sin cerrar iniciado en línea 3'],
            ['El análisis llega a FIN', 'ultimo_token', None, FIN],
        ],
    },
    {
        'archivo': 'caso08_indentacion.md',
        'titulo': 'Indentación inconsistente',
        'categoria': 'Error sintáctico',
        'objetivo': 'Un salto de 0 a 4 espacios (sintáctico), una sangría '
                    'impar de 3 espacios (léxico) y una sublista sin ítem '
                    'padre después de una línea vacía (sintáctico).',
        'verificaciones': [
            ['Errores', 'errores', None,
             ['INDENTACION_INVALIDA 2:3', 'INDENTACION_INVALIDA 4:4',
              'INDENTACION_INVALIDA 6:1']],
            ['Fase de cada error', 'fases', None, [S, L, S]],
            ['El árbol conserva todos los tokens (INDENT y DEDENT '
             'balanceados)', 'frontera', None, True],
        ],
    },
    {
        'archivo': 'caso09_citas_mal_formadas.md',
        'titulo': 'Citas mal formadas',
        'categoria': 'Error sintáctico',
        'objetivo': 'Un ">" sin espacio en los niveles 1 y 2, con las dos '
                    'notaciones, intercalado con líneas bien formadas.',
        'verificaciones': [
            ['Errores', 'errores', None,
             ['CITA_MAL_FORMADA 1:1', 'CITA_MAL_FORMADA 3:2',
              'CITA_MAL_FORMADA 5:3']],
            ['Fase de los errores', 'fases', None, [S, S, S]],
            ['Mensaje del primer error', 'mensaje', 0,
             'Cita mal formada en línea 1, columna 1'],
        ],
    },
    {
        'archivo': 'caso10_ambiguedades.md',
        'titulo': 'Casos borde: reglas de prioridad del AFD',
        'categoria': 'Caso borde',
        'objetivo': 'Viñeta contra cursiva, viñeta contra regla '
                    'horizontal, "#" sin espacio, maximal munch de "**" y '
                    '"*" dentro de código en línea.',
        'verificaciones': [
            ['Errores', 'errores', None, []],
            ['"* Viñeta" es VIÑETA', 'tipos_linea', 1,
             ['VIÑETA', 'TEXTO', 'SALTO_LINEA']],
            ['"*cursiva*" es CURSIVA', 'tipos_linea', 2,
             ['CURSIVA', 'TEXTO', 'CURSIVA', 'SALTO_LINEA']],
            ['"- - -" es VIÑETA', 'tipos_linea', 3,
             ['VIÑETA', 'TEXTO', 'SALTO_LINEA']],
            ['"---" es REGLA_HORIZONTAL', 'tipos_linea', 4,
             ['REGLA_HORIZONTAL', 'SALTO_LINEA']],
            ['"#sinespacio" es TEXTO', 'tipos_linea', 5,
             ['TEXTO', 'SALTO_LINEA']],
            ['"**" es NEGRITA antes que dos CURSIVA', 'tipos_linea', 6,
             ['NEGRITA', 'TEXTO', 'NEGRITA', 'TEXTO', 'CURSIVA', 'TEXTO',
              'CURSIVA', 'SALTO_LINEA']],
            ['"*" dentro de código no es cursiva', 'tipos_linea', 7,
             ['CODIGO_INLINE', 'TEXTO_LITERAL', 'CODIGO_INLINE', 'TEXTO',
              'SALTO_LINEA']],
        ],
    },
    {
        'archivo': 'caso11_sin_encabezados.md',
        'titulo': 'Documento sin encabezados',
        'categoria': 'Caso borde',
        'objetivo': 'El Reporte 3 debe indicar explícitamente que no hay '
                    'encabezados, en vez de mostrarse vacío.',
        'verificaciones': [
            ['Errores', 'errores', None, []],
            ['Encabezados', 'estadistica', 'encabezados', 0],
            ['El Reporte 3 lo dice explícitamente',
             'indice_sin_encabezados', None, True],
            ['Palabras', 'estadistica', 'palabras', 11],
        ],
    },
    {
        'archivo': 'caso12_windows_bom_sin_salto.md',
        'titulo': 'Archivo de Windows: BOM, \\r\\n y sin salto final',
        'categoria': 'Caso borde',
        'objetivo': 'Archivo guardado con marca BOM, fines de línea "\\r\\n" '
                    'y sin salto de línea al final. Las posiciones deben '
                    'ser las mismas que con un archivo normal.',
        'verificaciones': [
            ['Errores', 'errores', None, []],
            ['Línea 1 (la BOM no ocupa columna)', 'firmas_linea', 1,
             ['NUMERAL "#" 1:1', 'TEXTO "Título" 1:3',
              'SALTO_LINEA "\\n" 1:9']],
            ['Línea 3 (SALTO_LINEA virtual al final)', 'firmas_linea', 3,
             ['TEXTO "Texto final sin salto de línea" 3:1',
              'SALTO_LINEA "(virtual)" 3:31', 'FIN "(virtual)" 3:31']],
            ['HTML (Reporte 1)', 'html', None,
             '<h1 id="seccion-1">Título</h1>\n'
             '<p>Texto final sin salto de línea</p>\n'],
        ],
    },
    {
        'archivo': 'caso13_errores_multiples.md',
        'titulo': 'Todas las categorías de error en una sola pasada',
        'categoria': 'Recuperación',
        'objetivo': 'Un archivo con las 7 categorías de error de la sección '
                    '4.9. El análisis no se detiene en el primero (modo '
                    'pánico): los reporta todos, ordenados por posición.',
        'verificaciones': [
            ['Errores', 'errores', None,
             ['NEGRITA_SIN_CERRAR 3:11', 'CURSIVA_SIN_CERRAR 4:11',
              'CODIGO_INLINE_SIN_CERRAR 5:11', 'ENCABEZADO_INVALIDO 6:1',
              'INDENTACION_INVALIDA 8:3', 'CITA_MAL_FORMADA 9:1',
              'BLOQUE_CODIGO_SIN_CERRAR 12:1']],
            ['Fase de cada error', 'fases', None, [L, L, L, L, S, S, L]],
            ['El análisis llega a FIN', 'ultimo_token', None, FIN],
            ['La frontera del árbol son todos los tokens', 'frontera',
             None, True],
            ['Archivos generados', 'reportes', None, ['errores', 'arbol']],
        ],
    },
    {
        'archivo': 'caso14_alcance_opcional.md',
        'titulo': 'Alcance opcional: listas numeradas, tareas, tachado, '
                  'enlaces, imágenes, tablas y resaltado',
        'categoria': 'Alcance opcional',
        'objetivo': 'Un documento válido que usa todo el alcance opcional '
                    'de la sección 4.2: lista numerada con tareas, tachado, '
                    'un enlace con cursiva adentro, una tabla con las tres '
                    'alineaciones, una imagen y un bloque de código que el '
                    'Reporte 1 colorea con highlight.js.',
        'verificaciones': [
            ['Errores', 'errores', None, []],
            ['HTML del párrafo (tachado y enlace)', 'html_bloque', 1,
             '<p>Este archivo usa todo lo opcional: <del>nada '
             'obligatorio</del> y un enlace a la\n<a href="https://docs.'
             'python.org/3/">documentación de <em>Python</em></a>.</p>'],
            ['HTML de la lista numerada con tareas', 'html_bloque', 3,
             '<ol><li>Diseñar la gramática</li><li>Programar el <strong>'
             'parser</strong><ul><li class="tarea"><input type="checkbox" '
             'disabled checked> Funciones de bloques</li><li class="tarea">'
             '<input type="checkbox" disabled> Funciones en línea</li></ul>'
             '</li><li>Probar los casos</li></ol>'],
            ['Encabezado de la tabla y su alineación', 'html_contiene',
             '<thead><tr><th style="text-align: left">Token</th><th style='
             '"text-align: center">Ejemplo</th><th style="text-align: '
             'right">Fase</th></tr></thead>', True],
            ['HTML de la imagen', 'html_bloque', 6,
             '<p><img src="../../docs/diseno/afd_markdowncheck.png" '
             'alt="Diagrama del AFD"></p>'],
            ['Listas numeradas, tareas y tareas hechas', 'estadisticas',
             ['listas_numeradas', 'tareas', 'tareas_hechas'], [1, 2, 1]],
            ['Tachados, enlaces, imágenes y tablas', 'estadisticas',
             ['tachados', 'enlaces', 'imagenes', 'tablas'], [1, 1, 1, 1]],
            ['Palabras (la imagen no cuenta)', 'estadistica', 'palabras', 50],
            ['El Reporte 1 trae highlight.js para el bloque python',
             'resaltado', None, True],
            ['Archivos generados', 'reportes', None,
             ['documento', 'estadisticas', 'indice', 'arbol']],
        ],
    },
    {
        'archivo': 'caso15_errores_alcance_opcional.md',
        'titulo': 'Errores del alcance opcional',
        'categoria': 'Alcance opcional',
        'objetivo': 'Un tachado sin cerrar (léxico) y tres tablas mal '
                    'formadas (sintáctico): sin fila separadora, una fila '
                    'con una celda de más y una fila que no termina con '
                    '"|". Un corchete que no forma un enlace completo es '
                    'texto, no un error.',
        'verificaciones': [
            ['Errores', 'errores', None,
             ['TACHADO_SIN_CERRAR 3:6', 'TABLA_MAL_FORMADA 5:1',
              'TABLA_MAL_FORMADA 10:1', 'TABLA_MAL_FORMADA 11:1']],
            ['Fase de cada error', 'fases', None, [L, S, S, S]],
            ['Mensaje del tachado', 'mensaje', 0,
             'Tachado sin cerrar iniciado en línea 3, columna 6'],
            ['Mensaje de la fila con una celda de más', 'mensaje', 2,
             'Tabla mal formada en línea 10, columna 1: la fila tiene 3 '
             'celdas y la tabla 2 columnas'],
            ['La última línea es solo texto', 'tipos_linea', 13,
             ['TEXTO', 'TEXTO', 'SALTO_LINEA']],
            ['La frontera del árbol son todos los tokens', 'frontera',
             None, True],
            ['Archivos generados', 'reportes', None, ['errores', 'arbol']],
        ],
    },
]


# ======================================================================
# Ejecucion
# ======================================================================

class Resultado:
    """Todo lo que produjo el programa al analizar un caso."""

    def __init__(self, archivo):
        ruta = os.path.join(CARPETA_CASOS, archivo)
        entrada = open(ruta, 'rb')
        self.bytes = entrada.read()
        entrada.close()
        self.texto = self.bytes.decode('utf-8-sig')

        self.gestor = GestorErrores()
        self.lexico = AnalizadorLexico(self.texto, self.gestor)
        self.parser = AnalizadorSintactico(self.lexico, self.gestor)
        self.raiz = self.parser.analizar()
        self.tokens = self.lexico.tokens
        self.estadisticas = GeneradorEstadisticas(self.raiz, archivo)
        carpeta = os.path.join(CARPETA_SALIDA, quitar_md(archivo))
        self.rutas = generar_todos(self.raiz, self.gestor, archivo, carpeta)


def quitar_md(nombre):
    resultado = ''
    i = 0
    while i < len(nombre) - 3:
        resultado = resultado + nombre[i]
        i = i + 1
    return resultado


def firma(token):
    return (token.tipo + ' "' + token.lexema_visible() + '" ' +
            str(token.linea) + ':' + str(token.columna))


def hojas(nodo, tokens):
    if nodo.es_terminal():
        tokens.append(nodo.token)
    i = 0
    while i < len(nodo.hijos):
        hojas(nodo.hijos[i], tokens)
        i = i + 1
    return tokens


def obtener(r, medida, parametro):
    """Calcula el RESULTADO OBTENIDO de una verificacion."""
    if medida == 'errores':
        lista = []
        i = 0
        while i < len(r.gestor.errores):
            e = r.gestor.errores[i]
            lista.append(e.tipo + ' ' + str(e.linea) + ':' + str(e.columna))
            i = i + 1
        return lista
    if medida == 'fases':
        lista = []
        i = 0
        while i < len(r.gestor.errores):
            lista.append(r.gestor.errores[i].fase)
            i = i + 1
        return lista
    if medida == 'mensaje':
        return r.gestor.errores[parametro].descripcion
    if medida == 'cantidad_tokens':
        return len(r.tokens)
    if medida == 'bloques':
        lista = []
        i = 0
        while i < len(r.raiz.hijos):
            if r.raiz.hijos[i].es('<bloque>'):
                lista.append(r.raiz.hijos[i].hijos[0].simbolo)
            i = i + 1
        return lista
    if medida == 'estadistica':
        return getattr(r.estadisticas, parametro)
    if medida == 'html':
        return GeneradorHTML(r.raiz, 'x.md').traducir_documento()
    if medida == 'html_bloque':
        return html_de_bloque(r, parametro)
    if medida == 'html_contiene':
        return contiene(GeneradorHTML(r.raiz, 'x.md').traducir_documento(),
                        parametro)
    if medida == 'estadisticas':
        lista = []
        i = 0
        while i < len(parametro):
            lista.append(getattr(r.estadisticas, parametro[i]))
            i = i + 1
        return lista
    if medida == 'resaltado':
        return contiene(GeneradorHTML(r.raiz, 'x.md').generar(),
                        'hljs.highlightElement')
    if medida == 'tipos_linea':
        lista = []
        i = 0
        while i < len(r.tokens):
            if r.tokens[i].linea == parametro:
                lista.append(r.tokens[i].tipo)
            i = i + 1
        return lista
    if medida == 'firmas_linea':
        lista = []
        i = 0
        while i < len(r.tokens):
            if r.tokens[i].linea == parametro:
                lista.append(firma(r.tokens[i]))
            i = i + 1
        return lista
    if medida == 'contar_tipo':
        total = 0
        i = 0
        while i < len(r.tokens):
            if r.tokens[i].tipo == parametro:
                total = total + 1
            i = i + 1
        return total
    if medida == 'reportes':
        claves = ['documento', 'estadisticas', 'indice', 'errores', 'arbol']
        lista = []
        i = 0
        while i < len(claves):
            if claves[i] in r.rutas:
                lista.append(claves[i])
            i = i + 1
        return lista
    if medida == 'indice_sin_encabezados':
        pagina = GeneradorIndice(r.raiz, 'x.md').generar()
        return contiene(pagina, 'no tiene encabezados')
    if medida == 'frontera':
        frontera = hojas(r.raiz, [])
        if len(frontera) != len(r.tokens):
            return False
        i = 0
        while i < len(frontera):
            if frontera[i] is not r.tokens[i]:
                return False
            i = i + 1
        return True
    if medida == 'ultimo_token':
        return r.tokens[len(r.tokens) - 1].tipo
    return 'medida desconocida: ' + medida


def html_de_bloque(r, indice):
    """
    El HTML de un solo bloque: la linea 'indice' del Reporte 1. Un salto
    dentro de un <pre> o de un <p> (parrafo de varias lineas) no separa
    bloques.
    """
    html = GeneradorHTML(r.raiz, 'x.md').traducir_documento()
    lineas = []
    actual = ''
    i = 0
    while i < len(html):
        if (html[i] == '\n' and not dentro_de(html, i, '<pre>', '</pre>')
                and not dentro_de(html, i, '<p>', '</p>')):
            lineas.append(actual)
            actual = ''
        else:
            actual = actual + html[i]
        i = i + 1
    if indice < len(lineas):
        return lineas[indice]
    return ''


def dentro_de(html, posicion, apertura, cierre):
    """True si 'posicion' esta entre una etiqueta 'apertura' y su cierre."""
    abiertos = 0
    i = 0
    while i < posicion:
        if empieza_con(html, i, apertura):
            abiertos = abiertos + 1
        elif empieza_con(html, i, cierre):
            abiertos = abiertos - 1
        i = i + 1
    return abiertos > 0


def empieza_con(texto, posicion, buscado):
    if posicion + len(buscado) > len(texto):
        return False
    j = 0
    while j < len(buscado):
        if texto[posicion + j] != buscado[j]:
            return False
        j = j + 1
    return True


def contiene(texto, buscado):
    i = 0
    while i + len(buscado) <= len(texto):
        if empieza_con(texto, i, buscado):
            return True
        i = i + 1
    return False


# ======================================================================
# Documento
# ======================================================================

CSS_DOCUMENTO = """
body { background: #ffffff; }
.hoja { max-width: 900px; border: 0; margin: 0 auto; padding: 24px 32px; }
.portada { padding: 40px 0 24px; border-bottom: 3px solid var(--acento); }
.portada h1 { border: 0; margin: 0 0 8px; font-size: 2.2em; }
.portada p { margin: 2px 0; color: var(--suave); }
.caso { page-break-before: always; }
.caso h2 { margin-top: 0; }
.etiqueta {
  display: inline-block; padding: 1px 10px; border-radius: 999px;
  font-size: 12px; background: var(--codigo-fondo); color: var(--suave);
}
.ok { color: var(--ok-texto); font-weight: 700; }
.fallo { color: var(--error-texto); font-weight: 700; }
td pre, td code { white-space: pre-wrap; word-break: break-word; }
td pre {
  margin: 0; padding: 6px 8px; background: var(--codigo-fondo);
  color: var(--texto); border-radius: 4px; font-size: 11.5px;
}
.entrada { counter-reset: linea; white-space: pre-wrap; }
.entrada span { display: block; }
.entrada span::before {
  counter-increment: linea; content: counter(linea);
  display: inline-block; width: 2.2em; margin-right: 10px;
  color: #7d8590; text-align: right;
}
table { font-size: 13px; }
th { white-space: nowrap; }
tr { page-break-inside: avoid; }
h3 { page-break-after: avoid; }
@media print { .caso { page-break-before: always; } }
"""


def mostrar(valor):
    """Un valor esperado u obtenido, listo para una celda de la tabla."""
    if isinstance(valor, list):
        if len(valor) == 0:
            return '<em>(ninguno)</em>'
        texto = ''
        i = 0
        while i < len(valor):
            texto = texto + escapar(str(valor[i])) + '\n'
            i = i + 1
        return '<pre>' + texto + '</pre>'
    if valor is True:
        return 'Sí'
    if valor is False:
        return 'No'
    if isinstance(valor, str) and (contiene(valor, '<') or
                                   contiene(valor, '\n')):
        return '<pre>' + escapar(valor) + '</pre>'
    return escapar(str(valor))


def entrada_visible(r):
    """El texto del caso; la BOM y los \\r se hacen visibles."""
    texto = r.bytes.decode('utf-8')
    visible = ''
    i = 0
    while i < len(texto):
        c = texto[i]
        if c == '\ufeff':
            visible = visible + '[BOM]'
        elif c == '\r':
            visible = visible + '\\r'
        else:
            visible = visible + c
        i = i + 1
    html = ''
    linea = ''
    i = 0
    while i < len(visible):
        if visible[i] == '\n':
            html = html + '<span>' + escapar(linea) + '</span>'
            linea = ''
        else:
            linea = linea + visible[i]
        i = i + 1
    if linea != '':
        html = html + '<span>' + escapar(linea) + '</span>'
    return '<pre class="entrada">' + html + '</pre>'


def tabla_errores(r):
    if not r.gestor.hay_errores():
        return ''
    html = ('<h3>Tabla de errores obtenida</h3>\n<table><tr><th>No.</th>'
            '<th>Lexema</th><th>Tipo</th><th>Fase</th><th>Descripción</th>'
            '</tr>\n')
    i = 0
    while i < len(r.gestor.errores):
        e = r.gestor.errores[i]
        html = (html + '<tr><td>' + str(e.numero) + '</td><td><code>' +
                escapar(e.lexema) + '</code></td><td>' + e.tipo +
                '</td><td>' + e.fase + '</td><td>' + escapar(e.descripcion) +
                '</td></tr>\n')
        i = i + 1
    return html + '</table>\n'


def main():
    total_ok = 0
    total_fallo = 0
    resumen = ''
    secciones = ''

    n = 0
    while n < len(CASOS):
        caso = CASOS[n]
        numero = n + 1
        print('')
        print('Caso ' + str(numero) + ': ' + caso['titulo'])
        r = Resultado(caso['archivo'])

        filas = ''
        caso_ok = True
        j = 0
        while j < len(caso['verificaciones']):
            v = caso['verificaciones'][j]
            obtenido = obtener(r, v[1], v[2])
            if obtenido == v[3]:
                total_ok = total_ok + 1
                estado = '<span class="ok">Cumple</span>'
                print('  [OK]    ' + v[0])
            else:
                total_fallo = total_fallo + 1
                caso_ok = False
                estado = '<span class="fallo">No cumple</span>'
                print('  [FALLO] ' + v[0])
                print('          esperado: ' + str(v[3]))
                print('          obtenido: ' + str(obtenido))
            filas = (filas + '<tr><td>' + escapar(v[0]) + '</td><td>' +
                     mostrar(v[3]) + '</td><td>' + mostrar(obtenido) +
                     '</td><td>' + estado + '</td></tr>\n')
            j = j + 1

        veredicto = '<span class="ok">Aprobado</span>'
        if not caso_ok:
            veredicto = '<span class="fallo">Fallido</span>'
        resumen = (resumen + '<tr><td>' + str(numero) + '</td><td>' +
                   escapar(caso['titulo']) + '</td><td>' + caso['categoria'] +
                   '</td><td>' + str(len(caso['verificaciones'])) +
                   '</td><td>' + veredicto + '</td></tr>\n')

        secciones = (secciones + '<section class="caso">\n'
                     '<h2>Caso ' + str(numero) + ': ' +
                     escapar(caso['titulo']) + '</h2>\n'
                     '<p><span class="etiqueta">' + caso['categoria'] +
                     '</span> &nbsp; Archivo: <code>examples/casos/' +
                     caso['archivo'] + '</code></p>\n'
                     '<p><strong>Objetivo.</strong> ' +
                     escapar(caso['objetivo']) + '</p>\n'
                     '<h3>Entrada</h3>\n' + entrada_visible(r) +
                     '<h3>Resultado esperado y obtenido</h3>\n'
                     '<table><tr><th>Verificación</th><th>Resultado '
                     'esperado</th><th>Resultado obtenido</th><th>Estado'
                     '</th></tr>\n' + filas + '</table>\n' +
                     tabla_errores(r) + '<p>Veredicto: ' + veredicto +
                     '</p>\n</section>\n')
        n = n + 1

    total = total_ok + total_fallo
    cuerpo = ('<div class="portada">\n<h1>Casos de Prueba</h1>\n'
              '<p><strong>MarkdownCheck</strong> &mdash; analizador '
              'léxico-sintáctico de Markdown a HTML</p>\n'
              '<p>Proyecto 2 &middot; Lenguajes Formales y de Programación '
              '&middot; Sección B+ &middot; Segundo semestre 2026</p>\n'
              '<p>Diego Alejandro Barrios &middot; Facultad de Ingeniería, '
              'Universidad de San Carlos de Guatemala</p>\n</div>\n'
              '<h2>Cómo se ejecutaron</h2>\n'
              '<p>Cada caso es un archivo de <code>examples/casos/</code>. '
              'El script <code>tests/prueba_casos.py</code> lo analiza con '
              'el programa completo (analizador léxico, parser y '
              'generación de reportes) y compara cada <em>resultado '
              'esperado</em>, escrito a mano antes de ejecutar, con el '
              '<em>resultado obtenido</em>. Este documento lo genera ese '
              'mismo script, así que lo obtenido es siempre la salida real '
              'del programa.</p>\n'
              '<p>Notación: <code>TIPO línea:columna</code> para errores; '
              '<code>TIPO "lexema" línea:columna</code> para tokens. Las '
              'posiciones empiezan en 1.</p>\n'
              '<h2>Resumen</h2>\n'
              '<p>' + str(len(CASOS)) + ' casos, ' + str(total) +
              ' verificaciones: ' + str(total_ok) + ' cumplen, ' +
              str(total_fallo) + ' no cumplen.</p>\n'
              '<table><tr><th>No.</th><th>Caso</th><th>Categoría</th>'
              '<th>Verificaciones</th><th>Veredicto</th></tr>\n' +
              resumen + '</table>\n' + secciones)

    documento = ('<!DOCTYPE html>\n<html lang="es">\n<head>\n'
                 '<meta charset="utf-8">\n<title>Casos de Prueba - '
                 'MarkdownCheck</title>\n<style>' + CSS + CSS_DOCUMENTO +
                 '</style>\n</head>\n<body>\n<main class="hoja">\n' +
                 cuerpo + '</main>\n</body>\n</html>\n')
    if not os.path.isdir(CARPETA_DOCUMENTO):
        os.makedirs(CARPETA_DOCUMENTO)
    ruta = os.path.join(CARPETA_DOCUMENTO, 'casos_de_prueba.html')
    archivo = open(ruta, 'w', encoding='utf-8')
    archivo.write(documento)
    archivo.close()

    print('')
    print('=' * 60)
    print('Casos: ' + str(len(CASOS)) + '   verificaciones: ' + str(total) +
          '   correctas: ' + str(total_ok) + '   fallidas: ' +
          str(total_fallo))
    print('Documento: ' + ruta)
    print('=' * 60)
    if total_fallo > 0:
        sys.exit(1)


main()
