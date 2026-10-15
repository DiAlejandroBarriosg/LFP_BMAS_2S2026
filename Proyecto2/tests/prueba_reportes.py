# -*- coding: utf-8 -*-
"""
prueba_reportes.py
Pruebas del Reporte 1 (GeneradorHTML) y de arbol.dot (GeneradorDOT).

Uso, desde la carpeta Proyecto2:
    python tests/prueba_reportes.py

Ademas de verificar, deja los archivos generados del ejemplo del enunciado
en la carpeta salida/ para abrirlos en el navegador.
"""

import os
import shutil
import subprocess
import sys

CARPETA_TESTS = os.path.dirname(os.path.abspath(__file__))
CARPETA_PROYECTO = os.path.dirname(CARPETA_TESTS)
sys.path.insert(0, os.path.join(CARPETA_PROYECTO, 'src'))

from lexico.analizador_lexico import AnalizadorLexico
from sintactico.analizador_sintactico import AnalizadorSintactico
from errores.gestor_errores import GestorErrores
from reportes.generador_html import GeneradorHTML
from reportes.generador_dot import GeneradorDOT
from reportes.generador_dot import COLOR_RAIZ, COLOR_TERMINAL
from reportes.generador_estadisticas import GeneradorEstadisticas
from reportes.generador_estadisticas import contar_palabras
from reportes.generador_indice import GeneradorIndice
from reportes.generador_errores import GeneradorErrores
from reportes.generador_reportes import generar_todos, ARCHIVOS_DE_SALIDA

CARPETA_SALIDA = os.path.join(CARPETA_PROYECTO, 'salida')


class Verificador:

    def __init__(self):
        self.correctas = 0
        self.fallidas = 0

    def verificar(self, descripcion, obtenido, esperado):
        if obtenido == esperado:
            self.correctas = self.correctas + 1
            print('  [OK]    ' + descripcion)
        else:
            self.fallidas = self.fallidas + 1
            print('  [FALLO] ' + descripcion)
            print('          esperado: ' + str(esperado))
            print('          obtenido: ' + str(obtenido))


def analizar(texto):
    gestor = GestorErrores()
    lexico = AnalizadorLexico(texto, gestor)
    parser = AnalizadorSintactico(lexico, gestor)
    parser.analizar()
    return parser


def leer_ejemplo(nombre):
    ruta = os.path.join(CARPETA_PROYECTO, 'examples', nombre)
    archivo = open(ruta, 'r', encoding='utf-8-sig')
    texto = archivo.read()
    archivo.close()
    return texto


def html_de(texto):
    """Solo el contenido traducido (sin la pagina) de un texto Markdown."""
    parser = analizar(texto)
    return GeneradorHTML(parser.raiz, 'prueba.md').traducir_documento()


def contiene(texto, buscado):
    """True si 'buscado' aparece dentro de 'texto' (busqueda manual)."""
    i = 0
    while i + len(buscado) <= len(texto):
        j = 0
        coincide = True
        while coincide and j < len(buscado):
            if texto[i + j] != buscado[j]:
                coincide = False
            j = j + 1
        if coincide:
            return True
        i = i + 1
    return False


def contar_apariciones(texto, buscado):
    total = 0
    i = 0
    while i + len(buscado) <= len(texto):
        j = 0
        coincide = True
        while coincide and j < len(buscado):
            if texto[i + j] != buscado[j]:
                coincide = False
            j = j + 1
        if coincide:
            total = total + 1
        i = i + 1
    return total


def contar_nodos(nodo):
    total = 1
    i = 0
    while i < len(nodo.hijos):
        total = total + contar_nodos(nodo.hijos[i])
        i = i + 1
    return total


def titulo(texto):
    print('')
    print(texto)
    print('-' * len(texto))


# ======================================================================
# A. Reporte 1 del ejemplo del enunciado
# ======================================================================

def prueba_reporte1_ejemplo(v):
    titulo('A. Reporte 1 de ejemplo_valido.md')
    parser = analizar(leer_ejemplo('ejemplo_valido.md'))
    generador = GeneradorHTML(parser.raiz, 'ejemplo_valido.md')

    esperado = (
        '<h1 id="seccion-1">Proyecto de Lenguajes Formales</h1>\n'
        '<p>Este curso combina <strong>teoría sólida</strong> y '
        '<em>práctica de código</em>, con ejemplos en <code>Python</code> .'
        '</p>\n'
        '<h2 id="seccion-2">Contenido del curso</h2>\n'
        '<ul><li>Análisis léxico<ul><li>Autómatas finitos</li>'
        '<li>Expresiones regulares</li></ul></li>'
        '<li>Análisis sintáctico<ul><li>Gramáticas libres de contexto'
        '<ul><li>Recursión por la izquierda</li>'
        '<li>Recursión por la derecha</li></ul></li></ul></li>'
        '<li>Generación de código</li></ul>\n'
        '<blockquote><p>El análisis sintáctico es donde la teoría se '
        'encuentra con la práctica.</p><blockquote><p>Y donde más se '
        'aprende, según los estudiantes.</p></blockquote></blockquote>\n'
        '<pre><code class="language-python">def hola():\n'
        '    print(&quot;Hola LFP&quot;)</code></pre>\n'
        '<hr>\n'
        '<p>Fin del documento.</p>\n')
    v.verificar('el HTML traducido es exactamente el esperado',
                generador.traducir_documento(), esperado)

    pagina = generador.generar()
    v.verificar('documento HTML completo, en UTF-8',
                [contiene(pagina, '<!DOCTYPE html>'),
                 contiene(pagina, '<meta charset="utf-8">')], [True, True])
    v.verificar('CSS embebido (sin archivos externos)',
                [contiene(pagina, '<style>'),
                 contiene(pagina, '<link rel="stylesheet"')], [True, False])
    v.verificar('indicador de analisis sin errores',
                contiene(pagina, 'Análisis completado sin errores'), True)

    ruta = generador.guardar(CARPETA_SALIDA)
    v.verificar('se guarda como salida/reporte1_documento.html',
                os.path.isfile(ruta), True)


# ======================================================================
# B. Traduccion de cada construccion
# ======================================================================

def prueba_traducciones(v):
    titulo('B. Traduccion de cada elemento')

    v.verificar('H1 a H6 con anclas en orden',
                html_de('# a\n## b\n### c\n#### d\n##### e\n###### f\n'),
                '<h1 id="seccion-1">a</h1>\n<h2 id="seccion-2">b</h2>\n'
                '<h3 id="seccion-3">c</h3>\n<h4 id="seccion-4">d</h4>\n'
                '<h5 id="seccion-5">e</h5>\n<h6 id="seccion-6">f</h6>\n')
    v.verificar('cursiva dentro de negrita',
                html_de('**a *b* c**\n'),
                '<p><strong>a <em>b</em> c</strong></p>\n')
    v.verificar('negrita dentro de cursiva dentro de negrita',
                html_de('**a *b **c** d* e**\n'),
                '<p><strong>a <em>b <strong>c</strong> d</em> e</strong>'
                '</p>\n')
    v.verificar('"***ambas***"', html_de('***ambas***\n'),
                '<p><strong><em>ambas</em></strong></p>\n')
    v.verificar('"***a** b*": la cursiva queda afuera',
                html_de('***a** b*\n'),
                '<p><em><strong>a</strong> b</em></p>\n')
    v.verificar('"***a* b**": la negrita queda afuera',
                html_de('***a* b**\n'),
                '<p><strong><em>a</em> b</strong></p>\n')
    v.verificar('codigo en linea: su contenido no se interpreta',
                html_de('`**no**`\n'), '<p><code>**no**</code></p>\n')
    v.verificar('parrafo de varias lineas en un solo <p>',
                html_de('uno\ndos\n'), '<p>uno\ndos</p>\n')
    v.verificar('negrita y cursiva que cruzan lineas de un parrafo (D-02)',
                html_de('a **b\nc** *d\ne*\n'),
                '<p>a <strong>b\nc</strong> <em>d\ne</em></p>\n')
    v.verificar('codigo en linea que cruza lineas: el salto es un espacio',
                html_de('a `b\nc` d\n'), '<p>a <code>b c</code> d</p>\n')
    v.verificar('lista de 4 niveles',
                html_de('- a\n  - b\n    - c\n      - d\n'),
                '<ul><li>a<ul><li>b<ul><li>c<ul><li>d</li></ul></li></ul>'
                '</li></ul></li></ul>\n')
    v.verificar('cita de 3 niveles que vuelve al nivel 1',
                html_de('> a\n>> b\n>>> c\n> d\n'),
                '<blockquote><p>a</p><blockquote><p>b</p><blockquote>'
                '<p>c</p></blockquote></blockquote><p>d</p></blockquote>\n')
    v.verificar('salto de cita 1 a 3: blockquote intermedio vacio',
                html_de('> a\n>>> c\n'),
                '<blockquote><p>a</p><blockquote><blockquote><p>c</p>'
                '</blockquote></blockquote></blockquote>\n')
    v.verificar('encabezado dentro de una cita, con su ancla',
                html_de('# Uno\n\n> ## Dos\n> texto\n'),
                '<h1 id="seccion-1">Uno</h1>\n<blockquote>'
                '<h2 id="seccion-2">Dos</h2><p>texto</p></blockquote>\n')
    v.verificar('una linea de cita vacia no produce <p></p>',
                html_de('> a\n>\n> b\n'),
                '<blockquote><p>a</p><p>b</p></blockquote>\n')
    v.verificar('bloque de codigo sin lenguaje, con linea vacia y sangria',
                html_de('```\nif x:\n\n    y = 1\n```\n'),
                '<pre><code>if x:\n\n    y = 1</code></pre>\n')
    v.verificar('el contenido del bloque de codigo no se interpreta',
                html_de('```\n# no es titulo\n**ni negrita**\n```\n'),
                '<pre><code># no es titulo\n**ni negrita**</code></pre>\n')
    v.verificar('regla horizontal', html_de('---\n'), '<hr>\n')

    v.verificar('los caracteres especiales de HTML se escapan',
                html_de('a < b && c > d\n'),
                '<p>a &lt; b &amp;&amp; c &gt; d</p>\n')
    v.verificar('una etiqueta escrita en el texto no se ejecuta',
                html_de('<script>alert(1)</script>\n'),
                '<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>\n')
    v.verificar('escape dentro de codigo y de bloques de codigo',
                html_de('`<b>`\n\n```html\n<p>"x"</p>\n```\n'),
                '<p><code>&lt;b&gt;</code></p>\n'
                '<pre><code class="language-html">&lt;p&gt;&quot;x&quot;'
                '&lt;/p&gt;</code></pre>\n')


# ======================================================================
# C. arbol.dot
# ======================================================================

def prueba_dot(v):
    titulo('C. arbol.dot (arbol de derivacion en Graphviz)')
    parser = analizar(leer_ejemplo('ejemplo_valido.md'))
    generador = GeneradorDOT(parser.raiz)
    dot = generador.generar()

    total_nodos = contar_nodos(parser.raiz)
    v.verificar('un nodo DOT por cada nodo del arbol (' + str(total_nodos) +
                ')', contar_apariciones(dot, ' [label="'), total_nodos)
    v.verificar('una arista por nodo, menos la raiz',
                contar_apariciones(dot, ' -> '), total_nodos - 1)
    v.verificar('la raiz es <documento>, en azul oscuro',
                contiene(dot, 'n0 [label="<documento>", fillcolor="' +
                         COLOR_RAIZ + '", fontcolor=white]'), True)
    v.verificar('los 77 tokens son hojas en amarillo',
                contar_apariciones(dot, 'fillcolor="' + COLOR_TERMINAL + '"'),
                77)
    v.verificar('las comillas del lexema se escapan',
                contiene(dot, 'print(\\"Hola LFP\\")'), True)
    v.verificar('la lista de nivel 3 muestra su atributo',
                contiene(dot, '<lista>\\nnivel 3'), True)

    ruta = generador.guardar(CARPETA_SALIDA)
    v.verificar('se guarda como salida/arbol.dot', os.path.isfile(ruta),
                True)

    if shutil.which('dot') is None:
        print('  [--]    Graphviz no esta instalado: no se valida la '
              'sintaxis con dot')
        return
    imagen = os.path.join(CARPETA_SALIDA, 'arbol.png')
    resultado = subprocess.run(['dot', '-Tpng', ruta, '-o', imagen],
                               capture_output=True, text=True)
    v.verificar('Graphviz acepta el archivo y genera arbol.png',
                [resultado.returncode, os.path.isfile(imagen)], [0, True])

    parser = analizar(leer_ejemplo('errores_sintacticos.md'))
    ruta_errores = GeneradorDOT(parser.raiz).guardar(
        os.path.join(CARPETA_SALIDA, 'con_errores'))
    resultado = subprocess.run(['dot', '-Tsvg', ruta_errores],
                               capture_output=True, text=True)
    v.verificar('tambien genera un arbol valido para un archivo con errores',
                resultado.returncode, 0)


# ======================================================================
# D. Reporte 2 - Estadisticas
# ======================================================================

def estadisticas(texto):
    return GeneradorEstadisticas(analizar(texto).raiz, 'prueba.md')


def prueba_estadisticas(v):
    titulo('D. Reporte 2 (valores del ejemplo de la seccion 4.8)')
    e = GeneradorEstadisticas(analizar(leer_ejemplo('ejemplo_valido.md'))
                              .raiz, 'ejemplo_valido.md')

    v.verificar('tarjetas: 67 palabras, 2 parrafos, 2 encabezados',
                [e.palabras, e.parrafos, e.encabezados], [67, 2, 2])
    v.verificar('8 items, 2 lineas de cita, 1 bloque de codigo',
                [e.items, e.lineas_cita, e.bloques_codigo], [8, 2, 1])
    v.verificar('1 lista y 1 cita (de primer nivel)', [e.listas, e.citas],
                [1, 1])
    v.verificar('encabezados por nivel: H1=1, H2=1, H3..H6=0', e.por_nivel,
                [1, 1, 0, 0, 0, 0])
    v.verificar('profundidad maxima: listas 3, citas 2',
                [e.profundidad_listas, e.profundidad_citas], [3, 2])
    v.verificar('negrita, cursiva, codigo en linea y regla: 1 de cada uno',
                [e.negritas, e.cursivas, e.codigos_inline, e.reglas],
                [1, 1, 1, 1])

    v.verificar('contar_palabras: separadores repetidos y tabuladores',
                [contar_palabras('  uno   dos\ttres '), contar_palabras(''),
                 contar_palabras('   ')], [3, 0, 0])
    v.verificar('palabras partidas por formato cuentan como una (D-14)',
                estadisticas('pa**la**bra y `co`digo\n').palabras, 3)
    v.verificar('en una negrita que cruza lineas, el salto separa palabras',
                estadisticas('**uno\ndos** `tres\ncuatro`\n').palabras, 4)
    v.verificar('los bloques de codigo no cuentan palabras',
                estadisticas('uno dos\n\n```\ntres cuatro cinco\n```\n')
                .palabras, 2)
    v.verificar('documento vacio: todo en cero',
                [estadisticas('').palabras, estadisticas('').por_nivel],
                [0, [0, 0, 0, 0, 0, 0]])

    pagina = e.generar()
    v.verificar('el HTML muestra las 6 barras H1..H6',
                contar_apariciones(pagina, 'class="barra-fila"'), 6)
    v.verificar('la barra del nivel con mas encabezados mide 100%',
                contiene(pagina, 'style="width: 100%"'), True)
    v.verificar('profundidades en texto', [contiene(pagina, '3 niveles'),
                                          contiene(pagina, '2 niveles')],
                [True, True])
    e.guardar(CARPETA_SALIDA)


# ======================================================================
# E. Reporte 3 - Tabla de contenido
# ======================================================================

def prueba_indice(v):
    titulo('E. Reporte 3 (tabla de contenido)')
    parser = analizar(leer_ejemplo('ejemplo_valido.md'))
    pagina = GeneradorIndice(parser.raiz, 'ejemplo_valido.md').generar()

    v.verificar('una entrada por encabezado',
                contar_apariciones(pagina, 'class="entrada"'), 2)
    v.verificar('cada entrada enlaza a su ancla dentro del Reporte 1',
                [contiene(pagina, 'href="reporte1_documento.html#seccion-1"'
                          '>Proyecto de Lenguajes Formales</a>'),
                 contiene(pagina, 'href="reporte1_documento.html#seccion-2"'
                          '>Contenido del curso</a>')], [True, True])
    v.verificar('la sangria refleja el nivel (H1: 0px, H2: 24px)',
                [contiene(pagina, 'padding-left: 0px"><span class="nivel">'
                          'H1'),
                 contiene(pagina, 'padding-left: 24px"><span class="nivel">'
                          'H2')], [True, True])

    reporte1 = GeneradorHTML(parser.raiz, 'x.md').generar()
    v.verificar('las anclas del indice existen en el Reporte 1',
                [contiene(reporte1, 'id="seccion-1"'),
                 contiene(reporte1, 'id="seccion-2"')], [True, True])

    pagina = GeneradorIndice(analizar('# A\n### C\n## B\n').raiz,
                             'x.md').generar()
    v.verificar('H3 mas adentro que H2, en el orden del documento',
                [contiene(pagina, 'padding-left: 48px"><span class="nivel">'
                          'H3</span><a href="reporte1_documento.html'
                          '#seccion-2">C'),
                 contiene(pagina, 'padding-left: 24px"><span class="nivel">'
                          'H2</span><a href="reporte1_documento.html'
                          '#seccion-3">B')], [True, True])
    v.verificar('el texto de la entrada va sin formato',
                contiene(GeneradorIndice(analizar('# Un **gran** `titulo`\n')
                                         .raiz, 'x.md').generar(),
                         '>Un gran titulo</a>'), True)

    pagina = GeneradorIndice(analizar('solo un parrafo\n').raiz,
                             'x.md').generar()
    v.verificar('sin encabezados: lo dice explicitamente',
                [contiene(pagina, 'no tiene encabezados'),
                 contar_apariciones(pagina, 'class="entrada"')], [True, 0])
    GeneradorIndice(parser.raiz, 'ejemplo_valido.md').guardar(CARPETA_SALIDA)


# ======================================================================
# F. Reporte de errores y seleccion de reportes
# ======================================================================

def prueba_errores_y_seleccion(v):
    titulo('F. Reporte de errores y que se genera en cada caso (D-16)')
    parser = analizar(leer_ejemplo('errores_sintacticos.md'))
    generador = GeneradorErrores(parser.gestor, 'errores_sintacticos.md')
    pagina = generador.generar()
    v.verificar('una fila por error (5) mas el encabezado',
                contar_apariciones(pagina, '<tr>'), 6)
    v.verificar('muestra fase, tipo y posicion',
                [contiene(pagina, '<td>Sintáctico</td>'),
                 contiene(pagina, '<td>Léxico</td>'),
                 contiene(pagina, '>CITA_MAL_FORMADA</td>')],
                [True, True, True])

    carpeta = os.path.join(CARPETA_SALIDA, 'seleccion_con_errores')
    rutas = generar_todos(parser.raiz, parser.gestor, 'x.md', carpeta)
    claves = []
    if 'errores' in rutas:
        claves.append('errores')
    if 'documento' in rutas:
        claves.append('documento')
    if 'arbol' in rutas:
        claves.append('arbol')
    v.verificar('con errores: solo reporte de errores y arbol.dot', claves,
                ['errores', 'arbol'])

    parser = analizar(leer_ejemplo('ejemplo_valido.md'))
    rutas = generar_todos(parser.raiz, parser.gestor, 'ejemplo_valido.md',
                          CARPETA_SALIDA)
    existen = True
    nombres = ['documento', 'estadisticas', 'indice', 'arbol']
    i = 0
    while i < len(nombres):
        if not os.path.isfile(rutas[nombres[i]]):
            existen = False
        i = i + 1
    v.verificar('sin errores: los 3 reportes y arbol.dot existen',
                [existen, 'errores' in rutas], [True, False])

    carpeta = os.path.join(CARPETA_SALIDA, 'reanalisis')
    generar_todos(parser.raiz, parser.gestor, 'x.md', carpeta)
    con_errores = analizar('**sin cerrar\n')
    generar_todos(con_errores.raiz, con_errores.gestor, 'x.md', carpeta)
    v.verificar('reanalisis con errores: se borran los reportes viejos',
                archivos_de(carpeta), ['reporte_errores.html', 'arbol.dot'])
    generar_todos(parser.raiz, parser.gestor, 'x.md', carpeta)
    v.verificar('reanalisis corregido: se borra el reporte de errores',
                archivos_de(carpeta),
                ['reporte1_documento.html', 'reporte2_estadisticas.html',
                 'reporte3_indice.html', 'arbol.dot'])


def archivos_de(carpeta):
    """Cuales archivos de salida hay en la carpeta, en el orden de la lista."""
    presentes = []
    i = 0
    while i < len(ARCHIVOS_DE_SALIDA):
        if os.path.isfile(os.path.join(carpeta, ARCHIVOS_DE_SALIDA[i])):
            presentes.append(ARCHIVOS_DE_SALIDA[i])
        i = i + 1
    return presentes


# ======================================================================
# G. Alcance opcional (D-29 a D-36)
# ======================================================================

def prueba_alcance_opcional(v):
    titulo('G. Alcance opcional')

    v.verificar('lista numerada: <ol>, y start si no empieza en 1',
                [html_de('1. a\n2. b\n'), html_de('3. c\n4. d\n')],
                ['<ol><li>a</li><li>b</li></ol>\n',
                 '<ol start="3"><li>c</li><li>d</li></ol>\n'])
    v.verificar('sublista con viñetas y numerada dentro del mismo item',
                html_de('- a\n  - b\n  1. c\n'),
                '<ul><li>a<ul><li>b</li></ul><ol><li>c</li></ol></li></ul>\n')
    v.verificar('tareas: casilla marcada y vacia',
                html_de('- [x] hecho\n- [ ] falta\n'),
                '<ul><li class="tarea"><input type="checkbox" disabled '
                'checked> hecho</li><li class="tarea"><input '
                'type="checkbox" disabled> falta</li></ul>\n')
    v.verificar('tachado -> <del>, con negrita adentro',
                html_de('a ~~b **c**~~\n'),
                '<p>a <del>b <strong>c</strong></del></p>\n')
    v.verificar('enlace -> <a href>, con la URL escapada',
                html_de('[la *doc*](https://x.org/?a=1&b=2)\n'),
                '<p><a href="https://x.org/?a=1&amp;b=2">la <em>doc</em></a>'
                '</p>\n')
    v.verificar('un enlace "javascript:" se queda sin destino',
                html_de('[a](javascript:alert)\n'),
                '<p><a href="">a</a></p>\n')
    v.verificar('imagen -> <img src alt>',
                html_de('![logo "py"](img/a.png)\n'),
                '<p><img src="img/a.png" alt="logo &quot;py&quot;"></p>\n')
    v.verificar('tabla: <thead> con <th>, <tbody> con <td> y alineaciones',
                html_de('| A | B |\n|:-:|--:|\n| 1 | **2** |\n'),
                '<table class="tabla-md"><thead><tr><th style="text-align: '
                'center">A</th><th style="text-align: right">B</th></tr>'
                '</thead><tbody><tr><td style="text-align: center">1</td>'
                '<td style="text-align: right"><strong>2</strong></td></tr>'
                '</tbody></table>\n')

    e = estadisticas('1. [x] a\n2. [ ] b\n  1. [x] c\n\n'
                     '~~t~~ [e](u) ![i](j) ![k](l)\n\n| a |\n|---|\n')
    v.verificar('Reporte 2: numeradas, tareas, hechas, tachados, enlaces, '
                'imagenes y tablas',
                [e.listas_numeradas, e.tareas, e.tareas_hechas, e.tachados,
                 e.enlaces, e.imagenes, e.tablas], [2, 3, 2, 1, 1, 2, 1])
    v.verificar('la seccion Alcance opcional solo aparece si se usa',
                [contiene(e.generar(), 'Alcance opcional'),
                 contiene(estadisticas('hola\n').generar(),
                          'Alcance opcional')], [True, False])
    v.verificar('el texto de un enlace cuenta palabras; el de una imagen no',
                estadisticas('[uno dos](u) ![tres cuatro](i)\n').palabras, 2)

    pagina_con = GeneradorHTML(analizar('```python\nx = 1\n```\n').raiz,
                               'x.md').generar()
    pagina_sin = GeneradorHTML(analizar('```\nx = 1\n```\n').raiz,
                               'x.md').generar()
    v.verificar('resaltado de sintaxis: highlight.js embebido solo si un '
                'bloque dice su lenguaje (D-36)',
                [contiene(pagina_con, 'hljs.highlightElement'),
                 contiene(pagina_con, 'Highlight.js v11.9.0'),
                 contiene(pagina_sin, 'hljs')], [True, True, False])
    v.verificar('... y el bloque sigue siendo el mismo <pre><code>',
                html_de('```python\nx = 1\n```\n'),
                '<pre><code class="language-python">x = 1</code></pre>\n')
    dot = GeneradorDOT(analizar('1. a\n').raiz).generar()
    v.verificar('arbol.dot: la lista numerada lo dice en su nodo',
                contiene(dot, '<lista>\\nnivel 1\\nnumerada'), True)


def main():
    v = Verificador()
    prueba_reporte1_ejemplo(v)
    prueba_traducciones(v)
    prueba_dot(v)
    prueba_estadisticas(v)
    prueba_indice(v)
    prueba_errores_y_seleccion(v)
    prueba_alcance_opcional(v)

    print('')
    print('=' * 60)
    total = v.correctas + v.fallidas
    print('Verificaciones: ' + str(total) + '   correctas: ' +
          str(v.correctas) + '   fallidas: ' + str(v.fallidas))
    print('=' * 60)
    if v.fallidas > 0:
        sys.exit(1)


main()
