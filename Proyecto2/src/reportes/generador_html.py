# -*- coding: utf-8 -*-
"""
generador_html.py
GeneradorHTML: Reporte 1, el documento HTML equivalente al .md.

El HTML se obtiene RECORRIENDO EL ARBOL DE DERIVACION, nunca el texto
original (criterio 2.6 del enunciado). Cada no terminal tiene su funcion de
traduccion, y la recursion del recorrido es la misma del parser: una lista
traduce sus items, cada item traduce su sublista, que traduce su lista...
Por eso el anidamiento del HTML queda igual al del archivo.

Mapa nodo -> etiqueta
    <encabezado> nivel n   <hn id="seccion-k">     _encabezado()
    <parrafo>              <p>                      _parrafo()
    <lista>                <ul>                     _lista()
    <item_lista>           <li>                     _item()
    <cita>                 <blockquote>             _cita()
    <bloque_codigo>        <pre><code>              _bloque_codigo()
    <regla_horizontal>     <hr>                     _bloque()
    <negrita>              <strong>                 _en_linea()
    <cursiva>              <em>                     _en_linea()
    <codigo_inline>        <code>                   _en_linea()
    TEXTO                  el texto, escapado       _en_linea()

  Alcance opcional
    <lista> numerada       <ol start="n">           _lista()
    CASILLA                <input type="checkbox">  _item()
    <tachado>              <del>                    _en_linea()
    <enlace>               <a href="url">           _en_linea()
    <imagen>               <img src="url" alt="">   _en_linea()
    <tabla>                <table> con <thead>      _tabla()
    <bloque_codigo>        coloreado con highlight.js (D-36), solo visual

El resaltado de sintaxis no cambia el analisis: el bloque de codigo sigue
siendo un TEXTO_LITERAL por linea. Solo se agrega a la pagina la libreria
highlight.js (con su tema), que colorea el <code class="language-x"> al
abrirla en el navegador.
"""

import os

from lexico.token import TEXTO, TEXTO_LITERAL, LENGUAJE_CODIGO
from lexico.token import SALTO_LINEA, CASILLA
from sintactico.nodo_ast import NT_BLOQUE, NT_ENCABEZADO, NT_PARRAFO
from sintactico.nodo_ast import NT_LINEA_TEXTO, NT_LISTA, NT_ITEM_LISTA
from sintactico.nodo_ast import NT_SUBLISTA, NT_CITA, NT_CONTENIDO_CITA
from sintactico.nodo_ast import NT_BLOQUE_CODIGO, NT_CONTENIDO_CODIGO
from sintactico.nodo_ast import NT_REGLA_HORIZONTAL, NT_EN_LINEA
from sintactico.nodo_ast import NT_EN_LINEA_N, NT_EN_LINEA_C
from sintactico.nodo_ast import NT_NEGRITA, NT_CURSIVA, NT_CODIGO_INLINE
from sintactico.nodo_ast import NT_TACHADO, NT_EN_LINEA_T, NT_ENLACE
from sintactico.nodo_ast import NT_IMAGEN, NT_TABLA, NT_FILA_TABLA, NT_CELDA
from reportes import recorridos
from reportes.plantilla import escapar, pagina, guardar

NOMBRE_REPORTE = 'reporte1_documento.html'

# highlight.js 11.9.0 (licencia BSD-3, en recursos/), copiado al Reporte 1
# para que el coloreado funcione sin internet (D-36).
CARPETA_RECURSOS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'recursos')
ARCHIVO_RESALTADO = 'highlight.min.js'
ARCHIVO_TEMA = 'github-dark.min.css'

# El tema trae su propio fondo y margen; se dejan los del reporte.
CSS_RESALTADO = 'pre code.hljs { padding: 0; background: none; }'

# Al abrir la pagina, se colorea cada bloque que declara su lenguaje.
SCRIPT_RESALTADO = (
    "document.querySelectorAll('pre code[class^=\"language-\"]')"
    ".forEach(function (bloque) { hljs.highlightElement(bloque); });")


class GeneradorHTML:

    def __init__(self, raiz, nombre_archivo):
        self.raiz = raiz
        self.nombre_archivo = nombre_archivo
        # Cada encabezado recibe su ancla segun su posicion en el documento.
        self.lista_encabezados = recorridos.encabezados(raiz)

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------

    def generar(self):
        """Devuelve el Reporte 1 completo como texto HTML."""
        cuerpo = ('<div class="estado">&#10003; Análisis completado sin '
                  'errores</div>\n')
        cuerpo = cuerpo + self.traducir_documento()
        cabecera = ''
        if self.tiene_codigo_con_lenguaje():
            cabecera = recursos_de_resaltado()
        return pagina('Reporte 1 - ' + self.nombre_archivo, cuerpo,
                      self.nombre_archivo, cabecera)

    def tiene_codigo_con_lenguaje(self):
        """True si algun bloque de codigo dice su lenguaje (```python)."""
        bloques = recorridos.buscar(self.raiz, NT_BLOQUE_CODIGO, [])
        i = 0
        while i < len(bloques):
            if recorridos.hijo_con_simbolo(bloques[i],
                                           LENGUAJE_CODIGO) is not None:
                return True
            i = i + 1
        return False

    def guardar(self, carpeta):
        return guardar(carpeta, NOMBRE_REPORTE, self.generar())

    def traducir_documento(self):
        """
        Solo el contenido traducido, sin la pagina alrededor. Lo usan las
        pruebas para comparar con el HTML esperado.
        """
        html = ''
        i = 0
        while i < len(self.raiz.hijos):
            hijo = self.raiz.hijos[i]
            if hijo.es(NT_BLOQUE):
                html = html + self._bloque(hijo.hijos[0])
            i = i + 1
        return html

    # ------------------------------------------------------------------
    # Bloques
    # ------------------------------------------------------------------

    def _bloque(self, nodo):
        """Despacha segun el no terminal que hay dentro del <bloque>."""
        if nodo.es(NT_ENCABEZADO):
            return self._encabezado(nodo) + '\n'
        if nodo.es(NT_PARRAFO):
            return self._parrafo(nodo)
        if nodo.es(NT_LISTA):
            return self._lista(nodo) + '\n'
        if nodo.es(NT_CITA):
            return self._cita(nodo) + '\n'
        if nodo.es(NT_BLOQUE_CODIGO):
            return self._bloque_codigo(nodo)
        if nodo.es(NT_REGLA_HORIZONTAL):
            return '<hr>\n'
        if nodo.es(NT_TABLA):
            return self._tabla(nodo) + '\n'
        return ''

    def _encabezado(self, nodo):
        """<encabezado> nivel n -> <hn id="seccion-k">...</hn>"""
        etiqueta = 'h' + str(nodo.nivel)
        numero = self._numero_encabezado(nodo)
        contenido = self._en_linea(recorridos.hijo_con_simbolo(nodo,
                                                               NT_EN_LINEA))
        return ('<' + etiqueta + ' id="' + recorridos.ancla(numero) + '">' +
                contenido + '</' + etiqueta + '>')

    def _numero_encabezado(self, nodo):
        """Posicion (desde 1) del encabezado en el documento."""
        i = 0
        while i < len(self.lista_encabezados):
            if self.lista_encabezados[i] is nodo:
                return i + 1
            i = i + 1
        return 0

    def _parrafo(self, nodo):
        """
        Todas las lineas del parrafo van en un mismo <p> (D-13), separadas
        por un salto de linea; el navegador lo muestra como un espacio.
        """
        contenido = ''
        i = 0
        while i < len(nodo.hijos):
            linea = nodo.hijos[i]
            if linea.es(NT_LINEA_TEXTO):
                if contenido != '':
                    contenido = contenido + '\n'
                contenido = contenido + self._en_linea(
                    recorridos.hijo_con_simbolo(linea, NT_EN_LINEA))
            i = i + 1
        return '<p>' + contenido + '</p>\n'

    def _lista(self, nodo):
        """
        <lista> -> <ul>, o <ol> si es numerada (D-29). Como en Markdown, el
        numero del primer item da el inicio ('3.' -> start="3"); los demas
        numeros no importan.
        """
        etiqueta = 'ul'
        apertura = '<ul>'
        if nodo.numerada:
            etiqueta = 'ol'
            apertura = '<ol>'
            inicio = recorridos.numero_inicial(nodo)
            if inicio != 1:
                apertura = '<ol start="' + str(inicio) + '">'
        html = apertura
        i = 0
        while i < len(nodo.hijos):
            if nodo.hijos[i].es(NT_ITEM_LISTA):
                html = html + self._item(nodo.hijos[i])
            i = i + 1
        return html + '</' + etiqueta + '>'

    def _item(self, nodo):
        """
        <li> con el texto del item y, si tiene, su sublista adentro: asi
        el <ul> interno queda dentro del <li> de su item padre. Un item con
        CASILLA es una tarea: lleva una casilla marcada o vacia (D-30).
        """
        html = '<li>'
        casilla = recorridos.hijo_con_simbolo(nodo, CASILLA)
        if casilla is not None:
            html = '<li class="tarea"><input type="checkbox" disabled'
            if casilla.token.lexema != '[ ]':
                html = html + ' checked'
            html = html + '> '
        html = html + self._en_linea(recorridos.hijo_con_simbolo(
            nodo, NT_EN_LINEA))
        sublista = recorridos.hijo_con_simbolo(nodo, NT_SUBLISTA)
        if sublista is not None:
            html = html + self._sublista(sublista)
        return html + '</li>'

    def _sublista(self, nodo):
        """
        La <sublista> no tiene etiqueta propia: es el INDENT/DEDENT que
        rodea a la lista interna. Se traduce solo su <lista>.
        """
        html = ''
        i = 0
        while i < len(nodo.hijos):
            hijo = nodo.hijos[i]
            if hijo.es(NT_LISTA):
                html = html + self._lista(hijo)
            elif hijo.es(NT_SUBLISTA):
                html = html + self._sublista(hijo)
            i = i + 1
        return html

    def _cita(self, nodo):
        """
        <cita> -> <blockquote>. Cada linea de texto es un <p> (D-10); un
        encabezado se traduce como encabezado; una <cita> hija es otro
        <blockquote> adentro, a la misma profundidad que en el archivo.
        """
        html = '<blockquote>'
        i = 0
        while i < len(nodo.hijos):
            hijo = nodo.hijos[i]
            if hijo.es(NT_CONTENIDO_CITA):
                html = html + self._contenido_cita(hijo)
            elif hijo.es(NT_CITA):
                html = html + self._cita(hijo)
            i = i + 1
        return html + '</blockquote>'

    def _contenido_cita(self, nodo):
        encabezado = recorridos.hijo_con_simbolo(nodo, NT_ENCABEZADO)
        if encabezado is not None:
            return self._encabezado(encabezado)
        contenido = self._en_linea(recorridos.hijo_con_simbolo(nodo,
                                                               NT_EN_LINEA))
        if contenido == '':
            # Una linea '>' vacia no produce un parrafo vacio.
            return ''
        return '<p>' + contenido + '</p>'

    def _bloque_codigo(self, nodo):
        """
        <pre><code class="language-x">: las lineas literales unidas con
        saltos de linea. Solo se escapan &, < y >; nada mas se interpreta,
        asi que un '**' dentro del bloque se ve tal cual.
        """
        clase = ''
        lenguaje = recorridos.hijo_con_simbolo(nodo, LENGUAJE_CODIGO)
        if lenguaje is not None:
            clase = ' class="language-' + escapar(lenguaje.token.lexema) + '"'

        contenido = ''
        primera = True
        cuerpo = recorridos.hijo_con_simbolo(nodo, NT_CONTENIDO_CODIGO)
        i = 0
        while i < len(cuerpo.hijos):
            hijo = cuerpo.hijos[i]
            if hijo.es(TEXTO_LITERAL):
                if not primera:
                    contenido = contenido + '\n'
                contenido = contenido + escapar(hijo.token.lexema)
                primera = False
            i = i + 1
        return '<pre><code' + clase + '>' + contenido + '</code></pre>\n'

    def _tabla(self, nodo):
        """
        <tabla> -> <table>. La primera fila es el encabezado (<th>) si va
        antes del SEPARADOR_TABLA; las demas van en <tbody>. Cada celda
        lleva la alineacion de su columna (D-33).
        """
        filas = []
        i = 0
        while i < len(nodo.hijos):
            if nodo.hijos[i].es(NT_FILA_TABLA):
                filas.append(nodo.hijos[i])
            i = i + 1
        hay_encabezado = recorridos.tabla_tiene_encabezado(nodo)

        html = '<table class="tabla-md">'
        primera_del_cuerpo = 0
        if hay_encabezado:
            html = (html + '<thead>' + self._fila(filas[0], 'th',
                                                  nodo.alineaciones) +
                    '</thead>')
            primera_del_cuerpo = 1
        if primera_del_cuerpo < len(filas):
            html = html + '<tbody>'
            i = primera_del_cuerpo
            while i < len(filas):
                html = html + self._fila(filas[i], 'td', nodo.alineaciones)
                i = i + 1
            html = html + '</tbody>'
        return html + '</table>'

    def _fila(self, fila, etiqueta, alineaciones):
        html = '<tr>'
        columna = 0
        i = 0
        while i < len(fila.hijos):
            celda = fila.hijos[i]
            if celda.es(NT_CELDA):
                estilo = ''
                if columna < len(alineaciones) and alineaciones[columna] != '':
                    estilo = (' style="text-align: ' + alineaciones[columna] +
                              '"')
                contenido = self._en_linea(recorridos.hijo_con_simbolo(
                    celda, NT_EN_LINEA))
                html = (html + '<' + etiqueta + estilo + '>' +
                        recorridos.quitar_espacios_finales(contenido) +
                        '</' + etiqueta + '>')
                columna = columna + 1
            i = i + 1
        return html + '</tr>'

    # ------------------------------------------------------------------
    # Elementos en linea
    # ------------------------------------------------------------------

    def _en_linea(self, nodo):
        """
        Traduce un <en_linea>, <en_linea_n> o <en_linea_c>. La negrita y la
        cursiva vuelven a llamar a esta funcion con su contenido: es la
        misma recursion mutua de la gramatica. Un SALTO_LINEA solo puede
        venir dentro de una negrita o una cursiva que cruza lineas de un
        parrafo (D-02): se traduce como el salto entre lineas del <p>. En
        un codigo en linea, texto_plano() lo convierte en un espacio.
        """
        if nodo is None:
            return ''
        html = ''
        i = 0
        while i < len(nodo.hijos):
            hijo = nodo.hijos[i]
            if hijo.es(TEXTO):
                html = html + escapar(hijo.token.lexema)
            elif hijo.es(SALTO_LINEA):
                html = html + '\n'
            elif hijo.es(NT_NEGRITA):
                interno = recorridos.hijo_con_simbolo(hijo, NT_EN_LINEA_N)
                html = html + '<strong>' + self._en_linea(interno)
                html = html + '</strong>'
            elif hijo.es(NT_CURSIVA):
                interno = recorridos.hijo_con_simbolo(hijo, NT_EN_LINEA_C)
                html = html + '<em>' + self._en_linea(interno) + '</em>'
            elif hijo.es(NT_CODIGO_INLINE):
                html = html + '<code>' + escapar(
                    recorridos.texto_plano(hijo)) + '</code>'
            elif hijo.es(NT_TACHADO):
                interno = recorridos.hijo_con_simbolo(hijo, NT_EN_LINEA_T)
                html = html + '<del>' + self._en_linea(interno) + '</del>'
            elif hijo.es(NT_ENLACE):
                interno = recorridos.hijo_con_simbolo(hijo, NT_EN_LINEA)
                html = (html + '<a href="' +
                        escapar(recorridos.destino(hijo)) + '">' +
                        self._en_linea(interno) + '</a>')
            elif hijo.es(NT_IMAGEN):
                alternativo = recorridos.hijo_con_simbolo(hijo, TEXTO_LITERAL)
                texto_alternativo = ''
                if alternativo is not None:
                    texto_alternativo = alternativo.token.lexema
                html = (html + '<img src="' +
                        escapar(recorridos.destino(hijo)) + '" alt="' +
                        escapar(texto_alternativo) + '">')
            i = i + 1
        return html


def recursos_de_resaltado():
    """
    El tema y la libreria highlight.js para la cabecera del Reporte 1,
    embebidos para que el reporte siga siendo un solo archivo y funcione
    sin internet. Si los archivos no estan, el codigo se ve sin colores.
    """
    tema = leer_recurso(ARCHIVO_TEMA)
    libreria = leer_recurso(ARCHIVO_RESALTADO)
    if tema == '' or libreria == '':
        return ''
    return ('<style>' + tema + '\n' + CSS_RESALTADO + '</style>\n'
            '<script>' + libreria + '</script>\n'
            '<script>window.addEventListener("DOMContentLoaded", '
            'function () { ' + SCRIPT_RESALTADO + ' });</script>\n')


def leer_recurso(nombre):
    ruta = os.path.join(CARPETA_RECURSOS, nombre)
    if not os.path.isfile(ruta):
        return ''
    archivo = open(ruta, 'r', encoding='utf-8')
    contenido = archivo.read()
    archivo.close()
    return contenido
