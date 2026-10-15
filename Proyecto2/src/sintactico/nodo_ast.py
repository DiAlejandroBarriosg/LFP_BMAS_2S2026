# -*- coding: utf-8 -*-
"""
nodo_ast.py
NodoAST: un nodo del arbol de derivacion.

Hay dos clases de nodo:
  - No terminal: una produccion de la gramatica que se aplico (<encabezado>,
    <lista>...). Tiene hijos y no tiene token.
  - Terminal (hoja): un token que el parser consumio (NUMERAL, TEXTO...).
    Tiene token y no tiene hijos.

Los nombres de los no terminales se declaran aqui una sola vez, con el
prefijo NT_ (no terminal), para que el parser y los generadores de reportes
usen exactamente el mismo texto.
"""

NT_DOCUMENTO = '<documento>'
NT_BLOQUE = '<bloque>'
NT_ENCABEZADO = '<encabezado>'
NT_PARRAFO = '<parrafo>'
NT_LINEA_TEXTO = '<linea_texto>'
NT_LISTA = '<lista>'
NT_ITEM_LISTA = '<item_lista>'
NT_SUBLISTA = '<sublista>'
NT_CITA = '<cita>'
NT_CONTENIDO_CITA = '<contenido_cita>'
NT_BLOQUE_CODIGO = '<bloque_codigo>'
NT_CONTENIDO_CODIGO = '<contenido_codigo>'
NT_REGLA_HORIZONTAL = '<regla_horizontal>'
NT_EN_LINEA = '<en_linea>'
NT_EN_LINEA_N = '<en_linea_n>'
NT_EN_LINEA_C = '<en_linea_c>'
NT_NEGRITA = '<negrita>'
NT_CURSIVA = '<cursiva>'
NT_CODIGO_INLINE = '<codigo_inline>'

# Alcance opcional (D-29 a D-33)
NT_TACHADO = '<tachado>'
NT_EN_LINEA_T = '<en_linea_t>'
NT_ENLACE = '<enlace>'
NT_IMAGEN = '<imagen>'
NT_DESTINO = '<destino>'
NT_TABLA = '<tabla>'
NT_FILA_TABLA = '<fila_tabla>'
NT_CELDA = '<celda>'


class NodoAST:
    """
    simbolo  nombre del no terminal ('<lista>') o tipo del token ('TEXTO')
    token    el Token, solo en las hojas; None en los no terminales
    hijos    nodos hijos, en el orden en que se reconocieron
    nivel    atributo de la gramatica (seccion 4.1 del diseno):
               <encabezado>  1 a 6, la cantidad de '#'
               <lista>       profundidad: la lista raiz es 1
               <cita>        el n de <cita(n)>: la cita raiz es 1
             En los demas nodos queda en 0.
    numerada     solo en <lista>: True si sus items usan NUMERO_LISTA, el
                 atributo t de <lista(t)> (D-29)
    alineaciones solo en <tabla>: la alineacion de cada columna ('left',
                 'center', 'right' o ''), sacada del SEPARADOR_TABLA
    """

    def __init__(self, simbolo, token):
        self.simbolo = simbolo
        self.token = token
        self.hijos = []
        self.nivel = 0
        self.numerada = False
        self.alineaciones = []

    def agregar(self, hijo):
        self.hijos.append(hijo)

    def es_terminal(self):
        return self.token is not None

    def es(self, simbolo):
        return self.simbolo == simbolo

    def descripcion(self):
        """
        Etiqueta del nodo, por ejemplo:
            <lista> nivel 2
            TEXTO "Hola"
        """
        if self.es_terminal():
            return self.simbolo + ' "' + self.token.lexema_visible() + '"'
        texto = self.simbolo
        if self.nivel > 0:
            texto = texto + ' nivel ' + str(self.nivel)
        if self.numerada:
            texto = texto + ' numerada'
        return texto


def no_terminal(simbolo):
    """Crea el nodo de un no terminal: sin token, todavia sin hijos."""
    return NodoAST(simbolo, None)


def terminal(token):
    """Crea la hoja de un token consumido. Su simbolo es el tipo del token."""
    return NodoAST(token.tipo, token)
