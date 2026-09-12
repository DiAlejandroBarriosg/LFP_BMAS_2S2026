# -*- coding: utf-8 -*-
"""
alfabeto.py
Definicion del alfabeto de HorarioScript y funciones de pertenencia.

RESTRICCION DEL PROYECTO: no se permite el modulo re ni funciones de alto
nivel de cadenas (split, find, strip, isalpha, isdigit, etc.) para la
tokenizacion. Todo aqui se resuelve comparando caracteres uno por uno contra
listas explicitas y recorriendo con indexacion.

===========================================================================
COMO MODIFICAR EL ALFABETO
===========================================================================
El alfabeto esta escrito como listas de caracteres, no como rangos
numericos. Para aceptar un caracter nuevo se agrega a la lista que
corresponda y no hay que tocar ninguna funcion.

Ejemplos:

  Aceptar el guion bajo dentro de las palabras
      agregar '_' a la lista EXTRA_PALABRA

  Aceptar letras con tilde y la enie
      agregar las vocales acentuadas a LETRAS_MINUSCULAS
      y sus mayusculas a LETRAS_MAYUSCULAS

  Aceptar un simbolo estructural nuevo, por ejemplo el parentesis
      agregar '(' y ')' a SIMBOLOS

  Dejar de aceptar el punto y coma
      quitar ';' de SIMBOLOS

Se eligieron listas explicitas en lugar de comparaciones de rango con ord()
a proposito: modificar el alfabeto no exige recordar ningun codigo numerico
ni recalcular limites. El costo es que una comprobacion recorre la lista en
lugar de hacer dos comparaciones, lo cual es irrelevante para archivos de
horario y se compensa con la facilidad de mantenimiento.
===========================================================================
"""

LETRAS_MAYUSCULAS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
                     'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V',
                     'W', 'X', 'Y', 'Z']

LETRAS_MINUSCULAS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
                     'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
                     'w', 'x', 'y', 'z']

DIGITOS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

# Caracteres adicionales admitidos DENTRO de una palabra o un codigo,
# despues del primer caracter. Hoy esta vacia; agregar '_' aqui habilita
# identificadores como mi_curso sin tocar ninguna funcion.
EXTRA_PALABRA = []

SIMBOLOS = ['{', '}', '[', ']', ':', ',', ';']

GUION = '-'
COMILLA = '"'
NUMERAL = '#'
DOS_PUNTOS = ':'

ESPACIOS = [' ', '\t', '\r', '\n']


# ----------------------------------------------------------------------
# Busqueda basica
# ----------------------------------------------------------------------

def esta_en(c, lista):
    """
    True si el caracter c aparece en la lista. Recorre con indexacion,
    sin usar el operador in.
    """
    i = 0
    while i < len(lista):
        if c == lista[i]:
            return True
        i = i + 1
    return False


def indice_en(c, lista):
    """Posicion de c en la lista, o -1 si no esta."""
    i = 0
    while i < len(lista):
        if c == lista[i]:
            return i
        i = i + 1
    return -1


# ----------------------------------------------------------------------
# Pertenencia al alfabeto
# ----------------------------------------------------------------------

def es_letra(c):
    """True si c es una letra del alfabeto definido arriba."""
    if c == '':
        return False
    if esta_en(c, LETRAS_MAYUSCULAS):
        return True
    if esta_en(c, LETRAS_MINUSCULAS):
        return True
    return False


def es_digito(c):
    """True si c es uno de los digitos definidos arriba."""
    if c == '':
        return False
    return esta_en(c, DIGITOS)


def es_alfanumerico(c):
    """
    True si c puede aparecer dentro de una palabra o un codigo, despues del
    primer caracter: letra, digito o cualquiera de EXTRA_PALABRA.
    """
    if es_letra(c):
        return True
    if es_digito(c):
        return True
    return esta_en(c, EXTRA_PALABRA)


def es_simbolo(c):
    """True si c es uno de los simbolos estructurales del lenguaje."""
    if c == '':
        return False
    return esta_en(c, SIMBOLOS)


def es_espacio(c):
    """True si c es espacio, tabulacion, retorno de carro o salto de linea."""
    if c == '':
        return False
    return esta_en(c, ESPACIOS)


# ----------------------------------------------------------------------
# Comparacion de cadenas
# ----------------------------------------------------------------------

def son_iguales(a, b):
    """
    Compara dos cadenas caracter por caracter.

    Se implementa a mano en lugar de usar == para dejar constancia de que la
    comparacion contra las palabras reservadas tambien opera a bajo nivel.
    """
    if len(a) != len(b):
        return False
    i = 0
    while i < len(a):
        if a[i] != b[i]:
            return False
        i = i + 1
    return True


def pertenece(lexema, coleccion):
    """True si lexema coincide con algun elemento de la coleccion."""
    i = 0
    while i < len(coleccion):
        if son_iguales(lexema, coleccion[i]):
            return True
        i = i + 1
    return False


# ----------------------------------------------------------------------
# Conversion de digitos a numero
# ----------------------------------------------------------------------

def valor_digito(c):
    """
    Valor numerico de un caracter digito, o -1 si no lo es.

    Se obtiene de la POSICION del caracter en la lista DIGITOS: el 0 esta en
    el indice 0, el 7 en el indice 7. Asi no hace falta restar 48 ni
    recordar ningun codigo ASCII.
    """
    return indice_en(c, DIGITOS)


def valor_entero(digitos):
    """
    Convierte una cadena de digitos a entero sin usar int().
    Recorre de izquierda a derecha acumulando: valor = valor * 10 + digito.
    Los caracteres que no sean digitos se ignoran.
    """
    valor = 0
    i = 0
    while i < len(digitos):
        d = valor_digito(digitos[i])
        if d >= 0:
            valor = valor * 10 + d
        i = i + 1
    return valor
