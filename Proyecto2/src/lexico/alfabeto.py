# -*- coding: utf-8 -*-
"""
alfabeto.py
Clases de caracteres que usa el AFD de MarkdownCheck.

RESTRICCION DEL PROYECTO: no se usa el modulo re. Cada clase de caracteres
se declara como una lista explicita y se consulta recorriendola indice por
indice con indice_en(), igual que en el Proyecto 1.

En Markdown cualquier caracter puede formar parte de un TEXTO, asi que aqui
solo se declaran los caracteres que tienen un significado especial para el
automata. Todo lo que no esta en estas listas es texto.
"""

# Separadores horizontales: separan un marcador de bloque (#, -, >) de su
# contenido, y forman la sangria de las listas.
SEPARADORES = [' ', '\t']

# Caracteres que forman una VIÑETA cuando van al inicio de la linea (despues
# de la sangria) y les sigue un separador.
MARCADORES_LISTA = ['-', '*', '+']

# Caracteres que cortan un TEXTO dentro de una linea (estado q15): a partir
# de ellos puede empezar NEGRITA, CURSIVA o CODIGO_INLINE.
DELIMITADORES_EN_LINEA = ['*', '`']


def indice_en(c, lista):
    """
    Posicion de c dentro de lista, o -1 si no esta.

    Es la funcion base del modulo: todas las pruebas de pertenencia se apoyan
    en ella. Se devuelve -1 y no 0 porque 0 es una posicion valida (el primer
    elemento de la lista).
    """
    i = 0
    while i < len(lista):
        if c == lista[i]:
            return i
        i = i + 1
    return -1


def es_separador(c):
    """True si c es espacio o tabulacion."""
    return indice_en(c, SEPARADORES) != -1


def es_marcador_lista(c):
    """True si c es '-', '*' o '+'."""
    return indice_en(c, MARCADORES_LISTA) != -1


def es_delimitador_en_linea(c):
    """True si c es '*' o '`'."""
    return indice_en(c, DELIMITADORES_EN_LINEA) != -1


def es_fin_de_linea(c):
    """
    True si c termina la linea actual.
    '\\n' es el salto de linea; '' significa que ya no queda texto (la
    ultima linea del archivo no siempre termina en '\\n').
    """
    if c == '\n':
        return True
    if c == '':
        return True
    return False
