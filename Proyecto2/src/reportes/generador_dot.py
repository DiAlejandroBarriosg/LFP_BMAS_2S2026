# -*- coding: utf-8 -*-
"""
generador_dot.py
GeneradorDOT: el arbol de derivacion real en codigo Graphviz (arbol.dot).

Se recorre el AST que construyo el parser, en preorden. Cada nodo recibe un
identificador n0, n1, n2... y una arista desde su padre (seccion 4.10):
  - la raiz <documento>, en azul oscuro con letra blanca;
  - los no terminales (<bloque>, <lista>...), en azul claro;
  - los terminales (tokens), en amarillo, con su tipo y su lexema.

Para ver la imagen:  dot -Tpng arbol.dot -o arbol.png
"""

from reportes.plantilla import guardar

NOMBRE_ARCHIVO = 'arbol.dot'

COLOR_RAIZ = '#2E75B6'
COLOR_NO_TERMINAL = '#D6EAF8'
COLOR_TERMINAL = '#F9E79F'

# Lexemas largos se recortan para que los nodos no queden enormes.
MAXIMO_LEXEMA = 24


class GeneradorDOT:

    def __init__(self, raiz):
        self.raiz = raiz
        self.contador = 0
        self.nodos = ''
        self.aristas = ''

    def generar(self):
        """Devuelve el codigo DOT completo."""
        self.contador = 0
        self.nodos = ''
        self.aristas = ''
        self._visitar(self.raiz, '')
        return ('digraph ArbolDerivacion {\n'
                '    rankdir=TB;\n'
                '    node [shape=box, style=filled, fontname="Arial"];\n'
                '    edge [arrowsize=0.6];\n' +
                self.nodos + self.aristas +
                '}\n')

    def guardar(self, carpeta):
        return guardar(carpeta, NOMBRE_ARCHIVO, self.generar())

    def _visitar(self, nodo, id_padre):
        """
        Escribe el nodo y su arista, y despues visita a sus hijos de
        izquierda a derecha. Devuelve el identificador que le toco.
        """
        identificador = 'n' + str(self.contador)
        self.contador = self.contador + 1

        if nodo.es_terminal():
            etiqueta = (nodo.simbolo + '\\n' +
                        self._recortar(nodo.token.lexema_visible()))
            estilo = 'fillcolor="' + COLOR_TERMINAL + '"'
        elif id_padre == '':
            etiqueta = nodo.simbolo
            estilo = 'fillcolor="' + COLOR_RAIZ + '", fontcolor=white'
        else:
            etiqueta = nodo.simbolo
            if nodo.nivel > 0:
                etiqueta = etiqueta + '\\nnivel ' + str(nodo.nivel)
            if nodo.numerada:
                etiqueta = etiqueta + '\\nnumerada'
            estilo = 'fillcolor="' + COLOR_NO_TERMINAL + '"'

        self.nodos = (self.nodos + '    ' + identificador + ' [label="' +
                      etiqueta + '", ' + estilo + '];\n')
        if id_padre != '':
            self.aristas = (self.aristas + '    ' + id_padre + ' -> ' +
                            identificador + ';\n')

        i = 0
        while i < len(nodo.hijos):
            self._visitar(nodo.hijos[i], identificador)
            i = i + 1
        return identificador

    def _recortar(self, texto):
        """
        Deja el lexema listo para ir entre comillas en DOT: como mucho
        MAXIMO_LEXEMA caracteres, y con \\ y " escapados para que Graphviz
        no los confunda con el fin de la etiqueta.
        """
        resultado = ''
        i = 0
        while i < len(texto) and i < MAXIMO_LEXEMA:
            c = texto[i]
            if c == '\\':
                resultado = resultado + '\\\\'
            elif c == '"':
                resultado = resultado + '\\"'
            else:
                resultado = resultado + c
            i = i + 1
        if len(texto) > MAXIMO_LEXEMA:
            resultado = resultado + '...'
        return resultado
