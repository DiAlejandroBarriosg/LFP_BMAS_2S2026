# -*- coding: utf-8 -*-
"""
alfabeto.py
Funciones de pertenencia al alfabeto de HorarioScript.

RESTRICCION DEL PROYECTO: no se permite el modulo re ni funciones de alto nivel
de cadenas (split, find, strip, isalpha, isdigit, in sobre str, etc.) para la
tokenizacion. Todo aqui se resuelve comparando codigos de caracter con ord() y
recorriendo tuplas indice por indice.
"""

# Codigos ASCII usados en las comparaciones
COD_A_MAY = 65   # 'A'
COD_Z_MAY = 90   # 'Z'
COD_A_MIN = 97   # 'a'
COD_Z_MIN = 122  # 'z'
COD_CERO = 48    # '0'
COD_NUEVE = 57   # '9'

SIMBOLOS = ('{', '}', '[', ']', ':', ',', ';')
ESPACIOS = (' ', '\t', '\r', '\n')


def es_letra(c):
    """True si c es una letra ASCII sin tilde (A-Z o a-z)."""
    if c == '':
        return False
    n = ord(c)
    if n >= COD_A_MAY and n <= COD_Z_MAY:
        return True
    if n >= COD_A_MIN and n <= COD_Z_MIN:
        return True
    return False


def es_digito(c):
    """True si c es un digito decimal (0-9)."""
    if c == '':
        return False
    n = ord(c)
    return n >= COD_CERO and n <= COD_NUEVE


def es_alfanumerico(c):
    return es_letra(c) or es_digito(c)


def es_simbolo(c):
    """True si c es uno de los simbolos estructurales del lenguaje."""
    i = 0
    while i < len(SIMBOLOS):
        if c == SIMBOLOS[i]:
            return True
        i = i + 1
    return False


def es_espacio(c):
    """True si c es espacio, tabulacion, retorno de carro o salto de linea."""
    i = 0
    while i < len(ESPACIOS):
        if c == ESPACIOS[i]:
            return True
        i = i + 1
    return False


def son_iguales(a, b):
    """
    Compara dos cadenas caracter por caracter.

    Se implementa a mano en lugar de usar == para dejar constancia de que la
    comparacion contra las palabras reservadas tambien se hace a bajo nivel.
    """
    if len(a) != len(b):
        return False
    i = 0
    while i < len(a):
        if a[i] != b[i]:
            return False
        i = i + 1
    return True


def pertenece(lexema, tupla):
    """True si lexema coincide exactamente con algun elemento de la tupla."""
    i = 0
    while i < len(tupla):
        if son_iguales(lexema, tupla[i]):
            return True
        i = i + 1
    return False


def valor_entero(digitos):
    """
    Convierte una cadena de digitos a entero sin usar int().
    Recorre de izquierda a derecha acumulando: valor = valor * 10 + digito.
    """
    valor = 0
    i = 0
    while i < len(digitos):
        valor = valor * 10 + (ord(digitos[i]) - COD_CERO)
        i = i + 1
    return valor
