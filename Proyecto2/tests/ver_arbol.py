# -*- coding: utf-8 -*-
"""
ver_arbol.py
Muestra en consola el arbol de derivacion de un archivo .md

Uso, desde la carpeta Proyecto2:
    python tests/ver_arbol.py examples/ejemplo_valido.md
    python tests/ver_arbol.py examples/errores_sintacticos.md

Sin argumento, analiza examples/ejemplo_valido.md.
Cada nivel del arbol se muestra con dos espacios mas de sangria. Los no
terminales van entre < >; las hojas muestran el tipo y el lexema del token.
"""

import os
import sys

CARPETA_TESTS = os.path.dirname(os.path.abspath(__file__))
CARPETA_PROYECTO = os.path.dirname(CARPETA_TESTS)
sys.path.insert(0, os.path.join(CARPETA_PROYECTO, 'src'))

# Una consola de Windows (cp850, cp1252) no tiene todos los caracteres que
# puede traer un documento ('—', '☑'...). Los que no puede mostrar se
# escriben como '?' en lugar de detener el programa.
sys.stdout.reconfigure(errors='replace')

from lexico.analizador_lexico import AnalizadorLexico
from sintactico.analizador_sintactico import AnalizadorSintactico
from errores.gestor_errores import GestorErrores


def imprimir_nodo(nodo, profundidad):
    """Recorrido en preorden: primero el nodo, despues cada hijo."""
    sangria = ''
    i = 0
    while i < profundidad:
        sangria = sangria + '  '
        i = i + 1
    print(sangria + nodo.descripcion())
    i = 0
    while i < len(nodo.hijos):
        imprimir_nodo(nodo.hijos[i], profundidad + 1)
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

    archivo = open(ruta, 'r', encoding='utf-8-sig')
    texto = archivo.read()
    archivo.close()

    gestor = GestorErrores()
    lexico = AnalizadorLexico(texto, gestor)
    parser = AnalizadorSintactico(lexico, gestor)
    raiz = parser.analizar()

    print('Archivo: ' + ruta)
    print('')
    imprimir_nodo(raiz, 0)
    print('')
    if not gestor.hay_errores():
        print('Sin errores.')
    i = 0
    while i < len(gestor.errores):
        print(gestor.errores[i].como_texto())
        i = i + 1


main()
