# -*- coding: utf-8 -*-
"""
ver_tokens.py
Muestra en consola la tabla de tokens y la tabla de errores de un archivo .md

Uso, desde la carpeta Proyecto2:
    python tests/ver_tokens.py examples/ejemplo_valido.md
    python tests/ver_tokens.py examples/errores_lexicos.md

Sin argumento, analiza examples/ejemplo_valido.md.
"""

import os
import sys

CARPETA_TESTS = os.path.dirname(os.path.abspath(__file__))
CARPETA_PROYECTO = os.path.dirname(CARPETA_TESTS)
sys.path.insert(0, os.path.join(CARPETA_PROYECTO, 'src'))

from lexico.analizador_lexico import AnalizadorLexico
from errores.gestor_errores import GestorErrores

ANCHO_LEXEMA = 40


def rellenar(texto, ancho):
    """Agrega espacios a la derecha hasta completar 'ancho' caracteres."""
    resultado = texto
    while len(resultado) < ancho:
        resultado = resultado + ' '
    return resultado


def recortar(texto, maximo):
    """Deja como mucho 'maximo' caracteres; si corta, termina en '...'."""
    if len(texto) <= maximo:
        return texto
    resultado = ''
    i = 0
    while i < maximo - 3:
        resultado = resultado + texto[i]
        i = i + 1
    return resultado + '...'


def imprimir_tokens(tokens):
    encabezado = (rellenar('No.', 6) + rellenar('Tipo', 18) +
                  rellenar('Lexema', ANCHO_LEXEMA + 2) +
                  rellenar('Linea', 7) + 'Columna')
    print(encabezado)
    print('-' * len(encabezado))
    i = 0
    while i < len(tokens):
        t = tokens[i]
        print(rellenar(str(t.numero), 6) + rellenar(t.tipo, 18) +
              rellenar(recortar(t.lexema_visible(), ANCHO_LEXEMA),
                       ANCHO_LEXEMA + 2) +
              rellenar(str(t.linea), 7) + str(t.columna))
        i = i + 1


def imprimir_errores(gestor):
    if not gestor.hay_errores():
        print('Sin errores.')
        return
    i = 0
    while i < len(gestor.errores):
        e = gestor.errores[i]
        print('E' + str(e.numero) + '  ' + rellenar(e.fase, 11) +
              rellenar(e.tipo, 26) + 'lexema: ' + e.lexema)
        print('     ' + e.descripcion)
        i = i + 1


def main():
    if len(sys.argv) > 1:
        ruta = sys.argv[1]
    else:
        ruta = os.path.join(CARPETA_PROYECTO, 'examples',
                            'ejemplo_valido.md')

    if not os.path.isfile(ruta):
        print('No existe el archivo: ' + ruta)
        sys.exit(1)

    # utf-8-sig quita la marca BOM si el editor la agrego.
    archivo = open(ruta, 'r', encoding='utf-8-sig')
    texto = archivo.read()
    archivo.close()

    gestor = GestorErrores()
    lexico = AnalizadorLexico(texto, gestor)
    tokens = lexico.analizar_todo()

    print('Archivo: ' + ruta)
    print('')
    imprimir_tokens(tokens)
    print('')
    print('Tokens: ' + str(len(tokens)) + '   Errores: ' +
          str(gestor.cantidad()))
    print('')
    imprimir_errores(gestor)


main()
